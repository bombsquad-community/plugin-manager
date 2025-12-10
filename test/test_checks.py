import git

import hashlib
import json
import re
import io
import os
import pathlib

from packaging.version import Version

import unittest


class TestPluginManagerMetadata(unittest.TestCase):
    def setUp(self):
        with open("index.json", "rb") as fin:
            self.content = json.load(fin)
        self.plugin_manager = "plugin_manager.py"
        self.api_version_regexp = re.compile(b"(?<=ba_meta require api )(.*)")
        self.plugin_manager_version_regexp = re.compile(b"(?<=PLUGIN_MANAGER_VERSION = )(.*)")

        self.current_path = pathlib.Path()
        self.changelog = self.current_path / "CHANGELOG.md"
        self.repository = git.Repo()

    def test_keys(self):
        self.assertTrue(isinstance(self.content["plugin_manager_url"], str))
        self.assertTrue(isinstance(self.content["versions"], dict))
        self.assertTrue(isinstance(self.content["categories"], list))
        self.assertTrue(isinstance(self.content["external_source_url"], str))

    def test_versions_order(self):
        versions = list(self.content["versions"].items())
        sorted_versions = sorted(
            versions,
            key=lambda version: Version(version[0]),
            reverse=True,
        )
        assert sorted_versions == versions

    def test_versions(self):
        for version_name, version_metadata in self.content["versions"].items():
            commit = self.repository.commit(version_metadata["commit_sha"])
            plugin_manager = commit.tree / self.plugin_manager
            with io.BytesIO(plugin_manager.data_stream.read()) as fin:
                content = fin.read()

            md5sum = hashlib.md5(content).hexdigest()
            api_version = self.api_version_regexp.search(content).group()
            plugin_manager_version = self.plugin_manager_version_regexp.search(content).group()

            if md5sum != version_metadata["md5sum"]:
                self.fail(
                    "Plugin manager MD5 checksum changed;\n"
                    f"{version_metadata['md5sum']} (mentioned in index.json) ->\n"
                    f"{md5sum} (actual)"
                )
            self.assertEqual(int(api_version.decode("utf-8")), version_metadata["api_version"])
            self.assertEqual(plugin_manager_version.decode("utf-8"), f'"{version_name}"')

    def test_latest_version(self):
        versions = tuple(self.content["versions"].items())
        latest_version_name, latest_version_metadata = versions[0]
        plugin_manager = self.current_path / self.plugin_manager
        with open(plugin_manager, "rb") as fin:
            content = fin.read()

        md5sum = hashlib.md5(content).hexdigest()
        api_version = self.api_version_regexp.search(content).group()
        plugin_manager_version = self.plugin_manager_version_regexp.search(content).group()

        if md5sum != latest_version_metadata["md5sum"]:
            self.fail(
                "Plugin manager MD5 checksum changed;\n"
                f"{latest_version_metadata['md5sum']} (mentioned in index.json) ->\n"
                f"{md5sum} (actual)"
            )
        self.assertEqual(int(api_version.decode("utf-8")), latest_version_metadata["api_version"])
        self.assertEqual(plugin_manager_version.decode("utf-8"), f'"{latest_version_name}"')

    def test_changelog_entries(self):
        versions = tuple(self.content["versions"].keys())
        with open(self.changelog, "r") as fin:
            changelog = fin.read()
        for version in versions:
            changelog_version_header = f"## {version}"
            if changelog_version_header not in changelog:
                self.fail(f"Changelog entry for plugin manager {version} is missing.")


class TestPluginMetadata(unittest.TestCase):
    def setUp(self):
        self.category_directories = tuple(
            f'{os.path.join("plugins", path)}'
            for path in os.listdir("plugins") if os.path.isdir(path)
        )

    def test_no_duplicates(self):
        unique_plugins = set()
        total_plugin_count = 0
        for category in self.category_directories:
            plugins = os.listdir(category)
            total_plugin_count += len(plugins)
            unique_plugins.update(plugins)
        self.assertEqual(len(unique_plugins), total_plugin_count)


class BaseCategoryMetadataTestCases:
    class BaseTest(unittest.TestCase):
        def setUp(self):
            self.api_version_regexp = re.compile(b"(?<=ba_meta require api )(.*)")

            self.current_path = pathlib.Path()
            self.repository = git.Repo()

        def test_keys(self):
            self.assertEqual(self.content["name"], self.name)
            self.assertTrue(isinstance(self.content["description"], str))
            self.assertTrue(self.content["plugins_base_url"].startswith("https"))
            self.assertTrue(isinstance(self.content["plugins"], dict))

        def test_versions_order(self):
            for plugin_metadata in self.content["plugins"].values():
                versions = list(plugin_metadata["versions"].items())
                sorted_versions = sorted(
                    versions,
                    key=lambda version: Version(version[0]),
                    reverse=True,
                )
                self.assertEqual(sorted_versions, versions)

        def test_plugin_keys(self):
            for plugin_metadata in self.content["plugins"].values():
                self.assertTrue(isinstance(plugin_metadata["description"], str))
                self.assertTrue(isinstance(plugin_metadata["external_url"], str))
                self.assertTrue(isinstance(plugin_metadata["authors"], list))
                self.assertTrue(len(plugin_metadata["authors"]) > 0)
                for author in plugin_metadata["authors"]:
                    self.assertTrue(isinstance(author["name"], str))
                    self.assertTrue(isinstance(author["email"], str))
                    self.assertTrue(isinstance(author["discord"], str))
                self.assertTrue(isinstance(plugin_metadata["versions"], dict))
                self.assertTrue(len(plugin_metadata["versions"]) > 0)

        def test_versions(self):
            for plugin_name, plugin_metadata in self.content["plugins"].items():
                for version_name, version_metadata in plugin_metadata["versions"].items():
                    commit = self.repository.commit(version_metadata["commit_sha"])
                    plugin = os.path.join(self.category, f"{plugin_name}.py")
                    plugin_commit_sha = commit.tree / plugin
                    with io.BytesIO(plugin_commit_sha.data_stream.read()) as fin:
                        content = fin.read()

                    md5sum = hashlib.md5(content).hexdigest()
                    api_version = self.api_version_regexp.search(content).group()

                    if md5sum != version_metadata["md5sum"]:
                        self.fail(
                            f"{plugin} checksum changed for version {version_name};\n"
                            f"{version_metadata['md5sum']} (mentioned in {self.category_metadata_file}) ->\n"
                            f"{md5sum} (actual)"
                        )
                    self.assertEqual(int(api_version.decode("utf-8")),
                                     version_metadata["api_version"])

        def test_latest_version(self):
            for plugin_name, plugin_metadata in self.content["plugins"].items():
                latest_version_name, latest_version_metadata = tuple(
                    plugin_metadata["versions"].items())[0]
                plugin = self.current_path / self.category / f"{plugin_name}.py"
                with open(plugin, "rb") as fin:
                    content = fin.read()

                md5sum = hashlib.md5(content).hexdigest()
                api_version = self.api_version_regexp.search(content).group()

                if md5sum != latest_version_metadata["md5sum"]:
                    self.fail(
                        f"Latest version {latest_version_name} of "
                        f"{plugin} checksum changed;\n"
                        f"{latest_version_metadata['md5sum']} (mentioned in {self.category_metadata_file}) ->\n"
                        f"{md5sum} (actual)"
                    )
                self.assertEqual(md5sum, latest_version_metadata["md5sum"])
                self.assertEqual(int(api_version.decode("utf-8")),
                                 latest_version_metadata["api_version"])


class TestUtilitiesCategoryMetadata(BaseCategoryMetadataTestCases.BaseTest):
    def setUp(self):
        super().setUp()
        self.name = "Utilities"
        self.category = os.path.join("plugins", "utilities")
        self.category_metadata_file = f"{self.category}.json"
        with open(self.category_metadata_file, "rb") as fin:
            self.content = json.load(fin)


class TestMapsCategoryMetadata(BaseCategoryMetadataTestCases.BaseTest):
    def setUp(self):
        super().setUp()
        self.name = "Maps"
        self.category = os.path.join("plugins", "maps")
        self.category_metadata_file = f"{self.category}.json"
        with open(self.category_metadata_file, "rb") as fin:
            self.content = json.load(fin)


class TestMinigamesCategoryMetadata(BaseCategoryMetadataTestCases.BaseTest):
    def setUp(self):
        super().setUp()
        self.name = "Minigames"
        self.category = os.path.join("plugins", "minigames")
        self.category_metadata_file = f"{self.category}.json"
        with open(self.category_metadata_file, "rb") as fin:
            self.content = json.load(fin)
