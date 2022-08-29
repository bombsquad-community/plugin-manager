import hashlib
import os
import json
import re

import asyncio
import aiohttp

import unittest


async def assert_for_md5sum(url, md5sum, aiohttp_session):
    async with aiohttp_session.get(url) as response:
        expected_response_status = 200
        assert response.status == expected_response_status, (
            f'Request to "{url}" returned status code {response.status} (expected {expected_response_status}.'
        )
        content = await response.read()
        caclulated_md5sum = hashlib.md5(content).hexdigest()
        assert caclulated_md5sum == md5sum, (
            f'"{url}" failed MD5 checksum:\nGot {caclulated_md5sum} (expected {md5sum}).'
        )


async def assert_for_commit_sha_and_md5sum_from_versions(base_url, versions, aiohttp_session):
        tasks = tuple(
            assert_for_md5sum(
                base_url.format(content_type="raw", tag=version["commit_sha"]),
                version["md5sum"],
                aiohttp_session,
            ) for number, version in versions.items()
        )
        await asyncio.gather(*tasks)


class TestPluginManagerMetadata(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        with open("index.json", "rb") as fin:
            self.content = json.load(fin)
        self.version_regexp = re.compile(b"PLUGIN_MANAGER_VERSION = .+")

    async def asyncTearDown(self):
        pass

    def test_keys(self):
        assert isinstance(self.content["plugin_manager_url"], str)
        assert isinstance(self.content["versions"], dict)
        assert isinstance(self.content["categories"], list)
        assert isinstance(self.content["external_source_url"], str)

    def test_versions_order(self):
        versions = list(self.content["versions"].items())
        sorted_versions = sorted(versions, key=lambda version: version[0])
        assert sorted_versions == versions

    async def test_versions_metadata(self):
        versions = tuple(self.content["versions"].items())
        latest_number, latest_version = versions[0]
        async with aiohttp.ClientSession() as session:
            await asyncio.gather(
                assert_for_commit_sha_and_md5sum_from_versions(
                    self.content["plugin_manager_url"],
                    self.content["versions"],
                    session,
                ),
                # Additionally assert for the latest version with tag as "main".
                assert_for_md5sum(
                    self.content["plugin_manager_url"].format(content_type="raw", tag="main"),
                    latest_version["md5sum"],
                    session,
                ),
            )


# class TestPluginsMetadata(unittest.IsolatedAsyncioTestCase):

# class TestExternalSourceMetadata(unittest.IsolatedAsyncioTestCase):
