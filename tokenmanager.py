import configparser
import os
from pathlib import Path


CONFIG_FILE_NAME = ".mojimanjerconfig"


def add_command_args(argparser):
    argparser.add_argument("--token", "-t",
                                 help="Api token, xoxs token required for upload. Grab it from your headers when uploading manually",
                                 action='store', required=False)
    argparser.add_argument("--workspace", "-w", action='store', required=False,
                                 help="Section from config to use and directory to output to")
    argparser.add_argument("--configfile", action='store', required=False,
                                 help="Path to config file.  Defaults (~/.mojimanjerconfig)",
                                 default=os.path.join(Path.home(), CONFIG_FILE_NAME))


def get_token(workspace, token, configfile):
    token_result = None
    if token:
        token_result = token
    if workspace:
        print(configfile)
        config = configparser.ConfigParser()
        if not token_result:
            config.read(configfile)
            if workspace in config:
                token_result = config[workspace]["token"]

        if token_result:
            if workspace not in config:
                config[workspace] = {}
            if "token" not in config[workspace] or token_result != config[workspace]["token"]:
                config[workspace]["token"] = token_result
                with open(configfile, 'w') as configfileupdate:
                    config.write(configfileupdate)

    if not token_result and not workspace:
        config = configparser.ConfigParser()
        config.read(configfile)
        if "default" in config:
            token_result = config["default"]["token"]

    if not token_result:
        print("\nNo token provided or found in " + configfile)
        print("""
Example config:

[default]
token = xoxs-1111111-111111111111...

[thegoodplace]
token = xoxs-946546546544-654656454659-968498546566-...

[thebadplace]
token = xoxp-998713211087-987979841210-306546506974-...

""")

    return token_result
