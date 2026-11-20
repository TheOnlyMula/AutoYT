import os
import re 
import demoji
import json

from dotenv import load_dotenv
load_dotenv() 

with open("assets/acronyms.json") as f: 
    ACRONYMS = json.load(f)
with open("assets/rewrite_prompt.txt") as f: 
    REWRITE_PROMPT = f.read().strip() 

from google import genai
client = genai.Client(api_key = os.getenv("GEMINI_API_KEY"))

def gemini_rewrite(post): 
    interaction = client.interactions.create(
        model = "gemini-3.5-flash-lite", 
        input = f"{REWRITE_PROMPT}\n{post}"
        )
    return interaction.output_text

def format_text(text: str) -> str:
    if not text:
        return ""

    return gemini_rewrite(clean_text(text))

def clean_text(text: str) -> str:
    """Strips Reddit formatting and expands acronyms and emoji. Makes no API calls."""
    if not text:
        return ""

    text = re.sub(r'\*\*|__|\*|_', '', text)
    text = re.sub(r'^>\s?', '', text, flags = re.MULTILINE) 
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'(?i)\b(edit|update\s?\d*):.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'(?i)\btl;?dr:?', 'Too long, didn\'t read: ', text)
    text = re.sub(r'\br/([a-zA-Z0-9_]+)', r'the \1 subreddit', text)
    text = re.sub(r'\bu/([a-zA-Z0-9_-]+)', r'user \1', text)

    for acronym, replacement in ACRONYMS.items():
        text = re.sub(rf'\b{re.escape(acronym)}\b', replacement, text, flags = re.IGNORECASE)

    text = demoji.replace_with_desc(text, sep=" ")
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text