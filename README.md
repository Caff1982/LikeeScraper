# LikeeScraper

A command-line application written in Python that can be used for scraping information from Likee.

## Installation

### Install with pip
```
pip install git+https://github.com/Caff1982/LikeeScraper
```

### Build from source
1. Clone repo
```
git clone https://github.com/Caff1982/LikeeScraper.git
```
2. Move to LikeeScraper directory
```
cd LikeeScraper
```
3. Install the `build` package (If not already installed)
```
pip install build
```
4. Start building
```
python -m build
```
5. Install the built `wheel` file
```
pip install dist/*.whl
```
#### Note
> Ensure Firefox browser and Geckodriver are installed to enable Selenium to run [(see here for more info)](https://selenium-python.readthedocs.io/installation.html#drivers)

## Usage

Get user-id using username
```
LikeeScraper user_id -un <username>
```
Get user info from Likee api
```
LikeeScraper user_info -ui <user-id>
```
Get user post counts
```
LikeeScraper user_post_count -ui <user-id>
```
Get 50 user videos
```
LikeeScraper user_videos -ui <user-id> -l 50
```
Get 50 trending videos
```
LikeeScraper trending_videos -l 50
```
Get trending hashtags
```
LikeeScraper trending_hashtags -l 50
```
Get videos by hashtag-id
```
LikeeScraper hashtag_videos -hi <hashtag-id> -l 50
```
Get the comments for a video
```
LikeeScraper video_comments -vu <video-url> -l 50
```

To save results to a JSON file use -o and specify the filename to save the results to.

To download videos use -d and set to True

Language, country and the directory to download videos to can be
specified in the config dictionary within scraper.py

