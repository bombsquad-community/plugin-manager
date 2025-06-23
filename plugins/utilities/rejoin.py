# ba_meta require api 9
import bascenev1 as bs
from babase import Plugin as v
from bauiv1 import buttonwidget as z, gettexture as x
from bauiv1lib.ingamemenu import InGameMenuWindow as m

m.i = m.p = 0
k = bs.connect_to_party


def j(address, port=43210, print_progress=False):
    try:
        if bool(bs.get_connection_to_host_info_2()):
            bs.disconnect_from_host()
    except:
        pass
    m.i = address
    m.p = port
    k(m.i, m.p, print_progress)


def R(s):
    def w(t, *f, **g):
        z(parent=t._root_widget, size=(23, 26), icon=x('replayIcon'),
          on_activate_call=bs.Call(j, m.i, m.p))
        return s(t, *f, **g)
    return w

# ba_meta export babase.Plugin


class byBordd(v):
    def __init__(s):
        m._refresh_in_game = R(m._refresh_in_game)
        bs.connect_to_party = j
