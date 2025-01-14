"""Health Indicator mod v1.2
Made by Cross Joy
For 1.7.20+"""

# ----------------------
# v1.2 update
# Enhance compatibility with other mods.
# Fixed the health is not displaying accurately.
# ----------------------

# You can contact me through discord:
# My Discord Id: Cross Joy#0721
# My BS Discord Server: https://discord.gg/JyBY6haARJ

# Add a simple health indicator on every player and bot.

# ba_meta require api 9

from __future__ import annotations

import babase
import bascenev1lib.actor.spaz
from bascenev1lib.actor.spaz import Spaz
import bascenev1 as bs
import bascenev1lib


def new_init_spaz_(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        m = bs.newnode('math',
                       owner=args[0].node,
                       attrs={'input1': (0, 0.7, 0),
                              'operation': 'add'})
        args[0].node.connectattr('position', m, 'input2')
        args[0]._hitpoint_text = bs.newnode(
            'text',
            owner=args[0].node,
            attrs={'text': "\ue047" + str(args[0].hitpoints),
                   'in_world': True,
                   'shadow': 1.0,
                   'flatness': 1.0,
                   'color': (1, 1, 1),
                   'scale': 0.0,
                   'h_align': 'center'})
        m.connectattr('output', args[0]._hitpoint_text, 'position')
        bs.animate(args[0]._hitpoint_text, 'scale', {0: 0.0, 1.0: 0.01})

    return wrapper


def new_handlemessage_spaz_(func):
    def wrapper(*args, **kwargs):
        def update_hitpoint_text(spaz):
            spaz._hitpoint_text.text = "\ue047" + str(spaz.hitpoints)
            r = spaz.hitpoints / 1000
            spaz._hitpoint_text.color = (1, r, r, 1)

        func(*args, **kwargs)
        if isinstance(args[1], bs.PowerupMessage):
            if args[1].poweruptype == 'health':
                update_hitpoint_text(args[0])
        if isinstance(
                args[1], bs.HitMessage) or isinstance(
                args[1], bs.ImpactDamageMessage):
            update_hitpoint_text(args[0])

    return wrapper


# ba_meta export plugin
class ByCrossJoy(babase.Plugin):

    def __init__(self):
        pass

    def on_app_running(self) -> None:
        Spaz.__init__ = new_init_spaz_(Spaz.__init__)
        Spaz.handlemessage = new_handlemessage_spaz_(Spaz.handlemessage)
