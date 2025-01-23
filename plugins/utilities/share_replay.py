# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
"""
                             Plugin by LoupGarou a.k.a Loup/Soup   
                                 Discord →ʟօʊքɢǟʀօʊ#3063 
Share replays easily with your friends or have a backup

Exported replays are stored in replays folder which is inside mods folder
You can start sharing replays by opening the watch window and going to share replay tab

Feel free to let me know if you use this plugin,i love to hear that :)

Message me in discord if you find some bug
Use this code for your experiments or plugin but please dont rename this plugin and distribute with your name,don't do that,its bad'
"""

# ba_meta require api 9
from __future__ import annotations
from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
    from typing import Any, Sequence, Callable, List, Dict, Tuple, Optional, Union

from os import listdir, mkdir, path, sep, remove
from shutil import copy, copytree

import babase
import bauiv1 as bui
import bascenev1 as bs
import _babase
from enum import Enum
from bauiv1lib.tabs import TabRow
from bauiv1lib.confirm import ConfirmWindow
from bauiv1lib.watch import WatchWindow
from bauiv1lib.popup import PopupWindow


title = "SHARE REPLAY"
internal_dir = _babase.get_replays_dir()+sep
external_dir = path.join(_babase.env()["python_directory_user"], "replays"+sep)
uiscale = bui.app.ui_v1.uiscale

# colors
pink = (1, 0.2, 0.8)
green = (0.4, 1, 0.4)
red = (1, 0, 0)
blue = (0.26, 0.65, 0.94)
blue_highlight = (0.4, 0.7, 1)
b_color = (0.6, 0.53, 0.63)
b_textcolor = (0.75, 0.7, 0.8)


def Print(*args, color=None):
    out = ""
    for arg in args:
        a = str(arg)
        out += a
    bui.screenmessage(out, color=color)


def cprint(*args):
    out = ""
    for arg in args:
        a = str(arg)
        out += a
    bs.chatmessage(out)


if not path.exists(external_dir):
    mkdir(external_dir)
    Print("You are ready to share replays", color=pink)


def override(cls: ClassType) -> Callable[[MethodType], MethodType]:
    def decorator(newfunc: MethodType) -> MethodType:
        funcname = newfunc.__code__.co_name
        if hasattr(cls, funcname):
            oldfunc = getattr(cls, funcname)
            setattr(cls, f'_old_{funcname}', oldfunc)

        setattr(cls, funcname, newfunc)
        return newfunc

    return decorator


class CommonUtilities:

    def sync_confirmation(self):
        ConfirmWindow(text="WARNING:\nreplays with same name in mods folder\n will be overwritten",
                      action=self.sync, cancel_is_selected=True)

    def sync(self):
        internal_list = listdir(internal_dir)
        external_list = listdir(external_dir)
        for i in internal_list:
            copy(internal_dir+sep+i, external_dir+sep+i)
        for i in external_list:
            if i in internal_list:
                pass
            else:
                copy(external_dir+sep+i, internal_dir+sep+i)
        Print("Synced all replays", color=pink)

    def _copy(self, selected_replay, tab_id):
        if selected_replay is None:
            Print("Select a replay", color=red)
            return
        elif tab_id == MyTabId.INTERNAL:
            copy(internal_dir+selected_replay, external_dir+selected_replay)
            Print(selected_replay[0:-4]+" exported", color=pink)
        else:
            copy(external_dir+selected_replay, internal_dir+selected_replay)
            Print(selected_replay[0:-4]+" imported", color=green)

    def delete_replay(self, selected_replay, tab_id, cls_inst):
        if selected_replay is None:
            Print("Select a replay", color=red)
            return

        def do_it():
            if tab_id == MyTabId.INTERNAL:
                remove(internal_dir+selected_replay)
            elif tab_id == MyTabId.EXTERNAL:
                remove(external_dir+selected_replay)
            cls_inst.on_tab_select(tab_id)  # updating the tab
            Print(selected_replay[0:-4]+" was deleted", color=red)
        ConfirmWindow(text=f"Delete \"{selected_replay.split('.')[0]}\" \nfrom {'internal directory' if tab_id == MyTabId.INTERNAL else 'external directory'}?",
                      action=do_it, cancel_is_selected=True)


CommonUtils = CommonUtilities()


class MyTabId(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    SHARE_REPLAYS = "share_replay"


class Help(PopupWindow):
    def __init__(self):
        self.width = 1200
        self.height = 250
        self.root_widget = bui.Window(bui.containerwidget(
            size=(self.width, self.height), on_outside_click_call=self.close, transition="in_right")).get_root_widget()

        bui.containerwidget(edit=self.root_widget, on_outside_click_call=self.close)
        bui.textwidget(parent=self.root_widget, position=(0, self.height * 0.7), corner_scale=1.2, color=green,
                       text=f"»Replays are exported to\n     {external_dir}\n»Copy replays to the above folder to be able to import them into the game\n»I would love to hear from you, meet me on discord\n -LoupGarou(author)")

    def close(self):
        bui.getsound('swish').play()
        bui.containerwidget(edit=self.root_widget, transition="out_right",)


class ShareTabUi(WatchWindow):
    def __init__(self, root_widget=None):
        self.tab_id = MyTabId.INTERNAL
        self.selected_replay = None

        if root_widget is None:
            self.root = bui.Window(bui.containerwidget(
                size=(1000, 600), on_outside_click_call=self.close, transition="in_right")).get_root_widget()

        else:
            self.root = root_widget

        self.draw_ui()

    def on_select_text(self, widget, name):
        existing_widgets = self.scroll2.get_children()
        for i in existing_widgets:
            bui.textwidget(edit=i, color=(1, 1, 1))
        bui.textwidget(edit=widget, color=(1.0, 1, 0.4))
        self.selected_replay = name

    def on_tab_select(self, tab_id):
        self.selected_replay = None
        self.tab_id = tab_id
        t_scale = 1.6

        if tab_id == MyTabId.INTERNAL:
            dir_list = listdir(internal_dir)
            bui.buttonwidget(edit=self.share_button, label="Export\nReplay")
        else:
            dir_list = listdir(external_dir)
            bui.buttonwidget(edit=self.share_button, label="Import\nReplay")

        self.tab_row.update_appearance(tab_id)
        dir_list = sorted(dir_list)
        existing_widgets = self.scroll2.get_children()
        if existing_widgets:  # deleting textwidgets from old tab
            for i in existing_widgets:
                i.delete()
        height = 900
        for i in dir_list:  # making textwidgets for all replays
            height -= 50
            a = i
            i = bui.textwidget(
                parent=self.scroll2,
                size=(self._my_replays_scroll_width/t_scale, 30),
                text=i.split(".")[0],
                position=(20, height),
                selectable=True,
                max_chars=40,
                corner_scale=t_scale,
                click_activate=True,
                always_highlight=True,)
            bui.textwidget(edit=i, on_activate_call=babase.Call(self.on_select_text, i, a))

    def draw_ui(self):
        self._r = 'watchWindow'
        x_inset = 100 if uiscale is babase.UIScale.SMALL else 0
        scroll_buffer_h = 130 + 2 * x_inset
        self._width = 1240 if uiscale is babase.UIScale.SMALL else 1040
        self._height = (
            578
            if uiscale is babase.UIScale.SMALL
            else 670
            if uiscale is babase.UIScale.MEDIUM
            else 800)
        self._scroll_width = self._width - scroll_buffer_h
        self._scroll_height = self._height - 180
        #
        c_width = self._scroll_width
        c_height = self._scroll_height - 20
        sub_scroll_height = c_height - 63
        self._my_replays_scroll_width = sub_scroll_width = (
            680 if uiscale is babase.UIScale.SMALL else 640
        )

        v = c_height - 30
        b_width = 140 if uiscale is babase.UIScale.SMALL else 178
        b_height = (
            107
            if uiscale is babase.UIScale.SMALL
            else 142
            if uiscale is babase.UIScale.MEDIUM
            else 190
        )
        b_space_extra = (
            0
            if uiscale is babase.UIScale.SMALL
            else -2
            if uiscale is babase.UIScale.MEDIUM
            else -5
        )

        b_color = (0.6, 0.53, 0.63)
        b_textcolor = (0.75, 0.7, 0.8)
        btnv = (c_height - (48
                if uiscale is babase.UIScale.SMALL
                else 45
                if uiscale is babase.UIScale.MEDIUM
                else 40) - b_height)
        btnh = 40 if uiscale is babase.UIScale.SMALL else 40
        smlh = 190 if uiscale is babase.UIScale.SMALL else 225
        tscl = 1.0 if uiscale is babase.UIScale.SMALL else 1.2

        stab_width = 500
        stab_height = 300
        stab_h = smlh

        v -= sub_scroll_height + 23
        scroll = bui.scrollwidget(
            parent=self.root,
            position=(smlh, v),
            size=(sub_scroll_width, sub_scroll_height),
        )

        self.scroll2 = bui.columnwidget(parent=scroll,
                                        size=(sub_scroll_width, sub_scroll_height))

        tabdefs = [(MyTabId.INTERNAL, 'INTERNAL'), (MyTabId.EXTERNAL, "EXTERNAL")]
        self.tab_row = TabRow(self.root, tabdefs, pos=(stab_h, sub_scroll_height),
                              size=(stab_width, stab_height), on_select_call=self.on_tab_select)

        helpbtn_space = 20
        helpbtn_v = stab_h+stab_width+helpbtn_space+120
        helpbtn_h = sub_scroll_height+helpbtn_space

        bui.buttonwidget(
            parent=self.root,
            position=(helpbtn_v, helpbtn_h),
            size=(35, 35),
            button_type="square",
            label="?",
            text_scale=1.5,
            color=b_color,
            textcolor=b_textcolor,
            on_activate_call=Help)

        def call_copy(): return CommonUtils._copy(self.selected_replay, self.tab_id)
        self.share_button = bui.buttonwidget(
            parent=self.root,
            size=(b_width, b_height),
            position=(btnh, btnv),
            button_type="square",
            label="Export\nReplay",
            text_scale=tscl,
            color=b_color,
            textcolor=b_textcolor,
            on_activate_call=call_copy)

        btnv -= b_height + b_space_extra
        sync_button = bui.buttonwidget(
            parent=self.root,
            size=(b_width, b_height),
            position=(btnh, btnv),
            button_type="square",
            label="Sync\nReplay",
            text_scale=tscl,
            color=b_color,
            textcolor=b_textcolor,
            on_activate_call=CommonUtils.sync_confirmation)

        btnv -= b_height + b_space_extra
        def call_delete(): return CommonUtils.delete_replay(self.selected_replay, self.tab_id, self)
        delete_replay_button = bui.buttonwidget(
            parent=self.root,
            size=(b_width, b_height),
            position=(btnh, btnv),
            button_type="square",
            label=babase.Lstr(resource=self._r + '.deleteReplayButtonText'),
            text_scale=tscl,
            color=b_color,
            textcolor=b_textcolor,
            on_activate_call=call_delete)

        self.on_tab_select(MyTabId.INTERNAL)

    def close(self):
        bui.getsound('swish').play()
        bui.containerwidget(edit=self.root, transition="out_right",)


# ++++++++++++++++for keyboard navigation++++++++++++++++

        # bui.widget(edit=self.enable_button, up_widget=decrease_button, down_widget=self.lower_text,left_widget=save_button, right_widget=save_button)

# ----------------------------------------------------------------------------------------------------

class ShareTab(WatchWindow):

    @override(WatchWindow)
    def __init__(self,
                 transition: str | None = 'in_right',
                 origin_widget: bui.Widget | None = None,
                 oldmethod=None):
        self.my_tab_container = None
        self._old___init__(transition, origin_widget)

        self._tab_row.tabs[self.TabID.MY_REPLAYS].button.delete()  # deleting old tab button

        tabdefs = [(self.TabID.MY_REPLAYS,
                    babase.Lstr(resource=self._r + '.myReplaysText'),),
                   (MyTabId.SHARE_REPLAYS, "Share Replays"),]

        uiscale = bui.app.ui_v1.uiscale
        x_inset = 100 if uiscale is babase.UIScale.SMALL else 0
        tab_buffer_h = 750 + 2 * x_inset
        self._tab_row = TabRow(
            self._root_widget,
            tabdefs,
            pos=((tab_buffer_h / 1.5) * 0.5, self._height - 130),
            size=((self._width - tab_buffer_h)*2, 50),
            on_select_call=self._set_tab)

        self._tab_row.update_appearance(self.TabID.MY_REPLAYS)

    @override(WatchWindow)
    def _set_tab(self, tab_id, oldfunc=None):
        self._old__set_tab(tab_id)
        if self.my_tab_container:
            self.my_tab_container.delete()
        if tab_id == MyTabId.SHARE_REPLAYS:

            scroll_left = (self._width - self._scroll_width) * 0.5
            scroll_bottom = self._height - self._scroll_height - 79 - 48

            c_width = self._scroll_width
            c_height = self._scroll_height - 20
            sub_scroll_height = c_height - 63
            self._my_replays_scroll_width = sub_scroll_width = (
                680 if uiscale is babase.UIScale.SMALL else 640
            )

            self.my_tab_container = bui.containerwidget(
                parent=self._root_widget,
                position=(scroll_left,
                          scroll_bottom + (self._scroll_height - c_height) * 0.5,),
                size=(c_width, c_height),
                background=False,
                selection_loops_to_parent=True,
            )

            ShareTabUi(self.my_tab_container)


# ba_meta export plugin

class Loup(babase.Plugin):
    def on_app_running(self):
        WatchWindow.__init__ = ShareTab.__init__

    def has_settings_ui(self):
        return True

    def show_settings_ui(self, button):
        Print("Open share replay tab in replay window to share your replays", color=blue)
