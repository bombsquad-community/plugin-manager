# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)

# ba_meta require api 9

"""
    AutoRun by TheMikirog
    Version 1
    
    Run without holding any buttons. Made for beginners or players on mobile.
    Keeps your character maneuverable.
    Start running as usual to override.
    
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
from bascenev1lib.actor.spaz import Spaz

if TYPE_CHECKING:
    pass

"""
    This mod is much more "technical" than my other mods.
    I highly recommend checking out the code of this mod once you have a good understanding of programming.
    At the very least check out my other heavily commented mods like my Hot Potato gamemode. It's pretty dank!
    Normally you shouldn't flood your scripts with comments like that. 
    I do it here to help people like you get the basic tools required to make your own mods similar to this one. 
    If you write your own code, only comment what can't be easily inferred from reading the code alone.
    Consider this an interactive tutorial of sorts.
    
    Let's start with the goal of this mod; the conception.
    If you play on mobile, the only way you get to run is if you press and hold any other action button like jump or punch.
    Basically, all action buttons do two things at once unless a gamemode disables one of those actions.
    Playing on a gamepad or keyboard gives you the luxury of a dedicated run button, which gives you much more control
    over your movement. This basically forces mobile players that are running to:
    - Punch and risk being open to attacks.
    - Kill all your momentum by jumping.
    - Using the bomb to run, but only after using that same button to throw an already held bomb.
    - Using an inconvenient out of the way grab button to avoid all of that hassle.
    It's a mess. Get a gamepad.
    This mod exists as an alternative to those who can't play on a gamepad, but don't want
    to be inconvenienced by running quirks if they JUST WANT TO PLAY.
    
    The naive implementation of this would be to just running all the time, but here's the catch:
    Running makes turning less tight, which is the compromise for being really fast.
    If you want to have tighter turns, you'd release the run button for a split second, turn and press it again.
    Much easier and more convenient to do if you're on a gamepad.
    The goal of this mod is to replicate this behavior and making it automatic.
    My aim is to get the player moving as fast as possible without making it significantly harder to control.
    This is supposed to help mobile players, not handicap them.
    I can imagine the sweet relief of not being forced to babysit an action button just for running fast.
    Actually it should help gamepad users too, since holding your trigger can be exhausting 
    or even impossible for those with physical disabilities.
    
    For your information, I started writing this mod THREE times.
    Each time with the goal of trying out different ways of achieving my goals.
    I used the code and failures of the previous scripts to make the next one better.
    What you're seeing here is the final iteration; the finished product.
    Don't expect your code to look like this the first time, especially if you're trying something ballsy.
    You will fail, but don't be afraid to experiment.
    Only through experimentation you can forge a failure into a success.
"""

# ba_meta export plugin


class AutoRun(babase.Plugin):
    # During my research and prototyping I figured I'd have to do some linear algebgra.
    # I didn't want to use libraries, since this is supposed to be a standalone mod.
    # Because of this I made certain functions from scratch that are easily accessible.
    # If you are curious over the details, look these up on the Internet.
    # I'll only briefly cover their purpose in the context of the mod.

    # Here's the dot product function.
    # To keep it short, it returns the difference in angle between two vectors.
    # We're gonna use that knowledge to check how tight our turn is.
    # I'll touch on that later.
    def dot(vector_a, vector_b):
        return vector_a[0] * vector_b[0] + vector_a[1] * vector_b[1]

    # This clamping function will make sure a certain value won't go above or below a certain threshold.
    # self.node.run attribute expects a value between 0-1, so this is one way of enforcing this.
    def clamp(num, min_value, max_value):
        num = max(min(num, max_value), min_value)
        return num

    # A vector can be of any length, but we need them to be of length 1.
    # This vector normalization function changes the magnitude of a vector without changing its direction.
    def normalize(vector):
        length = math.hypot(vector[0], vector[1])  # Pythagoras says hi
        # Sometimes we'll get a [0,0] vector and dividing by 0 is iffy.
        # Let's leave the vector unchanged if that's the case.
        if length > 0:
            return [vector[0] / length, vector[1] / length]
        else:
            return vector

    # We use a decorator to add extra code to existing code, increasing mod compatibility.
    # We're gonna use decorators ALOT in this mod.
    # Here I'm defining a new spaz init function that'll be replaced.
    def new_init(func):
        def wrapper(*args, **kwargs):
            # Here's where we execute the original game's code, so it's not lost.
            # We want to add our code at the end of the existing code, so our code goes under that.
            func(*args, **kwargs)

            # We define some variables that we need to keep track of.
            # For future reference, if you see args[0] anywhere, that is "self" in the original function.
            args[0].autorun_timer: bs.Timer | None = None
            args[0].autorun_override = False

            # We wanna do our auto run calculations when the player moves their analog stick to make it responsive.
            # However doing this ONLY tracks changes in analog stick position and some bugs come up because of that.
            # For example moving via dpad on a gamepad can sometimes not execute the run at all.
            # To keep the behavior predictable, we also want to update our auto run functionality with a periodic timer.
            # We could ignore the update on analog stick movement, but then it feels terrible to play. We need both.
            # Update on analog movement for responsive controls, timer to foolproof everything else.

            # To make our timer, we want to have access to our function responsible for doing the auto run logic.
            # The issue is that timers only work when a function is created within the context of the game.
            # Timer throws a tantrum if it references the run_update function, but NOT if that function is an intermediary.
            def spaz_autorun_update():
                AutoRun.run_update(args[0])

            # We don't want this logic to be ran on bots, only players.
            # Check if we have a player assigned to that spaz. If we do, let's make our timer.
            if args[0].source_player:
                # And here's our timer.
                # It loops indefinitely thanks to the 'repeat' argument that is set to True.
                # Notice how it's the capital T Timer instead of the small letter.
                # That's important, because big T returns a timer object we can manipulate.
                # We need it assigned to a variable, because we have to delete it once it stops being relevant.
                args[0].autorun_timer = bs.Timer(0.1, spaz_autorun_update, repeat=True)

        return wrapper

    # Let's replace the original function with our modified version.
    bascenev1lib.actor.spaz.Spaz.__init__ = new_init(
        bascenev1lib.actor.spaz.Spaz.__init__
    )

    # This is the bulk of our mod. Our run_update function.
    # The goal here is to change the self.node.run attribute of our character.
    # This attribute handles running behavior based on how far we pushed the running trigger.
    # 0 means not running and 1 means run trigger fully pressed.
    # On mobile it's always 0 and 1, but on gamepad you can have values between them
    # For example you can do a jog instead of a sprint.
    # We activate this function periodically via a timer and every time the player moves their analog stick.
    # The idea is to make it 1 when the player is running forward and make it 0
    # when the player makes the tightest turn possible.
    # We also want to account for how far the analog stick is pushed.
    def run_update(self) -> None:
        # Let's not run this code if our character does not exist or the player decides to run "manually".
        if not self.node or self.autorun_override:
            return

        # Let's read our player's analog stick.
        # Notice how the vertical direction is inverted (there's a minus in front of the variable).
        # We want the directions to corespond to the game world.
        vertical = -self.node.move_up_down
        horizontal = self.node.move_left_right
        movement_vector = [horizontal, vertical]

        # Get our character's facing direction
        facing_direction = (
            self.node.position[0] - self.node.position_forward[0],
            self.node.position[2] - self.node.position_forward[2],
        )
        # We want our character's facing direction to be a normalized vector (magnitude of 1).
        facing_direction = AutoRun.normalize(facing_direction)

        # We don't want to run our code if the player has their analog stick in a neutral position.
        if movement_vector == [0.0, 0.0]:
            return

        # Get the difference between our current facing direction and where we plan on moving towards.
        # Check the dot function higher up in the script for details.
        dot = AutoRun.dot(facing_direction, AutoRun.normalize(movement_vector))
        if dot > 0.0:
            # Our dot value ranges from -1 to 1.
            # We want it from 0 to 1.
            # 0 being 180 degree turn, 1 being running exactly straight.
            dot = (dot + 1) / 2

        # Let's read how far our player pushed his stick. 1 being full tilt, 0 being neutral.
        # Heres our homie Pythagoras once again
        run_power = math.hypot(movement_vector[0], movement_vector[1])

        # I noticed the player starts running too fast if the stick is pushed half-way.
        # I changed the linear scale to be exponential.
        # easings.net is a great website that shows you different ways of converting a linear curve to some other kind.
        # Here I used the EaseInQuad easing, which is just raising the value to the power of 2.
        # This should make half-way pushes less severe.
        run_power = pow(run_power, 2)

        # Just in case let's clamp our value from 0 to 1.
        run_power = AutoRun.clamp(run_power, 0.0, 1.0)

        # Here we combine our dot result with how far we pushed our stick to get the final running value.
        # Clamping from 0 to 1 for good measure.
        self.node.run = AutoRun.clamp(run_power * dot, 0.0, 1.0)

    # This function is called every time we want to run or touch a running trigger.
    # We have our auto run stuff, but we also want for our mod to play nice with the current running behavior.
    # We also want this to work with my Quickturn mod.
    def new_onrun(func):
        def wrapper(*args, **kwargs):
            # When we hold an action button or press our running trigger at any point, our mod should stop interfering.
            # This won't work if your gamepad has borked triggers though.
            args[0].autorun_override = args[1]
            # Here's our original unchanged function
            func(*args, **kwargs)

        return wrapper

    # We replace the character running function with our modified version.
    bascenev1lib.actor.spaz.Spaz.on_run = new_onrun(bascenev1lib.actor.spaz.Spaz.on_run)

    # There's two function that are called when our player pushes the analog stick - two for each axis.
    # Here's for the vertical axis.
    def new_updown(func):
        def wrapper(*args, **kwargs):
            # Original function
            func(*args, **kwargs)
            # If we're not holding the run button and we're a player, run our auto run behavior.
            if not args[0].autorun_override and args[0].source_player:
                AutoRun.run_update(args[0])

        return wrapper

    # You get the idea.
    bascenev1lib.actor.spaz.Spaz.on_move_up_down = new_updown(
        bascenev1lib.actor.spaz.Spaz.on_move_up_down
    )

    # Let's do the same for our horizontal axis.
    # Second verse same as the first.
    def new_leftright(func):
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            if not args[0].autorun_override and args[0].source_player:
                AutoRun.run_update(args[0])

        return wrapper

    bascenev1lib.actor.spaz.Spaz.on_move_left_right = new_leftright(
        bascenev1lib.actor.spaz.Spaz.on_move_left_right
    )

    # There's one downside to the looping timer - it runs constantly even if the player is dead.
    # We don't want to waste computational power on something like that.
    # Let's kill our timer when the player dies.
    def new_handlemessage(func):
        def wrapper(*args, **kwargs):
            # Only react to the death message.
            if isinstance(args[1], bs.DieMessage):
                # Kill the timer.
                args[0].autorun_timer = None
            # Original function.
            func(*args, **kwargs)

        return wrapper

    bascenev1lib.actor.spaz.Spaz.handlemessage = new_handlemessage(
        bascenev1lib.actor.spaz.Spaz.handlemessage
    )
