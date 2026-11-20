# Changelog

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