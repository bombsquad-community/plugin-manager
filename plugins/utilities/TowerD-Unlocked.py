# By Freaku / @[Just] Freak#4999


import ba
from bastd.maps import TowerD


@classmethod
def new_play_types(cls):
    """return valid play types for this map."""
    return ['melee', 'keep_away', 'team_flag', 'king_of_the_hill']


# ba_meta require api 7
# ba_meta export plugin
class byFreaku(ba.Plugin):
    def on_app_running(self):
        TowerD.get_play_types = new_play_types
