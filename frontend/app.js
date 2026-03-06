document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('workflow-form');
    const logDisplay = document.getElementById('log-display');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    // Utility: Add log entry
    function addLog(message, type = 'info') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        const time = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        entry.innerText = `[${time}] ${message}`;
        logDisplay.appendChild(entry);
        logDisplay.scrollTop = logDisplay.scrollHeight;
    }

    // Drag & Drop Handlers
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--primary)';
        dropZone.style.background = 'rgba(0, 242, 255, 0.05)';
    });

    ['dragleave', 'drop'].forEach(event => {
        dropZone.addEventListener(event, () => {
            dropZone.style.borderColor = 'var(--card-border)';
            dropZone.style.background = 'transparent';
        });
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFiles(files);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFiles(fileInput.files);
        }
    });

    function handleFiles(files) {
        Array.from(files).forEach(file => {
            addLog(`File detected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, 'info');
        });
    }

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const config = {
            campaignType: document.getElementById('campaign-type').value,
            folderId: document.getElementById('folder-id').value,
            moneyPages: document.getElementById('money-pages').value
        };

        if (!config.folderId) {
            addLog('Error: Google Drive Folder ID is required.', 'error');
            return;
        }

        addLog(`Starting Workflow 1: ${config.campaignType.toUpperCase()} campaign...`, 'system');
        addLog(`Folder targeting: ${config.folderId}`, 'info');
        addLog(`Mapping to ${config.moneyPages.split(',').length} pages...`, 'info');
        
        // Simulating processing for now (integration with FastAPI follows)
        addLog('Connecting to Python backend...', 'info');
        
        const executeBtn = form.querySelector('.btn-execute');
        executeBtn.disabled = true;
        executeBtn.style.opacity = '0.5';
        executeBtn.querySelector('span').innerText = 'Processing...';

        setTimeout(() => {
            addLog('Data merging in progress: GSC + Semrush...', 'info');
            setTimeout(() => {
                addLog('Filtering "near me" keywords...', 'info');
                setTimeout(() => {
                    addLog('Success! Report generated and uploaded to Google Drive.', 'system');
                    executeBtn.disabled = false;
                    executeBtn.style.opacity = '1';
                    executeBtn.querySelector('span').innerText = 'Execute Workflow 1';
                }, 2000);
            }, 1500);
        }, 1500);
    });
});
