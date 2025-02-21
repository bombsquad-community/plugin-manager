# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 9

"""
    TNT Respawn Text by TheMikirog
    Version 1
    
    Shows when a TNT box is about to respawn with non-intrusive text.
    
    Heavily commented for easy modding learning!
    
    No Rights Reserved
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Let's import everything we need and nothing more.
import babase
import bauiv1 as bui
import bascenev1 as bs
import bascenev1lib
import math
import random
from bascenev1lib.actor.bomb import Bomb

if TYPE_CHECKING:
    pass

"""
    Turns out TNT respawning got changed during the 1.5 update.
    At first I planned to make an accurate timer text that just counts down seconds to respawn.
    However, to prevent timer stacking, Eric decided to update the timer every 1.1s seconds instead of the standard 1.0s.
    This makes it a pain to mod, so instead I had to make some compromises and go for a percentage charge instead.
    
    The goal here is to make it easier to intuit when the box respawns, so you can still play around it.
    Percentage until respawn is still more helpful than absolutely nothing.
    I wanted to keep the original TNT box's respawn design here, so I didn't touch the timer.
    I prefer adding onto existing behavior than editing existing code.
    This mod is supposed to be a quality of life thing after all.
"""


# ba_meta export plugin
class TNTRespawnText(babase.Plugin):

    # This clamping function will make sure a certain value can't go above or below a certain threshold.
    # We're gonna need this functionality in just a bit.
    def clamp(num, min_value, max_value):
        num = max(min(num, max_value), min_value)
        return num

    # This function gets called every time the TNT dies. Doesn't matter how.
    # Explosions, getting thrown out of bounds, stuff.
    # I want the text appearing animation to start as soon as the TNT box blows up.
    def on_tnt_exploded(self):
        self.tnt_has_callback = False
        self._respawn_text.color = (1.0, 1.0, 1.0)
        bs.animate(
            self._respawn_text,
            'opacity',
            {
                0: 0.0,
                self._respawn_time * 0.5: 0.175,
                self._respawn_time: 0.4
            },
        )

    # We're gonna use the magic of decorators to expand the original code with new stuff.
    # This even works with other mods too! Don't replace functions, use decorators!
    # Anyway we're gonna access the TNTSpawner class' init function.
    def new_init(func):
        def wrapper(*args, **kwargs):

            # The update function is not only called by a timer, but also manually
            # during the original init function's execution.
            # This means the code expects a variable that doesn't exist.
            # Let's make it prematurely.
            # args[0] is "self" in the original game code.
            args[0]._respawn_text = None

            # This is where the original game's code is executed.
            func(*args, **kwargs)

            # For each TNT we make we want to add a callback.
            # It's basically a flag that tells the TNT to call a function.
            # We don't want to add several of the same flag at once.
            # We set this to True every time we add a callback.
            # We check for this variable before adding a new one.
            args[0].tnt_has_callback = True

            # Let's make the text.
            # We tap into the spawner position in order to decide where the text should be.
            respawn_text_position = (args[0]._position[0],
                                     args[0]._position[1] - 0.4,
                                     args[0]._position[2])
            args[0]._respawn_text = bs.newnode(
                'text',
                attrs={
                    'text': "",  # we'll set the text later
                    'in_world': True,
                    'position': respawn_text_position,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'color': (1.0, 1.0, 1.0),
                    'opacity': 0.0,
                    'scale': 0.0225,
                    'h_align': 'center',
                    'v_align': 'center',
                },
            )
            # Here we add our callback.
            # Timers don't like calling functions that are outside of the game's "universe".
            # If we call the function directly, we get a PyCallable error.
            # We make a dummy function to avoid this.

            def tnt_callback():
                TNTRespawnText.on_tnt_exploded(args[0])

            # One disadvantage of the documentation is that it doesn't tell you all functions related to the node system.
            # To learn about all possible atttributes and functions you just gotta explore the code and experiment.
            # This add_death_action function of the node system is used in the original game
            # to let the player know if the node got removed.
            # For bombs that would be explosions or when they go out of bounds.
            # This is used to increase the owner's bomb count by one.
            # Here however we'll use this function to manipulate our text logic.
            # We want to animate our text the moment the TNT box dies.
            args[0]._tnt.node.add_death_action(tnt_callback)
        return wrapper
    # Let's replace the original init function with our modified version.
    bascenev1lib.actor.bomb.TNTSpawner.__init__ = new_init(
        bascenev1lib.actor.bomb.TNTSpawner.__init__)

    # Our modified update function.
    # This gets called every 1.1s. Check the TNTSpawner class in the game's code for details.
    def new_update(func):
        def wrapper(*args, **kwargs):

            # Check if our TNT box is still kickin'.
            tnt_alive = args[0]._tnt is not None and args[0]._tnt.node

            func(*args, **kwargs)  # original code

            # The first time this code executes, nothing happens.
            # However once our text node is created properly, let's do some work.
            if args[0]._respawn_text:

                # Let's make a value that will represent percentage.
                # 0 means timer started and 100 means ready.
                value = args[0]._wait_time / args[0]._respawn_time

                # It's annoying when the number jumps from 99% to 100% and it's delayed.
                # Let's make sure this happens less often.
                # I turned a linear curve into an exponential one.
                value = math.pow(value - 0.001, 2)

                # Let's turn the value into a percentage.
                value = math.floor(value * 100)

                # Let's make sure it's actually between 0 and 100.
                value = TNTRespawnText.clamp(value, 0, 100)

                # Let's finish it off with a percentage symbol and preso!
                args[0]._respawn_text.text = str(value)+"%"

            # When the timer ticks, we do different things depending on the time and the state of our TNT box.
            if not tnt_alive:
                # Code goes here if we don't have a TNT box and we reached 100%.
                if args[0]._tnt is None or args[0]._wait_time >= args[0]._respawn_time and args[0]._respawn_text:
                    # Animate the text "bounce" to draw attention
                    bs.animate(
                        args[0]._respawn_text,
                        'scale',
                        {
                            0: args[0]._respawn_text.scale * 1.2,
                            0.3: args[0]._respawn_text.scale * 1.05,
                            0.6: args[0]._respawn_text.scale * 1.025,
                            1.1: args[0]._respawn_text.scale
                        },
                    )
                    # Fade the text away
                    bs.animate(
                        args[0]._respawn_text,
                        'opacity',
                        {
                            0: args[0]._respawn_text.opacity,
                            1.1: 0.0
                        },
                    )
                    # Make sure it says 100%, because our value we calculated earlier might not be accurate at that point.
                    args[0]._respawn_text.text = "100%"

                    # Make our text orange.
                    args[0]._respawn_text.color = (1.0, 0.75, 0.5)

                    # Make some sparks to draw the eye.
                    bs.emitfx(
                        position=args[0]._position,
                        count=int(5.0 + random.random() * 10),
                        scale=0.8,
                        spread=1.25,
                        chunk_type='spark',
                    )
            # What if we still have our TNT box?
            else:
                # If the TNT box is fresly spawned spawned earlier in the function, chances are it doesn't have a callback.
                # If it has, ignore. Otherwise let's add it.
                # Cloning code that already exists in init is not very clean, but that'll do.
                if args[0].tnt_has_callback:
                    return

                def tnt_callback():
                    TNTRespawnText.on_tnt_exploded(args[0])
                args[0]._tnt.node.add_death_action(tnt_callback)
        return wrapper

    # Let's replace the original update function with our modified version.
    bascenev1lib.actor.bomb.TNTSpawner._update = new_update(
        bascenev1lib.actor.bomb.TNTSpawner._update)
