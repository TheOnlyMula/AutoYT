import json
import random
import re
import shutil
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import NamedTuple

from utils import wav

VIDEO_CODEC = "h264_videotoolbox"
# Bits per pixel per frame: about 50 Mbps at 4K 60 fps and 12 Mbps at 1080p 60 fps,
# close to YouTube's recommended upload bitrates for H.264.
BITS_PER_PIXEL = 0.1

class Footage(NamedTuple):
    path: Path
    width: int
    height: int
    fps: float
    duration: float

def probe(path):
    path = Path(path).resolve()
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
        capture_output = True, text = True, check = True,
    ).stdout
    info = json.loads(out)
    stream = info["streams"][0]
    fps = float(Fraction(stream["r_frame_rate"]))  # reported as a fraction, e.g. "60/1"

    return Footage(path, stream["width"], stream["height"], fps, float(info["format"]["duration"]))

def output_path(title):
    # "/" would point into a folder that doesn't exist, Finder shows ":" as "/", and a leading "." hides the file.
    name = re.sub(r"[/:]", "-", title)
    name = re.sub(r"\s+", " ", name).strip().lstrip(".").strip()
    return Path(f"{name or 'output'}.mp4").resolve()

def generate_video(footage, audio, captions, config, title):
    padding = config["padding"]
    output = output_path(f"output/{title}")
    font_path = Path(config["font"]["path"])

    bitrate = round(footage.width * footage.height * footage.fps * BITS_PER_PIXEL)
    length = len(audio) / wav.SAMPLE_RATE + 2 * padding
    if length > footage.duration:
        raise SystemExit(f"Narration ({length:.0f}s) is longer than the gameplay clip ({footage.duration:.0f}s).")
    start = random.uniform(0, footage.duration - length)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        wav.write_wav(tmp / "narration.wav", audio)
        shutil.copy(font_path, tmp / font_path.name)
        (tmp / "captions.ass").write_text(captions, encoding = "utf-8")

        delay_ms = int(padding * 1000)
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats",
            "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(footage.path),  # seek before decoding
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

    return output
