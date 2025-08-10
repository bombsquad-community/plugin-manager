# Copyright 2025 - Solely by BrotherBoard
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Camera v1.0 - Say cheese.

Adds a button to pause menu. Camera is advanced
Camera allows you to change camera position and
target with a very easy graphical visualization
of how it would look like.
"""

from _babase import (
    get_display_resolution as GDR,
    clipboard_is_supported as CIS,
    set_camera_position as SCP,
    clipboard_set_text as COPY,
    set_camera_manual as SSCM,
    set_camera_target as SCT
)
from bascenev1 import (
    get_foreground_host_activity as ga,
    OutOfBoundsMessage,
    gettexture as gbt,
    getsound as gbs,
    timer as tick,
    Material,
    getmesh,
    newnode,
    animate,
    emitfx
)
from bauiv1 import (
    get_special_widget as gsw,
    containerwidget as cw,
    screenmessage as push,
    buttonwidget as bw,
    imagewidget as iw,
    textwidget as tw,
    gettexture as gt,
    apptimer as teck,
    getsound as gs,
    app as APP
)
from bauiv1lib.ingamemenu import InGameMenuWindow as igm
from babase import Plugin, InputType as IT
from math import sqrt, dist


class Camera:
    __doc__ = 'A simple camera.'
    __ins__ = None
    __lst__ = None
    __yes__ = False

    def __init__(s) -> None:
        c = s.__class__
        if c.__yes__:
            note('Stopped camera!', True)
            c.__ins__.done(talk=False)
            return
        c.__ins__ = s
        c.__yes__ = True
        if c.__lst__:
            SCM(False)
        s.stage = 0
        p = (0, 1, 0)
        s.tex = 'achievementCrossHair'
        s.kids = []
        s.okay = []
        with ga().context:
            s.M = Material()
            s.M.add_actions(
                conditions=(('they_are_older_than', 0)),
                actions=(
                    ('modify_part_collision', 'collide', False),
                    ('modify_part_collision', 'physical', False),
                    ('modify_part_collision', 'friction', 0),
                    ('modify_part_collision', 'stiffness', 0),
                    ('modify_part_collision', 'damping', 0)
                )
            )
            n = newnode(
                'prop',
                delegate=s,
                attrs={
                    'mesh': getmesh('tnt'),
                    'color_texture': gbt(s.tex),
                    'body': 'crate',
                    'reflection': 'soft',
                    'density': 4.0,
                    'reflection_scale': [1.5],
                    'shadow_size': 0.6,
                    'position': p,
                    'gravity_scale': 0,
                    'materials': [s.M],
                    'is_area_of_interest': True
                }
            )
            tick(0.15, animate(n, 'mesh_scale', {0: 2, 0.1: 0.5}).delete)
            gbs('powerup01').play(position=p)
            s.step = 0.01
        s.node = n
        s.wait = 0.001
        s.mode = 4
        s.llr = s.lud = 0.0
        s.overlay = Overlay()
        LN({
            'UP_DOWN': lambda a: s.manage(a),
            'LEFT_RIGHT': lambda a: s.manage(a, 1),
            'PICK_UP_PRESS': lambda: s.start(2),
            'JUMP_PRESS': lambda: s.start(0),
            'PICK_UP_RELEASE': lambda: s.stop(2),
            'JUMP_RELEASE': lambda: s.stop(0),
            'BOMB_PRESS': s.done,
            'BOMB_RELEASE': lambda: s.overlay.release(1),
            'PUNCH_PRESS': s.mark,
            'PUNCH_RELEASE': lambda: s.overlay.release(3),
        })
        s.move()
    """Write a tip"""
    def tip(s, t, p, h='left', b=True):
        n = newnode(
            'text',
            attrs={
                'in_world': True,
                'scale': 0.01,
                'flatness': 1,
                'color': (1, 1, 1),
                'shadow': 1.0,
                'position': p,
                'text': t,
                'h_align': h
            }
        )
        if b:
            s.kids.append(n)
        return n
    """Create a dot"""
    def dot(s, p, b=True, tex='black'):
        n = newnode(
            'prop',
            delegate=s,
            attrs={
                'mesh': getmesh('tnt'),
                'color_texture': gbt(tex),
                'body': 'crate',
                'mesh_scale': 0.1,
                'position': p,
                'gravity_scale': 0,
                'materials': [s.M],
            }
        )
        if b:
            s.kids.append(n)
        return n
    """Draw a line"""
    def line(s, p1, p2, i=2, tex='black'):
        x1, y1, z1 = p1
        x2, y2, z2 = p2
        n = dist(p1, p2)*i
        for i in range(1, int(n+1)):
            t = i/n
            x = x1+t*(x2-x1)
            y = y1+t*(y2-y1)
            z = z1+t*(z2-z1)
            s.kids.append(s.dot((x, y, z), tex=tex))
    """Mark"""
    def mark(s):
        if not s.stage:
            s.stage = 1
            p = s.getpos()
            s.p1 = (p[0]-0.01, p[1], p[2])
            s.okay.append(s.dot(s.p1, b=False))
            s.okay.append(
                s.tip(f'Camera position\n{tuple([round(i, 2) for i in s.p1])}', s.p1, b=False))
        else:
            [i.delete() for i in s.kids]
            s.kids.clear()
            p2 = s.p2 = s.getpos()

            r = GDR()
            w = r[0]/r[1]
            h = 1

            vd = sub(p2, s.p1)
            vd_n = norm(vd)

            t_up = (0, 1, 0)
            r_v = cross(vd_n, t_up)
            r_v_n = norm(r_v)

            up_v = cross(r_v_n, vd_n)
            up_v_n = norm(up_v)

            hw = w / 2.0
            hh = h / 2.0

            tr = add(p2, add(scale(r_v_n, hw), scale(up_v_n, hh)))
            tl = add(p2, add(scale(r_v_n, -hw), scale(up_v_n, hh)))
            br = add(p2, add(scale(r_v_n, hw), scale(up_v_n, -hh)))
            bl = add(p2, add(scale(r_v_n, -hw), scale(up_v_n, -hh)))

            s.line(s.p1, tr)
            s.line(s.p1, tl)
            s.line(s.p1, br)
            s.line(s.p1, bl)

            m = 4
            j = {'tex': 'crossOutMask'}
            s.line(tr, tl, m, **j)
            s.line(tl, bl, m, **j)
            s.line(bl, br, m, **j)
            s.line(br, tr, m, **j)

            s.tip(
                f'Your display\n{r[0]}x{r[1]} px\n{tuple([round(i, 2) for i in p2])}', tr, 'right')
            s.stage = 2
        s.overlay.press(3)
        tick(0.25, animate(s.node, 'mesh_scale', {0: 0.5, 0.1: 0.2, 0.2: 0.5}).delete)
        gbs('gunCocking').play(position=s.node.position)
    """Handle events"""
    def handlemessage(s, m):
        if isinstance(m, OutOfBoundsMessage):
            p = s.getpos()
            gbs('shatter').play(position=p)
            emitfx(
                scale=1,
                count=30,
                spread=0.1,
                position=p,
                chunk_type='ice'
            )
            s.destroy()
            note('Out of bounds!')
    """Destroy"""
    def destroy(s):
        with ga().context:
            n = s.node
            s.mode = 2
            n.delete()
        s.reset()
    """Reset input"""
    def reset(s):
        s.__class__.__yes__ = False
        me = getme()
        if not me:
            return
        me.resetinput()
        with ga().context:
            me.actor.connect_controls_to_player()
        [i.delete() for i in (s.kids+s.okay)]
    """Manage movement"""
    def manage(s, a, lr=0):
        if lr:
            s.llr = a
            return
        s.lud = a
    """Move"""
    def move(s):
        m = getme(1)
        if (not m) or m._dead:
            s.destroy()
        try:
            p = s.getpos()
        except:
            s.overlay.destroy()
            return
        s.setpos((p[0]+s.llr*s.step, p[1], p[2]-s.lud*s.step))
        s.overlay.up(*p, s.llr, s.lud)
        SCT(*p)
        teck(s.wait, s.move)
    """Start elevating"""
    def start(s, i):
        s.overlay.press(i)
        s.mode = i
        s.loop(i)
    """Keep elevating"""
    def loop(s, i):
        if s.mode != i:
            return
        try:
            p = list(s.node.position)
        except:
            return
        p[1] += s.step if i else -s.step
        s.node.position = tuple(p)
        teck(s.wait, lambda: s.loop(i))
    """Stop elevating"""
    def stop(s, i):
        s.overlay.release(i)
        s.mode = 4
    """Get position"""
    def getpos(s):
        return s.node.position
    """Set position"""
    def setpos(s, p):
        s.node.position = p
    """Done"""
    def done(s, talk=True):
        s.overlay.press(1)
        s.overlay.destroy()
        try:
            p = s.node.position
        except:
            return
        with ga().context:
            gbs('laser').play(position=p)
            tick(0.2, animate(s.node, 'mesh_scale', {0: 0.5, 0.08: 1, 0.2: 0}).delete)
            tick(0.2, s.node.delete)
        s.reset()
        if s.stage > 1 and talk:
            SCM(True)
            SCP(*s.p1)
            SCT(*s.p2)
            var('lp1', s.p1)
            var('lp2', s.p2)
            nice('Applied!')
        elif talk:
            note('Incomplete camera setup\nNo changes applied.')
        if s.__class__.__ins__ == s:
            s.__class__.__ins__ = None


"""Controls overlay"""


class Overlay:
    __lst__ = None
    """Place nodes"""
    def __init__(s):
        s.__class__.__lst__ = str(ga())
        s.colors = [
            [(0.2, 0.6, 0.2), (0.4, 1, 0.4)],
            [(0.6, 0, 0), (1, 0, 0)],
            [(0.2, 0.6, 0.6), (0.4, 1, 1)],
            [(0.6, 0.6, 0.2), (1, 1, 0.4)],
            [(0.3, 0.23, 0.5), (0.2, 0.13, 0.3)]
        ]
        s.pics = []
        s.texts = []
        s.pos = []
        s.nub = []
        s.old = [0, 0, 0]
        s.dead = False
        with ga().context:
            for i in range(4):
                j = ['Jump', 'Bomb', 'PickUp', 'Punch'][i]
                k = [600, 650, 600, 550][i]
                l = [170, 220, 270, 220][i]
                c = s.colors[i][0]
                n = newnode(
                    'image',
                    attrs={
                        'texture': gbt('button'+j),
                        'absolute_scale': True,
                        'position': (k, l),
                        'scale': (60, 60),
                        'color': c
                    }
                )
                s.pics.append(n)
                j = ['Down', 'Done', 'Up', 'Mark'][i]
                k = [600, 680, 600, 515][i]
                l = [115, 220, 325, 220][i]
                h = ['center', 'left', 'center', 'right'][i]
                v = ['bottom', 'center', 'top', 'center'][i]
                n = newnode(
                    'text',
                    attrs={
                        'text': j,
                        'position': (k, l),
                        'color': c,
                        'h_align': h,
                        'v_align': v
                    }
                )
                s.texts.append(n)
            for i in range(3):
                c = s.colors[[1, 0, 2][i]][0]
                n = newnode(
                    'text',
                    attrs={
                        'text': '0',
                        'position': (640, 155-30*i),
                        'color': c,
                        'h_align': 'left'
                    }
                )
                s.pos.append(n)
            s.np = (790, 140)
            for i in [0, 1]:
                j = [110, 60][i]
                n = newnode(
                    'image',
                    attrs={
                        'texture': gbt('nub'),
                        'absolute_scale': True,
                        'position': s.np,
                        'scale': (j, j),
                        'color': s.colors[4][i]
                    }
                )
                s.nub.append(n)
            s.fade()
    """Color overlays"""
    def set(s, i, c):
        s.pics[i].color = s.texts[i].color = c
    """Color position"""
    def pset(s, i, c):
        s.pos[i].color = c
    """Simulate pressed"""
    def press(s, i):
        s.set(i, s.colors[i][1])
        s.pics[i].opacity = 1.0
    """Simulate released"""
    def release(s, i):
        s.set(i, s.colors[i][0])
        s.pics[i].opacity = 0.7
    """Get all nodes"""
    def nodes(s):
        return s.pics+s.texts+s.pos+s.nub
    """Update position"""
    def up(s, x, y, z, lr, ud):
        new = [x, y, z]
        for i in range(3):
            c = s.colors[[1, 0, 2][i]]
            if s.old[i] == new[i]:
                s.pset(i, c[0])
                continue
            t = s.pos[i]
            t.text = str(round(new[i], 5))
            s.pset(i, c[1])
        s.old = new
        [setattr(s.nub[i], 'opacity', [[0.5, 0.2], [0.7, 0.3]][bool(lr or ud)][i]) for i in [0, 1]]
        p = s.np
        m = sqrt(lr**2+ud**2) or 1
        d = 25*min(sqrt(lr**2+ud**2), 1)
        lr /= m
        ud /= m
        s.nub[1].position = (p[0]+lr*d, p[1]+ud*d)
    """Fade"""
    def fade(s, i=0):
        if str(ga()) != s.__class__.__lst__:
            return
        mem = s.nodes()
        [tick(1, animate(n, 'opacity', {0: i, 0.5: abs(i-0.7)}).delete) for n in mem]
    """Destroy overlay"""
    def destroy(s):
        if s.dead:
            return
        s.dead = True
        with ga().context:
            tick(0.2, lambda: s.fade(0.7))
            tick(2, lambda: [n.delete() for n in s.nodes()])


# Mini tools
def note(t, b=False): return (push(t, color=(1, 1, 0)), gs('block').play() if b else None)
def nice(t): return (push(t, color=(0, 1, 0)), gs('dingSmallHigh').play())
def SCM(b): return (setattr(Camera, '__lst__', b), SSCM(b))
def scale(v, s): return (v[0]*s, v[1]*s, v[2]*s)
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])


def getme(actor=0):
    for p in ga().players:
        if p.sessionplayer.inputdevice.client_id == -1:
            return p.actor if actor else p


def LN(d): me = getme(); [me.assigninput(getattr(IT, k), d[k]) for k in d]


def RESUME():
    u = APP.ui_v1
    c = APP.classic
    c.resume()
    u.clear_main_window()
    [z() for z in c.main_menu_resume_callbacks]
    c.main_menu_resume_callbacks.clear()


def norm(v):
    a, b, c = v
    l = sqrt(a**2+b**2+c**2)
    return (0, 0, 0) if l == 0 else (a/l, b/l, c/l)


def var(s, v=None):
    c = APP.config
    s = 'cam_'+s
    if v is None:
        return c.get(s, v)
    c[s] = v
    c.commit()

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin


class byBordd(Plugin):
    def has_settings_ui(s): return True
    def show_settings_ui(s, src): return s.ui(source=src)
    col = (0.18, 0.18, 0.18)

    def __init__(s):
        o = igm._refresh_in_game

        def e(f, *a, **k):
            r = o(f, *a, **k)
            b = bw(
                label='',
                size=(90, 40),
                button_type='square',
                parent=f._root_widget,
                color=(0.18, 0.18, 0.18),
                position=(f._width-20, 0),
            )
            bw(b, on_activate_call=lambda: s.ui(source=b, main=True))
            iw(
                size=(40, 40),
                texture=gt('tv'),
                parent=f._root_widget,
                position=(f._width-20, 5)
            )
            tw(
                maxwidth=50,
                text='Camera',
                h_align='left',
                parent=f._root_widget,
                position=(f._width+15, 0)
            )
            return r
        igm._refresh_in_game = e
    """The UI"""
    def ui(s, source=None, main=False):
        s.main = main
        off = source.get_screen_space_center() if source else (0, 0)
        w = cw(
            color=s.col,
            size=(350, 305),
            stack_offset=off,
            transition='in_scale',
            parent=gsw('overlay_stack'),
            scale_origin_stack_offset=off
        )
        s.back = lambda b=True: (
            cw(w, transition=['out_right', 'out_scale'][bool(source) and b]), gs('swish').play() if b else None)
        cw(w, on_outside_click_call=s.back)
        b = Camera.__yes__
        t = [
            ('Camera is ready!', (0, 1, 1)),
            ('Camera is running!', (0, 1, 0)),
        ][b]
        tw(
            parent=w,
            text=t[0],
            scale=1.5,
            color=t[1],
            h_align='center',
            position=(155, 250)
        )
        for i in range(4):
            j = [
                ('3D Camera mapper', s.start),
                ('Last mapped config', s.load),
                ('Last dev command', s.copy),
                ('Reset all settings', s.reset)
            ][i]
            tw(
                parent=w,
                text=j[0],
                maxwidth=195,
                position=(20, 30+55*i)
            )
            k = [
                (['Start', 'Stop'][b], 'cursor'),
                ('Load', 'achievementOutline'),
                ('Copy', 'file'),
                ('Reset', 'replayIcon')
            ][i]
            bw(
                parent=w,
                label=k[0],
                color=s.col,
                size=(120, 50),
                icon=gt(k[1]),
                enable_sound=not i,
                textcolor=(1, 1, 1),
                button_type='square',
                on_activate_call=j[1],
                position=(220, 20+55*i)
            )
    """Gather last"""
    def gather(s):
        return var('lp1'), var('lp2')
    """Reset"""
    def reset(s):
        SCM(False)
        nice('Resetored original settings!')
    """Copy last"""
    def copy(s):
        if not CIS():
            note('Unsupported!', True)
            return
        g = s.gather()
        if not g[1]:
            note('Apply something first!', True)
            return
        g = [tuple([round(i, 2) for i in j]) for j in g]
        COPY(
            f'from _babase import set_camera_manual as SCM, set_camera_target as SCT, set_camera_position as SCP; SCM(True); SCP(*{g[0]}); SCT(*{g[1]})')
        nice('Copied command!\nPaste it in dev console anytime to load config!')
    """Load last"""
    def load(s):
        g = s.gather()
        if not g[1]:
            note('Apply something first!', True)
            return
        if Camera.__yes__:
            note('Stop camera first!', True)
            return
        SCM(True)
        SCP(*g[0])
        SCT(*g[1])
        nice('Loaded last config!')
    """Start camera"""
    def start(s):
        a = ga()
        if not a:
            note('Only mapping requires you to be the host!\nYou still can load previous config though', True)
            return
        if not getme():
            note('Join the game first!', True)
            return
        s.back(False)
        RESUME() if s.main else None
        with a.context:
            Camera()
