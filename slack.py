import requests
import json

from requests_toolbelt import MultipartEncoder


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


def upload_emoji(token, emojiname, filepath, dryrun=False):
    mp_encoder = MultipartEncoder(
        fields={
            'mode': 'data',
            'image': (filepath, open(filepath, 'rb'), 'form-data'),
            'name': emojiname
        }
    )
    h = {
        "Authorization": "Bearer " + token,
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
        "content-type": mp_encoder.content_type
    }
    if dryrun:
        return {'ok': True}
    else:
        initial_listing_response = requests.post("https://slack.com/api/emoji.add", headers=h, data=mp_encoder)
        return json.loads(initial_listing_response.content)