# COPYRIGHTED, and ee also i wasn't the only one working on this, so yeah we also got some ideas from fluffys party window, you can do changes here if you want.
"""
• Authors: Drap, Nizar
• Discord accs: drap._ — prollynizar [Contact for any bugs ONLY]
Have fun using our plugin!
"""
# ba_meta require api 9
from __future__ import annotations

import colorsys
import logging
import math
import random
import socket
import textwrap
import threading
import time
import traceback
import weakref
from collections import deque
from typing import Any, Dict, List, Optional, Sequence, Tuple

import babase
import bascenev1 as bs
import bauiv1 as bui
import bauiv1lib.party as bui_party
from bauiv1lib.colorpicker import ColorPickerExact
from bauiv1lib.confirm import ConfirmWindow
from bauiv1lib.popup import PopupMenuWindow

__version__ = "1.0.2"
__author__ = ["Nizar", "Drap"]

plugman = dict(
    plugin_name="Enhanced_PartyWindow",  # optional, defaults to the file name
    description="a fully enhanced version of the bs PartyWindow, includes many options and features!",
    external_url="https://discord.com/channels/1001896771347304639/1558597818359353515",
    authors=[
        {"name": __author__[0], "email": "", "discord": "prollynizar"},
        {"name": __author__[1], "email": "mrunittest@gmail.com", "discord": "drap._"}
    ],
    version=__version__,
)

def _print_exception(msg: str = '') -> None:
    try:
        logging.exception(msg or 'Unhandled exception')
    except Exception:
        traceback.print_exc()


def _get_ping_color(ping_val):
    try:
        if ping_val < 75:
            return (0.0, 1.0, 0.0)
        if ping_val < 150:
            return (0.5, 1.0, 0.0)
        if ping_val < 300:
            return (1.0, 1.0, 0.0)
        if ping_val < 600:
            return (1.0, 0.5, 0.0)
        return (1.0, 0.0, 0.0)
    except Exception:
        return (0.6, 0.6, 0.6)


def _creat_Lstr_list(strings: list) -> list:
    return [babase.Lstr(value=s) for s in strings]


def _popup_scale() -> float:
    ui = bui.app.ui_v1.uiscale
    return (2.3 if ui is bui.UIScale.SMALL else
            1.65 if ui is bui.UIScale.MEDIUM else 1.23)


_FX_T0 = time.time()
_CFG_THEME = 'BetterParty_Theme'
_CFG_FX = 'BetterParty_FX'
_CFG_SPEED = 'BetterParty_Speed'
_CFG_HISTORY = 'BetterParty_ServerHistory'
_CFG_HUB_TAB = 'BetterParty_HubTab'
_CFG_HUB_SORT = 'BetterParty_HubSort'
_CFG_AUTO = 'BetterParty_Auto'

_FX_LEVEL_NAMES = ['Off', 'Low', 'High']
_SPEED_VALUES = [0.5, 1.0, 1.8]
_SPEED_NAMES = ['Slow', 'Normal', 'Fast']

THEMES: Dict[str, Dict[str, Any]] = {
    'Aurora': dict(a=(0.16, 0.38, 0.92), b=(0.16, 0.75, 0.35), mode='wave',
                   tex=('circleSoft', 'star'), dir=1),
    'Neon Pink': dict(a=(1.0, 0.12, 0.62), b=(0.55, 0.15, 1.0), mode='wave',
                      tex=('heart', 'star', 'circleSoft'), dir=1),
    'Lava': dict(a=(1.0, 0.28, 0.05), b=(0.75, 0.05, 0.12), mode='wave',
                 tex=('star', 'circleSoft'), dir=1),
    'Ocean': dict(a=(0.05, 0.40, 0.95), b=(0.02, 0.78, 0.80), mode='wave',
                  tex=('circleOutline', 'circleSoft'), dir=1),
    'Toxic': dict(a=(0.25, 0.95, 0.12), b=(0.75, 0.90, 0.10), mode='wave',
                  tex=('circleSoft', 'star'), dir=1),
    'Galaxy': dict(a=(0.40, 0.10, 0.85), b=(0.08, 0.15, 0.55), mode='wave',
                   tex=('star', 'star', 'circleSoft'), dir=1),
    'Candy': dict(a=(1.0, 0.55, 0.80), b=(0.50, 0.80, 1.0), mode='wave',
                  tex=('heart', 'circleSoft'), dir=1),
    'Gold Rush': dict(a=(1.0, 0.78, 0.12), b=(0.95, 0.45, 0.05), mode='wave',
                      tex=('star', 'circleSoft'), dir=1),
    'Frost': dict(a=(0.55, 0.85, 1.0), b=(0.85, 0.93, 1.0), mode='wave',
                  tex=('circleSoft', 'star'), dir=-1),
    'Sunset': dict(a=(1.0, 0.35, 0.25), b=(0.65, 0.20, 0.90), mode='wave',
                   tex=('circleSoft', 'star'), dir=1),
    'Matrix': dict(a=(0.05, 0.80, 0.25), b=(0.0, 0.45, 0.15), mode='wave',
                   tex=('circleSoft',), dir=-1),
    'Midnight': dict(a=(0.08, 0.10, 0.30), b=(0.22, 0.12, 0.48), mode='wave',
                     tex=('star', 'circleSoft'), dir=1),
    'Rainbow': dict(a=(1.0, 0.2, 0.2), b=(0.2, 0.2, 1.0), mode='rainbow',
                    tex=('star', 'heart', 'circleSoft'), dir=1),
}
THEME_ORDER = list(THEMES.keys())


def _get_theme(name: str) -> Dict[str, Any]:
    th = THEMES.get(name)
    if th is not None:
        return th
    a, b = THEMES['Aurora']['a'], THEMES['Aurora']['b']
    try:
        saved = babase.app.config.get('PartyWindow_Wave_Colors')
        if (isinstance(saved, (list, tuple)) and len(saved) == 2
                and all(isinstance(c, (list, tuple)) and len(c) == 3 for c in saved)):
            a = tuple(float(x) for x in saved[0])
            b = tuple(float(x) for x in saved[1])
    except Exception:
        pass
    return dict(a=a, b=b, mode='wave', tex=('star', 'circleSoft'), dir=1)


def _theme_rgb(theme: Dict[str, Any], elapsed: float, speed: float = 1.0):
    period = 4.0 / max(0.25, speed)
    if theme.get('mode') == 'rainbow':
        h = (elapsed / (period * 2.5)) % 1.0
        s, v = 0.80, 0.95
    else:
        phase = (elapsed % period) / period
        t = (1 - math.cos(phase * 2 * math.pi)) / 2
        h_a, s_a, v_a = colorsys.rgb_to_hsv(*theme['a'])
        h_b, s_b, v_b = colorsys.rgb_to_hsv(*theme['b'])
        dh = h_b - h_a
        if dh > 0.5:
            dh -= 1.0
        elif dh < -0.5:
            dh += 1.0
        h = (h_a + dh * t) % 1.0
        s = s_a + (s_b - s_a) * t
        v = v_a + (v_b - v_a) * t
    v = min(1.0, v * (0.94 + 0.06 * math.sin(elapsed * 2.3)))
    return colorsys.hsv_to_rgb(h, s, v)


def _accent(rgb, sat: float = 0.55, val: float = 0.88):
    h, s, _v = colorsys.rgb_to_hsv(*rgb)
    return colorsys.hsv_to_rgb(h, min(1.0, 0.25 + s * sat), val)


def _light(rgb, k: float = 0.5):
    h, s, _v = colorsys.rgb_to_hsv(*rgb)
    return colorsys.hsv_to_rgb(h, s * k, 1.0)


def _fmt_dur(sec: float) -> str:
    m, s = divmod(int(max(0, sec)), 60)
    h, m = divmod(m, 60)
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'


def _ago(ts: float) -> str:
    if not ts:
        return ''
    d = time.time() - ts
    if d < 45:
        return 'just now'
    if d < 3600:
        return f'{int(d // 60)}m ago'
    if d < 86400:
        return f'{int(d // 3600)}h ago'
    return f'{int(d // 86400)}d ago'


class _FXLayer:

    N_PART = 14
    N_ORB = 5
    N_TWINKLE = 16
    N_RING = 3
    N_BURST = 14
    TAIL = 0.20

    def __init__(self, root: bui.Widget, width: float, height: float,
                 level: int, theme: Dict[str, Any],
                 halos: Optional[List[Any]] = None,
                 rim: Optional[List[Tuple[float, float]]] = None) -> None:
        self._w = float(width)
        self._h = float(height)
        self._level = level
        self._theme = theme
        self._n = 0
        self._rnd = random.Random()
        self._last_pulse = -9.0
        w, h = self._w, self._h
        rnd = random.Random(7)
        soft = bui.gettexture('circleSoft')
        star = bui.gettexture('star')

        def img(tex, size=(10, 10)):
            return bui.imagewidget(parent=root, position=(0, 0), size=size,
                                   texture=tex, color=(1, 1, 1), opacity=0.0)

        self._orbs: List[Dict[str, Any]] = []
        for i in range(self.N_ORB):
            self._orbs.append(dict(
                x=rnd.uniform(0.15, 0.85) * w, y=rnd.uniform(0.2, 0.8) * h,
                r=rnd.uniform(50, 100), fx=rnd.uniform(0.12, 0.3),
                fy=rnd.uniform(0.1, 0.25), ph=rnd.uniform(0, 6.28), w=img(soft)))
        self._twk: List[Dict[str, Any]] = []
        for i in range(self.N_TWINKLE):
            self._twk.append(dict(
                x=rnd.uniform(0.06, 0.94) * w, y=rnd.uniform(0.08, 0.92) * h,
                s=rnd.uniform(5, 10), f=rnd.uniform(0.6, 1.8),
                ph=rnd.uniform(0, 6.28), op=-1.0, w=img(star)))

        self._glow = bui.imagewidget(
            parent=root, position=(w * 0.12, h - 80), size=(w * 0.76, 90),
            texture=soft, color=(1, 1, 1), opacity=0.0)
        self._shine = bui.imagewidget(
            parent=root, position=(-80, 6), size=(46, h - 12),
            texture=bui.gettexture('softRectVertical'), color=(1, 1, 1),
            opacity=0.0)
        self._tshine = bui.imagewidget(
            parent=root, position=(-80, h - 62), size=(30, 46),
            texture=bui.gettexture('softRectVertical'), color=(1, 1, 1),
            opacity=0.0)
        self._tshine_on = False

        self._halos: List[Dict[str, Any]] = []
        for cx, cy, sz in (halos or []):
            self._halos.append(dict(x=cx, y=cy, s=sz, w=img(soft, (sz, sz))))

        self._dots: List[Dict[str, Any]] = []
        for i, (u, v) in enumerate(rim or []):
            x, y = u * w, v * h
            bloom = None
            if i % 2 == 0:
                bloom = bui.imagewidget(
                    parent=root, position=(x - 9, y - 9), size=(18, 18),
                    texture=soft, color=(1, 1, 1), opacity=0.0)
            self._dots.append(dict(x=x, y=y, op=-1.0, bloom=bloom, w=None))
        for d in self._dots:
            d['w'] = bui.imagewidget(
                parent=root, position=(d['x'] - 3, d['y'] - 3), size=(6, 6),
                texture=soft, color=(1, 1, 1), opacity=0.0)

        self._parts: List[Dict[str, Any]] = []
        for i in range(self.N_PART):
            self._parts.append(dict(
                x=rnd.uniform(0.07, 0.93) * w,
                speed=rnd.uniform(0.035, 0.10), off=rnd.random(),
                amp=rnd.uniform(4, 18), freq=rnd.uniform(0.6, 1.8),
                ph=rnd.uniform(0, 6.28), size=rnd.uniform(9, 22),
                maxop=rnd.uniform(0.35, 0.8), tex_i=i, w=img(soft, (12, 12))))

        self._shoot_w = [img(star, (14, 14)), img(soft, (10, 10)),
                         img(soft, (8, 8)), img(soft, (6, 6))]
        self._shoot: Optional[Dict[str, float]] = None
        self._next_shoot = 3.0

        self._rings = [dict(t0=None, x=0.0, y=0.0,
                            w=bui.imagewidget(
                                parent=root, position=(0, 0), size=(20, 20),
                                texture=bui.gettexture('circleOutline'),
                                color=(1, 1, 1), opacity=0.0))
                       for _ in range(self.N_RING)]
        self._bursts = [dict(t0=None, x=0.0, y=0.0, vx=0.0, vy=0.0,
                             col=(1, 1, 1), w=img(star if i % 2 else soft, (12, 12)))
                        for i in range(self.N_BURST)]
        self.set_theme(theme)
        self.set_level(level)

    def set_theme(self, theme: Dict[str, Any]) -> None:
        self._theme = theme
        texs = theme.get('tex') or ('circleSoft',)
        for p in self._parts:
            try:
                bui.imagewidget(edit=p['w'],
                                texture=bui.gettexture(texs[p['tex_i'] % len(texs)]))
            except Exception:
                pass

    def _hi_widgets(self):
        wl = [o['w'] for o in self._orbs] + [t['w'] for t in self._twk]
        wl += [hh['w'] for hh in self._halos] + list(self._shoot_w)
        wl += [d['bloom'] for d in self._dots if d['bloom'] is not None]
        wl.append(self._tshine)
        return wl

    def set_level(self, level: int) -> None:
        self._level = level
        hide = []
        if level <= 0:
            hide += self._hi_widgets() + [self._glow, self._shine]
            hide += [p['w'] for p in self._parts] + [d['w'] for d in self._dots]
            hide += [r['w'] for r in self._rings] + [b['w'] for b in self._bursts]
            self._shoot = None
            for r in self._rings:
                r['t0'] = None
            for b in self._bursts:
                b['t0'] = None
        else:
            if level < 2:
                hide += self._hi_widgets()
                self._shoot = None
                self._tshine_on = False
                for b in self._bursts:
                    b['t0'] = None
                hide += [b['w'] for b in self._bursts]
            hide += [p['w'] for p in self._parts[self._active_count():]]
        for d in self._dots:
            d['op'] = -1.0
        for t in self._twk:
            t['op'] = -1.0
        for wd in hide:
            try:
                bui.imagewidget(edit=wd, opacity=0.0)
            except Exception:
                pass

    def _active_count(self) -> int:
        return 0 if self._level <= 0 else (6 if self._level == 1 else self.N_PART)

    def pulse(self, x: Optional[float] = None, y: Optional[float] = None) -> None:
        if self._level <= 0:
            return
        now = time.time() - _FX_T0
        if now - self._last_pulse < 0.35:
            return
        self._last_pulse = now
        ring = min(self._rings, key=lambda r: -1.0 if r['t0'] is None else r['t0'])
        ring.update(t0=now, x=self._w / 2 if x is None else x,
                    y=self._h / 2 if y is None else y)

    def burst(self, x: Optional[float] = None, y: Optional[float] = None) -> None:
        if self._level < 2:
            return
        now = time.time() - _FX_T0
        cx = self._w / 2 if x is None else x
        cy = self._h * 0.6 if y is None else y
        rnd = self._rnd
        for b in self._bursts:
            a = rnd.uniform(0, 6.283)
            sp = rnd.uniform(70, 200)
            b.update(t0=now, x=cx, y=cy, vx=math.cos(a) * sp, vy=math.sin(a) * sp,
                     col=colorsys.hsv_to_rgb(rnd.random(), 0.55, 1.0))

    def tick(self, elapsed: float, rgb, speed: float) -> None:
        if self._level <= 0:
            return
        self._n += 1
        n = self._n
        w, h = self._w, self._h
        hi = self._level >= 2
        light = _light(rgb, 0.45)
        pulse = (1 + math.sin(elapsed * 1.6 * speed)) / 2
        ih = colorsys.rgb_to_hsv(*light)[0]

        bui.imagewidget(edit=self._glow, color=light, opacity=0.12 + 0.22 * pulse)
        sx = ((elapsed * 0.13 * speed) % 1.6 - 0.3) * w
        bui.imagewidget(edit=self._shine, position=(sx, 6), opacity=0.07)

        if n % (2 if hi else 3) == 0:
            cnt = len(self._dots)
            base = 0.30 + 0.10 * pulse
            h1 = (elapsed * 0.10 * speed) % 1.0
            h2 = (h1 + 0.5) % 1.0
            recolor = (n % 12 == 0)
            for i, d in enumerate(self._dots):
                t = i / cnt
                k = 0.0
                for head in (h1, h2):
                    dist = (head - t) % 1.0
                    if dist < self.TAIL:
                        k = max(k, (1.0 - dist / self.TAIL) ** 1.6)
                op = base + (0.98 - base) * k
                if k > 0.0 or abs(op - d['op']) > 0.02 or recolor:
                    sz = 6.0 + 5.0 * k
                    col = tuple(c + (1.0 - c) * 0.75 * k for c in light)
                    bui.imagewidget(
                        edit=d['w'], position=(d['x'] - sz / 2, d['y'] - sz / 2),
                        size=(sz, sz), color=col, opacity=op)
                    if hi and d['bloom'] is not None:
                        bs_ = 16.0 + 16.0 * k
                        bui.imagewidget(
                            edit=d['bloom'],
                            position=(d['x'] - bs_ / 2, d['y'] - bs_ / 2),
                            size=(bs_, bs_), color=light,
                            opacity=0.05 + 0.30 * k)
                    d['op'] = op

        direction = self._theme.get('dir', 1)
        span = h - 2 * 17 - 20
        for p in self._parts[:self._active_count()]:
            prog = (p['off'] + elapsed * p['speed'] * speed) % 1.0
            if direction < 0:
                prog = 1.0 - prog
            sz = p['size'] * (0.75 + 0.25 * math.sin(elapsed * 2 + p['ph']))
            x = p['x'] + math.sin(elapsed * p['freq'] + p['ph']) * p['amp']
            y = 17 + 10 + prog * span
            op = math.sin(math.pi * min(1.0, max(0.0, prog))) * p['maxop']
            bui.imagewidget(edit=p['w'], position=(x - sz / 2, y - sz / 2),
                            size=(sz, sz), opacity=op, color=light)

        for r in self._rings:
            if r['t0'] is None:
                continue
            age = elapsed - r['t0']
            if age >= 1.2:
                r['t0'] = None
                bui.imagewidget(edit=r['w'], opacity=0.0)
                continue
            f = age / 1.2
            sz = 30 + f * max(w, h) * 0.95
            bui.imagewidget(edit=r['w'], position=(r['x'] - sz / 2, r['y'] - sz / 2),
                            size=(sz, sz), color=light, opacity=0.65 * (1 - f) ** 1.5)

        if not hi:
            return

        if n % 2 == 0:
            for i, o in enumerate(self._orbs):
                x = o['x'] + math.sin(elapsed * o['fx'] + o['ph']) * 45
                y = o['y'] + math.cos(elapsed * o['fy'] + o['ph']) * 30
                sz = o['r'] * (1 + 0.08 * math.sin(elapsed * 0.9 + o['ph']))
                hh, ss, _vv = colorsys.rgb_to_hsv(*light)
                col = colorsys.hsv_to_rgb((hh + 0.07 * i) % 1.0, min(1.0, ss + 0.3), 1.0)
                bui.imagewidget(
                    edit=o['w'], position=(x - sz / 2, y - sz / 2), size=(sz, sz),
                    color=col,
                    opacity=0.05 + 0.05 * (1 + math.sin(elapsed * 0.6 + o['ph'])) / 2)
            for t in self._twk:
                k = max(0.0, math.sin(elapsed * t['f'] + t['ph'])) ** 3
                op = 0.05 + 0.75 * k
                if abs(op - t['op']) > 0.04:
                    sz = t['s'] * (0.7 + 0.5 * k)
                    bui.imagewidget(
                        edit=t['w'], position=(t['x'] - sz / 2, t['y'] - sz / 2),
                        size=(sz, sz), color=light, opacity=op)
                    t['op'] = op

        for i, hl in enumerate(self._halos):
            ph = math.sin(elapsed * 2.2 * speed + i * 1.3)
            sz = hl['s'] * (1 + 0.10 * ph)
            bui.imagewidget(
                edit=hl['w'], position=(hl['x'] - sz / 2, hl['y'] - sz / 2),
                size=(sz, sz), color=light, opacity=0.10 + 0.14 * (1 + ph) / 2)

        cyc = ((elapsed * speed) % 7.0) / 7.0
        if cyc < 0.22:
            f = cyc / 0.22
            bui.imagewidget(edit=self._tshine, position=(w * 0.2 + f * w * 0.6, h - 62),
                            color=(1, 1, 1), opacity=0.30 * math.sin(math.pi * f))
            self._tshine_on = True
        elif self._tshine_on:
            bui.imagewidget(edit=self._tshine, opacity=0.0)
            self._tshine_on = False

        sh = self._shoot
        if sh is None:
            if elapsed >= self._next_shoot:
                rn = self._rnd
                self._shoot = dict(t0=elapsed, x=rn.uniform(0.08, 0.5) * w,
                                   y=rn.uniform(0.7, 0.95) * h,
                                   vx=rn.uniform(260, 340), vy=-rn.uniform(120, 190))
        else:
            age = elapsed - sh['t0']
            if age > 1.0:
                for wd in self._shoot_w:
                    bui.imagewidget(edit=wd, opacity=0.0)
                self._shoot = None
                self._next_shoot = elapsed + self._rnd.uniform(5.0, 10.0)
            else:
                for j, wd in enumerate(self._shoot_w):
                    a = age - 0.05 * j
                    if a < 0:
                        continue
                    x = sh['x'] + sh['vx'] * a
                    y = sh['y'] + sh['vy'] * a
                    sz = (14, 10, 8, 6)[j]
                    bui.imagewidget(
                        edit=wd, position=(x - sz / 2, y - sz / 2), color=light,
                        opacity=(1 - age) * (0.95, 0.55, 0.35, 0.2)[j])

        for b in self._bursts:
            if b['t0'] is None:
                continue
            age = elapsed - b['t0']
            if age >= 1.1:
                b['t0'] = None
                bui.imagewidget(edit=b['w'], opacity=0.0)
                continue
            x = b['x'] + b['vx'] * age
            y = b['y'] + b['vy'] * age - 70.0 * age * age
            sz = 16 * (1 - 0.4 * age / 1.1)
            bui.imagewidget(edit=b['w'], position=(x - sz / 2, y - sz / 2),
                            size=(sz, sz), color=b['col'],
                            opacity=0.9 * (1 - age / 1.1) ** 1.2)


def _srv_key(addr, port) -> str:
    return f'{str(addr).strip()}@{int(port)}'


def _hist() -> Dict[str, Any]:
    cfg = babase.app.config
    h = cfg.get(_CFG_HISTORY)
    if not isinstance(h, dict):
        h = {}
        cfg[_CFG_HISTORY] = h
    return h


def history_record(addr, port, name: Optional[str] = None,
                   joined: bool = True) -> Optional[Dict[str, Any]]:
    try:
        addr = str(addr).strip()
        port = int(port)
        if not addr:
            return None
        h = _hist()
        key = _srv_key(addr, port)
        now = time.time()
        e = h.get(key)
        if not isinstance(e, dict):
            e = dict(addr=addr, port=port, name=(name or addr),
                     first=now, last=now, count=0)
            h[key] = e
        if joined:
            e['count'] = int(e.get('count', 0)) + 1
            e['last'] = now
        if name and name != e.get('name'):
            e['name'] = name
        babase.app.config.commit()
        return e
    except Exception:
        _print_exception('history_record failed')
        return None


def _saved_servers() -> Dict[str, Any]:
    cfg = babase.app.config
    s = cfg.get('Saved Servers')
    if not isinstance(s, dict):
        s = {}
        cfg['Saved Servers'] = s
    return s


def _find_favorite(addr, port) -> Optional[str]:
    addr = str(addr).strip()
    for k, v in _saved_servers().items():
        try:
            if (isinstance(v, dict) and str(v.get('addr', '')).strip() == addr
                    and int(v.get('port', -1)) == int(port)):
                return k
        except Exception:
            continue
    return None


def favorites_save(addr, port, name: str):
    addr = str(addr).strip()
    port = int(port)
    name = (name or '').strip() or addr
    saved = _saved_servers()
    k = _find_favorite(addr, port)
    if k is not None:
        old = str(saved[k].get('name', ''))
        if name != old:
            saved[k]['name'] = name
            babase.app.config.commit()
            return 'renamed', old
        return 'exists', old
    saved[_srv_key(addr, port)] = {'addr': addr, 'port': port, 'name': name}
    babase.app.config.commit()
    return 'added', ''


_PING_CACHE: Dict[str, Dict[str, Any]] = {}
_PING_SEM = threading.BoundedSemaphore(6)


def _ping_once(addr: str, port: int, tries: int = 3,
               timeout: float = 1.0) -> Optional[float]:
    sock = None
    try:
        infos = socket.getaddrinfo(addr, int(port), 0, socket.SOCK_DGRAM)
        fam, _typ, _proto, _cn, sockaddr = infos[0]
        sock = socket.socket(fam, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.connect(sockaddr)
        for _i in range(tries):
            t0 = time.time()
            sock.send(b'\x0b')
            try:
                res = sock.recv(10)
            except Exception:
                res = None
            if res == b'\x0c':
                return (time.time() - t0) * 1000.0
    except Exception:
        pass
    finally:
        try:
            if sock is not None:
                sock.close()
        except Exception:
            pass
    return None


def _ping_worker(addr: str, port: int, key: str) -> None:
    with _PING_SEM:
        ms = _ping_once(addr, port)
    _PING_CACHE[key] = dict(ms=ms, t=time.time(), busy=False)


def _ping_async(addr, port, force: bool = False) -> None:
    try:
        key = _srv_key(addr, port)
        cur = _PING_CACHE.get(key)
        if cur is not None and (cur.get('busy') or
                                (not force and time.time() - cur.get('t', 0) < 20)):
            return
        _PING_CACHE[key] = dict(ms=None, t=time.time(), busy=True)
        threading.Thread(target=_ping_worker, args=(str(addr), int(port), key),
                         daemon=True).start()
    except Exception:
        pass


def _ping_text(key: str):
    c = _PING_CACHE.get(key)
    if c is None:
        return '', None
    if c.get('busy'):
        return '...', None
    if c.get('ms') is None:
        return 'timeout', (1.0, 0.35, 0.35)
    return f"{int(c['ms'])} ms", _get_ping_color(c['ms'])


def _is_ip_literal(s: str) -> bool:
    for fam in (socket.AF_INET, socket.AF_INET6):
        try:
            socket.inet_pton(fam, s)
            return True
        except Exception:
            pass
    return False


def _hsv(h: float, s: float, v: float):
    return colorsys.hsv_to_rgb(h % 1.0, max(0.0, min(1.0, s)),
                               max(0.0, min(1.0, v)))


def _palette(rgb) -> Dict[str, Any]:
    h, s, _v = colorsys.rgb_to_hsv(*rgb)
    s = min(1.0, 0.15 + s * 0.8)
    return dict(
        body=_hsv(h, s * 0.9, 0.13), card=_hsv(h, s * 0.8, 0.21),
        head=_hsv(h, s * 0.8, 0.29), field=_hsv(h, s * 0.8, 0.10),
        edge=_hsv(h, s * 0.65, 0.72), edge_dim=_hsv(h, s * 0.65, 0.46),
        accent=_accent(rgb), light=_light(rgb, 0.45), text=_light(rgb, 0.16))


def _kind_colors(pal: Dict[str, Any]) -> Dict[str, Any]:
    return {'body': (pal['body'], pal['edge']),
            'card': (pal['card'], pal['edge_dim']),
            'head': (pal['head'], pal['edge']),
            'field': (pal['field'], pal['edge_dim'])}


class _RRect:

    def __init__(self, parent: bui.Widget, x: float, y: float, w: float,
                 h: float, r: float, color=(1, 1, 1)) -> None:
        r = max(1.0, min(r, w / 2.0, h / 2.0))
        white = bui.gettexture('white')
        disc = bui.gettexture('circle')
        self.parts: List[bui.Widget] = []

        def add(px, py, pw, ph, tex):
            self.parts.append(bui.imagewidget(
                parent=parent, position=(px, py), size=(pw, ph),
                texture=tex, color=color, opacity=1.0))

        add(x + r, y, w - 2 * r, h, white)
        add(x, y + r, r, h - 2 * r, white)
        add(x + w - r, y + r, r, h - 2 * r, white)
        tile = 2 * r / 0.97
        for cx, cy in ((x + r, y + r), (x + w - r, y + r),
                       (x + r, y + h - r), (x + w - r, y + h - r)):
            add(cx - tile / 2, cy - tile / 2, tile, tile, disc)

    def recolor(self, rgb) -> None:
        for p in self.parts:
            bui.imagewidget(edit=p, color=rgb)


class _Card:

    def __init__(self, parent, x, y, w, h, r, bw: float = 1.6) -> None:
        self.edge = _RRect(parent, x, y, w, h, r)
        self.fill = _RRect(parent, x + bw, y + bw, w - 2 * bw, h - 2 * bw,
                           max(1.0, r - bw))

    def recolor(self, edge, fill) -> None:
        self.edge.recolor(edge)
        self.fill.recolor(fill)


def _rounded_rim(w: float, h: float, radius: float, inset: float,
                 spacing: float = 18.0) -> List[Tuple[float, float]]:
    rr = max(2.0, radius - inset)
    x0, x1, y0, y1 = inset, w - inset, inset, h - inset
    lh = (x1 - x0) - 2 * rr
    lv = (y1 - y0) - 2 * rr
    arc = math.pi * rr / 2
    total = 2 * lh + 2 * lv + 4 * arc
    n = max(24, int(round(total / spacing)))
    pts = []
    for k in range(n):
        d = total * k / n
        if d < lh:
            p = (x0 + rr + d, y0)
        else:
            d -= lh
            if d < arc:
                a = -math.pi / 2 + d / rr
                p = (x1 - rr + rr * math.cos(a), y0 + rr + rr * math.sin(a))
            else:
                d -= arc
                if d < lv:
                    p = (x1, y0 + rr + d)
                else:
                    d -= lv
                    if d < arc:
                        a = d / rr
                        p = (x1 - rr + rr * math.cos(a), y1 - rr + rr * math.sin(a))
                    else:
                        d -= arc
                        if d < lh:
                            p = (x1 - rr - d, y1)
                        else:
                            d -= lh
                            if d < arc:
                                a = math.pi / 2 + d / rr
                                p = (x0 + rr + rr * math.cos(a),
                                     y1 - rr + rr * math.sin(a))
                            else:
                                d -= arc
                                if d < lv:
                                    p = (x0, y1 - rr - d)
                                else:
                                    d -= lv
                                    a = math.pi + d / rr
                                    p = (x0 + rr + rr * math.cos(a),
                                         y0 + rr + rr * math.sin(a))
        pts.append((p[0] / w, p[1] / h))
    return pts


class _Skin:

    def __init__(self, root: bui.Widget, w: float, h: float,
                 theme: Dict[str, Any], level: int,
                 cards: List[Tuple[float, float, float, float, float, str]],
                 halos: Optional[List[Any]] = None,
                 radius: float = 18.0) -> None:
        self._items: List[Tuple[_Card, str]] = []
        self._items.append((_Card(root, 0, 0, w, h, radius, bw=2.0), 'body'))
        for x, y, cw, ch, r, kind in cards:
            self._items.append((_Card(root, x, y, cw, ch, r), kind))
        self.fx = _FXLayer(root, w, h, level, theme, halos,
                           rim=_rounded_rim(w, h, radius, 5.0))
        self.pal: Dict[str, Any] = _palette(theme['a'])
        self.recolor(theme['a'])

    def recolor(self, rgb) -> None:
        pal = _palette(rgb)
        self.pal = pal
        kinds = _kind_colors(pal)
        for card, kind in self._items:
            fill, edge = kinds[kind]
            card.recolor(edge, fill)


_CFG_RECONNECT = 'BetterParty_Reconnect'
_CFG_ALERTS = 'BetterParty_Alerts'
_CFG_QUICK = 'BetterParty_Quick'
_CFG_CMDS = 'BetterParty_Cmds'
_DEFAULT_QUICK = ['gg', 'nice one', 'lol', 'wait for me', 'brb', 'ez']
_DEFAULT_CMDS = ['/list', '/help', '/ping', '/stats']


class _Live:

    def __init__(self) -> None:
        self.connected = False
        self.session_start: Optional[float] = None
        self.addr = ''
        self.port = 0
        self.name = ''
        self.target: Optional[Tuple[str, int]] = None
        self.ping_ms: Optional[float] = None
        self.ping_hist: deque = deque(maxlen=24)
        self.user_left = False
        self.reconnect_at: Optional[float] = None
        self.reconnect_tries = 0


_L = _Live()
_tracker_timer: Any = None
_orig_disconnect: Any = None


def _tracker_tick() -> None:
    try:
        info = bs.get_connection_to_host_info_2()
    except Exception:
        info = None
    now = time.time()
    cfg = babase.app.config
    try:
        if info is not None:
            addr = (getattr(info, 'address', '') or '')
            port = int(getattr(info, 'port', 0) or 0)
            name = (getattr(info, 'name', '') or '').strip()
            if not _L.connected:
                _L.connected = True
                _L.session_start = now
                _L.user_left = False
                _L.reconnect_at = None
                _L.reconnect_tries = 0
                _L.ping_hist.clear()
                if addr and port:
                    history_record(addr, port, name or None, joined=True)
            _L.addr, _L.port, _L.name = addr, port, name
            if addr and port:
                _L.target = (addr, port)
                e = _hist().get(_srv_key(addr, port))
                if name and isinstance(e, dict) and e.get('name') != name:
                    e['name'] = name
                    cfg.commit()
            return
        if _L.connected:
            _L.connected = False
            _L.session_start = None
            _L.ping_ms = None
            if cfg.get(_CFG_RECONNECT, False) and not _L.user_left and _L.target:
                _L.reconnect_tries = 0
                _L.reconnect_at = now + 5.0
                bui.screenmessage('Disconnected. Auto-reconnect in 5 s '
                                  '(turn it off in the ... menu)',
                                  color=(1, 0.8, 0.3))
            _L.user_left = False
        if _L.reconnect_at is not None and now >= _L.reconnect_at:
            if not cfg.get(_CFG_RECONNECT, False) or _L.target is None:
                _L.reconnect_at = None
                return
            _L.reconnect_tries += 1
            if _L.reconnect_tries > 3:
                _L.reconnect_at = None
                bui.screenmessage('Auto-reconnect gave up', color=(1, 0.4, 0.4))
                return
            bui.screenmessage(f'Reconnecting ({_L.reconnect_tries}/3) ...',
                              color=(0.5, 1, 0.7))
            _L.reconnect_at = now + 10.0
            join_server(_L.target[0], _L.target[1])
    except Exception:
        _print_exception('tracker tick failed')


def _ping_monitor() -> None:
    while True:
        try:
            t = _L.target
            if t is not None and _L.connected:
                ms = _ping_once(t[0], t[1], tries=2, timeout=0.8)
                _L.ping_ms = ms
                _L.ping_hist.append(ms if ms is not None else 999.0)
            time.sleep(1.2)
        except Exception:
            time.sleep(2.0)


def _migrate_history() -> None:
    cfg = babase.app.config
    try:
        if _CFG_HISTORY in cfg:
            return
        for key in list(cfg.keys()):
            val = cfg.get(key)
            if (key != _CFG_HISTORY and str(key).endswith('_ServerHistory')
                    and isinstance(val, dict) and val
                    and all(isinstance(e, dict) and 'addr' in e and 'port' in e
                            for e in val.values())):
                cfg[_CFG_HISTORY] = val
                cfg.commit()
                return
    except Exception:
        pass


def _install_hooks() -> None:
    global _orig_disconnect, _tracker_timer
    if _orig_disconnect is None:
        _orig_disconnect = bs.disconnect_from_host

        def _wrapped(*args, **kwargs):
            _L.user_left = True
            _L.reconnect_at = None
            return _orig_disconnect(*args, **kwargs)
        bs.disconnect_from_host = _wrapped
        threading.Thread(target=_ping_monitor, daemon=True).start()
    _tracker_timer = babase.AppTimer(1.0, _tracker_tick, repeat=True)


def join_server(addr, port) -> None:
    addr = str(addr).strip()
    port = int(port)

    def _go(ip: str) -> None:
        try:
            if bs.get_connection_to_host_info_2() is not None:
                _L.user_left = True
                bs.disconnect_from_host()
        except Exception:
            pass
        bs.connect_to_party(ip, port=port)

    if _is_ip_literal(addr):
        _go(addr)
        return

    def _work() -> None:
        try:
            res = socket.getaddrinfo(addr, port, 0, socket.SOCK_DGRAM)[0][4][0]
        except Exception:
            res = None

        def _done() -> None:
            if res is None:
                bui.screenmessage(
                    babase.Lstr(resource='internal.unableToResolveHostText'),
                    color=(1, 0, 0))
                bui.getsound('error').play()
            else:
                _go(res)
        bui.pushcall(_done, from_other_thread=True)
    threading.Thread(target=_work, daemon=True).start()


_UI_COLOR: List[Any] = [(0.16, 0.38, 0.92)]
_DISCORD_URL = 'https://discord.gg/V8KnB54fUF'
_CREDITS_BODY = (
    "As you can see, here we are, in a newer and a better version of "
    "PartyWindow. Let's just say it's the same as the regular one, but it "
    "looks way better, it has a lot of features and stuff, go check them out!")
_CREDITS_BY = 'Made by Nizar & Drap'


def _row_left(sx: float, sc: float, pad: float = 5.0) -> float:
    return -(sx * (1.0 - sc) / 2.0 + 9.0 - pad)


def _row_size(shift: float, sc: float) -> float:
    return 2.0 * shift / (1.0 - sc)


def _join_color(rgb):
    h, s, _v = colorsys.rgb_to_hsv(*rgb)
    return _hsv(h, 0.35 + s * 0.7, 1.0)


def _danger_color(rgb):
    h, s, _v = colorsys.rgb_to_hsv(*rgb)
    return _hsv(h, 0.3 + s * 0.5, 0.58)


def _dim(color, k: float = 0.5):
    return tuple(c * k for c in color[:3])


def _open_discord() -> None:
    try:
        bui.open_url(_DISCORD_URL)
        bui.screenmessage('Opening Discord ...', color=(0.55, 0.62, 1.0))
    except Exception:
        try:
            if bui.clipboard_is_supported():
                bui.clipboard_set_text(_DISCORD_URL)
        except Exception:
            pass
        bui.screenmessage('Discord link copied', color=(0.55, 0.62, 1.0))


def _options_items() -> Tuple[List[str], List[str]]:
    cfg = babase.app.config
    muted = cfg.resolve('Chat Muted')
    rc = cfg.get(_CFG_RECONNECT, False)
    al = cfg.get(_CFG_ALERTS, True)
    return (['mute', 'clear', 'reconnect', 'alerts', 'copyip', 'credits'],
            ['Unmute chat' if muted else 'Mute chat', 'Clear chat',
             f"Auto-reconnect: {'On' if rc else 'Off'}",
             f"Mention alerts: {'On' if al else 'Off'}", 'Copy IP:Port',
             'Credits'])


def _options_choice(choice: str, party: Any = None) -> None:
    cfg = babase.app.config
    if choice == 'mute':
        cfg['Chat Muted'] = not bool(cfg.resolve('Chat Muted'))
        cfg.apply_and_commit()
    elif choice == 'clear':
        if party is not None:
            party._clear_chat()
    elif choice == 'reconnect':
        cfg[_CFG_RECONNECT] = not cfg.get(_CFG_RECONNECT, False)
        cfg.commit()
        if not cfg[_CFG_RECONNECT]:
            _L.reconnect_at = None
        bui.screenmessage(
            f"Auto-reconnect: {'On' if cfg[_CFG_RECONNECT] else 'Off'}",
            color=(0.8, 0.9, 1))
    elif choice == 'alerts':
        cfg[_CFG_ALERTS] = not cfg.get(_CFG_ALERTS, True)
        cfg.commit()
        bui.screenmessage(
            f"Mention alerts: {'On' if cfg[_CFG_ALERTS] else 'Off'}",
            color=(0.8, 0.9, 1))
    elif choice == 'copyip':
        if _L.connected and _L.addr and bui.clipboard_is_supported():
            bui.clipboard_set_text(f'{_L.addr}:{_L.port}')
            bui.screenmessage(babase.Lstr(resource='copyConfirmText'),
                              color=(0, 1, 0))
        else:
            bui.screenmessage('Join a server first', color=(1, 1, 0))
            bui.getsound('error').play()
    elif choice == 'credits':
        _open_credits()


class _Overlay:

    def __init__(self, w: float, h: float, cards: List[Any]) -> None:
        ui = bui.app.ui_v1.uiscale
        scale = (1.7 if ui is bui.UIScale.SMALL else
                 1.3 if ui is bui.UIScale.MEDIUM else 1.0)
        self._root = bui.containerwidget(
            size=(w, h), transition='in_scale',
            parent=bui.get_special_widget('overlay_stack'),
            on_outside_click_call=self.close, scale=scale, background=False)
        self._cards: List[Tuple[_Card, str]] = [
            (_Card(self._root, 0, 0, w, h, 16, bw=2.0), 'body')]
        for x, y, cw, ch, r, kind in cards:
            self._cards.append((_Card(self._root, x, y, cw, ch, r), kind))
        self._pal = _palette(_UI_COLOR[0])
        self._btns: List[bui.Widget] = []
        self._texts: List[Tuple[bui.Widget, str]] = []
        self._paint()
        self._timer: Any = bui.AppTimer(
            0.25, bui.WeakCallStrict(self._tick), repeat=True)

    def _paint(self) -> None:
        kinds = _kind_colors(self._pal)
        for card, kind in self._cards:
            fill, edge = kinds[kind]
            card.recolor(edge, fill)

    def button(self, **kw) -> bui.Widget:
        b = bui.buttonwidget(
            parent=self._root, button_type='square', autoselect=True,
            color=self._pal['accent'], textcolor=self._pal['text'], **kw)
        self._btns.append(b)
        return b

    def text(self, role: str, **kw) -> bui.Widget:
        t = bui.textwidget(parent=self._root, color=self._pal[role], **kw)
        self._texts.append((t, role))
        return t

    def _tick(self) -> None:
        try:
            if not self._root.exists():
                self._timer = None
                return
            self._pal = pal = _palette(_UI_COLOR[0])
            self._paint()
            for b in self._btns:
                bui.buttonwidget(edit=b, color=pal['accent'],
                                 textcolor=pal['text'])
            for t, role in self._texts:
                bui.textwidget(edit=t, color=pal[role])
        except Exception:
            pass

    def close(self) -> None:
        try:
            if self._root and not self._root.transitioning_out:
                bui.containerwidget(edit=self._root, transition='out_scale')
        except Exception:
            pass


class _CreditsCard(_Overlay):
    def __init__(self) -> None:
        lines = textwrap.wrap(_CREDITS_BODY, 42)
        lh = 19.0
        W = 380.0
        content_h = 14 + len(lines) * lh + 14 + 28
        H = content_h + 128
        super().__init__(W, H, [
            (12, H - 58, W - 24, 46, 12, 'head'),
            (12, 62, W - 24, content_h, 12, 'card')])
        self.text('text', position=(W / 2, H - 35), size=(0, 0), scale=1.0,
                  text='Credits', h_align='center', v_align='center')
        top = 62 + content_h
        for i, line in enumerate(lines):
            self.text('text', position=(W / 2, top - 14 - lh * (i + 0.5)),
                      size=(0, 0), scale=0.62, text=line, maxwidth=W - 40,
                      h_align='center', v_align='center')
        self.text('light', position=(W / 2, 62 + 20), size=(0, 0), scale=0.85,
                  text=_CREDITS_BY, maxwidth=W - 40, h_align='center',
                  v_align='center')
        exit_btn = self.button(
            position=(W / 2 - 150, 14), size=(140, 40), label='Exit',
            on_activate_call=self.close)
        self.button(
            position=(W / 2 + 10, 14), size=(140, 40), label='Discord',
            icon=bui.gettexture('discordLogo'), iconscale=0.9,
            on_activate_call=_open_discord)
        bui.containerwidget(edit=self._root, cancel_button=exit_btn)


_credits_card: Any = None


def _open_credits() -> None:
    global _credits_card
    bui.getsound('swish').play()
    _credits_card = _CreditsCard()


class _EditDialog(_Overlay):
    def __init__(self, hub: Any, name: str, addr: str, port: int) -> None:
        self._hub_ref = weakref.ref(hub)
        W, H = 440.0, 316.0
        super().__init__(W, H, [(12, H - 58, W - 24, 46, 12, 'head')] + [
            (118, H - 118 - i * 54, W - 142, 38, 10, 'field')
            for i in range(3)])
        self.text('text', position=(W / 2, H - 35), size=(0, 0), scale=1.0,
                  text='Edit server', h_align='center', v_align='center')
        self._fields = []
        for i, (label, val, mc) in enumerate((
                ('Name', name, 60), ('Address', addr, 100),
                ('Port', str(port), 5))):
            y = H - 118 - i * 54
            self.text('light', position=(106, y + 19), size=(0, 0),
                      scale=0.7, text=label, h_align='right',
                      v_align='center')
            self._fields.append(bui.textwidget(
                parent=self._root, editable=True, size=(W - 156, 38),
                position=(124, y), text=val, max_chars=mc,
                description=label, autoselect=True, h_align='left',
                v_align='center', maxwidth=W - 164, color=(1, 1, 1)))
        cancel = self.button(position=(24, 14), size=(180, 40),
                             label=babase.Lstr(resource='cancelText'),
                             on_activate_call=self.close)
        self._save = self.button(position=(W - 204, 14), size=(180, 40),
                                 label='Save',
                                 on_activate_call=self._on_save)
        bui.widget(edit=cancel, right_widget=self._save)
        bui.widget(edit=self._save, left_widget=cancel)
        bui.containerwidget(edit=self._root, cancel_button=cancel,
                            start_button=self._save)

    def _on_save(self) -> None:
        hub = self._hub_ref()
        if hub is None:
            self.close()
            return
        try:
            name = (bui.textwidget(query=self._fields[0]) or '').strip()
            addr = (bui.textwidget(query=self._fields[1]) or '').strip()
            port = int(bui.textwidget(query=self._fields[2]))
            if not addr or port < 0 or port > 65535:
                raise ValueError
        except Exception:
            bui.screenmessage('Invalid address or port', color=(1, 0, 0))
            bui.getsound('error').play()
            return
        hub._apply_edit(name or addr, addr, port)
        self.close()


_HUB_SORTS = ['recent', 'name', 'joins', 'ping']
_HUB_SORT_NAMES = {'recent': 'Recent', 'name': 'A-Z',
                   'joins': 'Most joined', 'ping': 'Ping'}
_HUB_SHIFT = 100.0


class ServerHubWindow:

    def __init__(self, party: Any = None) -> None:
        cfg = babase.app.config
        ui = bui.app.ui_v1.uiscale
        self.W = 620
        self.H = (360 if ui is bui.UIScale.SMALL else
                  440 if ui is bui.UIScale.MEDIUM else 520)
        self._scale = (1.7 if ui is bui.UIScale.SMALL else
                       1.3 if ui is bui.UIScale.MEDIUM else 1.0)
        self._party_ref = weakref.ref(party) if party is not None else None
        self._restored = False
        tab = cfg.get(_CFG_HUB_TAB, 'history')
        self._tab = tab if tab in ('history', 'favorites') else 'history'
        sort = cfg.get(_CFG_HUB_SORT, 'recent')
        self._sort = sort if sort in _HUB_SORTS else 'recent'
        self._filter = ''
        self._selected: Optional[str] = None
        self._items: List[Dict[str, Any]] = []
        self._rows: Dict[str, Any] = {}
        self._shown: Dict[str, Any] = {}
        self._tick_n = 0
        self._dlg: Any = None
        self._edit_key = ''
        self._theme_name = cfg.get(_CFG_THEME, 'Aurora')
        self._theme = _get_theme(self._theme_name)
        self._speed = float(cfg.get(_CFG_SPEED, 1.0))
        level = cfg.get(_CFG_FX, 2)
        level = level if level in (0, 1, 2) else 2
        self._color = _theme_rgb(self._theme, time.time() - _FX_T0,
                                 self._speed)
        _UI_COLOR[0] = self._color
        w, h, P = self.W, self.H, 10
        hy = h - P - 54
        ty = hy - 6 - 32
        top = ty - 6
        info_h = 32
        list_y = P + info_h + 6
        list_h = top - list_y
        side_w = 168
        list_w = w - 2 * 18 - side_w - 8
        side_x = 18 + list_w + 8
        self._side = (side_x, list_y, side_w, list_h)

        self._root = bui.containerwidget(
            size=(w, h), transition='in_scale',
            parent=bui.get_special_widget('overlay_stack'),
            on_outside_click_call=self.close_with_sound,
            scale=self._scale, background=False,
            stack_offset=(0, -10) if ui is bui.UIScale.SMALL else (0, 0))
        party_obj = self._party_ref() if self._party_ref else None
        if party_obj is not None:
            try:
                party_obj._fx.set_level(0)
            except Exception:
                pass
        search_x = 366
        self._skin = _Skin(
            self._root, w, h, self._theme, level,
            [(P, hy, w - 2 * P, 54, 14, 'head'),
             (18, list_y, list_w, list_h, 12, 'card'),
             (side_x, list_y, side_w, list_h, 12, 'card'),
             (18, P, w - 36, info_h, 10, 'field'),
             (search_x, ty, w - 18 - search_x, 32, 8, 'field')])
        self._fx = self._skin.fx
        self._skin.recolor(self._color)
        pal = self._skin.pal

        self._cancel = bui.buttonwidget(
            parent=self._root, position=(P + 6, hy + 7), size=(40, 40),
            label=bui.charstr(bui.SpecialChar.CLOSE), button_type='square',
            autoselect=True, color=pal['accent'], textcolor=pal['text'],
            on_activate_call=self.close)
        bui.containerwidget(edit=self._root, cancel_button=self._cancel)
        self._title = bui.textwidget(
            parent=self._root, position=(w / 2, hy + 37), size=(0, 0),
            scale=0.95, text='Servers', maxwidth=300, h_align='center',
            v_align='center', color=pal['text'])
        self._subtitle = bui.textwidget(
            parent=self._root, position=(w / 2, hy + 15), size=(0, 0),
            scale=0.45, text='', h_align='center', v_align='center',
            color=(0.85, 0.93, 1.0), maxwidth=300)
        self._tab_hist = bui.buttonwidget(
            parent=self._root, position=(18, ty), size=(100, 32),
            label='History', button_type='square', autoselect=True,
            color=pal['accent'], textcolor=pal['text'],
            on_activate_call=bui.CallStrict(self._set_tab, 'history'))
        self._tab_fav = bui.buttonwidget(
            parent=self._root, position=(122, ty), size=(110, 32),
            label='Favorites', button_type='square', autoselect=True,
            color=pal['accent'], textcolor=pal['text'],
            on_activate_call=bui.CallStrict(self._set_tab, 'favorites'))
        self._sort_btn = bui.buttonwidget(
            parent=self._root, position=(236, ty), size=(124, 32),
            label='', button_type='square', autoselect=True,
            color=pal['accent'], textcolor=pal['text'], text_scale=0.8,
            on_activate_call=self._cycle_sort)
        self._search = bui.textwidget(
            parent=self._root, position=(search_x + 8, ty),
            size=(w - 18 - search_x - 16, 32), editable=True, text='',
            maxwidth=w - 18 - search_x - 24, max_chars=40,
            description='Search', h_align='left', v_align='center',
            autoselect=True, shadow=0.3, flatness=1.0, color=(1, 1, 1))
        self._search_hint = bui.textwidget(
            parent=self._root, position=(search_x + 12, ty + 16),
            size=(0, 0), text='search...', scale=0.7,
            color=(0.8, 0.9, 1.0, 0.55), h_align='left', v_align='center')

        self._list_w = list_w - 12
        self._sx_name = _row_size(_HUB_SHIFT, 0.85)
        self._sx_det = _row_size(_HUB_SHIFT, 0.55)
        self._scroll = bui.scrollwidget(
            parent=self._root, position=(24, list_y + 6),
            size=(list_w - 12, list_h - 12), color=(0.4, 0.6, 0.3),
            border_opacity=0.0)
        self._col = bui.columnwidget(
            parent=self._scroll, border=2,
            left_border=_row_left(self._sx_name, 0.85), margin=0)

        bx = side_x + 8
        bw = side_w - 16
        avail = list_h - 12
        join_h, gap = 34, 4
        bh = max(24, min(34, (avail - join_h - 5 * gap) / 5))
        y = list_y + list_h - 6 - join_h
        self._btn_join = bui.buttonwidget(
            parent=self._root, position=(bx, y), size=(bw, join_h),
            label='JOIN', button_type='square', autoselect=True,
            color=_join_color(self._color), textcolor=(1, 1, 1),
            text_scale=1.05, on_activate_call=self._join_selected)

        def side_btn(label, call, **kw):
            nonlocal y
            y -= gap + bh
            return bui.buttonwidget(
                parent=self._root, position=(bx, y), size=(bw, bh),
                label=label, button_type='square', autoselect=True,
                color=pal['accent'], textcolor=pal['text'], text_scale=0.85,
                on_activate_call=call, **kw)
        self._btn_fav = side_btn('Favorite', self._toggle_fav)
        self._btn_edit = side_btn('Edit name/ip/port', self._edit_selected)
        self._btn_copy = side_btn('Copy IP:Port', self._copy_selected)
        self._btn_ping = side_btn('Ping all', self._ping_all)
        self._btn_del = side_btn('Delete', self._delete_selected)
        bui.buttonwidget(edit=self._btn_del, color=_danger_color(self._color))
        self._info = bui.textwidget(
            parent=self._root, position=(w / 2, P + info_h / 2), size=(0, 0),
            scale=0.55, text='', h_align='center', v_align='center',
            maxwidth=w - 60, color=(0.9, 0.95, 1.0))
        self._accent_buttons = [
            self._cancel, self._tab_hist, self._tab_fav, self._sort_btn, self._btn_fav,
            self._btn_edit, self._btn_copy, self._btn_ping]

        self._refresh_tabs(pal)
        self._rebuild_list()
        self._timer: Any = bui.AppTimer(
            0.06, bui.WeakCallStrict(self._tick), repeat=True)

    def close(self) -> None:
        if not self._restored:
            self._restored = True
            party = self._party_ref() if self._party_ref else None
            if party is not None:
                try:
                    party._fx.set_level(party._fx_level)
                except Exception:
                    pass
        try:
            if self._root and not self._root.transitioning_out:
                bui.containerwidget(edit=self._root, transition='out_scale')
        except Exception:
            pass

    def close_with_sound(self) -> None:
        bui.getsound('swish').play()
        self.close()

    def _live_key(self) -> Optional[str]:
        try:
            if _L.connected and _L.addr:
                return _srv_key(_L.addr, _L.port)
        except Exception:
            pass
        return None

    def _load_items(self) -> List[Dict[str, Any]]:
        hist = _hist()
        favs = _saved_servers()
        fav_set = set()
        for v in favs.values():
            try:
                fav_set.add(_srv_key(v['addr'], v['port']))
            except Exception:
                pass
        items: List[Dict[str, Any]] = []
        if self._tab == 'history':
            for k, e in hist.items():
                try:
                    items.append(dict(
                        key=k, addr=str(e['addr']), port=int(e['port']),
                        name=str(e.get('name') or e['addr']),
                        count=int(e.get('count', 0)), last=float(e.get('last', 0)),
                        fav=_srv_key(e['addr'], e['port']) in fav_set))
                except Exception:
                    continue
        else:
            for k, v in favs.items():
                try:
                    pk = _srv_key(v['addr'], v['port'])
                    he = hist.get(pk) or {}
                    items.append(dict(
                        key=k, addr=str(v['addr']), port=int(v['port']),
                        name=str(v.get('name') or v['addr']),
                        count=int(he.get('count', 0)),
                        last=float(he.get('last', 0)), fav=True))
                except Exception:
                    continue
        for it in items:
            it['pkey'] = _srv_key(it['addr'], it['port'])
        q = self._filter.lower()
        if q:
            items = [i for i in items if q in i['name'].lower()
                     or q in i['addr'].lower() or q in str(i['port'])]
        if self._sort == 'name':
            items.sort(key=lambda i: i['name'].lower())
        elif self._sort == 'joins':
            items.sort(key=lambda i: -i['count'])
        elif self._sort == 'ping':
            def pk(i):
                c = _PING_CACHE.get(i['pkey'])
                return c['ms'] if c and c.get('ms') is not None else 1e9
            items.sort(key=pk)
        else:
            items.sort(key=lambda i: -i['last'])
        return items

    def _item(self, key: Optional[str]) -> Optional[Dict[str, Any]]:
        for it in self._items:
            if it['key'] == key:
                return it
        return None

    def _row_texts(self, it: Dict[str, Any]):
        sel = it['key'] == self._selected
        live = it['pkey'] == self._live_key()
        name = ('> ' if sel else '   ') + it['name'] + ('   [LIVE]' if live else '')
        ptxt, pcol = _ping_text(it['pkey'])
        bits = [f"{it['addr']}:{it['port']}"]
        if ptxt:
            bits.append(ptxt)
        if it['count']:
            bits.append(f"x{it['count']}")
        ago = _ago(it['last'])
        if ago:
            bits.append(ago)
        ncol = ((1, 1, 1) if sel else (0.5, 1.0, 0.7) if live
                else (1.0, 0.88, 0.4) if it['fav'] else (0.85, 0.92, 1.0))
        dcol = pcol if pcol else (0.7, 0.8, 0.9)
        return name, '   '.join(bits), ncol, dcol

    def _rebuild_list(self) -> None:
        for c in self._col.get_children():
            c.delete()
        self._rows = {}
        self._shown = {}
        self._items = self._load_items()
        if self._selected is None or self._item(self._selected) is None:
            self._selected = self._items[0]['key'] if self._items else None
        if not self._items:
            sx = _row_size(_HUB_SHIFT, 0.7)
            bui.textwidget(
                parent=self._col, size=(sx, 60), scale=0.7,
                text=('No servers match.' if self._filter else
                      'Nothing here yet. Join a server and it\nappears here automatically.'
                      if self._tab == 'history' else
                      'No favorites yet. Use the star button\nin the party window.'),
                h_align='left', v_align='center', color=(0.8, 0.9, 1.0))
        for idx, it in enumerate(self._items):
            name, det, ncol, dcol = self._row_texts(it)
            sel_call = bui.CallStrict(self._select, it['key'])
            act_call = bui.CallStrict(self._join_key, it['key'])
            n = bui.textwidget(
                parent=self._col, size=(self._sx_name, 22), text=name,
                scale=0.85, h_align='left', v_align='center', selectable=True,
                autoselect=True, color=ncol, maxwidth=self._list_w - 30,
                on_select_call=sel_call, on_activate_call=act_call)
            d = bui.textwidget(
                parent=self._col, size=(self._sx_det, 14), text=det,
                scale=0.55, h_align='left', v_align='center', color=dcol,
                maxwidth=self._list_w - 30, selectable=True,
                on_select_call=sel_call, on_activate_call=act_call)
            self._rows[it['key']] = (n, d)
            self._shown[it['key']] = (name, det)
            if idx < 12:
                _ping_async(it['addr'], it['port'])
        self._refresh_actions()

    def _refresh_rows(self) -> None:
        for it in self._items:
            r = self._rows.get(it['key'])
            if not r:
                continue
            name, det, ncol, dcol = self._row_texts(it)
            try:
                bui.textwidget(edit=r[0], text=name, color=ncol)
                if self._shown.get(it['key']) != (name, det):
                    bui.textwidget(edit=r[1], text=det, color=dcol)
                self._shown[it['key']] = (name, det)
            except Exception:
                pass

    def _select(self, key: str) -> None:
        if key != self._selected:
            self._selected = key
            self._refresh_rows()
            self._refresh_actions()

    def _select(self, key: str) -> None:
        if key != self._selected:
            self._selected = key
            self._refresh_rows()
            self._refresh_actions()

    def _refresh_actions(self) -> None:
        it = self._item(self._selected)
        try:
            bui.buttonwidget(edit=self._btn_fav,
                             label='Unfavorite' if (it and it['fav']) else 'Favorite')
            bui.buttonwidget(edit=self._sort_btn,
                             label='Sort: ' + _HUB_SORT_NAMES[self._sort])
            if it:
                ptxt, _pcol = _ping_text(it['pkey'])
                info = f"{it['name']}  -  {it['addr']}:{it['port']}"
                if it['count']:
                    info += f"  -  joined {it['count']}x"
                if it['last']:
                    info += f"  -  {_ago(it['last'])}"
                if ptxt:
                    info += f"  -  {ptxt}"
            else:
                info = 'Select a server'
            bui.textwidget(edit=self._info, text=info)
            bui.textwidget(
                edit=self._subtitle,
                text=f'{len(_hist())} in history   |   {len(_saved_servers())} favorites')
        except Exception:
            pass

    def _refresh_tabs(self, pal: Dict[str, Any]) -> None:
        on = pal['text']
        off = _dim(pal['text'], 0.5)
        bui.buttonwidget(edit=self._tab_hist,
                         textcolor=on if self._tab == 'history' else off)
        bui.buttonwidget(edit=self._tab_fav,
                         textcolor=on if self._tab == 'favorites' else off)

    def _apply_style(self, rgb, el: float) -> None:
        pal = self._skin.pal
        for b in self._accent_buttons:
            bui.buttonwidget(edit=b, color=pal['accent'], textcolor=pal['text'])
        bui.buttonwidget(edit=self._btn_join, color=_join_color(rgb),
                         textcolor=(1, 1, 1))
        bui.buttonwidget(edit=self._btn_del, color=_danger_color(rgb),
                         textcolor=pal['text'])
        self._refresh_tabs(pal)
        bui.textwidget(edit=self._title, color=_light(rgb, 0.3),
                       scale=0.95 + 0.03 * math.sin(el * 2.2))

    def _tick(self) -> None:
        try:
            if not self._root.exists():
                self._timer = None
                return
            elapsed = time.time() - _FX_T0
            rgb = _theme_rgb(self._theme, elapsed, self._speed)
            self._color = rgb
            _UI_COLOR[0] = rgb
            self._fx.tick(elapsed, rgb, self._speed)
            self._tick_n += 1
            if self._tick_n % 4 == 0:
                self._skin.recolor(rgb)
            if self._tick_n % 3 == 0:
                self._apply_style(rgb, elapsed)
            if self._tick_n % 8 == 0:
                q = (bui.textwidget(query=self._search) or '').strip()
                bui.textwidget(edit=self._search_hint,
                               text='' if q else 'search...')
                if q != self._filter:
                    self._filter = q
                    self._rebuild_list()
                else:
                    self._refresh_rows()
        except Exception:
            pass

    def _no_selection(self) -> None:
        bui.screenmessage('Select a server first', color=(1, 1, 0))
        bui.getsound('error').play()

    def _set_tab(self, tab: str) -> None:
        self._tab = tab
        babase.app.config[_CFG_HUB_TAB] = tab
        babase.app.config.commit()
        self._selected = None
        bui.getsound('click01').play()
        self._fx.pulse()
        self._refresh_tabs(self._skin.pal)
        self._rebuild_list()

    def _cycle_sort(self) -> None:
        self._sort = _HUB_SORTS[(_HUB_SORTS.index(self._sort) + 1) % len(_HUB_SORTS)]
        babase.app.config[_CFG_HUB_SORT] = self._sort
        babase.app.config.commit()
        bui.getsound('click01').play()
        self._rebuild_list()

    def _join_key(self, key: str) -> None:
        it = self._item(key)
        if it is None:
            return self._no_selection()
        bui.getsound('swish').play()
        bui.screenmessage(f"Joining {it['name']} ...", color=(0.5, 1, 0.7))
        join_server(it['addr'], it['port'])
        self.close()

    def _join_selected(self) -> None:
        self._join_key(self._selected)

    def _toggle_fav(self) -> None:
        it = self._item(self._selected)
        if it is None:
            return self._no_selection()
        if it['fav']:
            k = _find_favorite(it['addr'], it['port'])
            if k is not None:
                _saved_servers().pop(k, None)
                babase.app.config.commit()
            bui.getsound('shieldDown').play()
            bui.screenmessage(f"Removed from favorites: {it['name']}", color=(1, 0.8, 0.3))
        else:
            status, old = favorites_save(it['addr'], it['port'], it['name'])
            bui.getsound('gunCocking').play()
            self._fx.burst(self._side[0] + self._side[2] / 2, self._side[1] + self._side[3] / 2)
            bui.screenmessage(f"Saved to favorites: {it['name']}", color=(0, 1, 0))
        self._rebuild_list()

    def _copy_selected(self) -> None:
        it = self._item(self._selected)
        if it is None:
            return self._no_selection()
        if bui.clipboard_is_supported():
            bui.clipboard_set_text(f"{it['addr']}:{it['port']}")
            bui.screenmessage(babase.Lstr(resource='copyConfirmText'), color=(0, 1, 0))
        else:
            bui.screenmessage(f"{it['addr']}:{it['port']}", color=(0.8, 0.9, 1))

    def _ping_all(self) -> None:
        bui.getsound('click01').play()
        for it in self._items[:30]:
            _ping_async(it['addr'], it['port'], force=True)

    def _delete_selected(self) -> None:
        it = self._item(self._selected)
        if it is None:
            return self._no_selection()
        where = 'History' if self._tab == 'history' else 'Favorites'
        ConfirmWindow(
            babase.Lstr(value=f"Delete \"{it['name']}\" from {where}?"),
            bui.CallStrict(self._do_delete, it['key']), width=460, height=150)

    def _do_delete(self, key: str) -> None:
        store = _hist() if self._tab == 'history' else _saved_servers()
        store.pop(key, None)
        babase.app.config.commit()
        bui.getsound('shieldDown').play()
        self._selected = None
        self._rebuild_list()

    def _edit_selected(self) -> None:
        it = self._item(self._selected)
        if it is None:
            return self._no_selection()
        self._edit_key = it['key']
        self._dlg = _EditDialog(self, it['name'], it['addr'], it['port'])

    def _apply_edit(self, name: str, addr: str, port: int) -> None:
        old = self._edit_key
        newkey = _srv_key(addr, port)
        if self._tab == 'history':
            h = _hist()
            e = h.pop(old, None) or {}
            if newkey in h and newkey != old:
                t = h[newkey]
                t['name'] = name
                t['count'] = int(t.get('count', 0)) + int(e.get('count', 0))
                t['last'] = max(float(t.get('last', 0)), float(e.get('last', 0)))
            else:
                e.update(addr=addr, port=port, name=name)
                e.setdefault('count', 0)
                e.setdefault('first', time.time())
                e.setdefault('last', 0)
                h[newkey] = e
        else:
            s = _saved_servers()
            s.pop(old, None)
            s[newkey] = {'addr': addr, 'port': port, 'name': name}
        babase.app.config.commit()
        self._selected = newkey
        bui.getsound('gunCocking').play()
        self._rebuild_list()


_CHAT_LEFT = _row_left(900.0, 0.6)


class _PlayerCard:

    def __init__(self, party: 'BetterPartyWindow', ent: Dict[str, Any],
                 is_host: bool, anchor) -> None:
        self._party_ref = weakref.ref(party)
        self._last_col = party._color
        acc = str(ent.get('display_string') or '').strip()
        cid = ent.get('client_id')
        profs: List[str] = []
        for pl in (ent.get('players') or [])[:3]:
            nm = str(pl.get('name_full') or pl.get('name') or '').strip()
            if nm and nm not in profs:
                profs.append(nm)
        rows: List[Tuple[str, str]] = []
        if acc:
            rows.append(('ACCOUNT NAME', acc))
        rows += [('PROFILE NAME', p) for p in profs]
        if cid is not None:
            rows.append(('CLIENT ID', str(cid)))
        title = profs[0] if profs else (acc or 'Player')
        W = 380
        H = 70 + len(rows) * 42 + 58
        ui = bui.app.ui_v1.uiscale
        scale = (1.7 if ui is bui.UIScale.SMALL else
                 1.3 if ui is bui.UIScale.MEDIUM else 1.0)
        self._root = root = bui.containerwidget(
            size=(W, H), transition='in_scale',
            parent=bui.get_special_widget('overlay_stack'),
            on_outside_click_call=self.close, scale=scale, background=False)
        self._cards: List[Tuple[_Card, str]] = [
            (_Card(root, 0, 0, W, H, 16, bw=2.0), 'body'),
            (_Card(root, 12, H - 62, W - 24, 50, 12), 'head')]
        ys, y = [], H - 62 - 8 - 38
        for _r in rows:
            self._cards.append((_Card(root, 12, y, W - 24, 38, 10), 'card'))
            ys.append(y)
            y -= 42
        pal = _palette(party._color)
        self._paint(pal)

        self._btns: List[bui.Widget] = []
        close = bui.buttonwidget(
            parent=root, position=(18, H - 56), size=(38, 38),
            label=bui.charstr(bui.SpecialChar.CLOSE), button_type='square',
            autoselect=True, color=pal['accent'], textcolor=pal['text'], on_activate_call=self.close)
        bui.containerwidget(edit=root, cancel_button=close)
        self._btns.append(close)
        self._title = bui.textwidget(
            parent=root, position=(W / 2 + 14, H - 30), size=(0, 0),
            scale=0.9, text=bui.Lstr(value=title), maxwidth=W - 130,
            h_align='center', v_align='center', color=pal['text'])
        sub = 'host' if is_host else (f'client {cid}' if cid is not None else '')
        bui.textwidget(
            parent=root, position=(W / 2 + 14, H - 49), size=(0, 0),
            scale=0.45, text=f'tap Add to put a name in your message box   '
            f'{("(" + sub + ")") if sub else ""}', maxwidth=W - 130,
            h_align='center', v_align='center', color=(0.85, 0.93, 1.0))
        self._labels: List[bui.Widget] = []
        for (label, val), yy in zip(rows, ys):
            self._labels.append(bui.textwidget(
                parent=root, position=(22, yy + 29), size=(0, 0), scale=0.42,
                text=label, h_align='left', v_align='center',
                color=pal['light']))
            bui.textwidget(
                parent=root, position=(22, yy + 13), size=(0, 0), scale=0.8,
                text=bui.Lstr(value=val), h_align='left', v_align='center',
                maxwidth=200, color=(1, 1, 1))
            add = bui.buttonwidget(
                parent=root, position=(W - 12 - 8 - 58 * 2 - 6, yy + 4),
                size=(56, 30), label='Add', button_type='square',
                autoselect=True, color=pal['accent'], textcolor=pal['text'], text_scale=0.9,
                on_activate_call=bui.CallStrict(self._add, val))
            cp = bui.buttonwidget(
                parent=root, position=(W - 12 - 8 - 58, yy + 4),
                size=(56, 30), label='Copy', button_type='square',
                autoselect=True, color=pal['accent'], textcolor=pal['text'], text_scale=0.9,
                on_activate_call=bui.CallStrict(self._copy, val))
            self._btns += [add, cp]
        self._actions = bui.buttonwidget(
            parent=root, position=(20, 10), size=(160, 38),
            label='Kick / admin ...', button_type='square', autoselect=True,
            color=pal['accent'], textcolor=pal['text'], text_scale=0.9,
            on_activate_call=bui.CallStrict(
                self._open_actions, cid, is_host, title))
        done = bui.buttonwidget(
            parent=root, position=(W - 180, 10), size=(160, 38),
            label='Close', button_type='square', autoselect=True,
            color=pal['accent'], textcolor=pal['text'], text_scale=0.9, on_activate_call=self.close)
        self._btns += [self._actions, done]
        self._timer: Any = bui.AppTimer(
            0.25, bui.WeakCallStrict(self._tick), repeat=True)

    def _paint(self, pal) -> None:
        kinds = _kind_colors(pal)
        for card, kind in self._cards:
            fill, edge = kinds[kind]
            card.recolor(edge, fill)

    def _tick(self) -> None:
        try:
            if not self._root.exists():
                self._timer = None
                return
            party = self._party_ref()
            if party is not None:
                self._last_col = party._color
            pal = _palette(self._last_col)
            self._paint(pal)
            for b in self._btns:
                bui.buttonwidget(edit=b, color=pal['accent'], textcolor=pal['text'])
            bui.textwidget(edit=self._title, color=pal['text'])
            for lb in self._labels:
                bui.textwidget(edit=lb, color=pal['light'])
        except Exception:
            pass

    def _open_actions(self, cid, is_host: bool, name: str) -> None:
        party = self._party_ref()
        if party is not None:
            party._on_member_press(cid, is_host, self._actions, name)

    def _add(self, value: str) -> None:
        try:
            party = self._party_ref()
            if party is not None:
                party._append_to_field(value)
                party._fx.pulse()
        except Exception:
            pass
        bui.getsound('gunCocking').play()
        bui.screenmessage(f'Added to message: {value}', color=(0, 1, 0))
        self.close()

    def _copy(self, value: str) -> None:
        if bui.clipboard_is_supported():
            bui.clipboard_set_text(value)
            bui.screenmessage(babase.Lstr(resource='copyConfirmText'),
                              color=(0, 1, 0))

    def close(self) -> None:
        try:
            if self._root and not self._root.transitioning_out:
                bui.containerwidget(edit=self._root, transition='out_scale')
        except Exception:
            pass


class BetterPartyWindow(bui.Window):

    PAD = 10
    HEAD_H = 54
    FOOT_H = 50
    INFO_H = 18
    DOCK_W = 56
    ROSTER_W = 190

    def __init__(self, origin: Sequence[float] = (0, 0)) -> None:
        self._uiopenstate = bui.UIOpenState('classicparty')
        ui = bui.app.ui_v1.uiscale
        self._W = 620
        self._H = (360 if ui is bui.UIScale.SMALL else
                   440 if ui is bui.UIScale.MEDIUM else 520)
        scale = (1.7 if ui is bui.UIScale.SMALL else
                 1.3 if ui is bui.UIScale.MEDIUM else 1.0)

        cfg = babase.app.config
        self._theme_name = cfg.get(_CFG_THEME, 'Aurora')
        if self._theme_name not in THEMES and self._theme_name != 'Custom':
            self._theme_name = 'Aurora'
        self._theme = _get_theme(self._theme_name)
        lvl = cfg.get(_CFG_FX, 2)
        self._fx_level = lvl if lvl in (0, 1, 2) else 2
        self._speed = float(cfg.get(_CFG_SPEED, 1.0))
        self._auto = bool(cfg.get(_CFG_AUTO, False))
        self._auto_t = time.time()
        self._color = _theme_rgb(self._theme, time.time() - _FX_T0,
                                 self._speed)
        _UI_COLOR[0] = self._color
        self._bg_color_a = self._theme['a']
        self._bg_color_b = self._theme['b']
        self._blend_from: Any = None
        self._blend_t0 = 0.0
        self._n = 0
        self._popup_type: Optional[str] = None
        self._menu_popup: Optional[PopupMenuWindow] = None
        self._popup_cid: Optional[int] = None
        self._popup_is_host = False
        self._popup_name = ''
        self._pending_wave_pick: Optional[str] = None
        self._chat_rows: List[bui.Widget] = []
        self._chat_msgs: List[str] = []
        self._recall_i: Optional[int] = None
        self._recall_orig = ''
        self._hl: Optional[Tuple[bui.Widget, str]] = None
        self._roster: Any = None
        self._roster_widgets: List[bui.Widget] = []
        self._display_old = True
        self._was_connected = False
        self._was_muted = False
        self._last_title: Any = None
        self._toast: Optional[Tuple[str, Any, float]] = None
        self._my_name = ''
        try:
            self._my_name = (bui.app.plus.get_v1_account_name() or '').strip()
        except Exception:
            pass

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._W, self._H),
                transition='in_scale',
                parent=bui.get_special_widget('overlay_stack'),
                on_outside_click_call=self.close_with_sound,
                scale_origin_stack_offset=origin,
                scale=scale,
                stack_offset=((0, -10) if ui is bui.UIScale.SMALL else (0, 0)),
                darken_behind=True,
                background=False),
            prevent_main_window_auto_recreate=False)
        try:
            self._build()
        except Exception:
            try:
                bui.containerwidget(edit=self._root_widget, transition='out_scale')
            except Exception:
                pass
            raise

    def _build(self) -> None:
        W, H, P = self._W, self._H, self.PAD
        root = self._root_widget
        hy = H - P - self.HEAD_H
        cy0 = P + self.FOOT_H + self.INFO_H + 6
        cy1 = hy - 8
        ch = cy1 - cy0
        dock_x = P
        chat_x = P + self.DOCK_W + 8
        ros_x = W - P - self.ROSTER_W
        chat_w = ros_x - 8 - chat_x
        quick_w, send_w = 64, 70
        qx = P + 8
        sx = W - P - 8 - send_w
        aw = 30
        ax_up = qx + quick_w + 6
        ax_dn = ax_up + aw + 4
        fx_ = ax_dn + aw + 8
        fw = sx - 8 - fx_
        self._geo = dict(hy=hy, cy0=cy0, cy1=cy1, ch=ch, chat_x=chat_x,
                         chat_w=chat_w, ros_x=ros_x, sx=sx, send_w=send_w)

        bh, step = 34, 39
        dock_y = [cy1 - 5 - bh - i * step for i in range(5)]
        dbx = dock_x + 7
        menu_x = W - P - 6 - 40
        style_x = menu_x - 8 - 64
        halos = [(dbx + 21, dock_y[2] + 17, 64), (dbx + 21, dock_y[3] + 17, 64),
                 (sx + send_w / 2, P + 25, 92), (style_x + 32, hy + 27, 100)]

        self._skin = _Skin(
            root, W, H, self._theme, self._fx_level,
            [(P, hy, W - 2 * P, self.HEAD_H, 14, 'head'),
             (dock_x, cy0, self.DOCK_W, ch, 12, 'card'),
             (chat_x, cy0, chat_w, ch, 12, 'card'),
             (ros_x, cy0, self.ROSTER_W, ch, 12, 'card'),
             (P, P, W - 2 * P, self.FOOT_H, 14, 'head'),
             (fx_, P + 6, fw, self.FOOT_H - 12, 10, 'field')],
            halos=halos)
        self._fx = self._skin.fx
        self._skin.recolor(self._color)
        pal = self._skin.pal

        self._close_btn = bui.buttonwidget(
            parent=root, position=(P + 6, hy + 7), size=(40, 40),
            label=bui.charstr(bui.SpecialChar.CLOSE), button_type='square',
            autoselect=True, color=pal['accent'], textcolor=pal['text'], on_activate_call=self.close)
        bui.containerwidget(edit=root, cancel_button=self._close_btn)
        self._spark_x0 = P + 6 + 40 + 12
        self._spark_y0 = hy + 11
        self._spark = [bui.imagewidget(
            parent=root, position=(self._spark_x0 + i * 4.4, self._spark_y0),
            size=(3.2, 2), texture=bui.gettexture('white'),
            color=(0.5, 0.5, 0.5), opacity=0.0) for i in range(24)]
        self._title = bui.textwidget(
            parent=root, position=(W / 2, hy + 37), size=(0, 0), scale=0.95,
            text=bui.Lstr(resource='partyWindow.titleText'), maxwidth=230,
            h_align='center', v_align='center', color=pal['text'])
        self._sub = bui.textwidget(
            parent=root, position=(W / 2, hy + 15), size=(0, 0), scale=0.45,
            text='', maxwidth=300, h_align='center', v_align='center',
            color=(0.85, 0.93, 1.0))
        self._menu_btn = bui.buttonwidget(
            parent=root, position=(menu_x, hy + 7), size=(40, 40), label='...',
            button_type='square', autoselect=True, color=pal['accent'], textcolor=pal['text'],
            on_activate_call=self._on_menu_press)
        self._style_btn = bui.buttonwidget(
            parent=root, position=(style_x, hy + 9), size=(64, 36),
            label='Style', button_type='square', autoselect=True,
            color=pal['accent'], textcolor=pal['text'], text_scale=0.9,
            on_activate_call=self._on_style_press)

        def dock(i, **kw):
            return bui.buttonwidget(
                parent=root, position=(dbx, dock_y[i]), size=(42, bh),
                button_type='square', autoselect=True, color=pal['accent'], textcolor=pal['text'],
                **kw)
        self._ping_btn = dock(0, label='--', text_scale=0.95,
                              on_activate_call=self._share_ping)
        self._ip_btn = dock(1, label='IP', text_scale=1.05,
                            on_activate_call=self._share_ip)
        self._save_btn = dock(2, label='', icon=bui.gettexture('star'),
                              iconscale=1.0, on_activate_call=self._save_server)
        self._hub_btn = dock(3, label='', icon=bui.gettexture('logIcon'),
                             iconscale=1.0, on_activate_call=self._open_hub)
        self._cmd_btn = dock(4, label='/', text_scale=1.3,
                             on_activate_call=lambda: self._open_list('cmds'))

        self._chat_w = chat_w - 10
        self._scroll = bui.scrollwidget(
            parent=root, position=(chat_x + 5, cy0 + 5),
            size=(chat_w - 10, ch - 10), color=(0.4, 0.6, 0.3),
            border_opacity=0.0)
        self._col = bui.columnwidget(
            parent=self._scroll, border=2, left_border=_CHAT_LEFT, margin=0)
        self._muted_text = bui.textwidget(
            parent=root, position=(chat_x + chat_w / 2, cy0 + ch / 2),
            size=(0, 0), h_align='center', v_align='center',
            text=bui.Lstr(resource='chatMutedText'), color=(1, 1, 1, 0.0))

        self._ros_title = bui.textwidget(
            parent=root, position=(ros_x + self.ROSTER_W / 2, cy1 - 14),
            size=(0, 0), scale=0.6, text='PLAYERS', h_align='center',
            v_align='center', color=pal['light'])
        self._rscroll = bui.scrollwidget(
            parent=root, position=(ros_x + 5, cy0 + 5),
            size=(self.ROSTER_W - 10, ch - 32), color=(0.4, 0.6, 0.3),
            border_opacity=0.0)
        self._ros_sx = self.ROSTER_W - 34
        self._rcol = bui.columnwidget(
            parent=self._rscroll, border=2,
            left_border=_row_left(self._ros_sx, 0.62), margin=0)
        self._empty_ros = bui.textwidget(
            parent=root, position=(ros_x + self.ROSTER_W / 2, cy0 + ch / 2 - 10),
            size=(0, 0), scale=0.6, text='nobody here yet',
            h_align='center', v_align='center', color=(1, 1, 1, 0.45),
            maxwidth=self.ROSTER_W - 20)

        self._info = bui.textwidget(
            parent=root, position=(W / 2 - 170, P + self.FOOT_H + 2),
            size=(340, 16), scale=0.5, text='', h_align='center',
            v_align='center', maxwidth=330, color=(0.8, 0.9, 1.0),
            selectable=True, click_activate=True,
            on_activate_call=self._copy_ip)

        self._quick_btn = bui.buttonwidget(
            parent=root, position=(qx, P + 7), size=(quick_w, 36),
            label='Quick', button_type='square', autoselect=True,
            color=pal['accent'], textcolor=pal['text'], text_scale=0.9,
            on_activate_call=lambda: self._open_list('quick'))
        self._text_field = bui.textwidget(
            parent=root, position=(fx_ + 8, P + 6),
            size=((fw - 16) / 0.8, (self.FOOT_H - 12) / 0.8), editable=True,
            text='', maxwidth=(fw - 24) / 0.8, shadow=0.3, flatness=1.0,
            description=bui.Lstr(resource='partyWindow.chatMessageText'),
            autoselect=True, v_align='center', corner_scale=0.8)
        self._up_btn = bui.buttonwidget(
            parent=root, position=(ax_up, P + 7), size=(aw, 36),
            label=bui.charstr(bui.SpecialChar.UP_ARROW),
            button_type='square', autoselect=True, enable_sound=False,
            color=pal['accent'], textcolor=pal['text'],
            on_activate_call=bui.CallStrict(self._recall, True))
        self._down_btn = bui.buttonwidget(
            parent=root, position=(ax_dn, P + 7), size=(aw, 36),
            label=bui.charstr(bui.SpecialChar.DOWN_ARROW),
            button_type='square', autoselect=True, enable_sound=False,
            color=pal['accent'], textcolor=pal['text'],
            on_activate_call=bui.CallStrict(self._recall, False))
        self._send_btn = bui.buttonwidget(
            parent=root, position=(sx, P + 7), size=(send_w, 36),
            label=bui.Lstr(resource='partyWindow.sendText'),
            button_type='square', autoselect=True, color=pal['accent'], textcolor=pal['text'],
            on_activate_call=self._send_chat_message)
        try:
            bui.textwidget(edit=self._text_field,
                           on_submit_call=self._send_btn.activate)
        except Exception:
            bui.textwidget(edit=self._text_field,
                           on_return_press_call=self._send_btn.activate)
        bui.containerwidget(edit=root, selected_child=self._text_field)

        self._accent_btns = [
            self._close_btn, self._menu_btn, self._style_btn, self._ping_btn,
            self._ip_btn, self._save_btn, self._hub_btn, self._cmd_btn,
            self._quick_btn, self._send_btn, self._up_btn, self._down_btn]

        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCallStrict(self._update), repeat=True)
        self._fx_timer: Any = bui.AppTimer(
            0.05, bui.WeakCallStrict(self._tick), repeat=True)
        self._update()

    def _tick(self) -> None:
        try:
            if not self._root_widget.exists():
                self._fx_timer = None
                return
            el = time.time() - _FX_T0
            color = _theme_rgb(self._theme, el, self._speed)
            bf = self._blend_from
            if bf is not None:
                k = (time.time() - self._blend_t0) / 1.2
                if k >= 1.0:
                    self._blend_from = None
                else:
                    k = k * k * (3 - 2 * k)
                    color = tuple(bf[i] + (color[i] - bf[i]) * k
                                  for i in range(3))
            self._color = color
            _UI_COLOR[0] = color
            self._n += 1
            self._fx.tick(el, color, self._speed)
            if self._n % 4 == 0:
                self._skin.recolor(color)
            if self._n % 3 == 0:
                self._apply_accents(color, el)
            if self._auto and time.time() - self._auto_t > 25.0:
                self._auto_t = time.time()
                i = (THEME_ORDER.index(self._theme_name) + 1
                     if self._theme_name in THEME_ORDER else 0)
                self._apply_theme(THEME_ORDER[i % len(THEME_ORDER)],
                                  quiet=True)
        except Exception:
            pass

    def _apply_accents(self, rgb, el) -> None:
        pal = self._skin.pal
        acc = pal['accent']
        for b in self._accent_btns:
            try:
                if b is self._ping_btn:
                    bui.buttonwidget(edit=b, color=acc)
                else:
                    bui.buttonwidget(edit=b, color=acc, textcolor=pal['text'])
            except Exception:
                pass
        try:
            bui.textwidget(edit=self._title, color=_light(rgb, 0.3),
                           scale=0.95 + 0.03 * math.sin(el * 2.2))
            bui.textwidget(edit=self._ros_title, color=pal['light'])
        except Exception:
            pass

    def on_chat_message(self, msg: str) -> None:
        if babase.app.config.resolve('Chat Muted'):
            return
        self._add_msg(msg)
        try:
            self._fx.pulse(self._geo['chat_x'] + self._geo['chat_w'] / 2,
                           self._geo['cy0'] + self._geo['ch'] / 2)
            me = self._my_name.lower()
            if (babase.app.config.get(_CFG_ALERTS, True) and me
                    and not msg.lower().startswith(me + ':')
                    and me in msg.split(':', 1)[-1].lower()):
                bui.getsound('ding').play()
                self._fx.burst(self._geo['chat_x'] + 60, self._geo['cy1'] - 20)
                self._set_toast('someone mentioned you', (1.0, 0.85, 0.3))
        except Exception:
            pass

    def _msg_color(self, msg: str):
        low = msg.lower()
        me = self._my_name.lower()
        if 'joined ip' in low or low.startswith(' joined'):
            return (0.62, 0.75, 0.9)
        if me and low.startswith(me + ':'):
            return (0.65, 1.0, 0.75)
        if me and me in msg.split(':', 1)[-1].lower():
            return (1.0, 0.86, 0.35)
        return (0.94, 0.96, 1.0)

    def _add_msg(self, msg: str) -> None:
        txt = bui.textwidget(
            parent=self._col, h_align='left', v_align='center', scale=0.6,
            size=(900, 15), text=msg, autoselect=True,
            maxwidth=self._chat_w * 0.94, shadow=0.3, flatness=1.0,
            color=self._msg_color(msg), selectable=True,
            on_activate_call=bui.CallStrict(self._copy_msg, msg))
        self._chat_rows.append(txt)
        self._chat_msgs.append(msg)
        while len(self._chat_rows) > 60:
            old = self._chat_rows.pop(0)
            self._chat_msgs.pop(0)
            if self._hl is not None and self._hl[0] is old:
                self._hl = None
            old.delete()
        bui.containerwidget(edit=self._col, visible_child=txt)

    def _copy_msg(self, msg: str) -> None:
        if bui.clipboard_is_supported():
            content = msg.split(':', 1)[1].strip() if ':' in msg else msg
            bui.clipboard_set_text(content)
            bui.screenmessage(babase.Lstr(resource='copyConfirmText'),
                              color=(0, 1, 0))

    def _clear_chat(self) -> None:
        self._hl = None
        self._chat_msgs = []
        while self._chat_rows:
            self._chat_rows.pop().delete()

    def _clear_highlight(self) -> None:
        if self._hl is not None:
            row, msg = self._hl
            self._hl = None
            try:
                bui.textwidget(edit=row, color=self._msg_color(msg))
            except Exception:
                pass

    def _highlight(self, idx: Optional[int], msgs: List[str]) -> None:
        self._clear_highlight()
        if idx is None:
            return
        r = idx - (len(msgs) - len(self._chat_msgs))
        if not (0 <= r < len(self._chat_rows)) or self._chat_msgs[r] != msgs[idx]:
            try:
                r = self._chat_msgs.index(msgs[idx])
            except ValueError:
                return
        row = self._chat_rows[r]
        bui.textwidget(edit=row, color=(0.3, 1.0, 0.5))
        self._hl = (row, msgs[idx])
        bui.containerwidget(edit=self._col, visible_child=row)

    def _recall(self, older: bool) -> None:
        msgs = bs.get_chat_messages()
        if not msgs:
            bui.screenmessage('Empty chat', color=(1, 1, 0))
            bui.getsound('block').play()
            self._recall_i = None
            return
        n = len(msgs)
        if self._recall_i is None:
            self._recall_orig = bui.textwidget(query=self._text_field) or ''
            self._recall_i = n
        i = self._recall_i + (-1 if older else 1)
        if i < 0:
            i = n
        elif i > n:
            i = 0
        self._recall_i = i
        if i == n:
            text = self._recall_orig
            self._highlight(None, msgs)
        else:
            text = msgs[i].split(': ', 1)[1] if ': ' in msgs[i] else msgs[i]
            self._highlight(i, msgs)
        bui.textwidget(edit=self._text_field, text=text)
        bui.getsound('deek').play()

    def _send_chat_message(self) -> None:
        text = (bui.textwidget(query=self._text_field) or '').strip()
        if not text:
            return
        try:
            self._fx.pulse(self._geo['sx'] + self._geo['send_w'] / 2, 30)
        except Exception:
            pass
        if text == '.ip':
            self._share_ip()
        elif text == '.ping':
            self._share_ping()
        elif text == '.save':
            self._save_server()
        else:
            bs.chatmessage(text)
        bui.textwidget(edit=self._text_field, text='')
        self._recall_i = None
        self._clear_highlight()

    def _share_ping(self) -> None:
        ms = _L.ping_ms
        if ms is None:
            bui.screenmessage('No ping yet', color=(1, 1, 0))
            bui.getsound('error').play()
            return
        bs.chatmessage(f'PING >>> ({round(ms)} ms)')

    def _share_ip(self) -> None:
        if not _L.connected:
            bui.screenmessage('Join a server first', color=(1, 1, 0))
            bui.getsound('error').play()
            return
        bs.chatmessage(f'IP {_L.addr} PORT {_L.port}')

    def _copy_ip(self) -> None:
        if _L.connected and bui.clipboard_is_supported():
            bui.clipboard_set_text(f'{_L.addr}:{_L.port}')
            bui.screenmessage(babase.Lstr(resource='copyConfirmText'),
                              color=(0, 1, 0))

    def _save_server(self) -> None:
        if not _L.connected or not _L.addr:
            bui.screenmessage('Join a server first', color=(1, 1, 0))
            bui.getsound('error').play()
            return
        name = _L.name or _L.addr
        try:
            status, old = favorites_save(_L.addr, _L.port, name)
        except Exception:
            _print_exception('favorites_save failed')
            bui.getsound('error').play()
            return
        history_record(_L.addr, _L.port, name, joined=False)
        sc = (self._geo_center(2))
        try:
            self._fx.pulse(*sc)
            if status != 'exists':
                self._fx.burst(*sc)
        except Exception:
            pass
        if status == 'added':
            bui.getsound('gunCocking').play()
            bui.screenmessage(f'Saved: {name}  ({_L.addr}:{_L.port})',
                              color=(0, 1, 0))
        elif status == 'renamed':
            bui.getsound('ding').play()
            bui.screenmessage(f'Renamed favorite: {old} -> {name}',
                              color=(0.4, 0.9, 1))
        else:
            bui.getsound('click01').play()
            bui.screenmessage(f'Already in favorites: {name}',
                              color=(1, 1, 0.4))

    def _geo_center(self, i: int):
        g = self._geo
        return (self.PAD + 7 + 21, g['cy1'] - 5 - 34 - i * 39 + 17)

    def _open_hub(self) -> None:
        bui.getsound('swish').play()
        self._hub = ServerHubWindow(self)

    def _popup(self, kind: str, widget, choices: List[str],
               display: List[str], current: str) -> None:
        self._popup_type = kind
        self._menu_popup = PopupMenuWindow(
            position=widget.get_screen_space_center(), scale=_popup_scale(),
            choices=choices, choices_display=_creat_Lstr_list(display),
            current_choice=current, delegate=self)

    def popup_menu_closing(self, _popup_window) -> None:
        self._menu_popup = None

    def popup_menu_selected_choice(self, popup_window, choice: str) -> None:
        del popup_window
        t = self._popup_type
        try:
            if t == 'member':
                self._member_choice(choice)
            elif t == 'menu':
                self._menu_choice(choice)
            elif t in ('style', 'theme'):
                self._style_choice(choice)
            elif t in ('quick', 'cmds'):
                self._list_choice(t, choice)
            elif t in ('quick_rm', 'cmds_rm'):
                self._list_remove_choice(t, choice)
        except Exception:
            _print_exception('popup choice failed')

    def _on_menu_press(self) -> None:
        choices, display = _options_items()
        self._popup('menu', self._menu_btn, choices, display, 'alerts')

    def _menu_choice(self, choice: str) -> None:
        _options_choice(choice, self)
        if choice == 'mute':
            self._update()

    def _on_member_press(self, cid, is_host: bool, widget, name: str) -> None:
        self._popup_cid = cid
        self._popup_is_host = is_host
        self._popup_name = name
        host_session = bs.get_foreground_host_session() is not None
        info = bs.get_connection_to_host_info_2()
        choices, disp = [], []
        if host_session or (info is not None and info.build_number >= 14248):
            choices.append('kick')
            disp.append('Kick' if host_session else 'Kick vote')
        for cmd in ('kick', 'ban', 'ipban', 'mute', 'kill'):
            choices.append('c_' + cmd)
            disp.append(f'Chat: /{cmd}')
        choices.append('copy')
        disp.append('Copy name')
        self._popup('member', widget, choices, disp, choices[0])

    def _member_choice(self, choice: str) -> None:
        cid = self._popup_cid
        if choice == 'kick':
            if self._popup_is_host:
                bui.getsound('error').play()
                bui.screenmessage(
                    babase.Lstr(resource='internal.cantKickHostError'),
                    color=(1, 0, 0))
            elif cid is not None:
                if not bs.disconnect_client(cid, ban_time=5 * 60):
                    bui.getsound('error').play()
                    bui.screenmessage(
                        babase.Lstr(resource='getTicketsWindow.unavailableText'),
                        color=(1, 0, 0))
        elif choice.startswith('c_') and cid is not None:
            bs.chatmessage(f'/{choice[2:]} {cid}')
        elif choice == 'copy' and bui.clipboard_is_supported():
            bui.clipboard_set_text(self._popup_name)
            bui.screenmessage(babase.Lstr(resource='copyConfirmText'),
                              color=(0, 1, 0))

    @staticmethod
    def _roster_name(entry: Dict[str, Any]) -> str:
        try:
            pl = entry['players']
            if pl:
                if len(pl) == 1:
                    return pl[0]['name_full']
                s = '/'.join(e['name'] for e in pl)
                return s[:25] + '...' if len(s) > 25 else s
            return entry['display_string']
        except Exception:
            return '???'

    def _rebuild_roster(self) -> None:
        for wd in self._roster_widgets:
            wd.delete()
        self._roster_widgets = []
        roster = self._roster or []
        bui.textwidget(edit=self._ros_title,
                       text=f'PLAYERS  ({len(roster)})' if roster else 'PLAYERS')
        bui.textwidget(edit=self._empty_ros,
                       color=(1, 1, 1, 0.0 if roster else 0.45))
        me = self._my_name.lower()
        for i, ent in enumerate(roster):
            name = self._roster_name(ent)
            cid = ent.get('client_id')
            is_host = (cid == -1) if cid is not None else (i == 0)
            col = ((0.5, 1.0, 0.6) if is_host else
                   (1.0, 0.86, 0.35) if me and me in name.lower() else
                   (0.94, 0.96, 1.0))
            row = bui.textwidget(
                parent=self._rcol, size=(self._ros_sx, 21), scale=0.62,
                maxwidth=self._ros_sx - 10,
                text=bui.Lstr(value=name),
                h_align='left', v_align='center', selectable=True,
                autoselect=True, click_activate=True, color=col)
            bui.textwidget(edit=row, on_activate_call=bui.CallStrict(
                self._open_player_card, ent, is_host, row))
            self._roster_widgets.append(row)

    def _append_to_field(self, text: str) -> None:
        cur = bui.textwidget(query=self._text_field) or ''
        sep = '' if (not cur or cur.endswith(' ')) else ' '
        bui.textwidget(edit=self._text_field, text=cur + sep + text)
        try:
            bui.containerwidget(edit=self._root_widget,
                                selected_child=self._text_field)
        except Exception:
            pass

    def _open_player_card(self, ent: Dict[str, Any], is_host: bool,
                          anchor) -> None:
        bui.getsound('swish').play()
        self._card = _PlayerCard(self, ent, is_host, anchor)

    def _set_toast(self, text: str, color, secs: float = 4.0) -> None:
        self._toast = (text, color, time.time() + secs)

    def _list_items(self, kind: str) -> List[str]:
        key = _CFG_QUICK if kind == 'quick' else _CFG_CMDS
        default = _DEFAULT_QUICK if kind == 'quick' else _DEFAULT_CMDS
        items = babase.app.config.get(key)
        if not isinstance(items, list):
            items = list(default)
            babase.app.config[key] = items
        return [str(x) for x in items]

    def _open_list(self, kind: str) -> None:
        items = self._list_items(kind)
        widget = self._quick_btn if kind == 'quick' else self._cmd_btn
        self._popup(
            kind, widget,
            [f'i{k}' for k in range(len(items))] + ['add', 'remove'],
            items + ['+ Add text-box content', '- Remove one...'],
            'add')

    def _list_choice(self, kind: str, choice: str) -> None:
        key = _CFG_QUICK if kind == 'quick' else _CFG_CMDS
        items = self._list_items(kind)
        if choice == 'add':
            text = (bui.textwidget(query=self._text_field) or '').strip()
            if not text:
                bui.screenmessage('Type something in the box first',
                                  color=(1, 1, 0))
                bui.getsound('error').play()
                return
            if text not in items:
                items.append(text)
                babase.app.config[key] = items
                babase.app.config.commit()
            bui.getsound('gunCocking').play()
            bui.screenmessage(f'Added: {text}', color=(0, 1, 0))
        elif choice == 'remove':
            if not items:
                return
            widget = self._quick_btn if kind == 'quick' else self._cmd_btn
            self._popup(kind + '_rm', widget,
                        [f'r{k}' for k in range(len(items))], items, 'r0')
        elif choice.startswith('i'):
            try:
                bs.chatmessage(items[int(choice[1:])])
            except Exception:
                pass

    def _list_remove_choice(self, ptype: str, choice: str) -> None:
        kind = ptype[:-3]
        key = _CFG_QUICK if kind == 'quick' else _CFG_CMDS
        items = self._list_items(kind)
        try:
            gone = items.pop(int(choice[1:]))
        except Exception:
            return
        babase.app.config[key] = items
        babase.app.config.commit()
        bui.getsound('shieldDown').play()
        bui.screenmessage(f'Removed: {gone}', color=(1, 0.8, 0.3))

    def _on_style_press(self) -> None:
        sp = self._speed
        sname = (_SPEED_NAMES[_SPEED_VALUES.index(sp)]
                 if sp in _SPEED_VALUES else 'Normal')
        self._popup(
            'style', self._style_btn,
            ['themes', 'custom', 'random', 'auto', 'fx', 'speed'],
            [f'Themes  ({self._theme_name})', 'Custom colors', 'Random theme',
             f"Auto theme: {'On' if self._auto else 'Off'}",
             f'Effects: {_FX_LEVEL_NAMES[self._fx_level]}',
             f'Speed: {sname}'], 'themes')

    def _style_choice(self, choice: str) -> None:
        cfg = babase.app.config
        if self._popup_type == 'theme':
            if choice == 'Custom':
                self._on_color_picker_press()
            else:
                self._apply_theme(choice)
            return
        if choice == 'themes':
            names = THEME_ORDER + ['Custom']
            self._popup('theme', self._style_btn, names, names,
                        self._theme_name if self._theme_name in names
                        else 'Aurora')
        elif choice == 'custom':
            self._on_color_picker_press()
        elif choice == 'random':
            self._apply_theme(random.choice(THEME_ORDER))
        elif choice == 'auto':
            self._auto = not self._auto
            self._auto_t = time.time()
            cfg[_CFG_AUTO] = self._auto
            cfg.commit()
            bui.screenmessage(f"Auto theme: {'On' if self._auto else 'Off'}",
                              color=(0.8, 0.9, 1))
        elif choice == 'fx':
            self._fx_level = (self._fx_level + 1) % 3
            cfg[_CFG_FX] = self._fx_level
            cfg.commit()
            self._fx.set_level(self._fx_level)
            bui.screenmessage(f'Effects: {_FX_LEVEL_NAMES[self._fx_level]}',
                              color=(0.8, 0.9, 1))
        elif choice == 'speed':
            i = ((_SPEED_VALUES.index(self._speed) + 1) % 3
                 if self._speed in _SPEED_VALUES else 1)
            self._speed = _SPEED_VALUES[i]
            cfg[_CFG_SPEED] = self._speed
            cfg.commit()
            bui.screenmessage(f'Animation speed: {_SPEED_NAMES[i]}',
                              color=(0.8, 0.9, 1))

    def _apply_theme(self, name: str, quiet: bool = False) -> None:
        cfg = babase.app.config
        self._blend_from = self._color
        self._blend_t0 = time.time()
        self._theme_name = name
        self._theme = _get_theme(name)
        self._bg_color_a = self._theme['a']
        self._bg_color_b = self._theme['b']
        cfg[_CFG_THEME] = name
        cfg.commit()
        self._fx.set_theme(self._theme)
        self._fx.pulse()
        if not quiet:
            self._fx.burst()
            bui.getsound('ding').play()
            bui.screenmessage(f'Theme: {name}', color=_accent(self._color))

    def _on_color_picker_press(self) -> None:
        self._pending_wave_pick = 'wave1'
        ColorPickerExact(parent=self.get_root_widget(),
                         position=self.get_root_widget().get_screen_space_center(),
                         initial_color=self._bg_color_a, delegate=self,
                         tag='wave1')

    def color_picker_closing(self, picker) -> None:
        babase.app.config.commit()

    def color_picker_selected_color(self, picker, color) -> None:
        try:
            tag = picker.get_tag()
        except Exception:
            tag = self._pending_wave_pick
        if tag == 'wave1':
            self._bg_color_a = color
            self._pending_wave_pick = 'wave2'
            ColorPickerExact(parent=self.get_root_widget(),
                             position=self.get_root_widget().get_screen_space_center(),
                             initial_color=self._bg_color_b, delegate=self,
                             tag='wave2')
            return
        if tag == 'wave2':
            self._bg_color_b = color
            self._pending_wave_pick = None
            cfg = babase.app.config
            cfg['PartyWindow_Wave_Colors'] = [list(self._bg_color_a),
                                              list(self._bg_color_b)]
            cfg[_CFG_THEME] = 'Custom'
            cfg.commit()
            self._blend_from = self._color
            self._blend_t0 = time.time()
            self._theme_name = 'Custom'
            self._theme = _get_theme('Custom')
            self._fx.set_theme(self._theme)

    def _update(self) -> None:
        cfg = babase.app.config
        now = time.time()
        try:
            muted = cfg.resolve('Chat Muted')
            if muted != self._was_muted:
                self._was_muted = muted
                if not muted:
                    self._display_old = True
            bui.textwidget(edit=self._muted_text,
                           color=(1, 1, 1, 0.35 if muted else 0.0))
            if muted:
                self._clear_chat()
            elif self._display_old:
                for msg in bs.get_chat_messages():
                    self._add_msg(msg)
                self._display_old = False
        except Exception:
            pass

        info = bs.get_connection_to_host_info_2()
        connected = info is not None
        try:
            if connected != self._was_connected:
                self._was_connected = connected
                if connected:
                    self._fx.pulse()
                    self._fx.burst()
            title = (info.name if (info is not None and info.name)
                     else None)
            if title != self._last_title:
                self._last_title = title
                bui.textwidget(
                    edit=self._title,
                    text=(babase.Lstr(value=title) if title else
                          babase.Lstr(resource='partyWindow.titleText')))
        except Exception:
            pass

        try:
            roster = bs.get_game_roster()
            if roster != self._roster:
                old = self._roster
                self._roster = roster
                self._rebuild_roster()
                if old is not None:
                    a = {self._roster_name(e) for e in old}
                    b = {self._roster_name(e) for e in roster}
                    for n in sorted(b - a)[:2]:
                        self._set_toast(f'+ {n} joined', (0.5, 1.0, 0.6))
                        self._fx.pulse()
                    for n in sorted(a - b)[:2]:
                        self._set_toast(f'- {n} left', (1.0, 0.6, 0.5))
        except Exception:
            pass

        try:
            n_players = len(self._roster or [])
            ms = _L.ping_ms
            if self._toast is not None and now < self._toast[2]:
                bui.textwidget(edit=self._sub, text=self._toast[0],
                               color=self._toast[1])
            else:
                self._toast = None
                if connected and _L.session_start:
                    sub = (f'online {_fmt_dur(now - _L.session_start)}   |   '
                           f'{n_players} players')
                    if ms is not None:
                        sub += f'   |   {int(ms)} ms'
                elif connected:
                    sub = 'connecting...'
                elif bs.get_foreground_host_session() is not None:
                    sub = f'hosting   |   {n_players} players'
                else:
                    sub = 'not connected'
                bui.textwidget(edit=self._sub, text=sub,
                               color=(0.85, 0.93, 1.0))
            bui.textwidget(
                edit=self._info,
                text=(f'IP {_L.addr}    PORT {_L.port}    (tap to copy)'
                      if connected and _L.addr else
                      'no server address (not connected)'))
            if ms is not None:
                bui.buttonwidget(edit=self._ping_btn, label=f'{int(ms)}',
                                 textcolor=_get_ping_color(ms))
            else:
                bui.buttonwidget(edit=self._ping_btn, label='--',
                                 textcolor=(0.8, 0.8, 0.8))
            hist = list(_L.ping_hist)
            hist = [None] * (24 - len(hist)) + hist
            for bar, val in zip(self._spark, hist):
                if val is None:
                    bui.imagewidget(edit=bar, opacity=0.0)
                    continue
                hgt = 3 + min(1.0, val / 300.0) * 27
                bui.imagewidget(
                    edit=bar, size=(3.2, hgt), opacity=0.9,
                    color=_get_ping_color(val) if val < 999 else (1, 0.2, 0.2))
        except Exception:
            pass

    def close(self) -> None:
        if self._menu_popup is not None:
            try:
                self._menu_popup.on_popup_cancel()
            except Exception:
                pass
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(edit=self._root_widget, transition='out_scale')

    def close_with_sound(self) -> None:
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.getsound('swish').play()
        self.close()


_ORIG_PARTY_WINDOW = bui_party.PartyWindow


def _party_window_factory(origin: Sequence[float] = (0, 0)):
    try:
        return BetterPartyWindow(origin=origin)
    except Exception:
        _print_exception('BetterPartyWindow failed; using the stock window')
        return _ORIG_PARTY_WINDOW(origin=origin)


# ba_meta export babase.Plugin
class BetterPartyPlugin(babase.Plugin):

    def on_app_running(self) -> None:
        pass

    def __init__(self) -> None:
        super().__init__()
        _migrate_history()
        bui_party.PartyWindow = _party_window_factory
        _install_hooks()
