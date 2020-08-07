import requests
import json
from json.decoder import JSONDecodeError
import logging
from itertools import count
from time import sleep
from datetime import date
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from profile import Profile
from post import Post

logging.basicConfig(filename='ig_scrape_logs.log', level=logging.DEBUG)

PATH = "C:\\Program Files (x86)\\chromedriver_win32\\chromedriver.exe"
instagram_url = 'https://www.instagram.com'
explore_page_url = 'https://www.instagram.com/explore/grid/?is_prefetch=false&omit_cover_media=false&module=explore_popular&use_sectional_payload=true&cluster_id=explore_all%3A0&include_fixed_destinations=true&max_id='


def check_page_load():
    # TODO: turn check_page_load into() into an actual check
    sleep(5)

    # try:
    #     wait = WebDriverWait(ig_driver, 5)
    #     wait.until(EC.visibility_of_element_located((By.)))
    # except TimeoutError:
    #     raise TimeoutError('Timed out loading login page')


def run_scrape(number_of_posts) -> tuple:
    login()

    urls = get_image_urls(number_of_posts)
    post_data = get_image_data(urls)

    # set used because it gets rid of duplicates, commonly used in this script
    users = set((post['user'] for post in post_data))
    user_data = get_user_data(users)

    # TODO: Implement hashtag scrape in run_scrape()
    # tags = set((tag for tag in post['tags']) for post in post_data)
    # tag_data = get_tag_data(tags)

    return post_data, user_data


def login():
    """
    # TODO: turn login() function into context manager

    :return:
    """
    try:
        wait = WebDriverWait(ig_driver, 5)
        ig_driver.get('https://www.instagram.com')
        wait.until(EC.visibility_of_element_located((By.NAME, 'username')))
    except TimeoutError:
        raise TimeoutError('Timed out loading login page')

    username = ig_driver.find_element_by_name('username')
    username.send_keys('axndr')
    password = ig_driver.find_element_by_name('password')
    password.send_keys('dEq5A9qOrp0I')
    password.send_keys(Keys.RETURN)
    check_page_load()


def get_image_urls(requested=100) -> list:
    """

    :param requested:
    :return: List of urls to scrape
    """
    rv = []
    wait = WebDriverWait(ig_driver, 5)
    while len(rv) < requested:
        try:
            ig_driver.get('https://www.instagram.com/explore')
            wait.until(EC.visibility_of_all_elements_located((By.TAG_NAME, 'a')))
        except TimeoutError:
            raise TimeoutError('Timed out loading login page')

        check_page_load()
        # if ig_driver.current_url != 'https://www.instagram.com/explore':
        #     raise ConnectionError('Did not connect to explore page, quitting early')

        explore_soup = BeautifulSoup(ig_driver.page_source, 'html.parser')
        links = explore_soup.find_all('a')

        for link in links:
            url = link.get('href')
            if url[:3] == '/p/':
                if len(rv) < requested:
                    rv.append(f'https://www.instagram.com{url}')
                else:
                    break
            else:
                continue
    return rv


def get_image_data(urls) -> list:
    """
    TODO: Does a lot of work. Should this be broken up?


    :return:
        data = {
                post: {a: test.html, b: 2, c: 3, d: 4, e: 5, f: 6},
                post1: {a: test.html, b: 2, c...}
        }
    """
    post_data = []

    for index, url in enumerate(urls):
        logging.debug(f'Getting data for {index}: {url}')
        ig_driver.get(url)
        check_page_load()
        soup = BeautifulSoup(ig_driver.page_source, 'html.parser')

        try:
            script = soup.find_all('script')[19].contents[0]
            script_load = script[script.find('{'):-2]
            json_data = json.loads(script_load)
        except JSONDecodeError:
            # edge case for when soup the 19th script tag doesn't contain valid JSON
            try:
                script = soup.find_all('script')[18].contents[0]
                script_load = script[script.find('{'):-2]
                json_data = json.loads(script_load)
            except JSONDecodeError:
                # if there isn't valid JSON in index 18, grab a new URL
                logging.error(f'Replacing {url}, threw JSONDecodeError.')
                urls.pop(index)
                urls.append(get_image_urls(1)[0])
                continue

        rv = {
            'link': json_data['graphql']['shortcode_media']['shortcode'],
            'user': json_data['graphql']['shortcode_media']['owner']['username'], 'date_seen': date.today(),
            'date_posted': date.fromtimestamp(json_data['graphql']['shortcode_media']['taken_at_timestamp']),
            'is_video': json_data['graphql']['shortcode_media']['is_video'],
            'likes': json_data['graphql']['shortcode_media']['edge_media_preview_like']['count'],
            'comments': json_data['graphql']['shortcode_media']['edge_media_to_parent_comment']['count'],
            'liked': json_data['graphql']['shortcode_media']['viewer_has_liked'], 'is_seen': is_seen(),
            'tags': get_tags(soup),
            'from_explore': True,
            'from_liked': False,
            'is_ad': json_data['graphql']['shortcode_media']['is_ad']
        }

        rv['tag_count'] = len(rv['tags']),

        try:
            rv['views'] = json_data['graphql']['shortcode_media']['video_view_count']
        except KeyError:
            rv['views'] = None

        post_data.append(rv)

    return post_data


def is_seen() -> bool:
    # TODO: check database to see if post has been seen before
    return False


def get_tags(soup: BeautifulSoup, rv=[]) -> list:
    links = soup.find_all('a')
    for link in links:
        try:
            if link.text[0] == '#':
                rv.append(link.text)
        except IndexError:
            continue
    return rv


def get_user_data(users: set) -> list:
    rv = []
    data = {}

    for user in users:
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

        data['id'] = profile_data['id']
        data['username'] = profile_data['username']
        data['full_name'] = profile_data['full_name']
        data['followers'] = profile_data['edge_followed_by']['count']
        data['following'] = profile_data['followed_by_viewer']
        data['following_me'] = profile_data['follows_viewer']
        data['requested'] = profile_data['requested_by_viewer']
        data['requested_me'] = profile_data['has_requested_viewer']
        data['edge_followers'] = profile_data['edge_mutual_followed_by']['count']
        data['verified'] = profile_data['is_verified']
        data['is_business_account'] = profile_data['is_business_account']
        data['connected_fb_page'] = profile_data['connected_fb_page']
        data['is_joined_recently'] = profile_data['is_joined_recently']
        data['business_category_name'] = profile_data['business_category_name']
        data['category_enum'] = profile_data['category_enum']
        data['blocked_by_viewer'] = profile_data['blocked_by_viewer']
        data['has_blocked_viewer'] = profile_data['has_blocked_viewer']
        data['restricted_by_viewer'] = profile_data['restricted_by_viewer']
        data['is_private'] = profile_data['is_private']
        rv.append(data)
    return rv


# ! Depreciated, integrated into get_post_data()
def encode_json_post_data(urls) -> list:
    for index, url in enumerate(urls):
        logging.debug(f'Getting data for {index}: {url}')
        ig_driver.get(url)
        check_page_load()
        post_soup = BeautifulSoup(ig_driver.page_source, 'html.parser')

        try:
            post_data.append(get_image_data(post_soup))
            logging.debug(f'Post Data: {post_data[-1]}')
        except JSONDecodeError:
            logging.error(f'Replacing {url}, threw JSONDecodeError.')
            urls.pop(index)
            urls.append(get_image_urls(1)[0])

    return post_data


# ! Depreciated temporarily
# def get_tag_data(tags):
# TODO: Does this dataset need tags as a separate table? Can it not get gotten via joins on Posts?

#     rv = []
#     data = {}
#
#     for tag in tags:
#         response = requests.get(f'https://www.instagram.com/{tag}')
#         if response.ok:
#             soup = BeautifulSoup(response.text, 'html.parser')
#         else:
#             raise ConnectionError(f'Unable to connect to Instagram profile page')
#
#         all_scripts = soup.find_all('script', {'type': 'text/javascript'})
#         script = all_scripts[3].decode_contents()
#         json_string = (script[script.find('{'):]).split(';')[0]
#         d = json.loads(json_string)
#         profile_data = d['entry_data']['ProfilePage'][0]['graphql']['user']
#
#         data['id'] = profile_data['id']
#         data['username'] = profile_data['username']
#         data['full_name'] = profile_data['full_name']
#         data['followers'] = profile_data['edge_followed_by']['count']
#         data['following'] = profile_data['followed_by_viewer']
#         data['following_me'] = profile_data['follows_viewer']
#         data['requested'] = profile_data['requested_by_viewer']
#         data['requested_me'] = profile_data['has_requested_viewer']
#         data['edge_followers'] = profile_data['edge_mutual_followed_by']['count']
#         data['verified'] = profile_data['is_verified']
#         data['is_business_account'] = profile_data['is_business_account']
#         data['connected_fb_page'] = profile_data['connected_fb_page']
#         data['is_joined_recently'] = profile_data['is_joined_recently']
#         data['business_category_name'] = profile_data['business_category_name']
#         data['category_enum'] = profile_data['category_enum']
#         data['blocked_by_viewer'] = profile_data['blocked_by_viewer']
#         data['has_blocked_viewer'] = profile_data['has_blocked_viewer']
#         data['restricted_by_viewer'] = profile_data['restricted_by_viewer']
#         data['is_private'] = profile_data['is_private']
#         rv.append(data)
#     return rv

# ! Depreciated
def get_soup(url) -> BeautifulSoup:
    rv = requests.get(url)
    if rv.ok:
        soup = BeautifulSoup(rv.text, 'html.parser')
    else:
        raise ConnectionError(f'Unable to connect to {url}')
    return soup


# ! Depreciated, integrated into get_user_data()
def get_instagram_profile(username: str) -> Profile:
    """
    :param username:
    :return:
    """
    soup = get_soup(f'{instagram_url}/{username}')

    all_scripts = soup.find_all('script', {'type': 'text/javascript'})
    script = all_scripts[3].decode_contents()
    json_string = (script[script.find('{'):]).split(';')[0]
    d = json.loads(json_string)
    profile_data = d['entry_data']['ProfilePage'][0]['graphql']['user'].copy()
    rv = Profile(**profile_data)
    return rv


if __name__ == '__main__':
    with webdriver.Chrome(PATH) as ig_driver:
        (post_data, user_data) = run_scrape(2)
        pass
