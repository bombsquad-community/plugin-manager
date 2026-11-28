# ba_meta require api 9

from __future__ import annotations

import functools
import random
import weakref

import babase
import bascenev1 as bs
from bascenev1lib.actor.spaz import Spaz

plugman = dict(
    plugin_name="infinity_shield",
    description="Gives you unbreakable shield",
    external_url="https://youtu.be/hp7vbB-hUPg?si=i7Th0NP5xDPLN2P_",
    authors=[
        {"name": "JoseAng3l", "email": "", "discord": "joseang3l", "github": ""},
    ],
    version="1.2.0",
)


def _animate_shield(spaz_ref):
    spaz = spaz_ref()
    if spaz is None or not spaz.shield:
        return
    bs.animate_array(spaz.shield, 'color', 3, {
        0.0: spaz.shield.color,
        0.2: (random.random(), random.random(), random.random())
    })


def _patch_spaz():
    original_init = Spaz.__init__
    original_equip_shields = Spaz.equip_shields

    # Pass every argument through untouched: the engine adds new ones from
    # time to time (1.8.0 added cloud_spaz_def), and a copied parameter list
    # turns each of those into a TypeError that stops players spawning.
    def __init__(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        if self.source_player:
            self.equip_shields()
            # (A weak ref, so the timer doesn't keep a dead spaz alive.)
            self._infinity_shield_timer = bs.Timer(
                0.2, functools.partial(_animate_shield, weakref.ref(self)), repeat=True
            )
            self.impact_scale = 0

    def equip_shields(self, decay=False):
        # Players' shields never decay, whichever shield powerup they pick up.
        original_equip_shields(self, decay=decay and self.impact_scale != 0)

    Spaz.__init__ = __init__
    Spaz.equip_shields = equip_shields


# ba_meta export babase.Plugin
class InfinityShieldPlugin(babase.Plugin):
    def __init__(self):
        _patch_spaz()
