import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

import argparse
import json
from pathlib import Path

from kokoro import KPipeline
import soundfile as sf
import numpy as np

import re
import demoji

import random
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, CompositeVideoClip, TextClip

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
WORDS_PER_CAPTION = 3
ATOM = {"atom": "http://www.w3.org/2005/Atom"}
GAMEPLAY_PATH = Path(__file__).with_name("minecraftparkourgameplay.mp4")
PADDING = 1
HEADERS = {"User-Agent": "autoyt/1.0"}

with open(Path(__file__).with_name("acronyms.json"), encoding = "utf-8") as f: 
    ACRONYMS = json.load(f)

def format_reddit_body(text: str) -> str: 
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

def parse_feed(xml):
    entry = ET.fromstring(xml).find("atom:entry", ATOM)
    if entry is None:
        return None

    content = BeautifulSoup(entry.findtext("atom:content", "", ATOM), "html.parser")
    body = content.find("div", class_ = "md")
    text = "\n\n".join(p.get_text() for p in body.find_all("p")) if body else ""

    return {
        "title": entry.findtext("atom:title", "", ATOM),
        "link": entry.find("atom:link", ATOM).get("href"),
        "text": text,
    }

def fetch_feed(args):
    feed_url = f"https://www.reddit.com/r/{args.subreddit}/top/.rss"
    params = {"t": args.time_period, "limit": 1}
    response = requests.get(feed_url, params = params, headers = HEADERS, timeout = 15)
    response.raise_for_status()
    return response.content

def generate_tts_wav(text):
    text = format_reddit_body(text)
    pipeline = KPipeline(lang_code = "a")

    chunks, words = [], []
    offset = 0.0
    for result in pipeline(text, voice = "af_heart", speed = 1.0):
        for token in result.tokens:
            if token.start_ts is None or token.end_ts is None:
                continue
            start, end = offset + token.start_ts, offset + token.end_ts
            if words and not any(c.isalnum() for c in token.text):
                word, word_start, _ = words[-1]
                words[-1] = (word + token.text, word_start, end)  # attach punctuation to the previous word
            else:
                words.append((token.text, start, end))

        chunks.append(result.audio)
        offset += len(result.audio) / 24000

    sf.write("tts.wav", np.concatenate(chunks), 24000)
    return words

def make_captions(words, video_width):
    groups, current = [], []
    for word in words:
        current.append(word)
        if len(current) == WORDS_PER_CAPTION or word[0][-1] in ".?!":
            groups.append(current)
            current = []
    if current:
        groups.append(current)

    captions = []
    for i, group in enumerate(groups):
        text = " ".join(word for word, _, _ in group)
        start = group[0][1]
        end = groups[i + 1][0][1] if i + 1 < len(groups) else group[-1][2]

        caption = TextClip(
            font = FONT_PATH, text = text, font_size = 110,
            color = "white", stroke_color = "black", stroke_width = 6,
            method = "caption", size = (int(video_width * 0.8), None),
            text_align = "center", margin = (20, 20),
        )
        captions.append(caption.with_start(PADDING + start).with_end(PADDING + end).with_position("center"))
    return captions

def generate_video(words, audio_path = "tts.wav", output = "output.mp4"):
    with VideoFileClip(str(GAMEPLAY_PATH)) as gameplay, AudioFileClip(audio_path) as narration:
        length = narration.duration + 2 * PADDING
        start = random.uniform(0, gameplay.duration - length)

        clip = gameplay.subclipped(start, start + length)
        clip = CompositeVideoClip([clip, *make_captions(words, clip.w)])
        clip = clip.with_audio(CompositeAudioClip([narration.with_start(PADDING)]))
        clip.write_videofile(output, codec = "libx264", audio_codec = "aac")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-de', '--demo', action = 'store_true', help = "Whether or not the extract will use the demo post provided at demo/.")
    parser.add_argument('-sr', '--subreddit', type = str, help = "The subreddit to extract from.", default = "AmItheAsshole")
    parser.add_argument('-tp', '--time_period', choices = ["hour", "day", "week", "month", "year", "all"], help = "Select from the following: hour, day, week, month, year, and all.", default = "day")
    args = parser.parse_args() 

    if args.demo:
        with open("demo/feed.xml", "rb") as f:
            data = f.read()
    else:
        data = fetch_feed(args)
    post = parse_feed(data)

    if post is None:
        print("No posts found")
        return

    # print(f"Post:\n{post["title"]} \nBody:\n{post["text"]}") 
    # checking ^
    words = generate_tts_wav(f"{post["title"]} {post["text"]}")
    generate_video(words) 

if __name__ == '__main__':
    main()
