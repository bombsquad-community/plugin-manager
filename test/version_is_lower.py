import sys
from get_latest import get_latest


def semantic_to_str(semantic_version: str):
    out = ""
    for i in (semantic_version.split(".")):
        if len(i) == 1:
            out += "00"+i
        if len(i) == 2:
            out += "0"+i
    return out


def version_is_lower(version: str):
    latest = semantic_to_str(get_latest())
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
    out = version_is_lower(version)
    print(int(out))
