import requests
import json
import shutil
import time
import os
import sys
import argparse

from requests_toolbelt.multipart.encoder import MultipartEncoder


argument_parser = argparse.ArgumentParser(description="Slackmoji manager")
argument_parser.add_argument("--token", "-t", help="Api token, xoxs token required for upload. Grab it from your headers when uploading manually", action='store', required=True)
argument_parser.add_argument("--workspace", "-w", action='store', required=False, help="only used for creating folders", default='default')

argument_parser.add_argument("--collect", action='store_true',
                             help="Collect emojis to a folder", required=False)
argument_parser.add_argument("--create", action='store',
                             help="Folder to upload emojis from using the file name as the name", required=False)
argument_parser.add_argument("--batch_size", action='store', default=10,
                             help="Number of files to upload before sleeping to avoid rate limit.  Used with --create, optional", required=False)

if __name__== "__main__":
    if len(sys.argv) < 2:
        argument_parser.print_help()
        exit(0)

    args = argument_parser.parse_args(sys.argv[1:])
    if not (args.collect or args.create):
        print("Requires either create with folder path or collect arg")
    response = requests.get("https://slack.com/api/emoji.list?token=" + args.token)
    alias_list = {}
    if response.status_code == 200:
        emojimap = json.loads(response.content)['emoji']

        if args.collect:
            if not os.path.exists("data/" + args.workspace + "/emojis"):
                os.mkdir("data/" + args.workspace)
                os.mkdir("data/" + args.workspace + "/emojis")
            with open("data/" + args.workspace + "/" + str(int(time.time())), "w") as listing:
                listing.write(json.dumps(emojimap, sort_keys=True, indent=4))
            with open("data/" + args.workspace + "/keys" + str(int(time.time())), "w") as listing:
                l = list(emojimap.keys())
                l.sort()
                listing.write(json.dumps(l, sort_keys=True, indent=4))

            for x in emojimap.keys():
                if emojimap[x].startswith("alias:"):
                    alias_list[x] = emojimap[x]
                else:
                    ext =  emojimap[x][-3:]
                    location = "data/" + args.workspace + "/emojis/" + x + "." + ext
                    if not os.path.exists(location):
                        imageresponse = requests.get(emojimap[x], stream=True)
                        file = open(location, "wb")
                        imageresponse.raw.decode_content = True
                        # Copy the response stream raw data to local image file.
                        shutil.copyfileobj(imageresponse.raw, file)
            print(json.dumps(alias_list))

        if args.create:
            count = 0
            todo = 0
            batch_remaining = args.batch_size
            for filename in os.listdir(args.create):
                emojiname = filename.split('.')[0]
                if not emojiname in emojimap:
                    todo += 1
            for filename in os.listdir(args.create):
                emojiname = filename.split('.')[0]
                if not emojiname in emojimap:
                    mp_encoder = MultipartEncoder(
                        fields={
                            'mode': 'data',
                            'image': (filename, open(args.create + filename, 'rb'), 'form-data'),
                            'name': emojiname
                        }
                    )
                    h = {
                        "Authorization": "Bearer " + args.token,
                        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
                        "content-type": mp_encoder.content_type
                    }
                    response = requests.post("https://slack.com/api/emoji.add", headers=h, data=mp_encoder)
                    responsepayload = json.loads(response.content)
                    batch_remaining -= 1
                    if not responsepayload['ok']:
                        todo -= 1
                        print(emojiname)
                        print("not okay, sleeping")
                        print('\033[93m' + responsepayload['error'] + '\033[0m')
                        time.sleep(5)
                    else:
                        count += 1
                        print(str(count) + "/" + str(todo) + " " + emojiname)
                    if batch_remaining == 0:
                        print('\033[34mshhhh... sleeeping\033[0m')
                        time.sleep(10)
                        batch_remaining = args.batch_size


    else:
        print("Fail?")