# ba_meta require api 9

import babase
import bauiv1 as bui
import bauiv1lib.party
import bascenev1 as bs

class InfiniteImpactBombs(bauiv1lib.party.PartyWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bombs_enabled = False  # Track bomb state
        self._btn = bui.buttonwidget(
            parent=self._root_widget,
            size=(200, 50),
            scale=0.7,
            label="Toggle Impact Bombs",
            button_type="square",
            position=(self._width - 210, self._height - 50),
            on_activate_call=self._toggle_bombs
        )

    def _toggle_bombs(self):
        """Toggle infinite impact bombs for the player."""
        activity = bs.get_foreground_host_activity()
        if activity is None or not hasattr(activity, "players"):
            bui.screenmessage("No game running!", color=(1, 0, 0))
            return

        for player in activity.players:
            if player and player.actor:
                spaz = player.actor
                if self._bombs_enabled:
                    spaz.bomb_type = "normal"
                    bui.screenmessage("Impact Bombs Disabled", color=(1, 0, 0))
                else:
                    spaz.bomb_type = "impact"
                    bui.screenmessage("Impact Bombs Enabled", color=(0, 1, 0))
        
        self._bombs_enabled = not self._bombs_enabled

# ba_meta export plugin
class ByANES(babase.Plugin):
    def __init__(self):
        bauiv1lib.party.PartyWindow = InfiniteImpactBombs