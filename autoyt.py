import os
import logging
import warnings

# Silence third-party noise. This must run before kokoro is imported, since torch logs on import.
logging.getLogger("torch.distributed.elastic.multiprocessing.redirects").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub.utils._http").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message = r"dropout option adds dropout after all but last recurrent layer", category = UserWarning)
warnings.filterwarnings("ignore", message = r"`?torch\.nn\.utils\.weight_norm`? is deprecated", category = FutureWarning)
warnings.filterwarnings("ignore", message = r"`?torch\.jit\.script`? is deprecated", category = FutureWarning)

import json
import random
import re
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import demoji
import numpy as np
from dotenv import load_dotenv
from google import genai
from kokoro import KPipeline
from PIL import ImageColor, ImageFont

from dotenv import load_dotenv
load_dotenv()
client = genai.Client(api_key = os.getenv("GEMINI_API_KEY"))

CONFIG_PATH = "config.json"
SAMPLE_RATE = 24000  # Kokoro outputs 24 kHz audio
VIDEO_ENCODER = ['-c:v', "h264_videotoolbox", "-b:v", "8M"]

with open("assets/acronyms.json") as f: 
    ACRONYMS = json.load(f)
with open("assets/voices.json") as f:
    VO_CHOICES = json.load(f)
with open("assets/rewrite_prompt.txt") as f:
    REWRITE_PROMPT = f.read().strip()

def gemini_rewrite(post): 
    interaction = client.interactions.create(
        model = "gemini-3.5-flash-lite", 
        input = f"{REWRITE_PROMPT}\n{post}"
        )
    return interaction.output_text

def format_text(text: str) -> str: 
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

    return gemini_rewrite(text)

def load_config(path = CONFIG_PATH):
    with open(path) as f:
        config = json.load(f)

    if config["voice"] not in VO_CHOICES:
        raise SystemExit(f"{path}: unknown voice '{config['voice']}'. Choose one of: {', '.join(VO_CHOICES)}")
    for key, file in [("font.path", config["font"]["path"]), ("gameplay", config["gameplay_path"]), ("input", config["input_path"])]:
        if not Path(file).is_file():
            raise SystemExit(f"{path}: {key} file not found: {file}")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg not found. Install it with: brew install ffmpeg-full")
    filters = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output = True, text = True).stdout
    if not re.search(r"\ssubtitles\s", filters):
        raise SystemExit("ffmpeg library has no 'subtitles' filter. Install one that has it: brew install ffmpeg-full")
    return config

def generate_tts_wav(text, voice, speed):
    text = format_text(text)
    pipeline = KPipeline(lang_code = voice[0], repo_id = "hexgrad/Kokoro-82M")

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

def write_wav(path, audio): 
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w: 
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.tobytes())

def caption_time(t):
    cs = max(0, round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"

def caption_colour(colour):
    r, g, b = ImageColor.getrgb(colour)[:3]
    return f"&H00{b:02X}{g:02X}{r:02X}"

def caption_escape(text):
    return text.replace("\\", "/").replace("{", "(").replace("}", ")")

def build_caption(words, width, height, config):
    font, padding = config["font"], config["padding"]
    family, style = ImageFont.truetype(font["path"], 10).getname()
    bold = -1 if "bold" in (style or "").lower() else 0
    side_margin = int(width * 0.1)  # caption box = 80% of video width, like before

    groups, current = [], []
    for word in words:
        current.append(word)
        if len(current) == config["words_per_caption"] or word[0][-1] in ".?!":
            groups.append(current)
            current = []
    if current:
        groups.append(current)

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {width}",
        f"PlayResY: {height}",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{family},{font['size']},{caption_colour(font['color'])},{caption_colour(font['color'])},"
        f"{caption_colour(font['stroke_color'])},&H00000000,{bold},0,0,0,100,100,0,0,1,{font['stroke_width']},0,"
        f"5,{side_margin},{side_margin},0,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for i, group in enumerate(groups):
        text = caption_escape(" ".join(word for word, _, _ in group))
        start = padding + group[0][1]
        end = padding + (groups[i + 1][0][1] if i + 1 < len(groups) else group[-1][2])
        lines.append(f"Dialogue: 0,{caption_time(start)},{caption_time(end)},Default,,0,0,0,,{text}")
    return "\n".join(lines) + "\n"

def probe(path): 
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height:format=duration", "-of", "json", str(path)],
        capture_output = True, text = True, check = True,
    ).stdout
    info = json.loads(out)
    stream = info["streams"][0]

    return stream["width"], stream["height"], float(info["format"]["duration"])

def generate_video(post, config):
    audio, words = generate_tts_wav(post, config["voice"], config["speed"])
    padding = config["padding"]
    gameplay = Path(config["gameplay_path"]).resolve() 
    output = Path(config["output_path"]).resolve() 
    font_path = Path(config["font"]["path"])

    width, height, gameplay_duration = probe(gameplay)
    length = len(audio) / SAMPLE_RATE + 2 * padding
    if length > gameplay_duration: 
        raise SystemExit(f"Narration ({length:.0f}s) is longer than the gameplay clip ({gameplay_duration:.0f}s).")
    start = random.uniform(0, gameplay_duration - length)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        write_wav(tmp / "narration.wav", audio)
        shutil.copy(font_path, tmp / font_path.name)
        (tmp / "captions.ass").write_text(build_caption(words, width, height, config), encoding = "utf-8")

        delay_ms = int(padding * 1000)
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats",
            "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(gameplay),  # seek before decoding
            "-i", "narration.wav",
            "-filter_complex",
            "[0:v]subtitles=captions.ass:fontsdir=.[v];"
            f"[1:a]adelay={delay_ms}:all=1,apad,aformat=channel_layouts=stereo[a]",
            "-map", "[v]", "-map", "[a]", "-t", f"{length:.3f}",
            *VIDEO_ENCODER,
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(output),
        ]
        # Run inside the temp folder so ffmpeg's filter paths need no escaping.
        subprocess.run(cmd, cwd = tmp, check = True)

    print(f"Video ready: {output}")

def main():
    config = load_config()
    with open(config["input_path"]) as f:
        post = f.read()

    generate_video(post, config)

if __name__ == '__main__':
    main()
