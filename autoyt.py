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
import random
import shutil
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path

import utils.caption as caption
import utils.wav as wav

CONFIG_PATH = "config.json"
VIDEO_CODEC = "h264_videotoolbox"
# Bits per pixel per frame: about 50 Mbps at 4K 60 fps and 12 Mbps at 1080p 60 fps,
# close to YouTube's recommended upload bitrates for H.264.
BITS_PER_PIXEL = 0.1

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

def probe(path): 
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
        capture_output = True, text = True, check = True,
    ).stdout
    info = json.loads(out)
    stream = info["streams"][0]
    fps = float(Fraction(stream["r_frame_rate"]))  # reported as a fraction, e.g. "60/1"

    return stream["width"], stream["height"], fps, float(info["format"]["duration"])

def generate_video(post, config):
    audio, words = wav.generate_tts_wav(post, config["voice"], config["speed"])
    padding = config["padding"]
    gameplay = Path(config["gameplay_path"]).resolve() 
    output = Path(config["output_path"]).resolve() 
    font_path = Path(config["font"]["path"])

    width, height, fps, gameplay_duration = probe(gameplay)
    bitrate = round(width * height * fps * BITS_PER_PIXEL)
    length = len(audio) / wav.SAMPLE_RATE + 2 * padding
    if length > gameplay_duration: 
        raise SystemExit(f"Narration ({length:.0f}s) is longer than the gameplay clip ({gameplay_duration:.0f}s).")
    start = random.uniform(0, gameplay_duration - length)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        wav.write_wav(tmp / "narration.wav", audio)
        shutil.copy(font_path, tmp / font_path.name)
        (tmp / "captions.ass").write_text(caption.build_caption(words, width, height, config), encoding = "utf-8")

        delay_ms = int(padding * 1000)
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats",
            "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(gameplay),  # seek before decoding
            "-i", "narration.wav",
            "-filter_complex",
            "[0:v]subtitles=captions.ass:fontsdir=.[v];"
            f"[1:a]adelay={delay_ms}:all=1,apad,aformat=channel_layouts=stereo[a]",
            "-map", "[v]", "-map", "[a]", "-t", f"{length:.3f}",
            "-c:v", VIDEO_CODEC, "-b:v", str(bitrate),
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
