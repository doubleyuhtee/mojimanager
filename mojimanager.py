import requests
import json
import shutil
import time
import os
import sys
import argparse

argument_parser = argparse.ArgumentParser(description="Slackmoji manager")
argument_parser.add_argument("--token", "-t", action='store', required=True)
argument_parser.add_argument("--workspace", "-w", action='store', required=False, default='default')

argument_parser.add_argument("--collect", action='store_true',
                             help="Collect emojis to a folder", required=False)
argument_parser.add_argument("--create", action='store',
                             help="Folder to upload emojis from using the file name as the name", required=False)

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
            for filename in os.listdir(args.create):
                emojiname = filename.split('.')[0]
                if not emojiname in emojimap:
                    print(emojiname)
                    h = {"Authorization": "Bearer " + args.token}
                    data = {'token': args.token, 'mode': 'data', 'name': emojiname, 'image': open(args.create + filename, 'rb').read()}
                    # TODO figure out why this form upload fails
                    response = requests.post("https://slack.com/api/emoji.add", headers=h, data=data)
                    print(response)
                    print(response.content)
                    exit(1)


    else:
        print("Fail?")