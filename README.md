# AutoYT

AutoYT turns a Reddit post into a narrated short-form video. A text-to-speech voice reads the post aloud while word-timed captions play over background gameplay footage.

Speech is generated locally with [Kokoro](https://github.com/hexgrad/kokoro), an open-weight text-to-speech model, and the video is put together with [ffmpeg](https://ffmpeg.org). Before narration, the post is sent to Google's Gemini API to fix typos and grammar.

## How it works

1. **Cleans up the text.** Removes Markdown formatting, links and trailing "Edit:" or "Update:" notes. Writes out `r/` and `u/` references ("the AskReddit subreddit"), expands common Reddit acronyms such as AITA and TIL, and replaces emoji with their names so the narrator can read them. Gemini 3.5 Flash Lite is used to rewrite typos and errors. 
2. **Generates the narration.** Kokoro reads the cleaned text and records when each word is spoken.
3. **Builds the captions.** Groups the words into short captions (three words by default, with a new caption after each sentence) that appear in time with the speech.
4. **Assembles the video.** Cuts a random section of the gameplay footage to the length of the narration, then lays the captions and audio over it.

## Project status

The post text is currently supplied by hand. This project was started before Reddit shut down its public RSS feeds, and Reddit's JSON API needs developer approval, which is notoriously hard to get for personal scripts. The plan is to fetch posts automatically through an RSS bridge or something similar, which is still in development. 

## Requirements

- macOS. Videos are encoded with Apple's hardware encoder (`h264_videotoolbox`), and the default font path in `config.json` exists only on macOS.
- Python 3.10, 3.11 or 3.12. Kokoro does not support 3.13 or newer yet.
- [Homebrew](https://brew.sh), to install ffmpeg.
- ffmpeg built with libass, which draws the captions. Homebrew's regular `ffmpeg` leaves libass out, so install `ffmpeg-full` instead (see [Installation](#installation)).
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).
- A background gameplay video. None is included (see [Usage](#usage)).
- Disk space for PyTorch, which is installed with Kokoro, and for the Kokoro model. The model, a few hundred MB, downloads from Hugging Face the first time the script is run.

## Installation

1. **Install ffmpeg.** Homebrew does not add `ffmpeg-full` to the local PATH. Must be done manually:

   ```bash
   brew install ffmpeg-full
   echo 'export PATH="/opt/homebrew/opt/ffmpeg-full/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

   On an Intel Mac, replace `/opt/homebrew` with `/usr/local`. To check that it worked, run `ffmpeg -hide_banner -filters | grep subtitles`, which should print a line containing `subtitles`.

   NOTE: `pip install ffmpeg` is an unrelated Pyhon package. 

2. **Install the Python packages.**

   ```bash
   git clone https://github.com/TheOnlyMula/AutoYT.git
   cd AutoYT
   python3 -m venv .venv              # use Python 3.10–3.12
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Add Gemini API key.** Create a file called `.env` in the project folder containing:

   ```
   GEMINI_API_KEY = "KEY"
   ```

   `.env` is listed in `.gitignore`.

## Usage

1. **Add gameplay footage.** Videos are large and usually someone else's work, so none is included here. The video must be saved as `assets/minecraftparkourgameplay.mp4` or a custom `gameplay_path` in `config.json`. The footage must be longer than the narration plus padding.
2. **Add the post.** Paste the post's text into a file called `input.txt` in the project folder.
3. **Check the settings** in `config.json` (see [Configuration](#configuration)).
4. **Run the script** from the project folder:

   ```bash
   python autoyt.py
   ```

The finished video is saved as `output.mp4`. It has the same resolution and shape as the chosen gameplay footage. 

## Configuration

All settings are in `config.json`:

```json
{
    "voice": "af_heart",
    "speed": 1.0,
    "gameplay": "assets/minecraftparkourgameplay.mp4",
    "input": "input.txt",
    "output": "output.mp4",
    "padding": 1,
    "words_per_caption": 3,
    "font": {
        "path": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "size": 110,
        "color": "white",
        "stroke_color": "black",
        "stroke_width": 0
    }
}
```

| Setting | Functionality |
| --- | --- |
| `voice` | The narrator. Use any voice name from `assets/voices.json` (see [Voices](#voices)). |
| `speed` | How fast the narrator speaks. `1.0` is normal speed. |
| `gameplay` | Path to the background video. |
| `input` | Path to the text file containing the post. |
| `output` | Where the finished video is saved. |
| `padding` | Seconds of silence before and after the narration. |
| `words_per_caption` | The most words shown on screen at once. A caption also ends after `.`, `?` or `!`. |
| `font.path` | Path to a `.ttf` or `.otf` font file. Write the full path; `~` is not expanded. |
| `font.size` | Caption text size in pixels. |
| `font.color` | Caption text colour, as a name (`white`) or a hex code (`#FFD700`). |
| `font.stroke_color` | Colour of the outline around the text. |
| `font.stroke_width` | Outline thickness in pixels. `0` means no outline. |

Relative paths are resolved from the folder the the script is run in. If a voice name is wrong or a file is missing, the script stops with an error before doing any work.

## Voices

AutoYT supports Kokoro's 28 English voices. 

`assets/voices.json` lists each voice with Kokoro's quality grade. See Kokoro's [voice list](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) for details.

## Acronyms

`assets/acronyms.json` maps abbreviations to what the narrator should say instead, for example `"TIL": "Today I learned"`. Matching is case-insensitive and applies only to whole words.

## Built with

- [Kokoro](https://github.com/hexgrad/kokoro) for text-to-speech
- [ffmpeg](https://ffmpeg.org) and [libass](https://github.com/libass/libass) for video encoding and captions
- [Gemini API](https://ai.google.dev/gemini-api/docs) for fixing typos and grammar
- [demoji](https://github.com/bsolomon1124/demoji) for emoji descriptions