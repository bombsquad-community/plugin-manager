import json
import sys


def get_latest_version():
    """Get latest version entry from index.json"""
    with open('index.json', 'r') as file:
        content = json.loads(file.read())
        latest_version = list(content["versions"].keys())[0]
        return latest_version


def get_latest_api():
    """Get latest api entry from index.json"""
    with open('index.json', 'r') as file:
        content = json.loads(file.read())
        latest_api = content["versions"][get_latest_version()]["api_version"]
        return latest_api


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python3 {__file__.split('/')[-1]} function")
        sys.exit(1)
    print(globals()[sys.argv[1]]())  # used to call the fucntion passed as cli parameter
