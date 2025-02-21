# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 9

"""
    Ragdoll-B-Gone by TheMikirog
    
    Removes ragdolls. 
    Thanos snaps those pesky feet-tripping body sacks out of existence.
    Literally that's it.
    
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
import random
from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.actor.spazfactory import SpazFactory

if TYPE_CHECKING:
    pass

# ba_meta export plugin


class RagdollBGone(babase.Plugin):

    # We use a decorator to add extra code to existing code, increasing mod compatibility.
    # Any gameplay altering mod should master the decorator!
    # Here I'm defining a new handlemessage function that'll be replaced.
    def new_handlemessage(func):
        # This function will return our wrapper function, which is going to take the original function's base arguments.
        # Yes, in Python functions are objects that can be passed as arguments. It's bonkers.
        # arg[0] is "self", args[1] is "msg" in our original handlemessage function.
        # We're working kind of blindly here, so it's good to have the original function
        # open in a second window for argument reference.
        def wrapper(*args, **kwargs):
            if isinstance(args[1], bs.DieMessage):  # Replace Spaz death behavior

                # Here we play the gamey death noise in Co-op.
                if not args[1].immediate:
                    if args[0].play_big_death_sound and not args[0]._dead:
                        SpazFactory.get().single_player_death_sound.play()

                # If our Spaz dies by falling out of the map, we want to keep the ragdoll.
                # Ragdolls don't impact gameplay if Spaz dies this way, so it's fine if we leave the behavior as is.
                if args[1].how == bs.DeathType.FALL:
                    # The next two properties are all built-in, so their behavior can't be edited directly without touching the C++ layer.
                    # We can change their values though!
                    # "hurt" property is basically the health bar above the player and the blinking when low on health.
                    # 1.0 means empty health bar and the fastest blinking in the west.
                    args[0].node.hurt = 1.0
                    # Make our Spaz close their eyes permanently and then make their body disintegrate.
                    # Again, this behavior is built in. We can only trigger it by setting "dead" to True.
                    args[0].node.dead = True
                    # After the death animation ends (which is around 2 seconds) let's remove the Spaz our of existence.
                    bs.timer(2.0, args[0].node.delete)
                else:
                    # Here's our new behavior!
                    # The idea is to remove the Spaz node and make some sparks for extra flair.
                    # First we see if that node even exists, just in case.
                    if args[0].node:
                        # Make sure Spaz isn't dead, so we can perform the removal.
                        if not args[0]._dead:
                            # Run this next piece of code 4 times.
                            # "i" will start at 0 and becomes higher each iteration until it reaches 3.
                            for i in range(4):
                                # XYZ position of our sparks, we'll take the Spaz position as a base.
                                pos = (args[0].node.position[0],
                                       # Let's spread the sparks across the body, assuming Spaz is standing straight.
                                       # We're gonna change the Y axis position, which is height.
                                       args[0].node.position[1] + i * 0.2,
                                       args[0].node.position[2])
                               # This function allows us to spawn particles like sparks and bomb shrapnel.
                               # We're gonna use sparks here.
                                bs.emitfx(position=pos,  # Here we place our edited position.
                                          velocity=args[0].node.velocity,
                                          # Random amount of sparks between 2 and 5
                                          count=random.randrange(2, 5),
                                          scale=3.0,
                                          spread=0.2,
                                          chunk_type='spark')

                            # Make a Spaz death noise if we're not gibbed.
                            if not args[0].shattered:
                                # Get our Spaz's death noises, these change depending on character skins
                                death_sounds = args[0].node.death_sounds
                                # Pick a random death noise
                                sound = death_sounds[random.randrange(len(death_sounds))]
                                # Play the sound where our Spaz is
                                bs.Sound.play(sound, position=args[0].node.position)
                        # Delete our Spaz node immediately.
                        # Removing stuff is weird and prone to errors, so we're gonna delay it.
                        bs.timer(0.001, args[0].node.delete)

                # Let's mark our Spaz as dead, so he can't die again.
                # Notice how we're targeting the Spaz and not it's node.
                # "self.node" is a visual representation of the character while "self" is his game logic.
                args[0]._dead = True
                # Set his health to zero. This value is independent from the health bar above his head.
                args[0].hitpoints = 0
                return

            # Worry no longer! We're not gonna remove all the base game code!
            # Here's where we bring it all back.
            # If I wanted to add extra code at the end of the base game's behavior, I would just put that at the beginning of my function.
            func(*args, **kwargs)
        return wrapper

    # Finally we """travel through the game files""" to replace the function we want with our own version.
    # We transplant the old function's arguments into our version.
    bascenev1lib.actor.spaz.Spaz.handlemessage = new_handlemessage(
        bascenev1lib.actor.spaz.Spaz.handlemessage)
