import babase as ba
import bauiv1 as bui
import bauiv1lib.party
from bascenev1 import get_chat_messages as gcm, screenmessage as push


class VeryPW(bauiv1lib.party.PartyWindow):
    def __init__(s, *args, **kwargs):
        super().__init__(*args, **kwargs)
        s._n = 0
        s._o = ""
        s._f = True
        s._chat_texts_haxx = []
        for i in range(2):
            bui.buttonwidget(
                parent=s._root_widget,
                size=(30, 30),
                label=ba.charstr(ba.SpecialChar.DOWN_ARROW if i else ba.SpecialChar.UP_ARROW),
                button_type='square',
                position=(-15, 70 - (i * 40)),
                on_activate_call=(s._d if i else s._p)
            )

    def _c(s, t=""): bui.textwidget(edit=s._text_field, text=t)
    def _d(s): s._p(1)

    def _p(s, i=0):
        if s._f:
            s._o = bui.textwidget(query=s._text_field)
            s._f = False
            s._n = -1
        s._n = s._n + (1 if i else -1)
        s._w1 = gcm()
        try:
            s._c((s._w1+[s._o])[s._n].split(": ", 1)[1])
        except IndexError:
            if not s._w1:
                push("Empty chat")
                s._n = 0
                return
            s._n = -1
            s._c(s._o)

        for msg in s._chat_texts:
            msg.delete()
        for msg in s._chat_texts_haxx:
            msg.delete()
        for z in range(len(s._w1)):
            txt = bui.textwidget(parent=s._columnwidget,
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
                                 flatness=1.0)
            bui.textwidget(edit=txt,
                           on_activate_call=ba.Call(
                               s._copy_msg,
                               s._w1[z]))
            s._chat_texts_haxx.append(txt)
            bui.containerwidget(edit=s._columnwidget, visible_child=txt)

# ba_meta require api 9
# ba_meta export plugin


class byBordd(ba.Plugin):
    def __init__(s):
        bauiv1lib.party.PartyWindow = VeryPW