# ba_meta require api 7
import ba
import _ba
from bastd.ui import popup, confirm

import urllib.request
import http.client
import socket
import ssl
import json

import os
import sys
import asyncio
import re
import pathlib
import contextlib
import hashlib
import copy

from typing import Union, Optional

_env = _ba.env()
_uiscale = ba.app.ui.uiscale


PLUGIN_MANAGER_VERSION = "0.3.0"
REPOSITORY_URL = "https://github.com/bombsquad-community/plugin-manager"
CURRENT_TAG = "main"
INDEX_META = "{repository_url}/{content_type}/{tag}/index.json"
HEADERS = {
    "User-Agent": _env["user_agent_string"],
}
PLUGIN_DIRECTORY = _env["python_directory_user"]
REGEXP = {
    "plugin_api_version": re.compile(b"(?<=ba_meta require api )(.*)"),
    "plugin_entry_points": re.compile(b"(ba_meta export plugin\n+class )(.*)\\("),
    "minigames": re.compile(b"(ba_meta export game\n+class )(.*)\\("),
}
DISCORD_URL = "https://ballistica.net/discord"

_CACHE = {}


class MD5CheckSumFailedError(Exception):
    pass


class PluginNotInstalledError(Exception):
    pass


class CategoryDoesNotExistError(Exception):
    pass


class NoCompatibleVersionError(Exception):
    pass


def send_network_request(request):
    return urllib.request.urlopen(request)


async def async_send_network_request(request):
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, send_network_request, request)
    return response


def stream_network_response_to_file(request, file, md5sum=None, retries=3):
    response = urllib.request.urlopen(request)
    chunk_size = 16 * 1024
    content = b""
    with open(file, "wb") as fout:
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            fout.write(chunk)
            content += chunk
    if md5sum and hashlib.md5(content).hexdigest() != md5sum:
        if retries <= 0:
            raise MD5CheckSumFailedError("MD5 checksum match failed.")
        return stream_network_response_to_file(
            request,
            file,
            md5sum=md5sum,
            retries=retries-1,
        )
    return content


async def async_stream_network_response_to_file(request, file, md5sum=None, retries=3):
    loop = asyncio.get_event_loop()
    content = await loop.run_in_executor(
        None,
        stream_network_response_to_file,
        request,
        file,
        md5sum,
        retries,
    )
    return content


def play_sound():
    ba.playsound(ba.getsound('swish'))


def partial_format(string_template, **kwargs):
    for key, value in kwargs.items():
        string_template = string_template.replace("{" + key + "}", value)
    return string_template


class DNSBlockWorkaround:
    """
    Some ISPs put a DNS block on domains that are needed for plugin manager to
    work properly. This class stores methods to workaround such blocks by adding
    dns.google as a fallback.

    Such as Jio, a pretty popular ISP in India has a DNS block on
    raw.githubusercontent.com (sigh..).

    Usage:
    -----
    >>> import urllib.request
    >>> import http.client
    >>> import socket
    >>> import ssl
    >>> import json
    >>> DNSBlockWorkaround.apply()
    >>> response = urllib.request.urlopen("https://dnsblockeddomain.com/path/to/resource/")
    """

    _google_dns_cache = {}

    def apply():
        opener = urllib.request.build_opener(
            DNSBlockWorkaround._HTTPHandler,
            DNSBlockWorkaround._HTTPSHandler,
        )
        urllib.request.install_opener(opener)

    def _resolve_using_google_dns(hostname):
        response = urllib.request.urlopen(f"https://dns.google/resolve?name={hostname}")
        response = response.read()
        response = json.loads(response)
        resolved_host = response["Answer"][0]["data"]
        return resolved_host

    def _resolve_using_system_dns(hostname):
        resolved_host = socket.gethostbyname(hostname)
        return resolved_host

    def _resolve_with_workaround(hostname):
        resolved_host_from_cache = DNSBlockWorkaround._google_dns_cache.get(hostname)
        if resolved_host_from_cache:
            return resolved_host_from_cache

        resolved_host_by_system_dns = DNSBlockWorkaround._resolve_using_system_dns(hostname)

        if DNSBlockWorkaround._is_blocked(hostname, resolved_host_by_system_dns):
            resolved_host = DNSBlockWorkaround._resolve_using_google_dns(hostname)
            DNSBlockWorkaround._google_dns_cache[hostname] = resolved_host
        else:
            resolved_host = resolved_host_by_system_dns

        return resolved_host

    def _is_blocked(hostname, address):
        is_blocked = False
        if hostname == "raw.githubusercontent.com":
            # Jio's DNS server may be blocking it.
            is_blocked = address.startswith("49.44.")

        return is_blocked

    class _HTTPConnection(http.client.HTTPConnection):
        def connect(self):
            host = DNSBlockWorkaround._resolve_with_workaround(self.host)
            self.sock = socket.create_connection(
                (host, self.port),
                self.timeout,
            )

    class _HTTPSConnection(http.client.HTTPSConnection):
        def connect(self):
            host = DNSBlockWorkaround._resolve_with_workaround(self.host)
            sock = socket.create_connection(
                (host, self.port),
                self.timeout,
            )
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.verify_mode = ssl.CERT_REQUIRED
            context.check_hostname = True
            context.load_default_certs()
            sock = context.wrap_socket(sock, server_hostname=self.host)
            self.sock = sock

    class _HTTPHandler(urllib.request.HTTPHandler):
        def http_open(self, req):
            return self.do_open(DNSBlockWorkaround._HTTPConnection, req)

    class _HTTPSHandler(urllib.request.HTTPSHandler):
        def https_open(self, req):
            return self.do_open(DNSBlockWorkaround._HTTPSConnection, req)


class StartupTasks:
    def __init__(self):
        self.plugin_manager = PluginManager()

    def setup_config(self):
        # is_config_updated = False
        existing_plugin_manager_config = copy.deepcopy(
            ba.app.config.get("Community Plugin Manager"))

        plugin_manager_config = ba.app.config.setdefault("Community Plugin Manager", {})
        plugin_manager_config.setdefault("Custom Sources", [])
        installed_plugins = plugin_manager_config.setdefault("Installed Plugins", {})
        for plugin_name in tuple(installed_plugins.keys()):
            plugin = PluginLocal(plugin_name)
            if not plugin.is_installed:
                del installed_plugins[plugin_name]

        # This order is the options will show up in Settings window.
        current_settings = {
            "Auto Update Plugin Manager": True,
            "Auto Update Plugins": True,
            "Auto Enable Plugins After Installation": True,
            "Notify New Plugins": True
        }
        settings = plugin_manager_config.setdefault("Settings", {})

        for setting, value in settings.items():
            if setting in current_settings:
                current_settings[setting] = value

        plugin_manager_config["Settings"] = current_settings

        if plugin_manager_config != existing_plugin_manager_config:
            ba.app.config.commit()

    async def update_plugin_manager(self):
        if not ba.app.config["Community Plugin Manager"]["Settings"]["Auto Update Plugin Manager"]:
            return
        update_details = await self.plugin_manager.get_update_details()
        if update_details:
            to_version, commit_sha = update_details
            ba.screenmessage(f"Plugin Manager is being updated to v{to_version}")
            try:
                await self.plugin_manager.update(to_version, commit_sha)
            except MD5CheckSumFailedError:
                ba.playsound(ba.getsound('error'))
            else:
                ba.screenmessage("Update successful. Restart game to reload changes.",
                                 color=(0, 1, 0))
                ba.playsound(ba.getsound('shieldUp'))

    async def update_plugins(self):
        if not ba.app.config["Community Plugin Manager"]["Settings"]["Auto Update Plugins"]:
            return
        await self.plugin_manager.setup_index()
        all_plugins = await self.plugin_manager.categories["All"].get_plugins()
        plugins_to_update = []
        for plugin in all_plugins:
            if plugin.is_installed and await plugin.get_local().is_enabled() and plugin.has_update():
                plugins_to_update.append(plugin.update())
        await asyncio.gather(*plugins_to_update)

    async def notify_new_plugins(self):
        if not ba.app.config["Community Plugin Manager"]["Settings"]["Notify New Plugins"]:
            return

        await self.plugin_manager.setup_index()
        try:
            num_of_plugins = ba.app.config["Community Plugin Manager"]["Existing Number of Plugins"]
        except Exception:
            ba.app.config["Community Plugin Manager"]["Existing Number of Plugins"] = len(await self.plugin_manager.categories["All"].get_plugins())
            num_of_plugins = ba.app.config["Community Plugin Manager"]["Existing Number of Plugins"]
            ba.app.config.commit()
            return

        new_num_of_plugins = len(await self.plugin_manager.categories["All"].get_plugins())

        if num_of_plugins < new_num_of_plugins:
            ba.screenmessage("We got new Plugins for you to try!")
            ba.app.config["Community Plugin Manager"]["Existing Number of Plugins"] = new_num_of_plugins
            ba.app.config.commit()

    async def execute(self):
        self.setup_config()
        try:
            await asyncio.gather(
                self.update_plugin_manager(),
                self.update_plugins(),
                self.notify_new_plugins(),
            )
        except urllib.error.URLError:
            pass


class Category:
    def __init__(self, meta_url, is_3rd_party=False):
        self.meta_url = meta_url
        self.is_3rd_party = is_3rd_party
        self.request_headers = HEADERS
        self._metadata = _CACHE.get("categories", {}).get(meta_url, {}).get("metadata")
        self._plugins = _CACHE.get("categories", {}).get(meta_url, {}).get("plugins")

    async def fetch_metadata(self):
        if self._metadata is None:
            request = urllib.request.Request(
                self.meta_url.format(content_type="raw", tag=CURRENT_TAG),
                headers=self.request_headers,
            )
            response = await async_send_network_request(request)
            self._metadata = json.loads(response.read())
            self.set_category_global_cache("metadata", self._metadata)
        return self

    async def is_valid(self):
        try:
            await self.fetch_metadata()
        except urllib.error.HTTPError:
            return False
        try:
            await asyncio.gather(
                self.get_name(),
                self.get_description(),
                self.get_plugins_base_url(),
                self.get_plugins(),
            )
        except KeyError:
            return False
        else:
            return True

    async def get_name(self):
        await self.fetch_metadata()
        return self._metadata["name"]

    async def get_description(self):
        await self.fetch_metadata()
        return self._metadata["description"]

    async def get_plugins_base_url(self):
        await self.fetch_metadata()
        return self._metadata["plugins_base_url"]

    async def get_plugins(self):
        if self._plugins is None:
            await self.fetch_metadata()
            self._plugins = ([
                Plugin(
                    plugin_info,
                    f"{await self.get_plugins_base_url()}/{plugin_info[0]}.py",
                    is_3rd_party=self.is_3rd_party,
                )
                for plugin_info in self._metadata["plugins"].items()
            ])
            self.set_category_global_cache("plugins", self._plugins)
        return self._plugins

    def set_category_global_cache(self, key, value):
        if "categories" not in _CACHE:
            _CACHE["categories"] = {}
        if self.meta_url not in _CACHE["categories"]:
            _CACHE["categories"][self.meta_url] = {}
        _CACHE["categories"][self.meta_url][key] = value

    def unset_category_global_cache(self):
        try:
            del _CACHE["categories"][self.meta_url]
        except KeyError:
            pass

    def cleanup(self):
        self._metadata = None
        self._plugins.clear()
        self.unset_category_global_cache()

    async def refresh(self):
        self.cleanup()
        await self.get_plugins()

    def save(self):
        ba.app.config["Community Plugin Manager"]["Custom Sources"].append(self.meta_url)
        ba.app.config.commit()


class CategoryAll(Category):
    def __init__(self, plugins={}):
        super().__init__(meta_url=None)
        self._name = "All"
        self._description = "All plugins"
        self._plugins = plugins


class PluginLocal:
    def __init__(self, name):
        """
        Initialize a plugin locally installed on the device.
        """
        self.name = name
        self.install_path = os.path.join(PLUGIN_DIRECTORY, f"{name}.py")
        self._entry_point_initials = f"{self.name}."
        self.cleanup()

    def cleanup(self):
        self._content = None
        self._api_version = None
        self._entry_points = []
        self._has_minigames = None

    @property
    def is_installed(self):
        return os.path.isfile(self.install_path)

    @property
    def is_installed_via_plugin_manager(self):
        return self.name in ba.app.config["Community Plugin Manager"]["Installed Plugins"]

    def initialize(self):
        if self.name not in ba.app.config["Community Plugin Manager"]["Installed Plugins"]:
            ba.app.config["Community Plugin Manager"]["Installed Plugins"][self.name] = {}
        return self

    async def uninstall(self):
        if await self.has_minigames():
            self.unload_minigames()
        try:
            os.remove(self.install_path)
        except FileNotFoundError:
            pass
        try:
            del ba.app.config["Community Plugin Manager"]["Installed Plugins"][self.name]
        except KeyError:
            pass
        else:
            self.save()

    @property
    def version(self):
        try:
            version = (ba.app.config["Community Plugin Manager"]
                       ["Installed Plugins"][self.name]["version"])
        except KeyError:
            version = None
        return version

    def _get_content(self):
        with open(self.install_path, "rb") as fin:
            return fin.read()

    def _set_content(self, content):
        with open(self.install_path, "wb") as fout:
            fout.write(content)

    def has_settings(self):
        for plugin_entry_point, plugin_class in ba.app.plugins.active_plugins.items():
            if plugin_entry_point.startswith(self._entry_point_initials):
                return plugin_class.has_settings_ui()

    def launch_settings(self, source_widget):
        for plugin_entry_point, plugin_class in ba.app.plugins.active_plugins.items():
            if plugin_entry_point.startswith(self._entry_point_initials):
                return plugin_class.show_settings_ui(source_widget)

    async def get_content(self):
        if self._content is None:
            if not self.is_installed:
                raise PluginNotInstalledError("Plugin is not available locally.")
            loop = asyncio.get_event_loop()
            self._content = await loop.run_in_executor(None, self._get_content)
        return self._content

    async def get_api_version(self):
        if self._api_version is None:
            content = await self.get_content()
            self._api_version = REGEXP["plugin_api_version"].search(content).group()
        return self._api_version

    async def get_entry_points(self):
        if not self._entry_points:
            content = await self.get_content()
            groups = REGEXP["plugin_entry_points"].findall(content)
            # Actual entry points are stored in the first index inside the matching groups.
            entry_points = tuple(f"{self.name}.{group[1].decode('utf-8')}" for group in groups)
            self._entry_points = entry_points
        return self._entry_points

    async def has_minigames(self):
        if self._has_minigames is None:
            content = await self.get_content()
            self._has_minigames = REGEXP["minigames"].search(content) is not None
        return self._has_minigames

    async def has_plugins(self):
        entry_points = await self.get_entry_points()
        return len(entry_points) > 0

    def load_minigames(self):
        scanner = ba._meta.DirectoryScan(paths="")
        directory, module = self.install_path.rsplit(os.path.sep, 1)
        scanner._scan_module(
            pathlib.Path(directory),
            pathlib.Path(module),
        )
        scanned_results = set(ba.app.meta.scanresults.exports["ba.GameActivity"])
        for game in scanner.results.exports["ba.GameActivity"]:
            if game not in scanned_results:
                ba.screenmessage(f"{game} minigame loaded")
                ba.app.meta.scanresults.exports["ba.GameActivity"].append(game)

    def unload_minigames(self):
        scanner = ba._meta.DirectoryScan(paths="")
        directory, module = self.install_path.rsplit(os.path.sep, 1)
        scanner._scan_module(
            pathlib.Path(directory),
            pathlib.Path(module),
        )
        new_scanned_results_games = []
        for game in ba.app.meta.scanresults.exports["ba.GameActivity"]:
            if game in scanner.results.exports["ba.GameActivity"]:
                ba.screenmessage(f"{game} minigame unloaded")
            else:
                new_scanned_results_games.append(game)
        ba.app.meta.scanresults.exports["ba.GameActivity"] = new_scanned_results_games

    async def is_enabled(self):
        """
        Return True even if a single entry point is enabled or contains minigames.
        """
        if not await self.has_plugins():
            return True
        for entry_point, plugin_info in ba.app.config["Plugins"].items():
            if entry_point.startswith(self._entry_point_initials) and plugin_info["enabled"]:
                return True
        # XXX: The below logic is more accurate but less efficient, since it actually
        #      reads the local plugin file and parses entry points from it.
        # for entry_point in await self.get_entry_points():
        #     if ba.app.config["Plugins"][entry_point]["enabled"]:
        #         return True
        return False

    # XXX: Commenting this out for now, since `enable` and `disable` currently have their
    #      own separate logic.
    # async def _set_status(self, to_enable=True):
    #     for entry_point in await self.get_entry_points:
    #         if entry_point not in ba.app.config["Plugins"]:
    #             ba.app.config["Plugins"][entry_point] = {}
    #         ba.app.config["Plugins"][entry_point]["enabled"] = to_enable

    async def enable(self):
        for entry_point in await self.get_entry_points():
            if entry_point not in ba.app.config["Plugins"]:
                ba.app.config["Plugins"][entry_point] = {}
            ba.app.config["Plugins"][entry_point]["enabled"] = True
            if entry_point not in ba.app.plugins.active_plugins:
                self.load_plugin(entry_point)
                ba.screenmessage(f"{entry_point} loaded")
        if await self.has_minigames():
            self.load_minigames()
        # await self._set_status(to_enable=True)
        self.save()

    def load_plugin(self, entry_point):
        plugin_class = ba._general.getclass(entry_point, ba.Plugin)
        loaded_plugin_class = plugin_class()
        loaded_plugin_class.on_app_running()
        ba.app.plugins.active_plugins[entry_point] = loaded_plugin_class

    def disable(self):
        for entry_point, plugin_info in ba.app.config["Plugins"].items():
            if entry_point.startswith(self._entry_point_initials):
                # if plugin_info["enabled"]:
                plugin_info["enabled"] = False
        # XXX: The below logic is more accurate but less efficient, since it actually
        #      reads the local plugin file and parses entry points from it.
        # await self._set_status(to_enable=False)
        self.save()

    def set_version(self, version):
        app = ba.app
        app.config["Community Plugin Manager"]["Installed Plugins"][self.name]["version"] = version
        return self

    # def set_entry_points(self):
    #     if not "entry_points" in ba.app.config["Community Plugin Manager"]
    #                                                            ["Installed Plugins"][self.name]:
    #         ba.app.config["Community Plugin Manager"]["Installed Plugins"]
    #                                                             [self.name]["entry_points"] = []
    #     for entry_point in await self.get_entry_points():
    #         ba.app.config["Community Plugin Manager"]["Installed Plugins"][self.name]
    #                                                         ["entry_points"].append(entry_point)

    async def set_content(self, content):
        if not self._content:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._set_content, content)
            self._content = content
        return self

    async def set_content_from_network_response(self, request, md5sum=None, retries=3):
        if not self._content:
            self._content = await async_stream_network_response_to_file(
                request,
                self.install_path,
                md5sum=md5sum,
                retries=retries,
            )
        return self._content

    def save(self):
        ba.app.config.commit()
        return self


class PluginVersion:
    def __init__(self, plugin, version, tag=None):
        self.number, info = version
        self.plugin = plugin
        self.api_version = info["api_version"]
        self.commit_sha = info["commit_sha"]
        self.md5sum = info["md5sum"]

        if tag is None:
            tag = self.commit_sha

        self.download_url = self.plugin.url.format(content_type="raw", tag=tag)
        self.view_url = self.plugin.url.format(content_type="blob", tag=tag)

    def __eq__(self, plugin_version):
        return (self.number, self.plugin.name) == (plugin_version.number,
                                                   plugin_version.plugin.name)

    def __repr__(self):
        return f"<PluginVersion({self.plugin.name} {self.number})>"

    async def _download(self, retries=3):
        local_plugin = self.plugin.create_local()
        await local_plugin.set_content_from_network_response(
            self.download_url,
            md5sum=self.md5sum,
            retries=retries,
        )
        local_plugin.set_version(self.number)
        local_plugin.save()
        return local_plugin

    async def install(self, suppress_screenmessage=False):
        try:
            local_plugin = await self._download()
        except MD5CheckSumFailedError:
            if not suppress_screenmessage:
                ba.screenmessage(
                    f"{self.plugin.name} failed MD5 checksum during installation", color=(1, 0, 0))
            return False
        else:
            if not suppress_screenmessage:
                ba.screenmessage(f"{self.plugin.name} installed", color=(0, 1, 0))
            check = ba.app.config["Community Plugin Manager"]["Settings"]
            if check["Auto Enable Plugins After Installation"]:
                await local_plugin.enable()
            return True


class Plugin:
    def __init__(self, plugin, url, is_3rd_party=False):
        """
        Initialize a plugin from network repository.
        """
        self.name, self.info = plugin
        self.is_3rd_party = is_3rd_party
        self.install_path = os.path.join(PLUGIN_DIRECTORY, f"{self.name}.py")
        # if is_3rd_party:
        #     tag = CURRENT_TAG
        # else:
        #     tag = CURRENT_TAG
        tag = CURRENT_TAG
        self.url = url
        self.download_url = url.format(content_type="raw", tag=tag)
        self._local_plugin = None

        self._versions = None
        self._latest_version = None
        self._latest_compatible_version = None

    def __repr__(self):
        return f"<Plugin({self.name})>"

    @property
    def view_url(self):
        if self.latest_compatible_version == self.latest_version:
            tag = CURRENT_TAG
        else:
            tag = self.latest_compatible_version.commit_sha
        return self.url.format(content_type="blob", tag=tag)

    @property
    def is_installed(self):
        return os.path.isfile(self.install_path)

    @property
    def versions(self):
        if self._versions is None:
            self._versions = [
                PluginVersion(
                    self,
                    version,
                ) for version in self.info["versions"].items()
            ]
        return self._versions

    @property
    def latest_version(self):
        if self._latest_version is None:
            self._latest_version = PluginVersion(
                self,
                tuple(self.info["versions"].items())[0],
                tag=CURRENT_TAG,
            )
        return self._latest_version

    @property
    def latest_compatible_version(self):
        if self._latest_compatible_version is None:
            for number, info in self.info["versions"].items():
                if info["api_version"] == ba.app.api_version:
                    self._latest_compatible_version = PluginVersion(
                        self,
                        (number, info),
                        CURRENT_TAG if self.latest_version.number == number else None
                    )
                    break
        if self._latest_compatible_version is None:
            raise NoCompatibleVersionError(
                f"{self.name} has no version compatible with API {ba.app.api_version}."
            )
        return self._latest_compatible_version

    def get_local(self):
        if not self.is_installed:
            raise PluginNotInstalledError(
                f"{self.name} needs to be installed to get its local plugin.")
        if self._local_plugin is None:
            self._local_plugin = PluginLocal(self.name)
        return self._local_plugin

    def create_local(self):
        return (
            PluginLocal(self.name)
            .initialize()
        )

    async def uninstall(self):
        await self.get_local().uninstall()
        ba.screenmessage(f"{self.name} uninstalled", color=(0.9, 1, 0))

    def has_update(self):
        try:
            latest_compatible_version = self.latest_compatible_version
        except NoCompatibleVersionError:
            return False
        else:
            return self.get_local().version != latest_compatible_version.number

    async def update(self):
        if await self.latest_compatible_version.install(suppress_screenmessage=True):
            ba.screenmessage(f"{self.name} updated to {self.latest_compatible_version.number}",
                             color=(0, 1, 0))
            ba.playsound(ba.getsound('shieldUp'))
        else:
            ba.screenmessage(f"{self.name} failed MD5 checksum while updating to "
                             f"{self.latest_compatible_version.number}",
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))


class PluginWindow(popup.PopupWindow):
    def __init__(self, plugin, origin_widget, button_callback=lambda: None):
        self.plugin = plugin
        self.button_callback = button_callback
        self.scale_origin = origin_widget.get_screen_space_center()
        loop = asyncio.get_event_loop()
        loop.create_task(self.draw_ui())

    def get_description(self, minimum_character_offset=40):
        """
        Splits the loong plugin description into multiple lines.
        """
        string = self.plugin.info["description"]
        string_length = len(string)

        partitioned_string = ""
        partitioned_string_length = len(partitioned_string)

        while partitioned_string_length != string_length:
            next_empty_space = string[partitioned_string_length +
                                      minimum_character_offset:].find(" ")
            next_word_end_position = partitioned_string_length + \
                minimum_character_offset + max(0, next_empty_space)
            partitioned_string += string[partitioned_string_length:next_word_end_position]
            if next_empty_space != -1:
                # Insert a line break here, there's still more partitioning to do.
                partitioned_string += "\n"
            partitioned_string_length = len(partitioned_string)

        return partitioned_string

    async def draw_ui(self):
        # print(ba.app.plugins.active_plugins)

        play_sound()
        b_text_color = (0.75, 0.7, 0.8)
        s = 1.1 if _uiscale is ba.UIScale.SMALL else 1.27 if ba.UIScale.MEDIUM else 1.57
        width = 360 * s
        height = 100 + 100 * s
        color = (1, 1, 1)
        text_scale = 0.7 * s
        self._transition_out = 'out_scale'
        transition = 'in_scale'

        self._root_widget = ba.containerwidget(size=(width, height),
                                               # parent=_ba.get_special_widget(
                                               #     'overlay_stack'),
                                               on_outside_click_call=self._ok,
                                               transition=transition,
                                               scale=(2.1 if _uiscale is ba.UIScale.SMALL else 1.5
                                                      if _uiscale is ba.UIScale.MEDIUM else 1.0),
                                               scale_origin_stack_offset=self.scale_origin)

        pos = height * 0.8
        plugin_title = f"{self.plugin.name} (v{self.plugin.latest_compatible_version.number})"
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.49, pos), size=(0, 0),
                      h_align='center', v_align='center', text=plugin_title,
                      scale=text_scale * 1.25, color=color,
                      maxwidth=width * 0.9)
        pos -= 25
        # author =
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.49, pos),
                      size=(0, 0),
                      h_align='center',
                      v_align='center',
                      text='by ' + self.plugin.info["authors"][0]["name"],
                      scale=text_scale * 0.8,
                      color=color, maxwidth=width * 0.9)
        pos -= 35
        # status = ba.textwidget(parent=self._root_widget,
        #                        position=(width * 0.49, pos), size=(0, 0),
        #                        h_align='center', v_align='center',
        #                        text=status_text, scale=text_scale * 0.8,
        #                        color=color, maxwidth=width * 0.9)
        pos -= 25
        # info =
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.49, pos), size=(0, 0),
                      h_align='center', v_align='center',
                      text=self.get_description(),
                      scale=text_scale * 0.6, color=color,
                      maxwidth=width * 0.95)
        b1_color = None
        b2_color = (0.8, 0.15, 0.35)
        b3_color = (0.2, 0.8, 0.3)
        pos = height * 0.1
        button_size = (80 * s, 40 * s)

        to_draw_button1 = True
        to_draw_button4 = False
        if self.plugin.is_installed:
            self.local_plugin = self.plugin.get_local()
            if not await self.local_plugin.has_plugins():
                to_draw_button1 = False
            else:
                if await self.local_plugin.is_enabled():
                    button1_label = "Disable"
                    b1_color = (0.6, 0.53, 0.63)
                    button1_action = self.disable
                    if self.local_plugin.has_settings():
                        to_draw_button4 = True
                else:
                    button1_label = "Enable"
                    button1_action = self.enable
            button2_label = "Uninstall"
            button2_action = self.uninstall
            has_update = self.plugin.has_update()
            if has_update:
                button3_label = "Update"
                button3_action = self.update
        else:
            button1_label = "Install"
            button1_action = self.install

        if to_draw_button1:
            ba.buttonwidget(parent=self._root_widget,
                            position=(width * 0.1, pos),
                            size=button_size,
                            on_activate_call=button1_action,
                            color=b1_color,
                            textcolor=b_text_color,
                            button_type='square',
                            text_scale=1,
                            label=button1_label)

        if self.plugin.is_installed:
            ba.buttonwidget(parent=self._root_widget,
                            position=(width * 0.4, pos),
                            size=button_size,
                            on_activate_call=button2_action,
                            color=b2_color,
                            textcolor=b_text_color,
                            button_type='square',
                            text_scale=1,
                            label=button2_label)

            if has_update:
                # button3 =
                ba.buttonwidget(parent=self._root_widget,
                                position=(width * 0.7, pos),
                                size=button_size,
                                on_activate_call=button3_action,
                                color=b3_color,
                                textcolor=b_text_color,
                                autoselect=True,
                                button_type='square',
                                text_scale=1,
                                label=button3_label)
        ba.containerwidget(edit=self._root_widget,
                           on_cancel_call=self._ok)

        open_pos_x = (300 if _uiscale is ba.UIScale.SMALL else
                      360 if _uiscale is ba.UIScale.MEDIUM else 350)
        open_pos_y = (100 if _uiscale is ba.UIScale.SMALL else
                      110 if _uiscale is ba.UIScale.MEDIUM else 120)
        open_button = ba.buttonwidget(parent=self._root_widget,
                                      autoselect=True,
                                      position=(open_pos_x, open_pos_y),
                                      size=(40, 40),
                                      button_type="square",
                                      label="",
                                      # color=ba.app.ui.title_color,
                                      color=(0.6, 0.53, 0.63),
                                      on_activate_call=lambda: ba.open_url(self.plugin.view_url))
        ba.imagewidget(parent=self._root_widget,
                       position=(open_pos_x, open_pos_y),
                       size=(40, 40),
                       color=(0.8, 0.95, 1),
                       texture=ba.gettexture("file"),
                       draw_controller=open_button)
        ba.textwidget(parent=self._root_widget,
                      position=(open_pos_x-3, open_pos_y+12),
                      text="Source",
                      size=(10, 10),
                      draw_controller=open_button,
                      color=(1, 1, 1, 1),
                      rotate=25,
                      scale=0.45)

        # Below snippet handles the tutorial button in the plugin window
        tutorial_url = self.plugin.info["external_url"]
        if tutorial_url:
            def tutorial_confirm_window():
                text = "This will take you to \n\""+self.plugin.info["external_url"] + "\""
                tutorial_confirm_window = confirm.ConfirmWindow(
                    text=text,
                    action=lambda: ba.open_url(self.plugin.info["external_url"]),
                )
            open_pos_x = (350 if _uiscale is ba.UIScale.SMALL else
                          410 if _uiscale is ba.UIScale.MEDIUM else 400)
            open_pos_y = (100 if _uiscale is ba.UIScale.SMALL else
                          110 if _uiscale is ba.UIScale.MEDIUM else 120)
            open_button = ba.buttonwidget(parent=self._root_widget,
                                          autoselect=True,
                                          position=(open_pos_x, open_pos_y),
                                          size=(40, 40),
                                          button_type="square",
                                          label="",
                                          # color=ba.app.ui.title_color,
                                          color=(0.6, 0.53, 0.63),

                                          on_activate_call=tutorial_confirm_window)

            ba.imagewidget(parent=self._root_widget,
                           position=(open_pos_x, open_pos_y),
                           size=(40, 40),
                           color=(0.8, 0.95, 1),
                           texture=ba.gettexture("frameInset"),
                           draw_controller=open_button)
            ba.textwidget(parent=self._root_widget,
                          position=(open_pos_x - 3, open_pos_y + 12),
                          text="Tutorial",
                          size=(10, 10),
                          draw_controller=open_button,
                          color=(1, 1, 1, 1),
                          rotate=25,
                          scale=0.45)

        if to_draw_button4:
            settings_pos_x = (60 if _uiscale is ba.UIScale.SMALL else
                              60 if _uiscale is ba.UIScale.MEDIUM else 60)
            settings_pos_y = (100 if _uiscale is ba.UIScale.SMALL else
                              110 if _uiscale is ba.UIScale.MEDIUM else 120)
            settings_button = ba.buttonwidget(parent=self._root_widget,
                                              autoselect=True,
                                              position=(settings_pos_x, settings_pos_y),
                                              size=(40, 40),
                                              button_type="square",
                                              label="",
                                              color=(0, 0.75, 0.75),)
            ba.buttonwidget(
                edit=settings_button,
                on_activate_call=ba.Call(self.settings, settings_button),)
            ba.imagewidget(parent=self._root_widget,
                           position=(settings_pos_x, settings_pos_y),
                           size=(40, 40),
                           color=(0.8, 0.95, 1),
                           texture=ba.gettexture("settingsIcon"),
                           draw_controller=settings_button)

        # ba.containerwidget(edit=self._root_widget, selected_child=button3)
        # ba.containerwidget(edit=self._root_widget, start_button=button3)

    def _ok(self) -> None:
        play_sound()
        ba.containerwidget(edit=self._root_widget, transition='out_scale')

    def button(fn):
        async def asyncio_handler(fn, self, *args, **kwargs):
            await fn(self, *args, **kwargs)
            await self.button_callback()

        def wrapper(self, *args, **kwargs):
            self._ok()
            loop = asyncio.get_event_loop()
            if asyncio.iscoroutinefunction(fn):
                loop.create_task(asyncio_handler(fn, self, *args, **kwargs))
            else:
                fn(self, *args, **kwargs)
                loop.create_task(self.button_callback())

        return wrapper

    def settings(self, source_widget):
        self.local_plugin.launch_settings(source_widget)

    @button
    def disable(self) -> None:
        self.local_plugin.disable()

    @button
    async def enable(self) -> None:
        await self.local_plugin.enable()
        ba.playsound(ba.getsound('gunCocking'))

    @button
    async def install(self):
        await self.plugin.latest_compatible_version.install()
        ba.playsound(ba.getsound('cashRegister2'))

    @button
    async def uninstall(self):
        await self.plugin.uninstall()
        ba.playsound(ba.getsound('shieldDown'))

    @button
    async def update(self):
        await self.plugin.update()
        ba.playsound(ba.getsound('shieldUp'))


class PluginManager:
    def __init__(self):
        self.request_headers = HEADERS
        self._index = _CACHE.get("index", {})
        self.categories = {}
        self.module_path = sys.modules[__name__].__file__
        self._index_setup_in_progress = False

    async def get_index(self):
        if not self._index:
            request = urllib.request.Request(
                INDEX_META.format(
                    repository_url=REPOSITORY_URL,
                    content_type="raw",
                    tag=CURRENT_TAG
                ),
                headers=self.request_headers,
            )
            response = await async_send_network_request(request)
            index = json.loads(response.read())
            self.set_index_global_cache(index)
            self._index = index
        return self._index

    async def setup_index(self):
        while self._index_setup_in_progress:
            # Avoid making multiple network calls to the same resource in parallel.
            # Rather wait for the previous network call to complete.
            await asyncio.sleep(0.1)
        self._index_setup_in_progress = not bool(self._index)
        index = await self.get_index()
        await self.setup_plugin_categories(index)
        self._index_setup_in_progress = False

    async def setup_plugin_categories(self, plugin_index):
        # A hack to have the "All" category show at the top.
        self.categories["All"] = None

        requests = []
        for plugin_category_url in plugin_index["categories"]:
            category = Category(plugin_category_url)
            request = category.fetch_metadata()
            requests.append(request)
        for repository in ba.app.config["Community Plugin Manager"]["Custom Sources"]:
            plugin_category_url = partial_format(plugin_index["external_source_url"],
                                                 repository=repository)
            category = Category(plugin_category_url, is_3rd_party=True)
            request = category.fetch_metadata()
            requests.append(request)
        categories = await asyncio.gather(*requests)

        all_plugins = []
        for category in categories:
            self.categories[await category.get_name()] = category
            all_plugins.extend(await category.get_plugins())
        self.categories["All"] = CategoryAll(plugins=all_plugins)

    def cleanup(self):
        for category in self.categories.values():
            if category is not None:
                category.cleanup()
        self.categories.clear()
        self._index.clear()
        self.unset_index_global_cache()

    async def refresh(self):
        self.cleanup()
        await self.setup_index()

    def set_index_global_cache(self, index):
        _CACHE["index"] = index

    def unset_index_global_cache(self):
        try:
            del _CACHE["index"]
        except KeyError:
            pass

    async def get_update_details(self):
        index = await self.get_index()
        for version, info in index["versions"].items():
            if info["api_version"] != ba.app.api_version:
                # No point checking a version of the API game doesn't support.
                continue
            if version == PLUGIN_MANAGER_VERSION:
                # We're already on the latest version for the current API.
                return
            else:
                if next(iter(index["versions"])) == version:
                    # Version on the top is the latest, so no need to specify
                    # the commit SHA explicitly to GitHub to access the latest file.
                    commit_sha = None
                else:
                    commit_sha = info["commit_sha"]
                return version, commit_sha

    async def update(self, to_version=None, commit_sha=None):
        index = await self.get_index()
        if to_version is None:
            to_version, commit_sha = await self.get_update_details()
        to_version_info = index["versions"][to_version]
        tag = commit_sha or CURRENT_TAG
        download_url = index["plugin_manager_url"].format(
            content_type="raw",
            tag=tag,
        )
        response = await async_send_network_request(download_url)
        content = response.read()
        if hashlib.md5(content).hexdigest() != to_version_info["md5sum"]:
            raise MD5CheckSumFailedError("MD5 checksum failed during plugin manager update.")
        with open(self.module_path, "wb") as fout:
            fout.write(content)
        return to_version_info

    async def soft_refresh(self):
        pass


class PluginSourcesWindow(popup.PopupWindow):
    def __init__(self, origin_widget):
        play_sound()
        self.selected_source = None

        self.scale_origin = origin_widget.get_screen_space_center()

        b_textcolor = (0.75, 0.7, 0.8)
        # s = 1.1 if _uiscale is ba.UIScale.SMALL else 1.27 if ba.UIScale.MEDIUM else 1.57
        # text_scale = 0.7 * s
        self._transition_out = 'out_scale'
        transition = 'in_scale'
        self._root_widget = ba.containerwidget(size=(400, 340),
                                               # parent=_ba.get_special_widget(
                                               #     'overlay_stack'),
                                               on_outside_click_call=self._ok,
                                               transition=transition,
                                               scale=(2.1 if _uiscale is ba.UIScale.SMALL else 1.5
                                                      if _uiscale is ba.UIScale.MEDIUM else 1.0),
                                               scale_origin_stack_offset=self.scale_origin,
                                               on_cancel_call=self._ok)

        ba.textwidget(
            parent=self._root_widget,
            position=(155, 300),
            size=(100, 25),
            text="Custom Plugin Sources",
            color=ba.app.ui.title_color,
            scale=0.8,
            h_align="center",
            v_align="center",
            maxwidth=270,
        )

        scroll_size_x = (290 if _uiscale is ba.UIScale.SMALL else
                         300 if _uiscale is ba.UIScale.MEDIUM else 290)
        scroll_size_y = (170 if _uiscale is ba.UIScale.SMALL else
                         185 if _uiscale is ba.UIScale.MEDIUM else 180)
        scroll_pos_x = (55 if _uiscale is ba.UIScale.SMALL else
                        40 if _uiscale is ba.UIScale.MEDIUM else 60)
        scroll_pos_y = 105

        self._scrollwidget = ba.scrollwidget(parent=self._root_widget,
                                             size=(scroll_size_x, scroll_size_y),
                                             position=(scroll_pos_x, scroll_pos_y))
        self._columnwidget = ba.columnwidget(parent=self._scrollwidget,
                                             border=1,
                                             margin=0)

        delete_source_button_position_pos_x = 360
        delete_source_button_position_pos_y = 110
        delete_source_button = ba.buttonwidget(parent=self._root_widget,
                                               position=(delete_source_button_position_pos_x,
                                                         delete_source_button_position_pos_y),
                                               size=(25, 25),
                                               on_activate_call=self.delete_selected_source,
                                               label="",
                                               # texture=ba.gettexture("crossOut"),
                                               button_type="square",
                                               color=(0.6, 0, 0),
                                               textcolor=b_textcolor,
                                               # autoselect=True,
                                               text_scale=1)

        ba.imagewidget(parent=self._root_widget,
                       position=(delete_source_button_position_pos_x + 2,
                                 delete_source_button_position_pos_y),
                       size=(25, 25),
                       color=(5, 2, 2),
                       texture=ba.gettexture("crossOut"),
                       draw_controller=delete_source_button)

        warning_pos_x = (43 if _uiscale is ba.UIScale.SMALL else
                         35 if _uiscale is ba.UIScale.MEDIUM else
                         48)
        ba.textwidget(
            parent=self._root_widget,
            position=(warning_pos_x, 74),
            size=(50, 22),
            text=("Warning: 3rd party plugin sources are not moderated\n"
                  "               by the community and may be dangerous!"),
            color=(1, 0.23, 0.23),
            scale=0.5,
            h_align="left",
            v_align="center",
            maxwidth=400,
        )

        self._add_source_widget = ba.textwidget(parent=self._root_widget,
                                                # text="rikkolovescats/sahilp-plugins",
                                                size=(335, 50),
                                                position=(21, 22),
                                                h_align='left',
                                                v_align='center',
                                                editable=True,
                                                scale=0.75,
                                                maxwidth=215,
                                                # autoselect=True,
                                                description="Add Source")

        loop = asyncio.get_event_loop()

        ba.buttonwidget(parent=self._root_widget,
                        position=(330, 28),
                        size=(37, 37),
                        on_activate_call=lambda: loop.create_task(self.add_source()),
                        label="",
                        texture=ba.gettexture("startButton"),
                        # texture=ba.gettexture("chestOpenIcon"),
                        button_type="square",
                        color=(0, 0.9, 0),
                        textcolor=b_textcolor,
                        # autoselect=True,
                        text_scale=1)

        self.draw_sources()

    def draw_sources(self):
        for plugin in self._columnwidget.get_children():
            plugin.delete()

        color = (1, 1, 1)
        for custom_source in ba.app.config["Community Plugin Manager"]["Custom Sources"]:
            ba.textwidget(parent=self._columnwidget,
                          # size=(410, 30),
                          selectable=True,
                          # always_highlight=True,
                          color=color,
                          text=custom_source,
                          # click_activate=True,
                          on_select_call=lambda: self.select_source(custom_source),
                          h_align='left',
                          v_align='center',
                          scale=0.75,
                          maxwidth=260)

    def select_source(self, source):
        self.selected_source = source

    async def add_source(self):
        source = ba.textwidget(query=self._add_source_widget)
        meta_url = _CACHE["index"]["external_source_url"].format(
            repository=source,
            content_type="raw",
            tag=CURRENT_TAG
        )
        category = Category(meta_url, is_3rd_party=True)
        if not await category.is_valid():
            ba.screenmessage("Enter a valid plugin source", color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return
        if source in ba.app.config["Community Plugin Manager"]["Custom Sources"]:
            ba.screenmessage("Plugin source already exists")
            ba.playsound(ba.getsound('error'))
            return
        ba.app.config["Community Plugin Manager"]["Custom Sources"].append(source)
        ba.app.config.commit()
        ba.screenmessage("Plugin source added; Refresh plugin list to see changes",
                         color=(0, 1, 0))
        ba.playsound(ba.getsound('cashRegister2'))
        self.draw_sources()

    def delete_selected_source(self):
        if self.selected_source is None:
            return
        ba.app.config["Community Plugin Manager"]["Custom Sources"].remove(self.selected_source)
        ba.app.config.commit()
        ba.screenmessage("Plugin source deleted; Refresh plugin list to see changes",
                         color=(0.9, 1, 0))
        ba.playsound(ba.getsound('shieldDown'))
        self.draw_sources()

    def _ok(self) -> None:
        play_sound()
        ba.containerwidget(edit=self._root_widget, transition='out_scale')


class PluginCategoryWindow(popup.PopupMenuWindow):
    def __init__(self, choices, current_choice, origin_widget, asyncio_callback):
        choices = (*choices, "Custom Sources")
        self._asyncio_callback = asyncio_callback
        self.scale_origin = origin_widget.get_screen_space_center()
        super().__init__(
            position=(200, 0),
            scale=(2.3 if _uiscale is ba.UIScale.SMALL else
                   1.65 if _uiscale is ba.UIScale.MEDIUM else 1.23),
            choices=choices,
            current_choice=current_choice,
            delegate=self)
        self._update_custom_sources_widget()

    def _update_custom_sources_widget(self):
        ba.textwidget(edit=self._columnwidget.get_children()[-1],
                      color=(0.5, 0.5, 0.5),
                      on_activate_call=self.show_sources_window)

    def popup_menu_selected_choice(self, window, choice):
        loop = asyncio.get_event_loop()
        loop.create_task(self._asyncio_callback(choice))

    def popup_menu_closing(self, window):
        pass

    def show_sources_window(self):
        self._ok()
        PluginSourcesWindow(origin_widget=self.root_widget)

    def _ok(self) -> None:
        play_sound()
        ba.containerwidget(edit=self.root_widget, transition='out_scale')


class PluginManagerWindow(ba.Window):
    def __init__(self, transition: str = "in_right", origin_widget: ba.Widget = None):
        self.plugin_manager = PluginManager()
        self.category_selection_button = None
        self.selected_category = None
        self.plugins_in_current_view = {}

        loop = asyncio.get_event_loop()
        loop.create_task(self.draw_index())

        self._width = (700 if _uiscale is ba.UIScale.SMALL
                       else 550 if _uiscale is ba.UIScale.MEDIUM
                       else 570)
        self._height = (500 if _uiscale is ba.UIScale.SMALL
                        else 422 if _uiscale is ba.UIScale.MEDIUM
                        else 500)
        top_extra = 20 if _uiscale is ba.UIScale.SMALL else 0

        if origin_widget:
            self._transition_out = "out_scale"
            self._scale_origin = origin_widget.get_screen_space_center()
            transition = "in_scale"

        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height + top_extra),
            transition=transition,
            toolbar_visibility="menu_minimal",
            scale_origin_stack_offset=self._scale_origin,
            scale=(1.9 if _uiscale is ba.UIScale.SMALL
                   else 1.5 if _uiscale is ba.UIScale.MEDIUM
                   else 1.0),
            stack_offset=(0, -25) if _uiscale is ba.UIScale.SMALL else (0, 0)
        ))

        back_pos_x = 5 + (37 if _uiscale is ba.UIScale.SMALL else
                          27 if _uiscale is ba.UIScale.MEDIUM else 68)
        back_pos_y = self._height - (95 if _uiscale is ba.UIScale.SMALL else
                                     65 if _uiscale is ba.UIScale.MEDIUM else 50)
        self._back_button = back_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(back_pos_x, back_pos_y),
            size=(60, 60),
            scale=0.8,
            label=ba.charstr(ba.SpecialChar.BACK),
            # autoselect=True,
            button_type='backSmall',
            on_activate_call=self._back)

        ba.containerwidget(edit=self._root_widget, cancel_button=back_button)

        title_pos = self._height - (83 if _uiscale is ba.UIScale.SMALL else
                                    50 if _uiscale is ba.UIScale.MEDIUM else 50)
        ba.textwidget(
            parent=self._root_widget,
            position=(-10, title_pos),
            size=(self._width, 25),
            text="Community Plugin Manager",
            color=ba.app.ui.title_color,
            scale=1.05,
            h_align="center",
            v_align="center",
            maxwidth=270,
        )

        loading_pos_y = self._height - (275 if _uiscale is ba.UIScale.SMALL else
                                        235 if _uiscale is ba.UIScale.MEDIUM else 270)

        self._plugin_manager_status_text = ba.textwidget(
            parent=self._root_widget,
            position=(-5, loading_pos_y),
            size=(self._width, 25),
            text="Loading...",
            color=ba.app.ui.title_color,
            scale=0.7,
            h_align="center",
            v_align="center",
            maxwidth=400,
        )

    def _back(self) -> None:
        from bastd.ui.settings.allsettings import AllSettingsWindow
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            AllSettingsWindow(transition='in_left').get_root_widget())

    @contextlib.contextmanager
    def exception_handler(self):
        try:
            yield
        except urllib.error.URLError:
            ba.textwidget(edit=self._plugin_manager_status_text,
                          text="Make sure you are connected\n to the Internet and try again.")
        except RuntimeError:
            # User probably went back before a ba.Window could finish loading.
            pass

    async def draw_index(self):
        self.draw_search_bar()
        self.draw_plugins_scroll_bar()
        self.draw_category_selection_button(post_label="All")
        self.draw_refresh_icon()
        self.draw_settings_icon()
        with self.exception_handler():
            await self.plugin_manager.setup_index()
            ba.textwidget(edit=self._plugin_manager_status_text,
                          text="")
            await self.select_category("All")

    def draw_plugins_scroll_bar(self):
        scroll_size_x = (515 if _uiscale is ba.UIScale.SMALL else
                         430 if _uiscale is ba.UIScale.MEDIUM else 420)
        scroll_size_y = (245 if _uiscale is ba.UIScale.SMALL else
                         265 if _uiscale is ba.UIScale.MEDIUM else 335)
        scroll_pos_x = (70 if _uiscale is ba.UIScale.SMALL else
                        50 if _uiscale is ba.UIScale.MEDIUM else 70)
        scroll_pos_y = (100 if _uiscale is ba.UIScale.SMALL else
                        35 if _uiscale is ba.UIScale.MEDIUM else 40)
        self._scrollwidget = ba.scrollwidget(parent=self._root_widget,
                                             size=(scroll_size_x, scroll_size_y),
                                             position=(scroll_pos_x, scroll_pos_y))
        self._columnwidget = ba.columnwidget(parent=self._scrollwidget,
                                             border=2,
                                             margin=0)

    def draw_category_selection_button(self, post_label):
        category_pos_x = (440 if _uiscale is ba.UIScale.SMALL else
                          340 if _uiscale is ba.UIScale.MEDIUM else 350)
        category_pos_y = self._height - (141 if _uiscale is ba.UIScale.SMALL else
                                         110 if _uiscale is ba.UIScale.MEDIUM else 110)
        b_size = (140, 30)
        # b_textcolor = (0.75, 0.7, 0.8)
        b_textcolor = (0.8, 0.8, 0.85)
        # b_color = (0.6, 0.53, 0.63)

        label = f"Category: {post_label}"

        if self.category_selection_button is None:
            self.category_selection_button = ba.buttonwidget(parent=self._root_widget,
                                                             position=(category_pos_x,
                                                                       category_pos_y),
                                                             size=b_size,
                                                             on_activate_call=(
                                                                 self.show_categories_window),
                                                             label=label,
                                                             button_type="square",
                                                             # color=b_color,
                                                             textcolor=b_textcolor,
                                                             # autoselect=True,
                                                             text_scale=0.6)
        else:
            self.category_selection_button = ba.buttonwidget(edit=self.category_selection_button,
                                                             label=label)

    def draw_search_bar(self):
        search_bar_pos_x = (85 if _uiscale is ba.UIScale.SMALL else
                            68 if _uiscale is ba.UIScale.MEDIUM else 90)
        search_bar_pos_y = self._height - (
            145 if _uiscale is ba.UIScale.SMALL else
            110 if _uiscale is ba.UIScale.MEDIUM else 116)

        search_bar_size_x = (320 if _uiscale is ba.UIScale.SMALL else
                             230 if _uiscale is ba.UIScale.MEDIUM else 260)
        search_bar_size_y = (
            35 if _uiscale is ba.UIScale.SMALL else
            35 if _uiscale is ba.UIScale.MEDIUM else 45)

        filter_txt_pos_x = (60 if _uiscale is ba.UIScale.SMALL else
                            40 if _uiscale is ba.UIScale.MEDIUM else 60)
        filter_txt_pos_y = search_bar_pos_y + (3 if _uiscale is ba.UIScale.SMALL else
                                               4 if _uiscale is ba.UIScale.MEDIUM else 8)

        ba.textwidget(parent=self._root_widget,
                      text="Filter",
                      position=(filter_txt_pos_x, filter_txt_pos_y),
                      selectable=False,
                      h_align='left',
                      v_align='center',
                      color=ba.app.ui.title_color,
                      scale=0.5)

        filter_txt = ba.Lstr(resource='filterText')
        search_bar_maxwidth = search_bar_size_x - (95 if _uiscale is ba.UIScale.SMALL else
                                                   77 if _uiscale is ba.UIScale.MEDIUM else
                                                   85)
        self._filter_widget = ba.textwidget(parent=self._root_widget,
                                            text="",
                                            size=(search_bar_size_x, search_bar_size_y),
                                            position=(search_bar_pos_x, search_bar_pos_y),
                                            h_align='left',
                                            v_align='center',
                                            editable=True,
                                            scale=0.8,
                                            autoselect=True,
                                            maxwidth=search_bar_maxwidth,
                                            description=filter_txt)
        self._last_filter_text = None
        self._last_filter_plugins = []
        loop = asyncio.get_event_loop()
        loop.create_task(self.process_search_term())

    async def process_search_term(self):
        while True:
            await asyncio.sleep(0.2)
            try:
                filter_text = ba.textwidget(query=self._filter_widget)
            except RuntimeError:
                # Search filter widget got destroyed. No point checking for filter text anymore.
                return
            if self.selected_category is None:
                continue
            try:
                await self.draw_plugin_names(self.selected_category, search_term=filter_text)
            except CategoryDoesNotExistError:
                pass
            # XXX: This may be more efficient, but we need a way to get a plugin's textwidget
            # attributes like color, position and more.
            # for plugin in self._columnwidget.get_children():
            # for name, widget in tuple(self.plugins_in_current_view.items()):
            #     # print(ba.textwidget(query=plugin))
            #     # plugin.delete()
            #     print(dir(widget))
            #     if filter_text in name:
            #         import random
            #         if random.random() > 0.9:
            #             ba.textwidget(edit=widget).delete()
            #         else:
            #             ba.textwidget(edit=widget, position=None)
            #     else:
            #         ba.textwidget(edit=widget, position=None)

    def draw_settings_icon(self):
        settings_pos_x = (610 if _uiscale is ba.UIScale.SMALL else
                          500 if _uiscale is ba.UIScale.MEDIUM else 510)
        settings_pos_y = (130 if _uiscale is ba.UIScale.SMALL else
                          60 if _uiscale is ba.UIScale.MEDIUM else 70)
        controller_button = ba.buttonwidget(parent=self._root_widget,
                                            # autoselect=True,
                                            position=(settings_pos_x, settings_pos_y),
                                            size=(30, 30),
                                            button_type="square",
                                            label="",
                                            on_activate_call=ba.Call(PluginManagerSettingsWindow,
                                                                     self.plugin_manager,
                                                                     self._root_widget))
        ba.imagewidget(parent=self._root_widget,
                       position=(settings_pos_x, settings_pos_y),
                       size=(30, 30),
                       color=(0.8, 0.95, 1),
                       texture=ba.gettexture("settingsIcon"),
                       draw_controller=controller_button)

    def draw_refresh_icon(self):
        refresh_pos_x = (610 if _uiscale is ba.UIScale.SMALL else
                         500 if _uiscale is ba.UIScale.MEDIUM else 510)
        refresh_pos_y = (180 if _uiscale is ba.UIScale.SMALL else
                         108 if _uiscale is ba.UIScale.MEDIUM else 120)
        loop = asyncio.get_event_loop()
        controller_button = ba.buttonwidget(parent=self._root_widget,
                                            # autoselect=True,
                                            position=(refresh_pos_x, refresh_pos_y),
                                            size=(30, 30),
                                            button_type="square",
                                            label="",
                                            on_activate_call=lambda:
                                                loop.create_task(self.refresh()))
        ba.imagewidget(parent=self._root_widget,
                       position=(refresh_pos_x, refresh_pos_y),
                       size=(30, 30),
                       color=(0.8, 0.95, 1),
                       texture=ba.gettexture("replayIcon"),
                       draw_controller=controller_button)

    def search_term_filterer(self, plugin, search_term):
        if search_term in plugin.name:
            return True
        if search_term in plugin.info["description"].lower():
            return True
        for author in plugin.info["authors"]:
            if search_term in author["name"].lower():
                return True
        return False

    # async def draw_plugin_names(self, category):
    #     for plugin in self._columnwidget.get_children():
    #         plugin.delete()

    #     plugins = await self.plugin_manager.categories[category].get_plugins()
    #     plugin_names_to_draw = tuple(self.draw_plugin_name(plugin) for plugin in plugins)
    #     await asyncio.gather(*plugin_names_to_draw)

    # XXX: Not sure if this is the best way to handle search filters.
    async def draw_plugin_names(self, category, search_term=""):
        # Re-draw plugin list UI if either search term or category was switched.
        to_draw_plugin_names = (search_term, category) != (self._last_filter_text,
                                                           self.selected_category)
        if not to_draw_plugin_names:
            return

        try:
            category_plugins = await self.plugin_manager.categories[category].get_plugins()
        except (KeyError, AttributeError):
            raise CategoryDoesNotExistError(f"{category} does not exist.")

        if search_term:
            def search_term_filterer(plugin): return self.search_term_filterer(plugin, search_term)
            plugins = filter(search_term_filterer, category_plugins)
        else:
            plugins = category_plugins

        if plugins == self._last_filter_plugins:
            # Plugins names to draw on UI are already drawn.
            return

        self._last_filter_text = search_term
        self._last_filter_plugins = plugins

        plugin_names_to_draw = tuple(self.draw_plugin_name(plugin) for plugin in plugins)

        for plugin in self._columnwidget.get_children():
            plugin.delete()

        await asyncio.gather(*plugin_names_to_draw)

    async def draw_plugin_name(self, plugin):
        try:
            latest_compatible_version = plugin.latest_compatible_version
        except NoCompatibleVersionError:
            # We currently don't show plugins that have no compatible versions.
            return

        if plugin.is_installed:
            local_plugin = plugin.get_local()
            if await local_plugin.is_enabled():
                if not local_plugin.is_installed_via_plugin_manager:
                    color = (0.8, 0.2, 0.2)
                elif local_plugin.version == latest_compatible_version.number:
                    color = (0, 0.95, 0.2)
                else:
                    color = (1, 0.6, 0)
            else:
                color = (1, 1, 1)
        else:
            color = (0.5, 0.5, 0.5)

        plugin_name_widget_to_update = self.plugins_in_current_view.get(plugin.name)
        if plugin_name_widget_to_update:
            ba.textwidget(edit=plugin_name_widget_to_update,
                          color=color)
        else:
            text_widget = ba.textwidget(parent=self._columnwidget,
                                        size=(410, 30),
                                        selectable=True,
                                        always_highlight=True,
                                        color=color,
                                        # on_select_call=lambda: None,
                                        text=plugin.name,
                                        click_activate=True,
                                        on_activate_call=lambda: self.show_plugin_window(plugin),
                                        h_align='left',
                                        v_align='center',
                                        maxwidth=420)
            self.plugins_in_current_view[plugin.name] = text_widget
            # XXX: This seems nicer. Might wanna use this in future.
            # text_widget.add_delete_callback(lambda: self.plugins_in_current_view.pop(plugin.name))

    def show_plugin_window(self, plugin):
        PluginWindow(plugin, self._root_widget, lambda: self.draw_plugin_name(plugin))

    def show_categories_window(self):
        play_sound()
        PluginCategoryWindow(
            self.plugin_manager.categories.keys(),
            self.selected_category,
            self._root_widget,
            self.select_category,
        )

    async def select_category(self, category):
        self.plugins_in_current_view.clear()
        self.draw_category_selection_button(post_label=category)
        await self.draw_plugin_names(category, search_term=self._last_filter_text)
        self.selected_category = category

    def cleanup(self):
        self.plugin_manager.cleanup()
        for plugin in self._columnwidget.get_children():
            plugin.delete()
        self.plugins_in_current_view.clear()
        self._last_filter_text = None
        self._last_filter_plugins = []

    async def refresh(self):
        self.cleanup()
        ba.textwidget(edit=self._plugin_manager_status_text,
                      text="Refreshing...")

        with self.exception_handler():
            await self.plugin_manager.refresh()
            await self.plugin_manager.setup_index()
            ba.textwidget(edit=self._plugin_manager_status_text,
                          text="")
            await self.select_category(self.selected_category)

    def soft_refresh(self):
        pass


class PluginManagerSettingsWindow(popup.PopupWindow):
    def __init__(self, plugin_manager, origin_widget):
        play_sound()
        self._plugin_manager = plugin_manager
        self.scale_origin = origin_widget.get_screen_space_center()
        self.settings = ba.app.config["Community Plugin Manager"]["Settings"].copy()
        loop = asyncio.get_event_loop()
        loop.create_task(self.draw_ui())

    async def draw_ui(self):
        b_text_color = (0.8, 0.8, 0.85)
        s = 1.25 if _uiscale is ba.UIScale.SMALL else 1.27 if _uiscale is ba.UIScale.MEDIUM else 1.3
        width = 380 * s
        height = 150 + 150 * s
        color = (0.9, 0.9, 0.9)

        # Subtracting the default bluish-purple color from the texture, so it's as close
        # as to white as possible.
        discord_fg_color = (10 - 0.32, 10 - 0.39, 10 - 0.96)
        discord_bg_color = (0.525, 0.595, 1.458)
        github_bg_color = (0.23, 0.23, 0.23)
        text_scale = 0.7 * s
        self._transition_out = 'out_scale'
        transition = 'in_scale'
        button_size = (32 * s, 32 * s)
        # index = await self._plugin_manager.get_index()
        self._root_widget = ba.containerwidget(size=(width, height),
                                               # parent=_ba.get_special_widget(
                                               #     'overlay_stack'),
                                               on_outside_click_call=self._ok,
                                               transition=transition,
                                               scale=(2.1 if _uiscale is ba.UIScale.SMALL else 1.5
                                                      if _uiscale is ba.UIScale.MEDIUM else 1.0),
                                               scale_origin_stack_offset=self.scale_origin)
        pos = height * 0.9
        setting_title = "Settings"
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.49, pos),
                      size=(0, 0),
                      h_align='center',
                      v_align='center',
                      text=setting_title,
                      scale=text_scale,
                      color=ba.app.ui.title_color,
                      maxwidth=width * 0.9)

        pos -= 20
        self._save_button = ba.buttonwidget(parent=self._root_widget,
                                            position=((width * 0.82) - button_size[0] / 2, pos),
                                            size=(73, 35),
                                            on_activate_call=self.save_settings_button,
                                            textcolor=b_text_color,
                                            button_type='square',
                                            text_scale=1,
                                            scale=0,
                                            selectable=False,
                                            label="Save")
        pos -= 40

        for setting, value in self.settings.items():
            ba.checkboxwidget(parent=self._root_widget,
                              position=(width * 0.1, pos),
                              size=(170, 30),
                              text=setting,
                              value=value,
                              on_value_change_call=ba.Call(self.toggle_setting, setting),
                              maxwidth=500,
                              textcolor=(0.9, 0.9, 0.9),
                              scale=text_scale * 0.8)
            pos -= 34 * text_scale

        pos = height - 200
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.49, pos-5),
                      size=(0, 0),
                      h_align='center',
                      v_align='center',
                      text='Contribute to plugins or to this community plugin manager!',
                      scale=text_scale * 0.65,
                      color=color,
                      maxwidth=width * 0.95)

        pos -= 75
        self.discord_button = ba.buttonwidget(parent=self._root_widget,
                                              position=((width * 0.20) - button_size[0] / 2, pos),
                                              size=button_size,
                                              on_activate_call=lambda: ba.open_url(DISCORD_URL),
                                              textcolor=b_text_color,
                                              color=discord_bg_color,
                                              button_type='square',
                                              text_scale=1,
                                              label="")

        ba.imagewidget(parent=self._root_widget,
                       position=((width * 0.20)+0.5 - button_size[0] / 2, pos),
                       size=button_size,
                       texture=ba.gettexture("discordLogo"),
                       color=discord_fg_color,
                       draw_controller=self.discord_button)

        self.github_button = ba.buttonwidget(parent=self._root_widget,
                                             position=((width * 0.49) - button_size[0] / 2, pos),
                                             size=button_size,
                                             on_activate_call=lambda: ba.open_url(REPOSITORY_URL),
                                             textcolor=b_text_color,
                                             color=github_bg_color,
                                             button_type='square',
                                             text_scale=1,
                                             label='')

        ba.imagewidget(parent=self._root_widget,
                       position=((width * 0.49) + 0.5 - button_size[0] / 2, pos),
                       size=button_size,
                       texture=ba.gettexture("githubLogo"),
                       color=(1, 1, 1),
                       draw_controller=self.github_button)

        ba.containerwidget(edit=self._root_widget,
                           on_cancel_call=self._ok)

        try:
            plugin_manager_update_available = await self._plugin_manager.get_update_details()
        except urllib.error.URLError:
            plugin_manager_update_available = False
        if plugin_manager_update_available:
            text_color = (0.75, 0.2, 0.2)
            loop = asyncio.get_event_loop()
            button_size = (95 * s, 32 * s)
            update_button_label = f'Update to v{plugin_manager_update_available[0]}'
            self._update_button = ba.buttonwidget(parent=self._root_widget,
                                                  position=((width * 0.77) - button_size[0] / 2,
                                                            pos),
                                                  size=button_size,
                                                  on_activate_call=lambda:
                                                      loop.create_task(
                                                          self.update(
                                                              *plugin_manager_update_available
                                                          )
                                                  ),
                                                  textcolor=b_text_color,
                                                  button_type='square',
                                                  text_scale=1,
                                                  color=(0, 0.7, 0),
                                                  label=update_button_label)
            self._restart_to_reload_changes_text = ba.textwidget(parent=self._root_widget,
                                                                 position=(width * 0.79, pos + 20),
                                                                 size=(0, 0),
                                                                 h_align='center',
                                                                 v_align='center',
                                                                 text='',
                                                                 scale=text_scale * 0.65,
                                                                 color=(0, 0.8, 0),
                                                                 maxwidth=width * 0.9)
        else:
            text_color = (0, 0.8, 0)
        pos -= 25
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.49, pos),
                      size=(0, 0),
                      h_align='center',
                      v_align='center',
                      text=f'Plugin Manager v{PLUGIN_MANAGER_VERSION}',
                      scale=text_scale * 0.8,
                      color=text_color,
                      maxwidth=width * 0.9)
        pos -= 25
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.49, pos),
                      size=(0, 0),
                      h_align='center',
                      v_align='center',
                      text=f'API Version: {ba.app.api_version}',
                      scale=text_scale * 0.7,
                      color=(0.4, 0.8, 1),
                      maxwidth=width * 0.95)

        pos = height * 0.1

    def toggle_setting(self, setting, set_value):
        self.settings[setting] = set_value
        if self.settings == ba.app.config["Community Plugin Manager"]["Settings"]:
            ba.buttonwidget(edit=self._save_button,
                            scale=0,
                            selectable=False)
        else:
            ba.buttonwidget(edit=self._save_button,
                            scale=1,
                            selectable=True)

    def save_settings_button(self):
        ba.app.config["Community Plugin Manager"]["Settings"] = self.settings.copy()
        ba.app.config.commit()
        self._ok()
        ba.playsound(ba.getsound('gunCocking'))

    async def update(self, to_version=None, commit_sha=None):
        try:
            await self._plugin_manager.update(to_version, commit_sha)
        except MD5CheckSumFailedError:
            ba.screenmessage("MD5 checksum failed during plugin manager update", color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
        else:
            ba.screenmessage("Plugin manager update successful", color=(0, 1, 0))
            ba.playsound(ba.getsound('shieldUp'))
            ba.textwidget(edit=self._restart_to_reload_changes_text,
                          text='Update Applied!\nRestart game to reload changes.')
            self._update_button.delete()

    def _ok(self) -> None:
        play_sound()
        ba.containerwidget(edit=self._root_widget, transition='out_scale')


class NewAllSettingsWindow(ba.Window):
    def __init__(self,
                 transition: str = "in_right",
                 origin_widget: ba.Widget = None):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        import threading

        # Preload some modules we use in a background thread so we won"t
        # have a visual hitch when the user taps them.
        threading.Thread(target=self._preload_modules).start()

        ba.set_analytics_screen("Settings Window")
        scale_origin: Optional[tuple[float, float]]
        if origin_widget is not None:
            self._transition_out = "out_scale"
            scale_origin = origin_widget.get_screen_space_center()
            transition = "in_scale"
        else:
            self._transition_out = "out_right"
            scale_origin = None
        width = 900 if _uiscale is ba.UIScale.SMALL else 670
        x_inset = 75 if _uiscale is ba.UIScale.SMALL else 0
        height = 435
        self._r = "settingsWindow"
        top_extra = 20 if _uiscale is ba.UIScale.SMALL else 0

        super().__init__(root_widget=ba.containerwidget(
            size=(width, height + top_extra),
            transition=transition,
            toolbar_visibility="menu_minimal",
            scale_origin_stack_offset=scale_origin,
            scale=(1.75 if _uiscale is ba.UIScale.SMALL else
                   1.35 if _uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -8) if _uiscale is ba.UIScale.SMALL else (0, 0)))

        if ba.app.ui.use_toolbars and _uiscale is ba.UIScale.SMALL:
            self._back_button = None
            ba.containerwidget(edit=self._root_widget,
                               on_cancel_call=self._do_back)
        else:
            self._back_button = btn = ba.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(40 + x_inset, height - 55),
                size=(130, 60),
                scale=0.8,
                text_scale=1.2,
                label=ba.Lstr(resource="backText"),
                button_type="back",
                on_activate_call=self._do_back)
            ba.containerwidget(edit=self._root_widget, cancel_button=btn)

        ba.textwidget(parent=self._root_widget,
                      position=(0, height - 44),
                      size=(width, 25),
                      text=ba.Lstr(resource=self._r + ".titleText"),
                      color=ba.app.ui.title_color,
                      h_align="center",
                      v_align="center",
                      maxwidth=130)

        if self._back_button is not None:
            ba.buttonwidget(edit=self._back_button,
                            button_type="backSmall",
                            size=(60, 60),
                            label=ba.charstr(ba.SpecialChar.BACK))

        v = height - 80
        v -= 145

        basew = 200
        baseh = 160

        x_offs = x_inset + (105 if _uiscale is ba.UIScale.SMALL else
                            72) - basew  # now unused
        x_offs2 = x_offs + basew - 7
        x_offs3 = x_offs + 2 * (basew - 7)
        x_offs4 = x_offs + 3 * (basew - 7)
        x_offs5 = x_offs2 + 0.5 * (basew - 7)
        x_offs6 = x_offs5 + (basew - 7)

        def _b_title(x: float, y: float, button: ba.Widget,
                     text: Union[str, ba.Lstr]) -> None:
            ba.textwidget(parent=self._root_widget,
                          text=text,
                          position=(x + basew * 0.47, y + baseh * 0.22),
                          maxwidth=basew * 0.7, size=(0, 0),
                          h_align="center",
                          v_align="center",
                          draw_controller=button,
                          color=(0.7, 0.9, 0.7, 1.0))

        ctb = self._controllers_button = ba.buttonwidget(parent=self._root_widget,
                                                         autoselect=True,
                                                         position=(x_offs2, v),
                                                         size=(basew, baseh),
                                                         button_type="square",
                                                         label="",
                                                         on_activate_call=self._do_controllers)
        if ba.app.ui.use_toolbars and self._back_button is None:
            bbtn = _ba.get_special_widget("back_button")
            ba.widget(edit=ctb, left_widget=bbtn)
        _b_title(x_offs2, v, ctb,
                 ba.Lstr(resource=self._r + ".controllersText"))
        imgw = imgh = 130
        ba.imagewidget(parent=self._root_widget,
                       position=(x_offs2 + basew * 0.49 - imgw * 0.5, v + 35),
                       size=(imgw, imgh),
                       texture=ba.gettexture("controllerIcon"),
                       draw_controller=ctb)

        gfxb = self._graphics_button = ba.buttonwidget(parent=self._root_widget,
                                                       autoselect=True,
                                                       position=(x_offs3, v),
                                                       size=(basew, baseh),
                                                       button_type="square",
                                                       label="",
                                                       on_activate_call=self._do_graphics)
        if ba.app.ui.use_toolbars:
            pbtn = _ba.get_special_widget("party_button")
            ba.widget(edit=gfxb, up_widget=pbtn, right_widget=pbtn)
        _b_title(x_offs3, v, gfxb, ba.Lstr(resource=self._r + ".graphicsText"))
        imgw = imgh = 110
        ba.imagewidget(parent=self._root_widget,
                       position=(x_offs3 + basew * 0.49 - imgw * 0.5, v + 42),
                       size=(imgw, imgh),
                       texture=ba.gettexture("graphicsIcon"),
                       draw_controller=gfxb)

        abtn = self._audio_button = ba.buttonwidget(parent=self._root_widget,
                                                    autoselect=True,
                                                    position=(x_offs4, v),
                                                    size=(basew, baseh),
                                                    button_type="square",
                                                    label="",
                                                    on_activate_call=self._do_audio)
        _b_title(x_offs4, v, abtn, ba.Lstr(resource=self._r + ".audioText"))
        imgw = imgh = 120
        ba.imagewidget(parent=self._root_widget,
                       position=(x_offs4 + basew * 0.49 - imgw * 0.5 + 5, v + 35),
                       size=(imgw, imgh),
                       color=(1, 1, 0), texture=ba.gettexture("audioIcon"),
                       draw_controller=abtn)
        v -= (baseh - 5)

        avb = self._advanced_button = ba.buttonwidget(parent=self._root_widget,
                                                      autoselect=True,
                                                      position=(x_offs5, v),
                                                      size=(basew, baseh),
                                                      button_type="square",
                                                      label="",
                                                      on_activate_call=self._do_advanced)
        _b_title(x_offs5, v, avb, ba.Lstr(resource=self._r + ".advancedText"))
        imgw = imgh = 120
        ba.imagewidget(parent=self._root_widget,
                       position=(x_offs5 + basew * 0.49 - imgw * 0.5 + 5,
                                 v + 35),
                       size=(imgw, imgh),
                       color=(0.8, 0.95, 1),
                       texture=ba.gettexture("advancedIcon"),
                       draw_controller=avb)

        mmb = self._modmgr_button = ba.buttonwidget(parent=self._root_widget,
                                                    autoselect=True,
                                                    position=(x_offs6, v),
                                                    size=(basew, baseh),
                                                    button_type="square",
                                                    label="",
                                                    on_activate_call=self._do_modmanager)
        _b_title(x_offs6, v, mmb, ba.Lstr(value="Plugin Manager"))
        imgw = imgh = 112
        ba.imagewidget(parent=self._root_widget,
                       position=(x_offs6 + basew * 0.49 - imgw * 0.5 + 5,
                                 v + 35),
                       size=(imgw, imgh),
                       color=(0.8, 0.95, 1),
                       texture=ba.gettexture("storeIcon"),
                       draw_controller=mmb)

        self._restore_state()

    # noinspection PyUnresolvedReferences
    @staticmethod
    def _preload_modules() -> None:
        """Preload modules we use (called in bg thread)."""
        # import bastd.ui.mainmenu as _unused1
        # import bastd.ui.settings.controls as _unused2
        # import bastd.ui.settings.graphics as _unused3
        # import bastd.ui.settings.audio as _unused4
        # import bastd.ui.settings.advanced as _unused5

    def _do_back(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.mainmenu import MainMenuWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            MainMenuWindow(transition="in_left").get_root_widget())

    def _do_controllers(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.controls import ControlsSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition="out_left")
        ba.app.ui.set_main_menu_window(ControlsSettingsWindow(
            origin_widget=self._controllers_button).get_root_widget())

    def _do_graphics(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.graphics import GraphicsSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition="out_left")
        ba.app.ui.set_main_menu_window(GraphicsSettingsWindow(
            origin_widget=self._graphics_button).get_root_widget())

    def _do_audio(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.audio import AudioSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition="out_left")
        ba.app.ui.set_main_menu_window(AudioSettingsWindow(
            origin_widget=self._audio_button).get_root_widget())

    def _do_advanced(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.advanced import AdvancedSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition="out_left")
        ba.app.ui.set_main_menu_window(AdvancedSettingsWindow(
            origin_widget=self._advanced_button).get_root_widget())

    def _do_modmanager(self) -> None:
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition="out_left")
        ba.app.ui.set_main_menu_window(PluginManagerWindow(
            origin_widget=self._modmgr_button).get_root_widget())

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._controllers_button:
                sel_name = "Controllers"
            elif sel == self._graphics_button:
                sel_name = "Graphics"
            elif sel == self._audio_button:
                sel_name = "Audio"
            elif sel == self._advanced_button:
                sel_name = "Advanced"
            elif sel == self._modmgr_button:
                sel_name = "Mod Manager"
            elif sel == self._back_button:
                sel_name = "Back"
            else:
                raise ValueError(f"unrecognized selection \"{sel}\"")
            ba.app.ui.window_states[type(self)] = {"sel_name": sel_name}
        except Exception:
            ba.print_exception(f"Error saving state for {self}.")

    def _restore_state(self) -> None:
        try:
            sel_name = ba.app.ui.window_states.get(type(self),
                                                   {}).get("sel_name")
            sel: Optional[ba.Widget]
            if sel_name == "Controllers":
                sel = self._controllers_button
            elif sel_name == "Graphics":
                sel = self._graphics_button
            elif sel_name == "Audio":
                sel = self._audio_button
            elif sel_name == "Advanced":
                sel = self._advanced_button
            elif sel_name == "Mod Manager":
                sel = self._modmgr_button
            elif sel_name == "Back":
                sel = self._back_button
            else:
                sel = self._controllers_button
            if sel is not None:
                ba.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            ba.print_exception(f"Error restoring state for {self}.")


# ba_meta export plugin
class EntryPoint(ba.Plugin):
    def on_app_running(self) -> None:
        """Called when the app is being launched."""
        from bastd.ui.settings import allsettings
        allsettings.AllSettingsWindow = NewAllSettingsWindow
        DNSBlockWorkaround.apply()
        asyncio.set_event_loop(ba._asyncio._asyncio_event_loop)
        startup_tasks = StartupTasks()
        loop = asyncio.get_event_loop()
        loop.create_task(startup_tasks.execute())
