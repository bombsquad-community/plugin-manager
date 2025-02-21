# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 9

"""
    Bomb Radius Visualizer by TheMikirog
        
    With this cutting edge technology, you precisely know
    how close to the bomb you can tread. Supports modified blast radius values!
    
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
from bascenev1lib.actor.bomb import Bomb

if TYPE_CHECKING:
    pass

# ba_meta export plugin


class BombRadiusVisualizer(babase.Plugin):

    # We use a decorator to add extra code to existing code, increasing mod compatibility.
    # Here I'm defining a new bomb init function that'll be replaced.
    def new_bomb_init(func):
        # This function will return our wrapper function, which is going to take the original function's base arguments.
        # Yes, in Python functions are objects that can be passed as arguments. It's bonkers.
        # arg[0] is "self" in our original bomb init function.
        # We're working kind of blindly here, so it's good to have the original function
        # open in a second window for argument reference.
        def wrapper(*args, **kwargs):
            # Here's where we execute the original game's code, so it's not lost.
            # We want to add our code at the end of the existing code, so our code goes under that.
            func(*args, **kwargs)

            # Let's make a new node that's just a circle. It's the some one used in the Target Practice minigame.
            # This is going to make a slightly opaque red circle, signifying damaging area.
            # We aren't defining the size, because we're gonna animate it shortly after.
            args[0].radius_visualizer = bs.newnode('locator',
                                                   # Remove itself when the bomb node dies.
                                                   owner=args[0].node,
                                                   attrs={
                                                       'shape': 'circle',
                                                       'color': (1, 0, 0),
                                                       'opacity': 0.05,
                                                       'draw_beauty': False,
                                                       'additive': False
                                                   })
            # Let's connect our circle to the bomb.
            args[0].node.connectattr('position', args[0].radius_visualizer, 'position')

            # Let's do a fancy animation of that red circle growing into shape like a cartoon.
            # We're gonna read our bomb's blast radius and use it to decide the size of our circle.
            bs.animate_array(args[0].radius_visualizer, 'size', 1, {
                0.0: [0.0],
                0.2: [args[0].blast_radius * 2.2],
                0.25: [args[0].blast_radius * 2.0]
            })

            # Let's do a second circle, this time just the outline to where the damaging area ends.
            args[0].radius_visualizer_circle = bs.newnode('locator',
                                                          # Remove itself when the bomb node dies.
                                                          owner=args[0].node,
                                                          attrs={
                                                              'shape': 'circleOutline',
                                                              # Here's that bomb's blast radius value again!
                                                              'size': [args[0].blast_radius * 2.0],
                                                              'color': (1, 1, 0),
                                                              'draw_beauty': False,
                                                              'additive': True
                                                          })
            # Attach the circle to the bomb.
            args[0].node.connectattr('position', args[0].radius_visualizer_circle, 'position')

            # Let's animate that circle too, but this time let's do the opacity.
            bs.animate(
                args[0].radius_visualizer_circle, 'opacity', {
                    0: 0.0,
                    0.4: 0.1
                })
        return wrapper

    # Finally we """travel through the game files""" to replace the function we want with our own version.
    # We transplant the old function's arguments into our version.
    bascenev1lib.actor.bomb.Bomb.__init__ = new_bomb_init(bascenev1lib.actor.bomb.Bomb.__init__)
