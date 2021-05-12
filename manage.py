import requests
import json
import shutil
import time
import os
import sys
import argparse

from PIL import Image

import generate
import tokenmanager
import slack

from requests_toolbelt.multipart.encoder import MultipartEncoder

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".mng")

argument_parser = argparse.ArgumentParser(description="Slackmoji manager")
tokenmanager.add_command_args(argument_parser)
argument_parser.add_argument("--collect", action='store_true',
                             help="Collect emojis to a folder", required=False)
argument_parser.add_argument("--create", action='store',
                             help="Folder to upload emojis from using the file name as the name", required=False)
argument_parser.add_argument("--batch_size", action='store', default=8, type=int,
                             help="Number of files to upload before sleeping to avoid rate limit.  Used with --create, (optional, default 8)", required=False)
argument_parser.add_argument("--dryrun", action='store_true', required=False, help="Dryrun", default=False)
argument_parser.add_argument("--recursive", "-r", action='store_true', required=False, help="search recursively from the given directory for images to create", default=False)

argument_parser.add_argument("--approve", action='store',
                             help="Search term to find the user image and create an approve emoji", required=False)
argument_parser.add_argument("--push", action='store_true', required=False, help="Upload the new approve emoji instead of just creating it", default=False)



class ProgressBar:
    loading_bars = "▁▂▃▄▅▆▇█"

    def __init__(self, elements):
        self.step_size = int(elements / 800)
        self.loading = [" " for i in range(100)]
        self.loading_bar_position = 0
        self.curr = 0

    def progress(self, suffix=""):
        self.curr += 1
        if self.curr % self.step_size == 0:
            if self.curr/self.step_size == 8:
                self.loading_bar_position += 1
                self.curr = 0
            if self.loading_bar_position < len(self.loading):
                display_char_index = int(self.curr/self.step_size)
                if display_char_index < 0:
                    display_char_index = 0
                if display_char_index > len(self.loading_bars):
                    display_char_index = len(self.loading_bars) - 1
                self.loading[self.loading_bar_position] = self.loading_bars[display_char_index]
        print("\x1b[1K\r[" + "".join(self.loading) + "]" + suffix, end="")


if __name__== "__main__":
    if len(sys.argv) < 2:
        argument_parser.print_help()
        exit(0)

    args = argument_parser.parse_args(sys.argv[1:])

    token = tokenmanager.get_token(args.workspace, args.token, args.configfile)
    if not token:
        exit(1)

    emojimap = slack.emoji_listing(token)

    alias_list = {}
    if emojimap:
        print(str(len(emojimap.keys())) + " existing emoji")

        if not (args.collect or args.create or args.approve):
            print("Requires create with folder path, collect arg, or approve with search term")
            exit(1)

        if args.approve:
            users = slack.user_listing(token)
            print(json.dumps(users[1], indent=2))
            approveTarget = args.approve.lower()
            target_user = [u for u in users if u['id'].lower() == approveTarget or
                           u['profile']['real_name_normalized'].lower() == approveTarget or
                           u['profile']['display_name_normalized'].lower() == approveTarget]
            if len(target_user) != 1:
                print("Unable to find user")
                print(json.dumps(target_user))
                exit(1)
            print(json.dumps(target_user, indent=2))
            print(target_user[0]['profile'])
            im = Image.open(requests.get(target_user[0]['profile']['image_192'], stream=True).raw)
            name = target_user[0]['profile']['display_name_normalized']
            if not name or len(name) == 0:
                name = target_user[0]['profile']['real_name_normalized']
            result = generate.approves((name + '.png').lower(), im)
            if args.push:
                responsepayload = slack.upload_emoji(token, result['name'], result['path'], args.dryrun)

        if args.collect:
            if not os.path.exists("data/"):
                os.mkdir("data/")
            if not os.path.exists("data/" + args.workspace):
                os.mkdir("data/" + args.workspace)
            if not os.path.exists("data/" + args.workspace + "/emojis"):
                os.mkdir("data/" + args.workspace + "/emojis")

            with open("data/" + args.workspace + "/" + str(int(time.time())), "w") as listing:
                listing.write(json.dumps(emojimap, sort_keys=True, indent=4))
            with open("data/" + args.workspace + "/keys" + str(int(time.time())), "w") as listing:
                l = list(emojimap.keys())
                l.sort()
                listing.write(json.dumps(l, sort_keys=True, indent=4))
            progress_bar = ProgressBar(len(emojimap.keys()))
            for x in emojimap.keys():
                progress_bar.progress(x)
                if emojimap[x].startswith("alias:"):
                    alias_list[x] = emojimap[x]
                else:
                    ext = emojimap[x][-3:]
                    location = "data/" + args.workspace + "/emojis/" + x + "." + ext
                    if not os.path.exists(location):
                        if not args.dryrun:
                            imageresponse = requests.get(emojimap[x], stream=True)
                            file = open(location, "wb")
                            imageresponse.raw.decode_content = True
                            # Copy the response stream raw data to local image file.
                            shutil.copyfileobj(imageresponse.raw, file)
            print("")
            print(json.dumps(alias_list))

        if args.create:
            count = 0
            total_mismatch = 0
            failure_map = {}
            total_fail_count = 0
            batch_size = int(args.batch_size)
            batch_remaining = batch_size
            calculated_path = os.path.join(args.create, "")
            emoji_files = {}
            if args.recursive:
                for dirpath, dirs, filenames in os.walk(calculated_path):
                    for filename in filenames:
                        emojiname = filename.split('.')[0]
                        if filename.endswith(IMAGE_EXTENSIONS) and not (emojiname in emojimap) and not (emojiname in emoji_files):
                            emoji_files[emojiname] = os.path.join(dirpath, filename)
                            total_mismatch += 1
            else:
                for filename in os.listdir(calculated_path):
                    emojiname = filename.split('.')[0]
                    if filename.endswith(IMAGE_EXTENSIONS) and not emojiname in emojimap and not emojiname in emoji_files:
                        emoji_files[emojiname] = os.path.join(calculated_path, filename)
                        total_mismatch += 1
            print(emoji_files)
            for emojiname, filepath in emoji_files.items():

                if not emojiname == "" and not emojiname in emojimap:
                    responsepayload = slack.upload_emoji(token, emojiname, filepath, args.dryrun)
                    batch_remaining -= 1
                    if not responsepayload['ok']:
                        if not responsepayload['error'] in failure_map:
                            failure_map[responsepayload['error']] = 0
                        total_fail_count += 1
                        failure_map[responsepayload['error']] += 1
                        print(filename + " " + emojiname)
                        print("not okay, sleeping")
                        print('\033[93m' + responsepayload['error'] + '\033[0m')
                        time.sleep(5)
                    else:
                        count += 1
                        print(str(count) + "/" + str(total_mismatch - total_fail_count) + " " + emojiname)
                    if batch_remaining == 0:
                        print('\033[34mshhhh... sleeeping\033[0m')
                        time.sleep(10)
                        batch_remaining = batch_size
            print('\033[92m' + str(count) + "/" + str(total_mismatch) + '\033[0m success \033[31m' + str(total_fail_count) + " failed\033[0m")
            print(json.dumps(failure_map, sort_keys=True, indent=4))
    else:
        print("Fail?")