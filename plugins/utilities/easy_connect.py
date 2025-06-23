# -*- coding: utf-8 -*-
# ba_meta require api 9

''' ===========================================
 EasyConnect by Mr.Smoothy                    |
 verion 1.7                                   |
 https://discord.gg/ucyaesh                   |
 Serverconnector X IPPORTRevealer             |
 for bombsquad v1.7.37+                       |
 ==============================================
'''

# .................___________________________________________
# WATCH IN ACTION https://www.youtube.com/watch?v=jwi2wKwZblQ
# .................___________________________________________

# Have any idea/suggestion/bug report  >  send message on discord mr.smoothy#5824
# Download modshttps://bombsquad-community.web.app/mods
# Discord:-
# mr.smoothy#5824

# DONT EDIT ANYTHING WITHOUT PERMISSION

# join Bombsquad Community Server -

# https://discord.gg/ucyaesh

# REQUIREMENTS
# built for bs 1.7.37 and above

# by Mr.Smoothy for Bombsquad version 1.7.37+

import _babase
import babase
import bauiv1 as bui
import bascenev1 as bs
import threading
from bauiv1lib.gather import manualtab, publictab
from bauiv1lib import popup
from dataclasses import dataclass
import random
from enum import Enum
from bauiv1lib.popup import PopupMenuWindow
from typing import Any, Optional, Callable
from bauiv1lib.gather.publictab import PublicGatherTab
import json
import urllib.request
import time


ENABLE_SERVER_BANNING = True
DEBUG_SERVER_COMMUNICATION = False
DEBUG_PROCESSING = False
"""
This banned servers list is maintained by commmunity , its not official.
Reason for ban can be (not limited to) using abusive server names , using server name of a reputed server/community 
without necessary permissions.
Report such case on community discord channels   
https://discord.gg/ucyaesh
https://ballistica.net/discord
"""
BCSURL = 'https://bcs.ballistica.workers.dev/bannedservers'


def is_game_version_lower_than(version):
    """
    Returns a boolean value indicating whether the current game
    version is lower than the passed version. Useful for addressing
    any breaking changes within game versions.
    """
    game_version = tuple(map(int, babase.app.version.split(".")))
    version = tuple(map(int, version.split(".")))
    return game_version < version


def updateBannedServersCache():
    response = None
    config = babase.app.config
    if not isinstance(config.get('Banned Servers'), list):
        config['Banned Servers'] = []
    try:
        req = urllib.request.Request(BCSURL, headers={
                                     "User-Agent": f'BS{_babase.env().get("build_number", 0)}', "Accept-Language": "en-US,en;q=0.9", })
        response = urllib.request.urlopen(req).read()
        data = json.loads(response.decode('utf-8'))
        bannedlist = []
        for server in data["servers"]:
            bannedlist.append(server["ip"])
        config['Banned Servers'] = bannedlist
        config.commit()
        print("updated cache")
    except Exception as e:
        print(e)


class _HostLookupThread(threading.Thread):
    """Thread to fetch an addr."""

    def __init__(self, name: str, port: int,
                 call: Callable[[Optional[str], int], Any]):
        super().__init__()
        self._name = name
        self._port = port
        self._call = call

    def run(self) -> None:
        result: Optional[str]
        try:
            import socket
            result = socket.gethostbyname(self._name)
        except Exception:
            result = None
        babase.pushcall(lambda: self._call(result, self._port),
                        from_other_thread=True)


def newbuild_favorites_tab(self, region_width: float, region_height: float) -> None:
    c_height = region_height - 20
    v = c_height - 35 - 25 - 30
    self.retry_inter = 0.0
    uiscale = bui.app.ui_v1.uiscale
    self._width = region_width
    x_inset = 100 if uiscale is babase.UIScale.SMALL else 0
    self._height = (578 if uiscale is babase.UIScale.SMALL else
                    670 if uiscale is babase.UIScale.MEDIUM else 800)

    self._scroll_width = self._width - 130 + 2 * x_inset
    self._scroll_height = self._height - 180
    x_inset = 100 if uiscale is babase.UIScale.SMALL else 0

    c_height = self._scroll_height - 20
    sub_scroll_height = c_height - 63
    self._favorites_scroll_width = sub_scroll_width = (
        680 if uiscale is babase.UIScale.SMALL else 640)

    v = c_height - 30

    b_width = 140 if uiscale is babase.UIScale.SMALL else 178
    b_height = (90 if uiscale is babase.UIScale.SMALL else
                142 if uiscale is babase.UIScale.MEDIUM else 130)
    b_space_extra = (0 if uiscale is babase.UIScale.SMALL else
                     -2 if uiscale is babase.UIScale.MEDIUM else -5)

    btnv = (c_height - (48 if uiscale is babase.UIScale.SMALL else
                        45 if uiscale is babase.UIScale.MEDIUM else 40) -
            b_height)
    # ================= smoothy =============

    bui.textwidget(parent=self._container,
                   position=(90 if uiscale is babase.UIScale.SMALL else 120, btnv +
                             120 if uiscale is babase.UIScale.SMALL else btnv+90),
                   size=(0, 0),
                   h_align='center',
                   color=(0.8, 0.8, 0.8),
                   v_align='top',
                   text="Auto")
    btnv += 50 if uiscale is babase.UIScale.SMALL else 0

    bui.buttonwidget(parent=self._container,
                     size=(30, 30),
                     position=(25 if uiscale is babase.UIScale.SMALL else 40,
                               btnv+10),

                     color=(0.6, 0.53, 0.63),
                     textcolor=(0.75, 0.7, 0.8),
                     on_activate_call=self.auto_retry_dec,
                     text_scale=1.3 if uiscale is babase.UIScale.SMALL else 1.2,
                     label="-",
                     autoselect=True)
    self.retry_inter_text = bui.textwidget(parent=self._container,
                                           position=(
                                               90 if uiscale is babase.UIScale.SMALL else 120, btnv+25),
                                           size=(0, 0),
                                           h_align='center',
                                           color=(0.8, 0.8, 0.8),
                                           v_align='center',
                                           text=str(self.retry_inter) if self.retry_inter > 0.0 else 'off')
    bui.buttonwidget(parent=self._container,
                     size=(30, 30),
                     position=(125 if uiscale is babase.UIScale.SMALL else 155,
                               btnv+10),

                     color=(0.6, 0.53, 0.63),
                     textcolor=(0.75, 0.7, 0.8),
                     on_activate_call=self.auto_retry_inc,
                     text_scale=1.3 if uiscale is babase.UIScale.SMALL else 1.2,
                     label="+",
                     autoselect=True)

    btnv -= b_height + b_space_extra

    self._favorites_connect_button = btn1 = bui.buttonwidget(
        parent=self._container,
        size=(b_width, b_height),
        position=(25 if uiscale is babase.UIScale.SMALL else 40, btnv),
        button_type='square',
        color=(0.6, 0.53, 0.63),
        textcolor=(0.75, 0.7, 0.8),
        on_activate_call=self._on_favorites_connect_press,
        text_scale=1.0 if uiscale is babase.UIScale.SMALL else 1.2,
        label=babase.Lstr(resource='gatherWindow.manualConnectText'),
        autoselect=True)
    if uiscale is babase.UIScale.SMALL and bui.app.ui_v1.use_toolbars:
        bui.widget(edit=btn1,
                   left_widget=bui.get_special_widget('back_button'))
    btnv -= b_height + b_space_extra
    bui.buttonwidget(parent=self._container,
                     size=(b_width, b_height),
                     position=(25 if uiscale is babase.UIScale.SMALL else 40,
                               btnv),
                     button_type='square',
                     color=(0.6, 0.53, 0.63),
                     textcolor=(0.75, 0.7, 0.8),
                     on_activate_call=self._on_favorites_edit_press,
                     text_scale=1.0 if uiscale is babase.UIScale.SMALL else 1.2,
                     label=babase.Lstr(resource='editText'),
                     autoselect=True)
    btnv -= b_height + b_space_extra
    bui.buttonwidget(parent=self._container,
                     size=(b_width, b_height),
                     position=(25 if uiscale is babase.UIScale.SMALL else 40,
                               btnv),
                     button_type='square',
                     color=(0.6, 0.53, 0.63),
                     textcolor=(0.75, 0.7, 0.8),
                     on_activate_call=self._on_favorite_delete_press,
                     text_scale=1.0 if uiscale is babase.UIScale.SMALL else 1.2,
                     label=babase.Lstr(resource='deleteText'),
                     autoselect=True)

    v -= sub_scroll_height + 23
    self._scrollwidget = scrlw = bui.scrollwidget(
        parent=self._container,
        position=(190 if uiscale is babase.UIScale.SMALL else 225, v),
        size=(sub_scroll_width, sub_scroll_height),
        claims_left_right=True)
    bui.widget(edit=self._favorites_connect_button,
               right_widget=self._scrollwidget)
    self._columnwidget = bui.columnwidget(parent=scrlw,
                                          left_border=10,
                                          border=2,
                                          margin=0,
                                          claims_left_right=True)
    self._no_parties_added_text = bui.textwidget(
        parent=self._container,
        size=(0, 0),
        h_align='center',
        v_align='center',
        text='',
        color=(0.6, 0.6, 0.6),
        scale=1.2,
        position=(
            (
                (240 if uiscale is bui.UIScale.SMALL else 225)
                + sub_scroll_width * 0.5
            ),
            v + sub_scroll_height * 0.5,
        ),
        glow_type='uniform',
    )

    self._favorite_selected = None
    self._refresh_favorites()


def new_on_favorites_connect_press(self) -> None:
    if self._favorite_selected is None:
        self._no_favorite_selected_error()

    else:
        config = babase.app.config['Saved Servers'][self._favorite_selected]
        _HostLookupThread(name=config['addr'],
                          port=config['port'],
                          call=bs.WeakCall(
                              self._host_lookup_result)).start()

        if self.retry_inter > 0 and (bs.get_connection_to_host_info_2() == {} or bs.get_connection_to_host_info_2() == None or bs.get_connection_to_host_info_2()['build_number'] == 0):
            bui.screenmessage("Server full or unreachable, Retrying....")
            self._retry_timer = bs.AppTimer(self.retry_inter, babase.Call(
                self._on_favorites_connect_press))


def auto_retry_inc(self):

    self.retry_inter += 0.5
    bui.textwidget(edit=self.retry_inter_text, text='%.1f' % self.retry_inter)


def auto_retry_dec(self):
    if self.retry_inter > 0.0:
        self.retry_inter -= 0.5

    if self.retry_inter == 0.0:
        bui.textwidget(edit=self.retry_inter_text, text='off')
    else:
        bui.textwidget(edit=self.retry_inter_text, text='%.1f' % self.retry_inter)


@dataclass
class PartyEntry:
    """Info about a public party."""
    address: str
    index: int
    queue: Optional[str] = None
    port: int = -1
    name: str = ''
    size: int = -1
    size_max: int = -1
    claimed: bool = False
    ping: Optional[float] = None
    ping_interval: float = -1.0
    next_ping_time: float = -1.0
    ping_attempts: int = 0
    ping_responses: int = 0
    stats_addr: Optional[str] = None
    clean_display_index: Optional[int] = None

    def get_key(self) -> str:
        """Return the key used to store this party."""
        return f'{self.address}_{self.port}'


class SelectionComponent(Enum):
    """Describes what part of an entry is selected."""
    NAME = 'name'
    STATS_BUTTON = 'stats_button'


@dataclass
class Selection:
    """Describes the currently selected list element."""
    entry_key: str
    component: SelectionComponent


def _clear(self) -> None:
    for widget in [
            self._name_widget, self._size_widget, self._ping_widget,
            self._stats_button
    ]:
        if widget:

            widget.delete()


def update(self, index: int, party: PartyEntry, sub_scroll_width: float,
           sub_scroll_height: float, lineheight: float,
           columnwidget: bui.Widget, join_text: bui.Widget,
           filter_text: bui.Widget, existing_selection: Optional[Selection],
           tab: PublicGatherTab) -> None:
    """Update for the given data."""
    # pylint: disable=too-many-locals

    # Quick-out: if we've been marked clean for a certain index and
    # we're still at that index, we're done.
    plus = bui.app.plus
    assert plus is not None

    # Quick-out: if we've been marked clean for a certain index and
    # we're still at that index, we're done.
    if party.clean_display_index == index:
        return

    ping_good = plus.get_v1_account_misc_read_val('pingGood', 100)
    ping_med = plus.get_v1_account_misc_read_val('pingMed', 500)

    self._clear()
    hpos = 20
    vpos = sub_scroll_height - lineheight * index - 50
    self._name_widget = bui.textwidget(
        text=bui.Lstr(value=party.name),
        parent=columnwidget,
        size=(sub_scroll_width * 0.63, 20),
        position=(0 + hpos, 4 + vpos),
        selectable=True,
        on_select_call=bui.WeakCall(
            tab.set_public_party_selection,
            Selection(party.get_key(), SelectionComponent.NAME),
        ),
        on_activate_call=bui.WeakCall(tab.on_public_party_activate, party),
        click_activate=True,
        maxwidth=sub_scroll_width * 0.45,
        corner_scale=1.4,
        autoselect=True,
        color=(1, 1, 1, 0.3 if party.ping is None else 1.0),
        h_align='left',
        v_align='center',
    )
    bui.widget(
        edit=self._name_widget,
        left_widget=join_text,
        show_buffer_top=64.0,
        show_buffer_bottom=64.0,
    )
    if existing_selection == Selection(
        party.get_key(), SelectionComponent.NAME
    ):
        bui.containerwidget(
            edit=columnwidget, selected_child=self._name_widget
        )
    if party.stats_addr or True:
        url = party.stats_addr.replace(
            '${ACCOUNT}',
            plus.get_v1_account_misc_read_val_2(
                'resolvedAccountID', 'UNKNOWN'
            ),
        )
        self._stats_button = bui.buttonwidget(
            color=(0.3, 0.6, 0.94),
            textcolor=(1.0, 1.0, 1.0),
            label='....',
            parent=columnwidget,
            autoselect=True,
            on_activate_call=bui.Call(bui.open_url, url),
            on_select_call=bui.WeakCall(
                tab.set_public_party_selection,
                Selection(party.get_key(), SelectionComponent.STATS_BUTTON),
            ),
            size=(120, 40),
            position=(sub_scroll_width * 0.66 + hpos, 1 + vpos),
            scale=0.9,
        )
        bui.buttonwidget(edit=self._stats_button, on_activate_call=bui.WeakCall(
            self.on_stats_click, self._stats_button, party))
        if existing_selection == Selection(
            party.get_key(), SelectionComponent.STATS_BUTTON
        ):
            bui.containerwidget(
                edit=columnwidget, selected_child=self._stats_button
            )

    self._size_widget = bui.textwidget(
        text=str(party.size) + '/' + str(party.size_max),
        parent=columnwidget,
        size=(0, 0),
        position=(sub_scroll_width * 0.86 + hpos, 20 + vpos),
        scale=0.7,
        color=(0.8, 0.8, 0.8),
        h_align='right',
        v_align='center',
    )

    if index == 0:
        bui.widget(edit=self._name_widget, up_widget=filter_text)
        if self._stats_button:
            bui.widget(edit=self._stats_button, up_widget=filter_text)

    self._ping_widget = bui.textwidget(
        parent=columnwidget,
        size=(0, 0),
        position=(sub_scroll_width * 0.94 + hpos, 20 + vpos),
        scale=0.7,
        h_align='right',
        v_align='center',
    )
    if party.ping is None:
        bui.textwidget(
            edit=self._ping_widget, text='-', color=(0.5, 0.5, 0.5)
        )
    else:
        bui.textwidget(
            edit=self._ping_widget,
            text=str(int(party.ping)),
            color=(0, 1, 0)
            if party.ping <= ping_good
            else (1, 1, 0)
            if party.ping <= ping_med
            else (1, 0, 0),
        )

    party.clean_display_index = index


def _get_popup_window_scale() -> float:
    uiscale = bui.app.ui_v1.uiscale
    return (2.3 if uiscale is babase.UIScale.SMALL else
            1.65 if uiscale is babase.UIScale.MEDIUM else 1.23)


_party = None


def on_stats_click(self, widget, party):
    global _party
    _party = party
    choices = ['connect', 'copyqueue', "save"]
    DisChoices = [babase.Lstr(resource="ipp", fallback_value="Connect by IP"), babase.Lstr(
        resource="copy id", fallback_value="Copy Queue ID"), babase.Lstr(value="Save")]
    if party.stats_addr:
        choices.append('stats')
        if 'discord' in party.stats_addr:
            txt = "Discord"
        elif 'yout' in party.stats_addr:
            txt = "Youtube"
        else:
            txt = party.stats_addr[0:13]
        DisChoices.append(babase.Lstr(value=txt))
    PopupMenuWindow(
        position=widget.get_screen_space_center(),
        scale=_get_popup_window_scale(),
        choices=choices,
        choices_display=DisChoices,
        current_choice="stats",
        delegate=self)


def popup_menu_closing(self, popup_window: popup.PopupWindow) -> None:
    pass


def popup_menu_selected_choice(self, window: popup.PopupMenu,
                               choice: str) -> None:
    """Called when a menu entry is selected."""
    # Unused arg.
    plus = babase.app.plus
    if choice == 'stats':
        url = _party.stats_addr.replace(
            '${ACCOUNT}',
            plus.get_v1_account_misc_read_val_2('resolvedAccountID',
                                                'UNKNOWN'))
        bui.open_url(url)
    elif choice == 'connect':
        PartyQuickConnect(_party.address, _party.port)
    elif choice == 'save':
        config = babase.app.config
        ip_add = _party.address
        p_port = _party.port
        title = _party.name
        if not isinstance(config.get('Saved Servers'), dict):
            config['Saved Servers'] = {}
        config['Saved Servers'][f'{ip_add}@{p_port}'] = {
            'addr': ip_add,
            'port': p_port,
            'name': title
        }
        config.commit()
        bui.screenmessage("Server saved to manual")
        bui.getsound('gunCocking').play()
    elif choice == "copyqueue":
        babase.clipboard_set_text(_party.queue)
        bui.getsound('gunCocking').play()


def _update_party_lists(self) -> None:
    if not self._party_lists_dirty:
        return
    starttime = time.time()
    config = babase.app.config
    plus = babase.app.plus
    bannedservers = config.get('Banned Servers', [])
    assert len(self._parties_sorted) == len(self._parties)

    self._parties_sorted.sort(
        key=lambda p: (
            p[1].ping if p[1].ping is not None else 999999.0,
            p[1].index,
        )
    )

    # If signed out or errored, show no parties.
    if (
        plus.get_v1_account_state() != 'signed_in'
        or not self._have_valid_server_list
    ):
        self._parties_displayed = {}
    else:
        if self._filter_value:
            filterval = self._filter_value.lower()
            self._parties_displayed = {
                k: v
                for k, v in self._parties_sorted
                if (filterval in v.name.lower() or filterval in v.address) and (v.address not in bannedservers if ENABLE_SERVER_BANNING else True)
            }
        else:
            self._parties_displayed = {
                k: v
                for k, v in self._parties_sorted
                if (v.address not in bannedservers if ENABLE_SERVER_BANNING else True)
            }

    # Any time our selection disappears from the displayed list, go back to
    # auto-selecting the top entry.
    if (
        self._selection is not None
        and self._selection.entry_key not in self._parties_displayed
    ):
        self._have_user_selected_row = False

    # Whenever the user hasn't selected something, keep the first visible
    # row selected.
    if not self._have_user_selected_row and self._parties_displayed:
        firstpartykey = next(iter(self._parties_displayed))
        self._selection = Selection(firstpartykey, SelectionComponent.NAME)

    self._party_lists_dirty = False
    if DEBUG_PROCESSING:
        print(
            f'Sorted {len(self._parties_sorted)} parties in'
            f' {time.time()-starttime:.5f}s.'
        )


def replace():
    manualtab.ManualGatherTab._build_favorites_tab = newbuild_favorites_tab
    manualtab.ManualGatherTab._on_favorites_connect_press = new_on_favorites_connect_press
    manualtab.ManualGatherTab.auto_retry_dec = auto_retry_dec
    manualtab.ManualGatherTab.auto_retry_inc = auto_retry_inc
    publictab.UIRow.update = update
    publictab.UIRow._clear = _clear
    publictab.UIRow.on_stats_click = on_stats_click
    publictab.UIRow.popup_menu_closing = popup_menu_closing
    publictab.UIRow.popup_menu_selected_choice = popup_menu_selected_choice
    # publictab.PublicGatherTab._update_party_lists = _update_party_lists


class PartyQuickConnect(bui.Window):
    def __init__(self, address: str, port: int):
        self._width = 800
        self._height = 400
        self._white_tex = bui.gettexture('white')
        self.lineup_tex = bui.gettexture('playerLineup')
        self.lineup_1_transparent_mesh = bui.getmesh(
            'playerLineup1Transparent')
        self.eyes_mesh = bui.getmesh('plasticEyesTransparent')
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(root_widget=bui.containerwidget(
            size=(self._width, self._height),
            color=(0.45, 0.63, 0.15),
            transition='in_scale',
            scale=(1.4 if uiscale is babase.UIScale.SMALL else
                   1.2 if uiscale is babase.UIScale.MEDIUM else 1.0)))
        self._cancel_button = bui.buttonwidget(parent=self._root_widget,
                                               scale=1.0,
                                               position=(60, self._height - 80),
                                               size=(50, 50),
                                               label='',
                                               on_activate_call=self.close,
                                               autoselect=True,
                                               color=(0.45, 0.63, 0.15),
                                               icon=bui.gettexture('crossOut'),
                                               iconscale=1.2)
        bui.containerwidget(edit=self._root_widget,
                            cancel_button=self._cancel_button)

        self.IP = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.55 + 60),
            size=(0, 0),
            color=(1.0, 3.0, 1.0),
            scale=1.3,
            h_align='center',
            v_align='center',
            text="IP: "+address + " PORT: "+str(port),
            maxwidth=self._width * 0.65)
        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.55),
            size=(0, 0),
            color=(1.0, 3.0, 1.0),
            scale=1.3,
            h_align='center',
            v_align='center',
            text="Retrying....",
            maxwidth=self._width * 0.65)
        self._line_image = bui.imagewidget(
            parent=self._root_widget,
            color=(0.0, 0.0, 0.0),
            opacity=0.2,
            position=(40.0, 120),
            size=(800-190+80, 4.0),
            texture=self._white_tex)
        self.dude_x = 60
        self._body_image_target = bui.buttonwidget(
            parent=self._root_widget,
            size=(1 * 60, 1 * 80),
            color=(random.random(), random.random(), random.random()),
            label='',
            texture=self.lineup_tex,
            position=(40, 110),
            mesh_transparent=self.lineup_1_transparent_mesh)
        self._eyes_image = bui.imagewidget(
            parent=self._root_widget,
            size=(1 * 36, 1 * 18),
            texture=self.lineup_tex,
            color=(1, 1, 1),
            position=(40, 165),
            mesh_transparent=self.eyes_mesh)
        # self._body_image_target2 = bui.imagewidget(
        #             parent=self._root_widget,
        #             size=(1* 60, 1 * 80),
        #             color=(1,0.3,0.4),
        #             texture=self.lineup_tex,
        #             position=(700,130),
        #             mesh_transparent=self.lineup_1_transparent_mesh)
        self.closed = False
        self.retry_count = 1
        self.direction = "right"
        self.connect(address, port)
        self.move_R = bs.AppTimer(0.01, babase.Call(self.move_right), repeat=True)

    def move_right(self):
        if self._body_image_target and self._eyes_image:
            bui.buttonwidget(edit=self._body_image_target, position=(self.dude_x, 110))
            bui.imagewidget(edit=self._eyes_image, position=(self.dude_x+10, 165))
        else:
            self.move_R = None
        if self.direction == "right":
            self.dude_x += 2
            if self.dude_x >= 650:
                self.direction = "left"
        else:
            self.dude_x -= 2
            if self.dude_x <= 50:
                self.direction = "right"

    def connect(self, address, port):
        if not self.closed and (bs.get_connection_to_host_info_2() == {} or bs.get_connection_to_host_info_2() == None or bs.get_connection_to_host_info_2()['build_number'] == 0):
            bui.textwidget(edit=self._title_text, text="Retrying....("+str(self.retry_count)+")")
            self.retry_count += 1
            bs.connect_to_party(address, port=port)
            self._retry_timer = bs.AppTimer(1.5, babase.Call(
                self.connect, address, port))

    def close(self) -> None:
        """Close the ui."""
        self.closed = True
        bui.containerwidget(edit=self._root_widget, transition='out_scale')


# ba_meta export babase.Plugin
class InitalRun(babase.Plugin):
    def __init__(self):
        replace()
        config = babase.app.config
        if config["launchCount"] % 5 == 0:
            updateBannedServersCache()
