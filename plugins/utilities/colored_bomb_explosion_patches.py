# ba_meta require api 9

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
import random
from bascenev1lib.actor import bomb

if TYPE_CHECKING:
    from typing import Sequence


class NewBlast(bomb.Blast):
    def __init__(
        self,
        *,
        position: Sequence[float] = (0.0, 1.0, 0.0),
        velocity: Sequence[float] = (0.0, 0.0, 0.0),
        blast_radius: float = 2.0,
        blast_type: str = 'normal',
        source_player: bs.Player | None = None,
        hit_type: str = 'explosion',
        hit_subtype: str = 'normal',
    ):
        super().__init__(
            position=position,
            velocity=velocity,
            blast_radius=blast_radius,
            blast_type=blast_type,
            source_player=source_player,
            hit_type=hit_type,
            hit_subtype=hit_subtype
        )
        scorch_radius = self.radius
        if self.blast_type == 'tnt':
            scorch_radius *= 1.15
        scorch = bs.newnode(
            'scorch',
            attrs={
                'position': position,
                'size': scorch_radius * 0.5,
                'big': (self.blast_type == 'tnt'),
            },
        )
        random_color = (random.random(), random.random(), random.random())
        scorch.color = babase.safecolor(random_color)
        bs.animate(scorch, 'presence', {3.000: 1, 13.000: 0})
        bs.timer(13.0, scorch.delete)


# ba_meta export babase.Plugin
class RandomColorsPlugin(babase.Plugin):
    bomb.Blast = NewBlast
