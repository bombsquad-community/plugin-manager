# Copyright 2026 - Solely by BrotherBoard
# Feel free to use this anywhere
# Bug? Feedback? Discord >> @BrotherBoard

"""
Checkboom v1.0.0 - Boom goes the king

Simple turn-based game I made because bored.
Experimental. Adds a Team game.
"""

import bauiv1 as bui
import bascenev1 as bs
from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.actor.text import Text
from collections import defaultdict, deque
from weakref import ref, WeakValueDictionary
from math import degrees, atan2, exp, cos, sin
from bascenev1lib.gameutils import SharedObjects
from random import choice, choices, random, uniform
from bascenev1lib.actor.powerupbox import PowerupBox, PowerupBoxFactory

__version__ = '1.0.0'

plugman = dict(
    plugin_name="checkboom",
    description=(
        "Simple turn-based game"
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

DEBUG = False


class Strings:
    CHECKBOOM = 'Checkboom'
    DESCRIPTION = f'A turn-based game.\nVersion {__version__}'
    INSTANCE_DESCRIPTION_SHORT = f'Kill their king, guard yours. v{__version__}'
    CONTROL = 'Control'
    RELEASE = 'Release'
    MOVE = 'Move'
    SELECT = 'Select'
    GO = 'Go'
    PUNCH = 'Punch'
    SPECIAL = 'Special'
    WAITING_FOR_PLAYERS = 'Waiting for players'
    PLACE_PIECES = 'Place your pieces'
    STAND_IN_POSITION = 'Stand in position'
    STARTING_IN = 'Starting in'
    CHECK = 'CHECK'
    BOOM = 'BOOM'
    SUBTITLES = [
        "That's how it's done",
        "Watch and learn",
        "Think three moves ahead",
        "Outplay. Outsmart. Outboom.",
        "Make every move count",
        "Get Checkboomed",
        "No mercy on the board",
        "Let the board burn",
        "That's what I was told",
        "Spaz sees mate in one",
        "What about it?",
        "Rest in pieces",
        "Your move. Not for long",
        "Pawns are people too",
        "Sacrifice is a strategy",
        "The king has left the building",
        "En passant? En passe-boom",
        "Long live the king. Not you",
        "Every square is a fuse",
        "Checkmate is for amateurs",
        "Bring your own bomb squad",
        "Blink and you're a crater",
        "Strategy meets detonation",
        "May the best bomber win",
        "Mind the blast radius",
        "Light the fuse, lose the king",
        "Fear the rook",
        "Knights fall, boards burn",
        "Zero chill, all thrill",
        "Boards are made to be broken",
        "Play dirty, play smart",
        "A calculated catastrophe",
        "It was always going to explode",
        "Trust no square",
        "Mate? More like blast",
        "Handle with care. Or don't",
        "Fortune favors the boldest bomb",
        "Chess, but louder",
        "Tick tick, your turn",
        "Winners walk away. Losers fly"
    ]
    HEALTH = 'HP'
    ATTACK = 'Attack'
    SPECIAL_POWER = 'Special'
    TEAM_TURN = "${TEAM}'s turn"
    TEAM_WINS = '${TEAM} wins!'
    CONTINUE = 'Press ${B}PUNCH to continue'
    PROCEEDING = 'Proceeding...'


class Checkboard(bs.Map):
    name = 'Checkboard'
    defs = type('', (), {
        'points': {
            'spawn1': (0, 0, 5, 0, 0, 5),
            'spawn2': (0, 0, -5, 0, 0, -5),
        },
        'boxes': {
            'area_of_interest_bounds': (0, 0, 0, 0, 0, 0, 10, 10, 10),
            'map_bounds': (0, 0, 0, 0, 0, 0, 200, 200, 200),
        }
    })

    @classmethod
    def get_preview_texture_name(cls):
        return 'checkboom'

    def __init__(self):
        super().__init__()
        shared = SharedObjects.get()

        floor_material = bs.Material()
        floor_material.add_actions(
            conditions=('they_are_older_than', -1),
            actions=(
                ('modify_part_collision', 'physical', True),
                ('modify_part_collision', 'collide', True),
            )
        )

        self.node = bs.newnode(
            'region',
            attrs={
                'position': (0, -0.001, 0),
                'type': 'box',
                'scale': (20, 0.001, 20),
                'materials': [floor_material, shared.footing_material]
            }
        )

        self.tiles = []
        self.fills = {}
        self.inner_fills = {}
        tile_size = 1.0
        board_dim = 8
        offset = (board_dim * tile_size) / 2 - (tile_size / 2)
        for row in range(board_dim):
            for col in range(board_dim):
                x = col * tile_size - offset
                z = row * tile_size - offset
                tile = bs.newnode(
                    'locator',
                    attrs={
                        'position': (x, 0, z),
                        'size': (tile_size, 0.01, tile_size),
                        'color': (1, 1, 1),
                        'shape': 'box',
                        'opacity': 1.0
                    }
                )
                self.tiles.append(tile)
                fill = bs.newnode(
                    'locator',
                    attrs={
                        'shape': 'circle',
                        'position': (x, 0.005, z),
                        'size': (tile_size * 0.9,),
                        'color': (1, 1, 1),
                        'opacity': 0.0,
                        'additive': True,
                        'draw_beauty': True
                    }
                )
                self.fills[(round(x, 1), round(z, 1))] = fill
                inner_fill = bs.newnode(
                    'locator',
                    attrs={
                        'shape': 'circleOutline',
                        'position': (x, 0.006, z),
                        'size': (0.57,),
                        'color': (1, 1, 1),
                        'opacity': 0.0,
                        'additive': True,
                        'draw_beauty': True
                    }
                )
                self.inner_fills[(round(x, 1), round(z, 1))] = inner_fill


def loop_array(node, attr, size, keys):
    combine = bs.newnode('combine', owner=node, attrs={'size': size})
    items = sorted(keys.items())
    gnode = bs.getactivity().globalsnode
    out = [combine]
    for i in range(size):
        curve = bs.newnode('animcurve', owner=node)
        gnode.connectattr('time', curve, 'in')
        curve.times = [int(1000 * t) for t, _ in items]
        curve.values = [v[i] for _, v in items]
        curve.offset = int(bs.time() * 1000.0)
        curve.loop = True
        curve.connectattr('out', combine, 'input' + str(i))
        out.append(curve)
    combine.connectattr('output', node, attr)
    return out


def kill_anims(nodes):
    for n in nodes or ():
        try:
            n and n.exists() and n.delete()
        except Exception:
            pass


def pfx(a, dmg, d, dead=False):
    pos = a.node.position
    d = d or (0.0, 1.0, 0.0)
    h = dmg * 0.003
    bs.getsound(choice(('punchStrong01', 'punchStrong02'))).play(1.0, position=pos)
    if dmg >= 400:
        bs.getsound('superPunch').play(1.0, position=pos)
    if dmg >= 350:
        bs.show_damage_count('-' + str(int(dmg / 10)) + '%', pos, d)
    bs.emitfx(position=pos, velocity=(d[0] * 0.5, d[1] * 0.5, d[2] * 0.5),
              count=min(20, 3 + int(dmg * 0.01)), scale=0.4, spread=0.05)
    bs.emitfx(position=pos, chunk_type='sweat', velocity=(
        d[0] * 1.3, d[1] * 1.3 + 5.0, d[2] * 1.3), count=min(40, 3 + int(dmg * 0.06)), scale=1.0, spread=0.3)
    if dmg >= 250:
        bs.emitfx(position=pos, chunk_type='spark', velocity=(0.0, 3.0, 0.0),
                  count=min(40, int(dmg * 0.08)), scale=0.6, spread=0.5)
    c = (1.0, 0.8, 0.4)
    light = bs.newnode('light', attrs={'position': pos, 'radius': 0.15 + h * 0.2,
                       'intensity': 0.5 * (1.0 + h), 'height_attenuated': False, 'color': c})
    flash = bs.newnode('flash', attrs={'position': pos, 'size': 0.3 + 0.36 * h, 'color': c})
    bs.timer(0.08 + h * 0.05, light.delete)
    bs.timer(0.08 + h * 0.05, flash.delete)
    if dmg >= 300:
        boom = bs.newnode('explosion', attrs={'position': pos, 'velocity': (
            0.0, 0.0, 0.0), 'radius': 0.3 + dmg * 0.001, 'big': False})
        bs.timer(0.5, boom.delete)


def fl(n, c, hi=2.0, lo=1.0):
    cb = bs.newnode('combine', owner=n, attrs={'input3': 1.0, 'size': 4})
    for i in range(3):
        bs.animate(cb, f'input{i}', {0: c[i] * hi, 0.3: c[i] * lo, 0.6: c[i] * hi}, loop=True)
    cb.connectattr('output', n, 'color')


def readable(c, lo=0.45):
    # lighten
    c = tuple(max(0.0, min(1.0, float(v))) for v in c[:3])
    def lum(x): return 0.2126 * x[0] + 0.7152 * x[1] + 0.0722 * x[2]
    if lum(c) >= lo:
        return c
    k = 0.0
    while k < 1.0 and lum(tuple(v + (1 - v) * k for v in c)) < lo:
        k += 0.05
    return tuple(v + (1 - v) * k for v in c)


def glv(a, msg):
    if not a.node or getattr(a, 'is_dead', False):
        return
    a.gl = True
    a.node.boxing_gloves = True
    a._flash_billboard(PowerupBoxFactory.get().tex_punch)
    if msg.sourcenode:
        msg.sourcenode.handlemessage(bs.PowerupAcceptMessage())


def cap_players(session):
    # backup
    if not hasattr(session, '_cb_mp'):
        session._cb_mp = session.max_players
    session.max_players = 2


def uncap_players(session):
    if hasattr(session, '_cb_mp'):
        session.max_players = session._cb_mp
        del session._cb_mp


class Piece(Spaz):
    def __init__(self, *args, game=None, team_id=None, character='Spaz', **kwargs):
        super().__init__(*args, character=character, **kwargs)
        self._game = ref(game) if game else None
        self._src_plr = None
        self.team_id = team_id
        self.character = character
        self.can_take_damage = False
        self.claimed_by = None
        self.is_master = False
        self.is_dead = False
        self.zoe_looking_at_master = False

    @property
    def game(self):
        return self._game() if self._game else None

    @property
    def source_player(self):
        return self._src_plr() if self._src_plr else None

    @source_player.setter
    def source_player(self, val):
        self._src_plr = ref(val) if val else None

    def handlemessage(self, msg):
        if isinstance(msg, bs.PowerupMessage) and msg.poweruptype == 'punch':
            glv(self, msg)
            return True
        if isinstance(msg, bs.HitMessage):
            if getattr(msg, 'is_backend', False):
                dmg = getattr(msg, 'custom_damage', 180)
                self.hitpoints = max(0, self.hitpoints - dmg)
                if self.node:
                    self.node.hurt = 1.0 - float(self.hitpoints) / self.hitpoints_max
                    self.node.handlemessage('flash')
                if self.node and msg.hit_type != 'explosion':
                    pfx(self, dmg, msg.force_direction, self.hitpoints <= 0)
                else:
                    bs.getsound('punch01').play(position=self.node.position if self.node else None)
                if self.hitpoints <= 0:
                    self.handlemessage(bs.DieMessage())
                return
            puncher = msg.get_source_player(bs.Player)
            if (
                msg.hit_type == 'punch'
                and puncher is not None
                and puncher.team.id == self.team_id
                and self.game
            ):
                self.game.claim_spaz(puncher, self)
            return
        elif isinstance(msg, bs.PickedUpMessage):
            if msg.node and self.game and any(p.actor and p.actor.node == msg.node and p.team.id != self.team_id for p in self.game.memory['players'].values()):
                msg.node.hold_node = None
        elif isinstance(msg, bs.OutOfBoundsMessage):
            # prestart
            if self.game and not self.game.memory.get('started'):
                self.game.respawn_spaz(self)
                return
        elif isinstance(msg, bs.DieMessage):
            if self.game:
                self.game.stop_run(self)
                if not msg.immediate:
                    self.game.retire_dead_spaz(self)
                    return
        super().handlemessage(msg)


class Floater(bs.Actor):
    def __init__(self, game, pos, col, instant=False):
        super().__init__()
        self.gm, self.col = ref(game), col
        s = self.s = uniform(0.2, 0.5)
        mx = max(col) or 1.0
        nc = [(x / mx) ** 2.5 for x in col]
        gain = 1.5 * 11 ** random()  # logarithmic
        rs = [x * gain for x in nc]
        self.life = uniform(20, 40)
        self.t0 = bs.time()
        self.g = 0.0
        self.up = random() < 0.5
        self.dying = False
        self.li = 0.9 + 0.2 * gain
        self.node = bs.newnode('prop', delegate=self, attrs={
            'body': 'box', 'position': pos, 'mesh': bs.getmesh('box'),
            'color_texture': bs.gettexture('black'), 'body_scale': s, 'mesh_scale': s,
            'gravity_scale': 0.0, 'damping': 0.004, 'max_speed': 1.2,
            'reflection': 'soft', 'reflection_scale': rs,
            'shadow_size': 0.0, 'materials': [game.fmat]
        })
        # glow
        self.light = bs.newnode('light', owner=self.node, attrs={
            'color': nc, 'radius': (0.18 + 0.5 * s) * 1.3 * 0.2, 'intensity': self.li if instant else 0.0, 'height_attenuated': False
        })
        self.node.connectattr('position', self.light, 'position')
        if not instant:
            bs.animate(self.node, 'mesh_scale', {0: 0, 0.4: s})
            bs.animate(self.light, 'intensity', {0: 0, 0.4: self.li})
        _s = ref(self)
        rot = game.rotating
        self.timers = [
            bs.Timer(uniform(4, 8), lambda: _s() and _s().gtick(), repeat=True),
            bs.Timer(uniform(1.0, 2.5) if rot else uniform(3, 6),
                     lambda: _s() and _s().push(), repeat=True),
            bs.Timer(0.25, lambda: _s() and _s().chk(), repeat=True),
            bs.Timer(self.life, lambda: _s() and _s().fade())
        ]
        self.push()

    def gtick(self):
        if not self.node:
            return
        y = self.node.position[1]
        # flip
        self.up = not self.up
        if y > 7.0:
            self.up = False
        if y < 1.0:
            self.up = True
        g = uniform(0.004, 0.012) * (-1 if self.up else 1)
        bs.animate(self.node, 'gravity_scale', {0: self.g, uniform(3.0, 6.0): g})
        self.g = g

    def push(self):
        if not self.node:
            return
        g = self.gm()
        rot = g and g.rotating
        p = self.node.position
        a = uniform(0, 6.2832)
        d = [cos(a), uniform(-0.3, 0.3), sin(a)]
        # shy
        if abs(p[0]) < 5.0 and abs(p[2]) < 5.0:
            d[0] += p[0] * 0.03
            d[2] += p[2] * 0.03
        # steer
        if not rot and p[2] > 0 and abs(p[0]) < 0.81 * p[2] + 1.0:
            d[2] -= 1
            d[0] += 0.5 if p[0] >= 0 else -0.5
        n = (d[0] ** 2 + d[1] ** 2 + d[2] ** 2) ** 0.5 or 1.0
        m = uniform(20, 50) * (self.s / 0.35) ** 3 * (2.2 if rot else 1.0)
        self.node.handlemessage('impulse', p[0], p[1], p[2], 0,
                                0, 0, m, 0, 0, 0, d[0] / n, d[1] / n, d[2] / n)

    def chk(self):
        if not self.node:
            return
        x, y, z = self.node.position
        g = self.gm()
        if g and g.rotating:
            if y < -1.0 or y > 16.0 or abs(x) > 33.0 or abs(z) > 33.0 or (abs(x) < 3.95 and abs(z) < 3.95):
                self.fade()
            return
        if y < -1.0 or y > 14.0 or abs(x) > 21.0 or z < -25.0 or (abs(x) < 3.95 and abs(z) < 3.95) or z > 25.0 or (z > 0 and abs(x) < 0.81 * z - 0.5):
            self.fade()

    def fade(self):
        if self.dying or not self.node:
            return
        self.dying = True
        bs.animate(self.node, 'mesh_scale', {0: self.s, 0.4: 0})
        bs.animate(self.light, 'intensity', {0: self.li, 0.4: 0})
        _n = self.node
        bs.timer(0.45, lambda: _n.delete() if _n else None)

    def handlemessage(self, msg):
        if isinstance(msg, bs.OutOfBoundsMessage):
            # recreate
            g = self.gm()
            self.timers = []
            self.node and self.node.delete()
            g and g.mkfloater()
        elif isinstance(msg, bs.DieMessage):
            self.fade()
        else:
            super().handlemessage(msg)

# ba_meta export bascenev1.GameActivity


class Checkboom(bs.TeamGameActivity[bs.Player, bs.Team]):
    name = Strings.CHECKBOOM
    description = Strings.DESCRIPTION

    @classmethod
    def supports_session_type(cls, type):
        return True

    @classmethod
    def get_available_settings(cls, sessiontype):
        return [
            bs.BoolSetting('Fancy Graphics', default=True),
            bs.IntChoiceSetting('Turn Time', choices=[
                                ('None', 0), ('15 Seconds', 15), ('30 Seconds', 30), ('60 Seconds', 60)], default=0),
            bs.BoolSetting('Powerups', default=True),
            bs.BoolSetting('Pre-Placed Pieces', default=False),
        ]

    def get_supported_maps(self):
        return ['Checkboard']

    def get_instance_description_short(self):
        return Strings.INSTANCE_DESCRIPTION_SHORT

    def _show_info(self) -> None:
        pass

    def _show_tip(self) -> None:
        pass

    @property
    def playing(self):
        return self.memory.get('playing', False)

    @playing.setter
    def playing(self, val):
        self.memory['playing'] = val

    @property
    def selector_pos(self):
        if self.current_turn_team_id is not None:
            return self.team_selector_pos.get(self.current_turn_team_id)
        return None

    @selector_pos.setter
    def selector_pos(self, val):
        if self.current_turn_team_id is not None:
            self.team_selector_pos[self.current_turn_team_id] = val

    @property
    def selector(self):
        if self.current_turn_team_id is not None:
            return self.team_selectors.get(self.current_turn_team_id)
        return None

    def __init__(self, settings):
        super().__init__(settings)
        self.default_music = bs.MusicType.GRAND_ROMP
        self.fancy = bool(settings.get('Fancy Graphics', True))
        self.turn_time = int(settings.get('Turn Time', 0))
        self.powerups = bool(settings.get('Powerups', True))
        self.autoplace = bool(settings.get('Pre-Placed Pieces', False))
        self.memory = defaultdict(dict)
        self.memory['players'] = WeakValueDictionary()
        self.memory['control'] = WeakValueDictionary()
        self.memory['placeholder_masters'] = {}
        self.memory['graveyard'] = defaultdict(list)
        self.memory['cooldowns'] = {}
        self.playing = False
        self.fmat = bs.Material()
        self.fmat.add_actions(conditions=('they_dont_have_material', self.fmat),
                              actions=('modify_part_collision', 'collide', False))
        self.memory['floaters'] = []
        self.st = self.new_st()
        self.turn_t0 = None
        self.memory['win_2d'] = []

        # selectors
        self.team_selectors = {}
        self.team_selector_pos = {}
        self.team_selector_anim = {}
        self.team_selector_blink = {}

        self.current_turn_team_id = None
        self.turn_active = False
        self.game_over = False
        self.rotating = False
        self.move_state = {'x_held': 0, 'z_held': 0}
        self.pending_action = None

        self.selected_spaz = None
        self.valid_move_tiles = []
        self.valid_attack_tiles = []
        self.move_highlighted_tiles = []
        self.attack_highlighted_tiles = []
        self.glows = []
        self.attack_anims = []
        self.king_anims = {}
        self.char_overlay_nodes = []

        self.subtext = bs.newnode(
            'text',
            attrs={
                'v_attach': 'top',
                'h_align': 'center',
                'position': (0, -50)
            }
        )
        self.legend = []
        self.rel = []
        self.rel_op = 0.0
        for i, (tex, c, t) in enumerate((
            ('buttonPunch', (1, 1, 0.4), Strings.CONTROL),
            ('buttonBomb', (1, 0, 0), Strings.RELEASE),
        )):
            y = 40 - i * 50
            self.legend.append(bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture(tex),
                    'absolute_scale': True,
                    'attach': 'centerLeft',
                    'position': (30, y),
                    'scale': (50, 50),
                    'color': c,
                    'opacity': 0
                }
            ))
            self.legend.append(bs.newnode(
                'text',
                attrs={
                    'text': t,
                    'h_attach': 'left',
                    'v_attach': 'center',
                    'position': (60, y),
                    'v_align': 'center',
                    'color': c,
                    'opacity': 0
                }
            ))
            i and self.rel.extend(self.legend[-2:])

    def on_transition_in(self):
        super().on_transition_in()
        for attr in ('_standard_game_title', '_title_text', '_game_title_text', '_title'):
            if hasattr(self, attr):
                val = getattr(self, attr)
                if val:
                    if hasattr(val, 'node') and val.node:
                        val.node.delete()
                    elif hasattr(val, 'delete'):
                        val.delete()
                setattr(self, attr, None)

    def on_transition_out(self):
        super().on_transition_out()
        uncap_players(self.session)
        # fade
        for n in self.memory['win_2d']:
            if n and n.exists():
                bs.animate(n, 'opacity', {0.0: n.opacity, 0.5: 0.0})

    def on_begin(self):
        super().on_begin()
        cap_players(bs.getsession())
        _s = ref(self)
        self.memory['timers']['bounds'] = bs.Timer(
            0.1, lambda: _s() and _s().bounds_tick(), repeat=True)
        if self.fancy:
            self.memory['timers']['floaters'] = bs.Timer(
                0.3, lambda: _s() and _s().floaters_tick(), repeat=True)
            self.floaters_tick(True)
        self.sanity_tick()

    def init_stand(self, pos, rot):
        # offset
        return bs.StandMessage((pos[0], pos[1] - 0.2, pos[2]), rot)

    def alert(self, text, color=(1, 1, 1)):
        self.subtext.text = text
        self.subtext.color = color

    def playsnd(self, name, vol=1.0):
        return bs.newnode('sound', attrs={'sound': bs.getsound(name), 'volume': vol})

    def is_on_cooldown(self, spaz):
        return spaz in self.memory.get('cooldowns', {})

    def apply_cooldown(self, spaz, turns=2):
        if not spaz or not spaz.node:
            return
        tid = getattr(spaz, 'team_id', 0)
        if 'cooldowns' not in self.memory:
            self.memory['cooldowns'] = {}
        prev = self.memory['cooldowns'].get(spaz)
        if prev and prev.get('orig_color') is not None:
            orig_color, orig_hl = prev['orig_color'], prev['orig_highlight']
        else:
            orig_color, orig_hl = tuple(spaz.node.color), tuple(spaz.node.highlight)
        bs.animate_array(spaz.node, 'color', 3, {0.0: spaz.node.color, 0.2: (0.35, 0.35, 0.35)})
        bs.animate_array(spaz.node, 'highlight', 3, {
                         0.0: spaz.node.highlight, 0.2: (0.2, 0.2, 0.2)})
        self.memory['cooldowns'][spaz] = {
            'team_id': tid,
            'turns_left': turns,
            'orig_color': orig_color,
            'orig_highlight': orig_hl,
        }

    def restore_spaz_from_cooldown(self, spaz):
        cooldowns = self.memory.get('cooldowns', {})
        info = cooldowns.pop(spaz, None) or {}
        if spaz and spaz.node and spaz.is_alive() and not getattr(spaz, 'is_dead', False):
            if getattr(spaz, 'is_master', False):
                tid = getattr(spaz, 'team_id', 0)
                col = self.get_team_color(tid)
                oc = info.get('orig_color') or (1.0, 1.0, 1.0)
                oh = info.get('orig_highlight') or col
                bs.animate_array(spaz.node, 'color', 3, {0.0: spaz.node.color, 0.3: oc})
                bs.animate_array(spaz.node, 'highlight', 3, {0.0: spaz.node.highlight, 0.3: oh})
            else:
                self.recolor(spaz, occupied=True)
            bs.getsound('dingSmall').play(position=spaz.node.position)
            spaz.node.handlemessage('flash')

    def on_team_turn_end(self, finished_team_id):
        cooldowns = self.memory.get('cooldowns', {})
        to_restore = []
        for spaz, info in list(cooldowns.items()):
            if info.get('team_id') == finished_team_id:
                info['turns_left'] -= 1
                if info['turns_left'] <= 0:
                    to_restore.append(spaz)
        for spaz in to_restore:
            self.restore_spaz_from_cooldown(spaz)

    def check_held_nodes(self):
        if not self.playing or not self.memory.get('started'):
            return
        pa = self.pending_action
        kronk_holding = None
        if pa and pa.get('type') == 'special' and pa.get('state') == 'holding':
            kronk_holding = pa.get('spaz')

        for p in self.memory['players'].values():
            if p.actor and p.actor.node and p.actor.node.hold_node:
                if p.actor is not kronk_holding:
                    p.actor.node.hold_node = None

        for m in self.memory['placeholder_masters'].values():
            if m and m.node and m.node.hold_node:
                if m is not kronk_holding:
                    m.node.hold_node = None

        for team in self.memory['spazzes'].values():
            for b in team:
                if b and b.node and b.node.hold_node:
                    if b is not kronk_holding:
                        b.node.hold_node = None

    def start_pulse(self, spaz):
        if not spaz or not spaz.node:
            return
        pid = id(spaz)
        run_val = [0]
        _s, _b = ref(self), ref(spaz)

        def pulse_tick():
            s, b = _s(), _b()
            if not s or not b or not b.node or not b.is_alive() or getattr(b, 'is_dead', False):
                if s:
                    s.memory['timers'][f'run_pulse_{pid}'] = None
                return
            if s.is_on_cooldown(b):
                b.on_run(0)
                return
            run_val[0] = 1 - run_val[0]
            b.on_run(run_val[0])
        pulse_tick()
        self.memory['timers'][f'run_pulse_{pid}'] = bs.Timer(0.2, pulse_tick, repeat=True)

    def start_run(self, piece):
        if not piece or not piece.node:
            return
        pid = id(piece)
        _s, _b = ref(self), ref(piece)

        def run_tick():
            s, b = _s(), _b()
            if not s or not b or not b.node or not b.is_alive() or b.claimed_by is not None:
                if s and b:
                    s.stop_run(b)
                return

            sq = s.memory['squares'].get(b)
            if sq:
                px, _, pz = b.node.position
                dist = ((sq[0] - px) ** 2 + (sq[1] - pz) ** 2) ** 0.5
                if dist <= 2.0:
                    b.on_run(0)
                    return

            b.on_run(0)
            s.memory['timers'][f'run_pulse_old_{pid}'] = bs.Timer(
                0.01, lambda: b.node and b.on_run(1)
            )

        run_tick()
        self.memory['timers'][f'run_{pid}'] = bs.Timer(0.1, run_tick, repeat=True)

    def stop_run(self, piece):
        if not piece:
            return
        pid = id(piece)
        self.memory['timers'][f'run_{pid}'] = None
        self.memory['timers'][f'run_pulse_old_{pid}'] = None
        self.memory['timers'][f'run_pulse_{pid}'] = None
        if piece.node:
            piece.on_run(0)

    def assign_controls(self, player, target):
        player.resetinput()
        for name, handler in (
            ('UP_DOWN', target.on_move_up_down),
            ('LEFT_RIGHT', target.on_move_left_right),
            ('RUN', target.on_run),
            ('JUMP_PRESS', target.on_jump_press),
            ('JUMP_RELEASE', target.on_jump_release),
            ('PUNCH_PRESS', target.on_punch_press),
            ('PUNCH_RELEASE', target.on_punch_release),
            ('PICK_UP_PRESS', target.on_pickup_press),
            ('PICK_UP_RELEASE', target.on_pickup_release),
        ):
            player.assigninput(getattr(bs.InputType, name), handler)

        _s, _p, _t = ref(self), ref(player), ref(target)
        if isinstance(target, Piece):
            player.assigninput(bs.InputType.BOMB_PRESS, lambda: (
                _s() and _p() and _t()) and _s().release_control(_p(), _t()))
            player.assigninput(bs.InputType.BOMB_RELEASE, lambda: None)
        else:
            player.assigninput(bs.InputType.BOMB_PRESS, lambda: None)
            player.assigninput(bs.InputType.BOMB_RELEASE, lambda: None)

    def on_player_join(self, player):
        super().on_player_join(player)
        actor = player.actor
        actor.team_id = player.team.id
        actor.is_master = True
        actor.is_dead = False
        if DEBUG:
            actor.hitpoints = actor.hitpoints_max = 50
        actor.orig_pos = self.map.defs.points[f'spawn{player.team.id+1}'][:3]
        actor.orig_rot = 0 if player.team.id else 180
        _s, _a = ref(self), ref(actor)
        actor.handlemessage = lambda msg: _s() and _a() and _s().handlemessage(_a(), msg)
        self.memory['team_colors'][player.team.id] = getattr(player.team, 'color', actor.node.color)
        old_pick = actor.on_pickup_press
        _p = ref(player)

        def safe_pick():
            old_pick()

            def chk():
                s, a, p = _s(), _a(), _p()
                if not s or not a or not p or not a.node or not a.node.hold_node:
                    return
                for tid, bots in s.memory['spazzes'].items():
                    if tid != p.team.id and any(b and b.node == a.node.hold_node for b in bots):
                        a.node.hold_node = None
            if s := _s():
                s.memory['timers'][f'pick1_{id(actor)}'] = bs.Timer(0.01, chk)
                s.memory['timers'][f'pick2_{id(actor)}'] = bs.Timer(0.05, chk)
        actor.on_pickup_press = safe_pick
        actor.handlemessage(self.init_stand(actor.orig_pos, actor.orig_rot))
        self.assign_controls(player, actor)
        self.memory['players'][player.team.id] = player
        self.sanity_tick()

    def on_player_leave(self, player):
        if target := self.memory['control'].get(player.team.id):
            self.release_control(player, target)
        if player.actor:
            self.memory['timers'][f'retain_{id(player.actor)}'] = None
            self.memory['timers'][f'run_pulse_{id(player.actor)}'] = None
            if player.actor.node:
                player.actor.node.delete()
            player.actor = None
        super().on_player_leave(player)
        self.memory['players'].pop(player.team.id, None)
        if self.memory.get('started'):
            # forfeit
            lt = player.team.id
            self.game_over or self.mdead(None, lt=lt)
            self.remove_team(lt)  # cleanup
            return
        self.stop_countdown()
        self.remove_team(player.team.id)
        self.sanity_tick()

    def handlemessage(self, actor, msg):
        if not actor or not actor.node:
            return
        # prestart
        if isinstance(msg, bs.OutOfBoundsMessage) and not self.memory.get('started'):
            return self.respawn_spaz(actor)
        if isinstance(msg, bs.PowerupMessage) and msg.poweruptype == 'punch':
            glv(actor, msg)
            return True
        if isinstance(msg, bs.HitMessage):
            if getattr(msg, 'is_backend', False):
                dmg = getattr(msg, 'custom_damage', 180)
                actor.hitpoints = max(0, actor.hitpoints - dmg)
                actor.node.hurt = 1.0 - float(actor.hitpoints) / actor.hitpoints_max
                actor.node.handlemessage('flash')
                if msg.hit_type != 'explosion':
                    pfx(actor, dmg, msg.force_direction, actor.hitpoints <= 0)
                else:
                    bs.getsound('punch01').play(position=actor.node.position)
                if actor.hitpoints <= 0:
                    actor.handlemessage(bs.DieMessage())
                return
            return
        if isinstance(msg, bs.DieMessage):
            if not msg.immediate:
                self.retire_dead_spaz(actor)
                return
        return type(actor).handlemessage(actor, msg)

    def retire_dead_spaz(self, spaz):
        if not spaz or not spaz.node:
            return
        pid = id(spaz)
        self.memory['timers'][f'retain_{pid}'] = None
        self.memory['timers'][f'run_pulse_{pid}'] = None
        was, spaz.is_dead = getattr(spaz, 'is_dead', False), True
        (was or self.game_over) or self.tally(spaz)
        spaz.node.hold_node = None

        if spaz in self.memory.get('cooldowns', {}):
            del self.memory['cooldowns'][spaz]

        old_sq = self.memory['squares'].pop(spaz, None)
        if old_sq:
            self.highlight_tile(old_sq, active=False)
        if getattr(spaz, 'is_master', False):
            ksq = self.memory['kings'].get(getattr(spaz, 'team_id', None))
            if ksq:
                self.set_master_tile(ksq, (1, 1, 1), active=False)
            # master
            self.mdead(spaz)
            return

        ds = getattr(spaz.node, 'death_sounds', None)
        if ds:
            choice(ds).play(position=spaz.node.position)

        team_id = getattr(spaz, 'team_id', 0)
        opp_tid = 1 if team_id == 0 else 0
        opp_z = self.map.defs.points[f'spawn{opp_tid+1}'][2]
        side = 1 if opp_z > 0 else -1
        deck_z = side * 4.0 + (opp_z - side * 4.0) * 2

        gy = self.memory['graveyard'][opp_tid]
        idx = len(gy)
        gy.append(spaz)

        gx = -3.2 + (idx % 6) * 1.25
        gz = deck_z + (0.5 if (idx // 6) else -0.5)

        spaz.handlemessage(bs.StandMessage((gx, 0.0, gz), 0 if opp_tid == 0 else 180))
        spaz.node.color = (0.35, 0.35, 0.35)
        spaz.node.highlight = (0.2, 0.2, 0.2)
        spaz.node.hurt = 1.0
        spaz.node.name = ''
        spaz.on_move_left_right(0)
        spaz.on_move_up_down(0)
        spaz.on_run(0)

        _s, _sp = ref(self), ref(spaz)

        def dead_tick():
            s, sp = _s(), _sp()
            if not s or not sp or not sp.node:
                if s:
                    s.memory['timers'][f'dead_knock_{pid}'] = None
                return
            sp.node.handlemessage('knockout', 100)
            sp.node.color = (0.35, 0.35, 0.35)
            sp.node.highlight = (0.2, 0.2, 0.2)

        dead_tick()
        self.memory['timers'][f'dead_knock_{pid}'] = bs.Timer(0.09, dead_tick, repeat=True)

    def actors(self):
        return [a for a in [p.actor for p in self.memory['players'].values()] + list(self.memory['placeholder_masters'].values()) + [b for t in self.memory['spazzes'].values() for b in t] if a and a.node]

    def tally(self, v):
        t = getattr(v, 'team_id', 0)
        k, d = (self.memory['players'].get(i) for i in (1 - t, t))
        if (role := self.get_spaz_role(v)) != 'king':
            self.st[1 - t]['caps'][role] = self.st[1 - t]['caps'].get(role, 0) + 1
            self.st[t]['lost'] += 1
        k and self.stats.player_scored(k, 0, kill=True, display=False,
                                       screenmessage=False, showpoints=False)
        (d and not getattr(v, 'is_master', False)) and self.stats.player_was_killed(d, killed=True, killer=k)

    def mdead(self, m, lt=None):
        # result
        if self.game_over:
            return
        self.game_over = True
        lt = getattr(m, 'team_id', 0) if lt is None else lt
        wt, _s, _m, mid = 1 - lt, ref(self), (ref(m) if m else (lambda: None)), id(m)
        self.end_clock(self.current_turn_team_id)
        self.turn_active, self.pending_action = False, None
        self.stop_all_move_repeats()
        self.clear_selection()
        [self.hide_team_selector(t) for t in list(self.team_selectors)]
        [(p := self.memory['players'].get(t)) and (c := self.memory['control'].get(t))
         and self.release_control(p, c) for t in (wt, lt)]
        [self.memory['timers'].__setitem__(k, None) for k in list(
            self.memory['timers']) if not str(k).startswith('dead_knock_') and k != 'floaters']
        self.hide_legend(0.5)
        [p.resetinput() for p in self.players]
        for a in self.actors():
            a.node.hold_node = None
            a.on_move_left_right(0)
            a.on_move_up_down(0)
            a.on_run(0)
        # loser
        m and m.node and setattr(m.node, 'name', '')

        def zz():
            s, a = _s(), _m()
            if not s or not a or not a.node:
                return s and s.memory['timers'].__setitem__(f'dead_knock_{mid}', None)
            a.node.handlemessage('knockout', 100)
            a.node.color, a.node.highlight = (0.35,) * 3, (0.2,) * 3
        if m:
            zz()
            self.memory['timers'][f'dead_knock_{mid}'] = bs.Timer(0.09, zz, repeat=True)
        # winner
        ws = [a for a in self.actors() if getattr(a, 'team_id', None) == wt and a.is_alive()
              and not getattr(a, 'is_dead', False)]
        [a.node.handlemessage('knockout', 0.0) for a in ws if a.node]
        [self.restore_spaz_from_cooldown(a) for a in ws if self.is_on_cooldown(a)]
        self.alert('')
        bs.setmusic(None)
        wp = self.memory['players'].get(wt)
        wname = wp.team.name if wp and wp.team else self.teams[wt].name if len(
            self.teams) > wt else f'Team {wt + 1}'
        wtext = bui.Lstr(value=Strings.TEAM_WINS, subs=[('${TEAM}', wname)])
        total = 5.9

        def cel():
            if (s := _s()) and s.game_over:
                for a in ws:
                    if a and a.node and a.is_alive():
                        a.node.handlemessage('celebrate', 900)
                        d = uniform(0, 0.35)
                        bs.timer(d, lambda a=a: a.node and a.on_jump_press())
                        bs.timer(d + 0.12, lambda a=a: a.node and a.on_jump_release())

        def on_wins():
            s = _s()
            if not s or not s.game_over:
                return
            bs.setmusic(s.default_music)
            cel()
            s.memory['timers']['celebrate'] = bs.Timer(0.8, cel, repeat=True)
            # sequence
            s.memory['timers']['analysis'] = bs.Timer(
                2.0, lambda: (s2 := _s()) and s2.show_analysis(wt))

        def stt():
            s = _s()
            if s and s.game_over:
                s.ttl(wtext, s.get_team_color(wt), total, on_sub=on_wins, hold=True)

        t = self.memory['timers']
        # overlay
        self.memory['win_overlay'] = ov = bs.newnode('image', attrs={'texture': bs.gettexture(
            'white'), 'absolute_scale': True, 'attach': 'center', 'scale': (4000, 3000), 'color': (0, 0, 0), 'opacity': 0.0})
        self.memory['win_2d'].append(ov)
        t['wtt'] = bs.Timer(1.0, stt)

    def new_st(self):
        return {t: {'time': 0.0, 'turns': 0, 'longest': 0.0, 'caps': {}, 'lost': 0, 'mov': 0, 'atk': 0, 'spc': 0} for t in (0, 1)}

    def end_clock(self, tid):
        if tid is None or self.turn_t0 is None:
            return
        d, self.turn_t0 = bs.time() - self.turn_t0, None
        r = self.st[tid]
        r['time'] += d
        r['turns'] += 1
        r['longest'] = max(r['longest'], d)

    def show_analysis(self, wt):
        if not self.game_over:
            return
        self.globalsnode.camera_mode = 'rotate'
        # burst
        self.rotating = True
        for f in self.memory['floaters']:
            f.node and f.push()
        for _ in range(91):
            self.mkfloater()
        ov = self.memory.get('win_overlay')
        ov and ov.exists() and bs.animate(ov, 'opacity', {0: 0.0, 0.8: 0.3})

        def tm(x): return f'{int(x // 60)}:{x % 60:04.1f}'
        order = (('queen', 'Q'), ('rook', 'R'), ('bishop', 'B'), ('knight', 'N'), ('pawn', 'P'))

        def cp(c): return f"{sum(c.values())}" + (' (' +
                                                  ' '.join(f'{c[k]}{l}' for k, l in order if c.get(k)) + ')' if c else '')

        def left(t): return sum(1 for a in self.memory['spazzes'].get(
            t, []) if a and not getattr(a, 'is_dead', False))
        S = self.st
        # rows
        rows = (
            ('Time used', [tm(S[t]['time'])
             for t in (0, 1)], [S[t]['time'] for t in (0, 1)], 'low'),
            ('Turns', [str(S[t]['turns']) for t in (0, 1)], None, None),
            ('Avg turn', [tm(S[t]['time'] / max(1, S[t]['turns'])) for t in (0, 1)],
             [S[t]['time'] / max(1, S[t]['turns']) for t in (0, 1)], 'low'),
            ('Longest turn', [tm(S[t]['longest']) for t in (0, 1)], None, None),
            ('Captured', [cp(S[t]['caps']) for t in (0, 1)], [
             sum(S[t]['caps'].values()) for t in (0, 1)], 'high'),
            ('Lost', [str(S[t]['lost']) for t in (0, 1)], [S[t]['lost'] for t in (0, 1)], 'low'),
            ('Moves / Attacks / Specials',
             [f"{S[t]['mov']} / {S[t]['atk']} / {S[t]['spc']}" for t in (0, 1)], None, None),
            ('Pieces left', [str(left(t)) for t in (0, 1)], [left(t) for t in (0, 1)], 'high'),
            ('Score', [str(self.tsc(t, t == wt))
             for t in (0, 1)], [self.tsc(t, t == wt) for t in (0, 1)], 'high'),
        )
        gold, grey = (1.0, 0.9, 0.5, 1.0), (0.7, 0.7, 0.8, 1.0)
        xs = (-190, 190)

        def tx(txt, x, y, col, sc, d, mw=None, pop=False):
            def mk():
                if pop and not self.game_over:
                    return
                t = Text(txt, position=(x, y), h_align=Text.HAlign.CENTER, v_align=Text.VAlign.CENTER, color=col, scale=sc,
                         maxwidth=mw, transition=None if pop else Text.Transition.FADE_IN, transition_delay=0.0 if pop else d)
                t.autoretain()
                self.memory['win_2d'].append(t.node)
            # instant
            bs.timer(d, mk) if pop else mk()

        d0 = 0.6
        for t in (0, 1):
            nm = self.teams[t].name if len(self.teams) > t else f'Team {t + 1}'
            tx(bui.Lstr(value='${T}', subs=[('${T}', nm)]), xs[t],
               42, tuple(self.get_team_color(t)) + (1.0,), 1.1, d0, 260)
        bs.timer(d0, bs.getsound('swip').play)
        for i, (lab, vals, cmpv, better) in enumerate(rows):
            d, y, last = d0 + 0.4 * (i + 1) + (0.5 if i == len(rows) -
                                               1 else 0.0), 12 - 25 * i, i == len(rows) - 1
            win = [False, False]
            if cmpv and cmpv[0] != cmpv[1]:
                win[0 if (cmpv[0] > cmpv[1]) == (better == 'high') else 1] = True
            tx(lab, 0, y, (0.5, 0.5, 0.6, 1.0), 0.7, d + 0.1 if last else d, 220, pop=last)
            for t in (0, 1):
                tx(vals[t], xs[t], y, gold if win[t] else grey,
                   1.2 if last else 0.9, d + 0.1, 260, pop=last)
            if last:
                bs.timer(d + 0.1, bs.getsound('cashRegister').play)

        # prompt
        _s, _wt = ref(self), wt

        def ask():
            s = _s()
            if not s or not s.game_over:
                return
            n = bs.newnode('text', attrs={
                'text': bui.Lstr(value=Strings.CONTINUE, subs=[('${B}', bui.charstr(bui.SpecialChar.LEFT_BUTTON))]),
                'scale': 1.0, 'v_attach': 'bottom', 'h_attach': 'center', 'h_align': 'center', 'v_align': 'center',
                'position': (0, 50), 'color': (1, 1, 1), 'opacity': 0.0
            })
            s.memory['win_2d'].append(n)
            fl(n, (1, 1, 1), 1.0, 0.6)
            bs.animate(n, 'opacity', {0: 0, 0.4: 1})

            def go():
                s2 = _s()
                if not s2 or not s2.game_over:
                    return
                for q in s2.players:
                    q.resetinput()
                bs.getsound('punch01').play()
                n.exists() and n.delete()
                s2.memory['win_2d'].append(bs.newnode('text', attrs={
                    'text': Strings.PROCEEDING,
                    'scale': 1.0, 'v_attach': 'bottom', 'h_attach': 'center', 'h_align': 'center', 'v_align': 'center',
                    'position': (0, 50), 'color': (1, 1, 0), 'opacity': 1.0
                }))
                s2.fin(_wt)
            for q in s.players:
                q.assigninput(bs.InputType.PUNCH_PRESS, go)
        self.memory['timers']['cont'] = bs.Timer(d + 0.9, ask)

    def fin(self, wt):
        if not self.game_over:
            return
        r = bs.GameResults()
        for t in self.teams:
            r.set_team_score(t, self.tsc(t.id, t.id == wt))
        self.end(results=r, announce_winning_team=False)

    def tsc(self, team_id, won):
        # scoring
        values = {'pawn': 10, 'knight': 30, 'bishop': 30, 'rook': 50, 'queen': 90}
        score = sum(
            values.get(self.get_spaz_role(a), 0)
            for a in self.memory['spazzes'].get(team_id, [])
            if a and not getattr(a, 'is_dead', False)
        )
        return score + (250 if won else 0)

    def sanity_tick(self):
        need = 1 if DEBUG else 2
        n = len(self.players)
        # pieces
        for tid in ([0, 1] if (DEBUG and n) else [p.team.id for p in self.players]):
            if not self.team_spawned(tid):
                self.spawn_team(tid)
        self.playing = n >= 1
        if n >= need:
            if not self.memory.get('started'):
                self.alert(Strings.PLACE_PIECES)
        else:
            self.alert(Strings.WAITING_FOR_PLAYERS, (1, 1, 0))

    def set_master_tile(self, sq, color, active=True):
        pt = (round(sq[0], 1), round(sq[1], 1))
        node = self.map.fills.get(pt)
        inner = self.map.inner_fills.get(pt)
        if active:
            if node:
                node.shape = 'circleOutline'
                node.size = (0.63,)
                node.color = color
                node.opacity = 0.7
            if inner:
                inner.shape = 'circleOutline'
                inner.size = (0.57,)
                inner.color = color
                inner.opacity = 0.7
        else:
            if node:
                node.shape = 'circle'
                node.size = (0.9,)
                node.opacity = 0.0
            if inner:
                inner.opacity = 0.0

    def team_spawned(self, team_id):
        return bool(self.memory['spazzes'].get(team_id))

    def spawn_team(self, team_id):
        if self.team_spawned(team_id):
            return
        bs.getsound('spawn').play()

        characters = ['Zoe', 'Agent Johnson', 'Pixel', 'Spaz', 'Kronk']

        board_edge = 4.0
        deck_x_min = -board_edge
        deck_x_max = board_edge
        spacing = (deck_x_max - deck_x_min) / (len(characters) - 1)

        spawn_z = self.map.defs.points[f'spawn{team_id+1}'][2]
        side = 1 if spawn_z > 0 else -1
        spawn_offset = spawn_z - side * board_edge
        deck_z = side * board_edge + spawn_offset * 2
        rotation = 0 if team_id == 0 else 180

        ksq = (0.5, 3.5 if side > 0 else -3.5)
        self.memory['kings'][team_id] = ksq
        self.team_selector_pos[team_id] = [round(ksq[0], 1), round(ksq[1], 1)]

        col = self.get_team_color(team_id)
        self.set_master_tile(ksq, self.neon(*col), active=True)
        for r in (3.5, 2.5):
            for c in range(8):
                self.map.tiles[int(side * r + 3.5) * 8 + c].color = col

        if team_id not in self.memory['players'] and DEBUG:
            master_bot = Spaz(
                character='Spaz',
                color=(1, 1, 1),
                highlight=col,
                start_invincible=False
            )
            master_bot.node.name = 'Master'
            master_bot.node.name_color = col
            master_bot.is_master = True
            master_bot.is_dead = False
            master_bot.hitpoints = master_bot.hitpoints_max = 50
            master_bot.team_id = team_id
            master_bot.orig_pos = (ksq[0], 0, ksq[1])
            master_bot.orig_rot = rotation
            master_bot.handlemessage = lambda m, s=ref(self), b=ref(
                master_bot): s() and b() and s().handlemessage(b(), m)
            master_bot.handlemessage(self.init_stand(master_bot.orig_pos, master_bot.orig_rot))
            self.recolor(master_bot, occupied=True)
            self.memory['placeholder_masters'][team_id] = master_bot
            self.retain(master_bot)

        self.memory['spazzes'][team_id] = []
        ap = DEBUG or self.autoplace
        first_rank_z = 3.5 if side > 0 else -3.5
        rank_xs = [-2.5, -1.5, -0.5, 1.5, 2.5]

        for i, character in enumerate(characters):
            x = deck_x_min + spacing * i
            bot = Piece(
                character=character,
                start_invincible=False,
                game=self,
                team_id=team_id
            )

            if ap:
                sq = (rank_xs[i], first_rank_z)
                bot.orig_pos = (sq[0], 0, sq[1])
                bot.orig_rot = rotation
                bot.handlemessage(self.init_stand(bot.orig_pos, bot.orig_rot))
                self.memory['squares'][bot] = sq
                self.highlight_tile(sq, color=self.get_team_color(team_id), active=True)
            else:
                bot.orig_pos = (x, 0, deck_z)
                bot.orig_rot = rotation
                bot.handlemessage(self.init_stand(bot.orig_pos, bot.orig_rot))

            bot.node.color = (1, 1, 1)
            bot.node.highlight = self.get_team_color(team_id)
            if ap:
                self.recolor(bot, occupied=True)
            self.memory['spazzes'][team_id].append(bot)
            self.retain(bot)
            if not ap:
                self.start_run(bot)

        if not self.memory.get('legend_on'):
            self.memory['legend_on'] = True
            self.memory['timers']['legend'] = arr = []
            for n in self.legend:
                n in self.rel or arr.append(
                    bs.Timer(1, bs.animate(n, 'opacity', {0: 0, 0.6: 0.7}).delete))

    def remove_team(self, team_id):
        t = self.memory['timers']
        for b in self.memory['spazzes'].pop(team_id, []):
            if not b:
                continue
            t[f'retain_{id(b)}'] = None
            t[f'run_pulse_{id(b)}'] = None
            self.stop_run(b)
            if sq := self.memory['squares'].pop(b, None):
                self.highlight_tile(sq, active=False)
            self.memory['cooldowns'].pop(b, None)
            if b.node:
                b.node.hold_node = None
                b.handlemessage(bs.DieMessage(immediate=True))
        if m := self.memory['placeholder_masters'].pop(team_id, None):
            t[f'retain_{id(m)}'] = None
            t[f'run_pulse_{id(m)}'] = None
            if m.node:
                m.handlemessage(bs.DieMessage(immediate=True))
        if ksq := self.memory['kings'].pop(team_id, None):
            kill_anims(self.king_anims.pop(team_id, None))
            self.set_master_tile(ksq, (1, 1, 1), active=False)
        self.king_anims.pop(team_id, None)
        self.memory['glow'].pop(team_id, None)
        self.memory['lm'].pop(team_id, None)
        self.memory['swap'].pop(team_id, None)
        self.memory['team_colors'].pop(team_id, None)
        self.team_selector_pos.pop(team_id, None)
        # ranks
        side = 1 if self.map.defs.points[f'spawn{team_id + 1}'][2] > 0 else -1
        for r in (3.5, 2.5):
            for c in range(8):
                self.map.tiles[int(side * r + 3.5) * 8 + c].color = (1, 1, 1)
        if team_id in self.team_selectors:
            self.hide_team_selector(team_id)
            if n := self.team_selectors.pop(team_id, None):
                n.delete()
        self.clear_selection()

    def claim_spaz(self, player, target):
        if target.claimed_by is not None:
            return

        self.memory['timers'][f'retain_{id(target)}'] = None
        self.stop_run(target)

        origin = player.actor
        prev = self.memory['control'].get(player.team.id)

        losing = prev or origin
        losing.node.hold_node = None

        target.claimed_by = player.team.id
        target.source_player = player
        self.memory['control'][player.team.id] = target

        bs.getsound('gunCocking').play(1.0, position=target.node.position)
        target.node.handlemessage('flash')

        if prev is None:
            self.memory['swap'][player.team.id] = (
                origin.node.name, origin.node.name_color,
                origin.node.color, origin.node.highlight
            )
            origin.node.name = ''

            bs.animate_array(origin.node, 'color', 3, {0: origin.node.color, 0.3: (0.5, 0.5, 0.5)})
            bs.animate_array(origin.node, 'highlight', 3, {
                             0: origin.node.highlight, 0.3: (0.5, 0.5, 0.5)})

            origin.on_move_up_down(0)
            origin.on_move_left_right(0)

            self.knockdown(player.team.id, origin)
        else:
            prev.claimed_by = None
            prev.source_player = None
            prev.node.name = ''

            prev.on_move_up_down(0)
            prev.on_move_left_right(0)

            self.handle_release(prev)
            self.start_run(prev)

        name, name_color = self.memory['swap'][player.team.id][:2]
        target.node.name = name
        target.node.name_color = name_color

        self.assign_controls(player, target)

    def release_control(self, player, target):
        if self.memory['control'].get(player.team.id) is not target:
            return

        self.memory['control'].pop(player.team.id, None)
        self.memory['timers'][f'knock{player.team.id}'] = None
        target.claimed_by = None
        target.source_player = None

        target.node.hold_node = None

        bs.getsound('laser').play(1.0, position=target.node.position)

        target.on_move_up_down(0)
        target.on_move_left_right(0)

        self.handle_release(target)
        self.start_run(target)

        if target.node:
            target.node.name = ''
        name, name_color, color, highlight = self.memory['swap'].pop(player.team.id)
        if player.actor and player.actor.node:
            player.actor.node.name = name
            player.actor.node.name_color = name_color
            bs.animate_array(player.actor.node, 'color', 3, {
                             0: player.actor.node.color, 0.3: color})
            bs.animate_array(player.actor.node, 'highlight', 3, {
                             0: player.actor.node.highlight, 0.3: highlight})
            self.assign_controls(player, player.actor)

    def handle_release(self, piece):
        if not piece or not piece.node:
            return
        px, _, pz = piece.node.position
        side = 1 if self.map.defs.points[f'spawn{piece.team_id+1}'][2] > 0 else -1
        rows = (6, 7) if side > 0 else (0, 1)
        if -4.0 <= px <= 4.0 and -4.0 <= pz <= 4.0 and (side * pz > 0):
            occupied = {v for k, v in self.memory['squares'].items(
            ) if k is not piece and k.is_alive()}
            occupied.update(self.memory['kings'].values())
            free = [
                (c - 3.5, r - 3.5)
                for r in rows for c in range(8)
                if (c - 3.5, r - 3.5) not in occupied
            ]
            if free:
                if prev_sq := self.memory['squares'].get(piece):
                    self.highlight_tile(prev_sq, active=False)

                sq = min(free, key=lambda s: (s[0] - px)**2 + (s[1] - pz)**2)
                self.memory['squares'][piece] = sq

                c = self.get_team_color(piece.team_id)
                self.highlight_tile(sq, color=c, active=True)

                self.recolor(piece, occupied=True)
                self.retain(piece)
                return
        if old_sq := self.memory['squares'].pop(piece, None):
            self.highlight_tile(old_sq, active=False)
        self.recolor(piece, occupied=False)
        self.retain(piece)

    def path(self, piece, pos, sq):
        px, pz = pos
        sx, sz = sq
        sc, sr = int(round(px + 3.5)), int(round(pz + 3.5))
        ec, er = int(round(sx + 3.5)), int(round(sz + 3.5))

        if (sc, sr) == (ec, er):
            return sq

        blocked = set()
        for p, s in self.memory['squares'].items():
            if p is not piece and p.is_alive():
                blocked.add((int(round(s[0] + 3.5)), int(round(s[1] + 3.5))))
        for k in self.memory['kings'].values():
            blocked.add((int(round(k[0] + 3.5)), int(round(k[1] + 3.5))))
        blocked.discard((ec, er))

        def bfs(allow_outside: bool):
            if not allow_outside:
                if not (0 <= sc < 8 and 0 <= sr < 8):
                    return None
                min_c, max_c = 0, 7
                min_r, max_r = 0, 7
            else:
                min_c = max(-5, min(-2, sc - 1))
                max_c = min(12, max(9, sc + 1))
                min_r = max(-5, min(-2, sr - 1))
                max_r = min(12, max(9, sr + 1))

            q = deque([(sc, sr)])
            prev = {(sc, sr): None}
            found = False

            while q:
                c, r = q.popleft()
                if (c, r) == (ec, er):
                    found = True
                    break
                neighbors = [(c + dc, r + dr) for dc, dr in ((0, 1), (0, -1), (1, 0), (-1, 0))]
                neighbors.sort(key=lambda n: (n[0] - ec) ** 2 + (n[1] - er) ** 2)
                for nc, nr in neighbors:
                    if (
                        min_c <= nc <= max_c
                        and min_r <= nr <= max_r
                        and (nc, nr) not in blocked
                        and (nc, nr) not in prev
                    ):
                        prev[(nc, nr)] = (c, r)
                        q.append((nc, nr))

            if not found:
                return None

            curr = (ec, er)
            trace = []
            while curr != (sc, sr):
                trace.append(curr)
                curr = prev[curr]

            nxt = trace[-1]
            return sq if nxt == (ec, er) else (nxt[0] - 3.5, nxt[1] - 3.5)

        res = bfs(allow_outside=False)
        if res is not None:
            return res

        res = bfs(allow_outside=True)
        if res is not None:
            return res

        corners = [
            (int(round(sx - 0.5)), int(round(sz - 0.5))),
            (int(round(sx - 0.5)), int(round(sz + 0.5))),
            (int(round(sx + 0.5)), int(round(sz - 0.5))),
            (int(round(sx + 0.5)), int(round(sz + 0.5))),
        ]
        tex, tez = min(corners, key=lambda c: (c[0] - px) ** 2 + (c[1] - pz) ** 2)
        start_gx = int(max(-4, min(4, round(px))))
        start_gz = int(max(-4, min(4, round(pz))))

        if ((px - start_gx) ** 2 + (pz - start_gz) ** 2) ** 0.5 > 0.2:
            return (float(start_gx), float(start_gz))

        if (start_gx, start_gz) == (tex, tez):
            return sq

        gq = deque([(start_gx, start_gz)])
        gprev = {(start_gx, start_gz): None}
        gfound = False

        while gq:
            cx, cz = gq.popleft()
            if (cx, cz) == (tex, tez):
                gfound = True
                break
            for ndx, ndz in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                ngx, ngz = cx + ndx, cz + ndz
                if -4 <= ngx <= 4 and -4 <= ngz <= 4 and (ngx, ngz) not in gprev:
                    gprev[(ngx, ngz)] = (cx, cz)
                    gq.append((ngx, ngz))

        if not gfound:
            return sq

        curr_g = (tex, tez)
        gtrace = []
        while curr_g != (start_gx, start_gz):
            gtrace.append(curr_g)
            curr_g = gprev[curr_g]

        next_g = gtrace[-1]
        return (float(next_g[0]), float(next_g[1]))

    def check_kings(self):
        if not self.playing or (len(self.players) < (1 if DEBUG else 2) and not DEBUG) or not self.memory.get('spazzes'):
            return

        both_ready = (len(self.memory['players']) >= (1 if DEBUG else 2) or DEBUG) and all(
            len(bots) > 0 and all(b in self.memory['squares'] for b in bots)
            for bots in self.memory['spazzes'].values()
        )
        both_in = True
        for tid, ksq in self.memory['kings'].items():
            player = self.memory['players'].get(tid)
            p_in = False
            if player and player.actor and player.actor.node:
                px, _, pz = player.actor.node.position
                p_in = abs(px - ksq[0]) < 0.5 and abs(pz - ksq[1]) < 0.5
            elif m := self.memory['placeholder_masters'].get(tid):
                if m.node:
                    mx, _, mz = m.node.position
                    p_in = abs(mx - ksq[0]) < 0.5 and abs(mz - ksq[1]) < 0.5
            if not p_in:
                both_in = False

            st = 'fade' if (both_ready and not p_in) else 'in'
            if st != self.memory['glow'].get(tid):
                self.memory['glow'][tid] = st
                c = self.get_team_color(tid)
                kill_anims(self.king_anims.pop(tid, None))
                if node := self.map.fills.get((round(ksq[0], 1), round(ksq[1], 1))):
                    node.shape = 'circleOutline'
                    node.size = (0.63,)
                    if st == 'in':
                        bs.animate_array(node, 'color', 3, {0.0: node.color, 0.2: self.neon(*c)})
                    else:
                        self.king_anims.setdefault(tid, []).extend(loop_array(
                            node, 'color', 3, {0.0: c, 0.8: c, 1.1: self.neon(*c), 1.4: c}))
                if inner := self.map.inner_fills.get((round(ksq[0], 1), round(ksq[1], 1))):
                    inner.shape = 'circleOutline'
                    inner.size = (0.57,)
                    inner.opacity = 0.7
                    if st == 'in':
                        bs.animate_array(inner, 'color', 3, {0.0: inner.color, 0.2: self.neon(*c)})
                    else:
                        self.king_anims.setdefault(tid, []).extend(loop_array(
                            inner, 'color', 3, {0.0: c, 0.8: c, 1.1: self.neon(*c), 1.4: c}))

        if self.memory.get('started'):
            return

        if not both_ready:
            self.stop_countdown()
            self.alert(Strings.PLACE_PIECES)
            return

        if both_in:
            if not self.memory['timers'].get('countdown'):
                self.start_countdown()
        else:
            self.stop_countdown()
            self.alert(Strings.STAND_IN_POSITION)

    def start_countdown(self):
        self.memory['count'] = 5
        _s = ref(self)

        def step():
            s = _s()
            if not s or s.memory.get('started'):
                return
            cnt = s.memory.get('count', 0)
            if cnt > 0:
                s.alert(f'{Strings.STARTING_IN} {cnt}', (1, 1, 0))
                bs.getsound('tick').play()
                s.memory['count'] -= 1
            else:
                s.stop_countdown()
                s.start_match()
        step()
        self.memory['timers']['countdown'] = bs.Timer(1.0, step, repeat=True)

    def stop_countdown(self):
        self.memory['timers']['countdown'] = None
        self.memory.pop('count', None)

    def schedule_idle_emote(self):
        delay = uniform(6.0, 12.0)
        _s = ref(self)
        self.memory['timers']['idle_emote'] = bs.Timer(
            delay, lambda: _s() and _s().trigger_idle_emote())

    def trigger_idle_emote(self):
        if not self.playing or not self.memory.get('started'):
            return
        candidates = []
        for team in self.memory['spazzes'].values():
            for b in team:
                if b and b.node and b.is_alive() and not getattr(b, 'is_dead', False):
                    if self.is_on_cooldown(b):
                        continue
                    char = (getattr(b, 'character', '') or '').lower()
                    if any(k in char for k in ('kronk', 'pixel', 'pixie', 'zoe')):
                        pa = self.pending_action
                        if not (pa and pa.get('spaz') is b):
                            sq = self.memory['squares'].get(b)
                            if sq:
                                px, _, pz = b.node.position
                                if ((sq[0] - px) ** 2 + (sq[1] - pz) ** 2) ** 0.5 <= 0.08:
                                    candidates.append(b)
        if candidates:
            b = choice(candidates)
            char = (getattr(b, 'character', '') or '').lower()
            if 'kronk' in char:
                b.on_punch_press()
                pid = id(b)
                self.memory['timers'][f'kronk_p_{pid}'] = bs.Timer(
                    0.15, lambda: b and b.node and b.on_punch_release())
            elif 'pixel' in char or 'pixie' in char:
                rdx, rdz = choice([(-1, 0), (1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)])
                b.on_move_left_right(rdx * 0.05)
                b.on_move_up_down(-rdz * 0.05)
                pid = id(b)
                self.memory['timers'][f'pixie_look_{pid}'] = bs.Timer(
                    1.5, lambda: b and b.node and (b.on_move_left_right(0), b.on_move_up_down(0)))
            elif 'zoe' in char:
                kpos = self.memory['kings'].get(b.team_id)
                if kpos and b.node:
                    px, _, pz = b.node.position
                    zvx, zvz = kpos[0] - px, kpos[1] - pz
                    zl = (zvx * zvx + zvz * zvz) ** 0.5 or 1.0
                    b.on_move_left_right((zvx / zl) * 0.05)
                    b.on_move_up_down((-zvz / zl) * 0.05)
                    pid = id(b)
                    b.zoe_looking_at_master = True

                    def end_zoe():
                        if b and b.node:
                            b.zoe_looking_at_master = False
                            b.on_move_left_right(0)
                            b.on_move_up_down(0)
                    self.memory['timers'][f'zoe_look_{pid}'] = bs.Timer(2.5, end_zoe)
        self.schedule_idle_emote()

    def start_match(self):
        self.memory['started'] = True
        self.alert('')
        self.hide_legend()

        for p in self.players:
            p.resetinput()

        for team in self.memory['spazzes'].values():
            for b in team:
                self.stop_run(b)
                if b and b.node:
                    b.on_move_left_right(0)
                    b.on_move_up_down(0)

        for tid, p in self.memory['players'].items():
            rot = 0 if tid else 180
            if p.actor and p.actor.node and (ksq := self.memory['kings'].get(tid)):
                p.actor.handlemessage(self.init_stand((ksq[0], 0, ksq[1]), rot))
            for b in self.memory['spazzes'].get(tid, []):
                if b and b.node and (sq := self.memory['squares'].get(b)):
                    b.handlemessage(self.init_stand((sq[0], 0, sq[1]), rot))

        for p in self.memory['players'].values():
            if p.actor and p.actor.node:
                self.retain(p.actor)
        for m in self.memory['placeholder_masters'].values():
            if m and m.node:
                self.retain(m)

        for team in self.memory['spazzes'].values():
            for b in team:
                self.start_pulse(b)
        for p in self.memory['players'].values():
            if p.actor:
                self.start_pulse(p.actor)
        for m in self.memory['placeholder_masters'].values():
            if m:
                self.start_pulse(m)

        self.schedule_idle_emote()

        _s = ref(self)

        def asub():
            s2 = _s()
            if s2:
                s2.memory['timers']['start_turn'] = bs.Timer(
                    4.0 - 0.45, lambda: _s() and _s().begin_turn_phase())
        self.ttl(choice(Strings.SUBTITLES), (1.0, 1.0, 1.0), 3.9, on_sub=asub)

    def ttl(self, stx, scol, total, on_sub=None, hold=False):
        _s = ref(self)
        snd = self.playsnd('cashRegister2')
        t1 = bs.newnode(
            'text',
            attrs={
                'text': Strings.CHECK,
                'big': True,
                'v_attach': 'center',
                'h_attach': 'center',
                'h_align': 'right',
                'v_align': 'center',
                'position': (-10, 100),
                'color': (1, 1, 1),
                'opacity': 0.0,
            }
        )
        try:
            t1.flatness = -2.0
        except Exception:
            pass
        bs.animate(t1, 'opacity', {0: 0, 0.1: 1} if hold else {
                   0: 0, 0.1: 1, total - 0.4: 1, total: 0})
        hold and self.memory['win_2d'].append(t1)
        bs.animate_array(t1, 'position', 2, {0.0: (-10.0, 100.0), total - 0.4: (-8.0, 100.0)})
        hold or bs.Timer(total, t1.delete)

        def on_boom():
            s = _s()
            if snd:
                snd.delete()
            if not s:
                return
            bs.getsound('explosion04').play()
            t2 = bs.newnode(
                'text',
                attrs={
                    'text': Strings.BOOM,
                    'big': True,
                    'v_attach': 'center',
                    'h_attach': 'center',
                    'h_align': 'left',
                    'v_align': 'center',
                    'position': (10, 100),
                    'color': (0.7, 0.7, 0.7),
                    'opacity': 0.0,
                }
            )
            try:
                t2.flatness = -2.0
            except Exception:
                pass
            hold and s.memory['win_2d'].append(t2)
            end2 = total - 0.45
            bs.animate(t2, 'opacity', {0: 0, 0.1: 1} if hold else {
                       0: 0, 0.1: 1, end2 - 0.4: 1, end2: 0})
            bs.animate_array(t2, 'position', 2, {0.0: (10.0, 100.0), end2 - 0.4: (8.0, 100.0)})
            hold or bs.Timer(end2, t2.delete)

            def sub_in():
                s2 = _s()
                if not s2:
                    return
                bs.getsound('dingSmallHigh').play()
                t_sub = bs.newnode(
                    'text',
                    attrs={
                        'text': stx,
                        'big': False,
                        'scale': 1.1,
                        'v_attach': 'center',
                        'h_attach': 'center',
                        'h_align': 'center',
                        'v_align': 'center',
                        'position': (0, 137),
                        'color': scol,
                        'opacity': 0.0,
                    }
                )
                hold and s2.memory['win_2d'].append(t_sub)
                sub_end = total - 0.45 - 0.45
                fl(t_sub, scol, 1.0, 0.6)
                bs.animate(t_sub, 'opacity', {0: 0, 0.1: 1} if hold else {
                           0: 0, 0.1: 1, sub_end - 0.4: 1, sub_end: 0})
                hold or bs.Timer(sub_end, t_sub.delete)
                if on_sub:
                    on_sub()

            s.memory['timers']['sbt'] = bs.Timer(0.45, sub_in)

        self.memory['timers']['title'] = bs.Timer(0.45, on_boom)

    def update_legend(self, mode: str):
        for n in self.legend:
            if n:
                n.delete()
        self.legend.clear()

        c_purple = (0.40, 0.23, 0.72)
        c_light_purple = (0.75, 0.50, 0.95)
        c_grab = (0.2, 0.45, 1.0)

        if mode == 'unselected':
            self.legend.append(bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('nub'),
                    'absolute_scale': True,
                    'attach': 'centerLeft',
                    'position': (30, 40),
                    'scale': (46, 46),
                    'color': c_purple,
                    'opacity': 0.0
                }
            ))
            self.legend.append(bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('nub'),
                    'absolute_scale': True,
                    'attach': 'centerLeft',
                    'position': (30, 40),
                    'scale': (22, 22),
                    'color': c_light_purple,
                    'opacity': 0.0
                }
            ))
            self.legend.append(bs.newnode(
                'text',
                attrs={
                    'text': Strings.MOVE,
                    'h_attach': 'left',
                    'v_attach': 'center',
                    'position': (62, 40),
                    'v_align': 'center',
                    'color': c_light_purple,
                    'opacity': 0.0
                }
            ))

            self.legend.append(bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('buttonPickUp'),
                    'absolute_scale': True,
                    'attach': 'centerLeft',
                    'position': (30, -10),
                    'scale': (46, 46),
                    'color': c_grab,
                    'opacity': 0.0
                }
            ))
            self.legend.append(bs.newnode(
                'text',
                attrs={
                    'text': Strings.SELECT,
                    'h_attach': 'left',
                    'v_attach': 'center',
                    'position': (62, -10),
                    'v_align': 'center',
                    'color': c_grab,
                    'opacity': 0.0
                }
            ))
        else:
            self.legend.append(bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('nub'),
                    'absolute_scale': True,
                    'attach': 'centerLeft',
                    'position': (30, 65),
                    'scale': (42, 42),
                    'color': c_purple,
                    'opacity': 0.0
                }
            ))
            self.legend.append(bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('nub'),
                    'absolute_scale': True,
                    'attach': 'centerLeft',
                    'position': (30, 65),
                    'scale': (20, 20),
                    'color': c_light_purple,
                    'opacity': 0.0
                }
            ))
            self.legend.append(bs.newnode(
                'text',
                attrs={
                    'text': Strings.MOVE,
                    'h_attach': 'left',
                    'v_attach': 'center',
                    'position': (62, 65),
                    'v_align': 'center',
                    'color': c_light_purple,
                    'opacity': 0.0
                }
            ))

            self.legend.append(bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('buttonPickUp'),
                    'absolute_scale': True,
                    'attach': 'centerLeft',
                    'position': (30, 15),
                    'scale': (42, 42),
                    'color': c_grab,
                    'opacity': 0.0
                }
            ))
            self.legend.append(bs.newnode(
                'text',
                attrs={
                    'text': Strings.GO,
                    'h_attach': 'left',
                    'v_attach': 'center',
                    'position': (62, 15),
                    'v_align': 'center',
                    'color': c_grab,
                    'opacity': 0.0
                }
            ))

            self.legend.append(bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('buttonBomb'),
                    'absolute_scale': True,
                    'attach': 'centerLeft',
                    'position': (30, -35),
                    'scale': (42, 42),
                    'color': (1.0, 0.2, 0.2),
                    'opacity': 0.0
                }
            ))
            self.legend.append(bs.newnode(
                'text',
                attrs={
                    'text': Strings.SPECIAL,
                    'h_attach': 'left',
                    'v_attach': 'center',
                    'position': (62, -35),
                    'v_align': 'center',
                    'color': (1.0, 0.3, 0.3),
                    'opacity': 0.0
                }
            ))

        for node in self.legend:
            bs.animate(node, 'opacity', {0.0: 0.0, 0.25: 0.8})

    def begin_turn_phase(self):
        if not self.playing or not self.memory.get('started'):
            return
        self.update_legend('unselected')
        first_team_id = 0
        _s = ref(self)
        self.memory['timers']['hold_node_check'] = bs.Timer(
            1.0, lambda: _s() and _s().check_held_nodes(), repeat=True
        )
        self.start_turn(first_team_id)

    def hide_team_selector(self, tid):
        for d in (self.team_selector_anim, self.team_selector_blink):
            d.get(tid) and d[tid].delete()
            d[tid] = None
        # delete
        (n := self.team_selectors.pop(tid, None)) and n.delete()

    def show_team_selector(self, tid):
        [self.hide_team_selector(o) for o in list(self.team_selectors) if o != tid]
        k = self.memory['kings'].get(tid, (0.5, 3.5 if tid == 0 else -3.5))
        pos = self.team_selector_pos.setdefault(tid, [round(k[0], 1), round(k[1], 1)])
        self.hide_team_selector(tid)
        n = self.team_selectors[tid] = bs.newnode('locator', attrs={'shape': 'box', 'position': (pos[0], 0.6, pos[1]), 'size': (
            1.0, 1.2, 1.0), 'color': self.neon(*self.get_team_color(tid)), 'opacity': 0.0, 'draw_beauty': True})
        self.team_selector_blink[tid] = bs.animate(
            n, 'opacity', {0.0: 0.0, 0.25: 0.85, 0.5: 0.0}, loop=True)

    def hide_legend(self, t=0.3):
        [n.exists() and bs.animate(n, 'opacity', {
            0.0: n.opacity, t: 0.0}) for n in self.legend if n]

    def hide_selector(self):
        if self.current_turn_team_id is not None:
            self.hide_team_selector(self.current_turn_team_id)

    def start_turn(self, team_id):
        if self.game_over or not self.playing or not self.memory.get('started'):
            return
        self.turn_active = True
        self.turn_t0 = bs.time()
        self.clear_selection()
        self.current_turn_team_id = team_id
        self.stop_all_move_repeats()

        bs.getsound('swip').play()

        player = self.memory['players'].get(team_id)
        if player and player.team:
            team_name = player.team.name
        elif len(self.teams) > team_id:
            team_name = self.teams[team_id].name
        else:
            team_name = f'Team {team_id + 1}'

        self.turn_msg = bui.Lstr(value=Strings.TEAM_TURN, subs=[('${TEAM}', team_name)])
        self.alert(self.turn_msg, (1, 1, 1))
        self.memory['timers']['turn_clock'] = None
        if self.turn_time:
            self.turn_end_t = bs.time() + self.turn_time
            self.turn_clock_tick()
            _s = ref(self)
            self.memory['timers']['turn_clock'] = bs.Timer(
                0.25, lambda: _s() and _s().turn_clock_tick(), repeat=True)

        self.setup_turn_inputs()
        self.sel_last(team_id)
        self.show_team_selector(team_id)

    def turn_clock_tick(self):
        if self.game_over or not self.turn_active or self.pending_action is not None or self.current_turn_team_id is None:
            return
        left = max(0, int(self.turn_end_t - bs.time() + 0.999))
        tid = self.current_turn_team_id
        try:
            txt = self.turn_msg.evaluate()
        except Exception:
            txt = str(self.turn_msg)
        self.alert(f'{txt}  {left}', readable(self.get_team_color(tid)))
        if bs.time() >= self.turn_end_t:
            self.memory['timers']['turn_clock'] = None
            self.stop_all_move_repeats()
            self.clear_selection()
            self.hide_team_selector(tid)
            self.hide_legend()
            bs.getsound('block').play()
            self.switch_turn()

    def sel_last(self, team_id):
        ref_ = self.memory['lm'].get(team_id)
        piece = ref_() if ref_ else None
        if not piece or not piece.node or not piece.is_alive() or getattr(piece, 'is_dead', False):
            sq = self.memory['kings'].get(team_id)
        else:
            sq = self.get_spaz_square(piece)
        if sq:
            self.team_selector_pos[team_id] = [round(sq[0], 1), round(sq[1], 1)]

    def setup_turn_inputs(self):
        _s = ref(self)
        for p in self.players:
            p.resetinput()
            _p = ref(p)
            p.assigninput(
                bs.InputType.UP_DOWN,
                lambda v, _p=_p: _s() and _p() and _s().handle_move_up_down(_p(), v)
            )
            p.assigninput(
                bs.InputType.LEFT_RIGHT,
                lambda v, _p=_p: _s() and _p() and _s().handle_move_left_right(_p(), v)
            )
            p.assigninput(
                bs.InputType.PICK_UP_PRESS,
                lambda _p=_p: _s() and _p() and _s().handle_grab_press(_p())
            )
            p.assigninput(
                bs.InputType.PUNCH_PRESS,
                lambda _p=_p: _s() and _p() and _s().handle_punch_press(_p())
            )
            p.assigninput(
                bs.InputType.BOMB_PRESS,
                lambda _p=_p: _s() and _p() and _s().handle_bomb_press(_p())
            )

    def can_control(self, player):
        if not self.turn_active or self.current_turn_team_id is None:
            return False
        if self.pending_action is not None:
            return False
        if player.team is None:
            return False
        if DEBUG and len(self.memory['players']) == 1:
            return True
        return player.team.id == self.current_turn_team_id

    def get_spaz_square(self, spaz):
        if not spaz:
            return None
        if spaz in self.memory['squares']:
            return self.memory['squares'][spaz]
        team_id = getattr(spaz, 'team_id', None)
        if team_id is not None and team_id in self.memory['kings']:
            if getattr(spaz, 'is_master', False):
                return self.memory['kings'][team_id]
        if spaz.node:
            px, _, pz = spaz.node.position
            return (round(px, 1), round(pz, 1))
        return None

    def get_spaz_at_square(self, sq):
        target_pt = (round(sq[0], 1), round(sq[1], 1))
        for team in self.memory['spazzes'].values():
            for b in team:
                if b and b.node and b.is_alive() and not getattr(b, 'is_dead', False):
                    b_sq = self.memory['squares'].get(b)
                    if b_sq and (round(b_sq[0], 1), round(b_sq[1], 1)) == target_pt:
                        return b
                    bx, _, bz = b.node.position
                    if ((bx - target_pt[0]) ** 2 + (bz - target_pt[1]) ** 2) ** 0.5 < 0.5:
                        return b

        for p in self.memory['players'].values():
            if p.actor and p.actor.node and p.actor.is_alive() and not getattr(p.actor, 'is_dead', False):
                ksq = self.memory['kings'].get(p.team.id)
                if ksq and (round(ksq[0], 1), round(ksq[1], 1)) == target_pt:
                    return p.actor
                px, _, pz = p.actor.node.position
                if ((px - target_pt[0]) ** 2 + (pz - target_pt[1]) ** 2) ** 0.5 < 0.5:
                    return p.actor

        for m in self.memory['placeholder_masters'].values():
            if m and m.node and m.is_alive() and not getattr(m, 'is_dead', False):
                ksq = self.memory['kings'].get(m.team_id)
                if ksq and (round(ksq[0], 1), round(ksq[1], 1)) == target_pt:
                    return m
                mx, _, mz = m.node.position
                if ((mx - target_pt[0]) ** 2 + (mz - target_pt[1]) ** 2) ** 0.5 < 0.5:
                    return m

        return None

    def get_spaz_role(self, spaz):
        is_master = getattr(spaz, 'is_master', False) or any(
            p.actor is spaz for p in self.memory['players'].values()
        )
        if is_master:
            return 'king'
        char = getattr(spaz, 'character', '') or ''
        char_lower = char.lower()
        if 'kronk' in char_lower:
            return 'pawn'
        if 'zoe' in char_lower:
            return 'bishop'
        if 'agent' in char_lower or 'johnson' in char_lower:
            return 'rook'
        if 'pixel' in char_lower or 'pixie' in char_lower:
            return 'queen'
        if 'spaz' in char_lower:
            return 'knight'
        return 'pawn'

    def atk(self, spaz):
        d = self.get_spaz_damage(spaz)
        if getattr(spaz, 'gl', False):
            spaz.gl = False
            d = int(d * 2)
            bs.timer(0.6, lambda: spaz.node and setattr(spaz.node, 'boxing_gloves', False))
        return d

    def get_spaz_damage(self, spaz):
        char = (getattr(spaz, 'character', '') or '').lower()
        if 'kronk' in char:
            return 360
        if 'agent' in char or 'johnson' in char:
            return 220
        if 'zoe' in char:
            return 180
        if 'pixel' in char or 'pixie' in char:
            return 140
        if getattr(spaz, 'is_master', False):
            return 260
        if 'spaz' in char:
            return 200
        return 180

    def get_spaz_special(self, spaz):
        char = (getattr(spaz, 'character', '') or '').lower()
        if 'kronk' in char:
            return 'Slam'
        if 'agent' in char or 'johnson' in char:
            return 'Double Hit'
        if 'zoe' in char:
            return 'Curse'
        if 'pixel' in char or 'pixie' in char:
            return 'Charm'
        if getattr(spaz, 'is_master', False):
            return 'Scare'
        if 'spaz' in char:
            return 'Boom'
        return 'Strike'

    def clear_char_overlay(self):
        for n in getattr(self, 'char_overlay_nodes', []):
            if n:
                n.delete()
        self.char_overlay_nodes = []

    def show_char_overlay(self, spaz):
        self.clear_char_overlay()
        if not spaz or not spaz.node:
            return

        is_master = getattr(spaz, 'is_master', False) or any(
            p.actor is spaz for p in self.memory['players'].values()
        ) or any(m is spaz for m in self.memory['placeholder_masters'].values())

        if is_master:
            char_name = spaz.node.name if (spaz.node and spaz.node.name) else 'Master'
            char_type = getattr(spaz, 'character', 'Spaz')
            name_color = spaz.node.name_color if (spaz.node and hasattr(
                spaz.node, 'name_color') and spaz.node.name_color) else (1.0, 1.0, 1.0)
        else:
            char_name = spaz.character if hasattr(spaz, 'character') else 'Spaz'
            char_type = char_name
            team_id = getattr(spaz, 'team_id', 0)
            name_color = (1.0, 1.0, 1.0)
            if player := self.memory['players'].get(team_id):
                if player.actor and player.actor.node and hasattr(player.actor.node, 'name_color') and player.actor.node.name_color:
                    name_color = player.actor.node.name_color
            elif m := self.memory['placeholder_masters'].get(team_id):
                if m.node and hasattr(m.node, 'name_color') and m.node.name_color:
                    name_color = m.node.name_color
            elif team_id in self.memory['swap']:
                name_color = self.memory['swap'][team_id][1]

        hp = max(0, getattr(spaz, 'hitpoints', 1000))
        atk = self.get_spaz_damage(spaz)
        special = self.get_spaz_special(spaz)

        team_id = getattr(spaz, 'team_id', 0)
        base_color = self.get_team_color(team_id)
        safe_color = tuple(spaz.node.color) if spaz.node else (1.0, 1.0, 1.0)
        safe_highlight = tuple(spaz.node.highlight) if spaz.node else tuple(base_color)

        bg = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('white'),
                'absolute_scale': True,
                'attach': 'bottomCenter',
                'position': (0, 75),
                'scale': (580, 105),
                'color': (0.05, 0.05, 0.05),
                'opacity': 0.0,
            }
        )
        bs.animate(bg, 'opacity', {0.0: 0.0, 0.2: 0.8})

        icon_tex = icon_mask_tex = None
        if is_master:
            plr = getattr(spaz, 'source_player', None) or self.memory['players'].get(team_id)
            if plr:
                try:
                    info = plr.get_icon()
                    icon_tex = info['texture']
                    icon_mask_tex = info['tint_texture']
                    char_type = None
                except Exception:
                    icon_tex = icon_mask_tex = None
        if icon_tex is None:
            try:
                appearance = bs.app.classic.spaz_appearances.get(
                    char_type) or bs.app.classic.spaz_appearances['Spaz']
                icon_tex = bs.gettexture(appearance.icon_texture)
                icon_mask_tex = bs.gettexture(appearance.icon_mask_texture)
            except Exception:
                icon_tex = bs.gettexture('spazIcon')
                icon_mask_tex = bs.gettexture('spazIconColorMask')

        border = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('characterIconMask'),
                'absolute_scale': True,
                'attach': 'bottomCenter',
                'position': (-215, 85),
                'scale': (68, 68),
                'color': safe_highlight,
                'opacity': 0.0,
            }
        )
        bs.animate(border, 'opacity', {0.0: 0.0, 0.2: 1.0})

        char_pic = bs.newnode(
            'image',
            attrs={
                'texture': icon_tex,
                'tint_texture': icon_mask_tex,
                'tint_color': safe_color,
                'tint2_color': safe_highlight,
                'mask_texture': bs.gettexture('characterIconMask'),
                'absolute_scale': True,
                'attach': 'bottomCenter',
                'position': (-215, 85),
                'scale': (64, 64),
                'opacity': 0.0,
            }
        )
        bs.animate(char_pic, 'opacity', {0.0: 0.0, 0.2: 1.0})

        t_name = bs.newnode(
            'text',
            attrs={
                'text': char_name,
                'scale': 0.85,
                'v_attach': 'bottom',
                'h_attach': 'center',
                'h_align': 'center',
                'v_align': 'center',
                'position': (-215, 42),
                'color': name_color,
                'opacity': 0.0,
            }
        )
        bs.animate(t_name, 'opacity', {0.0: 0.0, 0.2: 1.0})

        hp_icon = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('powerupHealth'),
                'absolute_scale': True,
                'attach': 'bottomCenter',
                'position': (-80, 90),
                'scale': (28, 28),
                'opacity': 0.0,
            }
        )
        bs.animate(hp_icon, 'opacity', {0.0: 0.0, 0.2: 1.0})

        bar_w = 220.0
        bar_h = 14.0
        bx = 60.0
        by = 90.0

        bar_red = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('white'),
                'absolute_scale': True,
                'attach': 'bottomCenter',
                'position': (bx, by),
                'scale': (bar_w, bar_h),
                'color': (0.6, 0.15, 0.15),
                'opacity': 0.0,
            }
        )
        bs.animate(bar_red, 'opacity', {0.0: 0.0, 0.2: 0.9})

        hp_frac = max(0.0, min(1.0, hp / 1000.0))
        gw = bar_w * hp_frac
        gx = bx - (bar_w - gw) / 2.0

        bar_green = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('white'),
                'absolute_scale': True,
                'attach': 'bottomCenter',
                'position': (gx, by),
                'scale': (max(0.001, gw), bar_h),
                'color': (0.15, 0.85, 0.15),
                'opacity': 0.0,
            }
        )
        if hp_frac > 0:
            bs.animate(bar_green, 'opacity', {0.0: 0.0, 0.2: 0.95})

        t_atk = bs.newnode(
            'text',
            attrs={
                'text': f'{Strings.ATTACK}: {atk}',
                'scale': 0.85,
                'v_attach': 'bottom',
                'h_attach': 'center',
                'h_align': 'left',
                'v_align': 'center',
                'position': (-80, 55),
                'color': (0.9, 0.9, 0.9),
                'opacity': 0.0,
            }
        )
        bs.animate(t_atk, 'opacity', {0.0: 0.0, 0.2: 1.0})

        spec_icon = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('buttonBomb'),
                'absolute_scale': True,
                'attach': 'bottomCenter',
                'position': (85, 55),
                'scale': (26, 26),
                'color': (1.0, 0.2, 0.2),
                'opacity': 0.0,
            }
        )
        bs.animate(spec_icon, 'opacity', {0.0: 0.0, 0.2: 1.0})

        t_spec = bs.newnode(
            'text',
            attrs={
                'text': f'{Strings.SPECIAL_POWER}: {special}',
                'scale': 0.85,
                'v_attach': 'bottom',
                'h_attach': 'center',
                'h_align': 'left',
                'v_align': 'center',
                'position': (105, 55),
                'color': (1.0, 0.2, 0.2),
                'opacity': 0.0,
            }
        )
        bs.animate(t_spec, 'opacity', {0.0: 0.0, 0.2: 1.0})

        self.char_overlay_nodes = [bg, border, char_pic, t_name,
                                   hp_icon, bar_red, bar_green, t_atk, spec_icon, t_spec]

    def compute_moves_and_attacks(self, spaz):
        cur_sq = self.get_spaz_square(spaz)
        if not cur_sq:
            return [], []

        team_id = getattr(spaz, 'team_id', None)
        if team_id is None:
            return [], []

        role = self.get_spaz_role(spaz)
        sx, sz = cur_sq

        moves = []
        attacks = []

        if role == 'pawn':
            side = 1 if self.map.defs.points[f'spawn{team_id+1}'][2] > 0 else -1
            dz = -1.0 if side > 0 else 1.0

            fwd_sq = (round(sx, 1), round(sz + dz, 1))
            if -3.5 <= fwd_sq[0] <= 3.5 and -3.5 <= fwd_sq[1] <= 3.5:
                occupant = self.get_spaz_at_square(fwd_sq)
                if occupant is None:
                    moves.append(fwd_sq)

            for dx in (-1.0, 1.0):
                diag_sq = (round(sx + dx, 1), round(sz + dz, 1))
                if -3.5 <= diag_sq[0] <= 3.5 and -3.5 <= diag_sq[1] <= 3.5:
                    occupant = self.get_spaz_at_square(diag_sq)
                    if occupant and getattr(occupant, 'team_id', None) != team_id:
                        if not any(a[0] == diag_sq for a in attacks):
                            attacks.append((diag_sq, occupant))

        elif role == 'knight':
            offsets = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
            for dx, dz in offsets:
                tgt = (round(sx + dx, 1), round(sz + dz, 1))
                if -3.5 <= tgt[0] <= 3.5 and -3.5 <= tgt[1] <= 3.5:
                    occupant = self.get_spaz_at_square(tgt)
                    if occupant is None:
                        moves.append(tgt)
                    elif getattr(occupant, 'team_id', None) != team_id:
                        attacks.append((tgt, occupant))

        elif role in ('rook', 'bishop', 'queen'):
            dirs = []
            if role in ('rook', 'queen'):
                dirs.extend([(1, 0), (-1, 0), (0, 1), (0, -1)])
            if role in ('bishop', 'queen'):
                dirs.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])

            for dx, dz in dirs:
                for step in range(1, 8):
                    tgt = (round(sx + dx * step, 1), round(sz + dz * step, 1))
                    if not (-3.5 <= tgt[0] <= 3.5 and -3.5 <= tgt[1] <= 3.5):
                        break
                    occupant = self.get_spaz_at_square(tgt)
                    if occupant is None:
                        moves.append(tgt)
                    else:
                        if getattr(occupant, 'team_id', None) != team_id:
                            attacks.append((tgt, occupant))
                        break

        elif role == 'king':
            for dx in (-1.0, 0.0, 1.0):
                for dz in (-1.0, 0.0, 1.0):
                    if dx == 0 and dz == 0:
                        continue
                    tgt = (round(sx + dx, 1), round(sz + dz, 1))
                    if -3.5 <= tgt[0] <= 3.5 and -3.5 <= tgt[1] <= 3.5:
                        occupant = self.get_spaz_at_square(tgt)
                        if occupant is None:
                            moves.append(tgt)
                        elif getattr(occupant, 'team_id', None) != team_id:
                            attacks.append((tgt, occupant))

        return moves, attacks

    def select_spaz(self, spaz):
        self.clear_selection()
        if not spaz or not spaz.node or not spaz.is_alive() or getattr(spaz, 'is_dead', False):
            return
        if self.is_on_cooldown(spaz):
            bs.getsound('block').play(position=spaz.node.position if spaz.node else None)
            return

        self.selected_spaz = spaz

        bs.getsound('gunCocking').play(position=spaz.node.position)
        spaz.on_jump_release()
        spaz.on_jump_press()
        _ts = ref(spaz)
        self.memory['timers'][f'jump_rel_{id(spaz)}'] = bs.Timer(
            0.1,
            lambda: _ts() and _ts().node and _ts().on_jump_release()
        )

        self.update_legend('selected')
        self.show_char_overlay(spaz)

        my_team_id = getattr(spaz, 'team_id', None)
        moves, attacks = self.compute_moves_and_attacks(spaz)

        self.valid_move_tiles = moves
        self.valid_attack_tiles = [a[0] for a in attacks]

        col = self.get_team_color(my_team_id)
        neon_col = self.neon(*col)
        for sq in moves:
            if node := self.map.fills.get((round(sq[0], 1), round(sq[1], 1))):
                node.color = neon_col
                node.opacity = 0.7
                node.size = (0.63,)
                self.move_highlighted_tiles.append(sq)

        for sq, enemy in attacks:
            if node := self.map.fills.get((round(sq[0], 1), round(sq[1], 1))):
                c_ours = self.get_team_color(my_team_id)
                c_enemy = self.get_team_color(getattr(enemy, 'team_id', None))
                getattr(enemy, 'is_master', False) and self.glows.append(node := bs.newnode('locator', attrs={'shape': 'circle', 'position': (
                    sq[0], 0.007, sq[1]), 'size': (0.9,), 'color': c_ours, 'opacity': 0.0, 'additive': True, 'draw_beauty': True}))
                self.attack_anims += loop_array(node, 'color', 3,
                                                {0.0: c_ours, 0.3: c_enemy, 0.6: c_ours})
                self.attack_anims.append(bs.animate(
                    node, 'opacity', {0.0: 0.0, 0.125: 0.8, 0.25: 0.0}, loop=True))
                self.attack_highlighted_tiles.append(sq)

    def clear_move_highlights(self):
        kill_anims(self.attack_anims)
        self.attack_anims.clear()
        for sq in self.move_highlighted_tiles:
            pt = (round(sq[0], 1), round(sq[1], 1))
            if node := self.map.fills.get(pt):
                owner_tid = None
                for tid, ksq in self.memory['kings'].items():
                    if (round(ksq[0], 1), round(ksq[1], 1)) == pt:
                        owner_tid = tid
                        break
                if owner_tid is not None:
                    self.set_master_tile(sq, self.neon(
                        *self.get_team_color(owner_tid)), active=True)
                elif any((round(s[0], 1), round(s[1], 1)) == pt for s in self.memory['squares'].values()):
                    for p, s in self.memory['squares'].items():
                        if (round(s[0], 1), round(s[1], 1)) == pt:
                            c = self.get_team_color(p.team_id)
                            node.opacity = 0.7
                            node.color = c
                            node.shape = 'circle'
                            node.size = (0.9,)
                            if inner := self.map.inner_fills.get(pt):
                                inner.opacity = 0.0
                            break
                else:
                    node.shape = 'circle'
                    node.size = (0.9,)
                    bs.animate(node, 'opacity', {0: node.opacity, 0.2: 0.0})
                    if inner := self.map.inner_fills.get(pt):
                        inner.opacity = 0.0

        for sq in self.attack_highlighted_tiles:
            pt = (round(sq[0], 1), round(sq[1], 1))
            if node := self.map.fills.get(pt):
                owner_tid = None
                for tid, ksq in self.memory['kings'].items():
                    if (round(ksq[0], 1), round(ksq[1], 1)) == pt:
                        owner_tid = tid
                        break
                if owner_tid is not None:
                    self.set_master_tile(sq, self.neon(
                        *self.get_team_color(owner_tid)), active=True)
                elif any((round(s[0], 1), round(s[1], 1)) == pt for s in self.memory['squares'].values()):
                    for p, s in self.memory['squares'].items():
                        if (round(s[0], 1), round(s[1], 1)) == pt:
                            c = self.get_team_color(p.team_id)
                            node.opacity = 0.7
                            node.color = c
                            node.shape = 'circle'
                            node.size = (0.9,)
                            if inner := self.map.inner_fills.get(pt):
                                inner.opacity = 0.0
                            break
                else:
                    node.shape = 'circle'
                    node.size = (0.9,)
                    bs.animate(node, 'opacity', {0: node.opacity, 0.2: 0.0})
                    if inner := self.map.inner_fills.get(pt):
                        inner.opacity = 0.0

        self.move_highlighted_tiles.clear()
        self.attack_highlighted_tiles.clear()
        [n.delete() for n in self.glows]
        self.glows.clear()

    def clear_selection(self):
        if self.selected_spaz and self.selected_spaz.node:
            self.selected_spaz.on_jump_release()
        self.clear_char_overlay()
        self.clear_move_highlights()
        self.selected_spaz = None
        self.valid_move_tiles = []
        self.valid_attack_tiles = []
        if self.turn_active:
            self.update_legend('unselected')

    def switch_turn(self):
        if self.game_over:
            return
        prev_team_id = self.current_turn_team_id
        self.end_clock(prev_team_id)
        if prev_team_id is not None:
            self.on_team_turn_end(prev_team_id)
        next_team_id = 1 if self.current_turn_team_id == 0 else 0
        self.dpu()
        self.start_turn(next_team_id)

    def dpu(self):
        if not self.powerups:
            return
        bx = self.memory['boxes']
        for k in [k for k, r in bx.items() if not (r() and r().node)]:
            del bx[k]
        ag = self.memory['bage']
        for k in list(bx):
            ag[k] = ag.get(k, 0) + 1
            if ag[k] >= 3:
                b = bx.pop(k)()
                ag.pop(k, None)
                if b and b.node:
                    PowerupBoxFactory.get().powerdown_sound.play(position=b.node.position)
                    b.handlemessage(bs.DieMessage())
        if len(bx) >= 1 or random() > 0.1:
            return
        used = {tuple(round(v, 1) for v in sq) for sq in self.memory['squares'].values()}
        used |= {tuple(round(v, 1) for v in sq) for sq in self.memory['kings'].values()}
        used |= {(round(r().node.position[0], 1), round(
            r().node.position[2], 1)) for r in bx.values()}
        tl = [(x - 3.5, z - 3.5) for x in range(8) for z in range(8)]
        tl = [t for t in tl if (round(t[0], 1), round(t[1], 1)) not in used]
        if not tl:
            return
        w = [exp(-(x * x + z * z) / 9.0) for x, z in tl]
        x, z = choices(tl, w)[0]
        kind = choices(['health', 'punch'], [3, 2])[0]
        b = PowerupBox(position=(x, 1.2, z), poweruptype=kind, expire=False).autoretain()
        bx[id(b)] = ref(b)
        ag[id(b)] = 0
        bs.getsound('dingSmallHigh').play(position=(x, 1.2, z))
        _b, k = ref(b), f'bxl{id(b)}'
        tm = self.memory['timers']

        def lock():
            n = _b() and _b().node
            if not n:
                tm[k] = None
                return
            v = n.velocity
            n.position = (x, n.position[1], z)
            n.velocity = (0.0, v[1], 0.0)
        tm[k] = bs.Timer(0.03, lock, repeat=True)

    def stop_all_move_repeats(self):
        self.stop_move_repeat('x')
        self.stop_move_repeat('z')
        self.move_state['x_held'] = 0
        self.move_state['z_held'] = 0

    def stop_move_repeat(self, axis):
        self.memory['timers'][f'repeat_delay_{axis}'] = None
        self.memory['timers'][f'repeat_{axis}'] = None

    def start_move_repeat(self, axis, dx, dz):
        self.stop_move_repeat(axis)
        _s = ref(self)

        def repeat_step():
            s = _s()
            if not s or not s.turn_active or s.pending_action is not None:
                if s:
                    s.stop_all_move_repeats()
                return
            s.move_selector(dx, dz)

        def initial_delay():
            s = _s()
            if not s or not s.turn_active or s.pending_action is not None:
                if s:
                    s.stop_all_move_repeats()
                return
            s.memory['timers'][f'repeat_{axis}'] = bs.Timer(0.18, repeat_step, repeat=True)
        self.memory['timers'][f'repeat_delay_{axis}'] = bs.Timer(0.35, initial_delay)

    def handle_grab_press(self, player):
        if not self.can_control(player):
            return

        active_team_id = self.current_turn_team_id
        sel_pos = self.team_selector_pos.get(active_team_id)
        if not sel_pos:
            return
        sel_sq = (sel_pos[0], sel_pos[1])

        if self.selected_spaz is None:
            occupant = self.get_spaz_at_square(sel_sq)
            if occupant and getattr(occupant, 'team_id', None) == active_team_id and not getattr(occupant, 'is_dead', False):
                if self.is_on_cooldown(occupant):
                    bs.getsound('block').play(position=(sel_pos[0], 0, sel_pos[1]))
                    return
                self.select_spaz(occupant)
            else:
                bs.getsound('block').play(position=(sel_pos[0], 0, sel_pos[1]))
            return

        spaz = self.selected_spaz

        cur_spaz_sq = self.get_spaz_square(spaz)
        if cur_spaz_sq and (round(cur_spaz_sq[0], 1), round(cur_spaz_sq[1], 1)) == sel_sq:
            self.clear_selection()
            bs.getsound('laser').play(position=spaz.node.position if spaz.node else None)
            return

        # attack
        if sel_sq in self.valid_attack_tiles:
            victim = self.get_spaz_at_square(sel_sq)
            old_sq = self.get_spaz_square(spaz)
            self.st[active_team_id]['atk'] += 1
            self.turn_active = False
            self.stop_all_move_repeats()
            self.hide_team_selector(active_team_id)
            self.hide_legend()

            bs.getsound('gunCocking').play(position=spaz.node.position if spaz.node else None)
            if spaz and spaz.node and getattr(spaz.node, 'jump_sounds', None):
                choice(spaz.node.jump_sounds).play()

            self.memory['lm'][getattr(spaz, 'team_id', 0)] = ref(spaz)
            self.pending_action = {
                'type': 'attack',
                'spaz': spaz,
                'start_sq': old_sq,
                'target_sq': sel_sq,
                'victim': victim,
                'state': 'moving_to_target'
            }
            self.clear_selection()
            return

        # move
        if sel_sq in self.valid_move_tiles:
            old_sq = self.get_spaz_square(spaz)
            is_master = getattr(spaz, 'is_master', False) or any(
                p.actor is spaz for p in self.memory['players'].values()
            ) or any(m is spaz for m in self.memory['placeholder_masters'].values())

            if old_sq:
                if is_master:
                    self.set_master_tile(old_sq, (1, 1, 1), active=False)
                else:
                    self.highlight_tile(old_sq, active=False)

            if is_master:
                self.memory['kings'][spaz.team_id] = sel_sq
                self.set_master_tile(sel_sq, self.neon(
                    *self.get_team_color(spaz.team_id)), active=True)
            else:
                self.memory['squares'][spaz] = sel_sq
                self.highlight_tile(
                    sel_sq,
                    color=self.get_team_color(spaz.team_id),
                    active=True
                )

            bs.getsound('gunCocking').play(position=spaz.node.position if spaz.node else None)
            if spaz and spaz.node and getattr(spaz.node, 'jump_sounds', None):
                choice(spaz.node.jump_sounds).play()

            self.st[active_team_id]['mov'] += 1
            self.turn_active = False
            self.stop_all_move_repeats()
            self.hide_team_selector(active_team_id)
            self.hide_legend()
            self.memory['lm'][getattr(spaz, 'team_id', 0)] = ref(spaz)
            self.pending_action = {
                'type': 'move',
                'spaz': spaz,
                'target_sq': sel_sq,
                'state': 'moving'
            }
            self.clear_selection()
            return

        # switch
        occupant = self.get_spaz_at_square(sel_sq)
        if occupant and getattr(occupant, 'team_id', None) == active_team_id and not getattr(occupant, 'is_dead', False):
            if self.is_on_cooldown(occupant):
                bs.getsound('block').play(position=(sel_pos[0], 0, sel_pos[1]))
                return
            self.clear_selection()
            self.select_spaz(occupant)
            return

        self.clear_selection()
        bs.getsound('block').play(position=(sel_pos[0], 0, sel_pos[1]))

    def handle_punch_press(self, player):
        if not self.can_control(player):
            return

        sel_pos = self.team_selector_pos.get(self.current_turn_team_id)
        if not sel_pos:
            return
        sel_sq = (sel_pos[0], sel_pos[1])

        if self.selected_spaz is None:
            bs.getsound('block').play(position=(sel_pos[0], 0, sel_pos[1]))
            return

        occupant = self.get_spaz_at_square(sel_sq)
        if occupant is None:
            self.clear_selection()
            bs.getsound('block').play(position=(sel_pos[0], 0, sel_pos[1]))
            return

        if sel_sq in self.valid_attack_tiles:
            self.handle_grab_press(player)
            return

        spaz = self.selected_spaz
        if spaz and spaz.node and spaz.is_alive():
            px, _, pz = spaz.node.position
            dx = sel_sq[0] - px
            dz = sel_sq[1] - pz
            spaz.on_move_left_right(dx)
            spaz.on_move_up_down(-dz)
            spaz.on_punch_press()
            _ts = ref(spaz)
            self.memory['timers'][f'punch_rel_{id(spaz)}'] = bs.Timer(
                0.15,
                lambda: _ts() and _ts().node and (_ts().on_punch_release(),
                                                  _ts().on_move_left_right(0), _ts().on_move_up_down(0))
            )

        self.clear_selection()

    def handle_bomb_press(self, player):
        if not self.can_control(player):
            return

        sel_pos = self.team_selector_pos.get(self.current_turn_team_id)
        if not sel_pos:
            return
        sel_sq = (sel_pos[0], sel_pos[1])

        if self.selected_spaz is None:
            bs.getsound('block').play(position=(sel_pos[0], 0, sel_pos[1]))
            return

        spaz = self.selected_spaz
        target_spaz = self.get_spaz_at_square(sel_sq)

        is_master = getattr(spaz, 'is_master', False) or any(
            p.actor is spaz for p in self.memory['players'].values()
        ) or any(m is spaz for m in self.memory['placeholder_masters'].values())

        valid = False
        if is_master:
            if target_spaz and getattr(target_spaz, 'team_id', None) != spaz.team_id and not getattr(target_spaz, 'is_dead', False):
                valid = True
        else:
            if sel_sq in self.valid_attack_tiles and target_spaz and getattr(target_spaz, 'team_id', None) != spaz.team_id:
                valid = True

        if not valid or not target_spaz:
            bs.getsound('block').play(position=(sel_pos[0], 0, sel_pos[1]))
            return

        old_sq = self.get_spaz_square(spaz)
        self.st[self.current_turn_team_id]['spc'] += 1
        self.turn_active = False
        self.stop_all_move_repeats()
        self.hide_team_selector(self.current_turn_team_id)
        self.hide_legend()

        bs.getsound('gunCocking').play(position=spaz.node.position if spaz.node else None)
        if spaz and spaz.node and getattr(spaz.node, 'jump_sounds', None):
            choice(spaz.node.jump_sounds).play()

        self.memory['lm'][getattr(spaz, 'team_id', 0)] = ref(spaz)
        self.pending_action = {
            'type': 'special',
            'spaz': spaz,
            'start_sq': old_sq,
            'target_sq': sel_sq,
            'victim': target_spaz,
            'state': 'moving_to_target'
        }
        if self.get_spaz_role(spaz) == 'knight':
            self.pending_action['state'] = 'bwk'
            self.bbg(self.pending_action)
        self.clear_selection()

    def move_selector(self, dx, dz):
        if not self.turn_active or self.pending_action is not None:
            return
        tid = self.current_turn_team_id
        if tid is None:
            return
        node = self.team_selectors.get(tid)
        pos = self.team_selector_pos.get(tid)
        if not node or not pos:
            return

        nx = max(-3.5, min(3.5, pos[0] + dx * 1.0))
        nz = max(-3.5, min(3.5, pos[1] + dz * 1.0))
        nx = round(nx, 1)
        nz = round(nz, 1)

        if nx == pos[0] and nz == pos[1]:
            return

        pos[0] = nx
        pos[1] = nz

        cur_pos = node.position
        target_pos = (pos[0], 0.6, pos[1])

        if tid in self.team_selector_anim and self.team_selector_anim[tid]:
            try:
                self.team_selector_anim[tid].delete()
            except Exception:
                pass
            self.team_selector_anim[tid] = None

        self.team_selector_anim[tid] = bs.animate_array(
            node,
            'position',
            3,
            {0.0: cur_pos, 0.08: target_pos}
        )

        _s = ref(self)

        def cleanup_lerp(_tid=tid, _tgt=target_pos):
            s = _s()
            if not s:
                return
            if _tid in s.team_selector_anim and s.team_selector_anim[_tid]:
                try:
                    s.team_selector_anim[_tid].delete()
                except Exception:
                    pass
                s.team_selector_anim[_tid] = None
            sel_node = s.team_selectors.get(_tid)
            if sel_node:
                sel_node.position = _tgt

        s_timer_key = f'selector_lerp_{tid}'
        self.memory['timers'][s_timer_key] = bs.Timer(0.08, cleanup_lerp)

    def handle_move_left_right(self, player, val):
        if not self.can_control(player):
            self.stop_move_repeat('x')
            self.move_state['x_held'] = 0
            return
        if val > 0.5:
            dir_x = 1
        elif val < -0.5:
            dir_x = -1
        else:
            dir_x = 0

        if dir_x != self.move_state['x_held']:
            self.move_state['x_held'] = dir_x
            if dir_x != 0:
                self.move_selector(dir_x, 0)
                self.start_move_repeat('x', dir_x, 0)
            else:
                self.stop_move_repeat('x')

    def handle_move_up_down(self, player, val):
        if not self.can_control(player):
            self.stop_move_repeat('z')
            self.move_state['z_held'] = 0
            return
        if val > 0.5:
            dir_z = -1
        elif val < -0.5:
            dir_z = 1
        else:
            dir_z = 0

        if dir_z != self.move_state['z_held']:
            self.move_state['z_held'] = dir_z
            if dir_z != 0:
                self.move_selector(0, dir_z)
                self.start_move_repeat('z', 0, dir_z)
            else:
                self.stop_move_repeat('z')

    def retain(self, piece):
        cnt = [0]
        _s, _b = ref(self), ref(piece)

        def tick():
            cnt[0] += 1
            s, b = _s(), _b()
            if not s or not b:
                return
            if not b.node or not b.is_alive() or getattr(b, 'is_dead', False):
                s.memory['timers'][f'retain_{id(b)}'] = None
                if old_sq := s.memory['squares'].pop(b, None):
                    s.highlight_tile(old_sq, active=False)
                return
            if getattr(b, 'claimed_by', None) is not None or not s.playing:
                s.memory['timers'][f'retain_{id(b)}'] = None
                return

            team_id = getattr(b, 'team_id', None)
            if team_id is None:
                for tid, p in s.memory['players'].items():
                    if p.actor is b:
                        team_id = tid
                        b.team_id = tid
                        break
            if team_id is None:
                return

            pa = s.pending_action

            # drop
            for p in s.memory['players'].values():
                if p.actor and p.actor.node and p.actor.node.hold_node == b.node and p.team.id != team_id:
                    if not (pa and pa.get('type') == 'special' and pa.get('state') == 'holding'):
                        p.actor.node.hold_node = None
            # held
            holders = [
                p.actor for p in s.memory['players'].values() if p.actor and p.actor.node
            ] + [
                bot for team in s.memory['spazzes'].values() for bot in team if bot and bot.node
            ] + [
                m for m in s.memory['placeholder_masters'].values() if m and m.node
            ]
            if any(getattr(h.node, 'hold_node', None) == b.node for h in holders):
                if not (pa and pa.get('victim') is b and pa.get('type') == 'special'):
                    if cnt[0] % 5 == 0:
                        b.on_jump_release()
                        b.on_jump_press()
                        b.on_jump_release()
                b.on_move_up_down(0)
                b.on_move_left_right(0)
                return

            px, _, pz = b.node.position
            side = 1 if s.map.defs.points[f'spawn{team_id+1}'][2] > 0 else -1
            is_master = getattr(b, 'is_master', False) or any(p.actor is b for p in s.memory['players'].values(
            )) or any(m is b for m in s.memory['placeholder_masters'].values())

            # active
            if pa and pa.get('spaz') is b:
                p_type = pa.get('type')
                p_state = pa.get('state')
                char = (getattr(b, 'character', '') or '').lower()
                has_run = any(k in char for k in ('agent', 'johnson', 'zoe', 'pixel', 'pixie'))

                if p_type == 'move':
                    sq = pa.get('target_sq')
                    tgt = s.path(b, (px, pz), sq)
                    dx, dz = tgt[0] - px, tgt[1] - pz
                    dist = (dx * dx + dz * dz) ** 0.5
                    if dist > 0.08 or tgt != sq:
                        spd = (3.0 if dist > 0.8 else 1.2) if has_run else (
                            1.4 if dist > 0.8 else 1.0)
                        b.on_move_left_right(max(-1.0, min(1.0, dx * spd)))
                        b.on_move_up_down(max(-1.0, min(1.0, -dz * spd)))
                    else:
                        if p_state == 'moving':
                            pa['state'] = 'arrived'
                            b.on_move_left_right(0)
                            b.on_move_up_down(0)

                            def finish_move():
                                s.pending_action = None
                                s.switch_turn()
                            s.memory['timers']['turn_delay'] = bs.Timer(0.2, finish_move)
                    return

                elif p_type == 'attack':
                    if p_state == 'moving_to_target':
                        sq = pa.get('target_sq')
                        victim = pa.get('victim')
                        vx, vz = (victim.node.position[0], victim.node.position[2]) if (
                            victim and victim.node) else (sq[0], sq[1])
                        dx, dz = vx - px, vz - pz
                        col_dist = (dx * dx + dz * dz) ** 0.5

                        if col_dist > 0.65:
                            tgt = s.path(b, (px, pz), sq)
                            tdx, tdz = tgt[0] - px, tgt[1] - pz
                            spd = 3.5 if has_run else 2.0
                            b.on_move_left_right(max(-1.0, min(1.0, tdx * spd)))
                            b.on_move_up_down(max(-1.0, min(1.0, -tdz * spd)))
                        else:
                            pa['state'] = 'punching'
                            b.on_move_left_right(dx)
                            b.on_move_up_down(-dz)
                            b.on_punch_press()

                            def execute_hit():
                                b.on_punch_release()
                                b.on_move_left_right(0)
                                b.on_move_up_down(0)
                                v = pa.get('victim')
                                if v and v.node and v.is_alive():
                                    dmg = s.atk(b)
                                    hit = bs.HitMessage(
                                        pos=v.node.position,
                                        velocity=(0.0, 0.0, 0.0),
                                        magnitude=0.0,
                                        velocity_magnitude=0.0,
                                        radius=1.0,
                                        srcnode=b.node,
                                        force_direction=(0.0, 1.0, 0.0),
                                        hit_type='attack',
                                    )
                                    setattr(hit, 'is_backend', True)
                                    setattr(hit, 'custom_damage', dmg)
                                    v.handlemessage(hit)
                                pa['state'] = 'returning'

                            s.memory['timers']['punch_hit'] = bs.Timer(0.2, execute_hit)
                        return

                    elif p_state == 'returning':
                        sq = pa.get('start_sq')
                        tgt = s.path(b, (px, pz), sq)
                        dx, dz = tgt[0] - px, tgt[1] - pz
                        dist = (dx * dx + dz * dz) ** 0.5
                        if dist > 0.08 or tgt != sq:
                            spd = (3.0 if dist > 0.8 else 1.2) if has_run else (
                                1.4 if dist > 0.8 else 1.0)
                            b.on_move_left_right(max(-1.0, min(1.0, dx * spd)))
                            b.on_move_up_down(max(-1.0, min(1.0, -dz * spd)))
                        else:
                            pa['state'] = 'arrived'
                            b.on_move_left_right(0)
                            b.on_move_up_down(0)

                            def finish_attack():
                                s.pending_action = None
                                s.switch_turn()
                            s.memory['timers']['turn_delay'] = bs.Timer(0.2, finish_attack)
                        return

                elif p_type == 'special':
                    sq = pa.get('target_sq')
                    victim = pa.get('victim')
                    vx, vz = (victim.node.position[0], victim.node.position[2]) if (
                        victim and victim.node) else (sq[0], sq[1])
                    dx, dz = vx - px, vz - pz
                    col_dist = (dx * dx + dz * dz) ** 0.5

                    if p_state == 'moving_to_target':
                        if col_dist > 0.65:
                            tgt = s.path(b, (px, pz), sq)
                            tdx, tdz = tgt[0] - px, tgt[1] - pz
                            spd = 3.5 if has_run else 2.0
                            b.on_move_left_right(max(-1.0, min(1.0, tdx * spd)))
                            b.on_move_up_down(max(-1.0, min(1.0, -tdz * spd)))
                        else:
                            b.on_move_left_right(0)
                            b.on_move_up_down(0)

                            # kronk
                            if 'kronk' in char:
                                pa['state'] = 'holding'
                                b.node.hold_node = victim.node
                                pa['victim_orig_sq'] = s.get_spaz_square(victim)
                                bs.getsound('corkPop').play(position=b.node.position)

                                walk_dir = -1.0 if side > 0 else 1.0
                                b.on_move_up_down(walk_dir * 0.4)

                                def throw_target():
                                    if b and b.node:
                                        b.on_move_up_down(0)
                                        b.on_move_left_right(0)
                                        b.node.hold_node = None

                                    if victim and victim.node and victim.is_alive():
                                        victim.node.handlemessage(
                                            'impulse',
                                            victim.node.position[0], 0.2, victim.node.position[2],
                                            0, 3.5, walk_dir * 3.0,
                                            8.0, 0, 0, 0, 0, 1.0, 0
                                        )

                                    def on_airtime_fall():
                                        if victim and victim.node and victim.is_alive():
                                            dmg = 480
                                            hit = bs.HitMessage(
                                                pos=victim.node.position,
                                                velocity=(0.0, -8.0, 0.0),
                                                magnitude=30.0,
                                                velocity_magnitude=30.0,
                                                radius=1.0,
                                                srcnode=b.node if b else None,
                                                force_direction=(0.0, -1.0, 0.0),
                                                hit_type='attack',
                                            )
                                            setattr(hit, 'is_backend', True)
                                            setattr(hit, 'custom_damage', dmg)
                                            victim.handlemessage(hit)
                                            bs.emitfx(position=victim.node.position, count=20,
                                                      scale=0.2, spread=0.4, chunk_type='spark')
                                            bs.getsound('punch01').play(
                                                position=victim.node.position)

                                            def sleep_spam():
                                                if pa and pa.get('type') == 'special' and pa.get('state') == 'returning':
                                                    if victim and victim.node and victim.is_alive():
                                                        victim.node.handlemessage(
                                                            'knockout', 1000.0)
                                            s.memory['timers']['kronk_victim_sleep'] = bs.Timer(
                                                0.1, sleep_spam, repeat=True)

                                        pa['state'] = 'returning'

                                    s.memory['timers']['slam_fall'] = bs.Timer(0.3, on_airtime_fall)

                                s.memory['timers']['kronk_throw_wait'] = bs.Timer(2.0, throw_target)

                            # agent
                            elif 'agent' in char or 'johnson' in char:
                                pa['state'] = 'assault_hit1'
                                b.on_move_left_right(dx)
                                b.on_move_up_down(-dz)
                                b.on_punch_press()

                                def execute_hit1():
                                    b.on_punch_release()
                                    b.on_move_left_right(0)
                                    b.on_move_up_down(0)
                                    if victim and victim.node and victim.is_alive():
                                        dmg = s.atk(b)
                                        hit1 = bs.HitMessage(
                                            pos=victim.node.position,
                                            velocity=(0.0, 0.0, 0.0),
                                            magnitude=0.0,
                                            velocity_magnitude=0.0,
                                            radius=1.0,
                                            srcnode=b.node,
                                            force_direction=(0.0, 1.0, 0.0),
                                            hit_type='attack',
                                        )
                                        setattr(hit1, 'is_backend', True)
                                        setattr(hit1, 'custom_damage', dmg)
                                        victim.handlemessage(hit1)

                                    pa['state'] = 'waiting_hit2'

                                    def execute_hit2_press():
                                        if not b or not b.node or not b.is_alive():
                                            pa['state'] = 'returning'
                                            return
                                        pa['state'] = 'assault_hit2'
                                        vx_c, vz_c = (victim.node.position[0], victim.node.position[2]) if (
                                            victim and victim.node) else (sq[0], sq[1])
                                        px_c, _, pz_c = b.node.position
                                        b.on_move_left_right(vx_c - px_c)
                                        b.on_move_up_down(-(vz_c - pz_c))
                                        b.on_punch_press()

                                        def execute_hit2():
                                            b.on_punch_release()
                                            b.on_move_left_right(0)
                                            b.on_move_up_down(0)
                                            if victim and victim.node and victim.is_alive():
                                                dmg = s.atk(b)
                                                hit2 = bs.HitMessage(
                                                    pos=victim.node.position,
                                                    velocity=(0.0, 0.0, 0.0),
                                                    magnitude=0.0,
                                                    velocity_magnitude=0.0,
                                                    radius=1.0,
                                                    srcnode=b.node,
                                                    force_direction=(0.0, 1.0, 0.0),
                                                    hit_type='attack',
                                                )
                                                setattr(hit2, 'is_backend', True)
                                                setattr(hit2, 'custom_damage', dmg)
                                                victim.handlemessage(hit2)

                                            def start_agent_return():
                                                pa['state'] = 'returning'
                                            s.memory['timers']['agent_turn_delay'] = bs.Timer(
                                                0.3, start_agent_return)

                                        s.memory['timers']['agent_p2_rel'] = bs.Timer(
                                            0.18, execute_hit2)

                                    s.memory['timers']['agent_p2_wait'] = bs.Timer(
                                        0.5, execute_hit2_press)

                                s.memory['timers']['agent_p1_rel'] = bs.Timer(0.18, execute_hit1)

                            # pixie
                            elif 'pixel' in char or 'pixie' in char:
                                pa['state'] = 'pixie_casting'
                                b.on_jump_press()
                                b.node.handlemessage('celebrate', 1750)
                                s.memory['timers']['pixie_jrel'] = bs.Timer(
                                    0.2, lambda: b and b.node and b.on_jump_release())
                                bs.getsound('shieldUp').play(position=victim.node.position)

                                def cast_sparks():
                                    if victim and victim.node and victim.is_alive():
                                        bs.emitfx(position=victim.node.position, count=12,
                                                  scale=0.2, spread=0.5, chunk_type='spark')
                                cast_sparks()
                                s.memory['timers']['pixie_fx1'] = bs.Timer(0.5, cast_sparks)
                                s.memory['timers']['pixie_fx2'] = bs.Timer(1.0, cast_sparks)

                                def on_cast_finished():
                                    is_victim_master = getattr(victim, 'is_master', False) or any(
                                        p.actor is victim for p in s.memory['players'].values()
                                    ) or any(m is victim for m in s.memory['placeholder_masters'].values())

                                    if is_victim_master:
                                        if victim and victim.node and victim.is_alive():
                                            px_b, _, pz_b = b.node.position
                                            vx_n, _, vz_n = victim.node.position
                                            victim.on_move_left_right(px_b - vx_n)
                                            victim.on_move_up_down(-(pz_b - vz_n))
                                            victim.on_punch_press()

                                            def finish_counter():
                                                victim.on_punch_release()
                                                victim.on_move_left_right(0)
                                                victim.on_move_up_down(0)
                                                if b and b.node and b.is_alive():
                                                    m_dmg = s.atk(victim)
                                                    hit = bs.HitMessage(
                                                        pos=b.node.position,
                                                        velocity=(0.0, 0.0, 0.0),
                                                        magnitude=0.0,
                                                        velocity_magnitude=0.0,
                                                        radius=1.0,
                                                        srcnode=victim.node,
                                                        force_direction=(0.0, 1.0, 0.0),
                                                        hit_type='attack',
                                                    )
                                                    setattr(hit, 'is_backend', True)
                                                    setattr(hit, 'custom_damage', m_dmg)
                                                    b.handlemessage(hit)
                                                pa['state'] = 'returning'
                                            s.memory['timers']['m_punch_rel'] = bs.Timer(
                                                0.2, finish_counter)
                                    else:
                                        v_tid = getattr(victim, 'team_id', 0)
                                        teammates = []
                                        for bot in s.memory['spazzes'].get(v_tid, []):
                                            if bot and bot.node and bot is not victim and bot.is_alive() and not getattr(bot, 'is_dead', False):
                                                teammates.append(bot)
                                        if plr := s.memory['players'].get(v_tid):
                                            if plr.actor and plr.actor.node and plr.actor is not victim and plr.actor.is_alive() and not getattr(plr.actor, 'is_dead', False):
                                                teammates.append(plr.actor)
                                        elif m := s.memory['placeholder_masters'].get(v_tid):
                                            if m and m.node and m is not victim and m.is_alive() and not getattr(m, 'is_dead', False):
                                                teammates.append(m)

                                        if teammates and victim.node:
                                            vx_n, _, vz_n = victim.node.position
                                            nearest_tm = min(teammates, key=lambda tm: (
                                                (tm.node.position[0]-vx_n)**2 + (tm.node.position[2]-vz_n)**2))
                                            pa['charm_pending'] = True
                                            pa['victim_orig_sq'] = s.get_spaz_square(victim)
                                            pa['nearest_tm'] = nearest_tm
                                        pa['state'] = 'returning'

                                s.memory['timers']['pixie_cast_timer'] = bs.Timer(
                                    2.0, on_cast_finished)

                            # zoe
                            elif 'zoe' in char:
                                pa['state'] = 'zoe_curse'
                                b.on_move_left_right(dx)
                                b.on_move_up_down(-dz)
                                b.on_punch_press()

                                def execute_curse():
                                    b.on_punch_release()
                                    b.on_move_left_right(0)
                                    b.on_move_up_down(0)
                                    if victim and victim.node and victim.is_alive():
                                        dmg = s.atk(b)
                                        hit = bs.HitMessage(
                                            pos=victim.node.position,
                                            velocity=(0.0, 0.0, 0.0),
                                            magnitude=0.0,
                                            velocity_magnitude=0.0,
                                            radius=1.0,
                                            srcnode=b.node,
                                            force_direction=(0.0, 1.0, 0.0),
                                            hit_type='attack',
                                        )
                                        setattr(hit, 'is_backend', True)
                                        setattr(hit, 'custom_damage', dmg)
                                        victim.handlemessage(hit)
                                        bs.emitfx(position=victim.node.position, count=25,
                                                  scale=0.9, spread=0.5, chunk_type='spark')
                                        bs.getsound('shieldDown').play(
                                            position=victim.node.position)
                                        s.apply_cooldown(victim, turns=1)
                                    pa['state'] = 'returning'
                                s.memory['timers']['zoe_curse_hit'] = bs.Timer(0.2, execute_curse)

                            # king
                            elif is_master:
                                pa['state'] = 'king_scaring'
                                scare_dur = 0.4
                                b.node.handlemessage('celebrate', int(scare_dur * 1000))
                                falls = getattr(b.node, 'fall_sounds', None)
                                if falls:
                                    choice(falls).play()

                                v_tid = getattr(victim, 'team_id', 0)
                                v_king_sq = s.memory['kings'].get(
                                    v_tid, (0.5, 3.5 if v_tid == 0 else -3.5))
                                cur_v_sq = s.get_spaz_square(victim)
                                dist_to_king = ((cur_v_sq[0] - v_king_sq[0])
                                                ** 2 + (cur_v_sq[1] - v_king_sq[1])**2)**0.5

                                occupied = {(round(sq[0], 1), round(sq[1], 1)) for p, sq in s.memory['squares'].items(
                                ) if p is not victim and p.is_alive()}
                                occupied.update({(round(k[0], 1), round(k[1], 1))
                                                for k in s.memory['kings'].values()})

                                all_free = [(c - 3.5, r - 3.5) for r in range(8) for c in range(8)
                                            if (round(c - 3.5, 1), round(r - 3.5, 1)) not in occupied]

                                if all_free:
                                    if dist_to_king > 2.0:
                                        new_sq = min(all_free, key=lambda sq: (
                                            (sq[0]-v_king_sq[0])**2 + (sq[1]-v_king_sq[1])**2))
                                    else:
                                        new_sq = max(all_free, key=lambda sq: (
                                            (sq[0]-v_king_sq[0])**2 + (sq[1]-v_king_sq[1])**2))

                                    s.highlight_tile(cur_v_sq, active=False)
                                    s.memory['squares'][victim] = new_sq
                                    s.highlight_tile(
                                        new_sq, color=s.get_team_color(v_tid), active=True)

                                    victim.on_run(1)
                                    v_falls = getattr(victim.node, 'fall_sounds', None)
                                    if v_falls:
                                        choice(v_falls).play()

                                def finish_scare():
                                    pa['state'] = 'returning'
                                s.memory['timers']['scare_dur'] = bs.Timer(scare_dur, finish_scare)

                            else:
                                pa['state'] = 'returning'
                        return

                    elif p_state == 'bwk':
                        if col_dist > 0.65:
                            total = pa.get('btot') or 1.0
                            if not pa.get('bj') and 1.0 - col_dist / total >= 0.3:
                                pa['bj'] = True
                                pa['bjt'] = bs.time()
                                b.on_jump_press()
                                if getattr(b.node, 'jump_sounds', None):
                                    choice(b.node.jump_sounds).play(position=b.node.position)
                                _tb = ref(b)
                                s.memory['timers']['bjr'] = bs.Timer(
                                    0.15, lambda: _tb() and _tb().node and _tb().on_jump_release()
                                )
                            tgt = s.path(b, (px, pz), sq)
                            tdx, tdz = tgt[0] - px, tgt[1] - pz
                            b.on_move_left_right(max(-1.0, min(1.0, tdx * 2.0)))
                            b.on_move_up_down(max(-1.0, min(1.0, -tdz * 2.0)))
                        else:
                            b.on_move_left_right(0)
                            b.on_move_up_down(0)
                            pa['state'] = 'bl'
                        return

                    elif p_state == 'bl':
                        b.on_move_left_right(0)
                        b.on_move_up_down(0)
                        if bs.time() - pa.get('bjt', 0.0) >= 0.4:
                            pa['state'] = 'bbl'
                            s.bexp(pa)
                        return

                    elif p_state == 'returning':
                        sq = pa.get('start_sq')
                        tgt = s.path(b, (px, pz), sq)
                        dx, dz = tgt[0] - px, tgt[1] - pz
                        dist = (dx * dx + dz * dz) ** 0.5
                        if dist > 0.08 or tgt != sq:
                            spd = (3.0 if dist > 0.8 else 1.2) if has_run else (
                                1.4 if dist > 0.8 else 1.0)
                            b.on_move_left_right(max(-1.0, min(1.0, dx * spd)))
                            b.on_move_up_down(max(-1.0, min(1.0, -dz * spd)))
                        else:
                            pa['state'] = 'arrived'
                            b.on_move_left_right(0)
                            b.on_move_up_down(0)

                            s.apply_cooldown(b, turns=2)

                            if pa.get('boom'):
                                pa['state'] = 'bw'
                                return

                            if 'kronk' in char:
                                s.memory['timers']['kronk_victim_sleep'] = None
                                if victim and victim.node and victim.is_alive():
                                    victim.node.handlemessage('knockout', 0.0)
                                    pa['state'] = 'victim_returning_home'
                                    return
                                else:
                                    s.pending_action = None
                                    s.switch_turn()
                                    return

                            if pa.get('charm_pending'):
                                pa['charm_pending'] = False
                                pa['victim_action'] = {
                                    'target': pa.get('nearest_tm'),
                                    'orig_sq': pa.get('victim_orig_sq'),
                                    'state': 'moving_to_tm'
                                }
                                pa['state'] = 'charmed_acting'
                                return

                            def finish_action():
                                s.pending_action = None
                                s.switch_turn()
                            s.memory['timers']['turn_delay'] = bs.Timer(0.2, finish_action)
                        return

                    else:
                        b.on_move_left_right(0)
                        b.on_move_up_down(0)
                        return

            if pa and pa.get('type') == 'special':
                victim = pa.get('victim')
                if pa.get('state') == 'victim_returning_home':
                    if victim and victim.node and victim.is_alive() and not getattr(victim, 'is_dead', False):
                        v_hsq = pa.get('victim_orig_sq')
                        v_px, _, v_pz = victim.node.position
                        if v_hsq:
                            v_step = s.path(victim, (v_px, v_pz), v_hsq)
                            v_dx, v_dz = v_step[0] - v_px, v_step[1] - v_pz
                            v_dist = (v_dx**2 + v_dz**2)**0.5
                            if v_dist > 0.08 or v_step != v_hsq:
                                victim.on_move_left_right(max(-1.0, min(1.0, v_dx * 2.0)))
                                victim.on_move_up_down(max(-1.0, min(1.0, -v_dz * 2.0)))
                            else:
                                victim.on_move_left_right(0)
                                victim.on_move_up_down(0)
                                s.pending_action = None
                                s.switch_turn()
                    else:
                        s.pending_action = None
                        s.switch_turn()

                va = pa.get('victim_action')
                if va and victim and victim.node and victim.is_alive() and not getattr(victim, 'is_dead', False):
                    v_state = va.get('state')
                    v_tgt_node = va.get('target')
                    v_px, _, v_pz = victim.node.position
                    if v_state == 'moving_to_tm':
                        if v_tgt_node and v_tgt_node.node and v_tgt_node.is_alive():
                            tx, _, tz = v_tgt_node.node.position
                            tdist = ((tx - v_px)**2 + (tz - v_pz)**2)**0.5
                            if tdist > 0.65:
                                v_step = s.path(victim, (v_px, v_pz), (tx, tz))
                                v_dx, v_dz = v_step[0] - v_px, v_step[1] - v_pz
                                victim.on_move_left_right(max(-1.0, min(1.0, v_dx * 2.5)))
                                victim.on_move_up_down(max(-1.0, min(1.0, -v_dz * 2.5)))
                            else:
                                va['state'] = 'waiting_tm'
                                victim.on_move_left_right(0)
                                victim.on_move_up_down(0)

                                def start_tm_punch():
                                    if s.pending_action is not pa or va.get('state') != 'waiting_tm':
                                        return
                                    if not (victim and victim.node and victim.is_alive()):
                                        return
                                    va['state'] = 'punching_tm'
                                    if v_tgt_node and v_tgt_node.node:
                                        w_px, _, w_pz = victim.node.position
                                        w_tx, _, w_tz = v_tgt_node.node.position
                                        victim.on_move_left_right(w_tx - w_px)
                                        victim.on_move_up_down(-(w_tz - w_pz))
                                    victim.on_punch_press()

                                    def execute_tm_hit():
                                        victim.on_punch_release()
                                        victim.on_move_left_right(0)
                                        victim.on_move_up_down(0)
                                        if v_tgt_node and v_tgt_node.node and v_tgt_node.is_alive():
                                            dmg = s.atk(victim)
                                            hit = bs.HitMessage(
                                                pos=v_tgt_node.node.position,
                                                velocity=(0.0, 0.0, 0.0),
                                                magnitude=0.0,
                                                velocity_magnitude=0.0,
                                                radius=1.0,
                                                srcnode=victim.node,
                                                force_direction=(0.0, 1.0, 0.0),
                                                hit_type='attack',
                                            )
                                            setattr(hit, 'is_backend', True)
                                            setattr(hit, 'custom_damage', dmg)
                                            v_tgt_node.handlemessage(hit)
                                        va['state'] = 'returning_home'
                                    s.memory['timers']['v_tm_hit'] = bs.Timer(0.2, execute_tm_hit)
                                s.memory['timers']['v_tm_wait'] = bs.Timer(0.2, start_tm_punch)
                        else:
                            va['state'] = 'returning_home'
                    elif v_state == 'returning_home':
                        v_hsq = va.get('orig_sq')
                        if v_hsq:
                            v_step = s.path(victim, (v_px, v_pz), v_hsq)
                            v_dx, v_dz = v_step[0] - v_px, v_step[1] - v_pz
                            v_dist = (v_dx**2 + v_dz**2)**0.5
                            if v_dist > 0.08 or v_step != v_hsq:
                                victim.on_move_left_right(max(-1.0, min(1.0, v_dx * 2.0)))
                                victim.on_move_up_down(max(-1.0, min(1.0, -v_dz * 2.0)))
                            else:
                                victim.on_move_left_right(0)
                                victim.on_move_up_down(0)
                                va['state'] = 'done'
                                s.pending_action = None
                                s.switch_turn()

            if pa and pa.get('type') == 'special' and pa.get('victim') is b and (pa.get('victim_action') or {}).get('state') == 'waiting_tm':
                return

            # target
            if is_master:
                sq = s.memory['kings'].get(team_id) if s.memory.get('started') else None
            else:
                sq = s.memory['squares'].get(b)

            if sq:
                tgt = s.path(b, (px, pz), sq)
                if tgt is None:
                    b.on_move_left_right(0)
                    b.on_move_up_down(0)
                    return

                dx, dz = tgt[0] - px, tgt[1] - pz
                dist = (dx * dx + dz * dz) ** 0.5
                if tgt != sq or dist > 0.08:
                    char = (getattr(b, 'character', '') or '').lower()
                    has_run = any(k in char for k in ('agent', 'johnson', 'zoe', 'pixel', 'pixie'))
                    spd = 3.0 if (has_run and dist > 0.8) else 1.4
                    b.on_move_left_right(max(-1.0, min(1.0, dx * spd)))
                    b.on_move_up_down(max(-1.0, min(1.0, -dz * spd)))
                else:
                    if s.memory.get('started'):
                        if s.is_on_cooldown(b):
                            b.on_move_left_right(0)
                            b.on_move_up_down(0)
                            b.on_run(0)
                            return

                        if getattr(b, 'zoe_looking_at_master', False):
                            return

                        try:
                            px_cur, _, pz_cur = b.node.position
                            fx, _, fz = b.node.position_forward
                            fw_x = px_cur - fx
                            fw_z = pz_cur - fz
                            fw_len = (fw_x * fw_x + fw_z * fw_z) ** 0.5
                        except Exception:
                            fw_len = 0.0

                        if fw_len > 0.001:
                            norm_x = fw_x / fw_len
                            norm_z = fw_z / fw_len
                            target_z = -1.0 if side > 0 else 1.0
                            dev_deg = degrees(atan2(abs(norm_x), norm_z * target_z))

                            if dev_deg > 5.0:
                                move_val = 0.04 if side > 0 else -0.04
                                b.on_move_left_right(0)
                                b.on_move_up_down(move_val)
                                pid = id(b)
                                s.memory['timers'][f'turn_face_{pid}'] = bs.Timer(
                                    0.04,
                                    lambda: b and b.node and (
                                        b.on_move_up_down(0), b.on_move_left_right(0))
                                )
                            else:
                                b.on_move_left_right(0)
                                b.on_move_up_down(0)
                        else:
                            b.on_move_left_right(0)
                            b.on_move_up_down(0)
                    else:
                        if cnt[0] % 30 == 0 and (plr := s.memory['players'].get(team_id)) and plr.actor and plr.actor.node:
                            mx, _, mz = plr.actor.node.position
                            vx, vz = mx - px, mz - pz
                            l = (vx * vx + vz * vz) ** 0.5 or 1
                            b.on_move_left_right((vx / l) * 0.05)
                            b.on_move_up_down((-vz / l) * 0.05)
                        else:
                            b.on_move_left_right(0)
                            b.on_move_up_down(0)
            else:
                if side * pz < 0:
                    dz = side * 1.5 - pz
                    b.on_move_left_right(max(-1.0, min(1.0, -px * 2)))
                    b.on_move_up_down(max(-1.0, min(1.0, -dz * 3)))
                else:
                    b.on_move_left_right(0)
                    b.on_move_up_down(0)

        self.memory['timers'][f'retain_{id(piece)}'] = bs.Timer(0.1, tick, repeat=True)

    # boom
    def bbg(self, pa):
        b, victim = pa['spaz'], pa['victim']
        pa['boom'] = True
        pa['bj'] = False
        pa['bxd'] = False
        pa['bv'] = []
        total = 1.0
        if b and b.node and victim and victim.node:
            px, _, pz = b.node.position
            vx, _, vz = victim.node.position
            total = max(((vx - px) ** 2 + (vz - pz) ** 2) ** 0.5, 0.01)
        pa['btot'] = total

    def bexp(self, pa):
        if pa.get('bxd') or self.game_over:
            return
        pa['bxd'] = True
        b, victim = pa['spaz'], pa['victim']
        if not b or not b.node:
            return
        cx, cy, cz = b.node.position

        # explosion
        bn = bs.newnode('explosion', attrs={
            'position': (cx, cy, cz),
            'velocity': (0.0, 0.0, 0.0),
            'radius': 1.5,
            'big': False,
        })
        bs.timer(1.0, bn.delete)
        bs.getsound('explosion01').play(position=(cx, cy, cz))

        # targets
        vsq = self.get_spaz_square(victim) if victim else pa.get('target_sq')
        hit_list = []
        for a in self.actors():
            if a is b or not a.node or not a.is_alive() or getattr(a, 'is_dead', False):
                continue
            if getattr(a, 'team_id', None) == getattr(b, 'team_id', None):
                continue
            if a is victim:
                hit_list.append((a, 400))
                continue
            sq = self.get_spaz_square(a)
            if not sq or not vsq:
                continue
            if max(abs(sq[0] - vsq[0]), abs(sq[1] - vsq[1])) > 1.01:
                continue
            hit_list.append((a, 250))

        for a, dmg in hit_list:
            if not a.node or not a.is_alive():
                continue
            hit = bs.HitMessage(
                pos=a.node.position,
                velocity=(0.0, 0.0, 0.0),
                magnitude=0.0,
                velocity_magnitude=0.0,
                radius=1.0,
                srcnode=b.node,
                force_direction=(0.0, 1.0, 0.0),
                hit_type='explosion',
            )
            setattr(hit, 'is_backend', True)
            setattr(hit, 'custom_damage', dmg)
            a.handlemessage(hit)
        if self.game_over:
            return

        # knock
        now = bs.time()
        for a, _ in hit_list:
            if not a.node or not a.is_alive() or getattr(a, 'is_dead', False):
                continue
            a.node.hold_node = None
            a.on_move_left_right(0)
            a.on_move_up_down(0)
            a.on_run(0)
            a.node.handlemessage('impulse', cx, cy - 0.3, cz, 0.0, 0.0,
                                 0.0, 900.0, 0.0, 2.0, 0, 0.0, 0.0, 0.0)
            a.node.handlemessage('knockout', 1000.0)
            tid = getattr(a, 'team_id', 0)
            home = self.memory['kings'].get(tid) if getattr(
                a, 'is_master', False) else self.memory['squares'].get(a)
            pa['bv'].append({
                'piece': a,
                'wk': now + 2.5,
                'woke': False,
                'home': home,
                'done': False,
                'hdl': now + 12.5,
            })

        _s, _pa = ref(self), pa

        def go_home():
            s = _s()
            if s and s.pending_action is _pa and not s.game_over:
                _pa['state'] = 'returning'
        self.memory['timers']['br'] = bs.Timer(0.2, go_home)

        def drive():
            s = _s()
            if not s or s.game_over or s.pending_action is not _pa:
                if s:
                    s.memory['timers']['bd'] = None
                return
            s.bdr(_pa)
        drive()
        self.memory['timers']['bd'] = bs.Timer(0.1, drive, repeat=True)

    def bdr(self, pa):
        now = bs.time()
        all_done = True
        for rec in pa['bv']:
            if rec['done']:
                continue
            a = rec['piece']
            if not a or not a.node or not a.is_alive() or getattr(a, 'is_dead', False):
                rec['done'] = True
                continue
            if now < rec['wk']:
                a.node.handlemessage('knockout', 1000.0)
                all_done = False
                continue
            if not rec['woke']:
                rec['woke'] = True
                a.node.handlemessage('knockout', 0.0)
                bs.getsound('dingSmall').play(position=a.node.position)
            home = rec['home']
            if not home:
                rec['done'] = True
                continue
            px, _, pz = a.node.position
            if ((px - home[0]) ** 2 + (pz - home[1]) ** 2) ** 0.5 <= 0.25:
                rec['done'] = True
                continue
            if now > rec['hdl']:
                rot = 0 if getattr(a, 'team_id', 0) else 180
                a.handlemessage(bs.StandMessage((home[0], 0, home[1]), rot))
                rec['done'] = True
                continue
            all_done = False

        if all_done and pa.get('state') == 'bw':
            self.memory['timers']['bd'] = None

            def finish():
                if self.pending_action is pa:
                    self.pending_action = None
                    self.switch_turn()
            self.memory['timers']['turn_delay'] = bs.Timer(0.2, finish)

    def knockdown(self, team_id, origin):
        _s, _o = ref(self), ref(origin)

        def tick():
            s, o = _s(), _o()
            if not s or not o or (target := s.memory['control'].get(team_id)) is None or not o.node:
                if s:
                    s.memory['timers'][f'knock{team_id}'] = None
                return
            o.node.handlemessage('knockout', 100)
            if target.node:
                tx, _, tz = target.node.position
                if not (-4.0 <= tx <= 4.0 and -4.0 <= tz <= 4.0):
                    if target in s.memory['squares']:
                        old_sq = s.memory['squares'].pop(target, None)
                        s.highlight_tile(old_sq, active=False)
                        s.recolor(target, occupied=False)

        self.memory['timers'][f'knock{team_id}'] = bs.Timer(0.09, tick, repeat=True)

    def sync_legend(self):
        # release
        if self.memory.get('started') or not self.rel:
            return
        want = 0.7 if self.memory['control'] else 0.0
        if want == self.rel_op:
            return
        self.rel_op = want
        for n in self.rel:
            n.exists() and bs.animate(n, 'opacity', {0.0: n.opacity, 0.25: want})

    def bounds_tick(self):
        self.sync_legend()
        for p in self.memory['players'].values():
            if p.actor and p.actor.node and not getattr(p.actor, 'is_dead', False):
                self.shove(p.actor)
        for m in self.memory['placeholder_masters'].values():
            if m and m.node and not getattr(m, 'is_dead', False):
                self.shove(m)
        for team in self.memory['spazzes'].values():
            for b in team:
                if b and b.node and not getattr(b, 'is_dead', False):
                    self.shove(b)
        self.check_kings()

    def shove(self, a):
        x, y, z = a.node.position
        if y < -1.0:
            return self.respawn_spaz(a)
        # bounds
        A = self.map.defs.boxes['area_of_interest_bounds']
        over = max(abs(x) - A[6], abs(z) - A[8])
        if over <= 0:
            return
        d = (x * x + z * z) ** 0.5 or 1.0
        a.node.handlemessage('impulse', x, y, z, 0, 0, 0, min(
            3000 + 1200 * over, 9000), 0, 0, 0, -x / d, 0.2, -z / d)

    def respawn_spaz(self, spaz):
        if not spaz or not spaz.node or getattr(spaz, 'is_dead', False):
            return
        pos = getattr(spaz, 'orig_pos', None)
        rot = getattr(spaz, 'orig_rot', 0)
        if not pos:
            return
        spaz.node.hold_node = None
        spaz.on_move_up_down(0)
        spaz.on_move_left_right(0)
        spaz.handlemessage(bs.StandMessage(pos, rot))
        if isinstance(spaz, Piece):
            self.start_run(spaz)
            if old_sq := self.memory['squares'].pop(spaz, None):
                self.highlight_tile(old_sq, active=False)
            self.recolor(spaz, occupied=False)
            if spaz.claimed_by is not None:
                if plr := self.memory['players'].get(spaz.claimed_by):
                    self.release_control(plr, spaz)
        else:
            if self.memory.get('started'):
                team_id = getattr(spaz, 'team_id', None)
                if team_id is not None and (ksq := self.memory['kings'].get(team_id)):
                    rot = 0 if team_id == 0 else 180
                    spaz.handlemessage(bs.StandMessage((ksq[0], 0, ksq[1]), rot))
                    self.set_master_tile(ksq, self.neon(*self.get_team_color(team_id)), active=True)
                self.retain(spaz)

    def floaters_tick(self, initial=False):
        if not self.fancy:
            return
        # prune
        t = bs.time()
        for f in self.memory['floaters']:
            # cap
            if f.node and t - f.t0 > f.life + 2:
                f.node.delete()
        fl = self.memory['floaters'] = [f for f in self.memory['floaters'] if f.node]
        cap = 247 if self.rotating else 140
        for _ in range(cap - len(fl) if initial else min(26 if self.rotating else 10, cap - len(fl))):
            self.mkfloater(initial)

    def mkfloater(self, instant=False):
        if not self.fancy:
            return
        if self.rotating:
            a, r = uniform(0, 6.2832), uniform(4.5 ** 2, 30.0 ** 2) ** 0.5
            x, z = r * cos(a), r * sin(a)
        else:
            for _ in range(80):
                x, z = uniform(-17.0, 17.0), uniform(-21.0, 17.0)
                if (abs(x) > 4.05 or abs(z) > 4.05) and not (z > 0 and abs(x) < 0.81 * z) and random() < exp(-(max(abs(x), abs(z)) - 4.0) / 5.0):
                    break
            else:
                return
        # colors
        c0, c1, r = self.get_team_color(0), self.get_team_color(1), random()
        if r < 0.3:
            col = c0
        elif r < 0.6:
            col = c1
        else:
            k = uniform(0.15, 0.85)
            col = tuple(a * (1 - k) + b * k for a, b in zip(c0, c1))
        self.memory['floaters'].append(
            Floater(self, (x, uniform(0.5, 12 if self.rotating else 7), z), col, instant))

    def neon(self, a, b, c, z=4):
        return (
            a*z, b*z, c*z
        )

    def get_team_color(self, team_id):
        if c := self.memory['team_colors'].get(team_id):
            return c
        if team_id in self.memory['swap']:
            return self.memory['swap'][team_id][2]
        if (plr := self.memory['players'].get(team_id)):
            c = getattr(plr.team, 'color', None)
            if c:
                self.memory['team_colors'][team_id] = c
                return c
            if plr.actor and plr.actor.node and plr.actor.node.color != (0.5, 0.5, 0.5):
                self.memory['team_colors'][team_id] = plr.actor.node.color
                return plr.actor.node.color
        if len(self.teams) > team_id:
            c = getattr(self.teams[team_id], 'color', None)
            if c:
                self.memory['team_colors'][team_id] = c
                return c
        default_colors = [(0.1, 0.25, 1.0), (1.0, 0.2, 0.2)]
        c = default_colors[team_id % len(default_colors)]
        self.memory['team_colors'][team_id] = c
        return c

    def recolor(self, piece, occupied=False):
        if not piece or not piece.node:
            return
        c = self.get_team_color(piece.team_id)
        tc = self.neon(*c) if occupied else (1, 1, 1)
        th = self.neon(*c) if occupied else c
        bs.animate_array(piece.node, 'color', 3, {0: piece.node.color, 0.3: tc})
        bs.animate_array(piece.node, 'highlight', 3, {0: piece.node.highlight, 0.3: th})

    def highlight_tile(self, sq, color=None, active=True):
        if not sq:
            return
        if node := self.map.fills.get((round(sq[0], 1), round(sq[1], 1))):
            target_op = 0.7 if active else 0.0
            bs.animate(node, 'opacity', {0: node.opacity, 0.3: target_op})
            if active and color:
                bs.animate_array(node, 'color', 3, {0: node.color, 0.3: color})

    def stop_game(self):
        self.playing = False
        self.stop_countdown()

        for tid in list(self.team_selectors.keys()):
            self.hide_team_selector(tid)
        for s_node in self.team_selectors.values():
            if s_node:
                s_node.delete()
        self.team_selectors.clear()
        self.team_selector_pos.clear()
        self.team_selector_anim.clear()
        self.team_selector_blink.clear()

        self.clear_selection()
        self.pending_action = None
        self.turn_active = False
        self.game_over = False
        self.rotating = False
        self.current_turn_team_id = None
        self.st = self.new_st()
        self.turn_t0 = None
        self.memory['win_2d'] = []
        self.stop_all_move_repeats()

        for n in self.legend:
            if n:
                n.delete()
        self.legend.clear()

        for p in self.memory['players'].values():
            if p.actor:
                self.memory['timers'][f'retain_{id(p.actor)}'] = None
                self.memory['timers'][f'run_pulse_{id(p.actor)}'] = None
        for m in self.memory['placeholder_masters'].values():
            if m:
                self.memory['timers'][f'retain_{id(m)}'] = None
                self.memory['timers'][f'run_pulse_{id(m)}'] = None
                if m.node:
                    m.handlemessage(bs.DieMessage(immediate=True))
        self.memory['placeholder_masters'] = {}

        for fill in self.map.fills.values():
            if fill:
                fill.opacity = 0.0
                fill.shape = 'circle'
                fill.size = (0.9,)
        for inner in self.map.inner_fills.values():
            if inner:
                inner.opacity = 0.0
        for team in self.memory['spazzes'].values():
            for b in team:
                if b:
                    self.memory['timers'][f'retain_{id(b)}'] = None
                    self.stop_run(b)
                    b.handlemessage(bs.DieMessage(immediate=True))
        # timers
        self.memory['timers'] = {k: v for k,
                                 v in self.memory['timers'].items() if k in ('bounds', 'floaters')}
        for k in ['squares', 'swap', 'spazzes', 'kings', 'glow', 'team_colors', 'graveyard', 'cooldowns', 'lm', 'boxes', 'bage']:
            self.memory[k] = {}
        for tid in list(self.king_anims):
            kill_anims(self.king_anims.pop(tid, None))
        self.memory['started'] = False
        self.memory.pop('legend_on', None)
        self.memory['control'] = WeakValueDictionary()

# ba_meta require api 9
# ba_meta export babase.Plugin


class byBordd(bs.Plugin):
    def __init__(self):
        bs.app.classic.maps['Checkboard'] = Checkboard
        if not getattr(bs.JoinActivity.on_transition_in, '_cb', False):
            old_jti = bs.JoinActivity.on_transition_in

            def jti(self):
                old_jti(self)
                getattr(self.session, '_next_game', None) is Checkboom and cap_players(self.session)
            jti._cb = True
            bs.JoinActivity.on_transition_in = jti
        old_gt = bui.gettexture

        def new_gt(tex):
            if tex == 'checkboom':
                return 'checkboom'
            return old_gt(tex)
        bui.gettexture = new_gt

        def wid(_):
            def new(*a, **k):
                if k.get('texture', None) == 'checkboom':
                    k['texture'] = old_gt('reflectionSharper_-z')
                    k['color'] = (0, 2, 2)
                    wid = _(*a, **k)
                    bui.textwidget(
                        parent=k['parent'],
                        big=True,
                        size=(size := k['size']),
                        scale=1.3*(scl := size[0]/220),
                        position=(
                            (p := k['position']) and
                            (p[0]-3*scl, p[1]-3*scl)
                        ),
                        h_align='center',
                        v_align='center',
                        text=Strings.CHECKBOOM,
                        flatness=-2,
                        color=(1.4, 1.4, 1.4),
                        draw_controller=k.get('draw_controller', wid)
                    )
                    return wid
                return _(*a, **k)
            new.__name__ = _.__name__
            new.__doc__ = _.__doc__
            return new
        bui.imagewidget = wid(_ := bui.imagewidget)
        bui.buttonwidget = wid(_ := bui.buttonwidget)
        old = bs.app.config.get
        bs.app.config.get = lambda b, *a, **k: (
            True if b == 'Auto Balance Teams' and
            (
                (
                    (activity := (session := bs.getsession()).getactivity()) and
                    isinstance(activity, bs.JoinActivity) and
                    session._next_game is Checkboom
                ) or isinstance(activity, Checkboom)
            )
            else old(b, *a, **k)
        )
