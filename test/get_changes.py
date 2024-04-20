import re
import sys


def get_version_changelog(version: str):
    """Get changelog entry from CHANGELOG.md for given version"""
    with open('CHANGELOG.md', 'r') as file:
        content = file.read()
        pattern = rf"### {version} \(\d\d-\d\d-\d{{4}}\)\n(.*?)(?=### \d+\.\d+\.\d+|\Z)"
        matches = re.findall(pattern, content, re.DOTALL)
        if matches:
            return matches[0].strip()
        else:
            return f"Changelog entry for version {version} not found."


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python3 {__file__.split('/')[-1]} version_number")
        sys.exit(1)

    version = sys.argv[1].replace("v", "", 1)
    changelog = get_version_changelog(version)
    print(changelog)
