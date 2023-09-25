import os
import tempfile
import unittest

from LikeeScraper.api import API


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.api = API(pause_time=4)

        self.username = 'ulvaatkins'
        self.user_id = '1420839773'
        self.limit = 5
        self.hashtag_id = '6628875352397581241'
        self.hashtag_str = 'OutdoorID'
        self.video_page_url = 'https://likee.video/@HouseofB/video/7263259022822072270'
        self.video_data_url = 'https://video.like.video/eu_live/9u1/1KWxuO_4.mp4?crc=2299292943&type=5'

    def check_video_data(self, videos):
        self.assertEqual(len(videos), self.limit, msg='Invalid video limit')
        for video in videos:
            self.assertTrue(video['videoUrl'].startswith('https://'),
                            msg=f"Invalid URL: {video['videoUrl']}")

    def test_get_user_id(self):
        user_id = self.api.get_user_id(self.username)
        self.assertEqual(user_id, self.user_id)

    def test_get_user_info(self):
        user_info = self.api.get_user_info(self.user_id)
        self.assertEqual(user_info['userName'], self.username)

    def test_get_post_count(self):
        post_count = self.api.get_user_post_count(self.user_id)
        self.assertGreater(post_count['allLikeCount'], 0)

    def test_get_user_videos(self):
        videos = self.api.get_user_videos(self.user_id, limit=self.limit)
        self.check_video_data(videos)

    def test_get_trending_videos(self):
        videos = self.api.get_trending_videos(limit=self.limit)
        self.check_video_data(videos)

    def test_get_trending_hashtags(self):
        hashtags = self.api.get_trending_hashtags(limit=self.limit)

        # Check that the number of hashtags returned is equal to the limit
        self.assertEqual(len(hashtags), self.limit)

        # Check that each hashtag has a valid id
        for hashtag in hashtags:
            self.assertTrue(hashtag['eventId'].isdigit())

    def test_get_hashtag_videos(self):
        videos = self.api.get_hashtag_videos(self.hashtag_id, limit=self.limit)
        self.check_video_data(videos)

    def test_get_video_comments(self):
        comments = self.api.get_video_comments(self.video_page_url,
                                               limit=self.limit)

        # Check that the number of comments returned is equal to the limit
        self.assertEqual(len(comments), self.limit)

        # Check that each comment has valid text
        for comment in comments:
            self.assertIsInstance(comment['comment_text'], str)

    def test_download_video(self):
        # Create a temporary directory to download the video to
        with tempfile.TemporaryDirectory() as download_dir:
            filename = 'test_video.mp4'
            filepath = os.path.join(download_dir, filename)
            self.api.download_video(self.video_data_url, filepath)
            self.assertTrue(os.path.exists(filepath),
                            msg='Video was not downloaded')

    def tearDown(self):
        self.api.driver.quit()


if __name__ == '__main__':
    unittest.main()
