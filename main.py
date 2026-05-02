import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import fitz  # PyMuPDF
from ebooklib import epub
from bs4 import BeautifulSoup

app = FastAPI(title="PDF to EPUB Converter")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Create static directory if it doesn't exist
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/convert")
async def convert_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF.")
    
    try:
        # Read the uploaded PDF file
        pdf_bytes = await file.read()
        
        # We will create the EPUB entirely in memory then write to a temp file
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        book = epub.EpubBook()
        
        # Set metadata
        title = file.filename.rsplit('.', 1)[0]
        book.set_identifier(f"id_{title}")
        book.set_title(title)
        book.set_language('fr')
        book.add_author('Convertisseur PDF vers EPUB')
        
        # Phase 1: Collect all text and image blocks sequentially
        all_blocks = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                block["page_num"] = page_num
                all_blocks.append(block)

        # Phase 2: Compute base font size
        font_sizes = []
        for block in all_blocks:
            if block['type'] == 0:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_sizes.append(span["size"])
        
        # Using statistics mode to find the most common font size
        import statistics
        try:
            base_size = statistics.mode([round(size) for size in font_sizes])
        except statistics.StatisticsError:
            base_size = 11 # Default fallback

        # Phase 3: Group into logical chapters and merge paragraphs
        logical_chapters = []
        current_chapter_title = "Début"
        current_chapter_blocks = []
        
        import re
        pending_text = ""
        
        for block in all_blocks:
            if block['type'] == 0:  # Text block
                block_text = ""
                max_size = 0
                for line in block["lines"]:
                    for span in line["spans"]:
                        block_text += span["text"] + " "
                        if span["size"] > max_size:
                            max_size = span["size"]
                
                clean_text = block_text.strip()
                
                # Ignorer les blocs qui ne contiennent qu'un numéro de page
                if re.fullmatch(r'[-–—]?\s*\d+\s*[-–—]?', clean_text) or not clean_text:
                    continue
                    
                # Is it a title? (Significantly larger than base font, short text)
                if max_size > base_size * 1.15 and len(clean_text) < 150:
                    # Flush pending text if any
                    if pending_text:
                        current_chapter_blocks.append({"type": "text", "content": pending_text})
                        pending_text = ""
                        
                    # Save current chapter if it has content
                    if current_chapter_blocks:
                        logical_chapters.append({"title": current_chapter_title, "blocks": current_chapter_blocks})
                        
                    # Start new chapter
                    current_chapter_title = clean_text
                    current_chapter_blocks = []
                    current_chapter_blocks.append({"type": "title", "content": clean_text})
                
                else:
                    # Normal text - logic to merge with pending
                    if pending_text:
                        # Si le texte en attente ne se termine pas par une ponctuation forte 
                        # et que le nouveau bloc commence par une minuscule
                        if not re.search(r'[.!?:]\s*$', pending_text) and clean_text and clean_text[0].islower():
                            pending_text += " " + clean_text
                        else:
                            current_chapter_blocks.append({"type": "text", "content": pending_text})
                            pending_text = clean_text
                    else:
                        pending_text = clean_text

            elif block['type'] == 1:  # Image block
                # Flush pending text before image
                if pending_text:
                    current_chapter_blocks.append({"type": "text", "content": pending_text})
                    pending_text = ""
                
                try:
                    base_image = doc.extract_image(block["number"])
                    if base_image:
                        current_chapter_blocks.append({
                            "type": "image",
                            "image_bytes": base_image["image"],
                            "ext": base_image["ext"],
                            "page_num": block["page_num"],
                            "block_num": block["number"]
                        })
                except Exception as e:
                    print(f"Failed to extract image: {e}")

        # Flush any remaining text
        if pending_text:
            current_chapter_blocks.append({"type": "text", "content": pending_text})
            
        if current_chapter_blocks:
            logical_chapters.append({"title": current_chapter_title, "blocks": current_chapter_blocks})
            
        # Phase 4: Create EPUB Chapters
        chapters = []
        for i, chapter_data in enumerate(logical_chapters):
            c_title = chapter_data["title"]
            c_file_name = f"chapter_{i}.xhtml"
            c = epub.EpubHtml(title=c_title, file_name=c_file_name, lang='fr')
            
            html_content = ""
            for item in chapter_data["blocks"]:
                if item["type"] == "title":
                    soup = BeautifulSoup(f"<h2>{item['content']}</h2>", "html.parser")
                    html_content += str(soup) + "\n"
                elif item["type"] == "text":
                    soup = BeautifulSoup(f"<p>{item['content']}</p>", "html.parser")
                    html_content += str(soup) + "\n"
                elif item["type"] == "image":
                    img_name = f"image_{item['page_num']}_{item['block_num']}.{item['ext']}"
                    
                    try:
                        epub_img = epub.EpubItem(
                            uid=img_name,
                            file_name=f"images/{img_name}",
                            media_type=f"image/{item['ext']}",
                            content=item["image_bytes"]
                        )
                        book.add_item(epub_img)
                    except ValueError:
                        pass
                        
                    html_content += f'<div style="text-align:center; margin: 1em 0;"><img src="images/{img_name}" alt="Image" style="max-width:100%;"/></div>\n'
            
            c.content = html_content
            book.add_item(c)
            chapters.append(c)
        
        # Create TOC and spine
        book.toc = tuple(chapters)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Spine
        book.spine = ['nav'] + chapters
        
        # Write EPUB to a temporary file
        fd, temp_path = tempfile.mkstemp(suffix=".epub")
        os.close(fd)
        epub.write_epub(temp_path, book, {})
        
        response_filename = f"{title}.epub"
        return FileResponse(path=temp_path, filename=response_filename, media_type='application/epub+zip', background=None)

    except Exception as e:
        print(f"Error during conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))
