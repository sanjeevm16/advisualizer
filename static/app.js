document.getElementById('sendBtn').addEventListener('click', sendMessage);
document.getElementById('userInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendMessage();
});

let ttsEnabled = true;
let recognition = null;
let isRecording = false;

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

function updateWorkflowTracker(stepName) {
    const steps = {
        'trend': document.getElementById('step-trend'),
        'product': document.getElementById('step-product'),
        'scene': document.getElementById('step-scene'),
        'ab': document.getElementById('step-ab')
    };

    // Remove active class from all
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
        delay += 1200; // Increment step animation every 1.2s
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

    // Append User Message
    appendMessage('You', message, 'user');
    userInput.value = '';
    
    // Reset tracker and start step animation
    updateWorkflowTracker(null);
    simulateWorkflowProgress();

    // Call Backend API
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        // Stop dynamic tracker simulation and keep all/last active or based on response
        // We will activate Variant Gen step as it's the final stage
        setTimeout(() => {
            updateWorkflowTracker('ab');
        }, 500);

        // Append AI Response
        appendMessage('Agent', data.response, 'agent');
        
        // Voice Synthesis (optional)
        if (ttsEnabled) {
            speak(data.response);
        }
        
        // Refresh Assets
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
        // Cancel current utterance before speaking next
        window.speechSynthesis.cancel();
        
        // Strip markdown/html from text for cleaner voice synthesis
        const cleanText = text.replace(/[*#`_\-]/g, '').trim();
        if (!cleanText) return;
        
        const utterance = new SpeechSynthesisUtterance(cleanText);
        window.speechSynthesis.speak(utterance);
    }
}

function loadAssets() {
    fetch('/assets')
    .then(response => response.json())
    .then(data => {
        const library = document.getElementById('assetLibrary');
        if (!library) return;
        library.innerHTML = '';
        
        data.assets.forEach(asset => {
            library.innerHTML += `
                <div class="col-md-6">
                    <div class="glass-panel asset-card">
                        <div class="asset-img-container">
                            <img src="${asset.url}" alt="${asset.name}" class="asset-img" onerror="this.src='https://placehold.co/400?text=No+Image';">
                            <div class="asset-overlay">
                                <span class="asset-tag">ID: ${asset.id}</span>
                                <h5 class="asset-title mt-2 text-white">${asset.name}</h5>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
    });
}

// Initial load
loadAssets();
