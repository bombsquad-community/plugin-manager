# ba_meta require api 7
"Made to you by @brostos & @Dliwk"

token = "paste-your-token-here"

from urllib.request import Request, urlopen , urlretrieve
from pathlib import Path

#installing websocket-client
def get_module():
    import os 
    import zipfile
    install_path = Path(f"{os.getcwd()}/ba_data/python") #For the guys like me on windows
    path = Path(f"{install_path}/websocket.zip")
    if not os.path.exists(f"{install_path}/websocket"):
        url = "https://github.com/brostosjoined/BombsquadRPC/releases/download/presence-1.0/websocket.zip"
        filename, headers = urlretrieve(url, filename = path)
        with zipfile.ZipFile(path) as f:
            f.extractall(install_path)
        os.remove(path)
get_module()

import threading
import time
import json
import uuid
import websocket
import ba
import _ba


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Tuple



heartbeat_interval = int(41250)
resume_gateway_url: str | None = None
session_id: str | None = None

start_time=time.time()
class Presence_update:
    def __init__(self):
        self.state: str | None = "In Game"
        self.details: str | None = "Main Menu"
        self.start_timestamp = time.time()
        self.large_image_key: str | None = "bombsquadicon"
        self.large_image_text: str | None = "BombSquad Icon"
        self.small_image_key: str | None = None
        self.small_image_text: str | None = (f"{_ba.app.platform.capitalize()}({_ba.app.version})")
        self.media_proxy = "mp:/app-assets/963434684669382696/{}.png"
        self.identify : bool = False
        self.party_id: str = str(uuid.uuid4())
        self.party_size = 1
        self.party_max = 8
    

    def presence(self):
        with open(dirpath, "r") as maptxt:
            largetxt = json.load(maptxt)[self.large_image_key]
        with open(dirpath, "r") as maptxt:
            smalltxt = json.load(maptxt)[self.small_image_key]
        presencepayload = {
            "op": 3,
            "d": {
                "since": None, #used to show how long the user went idle will add afk to work with this and then set the status to idle 
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
    #print("### closed ###")
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


dirpath = Path(f"{_ba.app.python_directory_user}/image_id.json")
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
    except:
        pass
    
    with open(dirpath, "w") as imagesets:
        jsonfile = json.dumps(asset_id_dict, indent=4)
        json.dump(asset_id_dict, imagesets)
    run_once = True



# ba_meta export plugin
class DiscordRP(ba.Plugin):
    def __init__(self) -> None:
        self.update_timer: ba.Timer | None = None
        self.presence_update = Presence_update()
        get_once_asset()
        

    def on_app_running(self) -> None:
        self.presence_update.start_timestamp = time.mktime(time.localtime())    
        self.update_timer = ba.Timer(
            4, ba.WeakCall(self.update_status), timetype=ba.TimeType.REAL, repeat=True
        )

    def on_app_shutdown(self) -> None:
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
            self.presence_update.large_image_key = "lobby"
            self.presence_update.large_image_text = "Bombing up"
        if name == "Ranking":
            self.presence_update.large_image_key = "ranking"
            self.presence_update.large_image_text = "Viewing Results"
        return name

    def _get_current_map_name(self) -> tuple[str | None, str | None]:
        act = _ba.get_foreground_host_activity()

        if isinstance(act, ba.GameActivity):
            texname = act.map.get_preview_texture_name()
            if texname:
                return act.map.name, texname.lower().removesuffix("preview")
        return None, None

    def update_status(self) -> None:

        roster = _ba.get_game_roster()
        connection_info = _ba.get_connection_to_host_info()
        

        self.presence_update.large_image_key = "bombsquadicon" #todo check if this block is needed
        self.presence_update.large_image_text = "BombSquad"
        self.presence_update.small_image_key = _ba.app.platform
        self.presence_update.small_image_text = (
            f"{_ba.app.platform.capitalize()}({_ba.app.version})"
        )

        if connection_info != {}:
            servername = connection_info["name"]
            self.presence_update.details = "Online"
            self.presence_update.party_size = max(
                1, sum(len(client["players"]) for client in roster)
            )
            self.presence_update.party_max = max(8, self.presence_update.party_size)

            if len(servername) == 19 and "Private Party" in servername:
                self.presence_update.state = "Private Party"
            elif servername == "":  # A local game joinable from the internet
                try:
                    offlinename = json.loads(_ba.get_game_roster()[0]["spec_string"])[
                        "n"
                    ]
                    if len(offlinename > 19):
                        self.presence_update.state = offlinename[slice(19)] + "..."
                    else:
                        self.presence_update.state = offlinename
                except IndexError:
                    pass
            else:
                if len(servername) > 19:
                    self.presence_update.state = servername[slice(19)] + "..."
                else:
                    self.presence_update.state = servername[slice(19)]
        if connection_info == {}:
            self.presence_update.party_size = max(1, len(roster))
            self.presence_update.party_max = max(1, _ba.get_public_party_max_size())
            self.presence_update.details = "Local"
            self.presence_update.state = self._get_current_activity_name()

            if (
                _ba.get_foreground_host_session() is not None
                and self.presence_update.details == "Local"
            ):
                session = (
                    _ba.get_foreground_host_session()
                    .__class__.__name__.replace("MainMenuSession", "")
                    .replace("EndSession", "")
                    .replace("FreeForAllSession", ": FFA")
                    .replace("DualTeamSession", ": Teams")
                    .replace("CoopSession", ": Coop")
                )
                self.presence_update.details = (
                    f"{self.presence_update.details} {session}"
                )
            if self.presence_update.state == "NoneType":
                self.presence_update.state = "Watching Replay"
                self.presence_update.large_image_key = "replay"
                self.presence_update.large_image_text = "Viewing Awesomeness"

            act = _ba.get_foreground_host_activity()
            if act:
                from bastd.game.elimination import EliminationGame
                from bastd.game.thelaststand import TheLastStandGame
                from bastd.game.meteorshower import MeteorShowerGame

                # noinspection PyUnresolvedReferences,PyProtectedMember
                try:#todo fixme use appropriate name
                    self.presence_update.start_timestamp = act._discordrp_start_time  # type: ignore
                except AttributeError:
                    # This can be the case if plugin launched AFTER activity
                    # has been created; in that case let's assume it was
                    # created just now.
                    self.presence_update.start_timestamp = act._discordrp_start_time = time.mktime(  # type: ignore
                        time.localtime()
                    )
                if isinstance(act, EliminationGame):
                    alive_count = len([p for p in act.players if p.lives > 0])
                    self.presence_update.details += f" ({alive_count} players left)"
                elif isinstance(act, TheLastStandGame):
                    # noinspection PyProtectedMember
                    points = act._score
                    self.presence_update.details += f" ({points} points)"
                elif isinstance(act, MeteorShowerGame):
                    with ba.Context(act):
                        sec = ba.time() - act._timer.getstarttime()
                    secfmt = ""
                    if sec < 60:
                        secfmt = f"{sec:.2f}"
                    else:
                        secfmt = f"{int(sec) // 60:02}:{sec:.2f}"
                    self.presence_update.details += f" ({secfmt})"

                # if isinstance(session, ba.DualTeamSession):
                #     scores = ':'.join([
                #         str(t.customdata['score'])
                #         for t in session.sessionteams
                #     ])
                #     self.presence_update.details += f' ({scores})'

            mapname, short_map_name = self._get_current_map_name()
            if mapname:
                self.presence_update.large_image_text = mapname
                self.presence_update.large_image_key = short_map_name
                self.presence_update.small_image_key = "bombsquadlogo2"
                self.presence_update.small_image_text = "BombSquad"

        if _ba.get_idle_time() / (1000 * 60) % 60 >= 0.2:
            self.presence_update.details = f"AFK in {self.presence_update.details}"
            # self.presence_update.large_image_key = (
            #     "mp:external/btl_oZF6BdUjijINOnrf9hw0_nCrwsHYJoJKEZKKye8/https/media.tenor.com/uAqNn6fv7x4AAAAM/bombsquad-spaz.gif"
            # )
        self.presence_update.presence()
