# Copyright 2025 - Solely by BrotherBoard
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Path v1.0 - Where it's going to be.

Experimental. Path tries to predict the next position of bomb.
Path relies on velocity to operate.
Optionally pass spaz node (holder) to assist prediction.
Feedback is appreciated.
"""

from babase import Plugin
from bascenev1 import (
    timer as tick,
    newnode
)

class Path:
    def __init__(s,node,holder=None):
        if node.body == 'crate': return
        s.node,s.kids = node,[]
        s.me = holder
        s.spy()
    def spy(s):
        n = s.node
        if not n.exists():
            [_.delete() for _ in s.kids]
            s.kids.clear()
            return

        [_.delete() for _ in s.kids]; s.kids.clear()

        ip = n.position
        iv = n.velocity
        if s.me and s.me.hold_node == n:
            mv = s.me.velocity
            iv = (iv[0]+mv[0],iv[1]+mv[1],iv[2]+mv[2])

        dots = 200
        ti = 1.2
        tpd = ti / dots

        tick(0.01, s.spy)
        for i in range(dots):
            t = i * tpd
            px = ip[0] + iv[0] * t
            py = ip[1] + iv[1] * t + 0.5 * -24 * t**2
            pz = ip[2] + iv[2] * t

            if py <=0:
                l = newnode(
                    'locator',
                    owner=n,
                    attrs={
                        'shape': 'circleOutline',
                        'size': [1],
                        'color': (1,1,0),
                        'draw_beauty': False,
                        'additive': True,
                        'position':(px,py,pz)
                    }
                )
                s.kids.append(l)
                break
            dot_node = newnode(
                'text',
                owner=n,
                attrs={
                    'text':'.',
                    'scale':0.02,
                    'position':(px, py, pz),
                    'flatness':1,
                    'in_world':True,
                    'color':(1-i*4/dots,0,0),
                    'shadow':0
                }
            )
            s.kids.append(dot_node)

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    def __init__(s):
        _ = __import__('bascenev1lib').actor.bomb.Bomb
        o = _.__init__
        _.__init__ = lambda z,*a,**k: (o(z,*a,**k),Path(z.node))[0]
