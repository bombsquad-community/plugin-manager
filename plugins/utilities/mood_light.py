# ba_meta require api 7
from __future__ import annotations
from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
    from typing import Any, Sequence, Callable, List, Dict, Tuple, Optional, Union

import random
import ba
import _ba
from ba._map import Map
from bastd import mainmenu
from bastd.ui.party import PartyWindow
from bastd.gameutils import SharedObjects

"""mood light plugin by ʟօʊքɢǟʀօʊ
type ml in chat or use plugin manager to open settings"""


def Print(*args):
    out = " ".join(args)
    ba.screenmessage(out)


def cprint(*args):
    out = "\n".join(args)
    _ba.chatmessage(out)


try:
    Ldefault, Udefault = ba.app.config.get("moodlightingSettings")
except:
    ba.app.config["moodlightingSettings"] = (15, 20)
    Ldefault, Udefault = ba.app.config.get("moodlightingSettings")
    Print("settings up moodlight")
    Print("Type ml in chat or use plugin manager to access settings")

try:
    loop = ba.app.config.get("moodlightEnabled")
except:
    ba.app.config["moodlightEnabled"] = True
    ba.app.config.commit()
    loop = True


class SettingWindow(ba.Window):
    def __init__(self):
        self.draw_ui()

    def increase_limit(self):
        global Ldefault, Udefault
        try:
            if Udefault >= 29 and self.selected == "upper":
                ba.textwidget(edit=self.warn_text,
                              text="Careful!You risk get blind beyond this point")
            elif self.selected == "lower" and Ldefault >= -20 or self.selected == "upper" and Udefault <= 30:
                ba.textwidget(edit=self.warn_text, text="")
            if self.selected == "lower":
                Ldefault += 1
                ba.textwidget(edit=self.lower_text, text=str(Ldefault))
            elif self.selected == "upper":
                Udefault += 1
                ba.textwidget(edit=self.upper_text, text=str(Udefault))
        except AttributeError:
            ba.textwidget(edit=self.warn_text, text="Click on number to select it")

    def decrease_limit(self):
        global Ldefault, Udefault
        try:
            if Ldefault <= -19 and self.selected == "lower":
                ba.textwidget(edit=self.warn_text,
                              text="DON'T BE AFRAID OF DARK,IT'S A PLACE WHERE YOU CAN HIDE")
            elif (self.selected == "upper" and Udefault <= 30) or (self.selected == "lower" and Ldefault >= -20):
                ba.textwidget(edit=self.warn_text, text="")
            if self.selected == "lower":
                Ldefault -= 1
                ba.textwidget(edit=self.lower_text, text=str(Ldefault))
            elif self.selected == "upper":
                Udefault -= 1
                ba.textwidget(edit=self.upper_text, text=str(Udefault))
        except AttributeError:
            ba.textwidget(edit=self.warn_text, text="Click on number to select it")

    def on_text_click(self, selected):
        self.selected = selected
        if selected == "upper":
            ba.textwidget(edit=self.upper_text, color=(0, 0, 1))
            ba.textwidget(edit=self.lower_text, color=(1, 1, 1))
        elif selected == "lower":
            ba.textwidget(edit=self.lower_text, color=(0, 0, 1))
            ba.textwidget(edit=self.upper_text, color=(1, 1, 1))
        else:
            Print("this should't happen from on_text_click")

    def draw_ui(self):
        self.uiscale = ba.app.ui.uiscale

        super().__init__(
            root_widget=ba.containerwidget(
                size=(670, 670),
                on_outside_click_call=self.close,
                transition="in_right",))

        moodlight_label = ba.textwidget(
            parent=self._root_widget,
            size=(200, 100),
            position=(150, 550),
            scale=2,
            selectable=False,
            h_align="center",
            v_align="center",
            text="Mood light settings",
            color=(0, 1, 0))

        self.enable_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(100, 470),
            size=(90, 70),
            scale=1.5,
            color=(1, 0, 0) if loop else (0, 1, 0),
            label="DISABLE" if loop else "ENABLE",
            on_activate_call=self.on_enableButton_press)

        save_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(520, 470),
            size=(90, 70),
            scale=1.5,
            label="SAVE",
            on_activate_call=self.save_settings)

        self.close_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(550, 590),
            size=(35, 35),
            icon=ba.gettexture("crossOut"),
            icon_color=(1, 0.2, 0.2),
            scale=2,
            color=(1, 0.2, 0.2),
            extra_touch_border_scale=5,
            on_activate_call=self.close)

        self.lower_text = ba.textwidget(
            parent=self._root_widget,
            size=(200, 100),
            scale=2,
            position=(100, 200),
            h_align="center",
            v_align="center",
            maxwidth=400.0,
            text=str(Ldefault),
            click_activate=True,
            selectable=True)

        lower_text_label = ba.textwidget(
            parent=self._root_widget,
            size=(200, 100),
            position=(100, 150),
            h_align="center",
            v_align="center",
            text="Limit darkness")

        self.upper_text = ba.textwidget(
            parent=self._root_widget,
            size=(200, 100),
            scale=2,
            position=(400, 200),
            h_align="center",
            v_align="center",
            maxwidth=400.0,
            text=str(Udefault),
            click_activate=True,
            selectable=True)

        upper_text_label = ba.textwidget(
            parent=self._root_widget,
            size=(200, 100),
            position=(400, 150),
            h_align="center",
            v_align="center",
            text="Limit brightness")

        decrease_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(100, 100),
            size=(5, 1),
            scale=3.5,
            extra_touch_border_scale=2.5,
            icon=ba.gettexture("downButton"),
            on_activate_call=self.decrease_limit)

        increase_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(600, 100),
            size=(5, 1),
            scale=3.5,
            extra_touch_border_scale=2.5,
            icon=ba.gettexture("upButton"),
            on_activate_call=self.increase_limit)

        self.warn_text = ba.textwidget(
            parent=self._root_widget,
            text="",
            size=(400, 200),
            position=(150, 300),
            h_align="center",
            v_align="center",
            maxwidth=600)

# ++++++++++++++++for keyboard navigation++++++++++++++++
        ba.widget(edit=self.enable_button, up_widget=decrease_button,
                  down_widget=self.lower_text, left_widget=save_button, right_widget=save_button)
        ba.widget(edit=save_button, up_widget=self.close_button, down_widget=self.upper_text,
                  left_widget=self.enable_button, right_widget=self.enable_button)
        ba.widget(edit=self.close_button, up_widget=increase_button, down_widget=save_button,
                  left_widget=self.enable_button, right_widget=save_button)
        ba.widget(edit=self.lower_text, up_widget=self.enable_button, down_widget=decrease_button,
                  left_widget=self.upper_text, right_widget=self.upper_text)
        ba.widget(edit=self.upper_text, up_widget=save_button, down_widget=increase_button,
                  left_widget=self.lower_text, right_widget=self.lower_text)
        ba.widget(edit=decrease_button, up_widget=self.lower_text, down_widget=self.enable_button,
                  left_widget=increase_button, right_widget=increase_button)
        ba.widget(edit=increase_button, up_widget=self.upper_text, down_widget=self.close_button,
                  left_widget=decrease_button, right_widget=decrease_button)
# --------------------------------------------------------------------------------------------------

        ba.textwidget(edit=self.upper_text, on_activate_call=ba.Call(self.on_text_click, "upper"))
        ba.textwidget(edit=self.lower_text, on_activate_call=ba.Call(self.on_text_click, "lower"))

    def on_enableButton_press(self):
        global loop
        loop = ba.app.config.get("moodlightEnabled")
        if loop:
            loop = False
            label = "ENABLE"
            color = (0, 1, 0)
        elif not loop:
            loop = True
            label = "DISABLE"
            color = (1, 0, 0)
            Print("Restart level to enable")
        ba.app.config["moodlightEnabled"] = loop
        ba.app.config.commit()
        ba.buttonwidget(edit=self.enable_button, label=label, color=color)

    def save_settings(self):
        ba.app.config["moodlightingSettings"] = (Ldefault, Udefault)
        ba.app.config.commit()
        Print("settings saved")
        self.close()

    def close(self):
        ba.containerwidget(edit=self._root_widget, transition="out_right",)


def new_chat_message(msg: Union[str, ba.Lstr], clients: Sequence[int] = None, sender_override: str = None):
    old_fcm(msg, clients, sender_override)
    if msg == 'ml':
        try:
            global Ldefault, Udefault
            Ldefault, Udefault = ba.app.config.get("moodlightingSettings")
            SettingWindow()
            cprint("Mood light settings opened")
        except Exception as err:
            Print(err, "-from new_chat_message")


old_fcm = _ba.chatmessage
_ba.chatmessage = new_chat_message
_ba.set_party_icon_always_visible(True)
Map._old_init = Map.__init__

# ba_meta export plugin


class moodlight(ba.Plugin):
    def __init__(self):
        pass

    def on_app_running(self):
        _ba.show_progress_bar()
        
    def on_plugin_manager_prompt(self):
        SettingWindow()

    def has_settings_ui(self):
        return True

    def show_settings_ui(self, button):
        SettingWindow()

    def _new_init(self, vr_overlay_offset: Optional[Sequence[float]] = None) -> None:
        self._old_init(vr_overlay_offset)
        in_game = not isinstance(_ba.get_foreground_host_session(), mainmenu.MainMenuSession)
        if not in_game:
            return

        gnode = _ba.getactivity().globalsnode
        default_tint = (1.100000023841858, 1.0, 0.8999999761581421)
        transition_duration = 1.0  # for future improvements

        def changetint():
            if loop:
                Range = (random.randrange(Ldefault, Udefault)/10, random.randrange(Ldefault,
                         Udefault)/10, random.randrange(Ldefault, Udefault)/10)
                ba.animate_array(gnode, 'tint', 3, {
                    0.0: gnode.tint,
                    transition_duration: Range
                })
            else:
                global timer
                timer = None
                ba.animate_array(gnode, "tint", 3, {0.0: gnode.tint, 0.4: default_tint})

        global timer
        timer = ba.Timer(0.3, changetint, repeat=True)

    Map.__init__ = _new_init
