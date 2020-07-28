import requests
import json
from itertools import count
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from profile import Profile

PATH = "C:\\Program Files (x86)\\chromedriver_win32\\chromedriver.exe"
instagram_url = 'https://www.instagram.com'
explore_page_url = 'https://www.instagram.com/explore/grid/?is_prefetch=false&omit_cover_media=false&module=explore_popular&use_sectional_payload=true&cluster_id=explore_all%3A0&include_fixed_destinations=true&max_id='


def check_page_load():
    sleep(5)


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


def login():
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


def get_image_urls(requested=100, rv=[]) -> list:
    if len(rv) < requested:
        ig_driver.get(f'https://www.instagram.com/explore')
        check_page_load()
        # if ig_driver.current_url != 'https://www.instagram.com/explore':
        #     raise ConnectionError('Did not connect to explore page, quitting early')

        explore_soup = BeautifulSoup(ig_driver.page_source, 'html.parser')
        urls = explore_soup.find_all('a')

        for url in urls[:10]:
            if url.get('href')[:3] == '/p/':
                if len(rv) < requested:
                    rv.append(f'https://www.instagram.com{url.get("href")}')
                else:
                    break
            else:
                continue

        return rv


def get_tags(url, container=[]):
    ig_driver.get(url)
    soup = BeautifulSoup(ig_driver.page_source, 'html.parser')
    tags = soup.find_all('a', {'class': 'xil3i'})
    for tag in tags:
        container.append(tag.text)
    return container


if __name__ == '__main__':
    users_to_scrape = ['axndr', 'emilycupples', '_theblessedone', 'reddogpizza', 'rei']

    with webdriver.Chrome(PATH) as ig_driver:
        # TODO: turn login() function into context manager
        login()
        links = get_image_urls(10)
        ig_driver.get(links[1])
        pass