"""
    Vanilla Wiggle Dance by SoK
    Pizza Tower dance ported to BombSquad.
    Originally made for Explodinary Rebombed.

    Wiggling left and right makes your character play music, wave arms and emit cool sparks :D
    For much cooler version of this plugin, check out BSE Rebombed Modpack! (not released yet)
    Version 1.0

    If you want to use this plugin in your own work, please let me know on Discord (sok05).
"""

from __future__ import annotations
from typing import override
import random
import math
import bascenev1 as bs
import babase

# ba_meta require api 9

# ba_meta export babase.Plugin


class WiggleDance(babase.Plugin):
    def add_dance_mechanic_to_spaz(spaz_class):
        """Add dance mechanic to the Spaz class"""

        # Store the original on_move_left_right method
        original_on_move_left_right = spaz_class.on_move_left_right

        # Override the on_move_left_right method
        def new_on_move_left_right(self, value: float) -> None:
            """Called to set the left/right joystick amount on this spaz"""
            # Call the original method first
            original_on_move_left_right(self, value)

            # Check for wiggling
            if not hasattr(self, '_last_wiggle_value'):
                self._last_wiggle_value = 0
                self._wiggle_count = 0
                self._wiggle_timer = None
                self._dance_timer = None
                self._dance_visual_timer = None
                self._dance_sound_node = None
                self.dancing = False
                self._last_dance_arm = 'left'

            # Detect significant change in direction (wiggle)
            if abs(value) > 0.5:
                # Add a wiggle
                self._wiggle_count += 1

                # Remove the existing timer
                if self._wiggle_timer:
                    self._wiggle_timer = None

                # Start a new timer
                self._wiggle_timer = bs.Timer(0.18, bs.WeakCall(self._reset_wiggle_count))

                # Check if we've been wiggling enough to start dancing
                if self._wiggle_count > 8 and not self.dancing:
                    self._start_dancing()

            # Update last wiggle value
            self._last_wiggle_value = value

        # Add new methods to the class
        def _reset_wiggle_count(self):
            """Reset wiggle count if timer expires"""
            if self.node and self.is_alive():
                self._wiggle_count = 0
                self._wiggle_timer = None

                # If we were dancing, stop dancing
                if self.dancing:
                    self._stop_dancing()

        def _start_dancing(self):
            """Start the dance sequence"""
            if not self.node or not self.is_alive():
                return

            self.dancing = True

            # Play sound
            bs.getsound('orchestraHit4').play(volume=0.35)

            # Create dance sound node
            # We gotta keep track if another Spaz is playing music currently
            # in our activity. We don't want multiple musics cuz.. annoying, man
            activity = bs.getactivity()
            if not hasattr(activity, 'music_spazzes'):
                activity.music_spazzes = 0
            if not self._dance_sound_node and activity.music_spazzes < 1:
                self._dance_sound_node = bs.newnode(
                    'sound',
                    owner=self.node,
                    attrs={'sound': bs.getsound('victoryMusic'), 'volume': 0.2, 'loop': True},
                )
                self.node.connectattr('position', self._dance_sound_node, 'position')

                # And add our Spaz as a music one for our activity
                activity.music_spazzes += 1

            # Start visual dance timer
            if not self._dance_visual_timer:
                self._dance_visual_timer = bs.Timer(
                    0.5, bs.WeakCall(self._dance_visual), repeat=True)

        def _dance_visual(self):
            """Create visual dance effects"""
            if not self.node or not self.is_alive() or not self.dancing:
                return

            # Emit sparks
            bs.emitfx(
                position=self.node.position,
                velocity=(random.uniform(-1, 1), 2, random.uniform(-1, 1)),
                count=random.randint(5, 10),
                scale=random.uniform(0.7, 1.1),
                spread=0.2,
                chunk_type='spark'
            )

            # Wave arms
            if self._last_dance_arm == 'left':
                self.node.handlemessage('celebrate_r', 50)
                self._last_dance_arm = 'right'
            else:
                self.node.handlemessage('celebrate', 50)
                self._last_dance_arm = 'left'

        def _stop_dancing(self):
            """Stop the dance sequence"""
            self.dancing = False

            # Clean up timers
            if self._dance_visual_timer:
                self._dance_visual_timer = None

            # Clean up sound
            if self._dance_sound_node:
                self._dance_sound_node.delete()
                self._dance_sound_node = None

            activity = bs.getactivity()

            # And remove our Spaz as a music one for our activity
            activity.music_spazzes -= 1

        # Add methods to the class
        spaz_class.on_move_left_right = new_on_move_left_right
        spaz_class._reset_wiggle_count = _reset_wiggle_count
        spaz_class._start_dancing = _start_dancing
        spaz_class._dance_visual = _dance_visual
        spaz_class._stop_dancing = _stop_dancing

        # Add cleanup
        original_on_expire = spaz_class.on_expire

        def new_on_expire(self):
            """Clean up dance resources when expiring"""
            if hasattr(self, 'dancing') and self.dancing:
                self._stop_dancing()
            original_on_expire(self)

        spaz_class.on_expire = new_on_expire

        return spaz_class

    # Apply the dance mechanic to the Spaz class
    from bascenev1lib.actor.spaz import Spaz
    Spaz = add_dance_mechanic_to_spaz(Spaz)
