# Aura AI - Voice Assistant NLP Project

An intelligent, voice-controlled assistant built with Flask, NLTK, and the Web Speech API. This project features a modern, responsive interface inspired by Gemini Live, capable of recognizing user intents and performing automated tasks.

## 🚀 Features

- **Gemini-Style UI**: Modern, light-themed, minimalist design with pill buttons and responsive layout.
- **Voice Recognition**: Real-time speech-to-text conversion using the Web Speech API.
- **Speech Synthesis**: Audible responses from the assistant using the SpeechSynthesis API.
- **NLP Preprocessing**: Robust intent recognition powered by NLTK (Tokenization, Stop-word removal).
- **Supported Scenarios**:
    - 🌤️ **Weather**: Get daily weather updates.
    - 🎵 **Music**: Play songs or search for music on YouTube.
    - ⏰ **Alarms/Reminders**: Schedule reminders verbally.
    - 🔍 **Search**: Perform Google searches via voice commands.
    - 📅 **Time/Date**: Query current system time and date.

## 🛠️ Tech Stack

- **Backend**: Python, Flask, NLTK
- **Frontend**: HTML5, CSS3 (Custom Cream Theme), JavaScript (Vanilla)
- **APIs**: Web Speech API, SpeechSynthesis API

## 📋 Prerequisites

- Python 3.8+
- Internet connection (for Speech APIs and NLTK data download)

## ⚙️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Amarjeet9305/voicegen-ai.git
   cd voicegen-ai
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the Assistant**:
   Open your browser and navigate to `http://127.0.0.1:5000`.

## 📖 How to Use

- Click the large centered **"Talk"** button or the **Mic icon** in the bottom bar.
- The assistant will ask "How may I help you today?"
- Speak your command (e.g., "Open YouTube", "What is the weather today?", "Play Lo-fi music").
- The assistant will recognize your intent, respond verbally, and execute the corresponding action.

---
Built with ❤️ by Amarjeet
