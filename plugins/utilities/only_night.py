# Ported by brostos to api 8
# Tool used to make porting easier.(https://github.com/bombsquad-community/baport)
"""Only Night."""

# ba_meta require api 9

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
from bascenev1._gameactivity import GameActivity

if TYPE_CHECKING:
    pass


# ba_meta export plugin
class OnlyNight(babase.Plugin):
    GameActivity.old_on_transition_in = GameActivity.on_transition_in

    def new_on_transition_in(self) -> None:
        self.old_on_transition_in()
        gnode = bs.getactivity().globalsnode
        if self.map.getname() in [
            "Monkey Face",
            "Rampage",
            "Roundabout",
            "Step Right Up",
            "Tip Top",
            "Zigzag",
            "The Pad",
        ]:
            gnode.tint = (0.4, 0.4, 0.4)
        elif self.map.getname() in [
            "Big G",
            "Bridgit",
            "Courtyard",
            "Crag Castle",
            "Doom Shroom",
            "Football Stadium",
            "Happy Thoughts",
            "Hockey Stadium",
        ]:
            gnode.tint = (0.5, 0.5, 0.5)
        else:
            gnode.tint = (0.3, 0.3, 0.3)

    GameActivity.on_transition_in = new_on_transition_in
