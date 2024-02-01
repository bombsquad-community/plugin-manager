# Ported to api 8 by brostos using baport.(https://github.com/bombsquad-community/baport)

# ba_meta require api 8

from __future__ import annotations
from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs
import random
from bascenev1lib.actor.onscreentimer import OnScreenTimer
from bascenev1lib.actor.spazbot import (
    SpazBot, SpazBotSet,
    BomberBot, BrawlerBot, BouncyBot,
    ChargerBot, StickyBot, TriggerBot,
    ExplodeyBot)

if TYPE_CHECKING:
    from typing import Any, List, Type, Optional


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        super().__init__()
        self.death_time: Optional[float] = None


class Team(bs.Team[Player]):
    """Our team type for this game."""


# ba_meta export bascenev1.GameActivity
class BotShowerGame(bs.TeamGameActivity[Player, Team]):
    """A babase.MeteorShowerGame but replaced with bots."""

    name = 'Bot Shower'
    description = 'Survive from the bots.'
    available_settings = [
        bs.BoolSetting('Spaz', default=True),
        bs.BoolSetting('Zoe', default=True),
        bs.BoolSetting('Kronk', default=True),
        bs.BoolSetting('Snake Shadow', default=True),
        bs.BoolSetting('Mel', default=True),
        bs.BoolSetting('Jack Morgan', default=True),
        bs.BoolSetting('Easter Bunny', default=True),
        bs.BoolSetting('Epic Mode', default=False),
    ]

    announce_player_deaths = True

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return ['Football Stadium', 'Hockey Stadium']

    def __init__(self, settings: dict) -> None:
        super().__init__(settings)
        self._epic_mode = settings['Epic Mode']
        self._last_player_death_time: Optional[float] = None
        self._timer: Optional[OnScreenTimer] = None
        self._bots: Optional[SpazBotSet] = None
        self._bot_type: List[SpazBot] = []

        if bool(settings['Spaz']) == True:
            self._bot_type.append(BomberBot)
        else:
            if BomberBot in self._bot_type:
                self._bot_type.remove(BomberBot)
        if bool(settings['Zoe']) == True:
            self._bot_type.append(TriggerBot)
        else:
            if TriggerBot in self._bot_type:
                self._bot_type.remove(TriggerBot)
        if bool(settings['Kronk']) == True:
            self._bot_type.append(BrawlerBot)
        else:
            if BrawlerBot in self._bot_type:
                self._bot_type.remove(BrawlerBot)
        if bool(settings['Snake Shadow']) == True:
            self._bot_type.append(ChargerBot)
        else:
            if ChargerBot in self._bot_type:
                self._bot_type.remove(ChargerBot)
        if bool(settings['Jack Morgan']) == True:
            self._bot_type.append(ExplodeyBot)
        else:
            if ExplodeyBot in self._bot_type:
                self._bot_type.remove(ExplodeyBot)
        if bool(settings['Easter Bunny']) == True:
            self._bot_type.append(BouncyBot)
        else:
            if BouncyBot in self._bot_type:
                self._bot_type.remove(BouncyBot)

        self.slow_motion = self._epic_mode
        self.default_music = (bs.MusicType.EPIC
                              if self._epic_mode else bs.MusicType.SURVIVAL)

    def on_begin(self) -> None:
        super().on_begin()
        self._bots = SpazBotSet()
        self._timer = OnScreenTimer()
        self._timer.start()

        if self._epic_mode:
            bs.timer(1.0, self._start_spawning_bots)
        else:
            bs.timer(5.0, self._start_spawning_bots)

        bs.timer(5.0, self._check_end_game)

    def spawn_player(self, player: Player) -> None:
        spaz = self.spawn_player_spaz(player)
        spaz.connect_controls_to_player(
            enable_punch=False,
            enable_bomb=False,
            enable_pickup=False)
        return spaz

    def on_player_join(self, player: Player) -> None:
        if self.has_begun():
            bui.screenmessage(
                babase.Lstr(resource='playerDelayedJoinText',
                            subs=[('${PLAYER}', player.getname(full=True))]),
                color=(1, 1, 0),
            )

            assert self._timer is not None
            player.death_time = self._timer.getstarttime()
            return
        self.spawn_player(player)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            curtime = bs.time()
            msg.getplayer(Player).death_time = curtime

            bs.timer(1.0, self._check_end_game)
        else:
            super().handlemessage(msg)

    def _start_spawning_bots(self) -> None:
        bs.timer(1.2, self._spawn_bot, repeat=True)
        bs.timer(2.2, self._spawn_bot, repeat=True)

    def _spawn_bot(self) -> None:
        assert self._bots is not None
        self._bots.spawn_bot(random.choice(self._bot_type), pos=(
            random.uniform(-11, 11), (9.8 if self.map.getname() == 'Football Stadium' else 5.0), random.uniform(-5, 5)))

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
