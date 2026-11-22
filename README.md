# AutoYT

AutoYT turns a Reddit post into a narrated short-form video. A text-to-speech voice reads the post aloud while word-timed captions play over background gameplay footage.

Speech is generated locally with [Kokoro](https://github.com/hexgrad/kokoro), an open-weight text-to-speech model, and the video is put together with [ffmpeg](https://ffmpeg.org). Before narration, the post is sent to Google's Gemini API to fix typos and grammar and to write a title for the video.

## How it works

1. **Cleans up the text.** Removes Markdown formatting, links and trailing "Edit:" or "Update:" notes. Writes out `r/` and `u/` references ("the AskReddit subreddit"), expands common Reddit acronyms such as AITA and TIL, and replaces emoji with their names so the narrator can read them. Gemini 3.5 Flash Lite then corrects typos and grammar, following the instructions in `assets/rewrite_prompt.txt`, and writes a title for the video.
2. **Generates the narration.** Kokoro reads the cleaned text and records when each word is spoken.
3. **Builds the captions.** Groups the words into short captions (three words by default, with a new caption after each sentence) that appear in time with the speech.
4. **Assembles the video.** Cuts a random section of the gameplay footage to the length of the narration plus padding, then lays the captions and audio over it. The video keeps the footage's resolution and frame rate, and is encoded at a bitrate matched to both.

## Project status

The post text is currently supplied by hand. This project was started before Reddit shut down its public RSS feeds, and Reddit's JSON API requires developer approval, which is difficult to obtain for personal scripts. Fetching posts automatically through an RSS bridge or a similar service is in development.

## Requirements

- macOS. Videos are encoded with Apple's hardware encoder (`h264_videotoolbox`), and the default font path in `config.example.json` exists only on macOS.
- Python 3.10, 3.11 or 3.12. Kokoro does not support 3.13 or newer yet.
- [Homebrew](https://brew.sh), to install ffmpeg.
- ffmpeg built with libass, which draws the captions. Homebrew's regular `ffmpeg` formula leaves libass out, so the `ffmpeg-full` formula is required instead (see [Installation](#installation)).
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).
- A background gameplay video. None is included (see [Usage](#usage)).
- Disk space for PyTorch, which is installed with Kokoro, and for the Kokoro model. The model, a few hundred MB, downloads from Hugging Face the first time the script is run. Finished videos also need space: about 375 MB per minute at 4K and 60 fps.

## Installation

1. **ffmpeg.** Homebrew does not add `ffmpeg-full` to the PATH, so it has to be added manually:

   ```bash
   brew install ffmpeg-full
   echo 'export PATH="/opt/homebrew/opt/ffmpeg-full/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

   On Intel Macs, Homebrew installs to `/usr/local` instead of `/opt/homebrew`. The command `ffmpeg -hide_banner -filters | grep subtitles` confirms the installation: it prints a line containing `subtitles` when libass is available.

   The `ffmpeg` package on PyPI (`pip install ffmpeg`) is an unrelated Python package and does not provide ffmpeg.

2. **Python packages.** The packages are installed into a virtual environment created with Python 3.10–3.12:

   ```bash
   git clone https://github.com/TheOnlyMula/AutoYT.git
   cd AutoYT
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

   `requirements.txt` includes pytest, which is needed only for running the tests.

3. **Gemini API key.** The key is read from a file called `.env` in the project folder:

   ```
   GEMINI_API_KEY = "KEY"
   ```

   `.env` is listed in `.gitignore`.

## Usage

1. **Gameplay footage.** Videos are large and usually someone else's work, so none is included in the repository. The video is expected at `assets/minecraftparkourgameplay.mp4`, or at a custom `gameplay_path` set in `config.json`. The footage must be longer than the narration plus padding.
2. **Post text.** The post's text is read from `input.txt` in the project folder.
3. **Configuration file.** `config.json` is created from the template. Its settings are described under [Configuration](#configuration).

   ```bash
   cp config.example.json config.json
   ```

4. **Running the script.** The script is run from the project folder, since `assets/` and the paths in `config.json` are read relative to the current folder:

   ```bash
   python autoyt.py
   ```

The finished video is saved in the project folder and named after the title Gemini writes for the post, as `<title>.mp4`. Any `/` or `:` in the title becomes `-` in the filename. It has the same resolution, aspect ratio and frame rate as the gameplay footage. The bitrate scales with the resolution and frame rate: about 50 Mbps, or 375 MB per minute, at 4K and 60 fps.

## Configuration

All settings are in `config.json`. The file is not tracked by git, so local changes stay out of the repository. `config.example.json` holds the defaults:

```json
{
    "voice": "af_heart",
    "speed": 1.0,
    "gameplay_path": "assets/minecraftparkourgameplay.mp4",
    "input_path": "input.txt",
    "padding": 1,
    "words_per_caption": 3,
    "font": {
        "path": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "size": 110,
        "color": "white",
        "stroke_color": "black",
        "stroke_width": 5
    }
}
```

| Setting | Functionality |
| --- | --- |
| `voice` | The narrator. Any voice name from `assets/voices.json` (see [Voices](#voices)). |
| `speed` | How fast the narrator speaks. `1.0` is normal speed. |
| `gameplay_path` | Path to the background video. |
| `input_path` | Path to the text file containing the post. |
| `padding` | Seconds of silence before and after the narration. |
| `words_per_caption` | The most words shown on screen at once. A caption also ends after `.`, `?` or `!`. |
| `font.path` | Path to a `.ttf` or `.otf` font file. The full path is required, since `~` is not expanded. |
| `font.size` | Caption text size in pixels. |
| `font.color` | Caption text colour, as a name (`white`) or a hex code (`#FFD700`). |
| `font.stroke_color` | Colour of the outline around the text. |
| `font.stroke_width` | Outline thickness in pixels. `0` means no outline. |

Relative paths are resolved from the folder the script is run in. If `config.json` is missing, the voice name is unknown, a file is missing or ffmpeg lacks the `subtitles` filter, the script stops with an error before doing any work.

## Voices

AutoYT supports Kokoro's 28 English voices. `assets/voices.json` lists each voice with its gender, accent and Kokoro's quality grade. Kokoro's [voice list](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) describes each voice in more detail.

## Acronyms

`assets/acronyms.json` maps abbreviations to the words the narrator says instead, for example `"TIL": "Today I learned"`. Matching is case-insensitive and applies only to whole words.

## Project structure

```
AutoYT/
├── autoyt.py                Entry point: loads the config and runs each step in order
├── config.example.json      Default settings, copied to config.json
├── pyproject.toml           pytest settings
├── requirements.txt         Python dependencies
├── assets/
│   ├── acronyms.json        Abbreviations and their spoken forms
│   ├── voices.json          Supported Kokoro voices
│   ├── rewrite_prompt.txt   Instructions sent to Gemini with each post
│   └── profile_picture.png  Profile picture, not used yet
├── utils/
│   ├── format_post.py       Text clean-up, Gemini rewrite and title
│   ├── wav.py               Narration and word timings from Kokoro
│   ├── caption.py           Caption file (.ass) generation
│   └── video.py             Footage probing and video assembly with ffmpeg
└── tests/                   pytest tests
```

`config.json`, `input.txt`, `.env` and video files are created locally and ignored by git.

## Tests

Tests are in `tests/` and run with pytest from the project folder:

```bash
pytest
```

`pyproject.toml` adds the project folder to the import path, so tests can import `autoyt.py` and the modules in `utils/`. The text clean-up in `utils/format_post.py` is separated into `clean_text`, which makes no API calls. `tests/test_gemini_rewrite.py` does call the Gemini API, so it needs the key in `.env` and uses API quota each time it runs. The test suite is in development.

## Built with

- [Kokoro](https://github.com/hexgrad/kokoro) for text-to-speech
- [ffmpeg](https://ffmpeg.org) and [libass](https://github.com/libass/libass) for video encoding and captions
- [Gemini API](https://ai.google.dev/gemini-api/docs) for fixing typos and grammar and writing titles
- [demoji](https://github.com/bsolomon1124/demoji) for emoji descriptions
