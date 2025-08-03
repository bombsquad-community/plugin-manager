# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Replay v2.5 - Simple replay player

Experimental. Feedback is appreciated.
Adds a button to pause menu and watch menu.

Features:
- Common features (pause/play/seek/speed/replay)
- Press on progress bar to seek anywhere
- Advanced free camera target control
- Ability to zoom in/out to target
- Uses pybrp to display how long a replay is
- Good UI with detailed toast pop ups
- Ability to show/hide UI
- Uses threading everywhere
"""

from babase import Plugin
from bauiv1 import (
    get_virtual_screen_size as res,
    get_special_widget as gsw,
    clipboard_set_text as COPY,
    get_replays_dir as rdir,
    containerwidget as ocw,
    screenmessage as push,
    spinnerwidget as spin,
    buttonwidget as obw,
    fade_screen as fade,
    scrollwidget as sw,
    SpecialChar as sc,
    imagewidget as iw,
    textwidget as otw,
    gettexture as gt,
    apptimer as teck,
    AppTimer as tock,
    getsound as gs,
    UIScale as UIS,
    charstr as cs,
    Call,
    app
)
from bascenev1 import (
    set_replay_speed_exponent as SET,
    get_replay_speed_exponent as GET,
    new_replay_session as PLAY,
    resume_replay as RESUME,
    pause_replay as PAUSE,
    seek_replay as SEEK,
    is_in_replay as ON
)
from _babase import (
    set_camera_position as SCP,
    get_camera_position as GCP,
    set_camera_manual as SCM,
    set_camera_target as SCT,
    get_camera_target as GCT
)
from os.path import join, dirname, getsize, basename
from time import time, strftime, gmtime
from random import uniform as uf
from threading import Thread
from os import listdir as ls
from struct import unpack

class Replay:
    VER = '2.5'
    COL1 = (0.18,0.18,0.18)
    COL2 = (1,1,1)
    COL3 = (0,1,0)
    COL4 = (0,1,1)
    BUSY = False
    @classmethod
    def BUS(c,b=None):
        if b is None: return c.BUSY
        c.BUSY = b
    def __init__(s,source=None):
        s.sl = s.rn = s.buf = None
        s.ohno = False
        s._h = _H()
        s.p = s.cw(
            src=source.get_screen_space_center(),
            p=GOS(),
            size=(400,500),
            oac=lambda:(ocw(s.p,transition='out_scale' if source and source.exists() else 'out_left'),s.snd('laser'),s.trs.stop())
        )
        s.trs = s.snd('powerup01')
        s.tw(
            p=s.p,
            h_align='center',
            text='Replay',
            pos=(175,460),
            scale=2
        )
        sy = 360
        p1 = sw(
           parent=s.p,
           size=(sy,sy),
           position=(25,80)
        )
        s.rd = rdir()
        a = [_ for _ in ls(s.rd) if _.endswith('.brp')]
        v = 30*len(a)
        p2 = ocw(
            parent=p1,
            background=False,
            size=(sy,v)
        )
        s.kids = []
        for i,_ in enumerate(a):
            t = s.tw(
                p=p2,
                click_activate=True,
                selectable=True,
                pos=(0,v-30*i-30),
                text=_,
                maxwidth=sy,
                size=(sy,30),
                color=s.COL2,
                oac=Call(s.hl,i,_)
            )
            s.kids.append(t)
        s.psrc = None
        for _ in range(3):
            b = s.bw(
                p=s.p,
                pos=(25+120*_,30),
                size=(120,40),
                label=['Show','Copy','Run'][_],
                oac=Call(s.con,[s.show,s.copy,s.play][_]),
                icon=gt(['folder','file','nextLevelIcon'][_])
            )
            if _ == 2: s.psrc = b
    def snd(s,t):
        h = gs(t)
        h.play()
        teck(uf(0.14,0.17),h.stop)
        return h
    def get(s):
        return join(s.rd,s.rn)
    def copy(s):
        s.snd('dingSmallHigh')
        COPY(s.get())
        push('Copied replay path to clipboard!',color=s.COL3)
    def show(s):
        gs('ding').play()
        push(s.get(),color=s.COL3)
    def con(s,f):
        if s.sl is None: BTW('Select a replay!'); return
        if ON(): BTW('A replay is already running!'); return
        return f()
    def hl(s,i,n):
        if s.sl == i:
            s.psrc = s.kids[i]
            s.play()
            return
        s.sl = i
        s.rn = n
        [otw(_,color=s.COL2) for _ in s.kids]
        otw(s.kids[i],color=s.COL3)
    def play(s):
        if s.BUS(): return
        s.BUS(True)
        gs('deek').play()
        s.load()
    def load(s):
        src = s.psrc.get_screen_space_center()
        if s.psrc.get_widget_type() == 'text':
            src = (src[0]-170,src[1])
        s.parc = c = s.cw(
            src=src,
            size=(300,200),
            p=GOS()
        )
        s.tw(
            p=c,
            text='Player',
            pos=(125,150),
            h_align='center',
            scale=1.4
        )
        spin(
            parent=c,
            size=60,
            position=(75,100)
        )
        s.st = s.tw(
            p=c,
            text='Reading...',
            pos=(115,87)
        )
        s.tpar = s.tw(
            p=c,
            pos=(125,30),
            maxwidth=240,
            text=f'{s.rn} with total of {getsize(s.get())} bytes\nstreaming bytes to pybrp_stream',
            h_align='center'
        )
        s.tpar2 = s.tw(
            p=c,
            maxwidth=240,
            pos=(30,20),
            v_align='bottom'
        )
        s.par = [0,1]
        teck(0.5,Thread(target=s.calc).start)
        teck(0.5,s.fpar)
        s.spy(s.calc2)
    def fpar(s):
        a,b = s.par
        teck(0.1,s.fpar) if (a!=b) and (not s.ohno) else 0
        if not a: return
        p = a/b*100
        t = '\u2588'*int(p)+'\u2591'*int(100-p)
        if not s.ohno:
            try:
                otw(s.tpar,text=t)
                otw(s.tpar2,text=f'{a} of {b} bytes read')
            except: return
    def calc(s):
        try: s.buf = GMS(s._h,s.get(),s.par)
        except: s.buf = 0
    def calc2(s,t):
        otw(s.st,text='Starting...' if t else 'Wait what?')
        otw(s.tpar2,text=f'result was {t} milleseconds') if t else t
        if not t:
            s.ohno = True
            otw(s.tpar,text='pybrp returned zero duration, error?\nclosing this window in 5 seconds')
            otw(s.tpar2,text='')
        teck(1 if t else 5,Call(s._play,t))
    def spy(s,f,i=60):
        if not i:
            s.buf = None
            f(None)
            return
        if s.buf is not None:
            b = s.buf
            s.buf = None
            f(b)
            return
        teck(0.5,Call(s.spy,f,i-1))
    def _play(s,t):
        if t == 0:
            BTW("Couldn't load replay!")
            ocw(s.parc,transition='out_scale')
            s.BUS(False)
            return
        SET(0)
        fade(1)
        Player(path=s.get(),duration=t)
        s.BUS(False)
    bw = lambda s,p=None,oac=None,pos=None,**k: obw(
        parent=p,
        color=s.COL1,
        textcolor=s.COL2,
        on_activate_call=oac,
        position=pos,
        button_type='square',
        enable_sound=False,
        **k
    )
    cw = lambda s,p=None,pos=None,src=None,oac=None,**k: ocw(
        color=s.COL1,
        parent=p,
        position=pos,
        scale_origin_stack_offset=src,
        transition='in_scale',
        on_outside_click_call=oac,
        **k
    )
    tw = lambda s,color=None,oac=None,p=None,pos=None,**k: otw(
        parent=p,
        position=pos,
        color=color or s.COL2,
        on_activate_call=oac,
        **k
    )

class Player:
    TICK = 0.01
    COL0 = (0.5,0,0)
    COL1 = (1,0,0)
    COL2 = (0.5,0.5,0)
    COL3 = (1,1,0)
    COL4 = (0,0.5,0)
    COL5 = (0,1,0)
    COL6 = (0,0.5,0.5)
    COL7 = (0,1,1)
    COL8 = (0.6,0.6,0.6)
    COL9 = (8,0,0)
    COL10 = (0.5,0.25,0)
    COL11 = (1,0.5,0)
    COL12 = (0.5,0.25,0.5)
    COL13 = (1,0.5,1)
    COL14 = (0.5,0.5,0.5)
    COL15 = (1,1,1)
    COL16 = (0.1, 0.2, 0.4)
    COL17 = (1, 1.7, 2)
    def __init__(s,path,duration):
        s.path = path
        s.du = duration
        s.ds = s.du / 1000
        s.ps = s.nah = s.camon = s.snma = s.gay = False
        s.caml = None
        s.rn = s.st = s.pr = 0
        s.camz = 1
        [setattr(s,_,[]) for _ in ['kids','camkids','hdkids','snkids','snuikids']]
        PLAY(path)
        x,y = res()
        s.sy = 80
        s.p = ocw(
            size=(x,s.sy),
            stack_offset=(0,-y/2+s.sy/2),
            background=False
        )
        s.bg = iw(
            parent=s.p,
            texture=gt('black'),
            size=(x+3,s.sy+5),
            position=(0,-2),
            opacity=0.4
        )
        s.mkui()
        s.mkhd()
        # finally
        s.sp = 1
        s.foc()
        s.play()
    def mkhd(s):
        f = s.hdkids.append
        s.tex=['\u25bc','\u25b2']
        s.kekb = s.bw(
            p=s.p,
            pos=(20,15),
            size=(50,50),
            oac=s.kek,
            color=s.COL10
        )
        f(s.kekb)
        s.kekt = otw(
            parent=s.p,
            text=s.tex[s.nah],
            position=(44,30),
            scale=2,
            shadow=0.4,
            color=s.COL11
        )
        f(s.kekt)
        f(iw(
            parent=s.p,
            position=(18,13),
            size=(54,54),
            color=s.COL10,
            texture=gt('white'),
            opacity=0.4
        ))
    def killhd(s):
        [_.delete() for _ in s.hdkids]
        s.hdkids.clear()
    def mkui(s):
        s.up = True
        f = s.kids.append
        x,y = res()
        sy = s.sy
        p = s.p
        # exit
        f(s.bw(
            p=p,
            pos=(x-65,15),
            size=(50,50),
            color=s.COL0,
            oac=s.bye
        ))
        c = s.COL1
        f(iw(
            parent=p,
            texture=gt('crossOut'),
            color=(c[0]*10,c[1]*10,c[2]*10),
            position=(x-60,20),
            size=(40,40)
        ))
        # speed
        for _ in range(2):
            a = [
                'FAST_FORWARD_BUTTON',
                'REWIND_BUTTON'
            ][_]
            pos = (x-130-260*_,15)
            f(s.bw(
                p=p,
                pos=pos,
                size=(50,50),
                color=s.COL2,
                oac=Call(s.boost,[1,-1][_]),
                repeat=True
            ))
            f(otw(
                parent=p,
                text=cs(getattr(sc,a)),
                color=s.COL3,
                position=(pos[0]-2,pos[1]+13),
                h_align='center',
                v_align='center',
                scale=1.8,
                shadow=0.3
            ))
        # seek
        for _ in range(2):
            a = [
                'RIGHT_ARROW',
                'LEFT_ARROW'
            ][_]
            pos = (x-195-130*_,15)
            f(s.bw(
                p=p,
                pos=pos,
                size=(50,50),
                color=s.COL4,
                oac=Call(s.seek,[1,-1][_]),
                repeat=True
            ))
            f(otw(
                parent=p,
                text=cs(getattr(sc,a)),
                color=s.COL5,
                position=(pos[0]-1,pos[1]+12),
                h_align='center',
                v_align='center',
                scale=1.7,
                shadow=0.2
            ))
        # pause
        pos = (x-260,15)
        f(s.bw(
            p=p,
            pos=pos,
            size=(50,50),
            color=s.COL6,
            oac=s.toggle
        ))
        s.tt = otw(
            parent=p,
            color=s.COL7,
            position=(pos[0]+12,pos[1]+11),
            scale=1.5,
            shadow=0.3
        )
        f(s.tt)
        s.toggle(dry=True)
        # replay
        pos = (x-455,15)
        f(s.bw(
            p=p,
            pos=pos,
            size=(50,50),
            color=s.COL12,
            oac=s.rloop
        ))
        c = s.COL13
        sk = 1.5
        f(iw(
            parent=p,
            texture=gt('replayIcon'),
            color=(c[0]*sk,c[1]*sk,c[2]*sk),
            position=(pos[0]+2,pos[1]+1),
            size=(47,47),
        ))
        # progress
        pos = (285,sy/2-2)
        s.px = x-790
        f(iw(
            parent=p,
            texture=gt('white'),
            size=(s.px,5),
            position=pos,
            opacity=0.4,
            color=s.COL8
        ))
        s.nbp = (pos[0]-24,pos[1]-22)
        s.nb = iw(
            parent=p,
            texture=gt('nub'),
            size=(50,50),
            position=s.nbp,
            opacity=0.4,
            color=s.COL9
        )
        f(s.nb)
        # timestamp
        s.ct = otw(
            parent=p,
            position=(155,40),
            color=s.COL7,
            text=FOR(s.rn-s.st)
        )
        f(s.ct)
        f(otw(
            parent=p,
            position=(155,11),
            text=FOR(s.ds),
            color=s.COL6
        ))
        # sensor
        sx,sy = (285,15)
        n = 100
        tp = s.px/n
        for _ in range(n):
            f(obw(
                label='',
                parent=p,
                position=(sx+tp*_,sy),
                size=(tp,50),
                texture=gt('empty'),
                enable_sound=False,
                on_activate_call=Call(s.jump,_/n),
                selectable=False
            ))
        # camera
        f(s.bw(
            p=s.p,
            pos=(85,15),
            size=(50,50),
            color=s.COL14,
            oac=s.cam
        ))
        c = s.COL15
        sk = 1.5
        f(iw(
            parent=s.p,
            texture=gt('achievementOutline'),
            position=(88,18),
            color=(c[0]*sk,c[1]*sk,c[2]*sk),
            size=(45,45)
        ))
        # info
        ix,iy = (443,98)
        s.ok = iw(
            texture=gt('white'),
            position=(x-456,100),
            parent=p,
            size=(ix,iy),
            opacity=0
        )
        f(s.ok)
        s.ok2 = otw(
            position=(x-ix+182.5,iy+64),
            h_align='center',
            scale=1.2,
            parent=p,
            maxwidth=ix-20
        )
        f(s.ok2)
        s.ok3 = otw(
            position=(x-ix+182.5,iy+10),
            h_align='center',
            parent=p,
            maxwidth=ix-20
        )
        f(s.ok3)
    def mkcamui(s):
        f = s.camkids.append
        x,y = (19,100)
        s.cambg = iw(
            parent=s.p,
            size=(235,260),
            position=(x,y),
            texture=gt('white'),
            color=s.COL14,
            opacity=0.05
        )
        f(s.cambg)
        # tip
        s.cambg2 = iw(
            parent=s.p,
            size=(235,100),
            opacity=0.05,
            position=(x,y+267),
            color=s.COL14,
            texture=gt('white')
        )
        f(s.cambg2)
        s.fcam()
        f(otw(
            parent=s.p,
            h_align='center',
            v_align='center',
            text='To maintain animated\nsmooth camera, keep\nzoom at auto.',
            maxwidth=205,
            max_height=190,
            position=(x+92,y+300),
            color=s.COL15
        ))
        # reset
        f(s.bw(
            p=s.p,
            label='Reset',
            color=s.COL14,
            textcolor=s.COL15,
            size=(205,30),
            pos=(x+15,y+7),
            oac=s.camr
        ))
        # seperator
        f(iw(
            parent=s.p,
            size=(219,2),
            position=(x+8,y+44),
            texture=gt('white'),
            color=s.COL15,
            opacity=0.6
        ))
        # look
        f(s.bw(
            p=s.p,
            label='Look',
            pos=(x+15,y+53),
            color=s.COL14,
            textcolor=s.COL15,
            size=(205,30),
            oac=s.look
        ))
        s.ltw = otw(
            parent=s.p,
            text=str(RND(s.caml) if s.caml else 'players'),
            v_align='center',
            h_align='center',
            position=(x+92,y+90),
            color=s.COL14,
            maxwidth=205,
            max_height=40
        )
        f(s.ltw)
        f(otw(
            parent=s.p,
            text='Currently looking at:',
            v_align='center',
            h_align='center',
            position=(x+92,y+120),
            color=s.COL15,
            maxwidth=205,
            max_height=40
        ))
        # seperator
        f(iw(
            parent=s.p,
            size=(219,2),
            position=(x+8,y+154),
            texture=gt('white'),
            color=s.COL15,
            opacity=0.6
        ))
        # zoom
        [f(s.bw(
            p=s.p,
            label=['-','+'][_],
            pos=(x+13+113*_,y+163),
            color=s.COL14,
            textcolor=s.COL15,
            size=(98,30),
            repeat=True,
            oac=Call(s.zoom,[1,-1][_])
        )) for _ in [0,1]]
        s.ztw = otw(
            parent=s.p,
            text=f'x{round(0.5**(s.camz-1),2)}' if s.camz != 1 else 'x1.0' if s.gay else 'auto',
            v_align='center',
            h_align='center',
            position=(x+92,y+200),
            color=s.COL14,
            maxwidth=205,
            max_height=40
        )
        f(s.ztw)
        f(otw(
            parent=s.p,
            text='Current zoom:',
            v_align='center',
            h_align='center',
            position=(x+92,y+227),
            color=s.COL15,
            maxwidth=205,
            max_height=40
        ))
    def zoom(s,i):
        n = round(s.camz+i*0.05,2)
        if s.camz == 1 and not s.gay:
            SCM(True)
            s.camp = GCP()
            s.caml = GCT()
            otw(s.ltw,text=str(RND(s.caml)))
        if n == 1 and not s.gay:
            SCM(False)
            s.caml = None
            otw(s.ltw,text='players')
        s.camz = n
        otw(s.ztw,text=f'x{round(0.5**(n-1),2)}' if n != 1 else 'x1.0' if s.gay else 'auto')
        s.zom()
    def look(s):
        s.killui()
        s.killhd()
        s.fkek(0.4,-0.1)
        s.camlo = s.caml
        s.campo = GCP()
        s.gayo = s.gay
        s.mksns()
        s.mksnui()
        s.mksnb()
        s.mksni()
    def _look(s,x,y):
        o = s.caml or GCT()
        sk = 0.7*s.camz
        s.caml = n = (o[0]+x*sk,o[1]+y*sk,o[2])
        0 if s.snma else otw(s.snt,text=str(RND(n)))
        s.camp = GCP()
        if s.camz != 1: s.gay = True
        s.camz = 1
    def foc(s):
        s.tfoc = tock(0.01,s.focus,repeat=True)
    def focus(s):
        SCT(*s.caml) if s.caml else 0
    def zom(s):
        if s.camz == 1 and not s.gay: return
        z = s.camz
        tx,ty,tz = GCT()
        px,py,pz = s.camp
        npx = tx+(px-tx)*z
        npy = ty+(py-ty)*z
        npz = tz+(pz-tz)*z
        SCP(npx,npy,npz)
    def fockill(s):
        s.tfoc = None
    def snsave(s):
        s.snbye()
    def snbye(s):
        s.killsn()
        s.mkui()
        s.mkhd()
        s.fkek(0,0.1)
        s.pro()
    def mksns(s):
        x,y = res()
        sz = 50
        a = int(x/sz)
        b = int(y/sz)
        ha = a/2
        hb = b/2
        [s.snkids.append(obw(
            parent=s.p,
            size=(sz,sz),
            position=(i*sz,j*sz),
            texture=gt('empty'),
            enable_sound=False,
            on_activate_call=Call(s._look,i-ha,j-hb),
            label='',
            repeat=True
        ))
        for i in range(a)
        for j in range(b)]
    def mksnui(s):
        f = s.snuikids.append
        f(iw(
            parent=s.p,
            position=(0,3),
            color=s.COL14,
            opacity=0.4,
            texture=gt('white'),
            size=(232,190)
        ))
        # buttons
        f(s.bw(
            p=s.p,
            pos=(14,50),
            size=(204,30),
            label='Target Players',
            color=s.COL14,
            textcolor=s.COL15,
            oac=s.sntar
        ))
        f(s.bw(
            p=s.p,
            pos=(10,90),
            color=s.COL14,
            label='Cancel',
            size=(99,30),
            textcolor=s.COL15,
            oac=s.sncancel
        ))
        f(s.bw(
            p=s.p,
            pos=(123,90),
            color=s.COL14,
            label='Save',
            size=(99,30),
            textcolor=s.COL15,
            oac=s.snsave
        ))
        # info
        f(otw(
            parent=s.p,
            position=(90,160),
            color=s.COL15,
            text='Currently looking at:',
            h_align='center',
            maxwidth=220
        ))
        s.snt = otw(
            parent=s.p,
            position=(90,130),
            color=s.COL14,
            h_align='center',
            text=str(RND(s.caml) if s.caml else 'players')
        )
        f(s.snt)
        # tip
        f(iw(
            parent=s.p,
            position=(0,200),
            color=s.COL14,
            opacity=0.4,
            texture=gt('white'),
            size=(232,110)
        ))
        f(otw(
            parent=s.p,
            position=(90,240),
            text='Longpress anywhere\nto look around. Tap on \nsomething to look at it.\nPause for calmer control!',
            h_align='center',
            v_align='center',
            maxwidth=225,
            max_height=105
        ))
        # crosshair
        x,y = res()
        h = 20
        [f(iw(
            parent=s.p,
            position=(x/2,y/2-h/2+h*0.1) if _ else (x/2-h/2,y/2+h*0.1),
            size=(3,h*1.15) if _ else (h*1.15,3),
            color=s.COL1,
            texture=gt('white')
        )) for _ in [0,1]]
        # top
        k = 60
        for j in range(2):
            f(iw(
                parent=s.p,
                texture=gt('white'),
                color=s.COL1,
                position=(x/2+[-k,k-h][j],y/2+k),
                size=(h*1.1,3)
            ))
        # right
        for j in range(2):
            f(iw(
                parent=s.p,
                texture=gt('white'),
                color=s.COL1,
                position=(x/2+k,y/2+[k-h,-k+h*0.3][j]),
                size=(3,h*+1.1)
            ))
        # bottom
        for j in range(2):
            f(iw(
                parent=s.p,
                texture=gt('white'),
                color=s.COL1,
                position=(x/2+[-k,k-h][j],y/2-h/2-k+h*0.8),
                size=(h*1.1,3)
            ))
        # left
        for j in range(2):
            f(iw(
                parent=s.p,
                texture=gt('white'),
                color=s.COL1,
                position=(x/2-k,y/2+[k-h,-k+h*0.3][j]),
                size=(3,h*1.1)
            ))
    def killsnui(s):
        [_.delete() for _ in s.snuikids]
    def snhide(s):
        if getattr(s,'snbusy',0): return
        s.snma = not s.snma
        s.snbusy = True
        if s.snma:
            s.snanim(204,14,-1)
            obw(s.snbtn,label=cs(sc.UP_ARROW))
            s.killsnui()
        else:
            obw(s.snbtn,texture=gt('white'))
            s.snanim(36,7,1)
            iw(s.sni,opacity=0)
    def mksni(s):
        s.sni = iw(
            parent=s.p,
            position=(7,8),
            color=s.COL14,
            opacity=0,
            size=(36,33),
            texture=gt('white')
        )
        s.snkids.append(s.sni)
    def mksnb(s):
        s.snbtn = s.bw(
            p=s.p,
            pos=(14,10),
            color=s.COL14,
            label='Cinema Mode',
            size=(204,30),
            textcolor=s.COL15,
            oac=s.snhide
        )
        s.snkids.append(s.snbtn)
    def snanim(s,a,b,i):
        a += (163/35)*i
        b += 0.2*i
        obw(s.snbtn,size=(a,30),position=(b,10))
        if not (14>=b>=7):
            s.snbusy = False
            if s.snma:
                obw(s.snbtn,texture=gt('empty'))
                iw(s.sni,opacity=0.4)
            else:
                s.mksnui()
                s.snbtn.delete()
                s.mksnb()
                obw(s.snbtn,label='Cinema Mode')
            return
        teck(0.004,Call(s.snanim,a,b,i))
    def killsn(s):
        s.killsnui()
        [_.delete() for _ in s.snkids]
    def all(s):
        return s.trash()+s.hdkids+s.snkids
    def sntar(s):
        s.caml = None
        otw(s.snt,text='players')
        if s.camz != 1 or s.gay:
            s.camz = 1
            s.gay = False
            SCM(False)
    def sncancel(s):
        s.caml = s.camlo
        s.camp = s.campo
        s.gay = s.gayo
        if s.camz != 1 or s.gay:
            SCM(True)
            SCP(*s.camp)
        s.snbye()
    def cam(s):
        if s.camon:
            s.camon = False
            [_.delete() for _ in s.camkids]
            s.camkids.clear()
            s.fcam(0.4,-0.1)
        else:
            s.camon = True
            s.mkcamui()
    def camr(s):
        SCM(False)
        s.caml = None
        s.gay = False
        s.camz = 1
        otw(s.ltw,text='players')
        otw(s.ztw,text='auto')
    def fcam(s,i=0,a=0.1):
        if i > 0.4 or i < 0:
            if a < 0: s.cambg.delete()
            return
        if not s.cambg.exists(): return
        iw(s.cambg,opacity=i)
        iw(s.cambg2,opacity=i)
        teck(0.02,Call(s.fcam,i+a,a))
    def rloop(s):
        s.loop()
        s.fixps()
        s.hm('Replay',f'Version {Replay.VER} BETA',s.COL12,s.COL13)
    def killui(s):
        s.up = s.camon = False
        [_.delete() for _ in s.trash()]
        s.kids.clear()
        s.camkids.clear()
    def trash(s):
        return s.kids+s.camkids
    def kek(s):
        if getattr(s,'kekbusy',0): return
        s.kekbusy = True
        if getattr(s,'tbye',0) and getattr(s,'frbro',0):
            s.frbro = s.tbye = False
        s.okt = None
        s.nah = b = not s.nah
        otw(s.kekt,text=s.tex[b])
        if b:
            teck(0.2,lambda:obw(s.kekb,texture=gt('empty')))
            s.fkek(0.4,-0.05)
            s.killui()
        else:
            obw(s.kekb,texture=gt('white'))
            s.fkek(0,0.05)
            s.mkui()
            s.pro()
        teck(0.21,Call(setattr,s,'kekbusy',0))
    def fkek(s,i=0,a=0.1):
        if i > 0.4 or i < 0: return
        if not s.bg.exists(): return
        iw(s.bg,opacity=i)
        teck(0.02,Call(s.fkek,i+a,a))
    def hm(s,t1,t2,c1,c2):
        if getattr(s,'tbye',0) and getattr(s,'frbro',0):
            s.frbro = s.tbye = False
        s.okt = None
        iw(s.ok,color=c1)
        otw(s.ok2,text=t1,color=c2)
        otw(s.ok3,text=t2,color=c2)
        s.fok()
        s.okt = tock(1.5,s.unhm)
    def unhm(s):
        s.fok(0.7,-0.1)
        [otw(_,text='') for _ in [s.ok2,s.ok3] if _.exists()]
    def fok(s,i=0,a=0.1):
        if i > 0.7 or i < 0: return
        if not s.ok.exists(): return
        iw(s.ok,opacity=i)
        teck(0.02,Call(s.fok,i+a,a))
    def toggle(s,dry=False,shut=False):
        if not dry: s.ps = not s.ps
        t = cs(getattr(sc,['PAUSE','PLAY'][s.ps]+'_BUTTON'))
        otw(s.tt,text=t)
        if not dry:
            if not shut: s.hm(['Resume','Pause'][s.ps],basename(s.path)+f' of {getsize(s.path)} bytes',s.COL6,s.COL7)
            if s.ps:
                s.stop()
                PAUSE()
            else:
                s.play()
                RESUME()
    def fixps(s):
        if not s.ps: return
        s.toggle(shut=True)
        teck(0.02,Call(s.toggle,shut=True))
    def clock(s):
        t = time()
        r = t - s.rt
        s.rt = t
        s.rn += r * s.sp
    def boost(s,i):
        n = GET()+i
        SET(n)
        s.sp = 2**n
        h = 'Snail Mode' if s.sp == 0.0625 else 'Slow Motion' if s.sp<1 else 'Quake Pro' if s.sp==16 else 'Fast Motion' if s.sp>1 else 'Normal Speed'
        s.hm(h,f'Current exponent: x{s.sp}',s.COL2,s.COL3)
    def play(s):
        s.rt = time()
        s.clock()
        s.ptplay()
        s.clt = tock(s.TICK,s.clock,repeat=True)
    def stop(s):
        s.clt = None
        s.ptkill()
    def ptkill(s):
        s.pt = None
    def ptplay(s):
        s.pt = tock(s.TICK,s.pro,repeat=True)
    def seek(s,i):
        h = ['Forward by','Rewind by'][i==-1]
        i = i * s.sp
        i = (s.ds/20)*i
        t = (s.rn-s.st)+i
        if (t >= s.ds) or (t <= 0):
            s.loop()
        else:
            s.st = s.rn-t
            s.replay()
            SEEK(t)
        s.rt = time()
        s.fixps()
        i = abs(round(i,2))
        s.hm('Seek',h+f" {i} second{['s',''][i==1]}",s.COL4,s.COL5)
    def jump(s,p):
        t = s.ds * p
        s.st = s.rn-t
        s.replay()
        SEEK(t)
        s.rt = time()
        s.fixps()
    def bye(s):
        if getattr(s,'frbro',0): s._bye(); return
        s.hm('Exit','Press again to confirm',s.COL0,s.COL1)
        s.frbro = True
        s.tbye = tock(1.5,Call(setattr,s,'frbro',False))
    def _bye(s):
        fade(0,time=0.75,endcall=Call(fade,1,time=0.75))
        gs('deek').play()
        BYE()
        s.stop()
        s.fockill()
        s.tbye = None
        SCM(False)
    def pro(s):
        t = s.rn-s.st
        if s.rn-s.st >= s.ds: s.loop()
        x,y = s.nbp
        p = (t/s.ds)*s.px
        try:
            iw(s.nb,position=(x+p,y))
            otw(s.ct,text=FOR(t))
        except ReferenceError: pass
    def replay(s):
        SEEK(-10**10)
    def loop(s):
        s.st = s.rn = 0
        s.replay()
    bw = lambda s,label='',p=None,oac=None,pos=None,texture='white',**k: obw(
        parent=p,
        on_activate_call=oac,
        position=pos,
        label=label,
        texture=gt(texture),
        enable_sound=False,
        **k
    )

# Tools
BYE = lambda: app.classic.return_to_main_menu_session_gracefully(reset_ui=False)
BTW = lambda t: (gs('block').play() or 1) and push(t,color=(1,1,0))
GOS = lambda: gsw('overlay_stack')
FOR = lambda t: strftime('%H:%M:%S',gmtime(t))
SCL = lambda a,b,c=None: ((s:=app.ui_v1.uiscale), a if s is UIS.SMALL else b if s is UIS.MEDIUM else (c or b))[1]
RND = lambda t: type(t)([round(_,1) for _ in t])

# pybrp
Z = lambda _:[0]*_
G_FREQS = lambda:[
    101342,9667,3497,1072,0,3793,*Z(2),2815,5235,*Z(3),3570,*Z(3),
    1383,*Z(3),2970,*Z(2),2857,*Z(8),1199,*Z(30),
    1494,1974,*Z(12),1351,*Z(122),1475,*Z(65)
]
CMD_NAMES=lambda:{0:'BaseTimeStep',1:'StepSceneGraph',2:'AddSceneGraph',3:'RemoveSceneGraph',4:'AddNode',5:'NodeOnCreate',6:'SetForegroundScene',7:'RemoveNode',8:'AddMaterial',9:'RemoveMaterial',10:'AddMaterialComponent',11:'AddTexture',12:'RemoveTexture',13:'AddMesh',14:'RemoveMesh',15:'AddSound',16:'RemoveSound',17:'AddCollisionMesh',18:'RemoveCollisionMesh',19:'ConnectNodeAttribute',20:'NodeMessage',21:'SetNodeAttrFloat',22:'SetNodeAttrInt32',23:'SetNodeAttrBool',24:'SetNodeAttrFloats',25:'SetNodeAttrInt32s',26:'SetNodeAttrString',27:'SetNodeAttrNode',28:'SetNodeAttrNodeNull',29:'SetNodeAttrNodes',30:'SetNodeAttrPlayer',31:'SetNodeAttrPlayerNull',32:'SetNodeAttrMaterials',33:'SetNodeAttrTexture',34:'SetNodeAttrTextureNull',35:'SetNodeAttrTextures',36:'SetNodeAttrSound',37:'SetNodeAttrSoundNull',38:'SetNodeAttrSounds',39:'SetNodeAttrMesh',40:'SetNodeAttrMeshNull',41:'SetNodeAttrMeshes',42:'SetNodeAttrCollisionMesh',43:'SetNodeAttrCollisionMeshNull',44:'SetNodeAttrCollisionMeshes',45:'PlaySoundAtPosition',46:'PlaySound',47:'EmitBGDynamics',48:'EndOfFile',49:'DynamicsCorrection',50:'ScreenMessageBottom',51:'ScreenMessageTop',52:'AddData',53:'RemoveData',54:'CameraShake'}
class _H:
    class _N:
        def __init__(self):
            self.l,self.r,self.p,self.f=-1,-1,0,0
    def __init__(self):
        gf,self.nodes=G_FREQS(),[self._N()for _ in range(511)]
        for i in range(256):self.nodes[i].f=gf[i]
        nc=256
        while nc<511:
            s1,s2=-1,-1
            i=0
            while self.nodes[i].p!=0:i+=1
            s1=i;i+=1
            while self.nodes[i].p!=0:i+=1
            s2=i;i+=1
            while i<nc:
                if self.nodes[i].p==0:
                    if self.nodes[s1].f>self.nodes[s2].f:
                        if self.nodes[i].f<self.nodes[s1].f:s1=i
                    elif self.nodes[i].f<self.nodes[s2].f:s2=i
                i+=1
            self.nodes[nc].f=self.nodes[s1].f+self.nodes[s2].f
            self.nodes[s1].p=self.nodes[s2].p=nc-255
            self.nodes[nc].r,self.nodes[nc].l=s1,s2
            nc+=1
    def decompress(self,src):
        if not src:return b''
        rem,comp=src[0]&15,src[0]>>7
        if not comp:return src
        out,ptr,l=bytearray(),src[1:],len(src)
        bl=((l-1)*8)-rem;bit=0
        while bit<bl:
            m_bit=(ptr[bit>>3]>>(bit&7))&1;bit+=1
            if m_bit:
                n=510
                while n>=256:
                    if bit>=bl:raise ValueError("Incomplete Huffman code")
                    p_bit=(ptr[bit>>3]>>(bit&7))&1;bit+=1
                    n=self.nodes[n].l if p_bit==0 else self.nodes[n].r
                out.append(n)
            else:
                if bit+8>bl:break
                bi,b_in_b=bit>>3,bit&7
                val=ptr[bi]if b_in_b==0 else(ptr[bi]>>b_in_b)|(ptr[bi+1]<<(8-b_in_b))
                out.append(val&255);bit+=8
        return bytes(out)
def GMS(_h, brp_path, par):
    total_ms = 0
    with open(brp_path, 'rb') as f:
        f.seek(0,2)
        par[1] = f.tell()
        f.seek(6)
        while True:
            if par: par[0] = f.tell()
            b_data = f.read(1)
            if not b_data:
                break
            b1, comp_len = b_data[0], 0
            if b1 < 254:
                comp_len = b1
            elif b1 == 254:
                comp_len = int.from_bytes(f.read(2), 'little')
            else: # 255
                comp_len = int.from_bytes(f.read(4), 'little')
            if comp_len == 0:
                continue
            raw_msg = _h.decompress(f.read(comp_len))
            if not raw_msg or raw_msg[0] != 1:
                continue
            sub_off = 1
            while sub_off < len(raw_msg):
                try:
                    sub_size = int.from_bytes(raw_msg[sub_off:sub_off+2], 'little')
                except IndexError:
                    break
                except ValueError:
                    break
                sub_data = raw_msg[sub_off+2:sub_off+2+sub_size]
                if sub_data and sub_data[0] == 0:
                    total_ms += sub_data[1]
                sub_off += 2 + sub_size
    if par: par[0] = par[1]
    return total_ms

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    def __init__(s):
        from bauiv1lib.ingamemenu import InGameMenuWindow as m
        a = '_refresh_in_game'; o = getattr(m,a)
        setattr(m,a,lambda v,*a,**k:(s.mk(v),o(v,*a,**k))[1])
        from bauiv1lib.watch import WatchWindow as n
        b = '__init__'; p = getattr(n,b)
        setattr(n,b,lambda v,*a,**k:(p(v,*a,**k),s.mk(v,1))[0])
    def mk(s,v,i=0):
        if i:
            x = v._width/2+SCL(v._scroll_width*-0.5+93,0)+100
            y = v.yoffs-SCL(63,10)-25
        s.b = Replay.bw(
            Replay,
            p=v._root_widget,
            label='Replay',
            pos=(x,y) if i else (-70,0),
            icon=gt('replayIcon'),
            iconscale=1.6 if i else 0.8,
            size=(140,50) if i else (90,35),
            oac=lambda:Replay(source=s.b)
        )

