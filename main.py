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


def run_scrape(number_of_posts) -> list:
    login()
    # image_urls = get_image_urls(10)
    urls = set(get_image_urls(number_of_posts))
    post_data = []

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
            urls.discard(url)
            urls.add(get_image_urls(1)[0])

    for index, element in enumerate(post_data):
        logging.debug(f'Item {index+1}: {element}')

    return post_data


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


def get_image_urls(requested=100):
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


def get_image_data(soup: BeautifulSoup) -> dict:
    """

    :return:
        data = {
                post: {a: test.html, b: 2, c: 3, d: 4, e: 5, f: 6},
                post1: {a: test.html, b: 2, c...}
        }
    """
    rv = {}
    script = soup.find_all('script')[19].contents[0]
    script_load = script[script.find('{'):-2]
    json_data = json.loads(script_load)

    rv['link'] = json_data['graphql']['shortcode_media']['shortcode']
    rv['user'] = json_data['graphql']['shortcode_media']['owner']['username']
    rv['date_seen'] = date.today()
    rv['date_posted'] = date.fromtimestamp(json_data['graphql']['shortcode_media']['taken_at_timestamp'])
    rv['is_video'] = json_data['graphql']['shortcode_media']['is_video']
    rv['likes'] = json_data['graphql']['shortcode_media']['edge_media_preview_like']['count']
    try:
        rv['views'] = json_data['graphql']['shortcode_media']['video_view_count']
    except KeyError:
        rv['views'] = None
    rv['comments'] = json_data['graphql']['shortcode_media']['edge_media_to_parent_comment']['count']
    rv['liked'] = json_data['graphql']['shortcode_media']['viewer_has_liked']
    rv['is_seen'] = is_seen()
    rv['tag_count'] = len(get_tags(soup))
    rv['from_explore'] = True
    rv['from_liked'] = False
    rv['is_ad'] = json_data['graphql']['shortcode_media']['is_ad']
    return rv


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


# ! Depreciated temporarily
def get_soup(url) -> BeautifulSoup:
    rv = requests.get(url)
    if rv.ok:
        soup = BeautifulSoup(rv.text, 'html.parser')
    else:
        raise ConnectionError(f'Unable to connect to {url}')
    return soup


# ! Depreciated temporarily
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
    # users_to_scrape = ['axndr', 'emilycupples', '_theblessedone', 'reddogpizza', 'rei']
    with webdriver.Chrome(PATH) as ig_driver:
        # rv = run_scrape(3)
        login()
        test = get_image_urls(10)
        print(test)
        pass
