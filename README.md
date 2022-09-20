# LikeeScraper

A command-line application written in Python that can be used for scraping information from Likee.

## Installation

1. Clone repo
```
git clone https://github.com/Caff1982/LikeeScraper.git
```
2. Install dependent packages
```
pip install -r requirements.txt
```
3. Ensure Firefox browser and Geckodriver are installed to enable Selenium to run [(see here for more info)](https://selenium-python.readthedocs.io/installation.html#drivers)

## Usage

Get user-id using username
```
python scraper.py user_id -un <username>
```
Get user info from Likee api
```
python scraper.py user_info -ui <user-id>
```
Get user post counts
```
python scraper.py user_post_counts -ui <user-id>
```
Get 50 user videos
```
python scraper.py user_videos -ui <user-id> -l 50
```
Get 50 trending videos
```
python scraper.py trending_videos -l 50
```
Get trending hashtags
```
python scraper.py trending_hashtags -l 50
```
Get videos by hashtag-id
```
python scraper.py hashtag_videos -hi <hashtag-id> -l 50
```
Get the comments for a video
```
python scraper.py video_comments -vu <video-url> -l 50
```

To save results to a JSON file use -o and specify the filename to save the results to.

To download videos use -d and set to True

Language, country and the directory to download videos to can be
specified in the config dictionary within scraper.py

