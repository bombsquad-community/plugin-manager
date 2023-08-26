# ba_meta require api 8
"""
Working for v1.7.20+ only
———————————————————————————————————————
• Menu Theme v1.0.9
• discord: riyukiiyan

I appreciate any kind of modification. So feel free to share, edit and change credit string... no problem
Credits are unnecessary but are a much-appreciated gesture to show support to others :D

[CHANGELOG]:
~ Support for BombSquad v1.7.26
~ Fixed "Show Logo Text" checkmark not updating on imports and reset
~ Music changes:
	>> Turn off music by selecting 'None'
	>> Removed dupes, renamed some and added 2 new musics

Special thanks to:
snowee, rikko, & unknown
———————————————————————————————————————
"""
from __future__ import annotations

from typing import List, Sequence, Callable, Any, cast

from bascenev1lib.mainmenu import MainMenuActivity, NewsDisplay, _preload1
from bauiv1lib.mainmenu import MainMenuWindow
from bauiv1lib.account.settings import AccountSettingsWindow
from bauiv1lib.colorpicker import ColorPicker, ColorPickerExact
from bauiv1lib.fileselector import FileSelectorWindow
from bauiv1lib.popup import PopupMenuWindow

import _babase as _ba
import babase as ba
import bascenev1 as bs
import bauiv1 as bui
import bascenev1lib.mainmenu as menu
import json
import os
import shutil
import random
import weakref


# defined version and author
__author__ = "Yann"
__version__ = "1.0.9"

# frequently used variables references
config = bs.app.config
ui_type = bs.app.ui_v1.uiscale
ui_small = bs.UIScale.SMALL
ui_medium = bs.UIScale.MEDIUM
ui_large = bs.UIScale.LARGE

# method references
original_unlocked_pro = bs.app.classic.accounts.have_pro
original_account_init = AccountSettingsWindow.__init__

# define globals
GLOBALS_REFLECTION = {
    'Powerup': 'powerup',
    'Character': 'char',
    'Soft': 'soft',
    'None': 'none'
}
GLOBALS_MUSIC = {
    'Menu': bs.MusicType.MENU,
    'Epic': bs.MusicType.EPIC,
    'Flag Catcher': bs.MusicType.FLAG_CATCHER,
    'Flying': bs.MusicType.FLYING,
    'Grand Romp': bs.MusicType.GRAND_ROMP,
    'Lobby': bs.MusicType.CHAR_SELECT,
    'Lobby Epic': bs.MusicType.SCORES,
    'Marching Forward': bs.MusicType.FORWARD_MARCH,
    'Marching Home': bs.MusicType.MARCHING,
    'Run Away': bs.MusicType.RUN_AWAY,
    'Scary': bs.MusicType.SCARY,
    'Sports': bs.MusicType.SPORTS,
    'Survival': bs.MusicType.SURVIVAL,
    'To The Death': bs.MusicType.TO_THE_DEATH,
    'None': None,
}
GLOBALS_MAPDATA = {
    "The Pad (with trees)": {
        "Camera Bounds": (0.3544110667, 4.493562578, -2.518391331, 16.64754831, 8.06138989, 18.5029888),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.3,
        "Ambient": (1.14, 1.1, 1.0),
        "Tint": (1.06, 1.04, 1.03),
        "Vignette Outer": (0.45, 0.55, 0.54),
        "Vignette Inner": (0.99, 0.98, 0.98)
    },
    "The Pad": {
        "Camera Bounds": (0.3544110667, 4.493562578, -2.518391331, 16.64754831, 8.06138989, 18.5029888),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.3,
        "Ambient": (1.1, 1.1, 1.0),
        "Tint": (1.1, 1.1, 1.0),
        "Vignette Outer": (0.7, 0.65, 0.75),
        "Vignette Inner": (0.95, 0.95, 0.93)
    },
    "Big G": {
        "Camera Bounds": (-0.4011866709, 2.331310176, -0.5426286416, 19.11746262, 10.19675564, 23.50119277),
        "Map Color": (0.7, 0.7, 0.7),
        "Map Reflection Scale": 0.0,
        "Ambient": (1.1, 1.2, 1.3),
        "Tint": (1.1, 1.2, 1.3),
        "Vignette Outer": (0.65, 0.6, 0.55),
        "Vignette Inner": (0.9, 0.9, 0.93)
    },
    "Bridgit": {
        "Camera Bounds": (-0.2457963347, 3.828181068, -1.528362695, 19.14849937, 7.312788846, 8.436232726),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.0,
        "Ambient": (1.1, 1.2, 1.3),
        "Tint": (1.1, 1.2, 1.3),
        "Vignette Outer": (0.65, 0.6, 0.55),
        "Vignette Inner": (0.9, 0.9, 0.93)
    },
    "Courtyard": {
        "Camera Bounds": (0.3544110667, 3.958431362, -2.175025358, 16.37702017, 7.755670126, 13.38680645),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.0,
        "Ambient": (1.2, 1.17, 1.1),
        "Tint": (1.2, 1.17, 1.1),
        "Vignette Outer": (0.6, 0.6, 0.64),
        "Vignette Inner": (0.95, 0.95, 0.93)
    },
    "Crag Castle": {
        "Camera Bounds": (0.7033834902, 6.55869393, -3.153439808, 16.73648528, 14.94789935, 11.60063102),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.0,
        "Ambient": (1.15, 1.05, 0.75),
        "Tint": (1.15, 1.05, 0.75),
        "Vignette Outer": (0.6, 0.65, 0.6),
        "Vignette Inner": (0.95, 0.95, 0.95)
    },
    "Doom Shroom": {
        "Camera Bounds": (0.4687647786, 2.320345088, -3.219423694, 21.34898078, 10.25529817, 14.67298352),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.0,
        "Ambient": (0.9, 1.3, 1.1),
        "Tint": (0.82, 1.10, 1.15),
        "Vignette Outer": (0.76, 0.76, 0.76),
        "Vignette Inner": (0.95, 0.95, 0.99)
    },
    "Happy Thoughts": {
        "Camera Bounds": (-1.045859963, 12.67722855, -5.401537075, 34.46156851, 20.94044653, 0.6931564611),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.0,
        "Ambient": (1.3, 1.23, 1.0),
        "Tint": (1.3, 1.23, 1.0),
        "Vignette Outer": (0.64, 0.59, 0.69),
        "Vignette Inner": (0.95, 0.95, 0.93)
    },
    "Football Stadium": {
        "Camera Bounds": (0.0, 1.185751251, 0.4326226188, 29.8180273, 11.57249038, 18.89134176),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.0,
        "Ambient": (1.3, 1.2, 1.0),
        "Tint": (1.3, 1.2, 1.0),
        "Vignette Outer": (0.57, 0.57, 0.57),
        "Vignette Inner": (0.9, 0.9, 0.9)
    },
    "Hockey Stadium": {
        "Camera Bounds": (0.0, 0.7956858119, 0.0, 30.80223883, 0.5961646365, 13.88431707),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.3,
        "Ambient": (1.15, 1.25, 1.6),
        "Tint": (1.2, 1.3, 1.33),
        "Vignette Outer": (0.66, 0.67, 0.73),
        "Vignette Inner": (0.93, 0.93, 0.95)
    },
    "Lake Frigid": {
        "Camera Bounds": (0.622753268, 3.958431362, -2.48708008, 20.62310543, 7.755670126, 12.33155049),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.0,
        "Ambient": (1, 1, 1),
        "Tint": (1, 1, 1),
        "Vignette Outer": (0.86, 0.86, 0.86),
        "Vignette Inner": (0.95, 0.95, 0.99)
    },
    "Monkey Face": {
        "Camera Bounds": (-1.657177611, 4.132574186, -1.580485661, 17.36258946, 10.49020453, 12.31460338),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.0,
        "Ambient": (1.1, 1.2, 1.2),
        "Tint": (1.1, 1.2, 1.2),
        "Vignette Outer": (0.60, 0.62, 0.66),
        "Vignette Inner": (0.97, 0.95, 0.93)
    },
    "Rampage": {
        "Camera Bounds": (0.3544110667, 5.616383286, -4.066055072, 19.90053969, 10.34051135, 8.16221072),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.0,
        "Ambient": (1.3, 1.2, 1.03),
        "Tint": (1.2, 1.1, 0.97),
        "Vignette Outer": (0.62, 0.64, 0.69),
        "Vignette Inner": (0.97, 0.95, 0.93)
    },
    "Roundabout": {
        "Camera Bounds": (-1.552280404, 3.189001207, -2.40908495, 11.96255385, 8.857531648, 9.531689995),
        "Map Color": (0.7, 0.7, 0.7),
        "Map Reflection Scale": 0.0,
        "Ambient": (1.0, 1.05, 1.1),
        "Tint": (1.0, 1.05, 1.1),
        "Vignette Outer": (0.63, 0.65, 0.7),
        "Vignette Inner": (0.97, 0.95, 0.93)
    },
    "Step Right Up": {
        "Camera Bounds": (0.3544110667, 6.07676405, -2.271833016, 22.55121262, 10.14644532, 14.66087273),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.0,
        "Ambient": (1.2, 1.1, 1.0),
        "Tint": (1.2, 1.1, 1.0),
        "Vignette Outer": (1.2, 1.1, 1.0),
        "Vignette Inner": (0.95, 0.95, 0.93)
    },
    "Tower D": {
        "Camera Bounds": (-0.4714933293, 2.887077774, -1.505479919, 17.90145968, 6.188484831, 15.96149117),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.0,
        "Ambient": (1.2, 1.1, 1.0),
        "Tint": (1.15, 1.11, 1.03),
        "Vignette Outer": (1.2, 1.1, 1.0),
        "Vignette Inner": (0.95, 0.95, 0.95)
    },
    "Tip Top": {
        "Camera Bounds": (0.004375512593, 7.141135803, -0.01745294675, 21.12506141, 4.959977313, 16.6885592),
        "Map Color": (0.7, 0.7, 0.7),
        "Map Reflection Scale": 0.0,
        "Ambient": (0.8, 0.9, 1.3),
        "Tint": (0.8, 0.9, 1.3),
        "Vignette Outer": (0.79, 0.79, 0.69),
        "Vignette Inner": (0.97, 0.97, 0.99)
    },
    "Zig Zag": {
        "Camera Bounds": (-1.807378035, 3.943412768, -1.61304303, 23.01413538, 13.27980464, 10.0098376),
        "Map Color": (1.0, 1.0, 1.0),
        "Map Reflection Scale": 0.0,
        "Ambient": (1.0, 1.15, 1.15),
        "Tint": (1.0, 1.15, 1.15),
        "Vignette Outer": (0.57, 0.59, 0.63),
        "Vignette Inner": (0.97, 0.95, 0.93)
    }
}


class CustomColorPicker(ColorPicker):

    def _select_other(self):
        from bauiv1lib import purchase

        CustomColorPickerExact(parent=self._parent,
                               position=self._position,
                               initial_color=self._initial_color,
                               delegate=self._delegate,
                               scale=self._scale,
                               offset=self._offset,
                               tag=self._tag)
        self._delegate = None
        self._transition_out()


class CustomColorPickerExact(ColorPickerExact):

    def _color_change_press(self, color_name: str, increasing: bool):
        current_time = bui.apptime()
        since_last = current_time - self._last_press_time
        if (
            since_last < 0.2
            and self._last_press_color_name == color_name
            and self._last_press_increasing == increasing
        ):
            self._change_speed += 0.25
        else:
            self._change_speed = 1.0
        self._last_press_time = current_time
        self._last_press_color_name = color_name
        self._last_press_increasing = increasing

        color_index = ('r', 'g', 'b').index(color_name)
        offs = int(self._change_speed) * (0.01 if increasing else -0.01)
        self._color[color_index] = max(
            -1.0, min(2.55, self._color[color_index] + offs)
        )
        self._update_for_color()


class ConfigCheckBox:
    widget: bui.Widget

    def __init__(
            self,
            parent: bui.Widget,
            configkey: str,
            position: tuple[float, float],
            size: tuple[float, float],
            displayname: str | bs.Lstr | None = None,
            scale: float | None = None,
            maxwidth: float | None = None,
            autoselect: bool = True,
            value_change_call: Callable[[Any], Any] | None = None):

        if displayname is None:
            displayname = configkey
        self._value_change_call = value_change_call
        self._configkey = configkey
        self.widget = bui.checkboxwidget(
            parent=parent,
            autoselect=autoselect,
            position=position,
            size=size,
            text=displayname,
            textcolor=(0.8, 0.8, 0.8),
            value=bs.app.config[configkey],
            on_value_change_call=self._value_changed,
            scale=scale,
            maxwidth=maxwidth,
        )
        # complain if we outlive our checkbox
        bui.uicleanupcheck(self, self.widget)

    def _value_changed(self, val: bool):
        cfg = bs.app.config
        cfg[self._configkey] = val
        if self._value_change_call is not None:
            self._value_change_call(val)
        cfg.apply_and_commit()


class FreeEditWindow(bui.Window):

    def _do_enter(self):

        def _error() -> None:
            bui.getsound('error').play(volume=2.0)
            bui.screenmessage('error ' + u'😑😑', color=(1.0, 0.0, 0.0))

        try:
            if self.name_only:
                value = bui.textwidget(query=self._text_field)
                if not value.strip():
                    return _error()

                self.delegate._export(self, txt=value)
            else:
                value = round(float(bui.textwidget(query=self._text_field)), 4)
                self.delegate.free_edit_enter(self, c=self.config_name, txt=value)

        except ValueError:
            return _error()
        bui.containerwidget(edit=self._root_widget, transition=self._transition_out)

    def _activate_enter_button(self):
        self._enter_button.activate()

    def _do_back(self):
        bui.containerwidget(edit=self._root_widget, transition=self._transition_out)

    def __init__(self, delegate: Any = None, config_name: str = 'Menu Map', whitelist: List = [], name_only: bool = False, origin_widget: bui.widget = None):
        self._transition_out = 'out_scale' if origin_widget else 'out_right'
        scale_origin = origin_widget.get_screen_space_center() if origin_widget else None
        transition = 'in_scale' if origin_widget else 'in_right'
        width, height = 450, 230
        uiscale = bs.app.ui_v1.uiscale

        super().__init__(root_widget=bui.containerwidget(
            size=(width, height),
            transition=transition,
            toolbar_visibility='menu_minimal_no_back',
            scale_origin_stack_offset=scale_origin,
            scale=(2.0 if uiscale is bs.UIScale.SMALL else
                   1.5 if uiscale is bs.UIScale.MEDIUM else 1.0)))

        btn = bui.buttonwidget(parent=self._root_widget,
                               scale=0.5,
                               position=(40, height - 40),
                               size=(60, 60),
                               label='',
                               on_activate_call=self._do_back,
                               autoselect=True,
                               color=(0.55, 0.5, 0.6),
                               icon=bui.gettexture('crossOut'),
                               iconscale=1.2)

        self.config_name, self.delegate, self.name_only = config_name, delegate, name_only

        self._text_field = bui.textwidget(
            parent=self._root_widget,
            position=(125, height - 121),
            size=(280, 46),
            text='',
            h_align='left',
            v_align='center',
            color=(0.9, 0.9, 0.9, 1.0),
            description='',
            editable=True,
            padding=4,
            max_chars=20 if name_only else 5,
            on_return_press_call=self._activate_enter_button)

        bui.textwidget(parent=self._root_widget,
                       text='Current: ' + str(config[config_name]) if not name_only else 'Save as',
                       position=(220, height - 44),
                       color=(0.5, 0.5, 0.5, 1.0),
                       size=(90, 30),
                       h_align='right')

        bui.widget(edit=btn, down_widget=self._text_field)

        b_width = 200
        self._enter_button = btn2 = bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.5 - b_width * 0.5, height - 200),
            size=(b_width, 60),
            scale=1.0,
            label='Enter',
            on_activate_call=self._do_enter)
        bui.containerwidget(edit=self._root_widget,
                            cancel_button=btn,
                            start_button=btn2,
                            selected_child=self._text_field)


class MenuThemeWindow:
    def __init__(self, origin_widget: bui.widget = None, accounts_window=None):
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None
            transition = 'in_right'

        self._choice_page: str = None
        self._accounts_window = accounts_window
        height = 500 if ui_type is ui_small else 772

        self._root_widget = bui.containerwidget(
            size=(445, 365) if ui_type is ui_small else (799, 576),
            transition=transition,
            toolbar_visibility='menu_minimal',
            scale_origin_stack_offset=scale_origin,
            scale=2.23 if ui_type is ui_small else 1.0,
            stack_offset=(0, -35) if ui_type is ui_small else (0, 0)
        )

        self._scroll_border_parent = bui.scrollwidget(
            parent=self._root_widget,
            position=(39, 58) if ui_type is ui_small else (86, 39),
            size=(375, 240) if ui_type is ui_small else (645, 463),
            color=(0.52, 0.48, 0.63)
        )

        self._scroll_parent = bui.containerwidget(
            parent=self._scroll_border_parent,
            size=(450, height),
            background=False,
            claims_left_right=False,
            claims_tab=False
        )

        self._back_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(23, 310) if ui_type is ui_small else (80, 511),
            size=(35, 35) if ui_type is ui_small else (55, 55),
            color=(0.76, 0.42, 0.38),
            button_type="backSmall",
            textcolor=(1, 1, 1),
            text_scale=0.8 if ui_type is ui_small else 1.0,
            label="",
            autoselect=True,
            on_activate_call=bs.Call(self.close)
        )

        self._home_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(383, 308) if ui_type is ui_small else (688, 511),
            size=(60, 60) if ui_type is ui_small else (55, 55),
            color=(0.76, 0.42, 0.38),
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
            scale=0.59 if ui_type is ui_small else 0.92,
            label="",
            autoselect=True,
            on_activate_call=bs.Call(self.close_all)
        )

        # menutheme title
        bui.textwidget(
            parent=self._root_widget,
            position=(225, 327) if ui_type is ui_small else (415, 547),
            size=(0, 0),
            text="Menu Theme",
            color=(0.8, 0.8, 0.8, 0.76),
            maxwidth=290,
            scale=0.95 if ui_type is ui_small else 1.25,
            h_align='center',
            v_align='center'
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(225, 309) if ui_type is ui_small else (415, 517),
            size=(0, 0),
            text=f"version: {__version__}",
            color=(0.6, 0.6, 0.6, 0.8),
            maxwidth=290,
            scale=0.454 if ui_type is ui_small else 0.653,
            h_align='center',
            v_align='center'
        )

        # settings txt
        bui.textwidget(
            parent=self._scroll_parent,
            position=(10, height - 27) if ui_type is ui_small else (30, height - 47),
            size=(0, 0),
            text="Map Type:",
            color=(1, 1, 1, 0.8),
            maxwidth=290,
            scale=0.7 if ui_type is ui_small else 1.3,
            h_align='left',
            v_align='center'
        )

        bui.textwidget(
            parent=self._scroll_parent,
            position=(10, height - 65) if ui_type is ui_small else (30, height - 104),
            size=(0, 0),
            text="Music:",
            color=(1, 1, 1, 0.8),
            maxwidth=290,
            scale=0.7 if ui_type is ui_small else 1.3,
            h_align='left',
            v_align='center'
        )

        bui.textwidget(
            parent=self._scroll_parent,
            position=(25, height - 147) if ui_type is ui_small else (45, height - 239),
            size=(0, 0),
            text="tint",
            color=(1, 1, 1, 0.8),
            maxwidth=290,
            scale=0.5 if ui_type is ui_small else 1.0,
            h_align='left',
            v_align='center'
        )

        bui.textwidget(
            parent=self._scroll_parent,
            position=(81, height - 147) if ui_type is ui_small else (140, height - 239),
            size=(0, 0),
            text="ambient",
            color=(1, 1, 1, 0.8),
            maxwidth=290,
            scale=0.5 if ui_type is ui_small else 1.0,
            h_align='left',
            v_align='center'
        )

        bui.textwidget(
            parent=self._scroll_parent,
            position=(147, height - 156) if ui_type is ui_small else (262, height - 258),
            size=(0, 0),
            text="vignette\n outer",
            color=(1, 1, 1, 0.8),
            maxwidth=290,
            scale=0.5 if ui_type is ui_small else 1.0,
            h_align='left',
            v_align='center'
        )

        bui.textwidget(
            parent=self._scroll_parent,
            position=(213, height - 156) if ui_type is ui_small else (382, height - 258),
            size=(0, 0),
            text="vignette\n inner",
            color=(1, 1, 1, 0.8),
            maxwidth=290,
            scale=0.5 if ui_type is ui_small else 1.0,
            h_align='left',
            v_align='center'
        )

        bui.textwidget(
            parent=self._scroll_parent,
            position=(279, height - 156) if ui_type is ui_small else (500, height - 258),
            size=(0, 0),
            text="reflection\n color",
            color=(1, 1, 1, 0.8),
            maxwidth=290,
            scale=0.5 if ui_type is ui_small else 1.0,
            h_align='left',
            v_align='center'
        )

        bui.textwidget(
            parent=self._scroll_parent,
            position=(10, height - 193) if ui_type is ui_small else (30, height - 320),
            size=(0, 0),
            text="Reflection Type:",
            color=(1, 1, 1, 0.8),
            maxwidth=290,
            scale=0.7 if ui_type is ui_small else 1.3,
            h_align='left',
            v_align='center'
        )

        bui.textwidget(
            parent=self._scroll_parent,
            position=(10, height - 227) if ui_type is ui_small else (30, height - 373),
            size=(0, 0),
            text="Reflection Scale:",
            color=(1, 1, 1, 0.8),
            maxwidth=290,
            scale=0.7 if ui_type is ui_small else 1.3,
            h_align='left',
            v_align='center'
        )

        bui.textwidget(
            parent=self._scroll_parent,
            position=(10, height - 260) if ui_type is ui_small else (30, height - 423),
            size=(0, 0),
            text="Camera Mode:",
            color=(1, 1, 1, 0.8),
            maxwidth=290,
            scale=0.7 if ui_type is ui_small else 1.3,
            h_align='left',
            v_align='center'
        )

        bui.textwidget(
            parent=self._scroll_parent,
            position=(10, height - 294) if ui_type is ui_small else (30, height - 480),
            size=(0, 0),
            text="Show Logo Text:",
            color=(1, 1, 1, 0.8),
            maxwidth=290,
            scale=0.7 if ui_type is ui_small else 1.3,
            h_align='left',
            v_align='center'
        )

        # prioritize this first for:
        # >> handling config-errors
        # >> debugging
        self._menu_configreset_button = bui.buttonwidget(
            parent=self._scroll_parent,
            position=(5, height - 486) if ui_type is ui_small else (12, height - 765),
            size=(329, 50) if ui_type is ui_small else (600, 80),
            color=(0.0, 0.67, 0.85),
            textcolor=(0.8, 0.8, 0.8),
            button_type="regular",
            label="Reset to Default Settings",
            text_scale=0.7 if ui_type is ui_small else 1.0,
            on_activate_call=bs.Call(self.reset_config)
        )

        # settings buttons
        self._menu_map_button = bui.buttonwidget(
            parent=self._scroll_parent,
            position=(112, height - 38) if ui_type is ui_small else (206, height - 67),
            size=(87, 24) if ui_type is ui_small else (149, 40),
            button_type="regular",
            label=config["Menu Map"],
            on_activate_call=bs.Call(self.choice_window, 'Map')
        )

        self._menu_music_button = bui.buttonwidget(
            parent=self._scroll_parent,
            position=(85, height - 75) if ui_type is ui_small else (149, height - 123),
            size=(87, 24) if ui_type is ui_small else (149, 40),
            button_type="regular",
            label=config["Menu Music"],
            text_scale=0.6 if ui_type is ui_small else 1.0,
            on_activate_call=bs.Call(self.choice_window, 'Music')
        )

        self._menu_tint_button = bui.buttonwidget(
            parent=self._scroll_parent,
            color=config["Menu Tint"],
            position=(15, height - 136) if ui_type is ui_small else (30, height - 220),
            size=(40, 40) if ui_type is ui_small else (70, 70),
            button_type="square",
            label="",
            on_activate_call=bs.WeakCall(self.color_picker_popup, "Menu Tint")
        )

        self._menu_ambient_button = bui.buttonwidget(
            parent=self._scroll_parent,
            color=config["Menu Ambient"],
            position=(81, height - 136) if ui_type is ui_small else (150, height - 220),
            size=(40, 40) if ui_type is ui_small else (70, 70),
            button_type="square",
            label="",
            on_activate_call=bs.WeakCall(self.color_picker_popup, "Menu Ambient")
        )

        self._menu_vignetteO_button = bui.buttonwidget(
            parent=self._scroll_parent,
            color=config["Menu Vignette Outer"],
            position=(147, height - 136) if ui_type is ui_small else (270, height - 220),
            size=(40, 40) if ui_type is ui_small else (70, 70),
            button_type="square",
            label="",
            on_activate_call=bs.WeakCall(self.color_picker_popup, "Menu Vignette Outer")
        )

        self._menu_vignetteI_button = bui.buttonwidget(
            parent=self._scroll_parent,
            color=config["Menu Vignette Inner"],
            position=(213, height - 136) if ui_type is ui_small else (390, height - 220),
            size=(40, 40) if ui_type is ui_small else (70, 70),
            button_type="square",
            label="",
            on_activate_call=bs.WeakCall(self.color_picker_popup, "Menu Vignette Inner")
        )

        self._menu_rcolor_button = bui.buttonwidget(
            parent=self._scroll_parent,
            color=config["Menu Map Color"],
            position=(279, height - 136) if ui_type is ui_small else (510, height - 220),
            size=(40, 40) if ui_type is ui_small else (70, 70),
            button_type="square",
            label="",
            on_activate_call=bs.WeakCall(self.color_picker_popup, "Menu Map Color")
        )

        self._menu_reflectiont_button = bui.buttonwidget(
            parent=self._scroll_parent,
            position=(148, height - 204) if ui_type is ui_small else (287, height - 339),
            size=(87, 24) if ui_type is ui_small else (149, 40),
            button_type="regular",
            label=config["Menu Reflection Type"],
            text_scale=0.6 if ui_type is ui_small else 1.0,
            on_activate_call=bs.Call(self.choice_window, 'Reflection Type')
        )

        self._menu_reflections_button = bui.buttonwidget(
            parent=self._scroll_parent,
            position=(153, height - 237) if ui_type is ui_small else (289, height - 392),
            size=(87, 24) if ui_type is ui_small else (149, 40),
            button_type="regular",
            label=str(config["Menu Reflection Scale"]),
            text_scale=0.6 if ui_type is ui_small else 1.0,
            on_activate_call=lambda: FreeEditWindow(
                delegate=self, whitelist=['num'], config_name='Menu Reflection Scale')
        )

        self._menu_cameramode_button = bui.buttonwidget(
            parent=self._scroll_parent,
            position=(138, height - 272) if ui_type is ui_small else (265, height - 444),
            size=(87, 24) if ui_type is ui_small else (149, 40),
            button_type="regular",
            label=str(config["Menu Camera Mode"]),
            text_scale=0.6 if ui_type is ui_small else 1.0,
            on_activate_call=bs.Call(self.choice_window, 'Camera Mode')
        )

        self._menu_logotext_button = ConfigCheckBox(
            parent=self._scroll_parent,
            configkey="Menu Logo Text",
            position=(151, height - 308) if ui_type is ui_small else (287, height - 520),
            size=(40, 40) if ui_type is ui_small else (56, 56),
            scale=0.62 if ui_type is ui_small else 1.4,
            displayname=""
        )

        self._menu_load_button = bui.buttonwidget(
            parent=self._scroll_parent,
            position=(11, height - 365) if ui_type is ui_small else (22, height - 590),
            size=(155, 45) if ui_type is ui_small else (280, 75),
            textcolor=(0.8, 0.8, 0.8),
            button_type="regular",
            label="Load Theme",
            text_scale=0.7 if ui_type is ui_small else 1.0,
            on_activate_call=bs.Call(self.popup_fileselector)
        )

        self._menu_save_button = bui.buttonwidget(
            parent=self._scroll_parent,
            position=(178, height - 365) if ui_type is ui_small else (312, height - 590),
            size=(155, 45) if ui_type is ui_small else (280, 75),
            textcolor=(0.8, 0.8, 0.8),
            button_type="regular",
            label="Save Theme",
            text_scale=0.7 if ui_type is ui_small else 1.0,
            on_activate_call=lambda: FreeEditWindow(delegate=self, name_only=True)
        )

        self._menu_mapdata_button = bui.buttonwidget(
            parent=self._scroll_parent,
            position=(5, height - 425) if ui_type is ui_small else (12, height - 677),
            size=(329, 50) if ui_type is ui_small else (600, 80),
            color=(0.23, 0.27, 0.55),
            textcolor=(0.8, 0.8, 0.8),
            button_type="regular",
            label="Map Data Overrides",
            text_scale=0.7 if ui_type is ui_small else 1.0,
            on_activate_call=bs.Call(self.checkbox_window)
        )

    def checkbox_window(self):
        self._root_widget_checkbox = bui.containerwidget(
            size=(800, 740),
            transition='in_scale',
            toolbar_visibility='menu_minimal',
            scale_origin_stack_offset=(0, 0),
            scale=0.6 if ui_type is ui_large else 0.88 if ui_type is ui_small else 0.76,
            color=(0.17, 0.2, 0.25),
            on_outside_click_call=bs.Call(self.checkbox_window_out),
            claim_outside_clicks=True,
            stack_offset=(0, -35) if ui_type is ui_small else (0, 0)
        )
        self._button_tint = ConfigCheckBox(
            parent=self._root_widget_checkbox,
            configkey="tint",
            position=(88, 600),
            size=(380, 40),
            scale=1.9,
            displayname='Tint'
        )
        self._button_ambient = ConfigCheckBox(
            parent=self._root_widget_checkbox,
            configkey="ambient_color",
            position=(88, 510),
            size=(380, 40),
            scale=1.9,
            displayname='Ambient Color'
        )
        self._button_vignette_outer = ConfigCheckBox(
            parent=self._root_widget_checkbox,
            configkey="vignette_outer",
            position=(88, 420),
            size=(380, 40),
            scale=1.9,
            displayname='Vignette Outer'
        )
        self._button_vignette_inner = ConfigCheckBox(
            parent=self._root_widget_checkbox,
            configkey="vignette_inner",
            position=(88, 330),
            size=(380, 40),
            scale=1.9,
            displayname='Vignette Inner'
        )
        self._button_map_color = ConfigCheckBox(
            parent=self._root_widget_checkbox,
            configkey="map_color",
            position=(88, 240),
            size=(380, 40),
            scale=1.9,
            displayname='Map Color'
        )
        self._button_map_reflection_scale = ConfigCheckBox(
            parent=self._root_widget_checkbox,
            configkey="map_reflection_scale",
            position=(88, 150),
            size=(380, 40),
            scale=1.9,
            displayname='Map Reflection Scale'
        )
        self._button_map_reflection_type = ConfigCheckBox(
            parent=self._root_widget_checkbox,
            configkey="map_reflection_type",
            position=(88, 60),
            size=(380, 40),
            scale=1.9,
            displayname='Map Reflection Type'
        )

    def checkbox_window_out(self):
        # Memory-leak prevention
        bui.containerwidget(edit=self._root_widget_checkbox, transition='out_scale')
        del self._button_tint
        del self._button_ambient
        del self._button_vignette_outer
        del self._button_vignette_inner
        del self._button_map_color
        del self._button_map_reflection_scale
        del self._button_map_reflection_type

    def choice_window(self, category: str):
        choices_map = {
            'Map': [
                'Big G',
                'Bridgit',
                'Courtyard',
                'Crag Castle',
                'Doom Shroom',
                'Football Stadium',
                'Happy Thoughts',
                'Hockey Stadium',
                'Lake Frigid',
                'Monkey Face',
                'Rampage',
                'Roundabout',
                'Step Right Up',
                'The Pad',
                'The Pad (with trees)',
                'Tower D',
                'Tip Top',
                'Zig Zag'
            ],
            'Camera Mode': [
                'rotate',
                'static'
            ],
            'Reflection Type': [
                'Soft',
                'None',
                'Powerup',
                'Character'
            ],
            'Music': [
                'Menu',
                'Epic',
                'Flag Catcher',
                'Flying',
                'Grand Romp',
                'Lobby',
                'Lobby Epic',
                'Marching Forward',
                'Marching Home',
                'Run Away',
                'Scary',
                'Sports',
                'Survival',
                'To The Death',
                'None'
            ]
        }

        if category in choices_map:
            PopupMenuWindow(
                position=(0, 0),
                scale=2.0 if ui_type is ui_small else 1.0,
                delegate=self,
                current_choice=bs.app.config[f"Menu {category}"],
                choices=choices_map[category]
            )
            self._choice_page = category

    def popup_menu_selected_choice(self, window: PopupMenuWindow, choice: str):
        if self._choice_page == 'Map':
            bs.app.config['Menu Map'] = choice
            if config["tint"]:
                bs.app.config["Menu Tint"] = GLOBALS_MAPDATA.get(config["Menu Map"]).get("Tint")
            if config["ambient_color"]:
                bs.app.config["Menu Ambient"] = GLOBALS_MAPDATA.get(
                    config["Menu Map"]).get("Ambient")
            if config["vignette_outer"]:
                bs.app.config["Menu Vignette Outer"] = GLOBALS_MAPDATA.get(
                    config["Menu Map"]).get("Vignette Outer")
            if config["vignette_inner"]:
                bs.app.config["Menu Vignette Inner"] = GLOBALS_MAPDATA.get(
                    config["Menu Map"]).get("Vignette Inner")
            if config["map_color"]:
                bs.app.config["Menu Map Color"] = GLOBALS_MAPDATA.get(
                    config["Menu Map"]).get("Map Color")
            if config["map_reflection_scale"]:
                bs.app.config["Menu Reflection Scale"] = GLOBALS_MAPDATA.get(
                    config["Menu Map"]).get("Map Reflection Scale")
            if config["map_reflection_type"]:
                bs.app.config["Menu Reflection Type"] = 'Soft'

        elif self._choice_page == 'Music':
            bs.app.config['Menu Music'] = choice

        elif self._choice_page == 'Reflection Type':
            bs.app.config['Menu Reflection Type'] = choice

        elif self._choice_page == 'Camera Mode':
            bs.app.config['Menu Camera Mode'] = choice
        bs.app.config.apply_and_commit()
        self.update_buttons()

    def popup_menu_closing(self, window: PopupMenuWindow):
        self._choice_page = None
        self.update_buttons()

    def popup_fileselector(self):
        self._file_selector = FileSelectorWindow(
            path=str(_ba.env()['python_directory_user']),
            callback=self._import,
            show_base_path=True,
            valid_file_extensions=['json'],
            allow_folders=False
        )

    def _import(self, path: str = None):
        try:
            self.path = path + '/'
            self.path = self.path[:-1]
            with open(self.path, 'r') as imported:
                selected = json.load(imported)
                handle_config([
                    selected["Menu Map"],
                    selected["Menu Tint"],
                    selected["Menu Ambient"],
                    selected["Menu Vignette Outer"],
                    selected["Menu Vignette Inner"],
                    selected["Menu Music"],
                    selected["Menu Map Color"],
                    selected["Menu Reflection Scale"],
                    selected["Menu Reflection Type"],
                    selected["Menu Camera Mode"],
                    selected["Menu Logo Text"],
                    selected["vignette_outer"],
                    selected["vignette_inner"],
                    selected["ambient_color"],
                    selected["tint"],
                    selected["map_reflection_scale"],
                    selected["map_reflection_type"],
                    selected["map_color"]],
                    False
                )
                self.update_buttons()
                bui.screenmessage(
                    f"Loaded {os.path.splitext(os.path.basename(self.path))[0]}!", color=(0.2, 0.4, 1.0))
        except:
            pass
        del self._file_selector

    def _export(self, window: FreeEditWindow, txt: Any):
        path = _ba.env()['python_directory_user'] + "/_menutheme/"
        try:
            a = _ba.env()['python_directory_user'] + "/_menutheme"
            os.makedirs(a, exist_ok=False)
        except:
            pass

        with open(path + txt + '.json', 'w') as file:
            my_config = {
                "Menu Map": config["Menu Map"],
                "Menu Tint": config["Menu Tint"],
                "Menu Ambient": config["Menu Ambient"],
                "Menu Vignette Outer": config["Menu Vignette Outer"],
                "Menu Vignette Inner": config["Menu Vignette Inner"],
                "Menu Music": config["Menu Music"],
                "Menu Map Color": config["Menu Map Color"],
                "Menu Reflection Scale": config["Menu Reflection Scale"],
                "Menu Reflection Type": config["Menu Reflection Type"],
                "Menu Camera Mode": config["Menu Camera Mode"],
                "Menu Logo Text": config["Menu Logo Text"],
                "vignette_outer": config["vignette_outer"],
                "vignette_inner": config["vignette_inner"],
                "ambient_color": config["ambient_color"],
                "tint": config["tint"],
                "map_color": config["map_color"],
                "map_reflection_scale": config["map_reflection_scale"],
                "map_reflection_type": config["map_reflection_type"]
            }
            json.dump(my_config, file, indent=4)
            bui.screenmessage(
                f"Saved {os.path.splitext(os.path.basename(path+txt+'.json'))[0]}!", color=(0.2, 0.4, 1.0))
            bui.getsound('gunCocking').play()

    def color_picker_popup(self, tag: str):
        bs.app.classic.accounts.have_pro = lambda: True
        CustomColorPicker(parent=self._root_widget,
                          position=(0, 0),
                          initial_color=config[tag],
                          delegate=self,
                          tag=tag)

    def color_picker_selected_color(self, picker: CustomColorPicker, color: Sequence[float, float, float]):
        if not self._root_widget:
            return
        self.update_color(tag=picker.get_tag(), color=color)
        self.update_buttons()

    def color_picker_closing(self, picker: ColorPicker):
        bs.app.classic.accounts.have_pro = original_unlocked_pro

    def free_edit_enter(self, window: FreeEditWindow, c: Any, txt: Any):
        bs.app.config[c] = float(txt)
        bs.app.config.apply_and_commit()
        self.update_buttons()

    def update_buttons(self):
        # menu labels
        bui.buttonwidget(edit=self._menu_map_button, label=config['Menu Map'])
        bui.buttonwidget(edit=self._menu_music_button, label=config['Menu Music'])
        bui.buttonwidget(edit=self._menu_reflectiont_button, label=config['Menu Reflection Type'])

        # menu colors
        bui.buttonwidget(edit=self._menu_tint_button, color=config['Menu Tint'])
        bui.buttonwidget(edit=self._menu_ambient_button, color=config['Menu Ambient'])
        bui.buttonwidget(edit=self._menu_vignetteO_button, color=config['Menu Vignette Outer'])
        bui.buttonwidget(edit=self._menu_vignetteI_button, color=config['Menu Vignette Inner'])
        bui.buttonwidget(edit=self._menu_rcolor_button, color=config['Menu Map Color'])

        # menu values
        bui.buttonwidget(edit=self._menu_reflections_button,
                         label=str(config['Menu Reflection Scale']))
        bui.buttonwidget(edit=self._menu_cameramode_button, label=str(config['Menu Camera Mode']))
        bui.checkboxwidget(edit=self._menu_logotext_button.widget, value=config['Menu Logo Text'])

    def update_color(self, tag: str, color: tuple[float, float, float]):
        bs.app.config[tag] = color
        bs.app.config.apply_and_commit()

    def reset_config(self):
        handle_config([
            "The Pad (with trees)",
            (1.14, 1.1, 1.0), (1.06, 1.04, 1.03),
            (0.45, 0.55, 0.54), (0.99, 0.98, 0.98), "Menu",
            (1.0, 1.0, 1.0), 0.3, 'None', 'rotate',
            True, True, True, True, True, True, True, True, True
        ], False
        )
        self.update_buttons()
        bui.screenmessage('Reset Settings', color=(0, 1, 0))

    def close(self):
        self._accounts_window = None
        bui.containerwidget(edit=self._root_widget, transition='out_scale')

    def close_all(self):
        accounts_window = self._accounts_window
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
        accounts_window._back(False)


class MainMenuTheme(MainMenuActivity):

    def _start_preloads(self):
        if self.expired:
            return
        with self.context:
            _preload1()

        bui.apptimer(0.5, self._start_menu_music)

    def _start_menu_music(self):
        music = GLOBALS_MUSIC.get(config['Menu Music'])
        if music is not None:
            bs.setmusic(music)

    def _make_word(self, *args, **kwargs) -> None:
        if not config['Menu Logo Text']:
            return
        super()._make_word(*args, **kwargs)

    def _make_logo(self, *args, **kwargs) -> None:
        if not config['Menu Logo Text']:
            return
        super()._make_logo(*args, **kwargs)

    def on_transition_in(self):
        bs.Activity.on_transition_in(self)
        random.seed(123)
        app = bs.app
        assert app.classic is not None

        plus = bui.app.plus
        assert plus is not None

        vr_mode = bs.app.vr_mode

        if not bs.app.toolbar_test:
            color = (1.0, 1.0, 1.0, 1.0) if vr_mode else (0.5, 0.6, 0.5, 0.6)

            scale = (
                0.9
                if (app.ui_v1.uiscale is bs.UIScale.SMALL or vr_mode)
                else 0.7
            )
            self.my_name = bs.NodeActor(
                bs.newnode(
                    'text',
                    attrs={
                        'v_attach': 'bottom',
                        'h_align': 'center',
                        'color': color,
                        'flatness': 1.0,
                        'shadow': 1.0 if vr_mode else 0.5,
                        'scale': scale,
                        'position': (0, 10),
                        'vr_depth': -10,
                        'text': '\xa9 2011-2023 Eric Froemling',
                    },
                )
            )

        tval = bs.Lstr(
            resource='hostIsNavigatingMenusText',
            subs=[('${HOST}', plus.get_v1_account_display_string())],
        )
        self._host_is_navigating_text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'text': tval,
                    'client_only': True,
                    'position': (0, -200),
                    'flatness': 1.0,
                    'h_align': 'center',
                },
            )
        )
        if not app.classic.main_menu_did_initial_transition and hasattr(
            self, 'my_name'
        ):
            assert self.my_name is not None
            assert self.my_name.node
            bs.animate(self.my_name.node, 'opacity', {2.3: 0, 3.0: 1.0})

        vr_mode = app.vr_mode
        uiscale = app.ui_v1.uiscale

        force_show_build_number = False

        if not bs.app.toolbar_test:
            if app.debug_build or app.test_build or force_show_build_number:
                if app.debug_build:
                    text = bs.Lstr(
                        value='${V} (${B}) (${D})',
                        subs=[
                            ('${V}', app.version),
                            ('${B}', str(app.build_number)),
                            ('${D}', bs.Lstr(resource='debugText')),
                        ],
                    )
                else:
                    text = bs.Lstr(
                        value='${V} (${B})',
                        subs=[
                            ('${V}', app.version),
                            ('${B}', str(app.build_number)),
                        ],
                    )
            else:
                text = bs.Lstr(value='${V}', subs=[('${V}', app.version)])
            scale = 0.9 if (uiscale is bs.UIScale.SMALL or vr_mode) else 0.7
            color = (1, 1, 1, 1) if vr_mode else (0.5, 0.6, 0.5, 0.7)
            self.version = bs.NodeActor(
                bs.newnode(
                    'text',
                    attrs={
                        'v_attach': 'bottom',
                        'h_attach': 'right',
                        'h_align': 'right',
                        'flatness': 1.0,
                        'vr_depth': -10,
                        'shadow': 1.0 if vr_mode else 0.5,
                        'color': color,
                        'scale': scale,
                        'position': (-260, 10) if vr_mode else (-10, 10),
                        'text': text,
                    },
                )
            )
            if not app.classic.main_menu_did_initial_transition:
                assert self.version.node
                bs.animate(self.version.node, 'opacity', {2.3: 0, 3.0: 1.0})

        self.beta_info = self.beta_info_2 = None
        if app.test_build and not (app.demo_mode or app.arcade_mode) and config['Menu Logo Text']:
            pos = (230, 35)
            self.beta_info = bs.NodeActor(
                bs.newnode(
                    'text',
                    attrs={
                        'v_attach': 'center',
                        'h_align': 'center',
                        'color': (1, 1, 1, 1),
                        'shadow': 0.5,
                        'flatness': 0.5,
                        'scale': 1,
                        'vr_depth': -60,
                        'position': pos,
                        'text': bs.Lstr(resource='testBuildText'),
                    },
                )
            )
            if not app.classic.main_menu_did_initial_transition:
                assert self.beta_info.node
                bs.animate(self.beta_info.node, 'opacity', {1.3: 0, 1.8: 1.0})

        b = GLOBALS_MAPDATA.get(config["Menu Map"]).get("Camera Bounds")
        b = (
            b[0] - b[3] / 2.0,
            b[1] - b[4] / 2.0,
            b[2] - b[5] / 2.0,
            b[0] + b[3] / 2.0,
            b[1] + b[4] / 2.0,
            b[2] + b[5] / 2.0
        )

        gnode = self.globalsnode
        gnode.camera_mode = 'follow' if config["Menu Camera Mode"] == 'static' else 'rotate'

        self.load_map_stuff()
        gnode.tint = config["Menu Tint"]
        gnode.ambient_color = config["Menu Ambient"]
        gnode.vignette_outer = config["Menu Vignette Outer"]
        gnode.vignette_inner = config["Menu Vignette Inner"]
        gnode.area_of_interest_bounds = b

        self.main.node.color = config["Menu Map Color"]
        self.main.node.reflection = GLOBALS_REFLECTION[config["Menu Reflection Type"]]
        self.main.node.reflection_scale = [float(config["Menu Reflection Scale"])]

        self._update_timer = bs.Timer(1.0, self._update, repeat=True)
        self._update()

        bui.add_clean_frame_callback(bs.WeakCall(self._start_preloads))

        random.seed()

        if not (app.demo_mode or app.arcade_mode) and not app.toolbar_test:
            self._news = NewsDisplay(self)

        with bs.ContextRef.empty():
            from bauiv1lib import specialoffer

            assert bs.app.classic is not None
            if bool(False):
                uicontroller = bs.app.ui_v1.controller
                assert uicontroller is not None
                uicontroller.show_main_menu()
            else:
                main_menu_location = bs.app.ui_v1.get_main_menu_location()

                # When coming back from a kiosk-mode game, jump to
                # the kiosk start screen.
                if bs.app.demo_mode or bs.app.arcade_mode:
                    # pylint: disable=cyclic-import
                    from bauiv1lib.kiosk import KioskWindow

                    bs.app.ui_v1.set_main_menu_window(
                        KioskWindow().get_root_widget()
                    )
                # ..or in normal cases go back to the main menu
                else:
                    if main_menu_location == 'Gather':
                        # pylint: disable=cyclic-import
                        from bauiv1lib.gather import GatherWindow

                        bs.app.ui_v1.set_main_menu_window(
                            GatherWindow(transition=None).get_root_widget()
                        )
                    elif main_menu_location == 'Watch':
                        # pylint: disable=cyclic-import
                        from bauiv1lib.watch import WatchWindow

                        bs.app.ui_v1.set_main_menu_window(
                            WatchWindow(transition=None).get_root_widget()
                        )
                    elif main_menu_location == 'Team Game Select':
                        # pylint: disable=cyclic-import
                        from bauiv1lib.playlist.browser import (
                            PlaylistBrowserWindow,
                        )

                        bs.app.ui_v1.set_main_menu_window(
                            PlaylistBrowserWindow(
                                sessiontype=bs.DualTeamSession, transition=None
                            ).get_root_widget()
                        )
                    elif main_menu_location == 'Free-for-All Game Select':
                        # pylint: disable=cyclic-import
                        from bauiv1lib.playlist.browser import (
                            PlaylistBrowserWindow,
                        )

                        bs.app.ui_v1.set_main_menu_window(
                            PlaylistBrowserWindow(
                                sessiontype=bs.FreeForAllSession,
                                transition=None,
                            ).get_root_widget()
                        )
                    elif main_menu_location == 'Coop Select':
                        # pylint: disable=cyclic-import
                        from bauiv1lib.coop.browser import CoopBrowserWindow

                        bs.app.ui_v1.set_main_menu_window(
                            CoopBrowserWindow(transition=None).get_root_widget()
                        )
                    elif main_menu_location == 'Benchmarks & Stress Tests':
                        # pylint: disable=cyclic-import
                        from bauiv1lib.debug import DebugWindow

                        bs.app.ui_v1.set_main_menu_window(
                            DebugWindow(transition=None).get_root_widget()
                        )
                    else:
                        # pylint: disable=cyclic-import
                        from bauiv1lib.mainmenu import MainMenuWindow

                        bs.app.ui_v1.set_main_menu_window(
                            MainMenuWindow(transition=None).get_root_widget()
                        )

                if not specialoffer.show_offer():

                    def try_again():
                        if not specialoffer.show_offer():
                            bui.apptimer(2.0, specialoffer.show_offer)

                    bui.apptimer(2.0, try_again)
        app.classic.main_menu_did_initial_transition = True

    def load_map_stuff(self):
        m = bs.getmesh
        t = bs.gettexture
        map_type = config["Menu Map"]
        if map_type == "The Pad (with trees)":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('thePadLevel'),
                    'color_texture': t('thePadLevelColor'),
                    'reflection': 'soft',
                    'reflection_scale': [0.3]
                }))
            self.trees = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('trees'),
                    'lighting': False,
                    'reflection': 'char',
                    'reflection_scale': [0.1],
                    'color_texture': t('treesColor')
                }))
            self.bgterrain = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('thePadBG'),
                    'color': (0.92, 0.91, 0.9),
                    'lighting': False,
                    'background': True,
                    'color_texture': t('menuBG'),
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('thePadLevelBottom'),
                    'lighting': False,
                    'reflection': 'soft',
                    'reflection_scale': [0.45],
                    'color_texture': t('thePadLevelColor')
                }))
        elif map_type == "The Pad":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('thePadLevel'),
                    'color_texture': t('thePadLevelColor'),
                    'reflection': 'soft',
                    'reflection_scale': [0.3]
                }))
            self.bgterrain = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('thePadBG'),
                    'color': (0.92, 0.91, 0.9),
                    'lighting': False,
                    'background': True,
                    'color_texture': t("menuBG")
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('thePadLevelBottom'),
                    'lighting': False,
                    'reflection': 'soft',
                    'reflection_scale': [0.45],
                    'color_texture': t('thePadLevelColor')
                }))
        elif map_type == "Hockey Stadium":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('hockeyStadiumOuter'),
                    'color_texture': t('hockeyStadium'),
                    'reflection': 'soft',
                    'reflection_scale': [0.3]
                }))
            self.inner = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('hockeyStadiumInner'),
                    'opacity': 0.92,
                    'opacity_in_low_or_ui_medium_quality': 1.0,
                    'color_texture': t('hockeyStadium')
                }))
            self.stands = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('hockeyStadiumStands'),
                    'visible_in_reflections': False,
                    'color_texture': t('footballStadium')
                }))
        elif map_type == "Football Stadium":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('footballStadium'),
                    'color_texture': t('footballStadium'),
                }))
        elif map_type == "Bridgit":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('bridgitLevelTop'),
                    'color_texture': t('bridgitLevelColor'),
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('bridgitLevelBottom'),
                    'lighting': False,
                    'color_texture': t('bridgitLevelColor'),
                }))
            self.background = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('natureBackground'),
                    'lighting': False,
                    'background': True,
                    'color_texture': t('natureBackgroundColor'),
                }))
        elif map_type == "Big G":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('bigG'),
                    'color': (0.7, 0.7, 0.7),
                    'color_texture': t('bigG'),
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('bigGBottom'),
                    'lighting': False,
                    'color': (0.7, 0.7, 0.7),
                    'color_texture': t('bigG'),
                }))
            self.background = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('natureBackground'),
                    'lighting': False,
                    'background': True,
                    'color_texture': t('natureBackgroundColor'),
                }))
        elif map_type == "Roundabout":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('roundaboutLevel'),
                    'color': (0.7, 0.7, 0.7),
                    'color_texture': t('roundaboutLevelColor'),
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('roundaboutLevelBottom'),
                    'lighting': False,
                    'color': (0.7, 0.7, 0.7),
                    'color_texture': t('roundaboutLevelColor'),
                }))
            self.background = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('natureBackground'),
                    'lighting': False,
                    'background': True,
                    'color_texture': t('natureBackgroundColor'),
                }))
        elif map_type == "Monkey Face":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('monkeyFaceLevel'),
                    'color_texture': t('monkeyFaceLevelColor'),
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('monkeyFaceLevelBottom'),
                    'lighting': False,
                    'color_texture': t('monkeyFaceLevelColor'),
                }))
            self.background = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('natureBackground'),
                    'lighting': False,
                    'color_texture': t('natureBackgroundColor'),
                }))
        elif map_type == "Monkey Face":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('monkeyFaceLevel'),
                    'color_texture': t('monkeyFaceLevelColor'),
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('monkeyFaceLevelBottom'),
                    'lighting': False,
                    'color_texture': t('monkeyFaceLevelColor'),
                }))
            self.background = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('natureBackground'),
                    'lighting': False,
                    'color_texture': t('natureBackgroundColor'),
                }))
        elif map_type == "Zig Zag":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('zigZagLevel'),
                    'color_texture': t('zigZagLevelColor'),
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('zigZagLevelBottom'),
                    'lighting': False,
                    'color_texture': t('zigZagLevelColor'),
                }))
            self.background = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('natureBackground'),
                    'lighting': False,
                    'color_texture': t('natureBackgroundColor'),
                }))
        elif map_type == "Doom Shroom":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('doomShroomLevel'),
                    'color_texture': t('doomShroomLevelColor'),
                }))
            self.stem = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('doomShroomStem'),
                    'lighting': False,
                    'color_texture': t('doomShroomLevelColor'),
                }))
            self.background = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('doomShroomBG'),
                    'lighting': False,
                    'background': True,
                    'color_texture': t('doomShroomBGColor'),
                }))
        elif map_type == "Lake Frigid":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('lakeFrigid'),
                    'color_texture': t('lakeFrigid'),
                }))
            self.top = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('lakeFrigidTop'),
                    'lighting': False,
                    'color_texture': t('lakeFrigid'),
                }))
            self.reflections = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('lakeFrigidReflections'),
                    'lighting': False,
                    'overlay': True,
                    'opacity': 0.15,
                    'color_texture': t('lakeFrigidReflections'),
                }))
        elif map_type == "Tip Top":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('tipTopLevel'),
                    'color': (0.7, 0.7, 0.7),
                    'color_texture': t('tipTopLevelColor'),
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('tipTopLevelBottom'),
                    'lighting': False,
                    'color': (0.7, 0.7, 0.7),
                    'color_texture': t('tipTopLevelColor'),
                }))
            self.background = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('tipTopBG'),
                    'lighting': False,
                    'color': (0.4, 0.4, 0.4),
                    'background': True,
                    'color_texture': t('tipTopBGColor'),
                }))
        elif map_type == "Crag Castle":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('cragCastleLevel'),
                    'color_texture': t('cragCastleLevelColor'),
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('cragCastleLevelBottom'),
                    'lighting': False,
                    'color_texture': t('cragCastleLevelColor'),
                }))
            self.background = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('thePadBG'),
                    'lighting': False,
                    'background': True,
                    'color_texture': t('menuBG'),
                }))
        elif map_type == "Tower D":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('towerDLevel'),
                    'color_texture': t('towerDLevelColor'),
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('towerDLevelBottom'),
                    'lighting': False,
                    'color_texture': t('towerDLevelColor'),
                }))
            self.background = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('thePadBG'),
                    'lighting': False,
                    'background': True,
                    'color_texture': t('menuBG'),
                }))
        elif map_type == "Happy Thoughts":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('alwaysLandLevel'),
                    'color_texture': t('alwaysLandLevelColor'),
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('alwaysLandLevelBottom'),
                    'lighting': False,
                    'color_texture': t('alwaysLandLevelColor'),
                }))
            self.background = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('alwaysLandBG'),
                    'lighting': False,
                    'background': True,
                    'color_texture': t('alwaysLandBGColor'),
                }))
        elif map_type == "Step Right Up":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('stepRightUpLevel'),
                    'color_texture': t('stepRightUpLevelColor'),
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('stepRightUpLevelBottom'),
                    'lighting': False,
                    'color_texture': t('stepRightUpLevelColor'),
                }))
            self.background = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('thePadBG'),
                    'lighting': False,
                    'background': True,
                    'color_texture': t('menuBG'),
                }))
        elif map_type == "Courtyard":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('courtyardLevel'),
                    'color_texture': t('courtyardLevelColor'),
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('courtyardLevelBottom'),
                    'lighting': False,
                    'color_texture': t('courtyardLevelColor'),
                }))
            self.background = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('thePadBG'),
                    'lighting': False,
                    'background': True,
                    'color_texture': t('menuBG'),
                }))
        elif map_type == "Rampage":
            self.main = bs.NodeActor(bs.newnode(
                'terrain',
                delegate=self,
                attrs={
                    'mesh': m('rampageLevel'),
                    'color_texture': t('rampageLevelColor'),
                }))
            self.bottom = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('rampageLevelBottom'),
                    'lighting': False,
                    'color_texture': t('rampageLevelColor'),
                }))
            self.background = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('rampageBG'),
                    'lighting': False,
                    'background': True,
                    'color_texture': t('rampageBGColor'),
                }))
            self.background_2 = bs.NodeActor(bs.newnode(
                'terrain',
                attrs={
                    'mesh': m('rampageBG2'),
                    'lighting': False,
                    'background': True,
                    'color_texture': t('rampageBGColor2'),
                }))


def menu_theme(self):
    this_class = self
    MenuThemeWindow(accounts_window=this_class)


def handle_config(keys: List[str], adding: bool = False):
    our_config = {
        "Menu Map": keys[0],
        "Menu Tint": keys[1],
        "Menu Ambient": keys[2],
        "Menu Vignette Outer": keys[3],
        "Menu Vignette Inner": keys[4],
        "Menu Music": keys[5],
        "Menu Map Color": keys[6],
        "Menu Reflection Scale": keys[7],
        "Menu Reflection Type": keys[8],
        "Menu Camera Mode": keys[9],
        "Menu Logo Text": keys[10],
        "vignette_outer": keys[11],
        "vignette_inner": keys[12],
        "ambient_color": keys[13],
        "tint": keys[14],
        "map_color": keys[15],
        "map_reflection_scale": keys[16],
        "map_reflection_type": keys[17]
    }
    config_keys = list(our_config.keys())
    p = 0

    for cf in config_keys:
        if cf not in bs.app.config and adding:
            config[cf] = keys[p]
        elif our_config[cf] is not None and not adding:
            config[cf] = keys[p]
        p += 1
    bs.app.config.apply_and_commit()


def new_init(self, *args, **kwargs):
    original_account_init(self, *args, **kwargs)

    self._menu_theme = bui.buttonwidget(
        parent=self._root_widget,
        position=((470, 330) if ui_type is ui_small else
                  (420, 434) if ui_type is ui_large else (445, 374)),
        scale=(1.2 if ui_type is ui_small else
               1.3 if ui_type is ui_large else 1.0),
        size=(160, 30) if ui_type is ui_small else (167, 30),
        color=(0.55, 0.7, 0.63),
        text_scale=(0.7 if ui_type is ui_medium else
                    0.65 if ui_type is ui_large else 0.5),
        autoselect=False,
        button_type="regular",
        label="Menu Theme",
        on_activate_call=self.menu_theme
    )
    self.previous_config = {
        "Menu Map": config["Menu Map"],
        "Menu Tint": config["Menu Tint"],
        "Menu Ambient": config["Menu Ambient"],
        "Menu Vignette Outer": config["Menu Vignette Outer"],
        "Menu Vignette Inner": config["Menu Vignette Inner"],
        "Menu Music": config["Menu Music"],
        "Menu Map Color": config["Menu Map Color"],
        "Menu Reflection Scale": config["Menu Reflection Scale"],
        "Menu Reflection Type": config["Menu Reflection Type"],
        "Menu Camera Mode": config["Menu Camera Mode"],
        "Menu Logo Text": config["Menu Logo Text"]
    }


def new_back(self, save_state: bool = True):
    assert bui.app.classic is not None
    if save_state:
        self._save_state()

    bui.containerwidget(edit=self._root_widget, transition=self._transition_out)

    main_menu_window = MainMenuWindow(transition='in_left').get_root_widget()
    bui.app.ui_v1.set_main_menu_window(main_menu_window)

    current_config = {
        "Menu Map": config["Menu Map"],
        "Menu Tint": config["Menu Tint"],
        "Menu Ambient": config["Menu Ambient"],
        "Menu Vignette Outer": config["Menu Vignette Outer"],
        "Menu Vignette Inner": config["Menu Vignette Inner"],
        "Menu Music": config["Menu Music"],
        "Menu Map Color": config["Menu Map Color"],
        "Menu Reflection Scale": config["Menu Reflection Scale"],
        "Menu Reflection Type": config["Menu Reflection Type"],
        "Menu Camera Mode": config["Menu Camera Mode"],
        "Menu Logo Text": config["Menu Logo Text"]
    }

    for x in self.previous_config:
        if current_config[x] != self.previous_config[x]:
            bs.pushcall(lambda: bs.new_host_session(menu.MainMenuSession))
            break


# ba_meta export plugin
class Plugin(ba.Plugin):
    def on_app_running(self):
        AccountSettingsWindow.__init__ = new_init
        AccountSettingsWindow._back = new_back
        AccountSettingsWindow.menu_theme = menu_theme

        menu.MainMenuActivity = MainMenuTheme

        handle_config([
            "The Pad (with trees)",
            (1.14, 1.1, 1.0), (1.06, 1.04, 1.03),
            (0.45, 0.55, 0.54), (0.99, 0.98, 0.98), "Menu",
            (1.0, 1.0, 1.0), 0.3, 'None', 'rotate',
            True, True, True, True, True, True, True, True, True
        ], True
        )
