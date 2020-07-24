import requests
import json
from bs4 import BeautifulSoup
from profile import Profile


instagram_url = 'https://www.instagram.com'


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
    users_to_scrape = ['axndr', 'emilycupples', '_theblessedone', 'reddogpizza', 'rei']
