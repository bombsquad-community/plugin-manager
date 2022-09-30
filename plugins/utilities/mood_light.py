# ba_meta require api 7
from __future__ import annotations
from typing import TYPE_CHECKING, cast

import ba
import _ba
import random
from ba._map import Map
from bastd import mainmenu
from bastd.ui.party import PartyWindow
from bastd.gameutils import SharedObjects
from time import sleep
if TYPE_CHECKING:
    from typing import Any, Sequence, Callable, List, Dict, Tuple, Optional, Union

# mood light plugin by ʟօʊքɢǟʀօʊ

def Print(arg1, arg2="", arg3=""):
    ba.screenmessage(str(arg1)+str(arg2)+str(arg3))


try:
    with open("moodlightSettings.txt", "r") as mltxt:
        global Ldefault, Udefault
        data = mltxt.read()
        Ldefault, Udefault = data.split("\n")
        Ldefault = int(Ldefault)
        Udefault = int(Udefault)
except:
    with open("moodlightSettings.txt", "w") as mltxt:
        mltxt.write("15 \n 20")
        Ldefault, Udefault = 15, 20


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
            h_align="center",
            v_align="center",
            text="Mood light settings",
            color=(0, 1, 0))

        increase_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(600, 100),
            size=(5, 1),
            scale=3.5,
            extra_touch_border_scale=2.5,
            icon=ba.gettexture("upButton"),
            on_activate_call=self.increase_limit)

        decrease_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(100, 100),
            size=(5, 1),
            scale=3.5,
            extra_touch_border_scale=2.5,
            icon=ba.gettexture("downButton"),
            on_activate_call=self.decrease_limit)

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

        self.warn_text = ba.textwidget(
            parent=self._root_widget,
            text="",
            size=(400, 200),
            position=(150, 300),
            h_align="center",
            v_align="center",
            maxwidth=600)

        self.close_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(550, 590),
            size=(35, 35),
            icon=ba.gettexture("crossOut"),
            icon_color=(1, 0.2, 0.2),
            scale=2,
            color=(1, 0.2, 0.2),
            extra_touch_border_scale=5,
            on_activate_call=self.close,
            button_type="square")

        save_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(520, 470),
            size=(90, 70),
            scale=1.5,
            label="SAVE",
            button_type="square",
            on_activate_call=self.save_settings)

        ba.textwidget(edit=self.upper_text, on_activate_call=ba.Call(self.on_text_click, "upper"))
        ba.textwidget(edit=self.lower_text, on_activate_call=ba.Call(self.on_text_click, "lower"))

    def save_settings(self):
        with open("moodlightSettings.txt", "w") as mltxt:
            data = "\n".join([str(Ldefault), str(Udefault)])
            mltxt.write(data)
        Print("settings saved")
        self.close()

    def close(self):
        ba.containerwidget(edit=self._root_widget, transition="out_right",)

# ba_meta export plugin


class moodlight(ba.Plugin):
    def __init__(self):
        pass
    Map._old_init = Map.__init__

    def on_app_running(self):
        try:
            _ba.timer(0.5, self.on_chat_message, True)
        except Exception as err:
            Print(err)

    def on_chat_message(self):
        messages = _ba.get_chat_messages()
        if len(messages) > 0:
            lastmessage = messages[-1].split(":")[-1].strip().lower()
            if lastmessage in ("/mood light", "/mood lighting", "/mood_light", "/mood_lighting", "/moodlight", "ml"):

                with open("moodlightSettings.txt", "r") as mltxt:
                    global Ldefault, Udefault
                    data = mltxt.read()
                    Ldefault, Udefault = data.split("\n")
                    Ldefault = int(Ldefault)
                    Udefault = int(Udefault)
                SettingWindow()
                _ba.chatmessage("Mood light settings opened")

    def on_plugin_manager_prompt(self):
        SettingWindow()

    def _new_init(self, vr_overlay_offset: Optional[Sequence[float]] = None) -> None:
        self._old_init(vr_overlay_offset)
        in_game = not isinstance(_ba.get_foreground_host_session(), mainmenu.MainMenuSession)
        if not in_game:
            return

        gnode = _ba.getactivity().globalsnode

        def changetint():
            Range = (random.randrange(Ldefault, Udefault)/10, random.randrange(Ldefault,
                     Udefault)/10, random.randrange(Ldefault, Udefault)/10)
            ba.animate_array(gnode, 'tint', 3, {
                0.0: gnode.tint,
                1.0: Range
            })
        _ba.timer(0.3, changetint, repeat=True)
    Map.__init__ = _new_init
