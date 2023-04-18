# Released under the MIT License. See LICENSE for details.
#
"""placeholder :clown:"""

# ba_meta require api 7
#!"Made to you by @brostos & @Dliwk"


from __future__ import annotations
from urllib.request import Request, urlopen, urlretrieve
from pathlib import Path
from os import getcwd, remove
from zipfile import ZipFile
from bastd.ui.popup import PopupWindow

import asyncio
import http.client
import ast
import uuid
import json
import time
import threading
import ba
import _ba

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Tuple


android = ba.app.platform == "android"

if android:  # !can add ios in future

    # Installing websocket
    def get_module():
        install_path = Path(f"{getcwd()}/ba_data/python")  # For the guys like me on windows
        path = Path(f"{install_path}/websocket.zip")
        file_path = Path(f"{install_path}/websocket")
        if not file_path.exists():
            url = "https://github.com/brostosjoined/bombsquadrpc/releases/download/presence-1.0/websocket.zip"
            filename, headers = urlretrieve(url, filename=path)
            with ZipFile(filename) as f:
                f.extractall(install_path)
            remove(path)
    get_module()

    import websocket

    heartbeat_interval = int(41250)
    resume_gateway_url: str | None = None
    session_id: str | None = None

    start_time = time.time()

    class PresenceUpdate:
        def __init__(self):
            self.state: str | None = "In Game"
            self.details: str | None = "Main Menu"
            self.start_timestamp = time.time()
            self.large_image_key: str | None = "bombsquadicon"
            self.large_image_text: str | None = "BombSquad Icon"
            self.small_image_key: str | None = None
            self.small_image_text: str | None = (
                f"{_ba.app.platform.capitalize()}({_ba.app.version})")
            self.media_proxy = "mp:/app-assets/963434684669382696/{}.png"
            self.identify: bool = False
            self.party_id: str = str(uuid.uuid4())
            self.party_size = 1
            self.party_max = 8

        def presence(self):
            with open(dirpath, "r") as maptxt:
                if self.large_image_key != "mp:external/btl_oZF6BdUjijINOnrf9hw0_nCrwsHYJoJKEZKKye8/https/media.tenor.com/uAqNn6fv7x4AAAAM/bombsquad-spaz.gif":
                    largetxt = json.load(maptxt)[self.large_image_key]
                # else: #!some junk here
                #     self.media_proxy = "mp:external/btl_oZF6BdUjijINOnrf9hw0_nCrwsHYJoJKEZKKye8{}"
                #     self.large_image_key = '/https/media.tenor.com/uAqNn6fv7x4AAAAM/bombsquad-spaz.gif'
            with open(dirpath, "r") as maptxt:
                smalltxt = json.load(maptxt)[self.small_image_key]

            presencepayload = {
                "op": 3,
                "d": {
                    "since": None,  # used to show how long the user went idle will add afk to work with this and then set the status to idle
                    "status": "online",
                    "afk": "false",
                    "activities": [
                        {
                            "name": "BombSquad",
                            "type": 0,
                            "application_id": "963434684669382696",
                            "state": self.state,
                            "details": self.details,
                            "timestamps": {
                                "start": start_time
                            },
                            "party": {
                                "id": self.party_id,
                                "size": [self.party_size, self.party_max]
                            },
                            "assets": {
                                "large_image": self.media_proxy.format(largetxt),
                                "large_text": self.large_image_text,
                                "small_image": self.media_proxy.format(smalltxt),
                                "small_text": self.small_image_text,
                            },
                            "client_info": {
                                "version": 0,
                                "os": "android",
                                "client": "mobile",
                            },
                            "buttons": ["Discord Server", "Download BombSquad"],
                            "metadata": {
                                "button_urls": [
                                    "https://discord.gg/bombsquad-ballistica-official-1001896771347304639",
                                    "https://bombsquad.ga/download",
                                ]
                            },
                        }
                    ],
                },
            }
            ws.send(json.dumps(presencepayload))

    def on_message(ws, message):
        global heartbeat_interval
        message = json.loads(message)
        try:
            get_interval = message["d"]["heartbeat_interval"]
            if get_interval:
                heartbeat_interval = get_interval
        except:
            pass

    def on_error(ws, error):
        ba.print_exception(error)

    def on_close(ws, close_status_code, close_msg):
        # print("### closed ###")
        pass

    def on_open(ws):
        print("Connected to Discord Websocket")

        def heartbeats():
            """Sending heartbeats to keep the connection alive"""
            global heartbeat_interval
            runonce = True
            while runonce:
                heartbeat_payload = {
                    "op": 1,
                    "d": 251,
                }  # step two keeping connection alive by sending heart beats and receiving opcode 11
                ws.send(json.dumps(heartbeat_payload))
                runonce = False

                def identify():
                    """Identifying to the gateway and enable by using user token and the intents we will be using e.g 256->For Presence"""
                    with open(f"{getcwd()}/token.txt", 'r') as f:
                        token = bytes.fromhex(f.read()).decode('utf-8')
                    identify_payload = {
                        "op": 2,
                        "d": {
                            "token": token,
                            "properties": {
                                "os": "linux",
                                "browser": "Discord Android",
                                "device": "android",
                            },
                            "intents": 256,
                        },
                    }  # step 3 send an identify
                    ws.send(json.dumps(identify_payload))
                identify()
            while not runonce:
                heartbeat_payload = {"op": 1, "d": heartbeat_interval}
                ws.send(json.dumps(heartbeat_payload))
                time.sleep(heartbeat_interval / 1000)

        threading.Thread(target=heartbeats, daemon=True, name="heartbeat").start()

    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        "wss://gateway.discord.gg/?encoding=json&v=10",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    threading.Thread(target=ws.run_forever, daemon=True, name="websocket").start()


if not android:

    # installing pypresence
    def get_module():
        install_path = Path(f"{getcwd()}/ba_data/python")
        path = Path(f"{install_path}/pypresence.zip")
        file_path = Path(f"{install_path}/pypresence")
        if not file_path.exists():
            url = "https://github.com/brostosjoined/bombsquadrpc/releases/download/presence-1.0/pypresence.zip"
            filename, headers = urlretrieve(url, filename=path)
            with ZipFile(filename) as f:
                f.extractall(install_path)
            remove(path)
    get_module()

    from pypresence.utils import get_event_loop
    import pypresence

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
            self._last_update_time: float = 0
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
                try:
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
                except:
                    pass

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
            )  # !Switch windows from discord window to bombsquad if possible

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
            )  # TODO- Add overlay like that one for achievements to show a requested invite request and button on the chat button to accept and maybe send


dirpath = Path(f"{_ba.app.python_directory_user}/image_id.json")
run_once = False


class Discordlogin(PopupWindow):

    def __init__(self):
        # pylint: disable=too-many-locals
        uiscale = ba.app.ui.uiscale
        self._transitioning_out = False
        self._width = 400
        self._height = 420
        self.consec_press = 0
        self.path = Path(f"{getcwd()}/token.txt")
        bg_color = (0.5, 0.4, 0.6)

        # creates our _root_widget
        PopupWindow.__init__(self,
                             position=(0.0, 0.0),
                             size=(self._width, self._height),
                             scale=1.2,
                             bg_color=bg_color)

        self._cancel_button = ba.buttonwidget(
            parent=self.root_widget,
            position=(25, self._height - 40),
            size=(50, 50),
            scale=0.58,
            label='',
            color=bg_color,
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=ba.gettexture('crossOut'),
            iconscale=1.2)

        self.terminate_button = ba.buttonwidget(parent=self.root_widget,
                                                position=(135, 250),
                                                size=(135, 90),
                                                on_activate_call=self.terminate,
                                                textcolor=(0.8, 0.8, 0.85),
                                                # (1.00, 0.15, 0.15)red
                                                color=(0.525, 0.595, 1.458),
                                                button_type='square',
                                                text_scale=1,
                                                label="")

        ba.imagewidget(parent=self.root_widget,
                       position=(143, 250),
                       size=(115, 90),
                       texture=ba.gettexture("discordLogo"),
                       color=(10 - 0.32, 10 - 0.39, 10 - 0.96),
                       draw_controller=self.terminate_button)

        self.email_widget = ba.textwidget(parent=self.root_widget,
                                          text="email",
                                          size=(360, 70),
                                          position=(35, 180),
                                          h_align='left',
                                          v_align='center',
                                          editable=True,
                                          scale=0.8,
                                          autoselect=True,
                                          maxwidth=220,)
        # description='Username')

        self.password_widget = ba.textwidget(parent=self.root_widget,
                                             text="password",
                                             size=(250, 70),
                                             position=(44, 120),
                                             h_align='left',
                                             v_align='center',
                                             editable=True,
                                             scale=0.8,
                                             autoselect=True,
                                             maxwidth=220,)
        # description='Username')

        ba.containerwidget(edit=self.root_widget,
                           cancel_button=self._cancel_button)
        self._login_button = ba.buttonwidget(
            parent=self.root_widget,
            position=(150, 65),
            size=(160, 90),
            scale=0.58,
            label='Login',
            color=(0.10, 0.95, 0.10),
            on_activate_call=self.login,
            autoselect=True,)
        # icon=ba.gettexture('crossOut'),
        # iconscale=1.2)

        ba.textwidget(
            parent=self.root_widget,
            position=(self._width * 0.5, self._height - 30),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=1.0,
            text="LOGIN/TERMINATE DISCORD",
            maxwidth=200,
            color=(0.10, 0.95, 0.10))

    def _on_cancel_press(self) -> None:
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            ba.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._transition_out()

    def login(self):
        if not self.path.exists():
            json_data = {
                'login': ba.textwidget(query=self.email_widget),
                'password': ba.textwidget(query=self.password_widget),
                'undelete': False,
                'captcha_key': None,
                'login_source': None,
                'gift_code_sku_id': None,
            }
            headers = {
                'user-agent': "Mozilla/5.0",
                'content-type': "application/json",
            }

            conn = http.client.HTTPSConnection("discord.com")

            payload = json.dumps(json_data)
            conn.request("POST", "/api/v9/auth/login", payload, headers)
            res = conn.getresponse().read()

            try:
                token = json.loads(res)['token'].encode().hex().encode()
                with open(self.path, 'wb') as f:
                    f.write(token)
                ba.screenmessage("Successfully logged in", (0.21, 1.0, 0.20))
                ba.playsound(ba.getsound('shieldUp'))
            except:
                ba.screenmessage("Incorrect credentials", (1.00, 0.15, 0.15))
                ba.playsound(ba.getsound('error'))

            conn.close()
        else:
            ba.screenmessage("Already logged in", (0.10, 0.35, 0.10))
            ba.playsound(ba.getsound('block'))

    def terminate(self):
        if self.consec_press > 9 and self.path.exists():
            remove(self.path)
            ba.playsound(ba.getsound('shieldDown'))
            ba.screenmessage("Account successfully removed!!", (0.10, 0.10, 1.00))
            self.consec_press = 0
        elif not self.path.exists():
            ba.playsound(ba.getsound('blip'))
            ba.screenmessage("Login First", (1.00, 0.50, 0.00))
        else:
            if self.consec_press <= 9:
                ba.playsound(ba.getsound('activateBeep'))
                ba.playsound(ba.getsound('warnBeeps'))
                ba.screenmessage(
                    f"You are {10-self.consec_press} steps from terminating your account", (0.50, 0.25, 1.00))
                self.consec_press += 1


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
            assets = json.loads(assets.read())
        asset = []
        asset_id = []
        for x in assets:
            dem = x["name"]
            don = x["id"]
            asset_id.append(don)
            asset.append(dem)
        asset_id_dict = dict(zip(asset, asset_id))

        with open(dirpath, "w") as imagesets:
            jsonfile = json.dumps(asset_id_dict, indent=4)
            json.dump(asset_id_dict, imagesets)
    except:
        pass
    run_once = True


def get_class():
    if android:
        return PresenceUpdate()
    elif not android:
        return RpcThread()


# ba_meta export plugin
class DiscordRP(ba.Plugin):
    def __init__(self) -> None:
        self.update_timer: ba.Timer | None = None
        self.rpc_thread = get_class()
        self._last_server_info: str | None = None

        if not android:
            _run_overrides()
        get_once_asset()

    def on_app_running(self) -> None:
        if not android:
            self.rpc_thread.start()  # !except incase discord is not open
            self.update_timer = ba.Timer(
                1, ba.WeakCall(self.update_status), timetype=ba.TimeType.REAL, repeat=True
            )
        if android:
            self.update_timer = ba.Timer(
                4, ba.WeakCall(self.update_status), timetype=ba.TimeType.REAL, repeat=True
            )

    def has_settings_ui(self):
        return True

    def show_settings_ui(self, button):
        if not android:
            ba.screenmessage("Nothing here achievement!!!", (0.26, 0.65, 0.94))
            ba.playsound(ba.getsound('achievement'))
        else:
            Discordlogin()

    def on_app_shutdown(self) -> None:
        if not android:
            self.rpc_thread.should_close = True
        else:
            ws.close()

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
            self.rpc_thread.small_image_key = "lobbysmall"
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
        if not android:
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
                #!self.rpc_thread.small_image_key = session.lower()
                self.rpc_thread.details = f"{self.rpc_thread.details} {session}"
            if (
                self.rpc_thread.state == "NoneType"
            ):  # sometimes the game just breaks which means its not really watching replay FIXME
                self.rpc_thread.state = "Watching Replay"
                self.rpc_thread.large_image_key = "replay"
                self.rpc_thread.large_image_text = "Viewing Awesomeness"
                #!self.rpc_thread.small_image_key = "replaysmall"

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
                with open(dirpath, 'r') as asset_dict:
                    asset_keys = json.load(asset_dict).keys()
                if short_map_name in asset_keys:
                    self.rpc_thread.large_image_text = mapname
                    self.rpc_thread.large_image_key = short_map_name

        if _ba.get_idle_time() / (1000 * 60) % 60 >= 0.2:
            self.rpc_thread.details = f"AFK in {self.rpc_thread.details}"
            self.rpc_thread.large_image_key = (
                "https://media.tenor.com/uAqNn6fv7x4AAAAM/bombsquad-spaz.gif"
            )
        if android:
            self.rpc_thread.presence()
