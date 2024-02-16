# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
"""Dark fields mini-game."""

# Minigame by Froshlee14
# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations
import random
from typing import TYPE_CHECKING

import _babase
import babase
import bauiv1 as bui
import bascenev1 as bs
from bascenev1lib.actor import bomb
from bascenev1._music import setmusic
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1._gameutils import animate_array
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.playerspaz import PlayerSpaz

if TYPE_CHECKING:
    from typing import Any, Sequence, Optional, List, Dict, Type, Type


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0

# ba_meta export bascenev1.GameActivity


class DarkFieldsGame(bs.TeamGameActivity[Player, Team]):

    name = 'Dark Fields'
    description = 'Get to the other side.'
    available_settings = [
        bs.IntSetting('Score to Win',
                      min_value=1,
                      default=3,
                      ),
        bs.IntChoiceSetting('Time Limit',
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
        bs.FloatChoiceSetting('Respawn Times',
                              choices=[
                                  ('Shorter', 0.25),
                                  ('Short', 0.5),
                                  ('Normal', 1.0),
                                  ('Long', 2.0),
                                  ('Longer', 4.0),
                              ],
                              default=1.0,
                              ),
        bs.BoolSetting('Epic Mode', default=False),
        bs.BoolSetting('Players as center of interest', default=True),
    ]

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return bs.app.classic.getmaps('football')

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return (issubclass(sessiontype, bs.DualTeamSession)
                or issubclass(sessiontype, bs.FreeForAllSession))

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._epic_mode = bool(settings['Epic Mode'])
        self._center_of_interest = bool(settings['Players as center of interest'])
        self._score_to_win_per_player = int(settings['Score to Win'])
        self._time_limit = float(settings['Time Limit'])

        self._scoreboard = Scoreboard()

        shared = SharedObjects.get()

        self._scoreRegionMaterial = bs.Material()
        self._scoreRegionMaterial.add_actions(
            conditions=("they_have_material", shared.player_material),
            actions=(("modify_part_collision", "collide", True),
                     ("modify_part_collision", "physical", False),
                     ("call", "at_connect", self._onPlayerScores)))

        self.slow_motion = self._epic_mode
        self.default_music = (bs.MusicType.EPIC if self._epic_mode else None)

    def on_transition_in(self) -> None:
        super().on_transition_in()
        gnode = bs.getactivity().globalsnode
        gnode.tint = (0.5, 0.5, 0.5)

        a = bs.newnode('locator', attrs={'shape': 'box', 'position': (12.2, 0, .1087926362),
                                         'color': (5, 0, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': [2.5, 0.1, 12.8]})

        b = bs.newnode('locator', attrs={'shape': 'box', 'position': (-12.1, 0, .1087926362),
                                         'color': (0, 0, 5), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': [2.5, 0.1, 12.8]})

    def on_begin(self) -> None:
        self._has_begun = False
        super().on_begin()

        self.setup_standard_time_limit(self._time_limit)
        self._score_to_win = (self._score_to_win_per_player *
                              max(1, max(len(t.players) for t in self.teams)))
        self._update_scoreboard()

        self.isUpdatingMines = False
        self._scoreSound = bs.getsound('dingSmall')

        for p in self.players:
            if p.actor is not None:
                try:
                    p.actor.disconnect_controls_from_player()
                except Exception:
                    print('Can\'t connect to player')

        self._scoreRegions = []
        defs = bs.getactivity().map.defs
        self._scoreRegions.append(bs.NodeActor(bs.newnode('region',
                                                          attrs={'position': defs.boxes['goal1'][0:3],
                                                                 'scale': defs.boxes['goal1'][6:9],
                                                                 'type': 'box',
                                                                 'materials': (self._scoreRegionMaterial,)})))
        self.mines = []
        self.spawnMines()
        bs.timer(0.8 if self.slow_motion else 1.7, self.start)

    def start(self):
        self._has_begun = True
        self._show_info()
        bs.timer(random.randrange(3, 7), self.doRandomLighting)
        if not self._epic_mode:
            setmusic(bs.MusicType.SCARY)
        animate_array(bs.getactivity().globalsnode, 'tint', 3,
                      {0: (0.5, 0.5, 0.5), 2: (0.2, 0.2, 0.2)})

        for p in self.players:
            self.doPlayer(p)

    def spawn_player(self, player):
        if not self._has_begun:
            return
        else:
            self.doPlayer(player)

    def doPlayer(self, player):
        pos = (-12.4, 1, random.randrange(-5, 5))
        player = self.spawn_player_spaz(player, pos)
        player.connect_controls_to_player(enable_punch=False, enable_bomb=False)
        player.node.is_area_of_interest = self._center_of_interest

    def _show_info(self) -> None:
        if self._has_begun:
            super()._show_info()

    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self._update_scoreboard()

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score, self._score_to_win)

    def doRandomLighting(self):
        bs.timer(random.randrange(3, 7), self.doRandomLighting)
        if self.isUpdatingMines:
            return

        delay = 0
        for mine in self.mines:
            if mine.node.exists():
                pos = mine.node.position
                bs.timer(delay, babase.Call(self.do_light, pos))
                delay += 0.005 if self._epic_mode else 0.01

    def do_light(self, pos):
        light = bs.newnode('light', attrs={
            'position': pos,
            'volume_intensity_scale': 1.0,
            'radius': 0.1,
            'color': (1, 0, 0)
        })
        bs.animate(light, 'intensity', {0: 2.0, 3.0: 0.0})
        bs.timer(3.0, light.delete)

    def spawnMines(self):
        delay = 0
        h_range = [10, 8, 6, 4, 2, 0, -2, -4, -6, -8, -10]
        for h in h_range:
            for i in range(random.randint(3, 4)):
                x = h+random.random()
                y = random.randrange(-5, 6)+(random.random())
                pos = (x, 1, y)
                bs.timer(delay, babase.Call(self.doMine, pos))
                delay += 0.015 if self._epic_mode else 0.04
        bs.timer(5.0, self.stopUpdateMines)

    def stopUpdateMines(self):
        self.isUpdatingMines = False

    def updateMines(self):
        if self.isUpdatingMines:
            return
        self.isUpdatingMines = True
        for m in self.mines:
            m.node.delete()
        self.mines = []
        self.spawnMines()

    def doMine(self, pos):
        b = bomb.Bomb(position=pos, bomb_type='land_mine').autoretain()
        b.add_explode_callback(self._on_bomb_exploded)
        b.arm()
        self.mines.append(b)

    def _on_bomb_exploded(self, bomb: Bomb, blast: Blast) -> None:
        assert blast.node
        p = blast.node.position
        pos = (p[0], p[1]+1, p[2])
        bs.timer(0.5, babase.Call(self.doMine, pos))

    def _onPlayerScores(self):
        player: Optional[Player]
        try:
            player = bs.getcollision().opposingnode.getdelegate(PlayerSpaz, True).getplayer(Player, True)
        except bs.NotFoundError:
            player = None
        if player.exists() and player.is_alive():
            player.team.score += 1
            self._scoreSound.play()
            pos = player.actor.node.position

            animate_array(bs.getactivity().globalsnode, 'tint', 3, {
                          0: (0.5, 0.5, 0.5), 2.8: (0.2, 0.2, 0.2)})
            self._update_scoreboard()

            light = bs.newnode('light',
                               attrs={
                                   'position': pos,
                                   'radius': 0.5,
                                   'color': (1, 0, 0)
                               })
            bs.animate(light, 'intensity', {0.0: 0, 0.1: 1, 0.5: 0}, loop=False)
            bs.timer(1.0, light.delete)

            player.actor.handlemessage(bs.DieMessage(how=bs.DeathType.REACHED_GOAL))
            self.updateMines()

            if any(team.score >= self._score_to_win for team in self.teams):
                bs.timer(0.5, self.end_game)

    def handlemessage(self, msg: Any) -> Any:

        if isinstance(msg, bs.PlayerDiedMessage):

            # Augment standard behavior.
            super().handlemessage(msg)

            player = msg.getplayer(Player)
            self.respawn_player(player)

        else:
            return super().handlemessage(msg)
        return None

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)
