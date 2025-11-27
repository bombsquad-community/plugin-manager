"""
Bots Fighting game. Pretty cool for if u want to bet with your mates, or let fate (randomess) decide on the winning team.

-credits-
made by rabbitboom, aka Johnny仔 (YouTube) or iCommerade (gaming world(???))
original idea by Froshlee08 (hence a bot named in his honour)
shoutout to EraOS who gave me quite a lot of solution and Brotherboard who also helped.
"""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING, override


import logging
import random
import weakref
import bascenev1 as bs
import efro.debug as Edebug

from bascenev1lib.actor.spaz import Spaz, PunchHitMessage
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.actor.spazbot import (
    SpazBotDiedMessage,
    SpazBotSet,
    ChargerBot,
    StickyBot,
    SpazBot,
    BrawlerBot,
    TriggerBot,
    BrawlerBotProShielded,
    ChargerBotProShielded,
    BouncyBot,
    TriggerBotProShielded,
    BomberBotProShielded,
)

if TYPE_CHECKING:
    from typing import Any, Sequence, Optional, List


class Player(bs.Player['Team']):
    """Our player type for this game."""


class SpazBot2(SpazBot):
    # custom bots that have custom behaviours requiring more msg and modules from spaz.py will have them imported here.
    from bascenev1lib.actor.spaz import Spaz, PunchHitMessage


class BouncyBotSemiLite(BouncyBot):
    # nerfed bouncybot. this is due to the base bouncybot being the same lv as pro bots.
    highlight = (1, 1, 0.8)
    punchiness = 0.85
    run = False
    default_boxing_gloves = False
    charge_dist_min = 5
    points_mult = 1


class FroshBot(SpazBot):
    # Slightly beefier version of BomberBots, with slightly altered behaviour.
    color = (0.13, 0.13, 0.13)
    highlight = (0.2, 1, 1)
    character = 'Bernard'
    run = True
    default_bomb_count = 2
    throw_rate = 0.8
    throwiness = 0.2
    punchiness = 0.85
    charge_dist_max = 3.0
    charge_speed_min = 0.3
    default_hitpoints = 1300


class FroshBotShielded(FroshBot):
    default_shields = True


class StickyBotShielded(StickyBot):
    # shielded stickybots. *not bonus bots cuz they act the same as normal stickybots
    default_shields = True


class IcePuncherBot(SpazBot2):
    # A bot who can freeze anyone on punch and is immune to freezing.
    color = (0, 0, 1)
    highlight = (.2, .2, 1)
    character = 'Pascal'
    run = True
    punchiness = 0.8
    charge_dist_min = 6
    charge_dist_max = 9999
    charge_speed_min = 0.3
    charge_speed_max = 0.85
    throw_dist_min = 9999
    throw_dist_max = 9999

    def handlemessage(self, msg):
        # Add the ability to freeze anyone on punch.
        if isinstance(msg, self.PunchHitMessage):
            node = bs.getcollision().opposingnode
            try:
                node.handlemessage(bs.FreezeMessage())
                bs.getsound('freeze').play()
            except Exception:
                print('freeze failed.')
            return super().handlemessage(msg)
        elif isinstance(msg, bs.FreezeMessage):
            pass  # resistant to freezing.
        else:
            return super().handlemessage(msg)


class IcePuncherBotShielded(IcePuncherBot):
    default_shields = True


class GliderBot(BrawlerBot):
    # A bot who can glide on terrain and navigate it safely as if it's ice skating.
    color = (0.5, 0.5, 0.5)
    highlight = (0, 10, 0)
    character = 'B-9000'
    charge_speed_min = 0.3
    charge_speed_max = 1.0

    def __init__(self) -> None:
        super().__init__()
        self.node.hockey = True  # Added the ability to move fast "like in hockey".


class GliderBotShielded(GliderBot):
    # Shielded version of GliderBot.
    default_shields = True


class TeamBotSet(SpazBotSet):
    """Bots that can gather in a team and kill other bots."""

    activity: BotsVSBotsGame

    def __init__(self, team: Team) -> None:
        super().__init__()
        activity = bs.getactivity()
        self._pro_bots = activity._pro_bots
        self._bonus_bots = activity._bonus_bots
        self._punching_bots_only = activity._punching_bots_only
        self.spawn_time = activity.spawn_time
        self._team = weakref.ref(team)

    def colorforteam(self, spaz) -> None:
        spaz.node.color = self.team.color

    def yell(self) -> None:
        for botlist in self._bot_lists:
            for bot in botlist:
                if bot:
                    assert bot.node
                    self.celebrate(self.spawn_time)
                    bs.Call(bot.node.handlemessage, 'jump_sound')
                    bs.timer(0, bs.Call(bot.node.handlemessage, 'attack_sound'))

    def _update(self) -> None:
        # Update one of our bot lists each time through.
        # First off, remove no-longer-existing bots from the list.
        try:
            bot_list = self._bot_lists[self._bot_update_list] = [
                b for b in self._bot_lists[self._bot_update_list] if b
            ]
        except Exception:
            bot_list = []
            logging.exception(
                'Error updating bot list: %s',
                self._bot_lists[self._bot_update_list],
            )
        self._bot_update_list = (
            self._bot_update_list + 1
        ) % self._bot_list_count

        # Update our list of player points for the bots to use.
        player_pts = []
        try:
            for n in bs.getnodes():
                if n.getnodetype() == 'spaz':
                    s = n.getdelegate(object)
                    if isinstance(s, SpazBot):
                        if not s in self.get_living_bots():
                            if s.is_alive():
                                player_pts.append((
                                    bs.Vec3(n.position),
                                    bs.Vec3(n.velocity)))
        except Exception:
            logging.exception('Error on bot-set _update.')

        for bot in bot_list:
            bot.set_player_points(player_pts)
            bot.update_ai()

    def get_bot_type(self):
        bot_types = [
            BrawlerBot,
            ChargerBot,
            BouncyBotSemiLite,
        ]
        if self._punching_bots_only == False:
            bot_types += [
                SpazBot,
                StickyBot,
            ]
        if self._pro_bots == True:
            bot_types += [
                BrawlerBotProShielded,
                ChargerBotProShielded,
                BouncyBot,
            ]
            if self._punching_bots_only == False:
                bot_types += [
                    BomberBotProShielded,
                    StickyBotShielded,
                ]
        if self._bonus_bots == True:
            bot_types += [
                IcePuncherBot,
                GliderBot,
            ]
            if self._punching_bots_only == False:
                bot_types += [
                    FroshBot,
                ]
        if self._bonus_bots and self._pro_bots == True:
            bot_types += [
                IcePuncherBotShielded,
                GliderBotShielded,
            ]
            if self._punching_bots_only == False:
                bot_types += [
                    FroshBotShielded,
                ]
        return random.choice(bot_types)

    @property
    def team(self) -> Team:
        """The bot's team."""
        return self._team()


class Team(bs.Team[TeamBotSet]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0
        self.bots = TeamBotSet(self)


# ba_meta export bascenev1.GameActivity
class BotsVSBotsGame(bs.TeamGameActivity[bs.Player, Team]):
    """A game type based on acquiring kills."""

    name = 'Bots VS Bots'
    description = 'Sit down and enjoy mobs from your team fight the opposing team for you. \n Feel free to enjoy some popcorn with it or place a bet with your friends.'

    @override
    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[bs.Setting]:
        settings = [
            bs.IntSetting(
                'Bots Per Team',
                min_value=5,
                default=20,
                increment=5,
            ),
            bs.BoolSetting('Epic Mode', default=False),
            bs.BoolSetting('Punchers only', default=False),
            bs.BoolSetting('Pro bots', default=False),
            bs.BoolSetting('Bonus bots', default=True),
        ]
        return settings

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession)

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return ['Football Stadium']

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._bots_per_team = int(settings['Bots Per Team'])
        self._dingsound = bs.getsound('dingSmall')
        self._punching_bots_only = bool(settings['Punchers only'])
        self._pro_bots = bool(settings['Pro bots'])
        self._bonus_bots = bool(settings['Bonus bots'])
        self._epic_mode = bool(settings['Epic Mode'])
        self._cheersound = bs.getsound('cheer')
        self._marchsoundA = bs.getsound('footimpact01')
        self._marchsoundB = bs.getsound('footimpact02')
        self._marchsoundC = bs.getsound('footimpact03')

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.spawn_time = 1.6 if self._epic_mode else 4.0
        self.default_music = (bs.MusicType.EPIC
                              if self._epic_mode else bs.MusicType.TO_THE_DEATH)

    @override
    def get_instance_description(self) -> str | Sequence:
        return 'Enjoy the battle.'

    @override
    def get_instance_description_short(self) -> str | Sequence:
        return 'Enjoy the battle.'

    @override
    def on_team_join(self, team: Team) -> None:
        self.spawn_team(team)

    @override
    def on_begin(self) -> None:
        bs.TeamGameActivity.on_begin(self)

    def spawn_player(self, player: Player) -> None:
        return None

    def spawn_team(self, team: Team) -> None:
        camp = self.map.get_flag_position(team.id)
        for i in range(self._bots_per_team):
            team.bots.spawn_bot(team.bots.get_bot_type(),
                                (camp[0], camp[1] + 1.8, random.randrange(-4, 5)),
                                self.spawn_time, team.bots.colorforteam)
        bs.timer(float(self.spawn_time) + 1.7, team.bots.yell)

    def update(self) -> None:
        if len(self._get_living_teams()) < 2:
            self._round_end_timer = bs.Timer(0, self.end_game)

    def _get_living_teams(self) -> list[Team]:
        return [
            team
            for team in self.teams
            if team.bots.have_living_bots()
        ]

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, SpazBotDiedMessage):
            bs.pushcall(self.update)

        else:
            return super().handlemessage(msg)
        return None

    @override
    def end_game(self) -> None:
        if self.has_ended():
            return
        results = bs.GameResults()
        self._cheersound.play()
        for team in self.teams:
            team.bots.final_celebrate()
            results.set_team_score(team, len(team.bots.get_living_bots()))
        self.end(results=results)
