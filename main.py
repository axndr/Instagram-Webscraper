import requests
import json
from json.decoder import JSONDecodeError
import logging
import sqlalchemy
import psycopg2
from itertools import count
from time import sleep
from datetime import date, datetime, timezone
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from profile import Profile
from post import Post
from dotenv import load_dotenv
import os

load_dotenv()


logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=f'C:\\Users\\alexc\\OneDrive\Documents\\projects\\insta_scraper\\logs\\ig_scrape{datetime.now().strftime("%Y%m%d-%H%M%S")}.log',
    level=logging.INFO)

PATH = "C:\\Program Files (x86)\\chromedriver_win32\\chromedriver.exe"

chrome_options = Options()
# chrome_options.add_argument("--headless")

instagram_url = 'https://www.instagram.com'
explore_page_url = 'https://www.instagram.com/explore/grid/?is_prefetch=false&omit_cover_media=false&module=explore_popular&use_sectional_payload=true&cluster_id=explore_all%3A0&include_fixed_destinations=true&max_id='

connection_arguments = {
    'database': os.getenv('PG_DATABASE_NAME'),
    'host': os.getenv('PG_HOST'),
    'port': os.getenv('PG_PORT'),
    'user': os.getenv('PG_USER'),
    'password': os.getenv('PG_PASSWORD'),
}

post_types = {
    'link': 'str',
    'user': 'str',
    'date_seen': 'datetime.date',
    'date_posted': 'datetime.date',
    'likes': 'int',
    'comments': 'int',
    'liked': 'bool',
    'is_video': 'bool',
    'is_seen': 'bool',
    'tag_count': 'int',
    'from_explore': 'bool',
    'from_liked': 'bool',
    'is_ad': 'bool',
    'views': 'int',
    'tags': 'list',
}

user_types = {
    'username': 'str',
    'followers': 'int',
    'following': 'bool',
    'following_me': 'bool',
    'requested': 'bool',
    'requested_me': 'bool',
    'edge_followers': 'int',
    'verified': 'bool',
    'is_business_account': 'bool',
    'id': 'int',
    'full_name': 'str',
    'connected_fb_page': 'bool',
    'is_joined_recently': 'bool',
    'business_category_name': 'str',
    'category_enum': 'str',
    'blocked_by_viewer': 'bool',
    'has_blocked_viewer': 'bool',
    'restricted_by_viewer': 'bool',
    'is_private': 'bool',
}


def run_scrape(number_of_posts) -> tuple:
    with webdriver.Chrome(PATH, options=chrome_options) as ig_driver:
        login(ig_driver)

        logger.info('Getting Post Data')
        post_urls = get_image_urls(ig_driver, number_of_posts)
        post_data = get_image_data(ig_driver, post_urls)

        logger.info('Getting User Data')
        user_urls = get_user_urls(ig_driver, (post['username'] for post in post_data))
        user_data = get_user_data(ig_driver, user_urls)

        # TODO: Implement hashtag scrape in run_scrape()
        # tags = set((tag for tag in post['tags']) for post in post_data)
        # tag_data = get_tag_data(tags)

        return post_data, user_data


def login(ig_driver):
    """
    # TODO: turn login() function into context manager

    :return:
    """
    wait = WebDriverWait(ig_driver, 5)
    try:
        ig_driver.get('https://www.instagram.com')
        wait.until(EC.visibility_of_element_located((By.NAME, 'username')))
    except TimeoutError:
        raise TimeoutError('Timed out loading login page')

    username = ig_driver.find_element_by_name('username')
    username.send_keys(os.getenv('INSTAGRAM_USERNAME'))
    password = ig_driver.find_element_by_name('password')
    password.send_keys(os.getenv('INSTAGRAM_PASSWORD'))
    # check_page_load()
    try:
        password.send_keys(Keys.RETURN)
        wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="react-root"]/section/main/div/div/div/section/div/button')))
    except TimeoutError:
        raise TimeoutError('Timed out loading login page')


def db_login():
    try:
        connection = psycopg2.connect(
            # engine = os.getenv('PG_ENGINE'),
            database=os.getenv('PG_DATABASE_NAME'),
            host=os.getenv('PG_HOST'),
            port=os.getenv('PG_PORT'),
            user=os.getenv('PG_USER'),
            password=os.getenv('PG_PASSWORD'),
        )
        connection.autocommit = False
        cursor = connection.cursor()
        amount = 2500
    except psycopg2.DatabaseError:
        raise psycopg2.DatabaseError(f'Could not connect to {os.getenv("PG_DATABASE_NAME")}')

    cursor.execute('ALTER TABLE posts ADD COLUMN test VARCHAR(20);')
    yield

    cursor.execute('ALTER TABLE posts DROP COLUMN test')

    # closing database connection.
    if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")


def get_image_urls(ig_driver, requested=100) -> list:
    """

    :param requested:
    :return: List of urls to scrape
    """
    rv = []
    while len(rv) < requested:
        try:
            wait = WebDriverWait(ig_driver, 5)
            ig_driver.get('https://www.instagram.com/explore')
            wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="react-root"]/section/main/div/div[1]/div/div[5]')))
        except TimeoutError:
            raise TimeoutError('Timed out loading image page')

        # check_page_load()
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
    logger.info(f'Retrieved {len(rv)} post urls)')
    return rv


def get_user_urls(ig_driver, partial_user_urls: list) -> list:
    rv = []
    for element in partial_user_urls:
        rv.append(f'https://www.instagram.com/{element}')
    logger.info(f'Retrieved {len(rv)} user urls)')
    return rv


def get_image_data(ig_driver, urls) -> list:
    posts = []
    post = {}

    wait = WebDriverWait(ig_driver, 5)
    for index, url in enumerate(urls):
        # response = requests.get(url)
        # if response.ok:
        #     soup = BeautifulSoup(response.text, 'html.parser')
        # else:
        #     raise ConnectionError(f'Unable to connect to Instagram post')

        # ! Reimplementing Selenium for checking posts data
        try:
            logger.info(f'Getting Image #{index+1} at {url}')
            ig_driver.get(url)
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'sDN5V')))
        except TimeoutException:
            if ig_driver.find_element_by_class_name('dialog-404'):
                print('Saw 404 page, waiting 30 seconds')
                ig_driver.implicitly_wait(30)
            try:
                logger.warning(f'Retrying Image #{index+1} at {url} after 30 second pause')
                ig_driver.get(url)
                wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'sDN5V')))
            except TimeoutError:
                raise TimeoutError('Timed out retrying image page')
        except TimeoutError:
            raise TimeoutError('Timed out loading image page')

        soup = BeautifulSoup(ig_driver.page_source, 'html.parser')

        json_data = get_post_script(soup)

        post['link'] = str(json_data['graphql']['shortcode_media']['shortcode'])
        post['username'] = str(json_data['graphql']['shortcode_media']['owner']['username'])
        post['date_seen'] = datetime.now(timezone.utc)
        post['date_posted'] = datetime.fromtimestamp(json_data['graphql']['shortcode_media']['taken_at_timestamp'], tz=timezone.utc)
        post['is_video'] = bool(json_data['graphql']['shortcode_media']['is_video'])
        post['likes'] = int(json_data['graphql']['shortcode_media']['edge_media_preview_like']['count'])
        post['comments'] = int(json_data['graphql']['shortcode_media']['edge_media_to_parent_comment']['count'])
        post['liked'] = bool(json_data['graphql']['shortcode_media']['viewer_has_liked'])
        post['is_seen'] = is_seen()
        post['tags'] = get_tags(soup).copy()
        post['from_explore'] = bool(True)
        post['from_liked'] = bool(False)
        post['is_ad'] = bool(json_data['graphql']['shortcode_media']['is_ad'])
        post['tag_count'] = len(post['tags'])
        try:
            post['views'] = int(json_data['graphql']['shortcode_media']['video_view_count'])
        except KeyError:
            post['views'] = 0
        posts.append(post.copy())
    return posts


def get_post_script(soup):
    """

    :param: index = 19 is due to 19 being the most common location for the script we're looking for
    :return:
    """
    rv = ""
    scripts = soup.find_all('script')

    # Script we're looking for is usually found around 18/19th index of 20ish
    for script in reversed(scripts):
        try:
            if script.contents[0][:29] == 'window.__additionalDataLoaded':
                rv = script.contents[0]
                break
        except IndexError:
            continue

    try:
        script_load = rv[rv.find('{'):].rsplit(')', maxsplit=1)[0]
        json_data = json.loads(script_load)
        return json_data
    except JSONDecodeError:
        raise JSONDecodeError


def is_seen() -> bool:
    # TODO: check database to see if post has been seen before
    return False


def get_tags(soup: BeautifulSoup) -> list:
    rv = []
    links = soup.find_all('a')
    for link in links:
        try:
            if link.text[0] == '#':
                rv.append(link.text)
        except IndexError:
            continue
    return rv


def get_user_data(ig_driver, urls) -> list:
    users = []
    user = {}

    wait = WebDriverWait(ig_driver, 5)
    for index, url in enumerate(urls):
        # response = requests.get(f'https://www.instagram.com/{url}')
        # if response.ok:
        #     soup = BeautifulSoup(response.text, 'html.parser')
        # else:
        #     raise ConnectionError(f'Unable to connect to Instagram profile page')

        # ! Reimplementing Selenium for checking posts data
        try:
            logger.info(f'Getting User #{index+1} at {url}')
            ig_driver.get(url)
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'sDN5V')))
        except TimeoutException:
            if ig_driver.find_element_by_class_name('dialog-404'):
                ig_driver.implicitly_wait(30)
            try:
                logger.warning(f'Retrying User #{index+1} at {url} after 30 second pause')
                ig_driver.get(url)
                wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'sDN5V')))
            except TimeoutError:
                raise TimeoutError('Timed out retrying user page')
        except TimeoutError:
            raise TimeoutError('Timed out loading user page')

        soup = BeautifulSoup(ig_driver.page_source, 'html.parser')
        json_data = get_user_script(soup)
        try:
            profile_data = json_data['entry_data']['ProfilePage'][0]['graphql']['user']
        except KeyError:
            raise KeyError

        user['id'] = int(profile_data['id'])
        user['username'] = str(profile_data['username'])
        user['full_name'] = str(profile_data['full_name'])
        user['followers'] = int(profile_data['edge_followed_by']['count'])
        user['following'] = bool(profile_data['followed_by_viewer'])
        user['following_me'] = bool(profile_data['follows_viewer'])  # ! Check on edge user script case
        user['requested'] = bool(profile_data['requested_by_viewer'])
        user['requested_me'] = bool(profile_data['has_requested_viewer'])  # ! Check on edge user script case
        user['edge_followers'] = int(profile_data['edge_mutual_followed_by']['count'])
        user['verified'] = bool(profile_data['is_verified'])
        user['is_business_account'] = bool(profile_data['is_business_account'])  # ! Check on edge user script case
        user['connected_fb_page'] = bool(profile_data['connected_fb_page'])  # ! Check on edge user script case
        user['is_joined_recently'] = bool(profile_data['is_joined_recently'])  # ! Check on edge user script case
        user['business_category_name'] = str(profile_data['business_category_name'])  # ! Check on edge user script case
        user['category_enum'] = str(profile_data['category_enum'])  # ! Check on edge user script case
        user['blocked_by_viewer'] = bool(profile_data['blocked_by_viewer'])
        user['has_blocked_viewer'] = bool(profile_data['has_blocked_viewer'])
        user['restricted_by_viewer'] = bool(profile_data['restricted_by_viewer'])
        user['is_private'] = bool(profile_data['is_private'])
        users.append(user.copy())
    return users


def get_user_script(soup):
    """

    :param soup:
    :return:
    """
    rv = ""
    scripts = soup.find_all('script', {'type': 'text/javascript'})

    for script in scripts:
        try:
            if script.contents[0][:31] == 'window._sharedData = {"config":':
                rv = script.contents[0]
                break
        except IndexError:
            continue

    try:
        script_load = (rv[rv.find('{'):]).rsplit(';', maxsplit=1)[0]
        if script_load[-1:] == ')':
            script_load = script_load[:-1]
        json_data = json.loads(script_load)
        return json_data
    except JSONDecodeError:
        raise JSONDecodeError


def upload_data(post_data, user_data):
    with psycopg2.connect(**connection_arguments) as conn:
        try:
            cur = conn.cursor()
            logger.info('Uploading User Data')
            upload_user_data(cur, user_data)
            logger.info('Uploading Post Data')
            upload_post_data(cur, post_data)
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)


def upload_post_data(cur, posts):
    for post in posts:
        (link, username, date_seen, date_posted, is_video, likes, comments, liked, is_seen, tags, from_explore,
         from_liked, is_ad, tag_count, views) = post.values()
        tags = build_tags(tags)
        logger.info(f'Uploading Post for {link}')
        # TODO: Implement date_seen and date_posted
        cur.execute(f"""INSERT INTO posts (link, username, likes, comments, liked, is_video, is_seen, tag_count, from_explore, from_liked, is_ad, views, tags) VALUES ('{link}', '{username}', {likes}, {comments}, {liked}, {is_video}, {is_seen}, {tag_count}, {from_explore}, {from_liked}, {is_ad}, {views}, '{tags}');""")


def upload_user_data(cur, users):
    for user in users:
        cur.execute(f"""SELECT username FROM users WHERE username='{user.get('username')}';""")
        if cur.fetchone() is None:
            (id, username, full_name, followers, following, following_me, requested, requested_me, edge_followers,
             verified, is_business_account, connected_fb_page, is_joined_recently, business_category_name, category_enum,
             blocked_by_viewer, has_blocked_viewer, restricted_by_viewer, is_private) = user.values()
            full_name = full_name.replace('\'', '')
            logger.info(f'Uploading User for {username}')
            cur.execute(f"""INSERT INTO users VALUES ('{username}', {followers}, {following}, {following_me}, {requested}, {requested_me}, {edge_followers}, {verified}, {is_business_account}, {id}, '{full_name}', {connected_fb_page}, {is_joined_recently}, '{business_category_name}', '{category_enum}', {blocked_by_viewer}, {has_blocked_viewer}, {restricted_by_viewer}, {is_private});""")
        else:
            logger.info(f'{user.get("username")} already exists')


def build_tags(tags) -> str:
    striped_tags = []
    for tag in tags:
        striped_tags.append(tag[:30])
    rv = json.dumps(striped_tags)
    rv = (rv.replace('[', '{')).replace(']', '}')
    return rv


if __name__ == '__main__':
    (post_data, user_data) = run_scrape(10)
    upload_data(post_data, user_data)
