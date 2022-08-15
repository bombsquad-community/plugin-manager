# ba_meta require api 7
import ba
import _ba
import bastd
from bastd.ui import popup

import urllib.request
import json
import os
import sys
import asyncio
import re
import pathlib

from typing import Union, Optional

_env = _ba.env()
_uiscale = ba.app.ui.uiscale


PLUGIN_MANAGER_VERSION = "0.1.1"
REPOSITORY_URL = "http://github.com/bombsquad-community/plugin-manager"
CURRENT_TAG = "main"
# XXX: Using https with `ba.open_url` seems to trigger a pop-up dialog box on Android currently (v1.7.6)
#      and won't open the actual URL in a web-browser. Let's fallback to http for now until this
#      gets resolved.
INDEX_META = "{repository_url}/{content_type}/{tag}/index.json"
HEADERS = {
    "User-Agent": _env["user_agent_string"],
}
PLUGIN_DIRECTORY = _env["python_directory_user"]
REGEXP = {
    "plugin_api_version": re.compile(b"(?<=ba_meta require api )(.*)"),
    "plugin_entry_points": re.compile(b"(ba_meta export plugin\n+class )(.*)\("),
    "minigames": re.compile(b"(ba_meta export game\n+class )(.*)\("),
}

_CACHE = {}


def setup_config():
    is_config_updated = False
    if "Community Plugin Manager" not in ba.app.config:
        ba.app.config["Community Plugin Manager"] = {}
    if "Installed Plugins" not in ba.app.config["Community Plugin Manager"]:
        ba.app.config["Community Plugin Manager"]["Installed Plugins"] = {}
        is_config_updated = True
    if "Custom Sources" not in ba.app.config["Community Plugin Manager"]:
        ba.app.config["Community Plugin Manager"]["Custom Sources"] = []
        is_config_updated = True
    for plugin_name in ba.app.config["Community Plugin Manager"]["Installed Plugins"].keys():
        plugin = PluginLocal(plugin_name)
        if not plugin.is_installed:
            del ba.app.config["Community Plugin Manager"]["Installed Plugins"][plugin_name]
            is_config_updated = True
    if "Settings" not in ba.app.config["Community Plugin Manager"]:
        ba.app.config["Community Plugin Manager"]["Settings"] = {}
    if "Auto Update Plugin Manager" not in ba.app.config["Community Plugin Manager"]["Settings"]:
        ba.app.config["Community Plugin Manager"]["Settings"]["Auto Update Plugin Manager"] = True
        is_config_updated = True
    if "Auto Update Plugins" not in ba.app.config["Community Plugin Manager"]["Settings"]:
        ba.app.config["Community Plugin Manager"]["Settings"]["Auto Update Plugins"] = True
        is_config_updated = True
    if "Load plugins immediately without restart" not in ba.app.config["Community Plugin Manager"]["Settings"]:
        ba.app.config["Community Plugin Manager"]["Settings"]["Load plugins immediately without restart"] = False
        is_config_updated = True
    if is_config_updated:
        ba.app.config.commit()


def send_network_request(request):
    return urllib.request.urlopen(request)


async def async_send_network_request(request):
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, send_network_request, request)
    return response


def stream_network_response_to_file(request, file):
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
    return content


async def async_stream_network_response_to_file(request, file):
    loop = asyncio.get_event_loop()
    content = await loop.run_in_executor(None, stream_network_response_to_file, request, file)
    return content


def play_sound():
    ba.playsound(ba.getsound('swish'))


def partial_format(string_template, **kwargs):
    for key, value in kwargs.items():
        string_template = string_template.replace("{" + key + "}", value)
    return string_template


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
        await self.fetch_metadata()
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

    async def refresh(self):
        self.cleanup()
        await self.get_plugins()

    def cleanup(self):
        self._metadata = None
        self._plugins.clear()
        self.unset_category_global_cache()

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
                return hasattr(plugin_class, "on_plugin_manager_prompt")
        return False

    def launch_settings(self):
        for plugin_entry_point, plugin_class in ba.app.plugins.active_plugins.items():
            if plugin_entry_point.startswith(self._entry_point_initials):
                return plugin_class.on_plugin_manager_prompt()

    async def get_content(self):
        if self._content is None:
            if not self.is_installed:
                # TODO: Raise a more fitting exception.
                raise TypeError("Plugin is not available locally.")
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
            if game not in scanner.results.exports["ba.GameActivity"]:
                new_scanned_results_games.append(game)
        ba.app.meta.scanresults.exports["ba.GameActivity"] = new_scanned_results_games

    async def is_enabled(self):
        """
        Return True even if a single entry point is enabled or contains minigames.
        """
        for entry_point, plugin_info in ba.app.config["Plugins"].items():
            if entry_point.startswith(self._entry_point_initials) and plugin_info["enabled"]:
                return True
        # XXX: The below logic is more accurate but less efficient, since it actually
        #      reads the local plugin file and parses entry points from it.
        # for entry_point in await self.get_entry_points():
        #     if ba.app.config["Plugins"][entry_point]["enabled"]:
        #         return True
        return await self.has_minigames()

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
        if await self.has_minigames():
            self.load_minigames()
        # await self._set_status(to_enable=True)
        self.save()
        ba.screenmessage("Plugin Enabled")

    def load_plugin(self, entry_point):
        plugin_class = ba._general.getclass(entry_point, ba.Plugin)
        loaded_plugin_class = plugin_class()
        loaded_plugin_class.on_app_running()
        ba.app.plugins.active_plugins[entry_point] = loaded_plugin_class

    def disable(self):
        for entry_point, plugin_info in ba.app.config["Plugins"].items():
            if entry_point.startswith(self._entry_point_initials):
                plugin_info["enabled"] = False
        # XXX: The below logic is more accurate but less efficient, since it actually
        #      reads the local plugin file and parses entry points from it.
        # await self._set_status(to_enable=False)
        self.save()
        ba.screenmessage("Plugin Disabled")

    def set_version(self, version):
        ba.app.config["Community Plugin Manager"]["Installed Plugins"][self.name]["version"] = version
        return self

    # def set_entry_points(self):
    #     if not "entry_points" in ba.app.config["Community Plugin Manager"]["Installed Plugins"][self.name]:
    #         ba.app.config["Community Plugin Manager"]["Installed Plugins"][self.name]["entry_points"] = []
    #     for entry_point in await self.get_entry_points():
    #         ba.app.config["Community Plugin Manager"]["Installed Plugins"][self.name]["entry_points"].append(entry_point)

    async def set_content(self, content):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._set_content, content)
        self._content = content
        return self

    async def set_content_from_network_response(self, request):
        content = await async_stream_network_response_to_file(request, self.install_path)
        self._content = content
        return self

    def save(self):
        ba.app.config.commit()
        return self


class PluginVersion:
    pass


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
        self.download_url = url.format(content_type="raw", tag=tag)
        self.view_url = url.format(content_type="blob", tag=tag)
        self._local_plugin = None

    def __repr__(self):
        return f"<Plugin({self.name})>"

    @property
    def is_installed(self):
        return os.path.isfile(self.install_path)

    @property
    def latest_version(self):
        # TODO: Return an instance of `PluginVersion`.
        return next(iter(self.info["versions"]))

    async def _download(self):
        local_plugin = self.create_local()
        await local_plugin.set_content_from_network_response(self.download_url)
        local_plugin.set_version(self.latest_version)
        local_plugin.save()
        return local_plugin

    def get_local(self):
        if not self.is_installed:
            raise ValueError("Plugin is not installed")
        if self._local_plugin is None:
            self._local_plugin = PluginLocal(self.name)
        return self._local_plugin

    def create_local(self):
        return (
            PluginLocal(self.name)
            .initialize()
        )

    async def install(self):
        local_plugin = await self._download()
        await local_plugin.enable()
        ba.screenmessage("Plugin Installed")

    async def uninstall(self):
        await self.get_local().uninstall()
        ba.screenmessage("Plugin Uninstalled")

    async def update(self):
        await self._download()
        ba.screenmessage("Plugin Updated")


class PluginWindow(popup.PopupWindow):
    def __init__(self, plugin, origin_widget, button_callback=lambda: None):
        self.plugin = plugin
        self.button_callback = button_callback
        self.scale_origin = origin_widget.get_screen_space_center()
        loop = asyncio.get_event_loop()
        loop.create_task(self.draw_ui())

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
        plugin_title = f"{self.plugin.name} (v{self.plugin.latest_version})"
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
                      text=self.plugin.info["description"],
                      scale=text_scale * 0.6, color=color,
                      maxwidth=width * 0.95)
        b1_color = (0.6, 0.53, 0.63)
        b2_color = (0.8, 0.15, 0.35)
        b3_color = (0.2, 0.8, 0.3)
        pos = height * 0.1
        button_size = (80 * s, 40 * s)

        to_draw_button1 = True
        to_draw_button4 = False
        if self.plugin.is_installed:
            self.local_plugin = self.plugin.get_local()
            if await self.local_plugin.has_minigames():
                to_draw_button1 = False
            else:
                if await self.local_plugin.is_enabled():
                    button1_label = "Disable"
                    button1_action = self.disable
                    if self.local_plugin.has_settings():
                        to_draw_button4 = True
                else:
                    button1_label = "Enable"
                    button1_action = self.enable
            button2_label = "Uninstall"
            button2_action = self.uninstall
            has_update = self.local_plugin.version != self.plugin.latest_version
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
                                            on_activate_call=lambda: ba.open_url(self.plugin.view_url))
        ba.imagewidget(parent=self._root_widget,
                       position=(open_pos_x, open_pos_y),
                       size=(40, 40),
                       color=(0.8, 0.95, 1),
                       texture=ba.gettexture("upButton"),
                       draw_controller=open_button)

        if to_draw_button4:
            settings_pos_x = (0 if _uiscale is ba.UIScale.SMALL else
                          60 if _uiscale is ba.UIScale.MEDIUM else 60)
            settings_pos_y = (100 if _uiscale is ba.UIScale.SMALL else
                          110 if _uiscale is ba.UIScale.MEDIUM else 120)
            settings_button = ba.buttonwidget(parent=self._root_widget,
                                                autoselect=True,
                                                position=(settings_pos_x, settings_pos_y),
                                                size=(40, 40),
                                                button_type="square",
                                                label="",
                                                on_activate_call=self.settings)
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

    def settings(self):
        self.local_plugin.launch_settings()

    @button
    def disable(self) -> None:
        self.local_plugin.disable()

    @button
    async def enable(self) -> None:
        await self.local_plugin.enable()

    @button
    async def install(self):
        await self.plugin.install()

    @button
    async def uninstall(self):
        await self.plugin.uninstall()

    @button
    async def update(self):
        await self.plugin.update()


class PluginManager:
    def __init__(self):
        self.request_headers = HEADERS
        self._index = _CACHE.get("index", {})
        self.categories = {}
        self.module_path = sys.modules[__name__].__file__

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
            self._index = json.loads(response.read())
            self.set_index_global_cache(self._index)
        return self._index

    async def setup_index(self):
        index = await self.get_index()
        await self._setup_plugin_categories(index)

    async def _setup_plugin_categories(self, plugin_index):
        # A hack to have the "All" category show at the top.
        self.categories["All"] = None

        requests = []
        for plugin_category_url in plugin_index["categories"]:
            category = Category(plugin_category_url)
            request = category.fetch_metadata()
            requests.append(request)
        for repository in ba.app.config["Community Plugin Manager"]["Custom Sources"]:
            plugin_category_url = partial_format(plugin_index["external_source_url"], repository=repository)
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

    async def update(self, to_version, commit_sha=None):
        index = await self.get_index()
        if to_version is None:
            to_version, commit_sha = await self.get_update_details()
        to_version_info = index["versions"][to_version]
        tag = commit_sha or CURRENT_TAG
        download_url = index["plugin_manager_url"].format(
            content_type="raw",
            tag=tag,
        )
        await async_stream_network_response_to_file(download_url, self.module_path)

    async def soft_refresh(self):
        pass


class PluginSourcesWindow(popup.PopupWindow):
    def __init__(self, origin_widget):
        play_sound()

        self.scale_origin = origin_widget.get_screen_space_center()

        b_textcolor = (0.75, 0.7, 0.8)
        s = 1.1 if _uiscale is ba.UIScale.SMALL else 1.27 if ba.UIScale.MEDIUM else 1.57
        text_scale = 0.7 * s
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

        scroll_size_x = (400 if _uiscale is ba.UIScale.SMALL else
                         380 if _uiscale is ba.UIScale.MEDIUM else 290)
        scroll_size_y = (225 if _uiscale is ba.UIScale.SMALL else
                         235 if _uiscale is ba.UIScale.MEDIUM else 180)
        scroll_pos_x = (70 if _uiscale is ba.UIScale.SMALL else
                        40 if _uiscale is ba.UIScale.MEDIUM else 60)
        scroll_pos_y = (125 if _uiscale is ba.UIScale.SMALL else
                        30 if _uiscale is ba.UIScale.MEDIUM else 105)
        self._scrollwidget = ba.scrollwidget(parent=self._root_widget,
                                             size=(scroll_size_x, scroll_size_y),
                                             position=(scroll_pos_x, scroll_pos_y))
        self._columnwidget = ba.columnwidget(parent=self._scrollwidget,
                                             border=1,
                                             margin=0)

        delete_source_button_position_pos_x = 360
        delete_source_button_position_pos_y = 110
        delete_source_button = ba.buttonwidget(parent=self._root_widget,
                        position=(delete_source_button_position_pos_x, delete_source_button_position_pos_y),
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
                       position=(delete_source_button_position_pos_x + 2, delete_source_button_position_pos_y),
                       size=(25, 25),
                       color=(5, 2, 2),
                       texture=ba.gettexture("crossOut"),
                       draw_controller=delete_source_button)
        ba.textwidget(
            parent=self._root_widget,
            position=(48, 74),
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
                                          text="rikkolovescats/sahilp-plugins",
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
            ba.screenmessage("Enter a valid plugin source")
            return
        if source in ba.app.config["Community Plugin Manager"]["Custom Sources"]:
            ba.screenmessage("Plugin source already exists")
            return
        ba.app.config["Community Plugin Manager"]["Custom Sources"].append(source)
        ba.app.config.commit()
        ba.screenmessage("Plugin source added, refresh plugin list to see changes")
        self.draw_sources()

    def delete_selected_source(self):
        ba.app.config["Community Plugin Manager"]["Custom Sources"].remove(self.selected_source)
        ba.app.config.commit()
        ba.screenmessage("Plugin source deleted, refresh plugin list to see changes")
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

        self._width = (490 if _uiscale is ba.UIScale.MEDIUM else 570)
        self._height = (500 if _uiscale is ba.UIScale.SMALL
                        else 380 if _uiscale is ba.UIScale.MEDIUM
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

        back_pos_x = 5 + (10 if _uiscale is ba.UIScale.SMALL else
                          27 if _uiscale is ba.UIScale.MEDIUM else 68)
        back_pos_y = self._height - (115 if _uiscale is ba.UIScale.SMALL else
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

        title_pos = self._height - (100 if _uiscale is ba.UIScale.SMALL else
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

        loading_pos_y = self._height - (235 if _uiscale is ba.UIScale.SMALL else
                                        220 if _uiscale is ba.UIScale.MEDIUM else 250)

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
        play_sound()
        from bastd.ui.settings.allsettings import AllSettingsWindow
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            AllSettingsWindow(transition='in_left').get_root_widget())

    async def draw_index(self):
        try:
            self.draw_search_bar()
            self.draw_plugins_scroll_bar()
            self.draw_category_selection_button(post_label="All")
            self.draw_refresh_icon()
            self.draw_settings_icon()
            await self.plugin_manager.setup_index()
            ba.textwidget(edit=self._plugin_manager_status_text,
                          text="")
            await self.select_category("All")
        except RuntimeError:
            # User probably went back before the PluginManagerWindow could finish loading.
            pass
        except urllib.error.URLError:
            ba.textwidget(edit=self._plugin_manager_status_text,
                          text="Make sure you are connected\n to the Internet and try again.")

    def draw_plugins_scroll_bar(self):
        scroll_size_x = (400 if _uiscale is ba.UIScale.SMALL else
                         380 if _uiscale is ba.UIScale.MEDIUM else 420)
        scroll_size_y = (225 if _uiscale is ba.UIScale.SMALL else
                         235 if _uiscale is ba.UIScale.MEDIUM else 335)
        scroll_pos_x = (70 if _uiscale is ba.UIScale.SMALL else
                        40 if _uiscale is ba.UIScale.MEDIUM else 70)
        scroll_pos_y = (125 if _uiscale is ba.UIScale.SMALL else
                        30 if _uiscale is ba.UIScale.MEDIUM else 40)
        self._scrollwidget = ba.scrollwidget(parent=self._root_widget,
                                             size=(scroll_size_x, scroll_size_y),
                                             position=(scroll_pos_x, scroll_pos_y))
        self._columnwidget = ba.columnwidget(parent=self._scrollwidget,
                                             border=2,
                                             margin=0)


    def draw_category_selection_button(self, post_label):
        category_pos_x = (330 if _uiscale is ba.UIScale.SMALL else
                          285 if _uiscale is ba.UIScale.MEDIUM else 350)
        category_pos_y = self._height - (145 if _uiscale is ba.UIScale.SMALL else
                                         110 if _uiscale is ba.UIScale.MEDIUM else 110)
        b_size = (140, 30)
        b_textcolor = (0.75, 0.7, 0.8)
        b_color = (0.6, 0.53, 0.63)

        label = f"Category: {post_label}"

        if self.category_selection_button is None:
            self.category_selection_button = ba.buttonwidget(parent=self._root_widget,
                                                             position=(category_pos_x,
                                                                       category_pos_y),
                                                             size=b_size,
                                                             on_activate_call=self.show_categories_window,
                                                             label=label,
                                                             button_type="square",
                                                             color=b_color,
                                                             textcolor=b_textcolor,
                                                             # autoselect=True,
                                                             text_scale=0.6)
        else:
            self.category_selection_button = ba.buttonwidget(edit=self.category_selection_button,
                                                             label=label)

    def draw_search_bar(self):
        search_bar_pos_x = (85 if _uiscale is ba.UIScale.SMALL else
                            65 if _uiscale is ba.UIScale.MEDIUM else 90)
        search_bar_pos_y = self._height - (
            145 if _uiscale is ba.UIScale.SMALL else
            110 if _uiscale is ba.UIScale.MEDIUM else 116)

        search_bar_size_x = (250 if _uiscale is ba.UIScale.SMALL else
                             230 if _uiscale is ba.UIScale.MEDIUM else 260)
        search_bar_size_y = (
            35 if _uiscale is ba.UIScale.SMALL else
            35 if _uiscale is ba.UIScale.MEDIUM else 45)

        filter_txt_pos_x = (60 if _uiscale is ba.UIScale.SMALL else
                            40 if _uiscale is ba.UIScale.MEDIUM else 60)
        filter_txt_pos_y = search_bar_pos_y + (5 if _uiscale is ba.UIScale.SMALL else
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
        self._filter_widget = ba.textwidget(parent=self._root_widget,
                                          text="",
                                          size=(search_bar_size_x, search_bar_size_y),
                                          position=(search_bar_pos_x, search_bar_pos_y),
                                          h_align='left',
                                          v_align='center',
                                          editable=True,
                                          scale=0.8,
                                          autoselect=True,
                                          description=filter_txt)

    def draw_settings_icon(self):
        settings_pos_x = (500 if _uiscale is ba.UIScale.SMALL else
                          440 if _uiscale is ba.UIScale.MEDIUM else 510)
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
        settings_pos_x = (500 if _uiscale is ba.UIScale.SMALL else
                          440 if _uiscale is ba.UIScale.MEDIUM else 510)
        settings_pos_y = (180 if _uiscale is ba.UIScale.SMALL else
                          105 if _uiscale is ba.UIScale.MEDIUM else 120)
        controller_button = ba.buttonwidget(parent=self._root_widget,
                                            # autoselect=True,
                                            position=(settings_pos_x, settings_pos_y),
                                            size=(30, 30),
                                            button_type="square",
                                            label="",
                                            on_activate_call=self.refresh)
        ba.imagewidget(parent=self._root_widget,
                       position=(settings_pos_x, settings_pos_y),
                       size=(30, 30),
                       color=(0.8, 0.95, 1),
                       texture=ba.gettexture("replayIcon"),
                       draw_controller=controller_button)

    async def draw_plugin_names(self, category):
        for plugin in self._columnwidget.get_children():
            plugin.delete()

        plugins = await self.plugin_manager.categories[category].get_plugins()
        plugin_names_to_draw = tuple(self.draw_plugin_name(plugin) for plugin in plugins)
        await asyncio.gather(*plugin_names_to_draw)

    async def draw_plugin_name(self, plugin):
        if plugin.is_installed:
            local_plugin = plugin.get_local()
            if await local_plugin.is_enabled():
                if not local_plugin.is_installed_via_plugin_manager:
                    color = (0.8, 0.2, 0.2)
                elif local_plugin.version == plugin.latest_version:
                    color = (0, 1, 0)
                else:
                    color = (1, 0.6, 0)
            else:
                color = (1, 1, 1)
        else:
            color = (0.5, 0.5, 0.5)

        plugin_to_update = self.plugins_in_current_view.get(plugin.name)
        if plugin_to_update:
            ba.textwidget(edit=plugin_to_update,
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
        self.selected_category = category
        self.plugins_in_current_view.clear()
        self.draw_category_selection_button(post_label=category)
        await self.draw_plugin_names(category)

    def cleanup(self):
        self.plugin_manager.cleanup()
        for plugin in self._columnwidget.get_children():
            plugin.delete()
        self.plugins_in_current_view.clear()

    async def _refresh(self):
        await self.plugin_manager.refresh()
        await self.plugin_manager.setup_index()
        ba.textwidget(edit=self._plugin_manager_status_text,
                      text="")
        await self.select_category(self.selected_category)

    def refresh(self):
        play_sound()
        self.cleanup()
        ba.textwidget(edit=self._plugin_manager_status_text,
                      text="Refreshing...")
        loop = asyncio.get_event_loop()
        loop.create_task(self._refresh())

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
        b_text_color = (0.75, 0.7, 0.8)
        s = 1.1 if _uiscale is ba.UIScale.SMALL else 1.27 if ba.UIScale.MEDIUM else 1.57
        width = 380 * s
        height = 150 + 150 * s
        color = (0.9, 0.9, 0.9)
        text_scale = 0.7 * s
        self._transition_out = 'out_scale'
        transition = 'in_scale'
        button_size = (60 * s, 32 * s)
        index = await self._plugin_manager.get_index()
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
                             scale=0.75)
            pos -= 32

        pos -= 20
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.49, pos-5),
                      size=(0, 0),
                      h_align='center',
                      v_align='center',
                      text='Contribute to plugins or to this community plugin manager!',
                      scale=text_scale * 0.65,
                      color=color,
                      maxwidth=width * 0.95)

        pos -= 70
        ba.buttonwidget(parent=self._root_widget,
                        position=((width * 0.49) - button_size[0] / 2, pos),
                        size=button_size,
                        on_activate_call=lambda: ba.open_url(REPOSITORY_URL),
                        textcolor=b_text_color,
                        button_type='square',
                        text_scale=1,
                        label='GitHub')
        ba.containerwidget(edit=self._root_widget,
                           on_cancel_call=self._ok)

        plugin_manager_update_available = await self._plugin_manager.get_update_details()
        if plugin_manager_update_available:
            text_color = (0.75, 0.2, 0.2)
            loop = asyncio.get_event_loop()
            button_size = (95 * s, 32 * s)
            self._update_button = ba.buttonwidget(parent=self._root_widget,
                                                  position=((width * 0.77) - button_size[0] / 2, pos),
                                                  size=button_size,
                                                  on_activate_call=lambda: loop.create_task(self.update(*plugin_manager_update_available)),
                                                  textcolor=b_text_color,
                                                  button_type='square',
                                                  text_scale=1,
                                                  color=(0, 0.7, 0),
                                                  label=f'Update to v{plugin_manager_update_available[0]}')
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

    async def update(self, to_version, commit_sha=None):
        await self._plugin_manager.update(to_version, commit_sha)
        ba.screenmessage("Update successful.")
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
        _b_title(x_offs6, v, avb, ba.Lstr(value="Plugin Manager"))
        imgw = imgh = 120
        ba.imagewidget(parent=self._root_widget,
                       position=(x_offs6 + basew * 0.49 - imgw * 0.5 + 5,
                                 v + 35),
                       size=(imgw, imgh),
                       color=(0.8, 0.95, 1),
                       texture=ba.gettexture("heart"),
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
        setup_config()
        from bastd.ui.settings import allsettings
        allsettings.AllSettingsWindow = NewAllSettingsWindow
        asyncio.set_event_loop(ba._asyncio._asyncio_event_loop)
        # loop = asyncio.get_event_loop()
        # loop.create_task(do())
        # pm = PluginManager()
        # pm.plugin_index()

    def on_app_pause(self) -> None:
        """Called after pausing game activity."""
        print("pause")

    def on_app_resume(self) -> None:
        """Called after the game continues."""
        print("resume")

    def on_app_shutdown(self) -> None:
        """Called before closing the application."""
        print("shutdown")
        # print(ba.app.config["Community Plugin Manager"])
        # with open(_env["config_file_path"], "r") as fin:
        #     c = fin.read()
        # import json
        # print(json.loads(c)["Community Plugin Manager"])
