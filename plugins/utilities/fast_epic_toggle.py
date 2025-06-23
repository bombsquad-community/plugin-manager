# ba_meta require api 9

import babase
import bauiv1 as bui
import bauiv1lib.party
import bascenev1 as bs


class FastEpicSwitcher(bauiv1lib.party.PartyWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Fast Mode Button
        self._fast_btn = bui.buttonwidget(
            parent=self._root_widget,
            size=(150, 60),
            scale=0.7,
            label='Fast Mode',
            button_type='square',
            position=(self._width - 62, self._height - 80),
            on_activate_call=self._set_fast_mode
        )

        # Epic Mode Button
        self._epic_btn = bui.buttonwidget(
            parent=self._root_widget,
            size=(150, 60),
            scale=0.7,
            label='Epic Mode',
            button_type='square',
            position=(self._width - 62, self._height - 150),
            on_activate_call=self._set_epic_mode
        )

    def _set_fast_mode(self):
        """Set the game to Fast Mode."""
        bs.get_foreground_host_activity().globalsnode.slow_motion = 0.5  # Fast Mode
        bui.screenmessage("Switched to Fast Mode", color=(0, 1, 0))

    def _set_epic_mode(self):
        """Set the game to Epic Mode."""
        bs.get_foreground_host_activity().globalsnode.slow_motion = 1.0  # Epic Mode (Slow)
        bui.screenmessage("Switched to Epic Mode!", color=(0, 1, 0))

# ba_meta export babase.Plugin


class ByANES(babase.Plugin):
    def on_app_running(self):
        bauiv1lib.party.PartyWindow = FastEpicSwitcher
