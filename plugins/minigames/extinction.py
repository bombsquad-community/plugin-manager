# Ported to api 8 by brostos using baport.(https://github.com/bombsquad-community/baport)
"""For 1.7.33"""

# ba_meta require api 8

from __future__ import annotations
from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs
import random
from bascenev1lib.actor.bomb import BombFactory, Blast, ImpactMessage
from bascenev1lib.actor.onscreentimer import OnScreenTimer
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence, Optional, Type


class Meteor(bs.Actor):
    """A giant meteor instead of bombs."""

    def __init__(self,
                 pos: Sequence[float] = (0.0, 1.0, 0.0),
                 velocity: Sequence[float] = (0.0, 0.0, 0.0)):
        super().__init__()

        shared = SharedObjects.get()
        factory = BombFactory.get()

        materials = (shared.object_material,
                     factory.impact_blast_material)

        self.pos = (pos[0], pos[1], pos[2])
        self.velocity = (velocity[0], velocity[1], velocity[2])

        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': self.pos,
                'velocity': self.velocity,
                'mesh': factory.sticky_bomb_mesh,
                'color_texture': factory.tnt_tex,
                'mesh_scale': 3.0,
                'body_scale': 2.99,
                'body': 'sphere',
                'shadow_size': 0.5,
                'reflection': 'soft',
                'reflection_scale': [0.45],
                'materials': materials
            })

    def explode(self) -> None:
        Blast(position=self.node.position,
              velocity=self.node.velocity,
              blast_type='tnt',
              blast_radius=2.0)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        elif isinstance(msg, ImpactMessage):
            self.explode()
            self.handlemessage(bs.DieMessage())
        else:
            super().handlemessage(msg)


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self):
        super().__init__()
        self.death_time: Optional[float] = None


class Team(bs.Team[Player]):
    """Our team type for this game."""


# ba_meta export bascenev1.GameActivity
class NewMeteorShowerGame(bs.TeamGameActivity[Player, Team]):
    """Minigame by Jetz."""

    name = 'Extinction'
    description = 'Survive the Extinction.'
    available_settings = [
        bs.BoolSetting('Epic Mode', default=False)]

    announce_player_deaths = True

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return ['Football Stadium']

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return (issubclass(sessiontype, bs.FreeForAllSession)
                or issubclass(sessiontype, bs.DualTeamSession))

    def __init__(self, settings: dict):
        super().__init__(settings)

        self._epic_mode = bool(settings['Epic Mode'])
        self._last_player_death_time: Optiobal[float] = None
        self._meteor_time = 2.0
        self._timer: Optional[OnScreenTimer] = None

        self.default_music = (bs.MusicType.EPIC
                              if self._epic_mode else bs.MusicType.SURVIVAL)

        if self._epic_mode:
            self.slow_motion = True

    def on_begin(self) -> None:
        super().on_begin()

        delay = 5.0 if len(self.players) > 2 else 2.5
        if self._epic_mode:
            delay *= 0.25
        bs.timer(delay, self._decrement_meteor_time, repeat=True)

        delay = 3.0
        if self._epic_mode:
            delay *= 0.25
        bs.timer(delay, self._set_meteor_timer)

        self._timer = OnScreenTimer()
        self._timer.start()
        self._check_end_game()

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
        self.spawn_player(player)

    def spawn_player(self, player: Player) -> None:
        spaz = self.spawn_player_spaz(player)

        spaz.connect_controls_to_player(enable_punch=False,
                                        enable_pickup=False,
                                        enable_bomb=False,
                                        enable_jump=False)
        spaz.play_big_death_sound = True

        return spaz

    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)

        self._check_end_game()

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            curtime = bs.time()

            msg.getplayer(Player).death_time = curtime
            bs.timer(1.0, self._check_end_game)
        else:
            return super().handlemessage(msg)

    def _spawn_meteors(self) -> None:
        pos = (random.randint(-6, 7), 12,
               random.uniform(-2, 1))
        velocity = (random.randint(-11, 11), 0,
                    random.uniform(-5, 5))
        Meteor(pos=pos, velocity=velocity).autoretain()

    def _spawn_meteors_cluster(self) -> None:
        delay = 0.0
        for _i in range(random.randrange(1, 3)):
            bs.timer(delay, self._spawn_meteors)
            delay += 1
        self._set_meteor_timer()

    def _decrement_meteor_time(self) -> None:
        self._meteor_time = max(0.01, self._meteor_time * 0.9)

    def _set_meteor_timer(self) -> None:
        bs.timer((1.0 + 0.2 * random.random()) * self._meteor_time,
                 self._spawn_meteors_cluster)

    def _check_end_game(self) -> None:
        living_team_count = 0
        for team in self.teams:
            for player in team.players:
                if player.is_alive():
                    living_team_count += 1
                    break

        if isinstance(self.session, bs.CoopSession):
            if living_team_count <= 0:
                self.end_game()
        else:
            if living_team_count <= 1:
                self.end_game()

    def end_game(self) -> None:
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
                    score += 50
                self.stats.player_scored(player, score, screenmessage=False)

        self._timer.stop(endtime=self._last_player_death_time)

        results = bs.GameResults()

        for team in self.teams:

            longest_life = 0.0
            for player in team.players:
                assert player.death_time is not None
                longest_life = max(longest_life,
                                   player.death_time - start_time)

            results.set_team_score(team, int(1000.0 * longest_life))

        self.end(results=results)


# ba_meta export plugin
class plugin(babase.Plugin):
    def __init__(self):
        ## Campaign support ##
        babase.app.classic.add_coop_practice_level(bs.Level(
            name='Extinction',
            gametype=NewMeteorShowerGame,
            settings={'Epic Mode': False},
            preview_texture_name='footballStadiumPreview'))
        babase.app.classic.add_coop_practice_level(bs.Level('Epic Extinction',
                                                            gametype=NewMeteorShowerGame,
                                                            settings={'Epic Mode': True},
                                                            preview_texture_name='footballStadiumPreview'))
