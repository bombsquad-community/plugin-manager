"""Quake Game Activity"""
# ba_meta require api 7
from __future__ import annotations

from typing import TYPE_CHECKING

import random
import enum
import ba
import _ba

from bastd.actor.scoreboard import Scoreboard
from bastd.actor.powerupbox import PowerupBox
from bastd.gameutils import SharedObjects

# from rocket
from bastd.actor.bomb import Blast

# from railgun
from bastd.actor.playerspaz import PlayerSpaz
from bastd.actor.spaz import Spaz


if TYPE_CHECKING:
    from typing import Optional, List, Any, Type, Union, Sequence


STORAGE_ATTR_NAME = f'_shared_{__name__}_factory'


# +++++++++++++++++++Rocket++++++++++++++++++++++++
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
        self.last_shot: Optional[int, float] = 0

    def give(self, spaz: Spaz) -> None:
        """Give spaz a rocket launcher"""
        spaz.punch_callback = self.shot
        self.last_shot = ba.time()

    # FIXME
    # noinspection PyUnresolvedReferences
    def shot(self, spaz: Spaz) -> None:
        """Release a rocket"""
        time = ba.time()
        if time - self.last_shot > 0.6:
            self.last_shot = time
            center = spaz.node.position_center
            forward = spaz.node.position_forward
            direction = [center[0] - forward[0], forward[1] - center[1],
                         center[2] - forward[2]]
            direction[1] = 0.0

            mag = 10.0 / ba.Vec3(*direction).length()
            vel = [v * mag for v in direction]
            Rocket(position=spaz.node.position,
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

# -------------------Rocket--------------------------


# ++++++++++++++++++Railgun++++++++++++++++++++++++++
class Railgun:
    """Very dangerous weapon"""

    def __init__(self) -> None:
        self.last_shot: Optional[int, float] = 0

    def give(self, spaz: Spaz) -> None:
        """Give spaz a railgun"""
        spaz.punch_callback = self.shot
        self.last_shot = ba.time()

    # FIXME
    # noinspection PyUnresolvedReferences
    def shot(self, spaz: Spaz) -> None:
        """Release a rocket"""
        time = ba.time()
        if time - self.last_shot > 0.6:
            self.last_shot = time
            center = spaz.node.position_center
            forward = spaz.node.position_forward
            direction = [
                center[0] - forward[0], forward[1] - center[1],
                center[2] - forward[2]
            ]
            direction[1] = 0.0

            RailBullet(position=spaz.node.position,
                       direction=direction,
                       owner=spaz.getplayer(ba.Player),
                       source_player=spaz.getplayer(ba.Player),
                       color=spaz.node.color).autoretain()


class TouchedToSpazMessage:
    """I hit!"""

    def __init__(self, spaz) -> None:
        self.spaz = spaz


class RailBullet(ba.Actor):
    """Railgun bullet"""

    def __init__(self,
                 position=(0, 5, 0),
                 direction=(0, 2, 0),
                 source_player=None,
                 owner=None,
                 color=(1, 1, 1)) -> None:
        super().__init__()
        self._color = color

        self.node = ba.newnode('light',
                               delegate=self,
                               attrs={
                                   'position': position,
                                   'color': self._color
                               })
        ba.animate(self.node, 'radius', {0: 0, 0.1: 0.5, 0.5: 0})

        self.source_player = source_player
        self.owner = owner
        self._life_timer = ba.Timer(
            0.5, ba.WeakCall(self.handlemessage, ba.DieMessage()))

        pos = position
        vel = tuple(i / 5 for i in ba.Vec3(direction).normalized())
        for _ in range(500):  # Optimization :(
            ba.newnode('explosion',
                       owner=self.node,
                       attrs={
                           'position': pos,
                           'radius': 0.2,
                           'color': self._color
                       })
            pos = (pos[0] + vel[0], pos[1] + vel[1], pos[2] + vel[2])

        for node in _ba.getnodes():
            if node and node.getnodetype() == 'spaz':
                # pylint: disable=invalid-name
                m3 = ba.Vec3(position)
                a = ba.Vec3(direction[2], direction[1], direction[0])
                m1 = ba.Vec3(node.position)
                # pylint: enable=invalid-name
                # distance between node and line
                dist = (a * (m1 - m3)).length() / a.length()
                if dist < 0.3:
                    if node and node != self.owner and node.getdelegate(
                            PlayerSpaz, True).getplayer(
                                ba.Player, True).team != self.owner.team:
                        node.handlemessage(ba.FreezeMessage())
                        pos = self.node.position
                        hit_dir = (0, 10, 0)

                        node.handlemessage(
                            ba.HitMessage(pos=pos,
                                          magnitude=50,
                                          velocity_magnitude=50,
                                          radius=0,
                                          srcnode=self.node,
                                          source_player=self.source_player,
                                          force_direction=hit_dir))

    def handlemessage(self, msg: Any) -> Any:
        super().handlemessage(msg)
        if isinstance(msg, ba.DieMessage):
            if self.node:
                self.node.delete()

        elif isinstance(msg, ba.OutOfBoundsMessage):
            self.handlemessage(ba.DieMessage())

# ------------------Railgun-------------------------


class Player(ba.Player['Team']):
    """Our player"""


class Team(ba.Team[Player]):
    """Our team"""

    def __init__(self) -> None:
        self.score = 0


class WeaponType(enum.Enum):
    """Type of weapon"""
    ROCKET = 0
    RAILGUN = 1


class ObstaclesForm(enum.Enum):
    """Obstacle form"""
    CUBE = 0
    SPHERE = 1
    RANDOM = 2


# ba_meta export game
class QuakeGame(ba.TeamGameActivity[Player, Team]):
    """Quake Team Game Activity"""
    name = 'Quake'
    description = 'Kill a set number of enemies to win.'
    available_settings = [
        ba.IntSetting(
            'Kills to Win Per Player',
            default=15,
            min_value=1,
            increment=1,
        ),
        ba.IntChoiceSetting(
            'Time Limit',
            choices=[('None', 0), ('1 Minute', 60), ('2 Minutes', 120),
                     ('5 Minutes', 300), ('10 Minutes', 600),
                     ('20 Minutes', 1200)],
            default=0,
        ),
        ba.FloatChoiceSetting(
            'Respawn Times',
            choices=[('At once', 0.0), ('Shorter', 0.25), ('Short', 0.5),
                     ('Normal', 1.0), ('Long', 2.0), ('Longer', 4.0)],
            default=1.0,
        ),
        ba.BoolSetting(
            'Speed',
            default=True,
        ),
        ba.BoolSetting(
            'Enable Jump',
            default=True,
        ),
        ba.BoolSetting(
            'Enable Pickup',
            default=True,
        ),
        ba.BoolSetting(
            'Enable Bomb',
            default=False,
        ),
        ba.BoolSetting(
            'Obstacles',
            default=True,
        ),
        ba.IntChoiceSetting(
            'Obstacles Form',
            choices=[('Cube', ObstaclesForm.CUBE.value),
                     ('Sphere', ObstaclesForm.SPHERE.value),
                     ('Random', ObstaclesForm.RANDOM.value)],
            default=0,
        ),
        ba.IntChoiceSetting(
            'Weapon Type',
            choices=[('Rocket', WeaponType.ROCKET.value),
                     ('Railgun', WeaponType.RAILGUN.value)],
            default=WeaponType.ROCKET.value,
        ),
        ba.BoolSetting(
            'Obstacles Mirror Shots',
            default=False,
        ),
        ba.IntSetting(
            'Obstacles Count',
            default=16,
            min_value=0,
            increment=2,
        ),
        ba.BoolSetting(
            'Random Obstacles Color',
            default=True,
        ),
        ba.BoolSetting(
            'Epic Mode',
            default=False,
        ),
    ]

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return issubclass(sessiontype, ba.MultiTeamSession) or issubclass(
            sessiontype, ba.FreeForAllSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        # TODO add more maps
        return ['Football Stadium', 'Monkey Face', 'Doom Shroom']

    def __init__(self, settings) -> None:
        super().__init__(settings)
        self._epic_mode = self.settings_raw['Epic Mode']
        self._score_to_win = self.settings_raw['Kills to Win Per Player']
        self._time_limit = self.settings_raw['Time Limit']
        self._obstacles_enabled = self.settings_raw['Obstacles']
        self._obstacles_count = self.settings_raw['Obstacles Count']
        self._speed_enabled = self.settings_raw['Speed']
        self._bomb_enabled = self.settings_raw['Enable Bomb']
        self._pickup_enabled = self.settings_raw['Enable Pickup']
        self._jump_enabled = self.settings_raw['Enable Jump']
        self._weapon_type = WeaponType(self.settings_raw['Weapon Type'])
        self.default_music = (ba.MusicType.EPIC
                              if self._epic_mode else ba.MusicType.GRAND_ROMP)
        self.slow_motion = self._epic_mode

        self.announce_player_deaths = True
        self._scoreboard = Scoreboard()
        self._ding_sound = ba.getsound('dingSmall')

        self._shield_dropper: Optional[ba.Timer] = None

    def get_instance_description(self) -> Union[str, Sequence]:
        return 'Kill ${ARG1} enemies.', self._score_to_win

    def on_team_join(self, team: Team) -> None:
        team.score = 0
        if self.has_begun():
            self._update_scoreboard()

    def on_begin(self) -> None:
        ba.TeamGameActivity.on_begin(self)
        ba.getactivity().globalsnode.tint = (0.5, 0.7, 1)
        self.drop_shield()
        self._shield_dropper = ba.Timer(8,
                                        ba.WeakCall(self.drop_shield),
                                        repeat=True)
        self.setup_standard_time_limit(self._time_limit)
        if self._obstacles_enabled:
            count = self._obstacles_count
            gamemap = self.map.getname()
            for i in range(count):  # TODO: tidy up around here
                if gamemap == 'Football Stadium':
                    radius = (random.uniform(-10, 1),
                              6,
                              random.uniform(-4.5, 4.5)) \
                        if i > count / 2 else (
                        random.uniform(10, 1), 6, random.uniform(-4.5, 4.5))
                else:
                    radius = (random.uniform(-10, 1),
                              6,
                              random.uniform(-8, 8)) \
                        if i > count / 2 else (
                        random.uniform(10, 1), 6, random.uniform(-8, 8))

                Obstacle(
                    position=radius,
                    mirror=self.settings_raw['Obstacles Mirror Shots'],
                    form=self.settings_raw['Obstacles Form']).autoretain()

        self._update_scoreboard()

    def drop_shield(self) -> None:
        """Drop a shield powerup in random place"""
        # FIXME: should use map defs
        shield = PowerupBox(poweruptype='shield',
                            position=(random.uniform(-10, 10), 6,
                                      random.uniform(-5, 5))).autoretain()

        ba.playsound(self._ding_sound)

        p_light = ba.newnode('light',
                             owner=shield.node,
                             attrs={
                                 'position': (0, 0, 0),
                                 'color': (0.3, 0.0, 0.4),
                                 'radius': 0.3,
                                 'intensity': 2,
                                 'volume_intensity_scale': 10.0
                             })

        shield.node.connectattr('position', p_light, 'position')

        ba.animate(p_light, 'intensity', {0: 2, 8: 0})

    def spawn_player(self, player: Player) -> None:
        spaz = self.spawn_player_spaz(player)
        if self._weapon_type == WeaponType.ROCKET:
            RocketLauncher().give(spaz)
        elif self._weapon_type == WeaponType.RAILGUN:
            Railgun().give(spaz)
        spaz.connect_controls_to_player(enable_jump=self._jump_enabled,
                                        enable_pickup=self._pickup_enabled,
                                        enable_bomb=self._bomb_enabled,
                                        enable_fly=False)

        spaz.node.hockey = self._speed_enabled
        spaz.spaz_light = ba.newnode('light',
                                     owner=spaz.node,
                                     attrs={
                                         'position': (0, 0, 0),
                                         'color': spaz.node.color,
                                         'radius': 0.12,
                                         'intensity': 1,
                                         'volume_intensity_scale': 10.0
                                     })

        spaz.node.connectattr('position', spaz.spaz_light, 'position')

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.PlayerDiedMessage):
            ba.TeamGameActivity.handlemessage(self, msg)
            player = msg.getplayer(Player)
            self.respawn_player(player)
            killer = msg.getkillerplayer(Player)
            if killer is None:
                return

            # handle team-kills
            if killer.team is player.team:
                # in free-for-all, killing yourself loses you a point
                if isinstance(self.session, ba.FreeForAllSession):
                    new_score = player.team.score - 1
                    new_score = max(0, new_score)
                    player.team.score = new_score
                # in teams-mode it gives a point to the other team
                else:
                    ba.playsound(self._ding_sound)
                    for team in self.teams:
                        if team is not killer.team:
                            team.score += 1
            # killing someone on another team nets a kill
            else:
                killer.team.score += 1
                ba.playsound(self._ding_sound)
                # in FFA show our score since its hard to find on
                # the scoreboard
                assert killer.actor is not None
                # noinspection PyUnresolvedReferences
                killer.actor.set_score_text(str(killer.team.score) + '/' +
                                            str(self._score_to_win),
                                            color=killer.team.color,
                                            flash=True)

            self._update_scoreboard()

            # if someone has won, set a timer to end shortly
            # (allows the dust to clear and draws to occur if
            # deaths are close enough)
            if any(team.score >= self._score_to_win for team in self.teams):
                ba.timer(0.5, self.end_game)

        else:
            ba.TeamGameActivity.handlemessage(self, msg)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score,
                                            self._score_to_win)

    def end_game(self) -> None:
        results = ba.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)

        self.end(results=results)


class Obstacle(ba.Actor):
    """Scene object"""

    def __init__(self,
                 position,
                 form=ObstaclesForm.CUBE,
                 mirror=False) -> None:
        ba.Actor.__init__(self)

        if form == ObstaclesForm.CUBE:
            model = 'tnt'
            body = 'crate'
        elif form == ObstaclesForm.SPHERE:
            model = 'bomb'
            body = 'sphere'
        else:  # ObstaclesForm.RANDOM:
            model = random.choice(['tnt', 'bomb'])
            body = 'sphere' if model == 'bomb' else 'crate'

        self.node = ba.newnode(
            'prop',
            delegate=self,
            attrs={
                'position':
                    position,
                'model':
                    ba.getmodel(model),
                'body':
                    body,
                'body_scale':
                    1.3,
                'model_scale':
                    1.3,
                'reflection':
                    'powerup',
                'reflection_scale': [0.7],
                'color_texture':
                    ba.gettexture('bunnyColor'),
                'materials': [SharedObjects.get().footing_material]
                if mirror else [
                        SharedObjects.get().object_material,
                        SharedObjects.get().footing_material
                    ]
            })

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.DieMessage):
            if self.node:
                self.node.delete()

        elif isinstance(msg, ba.OutOfBoundsMessage):
            if self.node:
                self.handlemessage(ba.DieMessage())

        elif isinstance(msg, ba.HitMessage):
            self.node.handlemessage('impulse', msg.pos[0], msg.pos[1],
                                    msg.pos[2], msg.velocity[0],
                                    msg.velocity[1], msg.velocity[2],
                                    msg.magnitude, msg.velocity_magnitude,
                                    msg.radius, 0, msg.velocity[0],
                                    msg.velocity[1], msg.velocity[2])
