document.getElementById('sendBtn').addEventListener('click', sendMessage);
document.getElementById('userInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendMessage();
});

let ttsEnabled = true;
let recognition = null;
let isRecording = false;
let selectedProductImageUrl = null;
let currentAgentSteps = {};

// Initialize TTS Toggle UI State
const voiceToggleBtn = document.getElementById('voiceToggleBtn');
if (voiceToggleBtn) {
    voiceToggleBtn.addEventListener('click', () => {
        ttsEnabled = !ttsEnabled;
        if (ttsEnabled) {
            voiceToggleBtn.classList.remove('opacity-50');
            voiceToggleBtn.title = "Disable Voice Output";
        } else {
            voiceToggleBtn.classList.add('opacity-50');
            voiceToggleBtn.title = "Enable Voice Output";
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
            }
        }
    });
}

// Initialize Speech-to-Text (webkitSpeechRecognition)
const micBtn = document.getElementById('micBtn');
if (micBtn && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        isRecording = true;
        micBtn.classList.add('active');
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById('userInput').value = transcript;
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        stopRecording();
    };

    recognition.onend = () => {
        stopRecording();
    };

    micBtn.addEventListener('click', () => {
        if (isRecording) {
            recognition.stop();
        } else {
            recognition.start();
        }
    });
} else if (micBtn) {
    micBtn.style.display = 'none'; // Hide if browser doesn't support it
}

function stopRecording() {
    isRecording = false;
    if (micBtn) micBtn.classList.remove('active');
}

// Initialize Upload features
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const selectedProductBar = document.getElementById('selectedProductBar');
const selectedProductName = document.getElementById('selectedProductName');
const clearProductBtn = document.getElementById('clearProductBtn');

if (uploadZone && fileInput) {
    uploadZone.addEventListener('click', () => fileInput.click());
    
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('border-primary');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('border-primary');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('border-primary');
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

if (clearProductBtn) {
    clearProductBtn.addEventListener('click', () => {
        selectedProductImageUrl = null;
        selectedProductBar.classList.add('d-none');
        document.querySelectorAll('.uploaded-product-thumbnail').forEach(el => {
            el.classList.remove('selected');
        });
    });
}

function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    const uploadText = uploadZone.querySelector('.upload-text');
    if (uploadText) uploadText.innerHTML = 'Uploading image...';

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (uploadText) uploadText.innerHTML = 'Drag & drop product image or click to upload';
        if (data.error) {
            alert('Upload failed: ' + data.error);
        } else {
            selectUploadedProduct(data.image);
            loadAssets();
            fetchSessionState();
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
        if (uploadText) uploadText.innerHTML = 'Drag & drop product image or click to upload';
        alert('File upload failed.');
    });
}

function selectUploadedProduct(image) {
    selectedProductImageUrl = image.url;
    if (selectedProductName) selectedProductName.innerText = image.name;
    if (selectedProductBar) selectedProductBar.classList.remove('d-none');
    
    document.querySelectorAll('.uploaded-product-thumbnail').forEach(el => {
        if (el.getAttribute('src') === image.url) {
            el.classList.add('selected');
        } else {
            el.classList.remove('selected');
        }
    });
}

function updateWorkflowTracker(stepName) {
    const steps = {
        'trend': document.getElementById('step-trend'),
        'product': document.getElementById('step-product'),
        'scene': document.getElementById('step-scene'),
        'ab': document.getElementById('step-ab')
    };

    Object.values(steps).forEach(el => {
        if (el) el.classList.remove('active');
    });

    if (stepName && steps[stepName]) {
        steps[stepName].classList.add('active');
    }
}

function simulateWorkflowProgress() {
    const steps = ['trend', 'product', 'scene', 'ab'];
    let delay = 0;
    
    steps.forEach((step, index) => {
        setTimeout(() => {
            updateWorkflowTracker(step);
        }, delay);
        delay += 1200;
    });
}

function appendMessage(sender, text, type = 'agent') {
    const chatBox = document.getElementById('chatBox');
    if (!chatBox) return;

    let bubbleClass = 'msg-agent';
    let senderPrefix = `<strong>Agent:</strong> `;
    
    if (type === 'user') {
        bubbleClass = 'msg-user';
        senderPrefix = `<strong>You:</strong> `;
    } else if (type === 'system') {
        bubbleClass = 'msg-system';
        senderPrefix = '';
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message-bubble ${bubbleClass}`;
    messageDiv.innerHTML = `${senderPrefix}${text}`;
    
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function sendMessage() {
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();

    if (!message) return;

    appendMessage('You', message, 'user');
    userInput.value = '';
    
    updateWorkflowTracker(null);
    simulateWorkflowProgress();

    const chatPayload = { message: message };
    if (selectedProductImageUrl) {
        chatPayload.image_url = selectedProductImageUrl;
    }

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(chatPayload)
    })
    .then(response => response.json())
    .then(data => {
        setTimeout(() => {
            updateWorkflowTracker('ab');
        }, 500);

        appendMessage('Agent', data.response, 'agent');
        
        if (ttsEnabled) {
            speak(data.response);
        }
        
        if (data.agent_steps) {
            renderAgentWorkspace(data.agent_steps);
            // Switch tabs to Agent Workspace automatically to show strategy results
            const agentsTabEl = document.getElementById('agents-tab');
            if (agentsTabEl) {
                const tab = new bootstrap.Tab(agentsTabEl);
                tab.show();
            }
        }
        
        loadAssets();
    })
    .catch(error => {
        console.error('Error:', error);
        appendMessage('System', 'Failed to communicate with agent orchestrator.', 'system');
        updateWorkflowTracker(null);
    });
}

function speak(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const cleanText = text.replace(/[*#`_\-]/g, '').trim();
        if (!cleanText) return;
        
        const utterance = new SpeechSynthesisUtterance(cleanText);
        window.speechSynthesis.speak(utterance);
    }
}

function renderAgentWorkspace(agentSteps) {
    currentAgentSteps = agentSteps;
    const container = document.getElementById('agentWorkspaceContainer');
    if (!container) return;
    container.innerHTML = '';

    const agentsList = [
        { key: 'TrendAnalyst', badgeClass: 'badge-ta', title: 'Trend Analyst' },
        { key: 'ProductCopier', badgeClass: 'badge-pc', title: 'Product Copier' },
        { key: 'SceneCompositor', badgeClass: 'badge-sc', title: 'Scene Compositor' },
        { key: 'ABVariantGenerator', badgeClass: 'badge-ab', title: 'A/B Variant Generator' }
    ];

    agentsList.forEach(agent => {
        const step = agentSteps[agent.key];
        if (!step) return;

        const card = document.createElement('div');
        card.className = 'agent-strategy-card animate-fade-in';
        
        let visualSectionHtml = '';
        
        if (agent.key === 'ABVariantGenerator') {
            let variantsHtml = '';
            if (step.prompts && step.prompts.length > 0) {
                step.prompts.forEach((prompt, idx) => {
                    const imageUrl = (step.images && step.images[idx]) || '';
                    variantsHtml += `
                        <div class="mb-3 p-3 rounded bg-black bg-opacity-20 border border-secondary border-opacity-10">
                            <span class="fs-7 fw-semibold text-accent-pink">Variant ${idx + 1}</span>
                            <div class="strategy-prompt-box my-2">${prompt}</div>
                            
                            <div class="d-flex flex-column gap-2 mt-2">
                                ${imageUrl ? `
                                    <div class="strategy-image-container">
                                        <img src="${imageUrl}" alt="Variant ${idx + 1}" class="strategy-image" onerror="this.src='https://placehold.co/400?text=Error+Loading';">
                                    </div>
                                ` : `
                                    <div class="strategy-placeholder" id="variant-placeholder-${idx}">
                                        <span class="fs-8">No image generated yet</span>
                                    </div>
                                `}
                                <div>
                                    <button class="btn-generate-strategy mt-2" onclick="generateAgentImage('${agent.key}', \`${prompt.replace(/'/g, "\\'")}\`, ${idx}, this)">
                                        ${imageUrl ? 'Regenerate Image' : 'Generate Image'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                });
            } else {
                variantsHtml = `<div class="text-secondary fs-8">No variant prompts generated yet. Run a campaign request in the chat.</div>`;
            }
            
            visualSectionHtml = `
                <div class="mt-3">
                    <h6 class="fs-7 text-secondary text-uppercase tracking-wider mb-2 font-family-outfit">Variant Strategies</h6>
                    ${variantsHtml}
                </div>
            `;
        } else {
            const imageUrl = step.image_url || '';
            const promptText = step.prompt || '';
            
            let btnLabel = imageUrl ? 'Regenerate Style Preview' : 'Generate Style Preview';
            let showBtn = true;
            
            if (agent.key === 'ProductCopier') {
                showBtn = false; // Mask is auto-generated by the Pillow mask generator on upload
            } else if (agent.key === 'SceneCompositor') {
                btnLabel = imageUrl ? 'Regenerate Backdrop' : 'Generate Backdrop';
            }

            visualSectionHtml = `
                ${promptText ? `
                    <div class="mt-3">
                        <span class="fs-8 text-secondary text-uppercase fw-semibold">Extracted Prompt / Input</span>
                        <div class="strategy-prompt-box mt-1 mb-2">${promptText}</div>
                    </div>
                ` : ''}
                
                <div class="mt-3">
                    ${imageUrl ? `
                        <div class="strategy-image-container">
                            <img src="${imageUrl}" alt="${agent.title}" class="strategy-image" onerror="this.src='https://placehold.co/400?text=Error+Loading';">
                        </div>
                    ` : `
                        <div class="strategy-placeholder">
                            <span class="fs-8">No image generated yet</span>
                        </div>
                    `}
                    
                    ${(showBtn && promptText) ? `
                        <button class="btn-generate-strategy mt-2" onclick="generateAgentImage('${agent.key}', \`${promptText.replace(/'/g, "\\'")}\`, null, this)">
                            ${btnLabel}
                        </button>
                    ` : ''}
                </div>
            `;
        }

        card.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="agent-badge ${agent.badgeClass}">${agent.title}</span>
                <span class="fs-8 text-secondary">Active Strategy</span>
            </div>
            <h6 class="fs-6 fw-semibold text-white mb-2 font-family-outfit">${step.name} Task Detail</h6>
            <p class="fs-7 text-secondary mb-3">${step.strategy || 'Waiting for action...'}</p>
            ${visualSectionHtml}
        `;
        
        container.appendChild(card);
    });
}

function generateAgentImage(agentName, prompt, variantIdx, buttonEl) {
    if (buttonEl) {
        buttonEl.disabled = true;
        buttonEl.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
    }

    fetch('/generate_agent_image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            agent_name: agentName,
            prompt: prompt,
            variant_idx: variantIdx
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Generation error: ' + data.error);
            if (buttonEl) {
                buttonEl.disabled = false;
                buttonEl.innerHTML = 'Retry Generation';
            }
        } else {
            renderAgentWorkspace(data.agent_steps);
            loadAssets();
        }
    })
    .catch(error => {
        console.error('Error generating image:', error);
        alert('Image generation failed.');
        if (buttonEl) {
            buttonEl.disabled = false;
            buttonEl.innerHTML = 'Retry Generation';
        }
    });
}

function loadAssets() {
    fetch('/assets')
    .then(response => response.json())
    .then(data => {
        // Render Generated Campaign Assets
        const library = document.getElementById('assetLibrary');
        if (library) {
            library.innerHTML = '';
            if (data.assets && data.assets.length > 0) {
                data.assets.forEach(asset => {
                    library.innerHTML += `
                        <div class="col-md-6">
                            <div class="glass-panel asset-card animate-fade-in">
                                <div class="asset-img-container">
                                    <img src="${asset.url}" alt="${asset.name}" class="asset-img" onerror="this.src='https://placehold.co/400?text=No+Image';">
                                    <div class="asset-overlay">
                                        <span class="asset-tag">ID: ${asset.id}</span>
                                        <h5 class="asset-title mt-2 text-white font-family-outfit">${asset.name}</h5>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
            } else {
                library.innerHTML = `<div class="text-secondary fs-7 italic p-3">No campaign assets generated yet.</div>`;
            }
        }
        
        // Render Uploaded Products Gallery
        const uploadsContainer = document.getElementById('uploadedProductsContainer');
        const noUploadsText = document.getElementById('noUploadsText');
        if (uploadsContainer) {
            if (data.uploads && data.uploads.length > 0) {
                if (noUploadsText) noUploadsText.style.display = 'none';
                uploadsContainer.innerHTML = '';
                data.uploads.forEach(img => {
                    const isSelected = selectedProductImageUrl === img.url ? 'selected' : '';
                    uploadsContainer.innerHTML += `
                        <img src="${img.url}" alt="${img.name}" 
                             class="uploaded-product-thumbnail ${isSelected}"
                             title="Click to select ${img.name}"
                             onclick="selectUploadedProduct({name: '${img.name}', url: '${img.url}'})">
                    `;
                });
            } else {
                if (noUploadsText) noUploadsText.style.display = 'block';
                uploadsContainer.innerHTML = '';
                if (noUploadsText) uploadsContainer.appendChild(noUploadsText);
            }
        }
    });
}

function fetchSessionState() {
    fetch('/session_state')
    .then(response => response.json())
    .then(data => {
        if (data.uploaded_images && data.uploaded_images.length > 0) {
            // Select the last uploaded image by default
            const lastImg = data.uploaded_images[data.uploaded_images.length - 1];
            selectUploadedProduct(lastImg);
        }
        if (data.agent_steps && Object.keys(data.agent_steps).length > 0) {
            renderAgentWorkspace(data.agent_steps);
        }
    });
}

// Initial load
loadAssets();
fetchSessionState();
