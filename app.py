from flask import Flask, render_template, request, jsonify
import datetime
import string
import os

app = Flask(__name__)

# Simple stop words list (avoids NLTK dependency which fails on Vercel's read-only filesystem)
STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're",
    "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he',
    'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's",
    'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
    'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because',
    'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
    'between', 'through', 'during', 'before', 'after', 'above', 'below', 'to',
    'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
    'all', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
    'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't',
    'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd',
    'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't",
    'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn',
    "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
    'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
}

def preprocess_text(text):
    """Tokenize and remove stop words / punctuation (no NLTK needed)."""
    # Simple whitespace + punctuation tokenizer
    text = text.lower()
    # Remove punctuation from text for tokenization
    translator = str.maketrans('', '', string.punctuation)
    cleaned = text.translate(translator)
    tokens = cleaned.split()
    filtered_tokens = [w for w in tokens if w not in STOP_WORDS]
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
