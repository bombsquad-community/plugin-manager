"""UFO Boss Fight v2.0:
Made by Cross Joy"""

# Anyone who wanna help me in giving suggestion/ fix bugs/ by creating PR,
# Can visit my github https://github.com/CrossJoy/Bombsquad-Modding

# You can contact me through discord:
# My Discord Id: Cross Joy#0721
# My BS Discord Server: https://discford.gg/JyBY6haARJ

# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)

# ---------------------------------------
# Update v2.0

# updated to api 8
# ---------------------------------------

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.actor.bomb import Blast, Bomb
from bascenev1lib.actor.onscreentimer import OnScreenTimer
from bascenev1lib.actor.spazbot import SpazBotSet, StickyBot
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence, Union, Callable


class UFODiedMessage:
    ufo: UFO
    """The UFO that was killed."""

    killerplayer: bs.Player | None
    """The bs.Player that killed it (or None)."""

    how: bs.DeathType
    """The particular type of death."""

    def __init__(
        self,
        ufo: UFO,
        killerplayer: bs.Player | None,
        how: bs.DeathType,
    ):
        """Instantiate with given values."""
        self.spazbot = ufo
        self.killerplayer = killerplayer
        self.how = how


class RoboBot(StickyBot):
    character = 'B-9000'
    default_bomb_type = 'land_mine'
    color = (0, 0, 0)
    highlight = (3, 3, 3)


class UFO(bs.Actor):
    """
    New AI for Boss
    """

    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-locals

    node: bs.Node

    def __init__(self, hitpoints: int = 5000):

        super().__init__()
        shared = SharedObjects.get()

        self.update_callback: Callable[[UFO], Any] | None = None
        activity = self.activity
        assert isinstance(activity, bs.GameActivity)

        self.platform_material = bs.Material()
        self.platform_material.add_actions(
            conditions=('they_have_material', shared.footing_material),
            actions=(
                'modify_part_collision', 'collide', True))
        self.ice_material = bs.Material()
        self.ice_material.add_actions(
            actions=('modify_part_collision', 'friction', 0.0))

        self._player_pts: list[tuple[bs.Vec3, bs.Vec3]] | None = None
        self._ufo_update_timer: bs.Timer | None = None
        self.last_player_attacked_by: bs.Player | None = None
        self.last_attacked_time = 0.0
        self.last_attacked_type: tuple[str, str] | None = None

        self.to_target: bs.Vec3 = bs.Vec3(0, 0, 0)
        self.dist = (0, 0, 0)

        self._bots = SpazBotSet()
        self.frozen = False
        self.bot_count = 3

        self.hitpoints = hitpoints
        self.hitpoints_max = hitpoints
        self._width = 240
        self._width_max = 240
        self._height = 35
        self._bar_width = 240
        self._bar_height = 35
        self._bar_tex = self._backing_tex = bs.gettexture('bar')
        self._cover_tex = bs.gettexture('uiAtlas')
        self._mesh = bs.getmesh('meterTransparent')
        self.bar_posx = -120

        self._last_hit_time: int | None = None
        self.impact_scale = 1.0
        self._num_times_hit = 0

        self._sucker_mat = bs.Material()

        self.ufo_material = bs.Material()
        self.ufo_material.add_actions(
            conditions=('they_have_material',
                        shared.player_material),
            actions=(('modify_node_collision', 'collide', True),
                     ('modify_part_collision', 'physical', True)))

        self.ufo_material.add_actions(
            conditions=(('they_have_material',
                         shared.object_material), 'or',
                        ('they_have_material',
                         shared.footing_material), 'or',
                        ('they_have_material',
                         self.ufo_material)),
            actions=('modify_part_collision', 'physical', False))

        activity = bs.get_foreground_host_activity()
        point = activity.map.get_flag_position(None)
        boss_spawn_pos = (point[0], point[1] + 1, point[2])

        self.node = bs.newnode('prop', delegate=self, attrs={
            'position': boss_spawn_pos,
            'velocity': (2, 0, 0),
            'color_texture': bs.gettexture('achievementFootballShutout'),
            'mesh': bs.getmesh('landMine'),
            # 'light_mesh': bs.getmesh('powerupSimple'),
            'mesh_scale': 3.3,
            'body': 'landMine',
            'body_scale': 3.3,
            'gravity_scale': 0.2,
            'density': 1,
            'reflection': 'soft',
            'reflection_scale': [0.25],
            'shadow_size': 0.1,
            'max_speed': 1.5,
            'is_area_of_interest':
                True,
            'materials': [shared.footing_material, shared.object_material]})

        self.holder = bs.newnode('region', attrs={
            'position': (
                boss_spawn_pos[0], boss_spawn_pos[1] - 0.25,
                boss_spawn_pos[2]),
            'scale': [6, 0.1, 2.5 - 0.1],
            'type': 'box',
            'materials': (self.platform_material, self.ice_material,
                          shared.object_material)})

        self.suck_anim = bs.newnode('locator',
                                    owner=self.node,
                                    attrs={'shape': 'circleOutline',
                                           'position': (
                                               boss_spawn_pos[0],
                                               boss_spawn_pos[1] - 0.25,
                                               boss_spawn_pos[2]),
                                           'color': (4, 4, 4),
                                           'opacity': 1.0,
                                           'draw_beauty': True,
                                           'additive': True})

        def suck_anim():
            bs.animate_array(self.suck_anim, 'position', 3,
                             {0: (
                                 self.node.position[0],
                                 self.node.position[1] - 5,
                                 self.node.position[2]),
                                 0.5: (
                                     self.node.position[
                                         0] + self.to_target.x / 2,
                                     self.node.position[
                                         1] + self.to_target.y / 2,
                                     self.node.position[
                                         2] + self.to_target.z / 2)})

        self.suck_timer = bs.Timer(0.5, suck_anim, repeat=True)

        self.blocks = []

        self._sucker_mat.add_actions(
            conditions=(
                ('they_have_material', shared.player_material)
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', self._levitate)

            ))

        # self.sucker = bs.newnode('region', attrs={
        #     'position': (
        #         boss_spawn_pos[0], boss_spawn_pos[1] - 2, boss_spawn_pos[2]),
        #     'scale': [2, 10, 2],
        #     'type': 'box',
        #     'materials': self._sucker_mat, })

        self.suck = bs.newnode('region',
                               attrs={'position': (
                                   boss_spawn_pos[0], boss_spawn_pos[1] - 2,
                                   boss_spawn_pos[2]),
                                   'scale': [1, 10, 1],
                                   'type': 'box',
                                   'materials': [self._sucker_mat]})

        self.node.connectattr('position', self.holder, 'position')
        self.node.connectattr('position', self.suck, 'position')

        bs.animate(self.node, 'mesh_scale', {
            0: 0,
            0.2: self.node.mesh_scale * 1.1,
            0.26: self.node.mesh_scale})

        self.shield_deco = bs.newnode('shield', owner=self.node,
                                      attrs={'color': (4, 4, 4),
                                             'radius': 1.2})
        self.node.connectattr('position', self.shield_deco, 'position')
        self._scoreboard()
        self._update()
        self.drop_bomb_timer = bs.Timer(1.5, bs.Call(self._drop_bomb),
                                        repeat=True)

        self.drop_bots_timer = bs.Timer(15.0, bs.Call(self._drop_bots), repeat=True)

    def _drop_bots(self) -> None:
        p = self.node.position
        for i in range(self.bot_count):
            bs.timer(
                1.0 + i,
                lambda: self._bots.spawn_bot(
                    RoboBot, pos=(self.node.position[0],
                                  self.node.position[1] - 1,
                                  self.node.position[2]), spawn_time=0.0
                ),
            )

    def _drop_bomb(self) -> None:
        t = self.to_target
        p = self.node.position
        if abs(self.dist[0]) < 2 and abs(self.dist[2]) < 2:
            Bomb(position=(p[0], p[1] - 0.5, p[2]),
                 velocity=(t[0] * 5, 0, t[2] * 5),
                 bomb_type='land_mine').autoretain().arm()
        elif self.hitpoints > self.hitpoints_max * 3 / 4:
            Bomb(position=(p[0], p[1] - 1.5, p[2]),
                 velocity=(t[0] * 8, 2, t[2] * 8),
                 bomb_type='normal').autoretain()
        elif self.hitpoints > self.hitpoints_max * 1 / 2:
            Bomb(position=(p[0], p[1] - 1.5, p[2]),
                 velocity=(t[0] * 8, 2, t[2] * 8),
                 bomb_type='ice').autoretain()

        elif self.hitpoints > self.hitpoints_max * 1 / 4:
            Bomb(position=(p[0], p[1] - 1.5, p[2]),
                 velocity=(t[0] * 15, 2, t[2] * 15),
                 bomb_type='sticky').autoretain()
        else:
            Bomb(position=(p[0], p[1] - 1.5, p[2]),
                 velocity=(t[0] * 15, 2, t[2] * 15),
                 bomb_type='impact').autoretain()

    def _levitate(self):
        node = bs.getcollision().opposingnode
        if node.exists():
            p = node.getdelegate(Spaz, True)

            def raise_player(player: bs.Player):
                if player.is_alive():
                    node = player.node
                    try:
                        node.handlemessage("impulse", node.position[0],
                                           node.position[1] + .5,
                                           node.position[2], 0, 5, 0, 3, 10, 0,
                                           0, 0, 5, 0)

                    except:
                        pass

            if not self.frozen:
                for i in range(7):
                    bs.timer(0.05 + i / 20, bs.Call(raise_player, p))

    def on_punched(self, damage: int) -> None:
        """Called when this spaz gets punched."""

    def do_damage(self, msg: Any) -> None:
        if not self.node:
            return None

        damage = abs(msg.magnitude)
        if msg.hit_type == 'explosion':
            damage /= 20

        self.hitpoints -= int(damage)
        if self.hitpoints <= 0:
            self.handlemessage(bs.DieMessage())

    def _get_target_player_pt(self) -> tuple[
            bs.Vec3 | None, bs.Vec3 | None]:
        """Returns the position and velocity of our target.

        Both values will be None in the case of no target.
        """
        assert self.node
        botpt = bs.Vec3(self.node.position)
        closest_dist: float | None = None
        closest_vel: bs.Vec3 | None = None
        closest: bs.Vec3 | None = None
        assert self._player_pts is not None
        for plpt, plvel in self._player_pts:
            dist = (plpt - botpt).length()

            # Ignore player-points that are significantly below the bot
            # (keeps bots from following players off cliffs).
            if (closest_dist is None or dist < closest_dist) and (
                plpt[1] > botpt[1] - 5.0
            ):
                closest_dist = dist
                closest_vel = plvel
                closest = plpt
        if closest_dist is not None:
            assert closest_vel is not None
            assert closest is not None
            return (
                bs.Vec3(closest[0], closest[1], closest[2]),
                bs.Vec3(closest_vel[0], closest_vel[1], closest_vel[2]),
            )
        return None, None

    def set_player_points(self, pts: list[tuple[bs.Vec3, bs.Vec3]]) -> None:
        """Provide the spaz-bot with the locations of its enemies."""
        self._player_pts = pts

    def exists(self) -> bool:
        return bool(self.node)

    def show_damage_count(self, damage: str, position: Sequence[float],
                          direction: Sequence[float]) -> None:
        """Pop up a damage count at a position in space.

        Category: Gameplay Functions
        """
        lifespan = 1.0
        app = bs.app

        # FIXME: Should never vary game elements based on local config.
        #  (connected clients may have differing configs so they won't
        #  get the intended results).
        do_big = app.ui.uiscale is bs.UIScale.SMALL or app.vr_mode
        txtnode = bs.newnode('text',
                             attrs={
                                 'text': damage,
                                 'in_world': True,
                                 'h_align': 'center',
                                 'flatness': 1.0,
                                 'shadow': 1.0 if do_big else 0.7,
                                 'color': (1, 0.25, 0.25, 1),
                                 'scale': 0.035 if do_big else 0.03
                             })
        # Translate upward.
        tcombine = bs.newnode('combine', owner=txtnode, attrs={'size': 3})
        tcombine.connectattr('output', txtnode, 'position')
        v_vals = []
        pval = 0.0
        vval = 0.07
        count = 6
        for i in range(count):
            v_vals.append((float(i) / count, pval))
            pval += vval
            vval *= 0.5
        p_start = position[0]
        p_dir = direction[0]
        bs.animate(tcombine, 'input0',
                   {i[0] * lifespan: p_start + p_dir * i[1]
                    for i in v_vals})
        p_start = position[1]
        p_dir = direction[1]
        bs.animate(tcombine, 'input1',
                   {i[0] * lifespan: p_start + p_dir * i[1]
                    for i in v_vals})
        p_start = position[2]
        p_dir = direction[2]
        bs.animate(tcombine, 'input2',
                   {i[0] * lifespan: p_start + p_dir * i[1]
                    for i in v_vals})
        bs.animate(txtnode, 'opacity', {0.7 * lifespan: 1.0, lifespan: 0.0})
        bs.timer(lifespan, txtnode.delete)

    def _scoreboard(self) -> None:
        self._backing = bs.NodeActor(
            bs.newnode('image',
                       attrs={
                           'position': (self.bar_posx + self._width / 2, -100),
                           'scale': (self._width, self._height),
                           'opacity': 0.7,
                           'color': (0.3,
                                     0.3,
                                     0.3),
                           'vr_depth': -3,
                           'attach': 'topCenter',
                           'texture': self._backing_tex
                       }))
        self._bar = bs.NodeActor(
            bs.newnode('image',
                       attrs={
                           'opacity': 1.0,
                           'color': (0.5, 0.5, 0.5),
                           'attach': 'topCenter',
                           'texture': self._bar_tex
                       }))
        self._bar_scale = bs.newnode('combine',
                                     owner=self._bar.node,
                                     attrs={
                                         'size': 2,
                                         'input0': self._bar_width,
                                         'input1': self._bar_height
                                     })
        self._bar_scale.connectattr('output', self._bar.node, 'scale')
        self._bar_position = bs.newnode(
            'combine',
            owner=self._bar.node,
            attrs={
                'size': 2,
                'input0': self.bar_posx + self._bar_width / 2,
                'input1': -100
            })
        self._bar_position.connectattr('output', self._bar.node, 'position')
        self._cover = bs.NodeActor(
            bs.newnode('image',
                       attrs={
                           'position': (self.bar_posx + 120, -100),
                           'scale':
                               (self._width * 1.15, self._height * 1.6),
                           'opacity': 1.0,
                           'color': (0.3,
                                     0.3,
                                     0.3),
                           'vr_depth': 2,
                           'attach': 'topCenter',
                           'texture': self._cover_tex,
                           'mesh_transparent': self._mesh
                       }))
        self._score_text = bs.NodeActor(
            bs.newnode('text',
                       attrs={
                           'position': (self.bar_posx + 120, -100),
                           'h_attach': 'center',
                           'v_attach': 'top',
                           'h_align': 'center',
                           'v_align': 'center',
                           'maxwidth': 130,
                           'scale': 0.9,
                           'text': '',
                           'shadow': 0.5,
                           'flatness': 1.0,
                           'color': (1, 1, 1, 0.8)
                       }))

    def _update(self) -> None:
        self._score_text.node.text = str(self.hitpoints)
        self._bar_width = self.hitpoints * self._width_max / self.hitpoints_max
        cur_width = self._bar_scale.input0
        bs.animate(self._bar_scale, 'input0', {
            0.0: cur_width,
            0.1: self._bar_width
        })
        cur_x = self._bar_position.input0

        bs.animate(self._bar_position, 'input0', {
            0.0: cur_x,
            0.1: self.bar_posx + self._bar_width / 2
        })

        if self.hitpoints > self.hitpoints_max * 3 / 4:
            bs.animate_array(self.shield_deco, 'color', 3,
                             {0: self.shield_deco.color, 0.2: (4, 4, 4)})
        elif self.hitpoints > self.hitpoints_max * 1 / 2:
            bs.animate_array(self.shield_deco, 'color', 3,
                             {0: self.shield_deco.color, 0.2: (3, 3, 5)})
            self.bot_count = 4

        elif self.hitpoints > self.hitpoints_max * 1 / 4:
            bs.animate_array(self.shield_deco, 'color', 3,
                             {0: self.shield_deco.color, 0.2: (1, 5, 1)})
            self.bot_count = 5

        else:
            bs.animate_array(self.shield_deco, 'color', 3,
                             {0: self.shield_deco.color, 0.2: (5, 0.2, 0.2)})
            self.bot_count = 6

    def update_ai(self) -> None:
        """Should be called periodically to update the spaz' AI."""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        if self.update_callback is not None:
            if self.update_callback(self):
                # Bot has been handled.
                return

        if not self.node:
            return

        pos = self.node.position
        our_pos = bs.Vec3(pos[0], pos[1] - 3, pos[2])

        target_pt_raw: bs.Vec3 | None
        target_vel: bs.Vec3 | None

        target_pt_raw, target_vel = self._get_target_player_pt()

        try:
            dist_raw = (target_pt_raw - our_pos).length()

            target_pt = (
                target_pt_raw + target_vel * dist_raw * 0.3
            )
        except:
            return
        diff = target_pt - our_pos
        # self.dist = diff.length()
        self.dist = diff
        self.to_target = diff.normalized()

        # p = spaz.node.position
        # pt = self.getTargetPosition(p)
        # pn = self.node.position
        # d = [pt[0] - pn[0], pt[1] - pn[1], pt[2] - pn[2]]
        # speed = self.getMaxSpeedByDir(d)
        # self.node.velocity = (self.to_target.x, self.to_target.y, self.to_target.z)
        if self.hitpoints == 0:
            setattr(self.node, 'velocity',
                    (0, self.to_target.y, 0))
            setattr(self.node, 'extra_acceleration',
                    (0, self.to_target.y * 80 + 70,
                     0))
        elif not self.frozen:
            setattr(self.node, 'velocity',
                    (self.to_target.x, self.to_target.y, self.to_target.z))
            setattr(self.node, 'extra_acceleration',
                    (self.to_target.x, self.to_target.y * 80 + 70,
                     self.to_target.z))

    def on_expire(self) -> None:
        super().on_expire()

        # We're being torn down; release our callback(s) so there's
        # no chance of them keeping activities or other things alive.
        self.update_callback = None

    def animate_mesh(self) -> None:
        if not self.node:
            return None
        # bs.animate(self.node, 'mesh_scale', {
        #     0: self.node.mesh_scale,
        #     0.08: self.node.mesh_scale * 0.9,
        #     0.15: self.node.mesh_scale})
        bs.emitfx(position=self.node.position,
                  velocity=self.node.velocity,
                  count=int(6 + random.random() * 10),
                  scale=0.5,
                  spread=0.4,
                  chunk_type='metal')

    def handlemessage(self, msg: Any) -> Any:
        # pylint: disable=too-many-branches
        assert not self.expired

        if isinstance(msg, bs.HitMessage):
            # Don't die on punches (that's annoying).
            self.animate_mesh()
            if self.hitpoints != 0:
                self.do_damage(msg)
            # self.show_damage_msg(msg)
            self._update()

        elif isinstance(msg, bs.DieMessage):
            if self.node:
                self.hitpoints = 0
                self.frozen = True
                self.suck_timer = False
                self.drop_bomb_timer = False
                self.drop_bots_timer = False

                p = self.node.position

                for i in range(6):
                    def ded_explode(count):
                        p_x = p[0] + random.uniform(-1, 1)
                        p_z = p[2] + random.uniform(-1, 1)
                        if count == 5:
                            Blast(
                                position=(p[0], p[1], p[2]),
                                blast_type='tnt',
                                blast_radius=5.0).autoretain()
                        else:
                            Blast(
                                position=(p_x, p[1], p_z),
                                blast_radius=2.0).autoretain()

                    bs.timer(0 + i, bs.Call(ded_explode, i))

                bs.timer(5, self.node.delete)
                bs.timer(0.1, self.suck.delete)
                bs.timer(0.1, self.suck_anim.delete)

        elif isinstance(msg, bs.OutOfBoundsMessage):
            activity = bs.get_foreground_host_activity()
            try:
                point = activity.map.get_flag_position(None)
                boss_spawn_pos = (point[0], point[1] + 1.5, point[2])
                assert self.node
                self.node.position = boss_spawn_pos
            except:
                self.handlemessage(bs.DieMessage())

        elif isinstance(msg, bs.FreezeMessage):
            if not self.frozen:
                self.frozen = True
                self.drop_bomb_timer = False
                self.drop_bots_timer = False
                setattr(self.node, 'velocity',
                        (0,  self.to_target.y, 0))
                setattr(self.node, 'extra_acceleration',
                        (0,  0, 0))
                self.node.reflection_scale = [2]

                def unfrozen():
                    self.frozen = False
                    self.drop_bomb_timer = bs.Timer(1.5,
                                                    bs.Call(self._drop_bomb),
                                                    repeat=True)

                    self.drop_bots_timer = bs.Timer(15.0,
                                                    bs.Call(self._drop_bots),
                                                    repeat=True)
                    self.node.reflection_scale = [0.25]

                bs.timer(3.0, unfrozen)

        else:
            super().handlemessage(msg)


class UFOSet:
    """A container/controller for one or more bs.SpazBots.

    category: Bot Classes
    """

    def __init__(self) -> None:
        """Create a bot-set."""

        # We spread our bots out over a few lists so we can update
        # them in a staggered fashion.
        self._ufo_bot_list_count = 5
        self._ufo_bot_add_list = 0
        self._ufo_bot_update_list = 0
        self._ufo_bot_lists: list[list[UFO]] = [
            [] for _ in range(self._ufo_bot_list_count)
        ]
        self._ufo_spawn_sound = bs.getsound('spawn')
        self._ufo_spawning_count = 0
        self._ufo_bot_update_timer: bs.Timer | None = None
        self.start_moving()

    def _update(self) -> None:

        # Update one of our bot lists each time through.
        # First off, remove no-longer-existing bots from the list.
        try:
            bot_list = self._ufo_bot_lists[self._ufo_bot_update_list] = [
                b for b in self._ufo_bot_lists[self._ufo_bot_update_list] if b
            ]
        except Exception:
            bot_list = []
            bs.print_exception(
                'Error updating bot list: '
                + str(self._ufo_bot_lists[self._ufo_bot_update_list])
            )
        self._bot_update_list = (
            self._ufo_bot_update_list + 1
        ) % self._ufo_bot_list_count

        # Update our list of player points for the bots to use.
        player_pts = []
        for player in bs.getactivity().players:
            assert isinstance(player, bs.Player)
            try:
                # TODO: could use abstracted player.position here so we
                # don't have to assume their actor type, but we have no
                # abstracted velocity as of yet.
                if player.is_alive():
                    assert isinstance(player.actor, UFO)
                    assert player.actor.node
                    player_pts.append(
                        (
                            bs.Vec3(player.actor.node.position),
                            bs.Vec3(player.actor.node.velocity),
                        )
                    )
            except Exception:
                bs.print_exception('Error on bot-set _update.')

        for bot in bot_list:
            bot.set_player_points(player_pts)
            bot.update_ai()

    def start_moving(self) -> None:
        """Start processing bot AI updates so they start doing their thing."""
        self._ufo_bot_update_timer = bs.Timer(
            0.05, bs.WeakCall(self._update), repeat=True
        )

    def spawn_bot(
        self,
        bot_type: type[UFO],
        pos: Sequence[float],
        spawn_time: float = 3.0,
        on_spawn_call: Callable[[UFO], Any] | None = None,
    ) -> None:
        """Spawn a bot from this set."""
        from bascenev1lib.actor import spawner

        spawner.Spawner(
            pt=pos,
            spawn_time=spawn_time,
            send_spawn_message=False,
            spawn_callback=bs.Call(
                self._spawn_bot, bot_type, pos, on_spawn_call
            ),
        )
        self._ufo_spawning_count += 1

    def _spawn_bot(
        self,
        bot_type: type[UFO],
        pos: Sequence[float],
        on_spawn_call: Callable[[UFO], Any] | None,
    ) -> None:
        spaz = bot_type()
        self._ufo_spawn_sound.play(position=pos)
        assert spaz.node
        spaz.node.handlemessage('flash')
        spaz.node.is_area_of_interest = False
        spaz.handlemessage(bs.StandMessage(pos, random.uniform(0, 360)))
        self.add_bot(spaz)
        self._ufo_spawning_count -= 1
        if on_spawn_call is not None:
            on_spawn_call(spaz)

    def add_bot(self, bot: UFO) -> None:
        """Add a bs.SpazBot instance to the set."""
        self._ufo_bot_lists[self._ufo_bot_add_list].append(bot)
        self._ufo_bot_add_list = (
            self._ufo_bot_add_list + 1) % self._ufo_bot_list_count

    def have_living_bots(self) -> bool:
        """Return whether any bots in the set are alive or spawning."""
        return self._ufo_spawning_count > 0 or any(
            any(b.is_alive() for b in l) for l in self._ufo_bot_lists
        )

    def get_living_bots(self) -> list[UFO]:
        """Get the living bots in the set."""
        bots: list[UFO] = []
        for botlist in self._ufo_bot_lists:
            for bot in botlist:
                if bot.is_alive():
                    bots.append(bot)
        return bots

    def clear(self) -> None:
        """Immediately clear out any bots in the set."""

        # Don't do this if the activity is shutting down or dead.
        activity = bs.getactivity(doraise=False)
        if activity is None or activity.expired:
            return

        for i, bot_list in enumerate(self._ufo_bot_lists):
            for bot in bot_list:
                bot.handlemessage(bs.DieMessage(immediate=True))
            self._ufo_bot_lists[i] = []


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""


# ba_meta export bascenev1.GameActivity
class UFOightGame(bs.TeamGameActivity[Player, Team]):
    """
    A co-op game where you try to defeat UFO Boss
    as fast as possible
    """

    name = 'UFO Fight'
    description = 'REal Boss Fight?'
    scoreconfig = bs.ScoreConfig(
        label='Time', scoretype=bs.ScoreType.MILLISECONDS, lower_is_better=True
    )
    default_music = bs.MusicType.TO_THE_DEATH

    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        # For now we're hard-coding spawn positions and whatnot
        # so we need to be sure to specify that we only support
        # a specific map.
        return ['Football Stadium']

    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        # We currently support Co-Op only.
        return issubclass(sessiontype, bs.CoopSession)

    # In the constructor we should load any media we need/etc.
    # ...but not actually create anything yet.
    def __init__(self, settings: dict):
        super().__init__(settings)
        self._winsound = bs.getsound('score')
        self._won = False
        self._timer: OnScreenTimer | None = None
        self._bots = UFOSet()
        self._preset = str(settings['preset'])
        self._credit = bs.newnode('text',
                                  attrs={
                                      'v_attach': 'bottom',
                                      'h_align': 'center',
                                      'color': (0.4, 0.4, 0.4),
                                      'flatness': 0.5,
                                      'shadow': 0.5,
                                      'position': (0, 20),
                                      'scale': 0.7,
                                      'text': 'By Cross Joy'
                                  })

    def on_transition_in(self) -> None:
        super().on_transition_in()
        gnode = bs.getactivity().globalsnode
        gnode.tint = (0.42, 0.55, 0.66)

    # Called when our game actually begins.
    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_powerup_drops()

        # In pro mode there's no powerups.

        # Make our on-screen timer and start it roughly when our bots appear.
        self._timer = OnScreenTimer()
        bs.timer(4.0, self._timer.start)

        def checker():
            if not self._won:
                self.timer = bs.Timer(0.1, self._check_if_won, repeat=True)

        bs.timer(10, checker)
        activity = bs.get_foreground_host_activity()

        point = activity.map.get_flag_position(None)
        boss_spawn_pos = (point[0], point[1] + 1.5, point[2])

        # Spawn some baddies.
        bs.timer(
            1.0,
            lambda: self._bots.spawn_bot(
                UFO, pos=boss_spawn_pos, spawn_time=3.0
            ),
        )

    # Called for each spawning player.

    def _check_if_won(self) -> None:
        # Simply end the game if there's no living bots.
        # FIXME: Should also make sure all bots have been spawned;
        #  if spawning is spread out enough that we're able to kill
        #  all living bots before the next spawns, it would incorrectly
        #  count as a win.
        if not self._bots.have_living_bots():
            self.timer = False
            self._won = True
            self.end_game()

    # Called for miscellaneous messages.
    def handlemessage(self, msg: Any) -> Any:

        # A player has died.
        if isinstance(msg, bs.PlayerDiedMessage):
            player = msg.getplayer(Player)
            self.stats.player_was_killed(player)
            bs.timer(0.1, self._checkroundover)

        # A spaz-bot has died.
        elif isinstance(msg, UFODiedMessage):
            # Unfortunately the ufo will always tell us there are living
            # bots if we ask here (the currently-dying bot isn't officially
            # marked dead yet) ..so lets push a call into the event loop to
            # check once this guy has finished dying.
            bs.pushcall(self._check_if_won)

        # Let the base class handle anything we don't.
        else:
            return super().handlemessage(msg)
        return None

    # When this is called, we should fill out results and end the game
    # *regardless* of whether is has been won. (this may be called due
    # to a tournament ending or other external reason).

    def _checkroundover(self) -> None:
        """End the round if conditions are met."""
        if not any(player.is_alive() for player in self.teams[0].players):
            self.end_game()

    def end_game(self) -> None:

        # Stop our on-screen timer so players can see what they got.
        assert self._timer is not None
        self._timer.stop()

        results = bs.GameResults()

        # If we won, set our score to the elapsed time in milliseconds.
        # (there should just be 1 team here since this is co-op).
        # ..if we didn't win, leave scores as default (None) which means
        # we lost.
        if self._won:
            elapsed_time_ms = int((bs.time() - self._timer.starttime) * 1000.0)
            bs.cameraflash()
            self._winsound.play()
            for team in self.teams:
                for player in team.players:
                    if player.actor:
                        player.actor.handlemessage(bs.CelebrateMessage())
                results.set_team_score(team, elapsed_time_ms)

        # Ends the activity.
        self.end(results)


# ba_meta export plugin
class MyUFOFightLevel(babase.Plugin):

    def on_app_running(self) -> None:
        babase.app.classic.add_coop_practice_level(
            bs.Level(
                name='The UFO Fight',
                displayname='${GAME}',
                gametype=UFOightGame,
                settings={'preset': 'regular'},
                preview_texture_name='footballStadiumPreview',
            )
        )
