# Released under the MIT License. See LICENSE for details.
#
"""
    game: One Punch
    description: A death match where a landed punch (almost) always results in
    a kill. This is influenced by the SWAT mode in Halo.
    author: levyfellow
    tested on: 1.7
"""

# ba_meta require api 7

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.game.deathmatch import DeathMatchGame, Player, Team

if TYPE_CHECKING:
    pass

# ba_meta export game
class OnePunchGame(DeathMatchGame):
    """Definition for the One Punch mini game"""

    name = 'One Punch'
    description = ('One Punch Kill!')

    def on_begin(self) -> None:
        """
        we need to override this function to prevent the power drops. It's
        basically a copy/paste of the standard function with one line removed
        (the one that adds powerups)
        """
        super(DeathMatchGame, self).on_begin()
        self.setup_standard_time_limit(self._time_limit)

        # Base kills needed to win on the size of the largest team.
        self._score_to_win = (self._kills_to_win_per_player *
                              max(1, max(len(t.players) for t in self.teams)))
        self._update_scoreboard()

    def spawn_player(self, player: Player) -> ba.Actor:
        """ Here we modify the player as we need for this mode """
        spaz = self.spawn_player_spaz(player)

        # don't allow bombs
        spaz.connect_controls_to_player(enable_bomb=False)
        # Make a super powerful punch.
        spaz._punch_power_scale = 6

        return spaz 
