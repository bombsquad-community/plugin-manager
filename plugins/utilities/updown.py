from bauiv1lib import party
from babase import (
    SpecialChar as sc,
    charstr as cs,
    Plugin,
    Call
)
from bauiv1 import (
    containerwidget as cw,
    buttonwidget as bw,
    textwidget as tw,
    getsound as gs
)
from bascenev1 import (
    get_chat_messages as gcm,
    screenmessage as push
)


class VeryPW(party.PartyWindow):
    def __init__(s, *args, **kwargs):
        super().__init__(*args, **kwargs)
        s._n = 0
        s._o = ""
        s._f = True
        for i in range(2):
            bw(
                parent=s._root_widget,
                size=(30, 30),
                label=cs(getattr(sc, f"{['UP', 'DOWN'][i]}_ARROW")),
                button_type='square',
                enable_sound=False,
                position=(-15, 70-(i*40)),
                on_activate_call=[s._p, s._d][i]
            )

    def _c(s, t=""): tw(edit=s._text_field, text=t)
    def _d(s): s._p(1)

    def _p(s, i=0):
        print(s._chat_texts)
        s._w1 = gcm()
        if s._f:
            s._o = tw(query=s._text_field)
            s._f = False
            s._n = 0 if i else len(s._w1)
        s._n = (s._n + (1 if i else -1)) % len(s._w1)
        try:
            s._c((s._w1+[s._o])[s._n].split(": ", 1)[1])
        except IndexError:
            if not s._w1:
                push("Empty chat")
                gs('block').play()
                s._n = 0
                return
            s._n = -1
            s._c(s._o)
        gs('deek').play()

        [z.delete() for z in s._columnwidget.get_children()]
        for z in range(len(s._w1)):
            txt = tw(
                parent=s._columnwidget,
                text=s._w1[z],
                h_align='left',
                v_align='center',
                size=(900, 13),
                scale=0.55,
                color=(1, 1, 1) if z != (s._n if s._n > -
                                         1 else s._n + len(s._w1) + 1) else (0, 0.7, 0),
                position=(-0.6, 0),
                selectable=True,
                autoselect=True,
                click_activate=True,
                maxwidth=s._scroll_width * 0.94,
                shadow=0.3,
                flatness=1.0
            )
            tw(
                txt,
                on_activate_call=Call(s._copy_msg, s._w1[z])
            )
            cw(edit=s._columnwidget, visible_child=txt)

# ba_meta require api 9

# ba_meta export babase.Plugin


class byBordd(Plugin):
    def __init__(s):
        party.PartyWindow = VeryPW
