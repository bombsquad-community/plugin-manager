# ba_meta require api 9

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
import random
from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.actor.spazfactory import SpazFactory

if TYPE_CHECKING:
    from typing import Sequence

if TYPE_CHECKING:
    pass


Spaz._old_init = Spaz.__init__


def __init__(self,
             *,
             color: Sequence[float] = (1.0, 1.0, 1.0),
             highlight: Sequence[float] = (0.5, 0.5, 0.5),
             character: str = 'Spaz',
             source_player: bs.Player = None,
             start_invincible: bool = True,
             can_accept_powerups: bool = True,
             powerups_expire: bool = False,
             demo_mode: bool = False):
    self._old_init(
        color=color,
        highlight=highlight,
        character=character,
        source_player=source_player,
        start_invincible=start_invincible,
        can_accept_powerups=can_accept_powerups,
        powerups_expire=powerups_expire,
        demo_mode=demo_mode
    )
    if self.source_player:
        self.equip_shields()

        def animate_shield():
            if not self.shield:
                return
            bs.animate_array(self.shield, 'color', 3, {
                0.0: self.shield.color,
                0.2: (random.random(), random.random(), random.random())
            })
        bs.timer(0.2, animate_shield, repeat=True)
        self.impact_scale = 0


def equip_shields(self, decay: bool = False) -> None:
    """
    Give this spaz a nice energy shield.
    """

    if not self.node:
        babase.print_error('Can\'t equip shields; no node.')
        return

    factory = SpazFactory.get()
    if self.shield is None:
        self.shield = bs.newnode('shield',
                                 owner=self.node,
                                 attrs={
                                     'color': (0.3, 0.2, 2.0),
                                     'radius': 1.3
                                 })
        self.node.connectattr('position_center', self.shield, 'position')
    self.shield_hitpoints = self.shield_hitpoints_max = 650
    self.shield_decay_rate = factory.shield_decay_rate if decay else 0
    self.shield.hurt = 0
    factory.shield_up_sound.play(1.0, position=self.node.position)

    if self.impact_scale == 0:
        return

    if self.shield_decay_rate > 0:
        self.shield_decay_timer = bs.Timer(0.5,
                                           bs.WeakCall(self.shield_decay),
                                           repeat=True)
        # So user can see the decay.
        self.shield.always_show_health_bar = True


# ba_meta export babase.Plugin
class InfinityShieldPlugin(babase.Plugin):
    Spaz.__init__ = __init__
    Spaz.equip_shields = equip_shields
