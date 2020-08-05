import json
import requests
from bs4 import BeautifulSoup


class_map = {
    'username': 'user',
    # 'full_name':
    'follower_count': 'followers',
    'edge_mutual_followed_by': 'edge_followers',
    'following': 'following',
    'following_me': 'following_me',
    'is_verified': 'verified',
    # 'connected_fb_page':
    'has_requested_viewer': 'requested_me',
    'is_business_account': 'is_business_account',
    # 'is_joined_recently':
    # 'business_category_name':
    # 'category_enum':
    'requested_by_viewer': 'requested',
}


class Profile:
    """
    User data scraped from given profile using BeautifulSoup

    example:
    > profile_1 = Profile('axndr')
    > print(profile_1)  # prints using custom __repr__
    > print(profile_1.full_name)

    ~ 'Profile axndr has 222 followers'
    ~ 'alex'
    """
    def __init__(self, user):
        """

        :param user:
        """
        response = requests.get(f'https://www.instagram.com/{user}')
        if response.ok:
            soup = BeautifulSoup(response.text, 'html.parser')
        else:
            raise ConnectionError(f'Unable to connect to Instagram profile page')

        all_scripts = soup.find_all('script', {'type': 'text/javascript'})
        script = all_scripts[3].decode_contents()
        json_string = (script[script.find('{'):]).split(';')[0]
        d = json.loads(json_string)
        profile_data = d['entry_data']['ProfilePage'][0]['graphql']['user']
        self.id = profile_data['id']
        self.username = profile_data['username']
        self.full_name = profile_data['full_name']
        self.follower_count = profile_data['edge_followed_by']['count']
        self.edge_mutual_followed_by = profile_data['edge_mutual_followed_by']
        self.following = profile_data['followed_by_viewer']
        self.following_me = profile_data['follows_viewer']
        self.is_verified = profile_data['is_verified']
        self.connected_fb_page = profile_data['connected_fb_page']
        self.has_requested_viewer = profile_data['has_requested_viewer']
        self.is_business_account = profile_data['is_business_account']
        self.is_joined_recently = profile_data['is_joined_recently']
        self.business_category_name = profile_data['business_category_name']
        self.category_enum = profile_data['category_enum']
        self.requested_by_viewer = profile_data['requested_by_viewer']

        self.blocked_by_viewer = profile_data['blocked_by_viewer']
        self.has_blocked_viewer = profile_data['has_blocked_viewer']
        self.restricted_by_viewer = profile_data['restricted_by_viewer']
        self.is_private = profile_data['is_private']

    def __repr__(self):
        return f'{self.username} has {self.follower_count} followers'

    def get_info(self):
        pass

    def get_view_status(self) -> bool:
        """
        blocked_by_viewer
        restricted_by_viewer
        country_block
        :param self:
        :return:
        """
        pass

    def relationship(self):
        """
        has_blocked_viewer
        has_requested_viewer
        :return:
        """
        pass
