# Ported to api 8 by brostos using baport.(https://github.com/bombsquad-community/baport)
"""you vs BombSquad / Created by: byANG3L"""

# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs
import _babase
import random
from bascenev1lib.actor.spazbot import SpazBotSet, BrawlerBot, SpazBotDiedMessage
from bascenev1lib.actor.onscreentimer import OnScreenTimer

if TYPE_CHECKING:
    from typing import Any, Optional

lang = bs.app.lang.language
if lang == 'Spanish':
    name = 'Tu vs BombSquad'
    name_easy = 'Tu vs BS Fácil'
    name_easy_epic = 'Tu vs BS Fácil Épico'
    name_hard = 'Tu vs BS Difícil'
    name_hard_epic = 'Tu vs BS Difícil Épico'
else:
    name = 'You vs BombSquad'
    name_easy = 'You vs BS Easy'
    name_easy_epic = 'You vs BS Easy Epic'
    name_hard = 'You vs BS Hard'
    name_hard_epic = 'You vs BS Hard Epic'


#### BOTS ####


class SpazBot(BrawlerBot):
    character = 'Spaz'
    color = (0.1, 0.35, 0.1)
    highlight = (1, 0.15, 0.15)


class ZoeBot(BrawlerBot):
    character = 'Zoe'
    color = (0.6, 0.6, 0.6)
    highlight = (0, 1, 0)


class SnakeBot(BrawlerBot):
    character = 'Snake Shadow'
    color = (1, 1, 1)
    highlight = (0.55, 0.8, 0.55)


class MelBot(BrawlerBot):
    character = 'Mel'
    color = (1, 1, 1)
    highlight = (0.1, 0.6, 0.1)


class JackBot(BrawlerBot):
    character = 'Jack Morgan'
    color = (1, 0.2, 0.1)
    highlight = (1, 1, 0)


class SantaBot(BrawlerBot):
    character = 'Santa Claus'
    color = (1, 0, 0)
    highlight = (1, 1, 1)


class FrostyBot(BrawlerBot):
    character = 'Frosty'
    color = (0.5, 0.5, 1)
    highlight = (1, 0.5, 0)


class BonesBot(BrawlerBot):
    character = 'Bones'
    color = (0.6, 0.9, 1)
    highlight = (0.6, 0.9, 1)


class BernardBot(BrawlerBot):
    character = 'Bernard'
    color = (0.7, 0.5, 0.0)
    highlight = (0.6, 0.5, 0.8)


class PascalBot(BrawlerBot):
    character = 'Pascal'
    color = (0.3, 0.5, 0.8)
    highlight = (1, 0, 0)


class TaobaoBot(BrawlerBot):
    character = 'Taobao Mascot'
    color = (1, 0.5, 0)
    highlight = (1, 1, 1)


class BBot(BrawlerBot):
    character = 'B-9000'
    color = (0.5, 0.5, 0.5)
    highlight = (1, 0, 0)


class AgentBot(BrawlerBot):
    character = 'Agent Johnson'
    color = (0.3, 0.3, 0.33)
    highlight = (1, 0.5, 0.3)


class GrumbledorfBot(BrawlerBot):
    character = 'Grumbledorf'
    color = (0.2, 0.4, 1.0)
    highlight = (0.06, 0.15, 0.4)


class PixelBot(BrawlerBot):
    character = 'Pixel'
    color = (0, 1, 0.7)
    highlight = (0.65, 0.35, 0.75)


class BunnyBot(BrawlerBot):
    character = 'Easter Bunny'
    color = (1, 1, 1)
    highlight = (1, 0.5, 0.5)


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""


# ba_meta export bascenev1.GameActivity
class TUvsBombSquad(bs.TeamGameActivity[Player, Team]):
    """A game type based on acquiring kills."""

    name = name
    description = 'Defeat all enemies.'
    scoreconfig = bs.ScoreConfig(label='Time',
                                 scoretype=bs.ScoreType.MILLISECONDS,
                                 lower_is_better=True)

    @classmethod
    def get_available_settings(
            cls, sessiontype: Type[bs.Session]) -> List[babase.Setting]:
        settings = [
            bs.BoolSetting('Hard Mode', default=False),
            bs.BoolSetting('Epic Mode', default=False),
        ]
        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return (issubclass(sessiontype, bs.CoopSession)
                or issubclass(sessiontype, bs.MultiTeamSession))

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return ['Football Stadium']

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._winsound = bs.getsound('score')
        self._won = False
        self._timer: Optional[OnScreenTimer] = None
        self._bots = SpazBotSet()
        self._hard_mode = bool(settings['Hard Mode'])
        self._epic_mode = bool(settings['Epic Mode'])

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (bs.MusicType.EPIC if self._epic_mode else
                              bs.MusicType.SURVIVAL)

        self._spaz_easy: list = [[(-5.4146, 0.9515, -3.0379), 23.0],
                                 [(-5.4146, 0.9515, 1.0379), 23.0]]
        self._spaz_hard: list = [[(11.4146, 0.9515, -5.0379), 3.0],
                                 [(-8.4146, 0.9515, -5.0379), 5.0],
                                 [(5.4146, 0.9515, -3.0379), 8.0],
                                 [(5.4146, 0.9515, 1.0379), 8.0]]
        self._zoe_easy: list = [[(5.4146, 0.9515, -1.0379), 23.0],
                                [(-5.4146, 0.9515, 5.0379), 23.0]]
        self._zoe_hard: list = [[(-11.4146, 0.9515, -5.0379), 3.0],
                                [(8.4146, 0.9515, -3.0379), 5.0],
                                [(-5.4146, 0.9515, -3.0379), 8.0],
                                [(-5.4146, 0.9515, 1.0379), 8.0]]
        self._snake_easy: list = [[(-5.4146, 0.9515, -1.0379), 23.0],
                                  [(5.4146, 0.9515, -5.0379), 23.0]]
        self._snake_hard: list = [[(11.4146, 0.9515, -3.0379), 3.0],
                                  [(-8.4146, 0.9515, -3.0379), 5.0],
                                  [(5.4146, 0.9515, -1.0379), 8.0],
                                  [(5.4146, 0.9515, 1.0379), 8.0]]
        self._kronk_easy: list = [[(8.4146, 0.9515, 1.0379), 10.0],
                                  [(5.4146, 0.9515, 3.0379), 23.0]]
        self._kronk_hard: list = [[(-11.4146, 0.9515, -3.0379), 3.0],
                                  [(8.4146, 0.9515, -1.0379), 5.0],
                                  [(-5.4146, 0.9515, -1.0379), 8.0],
                                  [(5.4146, 0.9515, 1.0379), 8.0]]
        self._mel_easy: list = [[(5.4146, 0.9515, 1.0379), 23.0],
                                [(-11.4146, 0.9515, 1.0379), 3.0]]
        self._mel_hard: list = [[(11.4146, 0.9515, -1.0379), 3.0],
                                [(-8.4146, 0.9515, -1.0379), 5.0],
                                [(5.4146, 0.9515, 1.0379), 8.0],
                                [(5.4146, 0.9515, 5.0379), 8.0]]
        self._jack_easy: list = [[(-8.4146, 0.9515, 1.0379), 10.0],
                                 [(5.4146, 0.9515, 1.0379), 23.0]]
        self._jack_hard: list = [[(-11.4146, 0.9515, -1.0379), 3.0],
                                 [(8.4146, 0.9515, 1.0379), 5.0],
                                 [(-5.4146, 0.9515, 1.0379), 8.0],
                                 [(-5.4146, 0.9515, 5.0379), 8.0],
                                 [(5.4146, 0.9515, -5.0379), 8.0]]
        self._frosty_easy: list = [[(8.4146, 0.9515, 1.0379), 10.0],
                                   [(8.4146, 0.9515, -5.0379), 10.0]]
        self._frosty_hard: list = [[(-11.4146, 0.9515, 1.0379), 3.0],
                                   [(-5.4146, 0.9515, 3.0379), 8.0],
                                   [(-5.4146, 0.9515, -5.0379), 8.0],
                                   [(5.4146, 0.9515, 3.0379), 8.0]]
        self._bunny_easy: list = [[(-8.4146, 0.9515, 3.0379), 10.0],
                                  [(5.4146, 0.9515, 5.0379), 23.0]]
        self._bunny_hard: list = [[(8.4146, 0.9515, -5.0379), 5.0],
                                  [(-5.4146, 0.9515, -5.0379), 8.0],
                                  [(-5.4146, 0.9515, 3.0379), 8.0],
                                  [(8.4146, 0.9515, 3.0379), 5.0]]
        self._bones_easy: list = [[(11.4146, 0.9515, -5.0379), 3.0],
                                  [(-8.4146, 0.9515, -5.0379), 10.0]]
        self._bones_hard: list = [[(5.4146, 0.9515, -3.0379), 8.0],
                                  [(-5.4146, 0.9515, 3.0379), 8.0],
                                  [(5.4146, 0.9515, 1.0379), 8.0],
                                  [(8.4146, 0.9515, 3.0379), 5.0]]
        self._bernard_easy: list = [[(-11.4146, 0.9515, -5.0379), 3.0],
                                    [(8.4146, 0.9515, -3.0379), 10.0]]
        self._bernard_hard: list = [[(-5.4146, 0.9515, -3.0379), 8.0],
                                    [(5.4146, 0.9515, 1.0379), 8.0],
                                    [(-5.4146, 0.9515, 1.0379), 8.0],
                                    [(-8.4146, 0.9515, 3.0379), 5.0]]
        self._pascal_easy: list = [[(11.4146, 0.9515, -3.0379), 3.0],
                                   [(-8.4146, 0.9515, -3.0379), 10.0]]
        self._pascal_hard: list = [[(5.4146, 0.9515, -1.0379), 8.0],
                                   [(-5.4146, 0.9515, 1.0379), 8.0],
                                   [(5.4146, 0.9515, 1.0379), 8.0],
                                   [(8.4146, 0.9515, 1.0379), 5.0]]
        self._taobao_easy: list = [[(-11.4146, 0.9515, -3.0379), 3.0],
                                   [(8.4146, 0.9515, -1.0379), 10.0]]
        self._taobao_hard: list = [[(-5.4146, 0.9515, -1.0379), 8.0],
                                   [(5.4146, 0.9515, 1.0379), 8.0],
                                   [(-5.4146, 0.9515, 1.0379), 8.0],
                                   [(-5.4146, 0.9515, 1.0379), 8.0]]
        self._bbot_easy: list = [[(11.4146, 0.9515, -1.0379), 3.0],
                                 [(-8.4146, 0.9515, -1.0379), 10.0]]
        self._bbot_hard: list = [[(-5.4146, 0.9515, 1.0379), 8.0],
                                 [(8.4146, 0.9515, 1.0379), 5.0],
                                 [(-5.4146, 0.9515, 1.0379), 8.0],
                                 [(-5.4146, 0.9515, 1.0379), 8.0]]
        self._agent_easy: list = [[(-11.4146, 0.9515, -1.0379), 3.0],
                                  [(8.4146, 0.9515, 1.0379), 10.0]]
        self._agent_hard: list = [[(5.4146, 0.9515, 5.0379), 8.0],
                                  [(-8.4146, 0.9515, 1.0379), 5.0],
                                  [(-11.4146, 0.9515, 1.0379), 3.0],
                                  [(-11.4146, 0.9515, 1.0379), 3.0]]
        self._wizard_easy: list = [[(11.4146, 0.9515, 1.0379), 3.0],
                                   [(-8.4146, 0.9515, 1.0379), 10.0]]
        self._wizard_hard: list = [[(-5.4146, 0.9515, 5.0379), 8.0],
                                   [(8.4146, 0.9515, 5.0379), 5.0],
                                   [(-5.4146, 0.9515, 1.0379), 8.0],
                                   [(11.4146, 0.9515, 1.0379), 3.0]]
        self._pixel_easy: list = [[(-5.4146, 0.9515, -5.0379), 23.0]]
        self._pixel_hard: list = [[(5.4146, 0.9515, -5.0379), 8.0],
                                  [(5.4146, 0.9515, 3.0379), 5.0],
                                  [(-8.4146, 0.9515, 5.0379), 5.0]]
        self._santa_easy: list = [[(-8.4146, 0.9515, 5.0379), 23.0]]
        self._santa_hard: list = [[(-8.4146, 0.9515, 1.0379), 5.0],
                                  [(-8.4146, 0.9515, 5.0379), 5.0],
                                  [(5.4146, 0.9515, 1.0379), 8.0]]

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_powerup_drops()
        self._timer = OnScreenTimer()
        bs.timer(4.0, self._timer.start)

        for i in range(len(self._spaz_easy)):
            self._spawn_bots(4.0, SpazBot,
                             self._spaz_easy[i][0], self._spaz_easy[i][1])
        for i in range(len(self._zoe_easy)):
            self._spawn_bots(4.0, ZoeBot,
                             self._zoe_easy[i][0], self._zoe_easy[i][1])
        for i in range(len(self._snake_easy)):
            self._spawn_bots(4.0, SnakeBot,
                             self._snake_easy[i][0], self._snake_easy[i][1])
        for i in range(len(self._kronk_easy)):
            self._spawn_bots(4.0, BrawlerBot,
                             self._kronk_easy[i][0], self._kronk_easy[i][1])
        for i in range(len(self._mel_easy)):
            self._spawn_bots(4.0, MelBot,
                             self._mel_easy[i][0], self._mel_easy[i][1])
        for i in range(len(self._jack_easy)):
            self._spawn_bots(4.0, JackBot,
                             self._jack_easy[i][0], self._jack_easy[i][1])
        for i in range(len(self._santa_easy)):
            self._spawn_bots(4.0, SantaBot,
                             self._santa_easy[i][0], self._santa_easy[i][1])
        for i in range(len(self._frosty_easy)):
            self._spawn_bots(4.0, FrostyBot,
                             self._frosty_easy[i][0], self._frosty_easy[i][1])
        for i in range(len(self._bunny_easy)):
            self._spawn_bots(4.0, BunnyBot,
                             self._bunny_easy[i][0], self._bunny_easy[i][1])
        for i in range(len(self._bones_easy)):
            self._spawn_bots(4.0, BonesBot,
                             self._bones_easy[i][0], self._bones_easy[i][1])
        for i in range(len(self._bernard_easy)):
            self._spawn_bots(4.0, BernardBot,
                             self._bernard_easy[i][0], self._bernard_easy[i][1])
        for i in range(len(self._pascal_easy)):
            self._spawn_bots(4.0, PascalBot,
                             self._pascal_easy[i][0], self._pascal_easy[i][1])
        for i in range(len(self._taobao_easy)):
            self._spawn_bots(4.0, TaobaoBot,
                             self._taobao_easy[i][0], self._taobao_easy[i][1])
        for i in range(len(self._bbot_easy)):
            self._spawn_bots(4.0, BBot,
                             self._bbot_easy[i][0], self._bbot_easy[i][1])
        for i in range(len(self._agent_easy)):
            self._spawn_bots(4.0, AgentBot,
                             self._agent_easy[i][0], self._agent_easy[i][1])
        for i in range(len(self._wizard_easy)):
            self._spawn_bots(4.0, GrumbledorfBot,
                             self._wizard_easy[i][0], self._wizard_easy[i][1])
        for i in range(len(self._pixel_easy)):
            self._spawn_bots(4.0, PixelBot,
                             self._pixel_easy[i][0], self._pixel_easy[i][1])

        if self._hard_mode:
            for i in range(len(self._spaz_hard)):
                self._spawn_bots(4.0, SpazBot,
                                 self._spaz_hard[i][0], self._spaz_hard[i][1])
            for i in range(len(self._zoe_hard)):
                self._spawn_bots(4.0, ZoeBot,
                                 self._zoe_hard[i][0], self._zoe_hard[i][1])
            for i in range(len(self._snake_hard)):
                self._spawn_bots(4.0, SnakeBot,
                                 self._snake_hard[i][0], self._snake_hard[i][1])
            for i in range(len(self._kronk_hard)):
                self._spawn_bots(4.0, BrawlerBot,
                                 self._kronk_hard[i][0], self._kronk_hard[i][1])
            for i in range(len(self._mel_hard)):
                self._spawn_bots(4.0, MelBot,
                                 self._mel_hard[i][0], self._mel_hard[i][1])
            for i in range(len(self._jack_hard)):
                self._spawn_bots(4.0, JackBot,
                                 self._jack_hard[i][0], self._jack_hard[i][1])
            for i in range(len(self._santa_hard)):
                self._spawn_bots(4.0, SantaBot,
                                 self._santa_hard[i][0], self._santa_hard[i][1])
            for i in range(len(self._frosty_hard)):
                self._spawn_bots(4.0, FrostyBot,
                                 self._frosty_hard[i][0], self._frosty_hard[i][1])
            for i in range(len(self._bunny_hard)):
                self._spawn_bots(4.0, BunnyBot,
                                 self._bunny_hard[i][0], self._bunny_hard[i][1])
            for i in range(len(self._bones_hard)):
                self._spawn_bots(4.0, BonesBot,
                                 self._bones_hard[i][0], self._bones_hard[i][1])
            for i in range(len(self._bernard_hard)):
                self._spawn_bots(4.0, BernardBot,
                                 self._bernard_hard[i][0], self._bernard_hard[i][1])
            for i in range(len(self._pascal_hard)):
                self._spawn_bots(4.0, PascalBot,
                                 self._pascal_hard[i][0], self._pascal_hard[i][1])
            for i in range(len(self._taobao_hard)):
                self._spawn_bots(4.0, TaobaoBot,
                                 self._taobao_hard[i][0], self._taobao_hard[i][1])
            for i in range(len(self._bbot_hard)):
                self._spawn_bots(4.0, BBot,
                                 self._bbot_hard[i][0], self._bbot_hard[i][1])
            for i in range(len(self._agent_hard)):
                self._spawn_bots(4.0, AgentBot,
                                 self._agent_hard[i][0], self._agent_hard[i][1])
            for i in range(len(self._wizard_hard)):
                self._spawn_bots(4.0, GrumbledorfBot,
                                 self._wizard_hard[i][0], self._wizard_hard[i][1])
            for i in range(len(self._pixel_hard)):
                self._spawn_bots(4.0, PixelBot,
                                 self._pixel_hard[i][0], self._pixel_hard[i][1])

    def _spawn_bots(self, time: float, bot: Any,
                    pos: float, spawn_time: float) -> None:
        bs.timer(time, lambda: self._bots.spawn_bot(
            bot, pos=pos, spawn_time=spawn_time))

    def on_player_join(self, player: Player) -> None:
        if self.has_begun():
            bs.broadcastmessage(
                babase.Lstr(resource='playerDelayedJoinText',
                            subs=[('${PLAYER}', player.getname(full=True))]),
                color=(0, 1, 0),
            )
            return
        self.spawn_player(player)

    # Called for each spawning player.
    def spawn_player(self, player: Player) -> bs.Actor:

        # Let's spawn close to the center.
        spawn_center = (0.0728, 0.0227, -1.9888)
        pos = (spawn_center[0] + random.uniform(-0.5, 0.5), spawn_center[1],
               spawn_center[2] + random.uniform(-0.5, 0.5))
        return self.spawn_player_spaz(player, position=pos)

    def _check_if_won(self) -> None:
        # Simply end the game if there's no living bots.
        # FIXME: Should also make sure all bots have been spawned;
        #  if spawning is spread out enough that we're able to kill
        #  all living bots before the next spawns, it would incorrectly
        #  count as a win.
        if not self._bots.have_living_bots():
            self._won = True
            self.end_game()

    # Called for miscellaneous messages.
    def handlemessage(self, msg: Any) -> Any:

        # A player has died.
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)  # Augment standard behavior.
            self.respawn_player(msg.getplayer(Player))

        # A spaz-bot has died.
        elif isinstance(msg, SpazBotDiedMessage):
            # Unfortunately the bot-set will always tell us there are living
            # bots if we ask here (the currently-dying bot isn't officially
            # marked dead yet) ..so lets push a call into the event loop to
            # check once this guy has finished dying.
            babase.pushcall(self._check_if_won)

        # Let the base class handle anything we don't.
        else:
            return super().handlemessage(msg)
        return None

    # When this is called, we should fill out results and end the game
    # *regardless* of whether is has been won. (this may be called due
    # to a tournament ending or other external reason).
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
class plugin(babase.Plugin):
    def __init__(self):
        ## Campaign support ##
        babase.app.classic.add_coop_practice_level(bs.Level(
            name=name_easy,
            gametype=TUvsBombSquad,
            settings={},
            preview_texture_name='footballStadiumPreview'))
        babase.app.classic.add_coop_practice_level(bs.Level(
            name_easy_epic,
            gametype=TUvsBombSquad,
            settings={'Epic Mode': True},
            preview_texture_name='footballStadiumPreview'))
        babase.app.classic.add_coop_practice_level(bs.Level(
            name=name_hard,
            gametype=TUvsBombSquad,
            settings={'Hard Mode': True},
            preview_texture_name='footballStadiumPreview'))
        babase.app.classic.add_coop_practice_level(bs.Level(
            name=name_hard_epic,
            gametype=TUvsBombSquad,
            settings={'Hard Mode': True,
                      'Epic Mode': True},
            preview_texture_name='footballStadiumPreview'))
