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

    // Wizard State
    let currentStep = 1;
    const totalSteps = 4;
    const nextBtn = document.getElementById('next-step');
    const prevBtn = document.getElementById('prev-step');
    const newCampaignBtn = document.getElementById('new-campaign-btn');

    function updateWizardUI() {
        // Show/Hide Steps
        document.querySelectorAll('.wizard-step').forEach(step => {
            step.classList.remove('active');
        });
        document.getElementById(`step-${currentStep}`).classList.add('active');

        // Update Nav Buttons
        prevBtn.style.visibility = (currentStep === 1) ? 'hidden' : 'visible';

        if (currentStep === totalSteps) {
            nextBtn.style.display = 'none';
        } else {
            nextBtn.style.display = 'flex';
            nextBtn.innerHTML = `Next Stage <i data-lucide="chevron-right"></i>`;
            lucide.createIcons();
        }

        // Update Progress Indicator
        document.querySelectorAll('.step-indicator').forEach((indicator, index) => {
            const stepNum = index + 1;
            indicator.classList.remove('active', 'completed');
            if (stepNum === currentStep) {
                indicator.classList.add('active');
            } else if (stepNum < currentStep) {
                indicator.classList.add('completed');
            }
        });
    }

    function validateStep(step) {
        if (step === 1) {
            const folderId = document.getElementById('folder-id').value;
            if (!folderId) {
                addLog('Error: Google Drive Folder ID is required.', 'error');
                return false;
            }
        } else if (step === 2) {
            const moneyPages = document.getElementById('money-pages').value;
            if (!moneyPages) {
                addLog('Error: Please list your money pages.', 'error');
                return false;
            }
        } else if (step === 3) {
            const semrushStatus = document.getElementById('semrush-status').value;
            const isBypassed = semrushStatus === 'no-ranking';
            const requiredFileCount = isBypassed ? 1 : 2;

            if (uploadedFiles.length < requiredFileCount) {
                addLog(`Error: Please upload ${requiredFileCount} CSV file(s) to continue.`, 'error');
                return false;
            }

            // Basic identification check
            const gscFile = uploadedFiles.find(f => f.name.toLowerCase().includes('gsc') || f.name.toLowerCase().includes('search-console'));
            if (!gscFile) {
                addLog('Error: GSC file not identified. Please ensure one file contains "gsc" in the name.', 'error');
                // return false; // Soft warning for now or strict? Let's stay flexible but warn.
            }
        }
        return true;
    }

    nextBtn.addEventListener('click', () => {
        if (validateStep(currentStep)) {
            currentStep++;
            updateWizardUI();
        }
    });

    prevBtn.addEventListener('click', () => {
        if (currentStep > 1) {
            currentStep--;
            updateWizardUI();
        }
    });

    newCampaignBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to restart the wizard? Current progress will be lost.')) {
            currentStep = 1;
            form.reset();
            uploadedFiles = [];
            updateFileList();
            updateWizardUI();
            logDisplay.innerHTML = '<div class="log-entry system">Standing by for execution...</div>';
        }
    });

    // Integrated Form Submission (Step 4 Execute)
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Final verification
        const folderId = document.getElementById('folder-id').value;
        const semrushStatus = document.getElementById('semrush-status').value;
        const isBypassed = semrushStatus === 'no-ranking';

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
                    const linkContainer = document.createElement('div');
                    linkContainer.style.marginTop = '15px';
                    linkContainer.innerHTML = `
                        <a href="${data.url}" target="_blank" class="btn-primary" style="display: inline-flex; align-items: center; gap: 8px; text-decoration: none; padding: 12px 24px; border-radius: 12px; font-size: 0.9rem; background: var(--primary); color: black;">
                            <i data-lucide="external-link"></i>
                            View Full Query Report
                        </a>
                    `;
                    logDisplay.appendChild(linkContainer);
                    lucide.createIcons();
                    logDisplay.scrollTop = logDisplay.scrollHeight;
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
        let gscFile = uploadedFiles.find(f =>
            f.name.toLowerCase().includes('gsc') ||
            f.name.toLowerCase().includes('search-console') ||
            f.name.toLowerCase().includes('queries') ||
            f.name.toLowerCase().includes('pages')
        );
        let semrushFile = uploadedFiles.find(f =>
            f.name.toLowerCase().includes('semrush') ||
            f.name.toLowerCase().includes('keyword')
        );

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
                let errorMsg = 'Failed to start workflow';
                try {
                    const errData = await response.json();
                    errorMsg = errData.detail || errorMsg;
                } catch (e) {
                    // Handle non-JSON response (e.g. 404 HTML)
                    errorMsg = `Backend Error (${response.status}): The API endpoint might be incorrectly routed or down.`;
                }
                throw new Error(errorMsg);
            }

        } catch (error) {
            addLog(`Error: ${error.message}`, 'error');
            eventSource.close();
            executeBtn.disabled = false;
            executeBtn.style.opacity = '1';
            executeBtn.querySelector('span').innerText = 'Execute Workflow 1';
        }
    });

    // Initialize UI
    updateWizardUI();
});
