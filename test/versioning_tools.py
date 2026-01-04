import sys
from get_latest import get_latest_plugman_version

"""if called directly from command line, it will check if given version is lower
than latest version in index.json"""


def semantic_to_str(semantic_version: str):
    """Convert version in the form of v1.2.3 to 001002003
    for comparing 2 version in semantic versioning format"""
    out = ""
    for i in semantic_version.split("."):
        if len(i) == 1:
            out += "00" + i
        if len(i) == 2:
            out += "0" + i
    return out


def plugman_version_is_lower_than(version: str):
    """Check if given version is lower than the latest entry in index.json"""
    latest = semantic_to_str(get_latest_plugman_version())
    version = semantic_to_str(version)
    if latest > version:
        return True
    else:
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python3 {__file__.split('/')[-1]} version_number")
        sys.exit(1)

    version = sys.argv[1].replace("v", "", 1)
    out = plugman_version_is_lower_than(version)
    print(int(out))
