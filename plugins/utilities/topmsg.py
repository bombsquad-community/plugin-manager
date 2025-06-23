from babase import app, Plugin as p
from bascenev1 import gettexture as x, apptimer as z
from bascenev1 import broadcastmessage as push, get_foreground_host_activity as ga, get_chat_messages as gcm

# ba_meta require api 9

# ba_meta export babase.Plugin


class byBordd(p):
    def ear(s):
        a = gcm()
        if a and s.la != a[-1]:
            if app.config.resolve('Chat Muted'):
                push(a[-1], (1, 1, 1), True, s.con)
            s.la = a[-1]
        z(0.1, s.ear)

    def get(s):
        with ga().context:
            s.con = x("upButton")
        s.la = None
        s.ear()


z(1.0, byBordd().get)
