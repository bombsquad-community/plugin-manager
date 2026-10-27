# ba_meta require api 9

# Import order matters here. Whatever breaks at import time breaks self-update
# with it, and a plugin manager that can't import can never fetch the release
# that fixes it. So: the standard library first, then only the bombsquad
# modules every API 9 build has, then everything build-specific guarded.
import logging
import urllib.error
import urllib.request
import http.client
import socket
import json

import re
import os
import copy
import asyncio
import pathlib
import hashlib
import weakref
import threading
import contextlib
import concurrent.futures

from dataclasses import replace
from typing import override
from datetime import datetime

# Only import bombsquad modules that every API 9 build has out here (the
# four below do). Anything newer or build-specific goes inside the
# try/except further down, so this file still imports on older builds.
import babase
import bauiv1 as bui
from bauiv1lib import popup, confirm

# BombSquad 1.8.0 (build 23058) replaced the classic top level settings
# window with a doc-ui page. Every API 9 client auto-updates to this file,
# including ones on older builds, so both are supported in place. Exactly
# one of settingsdocui and AllSettingsWindow is set on a supported build;
# neither is if the engine moved things again.
try:
    import bauiv1lib.settings.allsettingsdocui as settingsdocui
    import bauiv1lib.docui._layout as docui_layout
    import bauiv1lib.docui._window as docui_window
    import bacommon.docui.v2 as dui2
    from bacommon.docui.routes import PressSound
    from bacommon.langstr import LangStrSpecValue

    # Private engine names, read here so a rename lands in the except
    # below rather than failing the whole import. The row width is the
    # settings page's four stock buttons plus ours, with a button gap of
    # breathing room each side (see _settings_width_fraction).
    _StockSettingsController = settingsdocui.AllSettingsController
    _SETTINGS_ROW_WIDTH = (5 * settingsdocui._BW * settingsdocui._BUTTON_SCALE
                           + 6 * settingsdocui._BUTTON_SPACING)
    AllSettingsWindow = None
except (ImportError, AttributeError):
    settingsdocui = None
    try:
        from bauiv1lib.settings.allsettings import AllSettingsWindow
    except ImportError:
        AllSettingsWindow = None


# Plugin Manager's logger. It lives under ba.user, the engine's logger for
# problems with the player's own mods: entries show in the dev console's
# Logging tab (where its level can be changed), but on builds from 1.8.x
# on they never set off the engine's automatic error reports, which are
# meant for engine bugs. On older builds it's just a named logger.
logger = logging.getLogger("ba.user.pluginmanager")

PLUGIN_MANAGER_VERSION = "1.2.3"

# Oldest BombSquad build (babase.app.env.engine_build_number) this release
# runs on. CI copies it into this version's index.json entry, and plugin
# managers on older builds won't auto-update to it. Raise it only when a
# release drops support for older builds; supporting them in place (see
# the settingsdocui fallback) is preferred.
MIN_ENGINE_BUILD = 0

REPOSITORY_URL = "https://github.com/bombsquad-community/plugin-manager"

# Current tag can be changed to "staging" or any other branch in
# plugin manager repo for testing purpose.
CURRENT_TAG = "main"

_app_api_version = babase.app.env.api_version

PLUGIN_ISSUE_TEMPLATE = "plugin-bug-report.yml"
GITHUB_PLUGIN_ISSUE_META = "{repository_url}/issues/new?template={issue_template}"
INDEX_META = "{repository_url}/{content_type}/{tag}/index.json"
CHANGELOG_META = "{repository_url}/{content_type}/{tag}/CHANGELOG.md"
HEADERS = {
    "User-Agent": babase.user_agent_string(),
}
PLUGIN_DIRECTORY = babase.app.env.python_directory_user

NETWORK_REQUEST_TIMEOUT = 10  # seconds

# Consecutive failed self-updates (kept in the config) before the player
# is told to reinstall by hand.
UPDATE_FAILURES_CONFIG_KEY = "Failed Update Attempts"
UPDATE_FAILURES_BEFORE_NOTICE = 3


def _set_update_failures(count):
    config = babase.app.config["Community Plugin Manager"]
    if config[UPDATE_FAILURES_CONFIG_KEY] != count:
        config[UPDATE_FAILURES_CONFIG_KEY] = count
        babase.app.config.commit()


def _record_update_failure(to_version):
    failures = babase.app.config["Community Plugin Manager"][UPDATE_FAILURES_CONFIG_KEY] + 1
    _set_update_failures(failures)
    # Once, rather than every launch from here on; a successful update
    # (or catching up some other way) resets the count.
    if failures == UPDATE_FAILURES_BEFORE_NOTICE:
        bui.screenmessage(
            f"Plugin Manager couldn't update itself to v{to_version} "
            f"({failures} tries). Reinstall it from {REPOSITORY_URL}/releases/latest",
            color=(1, 0.5, 0),
        )


loop = babase.app.asyncio_loop
pool = babase.app.threadpool

# babase.app.threadpool (aka `pool`, also wired up as the asyncio loop's
# default executor) is reserved for short parallel work and warns/starves
# on long-running tasks. Network requests routinely run past that, so they
# get their own small dedicated pool instead.
_network_pool = concurrent.futures.ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="PluginManagerNetwork",
)


async def _shutdown_network_pool() -> None:
    """Drain _network_pool's workers so none outlive app shutdown.

    ThreadPoolExecutor.shutdown(wait=True) blocks, so it's run on a
    throwaway thread and awaited from here rather than blocking the
    event loop (other shutdown tasks run concurrently with this one).
    In-flight requests are bounded by NETWORK_REQUEST_TIMEOUT, so this
    settles quickly.
    """
    done = asyncio.Event()

    def _join() -> None:
        _network_pool.shutdown(wait=True, cancel_futures=True)
        loop.call_soon_threadsafe(done.set)

    threading.Thread(target=_join, daemon=True).start()
    await done.wait()


open_popups = []


def _add_popup(popup):
    open_popups.append(popup)


def _remove_popup(popup):
    try:
        open_popups.remove(popup)
    except ValueError:
        pass


def _runs_on_this_build(info):
    """Whether this game can run the release an index/catalog entry describes.

    Its API has to match, and its min_engine_build (missing means 0) can't
    be above this build. Shared by the plugin manager's own updates and by
    plugin installs and updates.
    """
    return (info["api_version"] == _app_api_version
            and info.get("min_engine_build", 0) <= babase.app.env.engine_build_number)


def _version_key(version):
    """A version string as a comparable tuple, or None if it isn't x.y.z.

    CI parses versions the same way (test/auto_apply_version_metadata.py's
    get_comparable_version_tuple_from_string); this file can't import it.
    """
    try:
        return tuple(int(part) for part in version.split("."))
    except (AttributeError, ValueError):
        return None


# Sort keys offered by the plugin list's filter popup, mapped to
# (label in the popup, short label on the main window's filter button).
SORT_OPTIONS = {
    "name_asc": ("Name (A - Z)", "A - Z"),
    "name_desc": ("Name (Z - A)", "Z - A"),
    "recently_added": ("Recently Added", "Newest"),
    "recently_updated": ("Recently Updated", "Updated"),
}


def _released_on_date(info):
    """A catalog version entry's release date, or datetime.min if unreadable.

    Custom sources aren't stamped by our CI, so don't trust their dates.
    """
    try:
        return datetime.strptime(info["released_on"], "%d-%m-%Y")
    except (KeyError, TypeError, ValueError):
        return datetime.min


def _first_released_date(plugin):
    dates = [_released_on_date(info) for info in plugin.info["versions"].values()]
    return min((date for date in dates if date != datetime.min), default=datetime.min)


def _last_updated_date(plugin):
    # The newest release this game can run, so a plugin doesn't look freshly
    # updated just because it got a release for another API.
    versions = list(plugin.info["versions"].values())
    runnable = [info for info in versions if _runs_on_this_build(info)]
    return max(map(_released_on_date, runnable or versions), default=datetime.min)


def _sort_plugins(plugins, sort):
    plugins = sorted(plugins, key=lambda plugin: plugin.name, reverse=(sort == "name_desc"))
    # sort() is stable, so plugins released on the same day stay A - Z.
    if sort == "recently_added":
        plugins.sort(key=_first_released_date, reverse=True)
    elif sort == "recently_updated":
        plugins.sort(key=_last_updated_date, reverse=True)
    return plugins


def _charstr(char):
    # remove this after 1.8 is widely adopted
    """A SpecialChar as text, without charstr()'s deprecation warning.

    From 1.8.0 a SpecialChar's value is the character itself and charstr()
    is deprecated; older API 9 builds have integer values and need it.
    """
    value = char.value
    return value if isinstance(value, str) else babase.charstr(char)


def _uiscale(): return bui.app.ui_v1.uiscale
def _regexp_friendly_class_name_shortcut(string): return string.replace(".", "\\.")


def _by_scale(a, b, c):
    u = _uiscale()
    return (
        a if u is babase.UIScale.SMALL else
        b if u is babase.UIScale.MEDIUM else
        c
    )


def _wrap_markdown_bullets(source_lines, max_width, scale):
    """Reflow markdown bullets so every rendered line fits `max_width`.

    CHANGELOG.md hard-wraps its bullets across several source lines, so the
    lines are first stitched back into whole bullets and then re-wrapped to
    the width we actually have. Drawing the source lines as-is left each one
    a different length, and since a text widget shrinks itself to its own
    maxwidth, long lines rendered visibly smaller than short ones.
    """
    bullets = []
    for line in source_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("-", "*")) or not bullets:
            bullets.append(stripped.lstrip("-*").strip())
        else:
            # A continuation of the bullet above it.
            bullets[-1] += " " + stripped

    lines = []
    for bullet in bullets:
        prefix, current = "- ", ""
        for word in bullet.split():
            candidate = f"{current} {word}" if current else word
            width = bui.get_string_width(prefix + candidate, suppress_warning=True)
            if current and width * scale > max_width:
                lines.append(prefix + current)
                # Indent wrapped remainders under the bullet's text.
                prefix, current = "   ", word
            else:
                current = candidate
        lines.append(prefix + current)
    return lines


REGEXP = {
    "plugin_api_version": re.compile(b"(?<=ba_meta require api )(.*)"),
    "plugin_entry_points": re.compile(
        bytes(
            "(ba_meta export (plugin|{})\n+class )(.*)\\(".format(
                _regexp_friendly_class_name_shortcut("babase.Plugin"),
            ),
            "utf-8"
        ),
    ),
    "minigames": re.compile(
        bytes(
            "(ba_meta export ({})\n+class )(.*)\\(".format(
                _regexp_friendly_class_name_shortcut("bascenev1.GameActivity"),
            ),
            "utf-8"
        ),
    ),
}
DISCORD_URL = "https://ballistica.net/discord"


_CACHE = {}


class MD5CheckSumFailed(Exception):
    pass


class PluginNotInstalled(Exception):
    pass


class CategoryDoesNotExist(Exception):
    pass


class NoCompatibleVersion(Exception):
    pass


class PluginSourceNetworkError(Exception):
    pass


class CategoryMetadataParseError(Exception):
    pass


@contextlib.contextmanager
def network_errors_as_urlerror():
    """Normalize network failures into urllib.error.URLError.

    Every caller in here reports connectivity problems by catching
    URLError, but urllib only guarantees that shape while it is building
    the request. Once urlopen() has returned, a socket timeout surfaces
    as a bare TimeoutError and a truncated/dropped response as an
    http.client.HTTPException, both of which sail past those handlers.
    Since NETWORK_REQUEST_TIMEOUT made timeouts reachable at all, wrap
    the whole fetch so callers only ever have one exception to catch.
    """
    try:
        yield
    except urllib.error.URLError:
        # Includes HTTPError; already the shape callers expect.
        raise
    except (TimeoutError, http.client.HTTPException) as e:
        raise urllib.error.URLError(e) from e


def send_network_request(request):
    """Fetch `request` and return its full body as bytes.

    The body is read here rather than handed back unread, because reading
    it is itself a blocking call that can time out, and callers await this
    from the event loop thread, where doing so would both stall the game
    and raise outside network_errors_as_urlerror()'s reach.
    """
    with network_errors_as_urlerror():
        with urllib.request.urlopen(request, timeout=NETWORK_REQUEST_TIMEOUT) as response:
            return response.read()


async def async_send_network_request(request):
    content = await loop.run_in_executor(_network_pool, send_network_request, request)
    return content


def stream_network_response_to_file(request, file, md5sum=None, retries=3):
    chunk_size = 16 * 1024
    content = b""
    with network_errors_as_urlerror():
        with urllib.request.urlopen(request, timeout=NETWORK_REQUEST_TIMEOUT) as response:
            with open(file, "wb") as fout:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    fout.write(chunk)
                    content += chunk
    if md5sum and hashlib.md5(content).hexdigest() != md5sum:
        if retries <= 0:
            raise MD5CheckSumFailed("MD5 checksum match failed.")
        return stream_network_response_to_file(
            request,
            file,
            md5sum=md5sum,
            retries=retries-1,
        )
    return content


async def async_stream_network_response_to_file(request, file, md5sum=None, retries=3):

    content = await loop.run_in_executor(
        _network_pool,
        stream_network_response_to_file,
        request,
        file,
        md5sum,
        retries,
    )
    return content


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

    References:
      * https://github.com/orgs/community/discussions/42655

    Usage:
    -----
    >>> import urllib.request
    >>> import socket
    >>> import json
    >>> DNSBlockWorkaround.apply()
    >>> response = urllib.request.urlopen("https://dnsblockeddomain.com/path/to/resource/")
    """

    # Hostnames worth second-guessing the system resolver on. Keeping this
    # explicit is what lets apply() patch a process-global function safely:
    # every other name the game looks up takes a set membership test and is
    # then handed straight to the original resolver.
    _blockable_hosts = frozenset(("raw.githubusercontent.com",))

    # Maps a hostname to the addresses to dial for it, or to None when the
    # host resolves normally and needs no workaround at all. Only populated
    # for hosts we've already checked, so the check happens once per session.
    _resolution_cache = {}

    _original_getaddrinfo = None

    @classmethod
    def apply(cls):
        """Correct socket.getaddrinfo() instead of rebuilding the HTTP stack.

        The block only ever corrupts one thing, the answer the resolver
        hands back, so that is the only thing worth replacing. Fixing it
        here leaves urllib, http.client and ssl completely stock:
        socket.create_connection() still does its own address walking,
        IPv6 handling and error aggregation, and TLS still verifies
        against the hostname rather than whatever address we dialed.
        """
        if cls._original_getaddrinfo is not None:
            # Already applied. Patching again would nest the wrapper.
            return
        cls._original_getaddrinfo = staticmethod(socket.getaddrinfo)
        socket.getaddrinfo = cls._getaddrinfo

    @classmethod
    def _getaddrinfo(cls, host, port, family=0, type=0, proto=0, flags=0):
        # Signature and argument names mirror socket.getaddrinfo(), which
        # callers pass both positionally and by keyword.
        if host in cls._blockable_hosts:
            addresses = cls._addresses_to_dial(host)
            if addresses is not None:
                # Re-resolving each literal address is just parsing; it
                # builds the 5-tuples callers expect without a lookup.
                return [
                    addrinfo
                    for address in addresses
                    for addrinfo in cls._original_getaddrinfo(
                        address, port, family, type, proto, flags)
                ]
        return cls._original_getaddrinfo(host, port, family, type, proto, flags)

    @classmethod
    def _resolve_using_google_dns(cls, hostname):
        response = urllib.request.urlopen(
            f"https://dns.google/resolve?name={hostname}",
            timeout=NETWORK_REQUEST_TIMEOUT,
        )
        response = response.read()
        response = json.loads(response)
        # Answers can include CNAME records (type 5) alongside the A (1) and
        # AAAA (28) records; only the latter are dialable.
        return [answer["data"] for answer in response.get("Answer", ())
                if answer.get("type") in (1, 28)]

    @classmethod
    def _resolve_using_system_dns(cls, hostname):
        resolved_host = socket.gethostbyname(hostname)
        return resolved_host

    @classmethod
    def _addresses_to_dial(cls, hostname):
        """Addresses to substitute for `hostname`, or None to leave it alone.

        Returning None is the common case and means the system resolver's
        answer stands. Note that both branches yield *every* usable address
        rather than one: socket.create_connection() walks the list until
        something answers, and raw.githubusercontent.com publishes four A
        records whose edge nodes are not all reachable from every network,
        so collapsing to a single address would fail a share of requests
        outright.
        """
        if hostname in cls._resolution_cache:
            return cls._resolution_cache[hostname]

        try:
            resolved_host_by_system_dns = cls._resolve_using_system_dns(hostname)
        except socket.gaierror:
            # A block that answers with NXDOMAIN rather than a bogus address.
            addresses = cls._resolve_using_google_dns(hostname) or None
        else:
            if cls._is_blocked(hostname, resolved_host_by_system_dns):
                addresses = cls._resolve_using_google_dns(hostname) or None
            else:
                addresses = None

        cls._resolution_cache[hostname] = addresses
        return addresses

    @classmethod
    def _is_blocked(cls, hostname, address):
        is_blocked = False
        if hostname == "raw.githubusercontent.com":
            # Jio's DNS server may be blocking it.
            is_blocked = address.startswith("49.44.")

        return is_blocked


class StartupTasks:
    def __init__(self):
        self.plugin_manager = PluginManager()

    def setup_config(self):
        # is_config_updated = False
        existing_plugin_manager_config = copy.deepcopy(
            babase.app.config.get("Community Plugin Manager"))

        plugin_manager_config = babase.app.config.setdefault("Community Plugin Manager", {})
        plugin_manager_config.setdefault("Custom Sources", [])
        installed_plugins = plugin_manager_config.setdefault("Installed Plugins", {})
        plugin_manager_config.setdefault(UPDATE_FAILURES_CONFIG_KEY, 0)
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
            babase.app.config.commit()

    async def update_plugin_manager(self):
        if not babase.app.config["Community Plugin Manager"]["Settings"]["Auto Update Plugin Manager"]:
            return
        # A failure to reach the index (offline, say) raises out of here
        # and isn't counted; only failures once an update is known to
        # exist are.
        update_details = await self.plugin_manager.get_update_details()
        if not update_details:
            # Caught up some other way (a manual reinstall, say).
            _set_update_failures(0)
            return
        to_version, commit_sha = update_details
        bui.screenmessage(f"Plugin Manager is being updated to v{to_version}")
        try:
            await self.plugin_manager.update(to_version, commit_sha)
        except (MD5CheckSumFailed, urllib.error.URLError):
            bui.getsound('error').play()
        else:
            bui.screenmessage("Update successful. Restart game to reload changes.",
                              color=(0, 1, 0))
            bui.getsound('shieldUp').play()

    async def update_plugins(self):
        if not babase.app.config["Community Plugin Manager"]["Settings"]["Auto Update Plugins"]:
            return
        await self.plugin_manager.setup_index()
        all_plugins = await self.plugin_manager.categories["All"].get_plugins()
        plugins_to_update = []
        for plugin in all_plugins:
            if plugin.is_installed and await plugin.get_local().is_enabled() and plugin.has_update():
                plugins_to_update.append(plugin.update())
        await asyncio.gather(*plugins_to_update)

    @staticmethod
    def _is_new_supported_plugin(plugin):
        is_an_update = len(plugin.versions) > 1
        if is_an_update:
            return False
        try:
            plugin.latest_compatible_version
        except NoCompatibleVersion:
            return False
        else:
            return True

    async def notify_new_plugins(self):
        if not babase.app.config["Community Plugin Manager"]["Settings"]["Notify New Plugins"]:
            return
        show_max_names = 2
        await self.plugin_manager.setup_index()
        new_num_of_plugins = len(await self.plugin_manager.categories["All"].get_plugins())
        try:
            existing_num_of_plugins = babase.app.config["Community Plugin Manager"]["Existing Number of Plugins"]
        except KeyError:
            babase.app.config["Community Plugin Manager"]["Existing Number of Plugins"] = new_num_of_plugins
            babase.app.config.commit()
            return

        def title_it(plug):
            plug = str(plug).replace('_', ' ').title()
            return plug
        if existing_num_of_plugins < new_num_of_plugins:
            new_plugin_count = new_num_of_plugins - existing_num_of_plugins
            all_plugins = await self.plugin_manager.categories["All"].get_plugins()
            new_supported_plugins = list(filter(self._is_new_supported_plugin, all_plugins))
            new_supported_plugins.sort(
                key=lambda plugin: plugin.latest_compatible_version.released_on_date,
                reverse=True,
            )
            new_supported_plugins = new_supported_plugins[:new_plugin_count]
            new_supported_plugins_count = len(new_supported_plugins)
            if new_supported_plugins_count > 0:
                new_supported_plugins = ", ".join(map(title_it, (new_supported_plugins
                                                                 if new_supported_plugins_count <= show_max_names else
                                                                 new_supported_plugins[0:show_max_names])
                                                      ))
                if new_supported_plugins_count == 1:
                    notification_text = f"{new_supported_plugins_count} new plugin ({new_supported_plugins}) is available!"
                else:
                    notification_text = new_supported_plugins + \
                        ('' if new_supported_plugins_count <= show_max_names else ' and +' +
                         str(new_supported_plugins_count-show_max_names)) + " new plugins are available"
                bui.screenmessage(notification_text, color=(0, 1, 0))

        if existing_num_of_plugins != new_num_of_plugins:
            babase.app.config["Community Plugin Manager"]["Existing Number of Plugins"] = new_num_of_plugins
            babase.app.config.commit()

    async def execute(self):
        try:
            self.setup_config()
        except Exception:
            # Self-update below still has a go; it reads only a couple of
            # config keys.
            logger.exception("Failed to set up the plugin manager config.")
        tasks = {
            "self-update": self.update_plugin_manager(),
            "plugin updates": self.update_plugins(),
            "new plugin notice": self.notify_new_plugins(),
        }
        # return_exceptions keeps one task's failure from hiding the
        # others'; each is reported on its own.
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for name, result in zip(tasks, results):
            if isinstance(result, urllib.error.URLError):
                # Usually just offline; nothing to tell the player about.
                logger.info("Skipped %s, network unavailable: %s", name, result)
            elif isinstance(result, Exception):
                logger.error("Startup %s failed.", name, exc_info=result)


class Category:
    def __init__(self, meta_url, tag=CURRENT_TAG):
        self.meta_url = meta_url
        self.tag = tag
        self.request_headers = HEADERS
        self._metadata = _CACHE.get("categories", {}).get(meta_url, {}).get("metadata")
        self._plugins = _CACHE.get("categories", {}).get(meta_url, {}).get("plugins")

    async def fetch_metadata(self):
        if self._metadata is None:
            # Let's keep depending on the "main" branch for 3rd party sources
            # even if we're using a different branch of plugin manager's repository.
            request = urllib.request.Request(
                self.meta_url.format(content_type="raw", tag=self.tag),
                headers=self.request_headers,
            )
            content = await async_send_network_request(request)
            self._metadata = json.loads(content)
            self.set_category_global_cache("metadata", self._metadata)
        return self

    async def validate(self):
        try:
            await self.fetch_metadata()
        except urllib.error.HTTPError as e:
            raise PluginSourceNetworkError(str(e))
        except json.decoder.JSONDecodeError as e:
            raise CategoryMetadataParseError(f"Failed to parse JSON: {str(e)}")
        try:
            await asyncio.gather(
                self.get_name(),
                self.get_description(),
                self.get_plugins_base_url(),
                self.get_plugins(),
            )
        except KeyError:
            raise CategoryMetadataParseError("Failed to parse JSON; missing required fields.")
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
                    tag=self.tag,
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
        babase.app.config["Community Plugin Manager"]["Custom Sources"].append(self.meta_url)
        babase.app.config.commit()


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
        return self.name in babase.app.config["Community Plugin Manager"]["Installed Plugins"]

    def initialize(self):
        if self.name not in babase.app.config["Community Plugin Manager"]["Installed Plugins"]:
            babase.app.config["Community Plugin Manager"]["Installed Plugins"][self.name] = {}
        return self

    async def uninstall(self):
        if await self.has_minigames():
            self.unload_minigames()
        try:
            os.remove(self.install_path)
        except FileNotFoundError:
            pass
        try:
            del babase.app.config["Community Plugin Manager"]["Installed Plugins"][self.name]
        except KeyError:
            pass
        else:
            self.save()

    @property
    def version(self):
        try:
            version = (babase.app.config["Community Plugin Manager"]
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
        for plugin_entry_point, plugin_spec in bui.app.plugins.plugin_specs.items():
            if plugin_entry_point.startswith(self._entry_point_initials):
                return plugin_spec.plugin.has_settings_ui()

    def launch_settings(self, source_widget):
        for plugin_entry_point, plugin_spec in bui.app.plugins.plugin_specs.items():
            if plugin_entry_point.startswith(self._entry_point_initials):
                return plugin_spec.plugin.show_settings_ui(source_widget)

    async def get_content(self):
        if self._content is None:
            if not self.is_installed:
                raise PluginNotInstalled("Plugin is not available locally.")

            self._content = await loop.run_in_executor(pool, self._get_content)
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
            # Actual entry points are stored in the last index inside the matching groups.
            entry_points = tuple(f"{self.name}.{group[-1].decode('utf-8')}" for group in groups)
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
        scanner = babase._meta.DirectoryScan(paths="")
        directory, module = self.install_path.rsplit(os.path.sep, 1)
        scanner._scan_module(
            pathlib.Path(directory),
            pathlib.Path(module),
        )
        scanned_results = set(babase.app.meta.scanresults.exports["bascenev1.GameActivity"])
        for game in scanner.results.exports["bascenev1.GameActivity"]:
            if game not in scanned_results:
                bui.screenmessage(f"{game} minigame loaded")
                babase.app.meta.scanresults.exports["bascenev1.GameActivity"].append(game)

    def unload_minigames(self):
        scanner = babase._meta.DirectoryScan(paths="")
        directory, module = self.install_path.rsplit(os.path.sep, 1)
        scanner._scan_module(
            pathlib.Path(directory),
            pathlib.Path(module),
        )
        new_scanned_results_games = []
        for game in babase.app.meta.scanresults.exports["bascenev1.GameActivity"]:
            if game in scanner.results.exports["bascenev1.GameActivity"]:
                bui.screenmessage(f"{game} minigame unloaded")
            else:
                new_scanned_results_games.append(game)
        babase.app.meta.scanresults.exports["bascenev1.GameActivity"] = new_scanned_results_games

    async def is_enabled(self):
        """
        Return True even if a single entry point is enabled or contains minigames.
        """
        if not await self.has_plugins():
            return True
        for entry_point, plugin_info in babase.app.config["Plugins"].items():
            if entry_point.startswith(self._entry_point_initials) and plugin_info["enabled"]:
                return True
        return False

    async def enable(self):
        for entry_point in await self.get_entry_points():
            if entry_point not in babase.app.config["Plugins"]:
                babase.app.config["Plugins"][entry_point] = {}
            babase.app.config["Plugins"][entry_point]["enabled"] = True
            plugin_spec = bui.app.plugins.plugin_specs.get(entry_point)
            if plugin_spec not in bui.app.plugins.active_plugins:
                self.load_plugin(entry_point)
                bui.screenmessage(f"{entry_point} loaded")
        if await self.has_minigames():
            self.load_minigames()
        self.save()

    def load_plugin(self, entry_point):
        plugin_class = babase.getclass(entry_point, babase.Plugin)
        loaded_plugin_instance = plugin_class()
        loaded_plugin_instance.on_app_running()

        plugin_spec = babase.PluginSpec(class_path=entry_point, loadable=True)
        plugin_spec.enabled = True
        plugin_spec.plugin = loaded_plugin_instance
        bui.app.plugins.plugin_specs[entry_point] = plugin_spec
        bui.app.plugins.active_plugins.append(plugin_spec.plugin)

    def disable(self):
        for entry_point, plugin_info in babase.app.config["Plugins"].items():
            if entry_point.startswith(self._entry_point_initials):
                plugin_info["enabled"] = False
        self.save()

    def set_version(self, version):
        app = babase.app
        app.config["Community Plugin Manager"]["Installed Plugins"][self.name]["version"] = version
        return self

    async def set_content(self, content):
        if not self._content:

            await loop.run_in_executor(pool, self._set_content, content)
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
        babase.app.config.commit()
        return self


class PluginVersion:
    def __init__(self, plugin, version, tag=CURRENT_TAG):
        self.number, info = version
        # Plugin already owns its PluginVersions (via `versions`,
        # `latest_version`, `latest_compatible_version`); holding a strong
        # back-reference here would form a Plugin<->PluginVersion cycle
        # that only the cyclic GC can free. A weakref avoids that so
        # they're freed by refcounting alone.
        self._plugin_ref = weakref.ref(plugin)
        self.api_version = info["api_version"]
        self.released_on = info["released_on"]
        self.commit_sha = info["commit_sha"]
        self.md5sum = info["md5sum"]

        self.download_url = plugin.url.format(content_type="raw", tag=tag)
        self.view_url = plugin.url.format(content_type="blob", tag=tag)

    @property
    def plugin(self):
        return self._plugin_ref()

    def __eq__(self, plugin_version):
        return (self.number, self.plugin.name) == (plugin_version.number,
                                                   plugin_version.plugin.name)

    def __repr__(self):
        return f"<PluginVersion({self.plugin.name} {self.number})>"

    @property
    def released_on_date(self):
        return datetime.strptime(self.released_on, "%d-%m-%Y")

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
        except MD5CheckSumFailed:
            logger.warning("%s %s failed its MD5 check during installation.",
                           self.plugin.name, self.number)
            if not suppress_screenmessage:
                bui.screenmessage(
                    f"{self.plugin.name} failed MD5 checksum during installation", color=(1, 0, 0))
            return False
        else:
            if not suppress_screenmessage:
                bui.screenmessage(f"{self.plugin.name} installed", color=(0, 1, 0))
            check = babase.app.config["Community Plugin Manager"]["Settings"]
            if check["Auto Enable Plugins After Installation"]:
                await local_plugin.enable()
            return True


class Plugin:
    def __init__(self, plugin, url, tag=CURRENT_TAG):
        """
        Initialize a plugin from network repository.
        """
        self.name, self.info = plugin
        self.install_path = os.path.join(PLUGIN_DIRECTORY, f"{self.name}.py")
        self.url = url
        self.tag = tag
        self._local_plugin = None

        self._versions = None
        self._latest_version = None
        self._latest_compatible_version = None

    def __repr__(self):
        return f"<Plugin({self.name})>"

    def __str__(self):
        return self.name

    @property
    def view_url(self):
        if not self.is_compatible or self.latest_compatible_version == self.latest_version:
            tag = self.tag
        else:
            tag = self.latest_compatible_version.commit_sha
        return self.url.format(content_type="blob", tag=tag)

    @property
    def is_compatible(self):
        try:
            self.latest_compatible_version
        except NoCompatibleVersion:
            return False
        return True

    @property
    def incompatibility_reason(self):
        """Why no version of this plugin runs here, in a few words; None if one does."""
        if self.is_compatible:
            return None
        min_builds = [
            info.get("min_engine_build", 0)
            for info in self.info["versions"].values()
            if info["api_version"] == _app_api_version
        ]
        if min_builds:
            return f"needs build {min(min_builds)}+"
        if not self.info["versions"]:
            return "no versions"
        return f"API {self.latest_version.api_version}"

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
                    tag=self.tag,
                ) for version in self.info["versions"].items()
            ]
        return self._versions

    @property
    def latest_version(self):
        if self._latest_version is None:
            self._latest_version = PluginVersion(
                self,
                tuple(self.info["versions"].items())[0],
                tag=self.tag,
            )
        return self._latest_version

    @property
    def latest_compatible_version(self):
        if self._latest_compatible_version is None:
            for number, info in self.info["versions"].items():
                if _runs_on_this_build(info):
                    self._latest_compatible_version = PluginVersion(
                        self,
                        (number, info),
                        tag=self.tag if self.latest_version.number == number else info["commit_sha"]
                    )
                    break
        if self._latest_compatible_version is None:
            raise NoCompatibleVersion(
                f"{self.name} has no version that runs on this game "
                f"(API {_app_api_version}, build {babase.app.env.engine_build_number})."
            )
        return self._latest_compatible_version

    def get_local(self):
        if not self.is_installed:
            raise PluginNotInstalled(
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
        bui.screenmessage(f"{self.name} uninstalled", color=(0.9, 1, 0))

    def has_update(self):
        try:
            latest_compatible_version = self.latest_compatible_version
        except NoCompatibleVersion:
            return False
        else:
            return self.get_local().version != latest_compatible_version.number

    async def update(self):
        if await self.latest_compatible_version.install(suppress_screenmessage=True):
            logger.info("Updated plugin %s to %s.", self.name,
                        self.latest_compatible_version.number)
            bui.screenmessage(f"{self.name} updated to {self.latest_compatible_version.number}",
                              color=(0, 1, 0))
            bui.getsound('shieldUp').play()
        else:
            bui.screenmessage(f"{self.name} failed MD5 checksum while updating to "
                              f"{self.latest_compatible_version.number}",
                              color=(1, 0, 0))
            bui.getsound('error').play()


class PluginManager:
    def __init__(self):
        self.request_headers = HEADERS
        self._index = _CACHE.get("index", {})
        # The raw changelog text, kept separate from the parsed entry in
        # _CACHE["changelog"]; see setup_changelog().
        self._changelog = _CACHE.get("changelog_source")
        self.categories = {}
        self.module_path = __file__
        self._index_setup_in_progress = False
        self._changelog_setup_in_progress = False

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
            content = await async_send_network_request(request)
            index = json.loads(content)
            self.set_index_global_cache(index)
            self._index = index
        return self._index

    async def setup_index(self):
        while self._index_setup_in_progress:
            # Avoid making multiple network calls to the same resource in parallel.
            # Rather wait for the previous network call to complete.
            await asyncio.sleep(0.1)
        self._index_setup_in_progress = not bool(self._index)
        try:
            index = await self.get_index()
            await self.setup_plugin_categories(index)
        finally:
            # Must clear even when the setup raised, or every later call
            # spins in the loop above forever waiting on a call that has
            # already given up.
            self._index_setup_in_progress = False

    async def get_changelog(self) -> str:
        """The full CHANGELOG.md text, fetched once per session."""
        if not self._changelog:
            request = urllib.request.Request(CHANGELOG_META.format(
                repository_url=REPOSITORY_URL,
                content_type="raw",
                tag=CURRENT_TAG
            ),
                headers=self.request_headers)
            content = await async_send_network_request(request)
            self._changelog = content.decode()
            self.set_changelog_source_global_cache(self._changelog)
        return self._changelog

    async def setup_changelog(self, version=None) -> None:
        if version is None:
            version = PLUGIN_MANAGER_VERSION
        while self._changelog_setup_in_progress:
            # Avoid making multiple network calls to the same resource in parallel.
            # Rather wait for the previous network call to complete.
            await asyncio.sleep(0.1)
        self._changelog_setup_in_progress = not bool(self._changelog)
        try:
            try:
                # Parsing is pure string work on text we already hold, so it
                # runs every time rather than only on the call that fetched.
                # Skipping it was what let the raw text reach the cache in
                # place of the parsed entry ChangelogWindow reads.
                full_changelog = await self.get_changelog()
                pattern = rf"### {version} \(\d\d-\d\d-\d{{4}}\)\n(.*?)(?=### \d+\.\d+\.\d+|\Z)"
                if (len(full_changelog.split(version)) > 1):
                    released_on = full_changelog.split(version)[1].split('\n')[0]
                    matches = re.findall(pattern, full_changelog, re.DOTALL)
                else:
                    released_on = ' (Not Provided)'
                    matches = None

                if matches:
                    changelog = {
                        'released_on': released_on,
                        'info': matches[0].strip()
                    }
                else:
                    changelog = {'released_on': released_on,
                                 'info': f"Changelog entry for version {version} not found."}
            except urllib.error.URLError:
                changelog = {'released_on': ' (Not Provided)',
                             'info': 'Could not get ChangeLog due to Internet Issues.'}
            self.set_changelog_global_cache(changelog)
        finally:
            # Must clear even when the setup raised, or every later call
            # spins in the loop above forever waiting on a call that has
            # already given up.
            self._changelog_setup_in_progress = False

    async def setup_plugin_categories(self, plugin_index):
        # A hack to have the "All" category show at the top.
        self.categories["All"] = None

        requests = []
        for meta_url in plugin_index["categories"]:
            category = Category(meta_url)
            request = category.fetch_metadata()
            requests.append(request)
        for source in babase.app.config["Community Plugin Manager"]["Custom Sources"]:
            source_splits = source.split("@", maxsplit=1)
            if len(source_splits) == 1:
                # Fallack to `main` if `@branchname` isn't specified in an external source URI.
                source_repo, source_tag = source_splits[0], "main"
            else:
                source_repo, source_tag = source_splits
            meta_url = partial_format(
                plugin_index["external_source_url"],
                repository=source_repo,
            )
            category = Category(meta_url, tag=source_tag)
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
        self._changelog = None
        self.unset_index_global_cache()

    async def refresh(self):
        self.cleanup()
        await self.setup_index()

    def set_index_global_cache(self, index):
        _CACHE["index"] = index

    def set_changelog_global_cache(self, changelog):
        _CACHE["changelog"] = changelog

    def set_changelog_source_global_cache(self, changelog_source):
        _CACHE["changelog_source"] = changelog_source

    def unset_index_global_cache(self):
        for key in ("index", "changelog", "changelog_source"):
            _CACHE.pop(key, None)

    async def get_update_details(self):
        """The (version, commit_sha) to update to, or None to stay put.

        That's the newest release this game build can run, and only if it
        is newer than the running one: a development or staging build
        ahead of the index is never "updated" backwards.
        """
        index = await self.get_index()
        current = _version_key(PLUGIN_MANAGER_VERSION)
        for version, info in index["versions"].items():
            if not _runs_on_this_build(info):
                # Another API, or built for a newer game than this one; fall
                # back to the newest version below it that this build can run.
                continue
            target = _version_key(version)
            if current is None or target is None or target <= current:
                return None
            # Always fetch at the release's own commit, never the branch:
            # raw.githubusercontent.com caches a branch for a few minutes,
            # per file, so right after a push index.json and
            # plugin_manager.py can disagree and fail the MD5 check.
            return version, info["commit_sha"]
        return None

    async def update(self, to_version, commit_sha):
        """Replace this file with `to_version`, fetched at `commit_sha`.

        Both auto-update and the settings window's update button come
        through here, so consecutive failures are counted here too (see
        _record_update_failure()).
        """
        index = await self.get_index()
        to_version_info = index["versions"][to_version]
        download_url = index["plugin_manager_url"].format(
            content_type="raw",
            tag=commit_sha,
        )
        try:
            content = await async_send_network_request(download_url)
            if hashlib.md5(content).hexdigest() != to_version_info["md5sum"]:
                raise MD5CheckSumFailed("MD5 checksum failed during plugin manager update.")
        except (MD5CheckSumFailed, urllib.error.URLError):
            logger.warning("Self-update to v%s failed.", to_version, exc_info=True)
            _record_update_failure(to_version)
            raise
        with open(self.module_path, "wb") as fout:
            fout.write(content)
        logger.info("Updated itself from v%s to v%s; takes effect on restart.",
                    PLUGIN_MANAGER_VERSION, to_version)
        _set_update_failures(0)
        return to_version_info

    async def soft_refresh(self):
        pass


class ChangelogWindow(popup.PopupWindow):
    def __init__(self, origin_widget):
        self.scale_origin = origin_widget.get_screen_space_center()
        s = 1.65 if _uiscale() is babase.UIScale.SMALL else 1.39 if _uiscale() is babase.UIScale.MEDIUM else 1.67
        width = 400 * s
        height = width * 0.6
        color = (1, 1, 1)
        text_scale = 0.7 * s
        self._transition_out = 'out_scale'
        transition = 'in_scale'

        self._root_widget = bui.containerwidget(
            size=(width, height),
            on_outside_click_call=self._back,
            transition=transition,
            scale=(1.5 if _uiscale() is babase.UIScale.SMALL else 1.5 if _uiscale()
                   is babase.UIScale.MEDIUM else 1.0),
            scale_origin_stack_offset=self.scale_origin
        )

        _add_popup(self)

        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.49, height * 0.87),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text='ChangeLog',
            scale=text_scale * 1.25,
            color=bui.app.ui_v1.title_color,
            maxwidth=width * 0.9
        )

        back_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.1, height * 0.8),
            size=(60, 60),
            scale=0.8,
            label=_charstr(babase.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self._back,
            enable_sound=False
        )

        bui.containerwidget(edit=self._root_widget, cancel_button=back_button)

        try:
            released_on = _CACHE['changelog']['released_on']
            logs = _CACHE['changelog']['info'].split('\n')
            h_align = 'left'
        except KeyError:
            released_on = ''
            logs = ["Could not load ChangeLog"]
            h_align = 'center'

        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.49, height * 0.75),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=PLUGIN_MANAGER_VERSION + released_on,
            scale=text_scale * 0.9,
            color=color,
            maxwidth=width * 0.9
        )

        bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.7, height * 0.72),
            size=(140, 60),
            scale=0.8,
            label='Full ChangeLog',
            button_type='square',
            enable_sound=False,
            on_activate_call=lambda: (
                bui.getsound('deek').play() or
                bui.open_url(REPOSITORY_URL + '/blob/main/CHANGELOG.md')
            )
        )

        # The entry can be arbitrarily long, so it scrolls rather than
        # spilling out of the bottom of the window.
        scroll_width = width * 0.88
        scroll_height = height * 0.62
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            size=(scroll_width, scroll_height),
            position=(width * 0.06, height * 0.04),
            capture_arrows=True
        )

        body_scale = text_scale * 0.7
        line_height = 36 * body_scale
        text_width = scroll_width - 30
        if h_align == 'left':
            # Leave headroom below `maxwidth` so no line ends up shrunk
            # (and thus smaller than its neighbours) by a rounding hair.
            logs = _wrap_markdown_bullets(logs, text_width * 0.95, body_scale)

        content_height = max(scroll_height, line_height * len(logs) + 20)
        content = bui.containerwidget(
            parent=self._scrollwidget,
            size=(text_width, content_height),
            background=False,
            claims_left_right=False
        )

        loop_height = content_height - line_height * 0.5 - 10
        for log in logs:
            bui.textwidget(
                parent=content,
                position=(text_width * 0.5 if h_align == 'center' else 0,
                          loop_height),
                size=(0, 0),
                h_align=h_align,
                v_align='center',
                text=log,
                scale=body_scale,
                color=color,
                maxwidth=text_width
            )
            loop_height -= line_height

    def _back(self) -> None:
        bui.getsound('swish').play()
        _remove_popup(self)
        bui.containerwidget(edit=self._root_widget, transition='out_scale')


class AuthorsWindow(popup.PopupWindow):
    def __init__(self, authors_info, origin_widget):
        self.authors_info = authors_info
        self.scale_origin = origin_widget.get_screen_space_center()
        s = 1.25 if _uiscale() is babase.UIScale.SMALL else 1.39 if _uiscale() is babase.UIScale.MEDIUM else 1.67
        width = 400 * s
        height = width * 0.8
        color = (1, 1, 1)
        text_scale = 0.7 * s
        self._transition_out = 'out_scale'
        transition = 'in_scale'

        self._root_widget = bui.containerwidget(
            size=(width, height),
            on_outside_click_call=self._back,
            transition=transition,
            scale=(1.5 if _uiscale() is babase.UIScale.SMALL else 1.5
                   if _uiscale() is babase.UIScale.MEDIUM else 1.0),
            scale_origin_stack_offset=self.scale_origin
        )

        _add_popup(self)

        pos = height * 0.9
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.49, pos),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text='Authors',
            scale=text_scale * 1.25,
            color=color,
            maxwidth=width * 0.9
        )

        back_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.1, height * 0.87),
            size=(60, 60),
            scale=0.8,
            label=_charstr(babase.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self._back,
            enable_sound=False
        )

        bui.containerwidget(edit=self._root_widget, cancel_button=back_button)

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            size=(width * 0.8, height * 0.75),
            position=(width * 0.1, height * 0.1)
        )
        self._columnwidget = bui.columnwidget(
            parent=self._scrollwidget,
            border=1,
            left_border=-15,
            margin=0
        )

        for author in self.authors_info:
            for key, value in author.items():
                text = f"{key.title()}: {value if value != '' else 'Not Provided'}"
                if key == 'name':
                    text = value
                bui.textwidget(
                    parent=self._columnwidget,
                    size=(width * 0.8, 35 if key == 'name' else 30),
                    color=color if key == 'name' else (0.75, 0.7, 0.8),
                    scale=(
                        (1.1 if key == 'name' else 0.9) if _uiscale() is babase.UIScale.SMALL else
                        (1.2 if key == 'name' else 1.0)
                    ),
                    text=text,
                    h_align='center',
                    v_align='center',
                    maxwidth=420
                )
            bui.textwidget(
                parent=self._columnwidget,
                size=(width * 0.8, 30),
                always_highlight=True,
                h_align='center',
                v_align='center'
            )

    def _back(self) -> None:
        bui.getsound('swish').play()
        _remove_popup(self)
        bui.containerwidget(edit=self._root_widget, transition='out_scale')


class PluginWindow(popup.PopupWindow):
    def __init__(
        self,
        plugin: Plugin,
        origin_widget,
        plugins_list,
        transition='in_scale',
        button_callback=lambda: None,
    ):
        self.plugin: Plugin = plugin
        self.transition = transition
        self.plugins_list = plugins_list
        self.button_callback = button_callback
        self.scale_origin = origin_widget.get_screen_space_center()

        loop.create_task(self.draw_ui())

    def get_description(self, minimum_character_offset=40):
        """
        Splits the long plugin description into multiple lines.
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
        bui.getsound('swish').play()
        b_text_color = (0.75, 0.7, 0.8)
        s = 1.25 if _uiscale() is babase.UIScale.SMALL else 1.39 if babase.UIScale.MEDIUM else 1.67
        width = 450 * s
        height = 120 + 100 * s
        color = (1, 1, 1)
        text_scale = 0.7 * s

        self._root_widget = bui.containerwidget(
            size=(width, height),
            on_outside_click_call=self._cancel,
            transition=self.transition,
            scale=(2.1 if _uiscale() is babase.UIScale.SMALL else 1.5
                   if _uiscale() is babase.UIScale.MEDIUM else 1.0),
            scale_origin_stack_offset=self.scale_origin
        )

        _add_popup(self)

        i = self.plugins_list.index(self.plugin)
        self.p_n_plugins = [
            self.plugins_list[i-1] if (i-1 > -1) else None,
            self.plugins_list[i+1] if (i+1 < len(self.plugins_list)) else None
        ]

        # initialize all widgets
        previous_plugin_button = None
        next_plugin_button = None
        author_text_control_btn = None
        button1 = None
        button2 = None
        button3 = None
        more_button = None
        settings_button = None
        tutorial_button = None

        # previous plugin button
        if self.p_n_plugins[0] is not None:
            previous_plugin_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(-12.5*s + (4 if _uiscale() is babase.UIScale.SMALL else -5),
                          height/2 - 20*s),
                label=_charstr(bui.SpecialChar.LEFT_ARROW),
                size=(25, 40),
                color=(1, 0.5, 0.5),
                scale=s,
                on_activate_call=self.show_previous_plugin,
                enable_sound=False,
                textcolor=(1, 1, 1)
            )

        # next plugin button
        if self.p_n_plugins[1] is not None:
            next_plugin_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(width - 12.5*s - (8 if _uiscale()
                          is babase.UIScale.SMALL else 0), height/2 - 20*s),
                label=_charstr(bui.SpecialChar.RIGHT_ARROW),
                size=(25, 40),
                color=(1, 0.5, 0.5),
                scale=s,
                on_activate_call=self.show_next_plugin,
                enable_sound=False,
                textcolor=(1, 1, 1)
            )

        pos = height * 0.85
        plug_name = self.plugin.name.replace('_', ' ').title()
        plugin_title = plug_name
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.49, pos),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=plugin_title,
            scale=text_scale * 1.25,
            color=color,
            maxwidth=width * 0.7 - 40
        )
        pos -= 25

        # author
        text = 'by ' + ', '.join([author["name"] for author in self.plugin.info["authors"]])
        author_text_control_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.49 - (len(text)*14/2), pos - 10),
            size=(len(text)*14, 20),
            label='',
            texture=bui.gettexture("empty"),
            on_activate_call=lambda: AuthorsWindow(self.plugin.info["authors"], self._root_widget)
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.49 - (len(text)*14/2), pos - 10),
            size=(len(text)*14, 20),
            h_align='center',
            v_align='center',
            text=text,
            scale=text_scale * 0.8,
            color=(0.75, 0.7, 0.8),
            maxwidth=width * 0.9,
            draw_controller=author_text_control_btn,
        )
        pos -= 60

        # info
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.49, pos),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=self.get_description(),
            scale=text_scale * 0.6,
            color=color,
            maxwidth=width * 0.95
        )

        b1_color = None
        b2_color = (0.8, 0.15, 0.35)
        b3_color = (0.2, 0.8, 0.3)
        pos = height * 0.1
        button_size = (80 * s, 40 * s)

        to_draw_button1 = True
        to_draw_settings_button = False
        has_update = False

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
                        to_draw_settings_button = True
                else:
                    button1_label = "Enable"
                    button1_action = self.enable
            button2_label = "Uninstall"
            button2_action = self.uninstall
            has_update = self.plugin.has_update()
            if has_update:
                button3_label = "Update"
                button3_action = self.update
        elif self.plugin.is_compatible:
            button1_label = "Install"
            button1_action = self.install
        else:
            to_draw_button1 = False
            bui.textwidget(
                parent=self._root_widget,
                position=(width * 0.49, pos + button_size[1] / 2),
                size=(0, 0),
                h_align='center',
                v_align='center',
                text=f"Not compatible with this game ({self.plugin.incompatibility_reason})",
                scale=text_scale * 0.7,
                color=(1, 0.4, 0.4),
                maxwidth=width * 0.7
            )

        # button1
        if to_draw_button1:
            button1 = bui.buttonwidget(
                parent=self._root_widget,
                position=(
                    width * (0.1 if self.plugin.is_installed and has_update else
                             0.25 if self.plugin.is_installed else 0.4), pos
                ),
                size=button_size,
                on_activate_call=button1_action,
                color=b1_color,
                textcolor=b_text_color,
                button_type='square',
                text_scale=1,
                label=button1_label
            )

        # button2
        if self.plugin.is_installed:
            button2 = bui.buttonwidget(
                parent=self._root_widget,
                position=(
                    width * (0.4 if has_update or not to_draw_button1 else 0.55), pos),
                size=button_size,
                on_activate_call=button2_action,
                color=b2_color,
                textcolor=b_text_color,
                button_type='square',
                text_scale=1,
                label=button2_label
            )

            # button3
            if has_update:
                button3 = bui.buttonwidget(
                    parent=self._root_widget,
                    position=(width * 0.7, pos),
                    size=button_size,
                    on_activate_call=button3_action,
                    color=b3_color,
                    textcolor=b_text_color,
                    autoselect=True,
                    button_type='square',
                    text_scale=1,
                    label=button3_label
                )

        # determine selected button
        selected_btn = button3 if has_update and self.plugin.is_installed else (
            button2 if self.plugin.is_installed else button1
        )

        bui.containerwidget(
            edit=self._root_widget,
            on_cancel_call=self._cancel,
            selected_child=selected_btn
        )

        # button math
        button_x = width - 90
        button_y = 210 - _by_scale(5, 10, 15)
        button_color = (0, 0.75, 0.75)
        button_image_color = (0.8, 0.95, 1)
        button_text_color = (1, 1, 1, 1)

        # more button
        more_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(button_x, button_y),
            size=(40, 40),
            button_type='square',
            label='',
            color=button_color
        )
        bui.buttonwidget(
            edit=more_button,
            on_activate_call=babase.CallPartial(
                MoreWindow,
                plugin=self.plugin,
                origin=more_button
            )
        )
        bui.imagewidget(
            parent=self._root_widget,
            position=(button_x, button_y),
            size=(40, 40),
            color=button_image_color,
            texture=bui.gettexture('file'),
            draw_controller=more_button
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(button_x-3, button_y+12),
            text='More...',
            size=(10, 10),
            draw_controller=more_button,
            color=button_text_color,
            rotate=25,
            scale=0.45
        )

        # settings button
        if to_draw_settings_button:
            button_y -= 50
            settings_button = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(button_x, button_y),
                size=(40, 40),
                button_type="square",
                label="",
                color=button_color
            )
            bui.buttonwidget(
                edit=settings_button,
                on_activate_call=babase.CallPartial(self.settings, settings_button)
            )
            bui.imagewidget(
                parent=self._root_widget,
                position=(button_x, button_y),
                size=(40, 40),
                color=button_image_color,
                texture=bui.gettexture("settingsIcon"),
                draw_controller=settings_button
            )

        # tutorial
        tutorial_url = self.plugin.info['external_url']
        if tutorial_url:
            button_y -= 50
            tutorial_button = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(button_x, button_y),
                size=(40, 40),
                button_type="square",
                label="",
                color=button_color
            )
            bui.imagewidget(
                parent=self._root_widget,
                position=(button_x, button_y),
                size=(40, 40),
                color=button_image_color,
                texture=bui.gettexture("frameInset"),
                draw_controller=tutorial_button
            )
            bui.textwidget(
                parent=self._root_widget,
                position=(button_x - 3, button_y + 12),
                text="Tutorial",
                size=(10, 10),
                draw_controller=tutorial_button,
                color=button_text_color,
                rotate=25,
                scale=0.45
            )
            bui.buttonwidget(
                tutorial_button,
                on_activate_call=bui.CallPartial(
                    confirm.ConfirmWindow,
                    text=f'This will take you to:\n{tutorial_url}',
                    origin_widget=tutorial_button,
                    action=bui.CallPartial(
                        bui.open_url, tutorial_url
                    )
                )
            )
        # navigation #XXX
        if button1 and button2 and button3:
            # three buttons
            leftmost_button = button1
            center_button = button2
            rightmost_button = button3
        elif button1 and button2:
            # two buttons
            leftmost_button = button1
            center_button = None
            rightmost_button = button2
        elif button2 and button3:
            # two buttons
            leftmost_button = button2
            center_button = None
            rightmost_button = button3
        elif button1:
            # one button
            leftmost_button = button1
            center_button = None
            rightmost_button = button1
        elif button2:
            # one button
            leftmost_button = button2
            center_button = None
            rightmost_button = button2
        else:
            # Incompatible and not installed: nothing to install or manage, so
            # More... is the first thing to land on.
            leftmost_button = more_button
            center_button = None
            rightmost_button = previous_plugin_button
            bui.containerwidget(edit=self._root_widget, selected_child=more_button)

        # determine vertical stack
        bottom_stack = tutorial_button or settings_button or more_button
        top_stack = more_button

        # previous plugin button
        if previous_plugin_button is not None:
            bui.buttonwidget(
                edit=previous_plugin_button,
                left_widget=next_plugin_button,
                right_widget=leftmost_button,
                up_widget=author_text_control_btn,
                down_widget=leftmost_button
            )

        # next plugin button
        if next_plugin_button is not None:
            bui.buttonwidget(
                edit=next_plugin_button,
                left_widget=bottom_stack,
                right_widget=bui.get_special_widget('squad_button'),
                up_widget=author_text_control_btn,
                down_widget=bottom_stack
            )

        # author button
        bui.buttonwidget(
            edit=author_text_control_btn,
            left_widget=previous_plugin_button,
            right_widget=top_stack,
            up_widget=center_button or leftmost_button,
            down_widget=leftmost_button
        )

        # button1
        if button1 is not None:
            bui.buttonwidget(
                edit=button1,
                left_widget=previous_plugin_button,
                right_widget=center_button or bottom_stack,
                up_widget=author_text_control_btn,
                down_widget=author_text_control_btn
            )

        # button2
        if button2 is not None:
            bui.buttonwidget(
                edit=button2,
                left_widget=button1 or previous_plugin_button,
                right_widget=button3 or bottom_stack,
                up_widget=author_text_control_btn,
                down_widget=author_text_control_btn
            )

        # button3
        if button3 is not None:
            bui.buttonwidget(
                edit=button3,
                left_widget=center_button or leftmost_button,
                right_widget=bottom_stack,
                up_widget=author_text_control_btn,
                down_widget=author_text_control_btn
            )

        # more button
        bui.buttonwidget(
            edit=more_button,
            left_widget=rightmost_button,
            right_widget=next_plugin_button,
            up_widget=author_text_control_btn,
            down_widget=settings_button
        )

        # settings button
        if settings_button is not None:
            bui.buttonwidget(
                edit=settings_button,
                left_widget=rightmost_button,
                right_widget=next_plugin_button,
                up_widget=more_button,
                down_widget=tutorial_button
            )

        # tutorial button
        if tutorial_button is not None:
            bui.buttonwidget(
                edit=tutorial_button,
                left_widget=rightmost_button,
                right_widget=next_plugin_button,
                up_widget=settings_button or more_button,
                down_widget=rightmost_button
            )

    def _ok(self) -> None:
        _remove_popup(self)
        bui.containerwidget(edit=self._root_widget, transition='out_scale')

    def _cancel(self) -> None:
        bui.getsound('swish').play()
        _remove_popup(self)
        bui.containerwidget(edit=self._root_widget, transition='out_scale')

    @staticmethod
    def button(fn):
        async def asyncio_handler(fn, self, *args, **kwargs):
            await fn(self, *args, **kwargs)
            await self.button_callback()

        def wrapper(self, *args, **kwargs):
            self._ok()

            if asyncio.iscoroutinefunction(fn):
                loop.create_task(asyncio_handler(fn, self, *args, **kwargs))
            else:
                fn(self, *args, **kwargs)
                loop.create_task(self.button_callback())

        return wrapper

    def settings(self, source_widget):
        self.local_plugin.launch_settings(source_widget)

    def show_previous_plugin(self):
        bui.containerwidget(edit=self._root_widget, transition='out_right')
        _remove_popup(self)
        PluginWindow(
            self.p_n_plugins[0],
            self._root_widget,
            transition='in_left',
            plugins_list=self.plugins_list,
            button_callback=lambda: None
        )

    def show_next_plugin(self):
        bui.containerwidget(edit=self._root_widget, transition='out_left')
        _remove_popup(self)
        PluginWindow(
            self.p_n_plugins[1],
            self._root_widget,
            transition='in_right',
            plugins_list=self.plugins_list,
            button_callback=lambda: None
        )

    @button
    def disable(self) -> None:
        self.local_plugin.disable()

    @button
    async def enable(self) -> None:
        await self.local_plugin.enable()
        bui.getsound('gunCocking').play()

    @button
    async def install(self):
        await self.plugin.latest_compatible_version.install()
        bui.getsound('cashRegister2').play()

    @button
    async def uninstall(self):
        await self.plugin.uninstall()
        bui.getsound('shieldDown').play()

    @button
    async def update(self):
        await self.plugin.update()
        bui.getsound('shieldUp').play()


class MoreWindow:
    def __init__(self, plugin: Plugin, origin=None):
        _add_popup(self)

        self.plugin = plugin
        # collect info
        # Versions are listed newest first, so the last one is the plugin's
        # first release, whichever API it targeted.
        released_on = tuple(plugin.info['versions'].values())[-1]['released_on']
        # Matches the version shown below: the newest one that runs here, or
        # for an incompatible plugin (listed via Show incompatible plugins),
        # the newest one overall.
        last_updated = (
            plugin.latest_compatible_version if plugin.is_compatible else plugin.latest_version
        ).released_on
        # math
        step = 40
        margin = 20
        width = 350
        px, py = margin, margin
        px2 = width-(margin+step)
        mw = px2-margin*2
        # root
        self.transition = origin and 'scale' or 'left'
        self._root_widget = bui.containerwidget(
            on_outside_click_call=self._back,
            transition=f'in_{self.transition}',
            scale=_by_scale(1.5, 1.5, 1),
            scale_origin_stack_offset=(
                origin and
                origin.get_screen_space_center()
                or None
            )
        )
        # last updated
        bui.textwidget(
            parent=self._root_widget,
            position=(px, py),
            h_align='left',
            v_align='center',
            maxwidth=width-margin*2,
            max_height=step,
            size=(step, step),
            text=(
                last_updated and
                f'Last updated on: {last_updated}'
                or 'Unknown'
            )
        )
        # released on
        py += margin+step/3
        bui.textwidget(
            parent=self._root_widget,
            position=(px, py),
            h_align='left',
            v_align='center',
            maxwidth=width-margin*2,
            max_height=step,
            size=(step, step),
            text=(
                released_on and
                f'Released on: {released_on}'
                or 'Unknown'
            )
        )
        # version
        py += margin+step/3
        bui.textwidget(
            parent=self._root_widget,
            position=(px, py),
            h_align='left',
            v_align='center',
            maxwidth=mw,
            max_height=step,
            size=(step, step),
            text=(
                f"Version: {plugin.latest_compatible_version.number}"
                if plugin.is_compatible else
                f"Version: {plugin.latest_version.number} ({plugin.incompatibility_reason})"
            )
        )
        # source url
        py += step+margin
        bui.textwidget(
            parent=self._root_widget,
            position=(px, py),
            h_align='left',
            v_align='center',
            maxwidth=mw,
            max_height=step,
            size=(step, step),
            text='Source URL:'
        )
        source_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(px2, py),
            size=(step, step),
            color=(0.6, 0.53, 0.63),
            button_type='square',
            label='',
            on_activate_call=bui.CallPartial(
                bui.open_url,
                plugin.view_url
            )
        )
        bui.imagewidget(
            parent=self._root_widget,
            position=(px2, py),
            size=(step, step),
            color=(0.8, 0.95, 1),
            texture=bui.gettexture('file'),
            draw_controller=source_button
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(px2-3, py+12),
            text='source',
            size=(10, 10),
            draw_controller=source_button,
            rotate=25,
            scale=0.45
        )
        # report bug
        py += step+margin
        bui.textwidget(
            parent=self._root_widget,
            position=(px, py),
            h_align='left',
            v_align='center',
            maxwidth=mw,
            max_height=step,
            size=(step, step),
            text='Report a bug:'
        )
        report_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(px2, py),
            size=(step, step),
            button_type='square',
            color=(0.6, 0.53, 0.63),
            label='',
            on_activate_call=self._open_bug_report_url
        )
        bui.imagewidget(
            parent=self._root_widget,
            position=(px2, py),
            size=(step, step),
            color=(0.8, 0.95, 1),
            texture=bui.gettexture('githubLogo'),
            draw_controller=report_button
        )
        # back
        py += step+margin
        back_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(px, py),
            size=(step, step),
            label=_charstr(babase.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self._back,
            enable_sound=False
        )
        # title
        px += margin
        bui.textwidget(
            parent=self._root_widget,
            position=(px+(step), py),
            h_align='left',
            v_align='center',
            maxwidth=width-margin*2,
            max_height=step*2,
            size=(step, step),
            text='More info',
            scale=1.4,
            shadow=0.8
        )
        # finally
        py += step+margin
        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=back_button,
            size=(width, py)
        )
        # navigation
        bui.buttonwidget(
            edit=back_button,
            left_widget=report_button,
            right_widget=report_button,
            up_widget=source_button,
            down_widget=report_button
        )

        bui.buttonwidget(
            edit=source_button,
            left_widget=back_button,
            right_widget=back_button,
            up_widget=report_button,
            down_widget=back_button
        )

        bui.buttonwidget(
            edit=report_button,
            left_widget=back_button,
            right_widget=back_button,
            up_widget=back_button,
            down_widget=source_button
        )

    def _open_bug_report_url(self):
        import platform
        import urllib.parse
        import baenv

        LOGS_LENGTH_LIMIT = 5000
        _logs = ""
        for entry in baenv._EnvGlobals.get().config.log_handler.get_cached().entries:
            _logs += entry.message + "\n"

        # reduce this more if it's too long
        error_logs = f"""```py
{_logs[:LOGS_LENGTH_LIMIT]}
```"""

        params = {
            "title": "[PLUGIN BUG]: " + self.plugin.name,
            "plugin-name": self.plugin.name,
            "plugin-version": self.plugin.create_local().version if self.plugin.is_installed else 'Not Installed',
            "plugin-manager-version": 'v' + PLUGIN_MANAGER_VERSION,
            "bombsquad-version": 'v' + babase.app.env.engine_version + " (" + str(babase.app.env.engine_build_number) + ")",
            "os-version": platform.platform() if platform else babase.app.env.platform.value + babase.app.env.os_version,
            "console-log": error_logs
        }
        query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        base_url = GITHUB_PLUGIN_ISSUE_META.format(
            repository_url=REPOSITORY_URL, issue_template=PLUGIN_ISSUE_TEMPLATE)
        final_url = f"{base_url}&{query_string}"
        bui.open_url(final_url)

    def _back(self) -> None:
        _remove_popup(self)
        bui.getsound('swish').play()
        bui.containerwidget(
            edit=self._root_widget,
            transition=f'out_{self.transition}'
        )


class PluginCustomSourcesWindow(popup.PopupWindow):
    def __init__(self, origin_widget):
        self.selected_source = None

        self.scale_origin = origin_widget.get_screen_space_center()

        b_textcolor = (0.75, 0.7, 0.8)
        self._transition_out = 'out_scale'
        transition = 'in_scale'
        self._root_widget = bui.containerwidget(
            size=(400, 340),
            on_outside_click_call=self._ok,
            transition=transition,
            scale=(2.1 if _uiscale() is babase.UIScale.SMALL else 1.5
                   if _uiscale() is babase.UIScale.MEDIUM else 1.0),
            scale_origin_stack_offset=self.scale_origin,
            on_cancel_call=self._ok
        )

        _add_popup(self)

        bui.textwidget(
            parent=self._root_widget,
            position=(155, 300),
            size=(100, 25),
            text="Custom Plugin Sources",
            color=bui.app.ui_v1.title_color,
            scale=0.8,
            h_align="center",
            v_align="center",
            maxwidth=270,
        )

        scroll_size_x = (290 if _uiscale() is babase.UIScale.SMALL else
                         300 if _uiscale() is babase.UIScale.MEDIUM else 290)
        scroll_size_y = (170 if _uiscale() is babase.UIScale.SMALL else
                         185 if _uiscale() is babase.UIScale.MEDIUM else 180)
        scroll_pos_x = (55 if _uiscale() is babase.UIScale.SMALL else
                        40 if _uiscale() is babase.UIScale.MEDIUM else 60)
        scroll_pos_y = 105

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            size=(scroll_size_x, scroll_size_y),
            position=(scroll_pos_x, scroll_pos_y)
        )
        self._columnwidget = bui.columnwidget(
            parent=self._scrollwidget,
            border=1, margin=0
        )

        delete_source_button_position_pos_x = 360
        delete_source_button_position_pos_y = 110
        delete_source_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(
                delete_source_button_position_pos_x, delete_source_button_position_pos_y
            ),
            size=(25, 25),
            label="",
            on_activate_call=self.delete_selected_source,
            button_type="square",
            color=(0.6, 0, 0)
        )

        bui.imagewidget(
            parent=self._root_widget,
            position=(
                delete_source_button_position_pos_x + 2, delete_source_button_position_pos_y
            ),
            size=(25, 25),
            color=(5, 2, 2),
            texture=bui.gettexture("crossOut"),
            draw_controller=delete_source_button
        )

        warning_pos_x = (43 if _uiscale() is babase.UIScale.SMALL else
                         35 if _uiscale() is babase.UIScale.MEDIUM else
                         48)
        bui.textwidget(
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

        self._add_source_widget = bui.textwidget(
            parent=self._root_widget,
            size=(335, 50),
            position=(21, 22),
            h_align='left',
            v_align='center',
            editable=True,
            scale=0.75,
            maxwidth=215,
            description="Add Source"
        )

        bui.buttonwidget(
            parent=self._root_widget,
            position=(330, 28),
            size=(37, 37),
            on_activate_call=lambda: loop.create_task(self.add_source()),
            label="",
            texture=bui.gettexture("startButton"),
            button_type="square",
            color=(0, 0.9, 0),
            textcolor=b_textcolor,
            text_scale=1
        )

        self.draw_sources()

    def draw_sources(self):
        for plugin in self._columnwidget.get_children():
            plugin.delete()

        color = (1, 1, 1)
        for custom_source in babase.app.config["Community Plugin Manager"]["Custom Sources"]:
            bui.textwidget(
                parent=self._columnwidget,
                selectable=True,
                color=color,
                text=custom_source,
                on_select_call=lambda: self.select_source(custom_source),
                h_align='left',
                v_align='center',
                scale=0.75,
                maxwidth=260
            )

    def select_source(self, source):
        self.selected_source = source

    async def add_source(self):
        source = bui.textwidget(query=self._add_source_widget)
        # External source URIs can optionally suffix `@branchname`, for example:
        # `bombsquad-community/sample-plugin-source@experimental`
        source_splits = source.split("@", maxsplit=1)
        if len(source_splits) == 1:
            # Fallack to `main` if `@branchname` isn't specified in an external source URI.
            source_repo, source_tag = source_splits[0], "main"
        else:
            source_repo, source_tag = source_splits
        meta_url = partial_format(
            _CACHE["index"]["external_source_url"],
            repository=source_repo,
        )
        category = Category(meta_url, tag=source_tag)
        try:
            await category.validate()
        except (PluginSourceNetworkError, CategoryMetadataParseError) as e:
            bui.screenmessage(str(e), color=(1, 0, 0))
            bui.getsound('error').play()
            return
        if source in babase.app.config["Community Plugin Manager"]["Custom Sources"]:
            bui.screenmessage("Plugin source already exists")
            bui.getsound('error').play()
            return
        babase.app.config["Community Plugin Manager"]["Custom Sources"].append(source)
        babase.app.config.commit()
        bui.screenmessage("Plugin source added; Refresh plugin list to see changes",
                          color=(0, 1, 0))
        bui.getsound('cashRegister2').play()
        self.draw_sources()

    def delete_selected_source(self):
        if self.selected_source is None:
            return
        babase.app.config["Community Plugin Manager"]["Custom Sources"].remove(self.selected_source)
        babase.app.config.commit()
        bui.screenmessage("Plugin source deleted; Refresh plugin list to see changes",
                          color=(0.9, 1, 0))
        bui.getsound('shieldDown').play()
        self.draw_sources()

    def _ok(self) -> None:
        bui.getsound('swish').play()
        _remove_popup(self)
        bui.containerwidget(edit=self._root_widget, transition='out_scale')


class PluginFilterWindow(popup.PopupWindow):
    """Pick the plugin list's category, sort order and incompatible-plugin visibility.

    Every change is applied to the list right away through `asyncio_callback`,
    called as `(category, sort, show_incompatible)`, so the popup can stay open
    while the user tries combinations.
    """

    def __init__(self, categories, category, sort, show_incompatible, origin_widget,
                 asyncio_callback):
        self._categories = (*categories, "Installed")
        self._category = category
        self._sort = sort
        self._show_incompatible = show_incompatible
        self._asyncio_callback = asyncio_callback
        self.scale_origin = origin_widget.get_screen_space_center()

        width, height = 420, 330
        column_width, column_height = 175, 140
        left_x, right_x = 25, 220
        column_y = 115
        b_textcolor = (0.8, 0.8, 0.85)

        self._root_widget = bui.containerwidget(
            size=(width, height),
            on_outside_click_call=self._ok,
            on_cancel_call=self._ok,
            transition='in_scale',
            scale=_by_scale(2.1, 1.5, 1.0),
            scale_origin_stack_offset=self.scale_origin
        )
        _add_popup(self)

        bui.textwidget(
            parent=self._root_widget,
            position=(0, height - 40),
            size=(width, 25),
            text="Filter & Sort",
            color=bui.app.ui_v1.title_color,
            scale=0.8,
            h_align="center",
            v_align="center",
            maxwidth=270,
        )
        for x, header in ((left_x, "Category"), (right_x, "Sort By")):
            bui.textwidget(
                parent=self._root_widget,
                position=(x + 5, column_y + column_height + 15),
                size=(column_width, 25),
                text=header,
                color=bui.app.ui_v1.title_color,
                scale=0.6,
                h_align="left",
                v_align="center",
            )

        self._category_rows, category_scroll = self._draw_choice_column(
            (left_x, column_y), (column_width, column_height),
            {name: name for name in self._categories}, self._select_category,
        )
        self._sort_rows, sort_scroll = self._draw_choice_column(
            (right_x, column_y), (column_width, column_height),
            {key: labels[0] for key, labels in SORT_OPTIONS.items()}, self._select_sort,
        )
        self._update_row_colors()

        incompatible_checkbox = bui.checkboxwidget(
            parent=self._root_widget,
            position=(left_x + 5, 68),
            size=(width - 2 * left_x, 30),
            text="Show incompatible plugins",
            value=self._show_incompatible,
            on_value_change_call=self._toggle_incompatible,
            maxwidth=width - 2 * left_x - 40,
            textcolor=(0.9, 0.9, 0.9),
            scale=0.8
        )

        done_button = bui.buttonwidget(
            parent=self._root_widget,
            position=((width - column_width) / 2, 20),
            size=(column_width, 35),
            label="Done",
            on_activate_call=self._ok,
            button_type="square",
            color=(0.2, 0.6, 0.3),
            textcolor=b_textcolor,
            text_scale=0.6
        )

        bui.widget(category_scroll, right_widget=sort_scroll, down_widget=incompatible_checkbox)
        bui.widget(sort_scroll, left_widget=category_scroll, down_widget=incompatible_checkbox)
        bui.widget(incompatible_checkbox, up_widget=category_scroll, down_widget=done_button)
        bui.widget(done_button, up_widget=incompatible_checkbox)
        bui.containerwidget(edit=self._root_widget, selected_child=category_scroll)

    def _draw_choice_column(self, position, size, choices, on_choose):
        """A scrollable column of selectable rows, one per choice; returns (rows, scroll)."""
        scroll = bui.scrollwidget(parent=self._root_widget, size=size, position=position)
        column = bui.columnwidget(parent=scroll, border=1, margin=0)
        rows = {}
        for key, label in choices.items():
            rows[key] = bui.textwidget(
                parent=column,
                size=(size[0] - 10, 28),
                selectable=True,
                always_highlight=True,
                click_activate=True,
                text=label,
                h_align='left',
                v_align='center',
                maxwidth=size[0] - 20,
                on_activate_call=babase.CallPartial(on_choose, key)
            )
        return rows, scroll

    def _update_row_colors(self):
        for rows, current in ((self._category_rows, self._category),
                              (self._sort_rows, self._sort)):
            for key, row in rows.items():
                bui.textwidget(
                    edit=row,
                    color=(0.5, 1, 0.5) if key == current else (0.75, 0.75, 0.75)
                )

    def _apply(self):
        self._update_row_colors()
        loop.create_task(
            self._asyncio_callback(self._category, self._sort, self._show_incompatible)
        )

    def _select_category(self, category):
        self._category = category
        bui.getsound('deek').play()
        self._apply()

    def _select_sort(self, sort):
        self._sort = sort
        bui.getsound('deek').play()
        self._apply()

    def _toggle_incompatible(self, value):
        self._show_incompatible = value
        self._apply()

    def _ok(self) -> None:
        bui.getsound('swish').play()
        _remove_popup(self)
        bui.containerwidget(edit=self._root_widget, transition='out_scale')


class PluginManagerWindow(bui.MainWindow):
    @override
    def main_window_should_preserve_selection(self) -> bool:
        return False

    def __init__(
        self,
        transition: str | None = "in_right",
        origin_widget: bui.Widget | None = None
    ):
        self.plugin_manager = PluginManager()
        self.filter_button = None
        self.selected_category = 'All'
        self.selected_sort = 'name_asc'
        self.show_incompatible = False
        self._draw_generation = 0
        self.plugins_in_current_view = {}
        global open_popups
        open_popups = []

        loop.create_task(self.draw_index())

        self._width = (700 if _uiscale() is babase.UIScale.SMALL
                       else 550 if _uiscale() is babase.UIScale.MEDIUM
                       else 570)
        self._height = (500 if _uiscale() is babase.UIScale.SMALL
                        else 422 if _uiscale() is babase.UIScale.MEDIUM
                        else 500)
        top_extra = 20 if _uiscale() is babase.UIScale.SMALL else 0

        if origin_widget:
            self._transition_out = "out_scale"
            self._scale_origin = origin_widget.get_screen_space_center()
            transition = "in_scale"

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + top_extra),
                toolbar_visibility="menu_minimal",
                scale=(1.9 if _uiscale() is babase.UIScale.SMALL
                       else 1.5 if _uiscale() is babase.UIScale.MEDIUM
                       else 1.0),
                stack_offset=(0, -25) if _uiscale() is babase.UIScale.SMALL else (0, 0)
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        back_pos_x = 5 + (37 if _uiscale() is babase.UIScale.SMALL else
                          27 if _uiscale() is babase.UIScale.MEDIUM else 68)
        back_pos_y = self._height - (95 if _uiscale() is babase.UIScale.SMALL else
                                     65 if _uiscale() is babase.UIScale.MEDIUM else 50)

        if _uiscale() is bui.UIScale.SMALL:
            self._back_button = None
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            self._back_button = back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(back_pos_x, back_pos_y),
                size=(60, 60),
                scale=0.8,
                label=_charstr(babase.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back
            )

            bui.containerwidget(edit=self._root_widget, cancel_button=back_button)

        title_pos = self._height - (83 if _uiscale() is babase.UIScale.SMALL else
                                    50 if _uiscale() is babase.UIScale.MEDIUM else 50)
        bui.textwidget(
            parent=self._root_widget,
            position=(-10, title_pos),
            size=(self._width, 25),
            text="Community Plugin Manager",
            color=bui.app.ui_v1.title_color,
            scale=1.05,
            h_align="center",
            v_align="center",
            maxwidth=270,
        )

        loading_pos_y = self._height - (275 if _uiscale() is babase.UIScale.SMALL else
                                        235 if _uiscale() is babase.UIScale.MEDIUM else 270)

        self._plugin_manager_status_text = bui.textwidget(
            parent=self._root_widget,
            position=(-5, loading_pos_y),
            size=(self._width, 25),
            text="",
            color=bui.app.ui_v1.title_color,
            scale=0.7,
            h_align="center",
            v_align="center",
            maxwidth=400,
        )
        self._loading_spinner = bui.spinnerwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, loading_pos_y),
            style='bomb',
            size=48,
        )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        # Close all open popups if ui changes.
        # check pr #390 for more info.
        for pup in open_popups:
            try:
                bui.containerwidget(edit=pup._root_widget, transition='out_scale')
            except:
                pass
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    def spin(self, show=False):
        w = self._loading_spinner
        p = self._root_widget
        bui.spinnerwidget(w, visible=show) if w.exists(
        ) and p.exists() and not p.transitioning_out else None

    @contextlib.contextmanager
    def exception_handler(self):
        try:
            yield
        except urllib.error.URLError:
            self.spin()
            try:
                bui.textwidget(
                    edit=self._plugin_manager_status_text,
                    text="Make sure you are connected\n to the Internet and try again."
                )
            except:
                pass
            self.plugin_manager._index_setup_in_progress = False
        except RuntimeError:
            # User probably went back before a bui.Window could finish loading.
            pass
        except Exception as e:
            self.spin()
            try:
                bui.textwidget(edit=self._plugin_manager_status_text, text=str(e))
            except:
                pass
            raise

    async def draw_index(self):
        self.draw_search_bar()
        self.draw_plugins_scroll_bar()
        self.draw_filter_button("All")
        self.draw_refresh_icon()
        self.draw_settings_icon()
        with self.exception_handler():
            await self.plugin_manager.setup_changelog()
            await self.plugin_manager.setup_index()
            self.spin()
            try:
                bui.textwidget(edit=self._plugin_manager_status_text, text="")
            except:
                pass
            await self.select_category("All")

    def draw_plugins_scroll_bar(self):
        scroll_size_x = self.scrollx = (515 if _uiscale() is babase.UIScale.SMALL else
                                        430 if _uiscale() is babase.UIScale.MEDIUM else 420)
        scroll_size_y = (245 if _uiscale() is babase.UIScale.SMALL else
                         265 if _uiscale() is babase.UIScale.MEDIUM else 335)
        scroll_pos_x = (70 if _uiscale() is babase.UIScale.SMALL else
                        50 if _uiscale() is babase.UIScale.MEDIUM else 70)
        scroll_pos_y = (100 if _uiscale() is babase.UIScale.SMALL else
                        35 if _uiscale() is babase.UIScale.MEDIUM else 40)
        self._scrollwidget = sw = bui.scrollwidget(
            parent=self._root_widget,
            size=(scroll_size_x, scroll_size_y),
            position=(scroll_pos_x, scroll_pos_y)
        )
        self._columnwidget = bui.columnwidget(
            parent=self._scrollwidget,
            border=2,
            margin=0
        )
        bui.widget(
            sw,
            left_widget=self._back_button,
            up_widget=self._filter_widget
        )
        bui.widget(
            self._filter_widget,
            down_widget=sw
        )

    def draw_filter_button(self, category):
        """One button that sums up the current view and opens PluginFilterWindow."""
        pos_x = (393 if _uiscale() is babase.UIScale.SMALL else
                 293 if _uiscale() is babase.UIScale.MEDIUM else 323)
        pos_y = self._height - (141 if _uiscale() is babase.UIScale.SMALL else
                                110 if _uiscale() is babase.UIScale.MEDIUM else 110)
        label = f"{category} | {SORT_OPTIONS[self.selected_sort][1]}"
        if self.show_incompatible:
            label += " | +Incompatible"

        if self.filter_button is None:
            self.filter_button = b = bui.buttonwidget(
                parent=self._root_widget,
                position=(pos_x, pos_y),
                size=(187, 30),
                label=label,
                button_type="square",
                textcolor=(0.8, 0.8, 0.85),
                text_scale=0.6,
                left_widget=self._filter_widget,
                down_widget=self._scrollwidget,
                up_widget=self._back_button
            )
            bui.buttonwidget(
                edit=b,
                on_activate_call=lambda: self.show_filter_window(source=b)
            )
        else:
            b = self.filter_button
            bui.buttonwidget(
                edit=b,
                label=label
            ) if b.exists() else None

    def draw_search_bar(self):
        search_bar_pos_x = (85 if _uiscale() is babase.UIScale.SMALL else
                            68 if _uiscale() is babase.UIScale.MEDIUM else 75)
        search_bar_pos_y = self._height - (
            145 if _uiscale() is babase.UIScale.SMALL else
            110 if _uiscale() is babase.UIScale.MEDIUM else 116)

        search_bar_size_x = (320 if _uiscale() is babase.UIScale.SMALL else
                             230 if _uiscale() is babase.UIScale.MEDIUM else 260)
        search_bar_size_y = (
            35 if _uiscale() is babase.UIScale.SMALL else
            35 if _uiscale() is babase.UIScale.MEDIUM else 45)

        filter_txt_pos_x = (60 if _uiscale() is babase.UIScale.SMALL else
                            40 if _uiscale() is babase.UIScale.MEDIUM else 50)
        filter_txt_pos_y = search_bar_pos_y + (3 if _uiscale() is babase.UIScale.SMALL else
                                               4 if _uiscale() is babase.UIScale.MEDIUM else 8)

        bui.textwidget(parent=self._root_widget,
                       text="Filter",
                       position=(filter_txt_pos_x, filter_txt_pos_y),
                       selectable=False,
                       h_align='left',
                       v_align='center',
                       color=bui.app.ui_v1.title_color,
                       scale=0.5)

        filter_txt = babase.Lstr(resource='filterText')
        search_bar_maxwidth = search_bar_size_x - (95 if _uiscale() is babase.UIScale.SMALL else
                                                   77 if _uiscale() is babase.UIScale.MEDIUM else
                                                   85)
        self._filter_widget = bui.textwidget(
            parent=self._root_widget,
            text="",
            size=(search_bar_size_x, search_bar_size_y),
            position=(search_bar_pos_x, search_bar_pos_y),
            h_align='left',
            v_align='center',
            editable=True,
            scale=0.8,
            autoselect=True,
            maxwidth=search_bar_maxwidth,
            description=filter_txt
        )
        self._last_filter_text = ""
        self._last_filter_plugins = []

        loop.create_task(self.process_search_term())

    async def process_search_term(self):
        while True:
            await asyncio.sleep(0.2)
            if not self._filter_widget:
                # Search filter widget got destroyed. No point checking for filter text anymore.
                return
            filter_text = bui.textwidget(parent=self._root_widget, query=self._filter_widget)
            if self.selected_category is None:
                continue
            try:
                await self.draw_plugin_names(self.selected_category, search_term=filter_text.lower())
            except CategoryDoesNotExist:
                pass

    def draw_settings_icon(self):
        settings_pos_x = (610 if _uiscale() is babase.UIScale.SMALL else
                          500 if _uiscale() is babase.UIScale.MEDIUM else 510)
        settings_pos_y = (130 if _uiscale() is babase.UIScale.SMALL else
                          60 if _uiscale() is babase.UIScale.MEDIUM else 70)
        controller_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(settings_pos_x, settings_pos_y),
            size=(30, 30),
            button_type="square",
            label="",
            left_widget=self._scrollwidget,
            right_widget=bui.get_special_widget('squad_button')
        )
        bui.buttonwidget(
            controller_button,
            on_activate_call=babase.CallPartial(
                PluginManagerSettingsWindow,
                self.plugin_manager,
                controller_button
            )
        )
        bui.imagewidget(
            parent=self._root_widget,
            position=(settings_pos_x, settings_pos_y),
            size=(30, 30),
            color=(0.8, 0.95, 1),
            texture=bui.gettexture("settingsIcon"),
            draw_controller=controller_button
        )

    def draw_refresh_icon(self):
        refresh_pos_x = (610 if _uiscale() is babase.UIScale.SMALL else
                         500 if _uiscale() is babase.UIScale.MEDIUM else 510)
        refresh_pos_y = (180 if _uiscale() is babase.UIScale.SMALL else
                         108 if _uiscale() is babase.UIScale.MEDIUM else 120)

        controller_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(refresh_pos_x, refresh_pos_y),
            size=(30, 30),
            button_type="square",
            label="",
            on_activate_call=lambda: (
                bui.getsound('deek').play() or
                loop.create_task(self.refresh())
            ),
            enable_sound=False,
            left_widget=self._scrollwidget,
            right_widget=bui.get_special_widget('squad_button')
        )
        bui.widget(
            self._scrollwidget,
            right_widget=controller_button
        )
        bui.imagewidget(
            parent=self._root_widget,
            position=(refresh_pos_x, refresh_pos_y),
            size=(30, 30),
            color=(0.8, 0.95, 1),
            texture=bui.gettexture("replayIcon"),
            draw_controller=controller_button
        )

    def search_term_filterer(self, plugin, search_term):
        # This helps resolve "plugin name" to "plugin_name".
        if search_term in plugin.info["description"].lower():
            return True
        search_term = search_term.replace(" ", "_")
        if search_term in plugin.name:
            return True
        for author in plugin.info["authors"]:
            if search_term in author["name"].lower():
                return True
        return False

    # XXX: Not sure if this is the best way to handle search filters.
    async def draw_plugin_names(self, category, search_term="", refresh=False):
        # Re-draw plugin list UI if either search term or category was switched.
        to_draw_plugin_names = (search_term, category) != (self._last_filter_text,
                                                           self.selected_category)
        if not (to_draw_plugin_names or refresh):
            return

        # Filter & Sort stays open and each click starts another draw, as do
        # search keystrokes, so several can be in flight at once. Each one
        # bails out after an await if a newer one has started, rather than
        # both clearing and filling the list.
        self._draw_generation += 1
        generation = self._draw_generation

        def superseded():
            return generation != self._draw_generation

        try:
            if self.plugin_manager.categories != {}:
                if self.plugin_manager.categories['All'] is not None:
                    category_plugins = await self.plugin_manager.categories[category if category != 'Installed' else 'All'].get_plugins()
                    if superseded():
                        return
                else:
                    return
            else:
                return
        except (KeyError, AttributeError):
            no_internet_text = "Make sure you are connected\n to the Internet and try again."
            if bui.textwidget(query=self._plugin_manager_status_text) != no_internet_text:
                raise CategoryDoesNotExist(f"{category} does not exist.")
            else:
                return

        if search_term:
            plugins = list(filter(
                lambda plugin: self.search_term_filterer(plugin, search_term),
                category_plugins,
            ))
        else:
            plugins = category_plugins

        # Returns a new list, leaving the category's own one in its original order.
        plugins = _sort_plugins(plugins, self.selected_sort)

        if plugins == self._last_filter_plugins and not refresh:
            # Plugins names to draw on UI are already drawn.
            return

        self._last_filter_text = search_term
        self._last_filter_plugins = plugins

        if not self._columnwidget.exists():
            return

        if category == 'Installed':
            plugin_names_to_draw = tuple(
                plugin for plugin in plugins if plugin.is_installed
            )
        else:
            plugin_names_to_draw = plugins

        for plugin in self._columnwidget.get_children():
            plugin.delete()
        text_widget = bui.textwidget(parent=self._columnwidget)
        text_widget.delete()
        # await asyncio.gather(*plugin_names_to_draw)

        # A plugin with no versions at all (possible in a custom source) has
        # nothing to show or install, so it stays hidden either way.
        plugin_names_ready_to_draw = [
            plugin for plugin in plugin_names_to_draw
            if plugin.is_compatible or (self.show_incompatible and plugin.info["versions"])
        ]

        for i, plugin in enumerate(plugin_names_ready_to_draw):
            await self.draw_plugin_name(plugin, plugin_names_ready_to_draw, generation)
            if superseded():
                return
        kids = self._columnwidget.get_children()
        if kids:
            bui.widget(kids[0], up_widget=self._filter_widget)
            bui.widget(kids[-1], down_widget=self._back_button)

    async def draw_plugin_name(self, plugin, plugins_list, generation=None):
        """Draw or recolor one row. `generation` is draw_plugin_names()' own,
        so a row from a superseded list draw isn't added after the newer one
        has cleared the list."""
        if not plugin.is_compatible:
            color = (0.6, 0.35, 0.35)
        elif plugin.is_installed:
            local_plugin = plugin.get_local()
            if await local_plugin.is_enabled():
                if not local_plugin.is_installed_via_plugin_manager:
                    color = (0.8, 0.2, 0.2)
                elif local_plugin.version == plugin.latest_compatible_version.number:
                    color = (0, 0.95, 0.2)
                else:
                    color = (1, 0.6, 0)
            else:
                color = (1, 1, 1)
            if generation is not None and generation != self._draw_generation:
                return
        else:
            color = (0.5, 0.5, 0.5)

        plugin_name_widget_to_update = self.plugins_in_current_view.get(plugin.name)
        if plugin_name_widget_to_update:
            bui.textwidget(
                edit=plugin_name_widget_to_update,
                color=color
            )
        else:
            text_widget = bui.textwidget(
                parent=self._columnwidget,
                size=(self.scrollx, 30),
                selectable=True,
                always_highlight=True,
                color=color,
                text=plugin.name.replace('_', ' ').title() + (
                    f" ({plugin.incompatibility_reason})" if not plugin.is_compatible else ""
                ),
                click_activate=True,
                h_align='left',
                v_align='center',
                maxwidth=self.scrollx-10
            )
            bui.textwidget(
                text_widget,
                on_activate_call=bui.CallPartial(
                    self.show_plugin_window,
                    plugin,
                    plugins_list,
                    text_widget
                )
            )
            self.plugins_in_current_view[plugin.name] = text_widget
            # XXX: This seems nicer. Might wanna use this in future.
            # text_widget.add_delete_callback(lambda: self.plugins_in_current_view.pop(plugin.name))

    def show_plugin_window(self, plugin, plugins_list, source):
        PluginWindow(
            plugin,
            source,
            plugins_list=plugins_list,
            button_callback=lambda: self.draw_plugin_name(plugin, plugins_list)
        )

    def show_filter_window(self, source):
        PluginFilterWindow(
            self.plugin_manager.categories.keys(),
            self.selected_category,
            self.selected_sort,
            self.show_incompatible,
            source,
            self.apply_filter,
        )

    async def apply_filter(self, category, sort, show_incompatible):
        self.selected_sort = sort
        self.show_incompatible = show_incompatible
        await self.select_category(category)

    async def select_category(self, category):
        self.plugins_in_current_view.clear()
        self.draw_filter_button(category)
        # Set before drawing: if another selection starts while this one is
        # still drawing, the newest choice must be the one that sticks.
        self.selected_category = category
        await self.draw_plugin_names(category, search_term=self._last_filter_text, refresh=True)

    def cleanup(self):
        self.plugin_manager.cleanup()
        for plugin in self._columnwidget.get_children():
            plugin.delete()
        self.plugins_in_current_view.clear()
        self._last_filter_text = ""
        self._last_filter_plugins = []

    async def refresh(self):
        self.cleanup()
        # try:
        #     bui.textwidget(edit=self._plugin_manager_status_text, text="Refreshing")
        # except:
        #     pass

        self.spin(True)

        with self.exception_handler():
            await self.plugin_manager.refresh()
            await self.plugin_manager.setup_changelog()
            await self.plugin_manager.setup_index()
            self.spin()
            try:
                bui.textwidget(edit=self._plugin_manager_status_text, text="")
            except:
                pass
            await self.select_category(self.selected_category)

    def soft_refresh(self):
        pass


class PluginManagerSettingsWindow(popup.PopupWindow):
    def __init__(self, plugin_manager, origin_widget):
        self._plugin_manager = plugin_manager
        self.scale_origin = origin_widget.get_screen_space_center()
        self.settings = babase.app.config["Community Plugin Manager"]["Settings"].copy()
        self._update_button = None
        loop.create_task(self.draw_ui())

    async def draw_ui(self):
        b_text_color = (0.8, 0.8, 0.85)
        s = 1.25 if _uiscale() is babase.UIScale.SMALL else 1.27 if _uiscale() is babase.UIScale.MEDIUM else 1.3
        width = 380 * s
        height = 150 + 150 * s
        # A band above the button row for the title, so the centred Custom
        # Sources button doesn't sit on it. Everything else is laid out from
        # `height` as before and keeps its distance from the bottom.
        title_band = 30
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
        self._root_widget = bui.containerwidget(
            size=(width, height + title_band),
            on_outside_click_call=self._ok,
            transition=transition,
            scale=(2.1 if _uiscale() is babase.UIScale.SMALL else 1.5
                   if _uiscale() is babase.UIScale.MEDIUM else 1.0),
            scale_origin_stack_offset=self.scale_origin
        )
        _add_popup(self)
        pos = height * 0.9
        setting_title = "Settings"
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.49, pos + title_band),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=setting_title,
            scale=text_scale,
            color=bui.app.ui_v1.title_color,
            maxwidth=width * 0.9
        )

        pos -= 20
        self._changelog_button = b = bui.buttonwidget(
            parent=self._root_widget,
            position=((width * 0.2) - button_size[0] / 2 - 5, pos),
            size=(80, 30),
            textcolor=b_text_color,
            button_type='square',
            label=''
        )
        bui.buttonwidget(b, on_activate_call=lambda: ChangelogWindow(b))
        bui.textwidget(
            parent=self._root_widget,
            position=((width * 0.2) - button_size[0] / 2, pos),
            size=(70, 30),
            scale=0.6,
            h_align='center',
            v_align='center',
            text='ChangeLog',
            color=b_text_color,
            draw_controller=self._changelog_button,
        )
        # Opened on top of this window, like the changelog, so unsaved
        # setting toggles survive a trip to the sources list.
        # On one line the label is ~108 wide at 0.6, more than the button, so
        # it's wrapped onto two lines at 0.5 (~45 x 32). The button is 6
        # taller than ChangeLog to fit them and stays centred on the same row.
        self._sources_button = bui.buttonwidget(
            parent=self._root_widget,
            position=((width * 0.5) - 45, pos - 3),
            size=(90, 36),
            textcolor=b_text_color,
            button_type='square',
            label='',
            on_activate_call=lambda: PluginCustomSourcesWindow(self._sources_button)
        )
        bui.textwidget(
            parent=self._root_widget,
            position=((width * 0.5) - 40, pos - 3),
            size=(80, 36),
            scale=0.5,
            h_align='center',
            v_align='center',
            text='Custom\nSources',
            color=b_text_color,
            maxwidth=80,
            draw_controller=self._sources_button,
        )
        self._save_button = bui.buttonwidget(
            parent=self._root_widget,
            position=((width * 0.82) - button_size[0] / 2, pos),
            size=(73, 35),
            on_activate_call=self.save_settings_button,
            textcolor=b_text_color,
            button_type='square',
            text_scale=1,
            scale=0,
            selectable=False,
            label="Save"
        )
        pos -= 40

        self.checkboxes = []
        for setting, value in self.settings.items():
            chk = bui.checkboxwidget(
                parent=self._root_widget,
                position=(width * 0.1, pos),
                size=(170, 30),
                text=setting,
                value=value,
                on_value_change_call=babase.CallPartial(self.toggle_setting, setting),
                maxwidth=500,
                textcolor=(0.9, 0.9, 0.9),
                scale=text_scale * 0.8
            )
            self.checkboxes.append(chk)
            pos -= 34 * text_scale
        bui.widget(
            self.checkboxes[0],
            up_widget=self._changelog_button
        )
        bui.widget(
            self._sources_button,
            down_widget=self.checkboxes[0]
        )
        bui.widget(
            self._changelog_button,
            down_widget=self.checkboxes[0]
        )
        self._update_top_row_navigation()

        pos = height - 200
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.49, pos-5),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text='Contribute to plugins or to this community plugin manager!',
            scale=text_scale * 0.65,
            color=color,
            maxwidth=width * 0.95
        )

        pos -= 75
        try:
            plugin_manager_update_available = await self._plugin_manager.get_update_details()
        except urllib.error.URLError:
            plugin_manager_update_available = False
        discord_width = (width * 0.20) if plugin_manager_update_available else (width * 0.31)
        self.discord_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(discord_width - button_size[0] / 2, pos),
            size=button_size,
            on_activate_call=lambda: bui.open_url(DISCORD_URL),
            textcolor=b_text_color,
            color=discord_bg_color,
            button_type='square',
            text_scale=1,
            label="",
            down_widget=self._changelog_button
        )
        bui.widget(
            self._changelog_button,
            up_widget=self.discord_button
        )

        bui.imagewidget(
            parent=self._root_widget,
            position=(discord_width+0.5 - button_size[0] / 2, pos),
            size=button_size,
            texture=bui.gettexture("discordLogo"),
            color=discord_fg_color,
            draw_controller=self.discord_button
        )

        github_width = (width * 0.49) if plugin_manager_update_available else (width * 0.65)
        self.github_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(github_width - button_size[0] / 2, pos),
            size=button_size,
            on_activate_call=lambda: bui.open_url(REPOSITORY_URL),
            textcolor=b_text_color,
            color=github_bg_color,
            button_type='square',
            text_scale=1,
            label='',
            up_widget=self.checkboxes[-1],
            down_widget=self._changelog_button
        )

        bui.imagewidget(
            parent=self._root_widget,
            position=(github_width + 0.5 - button_size[0] / 2, pos),
            size=button_size,
            texture=bui.gettexture("githubLogo"),
            color=(1, 1, 1),
            draw_controller=self.github_button
        )

        bui.containerwidget(edit=self._root_widget, on_cancel_call=self._ok)

        try:
            plugin_manager_update_available = await self._plugin_manager.get_update_details()
        except urllib.error.URLError:
            plugin_manager_update_available = False
        if plugin_manager_update_available:
            text_color = (0.75, 0.2, 0.2)
            button_size = (95 * s, 32 * s)
            update_button_label = f'Update to v{plugin_manager_update_available[0]}'
            self._update_button = bui.buttonwidget(
                parent=self._root_widget,
                position=((width * 0.77) - button_size[0] / 2, pos),
                size=button_size,
                on_activate_call=lambda: loop.create_task(
                    self.update(*plugin_manager_update_available)),
                textcolor=b_text_color,
                button_type='square',
                text_scale=1,
                color=(0, 0.7, 0),
                label=update_button_label,
                up_widget=self.checkboxes[-1],
                down_widget=self._changelog_button,
                right_widget=self.discord_button
            )
            bui.widget(
                self.discord_button,
                left_widget=self._update_button
            )
            self._restart_to_reload_changes_text = bui.textwidget(
                parent=self._root_widget,
                position=(width * 0.79, pos + 20),
                size=(0, 0),
                h_align='center',
                v_align='center',
                text='',
                scale=text_scale * 0.65,
                color=(0, 0.8, 0),
                maxwidth=width * 0.9
            )
        else:
            text_color = (0, 0.8, 0)
        pos -= 25
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.49, pos),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=f'Plugin Manager v{PLUGIN_MANAGER_VERSION}',
            scale=text_scale * 0.8,
            color=text_color,
            maxwidth=width * 0.9
        )
        pos -= 25
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.49, pos),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=f'API Version: {_app_api_version}',
            scale=text_scale * 0.7,
            color=(0.4, 0.8, 1),
            maxwidth=width * 0.95
        )

        pos = height * 0.1

    def toggle_setting(self, setting, set_value):
        self.settings[setting] = set_value
        check = self.settings == babase.app.config["Community Plugin Manager"]["Settings"]
        bui.buttonwidget(
            edit=self._save_button,
            scale=0 if check else 1,
            selectable=(not check)
        )
        self._update_top_row_navigation(save_visible=not check)
        # Only drawn when an update is available, and deleted once it's applied.
        if self._update_button is not None and self._update_button.exists():
            bui.widget(
                self._update_button,
                up_widget=(
                    check and self.checkboxes[0]
                    or self._save_button
                ),
                down_widget=(
                    check and self._changelog_button
                    or self._save_button
                )
            )

    def _update_top_row_navigation(self, save_visible=False):
        # Left/right wrap around ChangeLog, Custom Sources and, while there are
        # unsaved changes, the Save button (hidden at scale 0 otherwise).
        last = self._save_button if save_visible else self._sources_button
        bui.widget(self._changelog_button, right_widget=self._sources_button, left_widget=last)
        bui.widget(self._sources_button, left_widget=self._changelog_button,
                   right_widget=self._save_button if save_visible else self._changelog_button)
        if save_visible:
            bui.widget(self._save_button, left_widget=self._sources_button,
                       right_widget=self._changelog_button)

    def save_settings_button(self):
        babase.app.config["Community Plugin Manager"]["Settings"] = self.settings.copy()
        babase.app.config.commit()
        self._ok()
        bui.getsound('gunCocking').play()

    async def update(self, to_version=None, commit_sha=None):
        try:
            await self._plugin_manager.update(to_version, commit_sha)
            await self._plugin_manager.setup_changelog()
        except MD5CheckSumFailed:
            bui.screenmessage("MD5 checksum failed during plugin manager update", color=(1, 0, 0))
            bui.getsound('error').play()
        else:
            bui.screenmessage("Plugin manager update successful", color=(0, 1, 0))
            bui.getsound('shieldUp').play()
            bui.textwidget(
                edit=self._restart_to_reload_changes_text,
                text='Update Applied!\nRestart game to reload changes.'
            )
            self._update_button.delete()

    def _ok(self) -> None:
        bui.getsound('swish').play()
        _remove_popup(self)
        bui.containerwidget(edit=self._root_widget, transition='out_scale')


_PLUGMAN_ACTION = "plugin_manager"


if settingsdocui is not None:
    class PlugmanSettingsController(_StockSettingsController):
        """The settings page with a Plugin Manager button appended."""

        @override
        def fulfill_route(self, route):
            response = super().fulfill_route(route)
            # The stock page is a single ButtonRow sized for exactly four
            # buttons; it scrolls once a fifth overflows it (SCROLL layout).
            row = response.page.rows[0]
            if _uiscale() is not babase.UIScale.SMALL:
                # The wider window fits all five except at medium scale on a
                # 16:9 screen, where FIXED shrinks them a hair rather than
                # scrolling. Builds predating FIXED fall back to SCROLL.
                row.layout = dui2.ButtonRowLayout.FIXED

            # Clone a stock button so size, scale and decoration placement
            # match, then swap in our icon, label and action.
            template = row.buttons[-1]
            icon, label = template.decorations
            row.buttons.append(
                replace(
                    template,
                    widget_id=_PLUGMAN_ACTION,
                    selected=False,
                    action=dui2.Local(immediate_local_action=_PLUGMAN_ACTION),
                    decorations=[
                        replace(icon, texture=bui._classicassets.textures.store_icon),
                        replace(label, text=LangStrSpecValue.literal("Plugin Manager")),
                    ],
                )
            )
            return response

        # Our action isn't in the settings page's typed action family, so it's
        # handled here before the typed decoding, which would reject it.
        @override
        def get_local_action_press_sound(self, name):
            if name == _PLUGMAN_ACTION:
                return PressSound.SWISH
            return super().get_local_action_press_sound(name)

        @override
        def local_action(self, action):
            if action.name != _PLUGMAN_ACTION:
                return super().local_action(action)
            window = action.window
            if not window.main_window_has_control():
                return
            window.main_window_replace(
                lambda: PluginManagerWindow(origin_widget=action.widget)
            )

elif AllSettingsWindow is not None:
    class NewAllSettingsWindow(AllSettingsWindow):
        @override
        def main_window_should_preserve_selection(self) -> bool:
            return False

        """Window for selecting a settings category."""

        def __init__(
            self,
            transition: str | None = 'in_right',
            origin_widget: bui.Widget | None = None,
        ):
            # pylint: disable=too-many-statements
            # pylint: disable=too-many-locals
            assert bui.app.classic is not None
            uiscale = bui.app.ui_v1.uiscale
            width = 1000 if uiscale is bui.UIScale.SMALL else 800
            x_inset = 125 if uiscale is bui.UIScale.SMALL else 105
            height = 490
            top_extra = 20 if uiscale is bui.UIScale.SMALL else 0
            self._plugman_button = None

            super().__init__(transition, origin_widget)

            for child in self._root_widget.get_children():
                child.delete()

            bui.containerwidget(
                edit=self._root_widget, size=(width, height + top_extra)
            )

            if uiscale is bui.UIScale.SMALL:
                self._back_button = None
                bui.containerwidget(
                    edit=self._root_widget, on_cancel_call=self.main_window_back
                )
            else:
                self._back_button = btn = bui.buttonwidget(
                    parent=self._root_widget,
                    autoselect=True,
                    position=(x_inset - 20, height - 85),
                    size=(130, 60),
                    scale=0.8,
                    text_scale=1.2,
                    label=bui.Lstr(resource='backText'),
                    button_type='back',
                    on_activate_call=self.main_window_back,
                )
                bui.containerwidget(edit=self._root_widget, cancel_button=btn)

            bui.textwidget(
                parent=self._root_widget,
                position=(0, height - 80),
                size=(width, 25),
                text=bui.Lstr(resource=f'{self._r}.titleText'),
                color=bui.app.ui_v1.title_color,
                h_align='center',
                v_align='center',
                maxwidth=130,
            )

            if self._back_button is not None:
                bui.buttonwidget(
                    edit=self._back_button,
                    button_type='backSmall',
                    size=(60, 60),
                    label=_charstr(bui.SpecialChar.BACK),
                )

            v = height - 265
            basew = 280 if uiscale is bui.UIScale.SMALL else 230
            baseh = 170
            x_offs = (
                x_inset + (105 if uiscale is bui.UIScale.SMALL else 72) - basew
            )  # now unused
            x_dif = (basew - 7) / 2
            x_offs2 = x_offs + basew - 7
            x_offs3 = x_offs + 2 * (basew - 7)
            x_offs4 = x_offs + 3 * (basew - 7)
            x_offs5 = x_offs2
            x_offs6 = x_offs3
            x_offs2 -= x_dif
            x_offs3 -= x_dif
            x_offs4 -= x_dif

            def _b_title(
                x: float, y: float, button: bui.Widget, text: str | bui.Lstr
            ) -> None:
                bui.textwidget(
                    parent=self._root_widget,
                    text=text,
                    position=(x + basew * 0.47, y + baseh * 0.22),
                    maxwidth=basew * 0.7,
                    size=(0, 0),
                    h_align='center',
                    v_align='center',
                    draw_controller=button,
                    color=(0.7, 0.9, 0.7, 1.0),
                )

            ctb = self._controllers_button = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(x_offs2, v),
                size=(basew, baseh),
                button_type='square',
                label='',
                on_activate_call=self._do_controllers,
            )
            if self._back_button is None:
                bbtn = bui.get_special_widget('back_button')
                bui.widget(edit=ctb, left_widget=bbtn)
            _b_title(
                x_offs2, v, ctb, bui.Lstr(resource=f'{self._r}.controllersText')
            )
            imgw = imgh = 130
            bui.imagewidget(
                parent=self._root_widget,
                position=(x_offs2 + basew * 0.49 - imgw * 0.5, v + 35),
                size=(imgw, imgh),
                texture=bui.gettexture('controllerIcon'),
                draw_controller=ctb,
            )

            gfxb = self._graphics_button = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(x_offs3, v),
                size=(basew, baseh),
                button_type='square',
                label='',
                on_activate_call=self._do_graphics,
            )
            pbtn = bui.get_special_widget('squad_button')
            bui.widget(edit=gfxb, up_widget=pbtn, right_widget=pbtn)
            _b_title(x_offs3, v, gfxb, bui.Lstr(resource=f'{self._r}.graphicsText'))
            imgw = imgh = 110
            bui.imagewidget(
                parent=self._root_widget,
                position=(x_offs3 + basew * 0.49 - imgw * 0.5, v + 42),
                size=(imgw, imgh),
                texture=bui.gettexture('graphicsIcon'),
                draw_controller=gfxb,
            )

            abtn = self._audio_button = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(x_offs4, v),
                size=(basew, baseh),
                button_type='square',
                up_widget=pbtn,
                right_widget=pbtn,
                label='',
                on_activate_call=self._do_audio,
            )
            bui.buttonwidget(gfxb, right_widget=abtn)
            _b_title(x_offs4, v, abtn, bui.Lstr(resource=f'{self._r}.audioText'))
            imgw = imgh = 120
            bui.imagewidget(
                parent=self._root_widget,
                position=(x_offs4 + basew * 0.49 - imgw * 0.5 + 5, v + 35),
                size=(imgw, imgh),
                color=(1, 1, 0),
                texture=bui.gettexture('audioIcon'),
                draw_controller=abtn,
            )

            v -= baseh - 5

            avb = self._advanced_button = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(x_offs5, v),
                size=(basew, baseh),
                button_type='square',
                label='',
                on_activate_call=self._do_advanced,
            )
            _b_title(x_offs5, v, avb, bui.Lstr(resource=f'{self._r}.advancedText'))
            imgw = imgh = 120
            bui.imagewidget(
                parent=self._root_widget,
                position=(x_offs5 + basew * 0.49 - imgw * 0.5 + 5, v + 35),
                size=(imgw, imgh),
                color=(0.8, 0.95, 1),
                texture=bui.gettexture('advancedIcon'),
                draw_controller=avb,
            )

            self._plugman_button = pmb = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(x_offs6, v),
                size=(basew, baseh),
                button_type='square',
                label='',
                up_widget=abtn,
                on_activate_call=self._do_plugman
            )
            _b_title(x_offs6, v, pmb, bui.Lstr(value="Plugin Manager"))
            imgw = imgh = 120
            bui.imagewidget(
                parent=self._root_widget,
                position=(x_offs6 + basew * 0.49 - imgw * 0.5 + 5, v + 35),
                size=(imgw, imgh),
                color=(0.8, 0.95, 1),
                texture=bui.gettexture('storeIcon'),
                draw_controller=pmb
            )
            self._restore_state()

        def _do_plugman(self) -> None:
            # no-op if we're not in control.
            if not self.main_window_has_control():
                return

            self.main_window_replace(
                lambda: PluginManagerWindow(
                    origin_widget=self._plugman_button
                )
            )

        def _save_state(self) -> None:
            try:
                sel = self._root_widget.get_selected_child()
                if sel == self._controllers_button:
                    sel_name = 'Controllers'
                elif sel == self._graphics_button:
                    sel_name = 'Graphics'
                elif sel == self._audio_button:
                    sel_name = 'Audio'
                elif sel == self._advanced_button:
                    sel_name = 'Advanced'
                elif sel == self._plugman_button:
                    sel_name = 'PlugMan'
                elif sel == self._back_button:
                    sel_name = 'Back'
                else:
                    raise ValueError(f'unrecognized selection \'{sel}\'')
                assert bui.app.classic is not None
                bui.app.ui_v1.window_states[type(self)] = {'sel_name': sel_name}
            except Exception:
                logger.exception('Error saving state for %s.', self)

        def _restore_state(self) -> None:
            try:
                assert bui.app.classic is not None
                sel_name = bui.app.ui_v1.window_states.get(type(self), {}).get(
                    'sel_name'
                )
                sel: bui.Widget | None
                if sel_name == 'Controllers':
                    sel = self._controllers_button
                elif sel_name == 'Graphics':
                    sel = self._graphics_button
                elif sel_name == 'Audio':
                    sel = self._audio_button
                elif sel_name == 'Advanced':
                    sel = self._advanced_button
                elif sel_name == "PlugMan":
                    sel = self._plugman_button
                elif sel_name == 'Back':
                    sel = self._back_button
                else:
                    sel = self._controllers_button
                if sel is not None:
                    bui.containerwidget(edit=self._root_widget, selected_child=sel)
            except Exception:
                logger.exception('Error restoring state for %s.', self)


def _settings_window_layout(cls):
    # WIDER keeps WIDE's height but follows the screen's width at
    # medium/large scale; at small scale it's identical to WIDE.
    return dui2.WindowLayout.WIDER


def _settings_width_fraction(stock):
    """WIDER_SCREEN_WIDTH_FRACTION giving the settings window just the width
    its button row needs (never more than the stock fraction)."""
    uiscale = bui.app.ui_v1.uiscale
    if uiscale is babase.UIScale.SMALL:
        # WIDER ignores the fraction there; windows fill the screen.
        return stock
    layout = dui2.WindowLayout.WIDER
    # Inverse of layout_geometry()'s WIDER width (fraction * screen width /
    # root scale) and of window framing's page width (width - side insets
    # + scroll overhang).
    needed = (_SETTINGS_ROW_WIDTH + docui_layout.window_insets(layout)[0]
              - docui_layout.window_scroll_overhang(layout))
    screen_width = bui.get_virtual_screen_size()[0]
    return min(stock, needed * docui_layout.root_scale(uiscale) / screen_width)


def _wrap_window_init(func):
    # WIDER windows take 85% of the screen width, far more than the
    # settings row needs at large scale. layout_geometry() reads that
    # fraction from its module on every call, so lower it while the
    # settings window is built. That's done here rather than in
    # create_window because back navigation and resizes rebuild windows
    # straight through __init__.
    def wrapper(self, controller, *args, **kwargs):
        if not isinstance(controller, PlugmanSettingsController):
            return func(self, controller, *args, **kwargs)
        stock = docui_layout.WIDER_SCREEN_WIDTH_FRACTION
        try:
            fraction = _settings_width_fraction(stock)
        except Exception:
            # The engine reshuffled its layout helpers; a too-wide
            # window beats no settings window.
            logger.exception("Couldn't size the settings window; using the stock width.")
            fraction = stock
        docui_layout.WIDER_SCREEN_WIDTH_FRACTION = fraction
        try:
            return func(self, controller, *args, **kwargs)
        finally:
            docui_layout.WIDER_SCREEN_WIDTH_FRACTION = stock
    return wrapper


def _install_settings_patches():
    if settingsdocui is None:
        if AllSettingsWindow is None:
            logger.warning("No settings window this build supports;"
                           " the Plugin Manager button won't appear in settings.")
            return
        from bauiv1lib.settings import allsettings
        allsettings.AllSettingsWindow = NewAllSettingsWindow
        return
    # The game imports AllSettingsController by name when the settings
    # button is pressed, so rebinding it here is enough.
    settingsdocui.AllSettingsController = PlugmanSettingsController
    settingsdocui.SettingsRoute.get_window_layout = classmethod(_settings_window_layout)
    docui_window.DocUIWindow.__init__ = _wrap_window_init(docui_window.DocUIWindow.__init__)


# ba_meta export babase.Plugin
class EntryPoint(babase.Plugin):
    def on_app_running(self) -> None:
        """Called when the app is being launched."""
        # Self-update first, so nothing optional below can keep the
        # plugin manager from fetching a release that fixes it. The DNS
        # workaround is plain Python and has to be in place before the
        # first request.
        DNSBlockWorkaround.apply()
        loop.create_task(StartupTasks().execute())

        # Then the optional pieces, each on its own so one breaking (an
        # engine change, say) costs only that piece.
        try:
            babase.app.add_shutdown_task(_shutdown_network_pool())
        except Exception:
            logger.exception("Failed to register the network pool shutdown.")
        try:
            _install_settings_patches()
        except Exception:
            logger.exception("Failed to patch the settings window.")
