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

    let uploadedFiles = [];

    function updateFileList() {
        const container = document.getElementById('file-list-container');
        const list = document.getElementById('file-list');
        list.innerHTML = '';

        if (uploadedFiles.length === 0) {
            container.style.display = 'none';
        } else {
            container.style.display = 'block';
            uploadedFiles.forEach((file, index) => {
                const item = document.createElement('div');
                item.className = 'file-item';
                item.innerHTML = `
                    <span>${file.name}</span>
                    <i data-lucide="check-circle"></i>
                `;
                list.appendChild(item);
            });
        }
        lucide.createIcons();
    }

    // Clear Files Handler
    document.getElementById('clear-files').addEventListener('click', () => {
        uploadedFiles = [];
        fileInput.value = '';
        updateFileList();
        addLog('All attached files cleared.', 'info');
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
        const newFiles = Array.from(files);
        newFiles.forEach(file => {
            // Avoid duplicates by name
            if (!uploadedFiles.some(f => f.name === file.name)) {
                uploadedFiles.push(file);
                addLog(`File attached: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, 'info');
            }
        });
        updateFileList();
    }

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const folderId = document.getElementById('folder-id').value;
        const semrushStatus = document.getElementById('semrush-status').value;

        if (!folderId) {
            addLog('Error: Google Drive Folder ID is required.', 'error');
            return;
        }

        const isBypassed = semrushStatus === 'no-ranking';
        const requiredFileCount = isBypassed ? 1 : 2;

        if (uploadedFiles.length < requiredFileCount) {
            addLog(`Error: Please upload ${requiredFileCount} CSV file(s) for this configuration.`, 'error');
            return;
        }

        // 1. Start Log Streaming
        const eventSource = new EventSource('/logs');
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            addLog(data.message, data.type);

            if (data.status === 'complete') {
                eventSource.close();
                executeBtn.disabled = false;
                executeBtn.style.opacity = '1';
                executeBtn.querySelector('span').innerText = 'Execute Workflow 1';

                if (data.url) {
                    const link = document.createElement('a');
                    link.href = data.url;
                    link.target = '_blank';
                    link.innerText = ' [Open Spreadsheet]';
                    link.style.color = 'var(--primary)';
                    logDisplay.lastElementChild.appendChild(link);
                }
            }
        };

        // 2. Prepare Form Data
        const formData = new FormData();
        formData.append('campaign_type', document.getElementById('campaign-type').value);
        formData.append('folder_id', folderId);
        formData.append('money_pages', document.getElementById('money-pages').value);
        formData.append('semrush_status', semrushStatus);

        // Simple identification logic based on filename keywords
        let gscFile = uploadedFiles.find(f => f.name.toLowerCase().includes('gsc') || f.name.toLowerCase().includes('search-console'));
        let semrushFile = uploadedFiles.find(f => f.name.toLowerCase().includes('semrush') || f.name.toLowerCase().includes('keyword'));

        // Fallback to index if naming doesn't help
        if (!gscFile && uploadedFiles.length > 0) gscFile = uploadedFiles[0];
        if (!semrushFile && uploadedFiles.length > 1) {
            semrushFile = (uploadedFiles[0] === gscFile) ? uploadedFiles[1] : uploadedFiles[0];
        }

        if (gscFile) formData.append('gsc_csv', gscFile);
        if (semrushFile && !isBypassed) formData.append('semrush_csv', semrushFile);

        const executeBtn = form.querySelector('.btn-execute');
        executeBtn.disabled = true;
        executeBtn.style.opacity = '0.5';
        executeBtn.querySelector('span').innerText = 'Processing...';

        addLog('Connecting to Python backend...', 'info');

        try {
            const response = await fetch('/run-workflow', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Failed to start workflow');
            }

        } catch (error) {
            addLog(`Error: ${error.message}`, 'error');
            eventSource.close();
            executeBtn.disabled = false;
            executeBtn.style.opacity = '1';
            executeBtn.querySelector('span').innerText = 'Execute Workflow 1';
        }
    });
});
