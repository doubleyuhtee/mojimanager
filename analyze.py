import requests
import json
import shutil
import time
import os
import sys
import argparse
import configparser
from pathlib import Path
import random
from datetime import datetime

import plotly.graph_objects as go

CONFIG_FILE_NAME = ".mojimanjerconfig"

argument_parser = argparse.ArgumentParser(description="Slackmoji manager")
argument_parser.add_argument("--token", "-t", help="Api token, xoxs token required for upload. Grab it from your headers when uploading manually", action='store', required=False)
argument_parser.add_argument("--workspace", "-w", action='store', required=False, help="Section from config to use and directory to output to")
argument_parser.add_argument("--minimum", action='store', required=False, help="Minimum number of total emojis to have to be included in the graph", default=5)

def to_user_count_map(list):
    map = {}
    for entry in list:
        if entry["user_display_name"] not in map:
            map[entry["user_display_name"]] = []
        map[entry["user_display_name"]].append(entry["created"])
    for e in map.keys():
        map[e].sort()
    return map


if __name__== "__main__":
    if len(sys.argv) < 2:
        argument_parser.print_help()
        exit(0)

    args = argument_parser.parse_args(sys.argv[1:])
    token = None
    if args.token:
        token = args.token
    if args.workspace:
        configfile_location = str(Path.home()) + "/" + CONFIG_FILE_NAME
        print(configfile_location)
        config = configparser.ConfigParser()
        config.read(configfile_location)
        if args.workspace in config:
            token_name = "fetch"
            token = config[args.workspace][token_name]
    if not token:
        print("\nNo token found in" + str(Path.home()) + "/" + CONFIG_FILE_NAME)
        print("\nExample config:\n[backonfloor6]\nfetch = xoxp-654651463163-654654649845-245646546464-....\ncreate = xoxs-946546546544-654656454659-968498546566-...\nO\n[thebadplace]\nfetch = xoxp-998713211087-987979841210-306546506974-...")
        exit(1)

    response = requests.get("https://slack.com/api/emoji.adminList?limit=1000&token=" + token)

    if response.status_code == 200:
        content = json.loads(response.content)
        full_list = content["emoji"]
        content["emoji"] = []
        print(json.dumps(content, indent=2))
        page = 1
        while page < content["paging"]["pages"]:
            page += 1
            response = requests.get(f"https://slack.com/api/emoji.adminList?limit=1000&page={page}&token={token}")
            content = json.loads(response.content)
            full_list.extend(content["emoji"])
        print(len(full_list))
        print(json.dumps(random.choice(full_list), indent=2))
        userfied_map = to_user_count_map(full_list)

        plot_title = "moji analysis"
        fig = go.Figure(
            layout=go.Layout(
                title=plot_title
            )
        )
        now = datetime.now()
        for k,v in userfied_map.items():
            print(k + " " + str(len(v)))
            user_time_map = {}
            if len(v) >= int(args.minimum):
                for seconds in v:
                    time = datetime.fromtimestamp(seconds-(seconds%10)).strftime('%Y-%m-%d %H:%M:%S')
                    if time not in user_time_map:
                        user_time_map[time] = 0
                    user_time_map[time] += 1
                x = []
                y = []
                newcount = 0
                for date,count in user_time_map.items():
                    x.append(date)
                    newcount = count + newcount
                    y.append(newcount)
                x.append(now)
                y.append(newcount)
                fig.add_trace(go.Scatter(x=x, y=y, name=k))

        fig.write_html(plot_title + '.html', auto_open=True)

    else:
        print(response.status_code)
        print(response.content)
