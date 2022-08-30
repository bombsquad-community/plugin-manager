import hashlib
import os
import re

import asyncio


async def assert_for_network_file(url, md5sum, aiohttp_session, regexp=None, regexp_result=None):
    async with aiohttp_session.get(url) as response:
        expected_response_status = 200
        assert response.status == expected_response_status, (
            f'Request to "{url}" returned status code {response.status} '
            f'(expected {expected_response_status}).'
        )
        content = await response.read()
        caclulated_md5sum = hashlib.md5(content).hexdigest()
        assert caclulated_md5sum == md5sum, (
            f'"{url}" failed MD5 checksum:\nGot {caclulated_md5sum} '
            f'(expected {md5sum}).'
        )
        if regexp and regexp_result:
            result = regexp.search(content).group().decode("utf-8")
            assert result == regexp_result, (
                f'Regexp failed: Got ({result}) (expected {regexp_result}).'
            )


async def assert_for_network_files_from_versions(base_url, versions, aiohttp_session, regexp=None):
    tasks = tuple(
        assert_for_network_file(
            base_url.format(
                content_type="raw",
                tag=version["commit_sha"],
            ),
            version["md5sum"],
            aiohttp_session,
            regexp=regexp,
            regexp_result=str(version["api_version"]),
        ) for number, version in versions.items()
    )
    await asyncio.gather(*tasks)


class AssertPluginMetadata:
    def __init__(self, name, metadata):
        self.name = name
        self.metadata = metadata
        self.filename = f"{name}.py"
        self.api_number_regexp = re.compile(b"(?<=ba_meta require api )(.*)")

    def assert_keys(self):
        assert isinstance(self.metadata["description"], str)
        assert isinstance(self.metadata["external_url"], str)
        assert isinstance(self.metadata["authors"], list)
        assert len(self.metadata["authors"]) > 0
        for author in self.metadata["authors"]:
            assert isinstance(author["name"], str)
            assert isinstance(author["email"], str)
            assert isinstance(author["discord"], str)
        assert isinstance(self.metadata["versions"], dict)
        assert len(self.metadata["versions"]) > 0

    async def assert_for_versions_metadata(self, base_url, aiohttp_session):
        versions = tuple(self.metadata["versions"].items())
        latest_number, latest_version = versions[0]
        await asyncio.gather(
            assert_for_network_files_from_versions(
                f"{base_url}/{self.filename}",
                self.metadata["versions"],
                aiohttp_session,
                regexp=self.api_number_regexp
            ),
            # Additionally assert for the latest version with tag as "main".
            assert_for_network_file(
                f"{base_url}/{self.filename}".format(
                    content_type="raw",
                    tag="main",
                ),
                latest_version["md5sum"],
                aiohttp_session,
                regexp=self.api_number_regexp,
                regexp_result=str(latest_version["api_version"]),
            )
        )
        # TODO: Regex stuff to get api number from plugin file.
