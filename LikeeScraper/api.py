import re
import time
import json
import random

import requests
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import Firefox
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from LikeeScraper import config


class API:
    """
    A class to interact with the Likee API and scrape data from
    the Likee platform.

    This class provides methods to:
    - Fetch user information and videos.
    - Retrieve trending videos and hashtags.
    - Download videos from given URLs.
    - Extract comments from videos.

    Attributes:
        country (str): The country for the API requests. Default is 'US'.
        language (str): The language for the API requests. Default is 'en'.
        pause_time (int): The base time (in seconds) to pause between
            requests to avoid rate limits. A random additional time
            between 0 and 1 second is added to this base time. Default
            is 3.
        headless (bool): Whether to run the selenium browser in headless
            mode, useful for debugging. Default is True.
        timeout (int): The timeout time (in seconds) for API requests.
            Default is 10.

    Example:
        api = API(country='UK', language='en')
        user_id = api.get_user_id('example_username')
        user_info = api.get_user_info(user_id)
        print(user_info)
    """

    def __init__(self, country=config.COUNTRY, language=config.LANGUAGE,
                 pause_time=config.PAUSE_TIME, timeout=config.TIMEOUT_TIME,
                 headless=config.USE_HEADLESS):
        self.country = country
        self.language = language
        self.pause_time = pause_time
        self.timeout = timeout

        # API endpoints
        self.user_vids_endpoint = 'https://api.like-video.com/likee-activity-flow-micro/videoApi/getUserVideo'
        self.user_info_endpoint = 'https://api.like-video.com/likee-activity-flow-micro/userApi/getUserInfo'
        self.trending_vids_endpoint = 'https://api.like-video.com/likee-activity-flow-micro/videoApi/getSquareVideos'
        self.trending_hashtags_endpoint = 'https://likee.video/official_website/RecommendApi/getRecommendHashtag'
        self.hashtag_vids_endpoint = 'https://likee.video/official_website/VideoApi/getEventVideo'
        self.video_comments_endpoint = 'https://likee.video/live/home/comments'
        self.user_post_count_endpoint = 'https://api.like-video.com/likee-activity-flow-micro/userApi/getUserPostNum'

        # Creating both JSON and form headers
        self.json_headers = requests.utils.default_headers().update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
                'Content-Type': 'application/json',
                })
        self.form_headers = requests.utils.default_headers().update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded',
                })
        # Defining options for selenium browser
        self.browser_options = Options()
        if headless:
            self.browser_options.add_argument('--headless')
        self.driver = Firefox(options=self.browser_options)

    def pause(self):
        """
        Pauses api operations. Adds a random time between
        self.pause_time and self.pause_time + 1 to add
        stochasticity and avoid being blocked
        """
        time.sleep(self.pause_time + random.random())

    def make_post_request(self, payload, endpoint, content_type='json'):
        """
        Sends a POST request to the specified API endpoint.

        This method sends a POST request to the given endpoint with
        the provided payload. The headers used for the request are
        determined by the content_type argument.

        Parameters:
            payload (dict): The data to be sent in the POST request.
            endpoint (str): The URL of the API endpoint for the request.
            content_type (str, optional): The type of content being sent.
                It determines the headers used for the request.
                Accepts either 'json' (default) or 'url-form-encoded'.

        Returns:
            dict: The JSON response from the API if the request is successful.
                If there's an HTTP error or the API returns an error message,
                an empty dictionary is returned.

        Raises:
            None: Errors are handled internally by displaying error messages,
                no exceptions are raised to the caller.

        Example:
            payload = {'uid': '12345'}
            response = api.make_post_request(payload, 'example_endpoint')
            print(response)
        """
        if content_type == 'json':
            response = requests.post(endpoint,
                                     json=payload,
                                     headers=self.json_headers,
                                     timeout=self.timeout)
        else:
            response = requests.post(endpoint,
                                     data=payload,
                                     headers=self.form_headers,
                                     timeout=self.timeout)
        # Check response has no http errors
        if response.status_code != 200:
            print('HTTP error: ', response.status_code)
            return {}
        # Convert response to json and check for error message
        response = response.json()
        if ('message' in response and response['message'] != 'ok'):
            print('API Error: ', response['message'])
            return {}
        elif ('msg' in response and response['msg'] != 'success'):
            print('API Error: ', response['msg'])
            return {}
        else:
            return response

    def get_user_id(self, username):
        """
        Retrieves the user's unique identifier (uid) based on their username.

        This method navigates to the user's profile page, clicks on the
        first video, and then extracts the user's uid from the video page's
        source code using a regex pattern.

        The regex pattern 'window.data = ({.*?});' is used to capture the
        JSON data embedded in the page's JavaScript, which contains the
        user's uid among other details.

        Parameters:
            username (str): The username of the target user on Likee.

        Returns:
            str or None: The user's unique identifier (uid) if found,
                or returns None if the uid cannot be retrieved.

        Example:
            uid = api.get_user_id('example_username')
            print(uid)
        """
        # Get user's profile page
        response = self.driver.get(f'https://likee.video/@{username}')
        self.pause()
        # Try to click on first video on page
        try:
            first_vid = self.driver.find_element(By.XPATH,
                                                 '//div[@class="card-video poster-bg"]')
            first_vid.click()
        except Exception as e:
            print('Unable to get user id, no user videos found')
            print('Exception: ', e)
            return None

        self.pause()
        # Get current url (i.e. first video) and extract user data using regex
        response = requests.get(self.driver.current_url,
                                headers=self.json_headers)
        regex_pattern = re.compile('window.data = ({.*?});')
        str_data = regex_pattern.search(response.text).group(1)
        json_data = json.loads(str_data)

        return json_data['poster_uid']

    def get_user_info(self, user_id):
        """
        Retrieves detailed information about a user based on their
        unique identifier (uid).

        This method sends a POST request to the Likee API's user
        information endpoint to fetch details about the user. Note that the
        Likee API might return 'null' for some fields, indicating that the
        information is not available or not provided by the user.

        Parameters:
            user_id (str): The unique identifier (uid) of the user on Likee.

        Returns:
            dict: A dictionary containing the user's information.
        """
        payload = {
            'uid': user_id
        }
        response = self.make_post_request(payload, self.user_info_endpoint)
        return response['data']

    def get_user_videos(self, user_id, limit=10, last_post_id='', videos=[]):
        """
        Retrieves a list of videos uploaded by a user based on
        their unique identifier (uid).

        This method sends a POST request to the Likee API's user videos
        endpoint to fetch the videos uploaded by the user. It uses recursion
        to paginate through the results and fetch the desired number of
        videos specified by the `limit` parameter.

        Parameters:
            user_id (str): The unique identifier (uid) of the Likee user.
            limit (int, optional): The maximum number of videos to retrieve.
                Default is 10.
            last_post_id (str, optional): The post ID of the last video
                fetched in the previous request. Used for pagination.
                Default is an empty string.
            videos (list, optional): A list to store the fetched videos.
                Used internally for recursion. Default is an empty list.

        Returns:
            list: A list of dictionaries, each representing a video
            uploaded by the user. The structure and fields of these
            dictionaries depend on the Likee API's response.

        Example:
            user_videos = api.get_user_videos('12345', limit=20)
            for video in user_videos:
                print(video['likeeId'], video['videoUrl'])
        """
        payload = {
            'country': self.country,
            'count': 100,
            'page': 1,
            'pageSize': 28,
            'lastPostId': last_post_id,
            'tabType': 0,
            'uid': user_id
        }
        response = self.make_post_request(payload, self.user_vids_endpoint)
        videos.extend(response['data']['videoList'])

        if len(videos) < limit and len(response) > 0:
            self.pause()
            last_id = videos[-1]['postId']
            # Use recursion to get desired amount of videos
            return self.get_user_videos(user_id, limit,
                                        last_post_id=last_id,
                                        videos=videos)
        else:
            return videos[:limit]

    def get_user_post_count(self, user_id):
        """
        Returns the user's post count from the API.

        Parameters:
            user_id (str): The unique identifier (uid) of the Likee user.

        Returns:
            dict: A dictionary containing the user's post counts.
        """
        payload = {
            'country': self.country,
            'tabType': 0,
            'uid': user_id
        }
        response = self.make_post_request(payload,
                                          self.user_post_count_endpoint)
        counts = response['data']['postInfoMap'][user_id]
        return counts

    def get_trending_videos(self,
                            limit=30,
                            start=0,
                            last_post_id=0,
                            video_list=[]):
        """
        Retrieves a list of trending videos from the Likee platform.

        This method sends a POST request to the Likee API's trending
        videos endpoint to fetch the most popular videos. It uses recursion
        to paginate through the results and fetch the desired number of
        videos specified by the `limit` parameter.

        Parameters:
            limit (int, optional): The maximum number of trending videos
                to retrieve. Default is 30.
            start (int, optional): The starting number for pagination.
                Default is 0.
            last_post_id (int, optional): The post ID of the last video
                fetched in the previous request. Used for pagination.
                Default is 0.
            video_list (list, optional): A list to store the fetched videos.
                Typically used internally for recursion. Default is an
                empty list.

        Returns:
            list: A list of dictionaries, each representing a trending video.
            The structure and fields of these dictionaries depend on the
            Likee API's response.

        Example:
            trending_videos = api.get_trending_videos(limit=50)
            for video in trending_videos:
                print(video['title'], video['url'])
        """
        payload = {
            'scene': 'WELOG_POPULAR',
            'fetchNum': 30,
            'startNum': start,
            'lastPostId': last_post_id,
            'language': self.language,
            'country': self.country,
            'deviceId': '1',
            'uid': 1,
        }
        response = self.make_post_request(payload, self.trending_vids_endpoint)
        video_list.extend(response['data']['videoList'])

        if len(video_list) < limit:
            self.pause()
            last_id = video_list[-1]['postId']
            return self.get_trending_videos(limit=limit,
                                            last_post_id=last_id,
                                            video_list=video_list)
        else:
            return video_list[:limit]

    def get_trending_hashtags(self, limit=20, page=1, hashtags=[]):
        """
        Retrieves a list of trending hashtags from the Likee platform
        based on country and language.

        This method sends a POST request to the Likee API's trending
        hashtags endpoint to fetch the most popular hashtags. It uses
        recursion to paginate through the results and fetch the desired
        number of hashtags specified by the `limit` parameter.

        Parameters:
            limit (int, optional): The maximum number of trending hashtags
                to retrieve. Default is 20.
            page (int, optional): The page number for pagination.
                Default is 1.
            hashtags (list, optional): A list to store the fetched hashtags.
                Used internally for recursion. Default is an empty list.

        Returns:
            list: A list of dictionaries, each representing a trending
            hashtag. The structure and fields of these dictionaries depend
            on Likee API's response.
        """
        payload = {
            'pagesize': 20,
            'page': page,
            'language': self.language,
            'country': self.country
        }
        response = self.make_post_request(payload,
                                          self.trending_hashtags_endpoint,
                                          content_type='form')
        hashtags.extend(response['data']['eventList'])

        if len(hashtags) < limit and len(response['data']['eventList']) > 0:
            self.pause()
            return self.get_trending_hashtags(limit=limit,
                                              page=page+1,
                                              hashtags=hashtags)
        return hashtags[:limit]

    def get_hashtag_videos(self, hashtag_id, limit=50, page=1, videos=[]):
        """
        Retrieves a list of popular videos associated with a specific
        hashtag from the Likee platform.

        This method sends a POST request to the Likee API's hashtag
        videos endpoint to fetch videos associated with the given
        hashtag ID. It uses recursion to paginate through the results
        and fetch the desired number of videos specified by the `limit`
        parameter.

        Parameters:
            hashtag_id (str): The unique identifier of the target
                hashtag on Likee.
            limit (int, optional): The maximum number of videos to
                retrieve for the given hashtag. Default is 50.
            page (int, optional): The page number for pagination.
                Default is 1.
            videos (list, optional): A list to store the fetched videos.
                Used internally for recursion. Default is an empty list.

        Returns:
            list: A list of dictionaries, each representing a video
            associated with the hashtag. The structure and fields of
            these dictionaries depend on the Likee API's response.
        """
        payload = {
            'topicId': hashtag_id,
            'pageSize': 50,
            'page': page,
            'country': self.country,
        }
        response = self.make_post_request(payload,
                                          self.hashtag_vids_endpoint,
                                          content_type='form')
        videos.extend(response['data']['videoList'])
        if len(videos) < limit:
            self.pause()
            return self.get_hashtag_videos(hashtag_id,
                                           limit=limit,
                                           page=page+1,
                                           videos=videos)

        return videos[:limit]

    def get_video_comments(self, video_url, limit=10):
        """
        Retrieves a list of comments from a specified video URL on
        the Likee platform.

        This method navigates to the provided video URL, clicks on
        the video to view its comments, and then scrolls through the
        comments section to fetch the desired number of comments
        specified by the `limit` parameter. The method handles
        pagination by scrolling and fetching comments until the desired
        limit is reached or there are no more comments.

        Parameters:
            video_url (str): The URL of the target video on Likee.
            limit (int, optional): The maximum number of comments to
                retrieve for the given video. If the video has fewer
                comments than the specified limit, all available comments
                will be fetched. Default is 10.

        Returns:
            list: A list of dictionaries, each representing a comment.
                Each dictionary contains the following keys:
                - 'username': The username of the commenter.
                - 'comment_text': The text content of the comment.
                - 'time': The timestamp of the comment.
                - 'like_count': The number of likes the comment received.
        """
        # Open the url and click on image to view comments
        self.driver.get(video_url)
        self.pause()
        self.driver.find_elements(By.CLASS_NAME,
                                  'video-card')[0].click()
        self.pause()
        # Getting the number of total comments from the url
        comments_count = self.driver.find_element(By.XPATH,
                                                  '/html/body/div[2]/div[2]/div[1]/div/div[3]/div[1]/div[3]/span[2]')
        comments_count = comments_count.text.split()[0]
        if comments_count[-1] == 'K':
            num_comments = int(float(comments_count[:-1])) * 1000
        else:
            num_comments = int(comments_count)

        # Limit should be set to num_comments if this is less than limit
        limit = min(limit, num_comments)

        # Locate the comments as seperate elements
        elements = self.driver.find_elements(By.CLASS_NAME,
                                             'comment-item')
        # Use actions to move the cursor to first element,
        # (to be used for scrolling down)
        actions = ActionChains(self.driver)
        actions.move_to_element(elements[0])
        actions.perform()
        last_elem = elements[-1]

        comments_arr = []
        # Use a while loop to update elements until it reaches the limit
        while len(elements) < limit:
            self.driver.execute_script('arguments[0].scrollIntoView();',
                                       last_elem)
            self.pause()
            elements = self.driver.find_elements(By.CLASS_NAME,
                                                 'comment-item')
            # Update last_elem variable
            if last_elem == elements[-1]:
                # If reached the end of comments, break
                break

            last_elem = elements[-1]

        # Iterate through each comment and append to comment_arr
        for elem in elements[:limit]:
            try:  # Handle cases where comment text is not present
                text = elem.find_element(By.CLASS_NAME,
                                         'msg_min').text
            except Exception:
                text = ''
            like_count = elem.find_element(By.CLASS_NAME,
                                           'like-count').text
            try:  # Handle cases where comment has no likes
                like_count = int(like_count)
            except Exception:
                like_count = 0

            comments_arr.append({
                    'username': elem.find_element(By.CLASS_NAME,
                                                  'nickname').text,
                    'comment_text': text,
                    'time': elem.find_element(By.CLASS_NAME,
                                              'time').text,
                    'like_count': like_count,
                })

        return comments_arr

    def download_video(self, video_url, filepath):
        """
        Downloads a video from the specified URL and saves it to the
        given filepath.

        This method fetches the video content from the provided URL and
        writes it to a file at the specified filepath. Before downloading,
        the method modifies the URL to remove any watermark that might be
        present in the video. If the video download request times out, an
        error message is printed, and the method returns without saving
        the video.

        Parameters:
            video_url (str): The URL of the target video on Likee.
            filepath (str): The path (including filename and extension)
                where the video should be saved.

        Returns:
            None: The method saves the video to the specified filepath but
            does not return any value.

        Raises:
            None: Errors, such as timeouts, are handled internally by
                printing error messages, but no exceptions are raised
                to the caller.
        """
        # Removing '_4' from url to ensure the watermark is not present
        video_url = video_url.replace('_4', '')
        try:
            # Timeout raised if video download takes too long
            video = requests.get(video_url,
                                 headers=self.json_headers,
                                 timeout=self.timeout)
        except requests.exceptions.Timeout:
            print('Timeout error downloading video: ', video_url)
            return

        with open(filepath, 'wb') as f:
            f.write(video.content)
