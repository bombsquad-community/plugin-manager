import hashlib
import json
import os
import sys
import re
import datetime


class NullVersionedPlugin:
    def __init__(self, plugin_name, version_name, plugin_path, from_json={}):
        self.plugin_name = plugin_name
        self.version_name = version_name
        self.plugin_path = plugin_path
        self.json = from_json
        self.api_version_regexp = re.compile(b"(?<=ba_meta require api )(.*)")
        self._content = None

    def set_json(self, json):
        self.json = json
        return self

    def set_api_version(self):
        if self._content is None:
            with open(self.plugin_path, "rb") as fin:
                self._content = fin.read()

        versions = self.json["plugins"][self.plugin_name]["versions"]
        if versions[self.version_name] is None:
            versions[self.version_name] = {}

        api_version = self.api_version_regexp.search(self._content).group()
        versions[self.version_name]["api_version"] = int(api_version)
        return self

    def set_commit_sha(self, commit_sha):
        versions = self.json["plugins"][self.plugin_name]["versions"]
        if versions[self.version_name] is None:
            versions[self.version_name] = {}

        versions[self.version_name]["commit_sha"] = commit_sha[:8]
        return self

    def set_released_on(self, date):
        versions = self.json["plugins"][self.plugin_name]["versions"]
        if versions[self.version_name] is None:
            versions[self.version_name] = {}

        versions[self.version_name]["released_on"] = date
        return self

    def set_md5sum(self):
        if self._content is None:
            with open(self.plugin_path, "rb") as fin:
                self._content = fin.read()

        versions = self.json["plugins"][self.plugin_name]["versions"]
        if versions[self.version_name] is None:
            versions[self.version_name] = {}

        md5sum = hashlib.md5(self._content).hexdigest()
        versions[self.version_name]["md5sum"] = md5sum
        return self


class CategoryVersionMetadata:
    def __init__(self, category_metadata_base):
        self.category_metadata_base = category_metadata_base
        self.category_metadata_file = f"{self.category_metadata_base}.json"
        with open(self.category_metadata_file, "r") as fin:
            self.category_metadata = json.load(fin)

    def get_plugins_having_null_version_values(self):
        for plugin_name, plugin_metadata in self.category_metadata["plugins"].items():
            latest_version_name, latest_version_metadata = tuple(
                plugin_metadata["versions"].items())[0]
            if latest_version_metadata is None:
                plugin_path = f"{os.path.join(self.category_metadata_base, f'{plugin_name}.py')}"
                yield NullVersionedPlugin(
                    plugin_name,
                    latest_version_name,
                    plugin_path,
                )

    def apply_version_metadata_to_null_version_values(self, commit_sha):
        null_versioned_plugins = self.get_plugins_having_null_version_values()
        today = datetime.date.today().strftime("%d-%m-%Y")
        category_json = self.category_metadata
        for plugin in null_versioned_plugins:
            category_json = (
                plugin.set_json(category_json)
                      .set_api_version()
                      .set_commit_sha(commit_sha)
                      .set_released_on(today)
                      .set_md5sum()
                      .json
            )
        return category_json

    def save(self, category_json):
        with open(self.category_metadata_file, "w") as fout:
            json.dump(
                category_json,
                fout,
                indent=2,
                ensure_ascii=False,
            )


def auto_apply_version_metadata(last_commit_sha):
    utilities = CategoryVersionMetadata(os.path.join("plugins", "utilities"))
    category_json = utilities.apply_version_metadata_to_null_version_values(last_commit_sha)
    utilities.save(category_json)

    minigames = CategoryVersionMetadata(os.path.join("plugins", "minigames"))
    category_json = minigames.apply_version_metadata_to_null_version_values(last_commit_sha)
    minigames.save(category_json)


if __name__ == "__main__":
    try:
        last_commit_sha = sys.argv[1]
    except KeyError:
        raise ValueError("Last commit SHA not provided.")
    else:
        auto_apply_version_metadata(last_commit_sha)
