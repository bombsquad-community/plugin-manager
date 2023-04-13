# Released under the MIT License. See LICENSE for details.
#
"""placeholder :clown:"""

# ba_meta require api 7

from __future__ import annotations
from urllib.request import Request, urlopen, urlretrieve
from pathlib import Path

#installing pypresence
def get_module():
    import os
    import zipfile
    install_path = Path(f"{os.getcwd()}/ba_data/python")
    path = Path(f"{install_path}/pypresence.zip")
    if not os.path.exists(Path(f"{install_path}/pypresence")):
        url = "https://github.com/brostosjoined/BombsquadRPC/releases/download/presence-1.0/pypresence.zip"
        filename, headers = urlretrieve(url, filename = path)
        with zipfile.ZipFile(path) as f:
            f.extractall(install_path)
        os.remove(path)
get_module()

import asyncio
import ast
import uuid
import json
import pypresence
import time
import threading
import ba
import _ba


from pypresence.utils import get_event_loop
from codecs import encode

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Tuple

DEBUG = True


def print_error(err: str, include_exception: bool = False) -> None:
    if DEBUG:
        if include_exception:
            ba.print_exception(err)
        else:
            ba.print_error(err)
    else:
        print(f"ERROR in discordrp.py: {err}")


def log(msg: str) -> None:
    if DEBUG:
        print(f"LOG in discordrp.py: {msg}")


def _run_overrides() -> None:
    old_init = ba.Activity.__init__

    def new_init(self, *args: Any, **kwargs: Any) -> None:  # type: ignore
        old_init(self, *args, **kwargs)
        self._discordrp_start_time = time.mktime(time.localtime())

    ba.Activity.__init__ = new_init  # type: ignore

    old_connect = _ba.connect_to_party

    def new_connect(*args, **kwargs) -> None:  # type: ignore
        global _last_server_addr
        global _last_server_port
        old_connect(*args, **kwargs)
        c = kwargs.get("address") or args[0]
        _last_server_port = kwargs.get("port") or args[1]

    _ba.connect_to_party = ba.internal.connect_to_party = new_connect

start_time = time.time()
class RpcThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.rpc = pypresence.Presence(963434684669382696)
        self.state: str | None = "In Game"
        self.details: str | None = "Main Menu"
        self.start_timestamp = time.mktime(time.localtime())
        self.large_image_key: str | None = "bombsquadicon"
        self.large_image_text: str | None = "BombSquad Icon"
        self.small_image_key: str | None = None
        self.small_image_text: str | None = None
        self.party_id: str = str(uuid.uuid4())
        self.party_size = 1
        self.party_max = 8
        self.join_secret: str | None = None
        self._last_update_time : float = 0
        self._last_secret_update_time: float = 0
        self._last_connect_time: float = 0
        self.should_close = False

    def _generate_join_secret(self):
        # resp = requests.get('https://legacy.ballistica.net/bsAccessCheck').text
        connection_info = _ba.get_connection_to_host_info()
        if connection_info:
            addr = _last_server_addr
            port = _last_server_port
        else:
            with urlopen(
                "https://legacy.ballistica.net/bsAccessCheck"
            ) as resp:
                resp = resp.read().decode()
            resp = ast.literal_eval(resp)
            addr = resp["address"]
            port = 43210
        secret_dict = {
            "format_version": 1,
            "hostname": addr,
            "port": port,
        }
        self.join_secret = json.dumps(secret_dict)

    def _update_secret(self):
        threading.Thread(target=self._generate_join_secret, daemon=True).start()
        self._last_secret_update_time = time.time()

    def run(self) -> None:
        asyncio.set_event_loop(get_event_loop())
        while not self.should_close:
            if time.time() - self._last_update_time > 0.1:
                self._update_presence()
            if time.time() - self._last_secret_update_time > 15:
                self._update_secret()
            # if time.time() - self._last_connect_time > 120: #!Eric please add module manager(pip)
            #     for proc in psutil.process_iter():
            #         match proc.name().lower():
            #             case "discord" | "discord.exe" | "discord.app":
            #                 self._reconnect()
            time.sleep(0.03)

    def _subscribe(self, event: str, **args):
        self.rpc.send_data(
            1,
            {
                "nonce": f"{time.time():.20f}",
                "cmd": "SUBSCRIBE",
                "evt": event,
                "args": args,
            },
        )
        data = self.rpc.loop.run_until_complete(self.rpc.read_output())
        self.handle_event(data)

    def _subscribe_events(self):
        self._subscribe("ACTIVITY_JOIN")
        self._subscribe("ACTIVITY_JOIN_REQUEST")

    def _update_presence(self) -> None:
        self._last_update_time = time.time()
        try:
            self._do_update_presence()
        except Exception:
            try:
                self._reconnect()
            except Exception:
                print_error("failed to update presence", include_exception=True)

    def _reconnect(self) -> None:
        self.rpc.connect()
        self._subscribe_events()
        self._do_update_presence()
        self._last_connect_time = time.time()

    def _do_update_presence(self) -> None:
        data = self.rpc.update(
            state=self.state or "  ",
            details=self.details,
            start=start_time,
            large_image=self.large_image_key,
            large_text=self.large_image_text,
            small_image=self.small_image_key,
            small_text=self.small_image_text,
            party_id=self.party_id,
            party_size=[self.party_size, self.party_max],
            join=self.join_secret,
            # buttons = [ #!cant use buttons together with join
            #     {
            #         "label": "Discord Server", 
            #         "url": "https://ballistica.net/discord"
            #     },
            #     {
            #         "label": "Download Bombsquad",
            #         "url": "https://bombsquad.ga/download"}
            # ]
        )

        self.handle_event(data)

    def handle_event(self, data):
        evt = data["evt"]
        if evt is None:
            return

        data = data.get("data", {})

        if evt == "ACTIVITY_JOIN":
            secret = data.get("secret")
            try:
                server = json.loads(secret)
                format_version = server["format_version"]
            except Exception:
                ba.print_exception("discordrp: unknown activity join format")
            else:
                try:
                    if format_version == 1:
                        hostname = server["hostname"]
                        port = server["port"]
                        self._connect_to_party(hostname, port)
                except Exception:
                    ba.print_exception(
                        f"discordrp: incorrect activity join data, {format_version=}"
                    )

        elif evt == "ACTIVITY_JOIN_REQUEST":
            user = data.get("user", {})
            uid = user.get("id")
            username = user.get("username")
            discriminator = user.get("discriminator", None)
            avatar = user.get("avatar")
            self.on_join_request(username, uid, discriminator, avatar)

    def _connect_to_party(self, hostname, port) -> None:
        ba.pushcall(
            ba.Call(_ba.connect_to_party, hostname, port), from_other_thread=True
        ) #!Switch windows from discord window to bombsquad if possible

    def on_join_request(self, username, uid, discriminator, avatar) -> None:
        del uid  # unused
        del avatar  # unused
        ba.pushcall(
            ba.Call(
                ba.screenmessage,
                "Discord: {}#{} wants to join!".format(username, discriminator),
                color=(0.0, 1.0, 0.0),
            ),
            from_other_thread=True,
        )#TODO- Add overlay like that one for achievements to show a requested invite request and button on the chat button to accept and maybe send 


dirpath = Path(f"{_ba.app.python_directory_user}/largesets.txt")
run_once = False


def get_once_asset(): 
    global run_once
    if run_once:
        return
    response = Request(
        "https://discordapp.com/api/oauth2/applications/963434684669382696/assets",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    try:
        with urlopen(response) as assets:
            assets = json.loads(assets.read().decode())
        asset = [assetname["name"] for assetname in assets]
    except:
        pass
    with open(dirpath, "wb") as imagesets:
        imagesets.write(encode(str(asset)))
    run_once = True


def get_asset():
    with open(dirpath, "r") as maptxt:
        maptxt = maptxt.read()
    return maptxt


# ba_meta export plugin
class DiscordRP(ba.Plugin):
    def __init__(self) -> None:
        self.update_timer: ba.Timer | None = None
        self.rpc_thread = RpcThread()
        self._last_server_info : str | None = None

        _run_overrides()
        get_once_asset()
        get_asset()

    def on_app_running(self) -> None:
        self.rpc_thread.start() #!except incase discord is not open
        self.update_timer = ba.Timer(
            1, ba.WeakCall(self.update_status), timetype=ba.TimeType.REAL, repeat=True
        )

    def on_app_shutdown(self) -> None:
        self.rpc_thread.should_close = True

    def _get_current_activity_name(self) -> str | None:
        act = _ba.get_foreground_host_activity()
        if isinstance(act, ba.GameActivity):
            return act.name
        this = "Lobby"
        name: str | None = (
                act.__class__.__name__.replace("Activity", "")
                .replace("ScoreScreen", "Ranking")
                .replace("Coop", "")
                .replace("MultiTeam", "")
                .replace("Victory", "")
                .replace("EndSession", "")
                .replace("Transition", "")
                .replace("Draw", "")
                .replace("FreeForAll", "")
                .replace("Join", this)
                .replace("Team", "")
                .replace("Series", "")
                .replace("CustomSession", "Custom Session(mod)")
        )

        if name == "MainMenu":
            name = "Main Menu"
        if name == this:
            self.rpc_thread.large_image_key = "lobby"
            self.rpc_thread.large_image_text = "Bombing up"
        if name == "Ranking":
            self.rpc_thread.large_image_key = "ranking"
            self.rpc_thread.large_image_text = "Viewing Results"
        return name

    def _get_current_map_name(self) -> Tuple[str | None, str | None]:
        act = _ba.get_foreground_host_activity()
        if isinstance(act, ba.GameActivity):
            texname = act.map.get_preview_texture_name()
            if texname:
                return act.map.name, texname.lower().removesuffix("preview")
        return None, None

    def update_status(self) -> None:
        roster = _ba.get_game_roster()
        connection_info = _ba.get_connection_to_host_info()

        self.rpc_thread.large_image_key = "bombsquadicon"
        self.rpc_thread.large_image_text = "BombSquad"
        self.rpc_thread.small_image_key = _ba.app.platform
        self.rpc_thread.small_image_text = (
            f"{_ba.app.platform.capitalize()}({_ba.app.version})"
        )
        connection_info = _ba.get_connection_to_host_info()
        svinfo = str(connection_info)
        if self._last_server_info != svinfo:
            self._last_server_info = svinfo
            self.rpc_thread.party_id = str(uuid.uuid4())
            self.rpc_thread._update_secret()
        if connection_info != {}:
            servername = connection_info["name"]
            self.rpc_thread.details = "Online"
            self.rpc_thread.party_size = max(
                1, sum(len(client["players"]) for client in roster)
            )
            self.rpc_thread.party_max = max(8, self.rpc_thread.party_size)
            if len(servername) == 19 and "Private Party" in servername:
                self.rpc_thread.state = "Private Party"
            elif servername == "":  # A local game joinable from the internet
                try:
                    offlinename = json.loads(_ba.get_game_roster()[0]["spec_string"])[
                        "n"
                    ]
                    if len(offlinename > 19):
                        self.rpc_thread.state = offlinename[slice(19)] + "..."
                    else:
                        self.rpc_thread.state = offlinename
                except IndexError:
                    pass
            else:
                if len(servername) > 19:
                    self.rpc_thread.state = servername[slice(19)] + ".."
                else:
                    self.rpc_thread.state = servername[slice(19)]

        if connection_info == {}:
            self.rpc_thread.details = "Local"
            self.rpc_thread.state = self._get_current_activity_name()
            self.rpc_thread.party_size = max(1, len(roster))
            self.rpc_thread.party_max = max(1, _ba.get_public_party_max_size())

            if (
                _ba.get_foreground_host_session() is not None
                and self.rpc_thread.details == "Local"
            ):
                session = (
                    _ba.get_foreground_host_session()
                    .__class__.__name__.replace("MainMenuSession", "")
                    .replace("EndSession", "")
                    .replace("FreeForAllSession", ": FFA")
                    .replace("DualTeamSession", ": Teams")
                    .replace("CoopSession", ": Coop")
                )
                self.rpc_thread.details = f"{self.rpc_thread.details} {session}"
            if (
                self.rpc_thread.state == "NoneType"
            ):  # sometimes the game just breaks which means its not really watching replay FIXME
                self.rpc_thread.state = "Watching Replay"
                self.rpc_thread.large_image_key = "replay"
                self.rpc_thread.large_image_text = "Viewing Awesomeness"

            act = _ba.get_foreground_host_activity()
            session = _ba.get_foreground_host_session()
            if act:
                from bastd.game.elimination import EliminationGame
                from bastd.game.thelaststand import TheLastStandGame
                from bastd.game.meteorshower import MeteorShowerGame

                # noinspection PyUnresolvedReferences,PyProtectedMember
                try:
                    self.rpc_thread.start_timestamp = act._discordrp_start_time  # type: ignore
                except AttributeError:
                    # This can be the case if plugin launched AFTER activity
                    # has been created; in that case let's assume it was
                    # created just now.
                    self.rpc_thread.start_timestamp = act._discordrp_start_time = time.mktime(  # type: ignore
                        time.localtime()
                    )
                if isinstance(act, EliminationGame):
                    alive_count = len([p for p in act.players if p.lives > 0])
                    self.rpc_thread.details += f" ({alive_count} players left)"
                elif isinstance(act, TheLastStandGame):
                    # noinspection PyProtectedMember
                    points = act._score
                    self.rpc_thread.details += f" ({points} points)"
                elif isinstance(act, MeteorShowerGame):
                    with ba.Context(act):
                        sec = ba.time() - act._timer.getstarttime()
                    secfmt = ""
                    if sec < 60:
                        secfmt = f"{sec:.2f}"
                    else:
                        secfmt = f"{int(sec) // 60:02}:{sec:.2f}"
                    self.rpc_thread.details += f" ({secfmt})"

                # if isinstance(session, ba.DualTeamSession):
                #     scores = ':'.join([
                #         str(t.customdata['score'])
                #         for t in session.sessionteams
                #     ])
                #     self.rpc_thread.details += f' ({scores})'

            mapname, short_map_name = self._get_current_map_name()
            if mapname:
                if short_map_name in get_asset():
                    self.rpc_thread.large_image_text = mapname
                    self.rpc_thread.large_image_key = short_map_name
                    self.rpc_thread.small_image_key = "bombsquadlogo2"
                    self.rpc_thread.small_image_text = "BombSquad"

        if _ba.get_idle_time() / (1000 * 60) % 60 >= 0.2:
            self.rpc_thread.details = f"AFK in {self.rpc_thread.details}"
            self.rpc_thread.large_image_key = (
                "https://media.tenor.com/uAqNn6fv7x4AAAAM/bombsquad-spaz.gif"
            )
