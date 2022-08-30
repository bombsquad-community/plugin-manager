import json
import re

import asyncio
import aiohttp

import unittest
from test import helpers


class TestPluginManagerMetadata(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        with open("index.json", "rb") as fin:
            self.content = json.load(fin)

    async def asyncTearDown(self):
        pass

    def test_keys(self):
        self.assertTrue(self.content["plugin_manager_url"].startswith("http"))
        self.assertTrue(isinstance(self.content["versions"], dict))
        self.assertTrue(isinstance(self.content["categories"], list))
        for category in self.content["categories"]:
            self.assertTrue(category.startswith("http"))
        self.assertTrue(self.content["external_source_url"].startswith("http"))

    def test_versions_order(self):
        versions = list(self.content["versions"].items())
        sorted_versions = sorted(
            versions,
            key=lambda version: version[0],
            reverse=True,
        )
        self.assertEqual(sorted_versions, versions)

    async def test_versions_metadata(self):
        versions = tuple(self.content["versions"].items())
        latest_number, latest_version = versions[0]
        async with aiohttp.ClientSession() as session:
            await asyncio.gather(
                helpers.assert_for_network_files_from_versions(
                    self.content["plugin_manager_url"],
                    self.content["versions"],
                    session,
                ),
                # Additionally assert for the latest version with tag as "main".
                helpers.assert_for_network_file(
                    self.content["plugin_manager_url"].format(
                        content_type="raw",
                        tag="main",
                    ),
                    latest_version["md5sum"],
                    session,
                ),
            )
