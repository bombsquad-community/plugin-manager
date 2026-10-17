import git

import hashlib
import json
import re
import io
import os
import pathlib

from packaging.version import Version

import unittest

# Raised by Repo.commit() when a revision cannot be resolved. Both entries are
# required because which one you get depends on how the sha is spelled: an
# unresolvable abbreviated name - the 7-8 char form this repo actually stores,
# see auto_apply_version_metadata.py - raises BadName, whereas a full-length
# but absent 40-hex sha raises plain ValueError. BadName/BadObject are NOT
# ValueError subclasses, so neither entry is redundant. Kept narrow so lenient
# mode can't mask unrelated repository errors.
#
# BadName/BadObject originate in gitdb but are re-exported by GitPython in
# git.exc.__all__, so git.exc.* is the supported public spelling and is used
# here deliberately - it avoids importing gitdb, a transitive dependency that
# test/pip_reqs.txt does not declare directly.
UNRESOLVED_COMMIT_ERRORS = (ValueError, git.exc.BadName, git.exc.BadObject)

# A GitHub username: alphanumerics and hyphens, not starting or ending with
# a hyphen, at most 39 characters. Kept in sync with the issue-assignment
# workflow (.github/workflows/assign-plugin-owners.yml).
GITHUB_USERNAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?")


def is_unpublished_version(repository, version_metadata):
    """True if this version entry is being introduced by the PR under test.

    Such an entry can't satisfy the history checks yet: its metadata is either
    still an unstamped ``null`` placeholder, or was stamped against the current
    HEAD by ci-check.yml's preview - describing the reformatted working tree
    rather than anything committed. Published entries always point at an
    earlier commit whose tree really does contain the described file, so they
    are unaffected. Only consulted in lenient mode (ci-check.yml); the
    authoritative strict run on push-to-main still validates these.
    """
    if not version_metadata or not version_metadata.get("commit_sha"):
        return True
    try:
        return repository.commit(version_metadata["commit_sha"]) == repository.head.commit
    except UNRESOLVED_COMMIT_ERRORS:
        return False  # unresolvable: let the caller's handler report it


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
        lenient = os.environ.get("PLUGMAN_CI_LENIENT_HISTORY") == "1"
        for version_name, version_metadata in self.content["versions"].items():
            if lenient and is_unpublished_version(self.repository, version_metadata):
                print(f"[lenient] skipping {version_name}: not committed yet")
                continue
            try:
                commit = self.repository.commit(version_metadata["commit_sha"])
            except UNRESOLVED_COMMIT_ERRORS as err:
                if lenient:
                    print(f"[lenient] skipping {version_name}: commit "
                          f"{version_metadata['commit_sha']} not found yet ({err})")
                    continue
                raise
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
        # os.path.isdir() must be given the joined path. Testing the bare name
        # resolves it against the repo root, where no such directory exists, so
        # this tuple came out empty and every test below passed vacuously.
        self.category_directories = tuple(
            os.path.join("plugins", path)
            for path in sorted(os.listdir("plugins"))
            if os.path.isdir(os.path.join("plugins", path))
        )
        # Fail loudly if discovery ever goes empty again, rather than reporting
        # a pass for a comparison of nothing against nothing.
        self.assertTrue(self.category_directories,
                        "no category directories discovered under plugins/")
        self.api_version_regexp = re.compile(b"(?<=ba_meta require api )(.*)")
        self.entry_point_regexp = re.compile(b"ba_meta export ")

    def plugin_files(self, category):
        return sorted(name for name in os.listdir(category) if name.endswith(".py"))

    def test_no_duplicates(self):
        unique_plugins = set()
        total_plugin_count = 0
        for category in self.category_directories:
            plugins = self.plugin_files(category)
            total_plugin_count += len(plugins)
            unique_plugins.update(plugins)
        self.assertEqual(len(unique_plugins), total_plugin_count)

    def test_plugin_files_and_manifest_entries_agree(self):
        """Catches a plugin whose metadata step produced nothing at all.

        auto_apply_plugin_metadata.py now raises rather than skipping a file it
        cannot read a plugman dict out of, but this is the independent check on
        the result: a .py with no entry would be invisible in-game, and an entry
        with no .py makes the manager offer a download that cannot exist.
        """
        for category in self.category_directories:
            manifest_file = f"{category}.json"
            with self.subTest(category=category):
                self.assertTrue(os.path.isfile(manifest_file),
                                f"{category} has no matching {manifest_file}")
                with open(manifest_file, "rb") as fin:
                    entries = set(json.load(fin)["plugins"])
                files = {name[:-len(".py")] for name in self.plugin_files(category)}
                self.assertEqual(
                    sorted(files - entries), [],
                    f"plugin file(s) under {category} with no entry in {manifest_file}; "
                    "bump the version in the plugman dict so CI can generate one"
                )
                self.assertEqual(
                    sorted(entries - files), [],
                    f"entries in {manifest_file} with no matching .py under {category}"
                )

    def test_plugins_declare_their_ba_meta_directives(self):
        for category in self.category_directories:
            for name in self.plugin_files(category):
                plugin = os.path.join(category, name)
                with open(plugin, "rb") as fin:
                    content = fin.read()
                with self.subTest(plugin=plugin):
                    self.assertIsNotNone(
                        self.api_version_regexp.search(content),
                        f"{plugin} declares no '# ba_meta require api <n>'. The version "
                        "tests read that straight out of the source, so without it they "
                        "fail with an unhelpful AttributeError instead."
                    )
                    self.assertIsNotNone(
                        self.entry_point_regexp.search(content),
                        f"{plugin} declares no '# ba_meta export', so the game would "
                        "load nothing from it."
                    )


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
            for plugin_name, plugin_metadata in self.content["plugins"].items():
                self.assertTrue(isinstance(plugin_metadata["description"], str))
                self.assertTrue(isinstance(plugin_metadata["external_url"], str))
                self.assertTrue(isinstance(plugin_metadata["authors"], list))
                self.assertTrue(len(plugin_metadata["authors"]) > 0)
                for author in plugin_metadata["authors"]:
                    for key in ("name", "email", "discord", "github"):
                        self.assertIn(key, author, f"{plugin_name}: an author is missing "
                                      f"{key!r} in plugman (use \"\" if you have none)")
                        self.assertTrue(isinstance(author[key], str))
                    github = author["github"]
                    self.assertTrue(
                        github == "" or GITHUB_USERNAME.fullmatch(github),
                        f"{plugin_name}: invalid GitHub username {github!r} "
                        "(leave out the @ and the URL)",
                    )
                self.assertTrue(isinstance(plugin_metadata["versions"], dict))
                self.assertTrue(len(plugin_metadata["versions"]) > 0)

        def test_versions(self):
            lenient = os.environ.get("PLUGMAN_CI_LENIENT_HISTORY") == "1"
            for plugin_name, plugin_metadata in self.content["plugins"].items():
                for version_name, version_metadata in plugin_metadata["versions"].items():
                    if lenient and is_unpublished_version(self.repository, version_metadata):
                        print(f"[lenient] skipping {plugin_name} {version_name}: "
                              "not committed yet")
                        continue
                    try:
                        commit = self.repository.commit(version_metadata["commit_sha"])
                    except UNRESOLVED_COMMIT_ERRORS as err:
                        if lenient:
                            print(f"[lenient] skipping {plugin_name} {version_name}: "
                                  f"commit {version_metadata['commit_sha']} not found yet ({err})")
                            continue
                        raise
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
