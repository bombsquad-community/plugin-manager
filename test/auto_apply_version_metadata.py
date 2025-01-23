import hashlib
import json
import os
import sys
import re
import datetime


def get_comparable_version_tuple_from_string(version_string):
    return tuple(map(int, version_string.split(".")))


class PluginVersionMetadata:
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

        md5sum = self.calculate_md5sum()
        versions[self.version_name]["md5sum"] = md5sum
        return self

    def calculate_md5sum(self):
        if self._content is None:
            with open(self.plugin_path, "rb") as fin:
                self._content = fin.read()

        md5sum = hashlib.md5(self._content).hexdigest()
        return md5sum

    def sort_versions(self):
        if self._content is None:
            with open(self.plugin_path, "rb") as fin:
                self._content = fin.read()

        versions = self.json["plugins"][self.plugin_name]["versions"]
        sorted_versions = dict(sorted(
            tuple(versions.items()),
            key=lambda version: get_comparable_version_tuple_from_string(version[0]),
            reverse=True,
        ))
        self.json["plugins"][self.plugin_name]["versions"] = sorted_versions
        return self


class CategoryVersionMetadata:
    def __init__(self, category_metadata_base):
        self.category_metadata_base = category_metadata_base
        self.category_metadata_file = f"{self.category_metadata_base}.json"
        with open(self.category_metadata_file, "r") as fin:
            self.category_metadata = json.load(fin)

    def get_plugins_having_null_version_values(self):
        for plugin_name, plugin_metadata in self.category_metadata["plugins"].items():
            for version_name, version_metadata in plugin_metadata["versions"].items():
                if version_metadata is None:
                    plugin_path = f"{os.path.join(
                        self.category_metadata_base, f'{plugin_name}.py')}"
                    yield PluginVersionMetadata(
                        plugin_name,
                        version_name,
                        plugin_path,
                    )

    def get_plugins_having_diff_last_md5sum_version_values(self):
        for plugin_name, plugin_metadata in self.category_metadata["plugins"].items():
            latest_version_name, latest_version_metadata = tuple(
                plugin_metadata["versions"].items())[0]

            plugin_path = f"{os.path.join(self.category_metadata_base, f'{plugin_name}.py')}"
            plugin_version_metadata = PluginVersionMetadata(
                plugin_name,
                latest_version_name,
                plugin_path,
            )
            if plugin_version_metadata.calculate_md5sum() != latest_version_metadata["md5sum"]:
                yield plugin_version_metadata

    def apply_version_metadata_to_null_version_values(self, commit_sha):
        null_versioned_plugins = self.get_plugins_having_null_version_values()
        return self.apply_metadata_to_plugins(commit_sha, null_versioned_plugins)

    def apply_version_metadata_to_last_version_values(self, commit_sha):
        diff_md5sum_plugins = self.get_plugins_having_diff_last_md5sum_version_values()
        return self.apply_metadata_to_plugins(commit_sha, diff_md5sum_plugins)

    def apply_metadata_to_plugins(self, commit_sha, plugins):
        today = datetime.date.today().strftime("%d-%m-%Y")
        category_json = self.category_metadata
        for plugin in plugins:
            category_json = (
                plugin.set_json(category_json)
                      .set_api_version()
                      .set_commit_sha(commit_sha)
                      .set_released_on(today)
                      .set_md5sum()
                      .sort_versions()
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


class PluginManagerVersionMetadata:
    def __init__(self):
        with open("plugin_manager.py", "rb") as fin:
            self._content = fin.read()
        self.metadata_path = "index.json"
        with open(self.metadata_path, "rb") as fin:
            self.json = json.load(fin)
        self.api_version_regexp = re.compile(b"(?<=ba_meta require api )(.*)")

    def set_api_version(self, version_name):
        version = self.json["versions"][version_name]
        api_version = self.api_version_regexp.search(self._content).group()
        version["api_version"] = int(api_version)

    def calculate_md5sum(self):
        md5sum = hashlib.md5(self._content).hexdigest()
        return md5sum

    def apply_version_metadata_to_null_version_value(self, commit_sha):
        today = datetime.date.today().strftime("%d-%m-%Y")
        latest_version_name, latest_version_metadata = tuple(
            self.json["versions"].items())[0]

        if self.json["versions"][latest_version_name] is None:
            self.json["versions"][latest_version_name] = {}
            version = self.json["versions"][latest_version_name]
            self.set_api_version(latest_version_name)
            version["commit_sha"] = commit_sha[:8]
            version["released_on"] = today
            version["md5sum"] = self.calculate_md5sum()

        return self.json

    def save(self, metadata):
        with open(self.metadata_path, "w") as fout:
            json.dump(
                metadata,
                fout,
                indent=2,
                ensure_ascii=False,
            )


def auto_apply_version_metadata(last_commit_sha):
    plugin_manager = PluginManagerVersionMetadata()
    metadata = plugin_manager.apply_version_metadata_to_null_version_value(last_commit_sha)
    plugin_manager.save(metadata)

    utilities = CategoryVersionMetadata(os.path.join("plugins", "utilities"))
    category_json = utilities.apply_version_metadata_to_null_version_values(last_commit_sha)
    utilities.save(category_json)

    maps = CategoryVersionMetadata(os.path.join("plugins", "maps"))
    category_json = maps.apply_version_metadata_to_null_version_values(last_commit_sha)
    maps.save(category_json)

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
