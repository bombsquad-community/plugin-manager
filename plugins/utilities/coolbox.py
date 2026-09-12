# Copyright 2026 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Coolbox v1.0.0 - Own the scene.

Experimental.
Coolbox is an advanced menu that can do almost everything!
Access the menu from pause menu.
This is a clean refactored version of Sandbox. Written from scratch.
The code itself acts like a closed environment.
Coolbox uses a lot of scene features for the sake of appearance.
"""

import bauiv1lib.ingamemenu as bui_igm
import babase as ba
import _babase as _ba
import bauiv1 as bui
import bascenev1 as bs
import random
import bascenev1lib.actor.powerupbox as bs_powerupbox
import bascenev1lib.actor.playerspaz as bs_playerspaz
import bascenev1lib.gameutils as bs_gameutils
import bascenev1lib.actor.bomb as bs_bomb
import bascenev1lib.actor.spazbot as bs_spazbot
import bascenev1lib.actor.spaz as bs_spaz
import traceback
import zlib
import inspect
import os.path
import math
import weakref
import time
import json
import os
import uuid

plugman = dict(
    plugin_name="coolbox",
    description=(
        "Coolbox is an advanced menu that can do almost everything! "
        "Access the menu from pause menu. "
        "This is a clean refactored version of Sandbox. Written from scratch."
    ),
    external_url="https://BroBordd.github.io/byBordd",
    authors=[
        {
            "name": "BrotherBoard",
            "email": "brobordd@gmail.com",
            "discord": "BrotherBoard"
        },
    ],
    version='1.0.0',
)

class Coolbox:
    @classmethod
    def state(s,t=0):
        bui.apptimer(0 if t else 0.13, bs.CallPartial(bui.buttonwidget, s.in_source, icon=bui.gettexture(f"chest{'Open' if t else ''}Icon")))
    def __init__(s, fresh=True, in_source=None, fb=None, fake=False, extra=None):
        # safe
        if not bs.get_foreground_host_activity(): btw(random.choice(NAH())); return
        if STATE(): btw('Coolbox is already running!'); return
        if in_source:
            s.__class__.in_source = in_source
            s.state(1)
        z = icw(
            title='Coolbox',
            shadow=True,
            show_back=False,
            show_nuke=not fake,
            show_tog=not fake,
            source_cls=s.__class__,
            nuke_anim='out_scale' if in_source else 'out_right',
            transition='in_scale' if fresh and in_source else 'in_right',
            in_source=in_source,
            out_source=in_source,
            note='CoolBox is a clean version of SandBox, written from scratch.',
            note_scale=0.5
        )
        # Buttons
        x,y = z.size
        w = z.widget
        mem = globals()
        kids = []
        for k in range(5):
            for j in range(3):
                l,i = s.get(j,k)
                b = bw(
                    p=w,
                    label=l,
                    pos=(47+171.5*j,300-64*k),
                    size=(173,64),
                    icon=bui.gettexture(i),
                )
                bcls = mem[l]
                args = (w,b,i,in_source,s.__class__,extra)
                if not fake: bw(b,oac=bs.CallPartial(bcls, *args))
                if fb == bcls.__name__: bui.apptimer(0.5, bs.CallPartial(bcls, *args))
                kids.append(b)
    """Icons and names"""
    def get(s,j,k):
        return (
            ('Spawn','cuteSpaz'),
            ('Modify','advancedIcon'),
            ('Control','controllerIcon'),
            ('Effect','graphicsIcon'),
            ('Deploy','star'),
            ('Listen','audioIcon'),
            ('Build','cursor'),
            ('Tweak','menuIcon'),
            ('Tune','settingsIcon'),
            ('Gather','achievementTeamPlayer'),
            ('Load','inventoryIcon'),
            ('Quick','nextLevelIcon'),
            ('Scene','nub'),
            ('Camera','tv'),
            ('About','heart')
        )[k*3+j]

class Bot(bs_spazbot.SpazBot):
    """A Bombsquad Bot"""
    def __init__(
        s,
        char=None,
        ignore=False,
        name='Bot',
        name_color=(1,1,1),
        mesh=[],
        ctex=None,
        ctex2=None
    ) -> None:
        mem = COLS()
        bs_spaz.Spaz.__init__(
            s,
            color=var(mem[0]),
            highlight=var(mem[1]),
            character=char or var('char'),
            start_invincible=False,
            can_accept_powerups=True
        )
        n = s.node
        n.name, n.name_color = name, name_color
        n.color_texture, n.color_mask_texture = bs.gettexture(ctex), bs.gettexture(ctex2)
        a = DIR('mesh')
        for i,m in enumerate(mesh):
            if not m: continue
            setattr(n,a[i],bs.getmesh(m))
        s.act = []
        s.uid = None
        s.group_id = var('lastid')
        s.held_count = 0
        s.last_player_attacked_by = None
        s.last_player_held_by = None
        ignore if ignore else bs.timer(0.1,s.load)
    def move(s,x=32767,y=32767):
        s.on_move_left_right(x)
        s.on_move_up_down(y)
    def stop(s):
        s.move(0,0)
    def move_to(s,t,min=0.7,time=10,chain=None):
        nah = 0
        def f(b=False):
            nonlocal nah
            if nah: s.stop(); return
            try: p = s.node.position
            except: return
            if t == p: return
            dx = t[0]-p[0]
            dz = p[2]-t[2]
            if b:
                m = (dx**2+dz**2)**0.5
                try: s.move(dx/m,dz/m)
                except ZeroDivisionError: pass
            if math.dist((p[0],p[2]),(t[0],t[2])) < min:
                nah = 1
                s.stop()
                if (chain is not None): s.wait(0.2,chain)
                return
            bs.timer(0.01,f)
        def g():
            nonlocal nah
            if (not nah) and (chain is not None): s.wait(0.2,chain)
            nah = 1
        f(True)
        bs.timer(time,g)
    def follow(s,n,min=0.7,time=10,chain=None):
        nah = 0
        def f():
            nonlocal nah
            if nah or not n.exists(): s.stop(); return
            try:
                p = s.node.position
                t = n.position
            except: return
            if t == p: return
            dx = t[0]-p[0]
            dz = p[2]-t[2]
            m = (dx**2+dz**2)**0.5
            if (min is not None) and math.dist((p[0],p[2]),(t[0],t[2])) < min:
                s.stop()
                nah = 1
                if (chain is not None): s.wait(0.2,chain)
                return
            else:
                try: s.move(dx/m,dz/m)
                except ZeroDivisionError: pass
            bs.timer(0.01, f)
        def g():
            nonlocal nah
            if (not nah) and (chain is not None): s.wait(0.2,chain)
            nah = 1
        f() if n is not None else n
        if time is not None: bs.timer(time,g)
    def wait(s,i,chain=None):
        if chain is not None: bs.timer(i,lambda: s.load(chain+1))
    def key(s,i,chain=None):
        [getattr(s,f"on_{['jump','bomb','pickup','punch'][i]}_{['press','release'][j]}")() for j in [0,1]]
        if chain is not None: s.wait(0.2,chain)
    def say(s,t,u,chain=None):
        if not s.node.exists(): return
        bs.timer(
            [0,0.1][not chain],
            lambda: Bubble(
                node=s.node,
                text=t,
                time=int(u),
                color=s.node.color,
            )
        )
        if chain is not None: s.wait(0.2,chain)
    def load(s,i=None):
        if i is None: s.act = var('act').copy(); i = 0
        try: a = s.act[i]
        except: return
        t = a[0]
        if t == 0: s.say(*a[1:],i)
        elif t == 1: s.move_to(*a[1:],i)
        elif t == 2: s.wait(a[1],i)
        elif t == 3:
            j = a[1]-1
            k = a[2]-1
            if k < 0: s.load(i+1); return
            s.act[i] = [t,j+1,k-1]
            s.load(j)
        elif t == 4: s.key(a[1],i)
        elif t == 5:
            who = a[1]
            if who == 'me': n = getme(1).node
            else:
                n = None
                for j in bs.getnodes():
                    if str(j) == who: n = j; break
            s.follow(n,*a[2:],i)

class Bubble:
    __doc__ = ("""
        Highly customizable floating bubble

        Arguments:
        - node: bascenev1.Node to follow (*required)
        - text: the text to show in bubble
        - color: the color of bubble
        - time: how long to show bubble (in seconds)
        - mode: how should the text animate

        Supported modes:
        - 0: random (default)
        - 1: text pops up with bubble
        - 2: text slides letter by letter
        - 3: text fades in letter by letter
        - 4: text comes up from bubble
        - 5: text waves in letter by letter

        Besides copy pasting, inline usage varies:
        >>> from bubble import Bubble
        >>> bub = Bubble(
        ...     text='Kill me please',
        ...     color=(0.2,0.8,0.9),
        ...     node=bot.node,
        ...     time=6
        ... )
        >>>
    """)
    __mem__ = {}
    def __init__(
        s,
        node: 'bascenev1.Node',
        text: str = 'Hello!',
        color: tuple = (1,1,1),
        time: float | int = 4,
        mode: int = 0,
        res: list = [('█'),('▼')]
    ) -> None:
        if not 0 <= mode <= 5 : raise ValueError(f'mode can be an integer from 0 to 5, not {mode}')
        if not mode: mode = random.choice([1,2,3,4,5])
        s.ans,s.kids,s.mats,s.time = [],[],[],time
        s.node,s.dead,s.text = node,False,text
        s.color,s.mode,s.res = color,mode,res
        # destroy existing bubbles if possible
        s.mem = lambda: s.__class__.__mem__
        m = s.mem()
        o = m.get(node,0)
        if not getattr(o,'dead',1): bs.timer(0.2,bs.CallPartial(o.delete,force=True))
        s.show()
        m[node] = s
    def show(s):
        q,l,r = s.mats,s.kids,s.ans
        # offset
        m = bs.newnode(
            'math',
            owner=s.node,
            attrs={
                'input1': (0,1.65,0),
                'operation': 'add'
            }
        )
        q.append(m)
        # the bubble
        c = list(s.color)
        w = GSW(s.res[0])
        b = bs.newnode(
            'text',
            owner=m,
            attrs={
                'text': f'{math.ceil((GSW(s.text)+2*w)/w)*s.res[0]}\n{s.res[1]}',
                'in_world': True,
                'shadow': 1.0,
                'flatness': 1.0,
                'color': (c[0],c[1],c[2],0.2),
                'scale': 0.01,
                'h_align': 'center'
            }
        )
        l.append(b)
        # the text
        txt = []
        mat = []
        kek = -GSW(s.text)/185
        sf = 0
        for i in range(len(s.text)):
            j = s.text[i]
            x = GSW(j)/95.0
            p1 = bs.newnode(
                'text',
                owner=m,
                attrs={
                    'text': j,
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'color': s.color,
                    'scale': 0.01,
                    'h_align': 'left'
                }
            )
            txt.append(p1)
            ok = kek+sf
            p2 = bs.newnode(
                'math',
                owner=m,
                attrs={
                    'input1': (ok,1.65,0),
                    'operation': 'add'
                }
            )
            mat.append([p2,ok])
            s.node.connectattr('position',p2,'input2')
            p2.connectattr('output',p1,'position')
            sf += x
        l += txt
        q += [mat[i][0] for i in range(len(mat))]
        # connect
        s.node.connectattr('position',m,'input2')
        m.connectattr('output',b,'position')
        # hardcoded animators
        # conditionally used based on animation
        z = s.time
        # scale bubble in out
        a = bs.animate(
            b,
            'scale',
            {
                0:0,
                z*0.041: 0.014,
                z*0.154: 0.014,
                z*0.167: 0.010,
                z*0.98: 0.010,
                z:0
            },
        )
        r.append(a)
        # move bubble up down
        a = bs.animate_array(
            m,
            'input1',
            3,
            {
                0:(0,1.2,0),
                z*0.04:(0,1.65,0),
                z*0.98:(0,1.65,0),
                z:(0,1.2,0)
            }
        )
        r.append(a)
        # scale text in out
        r += [
            bs.animate(
                txt[i],
                'scale',
                {
                    0:0,
                    z*0.041: 0.015,
                    z*0.154: 0.015,
                    z*0.167: 0.010,
                    z*0.98: 0.010,
                    z:0
                },
            )
            for i in range(len(mat))
        ] if s.mode in [1,4] else []
        # move text up down
        r += [
            bs.animate_array(
                mat[i][0],
                'input1',
                3,
                {
                    0:(mat[i][1]/4,1.2,0),
                    z*0.04:(mat[i][1]*1.5,1.65,0),
                    z*0.154:(mat[i][1]*1.5,1.65,0),
                    z*0.167:(mat[i][1],1.65,0),
                    z*0.98:(mat[i][1],1.65,0),
                    z:(mat[i][1]/4,1.2,0)
                }
            )
            for i in range(len(mat))
        ] if s.mode in [1,4] else []
        # slide in overshoot letter by letter
        ok = (z*0.04*1.6)
        hm = [0.03,0.05][s.mode==2]
        r += [
            bs.animate_array(
                j[0],
                'input1',
                3,
                {
                    0.5+i*hm:(j[1],1.4,0),
                    0.5+i*hm+(ok*0.6):(j[1],1.9,0),
                    0.5+i*hm+ok:(j[1],1.65,0),
                    (z-(z*0.02)):(j[1],1.65,0),
                    z:(j[1],1.2,0)
                }
            )
            for i,j in enumerate(mat)
        ] if s.mode in [2,5] else []
        # fade in letter by letter
        r += [
            bs.animate(
                txt[i],
                'opacity',
                {
                    0.5+i*hm:0,
                    (0.5+i*hm+ok)*0.98:1,
                    z*0.9:1,
                    z:0
                }
            )
            for i in range(len(mat))
        ] if s.mode in [2,4,5] else []
        # scale slide up text
        r += [
            bs.animate(
                txt[i],
                'scale',
                {
                    0:0,
                    z*0.154: 0,
                    z*0.167: 0.010,
                    z*0.98: 0.010,
                    z:0
                },
            )
            for i in range(len(mat))
        ] if s.mode == 3 else []
        # autokill
        bs.timer(z,s.delete)
    def delete(s,force=False):
        if s.dead: return
        s.dead = True
        [i.delete() for i in s.ans if hasattr(i,'delete')]
        bs.timer(0.2,lambda:[i.delete() for i in s.kids+s.mats if hasattr(i,'delete')])
        if not force: return
        [bs.animate(
            i,
            'opacity',
            {
                0:i.opacity,
                0.2:0
            }
        ) for i in s.kids]

_rgb_cycle_combines = []

class icw:
    """Instant container maker"""
    INS = []
    @classmethod
    def on_resume(cls):
        bui.apptimer(0.01,lambda: [i.update() for i in cls.INS])
    def __del__(s):
        s.__class__.INS.delete(s)
    def snd(s,t):
        l = bui.getsound(t)
        l.play()
        bui.apptimer(random.uniform(0.14,0.18),l.stop)
        return l
    def __init__(
        s, title, shadow=False, icon=None, show_tog=False,
        back_anim='out_right', nuke_anim='out_scale',
        on_back=lambda: None, on_nuke=lambda: None,
        show_nuke=True, show_back=True, in_source=None,
        out_source=None, cls=None, source_cls=None,
        outside_action=None, note=None, note_scale=0.7,
        note_pos=(50,15), extra=None, auto_offset=True,
        *a, **k
    ) -> None:
        s.snd('powerup01') if in_source else 0
        s.__class__.INS.append(s)
        r = bui.get_virtual_screen_size()
        k.update({
            'parent':gos(),
            'transition':'in_scale' if in_source else 'in_right',
            'size':k.get('size',0) or (600,450),
            'on_outside_click_call':lambda:s.nuke(True) if outside_action == 'nuke' else s.back(True) if outside_action == 'back' else lambda:None,
            'scale':[1.5,1.1,0.8][UIS()],
            'scale_origin_stack_offset':gc(in_source) if in_source else (0,0),
            'position':(r[0]*0.8,r[1]*0.05)
        })
        s.size = k['size']
        s.ouis = bui.app.ui_v1.uiscale
        x,y = s.size
        s.widget = w = cw(*a,**k)
        s.ao = auto_offset
        s.cls = cls(w,x,y,in_source,source_cls,extra) if cls else None
        s.on_back = on_back
        s.on_nuke = on_nuke
        s.nuke_anim = nuke_anim
        s.back_anim = back_anim
        s.icon = icon
        s.in_source = in_source
        s.out_source = out_source
        s.source_cls = source_cls
        # Exit buttons
        c = var('bg')
        if show_back:
            b = sbw(
                p=w,
                button_type='backSmall',
                pos=([30,55][s.size[0]>400],y-70),
                oac=s.back,
                label=bui.charstr(bui.SpecialChar.BACK),
            )
            cw(w,cancel_button=b)
            s.back_button = b
        if show_nuke:
            b = bw(
                p=w,
                pos=(510,y-70),
                oac=s.nuke,
                size=(43,43),
                label=bui.charstr(bui.SpecialChar.CLOSE),
            )
            if not show_back: cw(w,cancel_button=b)
            s.nuke_button = b
        if show_tog:
            b = bw(
                p=w,
                size=(43,43),
                pos=(455,y-70),
                oac=s.toggle,
            )
            s.tog_button = b
            s.toggle(True)
        # Icon shadow title
        c = var('t')
        for i in range(2):
            if not i and not shadow: continue
            tw(
                p=w,
                text=title,
                scale=1.5,
                h_align='left' if icon else 'center',
                v_align='center',
                color=c if i else darken(c),
                pos=(x/2.2+i*5,y-65+i*2),
                maxwidth=x/1.8,
            )
        if icon:
            bui.imagewidget(
                parent=w,
                position=(215,y-75),
                size=(50,50),
                texture=bui.gettexture(icon)
            )
        if note:
            tw(
                p=w,
                pos=note_pos,
                color=(1,1,1,0.2),
                text='* '+note,
                scale=note_scale
            )
        s.update()
    """Update"""
    def update(s):
        if not s.widget.exists() or s.widget.transitioning_out: return
        r = bui.get_virtual_screen_size()
        i = UIS()
        j = UIS(1)
        if s.ouis != j:
            s.ouis = j
            [bui.apptimer(z,bs.CallPartial(bui.app.set_ui_scale,j)) for z in [0.01,0.1]]
        a,b = [(0.2,0.007),(0.3,-0.0034),(0.33,0.0026)][i]
        ef = s.in_source
        of = gc(ef) if ef and ef.exists() else None
        cw(
            s.widget,
            stack_offset=(
                (a*s.size[0]/600)*r[0],
                r[1]*(b*s.size[1]/450)
            ) if s.ao else of,
            scale=[1.5,1.1,0.8][i],
            scale_origin_stack_offset=of
        )
    """Class specific"""
    def prekill(s):
        s.snd('laser')
        s.cls.back() if s.cls and hasattr(s.cls,'back') else None
    """On back"""
    def back(s, by_button=False):
        if by_button:
            try: s.back_button.activate()
            except: pass
        else:
            s.prekill()
            s.on_back() if callable(s.on_back) else None
            cw(s.widget, transition=s.back_anim if s.in_source else 'out_right')
    """On nuke"""
    def nuke(s,by_button=False):
        if not hasm(): pause(0)
        if by_button:
            try: s.nuke_button.activate()
            except: pass
        else:
            if s.out_source: forbtn(s.widget,s.out_source,60)
            s.prekill()
            s.on_nuke()
            cw(s.widget, transition=s.nuke_anim if s.out_source else 'out_right')
            if s.source_cls and s.out_source:
                s.source_cls.state()
    """Toggle pause"""
    def toggle(s,dry=False):
        assert hasattr(s,'tog_button')
        i = [[1,0],[0,1]][dry][pause()]
        bw(s.tog_button, label=bui.charstr([bui.SpecialChar.PAUSE_BUTTON,bui.SpecialChar.PLAY_BUTTON][i]))
        if dry: return
        bui.getsound('deek').play()
        pause(i)

class itw:
    """Indent text widget"""
    def __init__(s,*a,**k) -> None:
        s.a = a
        s.k = k
        k.update({'h_align':'center',
                  'v_align':'center'})
        s.position = k.get('position',(0,0))
        s.text = k.get('text','')
        s.h = k.get('size',(0,30))[1]
        s.kids = []
        s.set_text(s.text)
    """Set text"""
    def set_text(s,text) -> None:
        s.text = text
        z = len(text)
        p = list(s.position)
        m = s.max = max(text.replace('\\n','') or [''],key=GSW)
        l = s.max_len = GSW(str(m))/1.2
        s.total = l*len(max(text.split('\\n') or [''],key=len))
        [k.delete() for k in s.kids]
        s.kids.clear()
        x = 0
        for i in range(z):
            p[0] += [l,0][i==0]
            if x: x = 0; continue
            j = text[i]
            k = text[i+1] if (i+1) < z else j
            if j == '\\' and k == 'n':
                p[0] = s.position[0]-l*2
                p[1] = p[1] - s.h
                x = 1
                continue
            s.k.update({'position':(p[0],p[1]),
                        'text':j,
                        'size':(l,s.h)})
            s.kids.append(tw(*s.a,**s.k))
    """Set color"""
    def set_color(s,color):
        [tw(t,color=color) for t in s.kids]

class ctw:
    """Conditional text widget"""
    def __init__(
        s,*a,allow=[],tint=True,hint='',
        bad_image=None,conf=None,type=None,
        on_conf=(lambda *a: None),flash=False,
        on_edit=(lambda *a: None),blank=False,
        **k
    ):
        k.update({
            'editable':True,
            'v_align':'center',
            'h_align':'center',
            'allow_clear_button':False,
            'color':k.get('color',(1,1,1)),
            'description':k.get('description',hint) or 'Enter',
            'glow_type':'uniform'
        })
        s.color = k['color']
        s.widget = t = tw(*a,**k)
        k.update({
            'editable': False,
            'text': hint,
            'color': (0.5,0.5,0.5),
            'maxwidth':k.get('size')[0]
        })
        s.widget2 = u = tw(*a,**k)
        s.type = type
        s.conf = conf if isinstance(conf,tuple) else (conf,conf)
        s.forgive = s.silent = s.bad = False
        s.on_edit = on_edit
        s.blank = blank
        s.on_conf = on_conf
        s.hint = hint
        s.tint = tint
        s.allow = allow
        s.flash = flash
        s.bad_image = bad_image
        s.old = s.get_text()
        s.spy()
    """Blink"""
    def blink(s, c=(0,1,0)):
        oc = s.color
        tw(s.widget, color=c)
        def f():
            try: tw(s.widget, color=oc)
            except: pass
        bui.apptimer(0.3,f)
    """Get current text"""
    def get_text(s):
        return tw(query=s.widget)
    """Set text gracefully"""
    def set_text(s,t,silent=False):
        if t is None: return
        if s.get_text() == t: return
        s.forgive = True
        tw(s.widget, text=t)
        tw(s.widget, color=s.color)
        if silent: s.silent = True
    """Spy on input"""
    def spy(s):
        if not s.widget.exists(): return
        v = s.get_text()
        t = s.widget
        u = s.widget2
        tw(u,color=(0.5,0.5,0.5,0 if v else 1))
        bool = s.allow if s.allow is True else not v.translate({ord(c): None for c in s.allow})
        if bool and s.type == 'encoding':
            try: CHECK(v)
            except: bool = False
        if v and not bool:
            if not s.bad:
                push(f'Invalid {s.hint}',color=(1,0,0))
                bui.getsound('error').play()
                s.bad = True
                if s.tint: tw(t,color=(1,0,0))
                if s.bad_image: bui.imagewidget(s.bad_image,opacity=1)
        elif s.bad:
            s.bad = False
            if s.tint: tw(t,color=(1,1,1))
            if s.bad_image: bui.imagewidget(s.bad_image,opacity=0)
        if bool and v != s.old:
            if s.flash and s.old: s.blink()
            s.old = v
            if s.forgive: s.forgive = False
            else: s.on_edit(s.hint, v)
            if s.conf[0]:
                var(s.conf[0],v if (v or s.blank) else var(s.conf[1]))
                s.on_conf()
                if s.type == 'encoding' and not s.silent:
                    gun()
                elif s.silent: s.silent = False
        bui.apptimer(0.1, s.spy)

class SoundManager:
    """Sound manager"""
    def __init__(s,source=None,on_back=None,cols=None,prf=''):
        w = icw(
            title='Sound',
            outside_action='back',
            size=(350,400),
            show_nuke=False,
            on_back=on_back,
            in_source=source,
            back_anim='out_scale' if source else 'out_right'
        ).widget
        s.kids = []
        s.prf = prf
        s.D = D()
        s.cols = cols or COLS
        mem = DIR('sounds')
        for i in range(6):
            y = 270-50*i
            j = mem[i]
            b = bw(
                p=w,
                label=j.split('_')[0],
                size=(200,45),
                pos=(50,y)
            )
            bw(b,oac=bs.CallPartial(SoundPipe,pipe=s.fresh,source=b,action=i,prf=prf))
            b = pbw(
                p=w,
                pos=(260,y+7),
                size=(25.5,25.5),
                tex=s.cols()
            )
            s.kids.append(b)
        s.update()
        sbw(
            p=w,
            icon=bui.gettexture('backIcon'),
            pos=(275,330),
            color=darken(var('bg')),
            oac=s.reset
        )
    """Update"""
    def update(s):
        for o in range(len(DIR('sounds'))):
            v = var(f'{s.prf}sound{o}') or [0,0]
            t = v[1]
            i = v[0]
            if t == 1:
                ah = AUDIO()
                t = ah[i]
                bw(s.kids[o],texture=bui.gettexture('audioIcon'),oac=bs.CallPartial(bs.broadcastmessage,t),color=(1,1,1),tint_texture=bui.gettexture('black'))
            else:
                char = list(s.D.values())[i]
                bw(s.kids[o],texture=bui.gettexture(char.icon_texture),tint_texture=bui.gettexture(char.icon_mask_texture),oac=bs.CallPartial(bs.broadcastmessage,list(s.D)[i],color=var(s.cols()[2])),color=(1,1,1))
    """Reset"""
    def reset(s):
        c = var(f'{s.prf}char')
        fixsounds(c,prf=s.prf)
        bui.getsound('block').play()
        push('Restored default sounds!',color=(0.5,0.5,1))
        s.update()
    """Fresh"""
    def fresh(s,i,j):
        o, t = j
        var(f'{s.prf}sound{o}',[i,t])
        s.update()

class SoundPipe:
    """Sound pipe"""
    def __init__(s,pipe=lambda:None,source=None,action=None,prf=''):
        s.pipe = pipe
        s.z = icw(
            title=DIR('sounds')[action],
            show_nuke=False,
            in_source=source,
            outside_action='back',
            size=(400,200),
            back_anim='out_scale'
        )
        w = s.z.widget
        t = var(f'{prf}sound{action}') or [0,0]
        t = AUDIO()[t[0]] if t[1] else NAME()[t[0]]
        s.t = tw(
            p=w,
            pos=(175,85),
            h_align='center',
            text=t
        )
        b = bw(
            p=w,
            pos=(50,25),
            size=(150,50),
            label='Characters'
        )
        bw(b,oac=bs.CallPartial(CharPicker,pipe=s.pick,source=b,what='Select a sound',extra=[action,0],prf=None))
        b = bw(
            p=w,
            pos=(200,25),
            size=(150,50),
            label='All Sounds'
        )
        bw(b,oac=bs.CallPartial(SoundPicker,source=b,pipe=s.pick,extra=[action,1]))
    """Redirect all"""
    def pick(s,i,j):
        s.z.back()
        s.pipe(i,j)

class SoundPicker:
    """Sound picker"""
    def __init__(s,source=None,pipe=lambda a:None,what='Select a sound',extra=None):
        s.pipe = pipe
        s.extra = extra
        size = (600,500)
        al = s.al = AUDIO()
        s.z = z = icw(
            title=what,
            in_source=source,
            size=size,
            show_nuke=False,
            on_back=s.stop,
            back_anim='out_scale'
        )
        w = z.widget
        v = len(al)
        ss = 30 * v
        sv = bui.scrollwidget(
            parent=w,
            size=(210,360),
            position=(60,50),
            color=var('bg')
        )
        cv = cw(
            parent=sv,
            background=False,
            size=(280,ss)
        )
        s.texts = []
        # List sounds
        s.n = lambda: var('sp') or 0
        j = {'parent':cv,'size':(280,30)}
        for i in range(v):
            p = (10,(ss-30)-i*30)
            t = tw(
                pos=p,
                maxwidth=210,
                text=al[i],
                v_align='center',
                **j
            )
            bw(
                pos=p,
                oac=bs.CallPartial(s.preview,i,extra),
                texture=bui.gettexture('empty'),
                **j
            )
            s.texts.append(t)
        s.t = tw(
            p=w,
            pos=(300,370),
            maxwidth=290,
            text=al[s.n()]
        )
        s.up = lambda: cw(cv,visible_child=s.texts[s.n()])
        bw(
            p=w,
            label='Pick',
            size=(100,50),
            pos=(460,50),
            oac=lambda: s.pick(s.n(),extra)
        )
        for i in range(4):
            j = ['ouyaOButton','ouyaAButton','upButton','downButton'][i]
            k = [s.play,s.stop,s.prev,s.next][i]
            sbw(
                p=w,
                icon=bui.gettexture(j),
                pos=(300+50*i,300),
                repeat=i>1,
                oac=k
            )
        c = chk(
            parent=w,
            on_value_change_call=lambda auto: var('spa',auto),
            position=(300,50),
            size=(100,50),
            value=var('spa') or False,
            text='Autoplay'
        )
        chk(c,color=darken(var('bg')),textcolor=(1,1,1))
        s.update(True)
    """Prev"""
    def prev(s):
        n = s.n() - 1
        if n < 0: n = len(s.al) - 1
        var('sp',n)
        s.update()
    """Next"""
    def next(s):
        n = s.n() + 1
        if n >= len(s.al): n = 0
        var('sp',n)
        s.update()
    """Play"""
    def play(s):
        s.stop()
        s.v = bui.getsound(s.al[s.n()])
        s.v.play()
    """Stop"""
    def stop(s):
        try: s.v.stop()
        except: pass
    """Update"""
    def update(s,first=False):
        for i in range(len(s.texts)):
            tw(s.texts[i],color=(0,1,0) if s.n() == i else (1,1,1))
        s.up()
        if var('spa') and not first: s.play()
    """Preview"""
    def preview(s,n,e):
        s.stop()
        t = s.al[n]
        var('sp',n)
        tw(s.t, text=t)
        s.update()
    """Redirect"""
    def pick(s,i,j):
        s.stop()
        gun()
        s.pipe(i,j)
        s.z.back()

class MeshManager:
    """Mesh manager"""
    def __init__(s,source=None,on_back=None,prf='',cols=None):
        w = icw(
            title='Mesh',
            size=(400,530),
            show_nuke=False,
            in_source=source,
            outside_action='back',
            on_back=on_back,
            back_anim='out_scale' if source else 'out_right',
            note_scale=0.55,
            note_pos=(25,15),
            note='Some characters use kronk parts, it\'s not a bug.'
        ).widget
        s.kids = []
        s.mem = MESH()
        s.on_back = on_back
        s.cols = cols or COLS
        mem = DIR('mesh')
        s.prf = prf
        for i in range(len(mem)):
            px = [55,55,110,111,111,111,110,55,111][i]
            py = [245,190,350,90,189,45,237,300,140][i]
            sx = [50,50,100,100,100,100,100,50,100][i]
            sy = [50,50,100,45,50,40,120,50,45][i]
            l = mem[i][:-5]
            b = bw(
                p=w,
                pos=(100+px,py),
                size=(sx,sy),
                text_scale=[1,1.5][sx<51],
                label=l.split('_')[0]
            )
            bw(b,oac=bs.CallPartial(MeshPipe,pipe=s.fresh,source=b,part=i,title=l,prf=prf))
            tx = [105,105,325,325,325,325,325,105,325][i]
            ty = [253,199,385,97,199,49,282,307,147][i]
            t = pbw(
                p=w,
                pos=(tx,ty),
                size=(25.5,25.5),
                tex=s.cols()
            )
            s.kids.append(t)
        sbw(
            p=w,
            icon=bui.gettexture('backIcon'),
            pos=(320,461),
            color=darken(var('bg')),
            oac=s.reset
        )
        s.img = []
        for i in range(2):
            b = bw(
                p=w,
                pos=(50,115-73*i),
                size=(160,70)
            )
            j = ['Texture','Mask'][i]
            bw(b,oac=bs.CallPartial(TexPipe,source=b,pipe=s.update,prf=prf,mask=i,what=j))
            tw(
                p=w,
                pos=(120,135-73*i),
                h_align='center',
                text=j
            )
            s.img.append(bui.imagewidget(
                parent=w,
                position=(68,135-73*i),
                draw_controller=b,
                size=(30,30)
            ))
        b = bw(
            p=w,
            pos=(50,350),
            label='Select All',
            text_scale=1.3,
            size=(160,100)
        )
        bw(b,oac=lambda: CharPicker(pipe=s.all,source=b,note='To avoid confusion, character will be fully changed.',prf=None))
        s.update()
    """Set all"""
    def all(s,i,e=None):
        na = NAME()
        n = na[i]
        s.reset(n)
        if var(f'{s.prf}tchar') in na: var(f'{s.prf}tchar',n)
        var(f'{s.prf}char',n)
        push('Character changed!',color=(1,1,0))
        s.on_back() if callable(s.on_back) else None
    """Reset"""
    def reset(s,c=None):
        if not c:
            c = var(f'{s.prf}char')
            bui.getsound('block').play()
            push('Restored default mesh!',color=(0.5,0.5,1))
        fixmesh(c,prf=s.prf)
        s.update()
    """Update previews"""
    def update(s):
        for i in range(len(DIR('mesh'))):
            g = var(f'{s.prf}mesh{i}')
            bw(s.kids[i],texture=bui.gettexture('menuIcon'),color=(1,1,1),oac=bs.CallPartial(bs.broadcastmessage,g))
        bui.imagewidget(s.img[0],texture=bui.gettexture(var(f'{s.prf}ctex') or get_ctex(var('char'))))
        bui.imagewidget(s.img[1],texture=bui.gettexture(var(f'{s.prf}ctex2') or get_ctex2(var('char'))))
    """Fresh"""
    def fresh(s,j,n):
        var(f'{s.prf}mesh{j}',n)
        s.update()

class MeshPicker:
    """Mesh picker"""
    def __init__(s,source=None,pipe=lambda a:None,what='Select a mesh',mem=None,extra=None):
        s.pipe = pipe
        size = (420,500)
        al = s.al = mem or MESH()
        s.z = z = icw(
            title=what,
            in_source=source,
            size=size,
            show_nuke=False,
            back_anim='out_scale',
            outside_action='back'
        )
        w = z.widget
        v = len(al)
        ss = 30 * v
        sv = bui.scrollwidget(
            parent=w,
            size=(310,360),
            position=(60,50),
            color=var('bg')
        )
        cv = cw(
            parent=sv,
            background=False,
            size=(380,ss)
        )
        s.texts = []
        # List meshes
        s.n = lambda: var('mp') or 0
        for i in range(v):
            p = (10,(ss-30)-i*30)
            j = al[i]
            t = tw(
                pos=p,
                maxwidth=290,
                v_align='center',
                text=j,
                p=cv,
                size=(280,30),
                click_activate=True,
                selectable=True,
                on_activate_call=bs.CallPartial(s.fresh,i,j)
            )
            s.texts.append(t)
        s.up = lambda: cw(cv,visible_child=s.texts[s.n()])
        bw(
            p=w,
            label='Pick',
            size=(100,50),
            pos=(270,0),
            oac=bs.CallPartial(s.pick,extra)
        )
        s.fresh()
    """Refresh"""
    def fresh(s,i=None,j=None):
        if i is not None:
            var('mp',i)
            s.m = j
            [tw(t,color=(1,1,1)) for t in s.texts]
        else: i = s.n()
        tw(s.texts[i],color=(0,1,0))
        s.up()
    """Redirect"""
    def pick(s,e):
        n = s.n()
        try:
            with bs.get_foreground_host_activity().context: bs.getmesh(s.m)
        except: btw("Can't use this mesh!"); return
        gun()
        s.pipe(n,e)
        s.z.back()

class MeshPipe:
    """Mesh pipe"""
    def __init__(s,pipe=lambda:None,source=None,part=None,prf='',title=None):
        s.pipe = pipe
        s.part = part
        s.mem = MESH()
        s.title = title
        s.z = icw(
            title=title,
            show_nuke=False,
            in_source=source,
            outside_action='back',
            size=(400,200),
            back_anim='out_scale'
        )
        w = s.z.widget
        t = var(f'{prf}mesh{part}')
        s.t = tw(
            p=w,
            pos=(175,85),
            h_align='center',
            text=t
        )
        b = bw(
            p=w,
            pos=(50,25),
            size=(150,50),
            label='Characters'
        )
        bw(b,oac=bs.CallPartial(CharPicker,pipe=s.pick,source=b,what=f'Get {title} from',extra=0,prf=None))
        b = bw(
            p=w,
            pos=(200,25),
            size=(150,50),
            label='All Meshes'
        )
        bw(b,oac=bs.CallPartial(MeshPicker,source=b,pipe=s.pick,extra=1,mem=s.mem,what=f'Pick a mesh'))
    """Redirect all"""
    def pick(s,i,j):
        s.z.back()
        m = s.mem[i] if j else getattr(SPAZ()[i],s.title+'_mesh')
        s.pipe(s.part,m)

class TexPipe:
    """Texture pipe"""
    def __init__(s,pipe=lambda:None,source=None,prf='',mask=False,what='Texture'):
        s.pipe = pipe
        s.mask = mask
        s.z = icw(
            title=what,
            show_nuke=False,
            in_source=source,
            outside_action='back',
            size=(400,200),
            back_anim='out_scale'
        )
        w = s.z.widget
        s.prf = prf
        s.vs = f"{s.prf}ctex{['','2'][s.mask]}"
        s.vf = [get_ctex,get_ctex2][mask]
        v = var(s.vs) or s.vf(var('char'))
        s.t = tw(
            p=w,
            pos=(175,85),
            h_align='center',
            text=v
        )
        b = bw(
            p=w,
            pos=(50,25),
            size=(150,50),
            label='Characters'
        )
        bw(b,oac=bs.CallPartial(CharPicker,pipe=bs.CallPartial(s.pick,0),source=b,what='Get texture from',prf=None))
        b = bw(
            p=w,
            pos=(200,25),
            size=(150,50),
            label='All Textures'
        )
        bw(b,oac=bs.CallPartial(TexPicker,source=b,pipe=bs.CallPartial(s.pick,1)))
    """On pick"""
    def pick(s,n,p,e=None):
        s.z.back()
        var(s.vs,ALL()[p] if n else s.vf(NAME()[p]))
        s.pipe()

class TexPicker:
    """Texture picker"""
    def __init__(s,source=None,pipe=lambda a:None,what='Select a texture'):
        s.pipe = pipe
        size = (600,500)
        al = s.al = ALL()
        s.z = z = icw(
            title=what,
            in_source=source,
            size=size,
            outside_action='back',
            show_nuke=False,
            back_anim='out_scale'
        )
        w = z.widget
        h = 6
        v = len(al) // h
        ss = 100 * v
        sv = bui.scrollwidget(
            parent=w,
            size=(510,360),
            position=(60,50),
            color=var('bg')
        )
        cv = cw(
            parent=sv,
            background=False,
            size=(480,ss)
        )
        # List textures
        txt = {}
        for i in range(v):
            for j in range(h):
                n = (i*h)+j
                b = bw(
                    p=cv,
                    size=(65,65),
                    pos=(j*85,(ss-65)-i*100),
                    texture=bui.gettexture(al[n]),
                )
                bw(b, color=(1,1,1), oac=bs.CallPartial(s.pick,n))
                t = al[n]
                m = 15
                if len(t) > m: t = t[:m]+'\n'+t[m:]
                o = tw(p=cv,
                    maxwidth=65,
                    max_height=25,
                    pos=(j*85,(ss-100)-i*100),
                    v_align='top',
                    text=t
                )
                txt[al[n]] = o
    """Redirect"""
    def pick(s,n):
        gun()
        s.pipe(n)
        s.z.back()

class CharPicker:
    """Character picker"""
    def __init__(
        s,pipe,source=None,what='Select a character',
        note='',extra=None,cols=None,prf=''
    ):
        s.pipe = pipe
        size = (600,500)
        ah = s.ah = SPAZ()
        v = 1+len(ah) // 3
        s.z = z = icw(
            title=what,
            in_source=source,
            size=size,
            outside_action='back',
            show_nuke=False,
            note=note,
            back_anim='out_scale'
        )
        w = z.widget
        sv = bui.scrollwidget(
            parent=w,
            color=var('bg'),
            size=(510,360),
            position=(60,50))
        cv = cw(
            parent=sv,
            background=False,
            size=(480,v*150+180))
        # List characters
        txt = {}
        hm = NAME()
        mem = [COLS,cols][bool(cols)]()
        for i in range(v):
            for j in range(3):
                n = (i*3)+j
                if n >= len(ah): continue
                xp = 30+j*150
                yp = 1160-(i*180)-40
                pbw(
                    p=cv,
                    size=(120,120),
                    pos=(xp,yp-20),
                    texture=bui.gettexture(ah[n].icon_texture),
                    tint_texture=bui.gettexture(ah[n].icon_mask_texture),
                    oac=bs.CallPartial(s.pick,n,extra),
                    tex=mem
                )
                t = tw(
                    p=cv,
                    maxwidth=120,
                    pos=(xp+35,yp-52),
                    h_align='center',
                    v_align='center',
                    text=hm[n],
                    color=var(mem[2])
                )
                txt[hm[n]] = t
        if prf is not None: cw(cv, visible_child=txt[var(f'{prf}char')])
    """Redirect"""
    def pick(s,n,e):
        gun()
        s.z.back()
        s.pipe(n,*([e] if e is not None else []))

class SpazPicker:
    """Spaz picker"""
    def __init__(
        s,
        source,
        pipe,
        what='Select a spaz',
        deny=[],
        deny_msg="You can't pick that spaz!",
        note=None
    ):
        s.pipe = pipe
        s.deny = [deny,deny_msg]
        with bs.get_foreground_host_activity().context: all = [_ for _ in KIDS() if getattr(_,'exists',lambda:False)() and not getattr(_.getdelegate(object),'_dead',True)]
        l = len(all)
        v = l//3+[1,0][l%3<1]
        yl = v*185
        s.z = z = icw(
            title=what,
            in_source=source,
            size=(600,500),
            outside_action='back',
            show_nuke=False,
            back_anim='out_scale',
            note=note
        )
        w = z.widget
        sv = bui.scrollwidget(
            color=var('bg'),
            parent=w,
            size=(510,360),
            position=(60,50)
        )
        cv = cw(
            parent=sv,
            background=False,
            size=(480,yl)
        )
        yl -= 150
        # List characters
        tex = ALL()
        for i in range(v):
            for j in range(3):
                try: k = (i*3)+j; n = all[k]
                except: return
                ui = NTEX(n,tex)
                pbw(
                    p=cv,
                    size=(120,120),
                    pos=(155*j+30,yl-185*i),
                    oac=bs.CallPartial(s.pick,n),
                    **ui[0]
                )
                tw(
                    p=cv,
                    maxwidth=120,
                    pos=(155*j+65,yl-185*i-35),
                    h_align='center',
                    color=ui[1],
                    text=n.name or 'Unnamed'
                )
    """Clean up"""
    def pick(s,n):
        if n in s.deny[0]: btw(s.deny[1]); return
        s.z.back()
        s.pipe(n)

class ColorPicker:
    """Color picker"""
    def __init__(
        s,
        in_source: bui.buttonwidget,
        id: str,
        what: str,
        chr: str,
        on_back: callable,
        id2: str = None,
        mode: int = 0,
    ):
        s.mode = mode
        s.color = (var(what) or (1,1,1))
        s.what = what
        s.on_back = on_back
        s.in_source = in_source
        size = (450, 570)
        x,y = s.x,s.y = size
        s.rgb = ['Red','Green','Blue']
        z = icw(
            show_nuke=False,
            in_source=in_source,
            back_anim='out_scale',
            on_back=s.back,
            title=f'{what} color',
            size=size,
            outside_action='back',
            note='To support neon colors, a 12-point hex is used.',
            note_scale=0.5,
            note_pos=(50,6)
        )
        w = s.w = z.widget
        s.kids = {}
        s.rans = []
        s.shad = []
        char = D()[var(chr)]
        # Color preview
        pre = MK(char,id,id2)[mode>1]
        tex = bui.imagewidget(
            parent=w,
            color=(1,1,1),
            size=(165,165),
            position=(45,320),
            **pre
        )
        if s.mode == 2: bui.imagewidget(tex, color=s.color)
        s.pre = tex
        # RGBH editables
        for i in range(4):
            e = [*s.rgb,'Hex'][i]
            c = [(1,0,0),(0,1,0),(0,0,1),s.color][i]
            t = str(float(s.color[i]))[:5] if i < 3 else c2h(s.color)
            v = ['-#abcdef0123456789','-0.123456789'][i<3]
            xp = 220
            yp = 437-i*33
            bi = bui.imagewidget(
                parent=w,
                position=(xp+194,yp),
                size=(33,33),
                opacity=0,
                color=(30,0,0),
                texture=bui.gettexture('crossOut'),
            )
            o = ctw(
                parent=w,
                allow=v,
                on_edit=s.on_edit,
                tint=False,
                bad_image=bi,
                hint=e,
                color=c,
                size=(195,33),
                text=t,
                pos=(xp,yp)
            )
            s.kids[e] = o
        # Random button
        bw(
            p=w,
            size=(50,50),
            scale=0.9,
            color=darken(var('bg')),
            pos=(380,500),
            oac=s.randomize,
            icon=bui.gettexture('replayIcon'),
            button_type='regular',
            repeat=True,
            iconscale=1.2
        )
        # Color choices
        for i in range(3):
            for j in range(5):
                r = bw(
                    p=s.w,
                    size=(68,68),
                    pos=(56+j*73,237-i*69)
                )
                s.rans.append(r)
        # Shade row
        for j in range(5):
            r = bw(
                p=s.w,
                size=(68,68),
                pos=(56+j*73,30)
            )
            s.shad.append(r)
        s.shade()
        s.randomize(True)
    """Shade"""
    def shade(s):
        c = s.color
        for i in range(5):
            h = (i+0.5)/2
            d = (c[0]*h,c[1]*h,c[2]*h)
            bw(
                s.shad[i],
                color=d,
                oac=bs.CallPartial(s.set,d)
            )
    """Randomize"""
    def randomize(s,silent=False):
        min = -1
        max = 1
        ran = [[tuple([random.uniform(min+k/4,max+k/2) for i in range(3)]) for j in range(5)] for k in range(3)]
        lol = (i for i in s.rans)
        for i in range(3):
            for j in range(5):
                c = ran[i][j]
                r = bw(
                    next(lol),
                    color=c,
                    oac=bs.CallPartial(s.set,c),
                )
        None if silent else bui.getsound('cashRegister2').play()
    """Set color"""
    def set(s,c):
        bui.getsound('tap').play()
        for i in range(3):
            var(s.what+s.rgb[i], c[i])
            w = s.kids[s.rgb[i]].widget
            tw(w, text=str(c[i])[:5])
            tw(w, color=(1,0,0) if i < 1 else \
                        (0,1,0) if i < 2 else \
                        (0,0,1))
        var(s.what+'Hex', c2h(c))
        s.fresh(None)
    """Obtain rgb"""
    def get_rgb(s):
        a = []
        for i in s.rgb:
            o = var(s.what+i)
            v = float(o if o not in [None,''] else 1.0)
            a.append(v)
        return a
    """Obtain hex"""
    def get_hex(s):
        return c2h(s.get_rgb())
    """On edit"""
    def on_edit(s,k,v):
        if v == '' and k == 'Hex': return
        var(s.what+k,v)
        if k in s.rgb:
            if not '.' in v and v:
                v = v+".0"
                s.kids[k].set_text(v)
            var(s.what+'Hex',s.get_hex())
        elif k == 'Hex':
            if not v.startswith('#') and len(v) < 13:
                v = '#'+v
                s.kids['Hex'].set_text(v)
            if len(v.replace('#','')) < 12:
                for i in range(12-len(v)): v += '0'
            try: c = h2c(v)
            except: return
            [var(s.what+s.rgb[i],c[i]) for i in range(len(s.rgb))]
        s.fresh(k)
    """Refresh values"""
    def fresh(s,k):
        if k == 'Hex':
            for i in s.rgb:
                v = var(s.what+i)
                if v == '': continue
                s.kids[i].set_text(str(v)[:5])
        else:
            s.kids['Hex'].set_text(var(s.what+'Hex'))
        c = s.get_rgb()
        s.color = c
        s.shade()
        if not s.mode: bui.imagewidget(s.pre, tint_color=c)
        elif s.mode < 2: bui.imagewidget(s.pre, tint2_color=c)
        else: bui.imagewidget(s.pre, color=c)
        tw(s.kids['Hex'].widget, color=s.color)
    """On back"""
    def back(s):
        var(s.what, s.color)
        bw(s.in_source, color=s.color)
        s.on_back() if callable(s.on_back) else None

class NodeManager:
    """Node manager"""
    def __init__(s,node,source=None,pipe=None) -> None:
        s.node = node
        z = icw(
            in_source=source,
            title='Manage',
            show_nuke=False,
            size=(450,300),
            back_anim='out_scale',
            out_source=source,
            on_back=pipe
        )
        w = z.widget
        s.t = atw(
            p=w,
            obj=node,
            pos=(70,65),
            scale=1.3,
            size=(280,30)
        )
        s.btns = []
        for i in range(3):
            j = ['CallPartial','Random','Modify'][i]
            m = ['startButton','replayIcon','settingsIcon'][i]
            o = [s.call,s.random,s.modify][i]
            b = bw(
                p=w,
                label=j,
                icon=bui.gettexture(m),
                size=(130,35),
                oac=bs.CallPartial(s.t.insp,f=o),
                pos=(30+130*i,20)
            )
            s.btns.append(b)
    """Random"""
    def random(s,a):
        t = s.t.typ.__name__
        o = None
        if t == 'tuple': o = tuple([round(random.uniform(0,1),1) for _ in [0,0,0]])
        if t in ['float','int']: o = random.randrange(0,100)
        if o is None: btw('Unrecognized type!'); return
        Modder(
            obj=s.node,
            source=s.btns[1],
            attr=s.t.text,
            old=o,
            title='Random',
            label='Apply'
        )
    """CallPartial"""
    def call(s,a):
        if not callable(a): btw('Not callable!'); return
        CallPartialer(obj=a,source=s.btns[0])
    """Modify"""
    def modify(s,a):
        if s.t.dead: btw('Object is dead!'); return
        if callable(a): btw("You can't modify a callable!"); return
        Modder(
            obj=s.node,
            source=s.btns[2],
            attr=s.t.text,
            old=a
        )

class Confirm:
    """Action confirmer"""
    def __init__(s,source,pipe,title,label):
        z = icw(
            size=(280,150),
            title=title,
            auto_offset=False,
            back_anim='out_scale',
            in_source=source,
            outside_action='back',
            show_nuke=False
        )
        bw(
            p=z.widget,
            pos=(20,10),
            size=(240,50),
            label=label,
            oac=lambda:(pipe(),z.back())
        )

class CallPartialer:
    """Object caller"""
    def __init__(s,source,obj):
        z = icw(
            in_source=source,
            show_nuke=False,
            back_anim='out_scale',
            size=(450,500),
            title='CallPartial'
        )
        w = z.widget
        s.obj = obj
        tw(
            p=w,
            text=str(obj),
            color=(0,1,0),
            pos=(50,390),
            v_align='center',
            maxwidth=380
        )
        tw(
            p=w,
            text=GETSIG(obj),
            color=(0,0.6,1),
            pos=(50,362),
            v_align='center',
            maxwidth=380
        )
        s.at = ctw(
            allow=True,
            p=w,
            pos=(50,330),
            size=(380,30),
            description='Arguments will be passed to target method (eg. "True, 37, DieMessage"). Leave blank to pass nothing. Any input here will be evaluated, which means you can use args defined in Coolbox too! Enter',
            hint='Args separated by comma'
        )
        d = bui.hscrollwidget(
            parent=w,
            color=var('bg'),
            position=(44,70),
            size=(385,250)
        )
        s.c = cw(
            parent=d,
            size=(385,250),
            background=False
        )
        s.log = tw(
            p=s.c,
            pos=(0,210),
            max_height=250
        )
        s.log2 = itw(
            parent=s.c,
            position=(0,210),
            max_height=250
        )
        ok = chk(
            parent=w,
            position=(50,45),
            text='Same character width (beta)',
            textcolor=(1,1,1),
            scale=0.7,
            value=var('icall')
        )
        chk(ok,on_value_change_call=lambda v:(var('icall',v),chk(ok,value=v)))
        bw(
            p=w,
            pos=(325,20),
            icon=bui.gettexture('startButton'),
            label='CallPartial',
            size=(100,40),
            oac=s.call
        )
    """Real call"""
    def call(s):
        try: o = str(s.obj(*eval(f"[{s.at.get_text()}]")))
        except: bui.getsound('error').play(); o = traceback.format_exc(); c = (1,0,0)
        else: bui.getsound('ding').play(); c = (0,1,0)
        if var('icall'):
            tw(s.log,text='')
            s.log2.set_text(o.replace('\n','\\n'))
            s.log2.set_color((1,1,0))
            bui.apptimer(0.5,lambda:s.log2.set_color(c))
            m = s.log2.total+20
        else:
            m = GSW(max(o.splitlines(),key=len))+20
            tw(s.log,text=o,color=(1,1,0))
            s.log2.set_text('')
            bui.apptimer(0.5,lambda:tw(s.log,color=c))
        cw(s.c,visible_child=s.log,size=([m,385][m<385],250))

class Modder:
    """Object modifier"""
    def __init__(s,source,obj,attr,old,title='Modify',label='Modify'):
        s.obj = obj
        s.attr = attr
        s.z = icw(
            title=title,
            size=(450,180),
            show_nuke=False,
            back_anim='out_scale',
            in_source=source
        )
        w = s.z.widget
        s.t = ctw(
            allow=True,
            hint='New value (eg. True or "string")',
            description='Any input here will be evaluated. Which means you have to use quotes for strings (eg. "Name"), functions defined in coolbox.py can be used here! eg. gbt(\'agentColor\'). Enter',
            size=(400,30),
            text=f'"{old}"' if type(old) is str else str(old),
            p=w,
            pos=(28,68)
        )
        b = bw(
           p=w,
           pos=(330,20),
           icon=bui.gettexture('settingsIcon'),
           label=label,
           size=(100,40),
           oac=s.mod
        )
    """Actually modify"""
    def mod(s):
        v = s.t.get_text()
        try:
            with bs.get_foreground_host_activity().context:
                v = eval(v)
                if s.attr == 'position' and isinstance(v, (tuple, list)) and len(v) == 3:
                    v = tuple(round(c, 2) for c in v)
                setattr(s.obj,s.attr,v)
        except Exception as E: err(str(E))
        else:
            bui.getsound('ding').play()
            s.z.back()
            push('Success!',color=(0,1,0))
            if Zoom.__ob__ == s.obj: return
            Zoom(s.obj) if len(getattr(s.obj,'position',(0,0))) == 3 else None

class atw:
    """Attribute text widget"""
    def __init__(s,scale,obj,p,pos,size,*a,**k):
        k.update({
            'position':pos,
            'editable':True,
            'description':'Start typing to see matches. Write a star "*" to list all attrs. Enter',
            'parent':p,
            'maxwidth':size[0]+50,
            'scale':scale,
            'size':size
        })
        s.widget = tw(*a,**k)
        k.update({
            'editable':False,
            'text':'try "color" or "*"'
        })
        s.widget2 = tw(*a,**k)
        bw(
            p=p,
            pos=(400,pos[1]),
            size=(35,35),
            label=bui.charstr(bui.SpecialChar.UP_ARROW),
            oac=lambda:bui.getsound('tap').play()
        )
        s.kids = []
        for i in range(4):
            j = ['Type','Value','Name',str(obj)][i]
            c = [(1,1,0),(0,1,1),(0,1,0),(1,0,1)][i]
            s.kids.append(tw(p=p,
               text=j,
               maxwidth=400,
               color=c,
               v_align='center',
               pos=(25,100+(30*i))))
        s.parent = p
        s.pos = pos
        s.obj = obj
        s.type = getattr(obj,'getnodetype',lambda:'idk')()
        s.typ = 'Type'
        s.x, s.y = size
        s.attrs = dir(obj)
        s.scale = scale
        s.prev = []
        s.root = s.text = s.old = None
        s.dropped = s.active = s.dead = False
        s.ty = 30
        s.cnt = 8
        s.spy()
        s.tip(True)
    """Inspect"""
    def insp(s,f):
        if s.valid(): return f(s.get(s.text))
        btw('Attribute does not exist!')
    """Get"""
    def get(s,t):
        return getattr(s.obj,t,None) if not (s.type == 'spaz' and t in BAD()) else (0,0,0)
    """Control hint"""
    def tip(s,b):
        tw(s.widget2,color=(0.5,0.5,0.5,1 if b else 0))
    """Drop height"""
    def ht(s):
        l = len(s.prev)
        return (s.ty * (s.cnt if l > s.cnt else l) + 10)
    """Get text"""
    def get_text(s):
        if s.parent.transitioning_out or not s.parent.exists(): return
        return tw(query=s.widget)
    """Set text"""
    def set_text(s,t):
        ot = s.get_text()
        if ot == t: s.clear(False)
        tw(s.widget,text=t)
    """Validate"""
    def valid(s):
        for i in s.prev:
            if i == s.text: return True
    """Spy"""
    def spy(s):
        if not s.dead and not s.obj.exists(): s.dead = True
        try:
            if s.parent.transitioning_out or not s.parent.exists(): raise
            s.text = s.get_text()
            s.active = s.parent.get_selected_child() in [s.widget,s.root]
        except: return
        if s.text:
            s.apply(s.valid())
            if (s.old != s.text) and s.active:
                s.old = s.text
                s.refine()
                s.drop()
        if (not s.text and s.dropped) or (not s.active and s.dropped): s.clear(False)
        bui.apptimer(0.1, s.spy)
    """Apply for granted"""
    def apply(s,d):
        a = s.text if d else 'Name'
        v = s.get(a) if d else 'Value'
        t = type(v) if d else 'Type'
        [tw(s.kids[i],color=[(1,1,0),(0,1,1),(0,1,0)][i],text=f'{[t,v,a][i]}') for i in range(3)]
        s.typ = t
    """Refine prev"""
    def refine(s):
        s.prev = []
        [s.prev.append(p) if s.text in "*"+p else None for p in s.attrs]
    """Clear drop"""
    def clear(s,b):
        s.dropped = b
        if not b: s.anim(s.ht(),-1,True)
        elif s.root: s.root.delete()
        s.tip((not b) and (not s.text))
    """Dropdown"""
    def drop(s):
        s.px = s.pos[0]-52
        s.py = s.pos[1]-4
        b = s.dropped
        s.clear(True)
        l = len(s.prev)*s.ty
        s.root = bui.scrollwidget(
            parent=s.parent,
            size=(s.x+60,s.ht() if s.dropped else 0),
            highlight=False,
            color=var('bg'),
            border_opacity=0.0,
            position=(s.px,s.py-s.ht())
        )
        c = cw(
            parent=s.root,
            size=(s.x+60,l),
            background=False
        )
        bui.imagewidget(
            parent=c,
            size=(s.x+1500,l+1000),
            texture=bui.gettexture('black'),
            opacity=0.7,
            position=(-300,-500)
        )
        r = bui.hscrollwidget(
            parent=c,
            size=(s.x+40,l+200),
            color=var('bg'),
            border_opacity=0.0,
            highlight=False,
            position=(0,s.py-60)
        )
        c = cw(
            parent=r,
            size=(s.x,s.x),
            background=False
        )
        tl = tw(
            p=c,
            size=(1,1),
            text=" ",
            pos=(0,l))
        top = s.x
        for i in range(len(s.prev)):
            u = s.prev[i]
            y = l-(i+1)*s.ty
            t = tw(
                p=c,
                text=u,
                size=(s.x,s.ty),
                color=(0.6,0.6,0.6),
                pos=(0,y),
                selectable=True,
                click_activate=True,
                on_activate_call=bs.CallPartial(s.set_text,u)
            )
            txt = type(s.get(u)).__name__
            uw = GSW(u+" ")
            tw(
                p=c,
                text=txt,
                size=(s.x,s.ty),
                color=(1,1,0),
                pos=(uw,y)
            )
            new = GSW(u+" "+txt)
            if new > top: top = new
            o = None
            for j in range(len(u)):
                f = u.find(s.text,j)
                if f < 0: break
                if o == f: continue
                o = f
                tw(
                    p=c,
                    text=s.text,
                    size=(s.x,s.ty),
                    color=(0,1,0),
                    pos=(GSW(u[:o]),y)
                )
        if not b: s.anim(0,1)
        cw(
            c,
            size=(top+20,l+20),
            visible_child=tl
        )
    """Animate"""
    def anim(s,i,r,nuke=False):
        if (i > s.ht()) or (i < 0):
            if nuke: s.root.delete(); s.old = None
            return
        try: bui.scrollwidget(s.root, size=(s.x+60,i), position=(s.px,s.py-i))
        except: return
        bui.apptimer(0.0005, bs.CallPartial(s.anim,i+(1*r),r,nuke))

class NodePicker:
    """Node picker"""
    def __init__(s,pipe,source=None,which='node',allow='all',note=''):
        s.zins = None
        s.op = pause()
        s.z = icw(
            in_source=source,
            title='Select a '+which,
            back_anim='out_scale',
            size=(600,600),
            on_back=lambda:(npause(s.op),s.zins.x() if s.zins else None),
            show_nuke=False,
            note=note,
            note_scale=0.6
        )
        w = s.w = s.z.widget
        s.pipe = pipe
        s.allow = allow
        s.kids = []
        s.nuds = []
        s.sl = None
        s.blind = False
        sv = bui.scrollwidget(
            parent=w,
            size=(500,350),
            color=var('bg'),
            position=(50,50)
        )
        s.cv = cw(
            parent=sv,
            background=False
        )
        c = tuple([0.4 for i in range(3)])
        for i in range(3):
            j = ['Type','Position','Extra'][i]
            k = [65,195,430][i]
            tw(
                p=w,
                text=j,
                size=(40,20),
                color=c,
                pos=(k,410)
            )
        v = var('npp')
        s.btns = []
        for i in range(6):
            j = ['', 'Delete', 'Refresh','Manage','Clone','Pick'][i]
            k = ['black', 'textClearButton', 'replayIcon', 'menuIcon', 'achievementFreeLoader', 'ouyaOButton'][i]
            l = ([40,210,380]*2)[i]
            o = [s.toggle, s.delete, s.refresh, s.advanced, s.clone, s.pick][i]
            b = bw(
                p=w,
                pos=(l,[430,480][i<3]),
                label=j,
                size=(170,45),
                icon=bui.gettexture(k),
                oac=o
            )
            s.btns.append(b)
        s.up()
        s.toggle(0,False)
    """Advanced"""
    def advanced(s):
        n = s.now()
        if not n: return
        n = s.nuds[s.sl]
        NodeManager(source=s.btns[3],node=n)
    """Toggle pause"""
    def toggle(s,f=1,d=True):
        v = var('npp')
        if f: var('npp',[1,0][v]); v = not v
        if d: bui.getsound('deek').play()
        bw(s.btns[0], label=['Pause','Resume'][v], icon=bui.gettexture(['achievementFootballShutout','startButton'][v]))
        npause()
    """Confirm safely"""
    def confirm(s,what,f):
        Confirm(
            source=s.btns[1],
            title=what,
            label='Confirm (Risky!)',
            pipe=lambda:(f(),z.back())
        )
    """Locate node"""
    def delete(s):
        n = s.now()
        if not n: return
        def f():
            s.sl = None
            n.delete()
        s.confirm('Delete',f)
    """Refresh nodes"""
    def refresh(s):
        ding()
        s.sl = None
        s.up()
    """Obtain safely"""
    def now(s):
        if s.sl is None: btw('Select a node!'); return
        return s.nuds[s.sl]
    """Clone node"""
    def clone(s):
        n = s.now()
        if not n: return
        def f():
            d = dir(n)
            all = {}
            for i in d:
                a = getattr(n,i)
                if i.startswith('_') or callable(a): continue
                all[i] = a
            with bs.get_foreground_host_activity().context:
                try: c = bs.newnode(n.getnodetype(),attrs=all)
                except: return
            SPARK(c.position)
            push('Cloned!', color=(0,1,0))
        s.confirm('Clone',f)
    """Pick"""
    def pick(s):
        n = s.now()
        if not n: return
        if s.allow == '3D':
            try:
                p = n.position
                if len(p) != 3: raise
            except: btw('Must be a 3D node!'); return
        s.blind = True
        s.pipe(n)
        npause(0)
        s.z.back()
    """Update"""
    def up(s):
        with bs.get_foreground_host_activity().context: a = bs.getnodes()
        l = len(a)
        y = l * 30
        [[o.delete() for o in j] for j in s.kids]
        s.kids.clear()
        s.nuds.clear()
        for i in range(l):
            n = a[i]
            p = n.position if hasattr(n,'position') else ()
            q = len(p) if p else 0
            t = n.getnodetype()
            s.kids.append([])
            f = y-30*(i+1)
            for j in range(3):
                x = [10,140,375][j]
                k = [t,str(rnd(p)).replace('()','N/A'),bui.charstr(bui.SpecialChar.LOGO_FLAT) if hasattr(n,'color') else bui.charstr(bui.SpecialChar.DPAD_CENTER_BUTTON)][j]
                m = [120,200,150][j]
                t = tw(
                    p=s.cv,
                    text=k,
                    maxwidth=m,
                    size=(m,25),
                    h_align='left',
                    color=n.color if hasattr(n,'color') and j == 2 else (1,1,1),
                    v_align='center',
                    selectable=True,
                    click_activate=True,
                    on_activate_call=bs.CallPartial(s.select,i),
                    pos=(x,f)
                )
                s.kids[-1].append(t)
            t = str(getattr(n,'color_texture',0) or getattr(n,'texture','"empty"'))
            p1 = t.find('"')+1
            p2 = t[p1:t.find('"',p1)]
            try: t = bui.gettexture(p2)
            except: t = bui.gettexture('empty')
            g = bui.imagewidget(
                parent=s.cv,
                size=(25,25),
                position=(x+40,f),
                texture=t
            )
            s.nuds.append(n)
        cw(s.cv, size=(500,y))
        s.eye()
    """Check for existence"""
    def eye(s):
        z = 0
        for k in s.kids:
            n = s.nuds[z]
            if not n.exists():
                for t in k:
                    try:
                        if s.w.exists and s.w.transitioning_out: return
                        if t.exists: tw(t, color=(1,0,0))
                    except: return
                if s.sl is not None and s.sl == z:
                    btw('Selected node has died just now!')
                    s.sl = None
            z += 1
        if not s.blind: bui.apptimer(0.1,s.eye)
    """Highlight"""
    def hl(s, sl):
        if (sl is None): return
        try: n = s.nuds[sl]
        except: return
        if not n.exists():
            btw('Node is dead!')
            return False
        c = (1,1,1)
        try:
            k = s.kids[s.sl]
            [tw(k[i],color=c) for i in range(2)]
        except: pass
        c = (0,1,0)
        try:
            k = s.kids[sl]
            [tw(k[i],color=c) for i in range(2)]
            cw(s.cv, visible_child=k[0])
        except IndexError: return
        if len(getattr(n,'position',(0,0))) > 2:
            s.zins = Zoom(n)
        return sl
    """Select"""
    def select(s,i):
        r = s.hl(i)
        if r is not False: s.sl = r

class Zoom:
    """Smooth zoomer"""
    __up__ = False
    __ob__ = None
    def __init__(s,n):
        s.n = n
        c = s.__class__
        s.u = lambda: c.__up__
        s.v = lambda b: setattr(c,'__up__',b)
        s.w = lambda b: setattr(c,'__ob__',b)
        s.x = lambda: (s.v(False),_ba.set_camera_manual(False),s.w(None))
        s.step = 0
        if s.u(): s.x(); bui.apptimer(0.1,s.focus)
        else: s.focus(); s.w(n)
    def focus(s):
        s.v(True)
        s.w(s.n)
        s.step = 1
        s._focus()
        bui.apptimer(1.5,bs.CallPartial(setattr,s,'step',2))
    def _focus(s):
        if not s.u() or not s.n.exists(): s.x(); return
        if s.step == 2:
            _ba.set_camera_manual(True)
            s.zoom()
            return
        if s.step == 4: s.x(); return
        _ba.set_camera_target(*s.n.position)
        bui.apptimer(0.01,s._focus)
    def zoom(s):
        if not s.u() or not s.n.exists(): s.x(); return
        p = _ba.get_camera_position()
        q = s.n.position
        d = math.dist(p,q)
        if d < 5:
            s.step = 3
            s._focus()
            bui.apptimer(2,bs.CallPartial(setattr,s,'step',4))
            return
        e = 0.01+d*0.005
        e = min(e,0.8)
        dx = q[0]-p[0]
        dy = q[1]-p[1]
        dz = q[2]-p[2]
        sx = dx*e
        sy = dy*e
        sz = dz*e
        _ba.set_camera_position(*(p[0]+sx,p[1]+sy,p[2]+sz))
        _ba.set_camera_target(*q)
        bui.apptimer(0.0081,s.zoom)

class ActionManager:
    """Action manager"""
    actions = lambda c=0: ['Say','MoveTo','Wait','GoTo','Key','Follow']
    @classmethod
    def classes(cls):
        g = globals()
        return [g['Action'+i] for i in cls.actions()]
    @classmethod
    def which(cls,s):
        n = s.__class__
        i = cls.classes().index(n)
        return (cls.actions()[i],i)
    def __init__(s,source=None):
        s.z = icw(
            in_source=source,
            show_nuke=False,
            back_anim='out_scale',
            title='Actions',
            note='Advanced'
        )
        w = s.z.widget
        sv = bui.scrollwidget(parent=w,
                size=(400,310),
                color=var('bg'),
                position=(60,50))
        s.cv = cw(parent=sv,
                  background=False,
                  size=(400,0))
        b = bw(p=w,
               size=(100,50),
               pos=(470,310),
               label='Add',
               icon=bui.gettexture('powerupHealth'))
        bw(b,oac=bs.CallPartial(ActionPipe,source=b,pipe=s.add,what='Add'))
        s.kids = []
        for i in range(3):
            j = [s.edit,s.replace,s.delete][i]
            k = ['Edit','Replace','Delete'][i]
            l = [256,202,148][i]
            m = ['settingsIcon','replayIcon','crossOut'][i]
            b = bw(p=w,
                   size=(100,50),
                   pos=(470,l),
                   label=k,
                   icon=bui.gettexture(m),
                   oac=j)
            s.kids.append(b)
        for i in [-1,1]:
            j = ['Up','Down'][i<0]
            k = [94,40][i<0]
            bw(p=w,
               size=(100,50),
               pos=(470,k),
               label=j,
               icon=bui.gettexture(f'{j.lower()}Button'),
               repeat=True,
               oac=bs.CallPartial(s.nav,-i))
        s.texts = []
        s.sl = None
        s.update()
    """Index control"""
    def nav(s,i):
        l = len(var('act'))-1
        if s.sl is None: i = [0,l][i<0]
        else: i = s.sl + i
        if i < 0 or i > l: bui.getsound('block').play(); return
        s.select(i)
        bui.getsound('tap').play()
    """Conditional collect"""
    def collect(s,i):
        if i == 0: a = [0,var('say'),var('tsay')]
        elif i == 1: a = [i,[round(float(var(f'move{i}')),3) for i in range(3)],float(var('smove')),float(var('tmove'))]
        elif i == 2: a = [i,round(float(var('wait')),3)]
        elif i == 3: a = [i,int(var('goto')),int(var('egoto'))]
        elif i == 4: a = [i,var('lastkey')]
        elif i == 5: a = [i,var('follow'),float(var('sfollow')),float(var('tfollow'))]
        else: bs.broadcastmessage('nah '+str(i)); return
        return a
    """Add action"""
    def add(s,i):
        o = var('act')
        a = s.collect(i)
        o.append(a)
        var('act',o)
        s.update()
    """Edit action"""
    def edit(s):
        if s.sl is None: btw('Select an action to edit!'); return
        o = var('act')
        v = o[s.sl]
        i = v[0]
        def f():
            a = s.collect(i)
            o[s.sl] = a
            var('act',o)
            s.update()
            gun()
        s.classes()[i](source=s.kids[0],pipe=lambda z: f())
    """Replace action"""
    def replace(s):
        if s.sl is None: btw('Select an action to replace!'); return
        o = var('act')
        def f(i):
            a = s.collect(i)
            o[s.sl] = a
            var('act',o)
            s.update()
            gun()
        ActionPipe(source=s.kids[1],pipe=lambda i: f(i),what='Replace')
    """Update"""
    def update(s):
        v = var('act')
        l = len(v)
        [t.delete() for t in s.texts]
        s.texts.clear()
        w = s.cv
        y = l*30+10
        cw(w,size=(400,y))
        with bs.get_foreground_host_activity().context:
            nn = bs.getnodes()
            ns = [str(nn[i]) for i in range(len(nn))]
            del nn
        mem = s.actions()
        for i in range(len(v)):
            a = v[i]
            t = tw(
                p=w,
                text=f'{i+1} {mem[a[0]]} {a[1:]}',
                size=(350,30),
                maxwidth=350,
                selectable=True,
                click_activate=True,
                on_activate_call=bs.CallPartial(s.select,i),
                v_align='center',
                pos=(20,(y-40)-i*30)
            )
            s.texts.append(t)
            if a[0] == 5 and a[1] != 'me' and not a[1] in ns:
                tw(t, color=(1,0,0), on_activate_call=bs.CallPartial(s.select,i,dead=True))
        s.sl = None
    """Update selection"""
    def up(s):
        [tw(s.texts[i],color=[(1,1,1),(0,1,0)][i==s.sl]) for i in range(len(s.texts))]
        cw(s.cv,visible_child=s.texts[s.sl])
    """Select"""
    def select(s,i,dead=False):
        s.sl = i
        s.up()
        if dead: btw('Follow node is dead!\nAction will be ignored. Pick the node again.')
    """Delete selected"""
    def delete(s):
        if s.sl is not None: var('act').pop(s.sl); s.update(); bui.getsound('pop01').play()
        else: btw('Select an action to delete!')

class ActionPipe:
    """Action pipe"""
    def __init__(s,pipe,source=None,what='Action'):
        s.pipe = pipe
        ah = ActionManager.actions()
        eh = ActionManager.classes()
        l = len(ah)
        y = 130+60*l
        s.z = icw(in_source=source,
                  show_nuke=False,
                  back_anim='out_scale',
                  size=(300,y),
                  title=what)
        w = s.z.widget
        for i in range(l):
            b = bw(p=w,
                   pos=(25,(y-150)-60*i),
                   size=(250,55),
                   label=ah[i])
            bw(b,oac=bs.CallPartial(eh[i],s.pick,b))
    """Redirect"""
    def pick(s,i):
        s.z.back()
        s.pipe(i)

class ActionSay:
    """Action Say"""
    def __init__(s,pipe,source=None):
        s.which = ActionManager.which(s)
        s.pipe = pipe
        s.z = icw(
            in_source=source,
            title=s.which[0],
            size=(450,230),
            back_anim='out_scale',
            show_nuke=False,
            note='The more the duration, the slower the animation.',
            note_pos=(15,10),
            note_scale=0.6
        )
        w = s.z.widget
        s.txt = []
        for i in range(2):
            j = ['Say','And last for duration'][i]
            k = [120,90][i]
            l = ['say','tsay'][i]
            m = [True,'0123456789'][i]
            n = [80,310][i]
            o = [330,100][i]
            p = ['text','seconds'][i]
            tw(p=w,text=j,pos=(30,k))
            s.txt.append(ctw(conf=l,text=var(l),allow=m,hint=p,pos=(n,k),p=w,size=(o,30),h_align='left'))
        bw(
            p=w,
            pos=(330,30),
            size=(80,50),
            oac=s.pick,
            label='Done'
        )
    """Pick"""
    def pick(s):
        for t in s.txt:
            if t.bad or not t.get_text(): err(f'Invalid {t.hint}!\nFix your input!'); return
        [var(['say','tsay'][i],s.txt[i].get_text()) for i in [0,1]]
        s.z.back()
        gun()
        s.pipe(s.which[1])

class ActionFollow:
    """Action follow"""
    def __init__(s,pipe,source=None):
        s.which = ActionManager.which(s)
        s.z = icw(
            in_source=source,
            title=s.which[0],
            size=(450,230),
            back_anim='out_scale',
            show_nuke=False,
            note="Keep in mind that dist is relevant to target's center",
            note_scale=0.6,
            note_pos=(15,5)
        )
        w = s.z.widget
        s.pipe = pipe
        for i in range(2):
            j = ['Me','Pick'][i]
            b = bw(p=w,
                   label=j,
                   pos=(25,90-55*i),
                   size=(100,50))
            o = [bs.CallPartial(s.pick,'me'),bs.CallPartial(NodePicker,s.pick,b,allow='3D',note='Coolbox stores picked nodes as strings for portability')][i]
            bw(b,oac=o)
        for i in range(3):
            j = ['Stop following when:','- Distance is less than','- Time is more than'][i]
            k = [105,70,40][i]
            l = [300,200][i>1]
            tw(p=w,
               pos=(135,k),
               maxwidth=l,
               text=j)
        for i in range(2):
            j = [380,340][i]
            k = [67,37][i]
            l = ['sfollow','tfollow'][i]
            m = ['Bot might keep following until timeout if distance is too narrow or zero, enter','Time starts from the moment action is played, stop following when time is more than'][i]
            ctw(p=w,
                pos=(j,k),
                size=(65,30),
                allow='0.123456789',
                conf=l,
                description=m,
                text=var(l))
    """Redirect"""
    def pick(s,n):
        var('follow',str(n))
        s.pipe(s.which[1])
        s.z.back()
        gun()

class ActionKey:
    """Action send key"""
    def __init__(s,pipe,source=None):
        s.which = ActionManager.which(s)
        s.z = icw(
            in_source=source,
            title=s.which[0],
            size=(250,300),
            back_anim='out_scale',
            show_nuke=False
        )
        w = s.z.widget
        s.pipe = pipe
        for i in range(4):
            j = [105,155,105,55][i]
            k = [50,100,150,100][i]
            l = ['Jump','Bomb','PickUp','Punch'][i]
            sbw(
                p=w,
                pos=(j,k),
                icon=bui.gettexture('button'+l),
                oac=bs.CallPartial(s.set,i)
            )
    """Initial set"""
    def set(s,i):
        var('lastkey',i)
        s.pick()
    """Pick"""
    def pick(s):
        s.z.back()
        s.pipe(s.which[1])
        gun()

class ActionGoTo:
    """Action go to"""
    def __init__(s,pipe,source=None):
        s.which = ActionManager.which(s)
        s.z = icw(in_source=source,
                  title=s.which[0],
                  size=(500,200),
                  back_anim='out_scale',
                  show_nuke=False)
        w = s.z.widget
        s.pipe = pipe
        t = tw(pos=(60,90),
               p=w,
               text='Go to action with index')
        for i in range(2):
            j = ['Usable for','times'][i]
            t = tw(pos=(60+190*i,50),
                   p=w,
                   text=j)
        s.t = ctw(p=w,
              text=var('goto'),
              pos=(315,85),
              size=(65,40),
              conf='goto',
              description='Simulate a loop by going to a previous action again, or skip specific next actions. Enter',
              hint='num',
              allow='01223456789')
        s.u = ctw(p=w,
              text=var('egoto'),
              pos=(180,45),
              size=(65,40),
              conf='egoto',
              description='Expire after being used for',
              hint='num',
              allow='01223456789')
        bw(p=w,
           pos=(390,30),
           size=(80,40),
           oac=s.pick,
           label='Done')
    """Pick"""
    def pick(s):
        t = s.t.get_text()
        u = s.u.get_text()
        if s.t.bad or (not t) or (not u): err('Fix your input!'); return
        if ((int(t) <= 0) or (int(t) >= len(var('act')))):
            err('No such action exists!')
            return
        if (int(u) <= 0):
            btw("At least repeat it 1 time!")
            return
        s.z.back()
        s.pipe(s.which[1])
        gun()

class ActionWait:
    """Action wait"""
    def __init__(s,pipe,source=None):
        s.which = ActionManager.which(s)
        s.z = icw(in_source=source,
                  title=s.which[0],
                  size=(500,200),
                  back_anim='out_scale',
                  show_nuke=False)
        w = s.z.widget
        s.pipe = pipe
        for i in range(2):
            j = ['Keep waiting for','seconds'][i]
            t = tw(pos=(60+260*i,80),
               p=w,
               text=j)
        s.t = ctw(p=w,
                  text=var('wait'),
                  pos=(248,75),
                  size=(65,40),
                  conf='wait',
                  description='Do nothing for',
                  hint='num',
                  allow='0.1223456789')
        bw(p=w,
           pos=(390,30),
           size=(80,40),
           oac=s.pick,
           label='Done')
    """Pick"""
    def pick(s):
        if s.t.bad: err('Fix your input!'); return
        s.z.back()
        s.pipe(s.which[1])
        gun()

class ActionMoveTo:
    """Action move to"""
    def __init__(s,pipe,source=None):
        s.which = ActionManager.which(s)
        s.z = icw(in_source=source,
                  title=s.which[0],
                  size=(500,230),
                  back_anim='out_scale',
                  show_nuke=False)
        w = s.z.widget
        s.pipe = pipe
        s.pos = []
        tw(pos=(30,120),
           p=w,
           text='Directly move towards')
        tw(pos=(30,80),
           p=w,
           text='Stop when distance is less than')
        tw(pos=(30,40),
           p=w,
           text='Or when time is more than')
        for i in range(3):
            j = ['X','Y','Z'][i]
            t = ctw(p=w,
                    text=var(f'move{i}'),
                    pos=(290+60*i,115),
                    size=(55,40),
                    conf=f'move{i}',
                    hint=j+' position',
                    allow='-0.1223456789')
            s.pos.append(t)
        s.t = ctw(p=w,
                  text=var('smove'),
                  pos=(380,75),
                  size=(60,40),
                  conf='smove',
                  description='Minimum distance between bot and target',
                  hint='Dist',
                  allow='0.1223456789')
        s.u = ctw(p=w,
                  text=var('tmove'),
                  pos=(325,35),
                  size=(60,40),
                  conf='tmove',
                  description='Timeout before force stopping if dist is not met',
                  hint='Time',
                  allow='0.1223456789')
        bw(p=w,
           pos=(390,30),
           size=(80,40),
           oac=s.pick,
           label='Done')
    """Pick"""
    def pick(s):
        for t in s.pos+[s.t,s.u]:
            if t.bad: err('Fix your input!'); return
        s.z.back()
        s.pipe(s.which[1])
        gun()

class ConPipe:
    """Conditional pipe"""
    cons = lambda: ['Has Group ID','In Team']
    def __init__(s,source,pipe):
        s.pipe = pipe
        mem = s.__class__.cons()
        l = len(mem)
        y = 130+60*l
        s.z = icw(
            in_source=source,
            show_nuke=False,
            back_anim='out_scale',
            size=(300,y),
            note='Ignored until found',
            note_pos=(15,10),
            note_scale=0.6,
            title='Condition',
            outside_action='back',
            auto_offset=False
        )
        w = s.z.widget
        g = globals()
        for i in range(l):
            j = mem[i]
            b = bw(
                p=w,
                pos=(25,(y-150)-60*i),
                size=(250,55),
                label=j
            )
            bw(b,oac=bs.CallPartial(s.collect,b,i))
    """Collect"""
    def collect(s,b,i):
        s.extra = i
        Collector(source=b,pipe=s.pick,allow=['01223456789',True][i])
    """Redirect"""
    def pick(s,t):
        s.z.back()
        s.pipe([s.extra,t])

class Collector:
    """Value collector"""
    def __init__(
        s,
        source,
        pipe,
        allow=True,
        title='Input',
        first='text',
        double='',
        two=False,
        dallow=True,
        raw=False
    ):
        s.pipe = pipe
        s.two = two
        s.raw = raw
        s.z = icw(
            in_source=source,
            show_nuke=False,
            back_anim='out_scale',
            auto_offset=False,
            size=(300,150+[0,30][two]),
            title=title
        )
        w = s.z.widget
        s.t = ctw(
            p=w,
            allow=allow,
            hint=first,
            size=(200,30),
            pos=(30,30)
        )
        s.t2 = ctw(
            p=w,
            allow=dallow,
            hint=double,
            size=(200,30),
            pos=(30,65)
        ) if two else None
        bw(
            label='Done',
            p=w,
            pos=(230,30),
            size=(50,30),
            oac=bs.CallPartial(s.pick)
        )
    def pick(s):
        t = s.t.get_text()
        if s.t.bad or (not t and not s.raw): err(f'Invalid {"Input" if s.raw else s.t.hint}!\nFix your input!'); return
        if s.two:
            t2 = s.t2.get_text()
            if s.raw and t == "": v = ''
            elif s.raw:
                try: v = eval(t)
                except Exception as e:
                    err(str(e))
                    return
            else: v = t
            r = (t2,v)
        else: r = t
        s.z.back()
        s.pipe(r)

class Overlay:
    """Controls overlay"""
    def __init__(s,build=False):
        s.colors = [
            [(0.2,0.6,0.2),(0.4,1,0.4)],
            [(0.6,0,0),(1,0,0)],
            [(0.2,0.6,0.6),(0.4,1,1)],
            [(0.6,0.6,0.2),(1,1,0.4)],
            [(0.3,0.23,0.5),(0.2,0.13,0.3)]
        ]
        s.pics = []
        s.texts = []
        s.pos = []
        s.nub = []
        s.old = [0,0,0]
        with bs.get_foreground_host_activity().context:
            # This is a bascenev1 scene overlay, not a bauiv1 window - it
            # has to use the scene 'attach' node attr (like Scoreboard and
            # RespawnIcon do) to anchor to a screen corner. bui.get_virtual_
            # screen_size() is a bauiv1-only call and means nothing here,
            # which is why it went invisible/out of bounds. 'attach':
            # 'topRight' + small negative offsets keeps this pinned to the
            # bottom-right corner regardless of resolution.
            for i in range(4):
                j = ['Jump','Bomb','PickUp','Punch'][i]
                k = [-210,-160,-210,-260][i]
                l = [-175,-125,-75,-125][i]
                c = s.colors[i][0]
                n = bs.newnode(
                    'image',
                    attrs={
                        'texture': bs.gettexture('button'+j),
                        'absolute_scale': True,
                        'attach': 'topRight',
                        'position': (k,l),
                        'scale': (60,60),
                        'color': c
                    }
                )
                s.pics.append(n)
                j = (['Down','Exit','Up','Build'] if build else ['Down','Pick','Up','Boost'])[i]
                k = [-210,-130,-210,-295][i]
                l = [-230,-125,-20,-125][i]
                h = ['center','left','center','right'][i]
                v = ['bottom','center','top','center'][i]
                n = bs.newnode(
                    'text',
                    attrs={
                        'text': j,
                        'h_attach': 'right',
                        'v_attach': 'top',
                        'position': (k,l),
                        'color': c,
                        'h_align': h,
                        'v_align': v
                    }
                )
                s.texts.append(n)
            for i in range(3):
                c = s.colors[[1,0,2][i]][0]
                n = bs.newnode(
                    'text',
                    attrs={
                        'text': '0',
                        'h_attach': 'right',
                        'v_attach': 'top',
                        'position': (-170,[-190,-220,-250][i]),
                        'color': c,
                        'h_align': 'left'
                    }
                )
                s.pos.append(n)
            s.np = (-20,-205)
            for i in [0,1]:
                j = [110,60][i]
                n = bs.newnode(
                    'image',
                    attrs={
                        'texture': bs.gettexture('nub'),
                        'absolute_scale': True,
                        'attach': 'topRight',
                        'position': s.np,
                        'scale': (j,j),
                        'color': s.colors[4][i]
                    }
                )
                s.nub.append(n)
            s.fade()
    """Color overlays"""
    def set(s,i,c):
        s.pics[i].color = s.texts[i].color = c
    """Color position"""
    def pset(s,i,c):
        s.pos[i].color = c
    """Simulate pressed"""
    def press(s,i):
        s.set(i,s.colors[i][1])
        s.pics[i].opacity = 1.0
    """Simulate released"""
    def release(s,i):
        s.set(i,s.colors[i][0])
        s.pics[i].opacity = 0.7
    """Get all nodes"""
    def nodes(s):
        return s.pics+s.texts+s.pos+s.nub
    """Update position"""
    def up(s,x,y,z,lr,ud):
        new = [x,y,z]
        for i in range(3):
            c = s.colors[[1,0,2][i]]
            if s.old[i] == new[i]: s.pset(i,c[0]); continue
            t = s.pos[i]
            t.text = str(round(new[i],5))
            s.pset(i,c[1])
        s.old = new
        [setattr(s.nub[i],'opacity',[[0.5,0.2],[0.7,0.3]][bool(lr or ud)][i]) for i in [0,1]]
        p = s.np
        m = math.sqrt(lr**2+ud**2) or 1
        d = 25*min(math.sqrt(lr**2+ud**2),1)
        lr /= m
        ud /= m
        s.nub[1].position = (p[0]+lr*d,p[1]+ud*d)
    """Fade"""
    def fade(s,i=0):
        [bs.timer(1, bs.animate(n,'opacity',{0:i,0.5:abs(i-0.7)}).delete) for n in s.nodes()]
    """Destroy overlay"""
    def destroy(s):
        with bs.get_foreground_host_activity().context:
            bs.timer(0.2,lambda:s.fade(0.7))
            bs.timer(1,lambda: [n.delete() for n in s.nodes()])

class Mapper:
    """In-Game position mapper"""
    last = 0
    def __init__(s, pipe, pos=None, on_exit=None, build=False) -> None:
        s.tired = time.time_ns() - s.__class__.last < 10**9
        if s.tired: btw('Cool down!'); return
        p = pos or getpos()
        s.pipe = pipe
        s.on_exit = on_exit
        s.build_mode = build
        s.tex = 'achievementCrossHair'
        s.btex = 'achievementSuperPunch'
        with bs.get_foreground_host_activity().context:
            M = bs.Material()
            M.add_actions(
                conditions=(('they_are_older_than', 0)),
                actions=(
                    ('modify_part_collision', 'collide', False),
                    ('modify_part_collision', 'physical', False),
                    ('modify_part_collision', 'friction', 0),
                    ('modify_part_collision', 'stiffness', 0),
                    ('modify_part_collision', 'damping', 0)
                )
            )
            n = bs.newnode(
                'prop',
                delegate=s,
                attrs={
                    'mesh': bs.getmesh('tnt'),
                    'color_texture': bs.gettexture(s.tex),
                    'body': 'crate',
                    'reflection': 'soft',
                    'density': 4.0,
                    'reflection_scale': [1.5],
                    'shadow_size': 0.6,
                    'position': p,
                    'gravity_scale': 0,
                    'materials': [M],
                    'is_area_of_interest': True
                }
            )
            bs.timer(0.1, bs.animate(n,'mesh_scale',{0:2,0.1:0.5}).delete)
            SND('laser',p)
            s.safe = None
            def f(): s.safe = s.node.exists()
            bui.apptimer(1,f)
            s.step = s.ostep = 0.008
            l = len(KIDS())
            if l > 15: s.step = s.ostep = 0.008 + l/200
        s.node = n
        s.wait = 0.001
        s.bstep = s.step * (20/8)
        s.mode = 4
        s.llr = s.lud = 0.0
        s.overlay = Overlay(build=s.build_mode)
        binds = {
            'UP_DOWN': lambda a: s.manage(a),
            'LEFT_RIGHT': lambda a: s.manage(a,1),
            'PICK_UP_PRESS': lambda: s.start(2),
            'JUMP_PRESS': lambda: s.start(0),
            'PICK_UP_RELEASE': lambda: s.stop(2),
            'JUMP_RELEASE': lambda: s.stop(0),
        }
        if s.build_mode:
            binds['BOMB_PRESS'] = s.exit
            binds['PUNCH_PRESS'] = s.build
        else:
            binds['BOMB_PRESS'] = s.pick
            binds['PUNCH_PRESS'] = s.boost
            binds['PUNCH_RELEASE'] = lambda: s.boost(0)
        LN(binds)
        STATE(True)
        s.move()
    """Handle events"""
    def handlemessage(s, m):
        if isinstance(m, bs.OutOfBoundsMessage): s.destroy()
    """Destroy"""
    def destroy(s):
        with bs.get_foreground_host_activity().context:
            n = s.node
            MESS(n.position)
            s.mode = 2
            n.delete()
            bs.timer(1, s.reset)
    """Reset input"""
    def reset(s):
        me = getme()
        if not me: return
        me.resetinput()
        with bs.get_foreground_host_activity().context: me.actor.connect_controls_to_player()
    """Manage movement"""
    def manage(s,a,lr=0):
        if lr: s.llr = a; return
        s.lud = a
    """Move"""
    def move(s):
        m = getme(1)
        if (not m) or m._dead: s.destroy(); bs.broadcastmessage('nah2')
        try: p = s.getpos()
        except:
            if STATE():
                STATE(False)
                if bs.get_foreground_host_activity() != bs.get_foreground_host_activity(): return
                bui.apptimer(1,s.fail)
            return
        s.setpos((p[0]+s.llr*s.step,p[1],p[2]-s.lud*s.step))
        s.overlay.up(*p,s.llr,s.lud)
        _ba.set_camera_target(*p)
        bui.apptimer(s.wait,s.move)
    """Start elevating"""
    def start(s,i):
        s.overlay.press(i)
        s.mode = i
        s.loop(i)
    """Keep elevating"""
    def loop(s,i):
        if s.mode != i: return
        try: p = list(s.node.position)
        except: return
        p[1] += s.step if i else -s.step
        s.node.position = tuple(p)
        bui.apptimer(s.wait, lambda: s.loop(i))
    """Stop elevating"""
    def stop(s,i):
        s.overlay.release(i)
        s.mode = 4
    """Get position"""
    def getpos(s):
        return s.node.position
    """Set position"""
    def setpos(s,p):
        s.node.position = p
    """Pick position (single-shot: exits mapper immediately)"""
    def pick(s):
        s.overlay.press(1)
        s.overlay.destroy()
        try: p = s.node.position
        except: return
        with bs.get_foreground_host_activity().context:
            SND('powerup01',p)
            bs.timer(0.1, bs.animate(s.node,'mesh_scale',{0:0.5,0.1:1.5}).delete)
            bs.timer(0.1,lambda: (SPARK(p),s.node.delete()))
        STATE(False)
        s.pipe(p)
        bui.apptimer(1,s.reset)
        s.__class__.last = time.time_ns()
    """Boost"""
    def boost(s,i=1):
        s.step = s.bstep if i else s.ostep
        s.overlay.press(3) if i else s.overlay.release(3)
        if i:
            try: SND('punch01',s.node.position,2)
            except: return
        with bs.get_foreground_host_activity().context:
            try: s.node.color_texture = bs.gettexture(s.btex if i else s.tex)
            except: return
    """Build at current position (repeatable - does not exit)"""
    def build(s):
        s.overlay.press(3)
        try: p = s.node.position
        except: return
        with bs.get_foreground_host_activity().context:
            bs.timer(0.1, lambda: s.overlay.release(3))
            SND('gunCocking',p)
            bs.timer(0.2, bs.animate(s.node,'mesh_scale',{0:0.5,0.1:0.3,0.2:0.5}).delete)
            SPARK(p)
        s.pipe(p)
    """Exit mapper without building (graceful pick-style animation, no shatter)"""
    def exit(s):
        s.overlay.press(1)
        s.overlay.destroy()
        try: p = s.node.position
        except: p = None
        with bs.get_foreground_host_activity().context:
            if p:
                SND('powerup01',p)
                bs.timer(0.1, bs.animate(s.node,'mesh_scale',{0:0.5,0.1:1.5}).delete)
                bs.timer(0.1,lambda: (SPARK(p),s.node.delete()))
            else:
                s.node.delete()
        STATE(False)
        s.__class__.last = time.time_ns()
        if s.on_exit and p: bui.apptimer(1, bs.CallPartial(s.on_exit, p))
        bui.apptimer(1, s.reset)
    """Complain"""
    def complain(s):
        push('You destroyed the mapper!',color=(1,0,0))
        bui.getsound('swip').play()
        s.overlay.destroy()
        None if s.safe else btw('Mapper was destroyed too early.\nFix your positions!')
    """Handle move() losing the node (e.g. quitting mid-map): only
    call pipe() if it's the no-arg pick-style callback - build mode's
    pipe (dispatch) requires a real position and must not be called
    with none."""
    def fail(s):
        if not s.build_mode: s.pipe()
        s.complain()

def NEW(f):
    """New class-based entry decorator"""
    def g(w,b,i,in_source,source_cls,extra):
        if hasm(): RESUME()
        cw(w,transition="out_right")
        cls = icw(
            in_source=b,
            out_source=in_source,
            icon=i,
            title=f.__name__,
            cls=f,
            show_tog=True,
            extra=extra,
            nuke_anim='out_scale' if in_source else 'out_right',
            source_cls=source_cls,
            on_back=lambda:Coolbox(fresh=False, in_source=in_source)
        ).cls
        return cls
    g.__name__ = f.__name__
    g.__cls__ = f
    return g

@NEW
class Spawn:
    """Spawn bots to game"""
    def __init__(s,*a):
        s.args = a
        xoff = 45
        yoff = 45
        bx = 170
        by = 80
        s.mapper = None
        s.can_ran = s.can_blud = True
        ex = a[5]
        # Main buttons
        s.b = pbw(
            p=a[0],
            pos=(58.5,225),
            size=(136,136),
            tex=COLS()
        )
        c = lambda: CharPicker(pipe=s.fresh,source=s.b)
        bw(s.b, oac=c, color=(1,1,1))
        # Text
        s.t = tw(
            p=a[0],
            pos=(100,193),
            h_align='center',
            maxwidth=170
        )
        tw(
            p=a[0],
            pos=(280, 197),
            text='Position',
            h_align='center'
        )
        t = tw(
            p=a[0],
            pos=(455, 197),
            text='Seed',
            h_align='center'
        )
        # Positioning
        s.pos = []
        tx = 38
        for i in range(3):
            e = ['X','Y','Z'][i]
            t = ctw(
                flash=True,
                p=a[0],
                size=(150,45),
                conf=f'pos{i}',
                hint=e+' Position',
                allow='-0.1223456789',
                pos=(230, 315-45*i),
            ).widget
            s.pos.append(t)
        # Position smalls
        for j in range(3):
            i = ['scorch','slash','touchArrowsActions'][j]
            c = [s.dot,s.invert,s.same][j]
            sbw(
                p=a[0],
                pos=(230+50*j, 150),
                size=(43,43),
                icon=bui.gettexture(i),
                icon_tint=-8,
                cons=[None,CONS()[0]][j==2],
                oac=c
            )
        # Position buttons
        for i in range(2):
            bw(
                p=a[0],
                pos=(222,30+60*i),
                icon=bui.gettexture(['touchArrows','cursor'][i]),
                size=(160,55),
                label=['Teleport','Map'][i],
                cons={
                    **CONS()[0],
                    **[{},CONS()[1]][i]
                },
                oac=[s.teleport,s.map][i]
            )
        # Character smalls
        s.csm = {}
        e = COLS()
        for i in range(3):
            f = e[i]
            t = bw(
                p=a[0],
                pos=(60+50*i,150),
                size=(38,38),
            )
            oac = bs.CallPartial(
                ColorPicker,
                chr='char',
                in_source=t,
                on_back=s.fresh,
                id=e[0],
                id2=e[1],
                what=f,
                mode=i,
            )
            c = var(f)
            bw(t, oac=oac, color=c)
            s.csm[f] = t
        # Character buttons
        for i in range(2):
            j = ['Sound','Mesh'][i]
            k = ['audioIcon','menuIcon'][i]
            b = bw(
                p=a[0],
                pos=(48,30+60*i),
                icon=bui.gettexture(k),
                size=(160,55),
                label=j
            )
            bw(b,oac=bs.CallPartial([SoundManager,MeshManager][i],source=b,on_back=s.fresh))
        # Attributes
        s.t2 = ctw(
            p=a[0],
            pos=(408,315),
            size=(150,45),
            allow=True,
            text=var('tchar'),
            conf=('tchar','char'),
            description='Name',
            on_conf=s.fresh
        ).widget
        s.t3 = ctw(
            p=a[0],
            pos=(408,270),
            size=(150,45),
            allow="01223456789",
            text=var('lastid'),
            conf='lastid',
            flash=True,
            hint='Group ID'
        ).widget
        s.seed_t = ctw(
            p=a[0],
            pos=(410,225),
            size=(150,45),
            allow=True,
            conf='seed',
            type='encoding',
            text=var('seed'),
            on_conf=s.apply,
            hint='Seed',
            description='Seed includes name, character, colors, mesh, sounds and custom name. Sharing seed will share all these. Enter'
        )
        for i in range(3):
            j = ['replayIcon','file','logIcon'][i]
            k = [s.randomize,s.copy,s.paste][i]
            sbw(
                p=a[0],
                pos=(410+50*i,150),
                icon=bui.gettexture(j),
                oac=k
            )
        s.sbtn = []
        for i in range(2):
            j = ['Spawn','Actions'][i]
            k = ['downButton','trophy'][i]
            l = [
                s.spawn,
                lambda: ActionManager(source=s.sbtn[1])
            ][i]
            b = bw(
                p=a[0],
                pos=(398,30+60*i),
                icon=bui.gettexture(k),
                size=(160,55),
                label=j,
                oac=l
            )
            s.sbtn.append(b)
        # Resume
        s.fresh()
        [tw(s.pos[i],text=var(f'pos{i}')) for i in range(3)]
        if ex and rnd(ex) != getpos():
            bui.apptimer(0.2, lambda: (s.setpos(ex), gun()))
    """Copy seed"""
    def copy(s):
        bui.clipboard_set_text(var('seed'))
        bui.getsound('ding').play()
        s.seed_t.blink()
        push('Copied seed to clipboard!',color=(0,1,0))
    """Paste seed"""
    def paste(s):
        s.seed_t.set_text(PASTE(),silent=True)
        gun()
        s.seed_t.blink((0,1,1))
        push('Pasted seed from clipboard!',color=(0,1,1))
    """Randomize seed"""
    def randomize(s):
        if not s.can_ran: (setattr(s,'can_blud',False),btw(random.choice(SLOWDOWN())),bui.apptimer(5,bs.CallPartial(setattr,s,'can_blud',True))) if s.can_blud else bui.getsound('block').play(); return
        s.can_ran = False
        s.seed_t.set_text(RANDOM(),silent=True)
        bui.getsound('cashRegister2').play()
        push('Randomized seed!',color=(1,1,0))
        bui.apptimer(0.2,lambda:setattr(s,'can_ran',True))
    """Refresh previews"""
    def fresh(s,i=None,ms=True,silent=True):
        if i is not None: c = cc = NAME()[i]; var('char',c); var('tchar',c); fixall()
        else: c = var('char'); cc = var('tchar')
        mem = COLS()
        n = var(mem[2]) or (1,1,1)
        [tw(t,text=cc,color=n) for t in [s.t,s.t2]]
        char = D()[c]
        tc = var(mem[0]) or (1,1,1)
        tc2 = var(mem[1]) or (1,1,1)
        bw(
            s.b,
            texture=bui.gettexture(char.icon_texture),
            color=(1,1,1),
            tint_texture=bui.gettexture(char.icon_mask_texture),
            tint_color=tc,
            tint2_color=tc2
        )
        [bw(s.csm[z],color=var(z) or (1,1,1)) for z in list(s.csm.keys())]
        # char, tchar, main, hl, name, (*mesh,ctex,ctex2), (*sounds)
        if ms:
            e = SEED(c,cc,tuple(tc),tuple(tc2),tuple(n))
            var('seed',e)
            s.seed_t.set_text(e,silent=silent)
            s.seed_t.blink((1,1,0))
    """Apply seed"""
    def apply(s):
        try: a = CHECK(var('seed'))
        except: push('Found a bad seed in memory'); return
        mem = COLS()
        var('char',a[0])
        var('tchar',a[1])
        var(mem[0],a[2])
        var(mem[1],a[3])
        var(mem[2],a[4])
        arr = list(a[5])
        for i in range(len(DIR('mesh'))): var(f'mesh{i}',arr[i])
        var('ctex',arr[-2])
        var('ctex2',arr[-1])
        [var(f'sound{i}',a[6][i]) for i in range(len(DIR('sounds')))]
        s.fresh(ms=False)
        s.seed_t.blink((1,1,0))
    """Actually spawn"""
    def spawn(s):
        a = bs.get_foreground_host_activity()
        with a.context:
            i = Bot(
                name=var('tchar'),
                name_color=var('Name'),
                mesh=[var(f'mesh{i}') for i in range(len(DIR('mesh')))],
                ctex=var('ctex'),
                ctex2=var('ctex2')
            )
            id = UUID()
            i.uid = id
            a.customdata[id] = i
            s.on_spawn(i)
        return id
    """On spawn"""
    def on_spawn(s, b):
        n = b.node
        pos = getpos()
        bs.getsound('spawn').play(position=pos)
        n.handlemessage('flash')
        n.is_area_of_interest = True
        b.handlemessage(bs.StandMessage(pos,0))
        FOCUS(n,2,1)
        # Apply sounds
        set_sounds(n)
    """Teleport"""
    def teleport(s):
        me = getme(1)
        n = me.node
        FOCUS(n,2,1)
        p = getpos()
        me.handlemessage(bs.StandMessage(p, 0))
        n.handlemessage('flash')
        SND('spawn',p)
    """Draw dot"""
    def dot(s):
        p = getpos()
        LOOK(p, on_found=lambda: push('Located positon!', color=(1,1,1)))
    """Invert position"""
    def invert(s):
        p = getpos()
        s.setpos((-p[0],p[1],-p[2]))
        bui.getsound('deek').play()
        push('Inverted position!',color=(0.5,0.7,1))
    """Same player position"""
    def same(s):
        s.setpos(getme(1).node.position)
        gun()
        push('Used your position!', color=(1,0.7,0.2))
    """Set position"""
    def setpos(s,p):
        p = rnd(p)
        [tw(s.pos[i],text=str(p[i])) for i in range(3)]
    """Map position"""
    def map(s):
        s.mapper = Mapper(pipe=s.pick,pos=getpos())
        None if s.mapper.tired else cw(s.args[0], transition='out_right')
    """Pick position"""
    def pick(s,p=None):
        Coolbox(fb=s.__class__.__name__, fake=True, extra=(p or getpos()))

class shadow:
    """Widget blocker"""
    def __init__(s,p,pos,size,conf):
        s.add = s.pro = 0
        s.conf = conf
        s.size = size
        s.a = bui.imagewidget(
            texture=bui.gettexture('black'),
            parent=p,
            size=size,
            position=pos,
        )
        s.b = bui.scrollwidget(
            parent=p,
            color=var('bg'),
            size=size,
            position=pos,
            border_opacity=0
        )
        s.fresh()
    """Refresh"""
    def fresh(s):
        v = var(s.conf)
        bui.scrollwidget(s.b,size=([s.size,(0,0)][v]))
        s.add = [0.01,-0.01][v]
        def f(j):
            if s.add != j: return
            if s.pro > 0.8: s.pro = 0.8; return
            if s.pro < 0: s.pro = 0; return
            s.pro += j
            bui.imagewidget(s.a,opacity=s.pro)
            bui.apptimer(0.001,bs.CallPartial(f,j))
        f(s.add)

@NEW
class Modify:
    """Modify in-game players and bots"""
    def __init__(s,*a):
        s.a = a
        s.mem = WHAT()
        w = a[0]
        q = bui.scrollwidget(
            parent=w,
            color=var('bg'),
            size=(150,270),
            position=(50,100)
        )
        s.c = cw(
            parent=q,
            size=(150,100),
            background=False
        )
        for i in range(3):
            tw(
                text=['Position','Template','Who?'][i],
                pos=([435,250,75][i],[70,200][i<1]),
                h_align='center',
                size=(100,30),
                p=w
            )
            b = bw(
                p=w,
                pos=(53+50*i,25),
                label=[bui.charstr(bui.SpecialChar.UP_ARROW),'?','&'][i],
                text_scale=[1.2,1.4][i>0],
                size=(40,40),
                **([{},{'cons':CONS()[0]}][i>1])
            )
            o = [
                bs.CallPartial(SpazPicker,source=b,pipe=s.add,note="It's recommended to modify one spaz at a time"),
                bs.CallPartial(ConPipe,source=b,pipe=s.add),
                bs.CallPartial(s.kang,source=b)
            ][i]
            bw(b, oac=o)
        # Char name
        s.ct = tw(
            p=w,
            pos=(274,197),
            maxwidth=150,
            h_align='center',
            text=var('mchar')
        )
        b = bw(
            p=w,
            pos=(227,25),
            icon=bui.gettexture('achievementOutline'),
            label='Load',
            size=(150,40)
        )
        bw(b,oac=bs.CallPartial(SpazPicker,source=b,pipe=s.load,what='Copy who?'))
        bw(
            p=w,
            pos=(410,153),
            icon=bui.gettexture('cursor'),
            label='Map',
            size=(150,40),
            oac=s.map,
            cons=CONS()[1]
        )
        # Position editables
        s.pos = []
        for i in range(3):
            j = ['X','Y','Z'][i]+' Position'
            t = ctw(
                parent=w,
                pos=(410,310-40*i),
                size=(150,40),
                allow='-0.1223456789',
                hint=j,
                conf=f'mpos{i}',
                text=var(f'mpos{i}')
            )
            s.pos.append(t)
        s.cols = lambda: ['New '+i for i in COLS()]
        e = s.cols()
        s.cbs = []
        # Color smalls
        for i in range(3):
            f = e[i]
            t = bw(
                p=a[0],
                pos=(230+50*i,153),
                size=(40,40)
            )
            oac = bs.CallPartial(
                ColorPicker,
                in_source=t,
                on_back=s.fresh,
                id=e[0],
                id2=e[1],
                what=f,
                mode=i,
                chr='mchar'
            )
            bw(t, oac=oac, color=var(f) or (1,1,1))
            s.cbs.append(t)
            b = sbw(
                p=a[0],
                pos=(230+50*i,103),
                icon=bui.gettexture(['audioIcon','menuIcon','textClearButton'][i])
            )
            bw(b,oac=[
                bs.CallPartial(SoundManager,source=b,prf='m',cols=s.cols),
                bs.CallPartial(MeshManager,source=b,prf='m',cols=s.cols),
                bs.CallPartial(s.creset,source=b)
            ][i])
        # Character preview
        b = s.pre = bw(
            p=a[0],
            pos=(235,230),
            color=(1,1,1),
            size=(130,130)
        )
        bw(b,oac=bs.CallPartial(CharPicker,source=s.pre,pipe=s.pipe,cols=s.cols,prf='m'))
        s.targets = []
        s.kids = []
        # Name editable
        s.nm = ctw(
            p=a[0],
            allow=True,
            hint='Name',
            conf='mtchar',
            text=var('mtchar'),
            pos=(410,109),
            size=(150,35)
        )
        s.ct2 = s.nm.widget
        # Healh editable
        s.ht = ctw(
            p=a[0],
            hint='Health',
            description='Health ranges from 1 to 1000. Enter',
            conf='mhp',
            text=var('mhp'),
            pos=(410,72),
            allow='0.1223456789',
            size=(150,35)
        )
        # Modify button
        bw(
            p=a[0],
            oac=s.modify,
            label='Modify',
            icon=bui.gettexture('settingsIcon'),
            pos=(410,25),
            size=(150,40)
        )
        # What button
        b = sbw(
            p=a[0],
            icon=bui.gettexture('menuButton'),
            pos=(102,380),
            size=(40,40)
        )
        bw(b,oac=bs.CallPartial(s.what,b))
        # Attr button
        b = sbw(
            p=a[0],
            icon=bui.gettexture('file'),
            pos=(152,380),
            size=(40,40),
        )
        bw(b,oac=bs.CallPartial(s.attr,b))
        # Shadows
        s.shads = []
        for i in range(7):
            j = [
                (225,200),(225,150),
                (225,100),(275,100),
                (400,195),(405,107),
                (405,70)
            ][i]
            k = [
                (150,170),(150,50),
                (50,50),(50,50),
                (170,160),(160,40),
                (160,40)
            ][i]
            s.shads.append(
                shadow(
                    p=a[0],
                    pos=j,
                    size=k,
                    conf=f'what{i}'
                )
            )
        # Resume
        ex = a[5]
        if ex:
            s.targets = ex[1]
            s.fresh()
            s.setpos(ex[0])
        s.pipe(var('mchar'))
        s.spy()
    """Edit attrs"""
    def attr(s,b):
        a = s.targets
        if not len(a): btw('Select a target first!'); return
        if len(a) > 1: btw('This only works on one target!'); return
        t = a[0]
        NodeManager(source=b,node=t,pipe=s.fresh)
    """Optional modify"""
    def what(s,source=None):
        z = icw(
            in_source=source,
            title='Modify what?',
            back_anim='out_scale',
            size=(300,335),
            show_nuke=False,
            outside_action='back'
        )
        w = z.widget
        for i in range(7):
            j = s.mem[i]
            k = f'what{i}'
            chk(
                text=j,
                value=var(k),
                on_value_change_call=bs.CallPartial(s.opipe,k,i),
                parent=w,
                size=(200,20),
                position=(30,235-35*i)
            )
    """Optional pipe"""
    def opipe(s,k,i,b):
        var(k,b)
        s.shads[i].fresh()
    """Actually modify"""
    def modify(s):
        # node | [0,gid] | [1,tem]
        l = []
        with bs.get_foreground_host_activity().context: mem = KIDS()
        for t in s.targets:
            if isinstance(t,list):
                if t[0]:
                    for i in mem:
                        j = i.source_player
                        l.append(i) if j and j.team.name.evaluate() == t[1] else None
                else: [l.append(i) if getattr(i.getdelegate(object),'group_id',0) == t[1] else None for i in mem]
            else: l.append(t)
        if not len(l):
            btw('No targets found!')
            return
        co = s.cols()
        for n in l:
            [setattr(n,['color','highlight','name_color'][i],var(co[i]) or (1,1,1)) for i in range(3)] if var('what1') else None
            t = s.nm.get_text(); setattr(n,'name',t) if t and var('what5') else None
            t = s.ht.get_text(); [setattr(n.getdelegate(object),'hitpoints',float(t)),setattr(n,'hurt',1-(float(t)/1000))] if t and var('what6') else None
            n.handlemessage(bs.StandMessage(s.getpos(),0)) if var('what4') else None
        nam,spa = NAME(),SPAZ()
        mem = spa[nam.index(var('mchar'))]
        ok = ['color_texture','color_mask_texture']
        ok2 = DIR('mesh'); z = range(len(ok2))
        tex = [var(f'mmesh{i}') for i in z]
        act = bs.get_foreground_host_activity()
        with act.context:
            mem = [bs.gettexture(var('mctex')), bs.gettexture(getattr(mem,ok[1])), mem.style]
            tex = [bs.getmesh(tex[i]) for i in z]
            [[setattr(n,ok[i],mem[i]) for i in range(2)] for n in l] if var('what0') else None
            [[setattr(n,ok2[i],tex[i]) for i in z] for n in l] if var('what3') else None
            [set_sounds(n,prf='m',spa=spa) for n in l] if var(f'what2') else None
            SND('gunCocking',l[0].position)
            # style
            st = mem[2]
            mem = BRUH()
            for n in l:
                ot = n.style
                n.style = st
                if (ot in mem[0] and st not in mem[0]) or st in mem[1]:
                    sp = n.source_player
                    if sp: pass # TODO: recreate player when needed
                    else:
                        b = Bot(NAME()[0],ignore=True)
                        b.uid = UUID()
                        bn = b.node
                        act.customdata[b.uid] = b
                        mem = BAD()
                        for i in dir(bn):
                            if i == 'node': continue
                            if i.startswith('_') or i in mem: continue
                            try: j = getattr(n,i)
                            except AttributeError: continue
                            if callable(j): continue
                            try: setattr(bn,i,j)
                            except RuntimeError: continue
                        p = n.position
                        p = (p[0],p[1]-0.6,p[2])
                        b.handlemessage(bs.StandMessage(p,0))
                        s.targets[s.targets.index(n)] = bn
                        c = Control.__cls__
                        if c.__n__ == n: c.__n__ = bn; c.__in__.ln(b)
                        n.delete()
                n.handlemessage('flash')
        s.fresh(False)
        ding()
    """Kang hold node"""
    def kang(s,source=None):
        n = getme(1).node.hold_node
        if not n or n.getnodetype() != 'spaz': btw('You are not holding a spaz!'); return
        Confirm(
            source=source,
            title='Held player',
            label='Add as target',
            pipe=bs.CallPartial(s.add,n)
        )
    """Confirm reset"""
    def creset(s,source=None):
        Confirm(
            source=source,
            title='Sure?',
            label='Reset template',
            pipe=s.reset
        )
    """Reset"""
    def reset(s):
        o = NAME()[0]
        var('mchar',o)
        [var(c,(1,1,1)) for c in s.cols()]
        [bw(b,color=(1,1,1)) for b in s.cbs]
        tw(s.ct2,color=(1,1,1))
        fixall(o,prf='m')
        s.fresh()
        bui.getsound('swip').play()
    """Load spaz"""
    def load(s,n):
        ui = NTEX(n)
        var('mtchar',n.name)
        c = s.cols()
        var(c[0],ui[0]['tint_color'])
        var(c[1],ui[0]['tint2_color'])
        var(c[2],ui[1])
        [bw(s.cbs[i],color=var(c[i])) for i in range(3)]
        s.pipe(ICONS().index(ui[2]+'Icon'))
        o = n.getdelegate(object)
        s.ht.set_text(str(round(o.hitpoints,1)))
        gun()
    """Character pipe"""
    def pipe(s,i):
        if isinstance(i,str): i = NAME().index(i)
        else:
            ok = NAME()[i]
            var('mchar',ok)
            var('mhp','1000.0')
            fixall(prf='m')
        c = s.cols()
        ui = MK(SPAZ()[i],c[0],c[1])
        tw(s.ct,text=var('mchar'),color=var(c[2]))
        tw(s.ct2,text=var('mtchar'),color=var(c[2]))
        s.ht.set_text('1000.0')
        bw(s.pre,**ui[0])
    """Set position"""
    def setpos(s,p):
        p = rnd(p)
        h = []
        for i in range(3):
            t = s.pos[i]
            o = t.get_text()
            n = str(p[i])
            h.append(t) if o != n else None
            t.set_text(n)
        bui.apptimer(0.2,lambda:([t.blink() for t in h],gun())) if h else None
    """Get position"""
    def getpos(s):
        return rnd(tuple([float(var(f'mpos{i}')) for i in range(3)]))
    """Map"""
    def map(s):
        s.mapper = Mapper(pipe=s.pick,pos=s.getpos())
        None if s.mapper.tired else cw(s.a[0], transition='out_right')
    """Pick"""
    def pick(s,p=None):
        Coolbox(fb=s.__class__.__name__, fake=True, extra=[p or s.getpos(),s.targets])
    """Add target"""
    def add(s,t):
        if t in s.targets: btw('Target already exists!'); return
        s.targets.append(t)
        gun()
        s.fresh(pipe=False)
    """Remove target"""
    def remove(s,n):
        s.targets.remove(n)
        bui.getsound('pop01').play()
        s.fresh()
    """Refresh"""
    def fresh(s,pipe=True):
        a = s.targets
        l = len(a)
        [k.delete() for k in s.kids]
        tex = ALL()
        for i in range(l):
            n = a[i]
            b = not isinstance(n,list)
            if b:
                ui = NTEX(n,tex)
                t = getattr(n,'name','') or f'Target {i+1}'
            else:
                ui = {'color':(1,1,1),'texture':bui.gettexture(['achievementSharingIsCaring','achievementTeamPlayer'][n[0]])},(1,1,1)
                t = n[1]
            k1 = [bw,pbw][b](
                p=s.c,
                pos=(10,i*155+29),
                size=(110,110),
                oac=bs.CallPartial(s.remove,n),
                **ui[0]
            )
            k2 = tw(
                p=s.c,
                pos=(40,i*155-5),
                h_align='center',
                maxwidth=105,
                max_height=40,
                text=t,
                color=ui[1]
            )
            [s.kids.append(k) for k in [k1,k2]]
        cw(s.c, size=(100,l*155))
        v = var('mchar')
        if pipe and v: s.pipe(NAME().index(v))
    """Spy"""
    def spy(s):
        if not s.c.exists() or s.c.transitioning_out: return
        for n in s.targets:
            if isinstance(n,list) or n.exists(): continue
            btw(f'Target no. {s.targets.index(n)+1} is dead!')
            s.remove(n)
        bui.apptimer(0.1,s.spy)

@NEW
class Control:
    """Control anyone"""
    __up__ = False
    __in__ = None
    __n__ = None
    @classmethod
    def spy(c):
        if not c.__up__: return
        i = c.__in__
        n = c.__n__
        m = getme(1)
        if not m or m._dead and i: i.reset(n,True); c.__in__ = None; return
        if not n or not n.exists() or n.getdelegate(object)._dead and i: i.reset(n); c.__in__ = None; return
        bui.apptimer(0.1,c.spy)
    def __init__(s,*a):
        w = s.w = a[0]
        s.n = None
        # Target preview
        s.b = bw(
            p=w,
            color=(1,1,1),
            pos=(63.5,225),
            size=(136,136),
            texture=bui.gettexture('achievementEmpty')
        )
        bw(s.b,oac=s.pick)
        s.t = tw(
            p=w,
            text='Who?',
            maxwidth=170,
            pos=(105,193),
            h_align='center'
        )
        c = [
            (0.4,1,0.4),
            (1,0,0),
            (0.4,1,1),
            (1,1,0.4),
            [(0.3,0.23,0.5),(0.4,0.26,0.6)]
        ]
        bw(
            p=w,
            oac=s.apply,
            label='Apply',
            icon=bui.gettexture('settingsIcon'),
            pos=(410,15),
            size=(150,40)
        )
        b = bw(
            p=w,
            label='Hold',
            icon=bui.gettexture('achievementOutline'),
            pos=(235,15),
            size=(150,40)
        )
        bw(b,oac=bs.CallPartial(s.hold,b))
        bw(
            p=w,
            label='Right arm',
            icon=bui.gettexture('rightButton'),
            pos=(235,155),
            size=(150,40),
            oac=bs.CallPartial(s.yay,'_r'),
            repeat=True
        )
        bw(
            p=w,
            label='Left arm',
            icon=bui.gettexture('leftButton'),
            pos=(235,108),
            size=(150,40),
            oac=bs.CallPartial(s.yay,'_l'),
            repeat=True
        )
        bw(
            p=w,
            label='Both arms',
            icon=bui.gettexture('upButton'),
            pos=(235,60),
            size=(150,40),
            oac=s.yay,
            repeat=True
        )
        cls = s.__class__
        cls.__in__ = s
        b = cls.__up__
        s.sb = bw(
            p=w,
            oac=s.start,
            pos=(58.5,15),
            size=(150,40),
            cons=CONS()[0]
        )
        s.start(dry=True)
        for i in range(5):
            j = ['Jump','Bomb','PickUp','Punch','Move'][i]
            y = 175-30*i
            x = 410
            l = c[i]
            t = tw(
                p=w,
                text=j,
                pos=(x+35,y)
            )
            if i<4:
                bui.imagewidget(
                    parent=w,
                    size=(30,30),
                    color=c[i],
                    position=(x+4,y),
                    texture=bui.gettexture(f'button{j}')
                )
            else:
                [bui.imagewidget(
                    parent=w,
                    color=l[k],
                    texture=bui.gettexture('nub'),
                    size=[(35,35),(20,20)][k],
                    position=(x+1+7*k,y-2+7*k)
                ) for k in [0,1]]
                l = l[1]
            tw(t,color=l)
            v = f'cont{i}'
            b = var(v)
            bb = sbw(
                parent=w,
                textcolor=l,
                size=(20,20),
                text_scale=0.7,
                position=(x+115,y+5),
                label=['',bui.charstr(bui.SpecialChar.DPAD_CENTER_BUTTON)][b],
            )
            bw(bb,oac=bs.CallPartial(s.check,bb,i,b))
        for i in range(4):
            j = [
                'Block him',
                'Close this',
                'Invincible',
                'Block you'
            ][i]
            v = f'cconf{i}'
            chk(
                parent=s.w,
                text='',
                position=(63.5,155-33*i),
                value=var(v),
                size=(170,30),
                on_value_change_call=bs.CallPartial(s.cconf,v)
            )
            tw(
                p=s.w,
                text=j,
                maxwidth=95,
                position=(100.5,158-33*i),
            )
        for i in range(4):
            j = [460,505,460,415][i]
            k = [218,265,312,265][i]
            l = ['Jump','Bomb','PickUp','Punch'][i]
            sbw(
                p=s.w,
                pos=(j,k),
                color=c[i],
                size=(50,50),
                oac=bs.CallPartial(s.key,i),
                texture=bui.gettexture('button'+l)
            )
        s.mbs = []
        s.mb = None
        s.la = 0
        h = '_ARROW'
        for i in range(3):
            for j in range(3):
                ij = i*3+j
                k = [
                    '','DOWN'+h,'',
                    'LEFT'+h,'DPAD_CENTER_BUTTON','RIGHT'+h,
                    '','UP'+h,''
                ][ij]
                b = bw(
                    p=s.w,
                    label=bui.charstr(getattr(bui.SpecialChar,k)) if k else k,
                    repeat=True,
                    size=(40,40),
                    position=(240+50*j,225+50*i)
                )
                bw(b,oac=bs.CallPartial(s.move,i,j,b))
                s.mbs.append(b)
        for i in range(4):
            j = [
                (237.5,215),
                (360,190),
                (385,312.5),
                (262.5,337.5)
            ][i]
            tw(
                parent=s.w,
                position=j,
                text=bui.charstr(bui.SpecialChar.LEFT_ARROW),
                rotate=45+90*i
            )
        tw(
            text='Long press to run',
            color=(0.2,0.2,0.2),
            position=(235,195),
            parent=s.w,
            scale=0.71
        )
        n = cls.__n__
        s.fresh(n,False) if n else n
    """Celebrate"""
    def yay(s,pr=''):
        if s.nah(): return
        s.n.handlemessage('celebrate'+pr,100)
    """Hold"""
    def hold(s,b):
        if s.nah(): return
        if s.n.hold_node: btw("Target's already holding something!"); return
        NodePicker(pipe=lambda n: (bs.broadcastmessage(random.choice(HOLDSELF())) if s.n == n else None,bui.apptimer(0.2,lambda:(bs.broadcastmessage('Now resume the game to see changes') if pause() else None) if s.holds(n) else None)),source=b,allow='3D')
    """Safe hold"""
    def holds(s,w):
        if w.getnodetype() in HOLDABLE():
            s.n.hold_node = w
            return True
        btw("You can't hold that!")
    """Move target"""
    def move(s,i,j,b):
        if s.nah(): return
        o = s.n.getdelegate(object)
        if s.mb != b:
            s.mb = b
            bw(b,color=(0,1,0)) if i*3+j != 4 else None
            [bw(_,color=var('bg')) for _ in s.mbs if _ != b]
        else:
            with bs.get_foreground_host_activity().context:
                o.on_run(1)
                s.ls = time.time_ns()
                bs.timer(0.1,s.stop)
        v = 32767; a = [-v,0,v]
        x,y = a[j],a[i]
        o.on_move_left_right(x)
        o.on_move_up_down(y)
    """Stop running"""
    def stop(s):
        i = time.time_ns() - s.ls
        if i < 0.8*10**8: return
        else: s.n.getdelegate(object).on_run(0)
    """Back gracefully"""
    def back(s):
        if s.mb and s.mbs.index(s.mb) != 4: s.move(1,1,s.mbs[4])
    """Control config"""
    def cconf(s,v,b):
        var(v,b)
        if s.__class__.__up__ and getattr(s,'tcconf',True):
            s.tcconf = False
            bs.broadcastmessage('Restart control to apply changes')
            bui.apptimer(5,bs.CallPartial(setattr,s,'tcconf',True))
    """Send key"""
    def key(s,i):
        if s.nah(): return
        with bs.get_foreground_host_activity().context: [getattr(s.n.getdelegate(object),f"on_{['jump','bomb','pickup','punch'][i]}_{['press','release'][j]}")() for j in [0,1]]
    """Custom check"""
    def check(s,bb,i,b):
        b = not b
        var(f'cont{i}',b)
        bw(bb,label=['',bui.charstr(bui.SpecialChar.DPAD_CENTER_BUTTON)][b],oac=bs.CallPartial(s.check,bb,i,b))
        bui.getsound('deek').play()
    """Conditional CharPicker"""
    def pick(s):
        SpazPicker(source=s.b,pipe=s.fresh,deny=[s.n],deny_msg="Already picked!")
    """Verify"""
    def nah(s):
        if s.n is None: btw('No target selected!'); return 1
        elif (getattr(s.n,'exists',lambda:False)() and s.n.getdelegate(object)._dead) or (not s.n.exists()): btw('Selected target is dead!'); return 1
    """Apply inputs"""
    def apply(s,n=None,l=None):
        if not n:
            if s.nah(): return
            p = s.n.source_player
            if not p: btw("Not an actual player!"); return
            n = s.n
        else: p = n.source_player
        o = n.getdelegate(object)
        p.resetinput()
        l = l or [var(f'cont{i}') for i in range(5)]
        p.customdata['cont'] = (l,n)
        d = {'RUN': o.on_run}
        z = lambda a,i=0: getattr(o,f"on_{a}_{['press','release'][i]}")
        d.update({
            'UP_DOWN': o.on_move_up_down,
            'LEFT_RIGHT': o.on_move_left_right
        }) if l[4] else None
        d.update({
            'PICK_UP_PRESS': z('pickup'),
            'PICK_UP_RELEASE': z('pickup',1)
        }) if l[2] else None
        d.update({
            'JUMP_PRESS': z('jump'),
            'JUMP_RELEASE': z('jump',1)
        }) if l[0] else None
        d.update({
            'BOMB_PRESS': z('bomb'),
            'BOMB_RELEASE': z('bomb',1)
        }) if l[1] else None
        d.update({
            'PUNCH_PRESS': z('punch'),
            'PUNCH_RELEASE': z('punch',1)
        }) if l[3] else None
        with bs.get_foreground_host_activity().context: LN(d,p)
        ding()
        push('Applied controls!',color=(0,1,0))
        n.handlemessage('flash')
    """Start control"""
    def start(s,dry=False,shut=False,tran=False,hm=False):
        if not dry and s.nah(): return
        me = getme(1).node
        c = s.__class__
        if s.n == me and not shut:
            bui.getsound('block').play()
            if not getattr(s,'lmao1',True): return
            s.lmao1 = False
            bs.broadcastmessage(random.choice(["Now that's some self control lmao","Trying to control yourself?","Anyone but that.","But this is YOU!"]))
            bui.apptimer(5,bs.CallPartial(setattr,s,'lmao1',True))
            return
        b = s.__class__.__up__
        if not dry: s.__class__.__up__ = b = not b
        bw(s.sb,label=['Start','Stop'][b],icon=bui.gettexture(f"ouya{['O','A'][b]}Button"))
        if dry: return
        if not b: s.reset(tran=tran,hm=hm); return
        s.__class__.__n__ = s.n
        o = s.n.getdelegate(object)
        cw(s.w,transition='out_right') if var('cconf1') else None
        z = lambda a,i=0: getattr(o,f"on_{a}_{['press','release'][i]}")
        gun()
        bs.broadcastmessage(f"Now {s.n.name or 'This spaz'} moves "+['like','instead of'][var('cconf3')]+' you!', color=(0,1,0))
        s.__class__.spy()
        if var('cconf2'): me.invincible = True
        with bs.get_foreground_host_activity().context:
            s.ln(o)
            s.n.handlemessage('flash')
            FOCUS(s.n,2,1)
            sp = s.n.source_player
            if sp:
                if var('cconf0'): sp.resetinput()
                return
            Bubble(
                node=s.n,
                time=4,
                text=bui.charstr(getattr(bui.SpecialChar,random.choice([
                    'DPAD_CENTER_BUTTON',
                    'LOGO_FLAT'
                ])))+' '+random.choice(CONSTR()),
                color=s.n.color
            )
            p = s.n.position
            bs.timer(1,lambda:(o.on_jump_press(),o.on_jump_release()) if math.dist(p,o.node.position) < 0.2 else None)
    """Link"""
    def ln(s,o):
        m = getme(1)
        v = var('cconf3')
        a = lambda i: lambda e=None: (getattr(o,i)(*([e] if e is not None else [])),getattr(m,i)(*([e] if e is not None else [])) if not v else None)
        LN({
            'UP_DOWN': a('on_move_up_down'),
            'LEFT_RIGHT': a('on_move_left_right'),
            'PICK_UP_PRESS': a('on_pickup_press'),
            'PICK_UP_RELEASE': a('on_pickup_release'),
            'JUMP_PRESS': a('on_jump_press'),
            'JUMP_RELEASE': a('on_jump_release'),
            'BOMB_PRESS': a('on_bomb_press'),
            'BOMB_RELEASE': a('on_bomb_release'),
            'PUNCH_PRESS': a('on_punch_press'),
            'PUNCH_RELEASE': a('on_punch_release'),
            'RUN': a('on_run')
        })
    """Reset"""
    def reset(s,n=None,host=False,tran=False,hm=False):
        b = n is not None
        me = getme()
        c = s.__class__
        o = n.getdelegate(object) if b else None
        if b and n != s.__class__.__n__: return # denied
        if b and o._dead: bs.broadcastmessage('Target died!'+random.choice([' LOL','','','']),color=(1,1,0))
        elif b and host: btw('You died!'); me.resetinput(); o.on_move_up_down(0.0); o.on_move_left_right(0.0)
        else: push(['Stopped','Transferred'][tran and hm]+' control!',color=(1,1,0)); tran if tran else ding()
        sp = c.__n__.source_player
        if sp:
            l = sp.customdata.get('cont',0)
            if l and l[1].exists(): s.apply(n,l[0])
            else: sp.actor.connect_controls_to_player()
        c.__n__ = None
        c.__up__ = False
        cw(s.w,transition='out_right') if s.w.exists() and not s.w.transitioning_out and b and o._dead else None
        if host: return # host died
        me.resetinput()
        with bs.get_foreground_host_activity().context: me.actor.connect_controls_to_player()
        h = me.actor.node
        h.handlemessage('flash')
        if h.invincible: h.invincible = False
    """Refresh"""
    def fresh(s,n,b=True):
        s.move(1,1,s.mbs[4]) if s.n else None
        s.n = n
        ui = NTEX(n)
        tw(s.t,text=getattr(n,'name','') or 'Unnamed',color=ui[1])
        bw(s.b,**ui[0],mask_texture=bui.gettexture('characterIconMask'))
        if not b: return
        gun()
        c = s.__class__
        if c.__up__:
            bub = Bubble.__mem__.get(c.__n__,0)
            hm = n != getme(1).node
            s.start(shut=True,tran=True,hm=hm)
            s.start() if hm else None
            if not bub: return
            with bs.get_foreground_host_activity().context: bub.delete(force=True)

@NEW
class Effect:
    """Apply an effect to anyone"""
    MEM = {}
    def __init__(s,w,*a):
        s.n = None
        s.kids = []
        s.b = bw(
            p=w,
            color=(1,1,1),
            pos=(60,225),
            size=(136,136),
            texture=bui.gettexture('achievementEmpty')
        )
        bw(s.b,oac=s.pick)
        s.t = tw(
            p=w,
            text='Who?',
            maxwidth=170,
            pos=(101.5,193),
            h_align='center'
        )
        s1 = bui.scrollwidget(
            parent=w,
            position=(52, 52),
            color=var('bg'),
            size=(150.0, 140.0)
        )
        s.p1 = cw(
            parent=s1,
            background=False,
            size=(150,0)
        )
        s2 = bui.scrollwidget(
            color=var('bg'),
            parent=w,
            position=(231.1, 52),
            size=(150.0, 320.0)
        )
        res = s.res()
        p2 = cw(
            parent=s2,
            background=False,
            size=(150,155*len(res))
        )
        tw(
            parent=w,
            position=(75.0, 22.4),
            size=(100, 30),
            text='Active',
            h_align='center'
        )
        tw(
            parent=w,
            position=(255.0, 22.4),
            size=(100, 30),
            text='What',
            h_align='center'
        )
        tw(
            parent=w,
            position=(425.0, 22.4),
            size=(100, 30),
            text='More',
            h_align='center'
        )
        s.more = []
        r1 = s.res(1)
        for y in range(5):
            for x in range(2):
                _ = y*2+x
                i,j = r1[_]
                f = bs.CallPartial(s.pup,j) if _ else lambda: Collector(source=s.more[0],pipe=lambda t: wga(lambda: Bubble(s.n,t,s.n.color)))
                s.more.append(bw(
                    size=(60,60),
                    position=(405+x*70,315-65*y),
                    parent=w,
                    icon=bui.gettexture(i),
                    oac=bs.CallPartial(s.nah,f),
                    iconscale=1.2
                ))
        for _,g in enumerate(res):
            t,x = g
            tw(
                parent=p2,
                maxwidth=140,
                position=(40,0+_*155),
                text=t,
                max_height=30,
                h_align='center'
            )
            bw(
                parent=p2,
                size=(90,90),
                position=(22,18+20+_*155),
                texture=bui.gettexture(x),
                color=(1,1,1),
                oac=bs.CallPartial(s.nah,bs.CallPartial(s.add,_))
            )
    def pup(s,j):
        s.n.handlemessage(bs.PowerupMessage(j))
        bui.getsound('powerup01').play()
    def add(s,_):
        if _ in s.MEM.get(s.n,[]): btw('Already applied!'); return
        bui.getsound('powerup01').play()
        s.man(_)
        s.check()
    def man(s,_,a=True):
        e = lambda z:_==z
        o = s.MEM.get(s.n,[])
        [o.remove,o.append][a](_)
        s.MEM[s.n] = o
        if e(0):
            v = [1.2,15][a]
            t = '_punch_power_scale'
            b = DLG(s.n)
            h = bs.CallPartial(setattr,b,t,v)
            h()
            if not a: return
            g = bs.CallPartial(getattr,b,t)
            f = lambda: s.n and (_ in s.MEM[s.n]) and (h() if g() != v else 0,bs.timer(0.2,f))
            with bs.get_foreground_host_activity().context: f()
        if e(1):
            v = [400,0][a]
            t = '_punch_cooldown'
            b = DLG(s.n)
            h = bs.CallPartial(setattr,b,t,v)
            h()
            if not a: return
            g = bs.CallPartial(getattr,b,t)
            f = lambda: s.n and (_ in s.MEM[s.n]) and (h() if g() != v else 0,bs.timer(0.2,f))
            with bs.get_foreground_host_activity().context: f()
        if e(2): s.set(hockey=a)
        if e(3):
            if not a: return
            f = lambda: s.n and (_ in s.MEM.get(s.n,[])) and (s.n.handlemessage('knockout',500),bs.timer(0.4,f))
            with bs.get_foreground_host_activity().context: f(); Bubble(time=4,node=s.n,color=s.n.color,text=random.choice(ZZZ()))
        if e(4): s.set(invincible=a)
        if e(5): s.set(shattered=a)
        if e(6): s.set(frozen=a)
        s.n.handlemessage('flash')
    def rem(s,i):
        if not i in s.MEM.get(s.n,[]): btw('Effect isn\'t applied... hmm?'); return
        bui.getsound('pop01').play()
        s.man(i,False)
        s.check()
    def check(s):
        [_.delete() for _ in s.kids]; s.kids.clear()
        res = [_[0] for _ in s.res()]
        mem = s.MEM.get(s.n,[])
        for _,i in enumerate(mem):
            t = tw(
                parent=s.p1,
                size=(150,30),
                click_activate=True,
                selectable=True,
                position=(0,_*35),
                text=res[i],
                on_activate_call=bs.CallPartial(s.nah,bs.CallPartial(s.rem,i))
            )
            s.kids.append(t)
        cw(s.p1,size=(150,len(mem)*35))
    def res(s,i=0):
        return [[
            ('Super punch','achievementSuperPunch'),
            ('Fast punch','nextLevelIcon'),
            ('Super speed','achievementGotTheMoves'),
            ('Good night','achievementOffYouGo'),
            ('Invincible','star'),
            ('Shatter','achievementCrossHair'),
            ('Freeze','ouyaUButton')
        ],[
            ('achievementOutline','none'),
            ('powerupHealth','health'),
            ('powerupCurse','curse'),
            ('powerupStickyBombs','sticky_bombs'),
            ('powerupImpactBombs','impact_bombs'),
            ('powerupIceBombs','ice_bombs'),
            ('powerupBomb','triple_bombs'),
            ('powerupLandMines','land_mines'),
            ('powerupShield','shield'),
            ('powerupPunch','punch')
        ]][i]
    def sleep(s):
        k = lambda: s.n and (s.n.handlemessage('knockout',1000),bs.timer(0.9,k))
        with bs.get_foreground_host_activity().context: k()
    def set(s,obj=False,**k):
        n = s.n.getdelegate(object) if obj else s.n
        [setattr(n,a,v) for a,v in k.items()]
    def pick(s):
        SpazPicker(source=s.b,pipe=s.fresh,deny=[s.n],deny_msg="Already picked!")
    def fresh(s,n):
        gun()
        s.n = n
        ui = NTEX(n)
        tw(s.t,text=getattr(n,'name',0) or 'Unnamed',color=ui[1])
        bw(s.b,**ui[0],mask_texture=bui.gettexture('characterIconMask'))
        s.check()
    def nah(s,f):
        if s.n is None: btw('No target selected!'); return 1
        elif (getattr(s.n,'exists',lambda:False)() and getattr(s.n.getdelegate(object),'_dead',True)) or (not s.n.exists()): btw('Selected node is dead!\nPick a new target'); return 1
        f(); return True

@NEW
class Deploy:
    """Obtain any object or powerup in game"""
    @classmethod
    def get(c):
        with bs.get_foreground_host_activity().context:
            f = bs_bomb.BombFactory.get()
            o = bs_gameutils.SharedObjects.get()
        return {
            ('Safe Bomb','spinner0'):[
                'bomb',
                {
                    'mesh':f.bomb_mesh,
                    'color_texture':f.regular_tex,
                    'shadow_size':0.5,
                    'materials':[
                        o.object_material,
                        o.footing_material,
                        f.bomb_material
                    ]
                }
            ],
            ('Safe TNT','tnt'):[
                'prop',
                {
                    'mesh':f.tnt_mesh,
                    'body':'crate',
                    'color_texture':f.tnt_tex,
                    'shadow_size':0.5,
                    'materials':[
                        o.object_material,
                        o.footing_material,
                        f.bomb_material
                    ]
                }
            ],
            ('Light Ball','nub'):[
                'prop',
                {
                    'mesh':f.bomb_mesh,
                    'body':'sphere',
                    'color_texture':GA(lambda:bs.gettexture('white')),
                    'shadow_size':0.6,
                    'gravity_scale':0.5,
                    'materials':[
                        o.object_material,
                        o.footing_material,
                        f.bomb_material
                    ]
                }
            ],
            ('Gold Coin','coin'):[
                'prop',
                {
                    'mesh':GA(lambda:bs.getmesh('puck')),
                    'body':'puck',
                    'color_texture':GA(lambda:bs.gettexture('tokens4')),
                    'reflection':'sharper',
                    'reflection_scale':[5,5,5],
                    'materials':[
                        o.object_material,
                        o.footing_material
                    ]
                }
            ]
        }
    def __init__(s,w,*a):
        s.w = w
        s.data = {'attrs':{}}
        s.atkids = []
        s.edbs = []
        s.pos = []
        ex = a[4]
        prp1 = bui.scrollwidget(
            parent=w,
            position=(58.8, 59.5),
            color=var('bg'),
            size=(150.0, 310.0)
        )
        mem = s.__class__.get()
        py = 150*len(mem)
        s.prp = cw(
            parent=prp1,
            background=False,
            size=(150,py)
        )
        s.vc = ex[2] if ex else 0
        for _,g in enumerate(mem.items()):
            tx,at = g
            y = py-150-150*_
            b = bw(
                parent=s.prp,
                size=(100,100),
                texture=bui.gettexture(tx[1]),
                position=(15,y+50),
                color=(1,1,1),
                oac=bs.CallPartial(s.load,at,_)
            )
            t = tw(
                parent=s.prp,
                maxwidth=140,
                text=tx[0],
                position=(40,y+15),
                h_align='center',
                v_align='center'
            )
            if _ == s.vc: cw(s.prp,visible_child=t)
        tw(
            parent=w,
            position=(82.0, 26.7),
            size=(100, 30),
            text='Preset',
            h_align='center'
        )
        v = 'dplprop'
        e = var(v)
        s.propt = ctw(
            parent=w,
            position=(299.4, 335.2),
            size=(260.0, 30),
            text=e,
            conf=v,
            v_align='center',
            allow=True,
            hint='prop',
            blank=True
        )
        v = 'dplname'
        e = var(v)
        s.namet = ctw(
            parent=w,
            position=(309.4, 260.2),
            size=(250.0, 30),
            allow=True,
            hint='None',
            text=e,
            conf=v,
            blank=True
        )
        tw(
            parent=w,
            position=(220.4, 298.9),
            size=(100, 30),
            text='owner ='
        )
        s.ownert = tw(
            parent=w,
            position=(316.4, 298.9),
            size=(150.0, 30),
            text='None',
            color=(0.5,0.5,0.5),
            maxwidth=150
        )
        tw(
            parent=w,
            position=(220.4, 261.9),
            size=(90.0, 30),
            text='name ='
        )
        tw(
            parent=w,
            position=(220.4, 224.9),
            size=(70.0, 30),
            text='pos ='
        )
        tw(
            parent=w,
            position=(220.4, 335.9),
            size=(70.0, 30),
            text='type ='
        )
        s.pickb = bw(
            size=(82.0, 20.0),
            position=(477.3, 302.1),
            label='Pick',
            parent=w,
            oac=s.pick
        )
        for _ in range(3):
            h = ['X','Y','Z'][_]
            s.pos.append(ctw(
                parent=w,
                position=(293.3, 222.9-37*_),
                size=(270.0, 30),
                hint=h,
                conf=f'dpl{_}',
                allow='-0.1223456789',
                text=var(f'dpl{_}')
            ))
        bw(
            size=(60.0, 60.0),
            position=(217.1, 153.8),
            parent=w,
            icon=bui.gettexture('cursor'),
            iconscale=1.2,
            oac=s.map
        )
        atp1 = bui.scrollwidget(
            parent=w,
            position=(218.9, 60.2),
            color=var('bg'),
            size=(260.0, 80.0)
        )
        s.atp = cw(
            parent=atp1,
            background=False
        )
        bw(
            size=(70.0, 82.0),
            position=(492.4, 59.6),
            parent=w,
            iconscale=1.55,
            icon=bui.gettexture('downButton'),
            oac=s.make
        )
        tw(
            parent=w,
            position=(298.3, 29.4),
            size=(100, 30),
            text='Attrs',
            h_align='center'
        )
        tw(
            parent=w,
            position=(477, 29.4),
            size=(100, 30),
            text='Make',
            h_align='center'
        )
        # finally
        s.fattr()
        s.chk(ex)
    def load(s,at,vc):
        s.vc = vc
        ty,da = at
        s.propt.set_text(ty)
        s.data['attrs'] = da
        s.fattr()
    def chk(s,ex):
        if not ex: return
        p,da,_ = ex
        if p and p != s.getpos():
            bui.apptimer(0.2, lambda:s.setpos(p))
        s.data = da
        s.fattr()
        s.fresh()
    def make(s):
        p = s.getpos()
        d = s.data
        a = d['attrs'].copy()
        if not a:
            btw('No attrs!')
            return
        a.update({'position':p})
        with bs.get_foreground_host_activity().context:
            try:
                bs.newnode(
                    type=var('dplprop') or 'prop',
                    owner=d.get('owner',None),
                    name=var('dplname'),
                    attrs=a
                )
            except Exception as e:
                err(str(e))
        SND('spawn',p)
    def _fattr(s,t):
        a,v = t
        if not a:
            bs.broadcastmessage('Cancelled!')
            return
        if a in s.data['attrs']:
            bs.broadcastmessage('Updated existing attribute!')
        s.data['attrs'][a] = v
        s.fattr()
    def fattr(s):
        i = len(s.data['attrs'])
        cw(s.atp,size=(260,i*70+35))
        [_.delete() for _ in s.atkids]
        s.atkids.clear()
        s.edbs.clear()
        # attrs
        for _,g in enumerate(s.data['attrs'].items()):
            a,v = g
            y = 35+_*70
            s.atkids.append(tw(
                parent=s.atp,
                text=a,
                v_align='center',
                maxwidth=210,
                position=(5,y+35)
            ))
            dv = f"'{v}'" if isinstance(v,str) else str(v)
            edb = bw(
                position=(200,y+35),
                label='!',
                parent=s.atp,
                oac=bs.CallPartial(s.eattr,a,dv,old=(a,v),_=_),
                size=(30,30)
            )
            s.atkids.append(edb)
            s.edbs.append(edb)
            s.atkids.append(tw(
                parent=s.atp,
                text=dv,
                v_align='center',
                maxwidth=190,
                position=(5,y+4),
                color=(0.7,0.7,0.7)
            ))
            s.atkids.append(bw(
                position=(200,y+4),
                size=(30,26),
                label='-',
                parent=s.atp,
                oac=bs.CallPartial(s.dattr,a)
            ))
        s.atkids.append(tw(
            text='Add an attribute',
            position=(5,0),
            parent=s.atp,
            v_align='center',
            maxwidth=210
        ))
        s.aattrb = bw(
            label='+',
            position=(200,0),
            size=(30,30),
            parent=s.atp,
            oac=s.aattr
        )
        s.atkids.append(s.aattrb)
    def dattr(s,a):
        s.data['attrs'].pop(a)
        bui.getsound('pop01').play()
        s.fattr()
    def eattr(s,a,dv,old,_):
        Collector(
            source=s.edbs[_],
            first=dv,
            double=a,
            two=True,
            title='Edit',
            pipe=bs.CallPartial(s._eattr,old=old),
            raw=True
        )
    def _eattr(s,t,old):
        a,v = t
        s.data['attrs'].pop(old[0])
        s.data['attrs'][a or old[0]] = v if v != "" else old[1]
        s.fattr()
    def aattr(s):
        Collector(
            source=s.aattrb,
            first='Value',
            double='Attribute',
            two=True,
            title='Add',
            pipe=s._fattr,
            raw=True
        )
    def pick(s):
        NodePicker(
            source=s.pickb,
            pipe=s.fresh,
            allow='3D'
        )
    def fresh(s,n=None):
        if n: s.data['owner'] = n
        else: n = s.data.get('owner',None)
        if not n: return
        t = str(n)[1:][:-1]
        t = t[t.find('Node ')+5:t.find("'")]+n.getnodetype()
        tw(s.ownert,text=t,color=(1,1,1))
    def map(s):
        s.mapper = Mapper(pipe=s.mup,pos=s.getpos())
        None if s.mapper.tired else cw(s.w,transition='out_right')
    def mup(s,p=None):
        Coolbox(fb=s.__class__.__name__, fake=True, extra=(p or s.getpos(),s.data,s.vc))
    def getpos(s):
        return rnd(tuple([float(var(f'dpl{i}')) for i in range(3)]))
    def setpos(s,p):
        p = rnd(p)
        h = []
        for i in range(3):
            t = s.pos[i]
            o = t.get_text()
            n = str(p[i])
            h.append(t) if o != n else None
            t.set_text(n)
        bui.apptimer(0.2,lambda:([t.blink() for t in h],gun())) if h else None

@NEW
class Listen:
    """Music player and manager"""

    def __init__(s, *a):
        w = s.w = a[0]
        s.sl = None

        s.m_types = sorted([m for m in dir(bs.MusicType) if not m.startswith('_') and m.isupper()])
        s.M_NAME = [" ".join(word.capitalize() for word in m.split("_")) for m in s.m_types]

        s.tex_map = {
            "CHAR_SELECT": "neoSpazIcon", "CHOSEN_ONE": "achievementSuperPunch",
            "EPIC": "tipTopPreview", "EPIC_RACE": "bigGPreview", "FLAG_CATCHER": "bridgitPreview",
            "FLYING": "alwaysLandPreview", "FOOTBALL": "achievementFootballVictory",
            "FORWARD_MARCH": "cragCastlePreview", "GRAND_ROMP": "achievementFlawlessVictory",
            "HOCKEY": "hockeyStadiumPreview", "KEEP_AWAY": "thePadPreview",
            "MARCHING": "achievementRunaround", "MENU": "logo",
            "ONSLAUGHT": "doomShroomPreview", "RACE": "lakeFrigidPreview",
            "RUN_AWAY": "monkeyFacePreview", "SCARY": "powerupCurse",
            "SCORES": "achievementFootballShutout", "SPORTS": "footballStadiumPreview",
            "SURVIVAL": "rampagePreview", "TO_THE_DEATH": "achievementOnslaught",
            "VICTORY": "achievementMedalLarge"
        }

        sv = bui.scrollwidget(
            parent=w,
            color=var('bg'),
            position=(40, 50),
            size=(250, 320)
        )

        count = len(s.M_NAME)
        ss = max(320, count * 35)
        s.cv = cw(
            parent=sv,
            background=False,
            size=(230, ss)
        )

        s.texts = []
        for i in range(count):
            p_y = ss - 35 - (i * 35)
            t = tw(
                p=s.cv,
                text=s.M_NAME[i],
                pos=(10, p_y),
                size=(210, 30),
                maxwidth=200,
                v_align='center',
                selectable=True,
                click_activate=True,
                on_activate_call=bs.CallPartial(s.select, i)
            )
            s.texts.append(t)

        c_x = 440

        s.img = bui.imagewidget(
            parent=w,
            position=(c_x - 60, 220),
            size=(120, 120),
            texture=bui.gettexture('audioIcon'),
            mask_texture=bui.gettexture('characterIconMask'),
            color=(1, 1, 1)
        )

        s.t_name = tw(
            p=w,
            pos=(c_x - 100, 180),
            size=(200, 30),
            text='Select a Track',
            h_align='center',
            v_align='center',
            maxwidth=200,
            color=var('t') or (1, 1, 1),
            scale=1.2
        )

        s.t_desc = tw(
            p=w,
            pos=(c_x - 100, 150),
            size=(200, 30),
            text='...',
            h_align='center',
            v_align='center',
            maxwidth=200,
            color=(0.5, 0.5, 0.5),
            scale=0.8
        )

        s.b_play = bw(
            p=w,
            pos=(c_x - 110, 80),
            size=(100, 45),
            label='Play',
            icon=bui.gettexture('startButton'),
            oac=s.play
        )

        s.b_def = bw(
            p=w,
            pos=(c_x + 10, 80),
            size=(100, 45),
            label='Default',
            icon=bui.gettexture('replayIcon'),
            oac=s.play_def
        )

        tw(
            p=w,
            pos=(c_x - 125, 40),
            size=(250, 30),
            text='* Non-hosts will hear tracks locally.',
            h_align='center',
            v_align='center',
            maxwidth=250,
            color=(1, 1, 1, 0.3),
            scale=0.6
        )

        if count > 0:
            s.select(0)

    def select(s, i):
        if s.sl != i and s.sl is not None:
            bui.getsound('tap').play()
        s.sl = i

        for idx, t in enumerate(s.texts):
            tw(t, color=(0, 1, 0) if idx == i else var('t') or (1, 1, 1))

        tw(s.t_name, text=s.M_NAME[i])
        m_val = s.m_types[i]
        tw(s.t_desc, text=f"MusicType.{m_val}")

        tex_name = s.tex_map.get(m_val, 'audioIcon')
        try:
            tex = bui.gettexture(tex_name)
        except:
            tex = bui.gettexture('audioIcon')
        bui.imagewidget(s.img, texture=tex)

    def play(s):
        if s.sl is None:
            btw('Select a track to play!')
            return

        enum_name = s.m_types[s.sl]

        try:
            m_type = getattr(bs.MusicType, enum_name)
            with bs.get_foreground_host_activity().context:
                bs.setmusic(m_type)
            push(f"Now Playing: {s.M_NAME[s.sl]}", color=(0, 1, 0))
            ding()
        except Exception as e:
            err(f"Failed to play track: {e}")

    def play_def(s):
        try:
            with bs.get_foreground_host_activity().context:
                def_music = bs.get_foreground_host_activity().default_music
                bs.setmusic(def_music)
            push("Restored default music!", color=(0, 1, 0))
            ding()
        except Exception as e:
            err("Failed to restore default music.")

@NEW
class Tune:
    """The nice settings window"""
    
    def __init__(s, *a):
        w = s.w = a[0]
        
        sv = bui.scrollwidget(
            parent=w,
            position=(50, 50),
            color=var('bg'),
            size=(500, 320)
        )
        
        items = [
            ('npp', 'Auto-Pause', 'Automatically pause the match when Coolbox opens.'),
            ('icall', 'Fixed Width Logs', 'Use fixed-width fonts for CallPartial logs to align text.'),
            ('spa', 'Autoplay Sounds', 'Automatically play sounds when scrolling through the Sound Picker.'),
            ('cconf0', 'Control: Block Host', 'Block your normal player inputs when remote Control starts.'),
            ('cconf1', 'Control: Auto-Close', 'Close the Coolbox UI automatically when Control starts.'),
            ('cconf2', 'Control: Invincibility', 'Make your original spaz invincible while controlling a bot.'),
            ('cconf3', 'Control: Intercept', 'Prevent the remote bot from performing its original AI actions.')
        ]
        
        count = len(items)
        ss = max(320, count * 60 + 20)
        
        s.cv = cw(
            parent=sv,
            background=False,
            size=(480, ss)
        )
        
        for i, (key, title, desc) in enumerate(items):
            p_y = ss - 60 - (i * 60)
            
            chk(
                parent=s.cv,
                position=(20, p_y + 25),
                size=(200, 30),
                value=bool(var(key)),
                text=title,
                on_value_change_call=bs.CallPartial(s.toggle, key)
            )
            
            tw(
                p=s.cv,
                position=(55, p_y + 5),
                text=desc,
                color=(0.5, 0.5, 0.5),
                scale=0.65,
                maxwidth=400
            )
            
    def toggle(s, key, val):
        var(key, val)
        if key == 'npp':
            npause(1 if val else 0)
        bui.getsound('click01').play()

@NEW
class Quick:

    _disco_timer = None
    _disco_on = False

    def __init__(s, *a):
        w = s.w = a[0]

        tw(
            p=w, pos=(40, 310), size=(220, 30), text='World Overrides',
            h_align='center', v_align='center', scale=1.2, color=(0.1, 0.7, 1)
        )
        tw(
            p=w, pos=(320, 310), size=(250, 30), text='Mass Modifiers',
            h_align='center', v_align='center', scale=1.2, color=(0.1, 0.7, 1)
        )

        chk(
            parent=w, position=(40, 250), size=(200, 30),
            value=bool(var('epic_mode')), text='Epic Slow-Motion',
            on_value_change_call=s.epic
        )
        
        chk(
            parent=w, position=(40, 185), size=(200, 30),
            value=bool(type(s)._disco_on), text='Disco Lighting',
            on_value_change_call=s.disco
        )

        bw(
            p=w, pos=(40, 105), size=(220, 55),
            label='Meteor Shower', icon=bui.gettexture('powerupBomb'), oac=s.meteors
        )
        
        bw(
            p=w, pos=(40, 40), size=(220, 55),
            label='Earthquake', icon=bui.gettexture('achievementOnslaught'), oac=s.quake
        )

        b_list = [
            ('Shield All', 'powerupShield', 'shield', (320, 235)),
            ('Glove All', 'powerupPunch', 'punch', (450, 235)),
            ('Heal All', 'powerupHealth', 'health', (320, 170)),
            ('Curse All', 'powerupCurse', 'curse', (450, 170)),
            ('Ice Rink', 'powerupIceBombs', 'ice', (320, 105)),
            ('Sleep All', 'achievementOffYouGo', 'sleep', (450, 105)),
            ('Shatter All', 'achievementCrossHair', 'shatter', (320, 40)),
            ('God Mode', 'star', 'god', (450, 40))
        ]

        for lbl, ic, act, p in b_list:
            bw(p=w, pos=p, size=(120, 55), label=lbl, icon=bui.gettexture(ic), oac=bs.CallPartial(s.mass, act))

    def epic(s, v):
        var('epic_mode', v)
        with bs.get_foreground_host_activity().context:
            bs.get_foreground_host_activity().globalsnode.slow_motion = v
        bui.getsound('click01').play()

    def disco(s, v):
        type(s)._disco_on = v
        bui.getsound('click01').play()
        if v:
            s.__class__._disco_timer = bui.AppTimer(0.3, s.step_disco, repeat=True)
        else:
            s.__class__._disco_timer = None
            with bs.get_foreground_host_activity().context:
                bs.get_foreground_host_activity().globalsnode.tint = (1.3, 1.2, 1)

    def step_disco(s):
        c = (random.random(), random.random(), random.random())
        with bs.get_foreground_host_activity().context:
            bs.get_foreground_host_activity().globalsnode.tint = c

    def meteors(s):
        def drop():
            if not s.w.exists():
                return
            p = (random.uniform(-9, 9), 12, random.uniform(-6, 6))
            with bs.get_foreground_host_activity().context:
                bs_bomb.Bomb(position=p, bomb_type='normal').autoretain()
        
        for i in range(25):
            bui.apptimer(i * 0.15, drop)
            
        push("Meteors Incoming!", color=(1, 0.5, 0))
        bui.getsound('shieldDown').play()

    def quake(s):
        with bs.get_foreground_host_activity().context:
            bs.camerashake(10)
        push("Earthquake!", color=(0.8, 0.4, 0))
        bui.getsound('block').play()

    def mass(s, act):
        with bs.get_foreground_host_activity().context:
            for p in bs.get_foreground_host_activity().players:
                a = p.actor
                if not a or not a.node.exists():
                    continue
                if act in ('shield', 'punch', 'health', 'curse'):
                    a.node.handlemessage(bs.PowerupMessage(act))
                elif act == 'ice':
                    a.node.hockey = not a.node.hockey
                elif act == 'sleep':
                    a.node.handlemessage('knockout', 4000)
                elif act == 'shatter':
                    a.shatter(True)
                elif act == 'god':
                    a.node.invincible = True
                    a._punch_cooldown = 0
                    a._punch_power_scale = 10
        ding()
        push(f"Applied {act}!", color=(0, 1, 0))

@NEW
class Tweak:

    def __init__(s, *a):
        w = s.w = a[0]

        btn_defs = [
            ('Globals Node', 'settingsIcon', s.glob_node),
            ('Map Node', 'star', s.map_node),
            ('Disco Nodes', 'achievementGotTheMoves', s.disco_nodes),

            ('Pick & Bubble', 'achievementOutline', s.pick_bubble),
            ('Pick & Smite', 'powerupBomb', s.pick_smite),
            ('Pick & Teleport', 'achievementOffYouGo', s.pick_tp),

            ('Find by Name', 'textClearButton', s.find_name),
            ('Find by Type', 'logo', s.find_type),
            ('Reset Camera', 'replayIcon', s.res_cam),

            ('Clear Orphans', 'crossOut', s.clear_orphans),
            ('Draw Line', 'graphicsIcon', s.draw_line),
            ('Map Coord', 'cursor', s.map_coord),

            ('Moon Gravity', 'upButton', s.moon_grav),
            ('Shiny World', 'achievementFlawlessVictory', s.shiny_world),
            ('RGB Cycle', 'powerupShield', s.rgb_cycle)
        ]

        for i, (lbl, ic, oac) in enumerate(btn_defs):
            col = i % 3
            row = i // 3
            bx = 45 + col * 175
            by = 315 - row * 65
            
            b = bw(
                p=w, pos=(bx, by), size=(160, 55),
                label=lbl, icon=bui.gettexture(ic),
                text_scale=1.0, iconscale=1.0
            )
            bw(b, oac=bs.CallPartial(oac, b))

    def glob_node(s, b):
        NodeManager(node=bs.get_foreground_host_activity().globalsnode, source=b)

    def map_node(s, b):
        try:
            NodeManager(node=bs.get_foreground_host_activity().map.node, source=b)
        except Exception:
            btw('Map has no main node!')

    def disco_nodes(s, b):
        c = 0
        with bs.get_foreground_host_activity().context:
            for n in bs.getnodes():
                if hasattr(n, 'color') and n.getnodetype() != 'globals':
                    try:
                        n.color = (random.random(), random.random(), random.random())
                        c += 1
                    except Exception:
                        pass
        ding()
        push(f'Randomized colors for {c} nodes!', color=(0, 1, 0))

    def pick_bubble(s, b):
        NodePicker(source=b, allow='3D', pipe=bs.CallPartial(s._bubble_prompt, b))

    def _bubble_prompt(s, b, n):
        Collector(source=b, pipe=bs.CallPartial(s._apply_bubble, n), first='Message', title='Bubble Text')

    def _apply_bubble(s, n, txt):
        if not n.exists():
            return
        with bs.get_foreground_host_activity().context:
            Bubble(node=n, text=txt, time=10, color=(1, 1, 0))
        ding()

    def pick_smite(s, b):
        NodePicker(source=b, allow='3D', pipe=s._smite)

    def _smite(s, n):
        if not n.exists():
            return
        p = n.position
        with bs.get_foreground_host_activity().context:
            bmb = bs_bomb.Bomb(position=p, bomb_type='tnt').autoretain()
            bs.timer(0.1, bmb.explode)
        ding()

    def pick_tp(s, b):
        NodePicker(source=b, allow='3D', pipe=s._tp)

    def _tp(s, n):
        try:
            getme(1).node.handlemessage(bs.StandMessage(n.position, 0))
            ding()
        except Exception as e:
            err(f"Teleport failed: {e}")

    def find_name(s, b):
        Collector(source=b, pipe=bs.CallPartial(s._f_name, b), first='Node name', title='Find by Name')

    def _f_name(s, b, t):
        with bs.get_foreground_host_activity().context:
            for n in bs.getnodes():
                if getattr(n, 'name', '') == t:
                    NodeManager(node=n, source=b)
                    return
        btw('Node not found!')

    def find_type(s, b):
        Collector(source=b, pipe=bs.CallPartial(s._f_type, b), first='Node type', title='Find by Type')

    def _f_type(s, b, t):
        with bs.get_foreground_host_activity().context:
            for n in bs.getnodes():
                if n.getnodetype() == t:
                    NodeManager(node=n, source=b)
                    return
        btw('Node not found!')

    def res_cam(s, b):
        _ba.set_camera_manual(False)
        ding()
        push('Camera Reset!', color=(0, 1, 0))

    def clear_orphans(s, b):
        c = 0
        with bs.get_foreground_host_activity().context:
            for n in bs.getnodes():
                if n.getnodetype() in ('prop', 'light', 'math', 'text') and not n.getdelegate(object):
                    n.delete()
                    c += 1
        push(f'Cleared {c} orphaned nodes!', color=(1, 0.5, 0))
        bui.getsound('shieldDown').play()

    def draw_line(s, b):
        NodePicker(source=b, allow='3D', pipe=lambda n1: NodePicker(source=b, allow='3D', pipe=lambda n2: s._draw(n1, n2)))

    def _draw(s, n1, n2, count=30):
        if count <= 0 or not n1.exists() or not n2.exists():
            return
        
        p1 = n1.position
        p2 = n2.position
        d = math.dist(p1, p2)
        steps = max(2, int(d * 5))
        
        with bs.get_foreground_host_activity().context:
            for i in range(steps):
                t = i / (steps - 1)
                p = (
                    p1[0] + t * (p2[0] - p1[0]),
                    p1[1] + t * (p2[1] - p1[1]),
                    p1[2] + t * (p2[2] - p1[2])
                )
                bs.emitfx(position=p, chunk_type='spark', count=1, scale=0.5)
                
        if count == 30:
            ding()
            
        bui.apptimer(0.1, lambda: s._draw(n1, n2, count - 1))

    def map_coord(s, b):
        NodePicker(source=b, allow='3D', pipe=s._map)

    def _map(s, n):
        s.mapper = Mapper(pipe=lambda p2: Coolbox(fake=True, extra=p2), pos=n.position)
        cw(s.w, transition='out_right')

    def moon_grav(s, b):
        v = var('t_moongrav')
        nv = 0.2 if not v else 1.0
        var('t_moongrav', not v)
        c = 0
        with bs.get_foreground_host_activity().context:
            for n in bs.getnodes():
                if hasattr(n, 'gravity_scale'):
                    try:
                        n.gravity_scale = nv
                        c += 1
                    except Exception:
                        pass
        ding()
        push(f'Moon Gravity {"On" if not v else "Off"} ({c} nodes)!', color=(0.5, 0.5, 1))

    def shiny_world(s, b):
        v = var('t_shiny')
        nr = [3.0] if not v else [1.0]
        nrf = 'soft' if not v else 'powerup'
        var('t_shiny', not v)
        c = 0
        with bs.get_foreground_host_activity().context:
            for n in bs.getnodes():
                if hasattr(n, 'reflection_scale'):
                    try:
                        n.reflection_scale = nr
                        n.reflection = nrf
                        c += 1
                    except Exception:
                        pass
        ding()
        push(f'Shiny World {"On" if not v else "Off"} ({c} nodes)!', color=(1, 1, 0))

    def rgb_cycle(s, b):
        global _rgb_cycle_combines
        v = var('t_rgbcycle')
        if not v:
            c = 0
            with bs.get_foreground_host_activity().context:
                gnode = bs.get_foreground_host_activity().globalsnode
                keys = {0: (1, 0, 0), 1: (0, 1, 0), 2: (0, 0, 1), 3: (1, 0, 0)}
                items = sorted(keys.items())
                for n in bs.getnodes():
                    if hasattr(n, 'color') and n.getnodetype() != 'globals':
                        try:
                            combine = bs.newnode('combine', owner=n, attrs={'size': 3})
                            for i in range(3):
                                curve = bs.newnode('animcurve', owner=n)
                                gnode.connectattr('time', curve, 'in')
                                curve.times = [int(1000 * t) for t, _ in items]
                                curve.values = [val[i] for _, val in items]
                                curve.loop = True
                                curve.connectattr('out', combine, f'input{i}')
                            combine.connectattr('output', n, 'color')
                            _rgb_cycle_combines.append(combine)
                            c += 1
                        except Exception:
                            pass
            var('t_rgbcycle', True)
            ding()
            push(f'RGB Cycle On ({c} nodes)!', color=(0, 1, 0))
        else:
            with bs.get_foreground_host_activity().context:
                for combine in _rgb_cycle_combines:
                    try:
                        if combine.exists(): combine.delete()
                    except Exception:
                        pass
            _rgb_cycle_combines = []
            var('t_rgbcycle', False)
            ding()
            push('RGB Cycle Off!', color=(1, 1, 0))

@NEW
class Gather:
    """Modify party and team based stuff"""
    
    def __init__(s, *a):
        w = s.w = a[0]
        s.sl_t = None
        
        # Left Panel: Team List
        s.tsv = bui.scrollwidget(parent=w, color=var('bg'), position=(30, 65), size=(180, 305))
        s.tcv = cw(parent=s.tsv, background=False)
        
        # Add Team Button
        bw(
            p=w, pos=(30, 20), size=(180, 40), 
            label='Create Team', icon=bui.gettexture('achievementTeamPlayer'), 
            oac=s.add_team
        )
        
        # Right Panel: Team & Player Details
        s.dsv = bui.scrollwidget(parent=w, color=var('bg'), position=(220, 20), size=(350, 350))
        s.dcv = cw(parent=s.dsv, background=False)
        
        s.refresh()
        s.spy()
        
    def spy(s):
        if not s.w.exists(): return
        try:
            teams = bs.get_foreground_host_activity().teams
            c_t = len(teams)
            c_p = sum(len(t.players) for t in teams)
            if c_t != getattr(s, 'last_t', -1) or c_p != getattr(s, 'last_p', -1):
                s.last_t = c_t
                s.last_p = c_p
                s.refresh()
        except:
            pass
        bui.apptimer(1.0, s.spy)

    def add_team(s):
        Collector(source=s.w, pipe=s._add_team, first='Team Name', title='Create Team')
        
    def _add_team(s, name):
        tid = var('g_tid') or 2
        try:
            c = (random.random(), random.random(), random.random())
            t = bs.SessionTeam(team_id=tid, name=name, color=c)
            bs.get_foreground_host_activity().add_team(t)
            var('g_tid', tid + 1)
            ding()
            s.refresh()
        except Exception as e:
            err(f"Failed: {e}")

    def refresh(s):
        if not s.w.exists(): return
        [k.delete() for k in s.tcv.get_children()]
        try:
            teams = bs.get_foreground_host_activity().teams
        except:
            return
            
        ss = max(305, len(teams) * 45)
        cw(s.tcv, size=(160, ss))
        
        valid_sl = False
        for i, t in enumerate(teams):
            if t == s.sl_t: valid_sl = True
            y = ss - 40 - (i * 45)
            n = t.name.evaluate() if hasattr(t.name, 'evaluate') else t.name
            sl_color = tuple(min(1.0, ch * 1.4 + 0.15) for ch in t.color) if t == s.sl_t else t.color
            b = bw(
                p=s.tcv, pos=(5, y), size=(150, 35), label=n, color=sl_color,
                textcolor=var('t'),
                oac=bs.CallPartial(s.show_team, t)
            )
                
        if not valid_sl: s.sl_t = None
        s.show_team(s.sl_t)

    def show_team(s, t):
        s.sl_t = t
        [k.delete() for k in s.dcv.get_children()]
        if not t: return
        
        players = t.players
        count = len(players)
        ss = max(350, 180 + count * 45)
        cw(s.dcv, size=(330, ss))
        
        n = t.name.evaluate() if hasattr(t.name, 'evaluate') else t.name
        
        tw(p=s.dcv, pos=(10, ss - 40), size=(310, 30), text=n, color=t.color, scale=1.2, h_align='center', v_align='center')
        
        bw(p=s.dcv, pos=(10, ss - 85), size=(100, 35), label='Rename', oac=bs.CallPartial(s.rename_team, t))
        
        c_btn = bw(p=s.dcv, pos=(115, ss - 85), size=(100, 35), label='Color', color=t.color)
        var('t_col', t.color)
        bw(c_btn, oac=bs.CallPartial(ColorPicker, in_source=c_btn, id='t_col', what='t_col', id2='t_col', chr='char', on_back=bs.CallPartial(s.recolor_team, t), mode=2))
        
        bw(p=s.dcv, pos=(220, ss - 85), size=(100, 35), label='Nuke', icon=bui.gettexture('crossOut'), oac=bs.CallPartial(s.nuke_team, t))
        
        bw(p=s.dcv, pos=(10, ss - 130), size=(100, 35), label='Gather', icon=bui.gettexture('achievementTeamPlayer'), oac=bs.CallPartial(s.gather_team, t))
        bw(p=s.dcv, pos=(115, ss - 130), size=(100, 35), label='Smite', icon=bui.gettexture('achievementOffYouGo'), oac=bs.CallPartial(s.smite_team, t))
        bw(p=s.dcv, pos=(220, ss - 130), size=(100, 35), label='Heal', icon=bui.gettexture('powerupHealth'), oac=bs.CallPartial(s.heal_team, t))
        
        tw(p=s.dcv, pos=(10, ss - 170), text=f'Players ({count}):', color=(0.5, 0.5, 0.5), scale=0.8)
        
        for i, p in enumerate(players):
            y = ss - 210 - (i * 45)
            p_name = p.getname()
            
            tw(p=s.dcv, pos=(10, y + 5), text=p_name, maxwidth=150, color=getattr(p, 'color', (1,1,1)))
            
            bw(p=s.dcv, pos=(170, y), size=(70, 35), label='Fetch', oac=bs.CallPartial(s.fetch_player, p))
            bw(p=s.dcv, pos=(245, y), size=(70, 35), label='Goto', oac=bs.CallPartial(s.goto_player, p))

    def _refresh_scoreboard(s, t):
        """Force the current game's Scoreboard actor (if any) to rebuild
        this team's entry, since it bakes name/color in once at creation
        and never updates them live otherwise."""
        try:
            act = bs.get_foreground_host_activity()
            sb = getattr(act, '_scoreboard', None) or getattr(act, 'scoreboard', None)
            entries = getattr(sb, '_entries', None)
            if sb is not None and entries is not None and t.id in entries:
                sb.remove_team(t.id)
                sb._add_team(t)
        except Exception:
            pass

    def rename_team(s, t):
        Collector(source=s.w, pipe=bs.CallPartial(s._rename_team, t), first='New Name', title='Rename Team')
        
    def _rename_team(s, t, name):
        try:
            with bs.get_foreground_host_activity().context:
                t.name = name
                try:
                    t.sessionteam.name = name
                except Exception:
                    pass
                s._refresh_scoreboard(t)
            ding()
            s.refresh()
        except Exception as e:
            err(f'Failed to rename team: {e}')

    def recolor_team(s, t):
        try:
            c = var('t_col')
            with bs.get_foreground_host_activity().context:
                t.color = c
                try:
                    t.sessionteam.color = c
                except Exception:
                    pass
                # Update everyone currently on the team: their cached
                # color (so respawns pick it up) and their live spaz
                # node color (so it changes instantly if they're alive).
                for p in t.players:
                    p.color = c
                    try:
                        p.sessionplayer.color = c
                    except Exception:
                        pass
                    try:
                        if p.actor and p.actor.node.exists():
                            p.actor.node.color = c
                            p.actor.node.name_color = bs.safecolor(c, target_intensity=0.75)
                    except Exception:
                        pass
                s._refresh_scoreboard(t)
            s.refresh()
        except Exception as e:
            err(f'Failed to recolor team: {e}')

    def nuke_team(s, t):
        try:
            bs.get_foreground_host_activity().remove_team(t.sessionteam)
            s.sl_t = None
            ding()
            s.refresh()
        except Exception as e:
            err(f"Failed: {e}")

    def gather_team(s, t):
        me = getme(1)
        if not me or not me.node.exists(): return
        pos = me.node.position
        for p in t.players:
            if p.actor and p.actor.node.exists():
                p.actor.node.handlemessage(bs.StandMessage(pos, 0))
        ding()
        push('Team gathered!')

    def smite_team(s, t):
        for p in t.players:
            if p.actor and p.actor.node.exists():
                p.actor.node.handlemessage(bs.DieMessage())
        ding()
        
    def heal_team(s, t):
        for p in t.players:
            if p.actor and p.actor.node.exists():
                p.actor.node.handlemessage(bs.PowerupMessage('health'))
        ding()

    def fetch_player(s, p):
        me = getme(1)
        if not me or not me.node.exists(): return
        if p.actor and p.actor.node.exists():
            p.actor.node.handlemessage(bs.StandMessage(me.node.position, 0))
            ding()

    def goto_player(s, p):
        me = getme(1)
        if not me or not me.node.exists(): return
        if p.actor and p.actor.node.exists():
            me.node.handlemessage(bs.StandMessage(p.actor.node.position, 0))
            ding()

@NEW
class Load:

    def __init__(s, *a):
        w = s.w = a[0]
        s.sl = None

        s.presets = [
            # === SPAWN ===
            {
                'n': 'Kronk Buddy',
                'd': 'A friendly blue Kronk ready to help you win.',
                't': 'Spawn',
                'i': 'kronkIcon',
                'v': {'char': 'Kronk', 'tchar': 'Kronk Buddy', 'Main': (0, 1, 1), 'Highlight': (0, 0, 1), 'Name': (0, 0.5, 1)}
            },
            {
                'n': 'Golden God',
                'd': 'A shiny golden skeleton. Wealthy and terrifying.',
                't': 'Spawn',
                'i': 'bonesIcon',
                'v': {'char': 'Bones', 'tchar': 'Golden God', 'Main': (1, 0.8, 0), 'Highlight': (1, 1, 0), 'Name': (1, 0.9, 0.2)}
            },
            {
                'n': 'Shadow Ninja',
                'd': 'Silent, deadly, and extremely edgy.',
                't': 'Spawn',
                'i': 'ninjaIcon',
                'v': {'char': 'Snake Shadow', 'tchar': 'Shadow Ninja', 'Main': (0.1, 0.1, 0.1), 'Highlight': (1, 0, 0), 'Name': (1, 0, 0)}
            },
            {
                'n': 'Cyborg Unit',
                'd': 'Cold steel. No feelings. Probably.',
                't': 'Spawn',
                'i': 'cyborgIcon',
                'v': {'char': 'Cyborg', 'tchar': 'Cyborg Unit', 'Main': (0.4, 0.4, 0.5), 'Highlight': (0, 0.8, 1), 'Name': (0.5, 0.9, 1)}
            },
            {
                'n': 'Frosty',
                'd': 'A chilly snowman. Cool as ice.',
                't': 'Spawn',
                'i': 'frostyIcon',
                'v': {'char': 'Frosty', 'tchar': 'Frosty', 'Main': (0.5, 0.8, 1), 'Highlight': (1, 1, 1), 'Name': (0.7, 0.95, 1)}
            },
            {
                'n': 'Santa',
                'd': 'The big man himself. Ho ho ho.',
                't': 'Spawn',
                'i': 'santaIcon',
                'v': {'char': 'Santa Claus', 'tchar': 'Santa', 'Main': (0.9, 0.1, 0.1), 'Highlight': (1, 1, 1), 'Name': (1, 0.8, 0.8)}
            },
            {
                'n': 'Wizard',
                'd': 'A mysterious spellcaster in purple.',
                't': 'Spawn',
                'i': 'wizardIcon',
                'v': {'char': 'Wizard', 'tchar': 'Wizard', 'Main': (0.5, 0.1, 0.8), 'Highlight': (0.9, 0.5, 1), 'Name': (0.8, 0.4, 1)}
            },
            {
                'n': 'Evil Bones',
                'd': 'A skeleton painted in crimson rage.',
                't': 'Spawn',
                'i': 'bonesIcon',
                'v': {'char': 'Bones', 'tchar': 'Evil Bones', 'Main': (0.8, 0, 0), 'Highlight': (0.2, 0, 0), 'Name': (1, 0.2, 0.2)}
            },
            {
                'n': 'Toxic Kronk',
                'd': 'He has been through some things.',
                't': 'Spawn',
                'i': 'kronkIcon',
                'v': {'char': 'Kronk', 'tchar': 'Toxic Kronk', 'Main': (0.2, 0.9, 0.1), 'Highlight': (0.5, 0.1, 0.8), 'Name': (0.3, 1, 0.3)}
            },
            {
                'n': 'Pink Ninja',
                'd': 'Deadly. Also pink.',
                't': 'Spawn',
                'i': 'ninjaIcon',
                'v': {'char': 'Snake Shadow', 'tchar': 'Pink Ninja', 'Main': (1, 0.4, 0.7), 'Highlight': (1, 0.8, 0.9), 'Name': (1, 0.6, 0.8)}
            },
            {
                'n': 'Rainbow Bones',
                'd': 'Born to be wild and colorful.',
                't': 'Spawn',
                'i': 'bonesIcon',
                'v': {'char': 'Bones', 'tchar': 'Rainbow Bones', 'Main': (1, 0.2, 0.8), 'Highlight': (0.2, 1, 0.4), 'Name': (0.4, 0.8, 1)}
            },
            {
                'n': 'Agent Zero',
                'd': 'No name. No face. No mercy.',
                't': 'Spawn',
                'i': 'agentIcon',
                'v': {'char': 'Secret Agent', 'tchar': 'Agent Zero', 'Main': (0.15, 0.15, 0.15), 'Highlight': (0.8, 0.8, 0.8), 'Name': (0.6, 0.6, 0.6)}
            },
            {
                'n': 'Galaxy Penguin',
                'd': 'Waddling across the cosmos.',
                't': 'Spawn',
                'i': 'penguinIcon',
                'v': {'char': 'Penguin', 'tchar': 'Galaxy Penguin', 'Main': (0.1, 0, 0.5), 'Highlight': (0.6, 0.2, 1), 'Name': (0.7, 0.5, 1)}
            },
            {
                'n': 'Lava Wizard',
                'd': 'He studied the blade. Then set it on fire.',
                't': 'Spawn',
                'i': 'wizardIcon',
                'v': {'char': 'Wizard', 'tchar': 'Lava Wizard', 'Main': (1, 0.2, 0), 'Highlight': (1, 0.6, 0), 'Name': (1, 0.4, 0)}
            },
            {
                'n': 'Blueberry Bear',
                'd': 'Round. Soft. Slightly dangerous.',
                't': 'Spawn',
                'i': 'bearIcon',
                'v': {'char': 'B-9000', 'tchar': 'Blueberry Bear', 'Main': (0.2, 0.4, 1), 'Highlight': (0.5, 0.7, 1), 'Name': (0.6, 0.8, 1)}
            },
            {
                'n': 'Void Walker',
                'd': 'Came from nowhere. Going back.',
                't': 'Spawn',
                'i': 'cyborgIcon',
                'v': {'char': 'Cyborg', 'tchar': 'Void Walker', 'Main': (0, 0, 0), 'Highlight': (0.3, 0, 0.5), 'Name': (0.5, 0, 1)}
            },
            {
                'n': 'Sun God',
                'd': 'Blinding. Warm. Absolutely unhinged.',
                't': 'Spawn',
                'i': 'wizardIcon',
                'v': {'char': 'Wizard', 'tchar': 'Sun God', 'Main': (1, 0.9, 0), 'Highlight': (1, 0.5, 0), 'Name': (1, 1, 0.5)}
            },
            {
                'n': 'Midnight Agent',
                'd': 'Operates exclusively at 3am.',
                't': 'Spawn',
                'i': 'agentIcon',
                'v': {'char': 'Secret Agent', 'tchar': 'Midnight Agent', 'Main': (0.05, 0.05, 0.15), 'Highlight': (0.2, 0.2, 0.5), 'Name': (0.4, 0.4, 1)}
            },
            {
                'n': 'Cursed Frosty',
                'd': 'Do NOT let him near the thermostat.',
                't': 'Spawn',
                'i': 'frostyIcon',
                'v': {'char': 'Frosty', 'tchar': 'Cursed Frosty', 'Main': (0.3, 0, 0.1), 'Highlight': (0.8, 0, 0.3), 'Name': (1, 0, 0.4)}
            },
            {
                'n': 'Neon Jack',
                'd': 'He glows. You will too eventually.',
                't': 'Spawn',
                'i': 'jackIcon',
                'v': {'char': 'Jack Morgan', 'tchar': 'Neon Jack', 'Main': (0, 1, 0.5), 'Highlight': (0, 0.5, 1), 'Name': (0, 1, 0.8)}
            },
            {
                'n': 'Inferno Ali',
                'd': 'Float like a butterfly, burn like the sun.',
                't': 'Spawn',
                'i': 'aliIcon',
                'v': {'char': 'Ali', 'tchar': 'Inferno Ali', 'Main': (1, 0.3, 0), 'Highlight': (1, 0.7, 0), 'Name': (1, 0.5, 0.1)}
            },
            {
                'n': 'Ocean Mel',
                'd': 'Deep, mysterious, slightly salty.',
                't': 'Spawn',
                'i': 'melIcon',
                'v': {'char': 'Mel', 'tchar': 'Ocean Mel', 'Main': (0, 0.4, 0.8), 'Highlight': (0, 0.8, 1), 'Name': (0.3, 0.9, 1)}
            },
            {
                'n': 'Pixel Zoe',
                'd': 'She runs at exactly 8 frames per second.',
                't': 'Spawn',
                'i': 'zoeColorMask',
                'v': {'char': 'Zoe', 'tchar': 'Pixel Zoe', 'Main': (0.9, 0.5, 0.9), 'Highlight': (0.5, 0.9, 0.5), 'Name': (1, 0.8, 1)}
            },
            {
                'n': 'Rust Bot',
                'd': 'Outdated firmware. Still dangerous.',
                't': 'Spawn',
                'i': 'cyborgIcon',
                'v': {'char': 'Cyborg', 'tchar': 'Rust Bot', 'Main': (0.6, 0.3, 0.1), 'Highlight': (0.4, 0.2, 0), 'Name': (0.8, 0.5, 0.2)}
            },
            {
                'n': 'Plague Bear',
                'd': 'Unclear what disease. Very clear it works.',
                't': 'Spawn',
                'i': 'bearIcon',
                'v': {'char': 'B-9000', 'tchar': 'Plague Bear', 'Main': (0.3, 0.5, 0.1), 'Highlight': (0.6, 0.8, 0), 'Name': (0.5, 1, 0.2)}
            },
            {
                'n': 'Demon Santa',
                'd': 'He sees you when you\'re sleeping. Still.',
                't': 'Spawn',
                'i': 'santaIcon',
                'v': {'char': 'Santa Claus', 'tchar': 'Demon Santa', 'Main': (0.5, 0, 0), 'Highlight': (0.1, 0, 0), 'Name': (1, 0, 0)}
            },
            # === BUILD ===
            {
                'n': 'Bouncy TNT',
                'd': 'A highly reflective TNT block that barely obeys gravity.',
                't': 'Build',
                'i': 'tnt',
                'v': {'b_mode': 0, 'b_mesh': 'tnt', 'b_tex': 'tnt', 'b_body': 'crate', 'b_grav': '0.3'}
            },
            {
                'n': 'Giant Coin',
                'd': 'A massive golden puck that bounces around.',
                't': 'Build',
                'i': 'coin',
                'v': {'b_mode': 0, 'b_mesh': 'puck', 'b_tex': 'tokens4', 'b_body': 'puck', 'b_grav': '1.0'}
            },
            {
                'n': 'Sticky Bomb',
                'd': 'Clings to surfaces like it has something to prove.',
                't': 'Build',
                'i': 'bombStickyColor',
                'v': {'b_mode': 0, 'b_mesh': 'bomb', 'b_tex': 'bombStickyColor', 'b_body': 'sphere', 'b_grav': '1.0'}
            },
            {
                'n': 'Ice Ball',
                'd': 'A slippery ice bomb that glides around.',
                't': 'Build',
                'i': 'bombColorIce',
                'v': {'b_mode': 0, 'b_mesh': 'bomb', 'b_tex': 'bombColorIce', 'b_body': 'sphere', 'b_grav': '0.5'}
            },
            {
                'n': 'Floating Orb',
                'd': 'Weightless. Pointless. Beautiful.',
                't': 'Build',
                'i': 'powerupShield',
                'v': {'b_mode': 0, 'b_mesh': 'bomb', 'b_tex': 'powerupShield', 'b_body': 'sphere', 'b_grav': '0.0'}
            },
            {
                'n': 'Moon Rock',
                'd': 'Crate that floats like it forgot gravity exists.',
                't': 'Build',
                'i': 'tnt',
                'v': {'b_mode': 0, 'b_mesh': 'crate', 'b_tex': 'tnt', 'b_body': 'crate', 'b_grav': '0.15'}
            },
            {
                'n': 'Speed Puck',
                'd': 'Puck with basically no friction with reality.',
                't': 'Build',
                'i': 'coin',
                'v': {'b_mode': 0, 'b_mesh': 'puck', 'b_tex': 'puckColor', 'b_body': 'puck', 'b_grav': '0.6'}
            },
            {
                'n': 'Cursed Crate',
                'd': 'Crate shaped. Power unknown. Do not open.',
                't': 'Build',
                'i': 'achievementTNT',
                'v': {'b_mode': 0, 'b_mesh': 'crate', 'b_tex': 'powerupCurse', 'b_body': 'crate', 'b_grav': '1.0'}
            },
            {
                'n': 'Neon Text',
                'd': 'Bright glowing text to mark your territory.',
                't': 'Build',
                'i': 'achievementOutline',
                'v': {'b_mode': 1, 'b_txt': 'Danger!', 'Text': (1, 0, 0), 'b_scl': '0.02', 'b_inw': True}
            },
            {
                'n': 'Warning Sign',
                'd': 'For when something is definitely about to go wrong.',
                't': 'Build',
                'i': 'achievementTNT',
                'v': {'b_mode': 1, 'b_txt': 'WARNING!', 'Text': (1, 0.2, 0), 'b_scl': '0.025', 'b_inw': True}
            },
            {
                'n': 'Name Tag',
                'd': 'A floating name tag. Edit text to personalize.',
                't': 'Build',
                'i': 'achievementOutline',
                'v': {'b_mode': 1, 'b_txt': 'Player 1', 'Text': (0.4, 1, 0.4), 'b_scl': '0.015', 'b_inw': True}
            },
            {
                'n': 'Touch Grass',
                'd': 'Friendly reminder.',
                't': 'Build',
                'i': 'achievementOutline',
                'v': {'b_mode': 1, 'b_txt': 'Touch grass.', 'Text': (0.3, 0.9, 0.3), 'b_scl': '0.018', 'b_inw': True}
            },
            {
                'n': 'Skill Issue',
                'd': 'Post this wherever appropriate.',
                't': 'Build',
                'i': 'achievementSuperPunch',
                'v': {'b_mode': 1, 'b_txt': 'Skill Issue', 'Text': (1, 0.4, 0.1), 'b_scl': '0.022', 'b_inw': True}
            },
            {
                'n': 'GG Sign',
                'd': 'Place after winning. Or losing. Whatever.',
                't': 'Build',
                'i': 'achievementMedalLarge',
                'v': {'b_mode': 1, 'b_txt': 'GG!', 'Text': (0.2, 1, 0.5), 'b_scl': '0.03', 'b_inw': True}
            },
            {
                'n': 'Chaos Box',
                'd': 'Unknown mesh. Unknown body. You\'ll see.',
                't': 'Build',
                'i': 'powerupBomb',
                'v': {'b_mode': 0, 'b_mesh': 'tnt', 'b_tex': 'explosion', 'b_body': 'sphere', 'b_grav': '0.05'}
            },
            {
                'n': 'Ice Puck',
                'd': 'Hockey puck made of ice. Slide forever.',
                't': 'Build',
                'i': 'bombColorIce',
                'v': {'b_mode': 0, 'b_mesh': 'puck', 'b_tex': 'bombColorIce', 'b_body': 'puck', 'b_grav': '0.8'}
            },
            # === QUICK ===
            {
                'n': 'Cinematic Mode',
                'd': 'Epic slow motion with auto-pause disabled.',
                't': 'Quick',
                'i': 'settingsIcon',
                'v': {'epic_mode': True, 'npp': 0}
            },
            {
                'n': 'Disco Time',
                'd': 'RGB global tint cycle for a party vibe.',
                't': 'Quick',
                'i': 'achievementGotTheMoves',
                'v': {'disco': True}
            },
            {
                'n': 'Moon Physics',
                'd': 'Low gravity for all nodes in the scene.',
                't': 'Quick',
                'i': 'upButton',
                'v': {'t_moongrav': True}
            },
            {
                'n': 'Shiny World',
                'd': 'Crank up reflections on everything.',
                't': 'Quick',
                'i': 'achievementFlawlessVictory',
                'v': {'t_shiny': True}
            },
            {
                'n': 'God Mode Setup',
                'd': 'Open Quick and smash God Mode immediately.',
                't': 'Quick',
                'i': 'star',
                'v': {}
            },
            {
                'n': 'Freeze Frame',
                'd': 'Slow motion on, auto pause off. For clips.',
                't': 'Quick',
                'i': 'replayIcon',
                'v': {'epic_mode': True, 'npp': 0}
            },
            # === TUNE ===
            {
                'n': 'Chill Setup',
                'd': 'Autoplay sounds on, fixed logs off. Relaxed vibes.',
                't': 'Tune',
                'i': 'audioIcon',
                'v': {'spa': True, 'icall': False, 'npp': 1}
            },
            {
                'n': 'Dev Mode',
                'd': 'Fixed width logs, no auto pause, autoplay off.',
                't': 'Tune',
                'i': 'logIcon',
                'v': {'icall': True, 'spa': False, 'npp': 0}
            },
            {
                'n': 'Control Freak',
                'd': 'Block host, auto-close UI, intercept inputs.',
                't': 'Tune',
                'i': 'controllerIcon',
                'v': {'cconf0': True, 'cconf1': True, 'cconf2': False, 'cconf3': True}
            },
            {
                'n': 'Ghost Control',
                'd': 'Control without blocking host inputs. Sneaky.',
                't': 'Tune',
                'i': 'controllerIcon',
                'v': {'cconf0': False, 'cconf1': False, 'cconf2': False, 'cconf3': False}
            },
            {
                'n': 'Invincible Driver',
                'd': 'Invincibility on while controlling. No dying.',
                't': 'Tune',
                'i': 'star',
                'v': {'cconf2': True, 'cconf0': True, 'cconf3': True}
            },
        ]

        s.img = bui.imagewidget(
            parent=w,
            position=(50, 270),
            size=(90, 90),
            texture=bui.gettexture('empty'),
            mask_texture=bui.gettexture('empty')
        )

        s.t_name = tw(
            p=w, pos=(185, 315), size=(1, 35), text='',
            scale=1.2, h_align='left', v_align='center', maxwidth=215
        )

        s.t_desc = tw(
            p=w, pos=(185, 270), size=(1, 55), text='',
            scale=0.78, h_align='left', v_align='top', maxwidth=215,
            color=(0.6, 0.6, 0.6)
        )

        s.b_load = bw(
            p=w, pos=(420, 280), size=(130, 50),
            label='Load', icon=bui.gettexture('inventoryIcon'),
            oac=s.load_preset
        )

        sv = bui.scrollwidget(
            parent=w,
            position=(40, 40),
            size=(520, 200),
            color=var('bg')
        )

        count = len(s.presets)
        rows = math.ceil(count / 2)
        ss = max(200, rows * 45)

        s.cv = cw(
            parent=sv,
            background=False,
            size=(500, ss)
        )

        s.texts = []
        for i, p in enumerate(s.presets):
            col = i % 2
            row = i // 2
            x = 10 + col * 245
            y = ss - 45 - row * 45
            t = tw(
                p=s.cv, pos=(x, y), size=(235, 40),
                text=p['n'], color=var('t'),
                selectable=True, click_activate=True, maxwidth=230,
                on_activate_call=bs.CallPartial(s.select, i),
                h_align='center', v_align='center'
            )
            s.texts.append(t)

        if count > 0:
            s.select(0)

    def select(s, i):
        if s.sl != i and s.sl is not None:
            bui.getsound('tap').play()
        s.sl = i

        for idx, t in enumerate(s.texts):
            tw(t, color=(0, 1, 0) if idx == i else var('t'))

        p = s.presets[i]
        tw(s.t_name, text=p['n'], color=p['v'].get('Main', var('t')))
        tw(s.t_desc, text=p['d'])

        if p['t'] == 'Spawn':
            c_name = p['v'].get('char', NAME()[0])
            valid_char = c_name if c_name in NAME() else NAME()[0]
            char_obj = SPAZ()[NAME().index(valid_char)]
            bui.imagewidget(
                edit=s.img,
                texture=bui.gettexture(char_obj.icon_texture),
                mask_texture=bui.gettexture('characterIconMask'),
                tint_texture=bui.gettexture(char_obj.icon_mask_texture),
                color=(1, 1, 1),
                tint_color=p['v'].get('Main', (1, 1, 1)),
                tint2_color=p['v'].get('Highlight', (1, 1, 1))
            )
        else:
            try:
                tex = bui.gettexture(p.get('i') or 'logo')
            except Exception:
                tex = bui.gettexture('logo')
            bui.imagewidget(
                edit=s.img,
                texture=tex,
                mask_texture=bui.gettexture('empty'),
                tint_texture=bui.gettexture('empty'),
                color=(1, 1, 1),
                tint_color=(1, 1, 1),
                tint2_color=(1, 1, 1)
            )

    def load_preset(s):
        if s.sl is None:
            btw('Select a preset first!')
            return

        p = s.presets[s.sl]

        for k, v in p['v'].items():
            var(k, v)

        if p['t'] == 'Spawn':
            c_name = p['v'].get('char', NAME()[0])
            valid_char = c_name if c_name in NAME() else NAME()[0]
            fixall(valid_char)

        ding()
        push(f"Loaded {p['n']}!", color=(0, 1, 0))

        cw(s.w, transition='out_right')
        bui.apptimer(0.1, lambda: Coolbox(fb=p['t']))

class Mapper2D:

    last = 0

    def __init__(s, pipe, pos=None, on_exit=None):
        s.tired = time.time_ns() - s.__class__.last < 10**9
        if s.tired: btw('Cool down!'); return
        
        p = pos if pos and len(pos) == 2 else (0, 0)
        if pos and len(pos) == 3:
            p = (pos[0], pos[1])
            
        s.pipe = pipe
        s.on_exit = on_exit
        
        with bs.get_foreground_host_activity().context:
            s.node = bs.newnode('image', attrs={
                'texture': bs.gettexture('achievementCrossHair'),
                'absolute_scale': True,
                'scale': (50, 50),
                'position': p,
                'color': (0, 1, 0)
            })
            bui.getsound('laser').play()
            
            s.safe = None
            def f(): s.safe = s.node.exists()
            bui.apptimer(1, f)
            
            s.step = s.ostep = 3.0
            
        s.wait = 0.01
        s.bstep = s.step * 3
        s.llr = s.lud = 0.0
        
        s.overlay = Overlay(build=True)
        
        LN({
            'UP_DOWN': lambda a: s.manage(a, 0),
            'LEFT_RIGHT': lambda a: s.manage(a, 1),
            'BOMB_PRESS': s.exit,
            'PUNCH_PRESS': s.build,
        })
        STATE(True)
        s.move()

    def manage(s, a, lr=0):
        if lr: s.llr = a
        else: s.lud = a

    def move(s):
        m = getme(1)
        if not m or m._dead: s.destroy(); return
        try: p = s.node.position
        except:
            if STATE():
                STATE(False)
                bui.apptimer(1, s.fail)
            return
        
        new_p = (p[0] + s.llr * s.step, p[1] + s.lud * s.step)
        s.node.position = new_p
        s.overlay.up(new_p[0], new_p[1], 0, s.llr, s.lud)
        
        bui.apptimer(s.wait, s.move)

    def destroy(s):
        with bs.get_foreground_host_activity().context:
            n = s.node
            bui.getsound('shatter').play()
            n.delete()
            bs.timer(1, s.reset)

    def reset(s):
        me = getme()
        if not me: return
        me.resetinput()
        with bs.get_foreground_host_activity().context:
            me.actor.connect_controls_to_player()

    """Build at current position (repeatable - does not exit)"""
    def build(s):
        s.overlay.press(3)
        try: p = s.node.position
        except: return

        with bs.get_foreground_host_activity().context:
            bs.timer(0.1, lambda: s.overlay.release(3))
            bui.getsound('gunCocking').play()
            bs.animate_array(s.node,'scale',2,{0:(50,50),0.1:(30,30),0.2:(50,50)})

        s.pipe((p[0], p[1], 0.0))

    """Exit mapper without building (graceful, no shatter)"""
    def exit(s):
        s.overlay.press(1)
        s.overlay.destroy()
        try: p = s.node.position
        except: p = None
        with bs.get_foreground_host_activity().context:
            if p:
                bui.getsound('powerup01').play()
                bs.animate_array(s.node,'scale',2,{0:(50,50),0.1:(0,0)})
                bs.timer(0.1, s.node.delete)
            else:
                s.node.delete()
        STATE(False)
        s.__class__.last = time.time_ns()
        if s.on_exit and p: bui.apptimer(1, bs.CallPartial(s.on_exit, (p[0],p[1],0.0)))
        bui.apptimer(1, s.reset)

    def complain(s):
        push('You destroyed the mapper!', color=(1, 0, 0))
        bui.getsound('swip').play()
        s.overlay.destroy()
        None if s.safe else btw('Mapper destroyed too early.')

    """Mapper2D is always build mode (dispatch needs a real position),
    so on a lost node just complain - never call pipe() with none."""
    def fail(s):
        s.complain()


@NEW
class Build:

    def __init__(s, *a):
        w = s.w = a[0]
        s.ex = a[5]

        con('b_mesh', 'tnt')
        con('b_tex', 'tnt')
        con('b_body', 'crate')
        con('b_grav', '1.0')
        con('b_mscale', '1.0')
        con('b_bscale', '1.0')
        con('b_txt', 'Coolbox!')
        con('b_scl', '0.01')
        con('b_iscal', '100.0')
        con('Text', (1, 1, 1))
        con('Light', (1, 1, 1))
        con('Image', (1, 1, 1))
        con('b_rad', '1.0')
        con('b_int', '1.0')
        con('b_mode', 0)
        con('b_inw', True)

        sv = bui.scrollwidget(
            parent=w,
            position=(30, 50),
            color=var('bg'),
            size=(140, 320)
        )
        
        s.cv = cw(
            parent=sv,
            background=False,
            size=(120, 280)
        )

        s.rp = cw(
            parent=w,
            position=(180, 50),
            size=(390, 320),
            background=False
        )

        s.modes = ['Prop Builder', 'Text Builder', 'Light Builder', 'Image Builder', 'Node Tools', 'Fun Tools']
        s.m_btns = []
        for i, m in enumerate(s.modes):
            b = bw(
                p=s.cv,
                pos=(5, 240 - 45 * i),
                size=(110, 40),
                label=m,
                oac=bs.CallPartial(s.set_mode, i)
            )
            s.m_btns.append(b)

        s.kids = []
        s.set_mode(var('b_mode'))

        if s.ex:
            p, btype = s.ex
            for i in range(3):
                var(f'pos{i}', str(p[i]))

    def clear(s):
        for k in s.kids:
            if hasattr(k, 'delete'):
                k.delete()
        s.kids.clear()

    def set_mode(s, m):
        var('b_mode', m)
        s.clear()

        for i, b in enumerate(s.m_btns):
            bw(b, color=(0, 1, 0) if i == m else var('bg'))

        s.kids.append(tw(
            p=s.rp, pos=(195, 290), text=s.modes[m],
            h_align='center', scale=1.3, color=(0.1, 0.7, 1)
        ))

        bx = 100
        bw_sz = 250
        bh = 35
        tx = 20
        lw = bx - tx - 5

        r0y = 220
        r1y = 175
        r2y = 130
        r3y = 85

        def lbl(txt, ypos):
            s.kids.append(tw(p=s.rp, pos=(tx, ypos), size=(lw, bh), text=txt, v_align='center', h_align='left', maxwidth=lw))

        if m == 0:
            p0y,p1y,p2y,p3y,p4y,p5y = 245,210,175,140,105,70

            lbl('Mesh:', p0y)
            bm = bw(p=s.rp, pos=(bx, p0y), size=(bw_sz, bh), label=var('b_mesh'))
            bw(bm, oac=bs.CallPartial(MeshPicker, source=bm, pipe=s.pick_mesh, extra=bm))
            s.kids.append(bm)

            lbl('Texture:', p1y)
            bt = bw(p=s.rp, pos=(bx, p1y), size=(bw_sz, bh), label=var('b_tex'))
            bw(bt, oac=bs.CallPartial(TexPicker, source=bt, pipe=s.pick_tex))
            s.b_tex_btn = bt
            s.kids.append(bt)

            lbl('Body:', p2y)
            bb = ctw(
                p=s.rp, pos=(bx, p2y), size=(bw_sz, bh), allow=True,
                hint='crate/sphere/puck', conf='b_body', text=var('b_body')
            )
            s.kids.extend([bb.widget, bb.widget2])

            lbl('Gravity:', p3y)
            bg = ctw(
                p=s.rp, pos=(bx, p3y), size=(bw_sz, bh), allow='-0.123456789',
                conf='b_grav', text=var('b_grav'), hint='Float'
            )
            s.kids.extend([bg.widget, bg.widget2])

            lbl('Mesh Scale:', p4y)
            bms = ctw(
                p=s.rp, pos=(bx, p4y), size=(bw_sz, bh), allow='0.123456789',
                conf='b_mscale', text=var('b_mscale'), hint='Float'
            )
            s.kids.extend([bms.widget, bms.widget2])

            lbl('Body Scale:', p5y)
            bbs = ctw(
                p=s.rp, pos=(bx, p5y), size=(bw_sz, bh), allow='0.123456789',
                conf='b_bscale', text=var('b_bscale'), hint='Float'
            )
            s.kids.extend([bbs.widget, bbs.widget2])

            bp = bw(
                p=s.rp, pos=(115, 25), size=(160, 45), label='Map & Build',
                icon=bui.gettexture('cursor'), oac=bs.CallPartial(s.map_it, 'prop')
            )
            s.kids.append(bp)

        elif m == 1:
            lbl('Text:', r0y)
            btxt = ctw(
                p=s.rp, pos=(bx, r0y), size=(bw_sz, bh), allow=True,
                conf='b_txt', text=var('b_txt'), hint='String'
            )
            s.kids.extend([btxt.widget, btxt.widget2])

            lbl('Color:', r1y)
            bc = bw(p=s.rp, pos=(bx, r1y), size=(50, bh), color=var('Text'))
            bw(bc, oac=bs.CallPartial(
                ColorPicker, in_source=bc, id='Text', what='Text', id2='Text',
                chr='char', on_back=lambda: None, mode=2
            ))
            s.kids.append(bc)

            lbl('Scale:', r2y)
            bscl = ctw(
                p=s.rp, pos=(bx, r2y), size=(bw_sz, bh), allow='0.123456789',
                conf='b_scl', text=var('b_scl'), hint='Float'
            )
            s.kids.extend([bscl.widget, bscl.widget2])

            ck = chk(
                parent=s.rp, position=(bx, r3y + 5), size=(150, 30),
                value=bool(var('b_inw')), text='In World (3D)',
                on_value_change_call=bs.CallPartial(s.toggle_inw)
            )
            s.kids.append(ck)

            bp = bw(
                p=s.rp, pos=(115, 25), size=(160, 45), label='Map & Build',
                icon=bui.gettexture('cursor'), oac=bs.CallPartial(s.map_it, 'text')
            )
            s.kids.append(bp)

        elif m == 2:
            lbl('Color:', r0y)
            bc = bw(p=s.rp, pos=(bx, r0y), size=(50, bh), color=var('Light'))
            bw(bc, oac=bs.CallPartial(
                ColorPicker, in_source=bc, id='Light', what='Light', id2='Light',
                chr='char', on_back=lambda: None, mode=2
            ))
            s.kids.append(bc)

            lbl('Radius:', r1y)
            brad = ctw(
                p=s.rp, pos=(bx, r1y), size=(bw_sz, bh), allow='0.123456789',
                conf='b_rad', text=var('b_rad'), hint='Float'
            )
            s.kids.extend([brad.widget, brad.widget2])

            lbl('Intensity:', r2y)
            bint = ctw(
                p=s.rp, pos=(bx, r2y), size=(bw_sz, bh), allow='0.123456789',
                conf='b_int', text=var('b_int'), hint='Float'
            )
            s.kids.extend([bint.widget, bint.widget2])

            bp = bw(
                p=s.rp, pos=(115, 25), size=(160, 45), label='Map & Build',
                icon=bui.gettexture('cursor'), oac=bs.CallPartial(s.map_it, 'light')
            )
            s.kids.append(bp)

        elif m == 3:
            lbl('Texture:', r0y)
            bt = bw(p=s.rp, pos=(bx, r0y), size=(bw_sz, bh), label=var('b_tex'))
            bw(bt, oac=bs.CallPartial(TexPicker, source=bt, pipe=s.pick_tex))
            s.b_tex_btn = bt
            s.kids.append(bt)

            lbl('Color:', r1y)
            bc = bw(p=s.rp, pos=(bx, r1y), size=(50, bh), color=var('Image'))
            bw(bc, oac=bs.CallPartial(
                ColorPicker, in_source=bc, id='Image', what='Image', id2='Image',
                chr='char', on_back=lambda: None, mode=2
            ))
            s.kids.append(bc)

            lbl('Scale:', r2y)
            bscl = ctw(
                p=s.rp, pos=(bx, r2y), size=(bw_sz, bh), allow='0.123456789',
                conf='b_iscal', text=var('b_iscal'), hint='Float'
            )
            s.kids.extend([bscl.widget, bscl.widget2])

            bp = bw(
                p=s.rp, pos=(115, 25), size=(160, 45), label='Build (2D)',
                icon=bui.gettexture('cursor'), oac=bs.CallPartial(s.map_it, 'image')
            )
            s.kids.append(bp)

        elif m == 4:
            b1 = bw(
                p=s.rp, pos=(95, 215), size=(200, 45), label='Pick & Edit',
                icon=bui.gettexture('menuIcon')
            )
            bw(b1, oac=bs.CallPartial(NodePicker, source=b1, pipe=lambda n: NodeManager(node=n, source=b1)))
            s.kids.append(b1)

            b2 = bw(
                p=s.rp, pos=(95, 160), size=(200, 45), label='Pick & Delete',
                icon=bui.gettexture('crossOut')
            )
            bw(b2, oac=bs.CallPartial(
                NodePicker, source=b2,
                pipe=lambda n: (n.delete(), ding(), push('Node Deleted!', color=(1, 0, 0)))
            ))
            s.kids.append(b2)

            b3 = bw(
                p=s.rp, pos=(95, 105), size=(200, 45), label='Pick & Attach Light',
                icon=bui.gettexture('star')
            )
            bw(b3, oac=bs.CallPartial(NodePicker, source=b3, pipe=s.attach_light))
            s.kids.append(b3)

            b4 = bw(
                p=s.rp, pos=(95, 50), size=(200, 45), label='Pick & Scale Up',
                icon=bui.gettexture('upButton')
            )
            bw(b4, oac=bs.CallPartial(NodePicker, source=b4, pipe=s.scale_up))
            s.kids.append(b4)

        elif m == 5:
            b1 = bw(
                p=s.rp, pos=(95, 215), size=(200, 45), label='Rain Current Prop',
                icon=bui.gettexture('downButton')
            )
            bw(b1, oac=s.rain_props)
            s.kids.append(b1)

            b2 = bw(
                p=s.rp, pos=(95, 160), size=(200, 45), label='Clear All Props',
                icon=bui.gettexture('crossOut')
            )
            bw(b2, oac=bs.CallPartial(s.clear_nodes, 'prop'))
            s.kids.append(b2)

            b3 = bw(
                p=s.rp, pos=(95, 105), size=(200, 45), label='Clear All Texts',
                icon=bui.gettexture('crossOut')
            )
            bw(b3, oac=bs.CallPartial(s.clear_nodes, 'text'))
            s.kids.append(b3)

            b4 = bw(
                p=s.rp, pos=(95, 50), size=(200, 45), label='Clear All Images',
                icon=bui.gettexture('crossOut')
            )
            bw(b4, oac=bs.CallPartial(s.clear_nodes, 'image'))
            s.kids.append(b4)

    def toggle_inw(s, val):
        var('b_inw', val)

    def pick_mesh(s, idx, btn):
        m = MESH()[idx]
        var('b_mesh', m)
        bw(btn, label=m)

    def pick_tex(s, idx):
        t = ALL()[idx]
        var('b_tex', t)
        if hasattr(s, 'b_tex_btn') and s.b_tex_btn.exists():
            bw(s.b_tex_btn, label=t)

    def map_it(s, btype):
        if btype == 'image' or (btype == 'text' and not var('b_inw')):
            s.mapper = Mapper2D(
                pipe=bs.CallPartial(s.dispatch, btype),
                pos=getpos()[:2],
                on_exit=bs.CallPartial(s.reopen, btype)
            )
        else:
            s.mapper = Mapper(
                pipe=bs.CallPartial(s.dispatch, btype),
                pos=getpos(),
                on_exit=bs.CallPartial(s.reopen, btype),
                build=True
            )
        None if s.mapper.tired else cw(s.w, transition='out_right')

    """Reopen the Build window at the position mapping ended on, once
    the mapper is dismissed via bomb."""
    def reopen(s, btype, p):
        Coolbox(fb='Build', fake=True, extra=(p, btype))

    """Build directly at a mapped position - no menu/window round-trip,
    so this is safe to call repeatedly (e.g. once per punch) without
    tripping the Coolbox-already-running guard."""
    def dispatch(s, btype, p):
        {
            'prop': s.do_prop,
            'text': s.do_text,
            'light': s.do_light,
            'image': s.do_image,
        }[btype](p)

    def do_prop(s, pos, silent=False):
        with bs.get_foreground_host_activity().context:
            o = bs_gameutils.SharedObjects.get()
            try:
                bs.newnode('prop', attrs={
                    'position': pos,
                    'mesh': bs.getmesh(var('b_mesh')),
                    'color_texture': bs.gettexture(var('b_tex')),
                    'body': var('b_body'),
                    'materials': [o.object_material, o.footing_material],
                    'reflection': 'soft',
                    'reflection_scale': [0.5],
                    'gravity_scale': float(var('b_grav')),
                    'mesh_scale': float(var('b_mscale')),
                    'body_scale': float(var('b_bscale'))
                })
                if not silent:
                    SPARK(pos)
                    ding()
                    push('Prop Built!', color=(0, 1, 0))
            except Exception as e:
                err(f"Build Failed: {e}")

    def do_text(s, pos):
        in_w = var('b_inw')
        with bs.get_foreground_host_activity().context:
            try:
                n = bs.newnode('text', attrs={
                    'text': var('b_txt'),
                    'color': var('Text'),
                    'scale': float(var('b_scl')),
                    'in_world': in_w,
                    'h_align': 'center'
                })
                if in_w:
                    n.position = pos
                    SPARK(pos)
                else:
                    n.position = (pos[0], pos[1])
                ding()
                push('Text Built!', color=(0, 1, 0))
            except Exception as e:
                err(f"Build Failed: {e}")

    def do_light(s, pos):
        with bs.get_foreground_host_activity().context:
            try:
                bs.newnode('light', attrs={
                    'position': pos,
                    'color': var('Light'),
                    'radius': float(var('b_rad')),
                    'intensity': float(var('b_int'))
                })
                SPARK(pos)
                ding()
                push('Light Built!', color=(0, 1, 0))
            except Exception as e:
                err(f"Build Failed: {e}")

    def do_image(s, pos):
        try:
            scl = float(var('b_iscal'))
            with bs.get_foreground_host_activity().context:
                bs.newnode('image', attrs={
                    'position': (pos[0], pos[1]),
                    'texture': bs.gettexture(var('b_tex')),
                    'color': var('Image'),
                    'scale': (scl, scl),
                    'absolute_scale': True
                })
            ding()
            push('Image Built!', color=(0, 1, 0))
        except Exception as e:
            err(f"Build Failed: {e}")

    def attach_light(s, n):
        with bs.get_foreground_host_activity().context:
            l = bs.newnode('light', owner=n, attrs={
                'color': (random.random(), random.random(), random.random()),
                'radius': 1.2,
                'intensity': 1.0
            })
            n.connectattr('position', l, 'position')
        ding()
        push('Light Attached!', color=(1, 1, 0))

    def scale_up(s, n):
        with bs.get_foreground_host_activity().context:
            if hasattr(n, 'mesh_scale'):
                v = n.mesh_scale
                n.mesh_scale = [i * 1.5 for i in v] if isinstance(v, (list, tuple)) else v * 1.5
            if hasattr(n, 'scale'):
                v = n.scale
                n.scale = [i * 1.5 for i in v] if isinstance(v, (list, tuple)) else v * 1.5
        ding()
        push('Node Scaled Up!', color=(0, 1, 0))

    def clear_nodes(s, t):
        c = 0
        with bs.get_foreground_host_activity().context:
            for n in bs.getnodes():
                if n and n.getnodetype() == t and n != bs.get_foreground_host_activity().globalsnode:
                    n.delete()
                    c += 1
        bui.getsound('shieldDown').play()
        push(f'Cleared {c} {t}s!', color=(1, 0.5, 0))

    def rain_props(s):
        p = getpos()
        def drop():
            if not s.w.exists():
                return
            rp = (p[0] + random.uniform(-6, 6), p[1] + 15, p[2] + random.uniform(-6, 6))
            s.do_prop(rp, True)
        
        for i in range(25):
            bui.apptimer(i * 0.1, drop)
            
        bui.getsound('spawn').play()
        push('Raining Props!', color=(0, 1, 1))

@NEW
class Camera:
    """Camera control panel"""

    def __init__(s, *a):
        w = s.w = a[0]
        s.live = False
        s.live_timer = None
        s.manual = False

        # --- Position inputs ---
        tw(p=w, pos=(50, 335), text='Position', h_align='center', size=(150, 25))
        s.pos_inputs = []
        for i, label in enumerate(['X', 'Y', 'Z']):
            tw(p=w, pos=(50, 305 - i*40), text=label, size=(20, 30), v_align='center')
            t = ctw(
                p=w, pos=(75, 298 - i*40), size=(120, 35),
                allow='-0.123456789', hint=f'Pos {label}',
                conf=f'cam_pos{i}', text=str(round(_ba.get_camera_position()[i], 2))
            )
            s.pos_inputs.append(t)

        # --- Target inputs ---
        tw(p=w, pos=(230, 335), text='Target', h_align='center', size=(150, 25))
        s.tar_inputs = []
        for i, label in enumerate(['X', 'Y', 'Z']):
            tw(p=w, pos=(230, 305 - i*40), text=label, size=(20, 30), v_align='center')
            t = ctw(
                p=w, pos=(255, 298 - i*40), size=(120, 35),
                allow='-0.123456789', hint=f'Tar {label}',
                conf=f'cam_tar{i}', text=str(round(_ba.get_camera_target()[i], 2))
            )
            s.tar_inputs.append(t)

        # --- Manual mode checkbox ---
        s.man_chk = chk(
            parent=w, position=(410, 340),
            text='Manual', size=(150, 30),
            value=False,
            on_value_change_call=s.set_manual
        )

        # --- Live preview toggle ---
        s.b_live = bw(
            p=w, pos=(410, 290), size=(150, 40),
            label='Live Preview', icon=bui.gettexture('replayIcon'),
            oac=s.toggle_live
        )

        # --- Arrow controls ---
        # XZ plane (position)
        arrows = [
            ('Z-',  (460, 245), (0, 0, -1)),
            ('X-',  (410, 195), (-1, 0, 0)),
            ('·',   (460, 195), None),
            ('X+',  (510, 195), (1, 0, 0)),
            ('Z+',  (460, 145), (0, 0,  1)),
            ('Y+',  (560, 195), (0, 1, 0)),
            ('Y-',  (560, 145), (0, -1, 0)),
        ]
        labels = ['↑', '←', '·', '→', '↓', 'Y↑', 'Y↓']
        for (lbl, pos, delta), txt in zip(arrows, labels):
            if delta is None:
                tw(p=w, pos=pos, text='✛', h_align='center', size=(40, 40), v_align='center', color=(0.4, 0.4, 0.4))
                continue
            bw(
                p=w, pos=pos, size=(40, 40),
                label=txt, text_scale=1.1,
                oac=bs.CallPartial(s.nudge, delta),
                repeat=True
            )

        # Step size
        tw(p=w, pos=(50, 155), text='Step:', size=(50, 30), v_align='center')
        s.step_t = ctw(
            p=w, pos=(100, 148), size=(90, 35),
            allow='0.123456789', hint='Step',
            conf='cam_step', text=var('cam_step') or '0.5'
        )

        # Target mode toggle
        s.tar_mode = False
        s.b_mode = bw(
            p=w, pos=(50, 105), size=(150, 35),
            label='Moving: Pos', oac=s.toggle_mode
        )

        # --- Apply / Reset / Sync ---
        bw(p=w, pos=(220, 105), size=(120, 35),
           label='Apply', icon=bui.gettexture('settingsIcon'),
           oac=s.apply)

        bw(p=w, pos=(350, 105), size=(120, 35),
           label='Sync', icon=bui.gettexture('replayIcon'),
           oac=s.sync)

        bw(p=w, pos=(50, 55), size=(150, 35),
           label='Reset Camera', icon=bui.gettexture('replayIcon'),
           oac=s.reset)

        bw(p=w, pos=(220, 55), size=(250, 35),
           label='Pick Node → Focus', icon=bui.gettexture('star'),
           oac=s.pick_focus)

        # init sync
        s.sync()

    def get_pos(s):
        return tuple(float(s.pos_inputs[i].get_text() or '0') for i in range(3))

    def get_tar(s):
        return tuple(float(s.tar_inputs[i].get_text() or '0') for i in range(3))

    def set_manual(s, v):
        s.manual = v
        _ba.set_camera_manual(v)

    def toggle_mode(s):
        s.tar_mode = not s.tar_mode
        bw(s.b_mode, label=f"Moving: {'Tar' if s.tar_mode else 'Pos'}")
        bui.getsound('deek').play()

    def toggle_live(s):
        s.live = not s.live
        bw(s.b_live, color=(0, 0.6, 0) if s.live else var('bg'))
        if s.live:
            s.live_timer = bui.AppTimer(0.02, s._live_tick, repeat=True)
            bui.getsound('ding').play()
        else:
            s.live_timer = None
            bui.getsound('tap').play()

    def _live_tick(s):
        if not s.w.exists() or s.w.transitioning_out:
            s.live_timer = None
            return
        try:
            p = s.get_pos()
            t = s.get_tar()
            if s.manual:
                _ba.set_camera_position(*p)
            _ba.set_camera_target(*t)
        except Exception:
            pass

    def nudge(s, delta):
        step = float(s.step_t.get_text() or '0.5')
        inputs = s.tar_inputs if s.tar_mode else s.pos_inputs
        for i in range(3):
            if delta[i] == 0:
                continue
            cur = float(inputs[i].get_text() or '0')
            inputs[i].set_text(str(round(cur + delta[i] * step, 3)))
        if s.live:
            s._live_tick()

    def apply(s):
        try:
            p = s.get_pos()
            t = s.get_tar()
        except ValueError:
            btw('Invalid input!')
            return
        if s.manual:
            _ba.set_camera_position(*p)
        _ba.set_camera_target(*t)
        ding()
        push('Camera applied!', color=(0, 1, 0))

    def sync(s):
        p = _ba.get_camera_position()
        t = _ba.get_camera_target()
        for i in range(3):
            s.pos_inputs[i].set_text(str(round(p[i], 3)), silent=True)
            s.tar_inputs[i].set_text(str(round(t[i], 3)), silent=True)
        bui.getsound('tap').play()

    def reset(s):
        _ba.set_camera_manual(False)
        chk(s.man_chk, value=False)
        s.manual = False
        if s.live:
            s.toggle_live()
        s.sync()
        ding()
        push('Camera reset!', color=(0, 1, 0))

    def pick_focus(s):
        NodePicker(
            source=s.w,
            pipe=s._focus_on,
            allow='3D'
        )

    def _focus_on(s, n):
        try:
            p = n.position
        except Exception:
            btw('Node has no position!')
            return
        for i in range(3):
            s.tar_inputs[i].set_text(str(round(p[i], 3)), silent=True)
        _ba.set_camera_target(*p)
        FOCUS(p, 2)
        ding()


@NEW
class Scene:
    """Scene control: map, tint presets"""

    def __init__(s, *a):
        w = s.w = a[0]

        # MAP (left: x=40..290)
        assert bui.app.classic is not None
        maps = sorted(bui.app.classic.maps.keys())

        s.sel_map = None
        s.map_btns = []
        ROW = 32
        content_h = max(260, len(maps) * ROW)

        s._scroll = bui.scrollwidget(
            parent=w, position=(40, 110),
            size=(245, 260), color=var('bg'),
            border_opacity=0.4
        )
        s._cv = cw(parent=s._scroll, background=False,
                   size=(225, content_h))

        for i, m in enumerate(maps):
            y = content_h - ROW - i * ROW
            b = bw(
                p=s._cv, pos=(0, y), size=(225, ROW - 2),
                label=m, text_scale=0.75,
                oac=bs.CallPartial(s.select_map, i, m)
            )
            s.map_btns.append(b)

        s.b_switch = bw(
            p=w, pos=(40, 60), size=(118, 42),
            label='Switch Map', icon=bui.gettexture('levelIcon'),
            oac=s.do_map
        )
        s.b_mapnode = bw(
            p=w, pos=(166, 60), size=(118, 42),
            label='Map Node', icon=bui.gettexture('settingsIcon'),
            oac=s.map_node
        )

        # ── TINT (right top: x=305..555) ─────────────────────
        bw(p=w, pos=(305, 332), size=(120, 40),
           label='× 1.1', text_scale=0.9,
           oac=bs.CallPartial(s.mult_tint, 1.1))
        bw(p=w, pos=(433, 332), size=(120, 40),
           label='÷ 1.1', text_scale=0.9,
           oac=bs.CallPartial(s.mult_tint, 1 / 1.1))

        bw(p=w, pos=(305, 284), size=(250, 40),
           label='Reset Tint', icon=bui.gettexture('replayIcon'),
           oac=s.reset_tint)

        # ── TINT PRESETS (right bottom: x=305..555) ──────────
        presets = [
            ('Neutral', (1.0, 1.0, 1.0)),
            ('Warm',    (1.3, 1.0, 0.8)),
            ('Cold',    (0.8, 0.9, 1.3)),
            ('Dusk',    (1.2, 0.8, 0.6)),
            ('Horror',  (0.5, 0.7, 0.5)),
            ('Void',    (0.3, 0.3, 0.5)),
            ('Sunset',  (1.3, 0.85, 0.6)),
            ('Frost',   (0.85, 1.0, 1.2)),
            ('Toxic',   (0.6, 1.2, 0.5)),
        ]
        s.preset_btns = []
        for i, (lbl, col) in enumerate(presets):
            b = bw(
                p=w,
                pos=(305 + (i % 3) * 84, 238 - (i // 3) * 44),
                size=(78, 38), label=lbl,
                color=col, oac=bs.CallPartial(s.set_tint, col)
            )
            s.preset_btns.append(b)

        s.b_custom_tint = bw(
            p=w, pos=(305, 60), size=(250, 42),
            label='Custom Tint', icon=bui.gettexture('settingsIcon'),
            oac=s.open_tint
        )

    # ── helpers ───────────────────────────────────────────────

    def _glob(s):
        return bs.get_foreground_host_activity().globalsnode

    # tint

    def open_tint(s):
        try:
            c = s._glob().tint
        except Exception:
            c = (1.0, 1.0, 1.0)
        var('scene_tint', c)
        var('scene_tintRed',   str(round(c[0], 4)))
        var('scene_tintGreen', str(round(c[1], 4)))
        var('scene_tintBlue',  str(round(c[2], 4)))
        ColorPicker(
            in_source=s.b_custom_tint,
            id='scene_tint', what='scene_tint',
            id2='scene_tint', chr='char', mode=2,
            on_back=s.apply_tint
        )

    def apply_tint(s):
        c = var('scene_tint') or (1.0, 1.0, 1.0)
        with bs.get_foreground_host_activity().context:
            s._glob().tint = c
        ding()
        push('Tint applied!', color=(0, 1, 0))

    def mult_tint(s, factor):
        with bs.get_foreground_host_activity().context:
            c = s._glob().tint
            nc = tuple(c[i] * factor for i in range(3))
            s._glob().tint = nc
        ding()

    def reset_tint(s):
        with bs.get_foreground_host_activity().context:
            s._glob().tint = (1.0, 1.0, 1.0)
        ding()
        push('Tint reset!', color=(0, 1, 0))

    def set_tint(s, col):
        try:
            with bs.get_foreground_host_activity().context:
                s._glob().tint = col
        except Exception as e:
            err(str(e))
            return
        ding()
        push('Tint set!', color=col)

    # map

    def select_map(s, i, name):
        for idx, b in enumerate(s.map_btns):
            bw(b, color=(0.0, 0.45, 0.0) if idx == i else var('bg'))
        s.sel_map = name
        bui.getsound('tap').play()

    def do_map(s):
        if not s.sel_map:
            btw('Pick a map first!')
            return
        try:
            s._change_map(s.sel_map)
            ding()
            push(f'Map → {s.sel_map}!', color=(0, 1, 0))
        except Exception as e:
            err(str(e))

    def map_node(s):
        try:
            NodeManager(
                node=bs.get_foreground_host_activity().map.node,
                source=s.b_mapnode
            )
        except Exception:
            btw('Map has no main node!')

    def _change_map(s, ma):
        from bascenev1lib.gameutils import SharedObjects
        _act = bs.get_foreground_host_activity()
        old_map = _act.map
        cls = bs.get_map_class(ma)
        with _act.context:
            if type(old_map) in _act.preloads:
                del _act.preloads[type(old_map)]
            for attr in dir(old_map):
                if not attr.startswith('_') and attr not in [
                    'node', 'activity', 'getactivity', 'handlemessage',
                    'on_expire', 'autoretain', 'is_alive', 'exists'
                ]:
                    try:
                        val = getattr(old_map, attr)
                        if not callable(val):
                            if hasattr(val, 'delete') and hasattr(val, 'exists'):
                                try:
                                    if val.exists(): val.delete()
                                except Exception:
                                    pass
                            delattr(old_map, attr)
                    except Exception:
                        pass
            _act.preloads[cls] = preload = cls.on_preload()
            shared = SharedObjects.get()
            for node in bs.getnodes():
                if node.getnodetype() == 'terrain' and node != old_map.node:
                    try: node.delete()
                    except Exception: pass
            for attr in ['bottom', 'floor', 'stands', 'background', 'railing',
                         'bg_collide', 'stem', 'player_wall', 'bg2', 'node_bottom']:
                if hasattr(old_map, attr):
                    delattr(old_map, attr)
            if hasattr(old_map, 'node') and old_map.node:
                old_map.node.mesh = (
                    preload.get('mesh') or
                    preload.get('mesh_top') or
                    preload.get('meshes', [None])[0]
                )
                old_map.node.color_texture = preload['tex']
                old_map.node.collision_mesh = preload['collision_mesh']
                old_map.node.materials = (
                    [shared.footing_material, preload['ice_material']]
                    if 'ice_material' in preload
                    else [shared.footing_material]
                )
            if 'mesh_bottom' in preload or 'bottom_mesh' in preload:
                old_map.bottom = bs.newnode('terrain', attrs={
                    'mesh': preload.get('mesh_bottom') or preload.get('bottom_mesh'),
                    'lighting': False, 'color_texture': preload['tex']
                })
            if 'meshes' in preload and len(preload['meshes']) > 1:
                mats = (
                    [shared.footing_material, preload['ice_material']]
                    if 'ice_material' in preload else [shared.footing_material]
                )
                old_map.floor = bs.newnode('terrain', attrs={
                    'mesh': preload['meshes'][1],
                    'color_texture': preload['tex'],
                    'opacity': 0.92,
                    'opacity_in_low_or_medium_quality': 1.0,
                    'materials': mats
                })
            if 'meshes' in preload and len(preload['meshes']) > 2:
                old_map.stands = bs.newnode('terrain', attrs={
                    'mesh': preload['meshes'][2],
                    'visible_in_reflections': False,
                    'color_texture': preload.get('stands_tex', preload['tex'])
                })
            if 'mesh_bg' in preload or 'bgmesh' in preload:
                old_map.background = bs.newnode('terrain', attrs={
                    'mesh': preload.get('mesh_bg') or preload.get('bgmesh'),
                    'lighting': False, 'background': True,
                    'color_texture': preload.get('mesh_bg_tex') or preload.get('bgtex')
                })
            if 'bgmesh2' in preload:
                old_map.bg2 = bs.newnode('terrain', attrs={
                    'mesh': preload['bgmesh2'],
                    'lighting': False, 'background': True,
                    'color_texture': preload.get('bgtex2', preload.get('tex'))
                })
            if 'railing_collision_mesh' in preload or 'bumper_collision_mesh' in preload:
                old_map.railing = bs.newnode('terrain', attrs={
                    'collision_mesh': (
                        preload.get('railing_collision_mesh') or
                        preload.get('bumper_collision_mesh')
                    ),
                    'materials': [shared.railing_material],
                    'bumper': True
                })
            if 'collide_bg' in preload:
                old_map.bg_collide = bs.newnode('terrain', attrs={
                    'collision_mesh': preload['collide_bg'],
                    'materials': [
                        shared.footing_material,
                        preload.get('bg_material'),
                        shared.death_material
                    ]
                })
            if 'stem_mesh' in preload:
                old_map.stem = bs.newnode('terrain', attrs={
                    'mesh': preload['stem_mesh'],
                    'lighting': False, 'color_texture': preload['tex']
                })
            if 'player_wall_collision_mesh' in preload and isinstance(bs.getsession(), bs.CoopSession):
                old_map.player_wall = bs.newnode('terrain', attrs={
                    'collision_mesh': preload['player_wall_collision_mesh'],
                    'affect_bg_dynamics': False,
                    'materials': [preload['player_wall_material']],
                })
            old_map.preloaddata = preload
            old_map.defs = cls.defs
            old_map.is_hockey = (
                hasattr(cls, 'is_hockey') or
                cls.name in ['Hockey Stadium', 'Lake Frigid']
            )
            old_map.is_flying = cls.name == 'Happy Thoughts'
            gnode = _act.globalsnode
            gnode.area_of_interest_bounds = (
                old_map.get_def_bound_box('area_of_interest_bounds') or
                (-1, -1, -1, 1, 1, 1)
            )
            bs.set_map_bounds(
                old_map.get_def_bound_box('map_bounds') or
                (-30, -10, -30, 30, 100, 30)
            )

            # old_map keeps its cached point lists from whichever map it was
            # first built for (Map.__init__ only computes these once) -- with
            # defs swapped to the new map's defs those lists are now stale,
            # so recompute them the same way Map.__init__ does or players will
            # spawn/teleport into the old map's (possibly void) coordinates.
            old_map.spawn_points = old_map.get_def_points('spawn') or [(0, 0, 0, 0, 0, 0)]
            old_map.ffa_spawn_points = old_map.get_def_points('ffa_spawn') or [(0, 0, 0, 0, 0, 0)]
            old_map.spawn_by_flag_points = old_map.get_def_points('spawn_by_flag') or [(0, 0, 0, 0, 0, 0)]
            flag_pts = old_map.get_def_points('flag') or [(0, 0, 0)]
            old_map.flag_points = [p[:3] for p in flag_pts]
            old_map.flag_points_default = old_map.get_def_point('flag_default') or (0, 1, 0)
            pu_pts = old_map.get_def_points('powerup_spawn') or [(0, 0, 0)]
            old_map.powerup_spawn_points = [p[:3] for p in pu_pts]
            old_map.tnt_points = [p[:3] for p in (old_map.get_def_points('tnt') or [])]

            # Teleport every live player to a fresh spawn point on the new
            # map so nobody is left standing over what is now empty space.
            for i, p in enumerate(_act.players):
                if p.actor and p.actor.node.exists():
                    pos = old_map.get_start_position(i)
                    p.actor.node.handlemessage(bs.StandMessage(pos, 0))

            # Also StandMessage every bot spawned via Coolbox (tracked in
            # activity.customdata), so they don't stay stuck in the void.
            for i, v in enumerate(_act.customdata.values()):
                if isinstance(v, Bot) and v.node and v.node.exists():
                    pos = old_map.get_start_position(i)
                    v.node.handlemessage(bs.StandMessage(pos, 0))

@NEW
class About:
    """About Coolbox"""
    def __init__(s, *a):
        w, x, y = a[0], a[1], a[2]

        tw(
            p=w, pos=(x/2, y-170), size=(0,0), text='COOLBOX',
            h_align='center', v_align='center', scale=3.2,
            color=(0.1,0.7,1), big=True
        )

        tw(
            p=w, pos=(x/2, y-270), size=(0,0), text='version 1.0',
            h_align='center', v_align='center', scale=0.9,
            color=var('t')
        )

        tw(
            p=w, pos=(x/2, y-305), size=(0,0), text='made with love and tea',
            h_align='center', v_align='center', scale=0.9,
            color=var('t')
        )

        tw(
            p=w, pos=(x/2, y-355), size=(0,0), text='special thanks to: YOU for trying coolbox!',
            h_align='center', v_align='center', scale=0.8, maxwidth=x*0.85,
            color=(1,0.85,0.3)
        )

# Dynamic Resources
# Stored as callabes and only called when needed
# Very beneficial for performance and memory
def D(): d = bui.app.classic.spaz_appearances; [d.pop(i) for i in d.copy() if i != 'Pascal' and d[i].default_color == (0.3,0.5,0.8)]; return d
_INIT_CWD = os.getcwd()
def BASE():
    app_py_dir = getattr(bui.app.env, "python_directory_app", None)
    if app_py_dir:
        base_from_app = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(app_py_dir))),
            "ba_data"
        )
        if os.path.exists(base_from_app):
            return base_from_app

    base_from_cwd = os.path.join(_INIT_CWD, "ba_data")
    if os.path.exists(base_from_cwd):
        return base_from_cwd

    return os.path.join(
        os.path.dirname(bui.app.env.cache_directory),
        "ballistica_files",
        "ba_data"
    )
#BASE = lambda: os.path.join(os.path.dirname(bui.app.env.cache_directory),'ballistica_files','ba_data')
NAME = lambda: list(D())
SPAZ = lambda: list(D().values())
KIDS = lambda: [i for i in bs.getnodes() if i.getnodetype() == 'spaz']
ALL = lambda: sorted([i[:-4] for i in os.listdir(os.path.join(BASE(),'textures'))])
AUDIO = lambda: sorted([i[:-4] for i in os.listdir(os.path.join(BASE(),'audio'))])
MESH = lambda: sorted([i[:-4] for i in os.listdir(os.path.join(BASE(),'meshes'))])
ICONS = lambda: [i.icon_texture for i in SPAZ()]
CTEX = lambda: [i.color_texture for i in SPAZ()]
def DIR(t): a = dir(SPAZ()[0]); b = []; [b.append(i) if i.endswith('_'+t) else None for i in a]; return b
CONS = lambda: [
    {lambda:getme(1):lambda:btw('Join the game first!')},
    {lambda:not pause():lambda:btw('Resume the game first!')}
]
def BRUH(): mem = SPAZ(); return [[mem[i].style for i in [8,11,12,13]],mem[1].style]

# String Resources
# Stored in disk, not in memory
# Lambda is called on runtime when needed
COLS = lambda: ['Main','Highlight','Name']
WHAT = lambda: ['Character','Colors','Sound','Mesh','Position','Name','Health']
BAD = lambda: ['punch_velocity','punch_position','punch_momentum_linear']
HOLDABLE = lambda: ['prop','spaz','flag']
ZZZ = lambda: [
    'zzz',
    'I sleep',
    'naah bro I\'m out',
    'Goonight',
    'I\'ll lie down here a bit',
    'U know what? zzz',
    'Eyes closed',
    'Do not disturb',
    'I\'ll take a nap',
    'Sleep. Here and now.',
    'x y zzzzzz...',
    'Good feeling, sleeping is.',
    'Too much for one day. I sleep.',
    'No. Just no. gn.',
    'Don\'t wake me up.',
    'Z for Zleep. zzz.'
]
SLOWDOWN = lambda: [
    'Take it easy blud',
    'Cool down pal',
    'At least look at it',
    'You don\'t have to spam',
    'But you just clicked me',
    'OK OK just stop spamming',
    'Slow down bullet-kun',
    'You like the sound huh?',
    'I disencourage spamming',
    'Nou I just randomized',
    'The cooldown is 0.2 sec, and you surpassed it',
    'You can\'t wait 0.2 seconds can you?',
    'Wait 0.2 seconds I know that\'s a lot to ask',
    'Go to spammer jail',
    'If you really like the sound then go play it in Listen menu',
    'Dun (that means cool down)',
    'Too fast this is.',
    'Hello bullet I\'m cool down',
    'Knock knock - no, cool down.',
    'So you think clicking faster is better?',
    'The delay between your clicks is less than 200ms\nYou must be proud',
    'Keep spamming, and I will keep blocking.',
    'Too fast eh',
    'A 0.2s delay is too much to ask?'
]
HOLDSELF = lambda: [
    'You sure like holding yourself lmfao',
    'You look funny that way',
    'Holding your own neck LOL',
    'Is that a new form of suicide',
    'What are you doing lmao'
]
CONSTR = lambda: [
    'Yes!',
    'Where should I go?',
    'Let\'s get this done',
    'Yessir',
    'Just don\'t get me killed',
    'What next?',
    'Initiate!',
    'Why me?',
    'Can\'t you pick someone else',
    'Fine. Where are we going?',
    'Ready as ever!',
    'Sir yessir!',
    'I don\'t have a good feeling about this',
    'Ready for some moves!',
    'You move, I move.',
    'Controls linked!'
]
NAH = lambda: [
    "You're not the host!",
    "Nice try, but you're not in charge here.",
    "Host privileges required.",
    "This doesn't open for just anyone.",
    "Sorry, locked for non-hosts.",
    "Access denied. Not yours to open.",
    "Only the host gets to play with the cool toys.",
    "You're not cool enough (not the host).",
    "Error 403: Hosts only.",
    "Host status required.",
    "Back away, citizen.",
    "You don't have the key.",
    "Host-exclusive. Sorry!",
    "You need host powers for this.",
    "Refuses to cooperate with non-hosts.",
    "Nice try. Host only though!",
    "Secrets are for the host's eyes only.",
    "Host authentication failed.",
    "You're missing the magic word: Host permissions.",
    "*clicks shut* Not for you!",
    "Only responds to the host.",
    "Permission denied. Host privileges not detected.",
    "This isn't for everyone... just the host.",
    "You wish you could open this, huh?",
    "Nope! Host access only.",
    "Admin powers not found.",
    "Unauthorized. Move along.",
    "The host would disapprove.",
    "Not happening without host status."
]

# Config
# Our database is babase.app.config
def var(s, v=None, cb=True):
    cfg = bui.app.config
    if cb: s = 'cb_'+s
    if v is None: return cfg.get(s,v)
    else:
        cfg[s] = v
        cfg.commit()
def con(n,v): var(n,v) if var(n) is None else None
def reset_conf(): cfg = bui.app.config; [(cfg.pop(c) if c.startswith('cb_') else None) for c in cfg.copy()]; cfg.commit()

# Patches
# These few lines save huge amounts of lines later
f = ba.PluginSubsystem.on_screen_size_change; ba.PluginSubsystem.on_screen_size_change = lambda *a,**k: (icw.on_resume(),f(*a,**k))
f = ba.PluginSubsystem.on_ui_scale_change; ba.PluginSubsystem.on_ui_scale_change = lambda *a,**k: (icw.on_resume(),f(*a,**k))
gos = lambda: bui.get_special_widget("overlay_stack")
chk = lambda *a,**k: (k.update({'color':var('bg'),'textcolor':var('t')}),bui.checkboxwidget(*a,**k))[1]
def bw(*a,cons={},oac=None,pos=None,p=None,**k):
    if cons:
        o = oac
        oac = lambda: None if None in [True if c() else [cons[c](),None][1] for c in cons] else o()
    None if len(a) else k.update({
        'label':k.get('label',''),
        'button_type':k.get('button_type','square'),
        'color':k.get('color',var('bg')),
        'textcolor':k.get('textcolor',var('t')),
        'enable_sound':k.get('nable_sound',False)
    })
    if pos: k['position'] = pos
    if p: k['parent'] = p
    if oac: k['on_activate_call'] = oac
    return bui.buttonwidget(*a,**k)
def cw(*a,**k):
    only(k,'color',var('bg'))
    only(k,'parent', gos())
    return bui.containerwidget(*a,**k)
def tw(*a,p=None,pos=None,**k):
    only(k,'color',var('t'))
    if p: k['parent'] = p
    if pos: k['position'] = pos
    return bui.textwidget(*a,**k)
def pbw(*a,tex=None,**k):
    b = bw(*a,**k)
    if tex: bw(b,tint_color=var(tex[0]) or (1,1,1),tint2_color=var(tex[1]) or (1,1,1))
    bw(b,color=(1,1,1),mask_texture=bui.gettexture('characterIconMask'))
    return b
def sbw(*a,**k):
    k.update({
        'label':k.get('label',''),
        'size':k.get('size',(43,43)),
        'iconscale':k.get('iconscale',1.2),
        'text_scale':k.get('text_scale',1.4)
    })
    b = bw(*a,**k)
    return b

# Mini tools
# May look dirty, but they're extremely useful
err = lambda t: (bui.getsound('error').play(),bs.broadcastmessage(t,color=(1,0,0)))
btw = lambda t: (bui.getsound('block').play(),bs.broadcastmessage(t,color=(1,1,0)))
darken = lambda c: (c[0]/2,c[1]/2,c[2]/2)
gc = lambda w: w.get_screen_space_center()
smol = lambda c: [i/255 for i in c]
huge = lambda c: [int(i*255) for i in c]
gun = lambda: bui.getsound('gunCocking').play()
ding = lambda: bui.getsound('dingSmallHigh').play()
UUID = lambda: str(uuid.uuid4())[:5]
def GA(f):
    with bs.get_foreground_host_activity().context: return f()

# CJK-packed seed system (ported from movi.py) - denser than plain digit strings
CJK_SEED_RANGES = (
    (0x3400, 0x4DBF),    # CJK Unified Ideographs Extension A
    (0x4E00, 0x9FFF),    # CJK Unified Ideographs (basic)
    (0xF900, 0xFAFF),    # CJK Compatibility Ideographs
    (0x2F800, 0x2FA1F),  # CJK Compatibility Ideographs Supplement
    (0x20000, 0x2A6DF),  # CJK Unified Ideographs Extension B
    (0x2A700, 0x2B73F),  # CJK Unified Ideographs Extension C
    (0x2B740, 0x2B81F),  # CJK Unified Ideographs Extension D
    (0x2B820, 0x2CEAF),  # CJK Unified Ideographs Extension E
    (0x2CEB0, 0x2EBEF),  # CJK Unified Ideographs Extension F
    (0x2EBF0, 0x2EE5F),  # CJK Unified Ideographs Extension I
    (0x30000, 0x3134F),  # CJK Unified Ideographs Extension G
    (0x31350, 0x323AF),  # CJK Unified Ideographs Extension H
    (0x323B0, 0x3347F),  # CJK Unified Ideographs Extension J
)
def _cjk_build_table():
    table = []
    cum = 0
    for lo,hi in CJK_SEED_RANGES:
        size = hi-lo+1
        table.append((cum,cum+size-1,lo))
        cum += size
    return table,cum
CJK_SEED_TABLE,CJK_SEED_BASE = _cjk_build_table()
def cjk_digit_to_char(d):
    for start,end,lo in CJK_SEED_TABLE:
        if start <= d <= end:
            return chr(lo+(d-start))
    raise ValueError(f'seed digit out of range: {d}')
def cjk_char_to_digit(c):
    cp = ord(c)
    cum = 0
    for lo,hi in CJK_SEED_RANGES:
        size = hi-lo+1
        if lo <= cp <= hi:
            return cum+(cp-lo)
        cum += size
    raise ValueError(f'not a valid seed character: {c!r}')
def cjk_encode_int(n):
    if n == 0: return cjk_digit_to_char(0)
    digits = []
    while n:
        n,r = divmod(n,CJK_SEED_BASE)
        digits.append(r)
    return ''.join(cjk_digit_to_char(d) for d in reversed(digits))
def cjk_decode_int(s):
    n = 0
    for c in s:
        n = n*CJK_SEED_BASE + cjk_char_to_digit(c)
    return n
def ENCODE(a):
    c=zlib.compress(json.dumps(a,separators=(',',':'),sort_keys=True).encode('utf-8'))
    return cjk_encode_int(int.from_bytes(c,'big'))
def DECODE(s):
    n=cjk_decode_int(s)
    b=n.to_bytes((n.bit_length()+7)//8,'big')
    return json.loads(zlib.decompress(b).decode('utf-8'))
hasm = lambda: bui.app.ui_v1.has_main_window()
c2h = lambda c: '#{:04x}{:04x}{:04x}'.format(*huge(c))
DLG = lambda n: n.getdelegate(object)
def h2c(h):
    h = h.lstrip('#')
    return smol([int(h[i:i+4],16) for i in [0,4,8]])
def push(t,**k):
    v = var('lpush') or []
    if t in v: t = f'{t} [x{v[1]}]'; v = [v[0],v[1]+1]
    else: v = [t,2]
    var('lpush',v)
    bs.broadcastmessage(t,top=True,**k)
def UIS(j=0):
    i = bui.app.ui_v1.uiscale
    return [[[2,1][i==bui.UIScale.MEDIUM],0][i==bui.UIScale.SMALL],i][j]
def only(k,v,d): k[v] = r = k.get(v,d); return r
def forbtn(w,b,xoff=0):
    p = gc(b)
    cw(w, scale_origin_stack_offset=(p[0]-xoff,p[1]))
def PASTE():
    try: return ba.clipboard_get_text()
    except: pass
def CHECK(v): d = DECODE(v); d[4]; return d
def RANDOM():
    mem = NAME()
    n = random.choice(mem)
    c = [[round(random.uniform(0,2),2) for i in range(3)] for i in range(3)]
    return SEED(n,n if n != mem[0] else random.choice(bs.get_random_names()),tuple(c[0]),tuple(c[1]),tuple(c[2]),fix=n)
def getme(actor=0):
    for p in bs.get_foreground_host_activity().players:
        if p.sessionplayer.inputdevice.client_id == -1:
            return p.actor if actor else p
def RESUME():
    u = bui.app.ui_v1
    c = bui.app.classic
    c.resume()
    u.clear_main_window()
    [z() for z in c.main_menu_resume_callbacks]
    c.main_menu_resume_callbacks.clear()
def npause(i=None): bs.get_foreground_host_activity().globalsnode.paused = i if i is not None else var('npp')
def pause(i=None):
    g = bs.get_foreground_host_activity().globalsnode
    if i is None: return g.paused
    g.paused = i
def FOCUS(p,i,node=0):
    FOC = 0
    def f():
        nonlocal FOC
        if FOC: return
        try: _ba.set_camera_target(*(p.position if node else p))
        except: return
        bui.apptimer(0.01,f)
    def g():
        nonlocal FOC
        FOC = 1
    f(); bui.apptimer(i, g)
def SPARK(p):
    with bs.get_foreground_host_activity().context:
        SND('ding',p)
        bs.emitfx(position=p,
               scale=1,
               count=70,
               chunk_type='spark')
def MESS(p):
    with bs.get_foreground_host_activity().context:
        SND('shatter',p)
        bs.emitfx(
            position=p,
            scale=1,
            count=30,
            spread=0.1,
            chunk_type='ice'
        )
def LOOK(p,on_found=lambda: None):
    d = math.dist(p,_ba.get_camera_target())/17
    h = bui.getsound('shieldUp')
    FOCUS(p,2)
    h.play() if d > 0.3 else None
    bui.apptimer(d, lambda: (None if pause() else SPARK(p), h.stop(), on_found()))
def getpos(): return rnd(tuple([float(var(f'pos{i}')) for i in range(3)]))
def rnd(p): return tuple([round(i,3) for i in p])
def SND(s,p,v=3):
    with bs.get_foreground_host_activity().context: bs.getsound(s).play(v,position=p)
def STATE(b=None):
    if b is None: return var('active')
    var('active',b)
def fixsounds(c=None,prf=''):
    c = c or var(f'{prf}char')
    n = NAME()
    [var(f'{prf}sound{i}',[n.index(c),0]) for i in range(len(DIR('sounds')))]
def fixmesh(c=None,prf=''):
    c = SPAZ()[NAME().index(c or var(f'{prf}char'))]
    mem = DIR('mesh'); z = range(len(mem))
    [var(f'{prf}mesh{i}',getattr(c,mem[i])) for i in z]
    var(f'{prf}ctex',c.color_texture)
    var(f'{prf}ctex2',c.color_mask_texture)
def fixall(c=None,prf=''): fixmesh(c,prf); fixsounds(c,prf)
def get_ctex(c): return SPAZ()[NAME().index(c)].color_texture
def get_ctex2(c): return SPAZ()[NAME().index(c)].color_mask_texture
def set_sounds(n,prf='',dr=None,aud=None,spa=None):
    a = dr or DIR(f'sounds')
    aud = aud or AUDIO()
    spa = spa or SPAZ()
    for i in range(len(a)):
        j = var(f'{prf}sound{i}')
        if not j: continue
        if j[1]: v = [bs.getsound(aud[j[0]])]
        else: v = [bs.getsound(k) for k in getattr(spa[j[0]],a[i])]
        setattr(n,a[i],v)
def mesh_seed():
    r = []
    mem = SPAZ()[NAME().index(var('char'))]
    ok = DIR('mesh')
    for i in range(len(ok)):
        c = var(f'mesh{i}') or getattr(mem,ok[i])
        r.append(c)
    return r+[var('ctex') or get_ctex(var('char')),var('ctex2') or get_ctex2(var('char'))]
def sound_seed(): return [var(f'sound{i}') for i in range(len(DIR('sounds')))]
def SEED(char,tchar,main,hl,name,fix=None): fixall(fix) if fix else None; return ENCODE([char,tchar,main,hl,name,mesh_seed(),sound_seed()])
def LN(d,o=None): me = o or getme(); [me.assigninput(getattr(ba.InputType,k), d[k]) for k in d]
def GSW(t): return _ba.get_string_width(t,suppress_warning=True)
def GETSIG(o):
    try: return f"Supported args: {list(inspect.signature(o).parameters.keys())}"
    except: return 'No signature found :('
def NTEX(n,tex=None):
    t = str(getattr(n,'color_texture','"black"'))
    f = t.find('"')+1
    c = t[f:t.find('"',f)].replace('Color','')
    b = c+'Icon' in (tex or ALL())
    return {
        'texture':bui.gettexture(c+['','Icon'][b]),
        'tint_texture':bui.gettexture(c+['','IconColorMask'][b]),
        'tint_color':getattr(n,'color',(1,1,1)),
        'tint2_color':getattr(n,'highlight',(1,1,1))
    },getattr(n,'name_color',(1,1,1)),c
def MK(ch,f,g):
    j = {'tint_color':var(f)}
    return [{
        'tint2_color':var(g),
        'mask_texture':bui.gettexture('characterIconMask'),
        'tint_texture':bui.gettexture(ch.icon_mask_texture),
        'texture':bui.gettexture(ch.icon_texture),
        **j
    },{'texture':bui.gettexture('buttonSquare'),**j}]
def clone(n,a):
    sp = n.source_player
    b = bs_playerspaz.PlayerSpaz(player=sp) if sp else Bot(NAME()[0])
    bn = b.node
    a.customdata[UUID()] = b
    mem = BAD()
    for i in dir(bn):
        if i.startswith('_') or i in mem: continue
        try: j = getattr(n,i)
        except AttributeError: continue
        if callable(j): continue
        try: setattr(bn,i,j)
        except RuntimeError: continue
    p = n.position
    p = (p[0],p[1]-0.6,p[2])
    b.handlemessage(bs.StandMessage(p,0))
    if sp:
        b.connect_controls_to_player()
        sp.actor = b
        print (sp.actor == b, sp.actor.node == bn)
    return [sp,bn]
def wga(f):
    with bs.get_foreground_host_activity().context: f()

# Init
# Our default values on first run
c = NAME()[0]
d = {
    'first': True,
    'char':c,
    'tchar':c,
    'mchar':c,
    't':(1,1,1),
    'bg':(0.13,0.13,0.13),
    'act':[],
    'egoto':'1',
    'wait':'1',
    'smove':'1.1',
    'sfollow':'1.1',
    'tmove':'10',
    'tfollow':'10',
    'goto':'1',
    'icall':0,
    'uis':None,
    'npp':1,
    'say':'hi please kill me',
    'tsay':'3',
    'dplprop':'prop',
    'dplname':'',
    'cconf3':1
}; [con(i,d[i]) for i in d]
for i in range(3):
    con(f'pos{i}','0')
    con(f'mpos{i}','0')
    con(f'move{i}','0')
    con(f'dpl{i}','0')
    con(f'bld{i}','0')
    con(f'cconf{i}',[1,1,0,1][i])
[con(f'cont{i}',True) for i in range(5)]
[con(f'what{i}',True) for i in range(len(WHAT()))]
var('active',False)
var('lpush','')
if var('first'): var('first',False); fixall(prf='m')
del c,d

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(ba.Plugin):
    def __init__(s):
        og = bui_igm.InGameMenuWindow._refresh_in_game
        def entry(s,*a,**k):
            r = og(s,*a,**k)
            w = bw(
               p=s._root_widget,
               pos=(-80, s._height-50),
               label="Coolbox",
               icon=bui.gettexture('chestIcon'),
               iconscale=0.8,
               scale=1.0,
               size=(100, 40)
            )
            bw(w, oac=lambda: Coolbox(fresh=True, in_source=w))
            return r
        bui_igm.InGameMenuWindow._refresh_in_game = entry
