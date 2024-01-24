# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs
import random
from bascenev1lib.actor.bomb import BombFactory, Bomb
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.onscreentimer import OnScreenTimer

if TYPE_CHECKING:
    from typing import Any, Sequence, Optional, List, Dict, Type, Type


class _GotTouched():
    pass


class UFO(bs.Actor):

    def __init__(self, pos: float = (0, 0, 0)):
        super().__init__()
        shared = SharedObjects.get()
        self.r: Optional[int] = 0
        self.dis: Optional[List] = []
        self.target: float = (0.0, 0.0, 0.0)
        self.regs: List[bs.NodeActor] = []
        self.node = bs.newnode('prop',
                               delegate=self,
                               attrs={'body': 'landMine',
                                      'position': pos,
                                      'mesh': bs.getmesh('landMine'),
                                      'mesh_scale': 1.5,
                                      'body_scale': 0.01,
                                      'shadow_size': 0.000001,
                                      'gravity_scale': 0.0,
                                      'color_texture': bs.gettexture("achievementCrossHair"),
                                      'materials': [shared.object_material]})
        self.ufo_collide = None

    def create_target(self):
        if not self.node.exists():
            return
        self.dis = []
        shared = SharedObjects.get()
        try:
            def pass_():
                self.regs.clear()
                bs.timer(3875*0.001, self.move)
                try:
                    bs.timer(3277*0.001, lambda: Bomb(velocity=(0, 0, 0), position=(
                        self.target[0], self.node.position[1]-0.43999, self.target[2]), bomb_type='impact').autoretain().arm())
                except:
                    pass
            key = bs.Material()
            key.add_actions(
                conditions=('they_have_material', shared.object_material),
                actions=(
                        ('modify_part_collision', 'collide', True),
                        ('modify_part_collision', 'physical', False),
                        ('call', 'at_connect', pass_()),
                ))
        except:
            pass
        self.regs.append(bs.NodeActor(bs.newnode('region',
                                                 attrs={
                                                     'position': self.target,
                                                     'scale': (0.04, 22, 0.04),
                                                     'type': 'sphere',
                                                     'materials': [key]})))

    def move(self):
        if not self.node.exists():
            return
        try:
            self.create_target()
            for j in bs.getnodes():
                n = j.getdelegate(object)
                if j.getnodetype() == 'prop' and isinstance(n, TileFloor):
                    if n.node.exists():
                        self.dis.append(n.node)
            self.r = random.randint(0, len(self.dis)-1)
            self.target = (self.dis[self.r].position[0],
                           self.node.position[1], self.dis[self.r].position[2])
            bs.animate_array(self.node, 'position', 3, {
                0: self.node.position,
                3.0: self.target})
        except:
            pass

    def handlemessage(self, msg):

        if isinstance(msg, bs.DieMessage):
            self.node.delete()
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        else:
            super().handlemessage(msg)


class TileFloor(bs.Actor):
    def __init__(self,
                 pos: float = (0, 0, 0)):
        super().__init__()
        get_mat = SharedObjects.get()
        self.pos = pos
        self.scale = 1.5
        self.mat, self.mat2, self.test = bs.Material(), bs.Material(), bs.Material()
        self.mat.add_actions(conditions=('we_are_older_than', 1),
                             actions=(('modify_part_collision', 'collide', False)))
        self.mat2.add_actions(conditions=('we_are_older_than', 1),
                              actions=(('modify_part_collision', 'collide', True)))
        self.test.add_actions(
            conditions=('they_have_material', BombFactory.get().bomb_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', _GotTouched())))
        self.node = bs.newnode('prop',
                               delegate=self,
                               attrs={'body': 'puck',
                                      'position': self.pos,
                                      'mesh': bs.getmesh('buttonSquareOpaque'),
                                      'mesh_scale': self.scale*1.16,
                                      'body_scale': self.scale,
                                      'shadow_size': 0.0002,
                                      'gravity_scale': 0.0,
                                      'color_texture': bs.gettexture("tnt"),
                                      'is_area_of_interest': True,
                                      'materials': [self.mat, self.test]})
        self.node_support = bs.newnode('region',
                                       attrs={
                                           'position': self.pos,
                                           'scale': (self.scale*0.8918, 0.1, self.scale*0.8918),
                                           'type': 'box',
                                           'materials': [get_mat.footing_material, self.mat2]
                                       })

    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            self.node.delete()
            self.node_support.delete()
        elif isinstance(msg, _GotTouched):
            def do(): self.handlemessage(bs.DieMessage())
            bs.timer(0.1, do)
        else:
            super().handlemessage(msg)


class defs():
    points = boxes = {}
    boxes['area_of_interest_bounds'] = (-1.3440, 1.185751251, 3.7326226188) + (
        0.0, 0.0, 0.0) + (29.8180273, 15.57249038, 22.93859993)
    boxes['map_bounds'] = (0.0, 2.585751251, 0.4326226188) + (0.0, 0.0,
                                                              0.0) + (29.09506485, 15.81173179, 33.76723155)


class DummyMapForGame(bs.Map):
    defs, name = defs(), 'Tile Lands'

    @classmethod
    def get_play_types(cls) -> List[str]:
        return []

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'achievementCrossHair'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {'bg_1': bs.gettexture('rampageBGColor'), 'bg_2': bs.gettexture(
            'rampageBGColor2'), 'bg_mesh_1': bs.getmesh('rampageBG'), 'bg_mesh_2': bs.getmesh('rampageBG2'), }
        return data

    def __init__(self) -> None:
        super().__init__()
        self.bg1 = bs.newnode('terrain', attrs={
                              'mesh': self.preloaddata['bg_mesh_1'], 'lighting': False, 'background': True, 'color_texture': self.preloaddata['bg_2']})
        self.bg2 = bs.newnode('terrain', attrs={
                              'mesh': self.preloaddata['bg_mesh_2'], 'lighting': False, 'background': True, 'color_texture': self.preloaddata['bg_2']})
        a = bs.getactivity().globalsnode
        a.tint, a.ambient_color, a.vignette_outer, a.vignette_inner = (
            1.2, 1.1, 0.97), (1.3, 1.2, 1.03), (0.62, 0.64, 0.69), (0.97, 0.95, 0.93)


class DummyMapForGame2(bs.Map):
    defs, name = defs(), 'Tile Lands Night'

    @classmethod
    def get_play_types(cls) -> List[str]:
        return []

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'achievementCrossHair'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {'bg_1': bs.gettexture('menuBG'), 'bg_2': bs.gettexture(
            'menuBG'), 'bg_mesh_1': bs.getmesh('thePadBG'), 'bg_mesh_2': bs.getmesh('thePadBG'), }
        return data

    def __init__(self) -> None:
        super().__init__()
        self.bg1 = bs.newnode('terrain', attrs={
                              'mesh': self.preloaddata['bg_mesh_1'], 'lighting': False, 'background': True, 'color_texture': self.preloaddata['bg_2']})
        self.bg2 = bs.newnode('terrain', attrs={
                              'mesh': self.preloaddata['bg_mesh_2'], 'lighting': False, 'background': True, 'color_texture': self.preloaddata['bg_2']})
        a = bs.getactivity().globalsnode
        a.tint, a.ambient_color, a.vignette_outer, a.vignette_inner = (
            0.5, 0.7, 1.27), (2.5, 2.5, 2.5), (0.62, 0.64, 0.69), (0.97, 0.95, 0.93)


bs._map.register_map(DummyMapForGame)
bs._map.register_map(DummyMapForGame2)


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        super().__init__()
        self.death_time: Optional[float] = None


class Team(bs.Team[Player]):
    """Our team type for this game."""


# ba_meta export bascenev1.GameActivity
class UFOAttackGame(bs.TeamGameActivity[Player, Team]):

    name = 'UFO Attack'
    description = 'Dodge the falling bombs.'
    available_settings = [
        bs.BoolSetting('Epic Mode', default=False),
        bs.BoolSetting('Enable Run', default=True),
        bs.BoolSetting('Enable Jump', default=True),
        bs.BoolSetting('Display Map Area Dimension', default=False),
        bs.IntSetting('No. of Rows' + u' →', max_value=13, min_value=1, default=8, increment=1),
        bs.IntSetting('No. of Columns' + u' ↓', max_value=12, min_value=1, default=6, increment=1)
    ]
    scoreconfig = bs.ScoreConfig(label='Survived',
                                 scoretype=bs.ScoreType.SECONDS,
                                 version='B')

    # Print messages when players die (since its meaningful in this game).
    announce_player_deaths = True

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return ['Tile Lands', 'Tile Lands Night']

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return (issubclass(sessiontype, bs.DualTeamSession)
                or issubclass(sessiontype, bs.FreeForAllSession))

    def __init__(self, settings: dict):
        super().__init__(settings)

        self.col = int(settings['No. of Columns' + u' ↓'])
        self.row = int(settings['No. of Rows' + u' →'])
        self.bool1 = bool(settings['Enable Run'])
        self.bool2 = bool(settings['Enable Jump'])
        self._epic_mode = settings.get('Epic Mode', False)
        self._last_player_death_time: Optional[float] = None
        self._timer: Optional[OnScreenTimer] = None
        self.default_music = (bs.MusicType.EPIC
                              if self._epic_mode else bs.MusicType.SURVIVAL)
        if bool(settings["Display Map Area Dimension"]):
            self.game_name = "UFO Attack " + "(" + str(self.col) + "x" + str(self.row) + ")"
        else:
            self.game_name = "UFO Attack"
        if self._epic_mode:
            self.slow_motion = True

    def get_instance_display_string(self) -> babase.Lstr:
        return self.game_name

    def on_begin(self) -> None:
        super().on_begin()
        self._timer = OnScreenTimer()
        self._timer.start()
        # bs.timer(5.0, self._check_end_game)
        for r in range(self.col):
            for j in range(self.row):
                tile = TileFloor(pos=(-6.204283+(j*1.399), 3.425666,
                                      -1.3538+(r*1.399))).autoretain()
        self.ufo = UFO(pos=(-5.00410667, 6.616383286, -2.503472)).autoretain()
        bs.timer(7000*0.001, lambda: self.ufo.move())
        for t in self.players:
            self.spawn_player(t)

    def on_player_join(self, player: Player) -> None:
        if self.has_begun():
            bs.broadcastmessage(
                babase.Lstr(resource='playerDelayedJoinText',
                            subs=[('${PLAYER}', player.getname(full=True))]),
                color=(0, 1, 0),
            )
            assert self._timer is not None
            player.death_time = self._timer.getstarttime()
            return

    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        self._check_end_game()

    def spawn_player(self, player: Player) -> bs.Actor:
        dis = []
        for a in bs.getnodes():
            g = a.getdelegate(object)
            if a.getnodetype() == 'prop' and isinstance(g, TileFloor):
                dis.append(g.node)
        r = random.randint(0, len(dis)-1)
        spaz = self.spawn_player_spaz(player, position=(
            dis[r].position[0], dis[r].position[1]+1.005958, dis[r].position[2]))
        spaz.connect_controls_to_player(enable_punch=False,
                                        enable_bomb=False,
                                        enable_run=self.bool1,
                                        enable_jump=self.bool2,
                                        enable_pickup=False)
        spaz.play_big_death_sound = True
        return spaz

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)

            curtime = bs.time()
            msg.getplayer(Player).death_time = curtime
            bs.timer(1.0, self._check_end_game)

        else:
            return super().handlemessage(msg)
        return None

    def _check_end_game(self) -> None:
        living_team_count = 0
        for team in self.teams:
            for player in team.players:
                if player.is_alive():
                    living_team_count += 1
                    break
        if living_team_count <= 1:
            self.end_game()

    def end_game(self) -> None:
        self.ufo.handlemessage(bs.DieMessage())
        cur_time = bs.time()
        assert self._timer is not None
        start_time = self._timer.getstarttime()
        for team in self.teams:
            for player in team.players:
                survived = False
                if player.death_time is None:
                    survived = True
                    player.death_time = cur_time + 1
                score = int(player.death_time - self._timer.getstarttime())
                if survived:
                    score += 2
                self.stats.player_scored(player, score, screenmessage=False)
        self._timer.stop(endtime=self._last_player_death_time)
        results = bs.GameResults()
        for team in self.teams:
            longest_life = 0.0
            for player in team.players:
                assert player.death_time is not None
                longest_life = max(longest_life,
                                   player.death_time - start_time)

            # Submit the score value in milliseconds.
            results.set_team_score(team, int(longest_life))

        self.end(results=results)
