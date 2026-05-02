document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    
    const loadingState = document.getElementById('loading-state');
    const successState = document.getElementById('success-state');
    const errorState = document.getElementById('error-state');
    const errorMessage = document.getElementById('error-message');
    
    const downloadBtn = document.getElementById('download-btn');
    const resetBtn = document.getElementById('reset-btn');
    const retryBtn = document.getElementById('retry-btn');
    
    let currentBlobUrl = null;

    // Events for Drag and Drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('drag-active');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('drag-active');
        }, false);
    });

    dropZone.addEventListener('drop', handleDrop, false);

    // Events for click selection
    browseBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent triggering dropZone click if nested
        fileInput.click();
    });
    
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            handleFile(this.files[0]);
        }
    });

    resetBtn.addEventListener('click', resetUI);
    retryBtn.addEventListener('click', resetUI);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files && files[0]) {
            handleFile(files[0]);
        }
    }

    function handleFile(file) {
        if (file.type !== 'application/pdf') {
            showError('Veuillez sélectionner un fichier PDF valide.');
            return;
        }

        uploadFile(file);
    }

    async function uploadFile(file) {
        showLoading();

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/convert', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Une erreur est survenue lors de la conversion.');
            }

            // Get the filename from the Content-Disposition header if possible
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'converted.epub';
            if (contentDisposition && contentDisposition.indexOf('attachment') !== -1) {
                const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                const matches = filenameRegex.exec(contentDisposition);
                if (matches != null && matches[1]) { 
                    filename = matches[1].replace(/['"]/g, '');
                }
            }

            const blob = await response.blob();
            
            // Clean up previous blob if it exists
            if (currentBlobUrl) {
                URL.revokeObjectURL(currentBlobUrl);
            }
            
            currentBlobUrl = URL.createObjectURL(blob);
            
            showSuccess();
            
            // Setup download button
            downloadBtn.onclick = () => {
                const a = document.createElement('a');
                a.href = currentBlobUrl;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            };
            
            // Auto trigger download
            downloadBtn.click();

        } catch (error) {
            showError(error.message);
        }
    }

    function showLoading() {
        dropZone.classList.add('hidden');
        successState.classList.add('hidden');
        errorState.classList.add('hidden');
        loadingState.classList.remove('hidden');
    }

    function showSuccess() {
        dropZone.classList.add('hidden');
        loadingState.classList.add('hidden');
        errorState.classList.add('hidden');
        successState.classList.remove('hidden');
    }

    function showError(message) {
        dropZone.classList.add('hidden');
        loadingState.classList.add('hidden');
        successState.classList.add('hidden');
        errorState.classList.remove('hidden');
        errorMessage.textContent = message;
    }

    function resetUI() {
        fileInput.value = '';
        loadingState.classList.add('hidden');
        successState.classList.add('hidden');
        errorState.classList.add('hidden');
        dropZone.classList.remove('hidden');
    }
});
