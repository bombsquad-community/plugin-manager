import hashlib
import json
import re

import asyncio
import aiohttp

import unittest
from test import helpers


class TestMetadata(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        with open("plugins/utilities.json", "rb") as fin:
            self.content = json.load(fin)

    async def asyncTearDown(self):
        # This helps suppress aiohttp warnings. See:
        # https://github.com/aio-libs/aiohttp/issues/1115
        await asyncio.sleep(0.2)

    def test_keys(self):
        self.assertEqual(self.content["name"], "Utilities")
        self.assertTrue(isinstance(self.content["description"], str))
        self.assertTrue(self.content["plugins_base_url"].startswith("http"))
        self.assertTrue(isinstance(self.content["plugins"], dict))

    async def test_plugins_metadata(self):
        asserts_for_versions_metadata = []
        async with aiohttp.ClientSession() as session:
            for plugin in self.content["plugins"].items():
                metadata = helpers.AssertPluginMetadata(*plugin)
                metadata.assert_keys()
                asserts_for_versions_metadata.append(
                    metadata.assert_for_versions_metadata(
                        self.content["plugins_base_url"],
                        session,
                    )
                )
            await asyncio.gather(
                *asserts_for_versions_metadata
            )

    def test_versions_order(self):
        for plugin_metadata in self.content["plugins"].values():
            versions = list(plugin_metadata["versions"].items())
            sorted_versions = sorted(
                versions,
                key=lambda version: version[0],
                reverse=True,
            )
            self.assertEqual(sorted_versions, versions)
