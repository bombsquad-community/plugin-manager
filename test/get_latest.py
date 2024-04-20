import json


def get_latest():
    """Get latest version entry from index.json"""
    with open('index.json', 'r') as file:
        content = json.loads(file.read())
        latest_version = list(content["versions"].keys())[0]
        return latest_version


if __name__ == "__main__":
    print(get_latest())
