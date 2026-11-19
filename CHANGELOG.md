# Changelog

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