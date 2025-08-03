# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> GalaxyA14user

"""
Finder v1.0 - Find anyone

Experimental. Feedback is appreciated.
Useful if you are looking for someone, or just messing around.

Features:
- Fetch servers: Pings all servers, then sorts them by lowest
- Ability to cycle through x servers to collect users
- Ability to connect to servers by player name there

Combine with Power plugin for better control.
"""

from socket import socket, SOCK_DGRAM
from random import uniform as uf
from babase import Plugin, app
from threading import Thread
from time import time, sleep
from bauiv1 import (
    get_ip_address_type as IPT,
    clipboard_set_text as COPY,
    get_special_widget as zw,
    containerwidget as ocw,
    screenmessage as push,
    buttonwidget as obw,
    scrollwidget as sw,
    imagewidget as iw,
    textwidget as tw,
    gettexture as gt,
    apptimer as teck,
    getsound as gs,
    getmesh as gm,
    Call
)
from bascenev1 import (
    disconnect_from_host as BYE,
    connect_to_party as CON,
    protocol_version as PT,
    get_game_roster as GGR
)

class Finder:
    COL1 = (0,0.3,0.3)
    COL2 = (0,0.55,0.55)
    COL3 = (0,0.7,0.7)
    COL4 = (0,1,1)
    COL5 = (1,1,0)
    MAX = 0.3
    TOP = 15
    VER = '1.0'
    MEM = []
    BST = []
    SL = None
    def __init__(s,src):
        s.thr = []
        s.ikids = []
        s.busy = False
        s.s1 = s.snd('powerup01')
        c = s.__class__
        # parent
        z = (460,400)
        s.p = cw(
            scale_origin_stack_offset=src.get_screen_space_center(),
            size=z,
            oac=s.bye
        )[0]
        # footing
        sw(
            parent=s.p,
            size=z,
            border_opacity=0
        )
        # fetch
        tw(
            parent=s.p,
            text='Fetch Servers',
            color=s.COL4,
            position=(19,359)
        )
        bw(
            parent=s.p,
            position=(360,343),
            size=(80,39),
            label='Fetch',
            color=s.COL2,
            textcolor=s.COL4,
            oac=s.fresh
        )
        tw(
            parent=s.p,
            text='Fetches, pings, and sorts public servers.',
            color=s.COL3,
            scale=0.8,
            position=(15,330),
            maxwidth=320
        )
        # separator
        iw(
            parent=s.p,
            size=(429,1),
            position=(17,330),
            texture=gt('white'),
            color=s.COL2
        )
        # cycle
        tw(
            parent=s.p,
            text='Cycle Servers',
            color=s.COL4,
            position=(19,294)
        )
        bw(
            parent=s.p,
            position=(360,278),
            size=(80,39),
            label='Cycle',
            color=s.COL2,
            textcolor=s.COL4,
            oac=s.find
        )
        tw(
            parent=s.p,
            text='Cycles through best servers and saves their players.',
            color=s.COL3,
            scale=0.8,
            position=(15,265),
            maxwidth=320,
            v_align='center'
        )
        # separator
        iw(
            parent=s.p,
            size=(429,1),
            position=(17,265),
            texture=gt('white'),
            color=s.COL2
        )
        # top
        tw(
            parent=s.p,
            text='Server Cycle Limit',
            color=s.COL4,
            position=(19,230)
        )
        s.top = tw(
            parent=s.p,
            position=(398,228),
            size=(80,50),
            text=str(c.TOP),
            color=s.COL4,
            editable=True,
            h_align='center',
            v_align='center',
            corner_scale=0.1,
            scale=10,
            allow_clear_button=False,
            shadow=0,
            flatness=1,
        )
        tw(
            parent=s.p,
            text='Maximum number of servers to cycle.',
            color=s.COL3,
            scale=0.8,
            position=(15,201),
            maxwidth=320
        )
        # separator
        iw(
            parent=s.p,
            size=(429,1),
            position=(17,200),
            texture=gt('white'),
            color=s.COL2
        )
        # players
        pl = s.plys()
        sy = max(len(pl)*30,140)
        p1 = sw(
            parent=s.p,
            position=(20,18),
            size=(205,172),
            border_opacity=0.4
        )
        p2 = ocw(
            parent=p1,
            size=(205,sy),
            background=False
        )
        0 if pl else tw(
            parent=s.p,
            position=(90,100),
            text='Cycle some servers\nto collect players',
            color=s.COL4,
            maxwidth=175,
            h_align='center'
        )
        s.kids = []
        for _,g in enumerate(pl):
            p,a = g
            s.kids.append(tw(
                parent=p2,
                size=(200,30),
                selectable=True,
                click_activate=True,
                color=s.COL3,
                text=p,
                position=(0,sy-30-30*_),
                maxwidth=175,
                on_activate_call=Call(s.hl,_,p),
                v_align='center'
            ))
        # info
        iw(
            parent=s.p,
            position=(235,18),
            size=(205,172),
            texture=gt('scrollWidget'),
            mesh_transparent=gm('softEdgeOutside'),
            opacity=0.4
        )
        s.tip = tw(
            parent=s.p,
            position=(310,98),
            text='Select something to\nview server info',
            color=s.COL4,
            maxwidth=170,
            h_align='center'
        ) if c.SL is None else 0
    def hl(s,_,p):
        [tw(t,color=s.COL3) for t in s.kids]
        tw(s.kids[_],color=s.COL4)
        s.info(p)
    def info(s,p):
        [_.delete() for _ in s.ikids]
        s.ikids.clear()
        s.tip and s.tip.delete()
        bst = s.__class__.BST
        for _ in bst:
            for r in _['roster']:
                if r['display_string'] == p:
                    i = _
                    break
        for _ in range(3):
            t = str(i['nap'[_]])
            s.ikids.append(tw(
                parent=s.p,
                position=(250,155-40*_),
                h_align='center',
                v_align='center',
                maxwidth=175,
                text=t,
                color=s.COL4,
                size=(175,30),
                selectable=True,
                click_activate=True,
                on_activate_call=Call(s.copy,t)
            ))
        s.ikids.append(bw(
            parent=s.p,
            position=(253,30),
            size=(166,30),
            label='Connect',
            color=s.COL2,
            textcolor=s.COL4,
            oac=Call(CON,i['a'],i['p'],False)
        ))
    def copy(s,t):
        s.ding(1,1)
        TIP('Copied to clipboard!')
        COPY(t)
    def plys(s):
        z = []
        me = app.plus.get_v1_account_name()
        me = [me,'\ue063'+me]
        for _ in s.__class__.BST:
            a = _['a']
            if (r:=_.get('roster',{})):
                for p in r:
                    ds = p['display_string']
                    0 if ds in me else z.append((ds,a))
        return sorted(z,key=lambda _: _[0].startswith('\ue030Server'))
    def snd(s,t):
        l = gs(t)
        l.play()
        teck(uf(0.14,0.18),l.stop)
        return l
    def bye(s):
        s.s1.stop()
        ocw(s.p,transition='out_scale')
        l = s.snd('laser')
        f = lambda: teck(0.01,f) if s.p else l.stop()
        f()
    def ding(s,i,j):
        a = ['Small','']
        x,y = a[i],a[j]
        s.snd('ding'+x)
        teck(0.1,gs('ding'+y).play)
    def fresh(s):
        if s.busy: BTW("Still busy!"); return
        TIP('Fetching servers...')
        s.ding(1,0)
        s.busy = True
        p = app.plus
        p.add_v1_account_transaction(
            {
                'type': 'PUBLIC_PARTY_QUERY',
                'proto': PT(),
                'lang': 'English'
            },
            callback=s.kang,
        )
        p.run_v1_account_transactions()
    def kang(s,r):
        c = s.__class__
        c.MEM = r['l']
        s.thr = []
        for _ in s.__class__.MEM:
            t = Thread(target=Call(s.ping,_))
            s.thr.append(t)
            t.start()
        teck(s.MAX*4,s.join)
    def join(s):
        c = s.__class__
        [t.join() for t in s.thr]
        far = s.MAX*3000
        c.MEM = [_ for _ in c.MEM if _['ping']]
        c.MEM.sort(key=lambda _: _['ping'])
        s.thr.clear()
        TIP(f'Loaded {len(c.MEM)} servers!')
        s.ding(0,1)
        s.busy = False
    def find(s):
        if s.busy: BTW("Still busy!"); return
        c = s.__class__
        if not c.MEM:
            BTW('Fetch some servers first!')
            return
        t = tw(query=s.top)
        if not t.isdigit():
            BTW('Invalid cycle limit!')
            return
        top = int(t)
        if not (0 < top < len(c.MEM)):
            BTW('Cycle count is too '+['big','small'][top<=0]+'!')
            return
        c.TOP = top
        s.ding(1,0)
        TIP('Starting cycle...')
        s.busy = True
        s.ci = s.lr = 0
        c.BST = c.MEM[:top]
        s.cycle()
    def cycle(s):
        _ = s.__class__.BST[s.ci]
        s.ca = _['a']
        CON(s.ca,_['p'],False)
        s.wait()
    def wait(s,i=5):
        r = GGR()
        if (r != s.lr) and r: s.__class__.BST[s.ci]['roster'] = s.lr = r; return s.next()
        if not i: s.__class__.BST[s.ci]['roster'] = []; return s.next()
        teck(0.1,Call(s.wait,i-1))
    def next(s):
        s.ci += 1
        if s.ci >= len(s.__class__.BST):
            BYE()
            teck(0.5,s.yay)
            return
        s.cycle()
    def yay(s):
        TIP('Cycle finished!')
        s.ding(0,1)
        s.busy = False
        zw('squad_button').activate()
        teck(0.3,byBordd.up)
    def ping(s,_):
        sock = ping = None
        a,p = _['a'],_['p']
        sock = socket(IPT(a),SOCK_DGRAM)
        try: sock.connect((a,p))
        except: ping = None
        else:
            st = time()
            sock.settimeout(s.MAX)
            yes = False
            for _i in range(3):
                try:
                    sock.send(b'\x0b')
                    r = sock.recv(10)
                except: r = None
                if r == b'\x0c':
                    yes = True
                    break
                sleep(s.MAX)
            ping = (time()-st)*1000 if yes else None
        finally:
            _['ping'] = ping
            sock.close()

# Patches
bw = lambda *,oac=None,**k: obw(
    texture=gt('white'),
    on_activate_call=oac,
    enable_sound=False,
    **k
)
cw = lambda *,size=None,oac=None,**k: (p:=ocw(
    parent=zw('overlay_stack'),
    background=False,
    transition='in_scale',
    size=size,
    on_outside_click_call=oac,
    **k
)) and (p,iw(
    parent=p,
    texture=gt('softRect'),
    size=(size[0]*1.2,size[1]*1.2),
    position=(-size[0]*0.1,-size[1]*0.1),
    opacity=0.55,
    color=(0,0,0)
),iw(
    parent=p,
    size=size,
    texture=gt('white'),
    color=Finder.COL1
))

# Global
BTW = lambda t: (push(t,color=(1,1,0)),gs('block').play())
TIP = lambda t: push(t,Finder.COL3)

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    BTN = None
    @classmethod
    def up(c):
        c.BTN.activate() if c.BTN.exists() else None
    def __init__(s):
        from bauiv1lib import party
        p = party.PartyWindow
        a = '__init__'
        o = getattr(p,a)
        setattr(p,a,lambda z,*a,**k:(o(z,*a,**k),s.make(z))[0])
    def make(s,z):
        sz = (80,30)
        p = z._root_widget
        x,y = (-60,z._height-45)
        iw(
            parent=p,
            size=(sz[0]*1.34,sz[1]*1.4),
            position=(x-sz[0]*0.14,y-sz[1]*0.20),
            texture=gt('softRect'),
            opacity=0.2,
            color=(0,0,0)
        )
        s.b = s.__class__.BTN = bw(
            parent=p,
            position=(x,y),
            label='Finder',
            color=Finder.COL1,
            textcolor=Finder.COL3,
            size=sz,
            oac=lambda:Finder(s.b)
        )
