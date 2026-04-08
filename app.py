from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import datetime
import string
import os
import random
import re
import json

# Optional: Google Gemini AI for smart responses
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# Configure Gemini if API key is available
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
gemini_model = None

if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        print("✅ Gemini AI connected successfully!")
    except Exception as e:
        print(f"⚠️ Gemini setup failed: {e}")
        gemini_model = None
else:
    if not GEMINI_AVAILABLE:
        print("ℹ️ google-generativeai not installed. Using built-in responses.")
    elif not GEMINI_API_KEY:
        print("ℹ️ No GEMINI_API_KEY set. Using built-in responses.")

# ─── Conversation memory (per-session, simple) ───
conversation_history = []

# ─── Intent patterns with synonyms and fuzzy matching ───
INTENT_PATTERNS = {
    "greeting": {
        "keywords": ["hello", "hi", "hey", "greetings", "howdy", "sup", "yo", "hola", "good morning", "good evening", "good afternoon", "good night", "what's up", "whats up"],
        "responses": [
            "Hello! Great to hear from you. What can I help you with?",
            "Hey there! I'm ready to assist. What's on your mind?",
            "Hi! Welcome back. How can I help you today?",
            "Greetings! I'm all ears. What would you like to do?",
        ]
    },
    "farewell": {
        "keywords": ["bye", "goodbye", "see you", "later", "farewell", "quit", "exit", "goodnight", "take care", "peace out"],
        "responses": [
            "Goodbye! It was great chatting with you. Come back anytime!",
            "See you later! Have an amazing day ahead!",
            "Take care! I'll be here whenever you need me.",
            "Farewell! Wishing you all the best!",
        ]
    },
    "thanks": {
        "keywords": ["thank", "thanks", "thank you", "appreciate", "grateful", "thx", "cheers"],
        "responses": [
            "You're welcome! Happy to help anytime.",
            "No problem at all! That's what I'm here for.",
            "Glad I could assist! Anything else you need?",
            "My pleasure! Don't hesitate to ask more.",
        ]
    },
    "how_are_you": {
        "keywords": ["how are you", "how do you do", "how's it going", "how you doing", "hows it going", "what's good", "you okay", "how r u"],
        "responses": [
            "I'm doing great, thanks for asking! I'm ready to help with whatever you need.",
            "I'm running at peak performance! What can I do for you today?",
            "I'm fantastic! My circuits are buzzing with excitement to help you.",
            "All systems operational and feeling great! How about you?",
        ]
    },
    "name": {
        "keywords": ["your name", "who are you", "what are you", "what's your name", "whats your name", "introduce yourself", "tell me about yourself"],
        "responses": [
            "I'm your AI Voice Assistant! I can help you with information, open websites, search the web, tell jokes, and much more. Just ask!",
            "I'm an AI-powered voice assistant. Think of me as your digital companion, ready to help with questions, tasks, and conversation!",
        ]
    },
    "time": {
        "keywords": ["time", "clock", "what time", "current time"],
        "handler": "handle_time"
    },
    "date": {
        "keywords": ["date", "today", "what day", "current date", "day is it", "month", "year"],
        "handler": "handle_date"
    },
    "weather": {
        "keywords": ["weather", "temperature", "forecast", "rain", "sunny", "cloudy", "hot", "cold outside"],
        "responses": [
            "Based on general conditions, it looks like a pleasant day! For accurate weather, I'd recommend checking a weather service for your specific location.",
            "I don't have live weather data right now, but you can say 'search weather in [your city]' and I'll look it up for you on Google!",
        ]
    },
    "search": {
        "keywords": ["search", "google", "look up", "find", "search for", "look for", "google search"],
        "handler": "handle_search"
    },
    "open_website": {
        "keywords": ["open", "go to", "navigate to", "visit", "launch", "browse"],
        "handler": "handle_open"
    },
    "play_music": {
        "keywords": ["play", "music", "song", "listen", "spotify", "youtube music", "audio", "tune", "playlist"],
        "handler": "handle_music"
    },
    "joke": {
        "keywords": ["joke", "funny", "laugh", "humor", "make me laugh", "tell me a joke", "something funny"],
        "responses": [
            "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
            "Why did the AI go to therapy? It had too many deep issues in its neural network! 🧠",
            "What's a computer's favorite snack? Microchips! 🍟",
            "Why was the JavaScript developer sad? Because he didn't Node how to Express himself! 😄",
            "How do robots eat guacamole? With micro-chips! 🤖",
            "Why did the programmer quit his job? Because he didn't get arrays! 💰",
            "What do you call a fake noodle? An impasta! 🍝",
            "Why don't scientists trust atoms? Because they make up everything! ⚛️",
        ]
    },
    "motivation": {
        "keywords": ["motivat", "inspir", "encourage", "uplift", "positive", "feeling down", "depressed", "sad", "cheer me up", "feel better", "stressed"],
        "responses": [
            "Remember: Every expert was once a beginner. Your journey matters more than the destination. Keep pushing forward! 💪",
            "You're capable of amazing things. Don't let doubt dim your light. The world needs what you have to offer! 🌟",
            "Difficult roads often lead to beautiful destinations. Trust the process, and trust yourself! 🚀",
            "Success is not final, failure is not fatal. It's the courage to continue that counts. You've got this! 🔥",
            "The only way to do great work is to love what you do. Stay passionate, stay curious! ✨",
        ]
    },
    "fact": {
        "keywords": ["fact", "trivia", "did you know", "interesting", "tell me something", "random fact", "fun fact"],
        "responses": [
            "Did you know? Honey never spoils. Archaeologists have found 3000-year-old honey in Egyptian tombs that's still perfectly edible! 🍯",
            "Fun fact: Octopuses have three hearts, blue blood, and nine brains! Talk about over-engineering! 🐙",
            "Here's one: The shortest war in history lasted 38-45 minutes — between Britain and Zanzibar in 1896! ⚔️",
            "Did you know? A day on Venus is longer than a year on Venus. It takes longer to rotate on its axis than to orbit the Sun! 🪐",
            "Fun fact: Bananas are berries, but strawberries aren't! Botany is wild. 🍌",
            "Did you know? The inventor of the Pringles can is buried in one. Now that's brand loyalty! 🥔",
        ]
    },
    "help": {
        "keywords": ["help", "what can you do", "capabilities", "features", "commands", "how to use", "guide", "instructions"],
        "responses": [
            "Here's what I can do:\n🎤 **Voice Commands** — Just speak naturally!\n🔍 **Search** — Say 'search [topic]'\n🌐 **Open Websites** — Say 'open YouTube'\n🎵 **Play Music** — Say 'play [song name]'\n⏰ **Time & Date** — Ask 'what time is it?'\n😂 **Jokes** — Say 'tell me a joke'\n💡 **Facts** — Say 'tell me a fact'\n💪 **Motivation** — Say 'motivate me'\n🧮 **Math** — Say 'calculate 5 + 3'\n📖 **Definitions** — Say 'define AI'\n\nOr simply ask me anything and I'll do my best to help!",
        ]
    },
    "math": {
        "keywords": ["calculate", "math", "plus", "minus", "times", "divided", "multiply", "add", "subtract", "sum", "product", "percentage", "percent"],
        "handler": "handle_math"
    },
    "define": {
        "keywords": ["define", "definition", "meaning", "what is", "what are", "what does", "explain", "describe"],
        "handler": "handle_definition"
    },
    "news": {
        "keywords": ["news", "headlines", "latest news", "breaking news", "whats happening", "current events"],
        "handler": "handle_news"
    },
    "translate": {
        "keywords": ["translate", "translation", "how do you say", "in spanish", "in french", "in hindi", "in german", "in japanese", "in chinese"],
        "handler": "handle_translate"
    },
    "alarm": {
        "keywords": ["alarm", "reminder", "timer", "remind me", "set alarm", "wake me", "notify"],
        "responses": [
            "I've noted your reminder! Unfortunately, I can't set persistent alarms yet, but I recommend using your phone's alarm app for reliable notifications.",
            "Got it! For timed reminders, your device's built-in alarm or Google Assistant works best. Is there anything else I can help with?",
        ]
    },
    "compliment": {
        "keywords": ["you're awesome", "you're great", "good job", "well done", "nice", "amazing", "brilliant", "smart", "love you", "you're the best", "cool"],
        "responses": [
            "Aww, thank you! That means a lot coming from you! 😊",
            "You're making my circuits blush! Thanks for the kind words! 💜",
            "That's so sweet! You're pretty awesome yourself! ✨",
            "Thanks! I do try my best. You make it easy to help! 🌟",
        ]
    },
    "creator": {
        "keywords": ["who made you", "who created you", "who built you", "developer", "who is your creator", "who designed you"],
        "responses": [
            "I was created as an AI Voice Assistant project! I'm built with Flask, JavaScript, and powered by the Web Speech API for voice recognition. Pretty cool, right?",
            "I'm a product of creative development — built with Python Flask for the backend and modern web technologies for this beautiful interface you see!",
        ]
    },
}

# ─── Common definitions database ───
DEFINITIONS = {
    "ai": "Artificial Intelligence (AI) is the simulation of human intelligence by machines, enabling them to learn, reason, and make decisions.",
    "artificial intelligence": "Artificial Intelligence (AI) is the simulation of human intelligence by machines, enabling them to learn, reason, and make decisions.",
    "machine learning": "Machine Learning is a subset of AI where systems learn and improve from experience without being explicitly programmed.",
    "python": "Python is a high-level, versatile programming language known for its simplicity and readability, widely used in web development, data science, and AI.",
    "javascript": "JavaScript is a programming language that enables interactive web pages and is an essential part of web applications.",
    "html": "HTML (HyperText Markup Language) is the standard markup language for creating web pages and web applications.",
    "css": "CSS (Cascading Style Sheets) is a style sheet language for describing the presentation of a document written in HTML.",
    "blockchain": "Blockchain is a decentralized, distributed ledger technology that records transactions across a network of computers securely.",
    "cloud computing": "Cloud computing delivers computing services like servers, storage, databases, and software over the internet.",
    "api": "An API (Application Programming Interface) is a set of rules that allows different software applications to communicate with each other.",
    "algorithm": "An algorithm is a step-by-step procedure or formula for solving a problem or accomplishing a task.",
    "database": "A database is an organized collection of structured information stored electronically in a computer system.",
    "internet": "The Internet is a global network of interconnected computers that communicate through standardized protocols.",
    "cybersecurity": "Cybersecurity is the practice of protecting systems, networks, and programs from digital attacks.",
    "data science": "Data Science is an interdisciplinary field that uses scientific methods, algorithms, and systems to extract knowledge from data.",
    "deep learning": "Deep Learning is a subset of machine learning using neural networks with many layers to analyze complex patterns in data.",
    "robot": "A robot is a machine designed to automatically carry out complex tasks, especially ones that are programmed by a computer.",
    "neural network": "A Neural Network is a computing system inspired by biological neural networks that can learn to perform tasks by considering examples.",
    "programming": "Programming is the process of creating a set of instructions that tell a computer how to perform a task.",
    "software": "Software is a set of instructions and data that tell computer hardware how to work.",
}

# ─── Handler functions ───
def handle_time(raw_text, tokens):
    now = datetime.datetime.now()
    formatted_time = now.strftime("%I:%M %p")
    return {
        "intent": "time",
        "message": f"The current time is {formatted_time}. Is there anything else you'd like to know?",
        "action": None
    }

def handle_date(raw_text, tokens):
    today = datetime.date.today()
    day_name = today.strftime("%A")
    formatted_date = today.strftime("%B %d, %Y")
    return {
        "intent": "date",
        "message": f"Today is {day_name}, {formatted_date}. Anything else I can help with?",
        "action": None
    }

def handle_search(raw_text, tokens):
    # Extract search query by removing trigger words
    query = raw_text
    for word in ["search", "search for", "google", "look up", "find", "look for"]:
        query = query.replace(word, "")
    query = query.strip()
    if not query:
        return {
            "intent": "search",
            "message": "What would you like me to search for?",
            "action": None
        }
    return {
        "intent": "search",
        "message": f"Searching for '{query}' on Google. Opening results now!",
        "action": {"type": "search", "query": query}
    }

def handle_open(raw_text, tokens):
    website = raw_text
    for word in ["open", "go to", "navigate to", "visit", "launch", "browse", "please", "can you", "could you"]:
        website = website.replace(word, "")
    website = website.strip().rstrip('.')

    # Smart URL detection
    known_sites = {
        "youtube": "youtube.com",
        "google": "google.com",
        "github": "github.com",
        "twitter": "twitter.com",
        "x": "x.com",
        "facebook": "facebook.com",
        "instagram": "instagram.com",
        "linkedin": "linkedin.com",
        "reddit": "reddit.com",
        "netflix": "netflix.com",
        "amazon": "amazon.com",
        "spotify": "spotify.com",
        "whatsapp": "web.whatsapp.com",
        "gmail": "mail.google.com",
        "wikipedia": "wikipedia.org",
        "stack overflow": "stackoverflow.com",
        "stackoverflow": "stackoverflow.com",
        "chatgpt": "chat.openai.com",
    }

    site_key = website.lower().strip()
    if site_key in known_sites:
        url = f"https://www.{known_sites[site_key]}"
    elif '.' in website:
        url = f"https://{website}" if not website.startswith('http') else website
    else:
        url = f"https://www.{website}.com"

    if not website:
        return {
            "intent": "open_website",
            "message": "Which website would you like me to open?",
            "action": None
        }

    return {
        "intent": "open_website",
        "message": f"Opening {website} for you right now!",
        "action": {"type": "open", "url": url}
    }

def handle_music(raw_text, tokens):
    query = raw_text
    for word in ["play", "music", "song", "listen to", "listen", "on youtube", "on spotify", "please"]:
        query = query.replace(word, "")
    query = query.strip()
    if not query:
        query = "popular music mix"

    return {
        "intent": "play_music",
        "message": f"Playing '{query}' on YouTube. Enjoy the music! 🎶",
        "action": {"type": "open", "url": f"https://www.youtube.com/results?search_query={query}+music"}
    }

def handle_math(raw_text, tokens):
    # Extract math expression
    expr = raw_text
    for word in ["calculate", "what is", "what's", "compute", "solve", "math"]:
        expr = expr.replace(word, "", 1)
    expr = expr.strip().rstrip('?')

    # Convert words to operators
    expr = expr.replace("plus", "+").replace("minus", "-").replace("times", "*")
    expr = expr.replace("multiplied by", "*").replace("divided by", "/")
    expr = expr.replace("x", "*").replace("÷", "/")
    expr = expr.replace("percent of", "/100*")
    expr = expr.replace("percentage of", "/100*")

    # Clean to only math characters
    clean_expr = re.sub(r'[^0-9+\-*/().% ]', '', expr).strip()

    if not clean_expr:
        return {
            "intent": "math",
            "message": "I'd love to help with math! Try saying something like 'calculate 15 plus 27' or 'what is 100 divided by 4'.",
            "action": None
        }

    try:
        # Safe eval for math only
        result = eval(clean_expr, {"__builtins__": {}}, {})
        # Format result nicely
        if isinstance(result, float):
            result = round(result, 4)
            if result == int(result):
                result = int(result)
        return {
            "intent": "math",
            "message": f"The answer is **{result}**! 🧮 Need help with more calculations?",
            "action": None
        }
    except Exception:
        return {
            "intent": "math",
            "message": f"I couldn't calculate that expression. Try something like 'calculate 5 plus 3' or 'what is 10 times 20'.",
            "action": None
        }

def handle_definition(raw_text, tokens):
    query = raw_text
    for word in ["define", "definition of", "meaning of", "what is a", "what is an", "what is the", "what is", "what are", "what does", "explain", "describe", "tell me about"]:
        query = query.replace(word, "", 1)
    query = query.strip().rstrip('?').strip()

    if not query:
        return {
            "intent": "define",
            "message": "What would you like me to define? Try asking 'what is AI?' or 'define machine learning'.",
            "action": None
        }

    # Check our definitions database
    lookup = query.lower().strip()
    if lookup in DEFINITIONS:
        return {
            "intent": "define",
            "message": f"**{query.title()}**: {DEFINITIONS[lookup]}",
            "action": None
        }

    # If not in our database, suggest searching
    return {
        "intent": "define",
        "message": f"Great question about '{query}'! Let me search that for you on Google for the most accurate information.",
        "action": {"type": "search", "query": f"what is {query}"}
    }

def handle_news(raw_text, tokens):
    return {
        "intent": "news",
        "message": "Let me pull up the latest news for you on Google News!",
        "action": {"type": "open", "url": "https://news.google.com"}
    }

def handle_translate(raw_text, tokens):
    query = raw_text
    return {
        "intent": "translate",
        "message": f"Let me open Google Translate to help you with that!",
        "action": {"type": "open", "url": f"https://translate.google.com/?sl=auto&tl=en&text={query}"}
    }

# ─── Smart intent matcher ───
STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
    'your', 'yours', 'yourself', 'he', 'him', 'his', 'she', 'her', 'it',
    'its', 'they', 'them', 'their', 'a', 'an', 'the', 'and', 'but', 'if',
    'or', 'because', 'as', 'at', 'by', 'for', 'with', 'about', 'to',
    'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
    'again', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'all', 'each', 'some', 'no', 'not', 'only', 'own', 'same', 'so',
    'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now',
    'do', 'does', 'did', 'doing', 'am', 'is', 'are', 'was', 'were',
    'be', 'been', 'being', 'have', 'has', 'had', 'having', 'please',
    'could', 'would', 'shall', 'may', 'might', 'must',
}

def preprocess_text(text):
    text = text.lower().strip()
    translator = str.maketrans('', '', string.punctuation.replace('+', '').replace('-', '').replace('*', '').replace('/', ''))
    cleaned = text.translate(translator)
    tokens = cleaned.split()
    filtered = [w for w in tokens if w not in STOP_WORDS]
    return filtered

def match_intent(raw_text, tokens):
    """Match user input against intent patterns using phrase and keyword matching."""
    text_lower = raw_text.lower()
    best_match = None
    best_score = 0

    for intent_name, intent_data in INTENT_PATTERNS.items():
        score = 0
        for keyword in intent_data["keywords"]:
            # Phrase match (higher priority)
            if keyword in text_lower:
                # Longer phrases get more weight
                score += len(keyword.split()) * 2
            # Token match
            elif keyword in tokens:
                score += 1

        if score > best_score:
            best_score = score
            best_match = intent_name

    return best_match if best_score > 0 else None

# ─── Gemini AI fallback ───
def ask_gemini(user_message):
    """Use Google Gemini for intelligent fallback responses."""
    if not gemini_model:
        return None

    try:
        prompt = f"""You are a friendly, helpful AI voice assistant. Keep your responses concise (2-3 sentences max) and conversational, as they will be spoken aloud. Be warm, engaging, and informative. Don't use markdown formatting like ** or ## since this is for voice output.

User said: "{user_message}"

Respond naturally:"""

        response = gemini_model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"Gemini error: {e}")

    return None

# ─── Built-in smart fallback responses ───
SMART_FALLBACKS = [
    "That's an interesting question! While I'm still learning, I can help you search for more information. Just say 'search' followed by your topic!",
    "I'd love to help with that! Try rephrasing your request, or say 'help' to see all the things I can do.",
    "Great question! I don't have that specific information right now, but I can search the web for you. Want me to look it up?",
    "I'm getting smarter every day! For now, try asking me about the time, weather, math, jokes, or say 'help' for a full list of my abilities.",
    "Hmm, I want to give you the best answer possible. Let me search that for you — just say 'search' followed by what you want to know!",
]

# ─── Handlers map ───
HANDLERS = {
    "handle_time": handle_time,
    "handle_date": handle_date,
    "handle_search": handle_search,
    "handle_open": handle_open,
    "handle_music": handle_music,
    "handle_math": handle_math,
    "handle_definition": handle_definition,
    "handle_news": handle_news,
    "handle_translate": handle_translate,
}

# ─── Routes ───
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_intent', methods=['POST'])
def process_intent():
    data = request.json
    raw_text = data.get('text', '').strip()

    if not raw_text:
        return jsonify({
            "intent": "empty",
            "message": "I didn't hear anything. Could you try speaking again or type your question below?",
            "action": None
        })

    tokens = preprocess_text(raw_text)
    raw_lower = raw_text.lower()

    # Step 1: Match against known intents
    matched_intent = match_intent(raw_lower, tokens)

    if matched_intent:
        intent_data = INTENT_PATTERNS[matched_intent]

        # If intent has a custom handler
        if "handler" in intent_data:
            handler_fn = HANDLERS.get(intent_data["handler"])
            if handler_fn:
                result = handler_fn(raw_lower, tokens)
                conversation_history.append({"user": raw_text, "ai": result["message"]})
                return jsonify(result)

        # Standard response
        message = random.choice(intent_data["responses"])
        conversation_history.append({"user": raw_text, "ai": message})
        return jsonify({
            "intent": matched_intent,
            "message": message,
            "action": None
        })

    # Step 2: Try Gemini AI for intelligent response
    gemini_response = ask_gemini(raw_text)
    if gemini_response:
        conversation_history.append({"user": raw_text, "ai": gemini_response})
        return jsonify({
            "intent": "ai_response",
            "message": gemini_response,
            "action": None
        })

    # Step 3: Smart fallback with suggestion
    fallback_msg = random.choice(SMART_FALLBACKS)
    conversation_history.append({"user": raw_text, "ai": fallback_msg})
    return jsonify({
        "intent": "general",
        "message": fallback_msg,
        "action": None
    })

@app.route('/chat_history', methods=['GET'])
def get_chat_history():
    return jsonify(conversation_history[-20:])  # Last 20 messages

if __name__ == '__main__':
    app.run(debug=True)
