from flask import Flask, render_template, request, jsonify
import datetime
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string

# Download NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

app = Flask(__name__)

STOP_WORDS = set(stopwords.words('english'))

def preprocess_text(text):
    """Tokenize and remove stop words / punctuation."""
    tokens = word_tokenize(text.lower())
    filtered_tokens = [w for w in tokens if w not in STOP_WORDS and w not in string.punctuation]
    return filtered_tokens

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_intent', methods=['POST'])
def process_intent():
    data = request.json
    raw_text = data.get('text', '').lower()
    tokens = preprocess_text(raw_text)
    
    response = {
        "intent": "unknown",
        "message": "I'm sorry, I didn't quite catch that. Could you repeat?",
        "action": None
    }

    # Greeting
    if any(word in tokens for word in ['hello', 'hi', 'hey', 'greetings']):
        response["intent"] = "greeting"
        response["message"] = "Hello! How can I assist you today?"
        
    # Time / Date
    elif 'time' in raw_text:
        now = datetime.datetime.now().strftime("%H:%M")
        response["intent"] = "time"
        response["message"] = f"The current time is {now}."
    elif 'date' in raw_text:
        today = datetime.date.today().strftime("%B %d, %Y")
        response["intent"] = "date"
        response["message"] = f"Today is {today}."
        
    # Search
    elif 'search' in tokens or 'google' in tokens:
        query = raw_text.replace('search', '').replace('google', '').strip()
        response["intent"] = "search"
        response["message"] = f"Searching for {query} on Google."
        response["action"] = {"type": "search", "query": query}
        
    # Weather
    elif 'weather' in tokens:
        response["intent"] = "weather"
        response["message"] = "The weather today looks mostly clear with a slight breeze. Perfect for outdoor activities!"
        
    # Music
    elif 'music' in tokens or 'song' in tokens or 'play' in tokens:
        query = raw_text.replace('play', '').replace('music', '').replace('song', '').strip()
        if not query:
            query = "relaxing music"
        response["intent"] = "play_music"
        response["message"] = f"Playing {query} on YouTube."
        response["action"] = {"type": "open", "url": f"https://www.youtube.com/results?search_query={query}"}
        
    # Alarm / Reminder
    elif 'alarm' in tokens or 'reminder' in tokens or 'set' in tokens:
        response["intent"] = "alarm"
        response["message"] = "I've noted that down. I'll remind you at the right time!"
        
    # Open Websites
    elif 'open' in tokens:
        website = raw_text.replace('open', '').strip()
        response["intent"] = "open_website"
        response["message"] = f"Opening {website} for you."
        response["action"] = {"type": "open", "url": f"https://www.{website}.com"}

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
