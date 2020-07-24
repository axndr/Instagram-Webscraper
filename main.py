import requests
import json
from types import SimpleNamespace
from bs4 import BeautifulSoup
from person import Person

insta_url = 'https://www.instagram.com'


def dict_to_namespace(d):
    return SimpleNamespace(**d)


def get_follower_count(username: str) -> int:
    response = requests.get(f'{insta_url}/{username}')

    if response.ok:
        soup = BeautifulSoup(response.text, 'html.parser')
    else:
        raise ConnectionError(f'Unable to connect to {insta_url}')

    a = soup.find('script', {'type': 'application/ld+json'}).decode_contents()
    data = (a[a.find('{'):]).strip(';')
    profile_data = json.loads(data)
    follower_count = profile_data['mainEntityofPage']['interactionStatistic']['userInteractionCount']
    return follower_count


def get_followers(username: str) -> int:
    response = requests.get(f'{insta_url}/{username}')

    if response.ok:
        soup = BeautifulSoup(response.text, 'html.parser')
    else:
        raise ConnectionError(f'Unable to connect to {insta_url}')

    all_scripts = soup.find_all('script', {'type': 'text/javascript'})
    script = all_scripts[3].decode_contents()
    data = (script[script.find('{'):]).split(';')[0]
    profile_data = json.loads(data)
    followers = profile_data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_followed_by']['count']
    return followers


# def profile_information(username: str):
#     response = requests.get(f'{insta_url}/{username}')
#
#     if response.ok:
#         soup = BeautifulSoup(response.text, 'html.parser')
#     else:
#         raise ConnectionError(f'Unable to connect to {insta_url}')
#
#     all_scripts = soup.find_all('script', {'type': 'text/javascript'})
#     script = all_scripts[3].decode_contents()
#     data = (script[script.find('{'):]).split(';')[0]
#     data = json.loads(data)
#     data = data['entry_data']['ProfilePage'][0]['graphql']['user']
#     profile_data = json.load(json.dumps(data), object_hook=dict_to_namespace)
#
#     json_data = json.loads(data)
#     json_data = json.loads(data)
#
#     profile_data = json.load(json_data['entry_data']['ProfilePage'][0]['graphql']['user'], object_hook=dict_to_namespace)
#     return profile_data


if __name__ == '__main__':
    users = ['axndr', 'emilycupples', '_theblessedone', 'reddogpizza']

    for user in users:
        print(f'{user} has {get_followers(user)} followers!')
