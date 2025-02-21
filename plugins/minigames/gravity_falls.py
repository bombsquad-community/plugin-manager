# Ported to api 8 by brostos using baport.(https://github.com/bombsquad-community/baport)
# Made by MattZ45986 on GitHub
# Ported by: Freaku / @[Just] Freak#4999


import babase
import bauiv1 as bui
import bascenev1 as bs
from bascenev1lib.game.elimination import EliminationGame


# ba_meta require api 8
# ba_meta export bascenev1.GameActivity
class GFGame(EliminationGame):
    name = 'Gravity Falls'

    def spawn_player(self, player):
        actor = self.spawn_player_spaz(player, (0, 5, 0))
        if not self._solo_mode:
            bs.timer(0.3, babase.Call(self._print_lives, player))

        # If we have any icons, update their state.
        for icon in player.icons:
            icon.handle_player_spawned()
        bs.timer(1, babase.Call(self.raise_player, player))
        return actor

    def raise_player(self, player):
        if player.is_alive():
            try:
                player.actor.node.handlemessage(
                    "impulse", player.actor.node.position[0], player.actor.node.position[1]+.5, player.actor.node.position[2], 0, 5, 0, 3, 10, 0, 0, 0, 5, 0)
            except:
                pass
            bs.timer(0.05, babase.Call(self.raise_player, player))
