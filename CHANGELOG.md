# Changelog

## 2026-11-22
### Added
- Gemini now writes a title for each post as well as rewriting it. Its reply follows a JSON schema (the `Post` class in `utils/format_post.py`), so it always contains a `title` and a `body`.
- The finished video is named after that title and saved in the project folder. Any `/` or `:` in the title becomes `-` in the filename, since a `/` would otherwise point into a folder that doesn't exist.
- First test, `tests/test_gemini_rewrite.py`, checks that Gemini's reply has a non-empty title and body. It calls the Gemini API, so it needs the key in `.env`.
### Changed
- Rewrote `assets/rewrite_prompt.txt` for the reply's new title and body. It tells Gemini what makes a good title (a hook, true to the post, under YouTube's 100-character limit, plain text) and to keep the post's own Reddit title as the body's first sentence.
- `main()` in `autoyt.py` now runs every step in order and passes each result to the next: rewrite, narration, captions, then video. Each module in `utils/` does one step and no longer calls the others.
- `utils/format.py` renamed to `utils/format_post.py`. `format_text` returns a `Post` object with `title` and `body`.
- Video assembly moved from `autoyt.py` to `utils/video.py`. `probe` returns a `Footage` object with the clip's path, size, frame rate and length.
### Removed
- `output_path` setting, since the video is now named after its title. An `output_path` left in an existing `config.json` is ignored.
### Fixed
- An empty input file now stops the script with an error message instead of failing partway through.

## 2026-11-21
### Added 
- Profile picture added to `assets/` for future implementation. 
- `config.example.json` as a committed template for `config.json`. Script explains how to create `config.json` if it is missing.
- `pyproject.toml` so that `pytest` can be run from the project folder.
- `utils/__init__.py` to mark `utils/` as a package.
### Removed 
- `config.example.json` replaces `config.json`.
### Fixed
- README typos.
- Output video looked lower resolution than the gameplay footage, because the bitrate was fixed at 8 Mbps. The bitrate now scales with the footage's resolution and frame rate (about 50 Mbps at 4K 60 fps). On a 4K 60 fps sample, PSNR against the source rose from 39.5 dB to 50.8 dB.

## 2026-11-20
### Added
- Changed from using `MoviePy` to `ffmpeg` for faster processing. Video processing times for a 1881 character (or 1m:44s video) has reduced by 88.42%. (349.32s to 40.45s). 
- Added test folders so that recompiling with video system everytime isn't required. TODO: Add testcases. 
- Updated AI Prompt. 
- Test suite in development

## 2026-11-18
### Added 
- Changed from `parse.arguments` to `config.json` file since customisability is sky rocketing. 
- Integrated an AI model to format the text received from reddit. This was done since a large majority of reddit posts are riddled with typos and grammatical errors.
### Fixed
- Kokoro model would often get the pronounciation of typoed words wrong. This was fixed with the integration of the AI feature listed above.
### Removed
- Forced to remove auto-web-scraping due to Reddit's decision to remove the .RSS functionality from its pages. An alternative method must be found. 
### Known Issues
- Subtitle Cropping.

## 2026-11-14
### Added
- Init. 