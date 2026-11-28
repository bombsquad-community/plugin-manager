# ba_meta require api 9

from __future__ import annotations

import babase
import bascenev1 as bs
import random
from bascenev1lib.actor import bomb

plugman = dict(
    plugin_name="colored_bomb_explosion_patches",
    description="Creates patches of random color after bomb explosions",
    external_url="https://youtube.com/c/JoseANG3LYT",
    authors=[
        {"name": "JoseAng3l", "email": "", "discord": "joseang3l", "github": ""},
    ],
    version="1.1.0",
)


def _add_colored_scorch(blast, position):
    scorch_radius = blast.radius
    if blast.blast_type == 'tnt':
        scorch_radius *= 1.15
    scorch = bs.newnode(
        'scorch',
        attrs={
            'position': position,
            'size': scorch_radius * 0.5,
            'big': (blast.blast_type == 'tnt'),
        },
    )
    random_color = (random.random(), random.random(), random.random())
    scorch.color = babase.safecolor(random_color)
    bs.animate(scorch, 'presence', {3.000: 1, 13.000: 0})
    bs.timer(13.0, scorch.delete)


def _patch_blast():
    # Wrap Blast.__init__ in place rather than replacing bomb.Blast with a
    # subclass: other plugins patch Blast too, and some (better_camera_shake)
    # call super(type(self), self).__init__(), which recurses forever on a
    # subclass and leaves every bomb unexploded.
    original_init = bomb.Blast.__init__

    def __init__(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        _add_colored_scorch(self, kwargs.get('position', (0.0, 1.0, 0.0)))

    bomb.Blast.__init__ = __init__


# ba_meta export babase.Plugin
class RandomColorsPlugin(babase.Plugin):
    def __init__(self):
        _patch_blast()
