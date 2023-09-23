import re
import time
import json
import random
import urllib.parse
import os

import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import Firefox
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By


class API:
    """
    Main class for interacting with the Likee API
    """

    def __init__(self, country='US', language='en',
                 pause_time=3, headless=True):
        self.country = country
        self.language = language
        self.pause_time = pause_time

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
        A function to make all post requests to the API.
        content_type denotes the headers to be used, either
        json or url-form-encoded
        """
        if content_type == 'json':
            response = requests.post(endpoint,
                                     json=payload,
                                     headers=self.json_headers)
        else:
            response = requests.post(endpoint,
                                     data=payload,
                                     headers=self.form_headers)
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
        Returns the users id (uid) from username
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
        Gets the user's information using Likee API.
        N.B. This appears to return 'null' for most fields
        """
        payload = {
            'uid': user_id
        }
        response = self.make_post_request(payload, self.user_info_endpoint)
        return response['data']

    def get_user_videos(self, user_id, limit=10, last_post_id='', videos=[]):
        """
        Gets the user's uploaded videos and returns api json response.
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
        Returns the top 30 trending videos by default
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
        Get top hashtags by country/language.
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
        Returns most popular videos by hashtag_id
        within a country. Returns top 50 by default
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
        Gets the comments for specified video url
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
                # If same as before then break
                break

            last_elem = elements[-1]

        # Iterate through each comment and append to comment_arr
        for elem in elements:
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
        Downloads the video to the specified filepath.
        """
        # Removing '_4' from url to ensure the watermark is not present
        video_url = video_url.replace('_4', '')
        try:
            # Timeout after 10 seconds
            video = requests.get(video_url,
                                 headers=self.json_headers,
                                 timeout=10)
        except requests.exceptions.Timeout:
            print('Timeout error downloading video: ', video_url)
            return

        with open(filepath, 'wb') as f:
            f.write(video.content)


if __name__ == '__main__':
    # Dictionary to store configuration settings
    config = {
        'download_dir': '/home/stephen/Projects/likee/videos/',
        'country': 'US',
        'language': 'en'
    }

    def download_response(response):
        # Iterate through each video and download & save
        for item in response:
            video_url = item['videoUrl']
            filename = f"{item['likeeId']}_{item['postId']}.mp4"
            filepath = os.path.join(config['download_dir'], filename)

            print('Downloading: ', filepath)
            api.download_video(video_url, filepath)

    api = API(country='UK', language='en', headless=False)

    # Test user id from username
    user_id = api.get_user_id('ulvaatkins')
    print('User id: ', user_id)  # 1420839773