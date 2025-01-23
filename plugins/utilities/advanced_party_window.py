# -*- coding: utf-8 -*-
# ba_meta require api 9
'''
AdvancedPartyWindow by Mr.Smoothy

Updated to API 8 on 2nd July 2023 by Mr.Smoothy

build on base of plasma's modifypartywindow

discord mr.smoothy#5824

https://discord.gg/ucyaesh 


Youtube : Hey Smoothy

Download more mods from 
https://bombsquad-community.web.app/mods

'''

#  added advanced ID revealer
# live ping

# Made by Mr.Smoothy - Plasma Boson
import traceback
import codecs
import json
import re
import sys
import shutil
import copy
import urllib
import os
from bauiv1lib.account import viewer
from bauiv1lib.popup import PopupMenuWindow, PopupWindow
from babase._general import Call
import base64
import datetime
import ssl
import bauiv1lib.party as bascenev1lib_party
from typing import List, Sequence, Optional, Dict, Any, Union
from bauiv1lib.colorpicker import ColorPickerExact
from bauiv1lib.confirm import ConfirmWindow
from dataclasses import dataclass
import math
import time
import babase
import bauiv1 as bui
import bascenev1 as bs
import _babase
from typing import TYPE_CHECKING, cast
import urllib.request
import urllib.parse
from _thread import start_new_thread
import threading
version_str = "7"
BCSSERVER = 'mods.ballistica.workers.dev'

cache_chat = []
connect = bs.connect_to_party
disconnect = bs.disconnect_from_host
unmuted_names = []
smo_mode = 3
f_chat = False
chatlogger = False
screenmsg = True
ip_add = "127.0.0.1"
p_port = 43210
p_name = "local"
current_ping = 0.0
enable_typing = False    # this will prevent auto ping to update textwidget when user actually typing chat message
ssl._create_default_https_context = ssl._create_unverified_context


def newconnect_to_party(address, port=43210, print_progress=False):
    global ip_add
    global p_port
    bs.chatmessage(" Joined IP "+ip_add+" PORT "+str(p_port))
    dd = bs.get_connection_to_host_info()
    if dd.get('name', '') != '':
        title = dd['name']
        bs.chatmessage(title)
    if (dd != {}):
        bs.disconnect_from_host()

        ip_add = address
        p_port = port
        connect(address, port, print_progress)
    else:
        ip_add = address
        p_port = port
        # print(ip_add,p_port)
        connect(ip_add, port, print_progress)


DEBUG_SERVER_COMMUNICATION = False
DEBUG_PROCESSING = False


class PingThread(threading.Thread):
    """Thread for sending out game pings."""

    def __init__(self):
        super().__init__()

    def run(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        bui.app.classic.ping_thread_count += 1
        sock: Optional[socket.socket] = None
        try:
            import socket
            from babase._net import get_ip_address_type
            socket_type = get_ip_address_type(ip_add)
            sock = socket.socket(socket_type, socket.SOCK_DGRAM)
            sock.connect((ip_add, p_port))

            accessible = False
            starttime = time.time()

            # Send a few pings and wait a second for
            # a response.
            sock.settimeout(1)
            for _i in range(3):
                sock.send(b'\x0b')
                result: Optional[bytes]
                try:
                    # 11: BA_PACKET_SIMPLE_PING
                    result = sock.recv(10)
                except Exception:
                    result = None
                if result == b'\x0c':
                    # 12: BA_PACKET_SIMPLE_PONG
                    accessible = True
                    break
                time.sleep(1)
            ping = (time.time() - starttime) * 1000.0
            global current_ping
            current_ping = round(ping, 2)
        except ConnectionRefusedError:
            # Fine, server; sorry we pinged you. Hmph.
            pass
        except OSError as exc:
            import errno

            # Ignore harmless errors.
            if exc.errno in {
                    errno.EHOSTUNREACH, errno.ENETUNREACH, errno.EINVAL,
                    errno.EPERM, errno.EACCES
            }:
                pass
            elif exc.errno == 10022:
                # Windows 'invalid argument' error.
                pass
            elif exc.errno == 10051:
                # Windows 'a socket operation was attempted
                # to an unreachable network' error.
                pass
            elif exc.errno == errno.EADDRNOTAVAIL:
                if self._port == 0:
                    # This has happened. Ignore.
                    pass
                elif babase.do_once():
                    print(f'Got EADDRNOTAVAIL on gather ping'
                          f' for addr {self._address}'
                          f' port {self._port}.')
            else:
                babase.print_exception(
                    f'Error on gather ping '
                    f'(errno={exc.errno})', once=True)
        except Exception:
            babase.print_exception('Error on gather ping', once=True)
        finally:
            try:
                if sock is not None:
                    sock.close()
            except Exception:
                babase.print_exception('Error on gather ping cleanup', once=True)

        bui.app.classic.ping_thread_count -= 1
        time.sleep(4)
        self.run()


RecordFilesDir = os.path.join(_babase.env()["python_directory_user"], "Configs" + os.sep)
if not os.path.exists(RecordFilesDir):
    os.makedirs(RecordFilesDir)

version_str = "3.0.1"

Current_Lang = None

SystemEncode = sys.getfilesystemencoding()
if not isinstance(SystemEncode, str):
    SystemEncode = "utf-8"


PingThread().start()


class chatloggThread():
    """Thread for sending out game pings."""

    def __init__(self):
        super().__init__()
        self.saved_msg = []

    def run(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        global chatlogger
        self.timerr = babase.AppTimer(5.0, self.chatlogg, repeat=True)

    def chatlogg(self):
        global chatlogger
        chats = bs.get_chat_messages()
        for msg in chats:
            if msg in self.saved_msg:
                pass
            else:
                self.save(msg)
                self.saved_msg.append(msg)
                if len(self.saved_msg) > 45:
                    self.saved_msg.pop(0)
        if chatlogger:
            pass
        else:
            self.timerr = None

    def save(self, msg):
        x = str(datetime.datetime.now())
        t = open(os.path.join(_babase.env()["python_directory_user"], "Chat logged.txt"), "a+")
        t.write(x+" : " + msg + "\n")
        t.close()


class mututalServerThread():
    def run(self):
        self.timer = babase.AppTimer(10, self.checkPlayers, repeat=True)

    def checkPlayers(self):
        if bs.get_connection_to_host_info() != {}:
            server_name = bs.get_connection_to_host_info()["name"]
            players = []
            for ros in bs.get_game_roster():
                players.append(ros["display_string"])
            start_new_thread(dump_mutual_servers, (players, server_name,))


def dump_mutual_servers(players, server_name):
    filePath = os.path.join(RecordFilesDir, "players.json")
    data = {}
    if os.path.isfile(filePath):
        f = open(filePath, "r")
        data = json.load(f)
    for player in players:
        if player in data:
            if server_name not in data[player]:
                data[player].insert(0, server_name)
                data[player] = data[player][:3]
        else:
            data[player] = [server_name]
    f = open(filePath, "w")
    json.dump(data, f)


mututalServerThread().run()


class customchatThread():
    """."""

    def __init__(self):
        super().__init__()
        global cache_chat
        self.saved_msg = []
        try:
            chats = bs.get_chat_messages()
            for msg in chats:  # fill up old  chat , to avoid old msg popup
                cache_chat.append(msg)
        except:
            pass

    def run(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        global chatlogger
        self.timerr = babase.AppTimer(5.0, self.chatcheck, repeat=True)

    def chatcheck(self):
        global unmuted_names
        global cache_chat
        try:
            chats = bs.get_chat_messages()
        except:
            chats = []
        for msg in chats:
            if msg in cache_chat:
                pass
            else:
                if msg.split(":")[0] in unmuted_names:
                    bs.broadcastmessage(msg, color=(0.6, 0.9, 0.6))
                cache_chat.append(msg)
                if len(self.saved_msg) > 45:
                    cache_chat.pop(0)
            if babase.app.config.resolve('Chat Muted'):
                pass
            else:
                self.timerr = None


def chatloggerstatus():
    global chatlogger
    if chatlogger:
        return "Turn off Chat Logger"
    else:
        return "Turn on chat logger"


def _getTransText(text, isBaLstr=False, same_fb=False):
    global Current_Lang
    global chatlogger
    if Current_Lang != 'English':
        Current_Lang = 'English'
        global Language_Texts
        Language_Texts = {
            "Chinese": {

            },
            "English": {
                "Add_a_Quick_Reply": "Add a Quick Reply",
                "Admin_Command_Kick_Confirm": "Are you sure to use admin\
command to kick %s?",
                "Ban_For_%d_Seconds": "Ban for %d second(s).",
                "Ban_Time_Post": "Enter the time you want to ban(Seconds).",
                "Credits_for_This": "Credits for This",
                                    "Custom_Action": "Custom Action",
                                    "Debug_for_Host_Info": "Host Info Debug",
                                    "Game_Record_Saved": "Game replay %s is saved.",
                                    "Kick_ID": "Kick ID:%d",
                                    "Mention_this_guy": "Mention this guy",
                                    "Modify_Main_Color": "Modify Main Color",
                                    "No_valid_player_found": "Can't find a valid player.",
                                    "No_valid_player_id_found": "Can't find a valid player ID.",
                                    "Normal_kick_confirm": "Are you sure to kick %s?",
                                    "Remove_a_Quick_Reply": "Remove a Quick Reply",
                                    "Restart_Game_Record": "Save Recording",
                                    "Restart_Game_Record_Confirm": "Are you sure to restart recording game stream?",
                                    "Send_%d_times": "Send for %d times",
                                    "Something_is_added": "'%s' is added.",
                                    "Something_is_removed": "'%s' is removed.",
                                    "Times": "Times",
                                    "Translator": "Translator",
                                    "chatloggeroff": "Turn off Chat Logger",
                                    "chatloggeron": "Turn on Chat Logger",
                                    "screenmsgoff": "Hide ScreenMessage",
                                    "screenmsgon": "Show ScreenMessage",
                                    "unmutethisguy": "unmute this guy",
                                    "mutethisguy": "mute this guy",
                                    "muteall": "Mute all",
                                    "unmuteall": "Unmute all",
                                    "copymsg": "copy"

            }
        }

        Language_Texts = Language_Texts.get(Current_Lang)
        try:
            from Language_Packs import ModifiedPartyWindow_LanguagePack as ext_lan_pack
            if isinstance(ext_lan_pack, dict) and isinstance(ext_lan_pack.get(Current_Lang), dict):
                complete_Pack = ext_lan_pack.get(Current_Lang)
                for key, item in complete_Pack.items():
                    Language_Texts[key] = item
        except:
            pass

    return (Language_Texts.get(text, "#Unknown Text#" if not same_fb else text) if not isBaLstr else
            babase.Lstr(resource="??Unknown??", fallback_value=Language_Texts.get(text, "#Unknown Text#" if not same_fb else text)))


def _get_popup_window_scale() -> float:
    uiscale = bui.app.ui_v1.uiscale
    return (2.3 if uiscale is babase.UIScale.SMALL else
            1.65 if uiscale is babase.UIScale.MEDIUM else 1.23)


def _creat_Lstr_list(string_list: list = []) -> list:
    return ([babase.Lstr(resource="??Unknown??", fallback_value=item) for item in string_list])


customchatThread().run()


class ModifiedPartyWindow(bascenev1lib_party.PartyWindow):
    def __init__(self, origin: Sequence[float] = (0, 0)):
        bui.set_party_window_open(True)
        self._r = 'partyWindow'
        self.msg_user_selected = ''
        self._popup_type: Optional[str] = None
        self._popup_party_member_client_id: Optional[int] = None
        self._popup_party_member_is_host: Optional[bool] = None
        self._width = 500

        uiscale = bui.app.ui_v1.uiscale
        self._height = (365 if uiscale is babase.UIScale.SMALL else
                        480 if uiscale is babase.UIScale.MEDIUM else 600)

        # Custom color here
        self._bg_color = babase.app.config.get("PartyWindow_Main_Color", (0.40, 0.55, 0.20)) if not isinstance(
            self._getCustomSets().get("Color"), (list, tuple)) else self._getCustomSets().get("Color")
        if not isinstance(self._bg_color, (list, tuple)) or not len(self._bg_color) == 3:
            self._bg_color = (0.40, 0.55, 0.20)

        bui.Window.__init__(self, root_widget=bui.containerwidget(
            size=(self._width, self._height),
            transition='in_scale',
            color=self._bg_color,
            parent=bui.get_special_widget('overlay_stack'),
            on_outside_click_call=self.close_with_sound,
            scale_origin_stack_offset=origin,
            scale=(2.0 if uiscale is babase.UIScale.SMALL else
                   1.35 if uiscale is babase.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -10) if uiscale is babase.UIScale.SMALL else (
                240, 0) if uiscale is babase.UIScale.MEDIUM else (330, 20)))

        self._cancel_button = bui.buttonwidget(parent=self._root_widget,
                                               scale=0.7,
                                               position=(30, self._height - 47),
                                               size=(50, 50),
                                               label='',
                                               on_activate_call=self.close,
                                               autoselect=True,
                                               color=(0.45, 0.63, 0.15),
                                               icon=bui.gettexture('crossOut'),
                                               iconscale=1.2)
        self._smoothy_button = bui.buttonwidget(parent=self._root_widget,
                                                scale=0.6,
                                                position=(5, self._height - 47 - 40),
                                                size=(50, 50),
                                                label='69',
                                                on_activate_call=self.smoothy_roster_changer,
                                                autoselect=True,
                                                color=(0.45, 0.63, 0.15),
                                                icon=bui.gettexture('replayIcon'),
                                                iconscale=1.2)
        bui.containerwidget(edit=self._root_widget,
                            cancel_button=self._cancel_button)

        self._menu_button = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(self._width - 60, self._height - 47),
            size=(50, 50),
            label="\xee\x80\x90",
            autoselect=True,
            button_type='square',
            on_activate_call=bs.WeakCall(self._on_menu_button_press),
            color=(0.55, 0.73, 0.25),
            icon=bui.gettexture('menuButton'),
            iconscale=1.2)

        info = bs.get_connection_to_host_info()
        if info.get('name', '') != '':
            title = info['name']
        else:
            title = babase.Lstr(resource=self._r + '.titleText')

        self._title_text = bui.textwidget(parent=self._root_widget,
                                          scale=0.9,
                                          color=(0.5, 0.7, 0.5),
                                          text=title,
                                          size=(120, 20),
                                          position=(self._width * 0.5-60,
                                                    self._height - 29),
                                          on_select_call=self.title_selected,
                                          selectable=True,
                                          maxwidth=self._width * 0.7,
                                          h_align='center',
                                          v_align='center')

        self._empty_str = bui.textwidget(parent=self._root_widget,
                                         scale=0.75,
                                         size=(0, 0),
                                         position=(self._width * 0.5,
                                                   self._height - 65),
                                         maxwidth=self._width * 0.85,
                                         text="no one",
                                         h_align='center',
                                         v_align='center')

        self._scroll_width = self._width - 50
        self._scrollwidget = bui.scrollwidget(parent=self._root_widget,
                                              size=(self._scroll_width,
                                                    self._height - 200),
                                              position=(30, 80),
                                              color=(0.4, 0.6, 0.3))
        self._columnwidget = bui.columnwidget(parent=self._scrollwidget,
                                              border=2,
                                              left_border=-200,
                                              margin=0)
        bui.widget(edit=self._menu_button, down_widget=self._columnwidget)

        self._muted_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text="")
        self._chat_texts: List[bui.Widget] = []
        self._chat_texts_haxx: List[bui.Widget] = []

        # add all existing messages if chat is not muted
        # print("updates")
        if True:  # smoothy - always show chat in partywindow
            msgs = bs.get_chat_messages()
            for msg in msgs:
                self._add_msg(msg)
                # print(msg)
        # else:
        #   msgs=_babase.get_chat_messages()
        #   for msg in msgs:
        #     print(msg);
        #     txt = bui.textwidget(parent=self._columnwidget,
        #                         text=msg,
        #                         h_align='left',
        #                         v_align='center',
        #                         size=(0, 13),
        #                         scale=0.55,
        #                         maxwidth=self._scroll_width * 0.94,
        #                         shadow=0.3,
        #                         flatness=1.0)
            # self._chat_texts.append(txt)
            # if len(self._chat_texts) > 40:
            #     first = self._chat_texts.pop(0)
            #     first.delete()
            # bui.containerwidget(edit=self._columnwidget, visible_child=txt)
        self.ping_widget = txt = bui.textwidget(
            parent=self._root_widget,
            scale=0.6,
            size=(20, 5),
            color=(0.45, 0.63, 0.15),
            position=(self._width/2 - 20, 50),
            text="Ping:"+str(current_ping)+" ms",
            selectable=True,
            autoselect=False,
            v_align='center')
        _babase.ping_widget = self.ping_widget

        def enable_chat_mode():
            pass

        self._text_field = txt = bui.textwidget(
            parent=self._root_widget,
            editable=True,
            size=(530-80, 40),
            position=(44+60, 39),
            text='',
            maxwidth=494,
            shadow=0.3,
            flatness=1.0,
            description=babase.Lstr(resource=self._r + '.chatMessageText'),
            autoselect=True,
            v_align='center',
            corner_scale=0.7)

        # for m in  _babase.get_chat_messages():
        #   if m:
        #     ttchat=bui.textwidget(
        #               parent=self._columnwidget,
        #               size=(10,10),
        #               h_align='left',
        #               v_align='center',
        #               text=str(m),
        #               scale=0.6,
        #               flatness=0,
        #               color=(2,2,2),
        #               shadow=0,
        #               always_highlight=True

        #               )
        bui.widget(edit=self._scrollwidget,
                   autoselect=True,
                   left_widget=self._cancel_button,
                   up_widget=self._cancel_button,
                   down_widget=self._text_field)
        bui.widget(edit=self._columnwidget,
                   autoselect=True,
                   up_widget=self._cancel_button,
                   down_widget=self._text_field)
        bui.containerwidget(edit=self._root_widget, selected_child=txt)
        btn = bui.buttonwidget(parent=self._root_widget,
                               size=(50, 35),
                               label=babase.Lstr(resource=self._r + '.sendText'),
                               button_type='square',
                               autoselect=True,
                               position=(self._width - 70, 35),
                               on_activate_call=self._send_chat_message)

        def _times_button_on_click():
            # self._popup_type = "send_Times_Press"
            # allow_range = 100 if _babase.get_foreground_host_session() is not None else 4
            # PopupMenuWindow(position=self._times_button.get_screen_space_center(),
            #                             scale=_get_popup_window_scale(),
            #                             choices=[str(index) for index in range(1,allow_range + 1)],
            #                             choices_display=_creat_Lstr_list([_getTransText("Send_%d_times")%int(index) for index in range(1,allow_range + 1)]),
            #                             current_choice="Share_Server_Info",
            #                             delegate=self)
            Quickreply = self._get_quick_responds()
            if len(Quickreply) > 0:
                PopupMenuWindow(position=self._times_button.get_screen_space_center(),
                                scale=_get_popup_window_scale(),
                                choices=Quickreply,
                                choices_display=_creat_Lstr_list(Quickreply),
                                current_choice=Quickreply[0],
                                delegate=self)
                self._popup_type = "QuickMessageSelect"

        self._send_msg_times = 1

        self._times_button = bui.buttonwidget(parent=self._root_widget,
                                              size=(50, 35),
                                              label="Quick",
                                              button_type='square',
                                              autoselect=True,
                                              position=(30, 35),
                                              on_activate_call=_times_button_on_click)

        bui.textwidget(edit=txt, on_return_press_call=btn.activate)
        self._name_widgets: List[bui.Widget] = []
        self._roster: Optional[List[Dict[str, Any]]] = None

        self.smoothy_mode = 1
        self.full_chat_mode = False
        self._update_timer = babase.AppTimer(1.0,
                                             bs.WeakCall(self._update),
                                             repeat=True)

        self._update()

    def title_selected(self):

        self.full_chat_mode = self.full_chat_mode == False
        self._update()

    def smoothy_roster_changer(self):

        self.smoothy_mode = (self.smoothy_mode+1) % 3

        self._update()

    def on_chat_message(self, msg: str) -> None:
        """Called when a new chat message comes through."""
        # print("on_chat"+msg)
        if True:
            self._add_msg(msg)

    def _copy_msg(self, msg: str) -> None:
        if bui.clipboard_is_supported():
            bui.clipboard_set_text(msg)
            bui.screenmessage(
                bui.Lstr(resource='copyConfirmText'),
                color=(0, 1, 0)
            )

    def _on_chat_press(self, msg, widget, showMute):
        global unmuted_names
        choices = ['copy']
        choices_display = [_getTransText("copymsg", isBaLstr=True)]
        if showMute:
            if msg.split(":")[0].encode('utf-8') in unmuted_names:
                choices.append('mute')
                choices_display.append(_getTransText("mutethisguy", isBaLstr=True))
            else:
                choices.append('unmute')
                choices_display.append(_getTransText("unmutethisguy", isBaLstr=True))
        PopupMenuWindow(position=widget.get_screen_space_center(),
                        scale=_get_popup_window_scale(),
                        choices=choices,
                        choices_display=choices_display,
                        current_choice="@ this guy",
                        delegate=self)
        self.msg_user_selected = msg
        self._popup_type = "chatmessagepress"

        # bs.chatmessage("pressed")

    def _add_msg(self, msg: str) -> None:
        try:
            showMute = babase.app.config.resolve('Chat Muted')
            if True:
                txt = bui.textwidget(parent=self._columnwidget,
                                     text=msg,
                                     h_align='left',
                                     v_align='center',
                                     size=(900, 13),
                                     scale=0.55,
                                     position=(-0.6, 0),
                                     selectable=True,
                                     autoselect=True,
                                     click_activate=True,
                                     maxwidth=self._scroll_width * 0.94,
                                     shadow=0.3,
                                     flatness=1.0)
                bui.textwidget(edit=txt,
                               on_activate_call=babase.Call(
                                   self._on_chat_press,
                                   msg, txt, showMute))

          # btn = bui.buttonwidget(parent=self._columnwidget,
          #                       scale=0.7,
          #                       size=(100,20),
          #                       label="smoothy buttin",
          #                       icon=bs.gettexture('replayIcon'),
          #                       texture=None,
          #                       )
            self._chat_texts_haxx.append(txt)
            if len(self._chat_texts_haxx) > 40:
                first = self._chat_texts_haxx.pop(0)
                first.delete()
            bui.containerwidget(edit=self._columnwidget, visible_child=txt)
        except Exception:
            pass

    def _add_msg_when_muted(self, msg: str) -> None:

        txt = bui.textwidget(parent=self._columnwidget,
                             text=msg,
                             h_align='left',
                             v_align='center',
                             size=(0, 13),
                             scale=0.55,
                             maxwidth=self._scroll_width * 0.94,
                             shadow=0.3,
                             flatness=1.0)
        self._chat_texts.append(txt)
        if len(self._chat_texts) > 40:
            first = self._chat_texts.pop(0)
            first.delete()
        bui.containerwidget(edit=self._columnwidget, visible_child=txt)

    def color_picker_closing(self, picker) -> None:
        babase._appconfig.commit_app_config()

    def color_picker_selected_color(self, picker, color) -> None:
        # bs.animateArray(self._root_widget,"color",3,{0:self._bg_color,1500:color})
        bui.containerwidget(edit=self._root_widget, color=color)
        self._bg_color = color
        babase.app.config["PartyWindow_Main_Color"] = color

    def _on_nick_rename_press(self, arg) -> None:

        bui.containerwidget(edit=self._root_widget, transition='out_scale')
        c_width = 600
        c_height = 250
        uiscale = bui.app.ui_v1.uiscale
        self._nick_rename_window = cnt = bui.containerwidget(

            scale=(1.8 if uiscale is babase.UIScale.SMALL else
                   1.55 if uiscale is babase.UIScale.MEDIUM else 1.0),
            size=(c_width, c_height),
            transition='in_scale')

        bui.textwidget(parent=cnt,
                       size=(0, 0),
                       h_align='center',
                       v_align='center',
                       text='Enter nickname',
                       maxwidth=c_width * 0.8,
                       position=(c_width * 0.5, c_height - 60))
        id = self._get_nick(arg)
        self._player_nick_text = txt89 = bui.textwidget(
            parent=cnt,
            size=(c_width * 0.8, 40),
            h_align='left',
            v_align='center',
            text=id,
            editable=True,
            description='Players nick name',
            position=(c_width * 0.1, c_height - 140),
            autoselect=True,
            maxwidth=c_width * 0.7,
            max_chars=200)
        cbtn = bui.buttonwidget(
            parent=cnt,
            label=babase.Lstr(resource='cancelText'),
            on_activate_call=babase.Call(
                lambda c: bui.containerwidget(edit=c, transition='out_scale'),
                cnt),
            size=(180, 60),
            position=(30, 30),
            autoselect=True)
        okb = bui.buttonwidget(parent=cnt,
                               label='Rename',
                               size=(180, 60),
                               position=(c_width - 230, 30),
                               on_activate_call=babase.Call(
                                   self._add_nick, arg),
                               autoselect=True)
        bui.widget(edit=cbtn, right_widget=okb)
        bui.widget(edit=okb, left_widget=cbtn)
        bui.textwidget(edit=txt89, on_return_press_call=okb.activate)
        bui.containerwidget(edit=cnt, cancel_button=cbtn, start_button=okb)

    def _add_nick(self, arg):
        config = babase.app.config
        new_name_raw = cast(str, bui.textwidget(query=self._player_nick_text))
        if arg:
            if not isinstance(config.get('players nick'), dict):
                config['players nick'] = {}
            config['players nick'][arg] = new_name_raw
            config.commit()
        bui.containerwidget(edit=self._nick_rename_window,
                            transition='out_scale')
        # bui.containerwidget(edit=self._root_widget,transition='in_scale')

    def _get_nick(self, id):
        config = babase.app.config
        if not isinstance(config.get('players nick'), dict):
            return "add nick"
        elif id in config['players nick']:
            return config['players nick'][id]
        else:
            return "add nick"

    def _reset_game_record(self) -> None:
        try:
            dir_path = _babase.get_replays_dir()
            curFilePath = os.path.join(dir_path+os.sep, "__lastReplay.brp").encode(SystemEncode)
            newFileName = str(babase.Lstr(resource="replayNameDefaultText").evaluate(
            )+" (%s)" % (datetime.datetime.strftime(datetime.datetime.now(), "%Y_%m_%d_%H_%M_%S"))+".brp")
            newFilePath = os.path.join(dir_path+os.sep, newFileName).encode(SystemEncode)
            # print(curFilePath, newFilePath)
            # os.rename(curFilePath,newFilePath)
            shutil.copyfile(curFilePath, newFilePath)
            bs.broadcastmessage(_getTransText("Game_Record_Saved") % newFileName, color=(1, 1, 1))
        except:
            babase.print_exception()
            bs.broadcastmessage(babase.Lstr(resource="replayWriteErrorText").evaluate() +
                                ""+traceback.format_exc(), color=(1, 0, 0))

    def _on_menu_button_press(self) -> None:
        is_muted = babase.app.config.resolve('Chat Muted')
        global chatlogger
        choices = ["unmute" if is_muted else "mute", "screenmsg",
                   "addQuickReply", "removeQuickReply", "chatlogger", "credits"]
        DisChoices = [_getTransText("unmuteall", isBaLstr=True) if is_muted else _getTransText("muteall", isBaLstr=True),
                      _getTransText("screenmsgoff", isBaLstr=True) if screenmsg else _getTransText(
                          "screenmsgon", isBaLstr=True),

                      _getTransText("Add_a_Quick_Reply", isBaLstr=True),
                      _getTransText("Remove_a_Quick_Reply", isBaLstr=True),
                      _getTransText("chatloggeroff", isBaLstr=True) if chatlogger else _getTransText(
                          "chatloggeron", isBaLstr=True),
                      _getTransText("Credits_for_This", isBaLstr=True)
                      ]

        choices.append("resetGameRecord")
        DisChoices.append(_getTransText("Restart_Game_Record", isBaLstr=True))
        if self._getCustomSets().get("Enable_HostInfo_Debug", False):
            choices.append("hostInfo_Debug")
            DisChoices.append(_getTransText("Debug_for_Host_Info", isBaLstr=True))

        PopupMenuWindow(
            position=self._menu_button.get_screen_space_center(),
            scale=_get_popup_window_scale(),
            choices=choices,
            choices_display=DisChoices,
            current_choice="unmute" if is_muted else "mute", delegate=self)
        self._popup_type = "menu"

    def _on_party_member_press(self, client_id: int, is_host: bool,
                               widget: bui.Widget) -> None:
        # if we"re the host, pop up "kick" options for all non-host members
        if bs.get_foreground_host_session() is not None:
            kick_str = babase.Lstr(resource="kickText")
        else:
            kick_str = babase.Lstr(resource="kickVoteText")
        choices = ["kick", "@ this guy", "info", "adminkick"]

        choices_display = [kick_str, _getTransText("Mention_this_guy", isBaLstr=True), babase.Lstr(resource="??Unknown??", fallback_value="Info"),
                           babase.Lstr(resource="??Unknown??", fallback_value=_getTransText("Kick_ID") % client_id)]

        try:
            if len(self._getCustomSets().get("partyMemberPress_Custom") if isinstance(self._getCustomSets().get("partyMemberPress_Custom"), dict) else {}) > 0:
                choices.append("customAction")
                choices_display.append(_getTransText("Custom_Action", isBaLstr=True))
        except:
            babase.print_exception()

        PopupMenuWindow(position=widget.get_screen_space_center(),
                        scale=_get_popup_window_scale(),
                        choices=choices,
                        choices_display=choices_display,
                        current_choice="@ this guy",
                        delegate=self)
        self._popup_party_member_client_id = client_id
        self._popup_party_member_is_host = is_host
        self._popup_type = "partyMemberPress"

    def _send_chat_message(self) -> None:
        sendtext = bui.textwidget(query=self._text_field)
        if sendtext == ".ip":
            bs.chatmessage("IP "+ip_add+" PORT "+str(p_port))

            bui.textwidget(edit=self._text_field, text="")
            return
        elif sendtext == ".info":
            if bs.get_connection_to_host_info() == {}:
                s_build = 0
            else:
                s_build = bs.get_connection_to_host_info()['build_number']
            s_v = "0"
            if s_build <= 14365:
                s_v = " 1.4.148 or below"
            elif s_build <= 14377:
                s_v = "1.4.148 < x < = 1.4.155 "
            elif s_build >= 20001 and s_build < 20308:
                s_v = "1.5"
            elif s_build >= 20308 and s_build < 20591:
                s_v = "1.6 "
            else:
                s_v = "1.7 and above "
            bs.chatmessage("script version "+s_v+"- build "+str(s_build))
            bui.textwidget(edit=self._text_field, text="")
            return
        elif sendtext == ".ping":
            bs.chatmessage("My ping:"+str(current_ping))
            bui.textwidget(edit=self._text_field, text="")
            return
        elif sendtext == ".save":
            info = bs.get_connection_to_host_info()
            config = babase.app.config
            if info.get('name', '') != '':
                title = info['name']
                if not isinstance(config.get('Saved Servers'), dict):
                    config['Saved Servers'] = {}
                config['Saved Servers'][f'{ip_add}@{p_port}'] = {
                    'addr': ip_add,
                    'port': p_port,
                    'name': title
                }
                config.commit()
                bs.broadcastmessage("Server saved to manual")
                bui.getsound('gunCocking').play()
                bui.textwidget(edit=self._text_field, text="")
                return
        # elif sendtext != "":
        #     for index in range(getattr(self,"_send_msg_times",1)):
        if '\\' in sendtext:
            sendtext = sendtext.replace('\\d', ('\ue048'))
            sendtext = sendtext.replace('\\c', ('\ue043'))
            sendtext = sendtext.replace('\\h', ('\ue049'))
            sendtext = sendtext.replace('\\s', ('\ue046'))
            sendtext = sendtext.replace('\\n', ('\ue04b'))
            sendtext = sendtext.replace('\\f', ('\ue04f'))
            sendtext = sendtext.replace('\\g', ('\ue027'))
            sendtext = sendtext.replace('\\i', ('\ue03a'))
            sendtext = sendtext.replace('\\m', ('\ue04d'))
            sendtext = sendtext.replace('\\t', ('\ue01f'))
            sendtext = sendtext.replace('\\bs', ('\ue01e'))
            sendtext = sendtext.replace('\\j', ('\ue010'))
            sendtext = sendtext.replace('\\e', ('\ue045'))
            sendtext = sendtext.replace('\\l', ('\ue047'))
            sendtext = sendtext.replace('\\a', ('\ue020'))
            sendtext = sendtext.replace('\\b', ('\ue00c'))
        if sendtext == "":
            sendtext = "   "
        msg = sendtext
        msg1 = msg.split(" ")
        ms2 = ""
        if (len(msg1) > 11):
            hp = int(len(msg1)/2)

            for m in range(0, hp):
                ms2 = ms2+" "+msg1[m]

            bs.chatmessage(ms2)

            ms2 = ""
            for m in range(hp, len(msg1)):
                ms2 = ms2+" "+msg1[m]
            bs.chatmessage(ms2)
        else:
            bs.chatmessage(msg)

        bui.textwidget(edit=self._text_field, text="")
        # else:
        #     Quickreply = self._get_quick_responds()
        #     if len(Quickreply) > 0:
        #         PopupMenuWindow(position=self._text_field.get_screen_space_center(),
        #                                     scale=_get_popup_window_scale(),
        #                                     choices=Quickreply,
        #                                     choices_display=_creat_Lstr_list(Quickreply),
        #                                     current_choice=Quickreply[0],
        #                                     delegate=self)
        #         self._popup_type = "QuickMessageSelect"
        #     else:
        #         bs.chatmessage(sendtext)
        #         bui.textwidget(edit=self._text_field,text="")

    def _get_quick_responds(self):
        if not hasattr(self, "_caches") or not isinstance(self._caches, dict):
            self._caches = {}
        try:
            filePath = os.path.join(RecordFilesDir, "Quickmessage.txt")

            if os.path.exists(RecordFilesDir) is not True:
                os.makedirs(RecordFilesDir)

            if not os.path.isfile(filePath):
                with open(filePath, "wb") as writer:
                    writer.write(({"Chinese": u"\xe5\x8e\x89\xe5\xae\xb3\xef\xbc\x8c\xe8\xbf\x98\xe6\x9c\x89\xe8\xbf\x99\xe7\xa7\x8d\xe9\xaa\x9a\xe6\x93\x8d\xe4\xbd\x9c!\
\xe4\xbd\xa0\xe2\x84\xa2\xe8\x83\xbd\xe5\x88\xab\xe6\x89\x93\xe9\x98\x9f\xe5\x8f\x8b\xe5\x90\x97\xef\xbc\x9f\
\xe5\x8f\xaf\xe4\xbb\xa5\xe5\x95\x8a\xe5\xb1\x85\xe7\x84\xb6\xe8\x83\xbd\xe8\xbf\x99\xe4\xb9\x88\xe7\x8e\xa9\xef\xbc\x9f"}.get(Current_Lang, "Thats Amazing !")).encode("UTF-8"))
            if os.path.getmtime(filePath) != self._caches.get("Vertify_Quickresponse_Text"):
                with open(filePath, "r+", encoding="utf-8") as Reader:
                    Text = Reader.read()
                    if Text.startswith(str(codecs.BOM_UTF8)):
                        Text = Text[3:]
                    self._caches["quickReplys"] = (Text).split("\\n")
                    self._caches["Vertify_Quickresponse_Text"] = os.path.getmtime(filePath)
            return (self._caches.get("quickReplys", []))
        except:
            babase.print_exception()
            bs.broadcastmessage(babase.Lstr(resource="errorText"), (1, 0, 0))
            bui.getsound("error").play()

    def _write_quick_responds(self, data):
        try:
            with open(os.path.join(RecordFilesDir, "Quickmessage.txt"), "wb") as writer:
                writer.write("\\n".join(data).encode("utf-8"))
        except:
            babase.print_exception()
            bs.broadcastmessage(babase.Lstr(resource="errorText"), (1, 0, 0))
            bui.getsound("error").play()

    def _getCustomSets(self):
        try:
            if not hasattr(self, "_caches") or not isinstance(self._caches, dict):
                self._caches = {}
            try:
                from VirtualHost import MainSettings
                if MainSettings.get("Custom_PartyWindow_Sets", {}) != self._caches.get("PartyWindow_Sets", {}):
                    self._caches["PartyWindow_Sets"] = MainSettings.get(
                        "Custom_PartyWindow_Sets", {})
            except:
                try:
                    filePath = os.path.join(RecordFilesDir, "Settings.json")
                    if os.path.isfile(filePath):
                        if os.path.getmtime(filePath) != self._caches.get("Vertify_MainSettings.json_Text"):
                            with open(filePath, "r+", encoding="utf-8") as Reader:
                                Text = Reader.read()
                                if Text.startswith(str(codecs.BOM_UTF8)):
                                    Text = Text[3:]
                                self._caches["PartyWindow_Sets"] = json.loads(
                                    Text.decode("utf-8")).get("Custom_PartyWindow_Sets", {})
                            self._caches["Vertify_MainSettings.json_Text"] = os.path.getmtime(
                                filePath)
                except:
                    babase.print_exception()
            return (self._caches.get("PartyWindow_Sets") if isinstance(self._caches.get("PartyWindow_Sets"), dict) else {})

        except:
            babase.print_exception()

    def _getObjectByID(self, type="playerName", ID=None):
        if ID is None:
            ID = self._popup_party_member_client_id
        type = type.lower()
        output = []
        for roster in self._roster:
            if type.startswith("all"):
                if type in ("roster", "fullrecord"):
                    output += [roster]
                elif type.find("player") != -1 and roster["players"] != []:
                    if type.find("namefull") != -1:
                        output += [(i["name_full"]) for i in roster["players"]]
                    elif type.find("name") != -1:
                        output += [(i["name"]) for i in roster["players"]]
                    elif type.find("playerid") != -1:
                        output += [i["id"] for i in roster["players"]]
                elif type.lower() in ("account", "displaystring"):
                    output += [(roster["display_string"])]
            elif roster["client_id"] == ID and not type.startswith("all"):
                try:
                    if type in ("roster", "fullrecord"):
                        return (roster)
                    elif type.find("player") != -1 and roster["players"] != []:
                        if len(roster["players"]) == 1 or type.find("singleplayer") != -1:
                            if type.find("namefull") != -1:
                                return ((roster["players"][0]["name_full"]))
                            elif type.find("name") != -1:
                                return ((roster["players"][0]["name"]))
                            elif type.find("playerid") != -1:
                                return (roster["players"][0]["id"])
                        else:
                            if type.find("namefull") != -1:
                                return ([(i["name_full"]) for i in roster["players"]])
                            elif type.find("name") != -1:
                                return ([(i["name"]) for i in roster["players"]])
                            elif type.find("playerid") != -1:
                                return ([i["id"] for i in roster["players"]])
                    elif type.lower() in ("account", "displaystring"):
                        return ((roster["display_string"]))
                except:
                    babase.print_exception()

        return (None if len(output) == 0 else output)

    def _edit_text_msg_box(self, text, type="rewrite"):
        if not isinstance(type, str) or not isinstance(text, str):
            return
        type = type.lower()
        text = (text)
        if type.find("add") != -1:
            bui.textwidget(edit=self._text_field, text=bui.textwidget(query=self._text_field)+text)
        else:
            bui.textwidget(edit=self._text_field, text=text)

    def _send_admin_kick_command(self): bs.chatmessage(
        "/kick " + str(self._popup_party_member_client_id))

    def new_input_window_callback(self, got_text, flag, code):
        if got_text:
            if flag.startswith("Host_Kick_Player:"):
                try:
                    result = _babase.disconnect_client(
                        self._popup_party_member_client_id, ban_time=int(code))
                    if not result:
                        bui.getsound('error').play()
                        bs.broadcastmessage(
                            babase.Lstr(resource='getTicketsWindow.unavailableText'),
                            color=(1, 0, 0))
                except:
                    bui.getsound('error').play()
                    print(traceback.format_exc())

    def _kick_selected_player(self):
        """
        result = _babase._disconnectClient(self._popup_party_member_client_id,banTime)
        if not result:
            bs.getsound("error").play()
            bs.broadcastmessage(babase.Lstr(resource="getTicketsWindow.unavailableText"),color=(1,0,0))
        """
        if self._popup_party_member_client_id != -1:
            if bs.get_foreground_host_session() is not None:
                self._popup_type = "banTimePress"
                choices = [0, 30, 60, 120, 300, 600, 900, 1800, 3600, 7200, 99999999] if not (isinstance(self._getCustomSets().get("Ban_Time_List"), list)
                                                                                              and all([isinstance(item, int) for item in self._getCustomSets().get("Ban_Time_List")])) else self._getCustomSets().get("Ban_Time_List")
                PopupMenuWindow(position=self.get_root_widget().get_screen_space_center(),
                                scale=_get_popup_window_scale(),
                                choices=[str(item) for item in choices],
                                choices_display=_creat_Lstr_list(
                                    [_getTransText("Ban_For_%d_Seconds") % item for item in choices]),
                                current_choice="Share_Server_Info",
                                delegate=self)
                """
                NewInputWindow(origin_widget = self.get_root_widget(),
                            delegate = self,post_text = _getTransText("Ban_Time_Post"),
                            default_code = "300",flag = "Host_Kick_Player:"+str(self._popup_party_member_client_id))
                """
            else:
                # kick-votes appeared in build 14248
                if (bs.get_connection_to_host_info().get('build_number', 0) <
                        14248):
                    bui.getsound('error').play()
                    bs.broadcastmessage(
                        babase.Lstr(resource='getTicketsWindow.unavailableText'),
                        color=(1, 0, 0))
                else:

                    # Ban for 5 minutes.
                    result = bs.disconnect_client(
                        self._popup_party_member_client_id, ban_time=5 * 60)
                    if not result:
                        bui.getsound('error').play()
                        bs.broadcastmessage(
                            babase.Lstr(resource='getTicketsWindow.unavailableText'),
                            color=(1, 0, 0))
        else:
            bui.getsound('error').play()
            bs.broadcastmessage(
                babase.Lstr(resource='internal.cantKickHostError'),
                color=(1, 0, 0))

        # NewShareCodeWindow(origin_widget=self.get_root_widget(), delegate=None,code = "300",execText = u"_babase._disconnectClient(%d,{Value})"%self._popup_party_member_client_id)
    def joinbombspot(self):

        bui.open_url("https://discord.gg/ucyaesh")

    def _update(self) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-nested-blocks

        # # update muted state
        # if babase.app.config.resolve('Chat Muted'):
        #     bui.textwidget(edit=self._muted_text, color=(1, 1, 1, 0.3))
        #     # clear any chat texts we're showing
        #     if self._chat_texts:
        #         while self._chat_texts:
        #             first = self._chat_texts.pop()
        #             first.delete()
        # else:
        #     bui.textwidget(edit=self._muted_text, color=(1, 1, 1, 0.0))

        # update roster section

        roster = bs.get_game_roster()
        global f_chat
        global smo_mode
        if roster != self._roster or smo_mode != self.smoothy_mode or f_chat != self.full_chat_mode:
            self._roster = roster
            smo_mode = self.smoothy_mode
            f_chat = self.full_chat_mode
            # clear out old
            for widget in self._name_widgets:
                widget.delete()
            self._name_widgets = []

            if not self._roster:
                top_section_height = 60
                bui.textwidget(edit=self._empty_str,
                               text=babase.Lstr(resource=self._r + '.emptyText'))
                bui.scrollwidget(edit=self._scrollwidget,
                                 size=(self._width - 50,
                                       self._height - top_section_height - 110),
                                 position=(30, 80))
            elif self.full_chat_mode:
                top_section_height = 60
                bui.scrollwidget(edit=self._scrollwidget,
                                 size=(self._width - 50,
                                       self._height - top_section_height - 75),
                                 position=(30, 80))

            else:
                columns = 1 if len(
                    self._roster) == 1 else 2 if len(self._roster) == 2 else 3
                rows = int(math.ceil(float(len(self._roster)) / columns))
                c_width = (self._width * 0.9) / max(3, columns)
                c_width_total = c_width * columns
                c_height = 24
                c_height_total = c_height * rows
                for y in range(rows):
                    for x in range(columns):
                        index = y * columns + x
                        if index < len(self._roster):
                            t_scale = 0.65
                            pos = (self._width * 0.53 - c_width_total * 0.5 +
                                   c_width * x - 23,
                                   self._height - 65 - c_height * y - 15)

                            # if there are players present for this client, use
                            # their names as a display string instead of the
                            # client spec-string
                            try:
                                if self.smoothy_mode == 1 and self._roster[index]['players']:
                                    # if there's just one, use the full name;
                                    # otherwise combine short names
                                    if len(self._roster[index]
                                           ['players']) == 1:
                                        p_str = self._roster[index]['players'][
                                            0]['name_full']
                                    else:
                                        p_str = ('/'.join([
                                            entry['name'] for entry in
                                            self._roster[index]['players']
                                        ]))
                                        if len(p_str) > 25:
                                            p_str = p_str[:25] + '...'
                                elif self.smoothy_mode == 0:
                                    p_str = self._roster[index][
                                        'display_string']
                                    p_str = self._get_nick(p_str)

                                else:
                                    p_str = self._roster[index][
                                        'display_string']

                            except Exception:
                                babase.print_exception(
                                    'Error calcing client name str.')
                                p_str = '???'
                            try:
                                widget = bui.textwidget(parent=self._root_widget,
                                                        position=(pos[0], pos[1]),
                                                        scale=t_scale,
                                                        size=(c_width * 0.85, 30),
                                                        maxwidth=c_width * 0.85,
                                                        color=(1, 1,
                                                               1) if index == 0 else
                                                        (1, 1, 1),
                                                        selectable=True,
                                                        autoselect=True,
                                                        click_activate=True,
                                                        text=babase.Lstr(value=p_str),
                                                        h_align='left',
                                                        v_align='center')
                                self._name_widgets.append(widget)
                            except Exception:
                                pass
                            # in newer versions client_id will be present and
                            # we can use that to determine who the host is.
                            # in older versions we assume the first client is
                            # host
                            if self._roster[index]['client_id'] is not None:
                                is_host = self._roster[index][
                                    'client_id'] == -1
                            else:
                                is_host = (index == 0)

                            # FIXME: Should pass client_id to these sort of
                            #  calls; not spec-string (perhaps should wait till
                            #  client_id is more readily available though).
                            try:
                                bui.textwidget(edit=widget,
                                               on_activate_call=babase.Call(
                                                   self._on_party_member_press,
                                                   self._roster[index]['client_id'],
                                                   is_host, widget))
                            except Exception:
                                pass
                            pos = (self._width * 0.53 - c_width_total * 0.5 +
                                   c_width * x,
                                   self._height - 65 - c_height * y)

                            # Make the assumption that the first roster
                            # entry is the server.
                            # FIXME: Shouldn't do this.
                            if is_host:
                                twd = min(
                                    c_width * 0.85,
                                    _babase.get_string_width(
                                        p_str, suppress_warning=True) *
                                    t_scale)
                                try:
                                    self._name_widgets.append(
                                        bui.textwidget(
                                            parent=self._root_widget,
                                            position=(pos[0] + twd + 1,
                                                      pos[1] - 0.5),
                                            size=(0, 0),
                                            h_align='left',
                                            v_align='center',
                                            maxwidth=c_width * 0.96 - twd,
                                            color=(0.1, 1, 0.1, 0.5),
                                            text=babase.Lstr(resource=self._r +
                                                             '.hostText'),
                                            scale=0.4,
                                            shadow=0.1,
                                            flatness=1.0))
                                except Exception:
                                    pass
                try:
                    bui.textwidget(edit=self._empty_str, text='')
                    bui.scrollwidget(edit=self._scrollwidget,
                                     size=(self._width - 50,
                                           max(100, self._height - 139 -
                                               c_height_total)),
                                     position=(30, 80))
                except Exception:
                    pass

    def hide_screen_msg(self):
        file = open('ba_data/data/languages/english.json')
        eng = json.loads(file.read())
        file.close()
        eng['internal']['playerJoinedPartyText'] = ''
        eng['internal']['playerLeftPartyText'] = ''
        eng['internal']['chatBlockedText'] = ''
        eng['kickVoteStartedText'] = ''
        # eng['kickVoteText']=''
        eng['kickWithChatText'] = ''
        eng['kickOccurredText'] = ''
        eng['kickVoteFailedText'] = ''
        eng['votesNeededText'] = ''
        eng['playerDelayedJoinText'] = ''
        eng['playerLeftText'] = ''
        eng['kickQuestionText'] = ''
        file = open('ba_data/data/languages/english.json', "w")
        json.dump(eng, file)
        file.close()
        bs.app.lang.setlanguage(None)

    def restore_screen_msg(self):
        file = open('ba_data/data/languages/english.json')
        eng = json.loads(file.read())
        file.close()
        eng['internal']['playerJoinedPartyText'] = "${NAME} joined the pawri!"
        eng['internal']['playerLeftPartyText'] = "${NAME} left the pawri."
        eng['internal']['chatBlockedText'] = "${NAME} is chat-blocked for ${TIME} seconds."
        eng['kickVoteStartedText'] = "A kick vote has been started for ${NAME}."
        # eng['kickVoteText']=''
        eng['kickWithChatText'] = "Type ${YES} in chat for yes and ${NO} for no."
        eng['kickOccurredText'] = "${NAME} was kicked."
        eng['kickVoteFailedText'] = "Kick-vote failed."
        eng['votesNeededText'] = "${NUMBER} votes needed"
        eng['playerDelayedJoinText'] = "${PLAYER} will enter at the start of the next round."
        eng['playerLeftText'] = "${PLAYER} left the game."
        eng['kickQuestionText'] = "Kick ${NAME}?"
        file = open('ba_data/data/languages/english.json', "w")
        json.dump(eng, file)
        file.close()
        bs.app.lang.setlanguage(None)
    def popup_menu_selected_choice(self, popup_window: PopupMenuWindow,
                                   choice: str) -> None:
        """Called when a choice is selected in the popup."""
        global unmuted_names
        if self._popup_type == "banTimePress":
            result = _babase.disconnect_client(
                self._popup_party_member_client_id, ban_time=int(choice))
            if not result:
                bui.getsound('error').play()
                bs.broadcastmessage(
                    babase.Lstr(resource='getTicketsWindow.unavailableText'),
                    color=(1, 0, 0))
        elif self._popup_type == "send_Times_Press":
            self._send_msg_times = int(choice)
            bui.buttonwidget(edit=self._times_button, label="%s:%d" %
                             (_getTransText("Times"), getattr(self, "_send_msg_times", 1)))

        elif self._popup_type == "chatmessagepress":
            if choice == "mute":
                unmuted_names.remove(self.msg_user_selected.split(":")[0].encode('utf-8'))
            if choice == "unmute":
                unmuted_names.append(self.msg_user_selected.split(":")[0].encode('utf-8'))
            if choice == "copy":
                self._copy_msg(self.msg_user_selected)

        elif self._popup_type == "partyMemberPress":
            if choice == "kick":
                ConfirmWindow(text=_getTransText("Normal_kick_confirm") % self._getObjectByID("account"),
                              action=self._kick_selected_player, cancel_button=True, cancel_is_selected=True,
                              color=self._bg_color, text_scale=1.0,
                              origin_widget=self.get_root_widget())
            elif choice == "info":
                account = self._getObjectByID("account")

                self.loading_widget = ConfirmWindow(text="Searching .....",
                                                    color=self._bg_color, text_scale=1.0, cancel_button=False,
                                                    origin_widget=self.get_root_widget())
                start_new_thread(fetchAccountInfo, (account, self.loading_widget,))

            elif choice == "adminkick":
                ConfirmWindow(text=_getTransText("Admin_Command_Kick_Confirm") % self._getObjectByID("account"),
                              action=self._send_admin_kick_command, cancel_button=True, cancel_is_selected=True,
                              color=self._bg_color, text_scale=1.0,
                              origin_widget=self.get_root_widget())

            elif choice == "@ this guy":
                ChoiceDis = []
                NewChoices = []
                account = self._getObjectByID("account")
                ChoiceDis.append(account)
                temp = self._getObjectByID("playerNameFull")
                if temp is not None:
                    if isinstance(temp, str) and temp not in ChoiceDis:
                        ChoiceDis.append(temp)
                    elif isinstance(temp, (list, tuple)):
                        for item in temp:
                            if isinstance(item, str) and item not in ChoiceDis:
                                ChoiceDis.append(item)
                    # print("r\\""

                for item in ChoiceDis:
                    NewChoices.append(u"self._edit_text_msg_box('%s','add')" %
                                      (item.replace("'", r"'").replace('"', r'\\"')))

                else:
                    nick = self._get_nick(account)
                    ChoiceDis.append(nick)
                NewChoices.append(u"self._on_nick_rename_press('%s')" % (account))
                p = PopupMenuWindow(position=popup_window.root_widget.get_screen_space_center(),
                                    scale=_get_popup_window_scale(),
                                    choices=NewChoices,
                                    choices_display=_creat_Lstr_list(ChoiceDis),
                                    current_choice=NewChoices[0],
                                    delegate=self)
                self._popup_type = "Custom_Exec_Choice"
            elif choice == "customAction":
                customActionSets = self._getCustomSets()
                customActionSets = customActionSets.get("partyMemberPress_Custom") if isinstance(
                    customActionSets.get("partyMemberPress_Custom"), dict) else {}
                ChoiceDis = []
                NewChoices = []
                for key, item in customActionSets.items():
                    ChoiceDis.append(key)
                    NewChoices.append(item)
                if len(ChoiceDis) > 0:
                    p = PopupMenuWindow(position=popup_window.root_widget.get_screen_space_center(),
                                        scale=_get_popup_window_scale(),
                                        choices=NewChoices,
                                        choices_display=_creat_Lstr_list(ChoiceDis),
                                        current_choice=NewChoices[0],
                                        delegate=self)
                    self._popup_type = "customAction_partyMemberPress"
                else:
                    bui.getsound("error").play()
                    bs.broadcastmessage(
                        babase.Lstr(resource="getTicketsWindow.unavailableText"), color=(1, 0, 0))
        elif self._popup_type == "menu":
            if choice in ("mute", "unmute"):
                cfg = babase.app.config
                cfg['Chat Muted'] = (choice == 'mute')
                cfg.apply_and_commit()
                if cfg['Chat Muted']:
                    customchatThread().run()
                self._update()
            elif choice in ("credits",):
                ConfirmWindow(text="AdvancePartyWindow by Mr.Smoothy \n extended version of ModifyPartyWindow(Plasma Boson) \n Version 5.3 \n Dont modify or release the source code \n Discord : \n mr.smoothy#5824    Plasma Boson#4104",
                              action=self.joinbombspot, width=420, height=200,
                              cancel_button=False, cancel_is_selected=False,
                              color=self._bg_color, text_scale=1.0, ok_text="More mods >", cancel_text=None,
                              origin_widget=self.get_root_widget())
            elif choice == "chatlogger":
                # ColorPickerExact(parent=self.get_root_widget(), position=self.get_root_widget().get_screen_space_center(),
                #             initial_color=self._bg_color, delegate=self, tag='')
                global chatlogger
                if chatlogger:
                    chatlogger = False
                    bs.broadcastmessage("Chat logger turned OFF")
                else:
                    chatlogger = True
                    chatloggThread().run()
                    bs.broadcastmessage("Chat logger turned ON")
            elif choice == 'screenmsg':
                global screenmsg
                if screenmsg:
                    screenmsg = False
                    self.hide_screen_msg()
                else:
                    screenmsg = True
                    self.restore_screen_msg()
            elif choice == "addQuickReply":
                try:
                    newReply = bui.textwidget(query=self._text_field)
                    data = self._get_quick_responds()
                    data.append(newReply)
                    self._write_quick_responds(data)
                    bs.broadcastmessage(_getTransText("Something_is_added") %
                                        newReply, color=(0, 1, 0))
                    bui.getsound("dingSmallHigh").play()
                except:
                    babase.print_exception()
            elif choice == "removeQuickReply":
                Quickreply = self._get_quick_responds()
                PopupMenuWindow(position=self._text_field.get_screen_space_center(),
                                scale=_get_popup_window_scale(),
                                choices=Quickreply,
                                choices_display=_creat_Lstr_list(Quickreply),
                                current_choice=Quickreply[0],
                                delegate=self)
                self._popup_type = "removeQuickReplySelect"
            elif choice in ("hostInfo_Debug",) and isinstance(bs.get_connection_to_host_info(), dict):
                if len(bs.get_connection_to_host_info()) > 0:
                    # print(_babase.get_connection_to_host_info(),type(_babase.get_connection_to_host_info()))

                    ChoiceDis = list(bs.get_connection_to_host_info().keys())
                    NewChoices = ["bs.broadcastmessage(str(bs.get_connection_to_host_info().get('%s')))" % (
                        (str(i)).replace("'", r"'").replace('"', r'\\"')) for i in ChoiceDis]
                    PopupMenuWindow(position=popup_window.root_widget.get_screen_space_center(),
                                    scale=_get_popup_window_scale(),
                                    choices=NewChoices,
                                    choices_display=_creat_Lstr_list(ChoiceDis),
                                    current_choice=NewChoices[0],
                                    delegate=self)

                    self._popup_type = "Custom_Exec_Choice"
                else:
                    bui.getsound("error").play()
                    bs.broadcastmessage(
                        babase.Lstr(resource="getTicketsWindow.unavailableText"), color=(1, 0, 0))
            elif choice == "translator":
                chats = _babase._getChatMessages()
                if len(chats) > 0:
                    choices = [(item) for item in chats[::-1]]
                    PopupMenuWindow(position=popup_window.root_widget.get_screen_space_center(),
                                    scale=_get_popup_window_scale(),
                                    choices=choices,
                                    choices_display=_creat_Lstr_list(choices),
                                    current_choice=choices[0],
                                    delegate=self)
                    self._popup_type = "translator_Press"
                else:
                    bui.getsound("error").play()
                    bs.broadcastmessage(
                        babase.Lstr(resource="getTicketsWindow.unavailableText"), color=(1, 0, 0))
            elif choice == "resetGameRecord":
                ConfirmWindow(text=_getTransText("Restart_Game_Record_Confirm"),
                              action=self._reset_game_record, cancel_button=True, cancel_is_selected=True,
                              color=self._bg_color, text_scale=1.0,
                              origin_widget=self.get_root_widget())
        elif self._popup_type == "translator_Press":
            pass

        elif self._popup_type == "customAction_partyMemberPress":

            try:
                keyReplaceValue = (r"{$PlayerNameFull}", r"{$PlayerName}", r"{$PlayerID}",
                                   r"{$AccountInfo}", r"{$AllPlayerName}", r"{$AllPlayerNameFull}")
                pos = None
                curKeyWord = None
                for keyWord in keyReplaceValue:
                    CurPos = choice.find(keyWord)
                    if CurPos != -1 and (pos is None or CurPos < pos):
                        pos = CurPos
                        curKeyWord = keyWord
                if isinstance(pos, int) and isinstance(curKeyWord, str):
                    if curKeyWord in (r"{$PlayerNameFull}", r"{$PlayerName}", r"{$AllPlayerName}", r"{$AllPlayerNameFull}"):
                        # if choice.count(curKeyWord) != 0:
                        playerName = self._getObjectByID(
                            curKeyWord.replace("{$", "").replace("}", ""))
                        if isinstance(playerName, (list, tuple)):
                            ChoiceDis = []
                            NewChoices = []
                            for i in playerName:
                                ChoiceDis.append(i)
                                NewChoices.append(choice.replace(
                                    curKeyWord, (i.replace("'", r"'").replace('"', r'\\"')), 1))
                            p = PopupMenuWindow(position=popup_window.root_widget.get_screen_space_center(),
                                                scale=_get_popup_window_scale(),
                                                choices=NewChoices,
                                                choices_display=_creat_Lstr_list(ChoiceDis),
                                                current_choice=NewChoices[0],
                                                delegate=self)
                            self._popup_type = "customAction_partyMemberPress"
                        elif isinstance(playerName, str):
                            self.popup_menu_selected_choice(popup_window, choice.replace(
                                curKeyWord, (playerName.replace("'", r"'").replace('"', r'\\"')), 1))
                        else:
                            bs.broadcastmessage(_getTransText("No_valid_player_found"), (1, 0, 0))
                            bui.getsound("error").play()
                    elif curKeyWord in (r"{$PlayerID}",) != 0:
                        playerID = self._getObjectByID("PlayerID")
                        playerName = self._getObjectByID("PlayerName")
                        # print(playerID,playerName)
                        if isinstance(playerID, (list, tuple)) and isinstance(playerName, (list, tuple)) and len(playerName) == len(playerID):
                            ChoiceDis = []
                            NewChoices = []
                            for i1, i2 in playerName, playerID:
                                ChoiceDis.append(i1)
                                NewChoices.append(choice.replace(r"{$PlayerID}", str(
                                    i2).replace("'", r"'").replace('"', r'\\"')), 1)
                            p = PopupMenuWindow(position=popup_window.root_widget.get_screen_space_center(),
                                                scale=_get_popup_window_scale(),
                                                choices=NewChoices,
                                                choices_display=_creat_Lstr_list(ChoiceDis),
                                                current_choice=NewChoices[0],
                                                delegate=self)
                            self._popup_type = "customAction_partyMemberPress"
                        elif isinstance(playerID, int):
                            self.popup_menu_selected_choice(popup_window, choice.replace(
                                r"{$PlayerID}", str(playerID).replace("'", r"'").replace('"', r'\\"')))
                        else:
                            bs.broadcastmessage(_getTransText(
                                "No_valid_player_id_found"), (1, 0, 0))
                            bui.getsound("error").play()
                    elif curKeyWord in (r"{$AccountInfo}",) != 0:
                        self.popup_menu_selected_choice(popup_window, choice.replace(
                            r"{$AccountInfo}", (str(self._getObjectByID("roster"))).replace("'", r"'").replace('"', r'\\"'), 1))
                else:
                    exec(choice)
            except Exception as e:
                bs.broadcastmessage(repr(e), (1, 0, 0))
        elif self._popup_type == "QuickMessageSelect":
            # bui.textwidget(edit=self._text_field,text=self._get_quick_responds()[index])
            self._edit_text_msg_box(choice, "add")
        elif self._popup_type == "removeQuickReplySelect":
            data = self._get_quick_responds()
            if len(data) > 0 and choice in data:
                data.remove(choice)
                self._write_quick_responds(data)
                bs.broadcastmessage(_getTransText("Something_is_removed") % choice, (1, 0, 0))
                bui.getsound("shieldDown").play()
            else:
                bs.broadcastmessage(babase.Lstr(resource="errorText"), (1, 0, 0))
                bui.getsound("error").play()
        elif choice.startswith("custom_Exec_Choice_") or self._popup_type == "Custom_Exec_Choice":
            exec(choice[len("custom_Exec_Choice_"):]
                 if choice.startswith("custom_Exec_Choice_") else choice)
        else:
            print("unhandled popup type: "+str(self._popup_type))


def fetchAccountInfo(account, loading_widget):
    pbid = ""
    account_data = []
    servers = []
    try:
        filePath = os.path.join(RecordFilesDir, "players.json")
        fdata = {}
        if os.path.isfile(filePath):
            f = open(filePath, "r")
            fdata = json.load(f)
        if account in fdata:
            servers = fdata[account]
        url = f'https://{BCSSERVER}/player?key={base64.b64encode(account.encode("utf-8")).decode("utf-8")}&base64=true'
        req = urllib.request.Request(url, headers={
                                     "User-Agent": f'BS{_babase.env().get("build_number", 0)}', "Accept-Language": "en-US,en;q=0.9", })
        data = urllib.request.urlopen(req)
        account_data = json.loads(data.read().decode('utf-8'))[0]
        pbid = account_data["pbid"]

    except Exception as e:
        print(e)
        pass
    # _babase.pushcall(Call(updateAccountWindow,loading_widget,accounts[0]),from_other_thread=True)
    _babase.pushcall(Call(CustomAccountViewerWindow, pbid, account_data,
                          servers, loading_widget), from_other_thread=True)


class CustomAccountViewerWindow(viewer.AccountViewerWindow):
    def __init__(self, account_id, custom_data, servers, loading_widget):
        super().__init__(account_id)
        try:
            loading_widget._cancel()
        except:
            pass
        self.custom_data = custom_data
        self.pb_id = account_id
        self.servers = servers

    def _copy_pb(self):
        babase.clipboard_set_text(self.pb_id)
        bs.broadcastmessage(babase.Lstr(resource='gatherWindow.copyCodeConfirmText'))

    def _on_query_response(self, data):

        if data is None:
            bui.textwidget(edit=self._loading_text, text="")
            bui.textwidget(parent=self._scrollwidget,
                           size=(0, 0),
                           position=(170, 200),
                           flatness=1.0,
                           h_align='center',
                           v_align='center',
                           scale=0.5,
                           color=bui.app.ui_v1.infotextcolor,
                           text="Mutual servers",
                           maxwidth=300)
            v = 200-21
            for server in self.servers:
                bui.textwidget(parent=self._scrollwidget,
                               size=(0, 0),
                               position=(170, v),
                               h_align='center',
                               v_align='center',
                               scale=0.55,
                               text=server,
                               maxwidth=300)
                v -= 23
        else:
            for account in self.custom_data["accounts"]:
                if account not in data["accountDisplayStrings"]:
                    data["accountDisplayStrings"].append(account)
            try:
                self._loading_text.delete()
                trophystr = ''
                try:
                    trophystr = data['trophies']
                    num = 10
                    chunks = [
                        trophystr[i:i + num]
                        for i in range(0, len(trophystr), num)
                    ]
                    trophystr = ('\n\n'.join(chunks))
                    if trophystr == '':
                        trophystr = '-'
                except Exception:
                    babase.print_exception('Error displaying trophies.')
                account_name_spacing = 15
                tscale = 0.65
                ts_height = _babase.get_string_height(trophystr,
                                                      suppress_warning=True)
                sub_width = self._width - 80
                sub_height = 500 + ts_height * tscale + \
                    account_name_spacing * len(data['accountDisplayStrings'])
                self._subcontainer = bui.containerwidget(
                    parent=self._scrollwidget,
                    size=(sub_width, sub_height),
                    background=False)
                v = sub_height - 20

                title_scale = 0.37
                center = 0.3
                maxwidth_scale = 0.45
                showing_character = False
                if data['profileDisplayString'] is not None:
                    tint_color = (1, 1, 1)
                    try:
                        if data['profile'] is not None:
                            profile = data['profile']
                            character = babase.app.spaz_appearances.get(
                                profile['character'], None)
                            if character is not None:
                                tint_color = (profile['color'] if 'color'
                                                                  in profile else (1, 1, 1))
                                tint2_color = (profile['highlight']
                                               if 'highlight' in profile else
                                               (1, 1, 1))
                                icon_tex = character.icon_texture
                                tint_tex = character.icon_mask_texture
                                mask_texture = bui.gettexture(
                                    'characterIconMask')
                                bui.imagewidget(
                                    parent=self._subcontainer,
                                    position=(sub_width * center - 40, v - 80),
                                    size=(80, 80),
                                    color=(1, 1, 1),
                                    mask_texture=mask_texture,
                                    texture=bui.gettexture(icon_tex),
                                    tint_texture=bui.gettexture(tint_tex),
                                    tint_color=tint_color,
                                    tint2_color=tint2_color)
                                v -= 95
                    except Exception:
                        babase.print_exception('Error displaying character.')
                    bui.textwidget(
                        parent=self._subcontainer,
                        size=(0, 0),
                        position=(sub_width * center, v),
                        h_align='center',
                        v_align='center',
                        scale=0.9,
                        color=babase.safecolor(tint_color, 0.7),
                        shadow=1.0,
                        text=babase.Lstr(value=data['profileDisplayString']),
                        maxwidth=sub_width * maxwidth_scale * 0.75)
                    showing_character = True
                    v -= 33

                center = 0.75 if showing_character else 0.5
                maxwidth_scale = 0.45 if showing_character else 0.9

                v = sub_height - 20
                if len(data['accountDisplayStrings']) <= 1:
                    account_title = babase.Lstr(
                        resource='settingsWindow.accountText')
                else:
                    account_title = babase.Lstr(
                        resource='accountSettingsWindow.accountsText',
                        fallback_resource='settingsWindow.accountText')
                bui.textwidget(parent=self._subcontainer,
                               size=(0, 0),
                               position=(sub_width * center, v),
                               flatness=1.0,
                               h_align='center',
                               v_align='center',
                               scale=title_scale,
                               color=bui.app.ui_v1.infotextcolor,
                               text=account_title,
                               maxwidth=sub_width * maxwidth_scale)
                draw_small = (showing_character
                              or len(data['accountDisplayStrings']) > 1)
                v -= 14 if draw_small else 20
                for account_string in data['accountDisplayStrings']:
                    bui.textwidget(parent=self._subcontainer,
                                   size=(0, 0),
                                   position=(sub_width * center, v),
                                   h_align='center',
                                   v_align='center',
                                   scale=0.55 if draw_small else 0.8,
                                   text=account_string,
                                   maxwidth=sub_width * maxwidth_scale)
                    v -= account_name_spacing

                v += account_name_spacing
                v -= 25 if showing_character else 29
                # =======================================================================
                bui.textwidget(parent=self._subcontainer,
                               size=(0, 0),
                               position=(sub_width * center, v),
                               flatness=1.0,
                               h_align='center',
                               v_align='center',
                               scale=title_scale,
                               color=bui.app.ui_v1.infotextcolor,
                               text=str(self.pb_id),
                               maxwidth=sub_width * maxwidth_scale)
                self._copy_btn = bui.buttonwidget(
                    parent=self._subcontainer,
                    position=(sub_width * center - 120, v - 9),
                    size=(60, 30),
                    scale=0.5,
                    label='copy',
                    color=(0.6, 0.5, 0.6),
                    on_activate_call=self._copy_pb,
                    autoselect=True)

                v -= 24
                bui.textwidget(parent=self._subcontainer,
                               size=(0, 0),
                               position=(sub_width * center, v),
                               flatness=1.0,
                               h_align='center',
                               v_align='center',
                               scale=title_scale,
                               color=bui.app.ui_v1.infotextcolor,
                               text="Name",
                               maxwidth=sub_width * maxwidth_scale)
                v -= 26
                for name in self.custom_data["names"]:
                    bui.textwidget(parent=self._subcontainer,
                                   size=(0, 0),
                                   position=(sub_width * center, v),
                                   h_align='center',
                                   v_align='center',
                                   scale=0.51,
                                   text=name,
                                   maxwidth=sub_width * maxwidth_scale)
                    v -= 13
                v -= 8
                bui.textwidget(parent=self._subcontainer,
                               size=(0, 0),
                               position=(sub_width * center, v),
                               flatness=1.0,
                               h_align='center',
                               v_align='center',
                               scale=title_scale,
                               color=bui.app.ui_v1.infotextcolor,
                               text="Created On",
                               maxwidth=sub_width * maxwidth_scale)
                v -= 19
                d = self.custom_data["createdOn"]

                bui.textwidget(parent=self._subcontainer,
                               size=(0, 0),
                               position=(sub_width * center, v),
                               h_align='center',
                               v_align='center',
                               scale=0.55,
                               text=d[:d.index("T")],
                               maxwidth=sub_width * maxwidth_scale)
                v -= 29
                bui.textwidget(parent=self._subcontainer,
                               size=(0, 0),
                               position=(sub_width * center, v),
                               flatness=1.0,
                               h_align='center',
                               v_align='center',
                               scale=title_scale,
                               color=bui.app.ui_v1.infotextcolor,
                               text="Discord",
                               maxwidth=sub_width * maxwidth_scale)
                v -= 19
                if len(self.custom_data["discord"]) > 0:
                    bui.textwidget(parent=self._subcontainer,
                                   size=(0, 0),
                                   position=(sub_width * center, v),
                                   h_align='center',
                                   v_align='center',
                                   scale=0.55,
                                   text=self.custom_data["discord"][0]["username"] +
                                   ","+self.custom_data["discord"][0]["id"],
                                   maxwidth=sub_width * maxwidth_scale)
                v -= 26
                bui.textwidget(parent=self._subcontainer,
                               size=(0, 0),
                               position=(sub_width * center, v),
                               flatness=1.0,
                               h_align='center',
                               v_align='center',
                               scale=title_scale,
                               color=bui.app.ui_v1.infotextcolor,
                               text="Mutual servers",
                               maxwidth=sub_width * maxwidth_scale)
                v = -19
                v = 270
                for server in self.servers:
                    bui.textwidget(parent=self._subcontainer,
                                   size=(0, 0),
                                   position=(sub_width * center, v),
                                   h_align='center',
                                   v_align='center',
                                   scale=0.55,
                                   text=server,
                                   maxwidth=sub_width * maxwidth_scale)
                    v -= 13

                v -= 16
                # ==================================================================
                bui.textwidget(parent=self._subcontainer,
                               size=(0, 0),
                               position=(sub_width * center, v),
                               flatness=1.0,
                               h_align='center',
                               v_align='center',
                               scale=title_scale,
                               color=bui.app.ui_v1.infotextcolor,
                               text=babase.Lstr(resource='rankText'),
                               maxwidth=sub_width * maxwidth_scale)
                v -= 14
                if data['rank'] is None:
                    rank_str = '-'
                    suffix_offset = None
                else:
                    str_raw = babase.Lstr(
                        resource='league.rankInLeagueText').evaluate()
                    # FIXME: Would be nice to not have to eval this.
                    rank_str = babase.Lstr(
                        resource='league.rankInLeagueText',
                        subs=[('${RANK}', str(data['rank'][2])),
                              ('${NAME}',
                               babase.Lstr(translate=('leagueNames',
                                                      data['rank'][0]))),
                              ('${SUFFIX}', '')]).evaluate()
                    rank_str_width = min(
                        sub_width * maxwidth_scale,
                        _babase.get_string_width(rank_str, suppress_warning=True) *
                        0.55)

                    # Only tack our suffix on if its at the end and only for
                    # non-diamond leagues.
                    if (str_raw.endswith('${SUFFIX}')
                            and data['rank'][0] != 'Diamond'):
                        suffix_offset = rank_str_width * 0.5 + 2
                    else:
                        suffix_offset = None

                bui.textwidget(parent=self._subcontainer,
                               size=(0, 0),
                               position=(sub_width * center, v),
                               h_align='center',
                               v_align='center',
                               scale=0.55,
                               text=rank_str,
                               maxwidth=sub_width * maxwidth_scale)
                if suffix_offset is not None:
                    assert data['rank'] is not None
                    bui.textwidget(parent=self._subcontainer,
                                   size=(0, 0),
                                   position=(sub_width * center + suffix_offset,
                                             v + 3),
                                   h_align='left',
                                   v_align='center',
                                   scale=0.29,
                                   flatness=1.0,
                                   text='[' + str(data['rank'][1]) + ']')
                v -= 14

                str_raw = babase.Lstr(
                    resource='league.rankInLeagueText').evaluate()
                old_offs = -50
                prev_ranks_shown = 0
                for prev_rank in data['prevRanks']:
                    rank_str = babase.Lstr(
                        value='${S}:    ${I}',
                        subs=[
                            ('${S}',
                             babase.Lstr(resource='league.seasonText',
                                         subs=[('${NUMBER}', str(prev_rank[0]))])),
                            ('${I}',
                             babase.Lstr(resource='league.rankInLeagueText',
                                         subs=[('${RANK}', str(prev_rank[3])),
                                               ('${NAME}',
                                                babase.Lstr(translate=('leagueNames',
                                                                       prev_rank[1]))),
                                               ('${SUFFIX}', '')]))
                        ]).evaluate()
                    rank_str_width = min(
                        sub_width * maxwidth_scale,
                        _babase.get_string_width(rank_str, suppress_warning=True) *
                        0.3)

                    # Only tack our suffix on if its at the end and only for
                    # non-diamond leagues.
                    if (str_raw.endswith('${SUFFIX}')
                            and prev_rank[1] != 'Diamond'):
                        suffix_offset = rank_str_width + 2
                    else:
                        suffix_offset = None
                    bui.textwidget(parent=self._subcontainer,
                                   size=(0, 0),
                                   position=(sub_width * center + old_offs, v),
                                   h_align='left',
                                   v_align='center',
                                   scale=0.3,
                                   text=rank_str,
                                   flatness=1.0,
                                   maxwidth=sub_width * maxwidth_scale)
                    if suffix_offset is not None:
                        bui.textwidget(parent=self._subcontainer,
                                       size=(0, 0),
                                       position=(sub_width * center + old_offs +
                                                 suffix_offset, v + 1),
                                       h_align='left',
                                       v_align='center',
                                       scale=0.20,
                                       flatness=1.0,
                                       text='[' + str(prev_rank[2]) + ']')
                    prev_ranks_shown += 1
                    v -= 10

                v -= 13

                bui.textwidget(parent=self._subcontainer,
                               size=(0, 0),
                               position=(sub_width * center, v),
                               flatness=1.0,
                               h_align='center',
                               v_align='center',
                               scale=title_scale,
                               color=bui.app.ui_v1.infotextcolor,
                               text=babase.Lstr(resource='achievementsText'),
                               maxwidth=sub_width * maxwidth_scale)
                v -= 14
                bui.textwidget(parent=self._subcontainer,
                               size=(0, 0),
                               position=(sub_width * center, v),
                               h_align='center',
                               v_align='center',
                               scale=0.55,
                               text=str(data['achievementsCompleted']) + ' / ' +
                               str(len(bui.app.classic.ach.achievements)),
                               maxwidth=sub_width * maxwidth_scale)
                v -= 25

                if prev_ranks_shown == 0 and showing_character:
                    v -= 20
                elif prev_ranks_shown == 1 and showing_character:
                    v -= 10

                center = 0.5
                maxwidth_scale = 0.9

                bui.textwidget(parent=self._subcontainer,
                               size=(0, 0),
                               position=(sub_width * center, v),
                               h_align='center',
                               v_align='center',
                               scale=title_scale,
                               color=bui.app.ui_v1.infotextcolor,
                               flatness=1.0,
                               text=babase.Lstr(resource='trophiesThisSeasonText',
                                                fallback_resource='trophiesText'),
                               maxwidth=sub_width * maxwidth_scale)
                v -= 19
                bui.textwidget(parent=self._subcontainer,
                               size=(0, ts_height),
                               position=(sub_width * 0.5,
                                         v - ts_height * tscale),
                               h_align='center',
                               v_align='top',
                               corner_scale=tscale,
                               text=trophystr)

            except Exception:
                babase.print_exception('Error displaying account info.')

# ba_meta export plugin


class bySmoothy(babase.Plugin):
    def __init__(self):
        bs.connect_to_party = newconnect_to_party
        bascenev1lib_party.PartyWindow = ModifiedPartyWindow
