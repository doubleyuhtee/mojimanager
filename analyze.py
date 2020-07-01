import requests
import json
import sys
import argparse
import random
from datetime import datetime
import tokenmanager
import plotly.graph_objects as go


argument_parser = argparse.ArgumentParser(description="Slackmoji manager")
tokenmanager.add_command_args(argument_parser)
argument_parser.add_argument("--minimum", action='store', required=False, help="Minimum number of total emojis to have to be included in the graph", default=5)


def to_user_count_map(all_them_shits):
    name_to_entry_map = {}
    for entry in all_them_shits:
        if entry["user_display_name"] not in name_to_entry_map:
            name_to_entry_map[entry["user_display_name"]] = []
        name_to_entry_map[entry["user_display_name"]].append(entry["created"])
    for e in name_to_entry_map.keys():
        name_to_entry_map[e].sort()
    return name_to_entry_map


if __name__== "__main__":
    if len(sys.argv) < 2:
        argument_parser.print_help()
        exit(0)

    args = argument_parser.parse_args(sys.argv[1:])

    token = tokenmanager.get_token(args.workspace, args.token, args.configfile)
    if not token:
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
