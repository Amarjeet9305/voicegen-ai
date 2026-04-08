// Elements
const micTrigger = document.getElementById('mic-trigger');
const talkPill = document.getElementById('talk-pill');
const statusText = document.getElementById('ai-status');
const transcriptDisplay = document.getElementById('transcript-display');
const responseDisplay = document.getElementById('response-display');
const chatHistory = document.getElementById('chat-history');
const themeToggle = document.getElementById('theme-toggle');
const appBody = document.body;
const textInput = document.getElementById('text-input');
const sendBtn = document.getElementById('send-btn');

// Speech Recognition Init
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;
let isListening = false;
let finalTranscript = '';
let restartTimer = null;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = true;          // Keep listening until manually stopped
    recognition.interimResults = true;      // Show words as they're being spoken
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 3;        // Consider multiple interpretations

    recognition.onstart = () => {
        isListening = true;
        finalTranscript = '';
        appBody.classList.add('listening-mode');
        appBody.classList.add('active-voice');
        updateStatus("Listening...");
        transcriptDisplay.innerText = "🎙️ Speak now...";
        responseDisplay.innerText = "";
    };

    recognition.onresult = (event) => {
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
            } else {
                interimTranscript += transcript;
            }
        }

        // Show real-time feedback — interim in lighter color, final in bold
        if (finalTranscript || interimTranscript) {
            transcriptDisplay.innerHTML =
                `<span class="final-text">${finalTranscript}</span>` +
                `<span class="interim-text">${interimTranscript}</span>`;
        }
    };

    recognition.onend = () => {
        appBody.classList.remove('listening-mode');
        appBody.classList.remove('active-voice');

        // Process the final transcript if we have one
        const trimmed = finalTranscript.trim();
        if (trimmed) {
            addToHistory("You", trimmed);
            processIntent(trimmed);
        } else if (isListening) {
            // Recognition ended unexpectedly with no result — auto-restart
            updateStatus("Didn't catch that — retrying...");
            restartTimer = setTimeout(() => {
                try { recognition.start(); } catch (e) { /* already started */ }
            }, 300);
        }

        if (!isListening) {
            updateStatus("Standby");
        }
    };

    recognition.onerror = (event) => {
        console.error("Speech Recognition Error:", event.error);

        if (event.error === 'no-speech') {
            updateStatus("No speech detected — try again");
            // Auto-restart after no-speech
            if (isListening) {
                restartTimer = setTimeout(() => {
                    try { recognition.start(); } catch (e) {}
                }, 500);
            }
        } else if (event.error === 'audio-capture') {
            updateStatus("⚠️ No microphone found");
            stopListening();
        } else if (event.error === 'not-allowed') {
            updateStatus("⚠️ Microphone access denied");
            stopListening();
        } else if (event.error === 'network') {
            updateStatus("⚠️ Network error — check connection");
            stopListening();
        } else if (event.error === 'aborted') {
            // User stopped — do nothing
        } else {
            updateStatus("Error — try again");
            stopListening();
        }
    };

    // Handle audio start to confirm mic is working
    recognition.onaudiostart = () => {
        updateStatus("🎙️ Listening...");
    };

} else {
    // Browser doesn't support speech recognition
    if (micTrigger) micTrigger.style.display = 'none';
    if (talkPill) talkPill.innerHTML = '<span class="icon">⌨️</span> Type Instead';
    updateStatus("Voice not supported — use text input");
}

// Event Listeners
micTrigger.addEventListener('click', toggleMic);
talkPill.addEventListener('click', toggleMic);
themeToggle.addEventListener('click', toggleTheme);

// Text input: send on Enter
if (textInput) {
    textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && textInput.value.trim()) {
            sendTextInput();
        }
    });
}
if (sendBtn) {
    sendBtn.addEventListener('click', sendTextInput);
}

function sendTextInput() {
    const text = textInput.value.trim();
    if (!text) return;
    transcriptDisplay.innerText = `"${text}"`;
    addToHistory("You", text);
    processIntent(text);
    textInput.value = '';
}

function toggleMic() {
    if (!recognition) {
        updateStatus("Voice not supported — use text input below");
        return;
    }

    if (isListening) {
        stopListening();
    } else {
        startListening();
    }
}

function startListening() {
    // Stop any text-to-speech that's playing
    window.speechSynthesis.cancel();
    clearTimeout(restartTimer);
    finalTranscript = '';
    isListening = true;

    try {
        recognition.start();
    } catch (e) {
        // Already started
        recognition.stop();
        setTimeout(() => {
            try { recognition.start(); } catch (err) {}
        }, 200);
    }
}

function stopListening() {
    isListening = false;
    clearTimeout(restartTimer);
    try {
        recognition.stop();
    } catch (e) {}
    appBody.classList.remove('listening-mode');
    appBody.classList.remove('active-voice');
    updateStatus("Standby");
}

function updateStatus(text) {
    statusText.innerText = text;
}

function addToHistory(role, text) {
    const p = document.createElement('p');
    p.innerHTML = `<strong>${role}:</strong> ${text}`;
    p.style.opacity = "0";
    chatHistory.appendChild(p);
    setTimeout(() => p.style.opacity = "1", 100);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function processIntent(text) {
    updateStatus("Processing...");
    try {
        const response = await fetch('/process_intent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        
        const data = await response.json();
        updateStatus("Speaking...");
        displayResponse(data);
        speak(data.message);
        addToHistory("AI", data.message);
        
        if (data.action) {
            handleAction(data.action);
        }
    } catch (error) {
        console.error('Error:', error);
        updateStatus("System Offline");
        responseDisplay.innerText = "Connection error — please try again.";
    }
}

function displayResponse(data) {
    responseDisplay.innerText = data.message;
}

function handleAction(action) {
    setTimeout(() => {
        if (action.type === 'open') {
            window.open(action.url, '_blank');
        } else if (action.type === 'search') {
            window.open(`https://www.google.com/search?q=${encodeURIComponent(action.query)}`, '_blank');
        }
    }, 2000);
}

function speak(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1;
    
    // Try to pick a better voice
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v =>
        v.name.includes('Google') || v.name.includes('Microsoft') || v.name.includes('Samantha')
    );
    if (preferred) utterance.voice = preferred;

    utterance.onstart = () => {
        appBody.classList.add('active-voice');
        if (!isListening) updateStatus("Speaking...");
    };
    
    utterance.onend = () => {
        appBody.classList.remove('active-voice');
        if (!isListening) updateStatus("Standby");
    };

    window.speechSynthesis.speak(utterance);
}

// Pre-load voices (some browsers need this)
window.speechSynthesis.onvoiceschanged = () => {
    window.speechSynthesis.getVoices();
};

function toggleTheme() {
    appBody.classList.toggle('dark-theme');
    appBody.classList.toggle('light-theme');
    const isLight = appBody.classList.contains('light-theme');
    document.querySelector('.sun').style.display = isLight ? 'none' : 'block';
    document.querySelector('.moon').style.display = isLight ? 'block' : 'none';
}

// Particle.js Configuration
if (window.particlesJS) {
    particlesJS('particles-js', {
        "particles": {
            "number": { "value": 80, "density": { "enable": true, "value_area": 800 } },
            "color": { "value": "#ffffff" },
            "shape": { "type": "circle" },
            "opacity": { "value": 0.2, "random": false },
            "size": { "value": 2, "random": true },
            "line_linked": { "enable": true, "distance": 150, "color": "#ffffff", "opacity": 0.1, "width": 1 },
            "move": { "enable": true, "speed": 1.5, "direction": "none", "random": false, "straight": false, "out_mode": "out", "bounce": false }
        },
        "interactivity": {
            "detect_on": "canvas",
            "events": { "onhover": { "enable": true, "mode": "grab" }, "onclick": { "enable": true, "mode": "push" }, "resize": true }
        },
        "retina_detect": true
    });
}
