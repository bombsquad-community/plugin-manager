# ba_meta require api 9
from __future__ import annotations
from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
import random
from bascenev1lib.actor.spazbot import SpazBotSet, SpazBot, SpazBotDiedMessage
from bascenev1lib.actor.onscreentimer import OnScreenTimer

if TYPE_CHECKING:
    from typing import Any, List, Type, Optional


class Player(bs.Player['Team']):
    """Our player type for this game"""

    def __init__(self) -> None:
        super().__init__()
        self.death_time: Optional[float] = None


class MrSpazBot(SpazBot):
    """Our bot type for this game"""
    character = 'Spaz'
    run = True
    charge_dist_min = 10.0
    charge_dist_max = 9999.0
    charge_speed_min = 1.0
    charge_speed_max = 1.0
    throw_dist_min = 9999
    throw_dist_max = 9999


class Team(bs.Team[Player]):
    """Our team type for this minigame"""


# ba_meta export bascenev1.GameActivity
class BotChaseGame(bs.TeamGameActivity[Player, Team]):
    """Our goal is to survive from spawning bots"""
    name = 'Bot Chase'
    description = 'Try to survive from bots!'
    available_settings = [
        bs.BoolSetting(
            'Epic Mode',
            default=False
        ),
    ]

    announce_player_deaths = True

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return ['Football Stadium']

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        # Coop session unused
        return (issubclass(sessiontype, bs.FreeForAllSession) or issubclass(sessiontype, bs.DualTeamSession) or issubclass(sessiontype, bs.CoopSession))

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._bots = SpazBotSet()
        self._epic_mode = bool(settings['Epic Mode'])
        self._timer: Optional[OnScreenTimer] = None
        self._last_player_death_time: Optional[float] = None

        if self._epic_mode:
            self.slow_motion = True
        self.default_music = (bs.MusicType.EPIC if self._epic_mode else bs.MusicType.FORWARD_MARCH)

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

    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        self._check_end_game()

    def spawn_player(self, player: Player) -> bs.Actor:
        spaz = self.spawn_player_spaz(player)
        spaz.connect_controls_to_player(enable_punch=True,
                                        enable_bomb=True,
                                        enable_pickup=True)

        spaz.bomb_count = 3
        spaz.bomb_type = 'normal'

        # cerdo gordo
        spaz.node.color_mask_texture = bs.gettexture('melColorMask')
        spaz.node.color_texture = bs.gettexture('melColor')
        spaz.node.head_mesh = bs.getmesh('melHead')
        spaz.node.hand_mesh = bs.getmesh('melHand')
        spaz.node.torso_mesh = bs.getmesh('melTorso')
        spaz.node.pelvis_mesh = bs.getmesh('kronkPelvis')
        spaz.node.upper_arm_mesh = bs.getmesh('melUpperArm')
        spaz.node.forearm_mesh = bs.getmesh('melForeArm')
        spaz.node.upper_leg_mesh = bs.getmesh('melUpperLeg')
        spaz.node.lower_leg_mesh = bs.getmesh('melLowerLeg')
        spaz.node.toes_mesh = bs.getmesh('melToes')
        spaz.node.style = 'mel'
        # Sounds cerdo gordo
        mel_sounds = [bs.getsound('mel01'), bs.getsound('mel02'), bs.getsound('mel03'), bs.getsound('mel04'), bs.getsound('mel05'),
                      bs.getsound('mel06'), bs.getsound('mel07'), bs.getsound('mel08'), bs.getsound('mel09'), bs.getsound('mel10')]
        spaz.node.jump_sounds = mel_sounds
        spaz.node.attack_sounds = mel_sounds
        spaz.node.impact_sounds = mel_sounds
        spaz.node.pickup_sounds = mel_sounds
        spaz.node.death_sounds = [bs.getsound('melDeath01')]
        spaz.node.fall_sounds = [bs.getsound('melFall01')]

        spaz.play_big_death_sound = True
        return spaz

    def on_begin(self) -> None:
        super().on_begin()
        self._bots.spawn_bot(MrSpazBot, pos=(random.choice(
            [1, -1, 2, -2]), 1.34, random.choice([1, -1, 2, -2])), spawn_time=2.0)
        self._bots.spawn_bot(MrSpazBot, pos=(random.choice(
            [1, -1, 2, -2]), 1.34, random.choice([1, -1, 2, -2])), spawn_time=2.0)

        self._timer = OnScreenTimer()
        self._timer.start()

        bs.timer(10.0, self._spawn_this_bot, repeat=True)
        bs.timer(5.0, self._check_end_game)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):

            super().handlemessage(msg)

            curtime = bs.time()

            msg.getplayer(Player).death_time = curtime

            if isinstance(self.session, bs.CoopSession):
                babase.pushcall(self._check_end_game)

                self._last_player_death_time = curtime
            else:
                bs.timer(1.0, self._check_end_game)
        elif isinstance(msg, SpazBotDiedMessage):
            self._spawn_this_bot()
        else:
            return super().handlemessage(msg)
        return None

    def _spawn_this_bot(self) -> None:
        self._bots.spawn_bot(MrSpazBot, pos=(random.choice(
            [1, -1, 2, -2]), 1.34, random.choice([1, -1, 2, -2])), spawn_time=2.0)

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


# ba_meta export babase.Plugin
class plugin(babase.Plugin):
    def __init__(self):
        ## Campaign support ##
        babase.app.classic.add_coop_practice_level(bs.Level(
            name='Bot Chase', gametype=BotChaseGame,
            settings={},
            preview_texture_name='footballStadiumPreview'))
