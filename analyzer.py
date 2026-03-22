from textblob import TextBlob
import spacy
from collections import Counter
import re

# Load English NLP model
nlp = spacy.load("en_core_web_sm")

# Define our political topics and their related keywords
TOPIC_DICTIONARY = {
    "Economy 💰": ["economy", "jobs", "tax", "inflation", "growth", "business", "market", "employment"],
    "Healthcare 🏥": ["health", "hospital", "doctor", "medical", "medicine", "care", "patients", "disease"],
    "Education 🎓": ["school", "education", "college", "students", "teachers", "university", "learning"],
    "Infrastructure 🏗️": ["roads", "bridges", "infrastructure", "construction", "railway", "highway", "build"],
    "Defense 🛡️": ["military", "defense", "army", "security", "border", "police", "weapons"]
}

def analyze_speech(text):
    text_lower = text.lower()
    
    # 1. Sentiment Analysis
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1: sentiment = "Positive 😊"
    elif polarity < -0.1: sentiment = "Negative 😠"
    else: sentiment = "Neutral 😐"
        
    # 2. Keyword Extraction
    doc = nlp(text)
    keywords = [token.text.lower() for token in doc if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop]
    top_keywords = [word for word, count in Counter(keywords).most_common(5)]
    
    # 3. Promise Detection
    promise_phrases = ["we will", "i promise", "we guarantee", "government will", "my government will"]
    promises_made = [sentence.strip() for sentence in text.split('.') if any(phrase in sentence_lower for phrase in promise_phrases for sentence_lower in [sentence.lower()])]
    
    # 4. TOPIC DETECTION (NEW!)
    detected_topics = set()
    for topic, words in TOPIC_DICTIONARY.items():
        if any(word in text_lower for word in words):
            detected_topics.add(topic)
            
    # 5. FACT-CHECK ALERTS (NEW!)
    # We will flag any sentence that contains specific numbers, percentages, or money as "Needs Fact-Checking"
    fact_check_flags = []
    sentences = text.split('.')
    for sentence in sentences:
        # Check for numbers (e.g., "100", "million", "billion", "%", "dollars", "rupees")
        if re.search(r'\d+|million|billion|trillion|%|percent|dollars|rupees|crore|lakh', sentence.lower()):
            if len(sentence.strip()) > 5: # Ignore super short accidental sentences
                fact_check_flags.append(sentence.strip())

    return {
        "sentiment": sentiment,
        "top_keywords": top_keywords,
        "promises": promises_made,
        "topics": list(detected_topics) if detected_topics else ["General / Uncategorized"],
        "fact_checks": fact_check_flags
    }