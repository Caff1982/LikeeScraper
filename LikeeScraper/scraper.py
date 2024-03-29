import argparse
import json
import os
from LikeeScraper.api import API
from LikeeScraper import config


def usage():
    return """
        # Get user-id from username
        python scraper user_id -un <username>
        # Get user info from Likee api
        python scraper user_info -ui <user-id>
        # Get user post counts
        python scraper user_post_count -ui <user-id>
        # Get 50 user videos
        python scraper user_videos -ui <user-id> -l 50
        # Get 50 trending videos
        python scraper trending_videos -l 50
        # Get trending hashtags
        python scraper trending_hashtags -l 50
        # Get videos by hashtag-id
        python scraper hashtag_videos -hi <hashtag-id> -l 50
        # Get the comments from a video
        python video_comments -vu <video-url> -l 50

        To save results to a JSON file use -o and specify the
        filename to save the results to.

        To download videos use -d and set to True

        Language, country and the dir to download videos to can be
        specified in the config dictionary.
        """


def create_parser():
    """
    Creates and returns an ArgumentParser object for parsing
    command-line arguments.

    The parser is configured to recognize various modes and options
    for the Likee Scraper.These include fetching user information,
    videos, comments, and more, as well as specifying output formats
    and other preferences.

    Returns:
        argparse.ArgumentParser: The configured parser for
            command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Likee Scraper',
                                     usage=usage())
    parser.add_argument('mode',
                        help="""options:  [user_id, user_info, user_post_count,
                                           user_videos, trending_videos,
                                           trending_hashtags, hashtag_videos,
                                           video_comments]""")
    parser.add_argument('-l',
                        '--limit',
                        type=int,
                        help='The number of results to return',
                        default=None)
    parser.add_argument('-o',
                        '--output',
                        help='The json file to save the result to (optional)',
                        default=None)
    parser.add_argument('-un',
                        '--username',
                        help='The user-name to search for',
                        default=None)
    parser.add_argument('-ui',
                        '--userid',
                        help='The user-id to search for')
    parser.add_argument('-vu',
                        '--videourl',
                        help='The video-url to search for',
                        default=None)
    parser.add_argument('-hi',
                        '--hashtagid',
                        help='The hashtag-id to search for')
    parser.add_argument('-d',
                        '--download',
                        action='store_false',
                        help='Set to True to download videos.')
    parser.add_argument('-v',
                        '--verbose',
                        action='store_true',
                        help='Set to False to stop results being printed out.')
    return parser


def start_scraper():
    """
    Main driver function for the Likee Scraper.

    Parses command-line arguments, interacts with the Likee API,
    and manages the output. Depending on the mode specified, it can
    fetch user information, videos, comments, and more. Results can
    be printed to the console, saved to a file, or videos can be
    downloaded.

    Raises:
        Exception: If an invalid mode is entered or required
        arguments are missing.
    """

    # Parse command-line arguments
    parser = create_parser()
    args = parser.parse_args()
    # Instantiate API object
    api = API()
    # Raise an exception if invalid mode entered
    if args.mode not in ('user_id', 'user_info', 'user_post_count',
                         'user_videos', 'trending_videos', 'trending_hashtags',
                         'hashtag_videos', 'video_comments'):
        raise Exception(f'Mode: "{args.mode}" not recognized')

    if args.mode == 'user_id':
        if args.username is None:
            raise Exception('Username must be supplied for get user-id')
        response = api.get_user_id(args.username)
    elif args.mode == 'user_info':
        if args.userid is None:
            raise Exception('User-id must be supplied for get user-info')
        response = api.get_user_info(args.userid)
    elif args.mode == 'user_post_count':
        if args.userid is None:
            raise Exception('User-id must be supplied for get user-post-count')
        response = api.get_user_post_count(args.userid)
    elif args.mode == 'user_videos':
        if args.userid is None:
            raise Exception('User-id must be supplied for get user-videos')
        response = api.get_user_videos(args.userid, limit=args.limit)
    elif args.mode == 'trending_videos':
        response = api.get_trending_videos(limit=args.limit)
    elif args.mode == 'trending_hashtags':
        response = api.get_trending_hashtags(limit=args.limit)
    elif args.mode == 'hashtag_videos':
        if args.hashtagid is None:
            raise Exception('hashtag-id is required to get hashtag videos')
        response = api.get_hashtag_videos(args.hashtagid, limit=args.limit)
    elif args.mode == 'video_comments':
        if args.videourl is None:
            raise Exception('Video-url is required to get video comments')
        # Set default limit of 10
        limit = config.MAX_VIDEO_COMMENTS if not args.limit else args.limit
        response = api.get_video_comments(args.videourl, limit=limit)

    if args.output:  # Save response as json file
        with open(args.output, 'w') as f:
            f.write(json.dumps(response, indent=2))
    if args.verbose:  # Print to std out
        print(json.dumps(response, indent=2))
    if args.download:  # Download videos
        # Create download_dir if it does not exist
        if not os.path.exists(config.DOWNLOAD_DIR):
            os.mkdir(config.DOWNLOAD_DIR)
        # Iterate through each video in the response and save
        for item in response:
            video_url = item['videoUrl']
            filename = f"{item['likeeId']}_{item['postId']}.mp4"
            filepath = os.path.join(config.DOWNLOAD_DIR, filename)
            if args.verbose:
                print('Downloading: ', filepath)
            api.download_video(video_url, filepath)

    # Quit the Selenium driver
    api.driver.quit()


if __name__ == '__main__':
    start_scraper()
