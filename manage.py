import requests
import json
import shutil
import time
import os
import sys
import argparse
import configparser
from pathlib import Path

from requests_toolbelt.multipart.encoder import MultipartEncoder

CONFIG_FILE_NAME = ".mojimanjerconfig"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".mng")

argument_parser = argparse.ArgumentParser(description="Slackmoji manager")
argument_parser.add_argument("--token", "-t", help="Api token, xoxs token required for upload. Grab it from your headers when uploading manually", action='store', required=False)
argument_parser.add_argument("--workspace", "-w", action='store', required=False, help="Section from config to use and directory to output to")
argument_parser.add_argument("--collect", action='store_true',
                             help="Collect emojis to a folder", required=False)
argument_parser.add_argument("--create", action='store',
                             help="Folder to upload emojis from using the file name as the name", required=False)
argument_parser.add_argument("--batch_size", action='store', default=8, type=int,
                             help="Number of files to upload before sleeping to avoid rate limit.  Used with --create, (optional, default 8)", required=False)
argument_parser.add_argument("--configfile", action='store', required=False, help="Path to config file.  Defaults (~/.mojimanjerconfig)", default=os.path.join(Path.home(), CONFIG_FILE_NAME))
argument_parser.add_argument("--dryrun", action='store_true', required=False, help="Dryrun", default=False)
argument_parser.add_argument("--recursive", "-r", action='store_true', required=False, help="search recursively from the given directory for images to create", default=False)

if __name__== "__main__":
    if len(sys.argv) < 2:
        argument_parser.print_help()
        exit(0)

    args = argument_parser.parse_args(sys.argv[1:])
    token = None
    if args.token:
        token = args.token
    if args.workspace:
        print(args.configfile)
        config = configparser.ConfigParser()
        config.read(args.configfile)
        if args.workspace in config:
            token_name = "token" if "token" in config[args.workspace] else "create" if args.create else "fetch"
            token = config[args.workspace][token_name]

        if token:
            if args.workspace not in config:
                config[args.workspace] = {}
            if "token" not in config[args.workspace] or token != config[args.workspace]["token"]:
                config[args.workspace]["token"] = token
                with open(args.configfile, 'w') as configfileupdate:
                    config.write(configfileupdate)

    if not token and not args.workspace:
        config = configparser.ConfigParser()
        config.read(args.configfile)
        if "default" in config:
            token = config["default"]["token"]

    if not token:
        print("\nNo token found in " + args.configfile)
        print("\nExample config:\n[thegoodplace]\ntoken = xoxs-946546546544-654656454659-968498546566-...\nO\n[thebadplace]\ntoken = xoxp-998713211087-987979841210-306546506974-...")
        exit(1)
    response = requests.get("https://slack.com/api/emoji.list?token=" + token)
    alias_list = {}
    if response.status_code == 200:
        emojimap = json.loads(response.content)['emoji']
        print(str(len(emojimap.keys())) + " existing emoji")

        if not (args.collect or args.create):
            print("Requires either create with folder path or collect arg")
            exit(1)

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

            for x in emojimap.keys():
                if emojimap[x].startswith("alias:"):
                    alias_list[x] = emojimap[x]
                else:
                    ext =  emojimap[x][-3:]
                    location = "data/" + args.workspace + "/emojis/" + x + "." + ext
                    if not os.path.exists(location):
                        if not args.dryrun:
                            imageresponse = requests.get(emojimap[x], stream=True)
                            file = open(location, "wb")
                            imageresponse.raw.decode_content = True
                            # Copy the response stream raw data to local image file.
                            shutil.copyfileobj(imageresponse.raw, file)
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
                    # if args.dryrun:
                    responsepayload = {'ok': True}
                    # else:
                    #     response = requests.post("https://slack.com/api/emoji.add", headers=h, data=mp_encoder)
                    #     responsepayload = json.loads(response.content)
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