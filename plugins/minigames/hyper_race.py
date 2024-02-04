# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 8

from __future__ import annotations

import random
from typing import TYPE_CHECKING
from dataclasses import dataclass

import babase
import bauiv1 as bui
import bascenev1 as bs
from bascenev1 import _map
from bascenev1lib.actor.bomb import Bomb, Blast, BombFactory
from bascenev1lib.actor.powerupbox import PowerupBox
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import (Any, Type, Tuple, List, Sequence, Optional, Dict,
                        Union)
    from bascenev1lib.actor.onscreentimer import OnScreenTimer


class ThePadDefs:
    points = {}
    boxes = {}
    points['race_mine1'] = (0, 5, 12)
    points['race_point1'] = (0.2, 5, 2.86308) + (0.507, 4.673, 1.1)
    points['race_point2'] = (6.9301, 5.04988, 2.82066) + (0.911, 4.577, 1.073)
    points['race_point3'] = (6.98857, 4.5011, -8.88703) + (1.083, 4.673, 1.076)
    points['race_point4'] = (-6.4441, 4.5011, -8.88703) + (1.083, 4.673, 1.076)
    points['race_point5'] = (-6.31128, 4.5011, 2.82669) + (0.894, 4.673, 0.941)
    boxes['area_of_interest_bounds'] = (
        0.3544110667, 4.493562578, -2.518391331) + (
        0.0, 0.0, 0.0) + (16.64754831, 8.06138989, 18.5029888)
    points['ffa_spawn1'] = (-0, 5, 2.5)
    points['flag1'] = (-7.026110145, 4.308759233, -6.302807727)
    points['flag2'] = (7.632557137, 4.366002373, -6.287969342)
    points['flagDefault'] = (0.4611826686, 4.382076338, 3.680881802)
    boxes['map_bounds'] = (0.2608783669, 4.899663734, -3.543675157) + (
        0.0, 0.0, 0.0) + (29.23565494, 14.19991443, 29.92689344)
    points['powerup_spawn1'] = (-4.166594349, 5.281834349, -6.427493781)
    points['powerup_spawn2'] = (4.426873526, 5.342460464, -6.329745237)
    points['powerup_spawn3'] = (-4.201686731, 5.123385835, 0.4400721376)
    points['powerup_spawn4'] = (4.758924722, 5.123385835, 0.3494054559)
    points['shadow_lower_bottom'] = (-0.2912522507, 2.020798381, 5.341226521)
    points['shadow_lower_top'] = (-0.2912522507, 3.206066063, 5.341226521)
    points['shadow_upper_bottom'] = (-0.2912522507, 6.062361813, 5.341226521)
    points['shadow_upper_top'] = (-0.2912522507, 9.827201965, 5.341226521)
    points['spawn1'] = (-0, 5, 2.5)
    points['tnt1'] = (0.4599593402, 4.044276501, -6.573537395)


class ThePadMapb(bs.Map):
    defs = ThePadDefs()
    name = 'Racing'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['hyper']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'thePadPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'mesh': bs.getmesh('thePadLevel'),
            'bottom_mesh': bs.getmesh('thePadLevelBottom'),
            'collision_mesh': bs.getcollisionmesh('thePadLevelCollide'),
            'tex': bs.gettexture('thePadLevelColor'),
            'bgtex': bs.gettexture('black'),
            'bgmesh': bs.getmesh('thePadBG'),
            'railing_collision_mesh': bs.getcollisionmesh('thePadLevelBumper'),
            'vr_fill_mound_mesh': bs.getmesh('thePadVRFillMound'),
            'vr_fill_mound_tex': bs.gettexture('vrFillMound')
        }
        # fixme should chop this into vr/non-vr sections for efficiency
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        self.bottom = bs.newnode('terrain',
                                 attrs={
                                     'mesh': self.preloaddata['bottom_mesh'],
                                     'lighting': False,
                                     'color_texture': self.preloaddata['tex']
                                 })
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex']
            })
        self.railing = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['railing_collision_mesh'],
                'materials': [shared.railing_material],
                'bumper': True
            })
        bs.newnode('terrain',
                   attrs={
                       'mesh': self.preloaddata['vr_fill_mound_mesh'],
                       'lighting': False,
                       'vr_only': True,
                       'color': (0.56, 0.55, 0.47),
                       'background': True,
                       'color_texture': self.preloaddata['vr_fill_mound_tex']
                   })
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.1, 1.0)
        gnode.ambient_color = (1.1, 1.1, 1.0)
        gnode.vignette_outer = (0.7, 0.65, 0.75)
        gnode.vignette_inner = (0.95, 0.95, 0.93)


# ba_meta export plugin
class NewMap(babase.Plugin):
    """My first ballistica plugin!"""

    def on_app_running(self) -> None:
        _map.register_map(ThePadMapb)


class NewBlast(Blast):

    def __init__(self,
                 position: Sequence[float] = (0.0, 1.0, 0.0),
                 velocity: Sequence[float] = (0.0, 0.0, 0.0),
                 blast_radius: float = 2.0,
                 blast_type: str = 'normal',
                 source_player: bs.Player = None,
                 hit_type: str = 'explosion',
                 hit_subtype: str = 'normal'):
        bs.Actor.__init__(self)

        shared = SharedObjects.get()
        factory = BombFactory.get()

        self.blast_type = blast_type
        self._source_player = source_player
        self.hit_type = hit_type
        self.hit_subtype = hit_subtype
        self.radius = blast_radius

        # Set our position a bit lower so we throw more things upward.
        rmats = (factory.blast_material, shared.attack_material)
        self.node = bs.newnode(
            'region',
            delegate=self,
            attrs={
                'position': (position[0], position[1] - 0.1, position[2]),
                'scale': (self.radius, self.radius, self.radius),
                'type': 'sphere',
                'materials': rmats
            },
        )

        bs.timer(0.05, self.node.delete)

        # Throw in an explosion and flash.
        evel = (velocity[0], max(-1.0, velocity[1]), velocity[2])
        explosion = bs.newnode('explosion',
                               attrs={
                                   'position': position,
                                   'velocity': evel,
                                   'radius': self.radius,
                                   'big': (self.blast_type == 'tnt')
                               })
        if self.blast_type == 'ice':
            explosion.color = (0, 0.05, 0.4)

        bs.timer(1.0, explosion.delete)

        if self.blast_type != 'ice':
            bs.emitfx(position=position,
                      velocity=velocity,
                      count=int(1.0 + random.random() * 4),
                      emit_type='tendrils',
                      tendril_type='thin_smoke')
        bs.emitfx(position=position,
                  velocity=velocity,
                  count=int(4.0 + random.random() * 4),
                  emit_type='tendrils',
                  tendril_type='ice' if self.blast_type == 'ice' else 'smoke')
        bs.emitfx(position=position,
                  emit_type='distortion',
                  spread=1.0 if self.blast_type == 'tnt' else 2.0)

        # And emit some shrapnel.
        if self.blast_type == 'ice':

            def emit() -> None:
                bs.emitfx(position=position,
                          velocity=velocity,
                          count=30,
                          spread=2.0,
                          scale=0.4,
                          chunk_type='ice',
                          emit_type='stickers')

            # It looks better if we delay a bit.
            bs.timer(0.05, emit)

        elif self.blast_type == 'sticky':

            def emit() -> None:
                bs.emitfx(position=position,
                          velocity=velocity,
                          count=int(4.0 + random.random() * 8),
                          spread=0.7,
                          chunk_type='slime')
                bs.emitfx(position=position,
                          velocity=velocity,
                          count=int(4.0 + random.random() * 8),
                          scale=0.5,
                          spread=0.7,
                          chunk_type='slime')
                bs.emitfx(position=position,
                          velocity=velocity,
                          count=15,
                          scale=0.6,
                          chunk_type='slime',
                          emit_type='stickers')
                bs.emitfx(position=position,
                          velocity=velocity,
                          count=20,
                          scale=0.7,
                          chunk_type='spark',
                          emit_type='stickers')
                bs.emitfx(position=position,
                          velocity=velocity,
                          count=int(6.0 + random.random() * 12),
                          scale=0.8,
                          spread=1.5,
                          chunk_type='spark')

            # It looks better if we delay a bit.
            bs.timer(0.05, emit)

        elif self.blast_type == 'impact':

            def emit() -> None:
                bs.emitfx(position=position,
                          velocity=velocity,
                          count=int(4.0 + random.random() * 8),
                          scale=0.8,
                          chunk_type='metal')
                bs.emitfx(position=position,
                          velocity=velocity,
                          count=int(4.0 + random.random() * 8),
                          scale=0.4,
                          chunk_type='metal')
                bs.emitfx(position=position,
                          velocity=velocity,
                          count=20,
                          scale=0.7,
                          chunk_type='spark',
                          emit_type='stickers')
                bs.emitfx(position=position,
                          velocity=velocity,
                          count=int(8.0 + random.random() * 15),
                          scale=0.8,
                          spread=1.5,
                          chunk_type='spark')

            # It looks better if we delay a bit.
            bs.timer(0.05, emit)

        else:  # Regular or land mine bomb shrapnel.

            def emit() -> None:
                if self.blast_type != 'tnt':
                    bs.emitfx(position=position,
                              velocity=velocity,
                              count=int(4.0 + random.random() * 8),
                              chunk_type='rock')
                    bs.emitfx(position=position,
                              velocity=velocity,
                              count=int(4.0 + random.random() * 8),
                              scale=0.5,
                              chunk_type='rock')
                bs.emitfx(position=position,
                          velocity=velocity,
                          count=30,
                          scale=1.0 if self.blast_type == 'tnt' else 0.7,
                          chunk_type='spark',
                          emit_type='stickers')
                bs.emitfx(position=position,
                          velocity=velocity,
                          count=int(18.0 + random.random() * 20),
                          scale=1.0 if self.blast_type == 'tnt' else 0.8,
                          spread=1.5,
                          chunk_type='spark')

                # TNT throws splintery chunks.
                if self.blast_type == 'tnt':

                    def emit_splinters() -> None:
                        bs.emitfx(position=position,
                                  velocity=velocity,
                                  count=int(20.0 + random.random() * 25),
                                  scale=0.8,
                                  spread=1.0,
                                  chunk_type='splinter')

                    bs.timer(0.01, emit_splinters)

                # Every now and then do a sparky one.
                if self.blast_type == 'tnt' or random.random() < 0.1:

                    def emit_extra_sparks() -> None:
                        bs.emitfx(position=position,
                                  velocity=velocity,
                                  count=int(10.0 + random.random() * 20),
                                  scale=0.8,
                                  spread=1.5,
                                  chunk_type='spark')

                    bs.timer(0.02, emit_extra_sparks)

            # It looks better if we delay a bit.
            bs.timer(0.05, emit)

        lcolor = ((0.6, 0.6, 1.0) if self.blast_type == 'ice' else
                  (1, 0.3, 0.1))
        light = bs.newnode('light',
                           attrs={
                               'position': position,
                               'volume_intensity_scale': 10.0,
                               'color': lcolor
                           })

        scl = random.uniform(0.6, 0.9)
        scorch_radius = light_radius = self.radius
        if self.blast_type == 'tnt':
            light_radius *= 1.4
            scorch_radius *= 1.15
            scl *= 3.0

        iscale = 1.6
        bs.animate(
            light, 'intensity', {
                0: 2.0 * iscale,
                scl * 0.02: 0.1 * iscale,
                scl * 0.025: 0.2 * iscale,
                scl * 0.05: 17.0 * iscale,
                scl * 0.06: 5.0 * iscale,
                scl * 0.08: 4.0 * iscale,
                scl * 0.2: 0.6 * iscale,
                scl * 2.0: 0.00 * iscale,
                scl * 3.0: 0.0
            })
        bs.animate(
            light, 'radius', {
                0: light_radius * 0.2,
                scl * 0.05: light_radius * 0.55,
                scl * 0.1: light_radius * 0.3,
                scl * 0.3: light_radius * 0.15,
                scl * 1.0: light_radius * 0.05
            })
        bs.timer(scl * 3.0, light.delete)

        # Make a scorch that fades over time.
        scorch = bs.newnode('scorch',
                            attrs={
                                'position': position,
                                'size': scorch_radius * 0.5,
                                'big': (self.blast_type == 'tnt')
                            })
        if self.blast_type == 'ice':
            scorch.color = (1, 1, 1.5)

        bs.animate(scorch, 'presence', {3.000: 1, 13.000: 0})
        bs.timer(13.0, scorch.delete)

        if self.blast_type == 'ice':
            factory.hiss_sound.play(position=light.position)

        lpos = light.position
        factory.random_explode_sound().play(position=lpos)
        factory.debris_fall_sound.play(position=lpos)

        bs.camerashake(0.0)

        # TNT is more epic.
        if self.blast_type == 'tnt':
            factory.random_explode_sound().play(position=lpos)

            def _extra_boom() -> None:
                factory.random_explode_sound().play(position=lpos)

            bs.timer(0.25, _extra_boom)

            def _extra_debris_sound() -> None:
                factory.debris_fall_sound.play(position=lpos)
                factory.wood_debris_fall_sound.play(position=lpos)

            bs.timer(0.4, _extra_debris_sound)


class NewBomb(Bomb):

    def explode(self) -> None:
        """Blows up the bomb if it has not yet done so."""
        if self._exploded:
            return
        self._exploded = True
        if self.node:
            blast = NewBlast(position=self.node.position,
                             velocity=self.node.velocity,
                             blast_radius=self.blast_radius,
                             blast_type=self.bomb_type,
                             source_player=babase.existing(self._source_player),
                             hit_type=self.hit_type,
                             hit_subtype=self.hit_subtype).autoretain()
            for callback in self._explode_callbacks:
                callback(self, blast)

        # We blew up so we need to go away.
        # NOTE TO SELF: do we actually need this delay?
        bs.timer(0.001, bs.WeakCall(self.handlemessage, bs.DieMessage()))


class TNT(bs.Actor):

    def __init__(self,
                 position: Sequence[float] = (0.0, 1.0, 0.0),
                 velocity: Sequence[float] = (0.0, 0.0, 0.0),
                 tnt_scale: float = 1.0,
                 teleport: bool = True):
        super().__init__()
        self.position = position
        self.teleport = teleport

        self._no_collide_material = bs.Material()
        self._no_collide_material.add_actions(
            actions=('modify_part_collision', 'collide', False),
        )
        self._collide_material = bs.Material()
        self._collide_material.add_actions(
            actions=('modify_part_collision', 'collide', True),
        )

        if teleport:
            collide = self._collide_material
        else:
            collide = self._no_collide_material
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': position,
                'velocity': velocity,
                'mesh': bs.getmesh('tnt'),
                'color_texture': bs.gettexture('tnt'),
                'body': 'crate',
                'mesh_scale': tnt_scale,
                'body_scale': tnt_scale,
                'density': 2.0,
                'gravity_scale': 2.0,
                'materials': [collide]
            }
        )
        if not teleport:
            bs.timer(0.1, self._collide)

    def _collide(self) -> None:
        self.node.materials += (self._collide_material,)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.OutOfBoundsMessage):
            if self.teleport:
                self.node.position = self.position
                self.node.velocity = (0, 0, 0)
            else:
                self.node.delete()
        else:
            super().handlemessage(msg)


class RaceRegion(bs.Actor):
    """Region used to track progress during a race."""

    def __init__(self, pt: Sequence[float], index: int):
        super().__init__()
        activity = self.activity
        assert isinstance(activity, RaceGame)
        self.pos = pt
        self.index = index
        self.node = bs.newnode(
            'region',
            delegate=self,
            attrs={
                'position': pt[:3],
                'scale': (pt[3] * 2.0, pt[4] * 2.0, pt[5] * 2.0),
                'type': 'box',
                'materials': [activity.race_region_material]
            })


# MINIGAME
class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.distance_txt: Optional[bs.Node] = None
        self.last_region = 0
        self.lap = 0
        self.distance = 0.0
        self.finished = False
        self.rank: Optional[int] = None


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.time: Optional[float] = None
        self.lap = 0
        self.finished = False


# ba_meta export bascenev1.GameActivity
class RaceGame(bs.TeamGameActivity[Player, Team]):
    """Game of racing around a track."""

    name = 'Hyper Race'
    description = 'Creado Por Cebolla!!'
    scoreconfig = bs.ScoreConfig(label='Time',
                                 lower_is_better=True,
                                 scoretype=bs.ScoreType.MILLISECONDS)

    @classmethod
    def get_available_settings(
            cls, sessiontype: Type[bs.Session]) -> List[babase.Setting]:
        settings = [
            bs.IntSetting('Laps', min_value=1, default=3, increment=1),
            bs.IntChoiceSetting(
                'Time Limit',
                default=0,
                choices=[
                    ('None', 0),
                    ('1 Minute', 60),
                    ('2 Minutes', 120),
                    ('5 Minutes', 300),
                    ('10 Minutes', 600),
                    ('20 Minutes', 1200),
                ],
            ),
            bs.BoolSetting('Epic Mode', default=False),
        ]

        # We have some specific settings in teams mode.
        if issubclass(sessiontype, bs.DualTeamSession):
            settings.append(
                bs.BoolSetting('Entire Team Must Finish', default=False))
        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.MultiTeamSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return bs.app.classic.getmaps('hyper')

    def __init__(self, settings: dict):
        self._race_started = False
        super().__init__(settings)
        self.factory = factory = BombFactory.get()
        self.shared = shared = SharedObjects.get()
        self._scoreboard = Scoreboard()
        self._score_sound = bs.getsound('score')
        self._swipsound = bs.getsound('swip')
        self._last_team_time: Optional[float] = None
        self._front_race_region: Optional[int] = None
        self._nub_tex = bs.gettexture('nub')
        self._beep_1_sound = bs.getsound('raceBeep1')
        self._beep_2_sound = bs.getsound('raceBeep2')
        self.race_region_material: Optional[bs.Material] = None
        self._regions: List[RaceRegion] = []
        self._team_finish_pts: Optional[int] = None
        self._time_text: Optional[bs.Actor] = None
        self._timer: Optional[OnScreenTimer] = None
        self._scoreboard_timer: Optional[bs.Timer] = None
        self._player_order_update_timer: Optional[bs.Timer] = None
        self._start_lights: Optional[List[bs.Node]] = None
        self._laps = int(settings['Laps'])
        self._entire_team_must_finish = bool(
            settings.get('Entire Team Must Finish', False))
        self._time_limit = float(settings['Time Limit'])
        self._epic_mode = bool(settings['Epic Mode'])

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (bs.MusicType.EPIC_RACE
                              if self._epic_mode else bs.MusicType.RACE)

        self._safe_region_material = bs.Material()
        self._safe_region_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(('modify_part_collision', 'collide', True),
                     ('modify_part_collision', 'physical', True))
        )

    def get_instance_description(self) -> Union[str, Sequence]:
        if (isinstance(self.session, bs.DualTeamSession)
                and self._entire_team_must_finish):
            t_str = ' Your entire team has to finish.'
        else:
            t_str = ''

        if self._laps > 1:
            return 'Run ${ARG1} laps.' + t_str, self._laps
        return 'Run 1 lap.' + t_str

    def get_instance_description_short(self) -> Union[str, Sequence]:
        if self._laps > 1:
            return 'run ${ARG1} laps', self._laps
        return 'run 1 lap'

    def on_transition_in(self) -> None:
        super().on_transition_in()
        shared = SharedObjects.get()
        pts = self.map.get_def_points('race_point')
        mat = self.race_region_material = bs.Material()
        mat.add_actions(conditions=('they_have_material',
                                    shared.player_material),
                        actions=(
                            ('modify_part_collision', 'collide', True),
                            ('modify_part_collision', 'physical', False),
                            ('call', 'at_connect',
                             self._handle_race_point_collide),
        ))
        for rpt in pts:
            self._regions.append(RaceRegion(rpt, len(self._regions)))

        bs.newnode(
            'region',
            attrs={
                'position': (0.3, 4.044276501, -2.9),
                'scale': (11.7, 15, 9.5),
                'type': 'box',
                'materials': [self._safe_region_material]
            }
        )

    def _flash_player(self, player: Player, scale: float) -> None:
        assert isinstance(player.actor, PlayerSpaz)
        assert player.actor.node
        pos = player.actor.node.position
        light = bs.newnode('light',
                           attrs={
                               'position': pos,
                               'color': (1, 1, 0),
                               'height_attenuated': False,
                               'radius': 0.4
                           })
        bs.timer(0.5, light.delete)
        bs.animate(light, 'intensity', {0: 0, 0.1: 1.0 * scale, 0.5: 0})

    def _handle_race_point_collide(self) -> None:
        # FIXME: Tidy this up.
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-nested-blocks
        collision = bs.getcollision()
        try:
            region = collision.sourcenode.getdelegate(RaceRegion, True)
            spaz = collision.opposingnode.getdelegate(PlayerSpaz, True)
        except bs.NotFoundError:
            return

        if not spaz.is_alive():
            return

        try:
            player = spaz.getplayer(Player, True)
        except bs.NotFoundError:
            return

        last_region = player.last_region
        this_region = region.index

        if last_region != this_region:

            # If a player tries to skip regions, smite them.
            # Allow a one region leeway though (its plausible players can get
            # blown over a region, etc).
            if this_region > last_region + 2:
                if player.is_alive():
                    assert player.actor
                    player.actor.handlemessage(bs.DieMessage())
                    bs.broadcastmessage(babase.Lstr(
                        translate=('statements', 'Killing ${NAME} for'
                                   ' skipping part of the track!'),
                        subs=[('${NAME}', player.getname(full=True))]),
                        color=(1, 0, 0))
            else:
                # If this player is in first, note that this is the
                # front-most race-point.
                if player.rank == 0:
                    self._front_race_region = this_region

                player.last_region = this_region
                if last_region >= len(self._regions) - 2 and this_region == 0:
                    team = player.team
                    player.lap = min(self._laps, player.lap + 1)

                    # In teams mode with all-must-finish on, the team lap
                    # value is the min of all team players.
                    # Otherwise its the max.
                    if isinstance(self.session, bs.DualTeamSession
                                  ) and self._entire_team_must_finish:
                        team.lap = min([p.lap for p in team.players])
                    else:
                        team.lap = max([p.lap for p in team.players])

                    # A player is finishing.
                    if player.lap == self._laps:

                        # In teams mode, hand out points based on the order
                        # players come in.
                        if isinstance(self.session, bs.DualTeamSession):
                            assert self._team_finish_pts is not None
                            if self._team_finish_pts > 0:
                                self.stats.player_scored(player,
                                                         self._team_finish_pts,
                                                         screenmessage=False)
                            self._team_finish_pts -= 25

                        # Flash where the player is.
                        self._flash_player(player, 1.0)
                        player.finished = True
                        assert player.actor
                        player.actor.handlemessage(
                            bs.DieMessage(immediate=True))

                        # Makes sure noone behind them passes them in rank
                        # while finishing.
                        player.distance = 9999.0

                        # If the whole team has finished the race.
                        if team.lap == self._laps:
                            self._score_sound.play()
                            player.team.finished = True
                            assert self._timer is not None
                            elapsed = bs.time() - self._timer.getstarttime()
                            self._last_team_time = player.team.time = elapsed
                            self._check_end_game()

                        # Team has yet to finish.
                        else:
                            self._swipsound.play()

                    # They've just finished a lap but not the race.
                    else:
                        self._swipsound.play()
                        self._flash_player(player, 0.3)

                        # Print their lap number over their head.
                        try:
                            assert isinstance(player.actor, PlayerSpaz)
                            mathnode = bs.newnode('math',
                                                  owner=player.actor.node,
                                                  attrs={
                                                      'input1': (0, 1.9, 0),
                                                      'operation': 'add'
                                                  })
                            player.actor.node.connectattr(
                                'torso_position', mathnode, 'input2')
                            tstr = babase.Lstr(resource='lapNumberText',
                                               subs=[('${CURRENT}',
                                                      str(player.lap + 1)),
                                                     ('${TOTAL}', str(self._laps))
                                                     ])
                            txtnode = bs.newnode('text',
                                                 owner=mathnode,
                                                 attrs={
                                                     'text': tstr,
                                                     'in_world': True,
                                                     'color': (1, 1, 0, 1),
                                                     'scale': 0.015,
                                                     'h_align': 'center'
                                                 })
                            mathnode.connectattr('output', txtnode, 'position')
                            bs.animate(txtnode, 'scale', {
                                0.0: 0,
                                0.2: 0.019,
                                2.0: 0.019,
                                2.2: 0
                            })
                            bs.timer(2.3, mathnode.delete)
                        except Exception:
                            babase.print_exception('Error printing lap.')

    def on_team_join(self, team: Team) -> None:
        self._update_scoreboard()

    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)

        # A player leaving disqualifies the team if 'Entire Team Must Finish'
        # is on (otherwise in teams mode everyone could just leave except the
        # leading player to win).
        if (isinstance(self.session, bs.DualTeamSession)
                and self._entire_team_must_finish):
            bs.broadcastmessage(babase.Lstr(
                translate=('statements',
                           '${TEAM} is disqualified because ${PLAYER} left'),
                subs=[('${TEAM}', player.team.name),
                      ('${PLAYER}', player.getname(full=True))]),
                color=(1, 1, 0))
            player.team.finished = True
            player.team.time = None
            player.team.lap = 0
            bs.getsound('boo').play()
            for otherplayer in player.team.players:
                otherplayer.lap = 0
                otherplayer.finished = True
                try:
                    if otherplayer.actor is not None:
                        otherplayer.actor.handlemessage(bs.DieMessage())
                except Exception:
                    babase.print_exception('Error sending DieMessage.')

        # Defer so team/player lists will be updated.
        babase.pushcall(self._check_end_game)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            distances = [player.distance for player in team.players]
            if not distances:
                teams_dist = 0.0
            else:
                if (isinstance(self.session, bs.DualTeamSession)
                        and self._entire_team_must_finish):
                    teams_dist = min(distances)
                else:
                    teams_dist = max(distances)
            self._scoreboard.set_team_value(
                team,
                teams_dist,
                self._laps,
                flash=(teams_dist >= float(self._laps)),
                show_value=False)

    def on_begin(self) -> None:
        from bascenev1lib.actor.onscreentimer import OnScreenTimer
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        # self.setup_standard_powerup_drops()
        self._team_finish_pts = 100

        # Throw a timer up on-screen.
        self._time_text = bs.NodeActor(
            bs.newnode('text',
                       attrs={
                           'v_attach': 'top',
                           'h_attach': 'center',
                           'h_align': 'center',
                           'color': (1, 1, 0.5, 1),
                           'flatness': 0.5,
                           'shadow': 0.5,
                           'position': (0, -50),
                           'scale': 1.4,
                           'text': ''
                       }))
        self._timer = OnScreenTimer()

        self._scoreboard_timer = bs.Timer(0.25,
                                          self._update_scoreboard,
                                          repeat=True)
        self._player_order_update_timer = bs.Timer(0.25,
                                                   self._update_player_order,
                                                   repeat=True)

        if self.slow_motion:
            t_scale = 0.4
            light_y = 50
        else:
            t_scale = 1.0
            light_y = 150
        lstart = 7.1 * t_scale
        inc = 1.25 * t_scale

        bs.timer(lstart, self._do_light_1)
        bs.timer(lstart + inc, self._do_light_2)
        bs.timer(lstart + 2 * inc, self._do_light_3)
        bs.timer(lstart + 3 * inc, self._start_race)

        self._start_lights = []
        for i in range(4):
            lnub = bs.newnode('image',
                              attrs={
                                  'texture': bs.gettexture('nub'),
                                  'opacity': 1.0,
                                  'absolute_scale': True,
                                  'position': (-75 + i * 50, light_y),
                                  'scale': (50, 50),
                                  'attach': 'center'
                              })
            bs.animate(
                lnub, 'opacity', {
                    4.0 * t_scale: 0,
                    5.0 * t_scale: 1.0,
                    12.0 * t_scale: 1.0,
                    12.5 * t_scale: 0.0
                })
            bs.timer(13.0 * t_scale, lnub.delete)
            self._start_lights.append(lnub)

        self._obstacles()

        pts = self.map.get_def_points('race_point')
        for rpt in pts:
            bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (rpt[0], 4.382076338, rpt[2]),
                    'size': (rpt[3] * 2.0, 0, rpt[5] * 2.0),
                    'color': (0, 1, 0),
                    'opacity': 1.0,
                    'draw_beauty': False,
                    'additive': True
                }
            )

    def _obstacles(self) -> None:
        self._start_lights[0].color = (0.2, 0, 0)
        self._start_lights[1].color = (0.2, 0, 0)
        self._start_lights[2].color = (0.2, 0.05, 0)
        self._start_lights[3].color = (0.0, 0.3, 0)

        self._tnt((1.5, 5, 2.3), (0, 0, 0), 1.0)
        self._tnt((1.5, 5, 3.3), (0, 0, 0), 1.0)

        self._tnt((3.5, 5, 2.3), (0, 0, 0), 1.0)
        self._tnt((3.5, 5, 3.3), (0, 0, 0), 1.0)

        self._tnt((5.5, 5, 2.3), (0, 0, 0), 1.0)
        self._tnt((5.5, 5, 3.3), (0, 0, 0), 1.0)

        self._tnt((-6, 5, -7), (0, 0, 0), 1.3)
        self._tnt((-7, 5, -5), (0, 0, 0), 1.3)
        self._tnt((-6, 5, -3), (0, 0, 0), 1.3)
        self._tnt((-7, 5, -1), (0, 0, 0), 1.3)
        self._tnt((-6, 5, 1), (0, 0, 0), 1.3)

        bs.timer(0.1, bs.WeakCall(self._tnt, (-3.2, 5, 1),
                                  (0, 0, 0), 1.0, (0, 20, 60)), repeat=True)

        bs.timer(1.6, bs.WeakCall(self._bomb, 'impact',
                                  (6, 7, 1), (0, 0, 0), 1.0, 1.0), repeat=True)
        bs.timer(1.6, bs.WeakCall(self._bomb, 'impact',
                                  (6.8, 7, 1), (0, 0, 0), 1.0, 1.0), repeat=True)
        bs.timer(1.6, bs.WeakCall(self._bomb, 'impact',
                                  (7.6, 7, 1), (0, 0, 0), 1.0, 1.0), repeat=True)

        bs.timer(1.6, bs.WeakCall(self._bomb, 'impact',
                                  (6, 7, -2.2), (0, 0, 0), 1.0, 1.0), repeat=True)
        bs.timer(1.6, bs.WeakCall(self._bomb, 'impact',
                                  (6.8, 7, -2.2), (0, 0, 0), 1.0, 1.0), repeat=True)
        bs.timer(1.6, bs.WeakCall(self._bomb, 'impact',
                                  (7.6, 7, -2.2), (0, 0, 0), 1.0, 1.0), repeat=True)

        bs.timer(1.6, bs.WeakCall(self._bomb, 'impact',
                                  (6, 7, -5.2), (0, 0, 0), 1.0, 1.0), repeat=True)
        bs.timer(1.6, bs.WeakCall(self._bomb, 'impact',
                                  (6.8, 7, -5.2), (0, 0, 0), 1.0, 1.0), repeat=True)
        bs.timer(1.6, bs.WeakCall(self._bomb, 'impact',
                                  (7.6, 7, -5.2), (0, 0, 0), 1.0, 1.0), repeat=True)

        bs.timer(1.6, bs.WeakCall(self._bomb, 'impact',
                                  (6, 7, -8), (0, 0, 0), 1.0, 1.0), repeat=True)
        bs.timer(1.6, bs.WeakCall(self._bomb, 'impact',
                                  (6.8, 7, -8), (0, 0, 0), 1.0, 1.0), repeat=True)
        bs.timer(1.6, bs.WeakCall(self._bomb, 'impact',
                                  (7.6, 7, -8), (0, 0, 0), 1.0, 1.0), repeat=True)

        bs.timer(1.6, bs.WeakCall(self._bomb, 'impact',
                                  (-5, 5, 0), (0, 0, 0), 1.0, 1.0, (0, 20, 3)), repeat=True)
        bs.timer(1.6, bs.WeakCall(self._bomb, 'impact',
                                  (-1.5, 5, 0), (0, 0, 0), 1.0, 1.0, (0, 20, 3)), repeat=True)

        bs.timer(1.6, bs.WeakCall(self._bomb, 'sticky',
                                  (-1, 5, -8), (0, 10, 0), 1.0, 1.0), repeat=True)
        bs.timer(1.6, bs.WeakCall(self._bomb, 'sticky',
                                  (-1, 5, -9), (0, 10, 0), 1.0, 1.0), repeat=True)
        bs.timer(1.6, bs.WeakCall(self._bomb, 'sticky',
                                  (-1, 5, -10), (0, 10, 0), 1.0, 1.0), repeat=True)

        bs.timer(1.6, bs.WeakCall(self._bomb, 'sticky',
                                  (-4.6, 5, -8), (0, 10, 0), 1.0, 1.0), repeat=True)
        bs.timer(1.6, bs.WeakCall(self._bomb, 'sticky',
                                  (-4.6, 5, -9), (0, 10, 0), 1.0, 1.0), repeat=True)
        bs.timer(1.6, bs.WeakCall(self._bomb, 'sticky',
                                  (-4.6, 5, -10), (0, 10, 0), 1.0, 1.0), repeat=True)

        bs.timer(1.6, bs.WeakCall(
            self._powerup, (2, 5, -5), 'curse', (0, 20, -3)), repeat=True)
        bs.timer(1.6, bs.WeakCall(
            self._powerup, (4, 5, -5), 'curse', (0, 20, -3)), repeat=True)

    def _tnt(self,
             position: float,
             velocity: float,
             tnt_scale: float,
             extra_acceleration: float = None) -> None:
        if extra_acceleration:
            TNT(position, velocity, tnt_scale, False).autoretain(
            ).node.extra_acceleration = extra_acceleration
        else:
            TNT(position, velocity, tnt_scale).autoretain()

    def _bomb(self,
              type: str,
              position: float,
              velocity: float,
              mesh_scale: float,
              body_scale: float,
              extra_acceleration: float = None) -> None:
        if extra_acceleration:
            NewBomb(position=position,
                    velocity=velocity,
                    bomb_type=type).autoretain(
            ).node.extra_acceleration = extra_acceleration
        else:
            NewBomb(position=position,
                    velocity=velocity,
                    bomb_type=type).autoretain()

    def _powerup(self,
                 position: float,
                 poweruptype: str,
                 extra_acceleration: float = None) -> None:
        if extra_acceleration:
            PowerupBox(position=position,
                       poweruptype=poweruptype).autoretain(
            ).node.extra_acceleration = extra_acceleration
        else:
            PowerupBox(position=position, poweruptype=poweruptype).autoretain()

    def _do_light_1(self) -> None:
        assert self._start_lights is not None
        self._start_lights[0].color = (1.0, 0, 0)
        self._beep_1_sound.play()

    def _do_light_2(self) -> None:
        assert self._start_lights is not None
        self._start_lights[1].color = (1.0, 0, 0)
        self._beep_1_sound.play()

    def _do_light_3(self) -> None:
        assert self._start_lights is not None
        self._start_lights[2].color = (1.0, 0.3, 0)
        self._beep_1_sound.play()

    def _start_race(self) -> None:
        assert self._start_lights is not None
        self._start_lights[3].color = (0.0, 1.0, 0)
        self._beep_2_sound.play()
        for player in self.players:
            if player.actor is not None:
                try:
                    assert isinstance(player.actor, PlayerSpaz)
                    player.actor.connect_controls_to_player()
                except Exception:
                    babase.print_exception('Error in race player connects.')
        assert self._timer is not None
        self._timer.start()

        self._race_started = True

    def _update_player_order(self) -> None:

        # Calc all player distances.
        for player in self.players:
            pos: Optional[babase.Vec3]
            try:
                pos = player.position
            except bs.NotFoundError:
                pos = None
            if pos is not None:
                r_index = player.last_region
                rg1 = self._regions[r_index]
                r1pt = babase.Vec3(rg1.pos[:3])
                rg2 = self._regions[0] if r_index == len(
                    self._regions) - 1 else self._regions[r_index + 1]
                r2pt = babase.Vec3(rg2.pos[:3])
                r2dist = (pos - r2pt).length()
                amt = 1.0 - (r2dist / (r2pt - r1pt).length())
                amt = player.lap + (r_index + amt) * (1.0 / len(self._regions))
                player.distance = amt

        # Sort players by distance and update their ranks.
        p_list = [(player.distance, player) for player in self.players]

        p_list.sort(reverse=True, key=lambda x: x[0])
        for i, plr in enumerate(p_list):
            plr[1].rank = i
            if plr[1].actor:
                node = plr[1].distance_txt
                if node:
                    node.text = str(i + 1) if plr[1].is_alive() else ''

    def spawn_player(self, player: Player) -> bs.Actor:
        if player.team.finished:
            # FIXME: This is not type-safe!
            #   This call is expected to always return an Actor!
            #   Perhaps we need something like can_spawn_player()...
            # noinspection PyTypeChecker
            return None  # type: ignore
        pos = self._regions[player.last_region].pos

        # Don't use the full region so we're less likely to spawn off a cliff.
        region_scale = 0.8
        x_range = ((-0.5, 0.5) if pos[3] == 0 else
                   (-region_scale * pos[3], region_scale * pos[3]))
        z_range = ((-0.5, 0.5) if pos[5] == 0 else
                   (-region_scale * pos[5], region_scale * pos[5]))
        pos = (pos[0] + random.uniform(*x_range), pos[1],
               pos[2] + random.uniform(*z_range))
        spaz = self.spawn_player_spaz(
            player, position=pos, angle=90 if not self._race_started else None)
        assert spaz.node

        # Prevent controlling of characters before the start of the race.
        if not self._race_started:
            spaz.disconnect_controls_from_player()

        mathnode = bs.newnode('math',
                              owner=spaz.node,
                              attrs={
                                  'input1': (0, 1.4, 0),
                                  'operation': 'add'
                              })
        spaz.node.connectattr('torso_position', mathnode, 'input2')

        distance_txt = bs.newnode('text',
                                  owner=spaz.node,
                                  attrs={
                                      'text': '',
                                      'in_world': True,
                                      'color': (1, 1, 0.4),
                                      'scale': 0.02,
                                      'h_align': 'center'
                                  })
        player.distance_txt = distance_txt
        mathnode.connectattr('output', distance_txt, 'position')
        return spaz

    def _check_end_game(self) -> None:

        # If there's no teams left racing, finish.
        teams_still_in = len([t for t in self.teams if not t.finished])
        if teams_still_in == 0:
            self.end_game()
            return

        # Count the number of teams that have completed the race.
        teams_completed = len(
            [t for t in self.teams if t.finished and t.time is not None])

        if teams_completed > 0:
            session = self.session

            # In teams mode its over as soon as any team finishes the race

            # FIXME: The get_ffa_point_awards code looks dangerous.
            if isinstance(session, bs.DualTeamSession):
                self.end_game()
            else:
                # In ffa we keep the race going while there's still any points
                # to be handed out. Find out how many points we have to award
                # and how many teams have finished, and once that matches
                # we're done.
                assert isinstance(session, bs.FreeForAllSession)
                points_to_award = len(session.get_ffa_point_awards())
                if teams_completed >= points_to_award - teams_completed:
                    self.end_game()
                    return

    def end_game(self) -> None:

        # Stop updating our time text, and set it to show the exact last
        # finish time if we have one. (so users don't get upset if their
        # final time differs from what they see onscreen by a tiny amount)
        assert self._timer is not None
        if self._timer.has_started():
            self._timer.stop(
                endtime=None if self._last_team_time is None else (
                    self._timer.getstarttime() + self._last_team_time))

        results = bs.GameResults()

        for team in self.teams:
            if team.time is not None:
                # We store time in seconds, but pass a score in milliseconds.
                results.set_team_score(team, int(team.time * 1000.0))
            else:
                results.set_team_score(team, None)

        # We don't announce a winner in ffa mode since its probably been a
        # while since the first place guy crossed the finish line so it seems
        # odd to be announcing that now.
        self.end(results=results,
                 announce_winning_team=isinstance(self.session,
                                                  bs.DualTeamSession))

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment default behavior.
            super().handlemessage(msg)
            player = msg.getplayer(Player)
            if not player.finished:
                self.respawn_player(player, respawn_time=1)
        else:
            super().handlemessage(msg)
