"""
    Quickturn by TheMikirog
    
    Super Smash Bros Melee's wavedash mechanic ported and tuned for BombSquad.

    Sharp turns while running (releasing run button, changing direction, holding run again) are much faster with this mod, allowing for more dynamic, aggressive play. 
    Version 3

    No Rights Reserved
"""

# ba_meta require api 9

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
import math
import bascenev1lib

if TYPE_CHECKING:
    pass

# ba_meta export plugin


class Quickturn(babase.Plugin):

    class FootConnectMessage:
        """Spaz started touching the ground"""

    class FootDisconnectMessage:
        """Spaz stopped touching the ground"""

    def wavedash(self) -> None:
        if not self.node:
            return

        isMoving = abs(self.node.move_up_down) >= 0.5 or abs(self.node.move_left_right) >= 0.5

        if self._dead or not self.grounded or not isMoving:
            return

        if self.node.knockout > 0.0 or self.frozen or self.node.hold_node:
            return

        t_ms = bs.time() * 1000
        assert isinstance(t_ms, int)

        if t_ms - self.last_wavedash_time_ms >= self._wavedash_cooldown:

            move = [self.node.move_left_right, -self.node.move_up_down]
            vel = [self.node.velocity[0], self.node.velocity[2]]

            move_length = math.hypot(move[0], move[1])
            vel_length = math.hypot(vel[0], vel[1])
            if vel_length < 0.6:
                return
            move_norm = [m/move_length for m in move]
            vel_norm = [v/vel_length for v in vel]
            dot = sum(x*y for x, y in zip(move_norm, vel_norm))
            turn_power = min(round(math.acos(dot) / math.pi, 2)*1.3, 1)

            # https://easings.net/#easeInOutQuart
            if turn_power < 0.55:
                turn_power = 8 * turn_power * turn_power * turn_power * turn_power
            else:
                turn_power = 0.55 - pow(-2 * turn_power + 2, 4) / 2
            if turn_power < 0.1:
                return

            boost_power = math.sqrt(math.pow(vel[0], 2) + math.pow(vel[1], 2)) * 8
            boost_power = min(pow(boost_power, 8), 160)

            self.last_wavedash_time_ms = t_ms

            # FX
            bs.emitfx(position=self.node.position,
                      velocity=(vel[0]*0.5, -1, vel[1]*0.5),
                      chunk_type='spark',
                      count=5,
                      scale=boost_power / 160 * turn_power,
                      spread=0.25)

            # Boost itself
            pos = self.node.position
            for i in range(6):
                self.node.handlemessage('impulse', pos[0], 0.2+pos[1]+i*0.1, pos[2],
                                        0, 0, 0,
                                        boost_power * turn_power,
                                        boost_power * turn_power, 0, 0,
                                        move[0], 0, move[1])

    def new_spaz_init(func):
        def wrapper(*args, **kwargs):

            func(*args, **kwargs)

            # args[0] = self
            args[0]._wavedash_cooldown = 170
            args[0].last_wavedash_time_ms = -9999
            args[0].grounded = 0

        return wrapper
    bascenev1lib.actor.spaz.Spaz.__init__ = new_spaz_init(bascenev1lib.actor.spaz.Spaz.__init__)

    def new_factory(func):
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)

            args[0].roller_material.add_actions(
                conditions=('they_have_material',
                            bascenev1lib.gameutils.SharedObjects.get().footing_material),
                actions=(('message', 'our_node', 'at_connect', Quickturn.FootConnectMessage),
                         ('message', 'our_node', 'at_disconnect', Quickturn.FootDisconnectMessage)))
        return wrapper
    bascenev1lib.actor.spazfactory.SpazFactory.__init__ = new_factory(
        bascenev1lib.actor.spazfactory.SpazFactory.__init__)

    def new_handlemessage(func):
        def wrapper(*args, **kwargs):
            if args[1] == Quickturn.FootConnectMessage:
                args[0].grounded += 1
            elif args[1] == Quickturn.FootDisconnectMessage:
                if args[0].grounded > 0:
                    args[0].grounded -= 1

            func(*args, **kwargs)
        return wrapper
    bascenev1lib.actor.spaz.Spaz.handlemessage = new_handlemessage(
        bascenev1lib.actor.spaz.Spaz.handlemessage)

    def new_on_run(func):
        def wrapper(*args, **kwargs):
            if args[0]._last_run_value < args[1] and args[1] > 0.8:
                Quickturn.wavedash(args[0])
            func(*args, **kwargs)
        return wrapper
    bascenev1lib.actor.spaz.Spaz.on_run = new_on_run(bascenev1lib.actor.spaz.Spaz.on_run)
