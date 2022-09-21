#mood light plugin by ʟօʊքɢǟʀօʊ

# ba_meta require api 7
from __future__ import annotations
from typing import TYPE_CHECKING, cast

import ba
import _ba
import random
from ba._map import Map
from bastd import mainmenu
from bastd.gameutils import SharedObjects
from time import sleep
if TYPE_CHECKING:
    from typing import Any, Sequence, Callable, List, Dict, Tuple, Optional, Union

# ba_meta export plugin

class ColorSchemeWindow(ba.Window):
    def __init__(self, default_colors=((0.41, 0.39, 0.5), (0.5, 0.7, 0.25))):
        self._default_colors = default_colors
        self._color, self._highlight = ba.app.config.get("ColorScheme", (None, None))

        self._last_color = self._color
        self._last_highlight = self._highlight

        # Let's set the game's default colorscheme before opening the Window.
        # Otherwise the colors in the Window are tinted as per the already
        # applied custom colorscheme thereby making it impossible to visually
        # differentiate between different colors.
        # A hack to let players select any RGB color value through the UI,
        # otherwise this is limited only to pro accounts.
        ba.app.accounts_v1.have_pro = lambda: True

        self.draw_ui()

    def draw_ui(self):
        # Most of the stuff here for drawing the UI is referred from the
        # game's bastd/ui/profile/edit.py, and so there could be some
        # cruft here due to my oversight.
        uiscale = ba.app.ui.uiscale
        self._width = width = 480.0 if uiscale is ba.UIScale.SMALL else 380.0
        self._x_inset = x_inset = 40.0 if uiscale is ba.UIScale.SMALL else 0.0
        self._height = height = (
            275.0
            if uiscale is ba.UIScale.SMALL
            else 288.0
            if uiscale is ba.UIScale.MEDIUM
            else 300.0
        )
        spacing = 40
        self._base_scale = (
            2.05
            if uiscale is ba.UIScale.SMALL
            else 1.5
            if uiscale is ba.UIScale.MEDIUM
            else 1.0
        )
        top_extra = 15

        super().__init__(
            root_widget=ba.containerwidget(
                size=(width, height + top_extra),
                on_outside_click_call=self.cancel_on_outside_click,
                transition="in_right",
                scale=self._base_scale,
                stack_offset=(0, 15) if uiscale is ba.UIScale.SMALL else (0, 0),
            )
        )

        cancel_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(52 + x_inset, height - 60),
            size=(155, 60),
            scale=0.8,
            autoselect=True,
            label=ba.Lstr(resource="cancelText"),
            on_activate_call=self._cancel,
        )
        ba.containerwidget(edit=self._root_widget, cancel_button=cancel_button)

        save_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(width - (177 + x_inset), height - 110),
            size=(155, 60),
            autoselect=True,
            scale=0.8,
            label=ba.Lstr(resource="saveText"),
        )
        ba.widget(edit=save_button, left_widget=cancel_button)
        ba.buttonwidget(edit=save_button, on_activate_call=self.save)
        ba.widget(edit=cancel_button, right_widget=save_button)
        ba.containerwidget(edit=self._root_widget, start_button=save_button)

        reset_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(width - (177 + x_inset), height - 60),
            size=(155, 60),
            color=(0.2, 0.5, 0.6),
            autoselect=True,
            scale=0.8,
            label=ba.Lstr(resource="settingsWindowAdvanced.resetText"),
        )
        ba.widget(edit=reset_button, left_widget=reset_button)
        ba.buttonwidget(edit=reset_button, on_activate_call=self.reset)
        ba.widget(edit=cancel_button, right_widget=reset_button)
        ba.containerwidget(edit=self._root_widget, start_button=reset_button)

        v = height - 65.0
        v -= spacing * 3.0
        b_size = 80
        b_offs = 75

  
        ba.textwidget(
            parent=self._root_widget,
            h_align="center",
            v_align="center",
            position=(self._width * 0.5 - b_offs, v - 65),
            size=(0, 0),
            draw_controller=self._color_button,
            text=ba.Lstr(resource="editProfileWindow.colorText"),
            scale=0.7,
            color=ba.app.ui.title_color,
            maxwidth=120,
        )

        self._highlight_button = ba.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(self._width * 0.5 + b_offs - b_size * 0.5, v - 50),
            size=(b_size, b_size),
            color=self._last_highlight or self._default_colors[1],
            label="",
            button_type="square",
        )

        ba.buttonwidget(
            edit=self._highlight_button,
            on_activate_call=ba.Call(self._pick_color, "highlight"),
        )
        ba.textwidget(
            parent=self._root_widget,
            h_align="center",
            v_align="center",
            position=(self._width * 0.5 + b_offs, v - 65),
            size=(0, 0),
            draw_controller=self._highlight_button,
            text=ba.Lstr(resource="editProfileWindow.highlightText"),
            scale=0.7,
            color=ba.app.ui.title_color,
            maxwidth=120,
        )

    def cancel_on_outside_click(self):
        ba.playsound(ba.getsound("swish"))
        self._cancel()

    def _cancel(self):
        if self._last_color and self._last_highlight:
            colorscheme = ColorScheme(self._last_color, self._last_highlight)
            colorscheme.apply()
        # Good idea to revert this back now so we do not break anything else.
        ba.app.accounts_v1.have_pro = original_have_pro
        ba.containerwidget(edit=self._root_widget, transition="out_right")

    def reset(self, transition_out=True):
        if transition_out:
            ba.playsound(ba.getsound("gunCocking"))
        ba.app.config["ColorScheme"] = (None, None)
        # Good idea to revert this back now so we do not break anything else.
        ba.app.accounts_v1.have_pro = original_have_pro
        ba.app.config.commit()
        ba.containerwidget(edit=self._root_widget, transition="out_right")

    def save(self, transition_out=True):
        if transition_out:
            ba.playsound(ba.getsound("gunCocking"))
        colorscheme = ColorScheme(
            self._color or self._default_colors[0],
            self._highlight or self._default_colors[1],
        )
        ba.containerwidget(edit=self._root_widget, transition="out_right")

    





class UwUuser(ba.Plugin):
    Map._old_init = Map.__init__
    def on_plugin_manager_prompt(self):
        ColorSchemeWindow()
    def _new_init(self, vr_overlay_offset: Optional[Sequence[float]] = None) -> None:
        self._old_init(vr_overlay_offset)   
        in_game = not isinstance(_ba.get_foreground_host_session(), mainmenu.MainMenuSession)
        if not in_game: return
        
        gnode = _ba.getactivity().globalsnode

        lowerlimit=5
        upperlimit=20
        
        def changetint():
        	   ba.animate_array(gnode, 'tint', 3, {
                       0.0: gnode.tint, 
                       1.0: (random.randrange(lowerlimit,upperlimit)/10, random.randrange(lowerlimit,upperlimit)/10, random.randrange(lowerlimit, upperlimit)/10) 
               }) 
        _ba.timer(0.3, changetint, repeat= True) 
 
    
    Map.__init__ = _new_init
