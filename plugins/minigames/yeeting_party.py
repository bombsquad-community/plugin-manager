# Porting made easier by baport.(https://github.com/bombsquad-community/baport)
# Made by your friend: Freaku


import babase
import bascenev1 as bs
from bascenev1lib.game.deathmatch import Player, DeathMatchGame


plugman = dict(
    plugin_name='yeeting_party',
    description='Yeet your enemies out of the map!',
    external_url='',
    authors=[
        {'name': 'Freaku', 'email': '', 'discord': '', 'github': 'Freaku17'},
    ],
    version='2.1.0',
)


# ba_meta require api 9
# ba_meta export bascenev1.GameActivity
class YeetingGame(DeathMatchGame):
    """A game of yeeting people out of map"""

    name = 'Yeeting Party!'
    description = 'Yeet your enemies out of the map'

    @classmethod
    def get_supported_maps(cls, sessiontype):
        return ['Bridgit', 'Rampage', 'Monkey Face']

    def get_instance_description(self):
        return 'Yeet ${ARG1} enemies out of the map!', self._score_to_win

    def get_instance_description_short(self):
        return 'yeet ${ARG1} enemies', self._score_to_win

    def setup_standard_powerup_drops(self, enable_tnt: bool = True) -> None:
        pass

    def spawn_player(self, player: Player):
        spaz = self.spawn_player_spaz(player)
        spaz.connect_controls_to_player(enable_punch=False, enable_bomb=False)
        return spaz
