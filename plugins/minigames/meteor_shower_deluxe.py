# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 8
"""
GNU AFFERO GENERAL PUBLIC LICENSE
Version 3, 19 November 2007

Copyright (C) 2007 Free Software Foundation, Inc. <[1](https://fsf.org/)>

Everyone is permitted to copy and distribute verbatim copies of this license document, but changing it is not allowed.

This license is designed to ensure cooperation with the community in the case of network server software. It is a free, copyleft license for software and other kinds of works. The license guarantees your freedom to share and change all versions of a program, to make sure it remains free software for all its users.

The license identifier refers to the choice to use code under AGPL-3.0-or-later (i.e., AGPL-3.0 or some later version), as distinguished from use of code under AGPL-3.0-only. The license notice states which of these applies the code in the file.


"""
import random
import babase
import bauiv1 as bui
import bascenev1 as bs
from bascenev1lib.game.meteorshower import MeteorShowerGame
from bascenev1lib.actor.bomb import Bomb


class NewMeteorShowerGame(MeteorShowerGame):
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return bs.app.classic.getmaps("melee")

    def _drop_bomb_cluster(self) -> None:
        # Drop several bombs in series.
        delay = 0.0
        bounds = list(self._map.get_def_bound_box("map_bounds"))
        for _i in range(random.randrange(1, 3)):
            # Drop them somewhere within our bounds with velocity pointing
            # toward the opposite side.
            pos = (
                random.uniform(bounds[0], bounds[3]),
                bounds[4],
                random.uniform(bounds[2], bounds[5]),
            )
            dropdirx = -1 if pos[0] > 0 else 1
            dropdirz = -1 if pos[2] > 0 else 1
            forcex = (
                bounds[0] - bounds[3]
                if bounds[0] - bounds[3] > 0
                else -(bounds[0] - bounds[3])
            )
            forcez = (
                bounds[2] - bounds[5]
                if bounds[2] - bounds[5] > 0
                else -(bounds[2] - bounds[5])
            )
            vel = (
                (-5 + random.random() * forcex) * dropdirx,
                random.uniform(-3.066, -4.12),
                (-5 + random.random() * forcez) * dropdirz,
            )
            bs.timer(delay, babase.Call(self._drop_bomb, pos, vel))
            delay += 0.1
        self._set_meteor_timer()


# ba_meta export plugin
class byEra0S(babase.Plugin):
    MeteorShowerGame.get_supported_maps = NewMeteorShowerGame.get_supported_maps
    MeteorShowerGame._drop_bomb_cluster = NewMeteorShowerGame._drop_bomb_cluster
