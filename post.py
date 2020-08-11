import datetime
import json
import requests
from bs4 import BeautifulSoup

post_db = [
    'post_uuid',
    'link',
    'user',
    'date_seen',
    'date_posted',
    'likes',
    'comments',
    'liked',
    'is_video',
    'is_seen',
    'tag_count',
    'from_explore',
    'from_liked',
    'is_ad'
]


def get_tags(soup, container=[]):
    tags = soup.find_all('a', {'class': 'xil3i'})
    for tag in tags:
        container.append(tag.text)
    return container


def check_is_seen():
    """
    :return:
    """
    return False


class Post:
    def __init__(self, url):

        response = requests.get(f'https://www.instagram.com{url}')
        if response.ok:
            soup = BeautifulSoup(response.text, 'html.parser')
        else:
            raise ConnectionError(f'Unable to connect to Instagram profile page')


        all_scripts = soup.find_all('script', {'type': 'text/javascript'})
        script = all_scripts[19].decode_contents()
        json_string = (script[script.find('{'):]).split(';')[0]
        json_string = script[script.find('{'):].rsplit(')', 1)[0]
        d = json.loads(json_string)
        post_data = d['graphql']['shortcode_media']

        self.tags = get_tags(soup)

        self.link = url
        self.user = post_data['owner']['username']
        self.date_seen = datetime.datetime.now()
        self.date_posted = 'date_posted'
        self.likes = 'likes'
        self.comments = 'comments'
        self.liked = post_data['viewer_has_liked']
        self.is_seen = check_is_seen()
        self.tag_count = len(self.tags)
        # self.from_explore = 'from_explore'
        # self.from_liked = 'from_liked'
        self.is_video = post_data['is_video']
        self.is_ad = post_data['is_ad']

        # self.url =



