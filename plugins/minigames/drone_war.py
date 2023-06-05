# Released under the MIT License. See LICENSE for details.
#
"""
DroneWar - Attack enemies with drone, Fly with drone and fire rocket launcher.
Author:  Mr.Smoothy
Discord: https://discord.gg/ucyaesh
Youtube: https://www.youtube.com/c/HeySmoothy
Website: https://bombsquad-community.web.app
Github:  https://github.com/bombsquad-community
"""
# ba_meta require api 7
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import _ba
from ba._generated.enums import InputType
from bastd.actor.bomb import Blast

from bastd.gameutils import SharedObjects
from bastd.actor.playerspaz import PlayerSpaz, PlayerType
from bastd.game.deathmatch import DeathMatchGame, Player
from bastd.actor import spaz
if TYPE_CHECKING:
    from typing import Any, Sequence, Dict, Type, List, Optional, Union

STORAGE_ATTR_NAME = f'_shared_{__name__}_factory'

# SMoothy's Drone (fixed version of floater) with rocket launcher
# use drone as long as you want , unlike floater which dies after being idle.


class Drone(ba.Actor):
    def __init__(self, spaz):
        super().__init__()
        shared = SharedObjects.get()
        self._drone_material = ba.Material()
        self.loop_ascend = None
        self.loop_descend = None
        self.loop_lr = None
        self.loop_ud = None
        self.rocket_launcher = None
        self.x_direction = 0
        self.z_direction = 0
        self.spaz = spaz
        self._drone_material.add_actions(
            conditions=('they_have_material',
                        shared.player_material),
            actions=(('modify_node_collision', 'collide', True),
                     ('modify_part_collision', 'physical', True)))
        self._drone_material.add_actions(
            conditions=(('they_have_material',
                         shared.object_material), 'or',
                        ('they_have_material',
                         shared.footing_material), 'or',
                        ('they_have_material',
                        self._drone_material)),
            actions=('modify_part_collision', 'physical', False))
        self.node = ba.newnode(
            'prop',
            delegate=self,
            owner=None,
            attrs={
                'position': spaz.node.position,
                'model': ba.getmodel('landMine'),
                'light_model': ba.getmodel('landMine'),
                'body': 'landMine',
                'body_scale': 1,
                'model_scale': 1,
                'shadow_size': 0.25,
                'density': 999999,
                'gravity_scale': 0.0,
                'color_texture': ba.gettexture('achievementCrossHair'),
                'reflection': 'soft',
                'reflection_scale': [0.25],
                'materials': [shared.footing_material, self._drone_material]
            })
        self.grab_node = ba.newnode(
            'prop',
            owner=self.node,
            attrs={
                'position': (0, 0, 0),
                'body': 'sphere',
                'model': None,
                'color_texture': None,
                'body_scale': 0.2,
                'reflection': 'powerup',
                'density': 999999,
                'reflection_scale': [1.0],
                'model_scale': 0.2,
                'gravity_scale': 0,
                'shadow_size': 0.1,
                'is_area_of_interest': True,
                'materials': [shared.object_material, self._drone_material]
            })
        self.node.connectattr('position', self.grab_node, 'position')
        self._rcombine = ba.newnode('combine',
                                    owner=self.node,
                                    attrs={
                                        'input0': self.spaz.node.position[0],
                                        'input1': self.spaz.node.position[1]+3,
                                        'input2': self.spaz.node.position[2],
                                        'size': 3
                                    })

        self._rcombine.connectattr('output', self.node, 'position')

    def set_rocket_launcher(self, launcher: RocketLauncher):
        self.rocket_launcher = launcher

    def fire(self):
        if hasattr(self.grab_node, "position"):
            self.rocket_launcher.shot(self.spaz, self.x_direction, self.z_direction, (
                self.grab_node.position[0], self.grab_node.position[1] - 1, self.grab_node.position[2]))

    def ascend(self):
        def loop():
            if self.node.exists():
                ba.animate(self._rcombine, 'input1', {
                    0: self.node.position[1],
                    1: self.node.position[1] + 2
                })
        loop()
        self.loop_ascend = ba.Timer(1, loop, repeat=True)

    def pause_movement(self):
        self.loop_ascend = None

    def decend(self):
        def loop():
            if self.node.exists():
                ba.animate(self._rcombine, 'input1', {
                    0: self.node.position[1],
                    1: self.node.position[1] - 2
                })
        loop()
        self.loop_ascend = ba.Timer(1, loop, repeat=True)

    def pause_lr(self):
        self.loop_lr = None

    def pause_ud(self):
        self.loop_ud = None

    def left_(self, value=-1):
        def loop():
            if self.node.exists():
                ba.animate(self._rcombine, 'input0', {
                    0: self.node.position[0],
                    1: self.node.position[0] + 2 * value
                })
        if value == 0.0:
            self.loop_lr = None
        else:
            self.x_direction = value
            self.z_direction = 0
            loop()
            self.loop_lr = ba.Timer(1, loop, repeat=True)

    def right_(self, value=1):
        def loop():
            if self.node.exists():
                ba.animate(self._rcombine, 'input0', {
                    0: self.node.position[0],
                    1: self.node.position[0] + 2 * value
                })
        if value == 0.0:
            self.loop_lr = None
        else:
            self.x_direction = value
            self.z_direction = 0
            loop()
            self.loop_lr = ba.Timer(1, loop, repeat=True)

    def up_(self, value=1):
        def loop():
            if self.node.exists():
                ba.animate(self._rcombine, 'input2', {
                    0: self.node.position[2],
                    1: self.node.position[2] - 2 * value
                })
        if value == 0.0:
            self.loop_ud = None
        else:
            self.x_direction = 0
            self.z_direction = - value
            loop()
            self.loop_ud = ba.Timer(1, loop, repeat=True)

    def down_(self, value=-1):
        def loop():
            if self.node.exists():
                ba.animate(self._rcombine, 'input2', {
                    0: self.node.position[2],
                    1: self.node.position[2] - 2 * value
                })
        if value == 0.0:
            self.loop_ud = None
        else:
            self.x_direction = 0
            self.z_direction = - value
            loop()
            self.loop_ud = ba.Timer(1, loop, repeat=True)

    def handlemessage(self, msg):
        if isinstance(msg, ba.DieMessage):
            self.node.delete()
            self.grab_node.delete()
            self.loop_ascend = None
            self.loop_ud = None
            self.loop_lr = None
        elif isinstance(msg, ba.OutOfBoundsMessage):
            self.handlemessage(ba.DieMessage())
        else:
            super().handlemessage(msg)

#  =============================================Copied from Quake Game - Dliwk =====================================================================


class RocketFactory:
    """Quake Rocket factory"""

    def __init__(self) -> None:
        self.ball_material = ba.Material()

        self.ball_material.add_actions(
            conditions=((('we_are_younger_than', 5), 'or',
                         ('they_are_younger_than', 5)), 'and',
                        ('they_have_material',
                         SharedObjects.get().object_material)),
            actions=('modify_node_collision', 'collide', False))

        self.ball_material.add_actions(
            conditions=('they_have_material',
                        SharedObjects.get().pickup_material),
            actions=('modify_part_collision', 'use_node_collide', False))

        self.ball_material.add_actions(actions=('modify_part_collision',
                                                'friction', 0))

        self.ball_material.add_actions(
            conditions=(('they_have_material',
                         SharedObjects.get().footing_material), 'or',
                        ('they_have_material',
                         SharedObjects.get().object_material)),
            actions=('message', 'our_node', 'at_connect', ImpactMessage()))

    @classmethod
    def get(cls):
        """Get factory if exists else create new"""
        activity = ba.getactivity()
        if hasattr(activity, STORAGE_ATTR_NAME):
            return getattr(activity, STORAGE_ATTR_NAME)
        factory = cls()
        setattr(activity, STORAGE_ATTR_NAME, factory)
        return factory


class RocketLauncher:
    """Very dangerous weapon"""

    def __init__(self):
        self.last_shot = ba.time()

    def give(self, spaz: spaz.Spaz) -> None:
        """Give spaz a rocket launcher"""
        spaz.punch_callback = self.shot
        self.last_shot = ba.time()

    # FIXME
    # noinspection PyUnresolvedReferences
    def shot(self, spaz, x, z, position) -> None:
        """Release a rocket"""
        time = ba.time()
        if time - self.last_shot > 0.6:
            self.last_shot = time

            direction = [x, 0, z]
            direction[1] = 0.0

            mag = 10.0 / 1 if ba.Vec3(*direction).length() == 0 else ba.Vec3(*direction).length()
            vel = [v * mag for v in direction]
            Rocket(position=position,
                   velocity=vel,
                   owner=spaz.getplayer(ba.Player),
                   source_player=spaz.getplayer(ba.Player),
                   color=spaz.node.color).autoretain()


class ImpactMessage:
    """Rocket touched something"""


class Rocket(ba.Actor):
    """Epic rocket from rocket launcher"""

    def __init__(self,
                 position=(0, 5, 0),
                 velocity=(1, 0, 0),
                 source_player=None,
                 owner=None,
                 color=(1.0, 0.2, 0.2)) -> None:
        super().__init__()
        self.source_player = source_player
        self.owner = owner
        self._color = color
        factory = RocketFactory.get()

        self.node = ba.newnode('prop',
                               delegate=self,
                               attrs={
                                   'position': position,
                                   'velocity': velocity,
                                   'model': ba.getmodel('impactBomb'),
                                   'body': 'sphere',
                                   'color_texture': ba.gettexture(
                                       'bunnyColor'),
                                   'model_scale': 0.2,
                                   'is_area_of_interest': True,
                                   'body_scale': 0.8,
                                   'materials': [
                                       SharedObjects.get().object_material,
                                       factory.ball_material]
                               })  # yapf: disable
        self.node.extra_acceleration = (self.node.velocity[0] * 200, 0,
                                        self.node.velocity[2] * 200)

        self._life_timer = ba.Timer(
            5, ba.WeakCall(self.handlemessage, ba.DieMessage()))

        self._emit_timer = ba.Timer(0.001, ba.WeakCall(self.emit), repeat=True)
        self.base_pos_y = self.node.position[1]

        ba.camerashake(5.0)

    def emit(self) -> None:
        """Emit a trace after rocket"""
        ba.emitfx(position=self.node.position,
                  scale=0.4,
                  spread=0.01,
                  chunk_type='spark')
        if not self.node:
            return
        self.node.position = (self.node.position[0], self.base_pos_y,
                              self.node.position[2])  # ignore y
        ba.newnode('explosion',
                   owner=self.node,
                   attrs={
                       'position': self.node.position,
                       'radius': 0.2,
                       'color': self._color
                   })

    def handlemessage(self, msg: Any) -> Any:
        """Message handling for rocket"""
        super().handlemessage(msg)
        if isinstance(msg, ImpactMessage):
            self.node.handlemessage(ba.DieMessage())

        elif isinstance(msg, ba.DieMessage):
            if self.node:
                Blast(position=self.node.position,
                      blast_radius=2,
                      source_player=self.source_player)

                self.node.delete()
                self._emit_timer = None

        elif isinstance(msg, ba.OutOfBoundsMessage):
            self.handlemessage(ba.DieMessage())


# ba_meta export game
class ChooseQueen(DeathMatchGame):
    name = 'Drone War'

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return issubclass(sessiontype, ba.DualTeamSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ['Football Stadium']

    def spawn_player_spaz(
        self,
        player: PlayerType,
        position: Sequence[float] | None = None,
        angle: float | None = None,
    ) -> PlayerSpaz:
        spaz = super().spawn_player_spaz(player, position, angle)
        self.spawn_drone(spaz)
        return spaz

    def on_begin(self):
        super().on_begin()
        shared = SharedObjects.get()
        self.ground_material = ba.Material()
        self.ground_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('call', 'at_connect', ba.Call(self._handle_player_collide)),
            ),
        )
        pos = (0, 0.1, -5)
        self.main_region = ba.newnode('region', attrs={'position': pos, 'scale': (
            30, 0.001, 23), 'type': 'box', 'materials': [shared.footing_material, self.ground_material]})

    def _handle_player_collide(self):
        try:
            player = ba.getcollision().opposingnode.getdelegate(
                PlayerSpaz, True)
        except ba.NotFoundError:
            return
        if player.is_alive():
            player.shatter(True)

    def spawn_drone(self, spaz):
        with ba.Context(_ba.get_foreground_host_activity()):

            drone = Drone(spaz)
            r_launcher = RocketLauncher()
            drone.set_rocket_launcher(r_launcher)
            player = spaz.getplayer(Player, True)
            spaz.node.hold_node = drone.grab_node
            player.actor.disconnect_controls_from_player()
            player.resetinput()
            player.assigninput(InputType.PICK_UP_PRESS, drone.ascend)
            player.assigninput(InputType.PICK_UP_RELEASE, drone.pause_movement)
            player.assigninput(InputType.JUMP_PRESS, drone.decend)
            player.assigninput(InputType.PUNCH_PRESS, drone.fire)
            player.assigninput(InputType.LEFT_PRESS, drone.left_)
            player.assigninput(InputType.RIGHT_PRESS, drone.right_)
            player.assigninput(InputType.LEFT_RELEASE, drone.pause_lr)
            player.assigninput(InputType.RIGHT_RELEASE, drone.pause_lr)
            player.assigninput(InputType.UP_PRESS, drone.up_)
            player.assigninput(InputType.DOWN_PRESS, drone.down_)
            player.assigninput(InputType.UP_RELEASE, drone.pause_ud)
            player.assigninput(InputType.DOWN_RELEASE, drone.pause_ud)
