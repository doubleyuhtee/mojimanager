import requests
import json


def emoji_listing(token):
    initial_listing_response = requests.get("https://slack.com/api/emoji.list?token=" + token)
    if initial_listing_response.status_code == 200:
        return json.loads(initial_listing_response.content)['emoji']
    return None


def user_listing(token):
    initial_listing_response = requests.get("https://slack.com/api/users.list?token=" + token)
    if initial_listing_response.status_code == 200:
        return json.loads(initial_listing_response.content)['members']
    return None