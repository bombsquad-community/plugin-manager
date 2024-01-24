# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs
import random
from bascenev1lib.actor.bomb import Blast
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.spaz import PunchHitMessage
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.spazfactory import SpazFactory

if TYPE_CHECKING:
    from typing import Any, Sequence


lang = bs.app.lang.language

if lang == 'Spanish':
    name = 'Guerra de Nieve'
    snowball_rate = 'Intervalo de Ataque'
    snowball_slowest = 'Más Lento'
    snowball_slow = 'Lento'
    snowball_fast = 'Rápido'
    snowball_lagcity = 'Más Rápido'
    snowball_scale = 'Tamaño de Bola de Nieve'
    snowball_smallest = 'Más Pequeño'
    snowball_small = 'Pequeño'
    snowball_big = 'Grande'
    snowball_biggest = 'Más Grande'
    snowball_insane = 'Insano'
    snowball_melt = 'Derretir Bola de Nieve'
    snowball_bust = 'Rebotar Bola de Nieve'
    snowball_explode = 'Explotar al Impactar'
    snowball_snow = 'Modo Nieve'
else:
    name = 'Snowball Fight'
    snowball_rate = 'Snowball Rate'
    snowball_slowest = 'Slowest'
    snowball_slow = 'Slow'
    snowball_fast = 'Fast'
    snowball_lagcity = 'Lag City'
    snowball_scale = 'Snowball Scale'
    snowball_smallest = 'Smallest'
    snowball_small = 'Small'
    snowball_big = 'Big'
    snowball_biggest = 'Biggest'
    snowball_insane = 'Insane'
    snowball_melt = 'Snowballs Melt'
    snowball_bust = 'Snowballs Bust'
    snowball_explode = 'Snowballs Explode'
    snowball_snow = 'Snow Mode'


class Snowball(bs.Actor):

    def __init__(self,
                 position: Sequence[float] = (0.0, 1.0, 0.0),
                 velocity: Sequence[float] = (0.0, 0.0, 0.0),
                 blast_radius: float = 0.7,
                 bomb_scale: float = 0.8,
                 source_player: bs.Player | None = None,
                 owner: bs.Node | None = None,
                 melt: bool = True,
                 bounce: bool = True,
                 explode: bool = False):
        super().__init__()
        shared = SharedObjects.get()
        self._exploded = False
        self.scale = bomb_scale
        self.blast_radius = blast_radius
        self._source_player = source_player
        self.owner = owner
        self._hit_nodes = set()
        self.snowball_melt = melt
        self.snowball_bounce = bounce
        self.snowball_explode = explode
        self.radius = bomb_scale * 0.1
        if bomb_scale <= 1.0:
            shadow_size = 0.6
        elif bomb_scale <= 2.0:
            shadow_size = 0.4
        elif bomb_scale <= 3.0:
            shadow_size = 0.2
        else:
            shadow_size = 0.1

        self.snowball_material = bs.Material()
        self.snowball_material.add_actions(
            conditions=(
                (
                    ('we_are_younger_than', 5),
                    'or',
                    ('they_are_younger_than', 100),
                ),
                'and',
                ('they_have_material', shared.object_material),
            ),
            actions=('modify_node_collision', 'collide', False),
        )

        self.snowball_material.add_actions(
            conditions=('they_have_material', shared.pickup_material),
            actions=('modify_part_collision', 'use_node_collide', False),
        )

        self.snowball_material.add_actions(actions=('modify_part_collision',
                                                    'friction', 0.3))

        self.snowball_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(('modify_part_collision', 'physical', False),
                     ('call', 'at_connect', self.hit)))

        self.snowball_material.add_actions(
            conditions=(('they_dont_have_material', shared.player_material),
                        'and',
                        ('they_have_material', shared.object_material),
                        'or',
                        ('they_have_material', shared.footing_material)),
            actions=('call', 'at_connect', self.bounce))

        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': position,
                'velocity': velocity,
                'body': 'sphere',
                        'body_scale': self.scale,
                        'mesh': bs.getmesh('frostyPelvis'),
                        'shadow_size': shadow_size,
                        'color_texture': bs.gettexture('bunnyColor'),
                        'reflection': 'soft',
                        'reflection_scale': [0.15],
                        'density': 1.0,
                        'materials': [self.snowball_material]
            })
        self.light = bs.newnode(
            'light',
            owner=self.node,
            attrs={
                'color': (0.6, 0.6, 1.0),
                'intensity': 0.8,
                'radius': self.radius
            })
        self.node.connectattr('position', self.light, 'position')
        bs.animate(self.node, 'mesh_scale', {
            0: 0,
            0.2: 1.3 * self.scale,
            0.26: self.scale
        })
        bs.animate(self.light, 'radius', {
            0: 0,
            0.2: 1.3 * self.radius,
            0.26: self.radius
        })
        if self.snowball_melt:
            bs.timer(1.5, bs.WeakCall(self._disappear))

    def hit(self) -> None:
        if not self.node:
            return
        if self._exploded:
            return
        if self.snowball_explode:
            self._exploded = True
            self.do_explode()
            bs.timer(0.001, bs.WeakCall(self.handlemessage, bs.DieMessage()))
        else:
            self.do_hit()

    def do_hit(self) -> None:
        v = self.node.velocity
        if babase.Vec3(*v).length() > 5.0:
            node = bs.getcollision().opposingnode
            if node is not None and node and not (
                    node in self._hit_nodes):
                t = self.node.position
                hitdir = self.node.velocity
                self._hit_nodes.add(node)
                node.handlemessage(
                    bs.HitMessage(
                        pos=t,
                        velocity=v,
                        magnitude=babase.Vec3(*v).length()*0.5,
                        velocity_magnitude=babase.Vec3(*v).length()*0.5,
                        radius=0,
                        srcnode=self.node,
                        source_player=self._source_player,
                        force_direction=hitdir,
                        hit_type='snoBall',
                        hit_subtype='default'))

        if not self.snowball_bounce:
            bs.timer(0.05, bs.WeakCall(self.do_bounce))

    def do_explode(self) -> None:
        Blast(position=self.node.position,
              velocity=self.node.velocity,
              blast_radius=self.blast_radius,
              source_player=babase.existing(self._source_player),
              blast_type='impact',
              hit_subtype='explode').autoretain()

    def bounce(self) -> None:
        if not self.node:
            return
        if self._exploded:
            return
        if not self.snowball_bounce:
            vel = self.node.velocity
            bs.timer(0.01, bs.WeakCall(self.calc_bounce, vel))
        else:
            return

    def calc_bounce(self, vel) -> None:
        if not self.node:
            return
        ospd = babase.Vec3(*vel).length()
        dot = sum(x*y for x, y in zip(vel, self.node.velocity))
        if ospd*ospd - dot > 50.0:
            bs.timer(0.05, bs.WeakCall(self.do_bounce))

    def do_bounce(self) -> None:
        if not self.node:
            return
        if not self._exploded:
            self.do_effect()

    def do_effect(self) -> None:
        self._exploded = True
        bs.emitfx(position=self.node.position,
                  velocity=[v*0.1 for v in self.node.velocity],
                  count=10,
                  spread=0.1,
                  scale=0.4,
                  chunk_type='ice')
        sound = bs.getsound('impactMedium')
        sound.play(1.0, position=self.node.position)
        scl = self.node.mesh_scale
        bs.animate(self.node, 'mesh_scale', {
            0.0: scl*1.0,
            0.02: scl*0.5,
            0.05: 0.0
        })
        lr = self.light.radius
        bs.animate(self.light, 'radius', {
            0.0: lr*1.0,
            0.02: lr*0.5,
            0.05: 0.0
        })
        bs.timer(0.08,
                 bs.WeakCall(self.handlemessage, bs.DieMessage()))

    def _disappear(self) -> None:
        self._exploded = True
        if self.node:
            scl = self.node.mesh_scale
            bs.animate(self.node, 'mesh_scale', {
                0.0: scl*1.0,
                0.3: scl*0.5,
                0.5: 0.0
            })
            lr = self.light.radius
            bs.animate(self.light, 'radius', {
                0.0: lr*1.0,
                0.3: lr*0.5,
                0.5: 0.0
            })
            bs.timer(0.55,
                     bs.WeakCall(self.handlemessage, bs.DieMessage()))

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        else:
            super().handlemessage(msg)


class NewPlayerSpaz(PlayerSpaz):

    def __init__(self, *args: Any, **kwds: Any):
        super().__init__(*args, **kwds)
        self.snowball_scale = 1.0
        self.snowball_melt = True
        self.snowball_bounce = True
        self.snowball_explode = False

    def on_punch_press(self) -> None:
        if not self.node or self.frozen or self.node.knockout > 0.0:
            return
        t_ms = bs.time() * 1000
        assert isinstance(t_ms, int)
        if t_ms - self.last_punch_time_ms >= self._punch_cooldown:
            if self.punch_callback is not None:
                self.punch_callback(self)

            # snowball
            pos = self.node.position
            p1 = self.node.position_center
            p2 = self.node.position_forward
            direction = [p1[0]-p2[0], p2[1]-p1[1], p1[2]-p2[2]]
            direction[1] = 0.03
            mag = 20.0/babase.Vec3(*direction).length()
            vel = [v * mag for v in direction]
            Snowball(position=(pos[0], pos[1] + 0.1, pos[2]),
                     velocity=vel,
                     blast_radius=self.blast_radius,
                     bomb_scale=self.snowball_scale,
                     source_player=self.source_player,
                     owner=self.node,
                     melt=self.snowball_melt,
                     bounce=self.snowball_bounce,
                     explode=self.snowball_explode).autoretain()

            self._punched_nodes = set()  # Reset this.
            self.last_punch_time_ms = t_ms
            self.node.punch_pressed = True
            if not self.node.hold_node:
                bs.timer(
                    0.1,
                    bs.WeakCall(self._safe_play_sound,
                                SpazFactory.get().swish_sound, 0.8))
        self._turbo_filter_add_press('punch')

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, PunchHitMessage):
            pass
        else:
            return super().handlemessage(msg)
        return None


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export bascenev1.GameActivity
class SnowballFightGame(bs.TeamGameActivity[Player, Team]):
    """A game type based on acquiring kills."""

    name = name
    description = 'Kill a set number of enemies to win.'

    # Print messages when players die since it matters here.
    announce_player_deaths = True

    @classmethod
    def get_available_settings(
            cls, sessiontype: type[bs.Session]) -> list[babase.Setting]:
        settings = [
            bs.IntSetting(
                'Kills to Win Per Player',
                min_value=1,
                default=5,
                increment=1,
            ),
            bs.IntChoiceSetting(
                'Time Limit',
                choices=[
                    ('None', 0),
                    ('1 Minute', 60),
                    ('2 Minutes', 120),
                    ('5 Minutes', 300),
                    ('10 Minutes', 600),
                    ('20 Minutes', 1200),
                ],
                default=0,
            ),
            bs.FloatChoiceSetting(
                'Respawn Times',
                choices=[
                    ('Shorter', 0.25),
                    ('Short', 0.5),
                    ('Normal', 1.0),
                    ('Long', 2.0),
                    ('Longer', 4.0),
                ],
                default=1.0,
            ),
            bs.IntChoiceSetting(
                snowball_rate,
                choices=[
                    (snowball_slowest, 500),
                    (snowball_slow, 400),
                    ('Normal', 300),
                    (snowball_fast, 200),
                    (snowball_lagcity, 100),
                ],
                default=300,
            ),
            bs.FloatChoiceSetting(
                snowball_scale,
                choices=[
                    (snowball_smallest, 0.4),
                    (snowball_small, 0.6),
                    ('Normal', 0.8),
                    (snowball_big, 1.4),
                    (snowball_biggest, 3.0),
                    (snowball_insane, 6.0),
                ],
                default=0.8,
            ),
            bs.BoolSetting(snowball_melt, default=True),
            bs.BoolSetting(snowball_bust, default=True),
            bs.BoolSetting(snowball_explode, default=False),
            bs.BoolSetting(snowball_snow, default=True),
            bs.BoolSetting('Epic Mode', default=False),
        ]

        # In teams mode, a suicide gives a point to the other team, but in
        # free-for-all it subtracts from your own score. By default we clamp
        # this at zero to benefit new players, but pro players might like to
        # be able to go negative. (to avoid a strategy of just
        # suiciding until you get a good drop)
        if issubclass(sessiontype, bs.FreeForAllSession):
            settings.append(
                bs.BoolSetting('Allow Negative Scores', default=False))

        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return (issubclass(sessiontype, bs.DualTeamSession)
                or issubclass(sessiontype, bs.FreeForAllSession))

    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return bs.app.classic.getmaps('melee')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._score_to_win: int | None = None
        self._dingsound = bs.getsound('dingSmall')
        self._epic_mode = bool(settings['Epic Mode'])
        self._kills_to_win_per_player = int(
            settings['Kills to Win Per Player'])
        self._time_limit = float(settings['Time Limit'])
        self._allow_negative_scores = bool(
            settings.get('Allow Negative Scores', False))
        self._snowball_rate = int(settings[snowball_rate])
        self._snowball_scale = float(settings[snowball_scale])
        self._snowball_melt = bool(settings[snowball_melt])
        self._snowball_bounce = bool(settings[snowball_bust])
        self._snowball_explode = bool(settings[snowball_explode])
        self._snow_mode = bool(settings[snowball_snow])

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (bs.MusicType.EPIC if self._epic_mode else
                              bs.MusicType.TO_THE_DEATH)

    def get_instance_description(self) -> str | Sequence:
        return 'Crush ${ARG1} of your enemies.', self._score_to_win

    def get_instance_description_short(self) -> str | Sequence:
        return 'kill ${ARG1} enemies', self._score_to_win

    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self._update_scoreboard()

    def on_transition_in(self) -> None:
        super().on_transition_in()
        if self._snow_mode:
            gnode = bs.getactivity().globalsnode
            gnode.tint = (0.8, 0.8, 1.3)
            bs.timer(0.02, self.emit_snowball, repeat=True)

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        # self.setup_standard_powerup_drops()

        # Base kills needed to win on the size of the largest team.
        self._score_to_win = (self._kills_to_win_per_player *
                              max(1, max(len(t.players) for t in self.teams)))
        self._update_scoreboard()

    def emit_snowball(self) -> None:
        pos = (-10 + (random.random() * 30), 15,
               -10 + (random.random() * 30))
        vel = ((-5.0 + random.random() * 30.0) * (-1.0 if pos[0] > 0 else 1.0),
               -50.0, (-5.0 + random.random() * 30.0) * (
            -1.0 if pos[0] > 0 else 1.0))
        bs.emitfx(position=pos,
                  velocity=vel,
                  count=10,
                  scale=1.0 + random.random(),
                  spread=0.0,
                  chunk_type='spark')

    def spawn_player_spaz(self,
                          player: Player,
                          position: Sequence[float] = (0, 0, 0),
                          angle: float | None = None) -> PlayerSpaz:
        from babase import _math
        from bascenev1._gameutils import animate
        from bascenev1._coopsession import CoopSession

        if isinstance(self.session, bs.DualTeamSession):
            position = self.map.get_start_position(player.team.id)
        else:
            # otherwise do free-for-all spawn locations
            position = self.map.get_ffa_start_position(self.players)

        name = player.getname()
        color = player.color
        highlight = player.highlight

        light_color = _math.normalized_color(color)
        display_color = babase.safecolor(color, target_intensity=0.75)

        spaz = NewPlayerSpaz(color=color,
                             highlight=highlight,
                             character=player.character,
                             player=player)

        player.actor = spaz
        assert spaz.node

        # If this is co-op and we're on Courtyard or Runaround, add the
        # material that allows us to collide with the player-walls.
        # FIXME: Need to generalize this.
        if isinstance(self.session, CoopSession) and self.map.getname() in [
            'Courtyard', 'Tower D'
        ]:
            mat = self.map.preloaddata['collide_with_wall_material']
            assert isinstance(spaz.node.materials, tuple)
            assert isinstance(spaz.node.roller_materials, tuple)
            spaz.node.materials += (mat, )
            spaz.node.roller_materials += (mat, )

        spaz.node.name = name
        spaz.node.name_color = display_color
        spaz.connect_controls_to_player(
            enable_pickup=False, enable_bomb=False)

        # Move to the stand position and add a flash of light.
        spaz.handlemessage(
            bs.StandMessage(
                position,
                angle if angle is not None else random.uniform(0, 360)))
        self._spawn_sound.play(1, position=spaz.node.position)
        light = bs.newnode('light', attrs={'color': light_color})
        spaz.node.connectattr('position', light, 'position')
        animate(light, 'intensity', {0: 0, 0.25: 1, 0.5: 0})
        bs.timer(0.5, light.delete)

        # custom
        spaz._punch_cooldown = self._snowball_rate
        spaz.snowball_scale = self._snowball_scale
        spaz.snowball_melt = self._snowball_melt
        spaz.snowball_bounce = self._snowball_bounce
        spaz.snowball_explode = self._snowball_explode

        return spaz

    def handlemessage(self, msg: Any) -> Any:

        if isinstance(msg, bs.PlayerDiedMessage):

            # Augment standard behavior.
            super().handlemessage(msg)

            player = msg.getplayer(Player)
            self.respawn_player(player)

            killer = msg.getkillerplayer(Player)
            if killer is None:
                return None

            # Handle team-kills.
            if killer.team is player.team:

                # In free-for-all, killing yourself loses you a point.
                if isinstance(self.session, bs.FreeForAllSession):
                    new_score = player.team.score - 1
                    if not self._allow_negative_scores:
                        new_score = max(0, new_score)
                    player.team.score = new_score

                # In teams-mode it gives a point to the other team.
                else:
                    self._dingsound.play()
                    for team in self.teams:
                        if team is not killer.team:
                            team.score += 1

            # Killing someone on another team nets a kill.
            else:
                killer.team.score += 1
                self._dingsound.play()

                # In FFA show scores since its hard to find on the scoreboard.
                if isinstance(killer.actor, PlayerSpaz) and killer.actor:
                    killer.actor.set_score_text(str(killer.team.score) + '/' +
                                                str(self._score_to_win),
                                                color=killer.team.color,
                                                flash=True)

            self._update_scoreboard()

            # If someone has won, set a timer to end shortly.
            # (allows the dust to clear and draws to occur if deaths are
            # close enough)
            assert self._score_to_win is not None
            if any(team.score >= self._score_to_win for team in self.teams):
                bs.timer(0.5, self.end_game)

        else:
            return super().handlemessage(msg)
        return None

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score,
                                            self._score_to_win)

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)
