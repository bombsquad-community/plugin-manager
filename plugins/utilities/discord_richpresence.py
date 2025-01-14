# Released under the MIT and Apache License. See LICENSE for details.
#
"""placeholder :clown:"""

# ba_meta require api 9
#!"Made to you by @brostos & @Dliwk"


from __future__ import annotations
from urllib.request import Request, urlopen, urlretrieve
from pathlib import Path
from os import getcwd, remove
from bauiv1lib.popup import PopupWindow


import asyncio
import http.client
import ast
import uuid
import json
import time
import threading
import shutil
import hashlib
import babase
import _babase
import bascenev1 as bs
import bascenev1lib
import bauiv1 as bui
from baenv import TARGET_BALLISTICA_BUILD as build_number

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Tuple


ANDROID = babase.app.classic.platform == "android"
DIRPATH = Path(
    f"{_babase.app.python_directory_user if build_number < 21282 else _babase.app.env.python_directory_user}/image_id.json")
APP_VERSION = _babase.app.version if build_number < 21282 else (
    _babase.app.env.engine_version if build_number > 21823 else _babase.app.env.version)

if ANDROID:  # !can add ios in future

    # Installing websocket
    def get_module():
        install_path = Path(f"{getcwd()}/ba_data/python")  # For the guys like me on windows
        path = Path(f"{install_path}/websocket.tar.gz")
        file_path = Path(f"{install_path}/websocket")
        source_dir = Path(f"{install_path}/websocket-client-1.6.1/websocket")
        if not Path(f"{file_path}/__init__.py").exists():  # YouKnowDev
            url = "https://files.pythonhosted.org/packages/b1/34/3a5cae1e07d9566ad073fa6d169bf22c03a3ba7b31b3c3422ec88d039108/websocket-client-1.6.1.tar.gz"
            try:
                # fix issue where the file delete themselves
                try:
                    shutil.rmtree(file_path)
                except:
                    pass
                filename, headers = urlretrieve(url, filename=path)
                with open(filename, "rb") as f:
                    content = f.read()
                    assert hashlib.md5(content).hexdigest() == "86bc69b61947943627afc1b351c0b5db"
                shutil.unpack_archive(filename, install_path)
                remove(path)
                shutil.copytree(source_dir, file_path)
                shutil.rmtree(Path(f"{install_path}/websocket-client-1.6.1"))
            except Exception as e:
                if type(e) == shutil.Error:
                    shutil.rmtree(Path(f"{install_path}/websocket-client-1.6.1"))
                else:
                    pass
    get_module()

    from websocket import WebSocketConnectionClosedException
    import websocket

    start_time = time.time()

    class PresenceUpdate:
        def __init__(self):
            self.ws = websocket.WebSocketApp("wss://gateway.discord.gg/?encoding=json&v=10",
                                             on_open=self.on_open,
                                             on_message=self.on_message,
                                             on_error=self.on_error,
                                             on_close=self.on_close)
            self.heartbeat_interval = int(41250)
            self.resume_gateway_url: str | None = None
            self.session_id: str | None = None
            self.stop_heartbeat_thread = threading.Event()
            self.do_once = True
            self.state: str | None = "In Game"
            self.details: str | None = "Main Menu"
            self.start_timestamp = time.time()
            self.large_image_key: str | None = "bombsquadicon"
            self.large_image_text: str | None = "BombSquad Icon"
            self.small_image_key: str | None = None
            self.small_image_text: str | None = (
                f"{_babase.app.classic.platform.capitalize()}({APP_VERSION})")
            self.media_proxy = "mp:/app-assets/963434684669382696/{}.png"
            self.identify: bool = False
            self.party_id: str = str(uuid.uuid4())
            self.party_size = 1
            self.party_max = 8

        def presence(self):
            with open(DIRPATH, "r") as maptxt:
                largetxt = json.load(maptxt)[self.large_image_key]
            with open(DIRPATH, "r") as maptxt:
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
                                    "https://bombsquad-community.web.app/download",
                                ]
                            },
                        }
                    ],
                },
            }
            try:
                self.ws.send(json.dumps(presencepayload))
            except WebSocketConnectionClosedException:
                pass

        def on_message(self, ws, message):
            message = json.loads(message)
            try:
                self.heartbeat_interval = message["d"]["heartbeat_interval"]
            except:
                pass
            try:
                self.resume_gateway_url = message["d"]["resume_gateway_url"]
                self.session_id = message["d"]["session_id"]
            except:
                pass

        def on_error(self, ws, error):
            babase.print_exception(error)

        def on_close(self, ws, close_status_code, close_msg):
            print("Closed Discord Connection Successfully")

        def on_open(self, ws):
            print("Connected to Discord Websocket")

            def heartbeats():
                """Sending heartbeats to keep the connection alive"""
                if self.do_once:
                    heartbeat_payload = {
                        "op": 1,
                        "d": 251,
                    }  # step two keeping connection alive by sending heart beats and receiving opcode 11
                    self.ws.send(json.dumps(heartbeat_payload))
                    self.do_once = False

                    def identify():
                        """Identifying to the gateway and enable by using user token and the intents we will be using e.g 256->For Presence"""
                        with open(f"{_babase.app.env.python_directory_user}/__pycache__/token.txt", 'r') as f:
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
                        self.ws.send(json.dumps(identify_payload))
                    identify()
                while True:
                    heartbeat_payload = {"op": 1, "d": self.heartbeat_interval}

                    try:
                        self.ws.send(json.dumps(heartbeat_payload))
                        time.sleep(self.heartbeat_interval / 1000)
                    except:
                        pass

                    if self.stop_heartbeat_thread.is_set():
                        self.stop_heartbeat_thread.clear()
                        break

            threading.Thread(target=heartbeats, daemon=True, name="heartbeat").start()

        def start(self):
            if Path(f"{_babase.app.env.python_directory_user}/__pycache__/token.txt").exists():
                threading.Thread(target=self.ws.run_forever, daemon=True, name="websocket").start()

        def close(self):
            self.stop_heartbeat_thread.set()
            self.do_once = True
            self.ws.close()


if not ANDROID:
    # installing pypresence
    def get_module():
        install_path = Path(f"{getcwd()}/ba_data/python")
        path = Path(f"{install_path}/pypresence.tar.gz")
        file_path = Path(f"{install_path}/pypresence")
        source_dir = Path(f"{install_path}/pypresence-4.3.0/pypresence")
        if not file_path.exists():
            url = "https://files.pythonhosted.org/packages/f4/2e/d110f862720b5e3ba1b0b719657385fc4151929befa2c6981f48360aa480/pypresence-4.3.0.tar.gz"
            try:
                filename, headers = urlretrieve(url, filename=path)
                with open(filename, "rb") as f:
                    content = f.read()
                    assert hashlib.md5(content).hexdigest() == "f7c163cdd001af2456c09e241b90bad7"
                shutil.unpack_archive(filename, install_path)
                shutil.copytree(source_dir, file_path)
                shutil.rmtree(Path(f"{install_path}/pypresence-4.3.0"))
                remove(path)
            except:
                pass

            # Make modifications for it to work on windows
            if babase.app.classic.platform == "windows":
                with open(Path(f"{getcwd()}/ba_data/python/pypresence/utils.py"), "r") as file:
                    data = file.readlines()
                    data[45] = """
def get_event_loop(force_fresh=False):
    loop = asyncio.ProactorEventLoop() if sys.platform == 'win32' else asyncio.new_event_loop()
    if force_fresh:
        return loop
    try:
        running = asyncio.get_running_loop()
    except RuntimeError:
        return loop
    if running.is_closed():
        return loop
    else:
        if sys.platform in ('linux', 'darwin'):
            return running
        if sys.platform == 'win32':
            if isinstance(running, asyncio.ProactorEventLoop):
                return running
            else:
                return loop"""
                    # Thanks Loup
                    with open(Path(f"{getcwd()}/ba_data/python/pypresence/utils.py"), "w") as file:
                        for number, line in enumerate(data):
                            if number not in range(46, 56):
                                file.write(line)
        # fix the mess i did with the previous
        elif file_path.exists():
            with open(Path(f"{getcwd()}/ba_data/python/pypresence/utils.py"), "r") as file:
                data = file.readlines()
                first_line = data[0].rstrip("\n")
                if not first_line == '"""Util functions that are needed but messy."""':
                    shutil.rmtree(file_path)
                    get_module()
    get_module()

    from pypresence import PipeClosed, DiscordError, DiscordNotFound
    from pypresence.utils import get_event_loop
    import pypresence
    import socket

    DEBUG = True

    _last_server_addr = 'localhost'
    _last_server_port = 43210

    def print_error(err: str, include_exception: bool = False) -> None:
        if DEBUG:
            if include_exception:
                babase.print_exception(err)
            else:
                babase.print_error(err)
        else:
            print(f"ERROR in discordrp.py: {err}")

    def log(msg: str) -> None:
        if DEBUG:
            print(f"LOG in discordrp.py: {msg}")

    def _run_overrides() -> None:
        old_init = bs.Activity.__init__

        def new_init(self, *args: Any, **kwargs: Any) -> None:  # type: ignore
            old_init(self, *args, **kwargs)
            self._discordrp_start_time = time.mktime(time.localtime())

        bs.Activity.__init__ = new_init  # type: ignore

        old_connect = bs.connect_to_party

        def new_connect(*args, **kwargs) -> None:  # type: ignore
            global _last_server_addr
            global _last_server_port
            old_connect(*args, **kwargs)
            c = kwargs.get("address") or args[0]
            _last_server_port = kwargs.get("port") or args[1]

        bs.connect_to_party = new_connect

    start_time = time.time()

    class RpcThread(threading.Thread):
        def __init__(self):
            super().__init__(name="RpcThread")
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

        @staticmethod
        def is_discord_running():
            for i in range(6463, 6473):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.01)
                try:
                    conn = s.connect_ex(('localhost', i))
                    s.close()
                    if (conn == 0):
                        s.close()
                        return (True)
                except:
                    s.close()
                    return (False)

        def _generate_join_secret(self):
            # resp = requests.get('https://legacy.ballistica.net/bsAccessCheck').text
            try:
                connection_info = bs.get_connection_to_host_info(
                ) if build_number < 21727 else bs.get_connection_to_host_info_2()
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
            except:
                pass

        def _update_secret(self):
            threading.Thread(target=self._generate_join_secret, daemon=True).start()
            self._last_secret_update_time = time.time()

        def run(self) -> None:
            asyncio.set_event_loop(get_event_loop())
            while not self.should_close:
                if time.time() - self._last_update_time > 0.1:
                    self._do_update_presence()
                if time.time() - self._last_secret_update_time > 15:
                    self._update_secret()
                # if time.time() - self._last_connect_time > 120 and is_discord_running(): #!Eric please add module manager(pip)
                #     self._reconnect()
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

        # def _update_presence(self) -> None:
        #     self._last_update_time = time.time()
        #     try:
        #         self._do_update_presence()
        #     except (AttributeError, AssertionError):
        #         try:
        #             self._reconnect()
        #         except Exception:
        #             print_error("failed to update presence", include_exception= True)

        def _reconnect(self) -> None:
            self.rpc.connect()
            self._subscribe_events()
            self._do_update_presence()
            self._last_connect_time = time.time()

        def _do_update_presence(self) -> None:
            if RpcThread.is_discord_running():
                self._last_update_time = time.time()
                try:
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
                except (PipeClosed, DiscordError, AssertionError, AttributeError):
                    try:
                        self._reconnect()
                    except (DiscordNotFound, DiscordError):
                        pass

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
                    babase.print_exception("discordrp: unknown activity join format")
                else:
                    try:
                        if format_version == 1:
                            hostname = server["hostname"]
                            port = server["port"]
                            self._connect_to_party(hostname, port)
                    except Exception:
                        babase.print_exception(
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
            babase.pushcall(
                babase.Call(bs.connect_to_party, hostname, port), from_other_thread=True
            )

        def on_join_request(self, username, uid, discriminator, avatar) -> None:
            del uid  # unused
            del avatar  # unused
            babase.pushcall(
                babase.Call(
                    bui.screenmessage,
                    "Discord: {}{} wants to join!".format(
                        username, discriminator if discriminator != "#0" else ""),
                    color=(0.0, 1.0, 0.0),
                ),
                from_other_thread=True,
            )
            babase.pushcall(lambda: bui.getsound('bellMed').play(), from_other_thread=True)


class Discordlogin(PopupWindow):

    def __init__(self):
        # pylint: disable=too-many-locals
        _uiscale = bui.app.ui_v1.uiscale
        self._transitioning_out = False
        s = 1.25 if _uiscale is babase.UIScale.SMALL else 1.27 if _uiscale is babase.UIScale.MEDIUM else 1.3
        self._width = 380 * s
        self._height = 150 + 150 * s
        self.path = Path(f"{_babase.app.env.python_directory_user}/__pycache__/token.txt")
        bg_color = (0.5, 0.4, 0.6)
        log_btn_colour = (0.10, 0.95, 0.10) if not self.path.exists() else (1.00, 0.15, 0.15)
        log_txt = "LOG IN" if not self.path.exists() else "LOG OUT"
        self.code = False
        self.resp = "Placeholder"
        self.headers = {
            'user-agent': "Mozilla/5.0",
            'content-type': "application/json",
        }

        # creates our _root_widget
        PopupWindow.__init__(self,
                             position=(0.0, 0.0),
                             size=(self._width, self._height),
                             scale=(2.1 if _uiscale is babase.UIScale.SMALL else 1.5
                                    if _uiscale is babase.UIScale.MEDIUM else 1.0),
                             bg_color=bg_color)

        self._cancel_button = bui.buttonwidget(
            parent=self.root_widget,
            position=(25, self._height - 40),
            size=(50, 50),
            scale=0.58,
            label='',
            color=bg_color,
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=bui.gettexture('crossOut'),
            iconscale=1.2)

        bui.imagewidget(parent=self.root_widget,
                        position=(180, self._height - 55),
                        size=(32 * s, 32 * s),
                        texture=bui.gettexture("discordLogo"),
                        color=(10 - 0.32, 10 - 0.39, 10 - 0.96))

        self.email_widget = bui.textwidget(parent=self.root_widget,
                                           text="Email/Phone Number",
                                           size=(400, 70),
                                           position=(50, 180),
                                           h_align='left',
                                           v_align='center',
                                           editable=True,
                                           scale=0.8,
                                           autoselect=True,
                                           maxwidth=220)

        self.password_widget = bui.textwidget(parent=self.root_widget,
                                              text="Password",
                                              size=(400, 70),
                                              position=(50, 120),
                                              h_align='left',
                                              v_align='center',
                                              editable=True,
                                              scale=0.8,
                                              autoselect=True,
                                              maxwidth=220)

        bui.containerwidget(edit=self.root_widget,
                            cancel_button=self._cancel_button)

        bui.textwidget(
            parent=self.root_widget,
            position=(265, self._height - 37),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=1.0,
            text="Discord",
            maxwidth=200,
            color=(0.80, 0.80, 0.80))

        bui.textwidget(
            parent=self.root_widget,
            position=(265, self._height - 78),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=1.0,
            text="💀Use at your own risk💀\n ⚠️discord account might get terminated⚠️",
            maxwidth=200,
            color=(1.00, 0.15, 0.15))

        self._login_button = bui.buttonwidget(
            parent=self.root_widget,
            position=(120, 65),
            size=(400, 80),
            scale=0.58,
            label=log_txt,
            color=log_btn_colour,
            on_activate_call=self.login,
            autoselect=True)

    def _on_cancel_press(self) -> None:
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_bascenev1libup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._transition_out()

    def backup_2fa_code(self, tickt):
        if babase.do_once():
            self.email_widget.delete()
            self.password_widget.delete()

            self.backup_2fa_widget = bui.textwidget(parent=self.root_widget,
                                                    text="2FA/Discord Backup code",
                                                    size=(400, 70),
                                                    position=(50, 120),
                                                    h_align='left',
                                                    v_align='center',
                                                    editable=True,
                                                    scale=0.8,
                                                    autoselect=True,
                                                    maxwidth=220)

        json_data_2FA = {
            "code": bui.textwidget(query=self.backup_2fa_widget),
            "gift_code_sku_id": None,
            "ticket": tickt,
        }

        if json_data_2FA['code'] != "2FA/Discord Backup code":
            try:
                payload_2FA = json.dumps(json_data_2FA)
                conn_2FA = http.client.HTTPSConnection("discord.com")
                conn_2FA.request("POST", "/api/v9/auth/mfa/totp", payload_2FA, self.headers)
                res_2FA = conn_2FA.getresponse().read()
                token = json.loads(res_2FA)['token'].encode().hex().encode()

                with open(self.path, 'wb') as f:
                    f.write(token)
                bui.screenmessage("Successfully logged in", (0.21, 1.0, 0.20))
                bui.getsound('shieldUp').play()
                self.on_bascenev1libup_cancel()
                PresenceUpdate().start()
            except:
                self.code = True
                bui.screenmessage("Incorrect code", (1.00, 0.15, 0.15))
                bui.getsound('error').play()

    def login(self):
        if not self.path.exists() and self.code == False:
            try:

                json_data = {
                    'login': bui.textwidget(query=self.email_widget),
                    'password': bui.textwidget(query=self.password_widget),
                    'undelete': False,
                    'captcha_key': None,
                    'login_source': None,
                    'gift_code_sku_id': None,
                }

                conn = http.client.HTTPSConnection("discord.com")

                payload = json.dumps(json_data)
                # conn.request("POST", "/api/v9/auth/login", payload, headers)
                # res = conn.getresponse().read()
                conn.request("POST", "/api/v9/auth/login", payload, self.headers)
                res = conn.getresponse().read()

                try:
                    token = json.loads(res)['token'].encode().hex().encode()
                    with open(self.path, 'wb') as f:
                        f.write(token)
                        bui.screenmessage("Successfully logged in", (0.21, 1.0, 0.20))
                        bui.getsound('shieldUp').play()
                        self.on_bascenev1libup_cancel()
                        PresenceUpdate().start()
                except KeyError:
                    try:
                        ticket = json.loads(res)['ticket']
                        bui.screenmessage("Input your 2FA or Discord Backup code",
                                          (0.21, 1.0, 0.20))
                        bui.getsound('error').play()
                        self.resp = ticket
                        self.backup_2fa_code(tickt=ticket)
                        self.code = True
                    except KeyError:
                        bui.screenmessage("Incorrect credentials", (1.00, 0.15, 0.15))
                        bui.getsound('error').play()

            except:
                bui.screenmessage("Connect to the internet", (1.00, 0.15, 0.15))
                bui.getsound('error').play()

            conn.close()
        elif self.code == True:
            self.backup_2fa_code(tickt=self.resp)

        else:
            self.email_widget.delete()
            self.password_widget.delete()
            remove(self.path)
            bui.getsound('shieldDown').play()
            bui.screenmessage("Account successfully removed!!", (0.10, 0.10, 1.00))
            self.on_bascenev1libup_cancel()
            PresenceUpdate().close()


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
            assets = json.loads(assets.read())
        asset = []
        asset_id = []
        for x in assets:
            dem = x["name"]
            don = x["id"]
            asset_id.append(don)
            asset.append(dem)
        asset_id_dict = dict(zip(asset, asset_id))

        with open(DIRPATH, "w") as imagesets:
            jsonfile = json.dumps(asset_id_dict)
            json.dump(asset_id_dict, imagesets, indent=4)
    except:
        pass
    run_once = True


def get_class():
    if ANDROID:
        return PresenceUpdate()
    elif not ANDROID:
        return RpcThread()


# ba_meta export babase.Plugin
class DiscordRP(babase.Plugin):
    def __init__(self) -> None:
        self.update_timer: bs.Timer | None = None
        self.rpc_thread = get_class()
        self._last_server_info: str | None = None

        if not ANDROID:
            _run_overrides()
        get_once_asset()

    def on_app_running(self) -> None:
        if not ANDROID:
            self.rpc_thread.start()

            self.update_timer = bs.AppTimer(
                1, bs.WeakCall(self.update_status), repeat=True
            )
        if ANDROID:
            self.rpc_thread.start()
            self.update_timer = bs.AppTimer(
                4, bs.WeakCall(self.update_status), repeat=True
            )

    def has_settings_ui(self):
        return True

    def show_settings_ui(self, button):
        if not ANDROID:
            bui.screenmessage("Nothing here achievement!!!", (0.26, 0.65, 0.94))
            bui.getsound('achievement').play()
        if ANDROID:
            Discordlogin()

    def on_app_shutdown(self) -> None:
        if not ANDROID and self.rpc_thread.is_discord_running():
            self.rpc_thread.rpc.close()
            self.rpc_thread.should_close = True

    def on_app_pause(self) -> None:
        self.rpc_thread.close()

    def on_app_resume(self) -> None:
        global start_time
        start_time = time.time()
        self.rpc_thread.start()

    def _get_current_activity_name(self) -> str | None:
        act = bs.get_foreground_host_activity()
        if isinstance(act, bs.GameActivity):
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
            # self.rpc_thread.small_image_key = "lobbysmall"
        if name == "Ranking":
            self.rpc_thread.large_image_key = "ranking"
            self.rpc_thread.large_image_text = "Viewing Results"
        return name

    def _get_current_map_name(self) -> Tuple[str | None, str | None]:
        act = bs.get_foreground_host_activity()
        if isinstance(act, bs.GameActivity):
            texname = act.map.get_preview_texture_name()
            if texname:
                return act.map.name, texname.lower().removesuffix("preview")
        return None, None

    def update_status(self) -> None:
        roster = bs.get_game_roster()
        connection_info = bs.get_connection_to_host_info(
        ) if build_number < 21727 else bs.get_connection_to_host_info_2()

        self.rpc_thread.large_image_key = "bombsquadicon"
        self.rpc_thread.large_image_text = "BombSquad"
        self.rpc_thread.small_image_key = _babase.app.classic.platform
        self.rpc_thread.small_image_text = (
            f"{_babase.app.classic.platform.capitalize()}({APP_VERSION})"
        )
        if not ANDROID:
            svinfo = str(connection_info)
            if self._last_server_info != svinfo:
                self._last_server_info = svinfo
                self.rpc_thread.party_id = str(uuid.uuid4())
                self.rpc_thread._update_secret()
        if connection_info:
            servername = connection_info.name
            self.rpc_thread.details = "Online"
            self.rpc_thread.party_size = max(
                1, sum(len(client["players"]) for client in roster)
            )
            self.rpc_thread.party_max = max(8, self.rpc_thread.party_size)
            if len(servername) == 19 and "Private Party" in servername:
                self.rpc_thread.state = "Private Party"
            elif servername == "":  # A local game joinable from the internet
                try:
                    offlinename = json.loads(bs.get_game_roster()[0]["spec_string"])[
                        "n"
                    ]
                    if len(offlinename) > 19:  # Thanks Rikko
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

        if not connection_info:
            self.rpc_thread.details = "Local"  # ! replace with something like ballistica github cause
            self.rpc_thread.state = self._get_current_activity_name()
            self.rpc_thread.party_size = max(1, len(roster))
            self.rpc_thread.party_max = max(1, bs.get_public_party_max_size())

            if (
                bs.get_foreground_host_session() is not None
                and self.rpc_thread.details == "Local"
            ):
                session = (
                    bs.get_foreground_host_session()
                    .__class__.__name__.replace("MainMenuSession", "")
                    .replace("EndSession", "")
                    .replace("FreeForAllSession", ": FFA")  # ! for session use small image key
                    .replace("DualTeamSession", ": Teams")
                    .replace("CoopSession", ": Coop")
                )
                #! self.rpc_thread.small_image_key = session.lower()
                self.rpc_thread.details = f"{self.rpc_thread.details} {session}"
            if (
                self.rpc_thread.state == "NoneType"
            ):  # sometimes the game just breaks which means its not really watching replay FIXME
                self.rpc_thread.state = "Watching Replay"
                self.rpc_thread.large_image_key = "replay"
                self.rpc_thread.large_image_text = "Viewing Awesomeness"
                #!self.rpc_thread.small_image_key = "replaysmall"

            act = bs.get_foreground_host_activity()
            session = bs.get_foreground_host_session()
            if act:
                from bascenev1lib.game.elimination import EliminationGame
                from bascenev1lib.game.thelaststand import TheLastStandGame
                from bascenev1lib.game.meteorshower import MeteorShowerGame

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
                    with act.context:
                        sec = bs.time() - act._timer.getstarttime()
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
                with open(DIRPATH, 'r') as asset_dict:
                    asset_keys = json.load(asset_dict).keys()
                if short_map_name in asset_keys:
                    self.rpc_thread.large_image_text = mapname
                    self.rpc_thread.large_image_key = short_map_name
                    self.rpc_thread.small_image_key = 'bombsquadlogo2'
                    self.rpc_thread.small_image_text = 'BombSquad'

        if _babase.get_idle_time() / (1000 * 60) % 60 >= 0.4:
            self.rpc_thread.details = f"AFK in {self.rpc_thread.details}"
            if not ANDROID:
                self.rpc_thread.large_image_key = (
                    "https://media.tenor.com/uAqNn6fv7x4AAAAM/bombsquad-spaz.gif"
                )
        if ANDROID and Path(f"{_babase.app.env.python_directory_user}/__pycache__/token.txt").exists():
            self.rpc_thread.presence()
