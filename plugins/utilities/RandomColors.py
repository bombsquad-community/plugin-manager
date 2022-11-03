# ba_meta require api 7
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import random
from bastd.actor import bomb

if TYPE_CHECKING:
	from typing import Sequence


class NewBlast(bomb.Blast):
	def __init__(
        self,
        position: Sequence[float] = (0.0, 1.0, 0.0),
        velocity: Sequence[float] = (0.0, 0.0, 0.0),
        blast_radius: float = 2.0,
        blast_type: str = 'normal',
        source_player: ba.Player | None = None,
        hit_type: str = 'explosion',
        hit_subtype: str = 'normal',
    ):
		super().__init__(position, velocity, blast_radius, blast_type,
			source_player, hit_type, hit_subtype)
		scorch_radius = light_radius = self.radius
		if self.blast_type == 'tnt':
			scorch_radius *= 1.15
		scorch = ba.newnode(
			'scorch',
			attrs={
				'position': position,
				'size': scorch_radius * 0.5,
				'big': (self.blast_type == 'tnt'),
			},
		)
		random_color = (random.random(), random.random(), random.random())
		scorch.color = ba.safecolor(random_color)
		ba.animate(scorch, 'presence', {3.000: 1, 13.000: 0})
		ba.timer(13.0, scorch.delete)


# ba_meta export plugin
class RandomColorsPlugin(ba.Plugin):
	bomb.Blast = NewBlast
