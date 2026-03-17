// Elements
const micTrigger = document.getElementById('mic-trigger');
const talkPill = document.getElementById('talk-pill');
const statusText = document.getElementById('ai-status');
const transcriptDisplay = document.getElementById('transcript-display');
const responseDisplay = document.getElementById('response-display');
const chatHistory = document.getElementById('chat-history');
const themeToggle = document.getElementById('theme-toggle');
const appBody = document.body;
const waveform = document.getElementById('waveform').parentElement; // orb container for context class

// Speech Recognition Init
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    recognition.onstart = () => {
        appBody.classList.add('listening-mode');
        appBody.classList.add('active-voice');
        updateStatus("Listening...");
        transcriptDisplay.innerText = "";
        responseDisplay.innerText = "";
        speak("Awaiting your command.");
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        transcriptDisplay.innerText = `"${transcript}"`;
        addToHistory("User", transcript);
        processIntent(transcript);
    };

    recognition.onend = () => {
        appBody.classList.remove('listening-mode');
        appBody.classList.remove('active-voice');
        if (statusText.innerText === "Listening...") {
            updateStatus("Standby");
        }
    };

    recognition.onerror = (event) => {
        updateStatus("Error");
        console.error("Speech Recognition Error:", event.error);
    };
}

// Event Listeners
micTrigger.addEventListener('click', toggleMic);
talkPill.addEventListener('click', toggleMic);
themeToggle.addEventListener('click', toggleTheme);

function toggleMic() {
    if (appBody.classList.contains('listening-mode')) {
        recognition.stop();
    } else {
        recognition.start();
    }
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
        addToHistory("Jarvis", data.message);
        
        if (data.action) {
            handleAction(data.action);
        }
    } catch (error) {
        console.error('Error:', error);
        updateStatus("System Offline");
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
    utterance.rate = 1.1;
    utterance.pitch = 1;
    
    utterance.onstart = () => {
        appBody.classList.add('active-voice');
        if (statusText.innerText !== "Listening...") updateStatus("Speaking...");
    };
    
    utterance.onend = () => {
        appBody.classList.remove('active-voice');
        updateStatus("Standby");
    };

    window.speechSynthesis.speak(utterance);
}

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
