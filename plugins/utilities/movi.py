# Copyright 2026 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Movi v1.0.0 - Movie Maker

A simple movie maker with native BRP replay export.
Includes timeline sequencing, node manipulation,
custom cameras, code injection, VFX presets, and more.
"""

import babase as ba
import bauiv1 as bui
import _babase as _ba
import bascenev1 as bs

from re import sub
from math import ceil
from colorsys import hsv_to_rgb
from os import listdir
from io import StringIO
from shutil import copy
from hashlib import md5
from random import choice, uniform
from base64 import b85decode
from time import perf_counter
from datetime import datetime
from json import dumps, loads
from weakref import WeakMethod
from traceback import format_exc
from os.path import join, dirname
from threading import Thread, Event
from collections import defaultdict
from zlib import decompress, compress
from ctypes import pythonapi, c_long, py_object
from contextlib import redirect_stdout, redirect_stderr

__version__ = '1.0.0'

plugman = dict(
    plugin_name="movi",
    description=(
        "A simple movie maker with native BRP replay export. "
        "Includes timeline sequencing, node manipulation, "
        "custom cameras, code injection, VFX presets, and more."
    ),
    external_url="https://BroBordd.github.io/byBordd",
    authors=[
        {
            "name": "BrotherBoard",
            "email": "brobordd@gmail.com",
            "discord": "BrotherBoard"
        },
    ],
    version=__version__,
)


class Tracker:
    def __init__(self):
        self.active = {}
        self.active_actors = {}
        self.active_sounds = {}
        self.active_timers = {}
        self.active_codes = defaultdict(dict)
        self.active_seeds = {}
        self.internal_timers = []
        self.active_key_schedule = {}


class Editor:
    _shared = {'callbacks': [], 'on_create': []}

    @staticmethod
    def ui_safe(f):
        return lambda s, *a, **k: (
            hasattr(s, 'root') and
            s.root.exists() and
            s.ui_on and f(s, *a, **k)
        )

    @staticmethod
    def clickable(f):
        return lambda s, *a, **k: (
            f(s, *a, **k) if s.ui_clickable else
            None if not s.ui_on else
            s.toast(
                s.ui_clickable is None and
                Strings.INFO_SLOW_DOWN or
                Strings.ERROR_PAUSE_FIRST
            ) or
            Eval.SOUND(Const.BAD_SOUND).play()
        )

    @staticmethod
    def _call(sig):
        for callback_ref in Editor._shared['callbacks']:
            callback = callback_ref()
            callback(sig)

    def callback(s, cb):
        bui.apptimer(Const.BA_LAG_SMALL, getattr(s, cb))

    def __init__(s, map):
        s.shared_callback = WeakMethod(s.callback)
        type(s)._shared['callbacks'].append(s.shared_callback)
        s.ui_on = False
        s.ui_clickable = False
        s.original_map = map
        s.timeline = []
        s.timeline_index = 0
        s.active = {}
        s.active_actors = {}
        s.active_sounds = {}
        s.active_timers = {}
        s.active_key_schedule = {}
        s.active_codes = defaultdict(dict)
        s.active_seeds = {}
        s.play_timer = None
        s.playing = False
        s.playhead = None
        s.is_wide = False
        s.can_toast = True
        s.toast_zoom = None
        s.toast_blink = None
        s.last_toast = None
        s.menu_root = None
        s.menu_on = False
        s.seed_on = False
        s.menu_kids = []
        s.event_root = None
        s.event_on = False
        s.event_kids = {}
        s.event_top = None
        s.window_on = ()
        s.window_sub_on = None
        s.window_kids = []
        s.window_trash = []
        s.magic_x = 5.5
        s.magic_y = 5
        s.magic_right = 0.925
        s.magic_left = 1.4
        s.entry_xs = 40
        s.entry_ys = 40
        s.entry_xs_real = s.entry_xs * s.magic_right
        s.entry_ys_real = s.entry_ys * s.magic_right
        s.stamp_kids = []
        s.stamp_timeline = []
        s.stamp_hack = 14
        s.entries_per_sec = 5
        s.object_duration = Settings.get('entry_duration')
        s.memory = {}
        s.widgets = {}
        s.anims = defaultdict(dict)
        s.in_anims = []
        s.out_anims = []
        s.pending = []
        s.controls = []
        s.controls_shown = False
        s.tools = []
        s.tools_shown = False
        s.camera_timer = None
        s.camera_data = {}
        s.autosave_timer = None
        s.autosave_kids = []
        s.autosave_img_kids = []
        s.autosave_text_kids = []
        s.autosave_text_anim = {}
        s.autosave_kill_timer = None
        s.about_letter_kids = []
        s.sl = None
        s.global_butter = 0.3
        s.can_do = False
        s.blame = None
        s.increment = 1
        s.info_fps_was_on = bui.app.config.get(Const.CONFIG_FPS_KEY, False)
        s.info_dev_was_on = bui.app.config.get(Const.CONFIG_DEV_KEY, False)
        Settings.apply_all()
        s.grid_nodes = []
        s.aspect_bars = None
        s.aspect_fill_bars = []
        s.schedule_on_ui(
            s.on_ui_ready,
            lag=0.23
        )

    def schedule_on_ui(s, f, lag=0.3):
        if s.ui_on:
            f()
        else:
            s.pending.append((lag, f))

    def universal_back(s):
        if s.window_sub_on:
            s.window_sub_on[2]()
            return
        if s.window_on or s.event_on:
            s.event_button.activate()
        else:
            s.square.activate()

    @ui_safe
    def on_resize(s):
        s.on_scroll()
        s.wrap_all()

    @ui_safe
    def on_rescale(s):
        s.on_scroll()
        s.wrap_all()

    def save_state(s):
        Config.set('last', Eval.ENCODE(s.memory))

    @ui_safe
    def autosave(s):
        if not s.memory:
            return
        if not Settings.get('autosave_on'):
            return
        s.save_state()
        s.play_autosave_anim()

    def restart_autosave_timer(s):
        """Called whenever Settings' 'autosave_interval' changes so
        the live AppTimer picks up the new period immediately."""
        s.autosave_timer = None
        s.autosave_timer = bui.AppTimer(
            max(Settings.get('autosave_interval'), Const.AUTOSAVE_MIN_INTERVAL),
            s.autosave, repeat=True
        )

    def build_grid(s):
        """Populates the scene with spatial references while editing -
        a flat 2D grid, a full 3D lattice, or both, per their own
        independent settings. Purely visual - never touched by
        playback or export. Safe to call repeatedly (always clears
        the previous grid first).

        The 2D grid draws actual lines (thin red 'image' nodes tinted
        over the plain 'white' texture) rather than a dot at every
        intersection - the 3D grid stays as locator-box markers,
        since a full lattice of lines would just be visual noise."""
        s.destroy_grid()
        if s.playing:
            return
        show_2d = Settings.get('show_grid_2d')
        show_3d = Settings.get('show_grid_3d')
        if not show_2d and not show_3d:
            return
        try:
            activity = bs.get_foreground_host_activity()
        except Exception:
            return
        span = Const.GRID_SPAN
        step = Const.GRID_STEP
        n = int(span/step)
        try:
            with activity.context:
                if show_2d:
                    rx, ry = bui.get_virtual_screen_size()
                    step2d = min(rx, ry)/Const.GRID_2D_DIVISIONS
                    nx2d = int((rx/2)/step2d)
                    ny2d = int((ry/2)/step2d)
                    total_len_x = 2*nx2d*step2d
                    total_len_y = 2*ny2d*step2d
                    thickness = Const.GRID_2D_THICKNESS
                    grid_opacity = min(Color.OPACITY*1.6, 1)
                    for ix in range(-nx2d, nx2d+1):
                        s.grid_nodes.append(bs.newnode(
                            'image',
                            attrs={
                                'texture': bs.gettexture('white'),
                                'position': (ix*step2d, 0.0),
                                'scale': (thickness, total_len_y),
                                'color': (1, 0, 0),
                                'opacity': grid_opacity
                            }
                        ))
                    for iy in range(-ny2d, ny2d+1):
                        s.grid_nodes.append(bs.newnode(
                            'image',
                            attrs={
                                'texture': bs.gettexture('white'),
                                'position': (0.0, iy*step2d),
                                'scale': (total_len_x, thickness),
                                'color': (1, 0, 0),
                                'opacity': grid_opacity
                            }
                        ))
                if show_3d:
                    span_y = Const.GRID_SPAN_3D
                    step_y = Const.GRID_STEP_3D
                    ny = int(span_y/step_y)
                    for ix in range(-n, n+1):
                        for iy in range(-ny, ny+1):
                            for iz in range(-n, n+1):
                                if show_2d and iy == 0:
                                    continue
                                s.grid_nodes.append(bs.newnode(
                                    'locator',
                                    attrs={
                                        'position': (ix*step, iy*step_y, iz*step),
                                        'shape': 'box',
                                        'size': [Const.GRID_MARK_SIZE]*3,
                                        'color': Color.WARM,
                                        'opacity': min(Color.OPACITY*1.6, 1),
                                        'additive': False,
                                        'draw_beauty': True
                                    }
                                ))
        except Exception as e:
            print(format_exc())
            s.destroy_grid()

    def destroy_grid(s):
        for n in getattr(s, 'grid_nodes', None) or []:
            if n.exists():
                n.delete()
        s.grid_nodes = []

    def play_autosave_anim(s):
        for w in s.autosave_kids:
            if w.exists():
                w.delete()
        s.autosave_kids.clear()
        s.autosave_img_kids.clear()
        s.autosave_text_kids.clear()
        s.autosave_text_anim.clear()

        rx, ry = bui.get_virtual_screen_size()
        area = Const.AUTOSAVE_AREA
        marg = Const.AUTOSAVE_MARGIN
        pad = Const.AUTOSAVE_BG_PADDING
        fancy = Settings.get('fancy_autosave')
        epic = Settings.get('epic_mode')

        icon_pad = pad if fancy else Const.AUTOSAVE_COMPACT_BG_PAD/2

        # icon sits inset by `icon_pad` from the container's edges
        area_bl = (marg+icon_pad, ry-marg-icon_pad-area)
        area_cx = marg+icon_pad+area/2
        area_cy = ry-marg-icon_pad-area/2

        def square(size, pos, opacity):
            w = bui.imagewidget(
                parent=s.root,
                texture=Eval.TEXTURE(Const.SKIN),
                color=Color.BASE,
                position=pos,
                size=size,
                opacity=opacity
            )
            s.autosave_kids.append(w)
            s.autosave_img_kids.append(w)
            return w

        p_dur = Const.AUTOSAVE_PARENT_DUR

        if fancy:
            inner_w = Const.AUTOSAVE_BG_WIDTH
            bg_w = inner_w+pad*2
            bg_h = area+pad*2
        else:
            inner_w = area
            bg_w = bg_h = area+icon_pad*2
        bg_end_pos = (marg, ry-marg-bg_h)
        bg_cx = marg+bg_w/2
        bg_cy = ry-marg-bg_h/2
        pop = Const.AUTOSAVE_BG_POP_SCALE * (Const.EPIC_POP_MULT if epic else 1)
        bg_start_size = (bg_w*pop, bg_h*pop)
        bg_start_pos = (bg_cx-bg_start_size[0]/2, bg_cy-bg_start_size[1]/2)

        bg = square(bg_start_size, bg_start_pos, 0)
        Animate(
            widget=bg,
            duration=p_dur,
            attrs={
                'size': (bg_start_size, (bg_w, bg_h)),
                'position': (bg_start_pos, bg_end_pos),
                'opacity': (0, Color.OPACITY)
            }
        )

        text_x = area_bl[0]+area-5
        text_w = inner_w-area-pad

        title = None
        if fancy:
            title = bui.textwidget(
                parent=s.root,
                text=choice(Const.AUTOSAVE_TITLES),
                position=(text_x, bg_cy+14),
                size=(text_w, 20),
                h_align='left',
                v_align='center',
                scale=0.9,
                maxwidth=text_w,
                color=Const.INVISIBLE
            )
            s.autosave_kids.append(title)
            s.autosave_text_kids.append(title)
            s.autosave_text_anim[id(title)] = Animate(
                widget=title,
                duration=p_dur,
                attrs={'color': (Const.INVISIBLE, (*Color.TEXT, Color.TEXT_OPACITY))}
            )

        tips = []
        if fancy:
            for index, line in enumerate(
                choice(Const.AUTOSAVE_TIPS).splitlines()
            ):
                tip = bui.textwidget(
                    parent=s.root,
                    text=line,
                    position=(text_x-30, bg_cy-10-(index*15)),
                    size=(text_w, 30),
                    h_align='left',
                    v_align='center',
                    scale=0.6,
                    maxwidth=text_w,
                    color=Const.INVISIBLE
                )
                s.autosave_kids.append(tip)
                s.autosave_text_kids.append(tip)
                s.autosave_text_anim[id(tip)] = Animate(
                    widget=tip,
                    duration=p_dur,
                    attrs={'color': (Const.INVISIBLE, (*Color.TEXT, Color.TEXT_OPACITY*0.7))}
                )
                tips.append(tip)

        p_end_pos = (area_cx-area/2, area_cy-area/2)

        parent = square((area, area), p_end_pos, 0)
        Animate(
            widget=parent,
            duration=p_dur,
            attrs={
                'opacity': (0, Color.OPACITY)
            }
        )

        swap_dur = Const.AUTOSAVE_CHILD_GROW_DUR
        swap_wait = Const.AUTOSAVE_CHILD_WAIT1*2
        swap_count = Const.AUTOSAVE_SWAP_COUNT * (Const.EPIC_SWAP_MULT if epic else 1)
        min_diff = Const.AUTOSAVE_MIN_SPLIT_DIFF

        area_tr_corner = (marg+icon_pad+area, ry-marg-icon_pad)

        def bl_pos(sz):
            return area_bl

        def tr_pos(sz):
            return (area_tr_corner[0]-sz, area_tr_corner[1]-sz)

        def rand_split(prev_pct=None):
            while True:
                pct = uniform(0.15, 0.85)
                if prev_pct is None or abs(pct-prev_pct) >= min_diff:
                    return pct

        pct = rand_split()
        a_size, b_size = area*pct, area*(1-pct)

        # square A starts at bottom-left, square B at top-right
        a = square((a_size, a_size), bl_pos(a_size), 0)
        b = square((b_size, b_size), tr_pos(b_size), 0)

        Animate(
            widget=a,
            duration=p_dur,
            attrs={'opacity': (0, Color.OPACITY)}
        )
        Animate(
            widget=b,
            duration=p_dur,
            attrs={'opacity': (0, Color.OPACITY)}
        )

        last_delay = 0
        anims_off = not Settings.get('ui_anim_on')

        if not anims_off:
            for i in range(swap_count):
                base = p_dur+i*(swap_dur+swap_wait)
                a_from, b_from = a_size, b_size
                pct = rand_split(pct)
                a_size, b_size = area*pct, area*(1-pct)
                a_to, b_to = a_size, b_size

                Animate(
                    widget=a,
                    delay=base,
                    duration=swap_dur,
                    attrs={
                        'size': ((a_from, a_from), (a_to, a_to)),
                        'position': (bl_pos(a_from), bl_pos(a_to))
                    }
                )
                Animate(
                    widget=b,
                    delay=base,
                    duration=swap_dur,
                    attrs={
                        'size': ((b_from, b_from), (b_to, b_to)),
                        'position': (tr_pos(b_from), tr_pos(b_to))
                    }
                )

                last_delay = base+swap_dur+swap_wait
        else:
            last_delay = Const.AUTOSAVE_STATIC_HOLD

        def die():
            for w in (a, b, parent, title, *tips):
                if w is not None and w.exists():
                    w.delete()
                s.autosave_text_anim.pop(id(w), None)
            Animate(
                widget=bg,
                duration=p_dur,
                attrs={
                    'size': ((bg_w, bg_h), bg_start_size),
                    'position': (bg_end_pos, bg_start_pos),
                    'opacity': (Color.OPACITY, 0)
                },
                on_finish=lambda: bg.exists() and bg.delete()
            )
        s.autosave_kill_timer = bui.AppTimer(last_delay, die)

    def recreate(s):
        type(s)._shared['callbacks'].remove(s.shared_callback)
        Movi.recreate()

    @ui_safe
    def on_scroll(s):
        if s.event_on:
            for kid in s.event_kids:
                an = s.anims[id(kid)]
                for _ in ['extra', 'to']:
                    (a := an.get(_, None)) and a.cancel()

    def on_ui_ready(s):
        if (last := Config.get('last')):
            try:
                memory = Eval.DECODE(last)
            except Exception as e:
                s.toast(Format.ERROR(e))
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            s.load_memory(memory, shut=True)
        bui.apptimer(Const.BA_LAG_BIG, s.on_rescale)
        on_create = type(s)._shared['on_create']
        for call, args in on_create:
            call(s, *args)
        on_create.clear()
        s.autosave_timer = bui.AppTimer(
            max(Settings.get('autosave_interval'), Const.AUTOSAVE_MIN_INTERVAL), s.autosave, repeat=True
        )
        s.build_grid()

    def start_recording(s):
        s.export_flag = True
        s.play()
        s.toast(Strings.INFO_RECORDING_NOW)
        bui.buttonwidget(
            s.controls[0],
            label=Strings.STOP_RECORDING_LABEL
        )

    def render_export_filename(s, uid):
        """Turns the 'export_filename_template' setting (e.g.
        'movi_{uuid}') into a real, filesystem-safe base filename -
        no extension, that's added by the caller. Unknown {tokens}
        are dropped instead of raising, and anything that isn't
        alnum/underscore/dash collapses to '_' so a stray character
        in the template can't produce a broken path."""
        now = datetime.now()
        tokens = defaultdict(str, {
            'uuid': uid,
            'date': now.strftime('%Y%m%d'),
            'time': now.strftime('%H%M%S'),
        })
        template = Settings.get('export_filename_template') or Const.EXPORT_DEFAULT_TEMPLATE
        try:
            rendered = template.format_map(tokens)
        except Exception:
            rendered = Const.EXPORT_DEFAULT_TEMPLATE.format_map(tokens)
        rendered = sub(r'[^A-Za-z0-9_\-]+', '_', rendered).strip('_')
        return rendered or Const.EXPORT_PREFIX+uid

    def export_replay(s, wait=True):
        if wait:
            bui.apptimer(
                Const.BA_LAG_BIG,
                bui.CallPartial(
                    s.export_replay,
                    wait=False
                )
            )
            return
        uid = md5(
            dumps(
                s.memory,
                sort_keys=True
            ).encode()
        ).hexdigest()[:8]
        base_name = s.render_export_filename(uid)
        name = base_name+Const.EXPORT_SUFFIX
        copy(
            join(
                Const.REPLAYS,
                Const.STOCK_REPLAY
            ),
            join(
                Const.REPLAYS,
                name
            )
        )
        if Settings.get('brp_text_export'):
            text_name = base_name+Const.EXPORT_TEXT_SUFFIX
            try:
                with open(join(Const.REPLAYS, text_name), 'w', encoding='utf-8') as f:
                    f.write(dumps(s.memory, indent=2, sort_keys=True))
            except Exception as e:
                s.toast(Format.ERROR(e))
        s.toast(Format.SAVED_AS(name))
        Eval.SOUND(Const.GOOD_SOUND).play()

    def toast(s, inp=None, shut=1, extra=0):
        shut or Eval.SOUND(Const.OK_SOUND).play()
        if not s.can_toast and not shut:
            return
        if s.can_do and extra < 1:
            s.can_do = False
        if s.toast_blink:
            s.toast_blink.cancel()
            s.toast_blink = None
        if s.toast_zoom:
            s.toast_zoom.cancel()
        s.can_toast = False
        b = s.toast_bg
        t, desc = inp or ('', '')
        if not s.blame:
            s.blame = Strings.BLAME
        desc and bui.buttonwidget(
            b, on_activate_call=bui.CallPartial(
                s.toast,
                (desc, choice(s.blame)),
                shut=0,
                extra=extra-1
            )
        )
        text_width = t and Eval.STRING_WIDTH(t) or 0
        duration = 0.45
        end_size = dx, dy = (text_width+(t and 20 or 0), 30)
        start_size = (0, dy)
        start_opacity = 0
        zero = 0.0001
        x, y = ox, oy = s.toast_position
        end_pos = epx, epy = (ox-dx/2, oy)
        rush = False
        if (anim := s.anims.get(id(b), None)):
            start_size = stx, sty = anim.attrs_current['size']
            if (
                (int(stx) == int(dx)) and
                (int(sty) == int(dy))
            ):
                rush = True
            x, y = anim.attrs_current['position']
            start_opacity = anim.attrs_current['opacity']
            anim.cancel()

        def enable(): s.can_toast = True
        zoom_time = 0.2

        def zoom():
            s.toast_zoom = Animate(
                widget=b,
                attrs={
                    'size': (
                        end_size,
                        (dx*1.1, dy*1.1)
                    ),
                    'position': (
                        end_pos,
                        (epx-dx*0.1/2, epy-dy*0.1/2)
                    )
                },
                duration=zoom_time,
                on_finish=(enable,)
            )
        start_textcolor = (*Color.TEXT, Color.TEXT_OPACITY)
        blink_time = 0.2
        apply_text = bui.CallPartial(
            bui.buttonwidget,
            b, label=t
        )
        skip_blink = s.last_toast == t

        def blink():
            if (anim := s.toast_blink):
                anim.cancel()
            s.toast_blink = Animate(
                widget=b,
                attrs={
                    'textcolor': (
                        start_textcolor,
                        skip_blink and start_textcolor or Const.INVISIBLE
                    )
                },
                duration=skip_blink and zero or blink_time,
                on_finish=(None,),
                on_reverse=apply_text,
                on_cancel=apply_text
            )
        blink()
        s.anims[id(b)] = Animate(
            widget=b,
            attrs={
                'size': (start_size, end_size),
                'opacity': (
                    start_opacity,
                    t and Color.OPACITY or 0
                ),
                'position': (
                    (x, y),
                    end_pos
                )
            },
            duration=rush and zero or duration,
            on_finish=zoom
        )
        s.toast_timer = inp and bui.AppTimer(
            max(len(t)*0.07, Settings.get('toast_duration')),
            s.toast
        )
        s.last_toast = t

    def reset_toast_position(s):
        """toast()'s continuous-toast-chain animation deliberately
        starts each new toast from the previous one's current position
        (anim.attrs_current) instead of s.toast_position, so back-to-
        back toasts flow into each other instead of jumping. But that
        means once 'toast_top' changes, the very next toast still
        inherits the old anim's last position and springs across the
        screen to the new spot - only settling into place correctly
        from then on, since by then attrs_current matches the new
        s.toast_position. Dropping the stored anim here makes that
        next toast fall through to s.toast_position immediately,
        exactly like the very first toast of a session does."""
        if (anim := s.anims.pop(id(s.toast_bg), None)):
            anim.cancel()

    def make(s):
        s.root = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            background=False
        )
        bui.containerwidget(
            s.root,
            cancel_button=(
                bui.buttonwidget(
                    parent=s.root,
                    size=(0, 0),
                    label='',
                    selectable=False,
                    enable_sound=False,
                    on_activate_call=s.universal_back,
                    texture=Eval.TEXTURE(Const.EMPTY)
                )
            )
        )
        s.stamp_bg = bui.imagewidget(
            parent=s.root,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            opacity=0
        )
        s.square = bui.buttonwidget(
            parent=s.root,
            texture=Eval.TEXTURE(Const.SKIN),
            label=Eval.CHAR(Const.SQUARE),
            color=Color.BASE,
            textcolor=(*Color.TEXT, Color.TEXT_OPACITY),
            enable_sound=False,
            on_activate_call=s.on_square
        )
        s.triangle = bui.buttonwidget(
            parent=s.root,
            texture=Eval.TEXTURE(Const.SKIN),
            label=Eval.CHAR(Const.TRIANGLE),
            color=Color.BASE,
            textcolor=(*Color.TEXT, Color.TEXT_OPACITY),
            enable_sound=False,
            on_activate_call=s.on_triangle
        )
        s.circle = bui.buttonwidget(
            parent=s.root,
            texture=Eval.TEXTURE(Const.SKIN),
            label=Eval.CHAR(Const.CIRCLE),
            color=Color.BASE,
            textcolor=(*Color.TEXT, Color.TEXT_OPACITY),
            enable_sound=False,
            on_activate_call=s.on_circle
        )
        s.circle_shadow = bui.imagewidget(
            parent=s.root,
            opacity=0,
            texture=Eval.TEXTURE(Const.SHADOW),
            color=Color.SHADOW
        )
        s.about = bui.buttonwidget(
            parent=s.root,
            texture=Eval.TEXTURE(Const.SKIN),
            label=Strings.ABOUT_LABEL,
            color=Color.BASE,
            textcolor=(*Color.TEXT, Color.TEXT_OPACITY),
            enable_sound=False,
            on_activate_call=s.on_about
        )
        s.about_shadow = bui.imagewidget(
            parent=s.root,
            opacity=0,
            texture=Eval.TEXTURE(Const.SHADOW),
            color=Color.SHADOW
        )
        s.stamp_scroll = bui.scrollwidget(
            parent=s.root,
            border_opacity=0,
            color=Color.BASE,
            on_select_call=s.on_scroll
        )
        s.stamp_scroll_root = bui.containerwidget(
            parent=s.stamp_scroll,
            background=False
        )
        s.stamp_hscroll = bui.hscrollwidget(
            parent=s.stamp_scroll_root,
            border_opacity=0,
            color=Color.BASE
        )
        s.stamp_hscroll_root = bui.containerwidget(
            parent=s.stamp_hscroll,
            background=False
        )
        s.top_left_h = bui.textwidget(
            parent=s.stamp_hscroll_root
        )
        s.top_left_v = bui.textwidget(
            parent=s.stamp_scroll_root
        )
        s.bottom_left_h = bui.textwidget(
            parent=s.stamp_hscroll_root,
            position=(0, 0),
            size=(10, 10)
        )
        s.bottom_left_v = bui.textwidget(
            parent=s.stamp_scroll_root,
            position=(0, 0)
        )
        s.event_root = bui.imagewidget(
            parent=s.root,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            opacity=0
        )
        s.event_button = bui.buttonwidget(
            parent=s.root,
            label=Strings.EVENT_BUTTON_OFF,
            on_activate_call=s.toggle_event,
            texture=Eval.TEXTURE(Const.EMPTY),
            opacity=0,
            textcolor=Const.INVISIBLE,
            enable_sound=False
        )
        for i, n in enumerate(Strings.EVENTS):
            b = bui.buttonwidget(
                parent=s.root,
                label=n,
                color=Color.BASE,
                textcolor=Const.INVISIBLE,
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0,
                enable_sound=False,
                selectable=False
            )
            sh = bui.imagewidget(
                parent=s.root,
                opacity=0,
                texture=Eval.TEXTURE(Const.SHADOW),
                color=Color.SHADOW
            )
            s.event_kids[b] = {'shadow': sh}
        s.edit_button = bui.buttonwidget(
            parent=s.root,
            label=Strings.EDIT_BUTTON,
            on_activate_call=s.edit_window,
            texture=Eval.TEXTURE(Const.SKIN),
            opacity=0,
            textcolor=Const.INVISIBLE,
            enable_sound=False,
            color=Color.BASE
        )
        s.edit_button_shadow = bui.imagewidget(
            parent=s.root,
            opacity=0,
            texture=Eval.TEXTURE(Const.SHADOW),
            color=Color.SHADOW
        )
        s.key_button = bui.buttonwidget(
            parent=s.root,
            label=Strings.KEYS,
            on_activate_call=s.key_window,
            texture=Eval.TEXTURE(Const.SKIN),
            opacity=0,
            textcolor=Const.INVISIBLE,
            enable_sound=False,
            color=Color.BASE
        )
        s.key_button_shadow = bui.imagewidget(
            parent=s.root,
            opacity=0,
            texture=Eval.TEXTURE(Const.SHADOW),
            color=Color.SHADOW
        )
        for i, t in enumerate(Const.TOOLS):
            b = bui.buttonwidget(
                parent=s.root,
                color=Color.BASE,
                opacity=0,
                textcolor=Const.INVISIBLE,
                enable_sound=False,
                texture=Eval.TEXTURE(Const.SKIN),
                label=Eval.CHAR(t),
                on_activate_call=bui.CallPartial(
                    s.do_tool, i
                ),
                repeat=True
            )
            s.tools.append(b)
        for i, t in enumerate(Const.CONTROLS):
            b = bui.buttonwidget(
                parent=s.root,
                color=Color.BASE,
                opacity=0,
                textcolor=Const.INVISIBLE,
                enable_sound=False,
                texture=Eval.TEXTURE(Const.SKIN),
                label=(
                    isinstance(t, str)
                    and Eval.CHAR(t)
                    or Eval.CHAR(t[s.playing])
                ),
                on_activate_call=bui.CallPartial(
                    s.do_control, i
                ),
                size=(0, 0)
            )
            s.controls.append(b)
        s.toast_bg = bui.buttonwidget(
            parent=s.root,
            label='',
            enable_sound=False,
            selectable=False,
            size=(0, 0),
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE
        )
        s.make_menu()
        s.ui_clickable = True
        s.wrap_all(init=True)
        s.make_timeline(init=True)
        s.wrap_timeline()
        s.top_left()
        bui.apptimer(0.3, s.toggle_ui)
        for lag, call in s.pending:
            bui.apptimer(lag, call)
        s.pending.clear()

    def make_timeline(s, init=False):
        for i, j in s.stamp_timeline:
            i.delete()
            j.delete()
        s.stamp_timeline.clear()
        eps = s.entries_per_sec
        num_markers = int(s.stamp_deep_x / s.entry_xs_real) + 5
        for i in range(num_markers):
            t = bui.textwidget(
                parent=s.stamp_hscroll_root,
                text=(
                    i % eps == 0
                    and str(int(i/eps))
                    or '.'
                ),
                h_align=Const.ALIGN,
                v_align=Const.ALIGN,
                size=(10, 5),
                scale=0.5,
                color=(
                    Const.INVISIBLE if init else
                    (*Color.TEXT, Color.TEXT_OPACITY)
                )
            )
            l = bui.imagewidget(
                parent=s.stamp_hscroll_root,
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0 if init else Color.OPACITY/10,
                size=(2, s.stamp_deep_y*2),
                color=Color.TEXT
            )
            s.stamp_timeline.append((t, l))

    def build_timeline(s):
        s.timeline = []
        for btn_id, mem in s.memory.items():
            btn = next(
                (b for b in s.stamp_kids if id(b) == btn_id),
                None
            )
            if not btn:
                continue
            s.timeline.append({
                'time': mem['start'],
                'type': 'start',
                'button': btn,
                'memory': mem,
                'btn_id': btn_id
            })
            s.timeline.append({
                'time': mem['start'] + mem['duration'],
                'type': 'end',
                'button': btn,
                'memory': mem,
                'btn_id': btn_id
            })
        s.timeline.sort(key=lambda x: x['time'])
        s.max_time = s.timeline[-1]['time'] if s.timeline else 0

    def wrap_timeline(s):
        for i, g in enumerate(s.stamp_timeline):
            t, l = g
            px = i*s.entry_xs_real
            py = s.stamp_deep_y-20
            bui.textwidget(
                t,
                position=(px, py)
            )
            bui.imagewidget(
                l,
                position=(px+4, -s.stamp_deep_y/2)
            )

    def refresh_ui(s, message=None):
        """Existing widgets don't repaint themselves just because a
        live global (Color.OPACITY, Color.BASE/COLD/WARM/TEXT via a
        theme swap, or a Strings.* lookup via a language swap)
        changed underneath them - a hide/show cycle is what actually
        rebuilds them onto whatever's current (animate_in() re-reads
        every one of those fresh each time it runs). Shared by every
        setting that needs a full repaint - opacity, theme, and
        language all fall through to this one path. No-op if the UI
        was already hidden - nothing visible to refresh, and flipping
        it on would undo whatever the person hid it for."""
        if not s.ui_on:
            return
        message and s.toast(message)
        s.toggle_ui(on_finish=lambda: bui.apptimer(0.2, s.toggle_ui))

    def refresh_opacity_via_ui_toggle(s):
        s.refresh_ui(Strings.INFO_CHANGING_OPACITY)

    def repaint_theme(s):
        """refresh_ui()/animate_in() only ever re-paints the small
        handful of widgets wired into the hide/show fade - everything
        else built once in make() (or added to it later, like
        event_kids/stamp_kids) bakes in whatever Color.BASE was live
        at creation and just keeps it forever, so a theme change only
        ever reached that cherry-picked subset. This walks every
        persistent widget instead and snaps its fill straight to the
        current Color.BASE, so a theme switch actually repaints the
        whole UI - regardless of ui_on, since these exist either way.

        Only ever touches `color` (the background fill), never
        `textcolor`/`opacity` - several of these widgets (edit_button,
        key_button, event_root/event_kids, tools, controls) have their
        own separate show/hide state machine driving those, and
        stomping them here would fight that instead of just fixing
        the color underneath it. Shadow widgets get Color.SHADOW
        instead of Color.BASE - they're a separate, always-dark tint
        so a shadow still reads as a shadow on light/pale themes
        instead of brightening along with the panel it's cast by.

        stamp_kids are the one exception to the color-only rule above:
        unlike edit_button/tools/controls/etc, they don't have any
        ongoing show/hide cycle of their own once created (fade in
        once via add_entry/load_memory, then just sit on the timeline
        for the rest of the session) - nothing else was ever going to
        come back and refresh their textcolor, so it stayed pinned to
        whatever theme was live when each one was created."""
        if not (hasattr(s, 'root') and s.root.exists()):
            return
        bui.imagewidget(s.stamp_bg, color=Color.BASE)
        bui.buttonwidget(s.square, color=Color.BASE, textcolor=(*Color.TEXT, Color.TEXT_OPACITY))
        bui.buttonwidget(s.triangle, color=Color.BASE, textcolor=(*Color.TEXT, Color.TEXT_OPACITY))
        bui.buttonwidget(s.circle, color=Color.BASE, textcolor=(*Color.TEXT, Color.TEXT_OPACITY))
        bui.imagewidget(s.circle_shadow, color=Color.SHADOW)
        if (anim := s.anims.get(id(s.circle), {}).get('window')):
            anim.attrs_start['textcolor'] = (*Color.TEXT, Color.TEXT_OPACITY)
        bui.buttonwidget(s.about, color=Color.BASE, textcolor=(*Color.TEXT, Color.TEXT_OPACITY))
        bui.imagewidget(s.about_shadow, color=Color.SHADOW)
        if (anim := s.anims.get(id(s.about), {}).get('window')):
            anim.attrs_start['textcolor'] = (*Color.TEXT, Color.TEXT_OPACITY)
        bui.scrollwidget(s.stamp_scroll, color=Color.BASE)
        bui.hscrollwidget(s.stamp_hscroll, color=Color.BASE)
        bui.imagewidget(s.event_root, color=Color.BASE)
        for b, data in s.event_kids.items():
            b.exists() and bui.buttonwidget(b, color=Color.BASE)
            data['shadow'].exists() and bui.imagewidget(data['shadow'], color=Color.SHADOW)
        bui.buttonwidget(s.edit_button, color=Color.BASE)
        bui.imagewidget(s.edit_button_shadow, color=Color.SHADOW)
        bui.buttonwidget(s.key_button, color=Color.BASE)
        bui.imagewidget(s.key_button_shadow, color=Color.SHADOW)
        for b in s.tools:
            b.exists() and bui.buttonwidget(b, color=Color.BASE)
        for b in s.controls:
            b.exists() and bui.buttonwidget(b, color=Color.BASE)
        bui.buttonwidget(s.toast_bg, color=Color.BASE)
        for kid in s.stamp_kids:
            kid.exists() and bui.buttonwidget(
                kid, color=Color.BASE, textcolor=(*Color.TEXT, Color.TEXT_OPACITY)
            )
        for t, l in s.stamp_timeline:
            t.exists() and bui.textwidget(t, color=(*Color.TEXT, Color.TEXT_OPACITY))
            l.exists() and bui.imagewidget(l, color=Color.TEXT)
        bui.imagewidget(s.menu_bg, color=Color.BASE)
        for kid in s.menu_kids:
            kid.exists() and bui.buttonwidget(kid, color=Color.BASE)
        bui.textwidget(s.seed_input, color=(*Color.TEXT, Color.TEXT_OPACITY))

        for w in s.autosave_img_kids:
            w.exists() and bui.imagewidget(w, color=Color.BASE)
        for w in s.autosave_text_kids:
            if not w.exists():
                continue
            anim = s.autosave_text_anim.get(id(w))
            if not anim:
                continue
            for attrs in (anim.attrs_start, anim.attrs_end):
                c = attrs.get('color')
                if c and c != Const.INVISIBLE and len(c) == 4:
                    attrs['color'] = (*Color.TEXT, c[3])
            cur = anim.attrs_current.get('color')
            if cur and tuple(cur) != Const.INVISIBLE and len(cur) == 4:
                new_cur = (*Color.TEXT, cur[3])
                anim.attrs_current['color'] = list(new_cur)
                bui.textwidget(w, color=new_cur)

        for w in s.about_letter_kids:
            if not w.exists():
                continue
            if id(w) in s.anims and 'about_sweep' in s.anims[id(w)]:
                continue
            bui.imagewidget(w, color=Color.TEXT, opacity=Color.TEXT_OPACITY)

    def refresh_theme(s):
        Settings.apply_all()
        s.repaint_theme()
        s.refresh_ui(Strings.INFO_CHANGING_THEME)

    def repaint_language(s):
        if not (hasattr(s, 'root') and s.root.exists()):
            return
        bui.buttonwidget(s.about, label=Strings.ABOUT_LABEL)
        bui.buttonwidget(s.edit_button, label=Strings.EDIT_BUTTON)
        bui.buttonwidget(s.key_button, label=Strings.KEYS)
        bui.buttonwidget(
            s.event_button,
            label=s.event_on and Strings.EVENT_BUTTON_ON or Strings.EVENT_BUTTON_OFF
        )
        for kid, label in zip(s.menu_kids, Strings.MENUS):
            kid.exists() and bui.buttonwidget(kid, label=label)

    def refresh_language(s):
        s.repaint_language()
        s.refresh_ui(Strings.INFO_CHANGING_LANGUAGE)

    def toggle_ui(s, on_finish=None):
        if s.ui_on:
            s.animate_out(on_finish=on_finish)
            s.ui_on = False
            s.ui_clickable = False
        else:
            s.animate_in(on_finish=on_finish)
            s.ui_on = True
            s.ui_clickable = True
        if s.ui_on:
            s.restore_infos()
        else:
            s.set_infos(False)

    def set_infos(s, b):
        bui.app.config[Const.CONFIG_FPS_KEY] = b
        bui.app.config[Const.CONFIG_DEV_KEY] = b
        bui.app.config.apply_and_commit()

    def restore_infos(s):
        bui.app.config[Const.CONFIG_FPS_KEY] = s.info_fps_was_on
        bui.app.config[Const.CONFIG_DEV_KEY] = s.info_dev_was_on
        bui.app.config.apply_and_commit()

    def animate_in(s, on_finish=None):
        bui.scrollwidget(
            s.stamp_scroll,
            size=s.stamp_size
        )
        butter = s.global_butter * 2
        for anim in s.out_anims:
            anim.cancel()
        s.in_anims.clear()
        s.out_anims.clear()

        def cleanup():
            callable(on_finish) and on_finish()
        a = Animate(
            widget=s.stamp_bg,
            duration=butter,
            attrs={
                'opacity': (0, Color.OPACITY)
            },
            on_finish=cleanup
        )
        s.in_anims.append(a)
        for t, l in s.stamp_timeline:
            a = Animate(
                widget=t,
                duration=butter,
                attrs={
                    'color': (
                        Const.INVISIBLE,
                        (*Color.TEXT, Color.TEXT_OPACITY)
                    )
                }
            )
            s.in_anims.append(a)
            a = Animate(
                widget=l,
                duration=butter,
                attrs={
                    'opacity': (0, Color.OPACITY/10)
                }
            )
            s.in_anims.append(a)
        for kid in s.stamp_kids:
            a = Animate(
                widget=kid,
                duration=butter,
                attrs={
                    'opacity': (0, Color.OPACITY),
                    'color': (Color.BASE, Color.BASE)
                }
            )
            s.in_anims.append(a)
        a = Animate(
            widget=s.event_button,
            duration=butter,
            attrs={
                'textcolor': (
                    Const.INVISIBLE,
                    (*Color.TEXT, Color.TEXT_OPACITY)
                )
            }
        )
        s.in_anims.append(a)
        a = Animate(
            widget=s.event_root,
            duration=butter,
            attrs={
                'opacity': (0, Color.OPACITY)
            }
        )
        s.in_anims.append(a)
        a = Animate(
            widget=s.edit_button,
            duration=butter,
            attrs={
                'opacity': (0, Color.OPACITY),
                'textcolor': (
                    Const.INVISIBLE,
                    (*Color.TEXT, Color.TEXT_OPACITY)
                )
            }
        )
        s.in_anims.append(a)
        a = Animate(
            widget=s.key_button,
            duration=butter,
            attrs={
                'opacity': (0, Color.OPACITY),
                'textcolor': (
                    Const.INVISIBLE,
                    (*Color.TEXT, Color.TEXT_OPACITY)
                )
            }
        )
        s.in_anims.append(a)
        if len(s.memory):
            if s.sl:
                s.show_tools()
            else:
                s.show_controls()

    def animate_out(s, on_finish=None):
        butter = s.global_butter*2
        s.collapse_all(hard=True)
        bui.scrollwidget(
            s.stamp_scroll,
            size=(0, 0)
        )
        s.out_anims.clear()
        for anim in s.in_anims:
            a = anim.reverse(
                duration=butter
            )
            s.out_anims.append(a)
        s.in_anims.clear()
        callable(on_finish) and bui.apptimer(butter, on_finish)

    def collapse_all(s, hard=False):
        if s.window_sub_on:
            s.window_sub_on[2](instant=True)
        if not s.event_on and s.window_on:
            s.window_back(into_nothing=True)
        if s.event_on and s.window_on:
            s.window_back(into_nothing=True, skip=True)
            s.toggle_event()
        if s.event_on:
            s.toggle_event()
        if s.controls_shown and (hard or not s.memory):
            s.hide_controls()
        if s.tools_shown:
            s.hide_tools()

    @clickable
    def edit_window(s):
        s.dismiss_window()
        if not s.sl:
            Eval.SOUND(Const.BAD_SOUND).play()
            s.toast(Strings.ERROR_SELECT_SOMETHING)
            return
        Eval.SOUND(Const.OK_SOUND).play()
        bui.buttonwidget(
            s.edit_button,
            on_activate_call=Const.DO_NOTHING,
            selectable=False
        )
        start_pos = s.event_on and s.edit_button_pos2 or s.edit_button_pos
        end_pos = s.window_pos
        start_size = s.edit_button_size
        end_size = s.window_size
        butter = s.global_butter*1.3
        s.anims[id(s.edit_button)]['window'] = Animate(
            s.edit_button,
            duration=butter,
            attrs={
                'position': (start_pos, end_pos),
                'size': (start_size, end_size),
                'textcolor': (
                    (*Color.TEXT, Color.TEXT_OPACITY),
                    Const.INVISIBLE
                )
            }
        )
        s.anims[id(s.edit_button)]['shadow'] = (
            Animate(
                widget=s.edit_button_shadow,
                attrs={
                    'opacity': (0, Color.SHADOW_OPACITY),
                    'position': (
                        start_pos,
                        s.window_shadow_pos
                    ),
                    'size': (
                        start_size,
                        s.window_shadow_size
                    )
                },
                duration=butter
            )
        )
        b = s.sl
        mem = s.memory[id(b)]
        ret = s.make_window_kids(
            mem['event'], edit=mem
        )

        def on_back(): return (
            callable(ret) and ret(),
            s.toast(Strings.INFO_DISCARDED)
        )
        s.window_on = (s.edit_button, s.edit_window, on_back)

    @clickable
    def key_window(s):
        if not s.sl:
            Eval.SOUND(Const.BAD_SOUND).play()
            s.toast(Strings.ERROR_SELECT_SOMETHING)
            return
        si = s.memory[id(s.sl)]['event']
        if not (keys := Const.EVENT_KEYS.get(si, ())):
            Eval.SOUND(Const.BAD_SOUND).play()
            s.toast(Strings.NO_ACTIONS)
            return
        if s.window_on:
            s.dismiss_window()
        Eval.SOUND(Const.OK_SOUND).play()
        bui.buttonwidget(
            s.key_button,
            on_activate_call=Const.DO_NOTHING,
            selectable=False
        )
        start_pos = s.event_on and s.key_button_pos2 or s.key_button_pos
        end_pos = s.window_pos
        start_size = s.edit_button_size
        end_size = s.window_size
        butter = s.global_butter*1.3
        s.anims[id(s.key_button)]['window'] = Animate(
            s.key_button,
            duration=butter,
            attrs={
                'position': (start_pos, end_pos),
                'size': (start_size, end_size),
                'textcolor': (
                    (*Color.TEXT, Color.TEXT_OPACITY),
                    Const.INVISIBLE
                )
            }
        )
        s.anims[id(s.key_button)]['shadow'] = (
            Animate(
                widget=s.key_button_shadow,
                attrs={
                    'opacity': (0, Color.SHADOW_OPACITY),
                    'position': (
                        start_pos,
                        s.window_shadow_pos
                    ),
                    'size': (
                        start_size,
                        s.window_shadow_size
                    )
                },
                duration=butter
            )
        )
        ret = s.make_key_kids(
            title=Strings.KEYS_ON.format(
                list(Strings.EVENTS)[si]
            ),
            keys=keys
        )

        def on_back(): return (
            callable(ret) and ret(),
            s.key_clean()
        )
        s.window_on = (s.key_button, s.key_window, on_back)

    def make_key_kids(s, title, keys):
        s.make_window_default(title=title)
        s.make_key_default(keys)
        s.wrap_window_kids()
        s.animate_window_kids()

    def make_key_default(s, what):
        x, y = s.window_pos
        sx, sy = s.window_size
        text_push = 15
        delay = 0.35
        cur = s.memory[id(s.sl)]['keys']
        pos = (s.window_marg-s.window_fix, sy/2+s.window_marg-54)
        size = dx, dy = (150, sy/2-s.window_marg)
        what_scroll = bui.scrollwidget(
            parent=s.root,
            position=pos,
            color=Color.BASE,
            border_opacity=Color.OPACITY
        )
        s.window_kids.append((what_scroll, pos, text_push, delay,
                              ('size', ((dx-130, dy), size))
                              ))
        what_root = bui.containerwidget(
            parent=what_scroll,
            size=(dx, 30*len(what)),
            background=False
        )
        what_texts = []
        top = len(what)*30
        for j, i in enumerate(what, start=1):
            w = bui.textwidget(
                parent=what_root,
                size=(dx, 30),
                position=(0, top-j*30),
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                selectable=True,
                click_activate=True,
                on_activate_call=bui.CallPartial(
                    s.set_act, i
                ),
                text=Strings.ACTIONS[i],
                glow_type=Const.GLOW
            )
            what_texts.append(w)
        pos = (s.window_marg-s.window_fix, s.window_marg-4)
        size = dx, dy = (150, sy/2-(s.window_marg+50))
        cur_scroll = bui.scrollwidget(
            parent=s.root,
            position=pos,
            color=Color.BASE,
            border_opacity=Color.OPACITY
        )
        s.window_kids.append((cur_scroll, pos, text_push, delay,
                              ('size', ((dx-130, dy), size))
                              ))
        s.current_key_root = bui.containerwidget(
            parent=cur_scroll,
            size=(dx, 30*len(cur)),
            background=False
        )
        s.fresh_current_key_texts()
        pos = (sx*0.62, sy*0.43)
        t = bui.textwidget(
            parent=s.root,
            text=Strings.ACTION_PLACEHOLDER,
            position=pos,
            color=Const.INVISIBLE,
            h_align=Const.ALIGN,
            v_align=Const.ALIGN
        )
        s.window_kids.append((t, pos, 70, delay+0.13,
                              ('color', (
                                  Const.INVISIBLE,
                                  (*Color.TEXT, Color.TEXT_OPACITY)
                              ))
                              ))
        s.key_kids = [(t, 0)]
        s.window_trash = [what_texts, s.current_key_texts]

    def fresh_current_key_texts(s):
        for _ in s.current_key_root.get_children():
            _.delete()
        s.current_key_texts = []
        cur = s.memory[id(s.sl)]['keys']
        top = len(cur)*30
        dx = 150
        for i, g in enumerate(cur.items(), start=1):
            nam, c = g
            w = bui.textwidget(
                parent=s.current_key_root,
                size=(dx, 30),
                position=(0, top-i*30),
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                selectable=True,
                click_activate=True,
                maxwidth=dx-10,
                on_activate_call=bui.CallPartial(
                    s.set_act,
                    c['action'],
                    data=c['data'],
                    nam=nam
                ),
                text=nam,
                glow_type=Const.GLOW
            )
            s.current_key_texts.append(w)
        bui.containerwidget(s.current_key_root, size=(150, top))

    def key_clean(s):
        for k, _ in s.key_kids:
            if _ == 1:
                k.delete()
                continue
            s.anims[id(k)].reverse(
                on_finish=k.delete
            )
        s.key_kids.clear()

    def set_act(s, i, data=None, nam=''):
        butter = s.global_butter
        s.key_clean()
        x, y = (
            s.window_pos[0]+150+s.window_marg*2,
            s.window_pos[1]+s.window_marg
        )
        sx, sy = (
            s.window_size[0]-150-s.window_marg,
            s.window_size[1]-54
        )
        data = data or {}
        if i == 0:
            tx = Strings.ATTR
            t = bui.textwidget(
                parent=s.root,
                position=(x, y+sy-37-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            attr = bui.textwidget(
                parent=s.root,
                position=(x+70, y+sy-37-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80, 35),
                allow_clear_button=False,
                description=tx,
                v_align=Const.ALIGN,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                text=data.get('attr', '')
            )
            s.key_kids.append((attr, 1))
            tx = Strings.EVAL
            t = bui.textwidget(
                parent=s.root,
                position=(x, y+sy-37*2-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            val = bui.textwidget(
                parent=s.root,
                position=(x+70, y+sy-37*2-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80, 35),
                allow_clear_button=False,
                description=tx,
                v_align=Const.ALIGN,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                text=data.get('eval', '')
            )
            s.key_kids.append((val, 1))
            tx = Strings.NAME
            t = bui.textwidget(
                parent=s.root,
                position=(x, y+sy-37*3-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            name_inp = bui.textwidget(
                parent=s.root,
                position=(x+70, y+sy-37*3-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80, 35),
                allow_clear_button=False,
                description=tx,
                v_align=Const.ALIGN,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                text=nam
            )
            s.key_kids.append((name_inp, 1))
            bx, by = 100, 40
            tx = Strings.OFFSET
            t = bui.textwidget(
                parent=s.root,
                position=(x, y+sy-37*4-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            time_inp = bui.textwidget(
                parent=s.root,
                position=(x+70, y+sy-37*4-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80, 35),
                allow_clear_button=False,
                v_align=Const.ALIGN,
                description=tx,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                text=data.get('offset', '')
            )
            s.key_kids.append((time_inp, 1))
            _old_off = None

            def _off_spy():
                nonlocal _old_off
                if not time_inp.exists():
                    s.off_spy = None
                    return
                o = bui.textwidget(query=time_inp)
                if (
                    o.replace('.', '', 1).isdigit()
                    and (new := float(o)) != _old_off
                ):
                    mem = s.memory[id(s.sl)]
                    _old_off = new
                    mem.get('prev_off_wid') and s.widgets.pop(mem.pop('prev_off_wid')).delete()
                    if not (0 <= new <= mem['duration']):
                        return
                    s.prev_off_wid = bui.imagewidget(
                        parent=s.stamp_hscroll_root,
                        position=(
                            s.magic_x + s.entry_xs_real *
                            (mem['start'] + new) * s.entries_per_sec - s.entry_ys_real/4,
                            s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                        ),
                        size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                        texture=Eval.TEXTURE(Const.KEY),
                        color=Color.COLD,
                        opacity=Color.OPACITY
                    )
                    mem['prev_off'] = new
                    mem['prev_off_wid'] = id(s.prev_off_wid)
                    s.widgets[id(s.prev_off_wid)] = s.prev_off_wid
            s.off_spy = bui.AppTimer(
                0.02, _off_spy, repeat=True
            )

            def do_done():
                a = bui.textwidget(query=attr)
                ov = bui.textwidget(query=val)
                nam = bui.textwidget(query=name_inp)
                o = bui.textwidget(query=time_inp)
                if not a:
                    s.toast(Format.ERROR_EMPTY(Strings.ATTR))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not ov:
                    s.toast(Format.ERROR_EMPTY(Strings.EVAL))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not nam:
                    s.toast(Format.ERROR_EMPTY(Strings.NAME))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not o:
                    s.toast(Format.ERROR_EMPTY(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                try:
                    with bs.get_foreground_host_activity().context:
                        eval(ov)
                except Exception as e:
                    s.toast(Format.ERROR(e))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                try:
                    offset_val = float(o)
                except ValueError:
                    s.toast(Format.INVALID(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                mem = s.memory[id(s.sl)]
                if not (0 <= offset_val <= mem['duration']):
                    s.toast(Format.OUT_OF_RANGE(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                actual_time = mem['start'] + offset_val
                key_x = s.magic_x + s.entry_xs_real * actual_time * s.entries_per_sec - s.entry_ys_real/4
                key_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                key_wid = bui.imagewidget(
                    parent=s.stamp_hscroll_root,
                    position=(key_x, key_y),
                    size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                    texture=Eval.TEXTURE(Const.KEY),
                    color=Color.WARM,
                    opacity=Color.OPACITY
                )
                existed = False
                if nam in mem['keys']:
                    (wid := s.widgets.pop(mem['keys'][nam].get('widget'), None)) and wid.delete()
                    existed = True
                mem['keys'][nam] = {
                    'time': actual_time,
                    'action': i,
                    'data': {
                        'attr': a,
                        'eval': ov,
                        'offset': o
                    },
                    'widget': id(key_wid)
                }
                s.widgets[id(key_wid)] = key_wid
                s.toast(
                    existed and
                    Strings.INFO_EDITED_KEY or
                    Strings.INFO_ADDED_KEY
                )
                s.dismiss_window()
            b = bui.buttonwidget(
                parent=s.root,
                position=(x+sx-(bx+5), y),
                size=(bx, by),
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0,
                on_activate_call=do_done,
                enable_sound=False,
                label=Strings.DONE,
                color=Color.BASE,
                textcolor=Const.INVISIBLE
            )
            s.key_kids.append((b, 2))

            def do_pop():
                n = bui.textwidget(query=name_inp)
                if not n:
                    s.toast(Format.ERROR_EMPTY(Strings.NAME))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                mem = s.memory[id(s.sl)]
                if n not in mem['keys']:
                    s.toast(Format.NOT_FOUND(n))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                (wid := s.widgets.pop(mem['keys'].pop(n).get(
                    'widget', object()), None)) and wid.delete()
                s.toast(Strings.INFO_POPPED(n))
                Eval.SOUND(Const.OK_SOUND).play()
                s.fresh_current_key_texts()
            b = bui.buttonwidget(
                parent=s.root,
                position=(x+10, y),
                size=(bx, by),
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0,
                on_activate_call=do_pop,
                enable_sound=False,
                label=Strings.POP,
                color=Color.BASE,
                textcolor=Const.INVISIBLE
            )
            s.key_kids.append((b, 2))
        elif i == 1:
            if not s.event_on:
                s.toggle_event(passive=True)
            t = bui.textwidget(
                parent=s.root,
                position=(x+s.window_marg+5, y+sy-30),
                text=Strings.EXTEND_CODE,
                scale=1.5,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            t = bui.textwidget(
                parent=s.root,
                position=(x+s.window_marg-5, y+sy-70),
                text=Strings.CODE_HELP,
                maxwidth=sx-s.window_marg*2,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            tx = Strings.NAME
            t = bui.textwidget(
                parent=s.root,
                position=(x, y+sy-37*4.5+8),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            name_inp = bui.textwidget(
                parent=s.root,
                position=(x+70, y+sy-37*4.5+5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80, 35),
                allow_clear_button=False,
                v_align=Const.ALIGN,
                description=tx,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                text=data.get('name', '')
            )
            s.key_kids.append((name_inp, 1))
            tx = Strings.OFFSET
            t = bui.textwidget(
                parent=s.root,
                position=(x, y+sy-37*5.5+8),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            time_inp = bui.textwidget(
                parent=s.root,
                position=(x+70, y+sy-37*5.5+5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80, 35),
                allow_clear_button=False,
                v_align=Const.ALIGN,
                description=tx,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                text=str(data.get('offset', ''))
            )
            s.key_kids.append((time_inp, 1))
            _old_off = None

            def _off_spy():
                nonlocal _old_off
                if not time_inp.exists():
                    s.off_spy = None
                    return
                o = bui.textwidget(query=time_inp)
                if (
                    o.replace('.', '', 1).isdigit()
                    and (new := float(o)) != _old_off
                ):
                    mem = s.memory[id(s.sl)]
                    _old_off = new
                    mem.get('prev_off_wid') and s.widgets.pop(mem.pop('prev_off_wid')).delete()
                    if not (0 <= new <= mem['duration']):
                        return
                    s.prev_off_wid = bui.imagewidget(
                        parent=s.stamp_hscroll_root,
                        position=(
                            s.magic_x + s.entry_xs_real *
                            (mem['start'] + new) * s.entries_per_sec - s.entry_ys_real/4,
                            s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                        ),
                        size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                        texture=Eval.TEXTURE(Const.KEY),
                        color=Color.COLD,
                        opacity=Color.OPACITY
                    )
                    mem['prev_off'] = new
                    mem['prev_off_wid'] = id(s.prev_off_wid)
                    s.widgets[id(s.prev_off_wid)] = s.prev_off_wid
            s.off_spy = bui.AppTimer(
                0.02, _off_spy, repeat=True
            )

            def do_open():
                o = bui.textwidget(query=time_inp)
                n = bui.textwidget(query=name_inp)
                if not n:
                    s.toast(Format.ERROR_EMPTY(Strings.NAME))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not o:
                    s.toast(Format.ERROR_EMPTY(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                try:
                    offset_val = float(o)
                except ValueError:
                    s.toast(Format.INVALID(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                mem = s.memory[id(s.sl)]
                if not (0 <= offset_val <= mem['duration']):
                    s.toast(Format.OUT_OF_RANGE(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                s.forgive_prev_off = True
                node_mem = s.memory[id(s.sl)]
                is_spaz = node_mem.get('data', {}).get('type') == 'spaz'
                placeholder = (
                    Strings.SPAZ_CODE_PLACEHOLDER if is_spaz else None
                )
                s.event_window(
                    6,
                    force_title=Strings.CODE_EDITOR,
                    on_done=lambda final: add_key(final, n, offset_val, mem),
                    initial_code=data.get('code') or placeholder
                )

            def add_key(final, n, off, mem):
                actual_time = mem['start'] + off
                key_x = s.magic_x + s.entry_xs_real * actual_time * s.entries_per_sec - s.entry_ys_real/4
                key_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                key_wid = bui.imagewidget(
                    parent=s.stamp_hscroll_root,
                    position=(key_x, key_y),
                    size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                    texture=Eval.TEXTURE(Const.KEY),
                    color=Color.WARM,
                    opacity=Color.OPACITY
                )
                existed = False
                if n in mem['keys']:
                    (wid := s.widgets.pop(mem['keys'][n].get('widget'), None)) and wid.delete()
                    existed = True
                mem['keys'][n] = {
                    'time': actual_time,
                    'action': i,
                    'data': {
                        'offset': off,
                        'code': final['code'],
                        'name': n
                    },
                    'widget': id(key_wid)
                }
                s.widgets[id(key_wid)] = key_wid
                s.toast(
                    existed and
                    Strings.INFO_EDITED_KEY or
                    Strings.INFO_ADDED_KEY
                )
            bx, by = sx/2-s.window_marg*5, 40
            b = bui.buttonwidget(
                parent=s.root,
                position=(x+bx+s.window_marg*6+4, y),
                size=(bx, by),
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0,
                on_activate_call=do_open,
                enable_sound=False,
                label=Strings.NEXT,
                color=Color.BASE,
                textcolor=Const.INVISIBLE
            )
            s.key_kids.append((b, 2))

            def do_pop():
                n = bui.textwidget(query=name_inp)
                if not n:
                    s.toast(Format.ERROR_EMPTY(Strings.NAME))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                mem = s.memory[id(s.sl)]
                if n not in mem['keys']:
                    s.toast(Format.NOT_FOUND(n))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                (wid := s.widgets.pop(mem['keys'].pop(n).get(
                    'widget', object()), None)) and wid.delete()
                s.toast(Strings.INFO_POPPED(n))
                Eval.SOUND(Const.OK_SOUND).play()
                s.fresh_current_key_texts()
            b = bui.buttonwidget(
                parent=s.root,
                position=(x+10, y),
                size=(bx, by),
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0,
                on_activate_call=do_pop,
                enable_sound=False,
                label=Strings.POP,
                color=Color.BASE,
                textcolor=Const.INVISIBLE
            )
            s.key_kids.append((b, 2))
        elif i == 2:
            tx = Strings.VALUE
            t = bui.textwidget(
                parent=s.root,
                position=(x, y+sy-37-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            vol_inp = bui.textwidget(
                parent=s.root,
                position=(x+70, y+sy-37-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80, 35),
                allow_clear_button=False,
                v_align=Const.ALIGN,
                description=tx,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                text=str(data.get('volume', ''))
            )
            s.key_kids.append((vol_inp, 1))
            bx, by = 100, 40
            tx = Strings.OFFSET
            t = bui.textwidget(
                parent=s.root,
                position=(x, y+sy-37*2-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            time_inp = bui.textwidget(
                parent=s.root,
                position=(x+70, y+sy-37*2-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80, 35),
                allow_clear_button=False,
                v_align=Const.ALIGN,
                description=tx,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                text=str(data.get('offset', ''))
            )
            s.key_kids.append((time_inp, 1))
            tx = Strings.NAME
            t = bui.textwidget(
                parent=s.root,
                position=(x, y+sy-37*3-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            name_inp = bui.textwidget(
                parent=s.root,
                position=(x+70, y+sy-37*3-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80, 35),
                allow_clear_button=False,
                v_align=Const.ALIGN,
                description=tx,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                text=str(data.get('name', ''))
            )
            s.key_kids.append((name_inp, 1))
            _old_off = None

            def _off_spy():
                nonlocal _old_off
                if not time_inp.exists():
                    s.off_spy = None
                    return
                o = bui.textwidget(query=time_inp)
                if (
                    o.replace('.', '', 1).isdigit()
                    and (new := float(o)) != _old_off
                ):
                    mem = s.memory[id(s.sl)]
                    _old_off = new
                    mem.get('prev_off_wid') and s.widgets.pop(mem.pop('prev_off_wid')).delete()
                    if not (0 <= new <= mem['duration']):
                        return
                    s.prev_off_wid = bui.imagewidget(
                        parent=s.stamp_hscroll_root,
                        position=(
                            s.magic_x + s.entry_xs_real *
                            (mem['start'] + new) * s.entries_per_sec - s.entry_ys_real/4,
                            s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                        ),
                        size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                        texture=Eval.TEXTURE(Const.KEY),
                        color=Color.COLD,
                        opacity=Color.OPACITY
                    )
                    mem['prev_off'] = new
                    mem['prev_off_wid'] = id(s.prev_off_wid)
                    s.widgets[id(s.prev_off_wid)] = s.prev_off_wid
            s.off_spy = bui.AppTimer(
                0.02, _off_spy, repeat=True
            )

            def do_done():
                v = bui.textwidget(query=vol_inp)
                o = bui.textwidget(query=time_inp)
                nam = bui.textwidget(query=name_inp)
                if not v:
                    s.toast(Format.ERROR_EMPTY(Strings.VALUE))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not o:
                    s.toast(Format.ERROR_EMPTY(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not nam:
                    s.toast(Format.ERROR_EMPTY(Strings.NAME))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                try:
                    volume_val = round(float(v), 2)
                except ValueError:
                    s.toast(Format.INVALID(Strings.VOLUME))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                try:
                    offset_val = float(o)
                except ValueError:
                    s.toast(Format.INVALID(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                mem = s.memory[id(s.sl)]
                if not (0 <= offset_val <= mem['duration']):
                    s.toast(Format.OUT_OF_RANGE(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                actual_time = mem['start'] + offset_val
                key_x = s.magic_x + s.entry_xs_real * actual_time * s.entries_per_sec - s.entry_ys_real/4
                key_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                key_wid = bui.imagewidget(
                    parent=s.stamp_hscroll_root,
                    position=(key_x, key_y),
                    size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                    texture=Eval.TEXTURE(Const.KEY),
                    color=Color.WARM,
                    opacity=Color.OPACITY
                )
                existed = False
                if nam in mem['keys']:
                    existed = True
                    (wid := s.widgets.pop(mem['keys'][nam].get('widget'), None)) and wid.delete()
                mem['keys'][nam] = {
                    'time': actual_time,
                    'action': i,
                    'data': {
                        'volume': volume_val,
                        'offset': offset_val,
                        'name': nam
                    },
                    'widget': id(key_wid)
                }
                s.widgets[id(key_wid)] = key_wid
                s.toast(
                    existed and
                    Strings.INFO_EDITED_KEY or
                    Strings.INFO_ADDED_KEY
                )
                s.dismiss_window()
            b = bui.buttonwidget(
                parent=s.root,
                position=(x+sx-(bx+5), y),
                size=(bx, by),
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0,
                on_activate_call=do_done,
                enable_sound=False,
                label=Strings.DONE,
                color=Color.BASE,
                textcolor=Const.INVISIBLE
            )
            s.key_kids.append((b, 2))

            def do_pop():
                t = bui.textwidget(query=name_inp)
                mem = s.memory[id(s.sl)]
                if not t:
                    s.toast(Strings.INFO_POP_WHAT)
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if t not in mem['keys']:
                    s.toast(Format.NOT_FOUND(t))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                (wid := s.widgets.pop(mem['keys'].pop(t).get(
                    'widget', object()), None)) and wid.delete()
                s.toast(Strings.INFO_POPPED(t))
                Eval.SOUND(Const.OK_SOUND).play()
                s.fresh_current_key_texts()
            b = bui.buttonwidget(
                parent=s.root,
                position=(x+(sx/2-145), y),
                size=(bx, by),
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0,
                on_activate_call=do_pop,
                enable_sound=False,
                label=Strings.POP,
                color=Color.BASE,
                textcolor=Const.INVISIBLE
            )
            s.key_kids.append((b, 2))
        elif i == 3:
            tx = Strings.TEXT
            t = bui.textwidget(
                parent=s.root,
                position=(x, y+sy-37-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            text_inp = bui.textwidget(
                parent=s.root,
                position=(x+70, y+sy-37-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80, 35),
                allow_clear_button=False,
                description=tx,
                v_align=Const.ALIGN,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                text=str(data.get('text', 'Hello!'))
            )
            s.key_kids.append((text_inp, 1))
            tx = Strings.COLOR
            t = bui.textwidget(
                parent=s.root,
                position=(x, y+sy-37*2-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            color_inp = bui.textwidget(
                parent=s.root,
                position=(x+70, y+sy-37*2-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80, 35),
                allow_clear_button=False,
                description=tx,
                v_align=Const.ALIGN,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                text=str(data.get('color', '(1,1,1)'))
            )
            s.key_kids.append((color_inp, 1))
            tx = Strings.TIME
            t = bui.textwidget(
                parent=s.root,
                position=(x, y+sy-37*3-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            btime_inp = bui.textwidget(
                parent=s.root,
                position=(x+70, y+sy-37*3-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80, 35),
                allow_clear_button=False,
                description=tx,
                v_align=Const.ALIGN,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                text=str(data.get('time', 4))
            )
            s.key_kids.append((btime_inp, 1))
            tx = Strings.NAME
            t = bui.textwidget(
                parent=s.root,
                position=(x, y+sy-37*4-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            name_inp = bui.textwidget(
                parent=s.root,
                position=(x+70, y+sy-37*4-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80, 35),
                allow_clear_button=False,
                description=tx,
                v_align=Const.ALIGN,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                text=nam
            )
            s.key_kids.append((name_inp, 1))
            bx, by = 100, 40
            tx = Strings.OFFSET
            t = bui.textwidget(
                parent=s.root,
                position=(x, y+sy-37*5-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t, 0))
            time_inp = bui.textwidget(
                parent=s.root,
                position=(x+70, y+sy-37*5-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80, 35),
                allow_clear_button=False,
                v_align=Const.ALIGN,
                description=tx,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                text=str(data.get('offset', ''))
            )
            s.key_kids.append((time_inp, 1))
            _old_off = None

            def _off_spy():
                nonlocal _old_off
                if not time_inp.exists():
                    s.off_spy = None
                    return
                o = bui.textwidget(query=time_inp)
                if (
                    o.replace('.', '', 1).isdigit()
                    and (new := float(o)) != _old_off
                ):
                    mem = s.memory[id(s.sl)]
                    _old_off = new
                    mem.get('prev_off_wid') and s.widgets.pop(mem.pop('prev_off_wid')).delete()
                    if not (0 <= new <= mem['duration']):
                        return
                    s.prev_off_wid = bui.imagewidget(
                        parent=s.stamp_hscroll_root,
                        position=(
                            s.magic_x + s.entry_xs_real *
                            (mem['start'] + new) * s.entries_per_sec - s.entry_ys_real/4,
                            s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                        ),
                        size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                        texture=Eval.TEXTURE(Const.KEY),
                        color=Color.COLD,
                        opacity=Color.OPACITY
                    )
                    mem['prev_off'] = new
                    mem['prev_off_wid'] = id(s.prev_off_wid)
                    s.widgets[id(s.prev_off_wid)] = s.prev_off_wid
            s.off_spy = bui.AppTimer(
                0.02, _off_spy, repeat=True
            )

            def do_done():
                txt = bui.textwidget(query=text_inp)
                col = bui.textwidget(query=color_inp)
                bt = bui.textwidget(query=btime_inp)
                o = bui.textwidget(query=time_inp)
                nam = bui.textwidget(query=name_inp)
                if not txt:
                    s.toast(Format.ERROR_EMPTY(Strings.TEXT))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not col:
                    s.toast(Format.ERROR_EMPTY(Strings.COLOR))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not bt:
                    s.toast(Format.ERROR_EMPTY(Strings.TIME))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not nam:
                    s.toast(Format.ERROR_EMPTY(Strings.NAME))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not o:
                    s.toast(Format.ERROR_EMPTY(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                try:
                    with bs.get_foreground_host_activity().context:
                        eval(col)
                except Exception as e:
                    s.toast(Format.ERROR(e))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                try:
                    time_val = float(bt)
                except ValueError:
                    s.toast(Format.INVALID(Strings.TIME))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                try:
                    offset_val = float(o)
                except ValueError:
                    s.toast(Format.INVALID(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                mem = s.memory[id(s.sl)]
                if not (0 <= offset_val <= mem['duration']):
                    s.toast(Format.OUT_OF_RANGE(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                actual_time = mem['start'] + offset_val
                key_x = s.magic_x + s.entry_xs_real * actual_time * s.entries_per_sec - s.entry_ys_real/4
                key_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                key_wid = bui.imagewidget(
                    parent=s.stamp_hscroll_root,
                    position=(key_x, key_y),
                    size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                    texture=Eval.TEXTURE(Const.KEY),
                    color=Color.WARM,
                    opacity=Color.OPACITY
                )
                existed = False
                if nam in mem['keys']:
                    (wid := s.widgets.pop(mem['keys'][nam].get('widget'), None)) and wid.delete()
                    existed = True
                mem['keys'][nam] = {
                    'time': actual_time,
                    'action': i,
                    'data': {
                        'text': txt,
                        'color': col,
                        'time': time_val,
                        'offset': o,
                        'name': nam
                    },
                    'widget': id(key_wid)
                }
                s.widgets[id(key_wid)] = key_wid
                s.toast(
                    existed and
                    Strings.INFO_EDITED_KEY or
                    Strings.INFO_ADDED_KEY
                )
                s.dismiss_window()
            b = bui.buttonwidget(
                parent=s.root,
                position=(x+sx-(bx+5), y),
                size=(bx, by),
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0,
                on_activate_call=do_done,
                enable_sound=False,
                label=Strings.DONE,
                color=Color.BASE,
                textcolor=Const.INVISIBLE
            )
            s.key_kids.append((b, 2))

            def do_pop():
                n = bui.textwidget(query=name_inp)
                if not n:
                    s.toast(Format.ERROR_EMPTY(Strings.NAME))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                mem = s.memory[id(s.sl)]
                if n not in mem['keys']:
                    s.toast(Format.NOT_FOUND(n))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                (wid := s.widgets.pop(mem['keys'].pop(n).get(
                    'widget', object()), None)) and wid.delete()
                s.toast(Strings.INFO_POPPED(n))
                Eval.SOUND(Const.OK_SOUND).play()
                s.fresh_current_key_texts()
            b = bui.buttonwidget(
                parent=s.root,
                position=(x+10, y),
                size=(bx, by),
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0,
                on_activate_call=do_pop,
                enable_sound=False,
                label=Strings.POP,
                color=Color.BASE,
                textcolor=Const.INVISIBLE
            )
            s.key_kids.append((b, 2))
        for k, _ in s.key_kids:
            if _ == 1:
                continue
            attrs = _ == 2 and {
                'opacity': (0, Color.OPACITY),
                'textcolor': (
                    Const.INVISIBLE,
                    (*Color.TEXT, Color.TEXT_OPACITY)
                )
            } or {
                'color': (
                    Const.INVISIBLE,
                    (*Color.TEXT, Color.TEXT_OPACITY)
                )
            }
            s.anims[id(k)] = Animate(
                widget=k,
                attrs=attrs,
                duration=butter
            )

    def clear_memory(s):
        Config.set('last', None)

    def load_memory(s, memory, shut=False):
        sorted_entries = sorted(
            memory.items(),
            key=lambda x: x[1]['order']
        )

        total_count = len(sorted_entries)

        for idx, (old_id, mem_data) in enumerate(sorted_entries):
            data = mem_data['data'].copy()
            smol = mem_data.get('smol', False)

            if smol:
                size = (
                    s.entry_ys_real,
                    s.entry_ys_real - s.magic_y
                )
            else:
                size = (
                    s.entry_xs_real * (
                        mem_data['duration'] * s.entries_per_sec
                    ) * s.magic_right,
                    s.entry_ys_real - s.magic_y
                )

            btn = bui.buttonwidget(
                parent=s.stamp_hscroll_root,
                texture=Eval.TEXTURE(Const.SKIN),
                label=data['name'],
                textcolor=(*Color.TEXT, Color.TEXT_OPACITY),
                color=Color.BASE,
                opacity=0,
                enable_sound=False,
                size=size,
                button_type='square'
            )

            bui.buttonwidget(
                btn,
                on_activate_call=bui.CallPartial(s.select, btn)
            )

            s.stamp_kids.append(btn)

            new_mem = {
                'order': idx,
                'event': mem_data['event'],
                'data': data,
                'duration': mem_data['duration'],
                'start': mem_data['start'],
                'keys': {},
                'smol': smol
            }

            s.memory[id(btn)] = new_mem

            y_pos = s.entry_ys_real * (total_count - idx - 1)

            for key_name, key_data_orig in mem_data.get('keys', {}).items():
                key_data = key_data_orig.copy()

                if 'widget' in key_data:
                    del key_data['widget']

                key_time = key_data['time']
                key_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4

                key_wid = bui.imagewidget(
                    parent=s.stamp_hscroll_root,
                    position=(key_x, y_pos),
                    size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                    texture=Eval.TEXTURE(Const.KEY),
                    color=Color.WARM,
                    opacity=Color.OPACITY
                )

                new_mem['keys'][key_name] = {
                    **key_data,
                    'widget': id(key_wid)
                }
                s.widgets[id(key_wid)] = key_wid

            width_in_steps = mem_data['duration'] * s.entries_per_sec
            x_pos = s.magic_x + s.entry_xs_real * mem_data['start'] * s.entries_per_sec + (
                width_in_steps * s.magic_left
            )

            bui.buttonwidget(btn, position=(x_pos, y_pos))

        s.build_timeline()

        s.wrap([1, 2, 3], on_finish=s.bottom_left)
        s.make_timeline()
        s.wrap_timeline()

        if len(s.memory):
            s.show_controls()

        s.top_left()
        if shut:
            return
        Eval.SOUND(Const.OK_SOUND).play()
        s.toast(Format.LOADED_ENTRIES(len(memory)))

    def wrap(s, what=0, on_finish=None, init=False):
        rx, ry = s.real = bui.get_virtual_screen_size()
        sx, sy = s.stamp_size = (rx, 150)
        smoly = sy-s.stamp_hack
        old_deep_y = getattr(s, 'stamp_deep_y', smoly)
        s.stamp_deep_y = max(s.entry_ys_real*(len(s.memory)+1), smoly)
        smolx = sx-s.stamp_hack
        old_deep_x = getattr(s, 'stamp_deep_x', smolx)
        if hasattr(s, 'timeline') and s.timeline:
            s.max_time = s.timeline[-1]['time']
        else:
            times = [
                _['start'] + _['duration']
                for _ in s.memory.values()
            ] or [0]
            s.max_time = max(times)
        rightmost_edge = (
            s.max_time * s.entries_per_sec * s.entry_xs_real
        )
        s.stamp_deep_x = max(rightmost_edge + s.entry_xs_real * 1, smolx)
        y_off = 70
        xoff, = Eval.SCALE_REAL(25)
        one, = Eval.SCALE_REAL(1)
        s.event_kid_ts = one
        one_ba, = Eval.SCALE_BA(1)
        s.window_size = wx, wy = 450, 300
        s.window_pos = Eval.OFFSET(rx, ry, -wx/2, -wy/2, 0, -y_off*2)
        (
            s.window_shadow_pos,
            s.window_shadow_size
        ) = Eval.SHADOW(
            *s.window_pos,
            *s.window_size
        )
        s.event_button_size = dx, dy = Eval.SCALE_REAL(100, 40)
        s.event_kid_off, = Eval.SCALE_REAL(40)
        num_events = len(Strings.EVENTS)
        button_height = 40
        spacing = 10
        menu_height = button_height * (num_events + 1) + spacing * (num_events + 2)
        ex, ey = s.event_menu_size = Eval.SCALE_REAL(300, menu_height)
        s.event_kid_size = (ex-s.event_kid_off, dy)

        s.edit_button_xoff, = Eval.SCALE_REAL(200)
        s.edit_button_xtra, = Eval.SCALE_REAL(10)
        s.edit_button_pos = pos = (
            dx+s.edit_button_xtra,
            sy+6.5
        )
        s.edit_button_pos2 = (
            pos[0]+ex-dx,
            pos[1]
        )
        s.edit_button_size = (dx-4, dy-3)
        s.key_button_pos = pos = (
            (dx+s.edit_button_xtra)*2,
            sy+6.5
        )
        s.key_button_pos2 = (
            pos[0]+ex-dx,
            pos[1]
        )
        s.control_off, = Eval.SCALE_REAL(5)
        s.control_size = conx, cony = Eval.SCALE_REAL(50, 50)
        s.control_pos = lambda i: (
            sx-conx*(i+1)-s.control_off*i-2, sy+s.control_off
        )
        s.tool_off, = Eval.SCALE_REAL(5)
        s.tool_size = tx, ty = Eval.SCALE_REAL(50, 50)
        s.tool_pos = lambda i: (
            sx-tx*(i+1)-s.tool_off*i-2, sy+s.tool_off
        )
        if not isinstance(what, list):
            what = [what]
        yes = 0 in what
        if yes or 1 in what:
            bui.containerwidget(
                s.root,
                size=s.stamp_size,
                stack_offset=Eval.OFFSET(-rx, -ry, sx/2, sy/2)
            )
            s.toast_position = (
                sx/2,
                ry-40 if Settings.get('toast_top') else sy+10
            )
            bui.imagewidget(s.stamp_bg, size=s.stamp_size)
            bx, = Eval.SCALE_BA(55)
            px1, _ = Eval.OFFSET(
                rx, ry, *bui.get_special_widget(
                    'menu_button'
                ).get_screen_space_center(), bx, bx
            )
            px2, py = Eval.OFFSET(
                rx, ry, *bui.get_special_widget(
                    'squad_button'
                ).get_screen_space_center(), bx, bx
            )
            bui.buttonwidget(
                s.square,
                position=(px1, py),
                size=(bx, bx),
                text_scale=one_ba
            )
            bui.buttonwidget(
                s.triangle,
                position=(px2, py),
                size=(bx, bx),
                text_scale=one_ba
            )
            s.circle_pos = (px2-bx, py)
            s.circle_size = (bx, bx)
            s.about_pos = (px2-bx*2-s.control_off, py)
            s.about_size = (bx, bx)
            win = s.circle in s.window_on
            bui.buttonwidget(
                s.circle,
                position=(
                    win and s.window_pos
                    or s.circle_pos
                ),
                size=(
                    win and s.window_size
                    or s.circle_size
                ),
                text_scale=one_ba
            )
            if win:
                a = s.anims[id(s.circle)]['window'].attrs_start
                a['position'] = s.circle_pos
                a['size'] = s.circle_size
                a = s.anims[id(s.circle)]['shadow'].attrs_start
                a['position'] = s.circle_pos
                a['size'] = s.circle_size
            about_win = s.about in s.window_on
            bui.buttonwidget(
                s.about,
                position=(
                    about_win and s.window_pos
                    or s.about_pos
                ),
                size=(
                    about_win and s.window_size
                    or s.about_size
                ),
                text_scale=one_ba
            )
            if about_win:
                a = s.anims[id(s.about)]['window'].attrs_start
                a['position'] = s.about_pos
                a['size'] = s.about_size
                a = s.anims[id(s.about)]['shadow'].attrs_start
                a['position'] = s.about_pos
                a['size'] = s.about_size
            bui.textwidget(
                s.top_left_h,
                position=(0, s.stamp_deep_y)
            )
            bui.textwidget(
                s.top_left_v,
                position=(0, s.stamp_deep_y)
            )
        if yes or 2 in what:
            bui.scrollwidget(
                s.stamp_scroll,
                size=s.stamp_size
            )

            height_changed = old_deep_y != s.stamp_deep_y
            width_changed = old_deep_x != s.stamp_deep_x

            if height_changed or width_changed:
                butter = s.global_butter/2

                def fix_timeline_after_resize():
                    for i, (t, l) in enumerate(s.stamp_timeline):
                        px = i * s.entry_xs_real
                        py = s.stamp_deep_y - 20
                        bui.textwidget(t, position=(px, py))
                        bui.imagewidget(
                            l,
                            position=(px + 4, -s.stamp_deep_y / 2),
                            size=(2, s.stamp_deep_y * 2)
                        )
                    if callable(on_finish):
                        on_finish()

                s.anims[id(s.stamp_scroll_root)] = Animate(
                    widget=s.stamp_scroll_root,
                    attrs={
                        'size': (
                            (sx, old_deep_y),
                            (sx, s.stamp_deep_y)
                        )
                    },
                    duration=butter
                )
                s.anims[id(s.stamp_hscroll)] = Animate(
                    widget=s.stamp_hscroll,
                    attrs={
                        'size': (
                            (sx, old_deep_y),
                            (sx, s.stamp_deep_y)
                        )
                    },
                    duration=butter
                )
                s.anims[id(s.stamp_hscroll_root)] = Animate(
                    widget=s.stamp_hscroll_root,
                    attrs={
                        'size': (
                            (old_deep_x, old_deep_y),
                            (s.stamp_deep_x, s.stamp_deep_y)
                        )
                    },
                    duration=butter,
                    on_finish=fix_timeline_after_resize
                )
            else:
                bui.containerwidget(
                    s.stamp_scroll_root,
                    size=(sx, s.stamp_deep_y)
                )
                bui.hscrollwidget(
                    s.stamp_hscroll,
                    size=(sx, s.stamp_deep_y)
                )
                bui.containerwidget(
                    s.stamp_hscroll_root,
                    size=(s.stamp_deep_x, s.stamp_deep_y)
                )
                if callable(on_finish):
                    on_finish()
        if yes or 3 in what:
            if not init:
                s.wrap_timeline()
        if yes or 4 in what:
            dx, dy = (
                s.event_on and
                s.event_menu_size or
                s.event_button_size
            )
            bui.imagewidget(
                s.event_root,
                size=(dx, dy),
                position=(0, sy+5)
            )
            if s.event_on:
                a = s.anims[id(s.event_root)].attrs_end
                a['size'] = s.event_menu_size
                a = s.anims[id(s.event_root)].attrs_start
                a['size'] = s.event_button_size
                a = s.anims[id(s.event_root)].attrs_current
                a['size'] = s.event_menu_size
            bui.buttonwidget(
                s.event_button,
                size=s.event_button_size,
                position=(0, sy+5),
                text_scale=one
            )
            s.event_top = sy+ey+5
            s.ev_mult = s.event_button_size[1]+Eval.SCALE_REAL(10)[0]
            s.ev_x, = Eval.SCALE_REAL(20)
            for i, g in enumerate(s.event_kids.items(), start=1):
                kid, dat = g
                win = kid in s.window_on
                pos = (s.ev_x, s.event_top-s.ev_mult*i)
                size = s.event_kid_size
                bui.buttonwidget(
                    kid,
                    position=(
                        win and s.window_pos
                        or pos
                    ),
                    size=(
                        win and s.window_size
                        or size
                    ),
                    text_scale=one
                )
                bui.imagewidget(
                    dat['shadow'],
                    position=(
                        win and s.window_shadow_pos
                        or pos
                    ),
                    size=(
                        win and s.window_shadow_size
                        or size
                    )
                )
                if win:
                    a = s.anims[id(kid)]['window'].attrs_end
                    a['position'] = s.window_pos
                    a['size'] = s.window_size
                    a = s.anims[id(kid)]['window'].attrs_start
                    a['position'] = pos
                    a['size'] = size
                    a = s.anims[id(kid)]['window'].attrs_current
                    a['position'] = s.window_pos
                    a['size'] = s.window_size
                    a = s.anims[id(kid)]['shadow'].attrs_end
                    a['position'] = s.window_shadow_pos
                    a['size'] = s.window_shadow_size
                    a = s.anims[id(kid)]['shadow'].attrs_start
                    a['position'] = pos
                    a['size'] = size
                    a = s.anims[id(kid)]['shadow'].attrs_current
                    a['position'] = s.window_shadow_pos
                    a['size'] = s.window_shadow_size
        if yes or 5 in what:
            win = s.edit_button in s.window_on
            pos = (
                s.event_on and
                s.edit_button_pos2 or
                s.edit_button_pos
            )
            size = s.edit_button_size
            bui.buttonwidget(
                s.edit_button,
                size=(
                    win and s.window_size or
                    s.edit_button_size
                ),
                position=(
                    win and s.window_pos
                    or pos
                ),
                text_scale=one
            )
            if win:
                a = s.anims[id(s.edit_button)]['window'].attrs_start
                a['position'] = pos
                a['size'] = size
                a = s.anims[id(s.edit_button)]['shadow'].attrs_start
                a['position'] = pos
                a['size'] = size
        if yes or 6 in what:
            win = s.key_button in s.window_on
            pos = (
                s.event_on and
                s.key_button_pos2 or
                s.key_button_pos
            )
            size = s.edit_button_size
            bui.buttonwidget(
                s.key_button,
                size=(
                    win and s.window_size or
                    s.edit_button_size
                ),
                position=(
                    win and s.window_pos
                    or pos
                ),
                text_scale=one
            )
            if win:
                a = s.anims[id(s.key_button)]['window'].attrs_start
                a['position'] = pos
                a['size'] = size
                a = s.anims[id(s.key_button)]['shadow'].attrs_start
                a['position'] = pos
                a['size'] = size
        if yes or 9 in what:
            win = s.circle in s.window_on
            pos = s.circle_pos
            size = s.circle_size
            bui.buttonwidget(
                s.circle,
                size=(
                    win and s.window_size or
                    s.circle_size
                ),
                position=(
                    win and s.window_pos
                    or pos
                ),
                text_scale=one
            )
            if win:
                a = s.anims[id(s.circle)]['window'].attrs_start
                a['position'] = pos
                a['size'] = size
                a = s.anims[id(s.circle)]['shadow'].attrs_start
                a['position'] = pos
                a['size'] = size
            about_win = s.about in s.window_on
            about_pos = s.about_pos
            about_size = s.about_size
            bui.buttonwidget(
                s.about,
                size=(
                    about_win and s.window_size or
                    s.about_size
                ),
                position=(
                    about_win and s.window_pos
                    or about_pos
                ),
                text_scale=one
            )
            if about_win:
                a = s.anims[id(s.about)]['window'].attrs_start
                a['position'] = about_pos
                a['size'] = about_size
                a = s.anims[id(s.about)]['shadow'].attrs_start
                a['position'] = about_pos
                a['size'] = about_size
        if yes or 7 in what:
            for i, b in enumerate(s.controls):
                bui.buttonwidget(
                    b,
                    size=(
                        (0, 0) if init or not
                        s.controls_shown else
                        s.control_size
                    ),
                    position=s.control_pos(i),
                    text_scale=one
                )
        if yes or 8 in what:
            for i, b in enumerate(s.tools):
                bui.buttonwidget(
                    b,
                    size=init and (0, 0) or s.tool_size,
                    position=s.tool_pos(i),
                    text_scale=one
                )

    def bottom_left(s, dry=False):
        if not dry:
            bui.containerwidget(
                s.stamp_hscroll_root,
                visible_child=s.bottom_left_h
            )
            bui.containerwidget(
                s.stamp_scroll_root,
                visible_child=s.bottom_left_v
            )
        cx, cy = s.bottom_left_h.get_screen_space_center()
        rx, ry = s.real
        return (
            cx+rx/2-5+s.magic_x,
            cy+ry/2-5
        )

    def top_left(s):
        bui.containerwidget(
            s.stamp_hscroll_root,
            visible_child=s.top_left_h
        )
        bui.containerwidget(
            s.stamp_scroll_root,
            visible_child=s.top_left_v
        )

    def on_square(s):
        if s.ui_clickable is None:
            s.toast(Strings.INFO_SLOW_DOWN)
            Eval.SOUND(Const.BAD_SOUND)
            return
        s.toggle_menu()

    def on_triangle(s):
        bui.get_special_widget('squad_button').activate()

    @clickable
    def on_circle(s):
        if s.window_on:
            s.dismiss_window()
        Eval.SOUND(Const.OK_SOUND).play()
        bui.buttonwidget(
            s.circle,
            on_activate_call=Const.DO_NOTHING,
            selectable=False
        )
        start_pos = s.circle_pos
        end_pos = s.window_pos
        start_size = s.circle_size
        end_size = s.window_size
        butter = s.global_butter*1.3
        s.anims[id(s.circle)]['window'] = Animate(
            s.circle,
            duration=butter,
            attrs={
                'position': (start_pos, end_pos),
                'size': (start_size, end_size),
                'opacity': (1, Color.OPACITY),
                'textcolor': (
                    (*Color.TEXT, Color.TEXT_OPACITY),
                    Const.INVISIBLE
                )
            }
        )
        s.anims[id(s.circle)]['shadow'] = (
            Animate(
                widget=s.circle_shadow,
                attrs={
                    'opacity': (0, Color.SHADOW_OPACITY),
                    'position': (
                        start_pos,
                        s.window_shadow_pos
                    ),
                    'size': (
                        start_size,
                        s.window_shadow_size
                    )
                },
                duration=butter
            )
        )
        s.make_window_kids_settings()

        def settings_on_back():
            if s.settings_opacity_dirty:
                s.settings_opacity_dirty = False
                s.refresh_opacity_via_ui_toggle()
        s.window_on = (s.circle, s.on_circle, settings_on_back)

    @clickable
    def on_about(s):
        if s.window_on:
            s.dismiss_window()
        Eval.SOUND(Const.OK_SOUND).play()
        bui.buttonwidget(
            s.about,
            on_activate_call=Const.DO_NOTHING,
            selectable=False
        )
        start_pos = s.about_pos
        end_pos = s.window_pos
        start_size = s.about_size
        end_size = s.window_size
        butter = s.global_butter*1.3
        s.anims[id(s.about)]['window'] = Animate(
            s.about,
            duration=butter,
            attrs={
                'position': (start_pos, end_pos),
                'size': (start_size, end_size),
                'opacity': (1, Color.OPACITY),
                'textcolor': (
                    (*Color.TEXT, Color.TEXT_OPACITY),
                    Const.INVISIBLE
                )
            }
        )
        s.anims[id(s.about)]['shadow'] = (
            Animate(
                widget=s.about_shadow,
                attrs={
                    'opacity': (0, Color.SHADOW_OPACITY),
                    'position': (
                        start_pos,
                        s.window_shadow_pos
                    ),
                    'size': (
                        start_size,
                        s.window_shadow_size
                    )
                },
                duration=butter
            )
        )
        s.make_window_kids_about()
        s.window_on = (s.about, s.on_about, None)

    def open_side_picker(s, btn, btn_screen_pos, btn_size, shadow, options, get_current, on_pick, label=None, option_color=None, option_textcolor=None):
        """Generic 'grow a button into a side list' picker - the same
        interaction make_node_window uses for its node-type picker,
        pulled out so any button anywhere (settings' Theme/Language
        cycles included) can open one without re-implementing the
        grow/shrink/stagger/close_sub machinery. Traps on_back the
        same way: wires s.window_sub_on so universal_back and every
        other close-this-window path closes the picker first instead
        of falling through past it.

        btn: the button widget that grows into the picker panel.
        btn_screen_pos: that button's *screen-space* position (i.e.
            window position + its local offset) - needed because the
            grow animation interpolates from here, not from wherever
            the button's local (window-relative) position says.
        btn_size: the button's current (shrunk) size.
        shadow: an imagewidget used purely for the picker's drop
            shadow while open (mirrors type_btn_shadow).
        options: list of label strings, offered top-to-bottom.
        get_current: zero-arg callable returning whichever option is
            currently selected (drawn highlighted) - a callable
            rather than a fixed value so reopening after a pick
            always highlights the up-to-date choice.
        on_pick(value): called with the chosen option; picker closes
            right after.
        label: display text per option; defaults to the option itself
            (callers needing e.g. capitalized labels pass this).
        option_color(opt): optional - returns the swatch color for
            that specific option (e.g. the theme picker passes each
            theme's own 'base' tuple, so every row previews what it
            will actually set Color.BASE to). Defaults to None, which
            keeps the old behavior of every row sharing Color.BASE
            with only the current pick tinted Color.COLD.
        option_textcolor(opt): optional, same idea for the row's own
            label color (theme picker passes each theme's 'text').
            Defaults to None, which keeps using the live Color.TEXT
            for every row."""
        if s.window_sub_on:
            s.window_sub_on[2]()
        Eval.SOUND(Const.OK_SOUND).play()
        bui.buttonwidget(btn, on_activate_call=Const.DO_NOTHING, selectable=False)

        wx, wy = s.window_pos
        wsx, wsy = s.window_size
        picker_x, picker_sx = 150, 160
        picker_pos = (wx+wsx+100, wy)
        picker_size = (picker_sx, wsy)
        (
            picker_shadow_pos,
            picker_shadow_size
        ) = Eval.SHADOW(*picker_pos, *picker_size)

        btn_start_pos, btn_start_size = btn_screen_pos, btn_size
        butter = s.global_butter*1.3

        grow_anim = Animate(
            widget=btn,
            duration=butter,
            attrs={
                'position': (btn_start_pos, picker_pos),
                'size': (btn_start_size, picker_size),
                'textcolor': (
                    (*Color.TEXT, Color.TEXT_OPACITY),
                    Const.INVISIBLE
                )
            }
        )
        shadow_anim = Animate(
            widget=shadow,
            attrs={
                'opacity': (0, Color.SHADOW_OPACITY),
                'position': (btn_start_pos, picker_shadow_pos),
                'size': (btn_start_size, picker_shadow_size)
            },
            duration=butter
        )

        child_start_progress = 0.35
        child_delay = butter*child_start_progress
        child_duration = butter*(1-child_start_progress)+0.05

        picker_kids = []
        kid_anims = []

        picker_scroll = bui.scrollwidget(
            parent=s.root,
            position=picker_pos,
            size=(0, picker_size[1]),
            color=Color.COLD,
            border_opacity=0
        )
        picker_kids.append(picker_scroll)
        kid_anims.append(Animate(
            widget=picker_scroll,
            duration=child_duration,
            delay=child_delay,
            attrs={
                'size': ((0, picker_size[1]), picker_size),
                'border_opacity': (0, Color.OPACITY),
                'color': (Color.COLD, Color.BASE)
            }
        ))

        row_h = 35
        picker_root = bui.containerwidget(
            parent=picker_scroll,
            background=False,
            size=(picker_x, row_h*len(options))
        )
        picker_kids.append(picker_root)

        def close_sub(instant=False):
            s.window_sub_on = None
            for anim in kid_anims:
                anim.cancel()
            kid_anims.clear()
            for w in picker_kids:
                if w.exists():
                    w.delete()
            picker_kids.clear()
            dur = instant and 0.0001 or butter
            grow_anim.reverse(duration=dur)
            shadow_anim.reverse(duration=dur)
            bui.buttonwidget(btn, on_activate_call=reopen, selectable=True)
            if not instant:
                Eval.SOUND(Const.OK_SOUND).play()

        def pick(v):
            Eval.SOUND(Const.OK_SOUND).play()
            on_pick(v)
            close_sub()

        def reopen():
            s.open_side_picker(
                btn, btn_screen_pos, btn_size, shadow,
                options, get_current, on_pick, label, option_color, option_textcolor
            )

        current = get_current()
        row_off = 15
        for i, opt in enumerate(options):
            y_pos = row_h*(len(options)-1-i)
            txt = label(opt) if callable(label) else str(opt)
            if option_color:
                cr, cg, cb = option_color(opt)
                luma = (cr+cg+cb)/3
                nudge = 1.6 if luma < 1.0 else 0.75
                swatch = (cr*nudge, cg*nudge, cb*nudge) if opt == current else (cr, cg, cb)
            else:
                swatch = Color.BASE if opt != current else Color.COLD
            row_text = option_textcolor(opt) if option_textcolor else Color.TEXT
            b = bui.buttonwidget(
                parent=picker_root,
                position=(row_off, y_pos),
                size=(picker_x, row_h),
                label=txt,
                color=swatch,
                textcolor=Const.INVISIBLE,
                opacity=0,
                texture=Eval.TEXTURE(Const.SKIN),
                enable_sound=False,
                on_activate_call=bui.CallPartial(pick, opt)
            )
            picker_kids.append(b)
            stagger = 0.02*i
            kid_anims.append(Animate(
                widget=b,
                duration=child_duration,
                delay=child_delay+stagger,
                attrs={
                    'position': ((row_off, y_pos), (0, y_pos)),
                    'opacity': (0, Color.OPACITY),
                    'textcolor': (
                        Const.INVISIBLE,
                        (*row_text, Color.OPACITY)
                    )
                }
            ))

        s.window_sub_on = (btn, reopen, close_sub)

    def make_window_kids_settings(s):
        s.making_window_kids = True
        s.make_window_default(title=Strings.SETTINGS, reverse_off=True)
        s.settings_opacity_dirty = False

        sx, sy = s.window_size
        delay = 0.35
        row_h = Const.SETTINGS_ROW_H
        step = row_h+Const.SETTINGS_ROW_GAP
        ctrl_w = Const.SETTINGS_CYCLE_W
        num_w = Const.SETTINGS_NUMERIC_W

        tb_size = (35, 35)
        tb_w, tb_h = tb_size
        tb_gap = 8
        tb_inset = s.window_marg-s.window_fix
        top_y = sy-tb_h-s.window_marg
        lang_x = sx-tb_w-tb_inset
        theme_x = lang_x-tb_gap-tb_w

        size = dx, dy = (sx-s.window_marg*2-s.window_fix+10, sy-s.window_marg*9)
        pos = px, py = (s.window_marg-s.window_fix, s.window_marg-s.window_fix)
        scroll = bui.scrollwidget(
            parent=s.root,
            position=pos,
            color=Color.BASE,
            size=(0, 0),
            border_opacity=0
        )
        s.window_kids.append((scroll, pos, 20, delay,
                              ('size', ((dx*2/3, dy*2/3), size)),
                              ('border_opacity', (0, Color.OPACITY)),
                              ('color', (Color.COLD, Color.BASE))
                              ))
        root = bui.containerwidget(parent=scroll, background=False)

        trash = []
        label_w = dx-ctrl_w-40

        def add_label(y, text):
            trash.append(bui.textwidget(
                parent=root,
                position=(10, y),
                size=(label_w, row_h),
                text=text,
                h_align='left',
                v_align='center',
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                maxwidth=label_w
            ))

        def add_checkbox(y, text, key, on_change=None):
            add_label(y, text)

            def do(v):
                Settings.set(key, v)
                callable(on_change) and on_change(v)
            trash.append(bui.checkboxwidget(
                parent=root,
                position=(dx-54, y+row_h/2-15),
                size=(30, 30),
                text='',
                value=Settings.get(key),
                color=Color.BASE,
                textcolor=Const.INVISIBLE,
                on_value_change_call=do
            ))

        live_fields = []

        def add_numeric(y, text, key, fmt='{:.2f}', minv=None, maxv=None, on_change=None):
            add_label(y, text)
            field = bui.textwidget(
                parent=root,
                position=(dx-num_w-10, y+2),
                size=(num_w, row_h-4),
                text=fmt.format(Settings.get(key)),
                editable=True,
                allow_clear_button=False,
                h_align='center',
                v_align='center',
                color=(*Color.TEXT, Color.TEXT_OPACITY)
            )
            trash.append(field)
            live_fields.append({
                'kind': 'numeric', 'field': field, 'key': key, 'fmt': fmt,
                'minv': minv, 'maxv': maxv, 'on_change': on_change,
                'last': fmt.format(Settings.get(key))
            })

        def add_text(y, text, key, width, on_change=None):
            add_label(y, text)
            eat = 40
            field = bui.textwidget(
                parent=root,
                position=(dx-(width-eat)-10, y+2),
                size=(width-eat, row_h-4),
                text=str(Settings.get(key)),
                editable=True,
                allow_clear_button=False,
                h_align='center',
                v_align='center',
                color=(*Color.TEXT, Color.TEXT_OPACITY)
            )
            trash.append(field)
            live_fields.append({
                'kind': 'text', 'field': field, 'key': key,
                'on_change': on_change, 'last': str(Settings.get(key)),
                'fallback': Settings.DEFAULTS.get(key, '')
            })

        def poll_live_fields():
            if not root.exists():
                s.settings_live_timer = None
                return
            for lf in live_fields:
                field = lf['field']
                if not field.exists():
                    continue
                raw = bui.textwidget(query=field)
                if raw == lf['last']:
                    continue

                if lf['kind'] == 'text':
                    value = raw.strip() or lf['fallback']
                    if value != Settings.get(lf['key']):
                        Settings.set(lf['key'], value)
                        callable(lf['on_change']) and lf['on_change'](value)
                    lf['last'] = raw
                    continue

                try:
                    v = float(raw)
                except Exception:
                    lf['last'] = raw
                    continue
                clamped = v
                if lf['minv'] is not None:
                    clamped = max(lf['minv'], clamped)
                if lf['maxv'] is not None:
                    clamped = min(lf['maxv'], clamped)
                if clamped != Settings.get(lf['key']):
                    Settings.set(lf['key'], clamped)
                    callable(lf['on_change']) and lf['on_change'](clamped)
                shown = lf['fmt'].format(clamped)
                if shown != raw:
                    bui.textwidget(field, text=shown)
                lf['last'] = shown
        s.settings_live_timer = bui.AppTimer(0.1, poll_live_fields, repeat=True)

        def add_cycle(y, text, key, options, on_change=None):
            add_label(y, text)

            def do():
                cur = Settings.get(key)
                i = options.index(cur) if cur in options else 0
                nxt = options[(i+1) % len(options)]
                Settings.set(key, nxt)
                bui.buttonwidget(btn, label=str(nxt))
                Eval.SOUND(Const.OK_SOUND).play()
                callable(on_change) and on_change(nxt)
            btn = bui.buttonwidget(
                parent=root,
                position=(dx-ctrl_w-10, y+2),
                size=(ctrl_w, row_h-4),
                label=str(Settings.get(key)),
                texture=Eval.TEXTURE(Const.SKIN),
                color=Color.BASE,
                textcolor=(*Color.TEXT, Color.TEXT_OPACITY),
                enable_sound=False,
                on_activate_call=do
            )
            trash.append(btn)

        def add_top_picker(x, char_label, key, options, label=None, on_change=None, option_color=None, option_textcolor=None):
            pos = (x, top_y)
            btn = bui.buttonwidget(
                parent=s.root,
                position=pos,
                size=tb_size,
                label=char_label,
                enable_sound=False,
                texture=Eval.TEXTURE(Const.SKIN),
                color=Color.BASE,
                textcolor=Const.INVISIBLE,
                opacity=0,
                selectable=True
            )
            s.window_kids.append((btn, pos, -50, delay))
            shadow = bui.imagewidget(
                parent=s.root,
                opacity=0,
                texture=Eval.TEXTURE(Const.SHADOW),
                color=Color.SHADOW
            )
            trash.append(shadow)

            def do_pick(v):
                Settings.set(key, v)
                callable(on_change) and on_change(v)

            def open_picker():
                wx, wy = s.window_pos
                btn_screen_pos = (wx+pos[0], wy+pos[1])
                s.open_side_picker(
                    btn, btn_screen_pos, tb_size, shadow,
                    options, lambda: Settings.get(
                        key), do_pick, label, option_color, option_textcolor
                )
            bui.buttonwidget(btn, on_activate_call=open_picker, selectable=True)

        def add_button(y, text, on_press):
            def do():
                Eval.SOUND(Const.OK_SOUND).play()
                on_press()
            trash.append(bui.buttonwidget(
                parent=root,
                position=(10, y+2),
                size=(dx-20, row_h-4),
                label=text,
                texture=Eval.TEXTURE(Const.SKIN),
                color=Color.BASE,
                textcolor=(*Color.TEXT, Color.TEXT_OPACITY),
                enable_sound=False,
                on_activate_call=do
            ))

        def add_header(y, text):
            trash.append(bui.textwidget(
                parent=root,
                position=(0, y),
                size=(dx, row_h),
                text=text,
                h_align='center',
                v_align='center',
                scale=0.85,
                color=(*Color.TEMP, Color.OPACITY)
            ))

        add_top_picker(theme_x, Eval.CHAR(Const.THEME_ICON), 'theme', tuple(Settings.THEMES),
                       on_change=lambda v: s.refresh_theme(),
                       option_color=lambda v: Settings.THEMES[v]['base'],
                       option_textcolor=lambda v: Settings.THEMES[v]['text'])
        add_top_picker(lang_x, 'A\u3042', 'language', tuple(Strings.LANGUAGES),
                       label=lambda v: Strings.LANGUAGE_NAMES.get(v, v),
                       on_change=lambda v: s.refresh_language())

        general_rows = 16
        debug_rows = 6
        total_slots = general_rows+1+debug_rows  # +1 for the "Debug" header
        rsy = max(total_slots*step+20, dy-15)
        y = rsy-row_h

        add_numeric(y, Strings.SETTING_ENTRY_DURATION, 'entry_duration',
                    minv=0.05, maxv=60,
                    on_change=lambda v: setattr(s, 'object_duration', v))
        y -= step
        add_numeric(y, Strings.SETTING_ANIM_SPEED, 'anim_speed',
                    minv=0.1, maxv=5)
        y -= step
        add_numeric(y, Strings.SETTING_BASE_OPACITY, 'base_opacity',
                    minv=0.05, maxv=1,
                    on_change=lambda v: (
                        Settings.apply_all(),
                        setattr(s, 'settings_opacity_dirty', True)
                    ))
        y -= step
        add_numeric(y, Strings.SETTING_TEXT_OPACITY, 'text_opacity',
                    minv=0.05, maxv=1,
                    on_change=lambda v: (
                        Settings.apply_all(),
                        setattr(s, 'settings_opacity_dirty', True)
                    ))
        y -= step
        add_checkbox(y, Strings.SETTING_AUTOSAVE_ON, 'autosave_on')
        y -= step
        add_numeric(y, Strings.SETTING_AUTOSAVE_INTERVAL, 'autosave_interval',
                    fmt='{:.0f}', minv=Const.AUTOSAVE_MIN_INTERVAL, maxv=600,
                    on_change=lambda v: s.restart_autosave_timer())
        y -= step
        add_checkbox(y, Strings.SETTING_UI_ANIM_ON, 'ui_anim_on')
        y -= step
        add_checkbox(y, Strings.SETTING_SFX_EDITOR, 'sfx_editor_on')
        y -= step
        add_checkbox(y, Strings.SETTING_SFX_UI, 'sfx_ui_on')
        y -= step
        add_checkbox(y, Strings.SETTING_IGNORE_PLAYBACK_ERRORS, 'ignore_playback_errors')
        y -= step
        add_checkbox(y, Strings.SETTING_BRP_TEXT_EXPORT, 'brp_text_export')
        y -= step
        add_text(y, Strings.SETTING_EXPORT_FILENAME, 'export_filename_template',
                 dx-100)
        y -= step
        add_checkbox(y, Strings.SETTING_TOAST_TOP, 'toast_top',
                     on_change=lambda v: (s.wrap([1]), s.reset_toast_position()))
        y -= step
        add_checkbox(y, Strings.SETTING_FANCY_AUTOSAVE, 'fancy_autosave')
        y -= step
        add_numeric(y, Strings.SETTING_TOAST_DURATION, 'toast_duration',
                    fmt='{:.1f}', minv=0.5, maxv=15)
        y -= step
        add_checkbox(y, Strings.SETTING_EPIC_MODE, 'epic_mode',
                     on_change=lambda v: s.toast(
                         Strings.INFO_EPIC_ON if v else Strings.INFO_EPIC_OFF
                     ))
        y -= step

        add_header(y, Strings.SETTING_DEBUG_HEADER)
        y -= step

        add_checkbox(y, Strings.SETTING_SHOW_GRID_2D, 'show_grid_2d',
                     on_change=lambda v: s.build_grid())
        y -= step
        add_checkbox(y, Strings.SETTING_SHOW_GRID_3D, 'show_grid_3d',
                     on_change=lambda v: s.build_grid())
        y -= step
        add_button(y, Strings.SETTING_DUMP_MEMORY, lambda: (
            print('=== MOVI DEBUG: s.memory ==='),
            print(s.memory),
            s.toast(Strings.INFO_DUMPED_MEMORY)
        ))
        y -= step
        add_button(y, Strings.SETTING_DUMP_TIMELINE, lambda: (
            print('=== MOVI DEBUG: s.timeline ==='),
            print(s.timeline),
            s.toast(Strings.INFO_DUMPED_TIMELINE)
        ))
        y -= step
        add_cycle(y, Strings.SETTING_ASPECT_RATIO, 'aspect_ratio', Settings.ASPECT_RATIOS,
                  on_change=lambda v: s.wrap_aspect_bars())
        y -= step
        add_checkbox(y, Strings.SETTING_FILL_ASPECT_RATIO, 'fill_aspect_ratio',
                     on_change=lambda v: s.wrap_aspect_bars())
        y -= step

        bui.containerwidget(root, size=(dx, rsy))
        s.window_trash = [trash]

        s.wrap_window_kids()
        s.animate_window_kids()
        s.making_window_kids = False

    ABOUT_FONT_5X7 = {
        'M': ('10001', '11011', '10101', '10001', '10001', '10001', '10001'),
        'O': ('01110', '10001', '10001', '10001', '10001', '10001', '01110'),
        'V': ('10001', '10001', '10001', '10001', '10001', '01010', '00100'),
        'I': ('11111', '00100', '00100', '00100', '00100', '00100', '11111'),
    }

    def make_window_kids_about(s):
        """About window - same grow-from-button/back-button/scroll
        shell as make_window_kids_settings (make_window_default is
        shared with it), just a static bit of content instead of a
        settings list: a big "MOVI" logo built out of small square
        imagewidgets (a dot-matrix glyph per letter, see
        ABOUT_FONT_5X7) that does one hue sweep - each letter phase-
        shifted from its neighbour so the sweep reads as a single
        band of color walking left-to-right across the whole word -
        before settling on the theme's own text color, followed by
        the version, copyright, and a thank-you line."""
        s.making_window_kids = True
        s.make_window_default(title=Strings.ABOUT_TITLE, reverse_off=True)

        sx, sy = s.window_size
        x, y = s.window_pos
        delay = 0.35
        trash = []

        title_text = 'MOVI'
        cell = 11
        gap_px = 1
        letter_gap = 16
        cols, rows = 5, 7
        letter_w = cols*cell
        logo_w = len(title_text)*letter_w+(len(title_text)-1)*letter_gap
        start_x = sx/2-logo_w/2

        bottom_margin = 28
        text_h = 24
        thanks_y = bottom_margin+text_h/2
        tagline_y = thanks_y+26
        version_y = tagline_y+32
        logo_bottom_y = version_y+50
        logo_top_y = logo_bottom_y+rows*cell

        letter_pixel_groups = []
        pixel_widgets = []
        for li, ch in enumerate(title_text):
            pattern = s.ABOUT_FONT_5X7[ch]
            letter_x = start_x+li*(letter_w+letter_gap)
            pixels = []
            for r, row in enumerate(pattern):
                for c, bit in enumerate(row):
                    if bit != '1':
                        continue
                    px = x+letter_x+c*cell
                    py = y+logo_top_y-(r+1)*cell
                    w = bui.imagewidget(
                        parent=s.root,
                        texture=Eval.TEXTURE(Const.SKIN),
                        position=(px, py),
                        size=(cell-gap_px, cell-gap_px),
                        color=Color.BASE,
                        opacity=0
                    )
                    trash.append(w)
                    pixels.append(w)
                    pixel_widgets.append(w)
            letter_pixel_groups.append(pixels)

        hue_span = 0.85
        fine_steps = 48
        step_dur = 0.035

        def hue_color(h):
            r, g, b = hsv_to_rgb(h % 1.0, 1.0, 1.0)
            return (r*2.3, g*2.3, b*2.3)

        def make_stops(hue_start):
            return tuple(
                hue_color(hue_start+hue_span*(i/(fine_steps-1)))
                for i in range(fine_steps)
            )

        def settle_color(w):
            s.anims[id(w)].pop('about_sweep', None)
            if not w.exists():
                return
            bui.imagewidget(w, color=Color.TEXT, opacity=Color.TEXT_OPACITY)

        def sweep_pixel(w, prev_color, stops, step_dur):
            if not w.exists():
                s.anims[id(w)].pop('about_sweep', None)
                return
            if not stops:
                settle_color(w)
                return
            nxt, *rest = stops
            anim = Animate(
                widget=w,
                duration=step_dur,
                attrs={'color': (prev_color, nxt)},
                on_finish=lambda: sweep_pixel(w, nxt, rest, step_dur)
            )
            s.anims[id(w)]['about_sweep'] = anim

        letter_hue_offset = 0.05
        letter_stagger = 0.05
        for li, pixels in enumerate(letter_pixel_groups):
            stops = make_stops(li*letter_hue_offset)
            first, *rest = stops
            letter_delay = delay+li*letter_stagger
            for w in pixels:
                anim = Animate(
                    widget=w,
                    duration=step_dur,
                    delay=letter_delay,
                    attrs={
                        'opacity': (0, Color.TEXT_OPACITY),
                        'color': (Color.BASE, first)
                    },
                    on_finish=lambda w=w, rest=rest, first=first: sweep_pixel(
                        w, first, rest, step_dur)
                )
                s.anims[id(w)]['about_sweep'] = anim

        s.about_letter_kids = pixel_widgets

        version = bui.textwidget(
            parent=s.root,
            text=Strings.ABOUT_VERSION.format(__version__),
            position=(0, version_y),
            size=(sx, 24),
            h_align=Const.ALIGN,
            v_align=Const.ALIGN,
            scale=0.75,
            color=Const.INVISIBLE
        )
        trash.append(version)
        s.window_kids.append((version, (0, version_y), 50, delay+0.15))

        tagline_w = bui.textwidget(
            parent=s.root,
            text=Strings.ABOUT_TAGLINE,
            position=(0, tagline_y),
            size=(sx, 24),
            h_align=Const.ALIGN,
            v_align=Const.ALIGN,
            scale=0.68,
            color=Const.INVISIBLE
        )
        trash.append(tagline_w)
        s.window_kids.append((tagline_w, (0, tagline_y), 50, delay+0.2))

        thanks_w = bui.textwidget(
            parent=s.root,
            text=Strings.ABOUT_THANKS,
            position=(0, thanks_y),
            size=(sx, 24),
            h_align=Const.ALIGN,
            v_align=Const.ALIGN,
            scale=0.68,
            color=Const.INVISIBLE
        )
        trash.append(thanks_w)
        s.window_kids.append((thanks_w, (0, thanks_y), 50, delay+0.25))

        s.window_trash = [trash]

        s.wrap_window_kids()
        s.animate_window_kids()
        s.making_window_kids = False

    def kill(s, on_kill=None):
        def finish():
            callable(on_kill) and on_kill()
            s.hard_cleanup()
        s.animate_out(
            on_finish=finish
        )
        s.ui_on = False
        s.ui_clickable = False
        bs.get_foreground_host_activity().globalsnode.area_of_interest_bounds = Const.EXIT_BOUNDS

    def hard_cleanup(s):
        for attr in s.__dict__.copy():
            isinstance(attr, list) and attr.clear()
            delattr(s, attr)

    def make_menu(s):
        s.menu_bg = bui.imagewidget(
            parent=s.root,
            opacity=0,
            color=Color.BASE,
            texture=Eval.TEXTURE(Const.SKIN)
        )
        s.menu_kids = []
        for t in Strings.MENUS:
            w = bui.buttonwidget(
                parent=s.root,
                enable_sound=False,
                label=t,
                size=(0, 0),
                opacity=0,
                textcolor=Const.INVISIBLE,
                color=Color.BASE,
                texture=Eval.TEXTURE(Const.SKIN)
            )
            s.menu_kids.append(w)
        s.seed_input = bui.textwidget(
            parent=s.root,
            position=(0, 0),
            size=(0, 0),
            editable=True,
            allow_clear_button=False,
            color=(*Color.TEXT, Color.TEXT_OPACITY),
            v_align=Const.ALIGN,
            glow_type=Const.GLOW,
            description=Strings.SEED
        )

    def complete_all(s):
        for widget_id, anim_dict in s.anims.items():
            if isinstance(anim_dict, dict):
                for anim in list(anim_dict.values()):
                    anim.complete()
            else:
                anim_dict.complete()

    def wrap_all(s, autofix=True, init=False):
        s.complete_all()
        s.wrap(init=init)
        s.wrap_menu()
        s.wrap_window_kids()
        s.wrap_aspect_bars()
        autofix and bui.apptimer(
            Const.BA_LAG, bui.CallPartial(
                s.wrap_all, autofix=False
            ))

    def wrap_aspect_bars(s):
        """Letterbox/pillarbox preview: draws flat black bars over
        whatever's outside the chosen aspect ratio, so you can see
        what a recording would crop before it's too late.

        These are scene 'image' nodes attached to screen corners
        (bascenev1), not UI widgets - they belong on the scene screen
        itself so they sit under/over the world the same way a real
        letterbox would, independent of whichever editor window
        happens to be open.

        If 'fill_aspect_ratio' is on, four more bars are added behind
        these same four, each massively overscanned past the safe
        window's own edge (see Const.FILL_ASPECT_OVERSCAN) - like
        painting the wall around a window frame, not just the window
        itself, so whatever real device margin exists outside
        get_virtual_screen_size()'s safe box reads as part of the
        letterbox too instead of showing raw unpainted screen."""
        name = Settings.get('aspect_ratio')
        ratio = Const.ASPECT_RATIO_VALUES.get(name)
        if not ratio:
            s.destroy_aspect_bars()
            return
        rx, ry = bui.get_virtual_screen_size()
        target_w, target_h = rx, rx/ratio
        if target_h > ry:
            target_h, target_w = ry, ry*ratio
        bar_h = max((ry-target_h)/2, 0)
        bar_w = max((rx-target_w)/2, 0)
        fill = Settings.get('fill_aspect_ratio')
        over = Const.FILL_ASPECT_OVERSCAN
        try:
            activity = bs.get_foreground_host_activity()
        except Exception:
            return
        try:
            with activity.context:
                if not s.aspect_bars:
                    s.aspect_bars = [
                        bs.newnode('image', attrs={
                            'texture': bs.gettexture(Const.SKIN),
                            'color': (0, 0, 0),
                            'opacity': 1,
                            'attach': 'bottomLeft'
                        }) for _ in range(4)
                    ]
                if fill and not s.aspect_fill_bars:
                    s.aspect_fill_bars = [
                        bs.newnode('image', attrs={
                            'texture': bs.gettexture(Const.SKIN),
                            'color': (0, 0, 0),
                            'opacity': 1,
                            'attach': 'bottomLeft'
                        }) for _ in range(4)
                    ]
                elif not fill and s.aspect_fill_bars:
                    for n in s.aspect_fill_bars:
                        if n.exists():
                            n.delete()
                    s.aspect_fill_bars = []

                top, bottom, left, right = s.aspect_bars
                for n, pos, scale in (
                    (top,   (rx/2, ry-bar_h/2), (rx, bar_h)),
                    (bottom, (rx/2, bar_h/2),    (rx, bar_h)),
                    (left,  (bar_w/2, ry/2),    (bar_w, ry)),
                    (right, (rx-bar_w/2, ry/2), (bar_w, ry)),
                ):
                    n.position = pos
                    n.scale = scale

                if fill and s.aspect_fill_bars:
                    ftop, fbottom, fleft, fright = s.aspect_fill_bars
                    over_h = ry*over
                    over_w = rx*over
                    for n, pos, scale in (
                        (ftop,   (rx/2, ry-bar_h+over_h/2), (rx+over_w*2, over_h)),
                        (fbottom, (rx/2, bar_h-over_h/2),    (rx+over_w*2, over_h)),
                        (fleft,  (bar_w-over_w/2, ry/2),    (over_w, ry+over_h*2)),
                        (fright, (rx-bar_w+over_w/2, ry/2), (over_w, ry+over_h*2)),
                    ):
                        n.position = pos
                        n.scale = scale
        except Exception:
            print(format_exc())
            s.destroy_aspect_bars()

    def destroy_aspect_bars(s):
        for n in getattr(s, 'aspect_bars', None) or []:
            if n.exists():
                n.delete()
        s.aspect_bars = None
        for n in getattr(s, 'aspect_fill_bars', None) or []:
            if n.exists():
                n.delete()
        s.aspect_fill_bars = []

    def wrap_menu(s):
        rx, ry = bui.get_virtual_screen_size()
        sx, sy = s.menu_size = Eval.SCALE_REAL(240, 370)
        s.menu_start_size = (sx*0.8, sy*0.8)
        s.menu_yoff, = Eval.SCALE_REAL(62)
        s.menu_marg, = Eval.SCALE_REAL(10)
        x, y = s.menu_pos = rx-sx+2, ry-sy-s.menu_yoff
        s.menu_start_pos = (
            rx-s.menu_start_size[0],
            ry-s.menu_yoff-s.menu_start_size[1]
        )
        bx = sx-s.menu_marg*4
        by, = Eval.SCALE_REAL(40)
        one, = Eval.SCALE_REAL(1)
        s.menu_kid_size = bx, by
        s.menu_kid_start_size = (bx/2, by)
        s.menu_button_xp = x+s.menu_marg*2
        s.menu_kid_yp = lambda i: (
            y+s.menu_marg*1.5+(by+s.menu_marg)*i
        )
        s.menu_kid_start_pos = lambda i: (
            s.menu_button_xp+bx/2,
            s.menu_kid_yp(i)
        )
        s.menu_kid_pos = lambda i: (
            s.menu_button_xp,
            s.menu_kid_yp(i)
        )
        s.seed_button_shrunk_size = (s.menu_kid_size[0]*0.3, s.menu_kid_size[1])
        s.seed_input_size = (s.menu_kid_size[0]*0.7-s.menu_marg, s.menu_kid_size[1])
        s.seed_input_pos = lambda i: (
            s.menu_button_xp,
            s.menu_kid_yp(i)
        )
        bui.imagewidget(
            s.menu_bg,
            position=s.menu_pos,
            size=s.menu_size
        )
        if s.menu_on:
            a = s.anims[id(s.menu_bg)].attrs_start
            a['size'] = s.menu_start_size
            a['position'] = s.menu_start_pos
            a = s.anims[id(s.menu_bg)].attrs_end
            a['size'] = s.menu_size
            a['position'] = s.menu_pos
            a = s.anims[id(s.menu_bg)].attrs_current
            a['size'] = s.menu_size
            a['position'] = s.menu_pos
        for i, kid in enumerate(s.menu_kids):
            if i == 2 and s.seed_on:
                kid_size = s.seed_button_shrunk_size
                kid_pos = (
                    s.menu_button_xp + (s.menu_kid_size[0] - s.seed_button_shrunk_size[0]) + 5,
                    s.menu_kid_yp(i)
                )
            else:
                kid_size = (bx, by)
                kid_pos = (
                    s.menu_button_xp,
                    s.menu_kid_yp(i)
                )

            bui.buttonwidget(
                kid,
                size=kid_size,
                position=kid_pos,
                text_scale=one
            )

            if s.menu_on:
                a = s.anims[id(kid)]['main'].attrs_start
                a['size'] = s.menu_kid_start_size
                a['position'] = s.menu_kid_start_pos(i)
                a = s.anims[id(kid)]['main'].attrs_current
                a['size'] = kid_size
                a['position'] = kid_pos
                a = s.anims[id(kid)]['main'].attrs_end
                a['size'] = kid_size
                a['position'] = kid_pos
        bui.textwidget(
            s.seed_input,
            position=s.seed_input_pos(2),
            size=s.seed_on and s.seed_input_size or (0, 0)
        )

        if s.menu_on and (anim := s.anims.get(id(s.seed_input))):
            if s.seed_on:
                try:
                    anim.attrs_end['position'] = s.seed_input_pos(2)
                    anim.attrs_current['position'] = s.seed_input_pos(2)
                except NameError:
                    return

    def toggle_menu(s, on_finish=None, shut=False):
        shut or Eval.SOUND(Const.OK_SOUND).play()
        delay = 0.1
        butter = s.global_butter*0.7
        if s.menu_on:
            s.menu_on = False
            anim = s.anims[id(s.menu_bg)]
            s.anims[id(s.menu_bg)] = anim.reverse(
                duration=butter
            )
            (victim := s.anims[id(s.menu_kids[2])].pop('seed', None)) and victim.cancel()
            (victim := s.anims[id(s.seed_input)]) and s.seed_on and victim.cancel()
            bui.textwidget(s.seed_input, size=(0, 0))
            s.seed_on = False
            bui.buttonwidget(
                s.menu_kids[2],
                label=Strings.MENUS[2]
            )
            for i, kid in enumerate(s.menu_kids):
                anim = s.anims[id(kid)]['main']
                s.anims[id(kid)]['main'] = anim.reverse(
                    duration=butter*0.7
                )
                bui.buttonwidget(
                    kid, on_activate_call=Const.DO_NOTHING
                )
            return
        s.menu_on = True
        if (anim := s.anims[id(s.menu_bg)]):
            anim.cancel()
        s.anims[id(s.menu_bg)] = Animate(
            widget=s.menu_bg,
            duration=butter,
            attrs={
                'opacity': (0, Color.OPACITY),
                'position': (
                    s.menu_start_pos,
                    s.menu_pos
                ),
                'size': (
                    s.menu_start_size,
                    s.menu_size
                )
            }
        )

        def menu_action(i):
            if i == 0:
                Eval.SOUND(Const.OK_SOUND).play()
                s.toast(Strings.BYE)
                s.farewell()
            if i == 1:
                if s.can_do != 'nuke':
                    s.toast(Strings.INFO_CONFIRM_CLEAR, extra=2)
                    Eval.SOUND(Const.OK_SOUND).play()
                    s.can_do = 'nuke'
                    return
                if s.playing:
                    s.stop()
                s.clear_memory()
                type(s)._shared['on_create'].append((
                    lambda z: (
                        z.toast(Strings.INFO_MEMORY_CLEARED) or
                        Eval.SOUND(Const.ACTION_SOUND).play()
                    ), ()
                ))
                s.recreate()
            if i == 2:
                s.seed_on = not s.seed_on
                target_label = Strings.DONE if s.seed_on else Strings.MENUS[2]

                target_size = s.seed_button_shrunk_size
                target_pos = (
                    s.menu_button_xp + (s.menu_kid_size[0] - s.seed_button_shrunk_size[0]) + 5,
                    s.menu_kid_yp(2)
                )

                if s.seed_on:
                    anim = s.anims[id(s.menu_kids[1])].get('main')
                    start_size = s.menu_kid_size
                    start_pos = (s.menu_button_xp, s.menu_kid_yp(2))
                    if anim and not anim.finished:
                        start_size = anim.attrs_current['size']
                        start_pos = anim.attrs_current['position']
                        anim.cancel()

                    def change_label():
                        bui.buttonwidget(s.menu_kids[2], label=target_label)
                        Animate(
                            widget=s.menu_kids[2],
                            attrs={
                                'textcolor': (
                                    Const.INVISIBLE,
                                    (*Color.TEXT, Color.TEXT_OPACITY)
                                )
                            },
                            duration=s.global_butter / 2
                        )

                    s.anims[id(s.menu_kids[2])]['seed'] = Animate(
                        widget=s.menu_kids[2],
                        attrs={
                            'size': (start_size, target_size),
                            'position': (start_pos, target_pos),
                            'textcolor': (
                                (*Color.TEXT, Color.TEXT_OPACITY),
                                Const.INVISIBLE
                            )
                        },
                        duration=s.global_butter / 2,
                        on_finish=change_label
                    )
                else:
                    bui.buttonwidget(s.menu_kids[2], label=target_label)

                if s.seed_on:
                    anim_input = s.anims.get(id(s.seed_input))
                    start_input_size = (0, s.menu_kid_size[1])
                    if anim_input and not anim_input.finished:
                        start_input_size = anim_input.attrs_current['size']
                        anim_input.cancel()

                    s.anims[id(s.seed_input)] = Animate(
                        widget=s.seed_input,
                        attrs={
                            'size': (start_input_size, s.seed_input_size),
                            'color': (Const.INVISIBLE, (*Color.TEXT, Color.TEXT_OPACITY))
                        },
                        duration=s.global_butter
                    )
                else:
                    bui.textwidget(s.seed_input, size=(
                        0, s.menu_kid_size[1]), color=Const.INVISIBLE)

                if not s.seed_on:
                    seed_text = bui.textwidget(query=s.seed_input)
                    s.toggle_menu(shut=True)
                    if not seed_text:
                        s.toast(Format.ERROR_EMPTY(Strings.SEED))
                        Eval.SOUND(Const.BAD_SOUND).play()
                        return
                    bui.textwidget(s.seed_input, text='')
                    try:
                        memory = Eval.DECODE(seed_text)
                    except Exception as e:
                        s.toast(Format.ERROR(e))
                        Eval.SOUND(Const.BAD_SOUND).play()
                        return
                    s.clear_memory()
                    type(s)._shared['on_create'].append((
                        lambda z, mem: z.load_memory(mem),
                        (memory,)
                    ))
                    s.recreate()
                Eval.SOUND(Const.OK_SOUND).play()
            if i == 3:
                try:
                    seed = Eval.ENCODE(s.memory)
                except Exception as e:
                    s.toast(Format.ERROR(e))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                bui.clipboard_set_text(str(seed))
                Eval.SOUND(Const.GOOD_SOUND).play()
                s.toast(Strings.INFO_COPIED)
                s.toggle_menu()
            if i == 4:
                s.toggle_ui()
                s.toggle_menu()
                Eval.SOUND(Const.OK_SOUND).play()
            if i == 5:
                if not s.stamp_kids:
                    s.toast(Strings.ERROR_NO_MEMORY)
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                Eval.SOUND(Const.OK_SOUND).play()
                s.save_state()
                type(s)._shared['on_create'].append((
                    lambda z: z.start_recording(),
                    ()
                ))
                s.recreate()
            if i == 6:
                if not s.ui_on:
                    s.toast(Strings.ERROR_ALREADY_WIDE)
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                Eval.SOUND(Const.OK_SOUND).play()
                s.play()
                s.wrap_controls()
                s.is_wide = True
                s.toggle_ui()
                s.toggle_menu()
        for i, kid in enumerate(s.menu_kids):
            if (anim := s.anims[id(kid)].get('main')):
                anim.cancel()
            s.anims[id(kid)]['main'] = Animate(
                widget=kid,
                delay=delay+0.08-0.03*i,
                duration=butter,
                attrs={
                    'size': (
                        s.menu_kid_start_size,
                        s.menu_kid_size
                    ),
                    'opacity': (0, Color.OPACITY),
                    'textcolor': (
                        Const.INVISIBLE,
                        (*Color.TEXT, Color.TEXT_OPACITY)
                    ),
                    'position': (
                        s.menu_kid_start_pos(i),
                        s.menu_kid_pos(i)
                    )
                }
            )
            bui.buttonwidget(
                kid, on_activate_call=bui.CallPartial(
                    menu_action, i
                )
            )

    def farewell(s):
        s.restore_infos()
        s.toggle_menu()

        def on_kill():
            bui.app.classic.return_to_main_menu_session_gracefully(reset_ui=False)
            bui.apptimer(
                Const.BA_LAG+Const.BA_LAG_SMALL*16,
                bui.CallPartial(
                    _ba.set_camera_manual,
                    False
                )
            )
        s.kill(on_kill=on_kill)
        Eval.SOUND(Const.OK_SOUND).play()
        s.save_state()

    @clickable
    def toggle_event(s, passive=False):
        if s.window_on and not passive:
            s.dismiss_window()
            return
        Eval.SOUND(Const.OK_SOUND).play()
        for kid in s.event_kids:
            if (fix_anim := s.anims[id(kid)].get('fix', None)):
                fix_anim.cancel()
                s.anims[id(kid)].pop('fix', None)

        def push():
            w = s.edit_button
            ex, ey = s.edit_button_pos
            start, end = s.edit_button_pos, s.edit_button_pos2
            if (anim := s.anims[id(w)].get('push', None)):
                anim.cancel()
                start_pos = anim.attrs_current['position']
            else:
                start_pos = s.event_on and end or start
            end_pos = s.event_on and start or end
            s.anims[id(w)]['push'] = Animate(
                widget=w,
                attrs={
                    'position': (start_pos, end_pos)
                },
                duration=s.global_butter,
                delay=s.event_on and 0.07 or 0
            )
            w = s.key_button
            ex, ey = s.key_button_pos
            start, end = s.key_button_pos, s.key_button_pos2
            if (anim := s.anims[id(w)].get('push', None)):
                anim.cancel()
                start_pos = anim.attrs_current['position']
            else:
                start_pos = s.event_on and end or start
            end_pos = s.event_on and start or end
            if s.key_window in s.window_on:
                s.anims[id(w)]['window'].attrs_start['position'] = end_pos
                s.anims[id(w)]['shadow'].attrs_start['position'] = end_pos
                if 'push' in s.anims[id(w)]:
                    s.anims[id(w)]['push'].attrs_start['position'] = start_pos
                    s.anims[id(w)]['push'].attrs_end['position'] = end_pos
                    s.anims[id(w)]['push'].attrs_current['position'] = end_pos
                return
            s.anims[id(w)]['push'] = Animate(
                widget=w,
                attrs={
                    'position': (start_pos, end_pos)
                },
                duration=s.global_butter,
                delay=s.event_on and 0.07 or 0
            )
        push()
        dur = s.global_butter*1.5
        old_anim = s.anims.get(id(s.event_root), None)
        if s.event_on:
            s.event_on = False
            bui.buttonwidget(s.event_button, label=Strings.EVENT_BUTTON_OFF)

            s.anims[id(s.event_root)] = old_anim.reverse(
                duration=dur
            )
            for kid, d in s.event_kids.items():
                an = s.anims[id(kid)]
                if (anim := an.pop('window', None)):
                    anim.cancel()
                if (anim := an.pop('extra', None)):
                    anim.cancel()
                old = an.get('main', None)
                if old:
                    old.cancel()
                    s.anims[id(kid)]['main'] = old.reverse(
                        duration=dur/4
                    )
                bui.buttonwidget(
                    kid,
                    on_activate_call=Const.DO_NOTHING,
                    selectable=False
                )
            return

        s.event_on = True
        bui.buttonwidget(s.event_button, label=Strings.EVENT_BUTTON_ON)

        rx, ry = s.real
        sx, sy = s.event_menu_size
        dx, dy = s.event_button_size

        child_start_progress = 0.2
        child_delay = dur * child_start_progress
        child_duration = dur * (1 - child_start_progress)

        mx = sx - 40

        if old_anim:
            old_anim.cancel()
        s.anims[id(s.event_root)] = Animate(
            widget=s.event_root,

            attrs={
                'size': ((dx, dy), (sx, sy))
            },
            duration=dur
        )

        num = len(Strings.EVENTS)
        parent_width_progress = dx + (sx - dx) * child_start_progress
        start_width_ratio = (parent_width_progress - 40) / mx

        times = []
        for i, b in enumerate(s.event_kids):
            stagger = 0.02 * (num-i)
            s.anims[id(b)]['main'] = (
                Animate(
                    widget=b,
                    attrs={
                        'opacity': (0, Color.OPACITY),
                        'textcolor': (
                            Const.INVISIBLE,
                            (*Color.TEXT, Color.TEXT_OPACITY)
                        ),
                        'size': ((mx * start_width_ratio, dy), s.event_kid_size)
                    },
                    duration=child_duration,
                    delay=child_delay + stagger
                )
            )
            times.append(child_delay + stagger)
            bui.buttonwidget(
                b,
                on_activate_call=bui.CallPartial(
                    s.event_window, i
                ),
                position=(
                    s.ev_x,
                    s.event_top-s.ev_mult*(i+1)
                )
            )

    @clickable
    def event_window(s, i, edit={}, load=False, passive=False, **kw):
        if getattr(s, 'making_window_kids', False):
            s.toast(Strings.INFO_SLOW_DOWN)
            Eval.SOUND(Const.BAD_SOUND).play()
            return
        if s.window_on and not passive:
            s.dismiss_window()
        else:
            Eval.SOUND(Const.OK_SOUND).play()
        b = list(s.event_kids)[i]
        call = bui.CallPartial(s.event_window, i)
        s.window_on = [b, call, None]
        bui.buttonwidget(
            b,
            on_activate_call=Const.DO_NOTHING,
            selectable=False
        )
        s.event_kid_pos = (s.ev_x, s.event_top-s.ev_mult*(i+1))
        s.last_window_i = i
        sx, sy = s.window_size
        dx, dy = s.event_kid_size
        butter = 0.5
        s.anims[id(b)]['window'] = (
            Animate(
                widget=b,
                duration=butter,
                attrs={
                    'position': (
                        s.event_kid_pos,
                        s.window_pos
                    ),
                    'size': (
                        s.event_kid_size,
                        s.window_size
                    ),
                    'textcolor': (
                        (*Color.TEXT, Color.TEXT_OPACITY),
                        (*Color.TEXT, 0)
                    )
                }
            )
        )
        s.anims[id(b)]['shadow'] = (
            Animate(
                widget=s.event_kids[b]['shadow'],
                attrs={
                    'opacity': (0, Color.SHADOW_OPACITY),
                    'position': (
                        s.event_kid_pos,
                        s.window_shadow_pos
                    ),
                    'size': (
                        s.event_kid_size,
                        s.window_shadow_size
                    )
                },
                duration=butter
            )
        )
        s.window_on[2] = s.make_window_kids(i, edit=edit, load=load, **kw)

    def make_window_kids(s, i, edit={}, load=False, **kw):
        s.making_window_kids = True
        s.make_window_default(
            title=kw.pop('force_title', None) or (
                edit and not load and Strings.EDIT.format(
                    edit['data']['name']
                ) or list(Strings.EVENTS.values())[i]
            )
        )
        func = (
            i == 0 and s.make_node_window or
            i == 1 and s.make_camera_window or
            i == 2 and s.make_sound_window or
            i == 3 and s.make_fx_window or
            i == 4 and s.make_map_window or
            i == 5 and s.make_preset_window or
            i == 6 and s.make_code_window or
            i == 7 and s.make_seed_window or
            (lambda *a, **k: s.toast(Strings.COMING_SOON))
        )
        wait = 0

        def fin(): return (
            s.wrap_window_kids(),
            s.animate_window_kids(extra_delay=-wait),
            setattr(s, 'making_window_kids', False)
        )
        r = func(edit, load, **kw)
        if isinstance(r, tuple):
            wait, r = r
            bui.apptimer(wait, fin)
        else:
            fin()
        return r

    def animate_window_kids(s, extra_delay=0):
        x, y = s.window_pos
        for _, g in enumerate(s.window_kids):
            w, pos, off, delay, *extra = g
            px, py = pos
            extra = dict(extra)
            attrs = {
                'position': (
                    (x+px-off, y+py),
                    (x+px, y+py)
                ),
                **extra
            }
            ty = w.get_widget_type()
            if ty in ['button', 'checkbox']:
                attrs.update({
                    'textcolor': (
                        Const.INVISIBLE,
                        (*Color.TEXT, Color.TEXT_OPACITY)
                    )
                })
            if ty in ['text']:
                attrs.update({
                    'color': (
                        Const.INVISIBLE,
                        (*Color.TEXT, Color.TEXT_OPACITY)
                    )
                })
            if ty in ['image', 'button']:
                attrs.update({
                    'opacity': (0, Color.OPACITY)
                })
            s.anims[id(w)] = Animate(
                widget=w,
                attrs=attrs,
                duration=0.18,
                delay=delay+extra_delay
            )

    def wrap_window_kids(s):
        x, y = s.window_pos
        for kid in s.window_kids:
            w, p = kid[0:2]
            px, py = p
            Eval.WIDGET(w)(w, position=(x+px, y+py))

    def make_window_default(s, title, reverse_off=False):
        x, y = s.window_pos
        sx, sy = s.window_size

        def bye():
            if s.window_sub_on:
                s.window_sub_on[2]()
                return
            s.window_clean()
            s.window_back()
        s.window_marg = 5
        s.window_fix = 8
        dx, dy = 35, 35
        off = reverse_off and -50 or 50

        pos = (s.window_marg-s.window_fix, sy-dy-s.window_marg)
        back = bui.buttonwidget(
            parent=s.root,
            size=(dx, dy),
            enable_sound=False,
            label=Eval.CHAR(Const.BACK),
            on_activate_call=bye,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            textcolor=Const.INVISIBLE,
            opacity=0
        )
        s.window_back_btn = back
        s.window_kids.append((back, pos, off, 0.35))

        pos = (sx/2-s.window_marg*4, sy-s.window_marg-32.5)
        w = bui.textwidget(
            parent=s.root,
            text=title,
            color=Const.INVISIBLE,
            h_align=Const.ALIGN,
            v_align=Const.ALIGN,
            maxwidth=sx-s.window_marg*3-dx
        )
        s.window_kids.append((w, pos, off, 0.35))

    def add_entry(s, final, smol=False):
        nam = final['name']
        end_size = smol and (
            s.entry_ys_real,
            s.entry_ys_real - s.magic_y
        ) or (
            s.entry_xs_real * (
                s.entries_per_sec *
                s.object_duration
            )*s.magic_right,
            s.entry_ys_real-s.magic_y
        )
        btn = bui.buttonwidget(
            parent=s.stamp_hscroll_root,
            texture=Eval.TEXTURE(Const.SKIN),
            label=nam,
            textcolor=Const.INVISIBLE,
            color=Color.BASE,
            opacity=0,
            enable_sound=False,
            size=end_size,
            button_type='square'
        )
        bui.buttonwidget(
            btn,
            on_activate_call=bui.CallPartial(
                s.select, btn
            )
        )
        s.stamp_kids.append(btn)
        s.memory[id(btn)] = {
            'order': len(s.memory),
            'event': s.last_window_i,
            'data': final,
            'duration': s.object_duration/(smol and s.entries_per_sec or 1),
            'start': 0.0,
            'keys': {},
            'smol': smol
        }
        s.build_timeline()

        def push():
            for i, kid in enumerate(
                reversed(s.stamp_kids)
            ):
                mem = s.memory[id(kid)]
                width_in_steps = mem['duration'] * s.entries_per_sec
                old_x = s.magic_x + s.entry_xs_real * \
                    mem['start']*s.entries_per_sec + (width_in_steps * s.magic_left)
                end_pos = (
                    old_x,
                    s.entry_ys_real*i
                )
                s.anims[kid]['push'] = Animate(
                    widget=kid,

                    attrs={
                        'position': (
                            (old_x, s.entry_ys_real*(i-1)),
                            end_pos
                        )
                    },
                    duration=s.global_butter
                )
            for kid in reversed(s.stamp_kids):
                kid_mem = s.memory[id(kid)]

                for key_data in kid_mem.get('keys', {}).values():
                    if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                        wid = s.widgets[key_data['widget']]
                        wid_id = id(wid)
                        key_time = key_data['time']

                        new_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                        new_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 1)

                        old_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 2)

                        if wid_id not in s.anims:
                            s.anims[wid_id] = {}

                        s.anims[wid_id]['push'] = Animate(
                            widget=wid,
                            attrs={
                                'position': ((new_x, old_y), (new_x, new_y))
                            },
                            duration=s.global_butter
                        )
        push()
        s.wrap([1, 2, 3], on_finish=s.bottom_left)

        def appear():
            bui.buttonwidget(
                btn,
                textcolor=(
                    *Color.TEXT,
                    Color.OPACITY
                ),
                opacity=Color.OPACITY
            )
            if not s.tools_shown:
                s.show_controls()
            s.wrap()
        half_size = hx, hy = tuple(_/2 for _ in s.window_size)
        half_pos = (hx*3, hy*2.5)
        (
            half_shadow_pos,
            half_shadow_size
        ) = Eval.SHADOW(
            *half_pos,
            *half_size,
            d=0.18
        )
        opacity = Color.OPACITY
        half_opacity = opacity/2
        wait = 0.4
        width_in_steps = s.object_duration * s.entries_per_sec

        def where_to(): return (
            (bl := s.bottom_left(dry=True)) and (
                bl[0]+(
                    width_in_steps *
                    s.magic_left
                ), bl[1]
            )
        )
        s.window_back(
            to=lambda: {
                'position': (
                    half_pos,
                    where_to()
                ),
                'size': (
                    half_size,
                    end_size
                ),
                'text_scale': (s.event_kid_ts, 1)
            },
            shadow_to=lambda: {
                'opacity': (half_opacity, 0),
                'position': (
                    half_shadow_pos,
                    where_to()
                ),
                'size': (
                    half_shadow_size,
                    end_size
                )
            },
            on_fix=appear,
            wait=wait,
            instant={
                'label': nam
            },
            extra={
                'textcolor': (
                    Const.INVISIBLE,
                    (*Color.TEXT, Color.TEXT_OPACITY)
                ),
                'size': (
                    s.window_size,
                    half_size
                ),
                'position': (
                    s.window_pos,
                    half_pos
                )
            },
            shadow_extra={
                'size': (
                    s.window_shadow_size,
                    half_shadow_size
                ),
                'position': (
                    s.window_shadow_pos,
                    half_shadow_pos
                ),
                'opacity': (
                    opacity,
                    half_opacity
                )
            }
        )

    NODE_DEFAULT_ATTRS = {
        'prop': {'mesh': 'tnt', 'color_texture': 'tnt', 'body': 'crate', 'gravity_scale': '1.0', 'reflection': 'soft'},
        'text': {'text': 'Hello!', 'color': '(1, 1, 1)', 'scale': '0.02', 'in_world': 'True', 'h_align': 'center'},
        'light': {'color': '(1, 1, 1)', 'radius': '1.0', 'intensity': '1.0'},
        'math': {'input1': '(0, 0, 0)', 'operation': 'add'},
        'spaz': {
            'character': 'Spaz', 'color': '(1, 1, 1)', 'highlight': '(1, 1, 1)',
            'materials': '[_factory.spaz_material, _shared.object_material, _shared.player_material]',
            'roller_materials': '[_factory.roller_material, _shared.player_material]',
            'punch_materials': '[_factory.punch_material, _shared.attack_material]',
            'pickup_materials': '[_factory.pickup_material, _shared.pickup_material]',
        },
        'bomb': {'fuse_length': '3.0'},
        'combine': {'size': '3', 'input0': '0.0', 'input1': '0.0', 'input2': '0.0'},
        'explosion': {'radius': '2.0', 'color': '(1, 1, 1)', 'big': 'False'},
        'flag': {'color_texture': 'flagColor', 'color': '(1, 1, 1)', 'lightWeight': 'False'},
        'flash': {'size': '1.0', 'color': '(1, 1, 1)'},
        'image': {'texture': 'light', 'opacity': '1.0', 'color': '(1, 1, 1)', 'attach': 'center'},
        'locator': {'shape': 'box', 'size': '(1, 1, 1)', 'color': '(1, 1, 1)', 'opacity': '1.0'},
        'region': {'type': 'box', 'scale': '(1, 1, 1)'},
        'scorch': {'size': '1.0', 'presence': '1.0', 'color': '(0, 0, 0)'},
        'shield': {'radius': '1.0', 'color': '(1, 0.25, 0.25)'},
        'sound': {'sound': 'ding', 'volume': '1.0', 'loop': 'False', 'positional': 'True'},
        'terrain': {'mesh': 'thePad', 'color_texture': 'thePadColor', 'collision_mesh': 'thePadCollide', 'color': '(1, 1, 1)'},
        'texture_sequence': {'rate': '30'},
        'time_display': {'timemin': '0', 'timemax': '0', 'time1': '0', 'time2': '0'},
        'anim_curve': {'times': '(0, 1000)', 'values': '(0.0, 1.0)', 'loop': 'False'}
    }

    NODE_TYPES = [
        'prop', 'text', 'light', 'math', 'spaz', 'bomb', 'combine',
        'explosion', 'flag', 'flash', 'image', 'locator', 'region',
        'scorch', 'shield', 'sound', 'terrain', 'texture_sequence',
        'time_display', 'anim_curve'
    ]

    def make_node_window(s, edit=None, load=False):
        x, y = s.window_pos
        sx, sy = s.window_size
        text_push = 15
        delay = 0.35
        data = edit and edit['data']

        s.current_node_type = data.get('type', 'prop') if data else 'prop'

        init_pos = (0, 0, 0)
        s.current_attrs = {}

        def to_friendly(k, v):
            val = str(v).strip()
            for prefix in ['bs.getmesh("', "bs.getmesh('", 'bs.gettexture("', "bs.gettexture('", 'bs.getsound("', "bs.getsound('"]:
                if val.startswith(prefix):
                    return val[len(prefix):-2]
            if val.startswith('"') and val.endswith('"'):
                return val[1:-1]
            if val.startswith("'") and val.endswith("'"):
                return val[1:-1]
            return val

        def to_eval(k, v):
            v = str(v).strip()
            if k in ['mesh', 'collision_mesh', 'light_mesh', 'mesh_opaque', 'mesh_transparent']:
                return f'bs.getmesh("{v}")'
            if k in ['color_texture', 'color_mask_texture', 'texture', 'tint_texture', 'mask_texture']:
                return f'bs.gettexture("{v}")'
            if k == 'sound':
                return f'bs.getsound("{v}")'
            if k in ['name', 'body', 'reflection', 'text', 'h_align', 'v_align', 'chunk_type', 'emit_type', 'operation', 'attach', 'shape', 'type', 'character', 'style', 'counter_text']:
                return f'"{v}"'
            return v

        if data and 'attrs' in data:
            for k, v in data['attrs'].items():
                if k == 'position':
                    try:
                        init_pos = eval(v) if isinstance(v, str) else v
                    except:
                        pass
                else:
                    s.current_attrs[k] = to_friendly(k, v)
        else:
            for k, v in s.NODE_DEFAULT_ATTRS[s.current_node_type].items():
                s.current_attrs[k] = v

        left_x = 10

        pos_lbl = (left_x, sy - 85)
        w = bui.textwidget(parent=s.root, position=pos_lbl, size=(50, 30),
                           text=Strings.TYPE, color=Const.INVISIBLE, maxwidth=50, h_align='left')
        s.window_kids.append((w, pos_lbl, text_push, delay))

        pos_inp = (left_x + 60, sy - 90)
        type_btn = bui.buttonwidget(
            parent=s.root,
            position=pos_inp,
            size=(0, 0),
            label=s.current_node_type.capitalize(),
            color=Color.BASE,
            textcolor=Const.INVISIBLE,
            texture=Eval.TEXTURE(Const.SKIN),
            on_activate_call=lambda: open_type_picker(),
            enable_sound=False
        )
        s.window_kids.append((type_btn, pos_inp, text_push, delay, ('size', ((0, 35), (90, 35)))))

        type_btn_pos = (x + pos_inp[0], y + pos_inp[1])
        type_btn_shadow = bui.imagewidget(
            parent=s.root,
            opacity=0,
            texture=Eval.TEXTURE(Const.SHADOW),
            color=Color.SHADOW
        )
        s.window_trash.append([type_btn_shadow])

        def apply_type(new_type):
            s.current_node_type = new_type
            bui.buttonwidget(edit=type_btn, label=s.current_node_type.capitalize())

            s.current_attrs.clear()
            for k, v in s.NODE_DEFAULT_ATTRS[s.current_node_type].items():
                s.current_attrs[k] = v
            refresh_right_pane(initial=False)

        def open_type_picker():
            if s.window_sub_on:
                s.window_sub_on[2]()
            Eval.SOUND(Const.OK_SOUND).play()
            bui.buttonwidget(
                type_btn,
                on_activate_call=Const.DO_NOTHING,
                selectable=False
            )

            wx, wy = s.window_pos
            wsx, wsy = s.window_size
            picker_x, picker_sx = 120, 130
            picker_pos = (wx + wsx + 100, wy)
            picker_size = (picker_sx, wsy)
            (
                picker_shadow_pos,
                picker_shadow_size
            ) = Eval.SHADOW(*picker_pos, *picker_size)

            btn_start_pos, btn_start_size = type_btn_pos, (90, 35)
            butter = s.global_butter * 1.3

            grow_anim = Animate(
                widget=type_btn,
                duration=butter,
                attrs={
                    'position': (btn_start_pos, picker_pos),
                    'size': (btn_start_size, picker_size),
                    'textcolor': (
                        (*Color.TEXT, Color.TEXT_OPACITY),
                        Const.INVISIBLE
                    )
                }
            )
            shadow_anim = Animate(
                widget=type_btn_shadow,
                attrs={
                    'opacity': (0, Color.SHADOW_OPACITY),
                    'position': (btn_start_pos, picker_shadow_pos),
                    'size': (btn_start_size, picker_shadow_size)
                },
                duration=butter
            )

            child_start_progress = 0.35
            child_delay = butter * child_start_progress
            child_duration = butter * (1 - child_start_progress) + 0.05

            picker_kids = []
            kid_anims = []

            picker_scroll = bui.scrollwidget(
                parent=s.root,
                position=picker_pos,
                size=(0, picker_size[1]),
                color=Color.COLD,
                border_opacity=0
            )
            picker_kids.append(picker_scroll)
            kid_anims.append(Animate(
                widget=picker_scroll,
                duration=child_duration,
                delay=child_delay,
                attrs={
                    'size': ((0, picker_size[1]), picker_size),
                    'border_opacity': (0, Color.OPACITY),
                    'color': (Color.COLD, Color.BASE)
                }
            ))

            row_h = 35
            types = s.NODE_TYPES
            picker_root = bui.containerwidget(
                parent=picker_scroll,
                background=False,
                size=(picker_x, row_h * len(types))
            )
            picker_kids.append(picker_root)

            def close_sub(instant=False):
                s.window_sub_on = None
                for anim in kid_anims:
                    anim.cancel()
                kid_anims.clear()
                for w in picker_kids:
                    if w.exists():
                        w.delete()
                picker_kids.clear()
                dur = instant and 0.0001 or butter
                grow_anim.reverse(duration=dur)
                shadow_anim.reverse(duration=dur)
                bui.buttonwidget(
                    type_btn,
                    on_activate_call=open_type_picker,
                    selectable=True
                )
                if not instant:
                    Eval.SOUND(Const.OK_SOUND).play()

            def pick(t):
                Eval.SOUND(Const.OK_SOUND).play()
                apply_type(t)
                close_sub()

            row_off = 15
            for i, t in enumerate(types):
                y_pos = row_h * (len(types) - 1 - i)
                btn = bui.buttonwidget(
                    parent=picker_root,
                    position=(row_off, y_pos),
                    size=(picker_x, row_h),
                    label=t.capitalize(),
                    color=Color.BASE if t != s.current_node_type else Color.COLD,
                    textcolor=Const.INVISIBLE,
                    opacity=0,
                    texture=Eval.TEXTURE(Const.SKIN),
                    enable_sound=False,
                    on_activate_call=bui.CallPartial(pick, t)
                )
                picker_kids.append(btn)
                stagger = 0.02 * i
                kid_anims.append(Animate(
                    widget=btn,
                    duration=child_duration,
                    delay=child_delay + stagger,
                    attrs={
                        'position': ((row_off, y_pos), (0, y_pos)),
                        'opacity': (0, Color.OPACITY),
                        'textcolor': (
                            Const.INVISIBLE,
                            (*Color.TEXT, Color.TEXT_OPACITY)
                        )
                    }
                ))

            s.window_sub_on = (type_btn, open_type_picker, close_sub)

        pos_lbl = (left_x, sy - 130)
        w = bui.textwidget(parent=s.root, position=pos_lbl, size=(50, 30),
                           text=Strings.NAME, color=Const.INVISIBLE, maxwidth=50, h_align='left')
        s.window_kids.append((w, pos_lbl, text_push, delay + 0.05))

        pos_inp = (left_x + 60, sy - 130)
        incr = f'Node {s.increment}'
        name_text = bui.textwidget(
            parent=s.root,
            position=pos_inp,
            editable=True,
            allow_clear_button=False,
            size=(0, 0),
            maxwidth=80,
            description=Strings.NAME,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            glow_type=Const.GLOW,
            text=data.get('name', incr) if data else incr
        )
        s.window_kids.append((name_text, pos_inp, text_push, delay +
                             0.05, ('size', ((0, 35), (90, 35)))))

        pos_sep = (left_x + 2, sy - 133)
        w = bui.imagewidget(
            parent=s.root,
            position=pos_sep,
            texture=Eval.TEXTURE(Const.SKIN),
            size=(0, 0),
            opacity=0,
            color=Color.COLD
        )
        s.window_kids.append((w, pos_sep, text_push, delay + 0.1, ('size', ((0, 2), (145, 2)))))

        s.pos_inputs = []
        labels = ['X', 'Y', 'Z']

        for i, lbl in enumerate(labels):
            lbl_y = sy - 165 - (i * 40)
            inp_y = sy - 170 - (i * 40)

            pos_lbl = (left_x, lbl_y)
            w = bui.textwidget(parent=s.root, position=pos_lbl, size=(
                50, 30), text=f'Pos {lbl}', color=Const.INVISIBLE, maxwidth=50, h_align='left')
            s.window_kids.append((w, pos_lbl, text_push, delay + 0.15 + i*0.05))

            pos_inp = (left_x + 60, inp_y)
            inp = bui.textwidget(
                parent=s.root,
                position=pos_inp,
                editable=True,
                allow_clear_button=False,
                size=(0, 0),
                description=f'Pos {lbl}',
                color=Const.INVISIBLE,
                maxwidth=80,
                v_align=Const.ALIGN,
                glow_type=Const.GLOW,
                text=str(init_pos[i] if len(init_pos) > i else 0)
            )
            s.pos_inputs.append(inp)
            s.window_kids.append((inp, pos_inp, text_push, delay+0.15 +
                                 i*0.05, ('size', ((0, 35), (90, 35)))))

        scroll_x = 170
        scroll_y = 50
        scroll_w = sx - scroll_x - 10
        scroll_h = 195

        attr_scroll = bui.scrollwidget(
            parent=s.root,
            position=(scroll_x, scroll_y),
            color=Color.BASE,
            size=(scroll_w/2, 0),
            border_opacity=0
        )
        s.window_kids.append((attr_scroll, (scroll_x, scroll_y), 20, delay,
                              ('size', ((0, scroll_h), (scroll_w, scroll_h))),
                              ('border_opacity', (0, Color.OPACITY)),
                              ('color', (Color.COLD, Color.BASE))
                              ))

        s.attr_root = bui.containerwidget(parent=attr_scroll, background=False)

        s.attr_widgets = []
        s.current_inputs = {}

        def anim_scroll_kid(w, px, py, dt):
            if (anim := s.anims.get(id(w), {}).get('scroll')):
                anim.cancel()
            ty = w.get_widget_type()
            attrs = {'position': ((px + 50, py), (px, py))}
            if ty == 'text':
                attrs['color'] = (Const.INVISIBLE, (*Color.TEXT, Color.TEXT_OPACITY))
            elif ty == 'button':
                attrs['opacity'] = (0, Color.OPACITY)
                attrs['textcolor'] = (Const.INVISIBLE, (*Color.TEXT, Color.TEXT_OPACITY))
            s.anims[id(w)]['scroll'] = Animate(widget=w, attrs=attrs, duration=0.18, delay=dt)

        def sync_edits():
            for key, wid in s.current_inputs.items():
                s.current_attrs[key] = bui.textwidget(query=wid)

        def add_custom_attr(k_wid, v_wid):
            sync_edits()
            k = bui.textwidget(query=k_wid).strip()
            v = bui.textwidget(query=v_wid).strip()
            if not k:
                s.toast(Format.ERROR_EMPTY(Strings.ATTR))
                Eval.SOUND(Const.BAD_SOUND).play()
                return

            try:
                with bs.get_foreground_host_activity().context:
                    _shared = None
                    _factory = None
                    if s.current_node_type == 'spaz':
                        from bascenev1lib.gameutils import SharedObjects
                        from bascenev1lib.actor.spazfactory import SpazFactory
                        _shared = SharedObjects.get()
                        _factory = SpazFactory.get()
                    eval(to_eval(k, v))
            except Exception as e:
                s.toast(Format.ERROR(e))
                Eval.SOUND(Const.BAD_SOUND).play()
                return

            s.current_attrs[k] = v
            Eval.SOUND(Const.OK_SOUND).play()
            refresh_right_pane()

        def delete_attr(k):
            sync_edits()
            if k in s.current_attrs:
                del s.current_attrs[k]
            Eval.SOUND(Const.OK_SOUND).play()
            refresh_right_pane()

        def refresh_right_pane(initial=False):
            for w in s.attr_widgets:
                w.delete()
            s.attr_widgets.clear()
            s.current_inputs.clear()

            row_h = 35
            num_attrs = len(s.current_attrs)
            content_h = (num_attrs + 1) * row_h

            bui.containerwidget(edit=s.attr_root, size=(250, max(content_h, scroll_h)))

            keys = list(s.current_attrs.keys())
            for i, k in enumerate(keys):
                y_pos = max(content_h, scroll_h) - (i + 1) * row_h

                lbl = bui.textwidget(
                    parent=s.attr_root, position=(0, y_pos), size=(85, row_h),
                    text=k, h_align='left', v_align='center', maxwidth=80,
                    color=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
                )
                s.attr_widgets.append(lbl)

                val = str(s.current_attrs[k])
                inp = bui.textwidget(
                    parent=s.attr_root, position=(90, y_pos+5), size=(120, row_h-5),
                    text=val, editable=True, h_align='left', v_align='center',
                    glow_type=Const.GLOW, allow_clear_button=False,
                    color=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
                )
                s.attr_widgets.append(inp)
                s.current_inputs[k] = inp

                del_btn = bui.buttonwidget(
                    parent=s.attr_root, position=(215, y_pos+5), size=(30, row_h-5),
                    label='-', on_activate_call=bui.CallPartial(delete_attr, k),
                    button_type='square', enable_sound=False,
                    texture=Eval.TEXTURE(Const.SKIN), color=Color.BASE,
                    opacity=0 if initial else Color.OPACITY,
                    textcolor=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
                )
                s.attr_widgets.append(del_btn)

                if initial:
                    anim_scroll_kid(lbl, 0, y_pos, delay + 0.1 + i*0.03)
                    anim_scroll_kid(inp, 90, y_pos+5, delay + 0.1 + i*0.03)
                    anim_scroll_kid(del_btn, 215, y_pos+5, delay + 0.1 + i*0.03)

            y_pos = max(content_h, scroll_h) - (num_attrs + 1) * row_h
            new_k = bui.textwidget(
                parent=s.attr_root, position=(0, y_pos+5), size=(85, row_h-5),
                text="new_attr", editable=True, h_align='left', v_align='center',
                maxwidth=80, glow_type=Const.GLOW, allow_clear_button=False,
                color=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
            )
            s.attr_widgets.append(new_k)

            new_v = bui.textwidget(
                parent=s.attr_root, position=(90, y_pos+5), size=(120, row_h-5),
                text="value", editable=True, h_align='left', v_align='center',
                glow_type=Const.GLOW, allow_clear_button=False,
                color=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
            )
            s.attr_widgets.append(new_v)

            add_btn = bui.buttonwidget(
                parent=s.attr_root, position=(215, y_pos+5), size=(30, row_h-5),
                label='+', on_activate_call=lambda: add_custom_attr(new_k, new_v),
                button_type='square', enable_sound=False,
                texture=Eval.TEXTURE(Const.SKIN), color=Color.BASE,
                opacity=0 if initial else Color.OPACITY,
                textcolor=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
            )
            s.attr_widgets.append(add_btn)

            if initial:
                anim_scroll_kid(new_k, 0, y_pos+5, delay + 0.1 + num_attrs*0.03)
                anim_scroll_kid(new_v, 90, y_pos+5, delay + 0.1 + num_attrs*0.03)
                anim_scroll_kid(add_btn, 215, y_pos+5, delay + 0.1 + num_attrs*0.03)

        refresh_right_pane(initial=True)

        prv_on = False
        prv_node = None

        def do_preview():
            nonlocal prv_on, prv_node
            if prv_on:
                prv_on = False
                bui.buttonwidget(prv_btn, label=Strings.PREVIEW)
                if prv_node and prv_node.exists():
                    prv_node.delete()
                prv_node = None
                Eval.SOUND(Const.OK_SOUND).play()
                return

            try:
                pos_tuple = (
                    float(bui.textwidget(query=s.pos_inputs[0]) or '0'),
                    float(bui.textwidget(query=s.pos_inputs[1]) or '0'),
                    float(bui.textwidget(query=s.pos_inputs[2]) or '0')
                )
            except Exception:
                s.toast("Invalid Position!")
                Eval.SOUND(Const.BAD_SOUND).play()
                return

            sync_edits()
            try:
                with bs.get_foreground_host_activity().context:
                    _shared = None
                    _factory = None
                    if s.current_node_type == 'spaz':
                        from bascenev1lib.gameutils import SharedObjects
                        from bascenev1lib.actor.spazfactory import SpazFactory
                        _shared = SharedObjects.get()
                        _factory = SpazFactory.get()
                    kw = {} if s.current_node_type == 'spaz' else {'position': pos_tuple}
                    for key, val in s.current_attrs.items():
                        if val:
                            kw[key] = eval(to_eval(key, val))
                    if s.current_node_type == 'spaz':
                        from bascenev1lib.actor.spaz import Spaz
                        for extraneous in ('materials', 'roller_materials', 'punch_materials', 'pickup_materials', 'style'):
                            kw.pop(extraneous, None)
                        prv_actor = Spaz(
                            character=kw.pop('character', None) or 'Spaz',
                            color=kw.pop('color', (1, 1, 1)),
                            highlight=kw.pop('highlight', (1, 1, 1)),
                            start_invincible=False
                        ).autoretain()
                        for k, v in kw.items():
                            setattr(prv_actor.node, k, v)
                        prv_node = prv_actor.node
                        bs.timer(
                            0,
                            lambda a=prv_actor: a.node.exists() and a.handlemessage(bs.StandMessage(pos_tuple, 0.0))
                        )
                    else:
                        prv_node = bs.newnode(s.current_node_type, attrs=kw)
            except Exception as e:
                s.toast(Format.ERROR(e))
                Eval.SOUND(Const.BAD_SOUND).play()
                return

            Eval.SOUND(Const.OK_SOUND).play()
            bui.buttonwidget(prv_btn, label=Strings.STOP)
            prv_on = True

        pos = (left_x - 3, s.window_marg)
        size = (145, 40)
        prv_btn = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.PREVIEW,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_preview
        )
        s.window_kids.append((prv_btn, pos, 50, delay + 0.1, ('size', ((0, size[1]), size))))

        def do_done():
            nam = bui.textwidget(query=name_text)
            if not nam:
                s.toast(Format.ERROR_EMPTY(Strings.NAME))
                Eval.SOUND(Const.BAD_SOUND).play()
                return

            try:
                pos_tuple = (
                    float(bui.textwidget(query=s.pos_inputs[0]) or '0'),
                    float(bui.textwidget(query=s.pos_inputs[1]) or '0'),
                    float(bui.textwidget(query=s.pos_inputs[2]) or '0')
                )
            except Exception:
                s.toast("Invalid Position!")
                Eval.SOUND(Const.BAD_SOUND).play()
                return

            sync_edits()
            final_attrs = {'position': str(pos_tuple)}

            try:
                with bs.get_foreground_host_activity().context:
                    _shared = None
                    _factory = None
                    if s.current_node_type == 'spaz':
                        from bascenev1lib.gameutils import SharedObjects
                        from bascenev1lib.actor.spazfactory import SpazFactory
                        _shared = SharedObjects.get()
                        _factory = SpazFactory.get()
                    for key, val in s.current_attrs.items():
                        if val:
                            eval_str = to_eval(key, val)
                            eval(eval_str)
                            final_attrs[key] = eval_str
            except Exception as e:
                s.toast(Format.ERROR(e))
                Eval.SOUND(Const.BAD_SOUND).play()
                return

            final_data = {
                'type': s.current_node_type,
                'name': nam,
                'attrs': final_attrs
            }

            Eval.SOUND(Const.OK_SOUND).play()
            if edit and not load:
                data.update(final_data)
                bui.buttonwidget(s.stamp_kids[edit['order']], label=nam)
                s.dismiss_window()
                s.toast(Strings.INFO_SAVED)
            else:
                s.add_entry(final_data)
                s.increment += 1

        done_pos = (sx - 105, s.window_marg)
        done_btn = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=done_pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.DONE,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_done
        )
        s.window_kids.append((done_btn, done_pos, 50, delay+0.1, ('size', ((0, 40), (95, 40)))))

        s.window_trash = [s.attr_widgets]

        return lambda: prv_node and prv_node.exists() and prv_node.delete()

    def make_camera_window(s, edit=None, load=False):
        x, y = s.window_pos
        x += 1
        sx, sy = s.window_size
        bx, by = sx/3-s.window_marg*4, 40
        text_push = 15
        delay = 0.35
        off = s.window_marg*5+bx
        yoff = by+s.window_marg
        data = edit and edit['data']

        prv_on = False
        chks = [True, True, False]
        last_pos = _ba.get_camera_position()
        last_tar = _ba.get_camera_target()
        old_pos = list(last_pos)
        old_tar = list(last_tar)
        virgin = True
        current_manual = False

        prev_pos_node = None
        prev_tar_node = None

        def do_chk(i, v):
            chks[i] = v

        pos = (s.window_marg-3, by+s.window_marg*5)
        pos_chk = bui.checkboxwidget(
            parent=s.root,
            text=Strings.CAMERA_POSITION_CHECK,
            position=pos,
            color=Color.BASE,
            textcolor=Const.INVISIBLE,
            scale=0,
            maxwidth=bx-s.window_marg,
            value=chks[0],
            on_value_change_call=bui.CallPartial(do_chk, 0)
        )
        s.window_kids.append((pos_chk, pos, text_push, delay+0.12,
                              ('size', ((bx/2, by), (bx, by))),
                              ('scale', (0, 1))
                              ))

        pos_texts = []
        top = yoff*4.5
        for i, o in enumerate(old_pos):
            pos = (s.window_marg-3, top-yoff*i)
            w = bui.textwidget(
                parent=s.root,
                position=pos,
                editable=True,
                allow_clear_button=False,
                color=Const.INVISIBLE,
                size=(0, 0),
                text=str(round(o, 2))
            )
            pos_texts.append(w)
            s.window_kids.append((w, pos, text_push, delay+(0.24-0.06*i),
                                  ('size', ((bx/2, by), (bx, by)))
                                  ))

        pos = (off+s.window_marg*2-2, by+s.window_marg*5)
        tar_chk = bui.checkboxwidget(
            parent=s.root,
            text=Strings.CAMERA_TARGET_CHECK,
            position=pos,
            color=Color.BASE,
            textcolor=Const.INVISIBLE,
            scale=0,
            maxwidth=bx-s.window_marg,
            value=chks[1],
            on_value_change_call=bui.CallPartial(do_chk, 1)
        )
        s.window_kids.append((tar_chk, pos, text_push, delay+0.12,
                              ('size', ((bx/2, by), (bx, by))),
                              ('scale', (0, 1))
                              ))

        target_texts = []
        for i, o in enumerate(old_tar):
            pos = (off+s.window_marg-3, top-yoff*i)
            w = bui.textwidget(
                parent=s.root,
                position=pos,
                editable=True,
                allow_clear_button=False,
                color=Const.INVISIBLE,
                size=(0, 0),
                text=str(round(o, 2))
            )
            target_texts.append(w)
            s.window_kids.append((w, pos, text_push, delay+(0.24-0.06*i),
                                  ('size', ((bx/2, by), (bx, by)))
                                  ))

        pos = (off*2+s.window_marg*2-2, by+s.window_marg*5)
        man_chk = bui.checkboxwidget(
            parent=s.root,
            text=Strings.CAMERA_MANUAL_CHECK,
            position=pos,
            color=Color.BASE,
            textcolor=Const.INVISIBLE,
            scale=0,
            maxwidth=bx-s.window_marg,
            value=chks[2],
            on_value_change_call=bui.CallPartial(do_chk, 2)
        )
        s.window_kids.append((man_chk, pos, text_push, delay+0.12,
                              ('size', ((bx/2, by), (bx, by))),
                              ('scale', (0, 1))
                              ))

        def collect_pos():
            nonlocal last_pos
            last_pos = [float(bui.textwidget(query=w) or '0') for w in pos_texts]

        def collect_tar():
            nonlocal last_tar
            last_tar = [float(bui.textwidget(query=w) or '0') for w in target_texts]

        def collect():
            collect_pos()
            collect_tar()

        def kill_prev():
            nonlocal prev_pos_node, prev_tar_node
            if prev_pos_node and prev_pos_node.exists():
                prev_pos_node.delete()
                prev_pos_node = None
            if prev_tar_node and prev_tar_node.exists():
                prev_tar_node.delete()
                prev_tar_node = None

        def do_see():
            nonlocal prev_pos_node, prev_tar_node, current_manual

            if chks[2] != current_manual:
                _ba.set_camera_manual(chks[2])
                current_manual = chks[2]

            if chks[0]:
                collect_pos()
                _ba.set_camera_position(*last_pos)

                if prev_pos_node and prev_pos_node.exists():
                    prev_pos_node.text = bui.charstr(
                        getattr(bui.SpecialChar, Const.PIN_POINT)) + ' ' + Strings.POSITION
                    prev_pos_node.position = last_pos
                else:
                    with bs.get_foreground_host_activity().context:
                        prev_pos_node = bs.newnode(
                            'text',
                            attrs={
                                'text': bui.charstr(getattr(bui.SpecialChar, Const.PIN_POINT)) + ' ' + Strings.POSITION,
                                'position': last_pos,
                                'in_world': True,
                                'scale': 0.01,
                                'flatness': 1,
                                'color': Color.WARM,
                                'shadow': 1.0
                            }
                        )

            if chks[1]:
                collect_tar()
                _ba.set_camera_target(*last_tar)

                if prev_tar_node and prev_tar_node.exists():
                    prev_tar_node.text = bui.charstr(
                        getattr(bui.SpecialChar, Const.PIN_POINT)) + ' ' + Strings.TARGET
                    prev_tar_node.position = last_tar
                else:
                    with bs.get_foreground_host_activity().context:
                        prev_tar_node = bs.newnode(
                            'text',
                            attrs={
                                'text': bui.charstr(getattr(bui.SpecialChar, Const.PIN_POINT)) + ' ' + Strings.TARGET,
                                'position': last_tar,
                                'in_world': True,
                                'scale': 0.01,
                                'flatness': 1,
                                'color': Color.COLD,
                                'shadow': 1.0
                            }
                        )

        see_timer = None

        def start_preview():
            nonlocal see_timer, prv_on, virgin, current_manual
            prv_on = True
            virgin = False
            current_manual = chks[2]
            if chks[2]:
                _ba.set_camera_manual(True)
            see_timer = bui.AppTimer(0.02, do_see, repeat=True)

        def stop_preview():
            nonlocal see_timer, prv_on, current_manual
            prv_on = False
            see_timer = None
            kill_prev()

            if current_manual:
                _ba.set_camera_manual(False)
                current_manual = False

        def enforce():
            for w, d in zip(pos_texts, last_pos):
                bui.textwidget(w, text=str(d))
            for w, d in zip(target_texts, last_tar):
                bui.textwidget(w, text=str(d))
            for w, b in zip((pos_chk, tar_chk, man_chk), chks):
                bui.checkboxwidget(w, value=b)

        mod = 0
        stp = 1

        def add(*d):
            for i, w in enumerate(mod and target_texts or pos_texts):
                old = bui.textwidget(query=w) or '0'
                z = round(float(old)+d[i]*stp, 2)
                bui.textwidget(w, text=str(z))
            collect()

        def action(n):
            nonlocal mod
            if n == 0:
                add(0, 0, 1)
            if n == 1:
                add(-1, 0, 0)
            if n == 2:
                mod = 0
                s.toast(Strings.INFO_POSITION_MODE)
            if n == 3:
                add(0, -1, 0)
            if n == 4:
                pass
            if n == 5:
                add(0, 1, 0)
            if n == 6:
                add(0, 0, -1)
            if n == 7:
                add(1, 0, 0)
            if n == 8:
                mod = 1
                s.toast(Strings.INFO_TARGET_MODE)
            Eval.SOUND(Const.OK_SOUND).play()

        for i in range(3):
            for j in range(3):
                n = i*3+j
                pos = (sx-(by+s.window_marg)*(3-i), (by+s.window_marg+1)*(2.5+j))
                t = Const.CAMERA_TOOLS[n]
                t = len(t) > 1 and Eval.CHAR(t) or t
                w = bui.buttonwidget(
                    parent=s.root,
                    position=pos,
                    size=(0, 0),
                    opacity=0,
                    label=t,
                    color=Color.BASE,
                    textcolor=Const.INVISIBLE,
                    texture=Eval.TEXTURE(Const.SKIN),
                    enable_sound=False,
                    repeat=True,
                    on_activate_call=bui.CallPartial(action, n)
                )
                s.window_kids.append((w, pos, text_push, delay+0.15+0.02*n,
                                      ('size', ((by/2, by), (by, by)))
                                      ))

        pos = (s.window_marg-3, by+s.window_marg*4)
        size = (sx-s.window_marg, 2)
        w = bui.imagewidget(
            parent=s.root,
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            size=(0, 0),
            opacity=0,
            color=Color.COLD
        )
        s.window_kids.append((w, pos, text_push, delay+0.1,
                              ('size', ((0, size[1]), size))
                              ))

        def do_reset(shut=0):
            Eval.SOUND(Const.OK_SOUND).play()
            shut or s.toast(Strings.INFO_RESETTED)

            if prv_on:
                do_preview(1)
            else:
                nonlocal virgin
                virgin = True
                kill_prev()

            if not shut:
                for i in range(3):
                    bui.textwidget(pos_texts[i], text=str(round(old_pos[i], 2)))
                    bui.textwidget(target_texts[i], text=str(round(old_tar[i], 2)))

        pos = (s.window_marg, s.window_marg)
        w = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.CAMERA_RESET_BUTTON,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_reset
        )
        s.window_kids.append((w, pos, 50, delay+0.23,
                              ('size', ((bx/2, by), (bx, by)))
                              ))

        def do_preview(shut=0):
            nonlocal prv_on
            prv_on = not prv_on
            bui.buttonwidget(
                prv_button,
                label=prv_on and Strings.STOP or Strings.PREVIEW
            )
            shut or (
                s.toast(prv_on and Strings.INFO_PREVIEW_ON or Strings.PREVIEW_OFF) or
                Eval.SOUND(Const.OK_SOUND).play()
            )
            if prv_on:
                start_preview()
            else:
                stop_preview()

        pos = (s.window_marg+off, s.window_marg)
        prv_button = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.PREVIEW,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_preview
        )
        s.window_kids.append((prv_button, pos, 50, delay+0.23,
                              ('size', ((bx/2, by), (bx, by)))
                              ))

        def do_done():
            collect()
            nam = Strings.CAMERA_ENTRY
            final = {
                'chks': chks,
                'name': nam,
                'position': last_pos,
                'target': last_tar
            }
            Eval.SOUND(Const.OK_SOUND).play()
            if edit and not load:
                data.update(final)
                s.dismiss_window()
                s.toast(Strings.INFO_SAVED)
            else:
                s.add_entry(final)

        pos = (s.window_marg+off*2, s.window_marg)
        w = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.DONE,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_done
        )
        s.window_kids.append((w, pos, 50, delay+0.23,
                              ('size', ((bx/2, by), (bx, by)))
                              ))

        if edit:
            last_pos = data['position']
            last_tar = data['target']
            chks = data['chks']
            enforce()

        return lambda: (kill_prev(), stop_preview()) if not virgin else kill_prev()

    def make_sound_window(s, edit=None, load=False, wait=0.43):
        s.prv_sound = None
        if wait:
            bui.apptimer(
                wait, bui.CallPartial(
                    s.make_sound_window,
                    edit, wait=False
                )
            )
            return (wait, lambda: s.prv_sound and s.prv_sound.delete())
        x, y = s.window_pos
        sx, sy = s.window_size
        text_push = 15
        delay = 0.35
        data = edit and edit['data']

        sound_files = sorted(listdir(join(Const.BA_DATA, 'audio')), reverse=True)

        current_sound = data and data['file'] or None

        def format_name(filename):
            name = filename.replace('.ogg', '')
            spaced = sub(r'([a-z])([A-Z])', r'\1 \2', name)
            return spaced.title()

        def stop_current():
            if s.prv_sound:
                s.prv_sound.delete()

        size = dx, dy = (sx/2 - s.window_marg*3, sy - s.window_marg*9 - 55)
        pos = px, py = (s.window_marg - s.window_fix, s.window_marg - s.window_fix + 55)
        sound_scroll = bui.scrollwidget(
            parent=s.root,
            position=pos,
            color=Color.BASE,
            size=(dx/2, 0),
            border_opacity=0
        )
        s.window_kids.append((sound_scroll, pos, 20, delay + 0,
                              ('size', ((0, size[1]), size)),
                              ('border_opacity', (0, Color.OPACITY)),
                              ('color', (Color.COLD, Color.BASE))
                              ))

        sound_root = bui.containerwidget(
            parent=sound_scroll,
            background=False
        )

        chks = data.get('chks', [False, False])

        def do_chk(i, v):
            chks[i] = v
        bx, by = 80, 40
        pos = (s.window_marg-8, s.window_marg)
        pos_chk = bui.checkboxwidget(
            parent=s.root,
            text=Strings.EVERYWHERE,
            position=pos,
            color=Color.BASE,
            textcolor=Const.INVISIBLE,
            scale=0,
            maxwidth=bx-s.window_marg,
            value=chks[0],
            on_value_change_call=bui.CallPartial(do_chk, 0)
        )
        s.window_kids.append((pos_chk, pos, text_push, delay+0.12,
                              ('size', ((bx/2, by), (bx, by))),
                              ('scale', (0, 1))
                              ))

        bx, by = 80, 40
        pos = (s.window_marg-3+bx+40, s.window_marg)
        loop_chk = bui.checkboxwidget(
            parent=s.root,
            text=Strings.LOOP,
            position=pos,
            color=Color.BASE,
            textcolor=Const.INVISIBLE,
            scale=0,
            maxwidth=bx/2,
            value=chks[1],
            on_value_change_call=bui.CallPartial(do_chk, 1)
        )
        s.window_kids.append((loop_chk, pos, text_push, delay+0.12,
                              ('size', ((bx/2, by), (bx, by))),
                              ('scale', (0, 1))
                              ))

        text_y = 30
        sound_texts = []

        for i, filename in enumerate(sound_files):
            w = bui.textwidget(
                parent=sound_root,
                size=(dx, text_y),
                position=(0, i * text_y),
                maxwidth=dx - 15,
                selectable=True,
                glow_type=Const.GLOW,
                click_activate=True,
                text=filename,
                color=Const.INVISIBLE,
                v_align=Const.ALIGN
            )
            sound_texts.append(w)

        bui.containerwidget(
            sound_root,
            size=(dx, max(len(sound_files) * text_y, dy - 15))
        )

        title_pos = (sx/2 + s.window_marg, sy - s.window_marg - 80)
        title_text = bui.textwidget(
            parent=s.root,
            position=title_pos,
            text=current_sound and format_name(current_sound) or Strings.SOUND_PLACEHOLDER,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            maxwidth=sx/2 - s.window_marg*2,
            scale=1.2
        )
        s.window_kids.append((title_text, title_pos, text_push, delay + 0.1))

        input_width = (sx/2 - s.window_marg*5) / 3 + 5
        input_height = 35
        input_y = sy - s.window_marg - 150
        labels = ['X', 'Y', 'Z']
        position_inputs = []

        for idx, label in enumerate(labels):
            label_pos = (sx/2 + s.window_marg + idx *
                         (input_width + s.window_marg), input_y + input_height)
            label_widget = bui.textwidget(
                parent=s.root,
                position=label_pos,
                text=label,
                color=Const.INVISIBLE,
                scale=0.8
            )
            s.window_kids.append((label_widget, label_pos, text_push, delay + 0.12))

            input_pos = (sx/2 + s.window_marg + idx * (input_width + s.window_marg) - 5, input_y)
            input_widget = bui.textwidget(
                parent=s.root,
                position=input_pos,
                editable=True,
                allow_clear_button=False,
                color=Const.INVISIBLE,
                size=(0, 0),
                text=data and str(data.get(label.lower(), 0)) or '0',
                glow_type=Const.GLOW,
                v_align=Const.ALIGN
            )
            position_inputs.append(input_widget)
            s.window_kids.append((input_widget, input_pos, text_push, delay + 0.13,
                                  ('size', ((input_width/2, input_height), (input_width, input_height)))
                                  ))

        vol_label_pos = (sx/2, input_y - 36)
        vol_label = bui.textwidget(
            parent=s.root,
            position=vol_label_pos,
            text='Volume',
            color=Const.INVISIBLE,
            scale=0.8
        )
        s.window_kids.append((vol_label, vol_label_pos, text_push, delay + 0.15))

        vol_input_pos = (sx/2 + s.window_marg + 90, input_y - 40)
        volume_input = bui.textwidget(
            parent=s.root,
            position=vol_input_pos,
            editable=True,
            allow_clear_button=False,
            color=Const.INVISIBLE,
            size=(0, 0),
            text=data and str(data.get('volume', 1.0)) or '1.0',
            glow_type=Const.GLOW,
            v_align=Const.ALIGN
        )
        s.window_kids.append((volume_input, vol_input_pos, text_push, delay + 0.16,
                              ('size', ((input_width/2, input_height), (input_width * 1.8, input_height)))
                              ))

        def select_sound(filename):
            nonlocal current_sound
            stop_current()
            current_sound = filename
            bui.textwidget(title_text, text=format_name(filename))

        all_delay = (delay-0.35) + 0.05 + len(sound_files) * 0.01
        for i, (filename, w) in enumerate(zip(sound_files, sound_texts)):
            bui.textwidget(
                w,
                on_activate_call=bui.CallPartial(select_sound, filename)
            )
            butter = s.global_butter
            s.anims[id(w)] = Animate(
                widget=w,
                attrs={
                    'color': (
                        Const.INVISIBLE,
                        (*Color.TEXT, Color.TEXT_OPACITY)
                    ),
                    'position': (
                        (50, i * text_y),
                        (0, i * text_y)
                    )
                },
                duration=butter,
                delay=all_delay - i * 0.01
            )

        s.window_trash = [sound_texts]

        button_x = sx - (dx + s.window_marg*2)
        button_y = s.window_marg

        def do_play():
            if not current_sound:
                s.toast(Strings.ERROR_NO_SOUND_SELECTED)
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            stop_current()
            sound_name = current_sound.replace('.ogg', '')
            try:
                pos = collect_pos()
            except:
                s.toast(Strings.ERROR_INVALID.format(Strings.POSITION))
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            try:
                vol = float(bui.textwidget(query=volume_input) or '1.0')
            except Exception as e:
                Eval.SOUND(Const.BAD_SOUND).play()
                Format.ERROR(e)
                return
            with bs.get_foreground_host_activity().context:
                s.prv_sound = bs.newnode(
                    'sound',
                    attrs={
                        'sound': bs.getsound(sound_name),
                        'position': pos,
                        'volume': vol,
                        'positional': not chks[0],
                        'loop': chks[1]
                    }
                )

        play_pos = (button_x-5, button_y*3+by)
        play_button = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=play_pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Eval.CHAR(Const.PLAY_BUTTON),
            textcolor=Const.INVISIBLE,
            on_activate_call=do_play
        )
        s.window_kids.append((play_button, play_pos, 50, delay + 0.15,
                              ('size', ((0, by), (dx/2 - s.window_marg/2, by)))
                              ))

        def do_stop():
            stop_current()

        stop_pos = (button_x+dx/2+s.window_marg*2, button_y*3+by)
        stop_button = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=stop_pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Eval.CHAR(Const.PAUSE_BUTTON),
            textcolor=Const.INVISIBLE,
            on_activate_call=do_stop
        )
        s.window_kids.append((stop_button, stop_pos, 50, delay + 0.15,
                              ('size', ((0, by), (dx/2 - s.window_marg/2+2, by)))
                              ))

        def collect_pos():
            return [
                float(bui.textwidget(query=i) or '0')
                for i in position_inputs
            ]

        def do_done():
            if not current_sound:
                s.toast(Strings.ERROR_NO_SOUND_SELECTED)
                Eval.SOUND(Const.BAD_SOUND).play()
                return

            stop_current()

            try:
                x_val, y_val, z_val = collect_pos()
            except ValueError:
                s.toast(Strings.ERROR_INVALID.format(Strings.POSITION))
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            try:
                vol_val = float(bui.textwidget(query=volume_input) or '1.0')
            except Exception as e:
                Eval.SOUND(Const.BAD_SOUND).play()
                Format.ERROR(e)
                return

            Eval.SOUND(Const.OK_SOUND).play()

            final = {
                'name': format_name(current_sound),
                'file': current_sound,
                'x': x_val,
                'y': y_val,
                'z': z_val,
                'volume': vol_val,
                'chks': chks.copy(),
            }

            if edit and not load:
                data.update(final)
                bui.buttonwidget(
                    s.stamp_kids[edit['order']],
                    label=final['name']
                )
                s.dismiss_window()
                s.toast(Strings.INFO_SAVED)
            else:
                s.add_entry(final)

        done_pos = (sx - (dx + s.window_marg*2), button_y)
        done_button = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=done_pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.DONE,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_done
        )
        s.window_kids.append((done_button, done_pos, 50, delay + 0.2,
                              ('size', ((0, by), (sx/2 - s.window_marg*2, by)))
                              ))

    FX_TYPES = ['spark', 'impact', 'sticky', 'ice', 'custom']
    FX_DEFAULT_ATTRS = {
        'spark': {
            'count': '20', 'scale': '1.0', 'spread': '0.6',
            'chunk_type': 'spark',
        },
        'impact': {
            'count': '8', 'scale': '0.8', 'chunk_type': 'metal',
        },
        'sticky': {
            'count': '15', 'scale': '0.6', 'chunk_type': 'slime',
            'emit_type': 'stickers',
        },
        'ice': {
            'count': '20', 'scale': '0.5', 'spread': '0.2',
            'chunk_type': 'ice',
        },
        'custom': {
            'count': '20', 'emit_type': 'distortion',
        },
    }

    def make_fx_window(s, edit=None, load=False):
        x, y = s.window_pos
        sx, sy = s.window_size
        text_push = 15
        delay = 0.35
        data = edit and edit['data']

        VECTOR_KEYS = ('position',)

        def guess_type(attrs):
            ct = attrs.get('chunk_type')
            et = attrs.get('emit_type')
            if ct == 'spark' and et != 'stickers':
                return 'spark'
            if ct == 'metal':
                return 'impact'
            if et == 'stickers':
                return 'sticky'
            if ct == 'ice':
                return 'ice'
            return 'custom'

        s.current_fx_type = guess_type(data['attrs']) if data else 'spark'

        init_pos = (0, 0, 0)
        s.current_fx_attrs = {}

        def to_friendly(k, v):
            val = str(v).strip()
            if val.startswith('"') and val.endswith('"'):
                return val[1:-1]
            if val.startswith("'") and val.endswith("'"):
                return val[1:-1]
            return val

        def to_eval(k, v):
            v = str(v).strip()
            if k in ('chunk_type', 'emit_type', 'tendril_type'):
                return f'"{v}"'
            return v

        if data and 'attrs' in data:
            for k, v in data['attrs'].items():
                if k == 'position':
                    try:
                        init_pos = eval(v) if isinstance(v, str) else v
                    except Exception:
                        pass
                else:
                    s.current_fx_attrs[k] = to_friendly(k, v)
        else:
            for k, v in s.FX_DEFAULT_ATTRS[s.current_fx_type].items():
                s.current_fx_attrs[k] = v

        left_x = 10

        pos_lbl = (left_x, sy - 85)
        w = bui.textwidget(parent=s.root, position=pos_lbl, size=(50, 30),
                           text=Strings.TYPE, color=Const.INVISIBLE, maxwidth=50, h_align='left')
        s.window_kids.append((w, pos_lbl, text_push, delay))

        pos_inp = (left_x + 60, sy - 90)
        type_btn = bui.buttonwidget(
            parent=s.root,
            position=pos_inp,
            size=(0, 0),
            label=s.current_fx_type.capitalize(),
            color=Color.BASE,
            textcolor=Const.INVISIBLE,
            texture=Eval.TEXTURE(Const.SKIN),
            on_activate_call=lambda: open_type_picker(),
            enable_sound=False
        )
        s.window_kids.append((type_btn, pos_inp, text_push, delay, ('size', ((0, 35), (90, 35)))))

        type_btn_pos = (x + pos_inp[0], y + pos_inp[1])
        type_btn_shadow = bui.imagewidget(
            parent=s.root,
            opacity=0,
            texture=Eval.TEXTURE(Const.SHADOW),
            color=Color.SHADOW
        )
        s.window_trash.append([type_btn_shadow])

        def apply_type(new_type):
            s.current_fx_type = new_type
            bui.buttonwidget(edit=type_btn, label=s.current_fx_type.capitalize())

            s.current_fx_attrs.clear()
            for k, v in s.FX_DEFAULT_ATTRS[s.current_fx_type].items():
                s.current_fx_attrs[k] = v
            refresh_right_pane(initial=False)

        def open_type_picker():
            if s.window_sub_on:
                s.window_sub_on[2]()
            Eval.SOUND(Const.OK_SOUND).play()
            bui.buttonwidget(
                type_btn,
                on_activate_call=Const.DO_NOTHING,
                selectable=False
            )

            wx, wy = s.window_pos
            wsx, wsy = s.window_size
            picker_x, picker_sx = 120, 130
            picker_pos = (wx + wsx + 100, wy)
            picker_size = (picker_sx, wsy)
            (
                picker_shadow_pos,
                picker_shadow_size
            ) = Eval.SHADOW(*picker_pos, *picker_size)

            btn_start_pos, btn_start_size = type_btn_pos, (90, 35)
            butter = s.global_butter * 1.3

            grow_anim = Animate(
                widget=type_btn,
                duration=butter,
                attrs={
                    'position': (btn_start_pos, picker_pos),
                    'size': (btn_start_size, picker_size),
                    'textcolor': (
                        (*Color.TEXT, Color.TEXT_OPACITY),
                        Const.INVISIBLE
                    )
                }
            )
            shadow_anim = Animate(
                widget=type_btn_shadow,
                attrs={
                    'opacity': (0, Color.SHADOW_OPACITY),
                    'position': (btn_start_pos, picker_shadow_pos),
                    'size': (btn_start_size, picker_shadow_size)
                },
                duration=butter
            )

            child_start_progress = 0.35
            child_delay = butter * child_start_progress
            child_duration = butter * (1 - child_start_progress) + 0.05

            picker_kids = []
            kid_anims = []

            picker_scroll = bui.scrollwidget(
                parent=s.root,
                position=picker_pos,
                size=(0, picker_size[1]),
                color=Color.COLD,
                border_opacity=0
            )
            picker_kids.append(picker_scroll)
            kid_anims.append(Animate(
                widget=picker_scroll,
                duration=child_duration,
                delay=child_delay,
                attrs={
                    'size': ((0, picker_size[1]), picker_size),
                    'border_opacity': (0, Color.OPACITY),
                    'color': (Color.COLD, Color.BASE)
                }
            ))

            row_h = 35
            types = s.FX_TYPES
            picker_root = bui.containerwidget(
                parent=picker_scroll,
                background=False,
                size=(picker_x, row_h * len(types))
            )
            picker_kids.append(picker_root)

            def close_sub(instant=False):
                s.window_sub_on = None
                for anim in kid_anims:
                    anim.cancel()
                kid_anims.clear()
                for w in picker_kids:
                    if w.exists():
                        w.delete()
                picker_kids.clear()
                dur = instant and 0.0001 or butter
                grow_anim.reverse(duration=dur)
                shadow_anim.reverse(duration=dur)
                bui.buttonwidget(
                    type_btn,
                    on_activate_call=open_type_picker,
                    selectable=True
                )
                if not instant:
                    Eval.SOUND(Const.OK_SOUND).play()

            def pick(t):
                Eval.SOUND(Const.OK_SOUND).play()
                apply_type(t)
                close_sub()

            row_off = 15
            for i, t in enumerate(types):
                y_pos = row_h * (len(types) - 1 - i)
                btn = bui.buttonwidget(
                    parent=picker_root,
                    position=(row_off, y_pos),
                    size=(picker_x, row_h),
                    label=t.capitalize(),
                    color=Color.BASE if t != s.current_fx_type else Color.COLD,
                    textcolor=Const.INVISIBLE,
                    opacity=0,
                    texture=Eval.TEXTURE(Const.SKIN),
                    enable_sound=False,
                    on_activate_call=bui.CallPartial(pick, t)
                )
                picker_kids.append(btn)
                stagger = 0.02 * i
                kid_anims.append(Animate(
                    widget=btn,
                    duration=child_duration,
                    delay=child_delay + stagger,
                    attrs={
                        'position': ((row_off, y_pos), (0, y_pos)),
                        'opacity': (0, Color.OPACITY),
                        'textcolor': (
                            Const.INVISIBLE,
                            (*Color.TEXT, Color.TEXT_OPACITY)
                        )
                    }
                ))

            s.window_sub_on = (type_btn, open_type_picker, close_sub)

        pos_lbl = (left_x, sy - 130)
        w = bui.textwidget(parent=s.root, position=pos_lbl, size=(50, 30),
                           text=Strings.NAME, color=Const.INVISIBLE, maxwidth=50, h_align='left')
        s.window_kids.append((w, pos_lbl, text_push, delay + 0.05))

        pos_inp = (left_x + 60, sy - 130)
        name_text = bui.textwidget(
            parent=s.root,
            position=pos_inp,
            editable=True,
            allow_clear_button=False,
            size=(0, 0),
            maxwidth=80,
            description=Strings.FX_NAME_HELP,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            glow_type=Const.GLOW,
            text=(data and data['name'] or list(Strings.EVENTS)[3])
        )
        s.window_kids.append((name_text, pos_inp, text_push, delay +
                             0.05, ('size', ((0, 35), (90, 35)))))

        pos_sep = (left_x + 2, sy - 133)
        w = bui.imagewidget(
            parent=s.root,
            position=pos_sep,
            texture=Eval.TEXTURE(Const.SKIN),
            size=(0, 0),
            opacity=0,
            color=Color.COLD
        )
        s.window_kids.append((w, pos_sep, text_push, delay + 0.1, ('size', ((0, 2), (145, 2)))))

        s.fx_pos_inputs = []
        labels = ['X', 'Y', 'Z']
        for i, lbl in enumerate(labels):
            lbl_y = sy - 165 - (i * 40)
            inp_y = sy - 170 - (i * 40)

            pos_lbl = (left_x, lbl_y)
            w = bui.textwidget(parent=s.root, position=pos_lbl, size=(
                50, 30), text=f'Pos {lbl}', color=Const.INVISIBLE, maxwidth=50, h_align='left')
            s.window_kids.append((w, pos_lbl, text_push, delay + 0.15 + i * 0.05))

            pos_inp = (left_x + 60, inp_y)
            inp = bui.textwidget(
                parent=s.root,
                position=pos_inp,
                editable=True,
                allow_clear_button=False,
                size=(0, 0),
                description=f'Pos {lbl}',
                color=Const.INVISIBLE,
                maxwidth=80,
                v_align=Const.ALIGN,
                glow_type=Const.GLOW,
                text=str(init_pos[i] if len(init_pos) > i else 0)
            )
            s.fx_pos_inputs.append(inp)
            s.window_kids.append((inp, pos_inp, text_push, delay + 0.15 +
                                 i * 0.05, ('size', ((0, 35), (90, 35)))))

        scroll_x = 170
        scroll_y = 50
        scroll_w = sx - scroll_x - 10
        scroll_h = 195

        attr_scroll = bui.scrollwidget(
            parent=s.root,
            position=(scroll_x, scroll_y),
            color=Color.BASE,
            size=(scroll_w / 2, 0),
            border_opacity=0
        )
        s.window_kids.append((attr_scroll, (scroll_x, scroll_y), 20, delay,
                              ('size', ((0, scroll_h), (scroll_w, scroll_h))),
                              ('border_opacity', (0, Color.OPACITY)),
                              ('color', (Color.COLD, Color.BASE))
                              ))

        s.fx_attr_root = bui.containerwidget(parent=attr_scroll, background=False)

        s.fx_attr_widgets = []
        s.fx_current_inputs = {}

        def anim_scroll_kid(w, px, py, dt):
            if (anim := s.anims.get(id(w), {}).get('scroll')):
                anim.cancel()
            ty = w.get_widget_type()
            attrs = {'position': ((px + 50, py), (px, py))}
            if ty == 'text':
                attrs['color'] = (Const.INVISIBLE, (*Color.TEXT, Color.TEXT_OPACITY))
            elif ty == 'button':
                attrs['opacity'] = (0, Color.OPACITY)
                attrs['textcolor'] = (Const.INVISIBLE, (*Color.TEXT, Color.TEXT_OPACITY))
            s.anims[id(w)]['scroll'] = Animate(widget=w, attrs=attrs, duration=0.18, delay=dt)

        def sync_edits():
            for key, wid in s.fx_current_inputs.items():
                s.current_fx_attrs[key] = bui.textwidget(query=wid)

        def add_custom_attr(k_wid, v_wid):
            sync_edits()
            k = bui.textwidget(query=k_wid).strip()
            v = bui.textwidget(query=v_wid).strip()
            if not k:
                s.toast(Format.ERROR_EMPTY(Strings.ATTR))
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            if k in VECTOR_KEYS:
                s.toast(Format.ERROR(f'Use the {k.capitalize()} fields on the left'))
                Eval.SOUND(Const.BAD_SOUND).play()
                return

            try:
                with bs.get_foreground_host_activity().context:
                    eval(to_eval(k, v))
            except Exception as e:
                s.toast(Format.ERROR(e))
                Eval.SOUND(Const.BAD_SOUND).play()
                return

            s.current_fx_attrs[k] = v
            Eval.SOUND(Const.OK_SOUND).play()
            refresh_right_pane()

        def delete_attr(k):
            sync_edits()
            if k in s.current_fx_attrs:
                del s.current_fx_attrs[k]
            Eval.SOUND(Const.OK_SOUND).play()
            refresh_right_pane()

        def refresh_right_pane(initial=False):
            for w in s.fx_attr_widgets:
                w.delete()
            s.fx_attr_widgets.clear()
            s.fx_current_inputs.clear()

            row_h = 35
            num_attrs = len(s.current_fx_attrs)
            content_h = (num_attrs + 1) * row_h

            bui.containerwidget(edit=s.fx_attr_root, size=(250, max(content_h, scroll_h)))

            keys = list(s.current_fx_attrs.keys())
            for i, k in enumerate(keys):
                y_pos = max(content_h, scroll_h) - (i + 1) * row_h

                lbl = bui.textwidget(
                    parent=s.fx_attr_root, position=(0, y_pos), size=(85, row_h),
                    text=k, h_align='left', v_align='center', maxwidth=80,
                    color=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
                )
                s.fx_attr_widgets.append(lbl)

                val = str(s.current_fx_attrs[k])
                inp = bui.textwidget(
                    parent=s.fx_attr_root, position=(90, y_pos + 5), size=(120, row_h - 5),
                    text=val, editable=True, h_align='left', v_align='center',
                    maxwidth=100, glow_type=Const.GLOW, allow_clear_button=False,
                    color=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
                )
                s.fx_attr_widgets.append(inp)
                s.fx_current_inputs[k] = inp

                del_btn = bui.buttonwidget(
                    parent=s.fx_attr_root, position=(215, y_pos + 5), size=(30, row_h - 5),
                    label='-', on_activate_call=bui.CallPartial(delete_attr, k),
                    button_type='square', enable_sound=False,
                    texture=Eval.TEXTURE(Const.SKIN), color=Color.BASE,
                    opacity=0 if initial else Color.OPACITY,
                    textcolor=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
                )
                s.fx_attr_widgets.append(del_btn)

                if initial:
                    anim_scroll_kid(lbl, 0, y_pos, delay + 0.1 + i * 0.03)
                    anim_scroll_kid(inp, 90, y_pos + 5, delay + 0.1 + i * 0.03)
                    anim_scroll_kid(del_btn, 215, y_pos + 5, delay + 0.1 + i * 0.03)

            y_pos = max(content_h, scroll_h) - (num_attrs + 1) * row_h
            new_k = bui.textwidget(
                parent=s.fx_attr_root, position=(0, y_pos + 5), size=(85, row_h - 5),
                text="new_attr", editable=True, h_align='left', v_align='center',
                maxwidth=80, glow_type=Const.GLOW, allow_clear_button=False,
                color=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
            )
            s.fx_attr_widgets.append(new_k)

            new_v = bui.textwidget(
                parent=s.fx_attr_root, position=(90, y_pos + 5), size=(120, row_h - 5),
                text="value", editable=True, h_align='left', v_align='center',
                maxwidth=100, glow_type=Const.GLOW, allow_clear_button=False,
                color=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
            )
            s.fx_attr_widgets.append(new_v)

            add_btn = bui.buttonwidget(
                parent=s.fx_attr_root, position=(215, y_pos + 5), size=(30, row_h - 5),
                label='+', on_activate_call=lambda: add_custom_attr(new_k, new_v),
                button_type='square', enable_sound=False,
                texture=Eval.TEXTURE(Const.SKIN), color=Color.BASE,
                opacity=0 if initial else Color.OPACITY,
                textcolor=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
            )
            s.fx_attr_widgets.append(add_btn)

            if initial:
                anim_scroll_kid(new_k, 0, y_pos + 5, delay + 0.1 + num_attrs * 0.03)
                anim_scroll_kid(new_v, 90, y_pos + 5, delay + 0.1 + num_attrs * 0.03)
                anim_scroll_kid(add_btn, 215, y_pos + 5, delay + 0.1 + num_attrs * 0.03)

        refresh_right_pane(initial=True)

        def collect_final_attrs():
            sync_edits()
            pos_tuple = (
                float(bui.textwidget(query=s.fx_pos_inputs[0]) or '0'),
                float(bui.textwidget(query=s.fx_pos_inputs[1]) or '0'),
                float(bui.textwidget(query=s.fx_pos_inputs[2]) or '0')
            )
            final_attrs = {'position': str(pos_tuple)}
            for key, val in s.current_fx_attrs.items():
                if val:
                    final_attrs[key] = to_eval(key, val)
            return final_attrs

        prv_on = False

        def do_prv():
            raw_attrs = collect_final_attrs()
            try:
                with bs.get_foreground_host_activity().context:
                    kw = {k: eval(v) for k, v in raw_attrs.items()}
                    bs.emitfx(**kw)
            except Exception as e:
                if prv_on:
                    do_preview()
                s.toast(Format.ERROR(e))
                Eval.SOUND(Const.BAD_SOUND).play()

        def do_preview():
            nonlocal prv_on
            if prv_on:
                prv_on = False
                bui.buttonwidget(prv_btn, label=Strings.PREVIEW)
                s.prv_fx = None
                return
            s.prv_fx = bui.AppTimer(0.1, do_prv, repeat=True)
            bui.buttonwidget(prv_btn, label=Strings.STOP)
            prv_on = True

        pos = (left_x - 3, s.window_marg)
        size = (145, 40)
        prv_btn = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.PREVIEW,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_preview
        )
        s.window_kids.append((prv_btn, pos, 50, delay + 0.1, ('size', ((0, size[1]), size))))

        def do_done():
            nam = bui.textwidget(query=name_text)
            if not nam:
                s.toast(Format.ERROR_EMPTY(Strings.NAME))
                Eval.SOUND(Const.BAD_SOUND).play()
                return

            try:
                final_attrs = collect_final_attrs()
                with bs.get_foreground_host_activity().context:
                    for key, val in final_attrs.items():
                        eval(val)
            except Exception as e:
                s.toast(Format.ERROR(e))
                Eval.SOUND(Const.BAD_SOUND).play()
                return

            final_data = {'name': nam, 'attrs': final_attrs}

            Eval.SOUND(Const.OK_SOUND).play()
            if edit and not load:
                data.update(final_data)
                bui.buttonwidget(s.stamp_kids[edit['order']], label=nam)
                s.dismiss_window()
                s.toast(Strings.INFO_SAVED)
            else:
                s.add_entry(final_data)

        done_pos = (sx - 105, s.window_marg)
        done_btn = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=done_pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.DONE,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_done
        )
        s.window_kids.append((done_btn, done_pos, 50, delay + 0.1, ('size', ((0, 40), (95, 40)))))

        s.window_trash = [s.fx_attr_widgets]
        return lambda: setattr(s, 'prv_fx', None)

    def error(s, e):
        Eval.SOUND(Const.BAD_SOUND).play()
        s.toast(Format.ERROR(e))

    MAP_GNODE_DEFAULTS = {
        'Hockey Stadium': {
            'floor_reflection': True, 'debris_friction': 0.3, 'debris_kill_height': -0.3,
            'tint': (1.2, 1.3, 1.33), 'ambient_color': (1.15, 1.25, 1.6),
            'vignette_outer': (0.66, 0.67, 0.73), 'vignette_inner': (0.93, 0.93, 0.95),
            'vr_camera_offset': (0, -0.8, -1.1), 'vr_near_clip': 0.5,
        },
        'Football Stadium': {
            'tint': (1.3, 1.2, 1.0), 'ambient_color': (1.3, 1.2, 1.0),
            'vignette_outer': (0.57, 0.57, 0.57), 'vignette_inner': (0.9, 0.9, 0.9),
            'vr_camera_offset': (0, -0.8, -1.1), 'vr_near_clip': 0.5,
        },
        'Bridgit': {
            'tint': (1.1, 1.2, 1.3), 'ambient_color': (1.1, 1.2, 1.3),
            'vignette_outer': (0.65, 0.6, 0.55), 'vignette_inner': (0.9, 0.9, 0.93),
        },
        'Big G': {
            'tint': (0.75, 0.8, 0.85), 'ambient_color': (0.75, 0.8, 0.85),
            'vignette_outer': (0.5, 0.48, 0.45), 'vignette_inner': (0.85, 0.85, 0.88),
        },
        'Roundabout': {
            'tint': (1.0, 1.05, 1.1), 'ambient_color': (1.0, 1.05, 1.1), 'shadow_ortho': True,
            'vignette_outer': (0.63, 0.65, 0.7), 'vignette_inner': (0.97, 0.95, 0.93),
        },
        'Monkey Face': {
            'tint': (1.1, 1.2, 1.2), 'ambient_color': (1.2, 1.3, 1.3),
            'vignette_outer': (0.60, 0.62, 0.66), 'vignette_inner': (0.97, 0.95, 0.93),
            'vr_camera_offset': (-1.4, 0, 0),
        },
        'Zigzag': {
            'tint': (1.0, 1.15, 1.15), 'ambient_color': (1.0, 1.15, 1.15),
            'vignette_outer': (0.57, 0.59, 0.63), 'vignette_inner': (0.97, 0.95, 0.93),
            'vr_camera_offset': (-1.5, 0, 0),
        },
        'The Pad': {
            'tint': (1.1, 1.1, 1.0), 'ambient_color': (1.1, 1.1, 1.0),
            'vignette_outer': (0.7, 0.65, 0.75), 'vignette_inner': (0.95, 0.95, 0.93),
        },
        'Doom Shroom': {
            'tint': (0.82, 1.10, 1.15), 'ambient_color': (0.9, 1.3, 1.1), 'shadow_ortho': False,
            'vignette_outer': (0.76, 0.76, 0.76), 'vignette_inner': (0.95, 0.95, 0.99),
        },
        'Lake Frigid': {
            'tint': (1, 1, 1), 'ambient_color': (1, 1, 1), 'shadow_ortho': True,
            'vignette_outer': (0.86, 0.86, 0.86), 'vignette_inner': (0.95, 0.95, 0.99),
            'vr_near_clip': 0.5,
        },
        'Tip Top': {
            'tint': (0.8, 0.9, 1.3), 'ambient_color': (0.8, 0.9, 1.3),
            'vignette_outer': (0.79, 0.79, 0.69), 'vignette_inner': (0.97, 0.97, 0.99),
        },
        'Crag Castle': {
            'shadow_ortho': True, 'shadow_offset': (0, 0, -5.0),
            'tint': (1.15, 1.05, 0.75), 'ambient_color': (1.15, 1.05, 0.75),
            'vignette_outer': (0.6, 0.65, 0.6), 'vignette_inner': (0.95, 0.95, 0.95),
            'vr_near_clip': 1.0,
        },
        'Tower D': {
            'tint': (1.15, 1.11, 1.03), 'ambient_color': (1.2, 1.1, 1.0),
            'vignette_outer': (0.7, 0.73, 0.7), 'vignette_inner': (0.95, 0.95, 0.95),
        },
        'Happy Thoughts': {
            'happy_thoughts_mode': True, 'shadow_offset': (0.0, 8.0, 5.0),
            'tint': (1.3, 1.23, 1.0), 'ambient_color': (1.3, 1.23, 1.0),
            'vignette_outer': (0.64, 0.59, 0.69), 'vignette_inner': (0.95, 0.95, 0.93),
            'vr_near_clip': 1.0,
        },
        'Step Right Up': {
            'tint': (1.2, 1.1, 1.0), 'ambient_color': (1.2, 1.1, 1.0),
            'vignette_outer': (0.7, 0.65, 0.75), 'vignette_inner': (0.95, 0.95, 0.93),
        },
        'Courtyard': {
            'tint': (1.2, 1.17, 1.1), 'ambient_color': (1.2, 1.17, 1.1),
            'vignette_outer': (0.6, 0.6, 0.64), 'vignette_inner': (0.95, 0.95, 0.93),
        },
        'Rampage': {
            'tint': (1.2, 1.1, 0.97), 'ambient_color': (1.3, 1.2, 1.03),
            'vignette_outer': (0.62, 0.64, 0.69), 'vignette_inner': (0.97, 0.95, 0.93),
        },
    }

    def change_map(s, ma, extra={}):
        from bascenev1lib.gameutils import SharedObjects
        _act = bs.get_foreground_host_activity()
        old_map = _act.map
        cls = bs.get_map_class(ma)
        with _act.context:
            if type(old_map) in _act.preloads:
                del _act.preloads[type(old_map)]
            for attr in dir(old_map):
                if not attr.startswith('_') and attr not in ['node', 'activity', 'getactivity', 'handlemessage', 'on_expire', 'autoretain', 'is_alive', 'exists']:
                    try:
                        val = getattr(old_map, attr)
                        if not callable(val):
                            if hasattr(val, 'delete') and hasattr(val, 'exists'):
                                try:
                                    if val.exists():
                                        val.delete()
                                except Exception:
                                    pass
                            delattr(old_map, attr)
                    except Exception:
                        pass
            _act.preloads[cls] = cls.on_preload()
            preload = _act.preloads[cls]
            shared = SharedObjects.get()
            for node in bs.getnodes():
                if node.getnodetype() == 'terrain' and node != old_map.node:
                    try:
                        node.delete()
                    except Exception:
                        pass
            for attr in ['bottom', 'floor', 'stands', 'background', 'railing', 'bg_collide', 'stem', 'player_wall', 'bg2', 'node_bottom']:
                if hasattr(old_map, attr):
                    delattr(old_map, attr)
            if hasattr(old_map, 'node') and old_map.node:
                old_map.node.mesh = preload.get('mesh') or preload.get(
                    'mesh_top') or preload.get('meshes', [None])[0]
                old_map.node.color_texture = preload['tex']
                old_map.node.collision_mesh = preload['collision_mesh']
                if 'ice_material' in preload:
                    old_map.node.materials = [shared.footing_material, preload['ice_material']]
                else:
                    old_map.node.materials = [shared.footing_material]
            if 'mesh_bottom' in preload or 'bottom_mesh' in preload:
                old_map.bottom = bs.newnode('terrain', attrs={'mesh': preload.get('mesh_bottom') or preload.get(
                    'bottom_mesh'), 'lighting': False, 'color_texture': preload['tex']})
            if 'meshes' in preload and len(preload['meshes']) > 1:
                mats = [shared.footing_material, preload['ice_material']
                        ] if 'ice_material' in preload else [shared.footing_material]
                old_map.floor = bs.newnode('terrain', attrs={
                                           'mesh': preload['meshes'][1], 'color_texture': preload['tex'], 'opacity': 0.92, 'opacity_in_low_or_medium_quality': 1.0, 'materials': mats})
            if 'meshes' in preload and len(preload['meshes']) > 2:
                old_map.stands = bs.newnode('terrain', attrs={
                                            'mesh': preload['meshes'][2], 'visible_in_reflections': False, 'color_texture': preload.get('stands_tex', preload['tex'])})
            if 'mesh_bg' in preload or 'bgmesh' in preload:
                old_map.background = bs.newnode('terrain', attrs={'mesh': preload.get('mesh_bg') or preload.get(
                    'bgmesh'), 'lighting': False, 'background': True, 'color_texture': preload.get('mesh_bg_tex') or preload.get('bgtex')})
            if 'bgmesh2' in preload:
                old_map.bg2 = bs.newnode('terrain', attrs={
                                         'mesh': preload['bgmesh2'], 'lighting': False, 'background': True, 'color_texture': preload.get('bgtex2', preload.get('tex'))})
            if 'railing_collision_mesh' in preload or 'bumper_collision_mesh' in preload:
                old_map.railing = bs.newnode('terrain', attrs={'collision_mesh': preload.get('railing_collision_mesh') or preload.get(
                    'bumper_collision_mesh'), 'materials': [shared.railing_material], 'bumper': True})
            if 'collide_bg' in preload:
                old_map.bg_collide = bs.newnode('terrain', attrs={'collision_mesh': preload['collide_bg'], 'materials': [
                                                shared.footing_material, preload.get('bg_material'), shared.death_material]})
            if 'stem_mesh' in preload:
                old_map.stem = bs.newnode(
                    'terrain', attrs={'mesh': preload['stem_mesh'], 'lighting': False, 'color_texture': preload['tex']})
            if 'player_wall_collision_mesh' in preload and isinstance(bs.getsession(), bs.CoopSession):
                old_map.player_wall = bs.newnode('terrain', attrs={
                    'collision_mesh': preload['player_wall_collision_mesh'],
                    'affect_bg_dynamics': False,
                    'materials': [preload['player_wall_material']],
                })
            old_map.preloaddata = preload
            old_map.defs = cls.defs
            old_map.is_hockey = hasattr(cls, 'is_hockey') or cls.name in [
                'Hockey Stadium', 'Lake Frigid']
            old_map.is_flying = cls.name == 'Happy Thoughts'
            gnode = _act.globalsnode
            aoi_bounds = old_map.get_def_bound_box(
                'area_of_interest_bounds') or (-1, -1, -1, 1, 1, 1)
            gnode.area_of_interest_bounds = aoi_bounds
            map_bounds = old_map.get_def_bound_box('map_bounds') or (-30, -10, -30, 30, 100, 30)
            bs.set_map_bounds(map_bounds)
            if not hasattr(s, '_gnode_engine_defaults'):
                s._gnode_engine_defaults = {}
                all_gnode_keys = set()
                for d in s.MAP_GNODE_DEFAULTS.values():
                    all_gnode_keys.update(d.keys())
                for key in all_gnode_keys:
                    try:
                        s._gnode_engine_defaults[key] = getattr(gnode, key)
                    except Exception:
                        pass
            for key, default_val in s._gnode_engine_defaults.items():
                try:
                    setattr(gnode, key, default_val)
                except Exception:
                    pass
            for attr, val in s.MAP_GNODE_DEFAULTS.get(cls.name, {}).items():
                try:
                    setattr(gnode, attr, val)
                except Exception:
                    pass
            for key, val in extra.items():
                try:
                    v = eval(val)
                    if hasattr(old_map, key):
                        setattr(old_map, key, v)
                    elif hasattr(gnode, key):
                        setattr(gnode, key, v)
                    elif old_map.node and hasattr(old_map.node, key):
                        setattr(old_map.node, key, v)
                    else:
                        raise AttributeError(
                            f"'{key}' is not a valid attribute on the map, "
                            f"globals, or map node"
                        )
                except Exception as e:
                    bui.pushcall(
                        bui.CallPartial(
                            s.error, e
                        ), raw=True
                    )

    def make_map_window(s, edit=None, load=False):
        x, y = s.window_pos
        sx, sy = s.window_size
        text_push = 15
        delay = 0.35
        data = edit and edit['data']
        _act = bs.get_foreground_host_activity()

        assert bui.app.classic is not None
        map_names = sorted(bui.app.classic.maps.keys())

        old_ma = s.original_map
        try:
            start_ma = bs.get_filtered_map_name(data['map'] if data else old_ma)
        except Exception:
            start_ma = old_ma
        if start_ma not in map_names and map_names:
            start_ma = map_names[0]
        s.current_map_name = start_ma

        s.current_map_attrs = {}
        if data and 'attrs' in data:
            s.current_map_attrs = {k: str(v) for k, v in data['attrs'].items()}
        else:
            start_cls = bs.get_map_class(start_ma)
            s.current_map_attrs = {
                k: str(v) for k, v in s.MAP_GNODE_DEFAULTS.get(start_cls.name, {}).items()
            }

        left_x = 10

        pos_lbl = (left_x, sy - 85)
        w = bui.textwidget(parent=s.root, position=pos_lbl, size=(50, 30), text=list(
            Strings.EVENTS)[4], color=Const.INVISIBLE, maxwidth=140, h_align='left')
        s.window_kids.append((w, pos_lbl, text_push, delay))

        list_x = left_x
        list_y = 50
        list_w = 150
        list_h = sy - 145

        map_scroll = bui.scrollwidget(
            parent=s.root,
            position=(list_x, list_y),
            color=Color.BASE,
            size=(list_w / 2, 0),
            border_opacity=0
        )
        s.window_kids.append((map_scroll, (list_x, list_y), 20, delay,
                              ('size', ((0, list_h), (list_w, list_h))),
                              ('border_opacity', (0, Color.OPACITY)),
                              ('color', (Color.COLD, Color.BASE))
                              ))
        s.map_list_root = bui.containerwidget(parent=map_scroll, background=False)

        row_h = 32
        s.map_list_buttons = {}
        prv_state = {'on': False}

        def select_map(name):
            Eval.SOUND(Const.OK_SOUND).play()
            s.current_map_name = name
            for nm, btn in s.map_list_buttons.items():
                bui.buttonwidget(edit=btn, color=Color.BASE if nm != name else Color.COLD)

            cls = bs.get_map_class(name)
            s.current_map_attrs = {
                k: str(v) for k, v in s.MAP_GNODE_DEFAULTS.get(cls.name, {}).items()
            }
            refresh_right_pane(initial=False)
            if prv_state['on']:
                sync_edits()
                try:
                    s.change_map(s.current_map_name, extra=s.current_map_attrs)
                except Exception as e:
                    Eval.SOUND(Const.BAD_SOUND).play()
                    s.toast(Format.ERROR(e))

        content_h = max(len(map_names) * row_h, list_h)
        bui.containerwidget(edit=s.map_list_root, size=(list_w, content_h))
        for i, name in enumerate(map_names):
            y_pos = content_h - (i + 1) * row_h
            btn = bui.buttonwidget(
                parent=s.map_list_root,
                position=(0, y_pos),
                size=(list_w - 10, row_h - 4),
                label=name,
                color=Color.COLD if name == s.current_map_name else Color.BASE,
                textcolor=(*Color.TEXT, Color.TEXT_OPACITY),
                texture=Eval.TEXTURE(Const.SKIN),
                enable_sound=False,
                opacity=Color.OPACITY,
                on_activate_call=bui.CallPartial(select_map, name)
            )
            s.map_list_buttons[name] = btn

        scroll_x = 170
        scroll_y = 50
        scroll_w = sx - scroll_x - 10
        scroll_h = 195

        attr_scroll = bui.scrollwidget(
            parent=s.root,
            position=(scroll_x, scroll_y),
            color=Color.BASE,
            size=(scroll_w / 2, 0),
            border_opacity=0
        )
        s.window_kids.append((attr_scroll, (scroll_x, scroll_y), 20, delay,
                              ('size', ((0, scroll_h), (scroll_w, scroll_h))),
                              ('border_opacity', (0, Color.OPACITY)),
                              ('color', (Color.COLD, Color.BASE))
                              ))
        s.map_attr_root = bui.containerwidget(parent=attr_scroll, background=False)

        s.map_attr_widgets = []
        s.map_current_inputs = {}

        def anim_scroll_kid(w, px, py, dt):
            if (anim := s.anims.get(id(w), {}).get('scroll')):
                anim.cancel()
            ty = w.get_widget_type()
            attrs = {'position': ((px + 50, py), (px, py))}
            if ty == 'text':
                attrs['color'] = (Const.INVISIBLE, (*Color.TEXT, Color.TEXT_OPACITY))
            elif ty == 'button':
                attrs['opacity'] = (0, Color.OPACITY)
                attrs['textcolor'] = (Const.INVISIBLE, (*Color.TEXT, Color.TEXT_OPACITY))
            s.anims[id(w)]['scroll'] = Animate(widget=w, attrs=attrs, duration=0.18, delay=dt)

        def sync_edits():
            for key, wid in s.map_current_inputs.items():
                s.current_map_attrs[key] = bui.textwidget(query=wid)

        def add_custom_attr(k_wid, v_wid):
            sync_edits()
            k = bui.textwidget(query=k_wid).strip()
            v = bui.textwidget(query=v_wid).strip()
            if not k:
                s.toast(Format.ERROR_EMPTY(Strings.ATTR))
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            try:
                with bs.get_foreground_host_activity().context:
                    eval(v)
            except Exception as e:
                s.toast(Format.ERROR(e))
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            s.current_map_attrs[k] = v
            Eval.SOUND(Const.OK_SOUND).play()
            refresh_right_pane()

        def delete_attr(k):
            sync_edits()
            if k in s.current_map_attrs:
                del s.current_map_attrs[k]
            Eval.SOUND(Const.OK_SOUND).play()
            refresh_right_pane()

        def refresh_right_pane(initial=False):
            for w in s.map_attr_widgets:
                w.delete()
            s.map_attr_widgets.clear()
            s.map_current_inputs.clear()

            row_h2 = 35
            num_attrs = len(s.current_map_attrs)
            content_h2 = (num_attrs + 1) * row_h2

            bui.containerwidget(edit=s.map_attr_root, size=(250, max(content_h2, scroll_h)))

            keys = list(s.current_map_attrs.keys())
            for i, k in enumerate(keys):
                y_pos = max(content_h2, scroll_h) - (i + 1) * row_h2

                lbl = bui.textwidget(
                    parent=s.map_attr_root, position=(0, y_pos), size=(85, row_h2),
                    text=k, h_align='left', v_align='center', maxwidth=80,
                    color=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
                )
                s.map_attr_widgets.append(lbl)

                val = str(s.current_map_attrs[k])
                inp = bui.textwidget(
                    parent=s.map_attr_root, position=(90, y_pos + 5), size=(120, row_h2 - 5),
                    text=val, editable=True, h_align='left', v_align='center',
                    maxwidth=100, glow_type=Const.GLOW, allow_clear_button=False,
                    color=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
                )
                s.map_attr_widgets.append(inp)
                s.map_current_inputs[k] = inp

                del_btn = bui.buttonwidget(
                    parent=s.map_attr_root, position=(215, y_pos + 5), size=(30, row_h2 - 5),
                    label='-', on_activate_call=bui.CallPartial(delete_attr, k),
                    button_type='square', enable_sound=False,
                    texture=Eval.TEXTURE(Const.SKIN), color=Color.BASE,
                    opacity=0 if initial else Color.OPACITY,
                    textcolor=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
                )
                s.map_attr_widgets.append(del_btn)

                if initial:
                    anim_scroll_kid(lbl, 0, y_pos, delay + 0.1 + i * 0.03)
                    anim_scroll_kid(inp, 90, y_pos + 5, delay + 0.1 + i * 0.03)
                    anim_scroll_kid(del_btn, 215, y_pos + 5, delay + 0.1 + i * 0.03)

            y_pos = max(content_h2, scroll_h) - (num_attrs + 1) * row_h2
            new_k = bui.textwidget(
                parent=s.map_attr_root, position=(0, y_pos + 5), size=(85, row_h2 - 5),
                text="new_attr", editable=True, h_align='left', v_align='center',
                maxwidth=80, glow_type=Const.GLOW, allow_clear_button=False,
                color=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
            )
            s.map_attr_widgets.append(new_k)

            new_v = bui.textwidget(
                parent=s.map_attr_root, position=(90, y_pos + 5), size=(120, row_h2 - 5),
                text="value", editable=True, h_align='left', v_align='center',
                maxwidth=100, glow_type=Const.GLOW, allow_clear_button=False,
                color=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
            )
            s.map_attr_widgets.append(new_v)

            add_btn = bui.buttonwidget(
                parent=s.map_attr_root, position=(215, y_pos + 5), size=(30, row_h2 - 5),
                label='+', on_activate_call=lambda: add_custom_attr(new_k, new_v),
                button_type='square', enable_sound=False,
                texture=Eval.TEXTURE(Const.SKIN), color=Color.BASE,
                opacity=0 if initial else Color.OPACITY,
                textcolor=Const.INVISIBLE if initial else (*Color.TEXT, Color.TEXT_OPACITY)
            )
            s.map_attr_widgets.append(add_btn)

            if initial:
                anim_scroll_kid(new_k, 0, y_pos + 5, delay + 0.1 + num_attrs * 0.03)
                anim_scroll_kid(new_v, 90, y_pos + 5, delay + 0.1 + num_attrs * 0.03)
                anim_scroll_kid(add_btn, 215, y_pos + 5, delay + 0.1 + num_attrs * 0.03)

        refresh_right_pane(initial=True)

        def do_preview():
            if prv_state['on']:
                prv_state['on'] = False
                bui.buttonwidget(prv_btn, label=Strings.PREVIEW)
                s.change_map(old_ma)
                Eval.SOUND(Const.OK_SOUND).play()
                return
            sync_edits()
            try:
                s.change_map(s.current_map_name, extra=s.current_map_attrs)
            except Exception as e:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Format.ERROR(e))
                return
            Eval.SOUND(Const.OK_SOUND).play()
            bui.buttonwidget(prv_btn, label=Strings.STOP)
            prv_state['on'] = True

        pos = (left_x - 3, s.window_marg)
        size = (145, 40)
        prv_btn = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.PREVIEW,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_preview
        )
        s.window_kids.append((prv_btn, pos, 50, delay + 0.1, ('size', ((0, size[1]), size))))

        def do_done():
            sync_edits()
            Eval.SOUND(Const.OK_SOUND).play()
            final_data = {
                'map': s.current_map_name,
                'attrs': dict(s.current_map_attrs),
                'name': list(Strings.EVENTS)[4]
            }
            if edit and not load:
                data.update(final_data)
                s.dismiss_window()
                s.toast(Strings.INFO_SAVED)
            else:
                s.add_entry(final_data, smol=True)

        done_pos = (sx - 105, s.window_marg)
        done_btn = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=done_pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.DONE,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_done
        )
        s.window_kids.append((done_btn, done_pos, 50, delay + 0.1, ('size', ((0, 40), (95, 40)))))

        s.window_trash = [s.map_attr_widgets, s.map_list_buttons]

        return lambda: s.change_map(old_ma)

    def make_preset_window(s, edit=None, load=False):
        x, y = s.window_pos
        sx, sy = s.window_size
        text_push = 15
        delay = 0.35

        size = dx, dy = (sx/2 - s.window_marg*3, sy - s.window_marg*9)
        pos = px, py = (s.window_marg - s.window_fix, s.window_marg - s.window_fix)
        preset_scroll = bui.scrollwidget(
            parent=s.root,
            position=pos,
            color=Color.BASE,
            size=(dx/2, 0),
            border_opacity=0
        )
        s.window_kids.append((preset_scroll, pos, 20, delay + 0,
                              ('size', ((0, size[1]), size)),
                              ('border_opacity', (0, Color.OPACITY)),
                              ('color', (Color.COLD, Color.BASE))
                              ))

        preset_root = bui.containerwidget(
            parent=preset_scroll,
            background=False
        )

        sl = None

        def do_select(i, j, nam, dsc, data):
            nonlocal sl
            sl = (j, data)
            bui.textwidget(
                title_text,
                text=nam
            )
            bui.textwidget(
                desc_text,
                text=dsc
            )

        text_y = 30
        preset_texts = []

        presets = get_presets()
        rsy = max(len(presets) * text_y, dy - 15)
        for i, g in enumerate(presets, start=1):
            j, nam, dsc, data = g
            w = bui.textwidget(
                parent=preset_root,
                size=(dx, text_y),
                position=(0, rsy - i * text_y),
                maxwidth=dx - 25,
                selectable=True,
                glow_type=Const.GLOW,
                click_activate=True,
                text=nam,
                color=(*Color.TEXT, Color.TEXT_OPACITY),
                v_align=Const.ALIGN,
                on_activate_call=bui.CallPartial(
                    do_select, i, j, nam, dsc, data
                )
            )
            preset_texts.append(w)

        bui.containerwidget(
            preset_root,
            size=(dx, rsy)
        )

        title_pos = (sx/2 + s.window_marg, sy - s.window_marg - 80)
        title_text = bui.textwidget(
            parent=s.root,
            position=title_pos,
            text=Strings.PRESET_PLACEHOLDER,
            color=Const.INVISIBLE,
            maxwidth=sx/2 - s.window_marg*2,
            scale=1.2
        )
        s.window_kids.append((title_text, title_pos, text_push, delay + 0.1))

        desc_pos = (sx/2 + s.window_marg, sy - s.window_marg - 120)
        desc_text = bui.textwidget(
            parent=s.root,
            position=desc_pos,
            text=Strings.DESCRIPTION_HERE,
            color=Const.INVISIBLE,
            maxwidth=sx/2 - s.window_marg*2,
        )
        s.window_kids.append((desc_text, desc_pos, text_push, delay + 0.1))

        by = 40

        def do_load():
            Eval.SOUND(Const.OK_SOUND).play()
            s.event_window(sl[0], edit=sl[1], load=True)
        load_pos = (sx - (dx + s.window_marg*2), s.window_marg)
        load_button = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=load_pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.LOAD,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_load
        )
        s.window_kids.append((load_button, load_pos, 50, delay + 0.2,
                              ('size', ((0, by), (sx/2 - s.window_marg*2, by)))
                              ))

        s.window_trash = [preset_texts]

    def make_code_window(s, edit=None, load=False, on_done=None, initial_code=None):
        x, y = s.window_pos
        sx, sy = s.window_size
        delay = 0.35
        by = 40
        data = edit and edit['data']

        size = dx, dy = (sx+4, sy - s.window_marg*13-by)
        pos = px, py = (s.window_marg - s.window_fix, s.window_marg*4 - s.window_fix + by)
        code_scroll = bui.scrollwidget(
            parent=s.root,
            position=pos,
            color=Color.BASE,
            size=(dx/2, 0),
            border_opacity=0
        )
        s.window_kids.append((code_scroll, pos, 20, delay + 0,
                              ('size', ((0, size[1]), size)),
                              ('border_opacity', (0, Color.OPACITY)),
                              ('color', (Color.COLD, Color.BASE))
                              ))

        code_root = bui.containerwidget(
            parent=code_scroll,
            background=False
        )

        text_y = 30
        code_texts = []

        def make_text(**k):
            code_texts.append(
                bui.textwidget(
                    parent=code_root,
                    editable=True,
                    v_align=Const.ALIGN,
                    allow_clear_button=False,
                    size=(dx, text_y),
                    maxwidth=dx-20,
                    **k
                )
            )
            sync_texts()

        def sync_texts():
            ry = len(code_texts)*text_y
            for i, w in enumerate(code_texts, start=1):
                bui.textwidget(w, position=(0, ry-i*text_y))
            bui.containerwidget(code_root, size=(dx, ry), visible_child=w)

        make_text()

        def code_spy():
            t1 = bui.textwidget(query=code_texts[-1])
            t2 = bui.textwidget(query=code_texts[-2]) if len(code_texts) > 1 else True
            if t1:
                make_text()
            if not t1 and not t2:
                code_texts.pop(-1).delete()
                sync_texts()

        def start_spy(): return bui.AppTimer(
            0.02, code_spy, repeat=True
        )
        code_timer = start_spy()

        def get_code():
            code = '\n'.join(
                bui.textwidget(
                    query=t
                )
                for t in code_texts
            )
            if not code:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Strings.ERROR_EMPTY_CODE)
            return code

        def load_code(code):
            if not code:
                return
            code = code.split('\n')
            tail = code_texts[-1]
            if not bui.textwidget(query=tail):
                bui.textwidget(tail, text=code.pop(0))
            for l in code:
                make_text(text=l)
        running = False
        runner = None
        final = None

        def do_btn(i, btn):
            if i == 0:
                if (code := get_code()):
                    bui.clipboard_set_text(code)
                    Eval.SOUND(Const.GOOD_SOUND).play()
                    s.toast(Strings.INFO_COPIED)
            if i == 1:
                if not (t := ba.clipboard_get_text()):
                    Eval.SOUND(Const.BAD_SOUND).play()
                    s.toast(Strings.INFO_NO_CLIPBOARD)
                    return
                load_code(t)
                Eval.SOUND(Const.ACTION_SOUND).play()
                s.toast(Strings.INFO_PASTED)
            if i == 2:
                nonlocal running, runner
                if running:
                    running = False
                    bui.buttonwidget(btn, label=Strings.RUN)
                    runner.on_end()
                    runner = None
                    Eval.SOUND(Const.OK_SOUND).play()
                    return
                elif (code := get_code()):
                    running = True
                    bui.buttonwidget(btn, label=Strings.STOP)
                    runner = CodeRunner(
                        on_error=lambda e: (
                            s.toast(
                                Format.ERROR(e)
                            )
                        )
                    )
                    runner.on_start(code)
                    Eval.SOUND(Const.OK_SOUND).play()
            if i == 3:
                if not (code := get_code()):
                    return
                runner and runner.on_end()
                head = bui.textwidget(query=code_texts[0])
                na = Strings.CODE
                if head.startswith(Const.CONFIG_HEAD):
                    na = head.split(Const.CONFIG_HEAD, 1)[1] or na
                nonlocal final
                final = {
                    'code': code,
                    'name': na
                }
                if edit and not load:
                    data.update(final)
                    bui.buttonwidget(
                        s.stamp_kids[edit['order']],
                        label=na
                    )
                    s.dismiss_window()
                    s.toast(Strings.INFO_SAVED)
                elif not callable(on_done):
                    s.add_entry(final)
                else:
                    s.dismiss_window()
                    on_done(final)
        for i, t in enumerate((
            Strings.COPY,
            Strings.PASTE,
            Strings.RUN,
            Strings.DONE
        )):
            btn_pos = (s.window_marg - 4 + (sx/4 + s.window_marg)*i, s.window_marg)
            btn = bui.buttonwidget(
                parent=s.root,
                size=(0, 0),
                position=btn_pos,
                texture=Eval.TEXTURE(Const.SKIN),
                color=Color.BASE,
                enable_sound=False,
                label=t,
                textcolor=Const.INVISIBLE
            )
            bui.buttonwidget(
                btn,
                on_activate_call=bui.CallPartial(
                    do_btn, i, btn
                )
            )
            s.window_kids.append((btn, btn_pos, 50, delay + i*0.1,
                                  ('size', ((0, by), (sx/4 - s.window_marg*4, by)))
                                  ))

        s.window_trash = [code_texts]
        if data:
            load_code(data.get('code'))
        elif initial_code:
            load_code(initial_code)

        def cleanup():
            nonlocal code_timer
            code_timer = None
            runner and runner.on_end()
        return cleanup

    def make_seed_window(s, edit=None, load=False):
        x, y = s.window_pos
        sx, sy = s.window_size
        text_push = 15
        delay = 0.35
        data = edit and edit['data']
        bx = sx - s.window_marg*8
        by = 40

        pos = (s.window_marg, sy-(by+s.window_marg*10))
        tip = bui.textwidget(
            parent=s.root,
            position=pos,
            maxwidth=sx-s.window_marg*4,
            max_height=sy-(by*2+s.window_marg*14),
            text=Strings.SEED_TIP,
            color=Const.INVISIBLE
        )
        s.window_kids.append((tip, pos, text_push, delay+0))

        pos = (s.window_marg*2+2, s.window_marg*4+by)
        seed_inp = bui.textwidget(
            parent=s.root,
            position=pos,
            editable=True,
            allow_clear_button=False,
            size=(0, 0),
            maxwidth=(bx+20)-s.window_marg*2,
            description=Strings.SEED_HELP,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            glow_type=Const.GLOW,
            text=data and data['seed'] or ''
        )
        s.window_kids.append((seed_inp, pos, text_push, delay+0,
                              ('size', ((bx/2, by), (bx+20, by)))
                              ))

        def do_done():
            seed = bui.textwidget(query=seed_inp)
            if not seed:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Format.ERROR_EMPTY(Strings.SEED))
                return
            final = {
                'seed': seed,
                'name': Strings.SEED
            }
            if edit:
                data.update(final)
                s.dismiss_window()
                s.toast(Strings.INFO_SAVED)
            else:
                s.add_entry(final)
        done_pos = (s.window_marg*4, s.window_marg)
        done_button = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=done_pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.DONE,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_done
        )
        s.window_kids.append((done_button, done_pos, 50, delay + 0.2,
                              ('size', ((bx/2, by), (bx, by)))
                              ))

    def window_clean(s):
        for w, *_ in s.window_kids:
            s.anims[id(w)].reverse(
                duration=0.1,
                on_finish=w.delete,
                on_cancel=w.delete
            )
        s.window_kids.clear()
        for l in s.window_trash:
            for w in (
                l if isinstance(l, list)
                else l.values()
            ):
                w.delete()
        s.window_trash.clear()
        if getattr(s, 'forgive_prev_off', False):
            s.forgive_prev_off = False
        else:
            getattr(s, 'prev_off_wid', None) and s.prev_off_wid.delete()

    def dismiss_window(s, **kw):
        """Fully closes whatever window is open, popup included, in
        one call. window_back() on its own only peels off one layer -
        if a popup is open it closes *that* and returns, leaving
        window_on untouched, which is exactly the right feel for an
        actual back-button press (first press dismisses the popup,
        second press leaves the window). But every call site that
        means to open something else next - a different window, a
        select/delete action, toggling event view - wants the whole
        trap gone unconditionally. Calling window_back() alone there
        closes the popup but silently leaves window_on non-empty, so
        the window itself never gets torn down even though nothing
        appears to be covering it anymore. Route all of those through
        here instead so a live popup can never survive an attempt to
        open (or otherwise move past) a window."""
        if s.window_sub_on:
            s.window_sub_on[2](instant=True)
        if s.window_on:
            s.window_back(**kw)

    def window_back(s, to=None, shadow_to=None, on_fix=None, wait=0, extra={}, shadow_extra={}, instant={}, into_nothing=False, skip=False):
        if s.window_sub_on:
            s.window_sub_on[2]()
            return
        b, call, on_back = s.window_on
        butter = s.global_butter*1.66
        anim = s.anims[id(b)]['window']
        s.window_on = ()
        callable(on_back) and on_back()

        def enable():
            bui.buttonwidget(
                b,
                on_activate_call=call,
                selectable=True
            )
        Eval.SOUND(Const.OK_SOUND).play()
        s.window_clean()
        if to:
            last_i = s.last_window_i

            def fix():
                for _ in ['extra', 'to', 'shadow']:
                    anim = s.anims[id(b)].pop(_, None)
                    if not anim:
                        continue
                    anim.cancel()
                if s.event_on:
                    ox, oy = (s.ev_x, s.event_top - s.ev_mult * (last_i+1))
                    anim = Animate(
                        widget=b,
                        duration=s.global_butter,
                        attrs={
                            'textcolor': (
                                Const.INVISIBLE,
                                (*Color.TEXT, Color.TEXT_OPACITY)
                            ),
                            'opacity': (0, Color.OPACITY),
                            'position': (
                                (ox-50, oy),
                                (ox, oy)
                            ),
                        }
                    )
                    s.anims[id(b)]['fix'] = anim
                    enable()
                bui.buttonwidget(
                    b,
                    size=s.event_kid_size,
                    opacity=0,
                    textcolor=Const.INVISIBLE,
                    label=list(Strings.EVENTS)[last_i],
                    text_scale=s.event_kid_ts
                )
                bui.imagewidget(
                    s.event_kids[b]['shadow'],
                    opacity=0
                )
                if callable(on_fix):
                    on_fix()

            def do_anim():
                anim = Animate(
                    widget=b,
                    attrs=to(),
                    duration=butter,
                    on_finish=fix,
                    on_cancel=fix
                )
                s.anims[id(b)]['to'] = anim
                s.anims[id(b)]['shadow'] = Animate(
                    widget=s.event_kids[b]['shadow'],

                    attrs=shadow_to(),
                    duration=butter
                )
            if wait:
                s.after_scroll_t = bui.AppTimer(wait, do_anim)
            else:
                do_anim()
            if extra:
                def nevermind():
                    s.after_scroll_t = None
                    anim.cancel()
                    fix()
                s.anims[id(b)]['extra'] = Animate(
                    widget=b,
                    duration=wait,
                    attrs=extra,
                    on_cancel=nevermind
                )
            if shadow_extra:
                s.anims[id(b)]['shadow'] = Animate(
                    widget=s.event_kids[b]['shadow'],
                    duration=wait,
                    attrs=shadow_extra
                )
            instant and bui.buttonwidget(
                b, **instant
            )
        else:
            zero = 0.0001
            s.anims[id(b)]['window'] = anim.reverse(
                duration=skip and zero or butter
            )
            anim = s.anims[id(b)]['shadow']
            s.anims[id(b)]['shadow'] = anim.reverse(
                duration=skip and zero or butter
            )
            enable()

    def show_controls(s, up=False):
        if s.controls_shown:
            return
        s.controls_shown = True
        if up:
            dx, dy = s.control_size
            end_size = (dx, 0)
            for i, b in enumerate(s.controls):
                for a in s.anims[id(b)].values():
                    a.cancel()
                px, py = s.control_pos(i)
                bui.buttonwidget(
                    b,
                    position=(px, py+dy),
                    size=end_size,
                    textcolor=Const.INVISIBLE,
                    opacity=0
                )
                attrs = {
                    'size': (
                        end_size,
                        s.control_size
                    ),
                    'textcolor': (
                        Const.INVISIBLE,
                        (*Color.TEXT, Color.TEXT_OPACITY)
                    ),
                    'opacity': (0, Color.OPACITY),
                    'position': (
                        (px, py+dy),
                        (px, py)
                    )
                }
                s.anims[id(b)][up] = Animate(
                    widget=b,
                    duration=s.global_butter,
                    attrs=attrs
                )
        else:
            dx, dy = s.control_size
            sx, sy = s.stamp_size
            start_size = (dx, dy/4)
            for i, b in enumerate(s.controls):
                bui.buttonwidget(
                    b, position=s.control_pos(i)
                )
                for a in s.anims[id(b)].values():
                    a.cancel()
                attrs = {
                    'size': (
                        start_size,
                        s.control_size
                    ),
                    'textcolor': (
                        Const.INVISIBLE,
                        (*Color.TEXT, Color.TEXT_OPACITY)
                    ),
                    'opacity': (0, Color.OPACITY)
                }
                s.anims[id(b)][up] = Animate(
                    widget=b,
                    duration=s.global_butter,
                    attrs=attrs
                )

    @ui_safe
    def hide_controls(s, up=False):
        if not s.controls_shown:
            return
        s.controls_shown = False
        if up:
            dx, dy = s.control_size
            sx, sy = s.stamp_size
            end_size = (dx, 0)
            for i, b in enumerate(s.controls):
                for a in s.anims[id(b)].values():
                    a.cancel()
                px, py = s.control_pos(i)
                attrs = {
                    'size': (
                        s.control_size,
                        end_size
                    ),
                    'textcolor': (
                        (*Color.TEXT, Color.TEXT_OPACITY),
                        Const.INVISIBLE
                    ),
                    'opacity': (Color.OPACITY, 0),
                    'position': (
                        (px, py),
                        (px, py+dy)
                    )
                }
                s.anims[id(b)][up] = Animate(
                    widget=b,
                    duration=s.global_butter,
                    attrs=attrs
                )
        else:
            for b in s.controls:
                s.anims[id(b)][up].reverse()

    def do_control(s, i):
        if (
           not s.ui_on or
           s.tools_shown or
           not s.controls_shown
           ):
            return
        r = None
        if i == 0:
            s.toggle_play()
        if i == 1:
            r = s.stop()
        Eval.SOUND(
            r is None and Const.OK_SOUND
            or Const.BAD_SOUND
        ).play()

    def toggle_play(s):
        if s.playing:
            s.pause()
        else:
            s.play()
        s.toast(
            s.playing
            and Strings.INFO_PLAYING
            or Strings.INFO_PAUSED
        )
        s.wrap_controls()

    def wrap_controls(s):
        bui.buttonwidget(
            s.controls[0],
            label=Eval.CHAR(
                Const.CONTROLS[0][s.playing]
            )
        )

    def pause(s):
        s.playing = False
        s.pause_start = perf_counter()
        s.freeze_scene()
        for sound in s.active_sounds:
            sound.volume = 0

    def freeze_scene(s, b=True):
        bs.get_foreground_host_activity().globalsnode.paused = b

    def stop(s, shut=0):
        if not s.play_timer:
            s.toast(Strings.ERROR_NOT_PLAYING)
            return False
        s.playing = False
        s.play_timer = None
        s.ui_clickable = True
        s.kill_playhead()
        s.wrap_play()
        s.wrap_controls()

        def clean_tracker(tracker):
            for _ in tracker.active.values():
                if _.exists():
                    _.delete()
            tracker.active.clear()

            for _ in tracker.active_sounds:
                if _.exists():
                    _.delete()
            tracker.active_sounds.clear()

            tracker.active_timers.clear()

            for t in getattr(tracker, 'internal_timers', []):
                t = None
            if hasattr(tracker, 'internal_timers'):
                tracker.internal_timers.clear()

            for _ in tracker.active_codes.values():
                (main := _.get('main')) and main.on_end()
                (children := _.get('children')) and [
                    child.on_end() for child in children
                ]
            tracker.active_codes.clear()

            for seed_tracker in tracker.active_seeds.values():
                clean_tracker(seed_tracker)
            tracker.active_seeds.clear()

        clean_tracker(s)

        shut or s.toast(Strings.INFO_FINISHED)
        s.freeze_scene(False)
        s.change_map(s.original_map)
        if s.camera_data:
            s.camera_timer = None
            s.camera_data.clear()
            _ba.set_camera_manual(False)
        if getattr(s, 'export_flag', False):
            s.export_flag = False
            s.export_replay()
        if s.is_wide:
            s.is_wide = False
            if not s.ui_on:
                s.toggle_ui()
        s.build_grid()

    def wrap_play(s, init=False):
        s.pause_start = None
        s.play_start = perf_counter() if init else None
        s.play_elapsed = 0
        s.paused_time = 0
        s.timeline_index = 0

    def play(s):
        s.freeze_scene(False)
        s.playing = True
        if s.play_timer:
            s.paused_time += perf_counter() - s.pause_start
            s.pause_start = None
            for sound, vol in s.active_sounds.items():
                setattr(sound, 'volume', vol)
            return
        s.destroy_grid()
        s.collapse_all()
        s.ui_clickable = False
        s.make_playhead()
        s.wrap_play(init=True)
        s.play_timer = bui.AppTimer(
            0.01, s.do_play, repeat=True
        )
        s.wrap_playhead()

    def do_play(s):
        if not s.playing:
            return
        s.play_elapsed = (
            s.pause_start - s.play_start - s.paused_time
        ) if s.pause_start else (
            perf_counter() - s.play_start - s.paused_time
        )

        while (
            s.timeline_index < len(s.timeline) and
            s.timeline[s.timeline_index]['time'] <= s.play_elapsed
        ):
            event = s.timeline[s.timeline_index]
            try:
                s.execute_event(event)
            except Exception as e:
                print(format_exc())
                t = event['memory']['data']['name']
                s.toast(Strings.ERROR_EVENT(t, e))
                Eval.SOUND(Const.BAD_SOUND).play()
                if not Settings.get('ignore_playback_errors'):
                    s.stop(shut=1)
                    return
                s.timeline_index += 1
                continue
            s.timeline_index += 1

        for btn_id, keys in list(s.active_key_schedule.items()):
            for key_info in keys[:]:
                if s.play_elapsed >= key_info['time']:
                    try:
                        s.execute_key(
                            key_info['data'],
                            key_info['btn_id'],
                            key_info['event_type']
                        )
                    except Exception as e:
                        mem = s.memory.get(btn_id)
                        name = mem['data']['name'] if mem else 'Unknown'
                        s.toast(Strings.ERROR_EVENT(f"{name} (Key)", e))
                        Eval.SOUND(Const.BAD_SOUND).play()

                    keys.remove(key_info)

            if not keys:
                del s.active_key_schedule[btn_id]

        if s.play_elapsed >= s.max_time:
            s.stop()
            return

        s.move_playhead()

    def execute_event(s, e, tracker=None):
        tracker = tracker or s

        mem = e['memory']
        key = e['btn_id']
        start = e['type'] == 'start'
        what = mem['event']
        data = mem['data']
        call = None

        if what == 0:
            if start:
                with bs.get_foreground_host_activity().context:
                    _shared = None
                    _factory = None
                    if data['type'] == 'spaz':
                        from bascenev1lib.gameutils import SharedObjects
                        from bascenev1lib.actor.spazfactory import SpazFactory
                        from bascenev1lib.actor.spaz import Spaz
                        _shared = SharedObjects.get()
                        _factory = SpazFactory.get()
                    attrs = {}
                    for attr, val in data['attrs'].items():
                        attrs[attr] = eval(val)
                    if data['type'] == 'spaz':
                        for extraneous in ('materials', 'roller_materials', 'punch_materials', 'pickup_materials', 'style'):
                            attrs.pop(extraneous, None)
                        position = attrs.pop('position', None)
                        actor = Spaz(
                            character=attrs.pop('character', None) or 'Spaz',
                            color=attrs.pop('color', (1, 1, 1)),
                            highlight=attrs.pop('highlight', (1, 1, 1)),
                            start_invincible=False
                        ).autoretain()
                        for k, v in attrs.items():
                            setattr(actor.node, k, v)
                        tracker.active[key] = n = actor.node
                        tracker.active_actors[key] = actor
                        if position is not None:
                            activity = bs.get_foreground_host_activity()

                            def call(activity=activity, position=position, actor=actor):
                                with activity.context:
                                    bs.timer(
                                        0,
                                        lambda: actor.node.exists() and actor.handlemessage(bs.StandMessage(position, 0.0))
                                    )
                    else:
                        tracker.active[key] = n = bs.newnode(
                            type=data['type'],
                            name=data['name'],
                            attrs=attrs
                        )
            else:
                if key in tracker.active:
                    tracker.active.pop(key).delete()
                tracker.active_actors.pop(key, None)
                if key in tracker.active_codes:
                    codes = tracker.active_codes.pop(key)
                    if 'main' in codes:
                        codes['main'].on_end()
                    for child in codes.get('children', []):
                        child.on_end()

        if what == 1:
            if start:
                has_pos, has_tar, man = data['chks']
                s.camera_data[key] = (
                    has_pos and data['position'],
                    has_tar and data['target'],
                    man
                )
                if not s.camera_timer:
                    def apply():
                        if not s.camera_data:
                            return
                        pos, tar, man = next(
                            reversed(
                                s.camera_data.values()
                            )
                        )
                        if apply.last_man != man:
                            apply.last_man = man
                            _ba.set_camera_manual(man)
                        pos and _ba.set_camera_position(
                            *pos
                        )
                        pos and _ba.set_camera_target(
                            *tar
                        )
                    apply.last_man = False
                    s.camera_timer = bui.AppTimer(
                        0.02, apply, repeat=True
                    )
                    apply()
            else:
                if key in s.camera_data:
                    man = s.camera_data.pop(key)[2]
                    if not s.camera_data:
                        s.camera_timer = None
                        man and _ba.set_camera_manual(False)
        if what == 2:
            if start:
                sound_name = data['file'].replace('.ogg', '')
                position = (data['x'], data['y'], data['z'])
                volume = data['volume']
                with bs.get_foreground_host_activity().context:
                    tracker.active[key] = n = bs.newnode(
                        'sound',
                        attrs={
                            'position': position,
                            'sound': bs.getsound(sound_name),
                            'volume': volume,
                            'positional': not data['chks'][0],
                            'loop': data['chks'][1]
                        }
                    )
                    tracker.active_sounds[n] = volume
            else:
                if key in tracker.active:
                    n = tracker.active.pop(key)
                    if n in tracker.active_sounds:
                        tracker.active_sounds.pop(n)
                    n.delete()

        if what == 3:
            if start:
                at = {
                    attr: eval(val)
                    for attr, val in data['attrs'].items()
                }
                delay = at.pop('delay', 0.1)

                def _emit():
                    with bs.get_foreground_host_activity().context:
                        bs.emitfx(**at)
                tracker.active_timers[key] = bs.AppTimer(
                    delay, _emit, repeat=True
                )
            else:
                if key in tracker.active_timers:
                    tracker.active_timers.pop(key)

        if what == 4:
            if start:
                s.change_map(data['map'], extra=data['attrs'])

        if what == 6:
            if start:
                tracker.active_codes[key]['main'] = runner = CodeRunner(
                    on_error=lambda e: (
                        s.toast(
                            Format.ERROR(e)
                        )
                    )
                )
                runner.on_start(data['code'])
                tracker.active_codes[key]['children'] = []
            else:
                if key in tracker.active_codes:
                    codes = tracker.active_codes.pop(key)
                    codes['main'].on_end()
                    for child in codes['children']:
                        child.on_end()

        if what == 7:
            if start:
                try:
                    seed_mem = Eval.DECODE(data['seed'])
                except Exception as ex:
                    s.toast(Format.ERROR(ex))
                    return

                sub_tracker = Tracker()
                tracker.active_seeds[key] = sub_tracker

                for seed_key, seed_entry in seed_mem.items():
                    start_ev = {
                        'memory': seed_entry,
                        'btn_id': seed_key,
                        'type': 'start'
                    }
                    end_ev = {
                        'memory': seed_entry,
                        'btn_id': seed_key,
                        'type': 'end'
                    }

                    t_start = bui.AppTimer(
                        seed_entry['start'],
                        bui.CallPartial(s.execute_event, start_ev, tracker=sub_tracker)
                    )
                    sub_tracker.internal_timers.append(t_start)

                    t_end = bui.AppTimer(
                        seed_entry['start'] + seed_entry['duration'],
                        bui.CallPartial(s.execute_event, end_ev, tracker=sub_tracker)
                    )
                    sub_tracker.internal_timers.append(t_end)

                    for k_name, k_data in seed_entry.get('keys', {}).items():
                        t_key = bui.AppTimer(
                            k_data['time'],
                            bui.CallPartial(
                                s.execute_key,
                                k_data,
                                seed_key,
                                seed_entry['event'],
                                sub_tracker
                            )
                        )
                        sub_tracker.internal_timers.append(t_key)

            else:
                if key in tracker.active_seeds:
                    sub_tracker = tracker.active_seeds.pop(key)

                    sub_tracker.internal_timers.clear()

                    def kill_scope(t):
                        for _ in t.active.values():
                            if _.exists():
                                _.delete()
                        t.active.clear()
                        t.active_actors.clear()
                        for _ in t.active_sounds:
                            if _.exists():
                                _.delete()
                        t.active_sounds.clear()
                        t.active_timers.clear()
                        for _ in t.active_codes.values():
                            (m := _.get('main')) and m.on_end()
                            (c := _.get('children')) and [x.on_end() for x in c]
                        t.active_codes.clear()
                        for k, v in t.active_seeds.items():
                            kill_scope(v)
                        t.active_seeds.clear()

                    kill_scope(sub_tracker)

        if e['type'] == 'start' and tracker == s:
            tracker.active_key_schedule[key] = []
            for key_name, key_data in mem.get('keys', {}).items():
                tracker.active_key_schedule[key].append({
                    'time': key_data['time'],
                    'data': key_data,
                    'btn_id': key,
                    'event_type': what
                })

        callable(call) and call()

    def execute_key(s, key_data, btn_id, event_type, tracker=None):
        tracker = tracker or s
        action = key_data['action']

        if action == 0:
            da = key_data['data']
            attr_name, attr_eval = da['attr'], da['eval']

            if btn_id in tracker.active:
                node = tracker.active[btn_id]
                if node.exists():
                    try:
                        _shared = None
                        _factory = None
                        if attr_name in (
                            'materials', 'roller_materials',
                            'punch_materials', 'pickup_materials'
                        ):
                            from bascenev1lib.gameutils import SharedObjects
                            from bascenev1lib.actor.spazfactory import SpazFactory
                            _shared = SharedObjects.get()
                            _factory = SpazFactory.get()
                        setattr(node, attr_name, eval(attr_eval))
                    except Exception as e:
                        s.toast(Format.ERROR(e))
                        Eval.SOUND(Const.BAD_SOUND).play()

        elif action == 1:
            if btn_id in tracker.active_codes and 'main' in tracker.active_codes[btn_id]:
                parent_runner = tracker.active_codes[btn_id]['main']
                child_runner = CodeRunner(
                    on_error=lambda e: s.toast(Format.ERROR(e)),
                    parent_runner=parent_runner
                )
                child_runner.on_start(key_data['data']['code'])
                tracker.active_codes[btn_id]['children'].append(child_runner)
            else:
                bot = tracker.active_actors.get(btn_id)
                runner = CodeRunner(
                    on_error=lambda e: s.toast(Format.ERROR(e)),
                    extra_namespace={'bot': bot} if bot is not None else None
                )
                runner.on_start(key_data['data']['code'])
                tracker.active_codes[btn_id].setdefault('children', []).append(runner)

        elif action == 2:
            da = key_data['data']
            v = da['volume']
            if btn_id in tracker.active:
                node = tracker.active[btn_id]
                if node.exists():
                    if not s.paused:
                        try:
                            node.volume = v
                        except Exception as e:
                            s.toast(Format.ERROR(e))
                            Eval.SOUND(Const.BAD_SOUND).play()
                    tracker.active_sounds[node] = v

        elif action == 3:
            da = key_data['data']
            if btn_id in tracker.active:
                node = tracker.active[btn_id]
                if node.exists():
                    try:
                        with bs.get_foreground_host_activity().context:
                            Bubble(
                                node,
                                text=da['text'],
                                color=eval(da['color']),
                                time=da['time']
                            )
                    except Exception as e:
                        s.toast(Format.ERROR(e))
                        Eval.SOUND(Const.BAD_SOUND).play()

    def make_playhead(s):
        s.playhead and s.playhead.delete()
        s.playhead = bui.imagewidget(
            parent=s.stamp_hscroll_root,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.WARM,
            opacity=Color.OPACITY
        )

    def move_playhead(s):
        bui.imagewidget(
            s.playhead,
            position=s.playhead_pos(s.play_elapsed)
        )
        bui.containerwidget(
            s.stamp_hscroll_root,
            visible_child=s.playhead
        )

    def wrap_playhead(s):
        s.playhead_pos = lambda i: (
            i*(s.entries_per_sec*s.entry_xs_real)+4,
            -s.stamp_deep_y/2
        )
        s.playhead_size = (2, s.stamp_deep_y*2)
        bui.imagewidget(
            s.playhead,
            size=s.playhead_size
        )
        s.move_playhead()

    def kill_playhead(s, instant=False):
        if instant:
            s.playhead.delete()
            return
        px, py = s.playhead_pos(s.play_elapsed)
        sx, sy = s.playhead_size
        end_sx = sx*100
        s.anims[id(s.playhead)] = Animate(
            widget=s.playhead,
            attrs={
                'size': (
                    (sx, sy),
                    (end_sx, sy)
                ),
                'opacity': (
                    Color.OPACITY*0.6,
                    0
                ),
                'position': (
                    (px, py),
                    (px-end_sx/2, py)
                )
            },
            duration=s.global_butter*2,
            on_finish=s.playhead.delete
        )

    @clickable
    def select(s, b):
        Eval.SOUND(Const.OK_SOUND).play()
        if s.window_on and s.window_on[1] in (
            s.edit_window,
            s.key_window
        ):
            s.dismiss_window()
        sl = b

        def yes(): return bui.buttonwidget(
            b, color=Color.COLD
        )

        def no(): return bui.buttonwidget(
            s.sl, color=Color.BASE
        )
        if s.sl == sl:
            no()
            s.hide_tools()
            s.show_controls(up=True)
            s.sl = None
            return
        if s.sl:
            no()
        s.hide_controls(up=True)
        s.show_tools()
        s.sl = sl
        yes()

    def show_tools(s):
        if s.tools_shown:
            return
        s.tools_shown = True
        xs, ys = s.tool_size
        start_size = (xs, ys/4)
        start_tc = Const.INVISIBLE
        start_op = 0
        for i, b in enumerate(s.tools):
            if (a := s.anims.get(id(b), None)):
                a.cancel()
            s.anims[id(b)] = Animate(
                widget=b,
                duration=s.global_butter,
                attrs={
                    'size': (
                        start_size,
                        s.tool_size
                    ),
                    'textcolor': (
                        start_tc,
                        (*Color.TEXT, Color.TEXT_OPACITY)
                    ),
                    'opacity': (start_op, Color.OPACITY)
                }
            )

    @ui_safe
    def hide_tools(s):
        if not s.tools_shown:
            return
        s.tools_shown = False
        for b in s.tools:
            s.anims[id(b)].reverse(
                duration=s.global_butter,
                on_finish=bui.CallPartial(
                    bui.buttonwidget,
                    b, size=(0, 0)
                )
            )

    @clickable
    def do_tool(s, which):
        if not s.tools_shown:
            return
        if not s.sl:
            return
        b = s.sl
        mem = s.memory[id(b)]
        if mem.get('smol', False) and which in [2, 3]:
            Eval.SOUND(Const.BAD_SOUND).play()
            s.toast(Strings.ERROR_SMOL_NO_RESIZE)
            return
        new = {}
        scroll_butter = s.global_butter/2

        def restamp(): return (
            s.wrap(2),
            s.make_timeline(),
            s.wrap_timeline()
        )
        start_size = Eval.ENTRY_SIZE(s, mem)
        start_pos = Eval.ENTRY_POS(s, mem)

        def animate_key_widgets(anim_key, key_old_positions):
            for key_data in mem.get('keys', {}).values():
                if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                    wid = s.widgets[key_data['widget']]
                    wid_id = id(wid)
                    key_time = key_data['time']

                    new_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                    new_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)

                    start_wid_pos = key_old_positions.get(wid_id, (new_x, new_y))

                    if wid_id in s.anims and anim_key in s.anims[wid_id]:
                        if (anim := s.anims[wid_id].get(anim_key, None)) and not anim.finished:
                            start_wid_pos = anim.attrs_current['position']
                            anim.cancel()

                    if wid_id not in s.anims:
                        s.anims[wid_id] = {}

                    s.anims[wid_id].pop(anim_key, None)

                    s.anims[wid_id][anim_key] = Animate(
                        widget=wid,
                        attrs={'position': (start_wid_pos, (new_x, new_y))},
                        duration=s.global_butter
                    )

        if which == 0:
            for key in [1, 2, 3]:
                if (anim := s.anims[id(b)].get(key, None)):
                    anim.cancel()
                    s.anims[id(b)].pop(key, None)

            if (anim := s.anims[id(b)].get(0, None)) and not anim.finished:
                start_pos = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(b)].pop(0, None)

            mem['start'] += 1/s.entries_per_sec

            key_old_positions = {}
            for key_data in mem.get('keys', {}).values():
                if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                    wid = s.widgets[key_data['widget']]
                    wid_id = id(wid)

                    if wid_id in s.anims and 1 in s.anims[wid_id]:
                        if (anim := s.anims[wid_id].get(1, None)) and not anim.finished:
                            key_old_positions[wid_id] = anim.attrs_current['position']
                            anim.cancel()
                            s.anims[wid_id].pop(1, None)
                        else:
                            old_x = s.magic_x + s.entry_xs_real * \
                                key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                            old_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                            key_old_positions[wid_id] = (old_x, old_y)
                    else:
                        old_x = s.magic_x + s.entry_xs_real * \
                            key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                        old_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                        key_old_positions[wid_id] = (old_x, old_y)

            for key_data in mem.get('keys', {}).values():
                key_data['time'] += 1/s.entries_per_sec

            end_pos = Eval.ENTRY_POS(s, mem)
            new['position'] = (start_pos, end_pos)

            animate_key_widgets(0, key_old_positions)

            if mem.get('prev_off_wid') and s.widgets[mem['prev_off_wid']].exists():
                wid_id = mem['prev_off_wid']

                for key in [1, 4, 5]:
                    if (anim := s.anims.get(wid_id, {}).get(key, None)):
                        anim.cancel()
                        s.anims[wid_id].pop(key, None)

                old_wid_x = s.magic_x + s.entry_xs_real * \
                    (mem['start'] - 1/s.entries_per_sec + mem['prev_off']) * \
                    s.entries_per_sec - s.entry_ys_real/4
                new_wid_x = s.magic_x + s.entry_xs_real * \
                    (mem['start'] + mem['prev_off']) * s.entries_per_sec - s.entry_ys_real/4
                wid_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)

                start_wid_pos = (old_wid_x, wid_y)

                if (anim := s.anims.get(wid_id, {}).get(0, None)) and not anim.finished:
                    start_wid_pos = anim.attrs_current['position']
                    anim.cancel()

                if wid_id in s.anims:
                    s.anims[wid_id].pop(0, None)
                else:
                    s.anims[wid_id] = {}

                s.anims[wid_id][0] = Animate(
                    widget=s.widgets[mem['prev_off_wid']],
                    attrs={
                        'position': (start_wid_pos, (new_wid_x, wid_y))
                    },
                    duration=s.global_butter
                )

            restamp()

        if which == 1:
            if mem['start'] < 0.01:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Strings.ERROR_REACHED_ZERO)
                return

            for key in [0, 2, 3]:
                if (anim := s.anims[id(b)].get(key, None)):
                    anim.cancel()
                    s.anims[id(b)].pop(key, None)

            if (anim := s.anims[id(b)].get(1, None)) and not anim.finished:
                start_pos = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(b)].pop(1, None)

            mem['start'] -= 1/s.entries_per_sec

            key_old_positions = {}
            for key_data in mem.get('keys', {}).values():
                if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                    wid = s.widgets[key_data['widget']]
                    wid_id = id(wid)

                    if wid_id in s.anims and 0 in s.anims[wid_id]:
                        if (anim := s.anims[wid_id].get(0, None)) and not anim.finished:
                            key_old_positions[wid_id] = anim.attrs_current['position']
                            anim.cancel()
                            s.anims[wid_id].pop(0, None)
                        else:
                            old_x = s.magic_x + s.entry_xs_real * \
                                key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                            old_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                            key_old_positions[wid_id] = (old_x, old_y)
                    else:
                        old_x = s.magic_x + s.entry_xs_real * \
                            key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                        old_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                        key_old_positions[wid_id] = (old_x, old_y)

            for key_data in mem.get('keys', {}).values():
                key_data['time'] -= 1/s.entries_per_sec

            end_pos = Eval.ENTRY_POS(s, mem)
            new['position'] = (start_pos, end_pos)

            animate_key_widgets(1, key_old_positions)

            if mem.get('prev_off_wid') and s.widgets[mem['prev_off_wid']].exists():
                wid_id = mem['prev_off_wid']

                for key in [0, 4, 5]:
                    if (anim := s.anims.get(wid_id, {}).get(key, None)):
                        anim.cancel()
                        s.anims[wid_id].pop(key, None)

                old_wid_x = s.magic_x + s.entry_xs_real * \
                    (mem['start'] + 1/s.entries_per_sec + mem['prev_off']) * \
                    s.entries_per_sec - s.entry_ys_real/4
                new_wid_x = s.magic_x + s.entry_xs_real * \
                    (mem['start'] + mem['prev_off']) * s.entries_per_sec - s.entry_ys_real/4
                wid_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)

                start_wid_pos = (old_wid_x, wid_y)

                if (anim := s.anims.get(wid_id, {}).get(1, None)) and not anim.finished:
                    start_wid_pos = anim.attrs_current['position']
                    anim.cancel()

                if wid_id in s.anims:
                    s.anims[wid_id].pop(1, None)
                else:
                    s.anims[wid_id] = {}

                s.anims[wid_id][1] = Animate(
                    widget=s.widgets[mem['prev_off_wid']],
                    attrs={
                        'position': (start_wid_pos, (new_wid_x, wid_y))
                    },
                    duration=s.global_butter
                )

            restamp()

        if which == 2:
            if (shrink := s.anims[id(b)].get(3, None)):
                shrink.cancel()
                s.anims[id(b)].pop(3, None)

            if (anim := s.anims[id(b)].get(2, None)) and not anim.finished:
                start_size = anim.attrs_current['size']
                start_pos = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(b)].pop(2, None)

            mem['duration'] += 1 / s.entries_per_sec

            end_size = Eval.ENTRY_SIZE(s, mem)
            end_pos = Eval.ENTRY_POS(s, mem)

            new['size'] = (start_size, end_size)
            new['position'] = (start_pos, end_pos)

            restamp()

            for key_data in mem.get('keys', {}).values():
                key_offset = key_data['time'] - mem['start']
                if key_offset <= mem['duration']:
                    existing = key_data.get('widget')
                    if existing is None or existing not in s.widgets or not s.widgets[existing].exists():
                        key_x = s.magic_x + s.entry_xs_real * \
                            (mem['start'] + key_offset) * s.entries_per_sec - s.entry_ys_real/4
                        key_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)

                        key_w = bui.imagewidget(
                            parent=s.stamp_hscroll_root,
                            position=(key_x, key_y),
                            size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                            texture=Eval.TEXTURE(Const.KEY),
                            color=Color.WARM,
                            opacity=Color.OPACITY
                        )
                        key_data['widget'] = id(key_w)
                        s.widgets[id(key_w)] = key_w

            if mem.get('prev_off') is not None and s.window_on and s.window_on[1] == s.key_window:
                old_duration = mem['duration'] - 1/s.entries_per_sec
                new_duration = mem['duration']

                if old_duration < mem['prev_off'] and new_duration >= mem['prev_off']:
                    wid_x = s.magic_x + s.entry_xs_real * \
                        (mem['start'] + mem['prev_off']) * s.entries_per_sec - s.entry_ys_real/4
                    wid_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)

                    s.prev_off_wid = bui.imagewidget(
                        parent=s.stamp_hscroll_root,
                        position=(wid_x, wid_y),
                        size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                        texture=Eval.TEXTURE(Const.KEY),
                        color=Color.WARM,
                        opacity=Color.OPACITY
                    )
                    mem['prev_off_wid'] = id(s.prev_off_wid)
                    s.widgets[id(s.prev_off_wid)] = s.prev_off_wid

        if which == 3:
            current_ticks = round(mem['duration'] * s.entries_per_sec)
            if current_ticks <= 1:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Strings.ERROR_SMALLEST)
                return

            if (expand := s.anims[id(b)].get(2, None)):
                expand.cancel()
                s.anims[id(b)].pop(2, None)

            if (anim := s.anims[id(b)].get(3, None)) and not anim.finished:
                start_size = anim.attrs_current['size']
                start_pos = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(b)].pop(3, None)

            mem['duration'] -= 1 / s.entries_per_sec

            new_width_steps = mem['duration'] * s.entries_per_sec
            end_size = (
                s.entry_xs_real * new_width_steps * s.magic_right,
                s.entry_ys_real - s.magic_y
            )
            end_x = s.magic_x + s.entry_xs_real * \
                mem['start']*s.entries_per_sec + (new_width_steps * s.magic_left)
            end_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
            end_pos = (end_x, end_y)

            new['size'] = (start_size, end_size)
            new['position'] = (start_pos, end_pos)

            restamp()

            for key_data in mem.get('keys', {}).values():
                key_time = key_data['time'] - mem['start']
                if key_time > mem['duration']:
                    if 'widget' in key_data:
                        wid = s.widgets.pop(key_data['widget'], None)
                        wid and wid.exists() and wid.delete()
                        del key_data['widget']

            if mem.get('prev_off') is not None and s.window_on and s.window_on[1] == s.key_window:
                old_duration = mem['duration'] + 1/s.entries_per_sec
                new_duration = mem['duration']

                if old_duration >= mem['prev_off'] and new_duration < mem['prev_off']:
                    if mem.get('prev_off_wid') and s.widgets[mem['prev_off_wid']].exists():
                        s.widgets.pop(mem.pop('prev_off_wid')).delete()

        if which == 4:
            current_list_index = s.stamp_kids.index(b)
            if current_list_index == 0:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Strings.ERROR_AT_TOP)
                return

            Eval.SOUND(Const.OK_SOUND).play()

            target_list_index = current_list_index - 1
            other_btn = s.stamp_kids[target_list_index]
            other_mem = s.memory[id(other_btn)]

            start_pos_b = Eval.ENTRY_POS(s, mem)
            start_pos_other = Eval.ENTRY_POS(s, other_mem)
            new_y_up = Eval.ENTRY_Y(s, other_mem)
            new_y_down = Eval.ENTRY_Y(s, mem)

            key_old_positions = {}
            for key_data in mem.get('keys', {}).values():
                if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                    wid = s.widgets[key_data['widget']]
                    wid_id = id(wid)

                    found = False
                    for check_key in [4, 5]:
                        if wid_id in s.anims and check_key in s.anims[wid_id]:
                            if (anim := s.anims[wid_id].get(check_key, None)) and not anim.finished:
                                key_old_positions[wid_id] = anim.attrs_current['position']
                                anim.cancel()
                                s.anims[wid_id].pop(check_key, None)
                                found = True
                                break

                    if not found:
                        old_x = s.magic_x + s.entry_xs_real * \
                            key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                        old_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                        key_old_positions[wid_id] = (old_x, old_y)

            other_key_old_positions = {}
            for key_data in other_mem.get('keys', {}).values():
                if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                    wid = s.widgets[key_data['widget']]
                    wid_id = id(wid)

                    found = False
                    for check_key in [4, 5]:
                        if wid_id in s.anims and check_key in s.anims[wid_id]:
                            if (anim := s.anims[wid_id].get(check_key, None)) and not anim.finished:
                                other_key_old_positions[wid_id] = anim.attrs_current['position']
                                anim.cancel()
                                s.anims[wid_id].pop(check_key, None)
                                found = True
                                break
                    if not found:
                        old_x = s.magic_x + s.entry_xs_real * \
                            key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                        old_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)
                        other_key_old_positions[wid_id] = (old_x, old_y)

            mem['order'], other_mem['order'] = other_mem['order'], mem['order']

            s.stamp_kids[current_list_index] = other_btn
            s.stamp_kids[target_list_index] = b

            if (down := s.anims[id(b)].get(5, None)):
                down.cancel()
                s.anims[id(b)].pop(5, None)

            if (anim := s.anims[id(b)].get(4, None)) and not anim.finished:
                start_pos_b = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(b)].pop(4, None)

            end_pos_b = (start_pos_b[0], new_y_up)
            s.anims[id(b)][4] = Animate(
                widget=b,
                duration=s.global_butter,
                attrs={'position': (start_pos_b, end_pos_b)}
            )

            if (down := s.anims[id(other_btn)].get(5, None)):
                down.cancel()
                s.anims[id(other_btn)].pop(5, None)

            if (anim := s.anims[id(other_btn)].get(4, None)) and not anim.finished:
                start_pos_other = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(other_btn)].pop(4, None)

            end_pos_other = (start_pos_other[0], new_y_down)
            s.anims[id(other_btn)][4] = Animate(
                widget=other_btn,
                duration=s.global_butter,
                attrs={'position': (start_pos_other, end_pos_other)}
            )

            animate_key_widgets(4, key_old_positions)

            for key_data in other_mem.get('keys', {}).values():
                if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                    wid = s.widgets[key_data['widget']]
                    wid_id = id(wid)
                    key_time = key_data['time']

                    new_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                    new_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)

                    start_wid_pos = other_key_old_positions.get(wid_id, (new_x, new_y))

                    if wid_id in s.anims and 4 in s.anims[wid_id]:
                        if (anim := s.anims[wid_id].get(4, None)) and not anim.finished:
                            start_wid_pos = anim.attrs_current['position']
                            anim.cancel()

                    if wid_id not in s.anims:
                        s.anims[wid_id] = {}

                    s.anims[wid_id].pop(4, None)

                    s.anims[wid_id][4] = Animate(
                        widget=wid,
                        attrs={'position': (start_wid_pos, (new_x, new_y))},
                        duration=s.global_butter
                    )

            if mem.get('prev_off_wid') and s.widgets[mem['prev_off_wid']].exists():
                wid_id = mem['prev_off_wid']

                for key in [5, 0, 1]:
                    if (anim := s.anims.get(wid_id, {}).get(key, None)):
                        anim.cancel()
                        s.anims[wid_id].pop(key, None)

                wid_x = s.magic_x + s.entry_xs_real * \
                    (mem['start'] + mem['prev_off']) * s.entries_per_sec - s.entry_ys_real/4
                old_wid_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)
                new_wid_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)

                start_wid_pos = (wid_x, old_wid_y)

                if (anim := s.anims.get(wid_id, {}).get(4, None)) and not anim.finished:
                    start_wid_pos = anim.attrs_current['position']
                    anim.cancel()

                if wid_id in s.anims:
                    s.anims[wid_id].pop(4, None)
                else:
                    s.anims[wid_id] = {}

                s.anims[wid_id][4] = Animate(
                    widget=s.widgets[mem['prev_off_wid']],
                    attrs={
                        'position': (start_wid_pos, (wid_x, new_wid_y))
                    },
                    duration=s.global_butter
                )

            if other_mem.get('prev_off_wid') and s.widgets[other_mem['prev_off_wid']].exists():
                wid_id = other_mem['prev_off_wid']

                for key in [5, 0, 1]:
                    if (anim := s.anims.get(wid_id, {}).get(key, None)):
                        anim.cancel()
                        s.anims[wid_id].pop(key, None)

                wid_x = s.magic_x + s.entry_xs_real * \
                    (other_mem['start'] + other_mem['prev_off']) * \
                    s.entries_per_sec - s.entry_ys_real/4
                old_wid_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                new_wid_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)

                start_wid_pos = (wid_x, old_wid_y)

                if (anim := s.anims.get(wid_id, {}).get(4, None)) and not anim.finished:
                    start_wid_pos = anim.attrs_current['position']
                    anim.cancel()

                if wid_id in s.anims:
                    s.anims[wid_id].pop(4, None)
                else:
                    s.anims[wid_id] = {}

                s.anims[wid_id][4] = Animate(
                    widget=s.widgets[other_mem['prev_off_wid']],
                    attrs={
                        'position': (start_wid_pos, (wid_x, new_wid_y))
                    },
                    duration=s.global_butter
                )

        if which == 5:
            current_list_index = s.stamp_kids.index(b)
            max_list_index = len(s.stamp_kids) - 1
            if current_list_index == max_list_index:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Strings.ERROR_AT_BOTTOM)
                return

            Eval.SOUND(Const.OK_SOUND).play()

            target_list_index = current_list_index + 1
            other_btn = s.stamp_kids[target_list_index]
            other_mem = s.memory[id(other_btn)]

            start_pos_b = Eval.ENTRY_POS(s, mem)
            start_pos_other = Eval.ENTRY_POS(s, other_mem)
            new_y_down = Eval.ENTRY_Y(s, other_mem)
            new_y_up = Eval.ENTRY_Y(s, mem)

            key_old_positions = {}
            for key_data in mem.get('keys', {}).values():
                if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                    wid = s.widgets[key_data['widget']]
                    wid_id = id(wid)

                    found = False
                    for check_key in [4, 5]:
                        if wid_id in s.anims and check_key in s.anims[wid_id]:
                            if (anim := s.anims[wid_id].get(check_key, None)) and not anim.finished:
                                key_old_positions[wid_id] = anim.attrs_current['position']
                                anim.cancel()
                                s.anims[wid_id].pop(check_key, None)
                                found = True
                                break

                    if not found:
                        old_x = s.magic_x + s.entry_xs_real * \
                            key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                        old_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                        key_old_positions[wid_id] = (old_x, old_y)

            other_key_old_positions = {}
            for key_data in other_mem.get('keys', {}).values():
                if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                    wid = s.widgets[key_data['widget']]
                    wid_id = id(wid)

                    found = False
                    for check_key in [4, 5]:
                        if wid_id in s.anims and check_key in s.anims[wid_id]:
                            if (anim := s.anims[wid_id].get(check_key, None)) and not anim.finished:
                                other_key_old_positions[wid_id] = anim.attrs_current['position']
                                anim.cancel()
                                s.anims[wid_id].pop(check_key, None)
                                found = True
                                break

                    if not found:
                        old_x = s.magic_x + s.entry_xs_real * \
                            key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                        old_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)
                        other_key_old_positions[wid_id] = (old_x, old_y)

            mem['order'], other_mem['order'] = other_mem['order'], mem['order']

            s.stamp_kids[current_list_index] = other_btn
            s.stamp_kids[target_list_index] = b

            if (up := s.anims[id(b)].get(4, None)):
                up.cancel()
                s.anims[id(b)].pop(4, None)

            if (anim := s.anims[id(b)].get(5, None)) and not anim.finished:
                start_pos_b = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(b)].pop(5, None)

            end_pos_b = (start_pos_b[0], new_y_down)
            s.anims[id(b)][5] = Animate(
                widget=b,
                duration=s.global_butter,
                attrs={'position': (start_pos_b, end_pos_b)}
            )

            if (up := s.anims[id(other_btn)].get(4, None)):
                up.cancel()
                s.anims[id(other_btn)].pop(4, None)

            if (anim := s.anims[id(other_btn)].get(5, None)) and not anim.finished:
                start_pos_other = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(other_btn)].pop(5, None)

            end_pos_other = (start_pos_other[0], new_y_up)
            s.anims[id(other_btn)][5] = Animate(
                widget=other_btn,
                duration=s.global_butter,
                attrs={'position': (start_pos_other, end_pos_other)}
            )

            animate_key_widgets(5, key_old_positions)

            for key_data in other_mem.get('keys', {}).values():
                if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                    wid = s.widgets[key_data['widget']]
                    wid_id = id(wid)
                    key_time = key_data['time']

                    new_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                    new_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)

                    start_wid_pos = other_key_old_positions.get(wid_id, (new_x, new_y))

                    if wid_id in s.anims and 5 in s.anims[wid_id]:
                        if (anim := s.anims[wid_id].get(5, None)) and not anim.finished:
                            start_wid_pos = anim.attrs_current['position']
                            anim.cancel()

                    if wid_id not in s.anims:
                        s.anims[wid_id] = {}

                    s.anims[wid_id].pop(5, None)

                    s.anims[wid_id][5] = Animate(
                        widget=wid,
                        attrs={'position': (start_wid_pos, (new_x, new_y))},
                        duration=s.global_butter
                    )

            if mem.get('prev_off_wid') and s.widgets[mem['prev_off_wid']].exists():
                wid_id = mem['prev_off_wid']

                for key in [4, 0, 1]:
                    if (anim := s.anims.get(wid_id, {}).get(key, None)):
                        anim.cancel()
                        s.anims[wid_id].pop(key, None)

                wid_x = s.magic_x + s.entry_xs_real * \
                    (mem['start'] + mem['prev_off']) * s.entries_per_sec - s.entry_ys_real/4
                old_wid_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)
                new_wid_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)

                start_wid_pos = (wid_x, old_wid_y)

                if (anim := s.anims.get(wid_id, {}).get(5, None)) and not anim.finished:
                    start_wid_pos = anim.attrs_current['position']
                    anim.cancel()

                if wid_id in s.anims:
                    s.anims[wid_id].pop(5, None)
                else:
                    s.anims[wid_id] = {}

                s.anims[wid_id][5] = Animate(
                    widget=s.widgets[mem['prev_off_wid']],
                    attrs={
                        'position': (start_wid_pos, (wid_x, new_wid_y))
                    },
                    duration=s.global_butter
                )

            if other_mem.get('prev_off_wid') and s.widgets[other_mem['prev_off_wid']].exists():
                wid_id = other_mem['prev_off_wid']

                for key in [4, 0, 1]:
                    if (anim := s.anims.get(wid_id, {}).get(key, None)):
                        anim.cancel()
                        s.anims[wid_id].pop(key, None)

                wid_x = s.magic_x + s.entry_xs_real * \
                    (other_mem['start'] + other_mem['prev_off']) * \
                    s.entries_per_sec - s.entry_ys_real/4
                old_wid_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                new_wid_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)

                start_wid_pos = (wid_x, old_wid_y)

                if (anim := s.anims.get(wid_id, {}).get(5, None)) and not anim.finished:
                    start_wid_pos = anim.attrs_current['position']
                    anim.cancel()

                if wid_id in s.anims:
                    s.anims[wid_id].pop(5, None)
                else:
                    s.anims[wid_id] = {}

                s.anims[wid_id][5] = Animate(
                    widget=s.widgets[other_mem['prev_off_wid']],
                    attrs={
                        'position': (start_wid_pos, (wid_x, new_wid_y))
                    },
                    duration=s.global_butter
                )

        if which == 6:
            Eval.SOUND(Const.OK_SOUND).play()
            if s.can_do != which:
                s.toast(Strings.CONFIRM_DUPLICATE(
                    mem['data']['name']
                ), extra=2)
                s.can_do = which
                return
            s.on_scroll()

            for kid in s.stamp_kids:
                if (anim := s.anims[id(kid)].get(6, None)):
                    anim.cancel()
                    s.anims[id(kid)].pop(6, None)
                    bui.buttonwidget(
                        kid,
                        opacity=Color.OPACITY,
                        textcolor=(*Color.TEXT, Color.TEXT_OPACITY)
                    )

            original_data = mem.copy()
            original_event = original_data['event']
            original_duration = original_data['duration']
            original_start = original_data['start']
            original_order = original_data['order']
            node_data = {
                i: (
                    isinstance(j, (list, dict))
                    and j.copy() or j
                ) for i, j in original_data['data'].copy().items()
            }

            size = (
                s.entry_xs_real * (
                    original_duration *
                    s.entries_per_sec
                ) * s.magic_right,
                s.entry_ys_real - s.magic_y
            )
            btn = bui.buttonwidget(
                parent=s.stamp_hscroll_root,
                texture=Eval.TEXTURE(Const.SKIN),
                label=node_data['name'],
                textcolor=Const.INVISIBLE,
                color=Color.BASE,
                opacity=0,
                enable_sound=False,
                size=size,
                button_type='square'
            )

            original_list_index = s.stamp_kids.index(b)
            s.stamp_kids.insert(original_list_index + 1, btn)

            new_order = original_order + 1

            call = bui.CallPartial(
                s.select, btn
            )
            bui.buttonwidget(btn, on_activate_call=call)

            new_keys = {}
            for nam, key_data in original_data.get('keys', {}).items():
                new_key_data = key_data.copy()
                key_time = new_key_data['time']
                key_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                key_y = s.entry_ys_real * (len(s.memory) - new_order)

                new_key_wid = bui.imagewidget(
                    parent=s.stamp_hscroll_root,
                    position=(key_x, key_y),
                    size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                    texture=Eval.TEXTURE(Const.KEY),
                    color=Color.WARM,
                    opacity=0
                )
                new_key_data['widget'] = id(new_key_wid)
                s.widgets[id(new_key_wid)] = new_key_wid
                new_keys[nam] = new_key_data

            s.memory[id(btn)] = {
                'order': new_order,
                'event': original_event,
                'data': node_data,
                'duration': original_duration,
                'start': original_start,
                'keys': new_keys,
                'prev_off': original_data.get('prev_off'),
                'prev_off_wid': None
            }

            for kid in s.stamp_kids[original_list_index + 2:]:
                s.memory[id(kid)]['order'] += 1

            s.wrap([1, 2, 3])

            final_x = Eval.ENTRY_X(s, {'start': original_start, 'duration': original_duration})
            orig_y = Eval.ENTRY_Y(s, {'order': original_order})
            final_y = Eval.ENTRY_Y(s, {'order': new_order})

            bui.buttonwidget(btn, position=(final_x, orig_y))

            for kid in s.stamp_kids[:original_list_index + 1]:
                kid_mem = s.memory[id(kid)]
                kid_x = Eval.ENTRY_X(s, kid_mem)

                old_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 2)
                new_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 1)

                s.anims[id(kid)][which] = Animate(
                    widget=kid,
                    attrs={
                        'position': ((kid_x, old_y), (kid_x, new_y))
                    },
                    duration=s.global_butter
                )

            for kid in s.stamp_kids[:original_list_index + 1]:
                kid_mem = s.memory[id(kid)]
                kid_width_steps = kid_mem['duration'] * s.entries_per_sec
                kid_x = s.magic_x + s.entry_xs_real * \
                    kid_mem['start']*s.entries_per_sec + (kid_width_steps * s.magic_left)

                old_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 2)
                new_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 1)

                s.anims[id(kid)][which] = Animate(
                    widget=kid,
                    attrs={
                        'position': ((kid_x, old_y), (kid_x, new_y))
                    },
                    duration=s.global_butter
                )

                for key_data in kid_mem.get('keys', {}).values():
                    if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                        wid = s.widgets[key_data['widget']]
                        wid_id = id(wid)
                        key_time = key_data['time']

                        key_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                        old_key_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 2)
                        new_key_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 1)

                        if wid_id not in s.anims:
                            s.anims[wid_id] = {}

                        s.anims[wid_id][which] = Animate(
                            widget=wid,
                            attrs={
                                'opacity': (Color.OPACITY, Color.OPACITY),
                                'position': ((key_x, old_key_y), (key_x, new_key_y))
                            },
                            duration=s.global_butter
                        )

            s.anims[id(btn)][which] = Animate(
                widget=btn,
                attrs={
                    'opacity': (0, Color.OPACITY),
                    'textcolor': (
                        Const.INVISIBLE,
                        (*Color.TEXT, Color.TEXT_OPACITY)
                    ),
                    'position': ((final_x, orig_y), (final_x, final_y))
                },
                duration=s.global_butter
            )

            for key_data in new_keys.values():
                if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                    wid = s.widgets[key_data['widget']]
                    wid_id = id(wid)
                    key_time = key_data['time']

                    key_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                    key_y = s.entry_ys_real * (len(s.memory) - new_order - 1)

                    if wid_id not in s.anims:
                        s.anims[wid_id] = {}

                    s.anims[wid_id][which] = Animate(
                        widget=wid,
                        attrs={
                            'opacity': (0, Color.OPACITY),
                            'position': ((key_x, orig_y + 0), (key_x, key_y))
                        },
                        duration=s.global_butter
                    )

            s.scroll_to_timer = bui.AppTimer(
                s.global_butter / 2,
                bui.CallPartial(s.scroll_to, btn)
            )

            call()
            s.toast(Strings.INFO_DUPLICATED(node_data["name"]))
            s.build_timeline()
            bui.apptimer(s.global_butter, s.wrap)
            return

        if which == 7:
            Eval.SOUND(Const.OK_SOUND).play()
            if s.can_do != which:
                s.toast(Strings.CONFIRM_DELETE(
                    mem['data']['name']
                ), extra=2)
                s.can_do = which
                return

            if s.window_on and s.window_on[1] == s.edit_window:
                s.dismiss_window()

            node_name = mem['data']['name']
            deleted_order = mem['order']

            deleted_key_old_positions = {}
            for key_data in mem.get('keys', {}).values():
                if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                    wid = s.widgets[key_data['widget']]
                    wid_id = id(wid)
                    key_time = key_data['time']

                    old_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                    old_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                    deleted_key_old_positions[wid_id] = (old_x, old_y)

            def cleanup():
                for key_data in mem.get('keys', {}).values():
                    if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                        wid = s.widgets.pop(key_data['widget'])
                        wid_id = id(wid)

                        start_pos = deleted_key_old_positions.get(wid_id, (0, 0))

                        if wid_id in s.anims and which in s.anims[wid_id]:
                            if (anim := s.anims[wid_id].get(which, None)) and not anim.finished:
                                start_pos = anim.attrs_current['position']
                                anim.cancel()

                        if wid_id not in s.anims:
                            s.anims[wid_id] = {}

                        s.anims[wid_id].pop(which, None)

                        s.anims[wid_id][which] = Animate(
                            widget=wid,
                            attrs={
                                'opacity': (Color.OPACITY, 0),
                                'position': (start_pos, start_pos)
                            },
                            duration=s.global_butter / 2,
                            on_finish=wid.delete
                        )

                if mem.get('prev_off_wid') and s.widgets[mem['prev_off_wid']].exists():
                    wid = s.widgets.pop(mem['prev_off_wid'])
                    wid_id = id(wid)

                    if wid_id not in s.anims:
                        s.anims[wid_id] = {}

                    s.anims[wid_id][which] = Animate(
                        widget=wid,
                        attrs={'opacity': (Color.OPACITY, 0)},
                        duration=s.global_butter / 2,
                        on_finish=wid.delete
                    )
                    mem.pop('prev_off_wid')

                del s.memory[id(b)]
                s.stamp_kids.remove(b)

                if b.exists():
                    b.delete()

                for kid in s.stamp_kids:
                    kid_mem = s.memory[id(kid)]
                    if kid_mem['order'] > deleted_order:
                        kid_mem['order'] -= 1

                s.wrap([1, 2, 3])

                for idx, kid in enumerate(reversed(s.stamp_kids)):
                    kid_mem = s.memory[id(kid)]
                    if kid_mem['order'] >= deleted_order:
                        continue

                    old_x = Eval.ENTRY_X(s, kid_mem)
                    current_y = s.entry_ys_real * (idx + 1)
                    end_pos = (old_x, s.entry_ys_real * idx)

                    s.anims[id(kid)][which] = Animate(
                        widget=kid,
                        attrs={
                            'position': ((old_x, current_y), end_pos)
                        },
                        duration=s.global_butter
                    )

                    for key_data in kid_mem.get('keys', {}).values():
                        if 'widget' in key_data and s.widgets[key_data['widget']].exists():
                            wid = s.widgets[key_data['widget']]
                            wid_id = id(wid)
                            key_time = key_data['time']

                            new_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                            old_key_y = s.entry_ys_real * (idx + 1)
                            new_key_y = s.entry_ys_real * idx

                            start_wid_pos = (new_x, old_key_y)

                            if wid_id in s.anims and which in s.anims[wid_id]:
                                if (anim := s.anims[wid_id].get(which, None)) and not anim.finished:
                                    start_wid_pos = anim.attrs_current['position']
                                    anim.cancel()

                            if wid_id not in s.anims:
                                s.anims[wid_id] = {}

                            s.anims[wid_id].pop(which, None)

                            s.anims[wid_id][which] = Animate(
                                widget=wid,
                                attrs={
                                    'position': (start_wid_pos, (new_x, new_key_y))
                                },
                                duration=s.global_butter
                            )

                    if kid_mem.get('prev_off_wid') and s.widgets[kid_mem['prev_off_wid']].exists():
                        wid_id = kid_mem['prev_off_wid']

                        for key in [4, 5, 0, 1]:
                            if (anim := s.anims.get(wid_id, {}).get(key, None)):
                                anim.cancel()
                                s.anims[wid_id].pop(key, None)

                        wid_x = s.magic_x + s.entry_xs_real * \
                            (kid_mem['start'] + kid_mem['prev_off']) * \
                            s.entries_per_sec - s.entry_ys_real/4
                        old_wid_y = s.entry_ys_real * (idx + 1)
                        new_wid_y = s.entry_ys_real * idx

                        start_wid_pos = (wid_x, old_wid_y)

                        if (anim := s.anims.get(wid_id, {}).get(which, None)) and not anim.finished:
                            start_wid_pos = anim.attrs_current['position']
                            anim.cancel()

                        if wid_id in s.anims:
                            s.anims[wid_id].pop(which, None)
                        else:
                            s.anims[wid_id] = {}

                        s.anims[wid_id][which] = Animate(
                            widget=s.widgets[kid_mem['prev_off_wid']],
                            attrs={
                                'position': (start_wid_pos, (wid_x, new_wid_y))
                            },
                            duration=s.global_butter
                        )

                s.sl = None
                s.hide_tools()
                if len(s.memory):
                    s.show_controls(up=True)

                s.toast(Strings.INFO_DELETED(node_name))
                s.build_timeline()

            s.anims[id(b)][which] = Animate(
                widget=b,
                attrs={
                    'opacity': (Color.OPACITY, 0),
                    'textcolor': (
                        (*Color.TEXT, Color.TEXT_OPACITY),
                        Const.INVISIBLE
                    )
                },
                duration=s.global_butter / 2,
                on_finish=cleanup
            )

            s.wrap(2)
            return

        s.build_timeline()
        which not in [2, 3] and bui.apptimer(
            scroll_butter,
            bui.CallPartial(s.scroll_to, b)
        )
        butter = s.global_butter
        if new:
            s.anims[id(b)][which] = Animate(
                widget=b,
                duration=butter,
                attrs=new
            )
            Eval.SOUND(Const.OK_SOUND).play()

    def scroll_to(s, b):
        bui.containerwidget(
            s.stamp_hscroll_root,
            visible_child=b
        )
        rx, ry = s.real
        bx, by = b.get_screen_space_center()
        dx, dy = s.bottom_left_h.get_screen_space_center()
        to = Eval.RELATIVE(
            rx/2, ry/2,
            dx, dy,
            bx, by
        )
        temp = bui.textwidget(
            parent=s.stamp_scroll_root,
            position=to,
        )
        bui.containerwidget(
            s.stamp_scroll_root,
            visible_child=temp
        )
        temp.delete()
        s.on_scroll()


class Bubble:
    __mem__ = {}

    def __init__(
        s,
        node: 'bs.Node',
        text: str = 'Hello!',
        color: tuple = (1, 1, 1),
        time: float | int = 4,
        mode: int = 0,
        res: list = [('█'), ('▼')]
    ) -> None:
        if not 0 <= mode <= 5:
            raise ValueError(f'mode can be an integer from 0 to 5, not {mode}')
        if not mode:
            mode = choice([1, 2, 3, 4, 5])
        s.ans, s.kids, s.mats, s.time = [], [], [], time
        s.node, s.dead, s.text = node, False, text
        s.color, s.mode, s.res = color, mode, res
        s.mem = lambda: s.__class__.__mem__
        m = s.mem()
        o = m.get(node, 0)
        if not getattr(o, 'dead', 1):
            bs.timer(0.2, bs.CallPartial(o.delete, force=True))
        s.show()
        m[node] = s

    def show(s):
        q, l, r = s.mats, s.kids, s.ans
        m = bs.newnode(
            'math',
            owner=s.node,
            attrs={
                'input1': (0, 1.65, 0),
                'operation': 'add'
            }
        )
        q.append(m)
        c = list(s.color)
        w = Eval.STRING_WIDTH(s.res[0])
        b = bs.newnode(
            'text',
            owner=m,
            attrs={
                'text': f'{ceil((Eval.STRING_WIDTH(s.text)+2*w)/w)*s.res[0]}\n{s.res[1]}',
                'in_world': True,
                'shadow': 1.0,
                'flatness': 1.0,
                'color': (c[0], c[1], c[2], 0.2),
                'scale': 0.01,
                'h_align': 'center'
            }
        )
        l.append(b)
        txt = []
        mat = []
        kek = -Eval.STRING_WIDTH(s.text)/185
        sf = 0
        for i in range(len(s.text)):
            j = s.text[i]
            x = Eval.STRING_WIDTH(j)/95.0
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
                    'input1': (ok, 1.65, 0),
                    'operation': 'add'
                }
            )
            mat.append([p2, ok])
            s.node.connectattr('position', p2, 'input2')
            p2.connectattr('output', p1, 'position')
            sf += x
        l += txt
        q += [mat[i][0] for i in range(len(mat))]
        s.node.connectattr('position', m, 'input2')
        m.connectattr('output', b, 'position')
        z = s.time
        a = bs.animate(
            b,
            'scale',
            {
                0: 0,
                z*0.041: 0.014,
                z*0.154: 0.014,
                z*0.167: 0.010,
                z*0.98: 0.010,
                z: 0
            },
        )
        r.append(a)
        a = bs.animate_array(
            m,
            'input1',
            3,
            {
                0: (0, 1.2, 0),
                z*0.04: (0, 1.65, 0),
                z*0.98: (0, 1.65, 0),
                z: (0, 1.2, 0)
            }
        )
        r.append(a)
        r += [
            bs.animate(
                txt[i],
                'scale',
                {
                    0: 0,
                    z*0.041: 0.015,
                    z*0.154: 0.015,
                    z*0.167: 0.010,
                    z*0.98: 0.010,
                    z: 0
                },
            )
            for i in range(len(mat))
        ] if s.mode in [1, 4] else []
        r += [
            bs.animate_array(
                mat[i][0],
                'input1',
                3,
                {
                    0: (mat[i][1]/4, 1.2, 0),
                    z*0.04: (mat[i][1]*1.5, 1.65, 0),
                    z*0.154: (mat[i][1]*1.5, 1.65, 0),
                    z*0.167: (mat[i][1], 1.65, 0),
                    z*0.98: (mat[i][1], 1.65, 0),
                    z: (mat[i][1]/4, 1.2, 0)
                }
            )
            for i in range(len(mat))
        ] if s.mode in [1, 4] else []
        ok = (z*0.04*1.6)
        hm = [0.03, 0.05][s.mode == 2]
        r += [
            bs.animate_array(
                j[0],
                'input1',
                3,
                {
                    0.5+i*hm: (j[1], 1.4, 0),
                    0.5+i*hm+(ok*0.6): (j[1], 1.9, 0),
                    0.5+i*hm+ok: (j[1], 1.65, 0),
                    (z-(z*0.02)): (j[1], 1.65, 0),
                    z: (j[1], 1.2, 0)
                }
            )
            for i, j in enumerate(mat)
        ] if s.mode in [2, 5] else []
        r += [
            bs.animate(
                txt[i],
                'opacity',
                {
                    0.5+i*hm: 0,
                    (0.5+i*hm+ok)*0.98: 1,
                    z*0.9: 1,
                    z: 0
                }
            )
            for i in range(len(mat))
        ] if s.mode in [2, 4, 5] else []
        r += [
            bs.animate(
                txt[i],
                'scale',
                {
                    0: 0,
                    z*0.154: 0,
                    z*0.167: 0.010,
                    z*0.98: 0.010,
                    z: 0
                },
            )
            for i in range(len(mat))
        ] if s.mode == 3 else []
        bs.timer(z, s.delete)

    def delete(s, force=False):
        if s.dead:
            return
        s.dead = True
        [i.delete() for i in s.ans if hasattr(i, 'delete')]
        bs.timer(0.2, lambda: [i.delete() for i in s.kids+s.mats if hasattr(i, 'delete')])
        if not force:
            return
        [bs.animate(
            i,
            'opacity',
            {
                0: i.opacity,
                0.2: 0
            }
        ) for i in s.kids]


class Animate:
    def __init__(s, widget, attrs, duration, on_start=None, on_finish=None, on_cancel=None, delay=0, condition=None, on_reverse=None):
        """
        Dynamic animation system.

        Args:
            widget: The widget to animate
            func: The function to call (e.g., bui.imagewidget, bui.buttonwidget)
            attrs: Dict of attributes to animate, format:
                   {'attr_name': (start_value, end_value), ...}
                   Examples:
                   - {'opacity': (0, 1)}
                   - {'position': ((0,0), (100,200))}
                   - {'size': ((50,50), (200,300)), 'opacity': (0, 0.5)}
            duration: Animation duration in seconds
            on_start: Optional callback when animation starts
            on_finish: Optional callback when animation completes
            delay: Delay in seconds before starting animation
            condition: Optional callable that must return True
        """
        s.widget = widget
        s.on_start = on_start
        s.on_finish = (
            isinstance(on_finish, tuple) and bui.CallPartial(
                s.reverse,
                on_finish=on_finish[0]
            ) or on_finish
        )
        s.on_reverse = on_reverse
        s.on_cancel = on_cancel
        s.cancelled = False
        s.finished = False
        s.delay = delay
        s.delay_timer = None
        s.timer = None
        s.condition = condition
        if not widget.exists():
            return
        s.func = Eval.WIDGET(widget)

        s.attrs_start = {}
        s.attrs_end = {}
        s.attrs_current = {}

        for attr_name, (start_val, end_val) in attrs.items():
            s.attrs_start[attr_name] = start_val
            s.attrs_end[attr_name] = end_val
            if isinstance(start_val, (list, tuple)):
                s.attrs_current[attr_name] = list(start_val)
            else:
                s.attrs_current[attr_name] = start_val

        anim_speed = max(Settings.get('anim_speed') or 1.0, 0.05)
        if not Settings.get('ui_anim_on'):
            duration = Const.ANIM_INSTANT
            s.delay = 0
        else:
            duration = duration/anim_speed

        s.duration = duration
        s.start_time = None

        if s.delay > 0:
            s.delay_timer = bui.AppTimer(s.delay, s.start_animation)
        else:
            s.start_animation()

    def __del__(s):
        s.cancel()

    def start_animation(s):
        """Start the actual animation after delay."""
        if s.cancelled:
            return
        if callable(s.condition) and not s.condition():
            return
        s.delay_timer = None
        s.start_time = perf_counter()
        s.timer = bui.AppTimer(0.008, s.tick, repeat=True)
        if callable(s.on_start):
            s.on_start()

    def lerp(s, a, b, t):
        """Linear interpolation for single values or tuples/lists."""
        if isinstance(a, (list, tuple)):
            return [s.lerp(av, bv, t) for av, bv in zip(a, b)]
        return a + (b - a) * t

    def tick(s):
        if s.cancelled:
            s.timer = None
            return s.finish()

        if not s.widget.exists():
            s.timer = None
            s.delay_timer = None
            s.cancelled = True
            s._release_callbacks()
            return

        elapsed = perf_counter() - s.start_time
        progress = min(elapsed / s.duration, 1.0)

        t = s.ease_out(progress)

        kwargs = {}
        for attr_name in s.attrs_start:
            start_val = s.attrs_start[attr_name]
            end_val = s.attrs_end[attr_name]

            current_val = s.lerp(start_val, end_val, t)

            s.attrs_current[attr_name] = current_val

            if isinstance(current_val, list):
                current_val = tuple(current_val)

            kwargs[attr_name] = current_val

        if not s.widget.exists():
            s.timer = None
            s.delay_timer = None
            s.cancelled = True
            s._release_callbacks()
            return
        try:
            s.func(s.widget, **kwargs)
        except:
            s.timer = None
            s.delay_timer = None
            s.cancelled = True
            s._release_callbacks()
            return

        if progress >= 1.0:
            s.timer = None
            s.finish()

    def ease_out(s, t):
        return 1 - (1 - t) ** 3

    def _release_callbacks(s):
        """
        Drop callback references once they're no longer needed.
        on_finish in particular can hold a self-referencing CallPartial
        (see the tuple-on_finish handling in __init__, which wraps
        s.reverse -- a bound method of this very instance), so leaving
        it set after it's already fired keeps this instance alive as a
        reference cycle that only the periodic cyclic gc pass can
        collect, instead of being freed immediately by refcounting once
        nothing else references it.

        on_reverse is deliberately NOT cleared here -- it's only ever
        read inside reverse() itself (including synchronously, when a
        tuple on_finish auto-triggers reverse() from within finish()),
        so it's cleared there instead, right after it's actually used.
        """
        s.on_finish = None
        s.on_start = None
        s.on_cancel = None
        s.condition = None

    def finish(s):
        s.finished = True
        on_finish = s.on_finish
        should_call = callable(on_finish) and not s.cancelled
        s._release_callbacks()
        if should_call:
            on_finish()

    def complete(s):
        """Immediately complete the animation by applying final values."""
        if s.cancelled or s.finished:
            return

        on_finish = s.on_finish
        s.cancel()

        if s.widget.exists():
            kwargs = {}
            for attr_name, end_val in s.attrs_end.items():
                if isinstance(end_val, list):
                    end_val = tuple(end_val)
                kwargs[attr_name] = end_val
                s.attrs_current[attr_name] = end_val

            s.func(s.widget, **kwargs)

        s.finished = True
        if callable(on_finish):
            on_finish()

    def cancel(s):
        s.cancelled = True
        s.timer = None
        if s.delay_timer:
            s.delay_timer = None
        on_cancel = s.on_cancel
        should_call = callable(on_cancel) and not s.finished
        exists = s.widget and s.widget.exists()
        s._release_callbacks()
        if not exists:
            return
        if should_call:
            on_cancel()

    def get_state(s):
        """Returns current animation state for all attributes."""
        return {
            'current': s.attrs_current.copy(),
            'start': s.attrs_start.copy(),
            'end': s.attrs_end.copy()
        }

    def reverse(s, **kwargs):
        """
        Create and return a new animation that reverses this one.
        Uses current values as start and original start as end.

        Args:
            Anything __init__ accepts.

        Returns:
            New Animate instance with reversed animation
        """
        callable(s.on_reverse) and s.on_reverse()
        s.on_reverse = None
        s.cancel()

        reversed_attrs = {}
        for attr_name in s.attrs_current:
            current = s.attrs_current[attr_name]
            original_start = s.attrs_start[attr_name]

            if isinstance(current, list):
                current = tuple(current)
            if isinstance(original_start, list):
                original_start = tuple(original_start)

            reversed_attrs[attr_name] = (current, original_start)

        new = {
            'duration': s.duration
        }
        new.update(kwargs)
        return Animate(
            widget=s.widget,
            attrs=reversed_attrs,
            **new
        )

# hardcoded stuff


class _StringsEN:
    MAP_TITLE = 'Movi'
    MAP_DESCRIPTION = 'Movie Maker'
    INSTANCE_DESCRIPTION = 'Three Two One Action!'
    INSTANCE_DESCRIPTION_SHORT = f'Version {__version__}'
    MENUS = (
        'Save & Exit',
        'Clear Session',
        'Load Seed',
        'Copy Seed',
        'Toggle Editor',
        'Record BRP',
        'Wide Preview'
    )
    EDIT_BUTTON = 'Edit'
    SETTINGS = 'Settings'
    EVENT_BUTTON_OFF = 'Event'
    EVENT_BUTTON_ON = 'Back'
    EVENTS = {
        'Node': 'Make a scene node',
        'Camera': 'Tune the camera',
        'Sound': 'Play a sound',
        'FX': 'Emit an effect',
        'Map': 'Control the map',
        'Preset': 'Load a preset',
        'Code': 'Custom code',
        'Seed': 'Project seed'
    }
    LOADED_ENTRIES = 'Loaded {} entries!'
    LOADED_ENTRIES_HELP = 'Seeds are useful aren\'t they?'
    SAVED_AS = 'Saved as {}'
    SAVED_AS_HELP = 'Full path: {}'
    CODE = 'Code'
    CODE_HELP = "Keyframes continue from the\nevent's code. All variables and\nstate are shared."
    SPAZ_CODE_PLACEHOLDER = '\n'.join((
        '# This keyframe runs on the spaz\'s "bot" object',
        '# bot is the Spaz actor - full API exposed',
        '#',
        '# Example: make it walk forward for a bit',
        '# bot.node.move_up_down = 1.0',
        '# bs.timer(1.0, lambda: bot.node.exists() and setattr(bot.node, "move_up_down", 0.0))',
        '#',
        '# Other things you can do:',
        '# bot.node.punch_pressed = True',
        '# bot.handlemessage(bs.StandMessage((0, 1, 0), 0))',
        '# bot.node.handlemessage(bs.CelebrateMessage(duration=2.0))',
    ))
    EXTEND_CODE = 'Parallel Code'
    CODE_EDITOR = 'Code Editor'
    COPY = 'Copy'
    RUN = 'Run'
    SEED = 'Seed'
    PASTE = 'Paste'
    ATTR = 'Attr'
    NEXT = 'Next'
    NODE_ATTR_HELP = 'The node\'s attribute name in attr dict\nbascenev1.newnode(attrs={\'THIS\':value})\nEnter'
    FX_ATTR_HELP = 'The FX\'s attribute name in attr dict\nbascenev1.emitfx(THIS=value)\nEnter'
    MAP_ATTR_HELP = 'The Sound\'s attribute name in attr dict\nsetattr(bascenev1.getactivity().map.node,\'THIS\',value)\nEnter'
    EVAL = 'Eval'
    EVAL_HELP = 'The node\'s attr value in attr dict (evaluated)\nbascenev1.newnode(attrs={\'attr\':THIS})\nEnter'
    OFFSET = 'Offset'
    TEXT = 'Text'
    COLOR = 'Color'
    TIME = 'Time'
    BUBBLE_TEXT_HELP = 'The bubble\'s message\nEnter'
    BUBBLE_COLOR_HELP = 'The bubble\'s color (evaluated tuple)\nEnter'
    BUBBLE_TIME_HELP = 'How long the bubble stays, in seconds\nEnter'
    TYPE = 'Type'
    TYPE_HELP = 'The node\'s type kwarg\nbascenev1.newnode(type=\'THIS\')\nEnter'
    SEED_HELP = 'The Movi\'s project seed. Get it from Square -> Copy Seed\nEnter'
    NAME = 'Name'
    NODE_NAME_HELP = 'The node\'s name kwarg\nbascenev1.newnode(name=\'THIS\')\nEnter'
    SEED_TIP = 'A Movi seed contains all the memory of\nthe project, which is basically a dict of\nentry data. Get your seed by pressing on\nCopy Seed option in the square menu.'
    SEED = 'Seed'
    FX_NAME_HELP = 'The FX name, used only for recognition\nEnter'
    SET = 'Set'
    POP = 'Pop'
    KEYS = 'Keys'
    DONE = 'Done'
    TARGET = 'Traget'
    POSITION = 'Position'
    VALUE = 'Value'
    EVERYWHERE = 'Everywhere'
    LOOP = 'Loop'
    LOAD = 'Load'
    ACTIONS = [
        'Attribute',
        'Code',
        'Volume',
        'Bubble'
    ]
    ACTION_PLACEHOLDER = 'Select an action\nNice UI appears here'
    SOUND_PLACEHOLDER = 'Select a sound'
    PRESET_PLACEHOLDER = 'Select a preset'
    CAMERA_RESET_BUTTON = 'Reset'
    PREVIEW = 'Preview'
    STOP = 'Stop'
    CAMERA_POSITION_CHECK = 'Position'
    CAMERA_TARGET_CHECK = 'Target'
    CAMERA_MANUAL_CHECK = 'Manual'
    CAMERA_ENTRY = 'Camera'
    ERROR_ALREADY_WIDE = (
        'Already wide!',
        'UI is already collapsed blud'
    )
    ERROR_NO_MEMORY = (
        'There\'s nothing to record!',
        'Unless you want a blank BRP lol'
    )
    ERROR_NO_SOUND_SELECTED = (
        'No sound selected!',
        'Pick one from the list first'
    )
    ERROR_SMOL_NO_RESIZE = (
        'Not resizable!',
        'This is an instant action blud'
    )
    ERROR_EMPTY_CODE = (
        'Empty code!',
        'Enter something bud'
    )
    ERROR_INVALID = 'Invalid {}!'
    ERROR_INVALID_HELP = 'Check your input pal'
    ERROR_OUT_OF_RANGE = '{} out of range!'
    ERROR_OUT_OF_RANGE_HELP = 'You went too far'
    ERROR_EMPTY = 'Empty {}!'
    ERROR_EMPTY_HELP = 'Stop leaving empty text boxes around'
    ERROR = 'Error!'
    ERROR_E = 'Error: {}'
    ERROR_HELP = 'You\'re on your own pal'

    def ERROR_EVENT(t, e): return (
        f'{t}: {e}',
        'Your fault, not mine.'
    )
    ERROR_NOT_FOUND = 'Nothing here is called {}'
    ERROR_NOT_FOUND_HELP = 'Yeah, nothing happened'
    ERROR_REACHED_ZERO = (
        'Reached zero!',
        'Yeah I can\'t move it past that'
    )
    ERROR_AT_TOP = (
        'Already at the top!',
        'No entries above to swap'
    )
    ERROR_AT_BOTTOM = (
        'Hit the bottom!',
        'No entries below to swap'
    )
    ERROR_SMALLEST = (
        'Already at smallest size!',
        'Yeah it can\'t be smaller'
    )
    ERROR_SELECT_SOMETHING = (
        'Select something!',
        'Press on an entry to select it'
    )
    ERROR_NOT_PLAYING = (
        'Not even playing!',
        'There is no playhead to hide'
    )
    ERROR_PAUSE_FIRST = (
        'Stop playback first!',
        'The playhead is watching, I can\'t.'
    )
    NO_ACTIONS = (
        'No actions available!',
        'We\'re stuck with it as is'
    )
    INFO_CONFIRM_CLEAR = (
        'Really clear all memory?',
        'Press again to remove everything'
    )
    INFO_MEMORY_CLEARED = (
        'Memory Cleared!',
        'I\'m clean now, regret.'
    )
    INFO_RECORDING_NOW = (
        'Recording now! Press OK to finish recording',
        'Just watch your movie silently'
    )
    STOP_RECORDING_LABEL = 'OK'
    ABOUT_LABEL = '!'
    ABOUT_TITLE = 'About'
    ABOUT_VERSION = 'Version {}'
    ABOUT_TAGLINE = 'Made with love and tea.'
    ABOUT_THANKS = 'Special thanks to: YOU for trying Movi!'
    INFO_RECORDING_SAVED = (
        'Recording Saved!',
        'A wild shiny BRP file was created'
    )
    INFO_NO_CLIPBOARD = (
        'Empty clipboard!',
        'What are you trying to do exactly?'
    )
    INFO_COPIED = (
        'Copied to clipboard!',
        'Hope it\'s in good hands now'
    )
    INFO_PASTED = (
        'Pasted!',
        'Let\'s hope you did\'t click this by mistake'
    )
    INFO_SLOW_DOWN = (
        'Slow down poke',
        'I know you\'re spamming the ui'
    )
    INFO_POP_WHAT = (
        'Pop what?',
        'Buddy write some name'
    )
    INFO_SAVED = (
        'Saved changes!',
        'Go look at it'
    )
    INFO_DISCARDED = (
        'Discarded changes!',
        'Because you changed your mind'
    )

    def INFO_DELETED(n): return (
        f'Deleted "{n}"',
        'Now it\'s gone forever'
    )

    def INFO_DUPLICATED(n): return (
        f'Duplicated "{n}"',
        'Now there\'s two of them. This is getting out of hand.'
    )

    def INFO_ASSIGNED(a): return (
        f'Assigned new attribute {a}',
        'Use the same attr name to overwrite it later'
    )

    def INFO_UPDATED(a): return (
        f'Updated existing attribute {a}',
        'Since you used the same attr name'
    )

    def INFO_POPPED(n): return (
        f'Popped "{n}"',
        'It\'s in a better place now.'
    )
    INFO_TARGET_MODE = (
        'Target mode',
        'Now arrows apply to target boxes'
    )
    INFO_POSITION_MODE = (
        'Position mode',
        'Now arrows apply to position boxes'
    )
    INFO_PREVIEW_ON = (
        'Preview on',
        'Camera changes are previewed live'
    )
    PREVIEW_OFF = (
        'Preview off',
        'Forget I said anything'
    )
    INFO_RESETTED = (
        'Resetted',
        'Everything is clean once again'
    )
    INFO_PLAYING = (
        'Now playing!',
        'What else should\'ve happened?'
    )
    INFO_PAUSED = (
        'Playback paused!',
        'You just froze time'
    )
    INFO_FINISHED = (
        'Playback finished!',
        'The playhead is gone'
    )
    INFO_ADDED_KEY = (
        'Key added!',
        'Yeah, that red dot'
    )
    INFO_EDITED_KEY = (
        'Key edited!',
        'Now it does something else'
    )

    def CONFIRM_DUPLICATE(t): return (
        f'Make another "{t}"?',
        f'Press {Eval.CHAR(Const.TOOLS[6])} again to confirm'
    )

    def CONFIRM_DELETE(t): return (
        f'Really delete "{t}"?',
        f'Press {Eval.CHAR(Const.TOOLS[7])} again to confirm'
    )
    KEYS_ON = 'Keys on {}'
    BYE = (
        'That\'s a wrap!',
        'How fast can you read this'
    )
    EDIT = 'Edit {}'
    WELCOME = '{} joined the studio! Press for more'
    DESCRIPTION_HERE = 'Description here'
    WELCOME_HELP = 'Movi v{}, what could go wrong?'
    COMING_SOON = (
        'Coming soon!',
        'Aka not implemented yet lmao'
    )

    SETTING_ENTRY_DURATION = 'Default Entry Duration'
    SETTING_ANIM_SPEED = 'UI Animation Speed'
    SETTING_BASE_OPACITY = 'Base Opacity'
    SETTING_TEXT_OPACITY = 'Text Opacity'
    SETTING_THEME = 'Theme'
    SETTING_LANGUAGE = 'Language'
    SETTING_AUTOSAVE_ON = 'Autosave'
    SETTING_AUTOSAVE_INTERVAL = 'Autosave Interval (s)'
    SETTING_UI_ANIM_ON = 'UI Animations'
    SETTING_SFX_EDITOR = 'Editor SFX'
    SETTING_SFX_UI = 'UI SFX'
    SETTING_IGNORE_PLAYBACK_ERRORS = 'Ignore Errors During Playback'
    SETTING_SHOW_GRID_2D = 'Show 2D Grid'
    SETTING_SHOW_GRID_3D = 'Show 3D Grid'
    SETTING_BRP_TEXT_EXPORT = 'Also Export Memory JSON'
    SETTING_EXPORT_FILENAME = 'Filename'
    SETTING_TOAST_TOP = 'Toast at Top'
    SETTING_FANCY_AUTOSAVE = 'Fancy Autosave'
    SETTING_TOAST_DURATION = 'Toast Duration (s)'
    SETTING_EPIC_MODE = 'Epic Mode'
    SETTING_DEBUG_HEADER = 'Debug'
    SETTING_DUMP_MEMORY = 'Dump Memory to Log'
    SETTING_DUMP_TIMELINE = 'Dump Timeline to Log'
    SETTING_ASPECT_RATIO = 'Aspect Ratio'
    INFO_DUMPED_MEMORY = (
        'Memory dumped!',
        'Check your console/log'
    )
    INFO_DUMPED_TIMELINE = (
        'Timeline dumped!',
        'Check your console/log'
    )
    INFO_EPIC_ON = (
        'Epic mode engaged!',
        'The autosave panel is showing off now'
    )
    INFO_EPIC_OFF = (
        'Epic mode disengaged',
        'Back to being humble'
    )
    INFO_CHANGING_OPACITY = (
        'Changing opacity...',
        'Refreshing the timeline'
    )
    INFO_CHANGING_THEME = (
        'Changing theme...',
        'Refreshing the timeline'
    )
    INFO_CHANGING_LANGUAGE = (
        'Changing language...',
        'Refreshing the timeline'
    )
    SETTING_FILL_ASPECT_RATIO = 'Fill Outside Frame'
    BLAME = (
        'Did you just click again?',
        'Did you come here to make a film or start a beef with the UI?',
        'This is fine, Everything is fine (Except your movie progress)',
        'The timeline is lonely, Go give it some nodes',
        'You should be keyframing instead of clicking',
        'The real movie was the clicks we made along the way',
        'Your render queue called, It said hello?',
        "Great directors didn't become great by spamming toasts",
        'This button has a family, Think about them',
        "I'm not angry, Just wondering about your priorities",
        "The nodes aren't gonna place themselves bestie",
        "Plot twist there's no achievement for this",
        "Fun fact clicking here doesn't speed up rendering",
        'Your movie could be done by now, Just saying',
        'Breaking news local filmmaker discovers toast notifications',
        'Camera? Unmoved, Nodes? Zero, Hotel? Trivago',
        'This is technically procrastination but go off I guess',
        'Okay but have you considered making something?',
        'The timeline weeps, Can you hear it?',
        'Director mode disabled, Toast mode very enabled',
        'I respect the commitment to absolutely nothing',
        'What are we doing here? Really',
        'Your FPS called, It wants purpose',
        'This is a movie editor not a toast simulator',
        'The entire film industry is waiting on you',
        'Imagine if you put this energy into keyframes',
        'Zero nodes, Zero progress, Infinite clicks',
        "The cinematography handbook doesn't mention this technique",
        'Press triangle, Literally anything else, Please',
        'Your actors are just standing there, Menacingly',
        'This is between you and your productivity now',
        "The toast doesn't judge, I do though",
        'Legendary directors started with zero toasts, Think about it',
        'What would a real director do? Probably not this',
        'Achievement unlocked Professional Time Waster',
        'The editor supports you, Questions you, But supports you',
        'Are we having fun? Is this fun for you?',
        'My expectations were low but holy hell',
        'The universe is vast, Your timeline is empty, Coincidence?',
        "Bro discovered the one button that does nothing and won't stop",
    )


class _StringsMeta(type):
    def __getattr__(cls, name):
        table = _TRANSLATIONS.get(Settings.get('language'))
        if table and name in table:
            return table[name]
        return getattr(_StringsEN, name)


class Strings(metaclass=_StringsMeta):
    """Dynamic, language-aware replacement for the old flat Strings
    class. Every Strings.FOO lookup resolves against the current
    language's translation table, falling back to English (via
    _StringsEN) for anything not yet translated. See _StringsMeta."""
    LANGUAGES = ('English', 'Arabic', 'Japanese', 'French', 'Chinese',
                 'Spanish', 'German', 'Portuguese', 'Russian', 'Korean',
                 'Hindi', 'Italian', 'Bruh')
    LANGUAGE_NAMES = {
        'English':    'English',
        'Arabic':     'العربية',
        'Japanese':   '日本語',
        'French':     'Français',
        'Chinese':    '中文',
        'Spanish':    'Español',
        'German':     'Deutsch',
        'Portuguese': 'Português',
        'Russian':    'Русский',
        'Korean':     '한국어',
        'Hindi':      'हिन्दी',
        'Italian':    'Italiano',
        'Bruh':       'bruh 💀',
    }


_TRANSLATIONS = {
    'Arabic': {
        'SETTINGS': 'الإعدادات', 'EDIT_BUTTON': 'تعديل',
        'EVENT_BUTTON_OFF': 'حدث', 'EVENT_BUTTON_ON': 'رجوع',
        'DONE': 'تم', 'LOAD': 'تحميل', 'SET': 'ضبط', 'POP': 'إزالة',
        'KEYS': 'مفاتيح', 'NAME': 'الاسم', 'TYPE': 'النوع', 'VALUE': 'القيمة',
        'POSITION': 'الموضع', 'TARGET': 'الهدف', 'PREVIEW': 'معاينة',
        'STOP': 'إيقاف', 'COPY': 'نسخ', 'RUN': 'تشغيل', 'PASTE': 'لصق',
        'SEED': 'البذرة', 'CODE': 'الكود', 'NEXT': 'التالي', 'LOOP': 'تكرار',
        'EVERYWHERE': 'في كل مكان', 'ERROR': 'خطأ!',
        'MENUS': ('حفظ وخروج', 'مسح الجلسة', 'تحميل بذرة', 'نسخ البذرة',
                  'تبديل المحرر', 'تسجيل BRP', 'معاينة عريضة'),
        'EVENTS': {'Node': 'إنشاء عقدة مشهد', 'Camera': 'ضبط الكاميرا',
                   'Sound': 'تشغيل صوت', 'FX': 'إطلاق تأثير',
                   'Map': 'التحكم بالخريطة', 'Preset': 'تحميل إعداد مسبق',
                   'Code': 'كود مخصص', 'Seed': 'بذرة المشروع'},
        'SETTING_ENTRY_DURATION': 'مدة الإدخال الافتراضية',
        'SETTING_ANIM_SPEED': 'سرعة حركة الواجهة',
        'SETTING_BASE_OPACITY': 'الشفافية الأساسية',
        'SETTING_TEXT_OPACITY': 'شفافية النص',
        'SETTING_THEME': 'السمة', 'SETTING_LANGUAGE': 'اللغة',
        'SETTING_AUTOSAVE_ON': 'الحفظ التلقائي',
        'SETTING_AUTOSAVE_INTERVAL': 'فاصل الحفظ التلقائي (ث)',
        'SETTING_UI_ANIM_ON': 'حركات الواجهة',
        'SETTING_SFX_EDITOR': 'أصوات المحرر',
        'SETTING_SFX_UI': 'أصوات الواجهة',
        'SETTING_IGNORE_PLAYBACK_ERRORS': 'تجاهل الأخطاء أثناء التشغيل',
        'SETTING_SHOW_GRID_2D': 'إظهار الشبكة ثنائية الأبعاد',
        'SETTING_SHOW_GRID_3D': 'إظهار الشبكة ثلاثية الأبعاد',
        'SETTING_BRP_TEXT_EXPORT': 'تصدير JSON للذاكرة أيضاً',
        'SETTING_EXPORT_FILENAME': 'اسم الملف',
        'SETTING_TOAST_TOP': 'الإشعارات في الأعلى',
        'SETTING_FANCY_AUTOSAVE': 'حفظ تلقائي مزخرف',
        'SETTING_TOAST_DURATION': 'مدة الإشعار (ث)',
        'SETTING_EPIC_MODE': 'الوضع الملحمي',
        'SETTING_DEBUG_HEADER': 'التصحيح',
        'SETTING_DUMP_MEMORY': 'تفريغ الذاكرة إلى السجل',
        'SETTING_DUMP_TIMELINE': 'تفريغ الخط الزمني إلى السجل',
        'SETTING_ASPECT_RATIO': 'نسبة العرض إلى الارتفاع',
        'SETTING_FILL_ASPECT_RATIO': 'ملء ما وراء الإطار',
        'COMING_SOON': ('قريباً!', 'لم يتم تنفيذه بعد'),
    },
    'Japanese': {
        'SETTINGS': '設定', 'EDIT_BUTTON': '編集',
        'EVENT_BUTTON_OFF': 'イベント', 'EVENT_BUTTON_ON': '戻る',
        'DONE': '完了', 'LOAD': '読み込み', 'SET': '設定', 'POP': '削除',
        'KEYS': 'キー', 'NAME': '名前', 'TYPE': 'タイプ', 'VALUE': '値',
        'POSITION': '位置', 'TARGET': 'ターゲット', 'PREVIEW': 'プレビュー',
        'STOP': '停止', 'COPY': 'コピー', 'RUN': '実行', 'PASTE': '貼り付け',
        'SEED': 'シード', 'CODE': 'コード', 'NEXT': '次へ', 'LOOP': 'ループ',
        'EVERYWHERE': 'どこでも', 'ERROR': 'エラー！',
        'MENUS': ('保存して終了', 'セッションをクリア', 'シードを読み込む',
                  'シードをコピー', 'エディタ切替', 'BRPを録画',
                  'ワイドプレビュー'),
        'EVENTS': {'Node': 'シーンノードを作成', 'Camera': 'カメラを調整',
                   'Sound': 'サウンドを再生', 'FX': 'エフェクトを発生',
                   'Map': 'マップを操作', 'Preset': 'プリセットを読み込む',
                   'Code': 'カスタムコード', 'Seed': 'プロジェクトシード'},
        'SETTING_ENTRY_DURATION': 'デフォルトの継続時間',
        'SETTING_ANIM_SPEED': 'UIアニメーション速度',
        'SETTING_BASE_OPACITY': '基本の不透明度',
        'SETTING_TEXT_OPACITY': 'テキストの不透明度',
        'SETTING_THEME': 'テーマ', 'SETTING_LANGUAGE': '言語',
        'SETTING_AUTOSAVE_ON': '自動保存',
        'SETTING_AUTOSAVE_INTERVAL': '自動保存間隔（秒）',
        'SETTING_UI_ANIM_ON': 'UIアニメーション',
        'SETTING_SFX_EDITOR': 'エディタ効果音',
        'SETTING_SFX_UI': 'UI効果音',
        'SETTING_IGNORE_PLAYBACK_ERRORS': '再生中のエラーを無視',
        'SETTING_SHOW_GRID_2D': '2Dグリッドを表示',
        'SETTING_SHOW_GRID_3D': '3Dグリッドを表示',
        'SETTING_BRP_TEXT_EXPORT': 'メモリJSONも書き出す',
        'SETTING_EXPORT_FILENAME': 'ファイル名',
        'SETTING_TOAST_TOP': '通知を上部に表示',
        'SETTING_FANCY_AUTOSAVE': '装飾された自動保存',
        'SETTING_TOAST_DURATION': '通知の表示時間（秒）',
        'SETTING_EPIC_MODE': 'エピックモード',
        'SETTING_DEBUG_HEADER': 'デバッグ',
        'SETTING_DUMP_MEMORY': 'メモリをログに出力',
        'SETTING_DUMP_TIMELINE': 'タイムラインをログに出力',
        'SETTING_ASPECT_RATIO': 'アスペクト比',
        'SETTING_FILL_ASPECT_RATIO': 'フレーム外を塗りつぶす',
        'COMING_SOON': ('近日公開！', 'まだ実装されていません'),
    },
    'French': {
        'SETTINGS': 'Paramètres', 'EDIT_BUTTON': 'Modifier',
        'EVENT_BUTTON_OFF': 'Événement', 'EVENT_BUTTON_ON': 'Retour',
        'DONE': 'Terminé', 'LOAD': 'Charger', 'SET': 'Définir',
        'POP': 'Retirer', 'KEYS': 'Clés', 'NAME': 'Nom', 'TYPE': 'Type',
        'VALUE': 'Valeur', 'POSITION': 'Position', 'TARGET': 'Cible',
        'PREVIEW': 'Aperçu', 'STOP': 'Arrêter', 'COPY': 'Copier',
        'RUN': 'Exécuter', 'PASTE': 'Coller', 'SEED': 'Graine',
        'CODE': 'Code', 'NEXT': 'Suivant', 'LOOP': 'Boucle',
        'EVERYWHERE': 'Partout', 'ERROR': 'Erreur !',
        'MENUS': ('Enregistrer et quitter', 'Effacer la session',
                  'Charger une graine', 'Copier la graine',
                  "Basculer l'éditeur", 'Enregistrer BRP',
                  'Aperçu large'),
        'EVENTS': {'Node': 'Créer un nœud de scène',
                   'Camera': 'Régler la caméra', 'Sound': 'Jouer un son',
                   'FX': 'Émettre un effet', 'Map': 'Contrôler la carte',
                   'Preset': 'Charger un préréglage',
                   'Code': 'Code personnalisé', 'Seed': 'Graine du projet'},
        'SETTING_ENTRY_DURATION': "Durée d'entrée par défaut",
        'SETTING_ANIM_SPEED': "Vitesse d'animation UI",
        'SETTING_BASE_OPACITY': 'Opacité de base',
        'SETTING_TEXT_OPACITY': 'Opacité du texte',
        'SETTING_THEME': 'Thème', 'SETTING_LANGUAGE': 'Langue',
        'SETTING_AUTOSAVE_ON': 'Enregistrement automatique',
        'SETTING_AUTOSAVE_INTERVAL': 'Intervalle auto (s)',
        'SETTING_UI_ANIM_ON': "Animations de l'UI",
        'SETTING_SFX_EDITOR': "Sons de l'éditeur",
        'SETTING_SFX_UI': "Sons de l'UI",
        'SETTING_IGNORE_PLAYBACK_ERRORS':
            'Ignorer les erreurs pendant la lecture',
        'SETTING_SHOW_GRID_2D': 'Afficher la grille 2D',
        'SETTING_SHOW_GRID_3D': 'Afficher la grille 3D',
        'SETTING_BRP_TEXT_EXPORT':
            'Exporter aussi le JSON mémoire',
        'SETTING_EXPORT_FILENAME': 'Nom de fichier',
        'SETTING_TOAST_TOP': 'Notification en haut',
        'SETTING_FANCY_AUTOSAVE': 'Auto-save élaboré',
        'SETTING_TOAST_DURATION': 'Durée de notification (s)',
        'SETTING_EPIC_MODE': 'Mode épique',
        'SETTING_DEBUG_HEADER': 'Débogage',
        'SETTING_DUMP_MEMORY': 'Vider la mémoire dans le journal',
        'SETTING_DUMP_TIMELINE':
            'Vider la chronologie dans le journal',
        'SETTING_ASPECT_RATIO': "Format d'image",
        'SETTING_FILL_ASPECT_RATIO': 'Remplir hors du cadre',
        'COMING_SOON': ('Bientôt disponible !',
                        "Pas encore implémenté"),
    },
    'Chinese': {
        'SETTINGS': '设置', 'EDIT_BUTTON': '编辑',
        'EVENT_BUTTON_OFF': '事件', 'EVENT_BUTTON_ON': '返回',
        'DONE': '完成', 'LOAD': '加载', 'SET': '设置', 'POP': '移除',
        'KEYS': '关键帧', 'NAME': '名称', 'TYPE': '类型', 'VALUE': '值',
        'POSITION': '位置', 'TARGET': '目标', 'PREVIEW': '预览',
        'STOP': '停止', 'COPY': '复制', 'RUN': '运行', 'PASTE': '粘贴',
        'SEED': '种子', 'CODE': '代码', 'NEXT': '下一个', 'LOOP': '循环',
        'EVERYWHERE': '所有位置', 'ERROR': '错误！',
        'MENUS': ('保存并退出', '清除会话', '加载种子', '复制种子',
                  '切换编辑器', '录制BRP', '宽屏预览'),
        'EVENTS': {'Node': '创建场景节点', 'Camera': '调整摄像机',
                   'Sound': '播放声音', 'FX': '触发特效',
                   'Map': '控制地图', 'Preset': '加载预设',
                   'Code': '自定义代码', 'Seed': '项目种子'},
        'SETTING_ENTRY_DURATION': '默认条目时长',
        'SETTING_ANIM_SPEED': '界面动画速度',
        'SETTING_BASE_OPACITY': '基础不透明度',
        'SETTING_TEXT_OPACITY': '文字不透明度',
        'SETTING_THEME': '主题', 'SETTING_LANGUAGE': '语言',
        'SETTING_AUTOSAVE_ON': '自动保存',
        'SETTING_AUTOSAVE_INTERVAL': '自动保存间隔（秒）',
        'SETTING_UI_ANIM_ON': '界面动画',
        'SETTING_SFX_EDITOR': '编辑器音效',
        'SETTING_SFX_UI': '界面音效',
        'SETTING_IGNORE_PLAYBACK_ERRORS': '播放时忽略错误',
        'SETTING_SHOW_GRID_2D': '显示二维网格',
        'SETTING_SHOW_GRID_3D': '显示三维网格',
        'SETTING_BRP_TEXT_EXPORT': '同时导出内存JSON',
        'SETTING_EXPORT_FILENAME': '文件名',
        'SETTING_TOAST_TOP': '提示显示在顶部',
        'SETTING_FANCY_AUTOSAVE': '精美自动保存',
        'SETTING_TOAST_DURATION': '提示持续时间（秒）',
        'SETTING_EPIC_MODE': '史诗模式',
        'SETTING_DEBUG_HEADER': '调试',
        'SETTING_DUMP_MEMORY': '将内存转储到日志',
        'SETTING_DUMP_TIMELINE': '将时间线转储到日志',
        'SETTING_ASPECT_RATIO': '宽高比',
        'SETTING_FILL_ASPECT_RATIO': '填充画面外区域',
        'COMING_SOON': ('即将推出！', '还没实现呢'),
    },
    'Spanish': {
        'SETTINGS': 'Ajustes', 'EDIT_BUTTON': 'Editar',
        'EVENT_BUTTON_OFF': 'Evento', 'EVENT_BUTTON_ON': 'Volver',
        'DONE': 'Hecho', 'LOAD': 'Cargar', 'SET': 'Fijar', 'POP': 'Quitar',
        'KEYS': 'Claves', 'NAME': 'Nombre', 'TYPE': 'Tipo', 'VALUE': 'Valor',
        'POSITION': 'Posición', 'TARGET': 'Objetivo', 'PREVIEW': 'Vista previa',
        'STOP': 'Detener', 'COPY': 'Copiar', 'RUN': 'Ejecutar',
        'PASTE': 'Pegar', 'SEED': 'Semilla', 'CODE': 'Código',
        'NEXT': 'Siguiente', 'LOOP': 'Bucle', 'EVERYWHERE': 'En todas partes',
        'ERROR': '¡Error!',
        'MENUS': ('Guardar y salir', 'Borrar sesión', 'Cargar semilla',
                  'Copiar semilla', 'Cambiar editor', 'Grabar BRP',
                  'Vista previa amplia'),
        'EVENTS': {'Node': 'Crear nodo de escena',
                   'Camera': 'Ajustar cámara', 'Sound': 'Reproducir sonido',
                   'FX': 'Disparar efecto', 'Map': 'Controlar mapa',
                   'Preset': 'Cargar preajuste', 'Code': 'Código personalizado',
                   'Seed': 'Semilla del proyecto'},
        'SETTING_ENTRY_DURATION': 'Duración de entrada predeterminada',
        'SETTING_ANIM_SPEED': 'Velocidad de animación UI',
        'SETTING_BASE_OPACITY': 'Opacidad base',
        'SETTING_TEXT_OPACITY': 'Opacidad del texto',
        'SETTING_THEME': 'Tema', 'SETTING_LANGUAGE': 'Idioma',
        'SETTING_AUTOSAVE_ON': 'Autoguardado',
        'SETTING_AUTOSAVE_INTERVAL': 'Intervalo de autoguardado (s)',
        'SETTING_UI_ANIM_ON': 'Animaciones de UI',
        'SETTING_SFX_EDITOR': 'SFX del editor',
        'SETTING_SFX_UI': 'SFX de la UI',
        'SETTING_IGNORE_PLAYBACK_ERRORS':
            'Ignorar errores durante la reproducción',
        'SETTING_SHOW_GRID_2D': 'Mostrar cuadrícula 2D',
        'SETTING_SHOW_GRID_3D': 'Mostrar cuadrícula 3D',
        'SETTING_BRP_TEXT_EXPORT': 'También exportar JSON de memoria',
        'SETTING_EXPORT_FILENAME': 'Nombre de archivo',
        'SETTING_TOAST_TOP': 'Notificación arriba',
        'SETTING_FANCY_AUTOSAVE': 'Autoguardado elegante',
        'SETTING_TOAST_DURATION': 'Duración de notificación (s)',
        'SETTING_EPIC_MODE': 'Modo épico',
        'SETTING_DEBUG_HEADER': 'Depuración',
        'SETTING_DUMP_MEMORY': 'Volcar memoria al registro',
        'SETTING_DUMP_TIMELINE': 'Volcar línea de tiempo al registro',
        'SETTING_ASPECT_RATIO': 'Relación de aspecto',
        'SETTING_FILL_ASPECT_RATIO': 'Rellenar fuera del cuadro',
        'COMING_SOON': ('¡Próximamente!', 'Aún no implementado'),
    },
    'German': {
        'SETTINGS': 'Einstellungen', 'EDIT_BUTTON': 'Bearbeiten',
        'EVENT_BUTTON_OFF': 'Ereignis', 'EVENT_BUTTON_ON': 'Zurück',
        'DONE': 'Fertig', 'LOAD': 'Laden', 'SET': 'Setzen',
        'POP': 'Entfernen', 'KEYS': 'Schlüssel', 'NAME': 'Name',
        'TYPE': 'Typ', 'VALUE': 'Wert', 'POSITION': 'Position',
        'TARGET': 'Ziel', 'PREVIEW': 'Vorschau', 'STOP': 'Stopp',
        'COPY': 'Kopieren', 'RUN': 'Ausführen', 'PASTE': 'Einfügen',
        'SEED': 'Seed', 'CODE': 'Code', 'NEXT': 'Weiter', 'LOOP': 'Schleife',
        'EVERYWHERE': 'Überall', 'ERROR': 'Fehler!',
        'MENUS': ('Speichern und beenden', 'Sitzung löschen',
                  'Seed laden', 'Seed kopieren', 'Editor wechseln',
                  'BRP aufnehmen', 'Breite Vorschau'),
        'EVENTS': {'Node': 'Szenenknoten erstellen',
                   'Camera': 'Kamera anpassen', 'Sound': 'Sound abspielen',
                   'FX': 'Effekt auslösen', 'Map': 'Karte steuern',
                   'Preset': 'Voreinstellung laden',
                   'Code': 'Eigener Code', 'Seed': 'Projekt-Seed'},
        'SETTING_ENTRY_DURATION': 'Standard-Eintragsdauer',
        'SETTING_ANIM_SPEED': 'UI-Animationsgeschwindigkeit',
        'SETTING_BASE_OPACITY': 'Basisdeckkraft',
        'SETTING_TEXT_OPACITY': 'Textdeckkraft',
        'SETTING_THEME': 'Thema', 'SETTING_LANGUAGE': 'Sprache',
        'SETTING_AUTOSAVE_ON': 'Autospeichern',
        'SETTING_AUTOSAVE_INTERVAL': 'Autospeicher-Intervall (s)',
        'SETTING_UI_ANIM_ON': 'UI-Animationen',
        'SETTING_SFX_EDITOR': 'Editor-SFX',
        'SETTING_SFX_UI': 'UI-SFX',
        'SETTING_IGNORE_PLAYBACK_ERRORS':
            'Fehler während der Wiedergabe ignorieren',
        'SETTING_SHOW_GRID_2D': '2D-Raster anzeigen',
        'SETTING_SHOW_GRID_3D': '3D-Raster anzeigen',
        'SETTING_BRP_TEXT_EXPORT': 'Auch Speicher-JSON exportieren',
        'SETTING_EXPORT_FILENAME': 'Dateiname',
        'SETTING_TOAST_TOP': 'Benachrichtigung oben',
        'SETTING_FANCY_AUTOSAVE': 'Schickes Autospeichern',
        'SETTING_TOAST_DURATION': 'Benachrichtigungsdauer (s)',
        'SETTING_EPIC_MODE': 'Epischer Modus',
        'SETTING_DEBUG_HEADER': 'Debug',
        'SETTING_DUMP_MEMORY': 'Speicher ins Log schreiben',
        'SETTING_DUMP_TIMELINE': 'Zeitleiste ins Log schreiben',
        'SETTING_ASPECT_RATIO': 'Seitenverhältnis',
        'SETTING_FILL_ASPECT_RATIO': 'Außerhalb des Rahmens füllen',
        'COMING_SOON': ('Demnächst!', 'Noch nicht implementiert'),
    },
    'Portuguese': {
        'SETTINGS': 'Configurações', 'EDIT_BUTTON': 'Editar',
        'EVENT_BUTTON_OFF': 'Evento', 'EVENT_BUTTON_ON': 'Voltar',
        'DONE': 'Concluído', 'LOAD': 'Carregar', 'SET': 'Definir',
        'POP': 'Remover', 'KEYS': 'Chaves', 'NAME': 'Nome', 'TYPE': 'Tipo',
        'VALUE': 'Valor', 'POSITION': 'Posição', 'TARGET': 'Alvo',
        'PREVIEW': 'Pré-visualização', 'STOP': 'Parar', 'COPY': 'Copiar',
        'RUN': 'Executar', 'PASTE': 'Colar', 'SEED': 'Semente',
        'CODE': 'Código', 'NEXT': 'Próximo', 'LOOP': 'Loop',
        'EVERYWHERE': 'Em todo lugar', 'ERROR': 'Erro!',
        'MENUS': ('Salvar e sair', 'Limpar sessão', 'Carregar semente',
                  'Copiar semente', 'Trocar editor', 'Gravar BRP',
                  'Pré-visualização ampla'),
        'EVENTS': {'Node': 'Criar nó de cena', 'Camera': 'Ajustar câmera',
                   'Sound': 'Tocar som', 'FX': 'Disparar efeito',
                   'Map': 'Controlar mapa', 'Preset': 'Carregar predefinição',
                   'Code': 'Código personalizado', 'Seed': 'Semente do projeto'},
        'SETTING_ENTRY_DURATION': 'Duração padrão da entrada',
        'SETTING_ANIM_SPEED': 'Velocidade de animação da UI',
        'SETTING_BASE_OPACITY': 'Opacidade base',
        'SETTING_TEXT_OPACITY': 'Opacidade do texto',
        'SETTING_THEME': 'Tema', 'SETTING_LANGUAGE': 'Idioma',
        'SETTING_AUTOSAVE_ON': 'Salvamento automático',
        'SETTING_AUTOSAVE_INTERVAL': 'Intervalo de salvamento (s)',
        'SETTING_UI_ANIM_ON': 'Animações da UI',
        'SETTING_SFX_EDITOR': 'SFX do editor',
        'SETTING_SFX_UI': 'SFX da UI',
        'SETTING_IGNORE_PLAYBACK_ERRORS':
            'Ignorar erros durante a reprodução',
        'SETTING_SHOW_GRID_2D': 'Mostrar grade 2D',
        'SETTING_SHOW_GRID_3D': 'Mostrar grade 3D',
        'SETTING_BRP_TEXT_EXPORT': 'Também exportar JSON de memória',
        'SETTING_EXPORT_FILENAME': 'Nome do arquivo',
        'SETTING_TOAST_TOP': 'Notificação no topo',
        'SETTING_FANCY_AUTOSAVE': 'Salvamento automático chique',
        'SETTING_TOAST_DURATION': 'Duração da notificação (s)',
        'SETTING_EPIC_MODE': 'Modo épico',
        'SETTING_DEBUG_HEADER': 'Depuração',
        'SETTING_DUMP_MEMORY': 'Despejar memória no log',
        'SETTING_DUMP_TIMELINE': 'Despejar linha do tempo no log',
        'SETTING_ASPECT_RATIO': 'Proporção',
        'SETTING_FILL_ASPECT_RATIO': 'Preencher fora do quadro',
        'COMING_SOON': ('Em breve!', 'Ainda não implementado'),
    },
    'Russian': {
        'SETTINGS': 'Настройки', 'EDIT_BUTTON': 'Изменить',
        'EVENT_BUTTON_OFF': 'Событие', 'EVENT_BUTTON_ON': 'Назад',
        'DONE': 'Готово', 'LOAD': 'Загрузить', 'SET': 'Задать',
        'POP': 'Удалить', 'KEYS': 'Ключи', 'NAME': 'Имя', 'TYPE': 'Тип',
        'VALUE': 'Значение', 'POSITION': 'Позиция', 'TARGET': 'Цель',
        'PREVIEW': 'Превью', 'STOP': 'Стоп', 'COPY': 'Копировать',
        'RUN': 'Запуск', 'PASTE': 'Вставить', 'SEED': 'Сид',
        'CODE': 'Код', 'NEXT': 'Далее', 'LOOP': 'Цикл',
        'EVERYWHERE': 'Везде', 'ERROR': 'Ошибка!',
        'MENUS': ('Сохранить и выйти', 'Очистить сессию',
                  'Загрузить сид', 'Копировать сид',
                  'Сменить редактор', 'Записать BRP',
                  'Широкий просмотр'),
        'EVENTS': {'Node': 'Создать узел сцены',
                   'Camera': 'Настроить камеру', 'Sound': 'Воспроизвести звук',
                   'FX': 'Запустить эффект', 'Map': 'Управлять картой',
                   'Preset': 'Загрузить пресет', 'Code': 'Свой код',
                   'Seed': 'Сид проекта'},
        'SETTING_ENTRY_DURATION': 'Длительность записи по умолчанию',
        'SETTING_ANIM_SPEED': 'Скорость анимации интерфейса',
        'SETTING_BASE_OPACITY': 'Базовая непрозрачность',
        'SETTING_TEXT_OPACITY': 'Непрозрачность текста',
        'SETTING_THEME': 'Тема', 'SETTING_LANGUAGE': 'Язык',
        'SETTING_AUTOSAVE_ON': 'Автосохранение',
        'SETTING_AUTOSAVE_INTERVAL': 'Интервал автосохранения (с)',
        'SETTING_UI_ANIM_ON': 'Анимации интерфейса',
        'SETTING_SFX_EDITOR': 'Звуки редактора',
        'SETTING_SFX_UI': 'Звуки интерфейса',
        'SETTING_IGNORE_PLAYBACK_ERRORS':
            'Игнорировать ошибки при воспроизведении',
        'SETTING_SHOW_GRID_2D': 'Показать 2D-сетку',
        'SETTING_SHOW_GRID_3D': 'Показать 3D-сетку',
        'SETTING_BRP_TEXT_EXPORT': 'Также экспортировать JSON памяти',
        'SETTING_EXPORT_FILENAME': 'Имя файла',
        'SETTING_TOAST_TOP': 'Уведомление сверху',
        'SETTING_FANCY_AUTOSAVE': 'Красивое автосохранение',
        'SETTING_TOAST_DURATION': 'Длительность уведомления (с)',
        'SETTING_EPIC_MODE': 'Эпичный режим',
        'SETTING_DEBUG_HEADER': 'Отладка',
        'SETTING_DUMP_MEMORY': 'Сбросить память в лог',
        'SETTING_DUMP_TIMELINE': 'Сбросить таймлайн в лог',
        'SETTING_ASPECT_RATIO': 'Соотношение сторон',
        'SETTING_FILL_ASPECT_RATIO': 'Заполнять за пределами кадра',
        'COMING_SOON': ('Скоро!', 'Пока не реализовано'),
    },
    'Korean': {
        'SETTINGS': '설정', 'EDIT_BUTTON': '편집',
        'EVENT_BUTTON_OFF': '이벤트', 'EVENT_BUTTON_ON': '뒤로',
        'DONE': '완료', 'LOAD': '불러오기', 'SET': '설정', 'POP': '제거',
        'KEYS': '키', 'NAME': '이름', 'TYPE': '유형', 'VALUE': '값',
        'POSITION': '위치', 'TARGET': '대상', 'PREVIEW': '미리보기',
        'STOP': '정지', 'COPY': '복사', 'RUN': '실행', 'PASTE': '붙여넣기',
        'SEED': '시드', 'CODE': '코드', 'NEXT': '다음', 'LOOP': '반복',
        'EVERYWHERE': '모든 곳', 'ERROR': '오류!',
        'MENUS': ('저장 후 종료', '세션 지우기', '시드 불러오기',
                  '시드 복사', '에디터 전환', 'BRP 녹화',
                  '와이드 미리보기'),
        'EVENTS': {'Node': '씬 노드 생성', 'Camera': '카메라 조정',
                   'Sound': '사운드 재생', 'FX': '이펙트 실행',
                   'Map': '맵 제어', 'Preset': '프리셋 불러오기',
                   'Code': '사용자 코드', 'Seed': '프로젝트 시드'},
        'SETTING_ENTRY_DURATION': '기본 항목 길이',
        'SETTING_ANIM_SPEED': 'UI 애니메이션 속도',
        'SETTING_BASE_OPACITY': '기본 불투명도',
        'SETTING_TEXT_OPACITY': '텍스트 불투명도',
        'SETTING_THEME': '테마', 'SETTING_LANGUAGE': '언어',
        'SETTING_AUTOSAVE_ON': '자동 저장',
        'SETTING_AUTOSAVE_INTERVAL': '자동 저장 간격(초)',
        'SETTING_UI_ANIM_ON': 'UI 애니메이션',
        'SETTING_SFX_EDITOR': '에디터 효과음',
        'SETTING_SFX_UI': 'UI 효과음',
        'SETTING_IGNORE_PLAYBACK_ERRORS': '재생 중 오류 무시',
        'SETTING_SHOW_GRID_2D': '2D 그리드 표시',
        'SETTING_SHOW_GRID_3D': '3D 그리드 표시',
        'SETTING_BRP_TEXT_EXPORT': '메모리 JSON도 내보내기',
        'SETTING_EXPORT_FILENAME': '파일 이름',
        'SETTING_TOAST_TOP': '알림을 상단에 표시',
        'SETTING_FANCY_AUTOSAVE': '화려한 자동 저장',
        'SETTING_TOAST_DURATION': '알림 지속 시간(초)',
        'SETTING_EPIC_MODE': '에픽 모드',
        'SETTING_DEBUG_HEADER': '디버그',
        'SETTING_DUMP_MEMORY': '메모리를 로그로 덤프',
        'SETTING_DUMP_TIMELINE': '타임라인을 로그로 덤프',
        'SETTING_ASPECT_RATIO': '화면 비율',
        'SETTING_FILL_ASPECT_RATIO': '프레임 밖 채우기',
        'COMING_SOON': ('곧 공개!', '아직 구현되지 않음'),
    },
    'Hindi': {
        'SETTINGS': 'सेटिंग्स', 'EDIT_BUTTON': 'संपादित करें',
        'EVENT_BUTTON_OFF': 'इवेंट', 'EVENT_BUTTON_ON': 'वापस',
        'DONE': 'हो गया', 'LOAD': 'लोड करें', 'SET': 'सेट करें',
        'POP': 'हटाएं', 'KEYS': 'कीज़', 'NAME': 'नाम', 'TYPE': 'प्रकार',
        'VALUE': 'मान', 'POSITION': 'स्थिति', 'TARGET': 'लक्ष्य',
        'PREVIEW': 'पूर्वावलोकन', 'STOP': 'रोकें', 'COPY': 'कॉपी करें',
        'RUN': 'चलाएं', 'PASTE': 'पेस्ट करें', 'SEED': 'सीड',
        'CODE': 'कोड', 'NEXT': 'अगला', 'LOOP': 'लूप',
        'EVERYWHERE': 'हर जगह', 'ERROR': 'त्रुटि!',
        'MENUS': ('सेव करके बाहर निकलें', 'सत्र साफ़ करें',
                  'सीड लोड करें', 'सीड कॉपी करें', 'एडिटर बदलें',
                  'BRP रिकॉर्ड करें', 'वाइड पूर्वावलोकन'),
        'EVENTS': {'Node': 'सीन नोड बनाएं', 'Camera': 'कैमरा समायोजित करें',
                   'Sound': 'ध्वनि चलाएं', 'FX': 'इफ़ेक्ट चलाएं',
                   'Map': 'मैप नियंत्रित करें', 'Preset': 'प्रीसेट लोड करें',
                   'Code': 'कस्टम कोड', 'Seed': 'प्रोजेक्ट सीड'},
        'SETTING_ENTRY_DURATION': 'डिफ़ॉल्ट एंट्री अवधि',
        'SETTING_ANIM_SPEED': 'UI एनिमेशन गति',
        'SETTING_BASE_OPACITY': 'आधार अपारदर्शिता',
        'SETTING_TEXT_OPACITY': 'टेक्स्ट अपारदर्शिता',
        'SETTING_THEME': 'थीम', 'SETTING_LANGUAGE': 'भाषा',
        'SETTING_AUTOSAVE_ON': 'ऑटोसेव',
        'SETTING_AUTOSAVE_INTERVAL': 'ऑटोसेव अंतराल (से)',
        'SETTING_UI_ANIM_ON': 'UI एनिमेशन',
        'SETTING_SFX_EDITOR': 'एडिटर SFX',
        'SETTING_SFX_UI': 'UI SFX',
        'SETTING_IGNORE_PLAYBACK_ERRORS':
            'प्लेबैक के दौरान त्रुटियां अनदेखा करें',
        'SETTING_SHOW_GRID_2D': '2D ग्रिड दिखाएं',
        'SETTING_SHOW_GRID_3D': '3D ग्रिड दिखाएं',
        'SETTING_BRP_TEXT_EXPORT': 'मेमोरी JSON भी एक्सपोर्ट करें',
        'SETTING_EXPORT_FILENAME': 'फ़ाइल नाम',
        'SETTING_TOAST_TOP': 'सूचना ऊपर दिखाएं',
        'SETTING_FANCY_AUTOSAVE': 'स्टाइलिश ऑटोसेव',
        'SETTING_TOAST_DURATION': 'सूचना अवधि (से)',
        'SETTING_EPIC_MODE': 'एपिक मोड',
        'SETTING_DEBUG_HEADER': 'डीबग',
        'SETTING_DUMP_MEMORY': 'मेमोरी को लॉग में डंप करें',
        'SETTING_DUMP_TIMELINE': 'टाइमलाइन को लॉग में डंप करें',
        'SETTING_ASPECT_RATIO': 'आस्पेक्ट रेशियो',
        'SETTING_FILL_ASPECT_RATIO': 'फ्रेम के बाहर भरें',
        'COMING_SOON': ('जल्द आ रहा है!', 'अभी लागू नहीं हुआ'),
    },
    'Italian': {
        'SETTINGS': 'Impostazioni', 'EDIT_BUTTON': 'Modifica',
        'EVENT_BUTTON_OFF': 'Evento', 'EVENT_BUTTON_ON': 'Indietro',
        'DONE': 'Fatto', 'LOAD': 'Carica', 'SET': 'Imposta',
        'POP': 'Rimuovi', 'KEYS': 'Chiavi', 'NAME': 'Nome', 'TYPE': 'Tipo',
        'VALUE': 'Valore', 'POSITION': 'Posizione', 'TARGET': 'Obiettivo',
        'PREVIEW': 'Anteprima', 'STOP': 'Ferma', 'COPY': 'Copia',
        'RUN': 'Esegui', 'PASTE': 'Incolla', 'SEED': 'Seed',
        'CODE': 'Codice', 'NEXT': 'Avanti', 'LOOP': 'Ciclo',
        'EVERYWHERE': 'Ovunque', 'ERROR': 'Errore!',
        'MENUS': ('Salva ed esci', 'Cancella sessione', 'Carica seed',
                  'Copia seed', 'Cambia editor', 'Registra BRP',
                  'Anteprima ampia'),
        'EVENTS': {'Node': 'Crea nodo scena', 'Camera': 'Regola camera',
                   'Sound': 'Riproduci suono', 'FX': 'Avvia effetto',
                   'Map': 'Controlla mappa', 'Preset': 'Carica preset',
                   'Code': 'Codice personalizzato', 'Seed': 'Seed del progetto'},
        'SETTING_ENTRY_DURATION': 'Durata voce predefinita',
        'SETTING_ANIM_SPEED': 'Velocità animazioni UI',
        'SETTING_BASE_OPACITY': 'Opacità base',
        'SETTING_TEXT_OPACITY': 'Opacità del testo',
        'SETTING_THEME': 'Tema', 'SETTING_LANGUAGE': 'Lingua',
        'SETTING_AUTOSAVE_ON': 'Salvataggio automatico',
        'SETTING_AUTOSAVE_INTERVAL': 'Intervallo autosalvataggio (s)',
        'SETTING_UI_ANIM_ON': 'Animazioni UI',
        'SETTING_SFX_EDITOR': 'SFX editor',
        'SETTING_SFX_UI': 'SFX UI',
        'SETTING_IGNORE_PLAYBACK_ERRORS':
            "Ignora errori durante la riproduzione",
        'SETTING_SHOW_GRID_2D': 'Mostra griglia 2D',
        'SETTING_SHOW_GRID_3D': 'Mostra griglia 3D',
        'SETTING_BRP_TEXT_EXPORT': 'Esporta anche JSON di memoria',
        'SETTING_EXPORT_FILENAME': 'Nome file',
        'SETTING_TOAST_TOP': 'Notifica in alto',
        'SETTING_FANCY_AUTOSAVE': 'Autosalvataggio elegante',
        'SETTING_TOAST_DURATION': 'Durata notifica (s)',
        'SETTING_EPIC_MODE': 'Modalità epica',
        'SETTING_DEBUG_HEADER': 'Debug',
        'SETTING_DUMP_MEMORY': 'Scarica memoria nel log',
        'SETTING_DUMP_TIMELINE': 'Scarica timeline nel log',
        'SETTING_ASPECT_RATIO': 'Proporzioni',
        'SETTING_FILL_ASPECT_RATIO': "Riempi fuori dall'inquadratura",
        'COMING_SOON': ('Prossimamente!', 'Non ancora implementato'),
    },
    'Bruh': {
        'SETTINGS': 'settings ig', 'EDIT_BUTTON': 'edit',
        'EVENT_BUTTON_OFF': 'event', 'EVENT_BUTTON_ON': 'bye',
        'DONE': 'done ✅', 'LOAD': 'load', 'SET': 'set', 'POP': 'yeet it',
        'KEYS': 'keys', 'NAME': 'name', 'TYPE': 'type', 'VALUE': 'value',
        'POSITION': 'position', 'TARGET': 'target', 'PREVIEW': 'preview',
        'STOP': 'stop', 'COPY': 'copy', 'RUN': 'run it', 'PASTE': 'paste',
        'SEED': 'seed', 'CODE': 'code', 'NEXT': 'next', 'LOOP': 'loop',
        'EVERYWHERE': 'literally everywhere', 'ERROR': 'bro it broke 💀',
        'MENUS': ('save n dip', 'wipe the session lol',
                  'load a seed ig', 'copy the seed',
                  'swap editors', 'record some brp fr',
                  'wide preview (chefs kiss)'),
        'EVENTS': {'Node': 'spawn a scene node ig',
                   'Camera': 'nudge the camera bro',
                   'Sound': 'blast a sound',
                   'FX': 'send it (fx edition)',
                   'Map': 'mess with the map',
                   'Preset': 'load a preset fr',
                   'Code': 'ur cursed custom code',
                   'Seed': 'the project seed no cap'},
        'SETTING_ENTRY_DURATION': 'default entry duration ig',
        'SETTING_ANIM_SPEED': 'ui anim speed (zoomies)',
        'SETTING_BASE_OPACITY': 'base opacity fr fr',
        'SETTING_TEXT_OPACITY': 'text opacity but make it hit different',
        'SETTING_THEME': 'theme (pick ur vibe)',
        'SETTING_LANGUAGE': 'language (u already found it lol)',
        'SETTING_AUTOSAVE_ON': 'autosave (trust)',
        'SETTING_AUTOSAVE_INTERVAL': 'autosave interval (s) bro',
        'SETTING_UI_ANIM_ON': 'ui animations',
        'SETTING_SFX_EDITOR': 'editor sfx go brrr',
        'SETTING_SFX_UI': 'ui sfx',
        'SETTING_IGNORE_PLAYBACK_ERRORS':
            'ignore errors during playback, we ball',
        'SETTING_SHOW_GRID_2D': 'show that 2d grid',
        'SETTING_SHOW_GRID_3D': 'show that 3d grid',
        'SETTING_BRP_TEXT_EXPORT': 'also export the memory json ez',
        'SETTING_EXPORT_FILENAME': 'filename ig',
        'SETTING_TOAST_TOP': 'toast goes up top',
        'SETTING_FANCY_AUTOSAVE': 'fancy autosave (it slaps)',
        'SETTING_TOAST_DURATION': 'toast duration (s)',
        'SETTING_EPIC_MODE': 'epic mode 😳',
        'SETTING_DEBUG_HEADER': 'debug (send logs to the group chat)',
        'SETTING_DUMP_MEMORY': 'dump memory to the log, no cap',
        'SETTING_DUMP_TIMELINE': 'dump the timeline to the log too',
        'SETTING_ASPECT_RATIO': 'aspect ratio',
        'SETTING_FILL_ASPECT_RATIO': 'fill outside the frame ig',
        'COMING_SOON': ('soon (tm)',
                        'aka not done yet, screenshot this and send to the telegram group'),
    },
}


class Const:
    BA_DATA = join(
        dirname(
            bui.app.env.cache_directory
        ), 'ballistica_files', 'ba_data'
    )
    REPLAYS = join(
        dirname(
            dirname(
                bui.app.env.cache_directory
            )
        ), 'files', 'bombsquad_config', 'replays'
    )
    STOCK_REPLAY = '__lastReplay.brp'
    EXPORT_PREFIX = 'movi_'
    EXPORT_SUFFIX = '.brp'
    CONFIG_HEAD = '# MOVI '
    CONFIG_PREFIX = 'movi_'
    CONFIG_DEV_KEY = 'Show Dev Console Button'
    CONFIG_FPS_KEY = 'Show FPS'
    EXIT_BOUNDS = (0, 0, 0, 0, 35, 0)
    BA_LAG_BIG = 1.5
    BA_LAG = 0.04
    BA_LAG_SMALL = 0.01
    INVISIBLE = (0, 0, 0, 0)
    SCALE_BA = {
        bui.UIScale.SMALL: 1.275,
        bui.UIScale.MEDIUM: 1,
        bui.UIScale.LARGE: 0.764
    }
    SCALE_REAL = {
        bui.UIScale.SMALL: 0.93,
        bui.UIScale.MEDIUM: 0.9,
        bui.UIScale.LARGE: 0.7
    }
    SKIN = 'white'
    EMPTY = 'empty'
    SHADOW = 'softRect'
    GLOW = 'uniform'
    ALIGN = 'center'
    KEY = 'circleZigZag'
    PLAY_BUTTON = 'PLAY_BUTTON'
    PAUSE_BUTTON = 'PAUSE_BUTTON'
    CONTROLS = (
        ('PLAY_BUTTON', 'PAUSE_BUTTON'),
        'BACK'
    )
    PIN_POINT = 'PLAY_STATION_CROSS_BUTTON'
    TOOLS = (
        'RIGHT_ARROW',
        'LEFT_ARROW',
        'FAST_FORWARD_BUTTON',
        'REWIND_BUTTON',
        'UP_ARROW',
        'DOWN_ARROW',
        'DPAD_CENTER_BUTTON',
        'PLAY_STATION_CROSS_BUTTON'
    )
    EVENT_KEYS = {
        0: (0, 1, 3),
        2: (2,),
        6: (1,)
    }
    CAMERA_TOOLS = (
        '-',
        'LEFT_ARROW',
        'LEFT_BUTTON',
        'DOWN_ARROW',
        'DPAD_CENTER_BUTTON',
        'UP_ARROW',
        '+',
        'RIGHT_ARROW',
        'RIGHT_BUTTON'
    )
    OK_SOUND = 'deek'
    BAD_SOUND = 'block'
    ACTION_SOUND = 'gunCocking'
    GOOD_SOUND = 'dingSmall'
    TRIANGLE = 'PLAY_STATION_TRIANGLE_BUTTON'
    SQUARE = 'PLAY_STATION_SQUARE_BUTTON'
    CIRCLE = 'PLAY_STATION_CIRCLE_BUTTON'
    BACK = 'BACK'
    THEME_ICON = 'LOGO_FLAT'
    def DO_NOTHING(): return None

    FONT_METRICS = {
        ' ': 6.9609375, '!': 7.8203125, '"': 7.9921875, '#': 14.8671875,
        '$': 13.921875, '%': 19.078125, '&': 23.03125, "'": 5.328125,
        '(': 11.0859375, ')': 11.0859375, '*': 15.5546875, '+': 13.921875,
        ',': 6.9609375, '-': 6.015625, '.': 6.9609375, '/': 12.71875,
        '0': 13.921875, '1': 13.921875, '2': 13.921875, '3': 13.921875,
        '4': 13.921875, '5': 13.921875, '6': 13.921875, '7': 13.921875,
        '8': 13.921875, '9': 13.921875, ':': 6.9609375, ';': 6.9609375,
        '<': 13.921875, '=': 13.921875, '>': 13.921875, '?': 11.515625,
        '@': 20.96875, 'A': 16.7578125, 'B': 15.8984375, 'C': 15.5546875,
        'D': 16.15625, 'E': 14.3515625, 'F': 13.1484375, 'G': 15.8984375,
        'H': 17.1015625, 'I': 7.90625, 'J': 9.625, 'K': 15.7265625,
        'L': 13.234375, 'M': 20.8828125, 'N': 17.1015625, 'O': 17.1015625,
        'P': 15.0390625, 'Q': 17.359375, 'R': 15.984375, 'S': 15.5546875,
        'T': 15.0390625, 'U': 16.15625, 'V': 15.46875, 'W': 20.453125,
        'X': 15.296875, 'Y': 15.46875, 'Z': 14.953125, '[': 9.625,
        '\\': 8.6796875, ']': 9.625, '^': 14.09375, '_': 12.03125,
        '`': 9.28125, 'a': 12.546875, 'b': 12.890625, 'c': 11.7734375,
        'd': 13.0625, 'e': 12.6328125, 'f': 8.59375, 'g': 13.40625,
        'h': 13.0625, 'i': 6.359375, 'j': 7.3046875, 'k': 12.375,
        'l': 6.1875, 'm': 20.3671875, 'n': 13.3203125, 'o': 13.0625,
        'p': 12.6328125, 'q': 12.6328125, 'r': 10.2265625, 's': 12.4609375,
        't': 8.765625, 'u': 13.40625, 'v': 12.375, 'w': 17.359375,
        'x': 12.2890625, 'y': 12.375, 'z': 11.2578125, '{': 9.625,
        '|': 8.1640625, '}': 9.625, '~': 13.921875,
    }
    AUTOSAVE_INTERVAL = 25
    AUTOSAVE_AREA = 70
    AUTOSAVE_MARGIN = 20
    AUTOSAVE_PARENT_SIZE = 100
    AUTOSAVE_PARENT_DUR = 0.3
    AUTOSAVE_CHILD_GROW_DUR = 0.25
    AUTOSAVE_CHILD_WAIT1 = 0.2
    AUTOSAVE_CHILD_MOVE_DUR = 0.25
    AUTOSAVE_CHILD_WAIT2 = 0.3
    AUTOSAVE_SWAP_COUNT = 8
    AUTOSAVE_MIN_SPLIT_DIFF = 0.18
    AUTOSAVE_BG_WIDTH = 300
    AUTOSAVE_BG_PADDING = 16
    AUTOSAVE_BG_POP_SCALE = 1.1667
    AUTOSAVE_COMPACT_BG_PAD = 40
    EPIC_SWAP_MULT = 2
    EPIC_POP_MULT = 1.15
    AUTOSAVE_STATIC_HOLD = 2.5

    ANIM_INSTANT = 0.001
    GRID_SPAN = 12
    AUTOSAVE_MIN_INTERVAL = 8
    GRID_STEP = 2
    GRID_MARK_SIZE = 0.15
    GRID_2D_DIVISIONS = 12
    GRID_2D_THICKNESS = 2
    GRID_SPAN_3D = 6
    GRID_STEP_3D = 2
    EXPORT_TEXT_SUFFIX = '.json'
    EXPORT_DEFAULT_TEMPLATE = 'movi_{uuid}'
    ASPECT_RATIO_VALUES = {
        '16:9': 16/9,
        '4:3': 4/3,
        '21:9': 21/9,
        '1:1': 1.0
    }
    FILL_ASPECT_OVERSCAN = 8
    SETTINGS_ROW_H = 26
    SETTINGS_ROW_GAP = 10
    SETTINGS_NUMERIC_W = 70
    SETTINGS_CYCLE_W = 110

    class _Silent:
        """Stand-in returned by Eval.SOUND when the relevant SFX
        category is muted in Settings - has the same .play() shape
        as a real bui.Sound so every existing call site keeps working
        unmodified."""
        def play(s, *a, **k): pass
    SILENT_SOUND = _Silent()
    AUTOSAVE_TITLES = (
        'Saving your chaos...',
        'Backing up the damage...',
        'Committing your nonsense...',
        'Saving before you break it...',
        'Snapshotting the mess...',
        'Autosave, doing its one job...',
        'Committing to a bit...',
        'Quietly saving your seed...',
        'Backing up before you regret this...',
        'Saving. Try not to jinx it...',
        'Saving the director\'s cut...',
        'Yelling "Cut!" to back this up...',
        'Printing the dailies...',
        'Fixing it in post...',
        'Saving this cinematic masterpiece...',
        'Telling the actors to hold still...',
        'Archiving the blooper reel...',
        'Securing the Oscar nomination...',
        'Documenting your directorial debut...',
        'Waiting for the camera to focus...',
        'Saving... grab some popcorn.',
        'Rolling the credits on this session...',
        'Sending the footage to editing...',
        'Protecting your keyframes...',
        'Packing memory into CJK...',
        'Stashing your spaghetti code...',
        'Making sure the Spazes survive...',
        'Stashing your explosive ideas...',
        'Saving before the next explosion...',
        'Packing nodes into boxes...',
        'Sweeping the timeline for loose bombs...',
        'Updating the BRP manifest...',
        'Baking the keyframes...',
        'Reticulating splines...',
        'Securing the evidence...',
        'Saving your "art"...',
        'Preserving this timeline disaster...',
        'Saving... don\'t touch anything.',
        'Encoding your questionable choices...',
        'Saving before the engine crashes...',
        'Adding another layer of duct tape...',
        'Saving you from yourself...',
        'Preventing a total cinematic disaster...',
        'Hold please, writing to disk...',
        'Quick, act natural. Saving...',
        'Writing your "genius" to a file...',
        'Putting the timeline on ice...',
        'Holding the code together with glue...'
    )
    AUTOSAVE_TIPS = (
        'Wide Preview collapses the UI.\nTry it sometime.',
        'Toggle Editor hides all UI if it\'s\never in your way.',
        'Presets are just entries someone\nalready tuned.',
        'Code events run parallel to their\nown keyframes.',
        'Duplicating an entry is faster\nthan rebuilding it.',
        'Recording makes a BRP which is\njust replays.',
        'The square menu has seven options.\nTry one you haven\'t.',
        'Triangle just opens your squad.\nNothing fancier.',
        'Spam the UI too fast and it\'ll\ntell you to slow down.',
        'A seed is your whole project\nencoded as text.',
        'Always copy your seed before\nbig changes. There is no\nCtrl+Z in Movi!',
        'Need to reuse a complex setup?\nDuplicating an entry copies\nits keyframes too.',
        'You can make characters talk\nby adding a Bubble action\nin the Keys menu.',
        'Use Keyframes to change a node\'s\nattributes mid-scene without\ncoding.',
        'Need a soundtrack to fade out?\nUse a Volume keyframe on a\nSound entry.',
        'Map events can completely\nalter the arena\'s lighting,\ntint, and vignette.',
        'Evaluated attribute boxes let\nyou run Python directly to\nfetch textures or sounds.',
        'Your seeds look like ancient\ntexts because Movi uses CJK\ncharacters for compression.',
        'Movi was made with love and tea.\nProbably mostly tea.',
        'To create ambient background\nmusic, add a Sound event and\ncheck Everywhere and Loop.',
        'Code Keyframes run as children\nof the main event, meaning\nthey share the same variables.',
        'Recorded projects are exported\nas .brp files prefixed with\n"movi_" in your replays.',
        'Autosave is doing its best\nright now. Please do not\nperceive it.',
        'Who needs a render farm\nwhen you have BombSquad\nand a dream?',
        'Made a mistake with a\nkeyframe? Use the "Pop" button\nin the Keys menu to delete it.',
        'Keyframe offsets are relative\nto the start of the event.\n0.0 means it happens instantly.',
        'You can set a keyframe to\nexecute exact code. Perfect for\nfiring complex logic mid-scene.',
        'Movi automatically formats\nmesh and texture names for you.\nNo need to type bs.getmesh()!',
        'Need a dummy target? A locator\nnode is invisible in-game but\ngreat for the camera to track.',
        'You can share your projects\nwith other directors by copying\nthe Seed and sending the text.',
        'When you\'re ready to record a\nBRP, hide the UI with Wide\nPreview for a clean capture.',
        'Yes, the Code Editor lets\nyou do *anything*. Try not to\ndelete the universe by accident.',
        'Welcome to Movi v1.0.\nIf you find a bug, let\'s just\ncall it an avant-garde feature.',
        'Every masterpiece takes time.\nOr in this case, a lot of\nmeticulously placed keyframes.',
        'Need a cinematic look? Crank\nup the map\'s vignette_outer\nand vignette_inner attributes.',
        'The Random Sound Roulette\npreset is a highly effective\nway to annoy everyone on set.',
        'When playback stops, Movi\ncleans up all spawned nodes\nautomatically. No mess left!',
        'Map events let you swap the\narena mid-scene. Instant\nteleportation budget unlocked.',
        'The Playhead is your best\nfriend. Just click Play and\nwatch your timeline come to life.',
        'Spaz characters can be spawned\nvia Code events. Check the\nBasic Spaz preset to see how.',
        'The shared dictionary in\nthe Code Editor lets your\nseparate scripts talk.',
        'Seeds are pure text. Paste\nthem in a Notepad file to\nbuild your own movie library!',
        'If your actors aren\'t hitting\ntheir marks, remember: you\nliterally programmed them.',
        'No Spazes were harmed in\nthe making of this movie.\nWell, maybe just a few.',
        'Because we both know you\nweren\'t going to back\nthis up manually.',
        'We can fix it in post.\nWait, this IS post.\nUh oh.'
    )


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
    for lo, hi in CJK_SEED_RANGES:
        size = hi-lo+1
        table.append((cum, cum+size-1, lo))
        cum += size
    return table, cum


CJK_SEED_TABLE, CJK_SEED_BASE = _cjk_build_table()


def cjk_digit_to_char(d):
    for start, end, lo in CJK_SEED_TABLE:
        if start <= d <= end:
            return chr(lo+(d-start))
    raise ValueError(f'seed digit out of range: {d}')


def cjk_char_to_digit(c):
    cp = ord(c)
    cum = 0
    for lo, hi in CJK_SEED_RANGES:
        size = hi-lo+1
        if lo <= cp <= hi:
            return cum+(cp-lo)
        cum += size
    raise ValueError(f'not a valid seed character: {c!r}')


def cjk_encode_int(n):
    if n == 0:
        return cjk_digit_to_char(0)
    digits = []
    while n:
        n, r = divmod(n, CJK_SEED_BASE)
        digits.append(r)
    return ''.join(cjk_digit_to_char(d) for d in reversed(digits))


def cjk_decode_int(s):
    n = 0
    for c in s:
        n = n*CJK_SEED_BASE + cjk_char_to_digit(c)
    return n


class Eval:
    def CHAR(a): return bui.charstr(getattr(bui.SpecialChar, a))
    def TEXTURE(t): return bui.gettexture(t)

    def SOUND(s): return (
        bui.getsound(s) if Settings.sound_allowed(s) else Const.SILENT_SOUND
    )

    def SHADOW(px, py, sx, sy, d=0.16): return (
        (px-sx*d, py-sy*d),
        (sx+sx*(d*2), sy+sy*(d*2))
    )

    def RELATIVE(hx, hy, dx, dy, bx, by): return (
        (bx+hx)-(dx+hx),
        (by+hy)-(dy+hy)
    )

    def OFFSET(rx, ry, cx, cy, dx=0, dy=0): return (
        (rx/2+cx-dx/2, ry/2+cy-dy/2)
    )
    SCALE_BA = lambda *a: (
        (m := Const.SCALE_BA[
            bui.app.ui_v1.uiscale
        ]) and tuple(m*n for n in a)
    )
    SCALE_REAL = lambda *a: (
        (m := Const.SCALE_REAL[
            bui.app.ui_v1.uiscale
        ]) and tuple(m*n for n in a)
    )

    def WIDGET(w): return (
        getattr(
            bui, w.get_widget_type() + 'widget'
        )
    )

    def ENTRY_X(s, mem): return (
        s.magic_x +
        s.entry_xs_real * mem['start'] * s.entries_per_sec +
        (mem['duration'] * s.entries_per_sec * s.magic_left)
    )

    def ENTRY_Y(s, mem): return (
        s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
    )

    def ENTRY_POS(s, mem): return (
        Eval.ENTRY_X(s, mem),
        Eval.ENTRY_Y(s, mem)
    )

    def ENTRY_SIZE(s, mem): return (
        (s.entry_ys_real, s.entry_ys_real - s.magic_y) if mem.get('smol', False)
        else (
            s.entry_xs_real * (mem['duration'] * s.entries_per_sec) * s.magic_right,
            s.entry_ys_real - s.magic_y
        )
    )

    def STRING_WIDTH(s): return (
        bui.get_string_width(s, suppress_warning=True) or
        sum(Const.FONT_METRICS.get(c, 30) for c in s)
    )

    def ENCODE(data): return cjk_encode_int(
        int.from_bytes(
            compress(
                dumps(
                    data,
                    separators=(',', ':'),
                    sort_keys=True
                ).encode('utf-8')
            ),
            byteorder='big'
        )
    )

    def DECODE(s): return loads(
        decompress(
            (n := cjk_decode_int(s)).to_bytes(
                (n.bit_length() + 7) // 8,
                byteorder='big'
            )
        ).decode('utf-8')
    )

    def CONFIG(s, v): return (
        (cfg := bui.app.config) and (s := Const.CONFIG_PREFIX+s) and
        cfg.get(s, v) if v is None else (cfg.__setitem__(s, v), cfg.commit())
    )


class Config:
    @staticmethod
    def get(name):
        return bui.app.config.get(Const.CONFIG_PREFIX+name)

    def set(name, value):
        (config := bui.app.config)[Const.CONFIG_PREFIX+name] = value
        config.commit()


class Format:
    def ERROR(e): return (
        str(e) and Strings.ERROR_E.format(e)
        or Strings.ERROR,
        Strings.ERROR_HELP
    )

    def INVALID(e): return (
        Strings.ERROR_INVALID.format(e),
        Strings.ERROR_INVALID_HELP
    )

    def OUT_OF_RANGE(e): return (
        Strings.ERROR_OUT_OF_RANGE.format(e),
        Strings.ERROR_OUT_OF_RANGE_HELP
    )

    def ERROR_EMPTY(e): return (
        Strings.ERROR_EMPTY.format(e),
        Strings.ERROR_EMPTY_HELP
    )

    def NOT_FOUND(a): return (
        Strings.ERROR_NOT_FOUND.format(repr(a)),
        Strings.ERROR_NOT_FOUND_HELP
    )

    def WELCOME(n): return (
        Strings.WELCOME.format(n),
        Strings.WELCOME_HELP.format(__version__)
    )

    def SAVED_AS(n): return (
        Strings.SAVED_AS.format(n),
        Strings.SAVED_AS_HELP.format(join(Const.REPLAYS, n))
    )

    def LOADED_ENTRIES(t): return (
        Strings.LOADED_ENTRIES.format(t),
        Strings.LOADED_ENTRIES_HELP
    )


class Color:
    BASE = (0, 0, 0)
    COLD = (0.5, 0.5, 0.5)
    WARM = (2, 0, 0)
    TEXT = (2, 2, 2)
    TEMP = (2.2, 1.35, 0.15)
    SHADOW = (0.05, 0.05, 0.05)
    SHADOW_OPACITY = 0.4
    OPACITY = 0.4
    TEXT_OPACITY = 0.6


class Settings:
    """
    Single source of truth for every user-facing preference in Movi.

    Values are persisted through Config (bui.app.config), so they
    survive between sessions. Always go through get()/set() instead
    of touching Config directly - that's what guarantees every
    setting has exactly one key and one default, and lets the
    settings window stay a thin list of rows instead of a pile of
    bespoke read/write logic.

    apply_all() pushes the persisted values into the few *live*
    globals that things like Animate and Color read every frame
    (opacity, theme, animation speed). Call it once on startup and
    it stays correct - those globals are read at call-time, not
    cached, so nothing else needs to be re-run when a setting flips.
    """

    DEFAULTS = {
        'entry_duration':          1.0,
        'anim_speed':              1.0,
        'base_opacity':            Color.OPACITY,
        'text_opacity':            Color.TEXT_OPACITY,
        'theme':                   'Dark',
        'language':                'English',
        'autosave_on':             True,
        'autosave_interval':       float(Const.AUTOSAVE_INTERVAL),
        'ui_anim_on':              True,
        'sfx_editor_on':           True,
        'sfx_ui_on':               True,
        'ignore_playback_errors':  False,
        'show_grid_2d':            False,
        'show_grid_3d':            False,
        'brp_text_export':         False,
        'export_filename_template': Const.EXPORT_DEFAULT_TEMPLATE,
        'toast_top':               False,
        'fancy_autosave':          True,
        'toast_duration':          3.0,
        'epic_mode':               False,
        'aspect_ratio':            'Native',
        'fill_aspect_ratio':       False,
    }

    THEMES = {
        'Dark':         {'base': (0, 0, 0),          'cold': (0.5, 0.5, 0.5), 'warm': (2, 0, 0),        'text': (1, 1, 1), 'shadow': (0.05, 0.05, 0.05)},
        # Nord - cool arctic blues.
        'Nord':         {'base': (0.05, 0.14, 0.24),  'cold': (0.55, 0.7, 0.85), 'warm': (0.75, 0.55, 0.55), 'text': (2.0, 2.15, 2.3), 'shadow': (0.02, 0.04, 0.07)},
        # Dracula - violet/purple on near-black.
        'Dracula':      {'base': (0.14, 0.06, 0.22),  'cold': (0.75, 0.55, 1.0), 'warm': (2.3, 0.55, 0.85), 'text': (2.1, 2.0, 2.3),  'shadow': (0.05, 0.02, 0.08)},
        # Gruvbox (dark) - warm retro amber/orange.
        'Gruvbox':      {'base': (0.22, 0.14, 0.04),  'cold': (0.75, 0.6, 0.35), 'warm': (2.3, 0.85, 0.15), 'text': (2.15, 1.95, 1.55), 'shadow': (0.08, 0.05, 0.02)},
        # Catppuccin (Mocha) - soft pastel pink/mauve.
        'Catppuccin':   {'base': (0.18, 0.10, 0.20), 'cold': (0.85, 0.65, 0.9), 'warm': (2.2, 0.6, 0.75), 'text': (2.2, 2.0, 2.2),  'shadow': (0.07, 0.04, 0.08)},
        # Solarized (dark) - teal/cyan on deep blue-black.
        'Solarized':    {'base': (0.03, 0.16, 0.20),  'cold': (0.35, 0.75, 0.7), 'warm': (2.0, 0.9, 0.15), 'text': (1.7, 1.95, 1.95), 'shadow': (0.02, 0.07, 0.08)},
        # Tokyo Night - deep indigo with neon accents.
        'Tokyo Night':  {'base': (0.06, 0.06, 0.24), 'cold': (0.5, 0.6, 1.0),  'warm': (0.9, 2.1, 0.75), 'text': (1.95, 1.95, 2.25), 'shadow': (0.03, 0.03, 0.09)},
        # Everforest (dark) - muted forest green.
        'Everforest':   {'base': (0.07, 0.20, 0.08), 'cold': (0.55, 0.8, 0.5), 'warm': (2.1, 1.35, 0.15), 'text': (2.0, 2.1, 1.85), 'shadow': (0.03, 0.07, 0.03)},
        # Rosé Pine - dusty rose on plum-black.
        'Rose Pine':    {'base': (0.20, 0.08, 0.12), 'cold': (0.85, 0.65, 0.75), 'warm': (2.2, 0.65, 0.55), 'text': (2.15, 1.95, 2.05), 'shadow': (0.08, 0.03, 0.05)},
        # Cyberpunk - neon magenta/cyan on near-black.
        'Cyberpunk':    {'base': (0.10, 0.02, 0.22),  'cold': (0.14, 1.0, 1.0), 'warm': (1.0, 0.04, 0.58), 'text': (0.96, 0.96, 1.0), 'shadow': (0.06, 0.0, 0.09)},
        # Synthwave - hot pink/purple retro sunset.
        'Synthwave':    {'base': (0.16, 0.03, 0.28),  'cold': (0.39, 0.18, 1.0), 'warm': (1.0, 0.15, 0.37), 'text': (0.96, 0.87, 1.0), 'shadow': (0.07, 0.02, 0.12)},
        # Matrix - green phosphor terminal.
        'Matrix':       {'base': (0.02, 0.16, 0.04),  'cold': (0.13, 1.0, 0.19), 'warm': (0.13, 1.0, 0.17), 'text': (0.17, 1.0, 0.22), 'shadow': (0.0, 0.05, 0.0)},
        # Monokai - punchy green/pink on warm charcoal.
        'Monokai':      {'base': (0.16, 0.18, 0.06), 'cold': (0.2, 1.0, 0.8),  'warm': (1.0, 0.13, 0.37), 'text': (1.0, 1.0, 0.91), 'shadow': (0.06, 0.06, 0.03)},
        # Cobalt - deep blue with hot orange accents.
        'Cobalt':       {'base': (0.04, 0.10, 0.30),  'cold': (0.14, 0.36, 1.0), 'warm': (1.0, 0.48, 0.07), 'text': (0.87, 0.91, 1.0), 'shadow': (0.02, 0.04, 0.12)},
        # Aurora - teal/violet/green borealis glow.
        'Aurora':       {'base': (0.04, 0.20, 0.18),  'cold': (0.18, 1.0, 0.75), 'warm': (0.41, 0.18, 1.0), 'text': (0.86, 1.0, 0.95), 'shadow': (0.02, 0.06, 0.05)},
        # Inferno - fiery red/orange on near-black.
        'Inferno':      {'base': (0.26, 0.05, 0.02),  'cold': (1.0, 0.25, 0.05), 'warm': (1.0, 0.04, 0.02), 'text': (1.0, 0.83, 0.70), 'shadow': (0.1, 0.02, 0.0)},
        # Amethyst - rich purple/violet.
        'Amethyst':     {'base': (0.18, 0.04, 0.26),  'cold': (0.41, 0.23, 1.0), 'warm': (1.0, 0.15, 0.8), 'text': (0.96, 0.87, 1.0), 'shadow': (0.07, 0.02, 0.11)},
        # Midnight Ocean - deep navy with bioluminescent teal.
        'Midnight Ocean': {'base': (0.02, 0.06, 0.14), 'cold': (0.1, 0.55, 0.65), 'warm': (0.9, 0.55, 0.15), 'text': (1.9, 2.0, 2.1),  'shadow': (0.01, 0.03, 0.06)},
        # Blood Moon - deep crimson on near-black.
        'Blood Moon':   {'base': (0.16, 0.02, 0.03),  'cold': (0.55, 0.15, 0.15), 'warm': (1.0, 0.55, 0.1), 'text': (2.15, 1.9, 1.85), 'shadow': (0.06, 0.01, 0.01)},
        # Obsidian - near-pure black with icy blue-white accents.
        'Obsidian':     {'base': (0.01, 0.01, 0.02),  'cold': (0.6, 0.75, 0.9), 'warm': (0.9, 0.9, 1.0),  'text': (2.1, 2.1, 2.15), 'shadow': (0.0, 0.0, 0.01)},
        # Vaporwave - saturated purple/pink/cyan on indigo.
        'Vaporwave':    {'base': (0.12, 0.05, 0.24),  'cold': (0.2, 1.0, 1.0),  'warm': (1.0, 0.35, 0.85), 'text': (1.0, 0.95, 1.0), 'shadow': (0.05, 0.02, 0.1)},

        'Light':        {'base': (1.0, 1.0, 1.0),    'cold': (0.3, 0.4, 0.55), 'warm': (0.85, 0.15, 0.1), 'text': (0.05, 0.05, 0.05), 'shadow': (0.25, 0.25, 0.27)},
        # Solarized (light) - warm parchment with teal/orange accents.
        'Solarized Light': {'base': (1.0, 0.92, 0.68), 'cold': (0.05, 0.45, 0.5), 'warm': (0.75, 0.35, 0.0), 'text': (0.1, 0.2, 0.22), 'shadow': (0.3, 0.28, 0.2)},
        # Everforest (light) - warm paper with muted forest green.
        'Everforest Light': {'base': (0.85, 1.0, 0.72), 'cold': (0.15, 0.45, 0.15), 'warm': (0.7, 0.35, 0.0), 'text': (0.15, 0.2, 0.1), 'shadow': (0.28, 0.3, 0.22)},
        # Rosé Pine Dawn - warm cream with dusty rose.
        'Rose Pine Dawn': {'base': (1.0, 0.81, 0.79),  'cold': (0.5, 0.3, 0.35), 'warm': (0.75, 0.2, 0.15), 'text': (0.2, 0.12, 0.15), 'shadow': (0.32, 0.26, 0.25)},
        # Catppuccin Latte - soft lavender-white with mauve/pink.
        'Catppuccin Latte': {'base': (0.86, 0.79, 1.0), 'cold': (0.35, 0.25, 0.55), 'warm': (0.85, 0.2, 0.35), 'text': (0.15, 0.1, 0.2), 'shadow': (0.28, 0.25, 0.32)},
        # Nord (light) - frosty white-blue.
        'Nord Light':   {'base': (0.71, 0.86, 1.0),  'cold': (0.15, 0.35, 0.55), 'warm': (0.55, 0.25, 0.15), 'text': (0.08, 0.12, 0.18), 'shadow': (0.22, 0.28, 0.32)},
        # Gruvbox (light) - warm cream with retro amber/olive.
        'Gruvbox Light': {'base': (1.0, 0.88, 0.61), 'cold': (0.35, 0.3, 0.1), 'warm': (0.75, 0.25, 0.0), 'text': (0.15, 0.1, 0.02), 'shadow': (0.3, 0.27, 0.18)},
        # Dracula (light) - soft lilac-white with violet/pink accents.
        'Dracula Light': {'base': (0.93, 0.86, 1.0), 'cold': (0.4, 0.2, 0.6),  'warm': (0.75, 0.15, 0.4), 'text': (0.14, 0.08, 0.2), 'shadow': (0.28, 0.22, 0.35)},
        # Tokyo Day - crisp blue-white, the daytime Tokyo Night.
        'Tokyo Day':    {'base': (0.85, 0.9, 1.0),   'cold': (0.2, 0.35, 0.75), 'warm': (0.15, 0.55, 0.3), 'text': (0.08, 0.1, 0.2),  'shadow': (0.24, 0.28, 0.35)},

        'Paper':        {'base': (1.0, 0.98, 0.95),  'cold': (0.35, 0.35, 0.4), 'warm': (0.6, 0.2, 0.15), 'text': (0.03, 0.03, 0.03), 'shadow': (0.2, 0.2, 0.2)},
        # Cotton Candy - pale pink/lavender pastel.
        'Cotton Candy': {'base': (0.95, 0.81, 1.0),  'cold': (0.6, 0.4, 0.75), 'warm': (0.9, 0.35, 0.55), 'text': (0.1, 0.05, 0.15), 'shadow': (0.25, 0.2, 0.28)},
        # Mint Cream - pale mint/sage pastel.
        'Mint Cream':   {'base': (0.81, 1.0, 0.86), 'cold': (0.2, 0.6, 0.4),  'warm': (0.55, 0.35, 0.1), 'text': (0.03, 0.12, 0.06), 'shadow': (0.2, 0.28, 0.22)},
        # Sky - pale powder-blue pastel.
        'Sky':          {'base': (0.72, 0.86, 1.0), 'cold': (0.15, 0.45, 0.8), 'warm': (0.7, 0.35, 0.1), 'text': (0.02, 0.08, 0.16), 'shadow': (0.18, 0.24, 0.32)},
        # Pop Art - near-white with bold primary red/blue.
        'Pop Art':      {'base': (1.0, 0.92, 0.82),  'cold': (0.05, 0.3, 0.95), 'warm': (0.95, 0.05, 0.05), 'text': (0.02, 0.02, 0.02), 'shadow': (0.22, 0.22, 0.22)},
        # Vanilla - warm ivory with soft caramel accents.
        'Vanilla':      {'base': (1.0, 0.97, 0.88),  'cold': (0.55, 0.45, 0.3), 'warm': (0.8, 0.5, 0.15), 'text': (0.08, 0.06, 0.03), 'shadow': (0.2, 0.18, 0.14)},
        # Lavender Fields - pale lilac-white pastel.
        'Lavender Fields': {'base': (0.93, 0.89, 1.0), 'cold': (0.45, 0.3, 0.65), 'warm': (0.7, 0.3, 0.5), 'text': (0.1, 0.08, 0.16), 'shadow': (0.24, 0.2, 0.3)},
        # Peach - soft peach-white pastel.
        'Peach':        {'base': (1.0, 0.9, 0.83),   'cold': (0.35, 0.4, 0.55), 'warm': (0.85, 0.35, 0.15), 'text': (0.14, 0.08, 0.05), 'shadow': (0.24, 0.2, 0.18)},
    }

    UI_SOUNDS = {Const.OK_SOUND}
    EDITOR_SOUNDS = {Const.BAD_SOUND, Const.GOOD_SOUND, Const.ACTION_SOUND}

    ASPECT_RATIOS = ('Native',) + tuple(Const.ASPECT_RATIO_VALUES)

    @staticmethod
    def get(key):
        v = Config.get(key)
        return Settings.DEFAULTS[key] if v is None else v

    @staticmethod
    def set(key, value):
        Config.set(key, value)

    @staticmethod
    def sound_allowed(name):
        if name in Settings.UI_SOUNDS:
            return Settings.get('sfx_ui_on')
        if name in Settings.EDITOR_SOUNDS:
            return Settings.get('sfx_editor_on')
        return True

    @staticmethod
    def apply_theme(name=None):
        pal = Settings.THEMES.get(name or Settings.get('theme'), Settings.THEMES['Dark'])
        Color.BASE = pal['base']
        Color.COLD = pal['cold']
        Color.WARM = pal['warm']
        tmax = max(pal['text'])
        Color.TEXT = tuple(c/tmax for c in pal['text']) if tmax > 1 else pal['text']
        Color.SHADOW = pal['shadow']
        base_luma = sum(pal['base'])/3
        Color.SHADOW_OPACITY = max(0.10, min(0.5, 0.5-base_luma*0.42))
        Color.TEMP = (2.2, 1.35, 0.15) if base_luma < 0.5 else (0.55, 0.32, 0.02)

    @staticmethod
    def apply_all():
        """Push persisted settings into the live globals. Safe to
        call as often as needed - cheap, idempotent."""
        Color.OPACITY = Settings.get('base_opacity')
        Color.TEXT_OPACITY = Settings.get('text_opacity')
        Settings.apply_theme()

# ba_meta export bascenev1.GameActivity


class Movi(bs.GameActivity[bs.Player, bs.Team]):
    name = Strings.MAP_TITLE
    description = Strings.MAP_DESCRIPTION
    def get_availabe_settings(s): return []
    def supports_session_type(s): return True
    def get_supported_maps(s): return bs.app.classic.getmaps('melee')
    def get_instance_description(s): return Strings.INSTANCE_DESCRIPTION
    def get_instance_description_short(s): return Strings.INSTANCE_DESCRIPTION_SHORT

    @classmethod
    def recreate(cls):
        bs.new_host_session(cls.sessiontype)
        session = bs.get_foreground_host_session()
        with session.context:
            act = bs.newactivity(Movi, cls.settings)
            session.setactivity(act)

    def __init__(s, settings):
        super().__init__(settings)
        type(s).settings = settings
        session = bs.get_foreground_host_session()
        type(s).sessiontype = (
            session.use_teams and
            bs.DualTeamSession or
            bs.FreeForAllSession
        )
        s.default_music = None
        s.editor = None

    def ensure(s):
        if not s.editor:
            s.editor = type(s).INS = Editor(
                map=type(s).settings['map']
            )
            s.make_ui()

    def on_player_join(s, p):
        s.ensure()
        s.editor and s.editor.schedule_on_ui(
            lambda: s.editor.toast(
                Format.WELCOME(
                    p.sessionplayer.getname()
                )
            )
        )

    def on_begin(s):
        s.ensure()

    def make_ui(s):
        ba.pushcall(ba.CallPartial(
            s.editor.make
        ), raw=True)

    def kill_ui(s):
        ba.pushcall(s.editor.kill, raw=True)


class MoviSubsystem(ba.AppSubsystem):
    def on_screen_size_change(s):
        Editor._call('on_resize')

    def on_ui_scale_change(s):
        Editor._call('on_rescale')

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin


class byBordd(ba.Plugin):
    def __init__(s):
        ba.app.register_subsystem(MoviSubsystem())


class _BSWrapper:
    def __init__(self, original_module, newnode_func):
        self._original = original_module
        self.newnode = newnode_func

    def __getattr__(self, name):
        return getattr(self._original, name)

    def __setattr__(self, name, value):
        if name in ('_original', 'newnode'):
            object.__setattr__(self, name, value)
        else:
            setattr(self._original, name, value)


def _make_tracked_spaz(OriginalSpaz, runner):
    class TrackedSpaz(OriginalSpaz):
        def __init__(inner_self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            runner.created_actors.append(inner_self)
    return TrackedSpaz


class CodeRunner:
    _SHARED = {}

    def __init__(self, on_error=None, parent_runner=None, extra_namespace=None):
        self.on_error = on_error
        self.parent_runner = parent_runner
        self.extra_namespace = extra_namespace

        if parent_runner:
            self.namespace = parent_runner.namespace
            self.created_nodes = parent_runner.created_nodes
            self.created_actors = parent_runner.created_actors
            self._tracked_spaz = None
        else:
            self.namespace = {}
            self.created_nodes = []
            self.created_actors = []
            self._tracked_spaz = None

        self.stdout_capture = StringIO()
        self.stderr_capture = StringIO()
        self.running = False
        self.stop_flag = Event()
        self.main_thread = None
        self.children = []

    def _terminate_thread(self, thread):
        if not thread.is_alive():
            return
        try:
            exc = py_object(SystemExit)
            res = pythonapi.PyThreadState_SetAsyncExc(c_long(thread.ident), exc)
            if res > 1:
                pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        except:
            pass

    def _execute_code(self, code_string):
        import bascenev1 as bs
        import bascenev1lib as bsl
        from bascenev1lib.actor.spaz import Spaz as OriginalSpaz
        import bauiv1 as bui
        import babase as ba
        import _babase as _ba
        import math
        import random

        original_newnode = bs.newnode

        def tracked_newnode(*args, **kwargs):
            node = original_newnode(*args, **kwargs)
            self.created_nodes.append(node)
            return node

        root = self.parent_runner or self
        if root._tracked_spaz is None:
            root._tracked_spaz = _make_tracked_spaz(OriginalSpaz, root)
        TrackedSpaz = root._tracked_spaz

        bs_wrapped = _BSWrapper(bs, tracked_newnode)

        self.namespace.update({
            '__stop_flag__': self.stop_flag,
            'bascenev1': bs_wrapped,
            'bascenev1lib': bsl,
            'bauiv1': bui,
            'babase': ba,
            '_babase': _ba,
            'bs': bs_wrapped,
            'bsl': bsl,
            'bui': bui,
            'ba': ba,
            '_ba': _ba,
            'Spaz': TrackedSpaz,
            'math': math,
            'random': random,
            'Bubble': Bubble,
            '_SHARED': CodeRunner._SHARED
        })
        if self.extra_namespace:
            self.namespace.update(self.extra_namespace)

        try:
            with bs.get_foreground_host_activity().context:
                with redirect_stdout(self.stdout_capture), redirect_stderr(self.stderr_capture):
                    exec(code_string, self.namespace)
        except Exception as e:
            if callable(self.on_error):
                self.on_error(e)
            else:
                print(f"Error in user code: {e}")
                print(format_exc())

    def _cleanup_all(self):
        """Delete all tracked actors and nodes within the activity context"""
        import bascenev1 as bs

        try:
            with bs.get_foreground_host_activity().context:
                for actor in self.created_actors:
                    try:
                        if actor.is_alive():
                            actor.handlemessage(bs.DieMessage(immediate=True))
                    except:
                        pass
                self.created_actors.clear()

                for node in self.created_nodes:
                    try:
                        if node.exists():
                            node.delete()
                    except:
                        pass
                self.created_nodes.clear()
        except:
            self.created_actors.clear()
            self.created_nodes.clear()

    def _runner(self, code_string):
        try:
            bs.pushcall(lambda: self._execute_code(code_string), from_other_thread=True)
        except SystemExit:
            pass
        except Exception as e:
            if callable(self.on_error):
                self.on_error(e)
            else:
                print(f"Error in user code: {e}")
                print(format_exc())
        finally:
            self.running = False

    def on_start(self, code_string):
        if not self.parent_runner:
            self.namespace = {}
            self.created_nodes = []
            self.created_actors = []

        self.stdout_capture = StringIO()
        self.stderr_capture = StringIO()
        self.stop_flag.clear()
        self.running = True
        self.main_thread = Thread(target=self._runner, args=(code_string,), daemon=True)
        self.main_thread.start()

    def spawn_child(self, code_string):
        """Create and start a child runner that shares this namespace"""
        child = CodeRunner(
            on_error=self.on_error,
            parent_runner=self
        )
        self.children.append(child)
        child.on_start(code_string)
        return child

    def on_end(self):
        if not self.running and self.main_thread is None and not self.children:
            return

        self.stop_flag.set()

        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=0.1)
        if self.main_thread and self.main_thread.is_alive():
            self._terminate_thread(self.main_thread)
            self.main_thread.join(timeout=0.5)

        for child in self.children:
            child.on_end()
        self.children.clear()

        self._tracked_spaz = None

        if not self.parent_runner:
            bs.pushcall(self._cleanup_all)

            for value in list(self.namespace.values()):
                if hasattr(value, 'close') and callable(value.close):
                    try:
                        value.close()
                    except:
                        pass

            self.namespace.clear()

        self.main_thread = None
        self.running = False


def get_presets():
    """
    Return a list of Movi presets.

    Each entry is a tuple:
        (event_index, display_name, description, edit_like_dict)

    Where edit_like_dict is shaped exactly like the 'edit' parameter
    expected by the corresponding make_*_window function:
        {
            'data': { ...fields... }
        }

    event_index legend (matches Strings.EVENTS order):
        0 = Node    1 = Camera   2 = Sound   3 = FX
        4 = Map     6 = Code

    Rebuilt from scratch: every sound name, map name, character name,
    and chunk/emit type below was cross-checked against the actual
    BombSquad engine source, so nothing here should silently no-op or
    error on a bad asset name. Code presets that fire many sounds use
    a single seq=[...] list + for-loop instead of hand-unrolled
    bs.AppTimer blocks, so they're much shorter and easy to edit.
    """
    presets = []

    presets.append((
        0,
        'World Anchor',
        'Invisible dummy node at\norigin, handy to parent\nother nodes/effects to.',
        {
            'data': {
                'type': 'math',
                'name': 'WorldAnchor',
                'attrs': {'input1': (0, 0, 0), 'operation': 'add'}
            }
        }
    ))

    presets.append((
        0,
        'Offstage Anchor',
        'Dummy node placed off to\nthe side, out of frame -\nuseful as a parking spot.',
        {
            'data': {
                'type': 'math',
                'name': 'OffstageAnchor',
                'attrs': {'input1': (20, 0, 0), 'operation': 'add'}
            }
        }
    ))

    presets.append((
        0,
        'Basic Spaz',
        'Standard blue Spaz character\nat center stage - the safest\nstarting point.',
        {
            'data': {
                'type': 'spaz',
                'name': 'Spaz',
                'attrs': {
                    'character': '"Spaz"',
                    'color': '(0.4, 0.5, 0.8)',
                    'highlight': '(1.0, 1.0, 1.0)',
                    'materials': '[_factory.spaz_material, _shared.object_material, _shared.player_material]',
                    'roller_materials': '[_factory.roller_material, _shared.player_material]',
                    'punch_materials': '[_factory.punch_material, _shared.attack_material]',
                    'pickup_materials': '[_factory.pickup_material, _shared.pickup_material]',
                    'position': '(0, 1, 0)'
                }
            }
        }
    ))

    presets.append((
        0,
        'Neon Assassin',
        'Stealthy ninja with electric\npurple glow.',
        {
            'data': {
                'type': 'spaz',
                'name': 'Shadow Strike',
                'attrs': {
                    'character': '"Snake Shadow"',
                    'color': '(2.2, 0.0, 0.4)',
                    'highlight': '(2.5, 0.0, 4.0)',
                    'materials': '[_factory.spaz_material, _shared.object_material, _shared.player_material]',
                    'roller_materials': '[_factory.roller_material, _shared.player_material]',
                    'punch_materials': '[_factory.punch_material, _shared.attack_material]',
                    'pickup_materials': '[_factory.pickup_material, _shared.pickup_material]',
                    'position': '(0, 1, 0)'
                }
            }
        }
    ))

    presets.append((
        0,
        'Cyber Warrior',
        'Futuristic agent with intense\ncyan energy.',
        {
            'data': {
                'type': 'spaz',
                'name': 'NetRunner',
                'attrs': {
                    'character': '"Agent Johnson"',
                    'color': '(0.0, 0.1, 0.2)',
                    'highlight': '(0.0, 3.5, 5.0)',
                    'materials': '[_factory.spaz_material, _shared.object_material, _shared.player_material]',
                    'roller_materials': '[_factory.roller_material, _shared.player_material]',
                    'punch_materials': '[_factory.punch_material, _shared.attack_material]',
                    'pickup_materials': '[_factory.pickup_material, _shared.pickup_material]',
                    'position': '(2, 1, 0)'
                }
            }
        }
    ))

    presets.append((
        0,
        'Plasma Knight',
        'Medieval warrior radiating\nblue-white plasma.',
        {
            'data': {
                'type': 'spaz',
                'name': 'Sir Voltage',
                'attrs': {
                    'character': '"Kronk"',
                    'color': '(0.1, 0.15, 0.3)',
                    'highlight': '(1.5, 2.5, 6.0)',
                    'materials': '[_factory.spaz_material, _shared.object_material, _shared.player_material]',
                    'roller_materials': '[_factory.roller_material, _shared.player_material]',
                    'punch_materials': '[_factory.punch_material, _shared.attack_material]',
                    'pickup_materials': '[_factory.pickup_material, _shared.pickup_material]',
                    'position': '(-2, 1, 0)'
                }
            }
        }
    ))

    presets.append((
        0,
        'Toxic Menace',
        'Radioactive character with\nsickly green glow.',
        {
            'data': {
                'type': 'spaz',
                'name': 'Biohazard',
                'attrs': {
                    'character': '"Mel"',
                    'color': '(0.1, 0.2, 0.0)',
                    'highlight': '(2.0, 5.0, 0.0)',
                    'materials': '[_factory.spaz_material, _shared.object_material, _shared.player_material]',
                    'roller_materials': '[_factory.roller_material, _shared.player_material]',
                    'punch_materials': '[_factory.punch_material, _shared.attack_material]',
                    'pickup_materials': '[_factory.pickup_material, _shared.pickup_material]',
                    'position': '(0, 1, -2)'
                }
            }
        }
    ))

    presets.append((
        0,
        'Frosty Sentinel',
        'Icy pale character, good for\na winter/frozen-map scene.',
        {
            'data': {
                'type': 'spaz',
                'name': 'Permafrost',
                'attrs': {
                    'character': '"Frosty"',
                    'color': '(0.5, 0.7, 0.9)',
                    'highlight': '(0.8, 1.0, 1.3)',
                    'materials': '[_factory.spaz_material, _shared.object_material, _shared.player_material]',
                    'roller_materials': '[_factory.roller_material, _shared.player_material]',
                    'punch_materials': '[_factory.punch_material, _shared.attack_material]',
                    'pickup_materials': '[_factory.pickup_material, _shared.pickup_material]',
                    'position': '(0, 1, 2)'
                }
            }
        }
    ))

    presets.append((
        0,
        'Skeleton Crew',
        "Bones's default look, works\nwell for a spooky scene.",
        {
            'data': {
                'type': 'spaz',
                'name': 'Rattler',
                'attrs': {
                    'character': '"Bones"',
                    'color': '(0.8, 0.8, 0.75)',
                    'highlight': '(1.0, 1.0, 1.0)',
                    'materials': '[_factory.spaz_material, _shared.object_material, _shared.player_material]',
                    'roller_materials': '[_factory.roller_material, _shared.player_material]',
                    'punch_materials': '[_factory.punch_material, _shared.attack_material]',
                    'pickup_materials': '[_factory.pickup_material, _shared.pickup_material]',
                    'position': '(-2, 1, 2)'
                }
            }
        }
    ))

    presets.append((
        0,
        'Old Wizard',
        'Grumbledorf tinted purple for\na mystical caster look.',
        {
            'data': {
                'type': 'spaz',
                'name': 'The Archmage',
                'attrs': {
                    'character': '"Grumbledorf"',
                    'color': '(0.4, 0.1, 0.5)',
                    'highlight': '(0.9, 0.5, 1.4)',
                    'materials': '[_factory.spaz_material, _shared.object_material, _shared.player_material]',
                    'roller_materials': '[_factory.roller_material, _shared.player_material]',
                    'punch_materials': '[_factory.punch_material, _shared.attack_material]',
                    'pickup_materials': '[_factory.pickup_material, _shared.pickup_material]',
                    'position': '(0, 1, 0)'
                }
            }
        }
    ))

    presets.append((
        0,
        'Jungle Explorer',
        'Zoe recolored earthy green,\ngood for an adventurer role.',
        {
            'data': {
                'type': 'spaz',
                'name': 'Trailblazer',
                'attrs': {
                    'character': '"Zoe"',
                    'color': '(0.3, 0.5, 0.2)',
                    'highlight': '(0.9, 1.0, 0.6)',
                    'materials': '[_factory.spaz_material, _shared.object_material, _shared.player_material]',
                    'roller_materials': '[_factory.roller_material, _shared.player_material]',
                    'punch_materials': '[_factory.punch_material, _shared.attack_material]',
                    'pickup_materials': '[_factory.pickup_material, _shared.pickup_material]',
                    'position': '(2, 1, -2)'
                }
            }
        }
    ))

    presets.append((
        0,
        'Deep Sea Diver',
        'Pixel recolored deep blue,\nfits an underwater/submarine\nscene.',
        {
            'data': {
                'type': 'spaz',
                'name': 'Fathom',
                'attrs': {
                    'character': '"Pixel"',
                    'color': '(0.0, 0.2, 0.5)',
                    'highlight': '(0.3, 0.6, 1.2)',
                    'materials': '[_factory.spaz_material, _shared.object_material, _shared.player_material]',
                    'roller_materials': '[_factory.roller_material, _shared.player_material]',
                    'punch_materials': '[_factory.punch_material, _shared.attack_material]',
                    'pickup_materials': '[_factory.pickup_material, _shared.pickup_material]',
                    'position': '(0, 1, 0)'
                }
            }
        }
    ))

    presets.append((
        0,
        'Old-Timer Gunslinger',
        'Jack Morgan recolored dusty\nbrown for a western scene.',
        {
            'data': {
                'type': 'spaz',
                'name': 'Doc Ironside',
                'attrs': {
                    'character': '"Jack Morgan"',
                    'color': '(0.4, 0.3, 0.2)',
                    'highlight': '(0.9, 0.8, 0.6)',
                    'materials': '[_factory.spaz_material, _shared.object_material, _shared.player_material]',
                    'roller_materials': '[_factory.roller_material, _shared.player_material]',
                    'punch_materials': '[_factory.punch_material, _shared.attack_material]',
                    'pickup_materials': '[_factory.pickup_material, _shared.pickup_material]',
                    'position': '(-2, 1, -2)'
                }
            }
        }
    ))

    presets.append((
        0,
        'Butler Bernard',
        'Bernard kept close to natural\ncolors, calm supporting-cast\nlook.',
        {
            'data': {
                'type': 'spaz',
                'name': 'Bernard',
                'attrs': {
                    'character': '"Bernard"',
                    'color': '(0.5, 0.45, 0.4)',
                    'highlight': '(1.0, 1.0, 0.95)',
                    'materials': '[_factory.spaz_material, _shared.object_material, _shared.player_material]',
                    'roller_materials': '[_factory.roller_material, _shared.player_material]',
                    'punch_materials': '[_factory.punch_material, _shared.attack_material]',
                    'pickup_materials': '[_factory.pickup_material, _shared.pickup_material]',
                    'position': '(0, 1, 0)'
                }
            }
        }
    ))

    presets.append((
        0,
        'Mascot Todd',
        'Todd McBurton with a bright,\nfriendly palette - good for a\ncomic-relief role.',
        {
            'data': {
                'type': 'spaz',
                'name': 'Big Todd',
                'attrs': {
                    'character': '"Todd McBurton"',
                    'color': '(0.9, 0.6, 0.2)',
                    'highlight': '(1.2, 1.0, 0.6)',
                    'materials': '[_factory.spaz_material, _shared.object_material, _shared.player_material]',
                    'roller_materials': '[_factory.roller_material, _shared.player_material]',
                    'punch_materials': '[_factory.punch_material, _shared.attack_material]',
                    'pickup_materials': '[_factory.pickup_material, _shared.pickup_material]',
                    'position': '(2, 1, 2)'
                }
            }
        }
    ))

    presets.append((
        0,
        'Soft Fill Light',
        'Gentle omnidirectional fill\nabove center. Good default\nfor any scene.',
        {
            'data': {
                'type': 'light',
                'name': 'SoftFill',
                'attrs': {'intensity': 1.3, 'radius': 3.0, 'color': (1.0, 0.95, 0.9), 'position': (0, 2.0, 0), 'volume_intensity_scale': 0.0}
            }
        }
    ))

    presets.append((
        0,
        'Warm Key Light',
        'Strong warm key light,\nthe main light source for\na portrait-style shot.',
        {
            'data': {
                'type': 'light',
                'name': 'WarmKey',
                'attrs': {'intensity': 1.8, 'radius': 3.5, 'color': (1.3, 1.0, 0.7), 'position': (2.5, 3.5, -2.0), 'volume_intensity_scale': 0.0}
            }
        }
    ))

    presets.append((
        0,
        'Cool Key Light',
        'Cold blue-toned key light\nfor a tense or sci-fi mood.',
        {
            'data': {
                'type': 'light',
                'name': 'CoolKey',
                'attrs': {'intensity': 1.6, 'radius': 3.5, 'color': (0.6, 0.8, 1.4), 'position': (-2.5, 3.5, -2.0), 'volume_intensity_scale': 0.0}
            }
        }
    ))

    presets.append((
        0,
        'Rim Light Left',
        'Colored rim light from the\nleft to separate a subject\nfrom the background.',
        {
            'data': {
                'type': 'light',
                'name': 'RimLeft',
                'attrs': {'intensity': 1.0, 'radius': 4.0, 'color': (0.3, 0.5, 1.2), 'position': (-4, 3, 0), 'volume_intensity_scale': 0.0}
            }
        }
    ))

    presets.append((
        0,
        'Rim Light Right',
        'Mirror of Rim Light Left -\nuse both together for a\nclean two-sided glow.',
        {
            'data': {
                'type': 'light',
                'name': 'RimRight',
                'attrs': {'intensity': 1.0, 'radius': 4.0, 'color': (1.2, 0.5, 0.3), 'position': (4, 3, 0), 'volume_intensity_scale': 0.0}
            }
        }
    ))

    presets.append((
        0,
        'Top Spotlight',
        'A strong spotlight directly\nabove origin, good for a\nreveal moment.',
        {
            'data': {
                'type': 'light',
                'name': 'TopSpot',
                'attrs': {'intensity': 2.2, 'radius': 2.5, 'color': (1.0, 1.0, 1.0), 'position': (0, 5, 0), 'volume_intensity_scale': 0.0}
            }
        }
    ))

    presets.append((
        0,
        'Dramatic Underlight',
        'Uplight from below for a\nspooky or villainous look.',
        {
            'data': {
                'type': 'light',
                'name': 'Underlight',
                'attrs': {'intensity': 1.5, 'radius': 2.0, 'color': (0.9, 0.2, 0.9), 'position': (0, -0.5, 0), 'volume_intensity_scale': 0.0}
            }
        }
    ))

    presets.append((
        0,
        'Candle Glow',
        'Small warm practical light,\nlow radius, subtle flicker\nfeel for close-up scenes.',
        {
            'data': {
                'type': 'light',
                'name': 'CandleGlow',
                'attrs': {'intensity': 0.7, 'radius': 1.2, 'color': (1.4, 0.9, 0.5), 'position': (0, 1.0, 0.5), 'volume_intensity_scale': 0.0}
            }
        }
    ))

    presets.append((
        0,
        'Color Wash Red',
        'Big saturated red wash for\nalarm or danger beats.',
        {
            'data': {
                'type': 'light',
                'name': 'WashRed',
                'attrs': {'intensity': 1.4, 'radius': 6.0, 'color': (2.0, 0.1, 0.1), 'position': (0, 4, 0), 'volume_intensity_scale': 0.0}
            }
        }
    ))

    presets.append((
        0,
        'Color Wash Blue',
        'Big saturated blue wash for\ncalm, sad, or night beats.',
        {
            'data': {
                'type': 'light',
                'name': 'WashBlue',
                'attrs': {'intensity': 1.4, 'radius': 6.0, 'color': (0.1, 0.3, 2.0), 'position': (0, 4, 0), 'volume_intensity_scale': 0.0}
            }
        }
    ))

    presets.append((
        0,
        'Title Card',
        'Center title text hovering\nin the world.',
        {
            'data': {
                'type': 'text',
                'name': 'Title',
                'attrs': {'text': 'MOVI PRESENTS', 'position': (0, 2.2, 0), 'in_world': True, 'shadow': 1.0, 'flatness': 0.8, 'scale': 0.02, 'color': (2.0, 2.0, 2.0), 'h_align': 'center'}
            }
        }
    ))

    presets.append((
        0,
        'Lower Third Caption',
        'Small caption text near the\nbottom, good for names or\nsubtitles.',
        {
            'data': {
                'type': 'text',
                'name': 'LowerThird',
                'attrs': {'text': 'Caption goes here', 'position': (0, 0.6, 0), 'in_world': True, 'shadow': 1.0, 'flatness': 0.9, 'scale': 0.012, 'color': (1.8, 1.8, 1.8), 'h_align': 'center'}
            }
        }
    ))

    presets.append((
        0,
        'Chapter Marker',
        'Large bold marker text for\nswitching scenes/chapters.',
        {
            'data': {
                'type': 'text',
                'name': 'ChapterMarker',
                'attrs': {'text': 'CHAPTER ONE', 'position': (0, 3.0, 0), 'in_world': True, 'shadow': 1.0, 'flatness': 0.7, 'scale': 0.025, 'color': (2.2, 2.2, 1.0), 'h_align': 'center'}
            }
        }
    ))

    presets.append((
        0,
        'The End Card',
        'Simple closing card text for\nthe last frame of a movie.',
        {
            'data': {
                'type': 'text',
                'name': 'EndCard',
                'attrs': {'text': 'THE END', 'position': (0, 2.2, 0), 'in_world': True, 'shadow': 1.0, 'flatness': 0.8, 'scale': 0.022, 'color': (2.0, 2.0, 2.0), 'h_align': 'center'}
            }
        }
    ))

    presets.append((
        1,
        'Side Shot',
        'Side-on camera, slightly\nzoomed, focused on center.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [8.0, 3.0, 0.0],
                'target': [0.0, 1.5, 0.0]
            }
        }
    ))

    presets.append((
        1,
        'Hero Shot',
        'Low front angle, looking\nup at center - makes the\nsubject look powerful.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [0.0, 1.0, -7.5],
                'target': [0.0, 2.5, 0.0]
            }
        }
    ))

    presets.append((
        1,
        'Top Down',
        'Top-down overview of the\nwhole map.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [0.0, 13.0, 0.01],
                'target': [0.0, 0.5, 0.0]
            }
        }
    ))

    presets.append((
        1,
        'Over Shoulder',
        'Over-the-shoulder shot from\nbehind origin.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [0.0, 2.2, -4.5],
                'target': [0.0, 1.5, 2.0]
            }
        }
    ))

    presets.append((
        1,
        'Wide Establishing',
        'Pulled far back to show\nthe whole set - good as\na scene opener.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [0.0, 6.0, -14.0],
                'target': [0.0, 1.0, 0.0]
            }
        }
    ))

    presets.append((
        1,
        'Extreme Close-Up',
        'Very tight on center,\nfor an intense reaction\nbeat.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [0.0, 1.3, -1.6],
                'target': [0.0, 1.4, 0.0]
            }
        }
    ))

    presets.append((
        1,
        'Three-Quarter Shot',
        'Angled 3/4 view, a natural\ndefault for dialogue.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [5.0, 2.2, -3.0],
                'target': [0.0, 1.5, 0.0]
            }
        }
    ))

    presets.append((
        1,
        "Bird's Eye Corner",
        'High angle from a corner,\ngood for showing scale.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [10.0, 10.0, -10.0],
                'target': [0.0, 0.0, 0.0]
            }
        }
    ))

    presets.append((
        1,
        'Low Diagonal Drama',
        'Low, off-center angle for\na dramatic villain reveal.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [-3.0, 0.6, -5.0],
                'target': [0.0, 2.0, 0.0]
            }
        }
    ))

    presets.append((
        1,
        'Symmetric Front',
        'Dead-center front-on shot,\nclean and formal.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [0.0, 2.0, -8.0],
                'target': [0.0, 1.5, 0.0]
            }
        }
    ))

    presets.append((
        1,
        'Profile Shot',
        'Pure side profile at eye\nheight.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [6.5, 1.5, 0.0],
                'target': [0.0, 1.5, 0.0]
            }
        }
    ))

    presets.append((
        1,
        'Reverse Angle',
        'Opposite side of Side Shot -\nuse both to cut back and\nforth in a conversation.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [-8.0, 3.0, 0.0],
                'target': [0.0, 1.5, 0.0]
            }
        }
    ))

    presets.append((
        1,
        'Crane High Wide',
        'High sweeping wide angle,\nfeels cinematic for an\nending shot.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [12.0, 9.0, -6.0],
                'target': [0.0, 1.0, 0.0]
            }
        }
    ))

    presets.append((
        1,
        'Ground Level Macro',
        'Camera almost at ground\nlevel looking up - great\nfor a small-object focus.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [1.0, 0.15, -1.5],
                'target': [0.0, 0.4, 0.0]
            }
        }
    ))

    presets.append((
        1,
        'Push-In Close',
        'Slightly closer version of\nThree-Quarter Shot - swap\nbetween the two for a fake\ndolly-in cut.',
        {
            'data': {
                'name': 'Camera',
                'chks': [True, True, True],
                'position': [3.0, 1.8, -1.8],
                'target': [0.0, 1.5, 0.0]
            }
        }
    ))

    presets.append((
        2,
        'Crowd Cheer',
        'Positive crowd cheer,\ngreat after a win moment.',
        {
            'data': {
                'name': 'Crowd Cheer',
                'file': 'cheer.ogg',
                'x': 0,
                'y': 1,
                'z': 0,
                'volume': 1.0,
                'chks': [False, False]
            }
        }
    ))

    presets.append((
        2,
        'Crowd Boo',
        'Negative crowd reaction for\na villain or fail beat.',
        {
            'data': {
                'name': 'Crowd Boo',
                'file': 'boo.ogg',
                'x': 0,
                'y': 1,
                'z': 0,
                'volume': 1.0,
                'chks': [False, False]
            }
        }
    ))

    presets.append((
        2,
        'Crowd Chant Loop',
        'Looping ambient crowd chant\nfor a stadium scene.',
        {
            'data': {
                'name': 'Crowd Chant Loop',
                'file': 'crowdChant.ogg',
                'x': 0,
                'y': 0,
                'z': 0,
                'volume': 0.6,
                'chks': [False, True]
            }
        }
    ))

    presets.append((
        2,
        'Foghorn Sting',
        'Big blaring foghorn hit,\ngood comedic sting.',
        {
            'data': {
                'name': 'Foghorn Sting',
                'file': 'foghorn.ogg',
                'x': 0,
                'y': 1,
                'z': 0,
                'volume': 1.0,
                'chks': [True, False]
            }
        }
    ))

    presets.append((
        2,
        'Referee Whistle',
        'Sharp whistle to mark the\nstart/stop of an action.',
        {
            'data': {
                'name': 'Referee Whistle',
                'file': 'refWhistle.ogg',
                'x': 0,
                'y': 1,
                'z': 0,
                'volume': 1.0,
                'chks': [True, False]
            }
        }
    ))

    presets.append((
        2,
        'Cash Register Ka-Ching',
        'Cash register sound for a\nscore or reward beat.',
        {
            'data': {
                'name': 'Cash Register Ka-Ching',
                'file': 'cashRegister.ogg',
                'x': 0,
                'y': 1,
                'z': 0,
                'volume': 1.0,
                'chks': [True, False]
            }
        }
    ))

    presets.append((
        2,
        'Error Buzz',
        'Harsh error/negative buzz,\ngood for a mistake beat.',
        {
            'data': {
                'name': 'Error Buzz',
                'file': 'error.ogg',
                'x': 0,
                'y': 1,
                'z': 0,
                'volume': 1.0,
                'chks': [True, False]
            }
        }
    ))

    presets.append((
        2,
        'Warning Beep Loop',
        'Looping warning beep for a\ntense countdown scene.',
        {
            'data': {
                'name': 'Warning Beep Loop',
                'file': 'warnBeeps.ogg',
                'x': 0,
                'y': 1.5,
                'z': 0,
                'volume': 0.7,
                'chks': [False, True]
            }
        }
    ))

    presets.append((
        2,
        'Drum Roll Buildup',
        'Classic drum roll before a\nbig reveal.',
        {
            'data': {
                'name': 'Drum Roll Buildup',
                'file': 'drumRoll.ogg',
                'x': 0,
                'y': 1,
                'z': 0,
                'volume': 0.9,
                'chks': [True, False]
            }
        }
    ))

    presets.append((
        2,
        'Gong Hit',
        'Big resonant gong hit for a\ndramatic entrance.',
        {
            'data': {
                'name': 'Gong Hit',
                'file': 'gong.ogg',
                'x': 0,
                'y': 1.5,
                'z': 0,
                'volume': 1.1,
                'chks': [True, False]
            }
        }
    ))

    presets.append((
        2,
        'Boxing Bell',
        'Boxing ring bell, perfect\nfor a match start/end.',
        {
            'data': {
                'name': 'Boxing Bell',
                'file': 'boxingBell.ogg',
                'x': 0,
                'y': 1,
                'z': 0,
                'volume': 1.0,
                'chks': [True, False]
            }
        }
    ))

    presets.append((
        2,
        'Achievement Ding',
        'Positive achievement chime\nfor unlocking something.',
        {
            'data': {
                'name': 'Achievement Ding',
                'file': 'achievement.ogg',
                'x': 0,
                'y': 1,
                'z': 0,
                'volume': 0.9,
                'chks': [False, False]
            }
        }
    ))

    presets.append((
        2,
        'Distant Explosion',
        'Single positional boom off\nto the far right.',
        {
            'data': {
                'name': 'Distant Explosion',
                'file': 'explosion01.ogg',
                'x': 12.0,
                'y': 0.5,
                'z': 0.0,
                'volume': 1.1,
                'chks': [False, False]
            }
        }
    ))

    presets.append((
        2,
        'Cinematic Hit',
        'Short musical hit at\ncenter, non-positional.',
        {
            'data': {
                'name': 'Cinematic Hit',
                'file': 'impactHard.ogg',
                'x': 0.0,
                'y': 1.0,
                'z': 0.0,
                'volume': 1.4,
                'chks': [True, False]
            }
        }
    ))

    presets.append((
        2,
        'Underground Rumble Loop',
        'Low looping rumble from\nbelow the arena.',
        {
            'data': {
                'name': 'Underground Rumble Loop',
                'file': 'bigImpact2.ogg',
                'x': 0.0,
                'y': -4.0,
                'z': 0.0,
                'volume': 0.9,
                'chks': [False, True]
            }
        }
    ))

    presets.append((
        2,
        'Power-Up Chime',
        'Bright pickup chime, works\nwell layered under a\nreward FX.',
        {
            'data': {
                'name': 'Power-Up Chime',
                'file': 'powerup01.ogg',
                'x': 0,
                'y': 1,
                'z': 0,
                'volume': 1.0,
                'chks': [True, False]
            }
        }
    ))

    presets.append((
        2,
        'Freeze Sting',
        'Icy freeze sound effect for\na time-stop or slow-mo\nbeat.',
        {
            'data': {
                'name': 'Freeze Sting',
                'file': 'freeze.ogg',
                'x': 0,
                'y': 1,
                'z': 0,
                'volume': 1.0,
                'chks': [True, False]
            }
        }
    ))

    presets.append((
        2,
        'Fuse Burning Loop',
        'Looping fuse hiss for\nbuilding suspense.',
        {
            'data': {
                'name': 'Fuse Burning Loop',
                'file': 'fuse01.ogg',
                'x': 0,
                'y': 1,
                'z': 0,
                'volume': 0.7,
                'chks': [True, True]
            }
        }
    ))

    presets.append((
        3,
        'Spark Shower',
        'Burst of sparks at the\ncenter - a solid all-\npurpose impact effect.',
        {
            'data': {
                'name': 'Spark Shower',
                'attrs': {'position': (0, 1.2, 0), 'velocity': (0, 3, 0), 'count': 40, 'scale': 1.0, 'spread': 1.0, 'chunk_type': 'spark', 'emit_type': 'stickers'}
            }
        }
    ))

    presets.append((
        3,
        'Magic Ring',
        'Pulsing distortion ring\naround center, good for a\nspell or teleport.',
        {
            'data': {
                'name': 'Magic Ring',
                'attrs': {'position': (0, 1.0, 0), 'chunk_type': 'sweat', 'emit_type': 'distortion', 'count': 20, 'scale': 1.2, 'spread': 0.2}
            }
        }
    ))

    presets.append((
        3,
        'Soft Smoke Column',
        "Rising smoke plume. This is\nemit_type='tendrils' with\ntendril_type='smoke' - chunk_\ntype is unused by tendrils but\nstill a required argument.",
        {
            'data': {
                'name': 'Soft Smoke Column',
                'attrs': {'position': (0, 0.1, 0), 'velocity': (0, 2.5, 0), 'count': 25, 'scale': 1.1, 'chunk_type': 'rock', 'emit_type': 'tendrils', 'tendril_type': 'smoke', 'spread': 0.4}
            }
        }
    ))

    presets.append((
        3,
        'Thin Wispy Smoke',
        'Same as Soft Smoke Column but\nusing tendril_type=thin_smoke\nfor a lighter, less dense\ntrail.',
        {
            'data': {
                'name': 'Thin Wispy Smoke',
                'attrs': {'position': (0, 0.1, 0), 'velocity': (0, 2.0, 0), 'count': 18, 'scale': 0.9, 'chunk_type': 'rock', 'emit_type': 'tendrils', 'tendril_type': 'thin_smoke', 'spread': 0.3}
            }
        }
    ))

    presets.append((
        3,
        'Icy Vapor Trail',
        'Cold breath / icy vapor using\ntendril_type=ice - good for a\nfrozen-map or dragon-breath\nmoment.',
        {
            'data': {
                'name': 'Icy Vapor Trail',
                'attrs': {'position': (0, 1.4, 0), 'velocity': (0, 1.0, 0), 'count': 15, 'scale': 0.8, 'chunk_type': 'ice', 'emit_type': 'tendrils', 'tendril_type': 'ice', 'spread': 0.5}
            }
        }
    ))

    presets.append((
        3,
        'Fairy Dust Trail',
        "Uses the dedicated emit_\ntype='fairydust' - a light\nmagical sparkle trail, softer\nthan a spark burst.",
        {
            'data': {
                'name': 'Fairy Dust Trail',
                'attrs': {'position': (0, 1.5, 0), 'velocity': (0, 1.5, 0), 'chunk_type': 'spark', 'emit_type': 'fairydust', 'count': 25, 'scale': 1.0, 'spread': 1.0}
            }
        }
    ))

    presets.append((
        3,
        'Standard Debris Chunks',
        "The engine's own default\nemit_type ('chunks') - plain\nphysical debris, the most\nneutral all-purpose break FX.",
        {
            'data': {
                'name': 'Standard Debris Chunks',
                'attrs': {'position': (0, 1.0, 0), 'velocity': (0, 2.0, 0), 'chunk_type': 'rock', 'emit_type': 'chunks', 'count': 24, 'scale': 1.0, 'spread': 1.0}
            }
        }
    ))

    presets.append((
        3,
        'Small Blast',
        'Compact explosive burst -\nsize down for a bomb or\nfootstep impact.',
        {
            'data': {
                'name': 'Small Blast',
                'attrs': {'position': (0, 1.0, 0), 'chunk_type': 'rock', 'emit_type': 'stickers', 'count': 18, 'scale': 0.9, 'spread': 0.6}
            }
        }
    ))

    presets.append((
        3,
        'Big Explosion',
        'Large violent burst for a\nfinal boom / climax beat.',
        {
            'data': {
                'name': 'Big Explosion',
                'attrs': {'position': (0, 1.5, 0), 'velocity': (0, 5, 0), 'chunk_type': 'rock', 'emit_type': 'stickers', 'count': 60, 'scale': 2.0, 'spread': 1.5}
            }
        }
    ))

    presets.append((
        3,
        'Metal Shrapnel',
        'Sharp metallic burst, good\nfor a robot/machine break.',
        {
            'data': {
                'name': 'Metal Shrapnel',
                'attrs': {'position': (0, 1.0, 0), 'chunk_type': 'metal', 'emit_type': 'stickers', 'count': 30, 'scale': 1.0, 'spread': 0.8}
            }
        }
    ))

    presets.append((
        3,
        'Ice Shatter',
        'Icy shards bursting outward,\nfor a freeze/shatter beat.',
        {
            'data': {
                'name': 'Ice Shatter',
                'attrs': {'position': (0, 1.0, 0), 'velocity': (0, 1, 0), 'chunk_type': 'ice', 'emit_type': 'stickers', 'count': 35, 'scale': 1.1, 'spread': 1.0}
            }
        }
    ))

    presets.append((
        3,
        'Slime Splat',
        'Goopy slime splash, fun for\na comedic gross-out beat.',
        {
            'data': {
                'name': 'Slime Splat',
                'attrs': {'position': (0, 1.0, 0), 'chunk_type': 'slime', 'emit_type': 'stickers', 'count': 22, 'scale': 0.9, 'spread': 0.7}
            }
        }
    ))

    presets.append((
        3,
        'Wood Splinter Burst',
        'Wooden debris burst for a\ncrate/prop breaking.',
        {
            'data': {
                'name': 'Wood Splinter Burst',
                'attrs': {'position': (0, 0.8, 0), 'chunk_type': 'splinter', 'emit_type': 'stickers', 'count': 20, 'scale': 0.8, 'spread': 0.6}
            }
        }
    ))

    presets.append((
        3,
        'Energy Pulse',
        'Fast expanding distortion\npulse, reads like a shock-\nwave or sonic blast.',
        {
            'data': {
                'name': 'Energy Pulse',
                'attrs': {'position': (0, 1.5, 0), 'chunk_type': 'spark', 'emit_type': 'distortion', 'count': 45, 'scale': 1.6, 'spread': 1.2}
            }
        }
    ))

    presets.append((
        3,
        'Gentle Sparkle',
        "Light, slow sparkle drift -\nsubtle magical ambiance,\nlow count so it doesn't\noverpower a shot.",
        {
            'data': {
                'name': 'Gentle Sparkle',
                'attrs': {'position': (0, 2.0, 0), 'velocity': (0, 0.5, 0), 'chunk_type': 'spark', 'emit_type': 'tendrils', 'count': 10, 'scale': 0.6, 'spread': 1.5}
            }
        }
    ))

    presets.append((
        3,
        'Sweat Drip Panic',
        'Comedic sweat drops, useful\nfor a nervous character\nmoment.',
        {
            'data': {
                'name': 'Sweat Drip Panic',
                'attrs': {'position': (0, 1.6, 0), 'velocity': (0, -1, 0), 'chunk_type': 'sweat', 'emit_type': 'stickers', 'count': 8, 'scale': 0.7, 'spread': 0.3}
            }
        }
    ))

    presets.append((
        4,
        'Hockey Stadium (Bright)',
        'Hockey Stadium with crisp,\nslightly colder lighting.',
        {
            'data': {
                'map': 'Hockey Stadium',
                'name': 'Map',
                'attrs': {'ambient_color': (0.6, 0.7, 1.0), 'tint': (1.1, 1.2, 1.3), 'vignette_outer': (0.1, 0.1, 0.2), 'vignette_inner': (0.8, 0.9, 1.0)}
            }
        }
    ))

    presets.append((
        4,
        'Bridgit (Warm Sunset)',
        'Bridgit map with warm\nsunset-tinted lighting.',
        {
            'data': {
                'map': 'Bridgit',
                'name': 'Map',
                'attrs': {'ambient_color': (1.1, 0.8, 0.7), 'tint': (1.3, 1.0, 0.8), 'vignette_outer': (0.2, 0.1, 0.05), 'vignette_inner': (0.9, 0.8, 0.7)}
            }
        }
    ))

    presets.append((
        4,
        'Happy Thoughts (Dreamy)',
        'Extra dreamy, pastel-heavy\nHappy Thoughts mood.',
        {
            'data': {
                'map': 'Happy Thoughts',
                'name': 'Map',
                'attrs': {'ambient_color': (1.4, 1.0, 1.4), 'tint': (1.5, 1.0, 1.5), 'happy_thoughts_mode': True}
            }
        }
    ))

    presets.append((
        4,
        'Doom Shroom (Ominous)',
        'Doom Shroom pushed darker\nand greener for a horror\nfeel.',
        {
            'data': {
                'map': 'Doom Shroom',
                'name': 'Map',
                'attrs': {'ambient_color': (0.5, 0.7, 0.4), 'tint': (0.8, 1.0, 0.7), 'vignette_outer': (0.0, 0.05, 0.0), 'vignette_inner': (0.6, 0.7, 0.6)}
            }
        }
    ))

    presets.append((
        4,
        'Lake Frigid (Ice Blue)',
        'Lake Frigid pushed toward a\ncold, icy blue palette.',
        {
            'data': {
                'map': 'Lake Frigid',
                'name': 'Map',
                'attrs': {'ambient_color': (0.7, 0.85, 1.2), 'tint': (0.9, 1.0, 1.3), 'vignette_outer': (0.05, 0.08, 0.15), 'vignette_inner': (0.8, 0.9, 1.0)}
            }
        }
    ))

    presets.append((
        4,
        'Tip Top (High Noon)',
        'Tip Top with harsh bright\noverhead daylight.',
        {
            'data': {
                'map': 'Tip Top',
                'name': 'Map',
                'attrs': {'ambient_color': (1.2, 1.2, 1.1), 'tint': (1.2, 1.2, 1.1), 'vignette_outer': (0.15, 0.15, 0.1), 'vignette_inner': (1.0, 1.0, 0.95)}
            }
        }
    ))

    presets.append((
        4,
        'Crag Castle (Torchlit)',
        'Crag Castle warmed up like\nit is lit by torches.',
        {
            'data': {
                'map': 'Crag Castle',
                'name': 'Map',
                'attrs': {'ambient_color': (1.2, 0.8, 0.5), 'tint': (1.3, 0.9, 0.6), 'vignette_outer': (0.1, 0.05, 0.0), 'vignette_inner': (0.9, 0.7, 0.5)}
            }
        }
    ))

    presets.append((
        4,
        'Tower D (Neon Night)',
        'Tower D pushed into a\nsaturated neon night look.',
        {
            'data': {
                'map': 'Tower D',
                'name': 'Map',
                'attrs': {'ambient_color': (0.6, 0.4, 1.2), 'tint': (0.8, 0.6, 1.4), 'vignette_outer': (0.05, 0.0, 0.15), 'vignette_inner': (0.7, 0.5, 1.0)}
            }
        }
    ))

    presets.append((
        4,
        'Football Stadium (Overcast)',
        'Football Stadium under a\nflat, cloudy grey sky.',
        {
            'data': {
                'map': 'Football Stadium',
                'name': 'Map',
                'attrs': {'ambient_color': (0.8, 0.8, 0.85), 'tint': (0.9, 0.9, 0.95), 'vignette_outer': (0.1, 0.1, 0.12), 'vignette_inner': (0.85, 0.85, 0.9)}
            }
        }
    ))

    presets.append((
        4,
        'Big G (Golden Hour)',
        'Big G with a rich golden-\nhour glow.',
        {
            'data': {
                'map': 'Big G',
                'name': 'Map',
                'attrs': {'ambient_color': (1.3, 1.0, 0.6), 'tint': (1.4, 1.05, 0.7), 'vignette_outer': (0.15, 0.08, 0.0), 'vignette_inner': (1.0, 0.85, 0.6)}
            }
        }
    ))

    presets.append((
        4,
        'Roundabout (Cool Studio)',
        'Roundabout in a neutral,\ncool studio-lit look.',
        {
            'data': {
                'map': 'Roundabout',
                'name': 'Map',
                'attrs': {'ambient_color': (0.9, 0.95, 1.05), 'tint': (0.95, 1.0, 1.05), 'vignette_outer': (0.1, 0.1, 0.12), 'vignette_inner': (0.9, 0.92, 0.95)}
            }
        }
    ))

    presets.append((
        4,
        'Monkey Face (Jungle Haze)',
        'Monkey Face with a hazy\ngreen jungle-light feel.',
        {
            'data': {
                'map': 'Monkey Face',
                'name': 'Map',
                'attrs': {'ambient_color': (0.9, 1.1, 0.7), 'tint': (0.95, 1.1, 0.75), 'vignette_outer': (0.05, 0.1, 0.0), 'vignette_inner': (0.8, 0.95, 0.65)}
            }
        }
    ))

    presets.append((
        4,
        'Zigzag (Late Afternoon)',
        'Zigzag with a soft late-\nafternoon amber cast.',
        {
            'data': {
                'map': 'Zigzag',
                'name': 'Map',
                'attrs': {'ambient_color': (1.15, 0.95, 0.75), 'tint': (1.2, 1.0, 0.8), 'vignette_outer': (0.12, 0.08, 0.02), 'vignette_inner': (0.95, 0.85, 0.7)}
            }
        }
    ))

    presets.append((
        4,
        'The Pad (Moody Purple)',
        'The Pad tinted moody purple\nfor a stylish lounge feel.',
        {
            'data': {
                'map': 'The Pad',
                'name': 'Map',
                'attrs': {'ambient_color': (0.9, 0.6, 1.1), 'tint': (1.0, 0.7, 1.2), 'vignette_outer': (0.1, 0.0, 0.15), 'vignette_inner': (0.85, 0.6, 0.95)}
            }
        }
    ))

    presets.append((
        4,
        'Step Right Up (Carnival Bright)',
        'Step Right Up boosted for a\nfun, colorful carnival pop.',
        {
            'data': {
                'map': 'Step Right Up',
                'name': 'Map',
                'attrs': {'ambient_color': (1.2, 1.05, 0.9), 'tint': (1.25, 1.1, 0.95), 'vignette_outer': (0.15, 0.1, 0.05), 'vignette_inner': (1.0, 0.9, 0.8)}
            }
        }
    ))

    presets.append((
        4,
        'Courtyard (Soft Overcast)',
        'Courtyard with gentle,\ndiffused daylight.',
        {
            'data': {
                'map': 'Courtyard',
                'name': 'Map',
                'attrs': {'ambient_color': (0.95, 0.95, 0.9), 'tint': (1.0, 1.0, 0.95), 'vignette_outer': (0.1, 0.1, 0.08), 'vignette_inner': (0.9, 0.9, 0.85)}
            }
        }
    ))

    presets.append((
        4,
        'Rampage (Industrial Grey)',
        'Rampage pushed toward a\ncold industrial grey tone.',
        {
            'data': {
                'map': 'Rampage',
                'name': 'Map',
                'attrs': {'ambient_color': (0.75, 0.78, 0.8), 'tint': (0.85, 0.87, 0.9), 'vignette_outer': (0.08, 0.08, 0.1), 'vignette_inner': (0.8, 0.82, 0.85)}
            }
        }
    ))

    presets.append((
        6,
        'Grand Entrance',
        'One-shot hero intro: spotlight\nfades up, a drum roll builds,\nand a Spaz steps into frame.\nSaves wiring 3 separate\npresets together.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Grand Entrance',
                    'timers = []',
                    'bs.newnode("light", attrs={',
                    '    "intensity": 2.0, "radius": 3.0, "color": (1.0, 1.0, 1.0),',
                    '    "position": (0, 5, 0), "volume_intensity_scale": 0.0',
                    '})',
                    'timers.append(bs.AppTimer(0.0, lambda: bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("drumRoll"), "volume": 0.9, "loop": False',
                    '})))',
                    'def _spawn_hero():',
                    '    bot = Spaz(character="Spaz", start_invincible=False,',
                    '               color=(0.4, 0.5, 0.8), highlight=(1.0, 1.0, 1.0))',
                    '    bot.handlemessage(bs.StandMessage((0, 1, 0), 0))',
                    'timers.append(bs.AppTimer(1.6, _spawn_hero))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Instant Boss Reveal',
        'Dark red wash + gong hit +\noversized villain step-in, all\nin one preset for a fast boss\nintro.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Instant Boss Reveal',
                    'timers = []',
                    'bs.newnode("light", attrs={',
                    '    "intensity": 1.6, "radius": 5.0, "color": (2.0, 0.1, 0.1),',
                    '    "position": (0, 3, 0), "volume_intensity_scale": 0.0',
                    '})',
                    'timers.append(bs.AppTimer(0.0, lambda: bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("gong"), "volume": 1.1, "loop": False',
                    '})))',
                    'def _spawn_boss():',
                    '    bot = Spaz(character="Grumbledorf", start_invincible=False,',
                    '               color=(0.3, 0.0, 0.0), highlight=(1.5, 0.0, 0.0))',
                    '    bot.handlemessage(bs.StandMessage((0, 1, 0), 0))',
                    'timers.append(bs.AppTimer(0.8, _spawn_boss))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Victory Podium',
        'Cheer + achievement chime +\nspark shower + "WINNER" text,\nready to drop on a win screen.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Victory Podium',
                    'timers = []',
                    'bs.newnode("text", attrs={',
                    '    "text": "WINNER", "position": (0, 2.4, 0), "in_world": True,',
                    '    "shadow": 1.0, "flatness": 0.8, "scale": 0.024,',
                    '    "color": (2.0, 2.0, 0.4), "h_align": "center"',
                    '})',
                    'timers.append(bs.AppTimer(0.0, lambda: bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("cheer"), "volume": 1.0, "loop": False',
                    '})))',
                    'timers.append(bs.AppTimer(0.2, lambda: bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("achievement"), "volume": 0.9, "loop": False',
                    '})))',
                    'timers.append(bs.AppTimer(0.2, lambda: bs.emitfx(',
                    '    position=(0, 1.2, 0), velocity=(0, 3, 0), count=40, scale=1.0,',
                    '    spread=1.0, chunk_type="spark", emit_type="stickers"',
                    ')))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Countdown Launch',
        'Five-to-one voice countdown\nthat ends in an explosion -\nthe whole beat in one preset.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Countdown Launch',
                    'timers = []',
                    'announces = ["Five", "Four", "Three", "Two", "One"]',
                    'for i, num_name in enumerate(announces):',
                    '    t = i * 1.0',
                    '    sound_name = f"announce{num_name}"',
                    '    timers.append(bs.AppTimer(t, lambda s=sound_name: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(s), "volume": 0.9, "loop": False}',
                    '    )))',
                    'timers.append(bs.AppTimer(5.0, lambda: bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("explosion05"), "volume": 1.0, "loop": False',
                    '})))',
                    'timers.append(bs.AppTimer(5.0, lambda: bs.emitfx(',
                    '    position=(0, 1.5, 0), velocity=(0, 5, 0), chunk_type="rock",',
                    '    emit_type="stickers", count=60, scale=2.0, spread=1.5',
                    ')))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Quick Two-Character Duel',
        'Spawns two ready-to-go Spaz\ncharacters facing each other -\nsaves setting up both by hand.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Quick Two-Character Duel',
                    'left = Spaz(character="Spaz", start_invincible=False,',
                    '            color=(0.4, 0.5, 0.8), highlight=(1.0, 1.0, 1.0))',
                    'left.handlemessage(bs.StandMessage((-2, 1, 0), 1.57))',
                    'right = Spaz(character="Snake Shadow", start_invincible=False,',
                    '             color=(2.2, 0.0, 0.4), highlight=(2.5, 0.0, 4.0))',
                    'right.handlemessage(bs.StandMessage((2, 1, 0), -1.57))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Suspense Build',
        'Burning fuse loop + a dim red\nlight + a warning beep - a\nready-made tension bed.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Suspense Build',
                    'timers = []',
                    'bs.newnode("light", attrs={',
                    '    "intensity": 0.8, "radius": 2.0, "color": (1.2, 0.1, 0.1),',
                    '    "position": (0, 1.5, 0), "volume_intensity_scale": 0.0',
                    '})',
                    'timers.append(bs.AppTimer(0.0, lambda: bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("fuse01"), "volume": 0.7, "loop": True',
                    '})))',
                    'timers.append(bs.AppTimer(1.5, lambda: bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("warnBeep"), "volume": 0.8, "loop": False',
                    '})))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Comedy Fail',
        'Error buzz + crowd boo + a\nslime splat FX for a fast\nslapstick fail beat.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Comedy Fail',
                    'timers = []',
                    'timers.append(bs.AppTimer(0.0, lambda: bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("error"), "volume": 1.0, "loop": False',
                    '})))',
                    'timers.append(bs.AppTimer(0.3, lambda: bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("boo"), "volume": 0.9, "loop": False',
                    '})))',
                    'timers.append(bs.AppTimer(0.3, lambda: bs.emitfx(',
                    '    position=(0, 1.0, 0), chunk_type="slime", emit_type="stickers",',
                    '    count=22, scale=0.9, spread=0.7',
                    ')))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Sports Intro',
        'Boxing bell + looping crowd\nchant + a referee whistle -\nready for a match-start scene.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Sports Intro',
                    'timers = []',
                    'timers.append(bs.AppTimer(0.0, lambda: bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("crowdChant"), "volume": 0.6, "loop": True',
                    '})))',
                    'timers.append(bs.AppTimer(0.5, lambda: bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("boxingBell"), "volume": 1.0, "loop": False',
                    '})))',
                    'timers.append(bs.AppTimer(1.0, lambda: bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("refWhistle"), "volume": 1.0, "loop": False',
                    '})))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Retro Arcade Blips',
        'Quick ascending arcade-style\nblip run - good for a menu or\nscore-tick moment.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Retro Arcade Blips',
                    'timers = []',
                    'seq = [',
                    "    (0.0, 'ding', 0.7),",
                    "    (0.15, 'dingSmall', 0.6),",
                    "    (0.3, 'dingSmallHigh', 0.6),",
                    "    (0.45, 'ding', 0.7),",
                    "    (0.6, 'dingSmallHigh', 0.8),",
                    ']',
                    'for t, nm, vol in seq:',
                    '    timers.append(bs.AppTimer(t, lambda nm=nm, vol=vol: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(nm), "volume": vol, "loop": False}',
                    '    )))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Suspense Rising Tension',
        'Alarm pulse followed by rising\ndings - simple building tension\nbed.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Suspense Rising Tension',
                    'timers = []',
                    'seq = [',
                    "    (0.0, 'alarm', 0.4),",
                    "    (0.8, 'dingSmall', 0.3),",
                    "    (1.6, 'dingSmallHigh', 0.35),",
                    "    (2.4, 'bellHigh', 0.4),",
                    "    (3.2, 'bellHigh', 0.5),",
                    ']',
                    'for t, nm, vol in seq:',
                    '    timers.append(bs.AppTimer(t, lambda nm=nm, vol=vol: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(nm), "volume": vol, "loop": False}',
                    '    )))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Bell Chime Cascade',
        'Low-to-high bell run, works\nwell for a peaceful or magical\nmoment.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Bell Chime Cascade',
                    'timers = []',
                    'seq = [',
                    "    (0.0, 'bellLow', 0.6),",
                    "    (0.4, 'bellMed', 0.6),",
                    "    (0.8, 'bellHigh', 0.6),",
                    "    (1.4, 'bellLow', 0.4),",
                    "    (1.8, 'bellHigh', 0.5),",
                    ']',
                    'for t, nm, vol in seq:',
                    '    timers.append(bs.AppTimer(t, lambda nm=nm, vol=vol: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(nm), "volume": vol, "loop": False}',
                    '    )))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Explosive Climax',
        'Three layered explosions plus\na big particle burst, all on\none beat - a ready-made\nfinale moment.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Explosive Climax',
                    'timers = []',
                    'seq = [',
                    "    (0.0, 'explosion05', 1.0),",
                    "    (0.0, 'explosion04', 0.9),",
                    "    (0.05, 'bigImpact', 0.8),",
                    ']',
                    'for t, nm, vol in seq:',
                    '    timers.append(bs.AppTimer(t, lambda nm=nm, vol=vol: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(nm), "volume": vol, "loop": False}',
                    '    )))',
                    '',
                    'fx_events = [',
                    "    (0.0, {'position': (0, 2, 0), 'velocity': (0, 10, 0), 'count': 150, 'scale': 3.5, 'spread': 3.0, 'chunk_type': 'spark', 'emit_type': 'distortion'}),",
                    ']',
                    'for t, kwargs in fx_events:',
                    '    timers.append(bs.AppTimer(t, lambda kwargs=kwargs: bs.emitfx(**kwargs)))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Score Combo Ding',
        'Five quick rising dings for a\ncombo/score-multiplier feel.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Score Combo Ding',
                    'timers = []',
                    'seq = [',
                    "    (0.0, 'dingSmallHigh', 0.4),",
                    "    (0.12, 'dingSmallHigh', 0.5),",
                    "    (0.24, 'dingSmallHigh', 0.6),",
                    "    (0.36, 'dingSmallHigh', 0.75),",
                    "    (0.48, 'scoreHit02', 1.0),",
                    ']',
                    'for t, nm, vol in seq:',
                    '    timers.append(bs.AppTimer(t, lambda nm=nm, vol=vol: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(nm), "volume": vol, "loop": False}',
                    '    )))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Robotic Glitch Sequence',
        'Power up/down and error\nsounds layered for a glitching\nrobot/machine feel.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Robotic Glitch Sequence',
                    'timers = []',
                    'seq = [',
                    "    (0.0, 'powerup01', 0.7),",
                    "    (0.3, 'error', 0.5),",
                    "    (0.6, 'powerdown01', 0.6),",
                    "    (0.9, 'powerup01', 0.8),",
                    "    (1.1, 'click01', 0.5),",
                    ']',
                    'for t, nm, vol in seq:',
                    '    timers.append(bs.AppTimer(t, lambda nm=nm, vol=vol: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(nm), "volume": vol, "loop": False}',
                    '    )))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Impact Barrage',
        'Layered punch sounds for a\nfast, punchy fight montage\nbeat.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Impact Barrage',
                    'timers = []',
                    'seq = [',
                    "    (0.0, 'punch01', 0.8),",
                    "    (0.2, 'punchWeak01', 0.6),",
                    "    (0.4, 'punchStrong01', 0.9),",
                    "    (0.6, 'punchStrong02', 1.0),",
                    "    (0.9, 'superPunch', 1.0),",
                    ']',
                    'for t, nm, vol in seq:',
                    '    timers.append(bs.AppTimer(t, lambda nm=nm, vol=vol: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(nm), "volume": vol, "loop": False}',
                    '    )))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Crowd Hype Wave',
        'Cheer building into a looping\nchant with a bell hit - good\nfor a stadium hype moment.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Crowd Hype Wave',
                    'timers = []',
                    'seq = [',
                    "    (0.0, 'cheer', 0.9),",
                    "    (0.4, 'crowdChant', 0.6),",
                    "    (1.2, 'boxingBell', 0.8),",
                    ']',
                    'for t, nm, vol in seq:',
                    '    timers.append(bs.AppTimer(t, lambda nm=nm, vol=vol: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(nm), "volume": vol, "loop": False}',
                    '    )))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Footstep Walk Cycle',
        'Alternating footstep sounds\ntimed for a walk cycle - handy\nfor syncing to a character\nwalking on-screen.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Footstep Walk Cycle',
                    'timers = []',
                    'seq = [',
                    "    (0.0, 'footImpact01', 0.6),",
                    "    (0.4, 'footImpact02', 0.6),",
                    "    (0.8, 'footImpact03', 0.6),",
                    "    (1.2, 'footImpact01', 0.6),",
                    "    (1.6, 'footImpact02', 0.6),",
                    ']',
                    'for t, nm, vol in seq:',
                    '    timers.append(bs.AppTimer(t, lambda nm=nm, vol=vol: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(nm), "volume": vol, "loop": False}',
                    '    )))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Glass Break Sequence',
        'Shatter, splatter, and\ndebris fall layered for a full\nglass-breaking beat.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Glass Break Sequence',
                    'timers = []',
                    'seq = [',
                    "    (0.0, 'shatter', 1.0),",
                    "    (0.05, 'splatter', 0.6),",
                    "    (0.15, 'debrisFall', 0.7),",
                    ']',
                    'for t, nm, vol in seq:',
                    '    timers.append(bs.AppTimer(t, lambda nm=nm, vol=vol: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(nm), "volume": vol, "loop": False}',
                    '    )))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Metal Clang Rhythm',
        'Rhythmic metal hits for a\nmachine-shop or forge feel.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Metal Clang Rhythm',
                    'timers = []',
                    'seq = [',
                    "    (0.0, 'metalHit', 0.8),",
                    "    (0.5, 'metalSkid', 0.5),",
                    "    (1.0, 'metalHit', 0.8),",
                    "    (1.5, 'metalHit', 0.6),",
                    "    (2.0, 'metalSkid', 0.5),",
                    ']',
                    'for t, nm, vol in seq:',
                    '    timers.append(bs.AppTimer(t, lambda nm=nm, vol=vol: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(nm), "volume": vol, "loop": False}',
                    '    )))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Ticking Clock Loop',
        'Steady ticking that speeds up\ninto a final impact - great\nfor a time-pressure beat.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Ticking Clock Loop',
                    'timers = []',
                    'seq = [',
                    "    (0.0, 'tick', 0.5),",
                    "    (0.6, 'tick', 0.5),",
                    "    (1.1, 'tick', 0.5),",
                    "    (1.5, 'tick', 0.5),",
                    "    (1.8, 'ticking', 0.6),",
                    "    (2.1, 'ticking', 0.6),",
                    "    (2.3, 'bigImpact', 1.0),",
                    ']',
                    'for t, nm, vol in seq:',
                    '    timers.append(bs.AppTimer(t, lambda nm=nm, vol=vol: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(nm), "volume": vol, "loop": False}',
                    '    )))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Race Start Sequence',
        'Two warning beeps then a go-\nsignal and revving engine -\nready for a race start.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Race Start Sequence',
                    'timers = []',
                    'seq = [',
                    "    (0.0, 'raceBeep1', 0.8),",
                    "    (0.8, 'raceBeep1', 0.8),",
                    "    (1.6, 'raceBeep2', 1.0),",
                    "    (1.6, 'revUp', 0.9),",
                    ']',
                    'for t, nm, vol in seq:',
                    '    timers.append(bs.AppTimer(t, lambda nm=nm, vol=vol: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(nm), "volume": vol, "loop": False}',
                    '    )))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Cash Reward Jingle',
        'Powerup chime into a cash\nregister hit - a satisfying\nreward stinger.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Cash Reward Jingle',
                    'timers = []',
                    'seq = [',
                    "    (0.0, 'healthPowerup', 0.7),",
                    "    (0.3, 'powerup01', 0.7),",
                    "    (0.6, 'cashRegister', 1.0),",
                    ']',
                    'for t, nm, vol in seq:',
                    '    timers.append(bs.AppTimer(t, lambda nm=nm, vol=vol: bs.newnode(',
                    '        "sound", attrs={"sound": bs.getsound(nm), "volume": vol, "loop": False}',
                    '    )))',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Freeze Frame Flash',
        'Freeze sound + a bright white\nflash light + "FREEZE!" text -\ngood for a slow-mo/pause gag.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Freeze Frame Flash',
                    'bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("freeze"), "volume": 1.0, "loop": False',
                    '})',
                    'bs.newnode("light", attrs={',
                    '    "intensity": 3.0, "radius": 6.0, "color": (2.0, 2.0, 2.2),',
                    '    "position": (0, 3, 0), "volume_intensity_scale": 0.0',
                    '})',
                    'bs.newnode("text", attrs={',
                    '    "text": "FREEZE!", "position": (0, 2.4, 0), "in_world": True,',
                    '    "shadow": 1.0, "flatness": 0.8, "scale": 0.024,',
                    '    "color": (1.6, 1.9, 2.2), "h_align": "center"',
                    '})',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Chapter Title Sequence',
        'A gong hit paired with a\ncentered chapter title - a\nfast way to mark a new scene.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Chapter Title Sequence',
                    'bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("gong"), "volume": 1.0, "loop": False',
                    '})',
                    'bs.newnode("text", attrs={',
                    '    "text": "CHAPTER ONE", "position": (0, 3.0, 0), "in_world": True,',
                    '    "shadow": 1.0, "flatness": 0.7, "scale": 0.025,',
                    '    "color": (2.2, 2.2, 1.0), "h_align": "center"',
                    '})',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Slow-Mo Sting',
        'Freeze sound + a dim blue\nlight, useful right before a\nslow-motion replay beat.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Slow-Mo Sting',
                    'bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("freeze"), "volume": 0.8, "loop": False',
                    '})',
                    'bs.newnode("light", attrs={',
                    '    "intensity": 0.9, "radius": 4.0, "color": (0.4, 0.6, 1.4),',
                    '    "position": (0, 2, 0), "volume_intensity_scale": 0.0',
                    '})',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Credits Roll Setup',
        'Orchestra hit stinger + a\ncentered "THE END" card - a\nready-made closer.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Credits Roll Setup',
                    'bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("orchestraHit"), "volume": 1.0, "loop": False',
                    '})',
                    'bs.newnode("text", attrs={',
                    '    "text": "THE END", "position": (0, 2.2, 0), "in_world": True,',
                    '    "shadow": 1.0, "flatness": 0.8, "scale": 0.022,',
                    '    "color": (2.0, 2.0, 2.0), "h_align": "center"',
                    '})',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Confetti Celebration',
        'Gold spark burst + a cheer -\na quick celebratory moment\nwithout needing separate FX\nand Sound presets.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Confetti Celebration',
                    'bs.newnode("sound", attrs={',
                    '    "sound": bs.getsound("cheer"), "volume": 1.0, "loop": False',
                    '})',
                    'bs.emitfx(',
                    '    position=(0, 2.0, 0), velocity=(0, 4, 0), count=70, scale=1.3,',
                    '    spread=2.0, chunk_type="spark", emit_type="stickers"',
                    ')',
                ))
            }
        }
    ))

    presets.append((
        6,
        'Random Sound Roulette',
        'Fires a random sound from a\ncurated safe list every 0.4s -\na fun chaos/easter-egg preset\nfor testing or a silly montage.',
        {
            'data': {
                'code': '\n'.join((
                    '# MOVI Random Sound Roulette',
                    'timers = []',
                    'pool = ["ding", "boo", "cheer", "error", "gong", "achievement",',
                    '        "powerup01", "punchWeak01", "click01", "dripity"]',
                    'for i in range(8):',
                    '    t = i * 0.4',
                    '    timers.append(bs.AppTimer(t, lambda: bs.newnode("sound", attrs={',
                    '        "sound": bs.getsound(random.choice(pool)), "volume": 0.8, "loop": False',
                    '    })))',
                ))
            }
        }
    ))

    return presets
