import babase
import bauiv1 as bui
import bauiv1lib.party
import random
import bascenev1 as bs
from bascenev1 import screenmessage as push

# "%" random from sory
# "$" random from cash
sory = ["Sorry", "Sry", "Sryyy", "Sorryy"]
cash = ["My bad", "My fault", "My mistake", "My apologize"]
lmao = [
    "Oops %",
    "% didn't mean to",
    "%, that happens",
    "$, apologies!",
    "Ah I slipped, very %",
    "$, didn't mean to.",
    "Ah, % about that",
    "A- I did that $",
    "%, didn't mean to.",
    "$, forgive the slip",
    "%, didn't mean to mess up",
    "Ah % $",
    "$, forgive the error",
    "%, $ entirely"
]


class SorryPW(bauiv1lib.party.PartyWindow):
    def __init__(s, *args, **kwargs):
        super().__init__(*args, **kwargs)
        s._delay = s._a = 50  # 5 seconds
        s._btn = bui.buttonwidget(
            parent=s._root_widget,
            size=(50, 35),
            scale=0.7,
            label='Sorry',
            button_type='square',
            position=(s._width - 60, s._height - 83),
            on_activate_call=s._apologize
        )

    def _ok(s, a):
        if s._btn.exists():
            bui.buttonwidget(edit=s._btn, label=str((s._delay - a) / 10)
                             if a != s._delay else 'Sorry')
            s._a = a
        else:
            return

    def _apologize(s):
        if s._a != s._delay:
            push("Too fast!")
            return
        else:
            bs.chatmessage(random.choice(lmao).replace(
                '%', random.choice(sory)).replace('$', random.choice(cash)))
            for i in range(10, s._delay+1):
                bs.apptimer((i-10)/10, bs.Call(s._ok, i))

# ba_meta require api 9
# ba_meta export plugin


class byBordd(babase.Plugin):
    def __init__(s):
        bauiv1lib.party.PartyWindow = SorryPW
