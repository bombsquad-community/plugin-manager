# Copyright 2025 - Solely by BrotherBoard - Feel free to utilize/modify this for personal use
# Feedback is appreciated - Telegram >> @GalaxyA14user

"""
Sorry v3.1.0 - Because we need to.

Sorry adds a button to party window which
allows you to apologize if you made any mistake.
"""

import bauiv1 as bui
from random import choice
from bascenev1 import chatmessage
from bauiv1lib.party import PartyWindow

plugman = dict(
    plugin_name="sorry",
    description=(
        "Adds a button to party window which "
        "allows you to apologize if you made a mistake."
    ),
    external_url="https://BroBordd.github.io/byBordd",
    authors=[
        {
            "name": "BrotherBoard",
            "email": "brobordd@gmail.com",
            "discord": "BrotherBoard",
            "github": "BroBordd"
        },
    ],
    version='3.1.0',
)

sory = ["Sorry", "Sry", "Sryyy", "Sorryy"]
cash = ["My bad", "My fault", "My mistake", "My apologize"]
lmao = [
    "Oops %!",
    "% didn't mean to.",
    "%, my mistake.",
    "$, apologies!",
    "Ah I slipped, very %.",
    "$, didn't mean to.",
    "Ah, % about that.",
    "A- I did that, $.",
    "%, didn't mean to.",
    "$, %.",
    "$, so %.",
    "Ah % $.",
    "%, $ entirely."
]

def sorry(old):
    def ret(_,*a,**k):
        old(_,*a,**k)
        sorry.btn = bui.buttonwidget(
            parent=_._root_widget,
            size=(50, 35),
            scale=0.7,
            label='Sorry',
            button_type='square',
            position=(_._width - 60, _._height - 83),
            enable_sound=False
        )
        bui.buttonwidget(
            sorry.btn,
            on_activate_call=lambda:(
                getattr(sorry,'cool',1) and (
                    chatmessage(
                        choice(lmao)
                        .replace('%',choice(sory))
                        .replace('$',choice(cash))
                    ),
                    bui.getsound('deek').play(),
                    setattr(sorry,'cool',0),
                    getattr(sorry,'tick',0) or setattr(
                        sorry, 'tick', bui.AppTimer(
                            0.1, lambda:sorry.btn and (
                                bui.buttonwidget(
                                    sorry.btn, label=str(
                                        (time:=getattr(
                                            sorry,
                                            'time',
                                            50
                                        ))/10
                                    )
                                ),
                                setattr(
                                    sorry,
                                    'time',
                                    time-1
                                ) if time > 0 else (
                                    delattr(
                                        sorry,
                                        'tick'
                                    ),
                                    setattr(
                                        sorry,
                                        'time',
                                        50
                                    ),
                                    setattr(
                                        sorry,
                                        'cool',
                                        1
                                    ),
                                    bui.buttonwidget(
                                        sorry.btn, label='Sorry'
                                    )
                                )
                            ) or setattr(
                                sorry,
                                'time',
                                -1+getattr(
                                    sorry,
                                    'time',
                                    50
                                )
                            ),
                            repeat=True
                        )
                    )
                ) or (
                    bui.getsound('block').play(),
                    bui.screenmessage('Too fast!')
                )
            )
        )
    return ret

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(bui.Plugin):
    def __init__(s):
        PartyWindow.__init__ = sorry(_:=PartyWindow.__init__)
