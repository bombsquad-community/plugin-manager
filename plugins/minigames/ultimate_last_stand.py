"""Ultimate Last Stand V2:
Made by Cross Joy"""

# Anyone who wanna help me in giving suggestion/ fix bugs/ by creating PR,
# Can visit my github https://github.com/CrossJoy/Bombsquad-Modding

# You can contact me through discord:
# My Discord Id: Cross Joy#0721
# My BS Discord Server: https://discord.gg/JyBY6haARJ


# ----------------------------------------------------------------------------
# V2 What's new?

# - The "Player can't fight each other" system is removed,
# players exploiting the features and, I know ideas how to fix it especially
# the freeze handlemessage

# - Added new bot: Ice Bot

# - The bot spawn location will be more randomize rather than based on players
# position, I don't wanna players stay at the corner of the map.

# - Some codes clean up.

# ----------------------------------------------------------------------------

# ba_meta require api 7

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

import ba
from bastd.actor.playerspaz import PlayerSpaz
from bastd.actor.bomb import TNTSpawner
from bastd.actor.onscreentimer import OnScreenTimer
from bastd.actor.scoreboard import Scoreboard
from bastd.actor.spazfactory import SpazFactory
from bastd.actor.spazbot import (SpazBot, SpazBotSet, BomberBot,
                                 BomberBotPro, BomberBotProShielded,
                                 BrawlerBot, BrawlerBotPro,
                                 BrawlerBotProShielded, TriggerBot,
                                 TriggerBotPro, TriggerBotProShielded,
                                 ChargerBot, StickyBot, ExplodeyBot)

if TYPE_CHECKING:
    from typing import Any, Sequence
    from bastd.actor.spazbot import SpazBot


class IceBot(SpazBot):
    """A slow moving bot with ice bombs.

    category: Bot Classes
    """
    character = 'Pascal'
    punchiness = 0.9
    throwiness = 1
    charge_speed_min = 1
    charge_speed_max = 1
    throw_dist_min = 5.0
    throw_dist_max = 20
    run = True
    charge_dist_min = 10.0
    charge_dist_max = 11.0
    default_bomb_type = 'ice'
    default_bomb_count = 1
    points_mult = 3


class Icon(ba.Actor):
    """Creates in in-game icon on screen."""

    def __init__(self,
                 player: Player,
                 position: tuple[float, float],
                 scale: float,
                 show_lives: bool = True,
                 show_death: bool = True,
                 name_scale: float = 1.0,
                 name_maxwidth: float = 115.0,
                 flatness: float = 1.0,
                 shadow: float = 1.0):
        super().__init__()

        self._player = player
        self._show_lives = show_lives
        self._show_death = show_death
        self._name_scale = name_scale
        self._outline_tex = ba.gettexture('characterIconMask')

        icon = player.get_icon()
        self.node = ba.newnode('image',
                               delegate=self,
                               attrs={
                                   'texture': icon['texture'],
                                   'tint_texture': icon['tint_texture'],
                                   'tint_color': icon['tint_color'],
                                   'vr_depth': 400,
                                   'tint2_color': icon['tint2_color'],
                                   'mask_texture': self._outline_tex,
                                   'opacity': 1.0,
                                   'absolute_scale': True,
                                   'attach': 'bottomCenter'
                               })
        self._name_text = ba.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': ba.Lstr(value=player.getname()),
                'color': ba.safecolor(player.team.color),
                'h_align': 'center',
                'v_align': 'center',
                'vr_depth': 410,
                'maxwidth': name_maxwidth,
                'shadow': shadow,
                'flatness': flatness,
                'h_attach': 'center',
                'v_attach': 'bottom'
            })
        if self._show_lives:
            self._lives_text = ba.newnode('text',
                                          owner=self.node,
                                          attrs={
                                              'text': 'x0',
                                              'color': (1, 1, 0.5),
                                              'h_align': 'left',
                                              'vr_depth': 430,
                                              'shadow': 1.0,
                                              'flatness': 1.0,
                                              'h_attach': 'center',
                                              'v_attach': 'bottom'
                                          })
        self.set_position_and_scale(position, scale)

    def set_position_and_scale(self, position: tuple[float, float],
                               scale: float) -> None:
        """(Re)position the icon."""
        assert self.node
        self.node.position = position
        self.node.scale = [70.0 * scale]
        self._name_text.position = (position[0], position[1] + scale * 52.0)
        self._name_text.scale = 1.0 * scale * self._name_scale
        if self._show_lives:
            self._lives_text.position = (position[0] + scale * 10.0,
                                         position[1] - scale * 43.0)
            self._lives_text.scale = 1.0 * scale

    def update_for_lives(self) -> None:
        """Update for the target player's current lives."""
        if self._player:
            lives = self._player.lives
        else:
            lives = 0
        if self._show_lives:
            if lives > 0:
                self._lives_text.text = 'x' + str(lives - 1)
            else:
                self._lives_text.text = ''
        if lives == 0:
            self._name_text.opacity = 0.2
            assert self.node
            self.node.color = (0.7, 0.3, 0.3)
            self.node.opacity = 0.2

    def handle_player_spawned(self) -> None:
        """Our player spawned; hooray!"""
        if not self.node:
            return
        self.node.opacity = 1.0
        self.update_for_lives()

    def handle_player_died(self) -> None:
        """Well poo; our player died."""
        if not self.node:
            return
        if self._show_death:
            ba.animate(
                self.node, 'opacity', {
                    0.00: 1.0,
                    0.05: 0.0,
                    0.10: 1.0,
                    0.15: 0.0,
                    0.20: 1.0,
                    0.25: 0.0,
                    0.30: 1.0,
                    0.35: 0.0,
                    0.40: 1.0,
                    0.45: 0.0,
                    0.50: 1.0,
                    0.55: 0.2
                })
            lives = self._player.lives
            if lives == 0:
                ba.timer(0.6, self.update_for_lives)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.DieMessage):
            self.node.delete()
            return None
        return super().handlemessage(msg)


@dataclass
class SpawnInfo:
    """Spawning info for a particular bot type."""
    spawnrate: float
    increase: float
    dincrease: float


class Player(ba.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        super().__init__()
        self.death_time: float | None = None
        self.lives = 0
        self.icons: list[Icon] = []


class Team(ba.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.survival_seconds: int | None = None
        self.spawn_order: list[Player] = []


# ba_meta export game
class UltimateLastStand(ba.TeamGameActivity[Player, Team]):
    """Minigame involving dodging falling bombs."""

    name = 'Ultimate Last Stand'
    description = 'Only the strongest will stand at the end.'
    scoreconfig = ba.ScoreConfig(label='Survived',
                                 scoretype=ba.ScoreType.SECONDS,
                                 none_is_winner=True)

    # Print messages when players die (since its meaningful in this game).
    announce_player_deaths = True

    # Don't allow joining after we start
    # (would enable leave/rejoin tomfoolery).
    allow_mid_activity_joins = False

    @classmethod
    def get_available_settings(
            cls,
            sessiontype: type[ba.Session]) -> list[ba.Setting]:
        settings = [
            ba.IntSetting(
                'Lives Per Player',
                default=1,
                min_value=1,
                max_value=10,
                increment=1,
            ),
            ba.FloatChoiceSetting(
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
            ba.BoolSetting('Epic Mode', default=False),
        ]
        if issubclass(sessiontype, ba.DualTeamSession):
            settings.append(
                ba.BoolSetting('Balance Total Lives', default=False))
        return settings

    # We're currently hard-coded for one map.
    @classmethod
    def get_supported_maps(cls, sessiontype: type[ba.Session]) -> list[str]:
        return ['Rampage']

    # We support teams, free-for-all, and co-op sessions.
    @classmethod
    def supports_session_type(cls, sessiontype: type[ba.Session]) -> bool:
        return (issubclass(sessiontype, ba.DualTeamSession)
                or issubclass(sessiontype, ba.FreeForAllSession))

    def __init__(self, settings: dict):
        super().__init__(settings)

        self._scoreboard = Scoreboard()
        self._start_time: float | None = None
        self._vs_text: ba.Actor | None = None
        self._round_end_timer: ba.Timer | None = None
        self._lives_per_player = int(settings['Lives Per Player'])
        self._balance_total_lives = bool(
            settings.get('Balance Total Lives', False))
        self._epic_mode = settings.get('Epic Mode', True)
        self._last_player_death_time: float | None = None
        self._timer: OnScreenTimer | None = None
        self._tntspawner: TNTSpawner | None = None
        self._new_wave_sound = ba.getsound('scoreHit01')
        self._bots = SpazBotSet()
        self._tntspawnpos = (0, 5.5, -6)
        self.spazList = []

        # Base class overrides:
        self.slow_motion = self._epic_mode
        self.default_music = (ba.MusicType.EPIC
                              if self._epic_mode else ba.MusicType.SURVIVAL)

        self.node = ba.newnode('text',
                               attrs={
                                   'v_attach': 'bottom',
                                   'h_align': 'center',
                                   'color': (0.83, 0.69, 0.21),
                                   'flatness': 0.5,
                                   'shadow': 0.5,
                                   'position': (0, 75),
                                   'scale': 0.7,
                                   'text': 'By Cross Joy'
                               })

        # For each bot type: [spawnrate, increase, d_increase]
        self._bot_spawn_types = {
            BomberBot: SpawnInfo(1.00, 0.00, 0.000),
            BomberBotPro: SpawnInfo(0.00, 0.05, 0.001),
            BomberBotProShielded: SpawnInfo(0.00, 0.02, 0.002),
            BrawlerBot: SpawnInfo(1.00, 0.00, 0.000),
            BrawlerBotPro: SpawnInfo(0.00, 0.05, 0.001),
            BrawlerBotProShielded: SpawnInfo(0.00, 0.02, 0.002),
            TriggerBot: SpawnInfo(0.30, 0.00, 0.000),
            TriggerBotPro: SpawnInfo(0.00, 0.05, 0.001),
            TriggerBotProShielded: SpawnInfo(0.00, 0.02, 0.002),
            ChargerBot: SpawnInfo(0.30, 0.05, 0.000),
            StickyBot: SpawnInfo(0.10, 0.03, 0.001),
            IceBot: SpawnInfo(0.10, 0.03, 0.001),
            ExplodeyBot: SpawnInfo(0.05, 0.02, 0.002)
        }  # yapf: disable

        # Some base class overrides:
        self.default_music = (ba.MusicType.EPIC
                              if self._epic_mode else ba.MusicType.SURVIVAL)
        if self._epic_mode:
            self.slow_motion = True

    def get_instance_description(self) -> str | Sequence:
        return 'Only the strongest team will stand at the end.' if isinstance(
            self.session,
            ba.DualTeamSession) else 'Only the strongest will stand at the end.'

    def get_instance_description_short(self) -> str | Sequence:
        return 'Only the strongest team will stand at the end.' if isinstance(
            self.session,
            ba.DualTeamSession) else 'Only the strongest will stand at the end.'

    def on_transition_in(self) -> None:
        super().on_transition_in()
        ba.timer(1.3, ba.Call(ba.playsound, self._new_wave_sound))

    def on_player_join(self, player: Player) -> None:
        player.lives = self._lives_per_player

        # Don't waste time doing this until begin.
        player.icons = [Icon(player, position=(0, 50), scale=0.8)]
        if player.lives > 0:
            self.spawn_player(player)

        if self.has_begun():
            self._update_icons()

    def on_begin(self) -> None:
        super().on_begin()
        ba.animate_array(node=self.node, attr='color', size=3, keys={
            0.0: (0.5, 0.5, 0.5),
            0.8: (0.83, 0.69, 0.21),
            1.6: (0.5, 0.5, 0.5)
        }, loop=True)

        ba.timer(0.001, ba.WeakCall(self._start_bot_updates))
        self._tntspawner = TNTSpawner(position=self._tntspawnpos,
                                      respawn_time=10.0)

        self._timer = OnScreenTimer()
        self._timer.start()
        self.setup_standard_powerup_drops()

        # Check for immediate end (if we've only got 1 player, etc).
        self._start_time = ba.time()

        # If balance-team-lives is on, add lives to the smaller team until
        # total lives match.
        if (isinstance(self.session, ba.DualTeamSession)
            and self._balance_total_lives and self.teams[0].players
                and self.teams[1].players):
            if self._get_total_team_lives(
               self.teams[0]) < self._get_total_team_lives(self.teams[1]):
                lesser_team = self.teams[0]
                greater_team = self.teams[1]
            else:
                lesser_team = self.teams[1]
                greater_team = self.teams[0]
            add_index = 0
            while (self._get_total_team_lives(lesser_team) <
                   self._get_total_team_lives(greater_team)):
                lesser_team.players[add_index].lives += 1
                add_index = (add_index + 1) % len(lesser_team.players)

        ba.timer(1.0, self._update, repeat=True)
        self._update_icons()

        # We could check game-over conditions at explicit trigger points,
        # but lets just do the simple thing and poll it.

    def _update_icons(self) -> None:
        # pylint: disable=too-many-branches

        # In free-for-all mode, everyone is just lined up along the bottom.
        if isinstance(self.session, ba.FreeForAllSession):
            count = len(self.teams)
            x_offs = 85
            xval = x_offs * (count - 1) * -0.5
            for team in self.teams:
                if len(team.players) == 1:
                    player = team.players[0]
                    for icon in player.icons:
                        icon.set_position_and_scale((xval, 30), 0.7)
                        icon.update_for_lives()
                    xval += x_offs

        # In teams mode we split up teams.
        else:
            for team in self.teams:
                if team.id == 0:
                    xval = -50
                    x_offs = -85
                else:
                    xval = 50
                    x_offs = 85
                for player in team.players:
                    for icon in player.icons:
                        icon.set_position_and_scale((xval, 30), 0.7)
                        icon.update_for_lives()
                    xval += x_offs

    def on_player_leave(self, player: Player) -> None:
        # Augment default behavior.
        super().on_player_leave(player)
        player.icons = []

        # Update icons in a moment since our team will be gone from the
        # list then.
        ba.timer(0, self._update_icons)

        # If the player to leave was the last in spawn order and had
        # their final turn currently in-progress, mark the survival time
        # for their team.
        if self._get_total_team_lives(player.team) == 0:
            assert self._start_time is not None
            player.team.survival_seconds = int(ba.time() - self._start_time)

        # A departing player may trigger game-over.

    # overriding the default character spawning..
    def spawn_player(self, player: Player) -> ba.Actor:
        actor = self.spawn_player_spaz(player)
        ba.timer(0.3, ba.Call(self._print_lives, player))

        # If we have any icons, update their state.
        for icon in player.icons:
            icon.handle_player_spawned()
        return actor

    def _print_lives(self, player: Player) -> None:
        from bastd.actor import popuptext

        # We get called in a timer so it's possible our player has left/etc.
        if not player or not player.is_alive() or not player.node:
            return

        popuptext.PopupText('x' + str(player.lives - 1),
                            color=(1, 1, 0, 1),
                            offset=(0, -0.8, 0),
                            random_offset=0.0,
                            scale=1.8,
                            position=player.node.position).autoretain()

    def _get_total_team_lives(self, team: Team) -> int:
        return sum(player.lives for player in team.players)

    def _start_bot_updates(self) -> None:
        self._bot_update_interval = 3.3 - 0.3 * (len(self.players))
        self._update_bots()
        self._update_bots()
        if len(self.players) > 2:
            self._update_bots()
        if len(self.players) > 3:
            self._update_bots()
        self._bot_update_timer = ba.Timer(self._bot_update_interval,
                                          ba.WeakCall(self._update_bots))

    def _update_bots(self) -> None:
        assert self._bot_update_interval is not None
        self._bot_update_interval = max(0.5, self._bot_update_interval * 0.98)
        self._bot_update_timer = ba.Timer(self._bot_update_interval,
                                          ba.WeakCall(self._update_bots))
        botspawnpts: list[Sequence[float]] = [[-5.0, 5.5, -4.14],
                                              [0.0, 5.5, -4.14],
                                              [5.0, 5.5, -4.14]]
        for player in self.players:
            try:
                if player.is_alive():
                    assert isinstance(player.actor, PlayerSpaz)
                    assert player.actor.node
            except Exception:
                ba.print_exception('Error updating bots.')

        spawnpt = random.choice(
            [botspawnpts[0], botspawnpts[1], botspawnpts[2]])

        spawnpt = (spawnpt[0] + 3.0 * (random.random() - 0.5), spawnpt[1],
                   2.0 * (random.random() - 0.5) + spawnpt[2])

        # Normalize our bot type total and find a random number within that.
        total = 0.0
        for spawninfo in self._bot_spawn_types.values():
            total += spawninfo.spawnrate
        randval = random.random() * total

        # Now go back through and see where this value falls.
        total = 0
        bottype: type[SpazBot] | None = None
        for spawntype, spawninfo in self._bot_spawn_types.items():
            total += spawninfo.spawnrate
            if randval <= total:
                bottype = spawntype
                break
        spawn_time = 1.0
        assert bottype is not None
        self._bots.spawn_bot(bottype, pos=spawnpt, spawn_time=spawn_time)

        # After every spawn we adjust our ratios slightly to get more
        # difficult.
        for spawninfo in self._bot_spawn_types.values():
            spawninfo.spawnrate += spawninfo.increase
            spawninfo.increase += spawninfo.dincrease

    # Various high-level game events come through this method.
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.PlayerDiedMessage):

            # Augment standard behavior.
            super().handlemessage(msg)

            curtime = ba.time()

            # Record the player's moment of death.
            # assert isinstance(msg.spaz.player
            msg.getplayer(Player).death_time = curtime

            player: Player = msg.getplayer(Player)

            player.lives -= 1
            if player.lives < 0:
                player.lives = 0

            # If we have any icons, update their state.
            for icon in player.icons:
                icon.handle_player_died()

            # Play big death sound on our last death
            # or for every one in solo mode.
            if player.lives == 0:
                ba.playsound(SpazFactory.get().single_player_death_sound)

            # If we hit zero lives, we're dead (and our team might be too).
            if player.lives == 0:
                # If the whole team is now dead, mark their survival time.
                if self._get_total_team_lives(player.team) == 0:
                    assert self._start_time is not None
                    player.team.survival_seconds = int(ba.time() -
                                                       self._start_time)
            else:
                # Otherwise, in regular mode, respawn.
                self.respawn_player(player)

    def _get_living_teams(self) -> list[Team]:
        return [
            team for team in self.teams
            if len(team.players) > 0 and any(player.lives > 0
                                             for player in team.players)
        ]

    def _update(self) -> None:
        # If we're down to 1 or fewer living teams, start a timer to end
        # the game (allows the dust to settle and draws to occur if deaths
        # are close enough).
        if len(self._get_living_teams()) < 2:
            self._round_end_timer = ba.Timer(0.5, self.end_game)

    def end_game(self) -> None:
        # Stop updating our time text, and set the final time to match
        # exactly when our last guy died.
        self._timer.stop(endtime=self._last_player_death_time)

        # Ok now calc game results: set a score for each team and then tell
        # the game to end.
        results = ba.GameResults()

        # Remember that 'free-for-all' mode is simply a special form
        # of 'teams' mode where each player gets their own team, so we can
        # just always deal in teams and have all cases covered.
        for team in self.teams:
            # Submit the score value in milliseconds.
            results.set_team_score(team, team.survival_seconds)

        self.end(results=results)
