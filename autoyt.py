import logging
import warnings

# Silence third-party noise. This must run before kokoro is imported, since torch logs on import.
logging.getLogger("torch.distributed.elastic.multiprocessing.redirects").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub.utils._http").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message = r"dropout option adds dropout after all but last recurrent layer", category = UserWarning)
warnings.filterwarnings("ignore", message = r"`?torch\.nn\.utils\.weight_norm`? is deprecated", category = FutureWarning)
warnings.filterwarnings("ignore", message = r"`?torch\.jit\.script`? is deprecated", category = FutureWarning)

import re
import json
import shutil
import subprocess
from pathlib import Path

from utils import caption, format_post, video, wav

CONFIG_PATH = "config.json"

with open("assets/voices.json") as f:
    VO_CHOICES = json.load(f)

def load_config(path = CONFIG_PATH):
    if not Path(path).is_file():
        raise SystemExit(f"{path} not found. Copy config.example.json to {path} and edit it.")
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

def main():
    config = load_config()
    text = Path(config["input_path"]).read_text()
    if not text.strip():
        raise SystemExit(f"{config['input_path']} is empty. Paste the post's text into it.")
    
    footage = video.probe(config["gameplay_path"])
    post = format_post.format_text(text)
    audio, words = wav.generate_tts_wav(post.body, config["voice"], config["speed"])
    captions = caption.build_caption(words, footage.width, footage.height, config)
    output = video.generate_video(footage, audio, captions, config, post.title)

    print(f"Video ready: {output}")

if __name__ == '__main__':
    main()
