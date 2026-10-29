# Porting made easier by baport.(https://github.com/bombsquad-community/baport)
# -*- coding: utf-8 -*-
# ba_meta require api 9
'''
Server Switch Plugin by My.Smoothy
Let you switch recently joined servers very quickly
+ Added button to quicky look into public server list without leaving current game.

discord: mr.smoothy
https://discord.gg/ucyaesh 
Youtube : Hey Smoothy
Download more mods from 
https://bombsquad-community.web.app/mods
'''
import babase
from bauiv1lib.ingamemenu import InGameMenuWindow
import bauiv1 as bui
import bascenev1 as bs


plugman = dict(
    plugin_name='server_switch',
    description='Let you switch between recents servers',
    external_url='https://www.youtube.com/watch?v=QrES1jQGXF0',
    authors=[
        {'name': 'Mr.Smoothy', 'email': '', 'discord': 'mr.smoothy', 'github': 'imayushsaini'},
    ],
    version='2.1.0',
)
current_server_ip = "127.0.0.1"
current_server_port = 43210
servers = []


def _refresh_in_game(func):
    def wrapper(self, *args, **kwargs):
        returnValue = func(self, *args, **kwargs)
        uiscale = bui.app.ui_v1.uiscale
        bui.containerwidget(
            edit=self._root_widget,
            size=(self._width*2, self._height),  # double the width
            scale=(
                2.15
                if uiscale is bui.UIScale.SMALL
                else 1.6
                if uiscale is bui.UIScale.MEDIUM
                else 1.0
            ),
        )
        h = 125
        v = self._height - 60.0
        bui.textwidget(
            parent=self._root_widget,
            draw_controller=None,
            text="IP: "+current_server_ip+"  PORT: "+str(current_server_port),
            position=(h-self._button_width/2 + 130, v+60),
            h_align='center',
            v_align='center',
            size=(20, 60),
            scale=0.6)
        self._public_servers = bui.buttonwidget(
            color=(0.8, 0.45, 1),
            parent=self._root_widget,
            position=(h+self._button_width-10, v+60+20),
            size=(self._button_width/4, self._button_height/2),
            scale=1.0,
            autoselect=self._use_autoselect,
            label="~~~",
            on_activate_call=bs.CallPartial(public_servers, self))
        for server in servers:
            self._server_button = bui.buttonwidget(
                color=(0.8, 0, 1),
                parent=self._root_widget,
                position=((h - self._button_width / 2) + self._button_width + 20, v),
                size=(self._button_width, self._button_height),
                scale=1.0,
                autoselect=self._use_autoselect,
                label=server["name"][0:22],
                on_activate_call=bs.CallPartial(bs.connect_to_party, server["ip"], server["port"]))

            v -= 50

        return returnValue
    return wrapper


connect = bs.connect_to_party


def connect_to_party(address, port=43210, print_progress=False):
    global current_server_ip
    global current_server_port
    if (bs.get_connection_to_host_info() != {}):
        bs.disconnect_from_host()
    current_server_ip = address
    current_server_port = port
    connect(address, port, print_progress)
    babase.apptimer(1, check_connect_status)


def check_connect_status():
    global servers
    global current_server_ip
    global current_server_port
    if (bs.get_connection_to_host_info() != {}):
        if (not bs.get_connection_to_host_info()['name']):
            babase.apptimer(1, check_connect_status)
            return
        new_server = {"name":  bs.get_connection_to_host_info(
        )['name'], "ip": current_server_ip, "port": current_server_port}
        if new_server not in servers:
            servers.append(new_server)
            servers = servers[-3:]
    else:
        print("connection failed falling back to gather window")
        public_servers()


def public_servers(window=None):
    from bauiv1lib.gather import GatherWindow
    if window is None:
        window = bui.app.ui_v1.get_main_window()
    if window is not None:
        if not isinstance(window, GatherWindow) and window.main_window_has_control():
            window.main_window_replace(lambda: GatherWindow())
    else:
        bui.app.ui_v1.set_main_window(
            GatherWindow(), is_top_level=True, back_state=None, suppress_warning=True)

# ba_meta export babase.Plugin


class bySmoothy(babase.Plugin):
    def __init__(self):
        InGameMenuWindow._refresh_in_game = _refresh_in_game(
            InGameMenuWindow._refresh_in_game)
        bs.connect_to_party = connect_to_party
