# Ported to api 8 by brostos using baport.(https://github.com/bombsquad-community/baport)

# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs
from bascenev1lib.actor.spazbot import SpazBotSet, ExplodeyBot, SpazBotDiedMessage
from bascenev1lib.actor.onscreentimer import OnScreenTimer

if TYPE_CHECKING:
    from typing import Any, Type, Dict, List, Optional


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

# ba_meta export bascenev1.GameActivity


class ExplodoRunGame(bs.TeamGameActivity[Player, Team]):
    name = "Explodo Run"
    description = "Run For Your Life :))"
    available_settings = [bs.BoolSetting('Epic Mode', default=False)]
    scoreconfig = bs.ScoreConfig(label='Time',
                                 scoretype=bs.ScoreType.MILLISECONDS,
                                 lower_is_better=False)

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'rampagePreview'

    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Rampage']

    def __init__(self, settings: dict):
        settings['map'] = "Rampage"
        self._epic_mode = settings.get('Epic Mode', False)
        if self._epic_mode:
            self.slow_motion = True
        super().__init__(settings)
        self._timer: Optional[OnScreenTimer] = None
        self._winsound = bs.getsound('score')
        self._won = False
        self._bots = SpazBotSet()
        self.wave = 1
        self.default_music = bs.MusicType.TO_THE_DEATH

    def on_begin(self) -> None:
        super().on_begin()

        self._timer = OnScreenTimer()
        bs.timer(2.5, self._timer.start)

        # Bots Hehe
        bs.timer(2.5, self.street)

    def street(self):
        for a in range(self.wave):
            p1 = random.choice([-5, -2.5, 0, 2.5, 5])
            p3 = random.choice([-4.5, -4.14, -5, -3])
            time = random.choice([1, 1.5, 2.5, 2])
            self._bots.spawn_bot(ExplodeyBot, pos=(p1, 5.5, p3), spawn_time=time)
        self.wave += 1

    def botrespawn(self):
        if not self._bots.have_living_bots():
            self.street()

    def handlemessage(self, msg: Any) -> Any:

        # A player has died.
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)  # Augment standard behavior.
            self._won = True
            self.end_game()

        # A spaz-bot has died.
        elif isinstance(msg, SpazBotDiedMessage):
            # Unfortunately the bot-set will always tell us there are living
            # bots if we ask here (the currently-dying bot isn't officially
            # marked dead yet) ..so lets push a call into the event loop to
            # check once this guy has finished dying.
            babase.pushcall(self.botrespawn)

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
            name='Explodo Run',
            gametype=ExplodoRunGame,
            settings={},
            preview_texture_name='rampagePreview'))
        babase.app.classic.add_coop_practice_level(bs.Level('Epic Explodo Run',
                                                            gametype=ExplodoRunGame,
                                                            settings={'Epic Mode': True},
                                                            preview_texture_name='rampagePreview'))
