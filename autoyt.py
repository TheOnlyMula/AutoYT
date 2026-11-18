import xml.etree.ElementTree as ET

import json

import numpy as np

import re
import demoji

import random
from moviepy import VideoFileClip, AudioArrayClip, CompositeAudioClip, CompositeVideoClip, TextClip
from kokoro import KPipeline
from pathlib import Path

CONFIG_PATH = "config.json"
SAMPLE_RATE = 24000  # Kokoro outputs 24 kHz audio
HEADERS = {"User-Agent": "autoyt/1.0"}

with open("assets/acronyms.json") as f: 
    ACRONYMS = json.load(f)
with open("assets/voices.json") as f: 
    VO_CHOICES = json.load(f)

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

def load_config(path = CONFIG_PATH):
    with open(path) as f:
        config = json.load(f)

    if config["voice"] not in VO_CHOICES:
        raise SystemExit(f"{path}: unknown voice '{config['voice']}'. Choose one of: {', '.join(VO_CHOICES)}")
    for key, file in [("font.path", config["font"]["path"]), ("gameplay", config["gameplay_path"]), ("input", config["input"])]:
        if not Path(file).is_file():
            raise SystemExit(f"{path}: {key} file not found: {file}")
    return config

def generate_tts_wav(text, voice, speed):
    text = format_reddit_body(text)
    pipeline = KPipeline(lang_code = voice[0])

    chunks, words = [], []
    offset = 0.0
    for result in pipeline(text, voice = voice, speed = speed):
        for token in result.tokens:
            if token.start_ts is None or token.end_ts is None:
                continue
            start, end = offset + token.start_ts, offset + token.end_ts
            if words and not any(c.isalnum() for c in token.text):
                word, word_start, _ = words[-1]
                words[-1] = (word + token.text, word_start, end)
            else:
                words.append((token.text, start, end))

        chunks.append(result.audio)
        offset += len(result.audio) / SAMPLE_RATE

    audio = np.concatenate(chunks)
    return audio, words

def make_captions(words, video_width, config):
    font, padding = config["font"], config["padding"]

    groups, current = [], []
    for word in words:
        current.append(word)
        if len(current) == config["words_per_caption"] or word[0][-1] in ".?!":
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
            font = font["path"], text = text, font_size = font["size"],
            color = font["color"], stroke_color = font["stroke_color"], stroke_width = font["stroke_width"],
            method = "caption", size = (int(video_width * 0.8), None),
            text_align = "center", margin = (20, 20),
        )
        captions.append(caption.with_start(padding + start).with_end(padding + end).with_position("center"))
    return captions

def generate_video(post, config):
    audio, words = generate_tts_wav(post, config["voice"], config["speed"])
    padding = config["padding"]
    # AudioArrayClip expects (samples, channels); a single channel comes out garbled, so duplicate to stereo.
    stereo = np.column_stack([audio, audio])
    with VideoFileClip(config["gameplay_path"]) as gameplay, AudioArrayClip(stereo, fps = SAMPLE_RATE) as narration:
        length = narration.duration + 2 * padding
        start = random.uniform(0, gameplay.duration - length)

        clip = gameplay.subclipped(start, start + length)
        clip = CompositeVideoClip([clip, *make_captions(words, clip.w, config)])
        clip = clip.with_audio(CompositeAudioClip([narration.with_start(padding)]))
        clip.write_videofile(config["output"], codec = "libx264", audio_codec = "aac")

def main():
    config = load_config()
    with open(config["input"]) as f:
        post = f.read()

    generate_video(post, config)

if __name__ == '__main__':
    main()
