import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import fitz  # PyMuPDF
from ebooklib import epub
from bs4 import BeautifulSoup

app = FastAPI(title="PDF to EPUB Converter")

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
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
        
        chapters = []
        
        # Process each page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # HTML string for the chapter
            html_content = ""
            
            # Extract text blocks
            blocks = page.get_text("dict")["blocks"]
            import re
            
            for block in blocks:
                if block['type'] == 0:  # Text block
                    text_content = ""
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_content += span["text"] + " "
                            
                    clean_text = text_content.strip()
                    # Ignorer les blocs qui ne contiennent qu'un numéro de page (ex: "33", "- 33 -", "– 33 –")
                    if re.fullmatch(r'[-–—]?\s*\d+\s*[-–—]?', clean_text):
                        continue
                        
                    # Clean up with BeautifulSoup to ensure valid XML
                    soup = BeautifulSoup(f"<p>{clean_text}</p>", "html.parser")
                    html_content += str(soup) + "\n"
                
                elif block['type'] == 1:  # Image block
                    # Extract image
                    try:
                        base_image = doc.extract_image(block["number"])
                        if base_image:
                            image_bytes = base_image["image"]
                            image_ext = base_image["ext"]
                            image_name = f"image_{page_num}_{block['number']}.{image_ext}"
                            
                            # Add image to epub
                            epub_img = epub.EpubItem(
                                uid=image_name,
                                file_name=f"images/{image_name}",
                                media_type=f"image/{image_ext}",
                                content=image_bytes
                            )
                            book.add_item(epub_img)
                            
                            # Add img tag to html
                            html_content += f'<div style="text-align:center; margin: 1em 0;"><img src="images/{image_name}" alt="Image page {page_num+1}" style="max-width:100%;"/></div>\n'
                    except Exception as e:
                        print(f"Failed to extract image: {e}")
            
            # Create chapter
            c = epub.EpubHtml(title=f"Page {page_num + 1}", file_name=f"page_{page_num + 1}.xhtml", lang='fr')
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
