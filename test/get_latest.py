import json
import sys


def get_latest_plugman_version() -> str:
    """Get latest version entry from index.json"""
    with open('index.json', 'r') as file:
        content = json.loads(file.read())
        latest_version = list(content["versions"].keys())[0]
        return latest_version


def get_latest_plugin_version(plugin_name, json_path) -> str:
    """Get latest version entry from json file for a specific plugin"""
    with open(json_path, 'r') as file:
        content = json.loads(file.read())
        latest_version = list(content["plugins"][plugin_name]["versions"].keys())[0]
        return latest_version


def get_latest_api():
    """Get latest api entry from index.json"""
    with open('index.json', 'r') as file:
        content = json.loads(file.read())
        latest_api = content["versions"][get_latest_plugman_version()]["api_version"]
        return latest_api


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python3 {__file__.split('/')[-1]} function [args...]")
        sys.exit(1)
    function_name = sys.argv[1]
    function_args = sys.argv[2:]
    print(
        globals()[function_name](*function_args)
    )  # used to call the function passed as cli parameter with additional arguments
