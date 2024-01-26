# Ported to api 8 by brostos using baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations
from asyncio import base_subprocess

import math
import random
from enum import Enum, unique
from dataclasses import dataclass
from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs
from bascenev1lib.actor.popuptext import PopupText
from bascenev1lib.actor.bomb import TNTSpawner
from bascenev1lib.actor.playerspaz import PlayerSpazHurtMessage
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.controlsguide import ControlsGuide
from bascenev1lib.actor.powerupbox import PowerupBox, PowerupBoxFactory
from bascenev1lib.actor.spazbot import (
    SpazBotDiedMessage,
    SpazBotSet,
    ChargerBot,
    StickyBot,
    BomberBot,
    BomberBotLite,
    BrawlerBot,
    BrawlerBotLite,
    TriggerBot,
    BomberBotStaticLite,
    TriggerBotStatic,
    BomberBotProStatic,
    TriggerBotPro,
    ExplodeyBot,
    BrawlerBotProShielded,
    ChargerBotProShielded,
    BomberBotPro,
    TriggerBotProShielded,
    BrawlerBotPro,
    BomberBotProShielded,
)

if TYPE_CHECKING:
    from typing import Any, Sequence
    from bascenev1lib.actor.spazbot import SpazBot


@dataclass
class Wave:
    """A wave of enemies."""

    entries: list[Spawn | Spacing | Delay | None]
    base_angle: float = 0.0


@dataclass
class Spawn:
    """A bot spawn event in a wave."""

    bottype: type[SpazBot] | str
    point: Point | None = None
    spacing: float = 5.0


@dataclass
class Spacing:
    """Empty space in a wave."""

    spacing: float = 5.0


@dataclass
class Delay:
    """A delay between events in a wave."""

    duration: float


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.has_been_hurt = False
        self.respawn_wave = 0


class Team(bs.Team[Player]):
    """Our team type for this game."""


class OnslaughtFootballGame(bs.CoopGameActivity[Player, Team]):
    """Co-op game where players try to survive attacking waves of enemies."""

    name = 'Onslaught'
    description = 'Defeat all enemies.'

    tips: list[str | babase.GameTip] = [
        'Hold any button to run.'
        '  (Trigger buttons work well if you have them)',
        'Try tricking enemies into killing eachother or running off cliffs.',
        'Try \'Cooking off\' bombs for a second or two before throwing them.',
        'It\'s easier to win with a friend or two helping.',
        'If you stay in one place, you\'re toast. Run and dodge to survive..',
        'Practice using your momentum to throw bombs more accurately.',
        'Your punches do much more damage if you are running or spinning.',
    ]

    # Show messages when players die since it matters here.
    announce_player_deaths = True

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._new_wave_sound = bs.getsound('scoreHit01')
        self._winsound = bs.getsound('score')
        self._cashregistersound = bs.getsound('cashRegister')
        self._a_player_has_been_hurt = False
        self._player_has_dropped_bomb = False
        self._spawn_center = (0, 0.2, 0)
        self._tntspawnpos = (0, 0.95, -0.77)
        self._powerup_center = (0, 1.5, 0)
        self._powerup_spread = (6.0, 4.0)
        self._scoreboard: Scoreboard | None = None
        self._game_over = False
        self._wavenum = 0
        self._can_end_wave = True
        self._score = 0
        self._time_bonus = 0
        self._spawn_info_text: bs.NodeActor | None = None
        self._dingsound = bs.getsound('dingSmall')
        self._dingsoundhigh = bs.getsound('dingSmallHigh')
        self._have_tnt = False
        self._excluded_powerups: list[str] | None = None
        self._waves: list[Wave] = []
        self._tntspawner: TNTSpawner | None = None
        self._bots: SpazBotSet | None = None
        self._powerup_drop_timer: bs.Timer | None = None
        self._time_bonus_timer: bs.Timer | None = None
        self._time_bonus_text: bs.NodeActor | None = None
        self._flawless_bonus: int | None = None
        self._wave_text: bs.NodeActor | None = None
        self._wave_update_timer: bs.Timer | None = None
        self._throw_off_kills = 0
        self._land_mine_kills = 0
        self._tnt_kills = 0

        self._epic_mode = bool(settings['Epic Mode'])
        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.ONSLAUGHT
        )

    def on_transition_in(self) -> None:
        super().on_transition_in()
        self._spawn_info_text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'position': (15, -130),
                    'h_attach': 'left',
                    'v_attach': 'top',
                                'scale': 0.55,
                                'color': (0.3, 0.8, 0.3, 1.0),
                                'text': '',
                },
            )
        )
        self._scoreboard = Scoreboard(
            label=babase.Lstr(resource='scoreText'), score_split=0.5
        )

    def on_begin(self) -> None:
        super().on_begin()
        self._have_tnt = True
        self._excluded_powerups = []
        self._waves = []
        bs.timer(4.0, self._start_powerup_drops)

        # Our TNT spawner (if applicable).
        if self._have_tnt:
            self._tntspawner = TNTSpawner(position=self._tntspawnpos)

        self.setup_low_life_warning_sound()
        self._update_scores()
        self._bots = SpazBotSet()
        bs.timer(4.0, self._start_updating_waves)
        self._next_ffa_start_index = random.randrange(
            len(self.map.get_def_points('ffa_spawn'))
        )

    def _get_dist_grp_totals(self, grps: list[Any]) -> tuple[int, int]:
        totalpts = 0
        totaldudes = 0
        for grp in grps:
            for grpentry in grp:
                dudes = grpentry[1]
                totalpts += grpentry[0] * dudes
                totaldudes += dudes
        return totalpts, totaldudes

    def _get_distribution(
            self,
            target_points: int,
            min_dudes: int,
            max_dudes: int,
            group_count: int,
            max_level: int,
    ) -> list[list[tuple[int, int]]]:
        """Calculate a distribution of bad guys given some params."""
        max_iterations = 10 + max_dudes * 2

        groups: list[list[tuple[int, int]]] = []
        for _g in range(group_count):
            groups.append([])
        types = [1]
        if max_level > 1:
            types.append(2)
        if max_level > 2:
            types.append(3)
        if max_level > 3:
            types.append(4)
        for iteration in range(max_iterations):
            diff = self._add_dist_entry_if_possible(
                groups, max_dudes, target_points, types
            )

            total_points, total_dudes = self._get_dist_grp_totals(groups)
            full = total_points >= target_points

            if full:
                # Every so often, delete a random entry just to
                # shake up our distribution.
                if random.random() < 0.2 and iteration != max_iterations - 1:
                    self._delete_random_dist_entry(groups)

                # If we don't have enough dudes, kill the group with
                # the biggest point value.
                elif (
                        total_dudes < min_dudes and iteration != max_iterations - 1
                ):
                    self._delete_biggest_dist_entry(groups)

                # If we've got too many dudes, kill the group with the
                # smallest point value.
                elif (
                        total_dudes > max_dudes and iteration != max_iterations - 1
                ):
                    self._delete_smallest_dist_entry(groups)

                # Close enough.. we're done.
                else:
                    if diff == 0:
                        break

        return groups

    def _add_dist_entry_if_possible(
            self,
            groups: list[list[tuple[int, int]]],
            max_dudes: int,
            target_points: int,
            types: list[int],
    ) -> int:
        # See how much we're off our target by.
        total_points, total_dudes = self._get_dist_grp_totals(groups)
        diff = target_points - total_points
        dudes_diff = max_dudes - total_dudes

        # Add an entry if one will fit.
        value = types[random.randrange(len(types))]
        group = groups[random.randrange(len(groups))]
        if not group:
            max_count = random.randint(1, 6)
        else:
            max_count = 2 * random.randint(1, 3)
        max_count = min(max_count, dudes_diff)
        count = min(max_count, diff // value)
        if count > 0:
            group.append((value, count))
            total_points += value * count
            total_dudes += count
            diff = target_points - total_points
        return diff

    def _delete_smallest_dist_entry(
            self, groups: list[list[tuple[int, int]]]
    ) -> None:
        smallest_value = 9999
        smallest_entry = None
        smallest_entry_group = None
        for group in groups:
            for entry in group:
                if entry[0] < smallest_value or smallest_entry is None:
                    smallest_value = entry[0]
                    smallest_entry = entry
                    smallest_entry_group = group
        assert smallest_entry is not None
        assert smallest_entry_group is not None
        smallest_entry_group.remove(smallest_entry)

    def _delete_biggest_dist_entry(
            self, groups: list[list[tuple[int, int]]]
    ) -> None:
        biggest_value = 9999
        biggest_entry = None
        biggest_entry_group = None
        for group in groups:
            for entry in group:
                if entry[0] > biggest_value or biggest_entry is None:
                    biggest_value = entry[0]
                    biggest_entry = entry
                    biggest_entry_group = group
        if biggest_entry is not None:
            assert biggest_entry_group is not None
            biggest_entry_group.remove(biggest_entry)

    def _delete_random_dist_entry(
            self, groups: list[list[tuple[int, int]]]
    ) -> None:
        entry_count = 0
        for group in groups:
            for _ in group:
                entry_count += 1
        if entry_count > 1:
            del_entry = random.randrange(entry_count)
            entry_count = 0
            for group in groups:
                for entry in group:
                    if entry_count == del_entry:
                        group.remove(entry)
                        break
                    entry_count += 1

    def spawn_player(self, player: Player) -> bs.Actor:

        # We keep track of who got hurt each wave for score purposes.
        player.has_been_hurt = False
        pos = (
            self._spawn_center[0] + random.uniform(-1.5, 1.5),
            self._spawn_center[1],
            self._spawn_center[2] + random.uniform(-1.5, 1.5),
        )
        spaz = self.spawn_player_spaz(player, position=pos)
        spaz.add_dropped_bomb_callback(self._handle_player_dropped_bomb)
        return spaz

    def _handle_player_dropped_bomb(
            self, player: bs.Actor, bomb: bs.Actor
    ) -> None:
        del player, bomb  # Unused.
        self._player_has_dropped_bomb = True

    def _drop_powerup(self, index: int, poweruptype: str | None = None) -> None:
        poweruptype = PowerupBoxFactory.get().get_random_powerup_type(
            forcetype=poweruptype, excludetypes=self._excluded_powerups
        )
        PowerupBox(
            position=self.map.powerup_spawn_points[index],
            poweruptype=poweruptype,
        ).autoretain()

    def _start_powerup_drops(self) -> None:
        self._powerup_drop_timer = bs.Timer(
            3.0, bs.WeakCall(self._drop_powerups), repeat=True
        )

    def _drop_powerups(
            self, standard_points: bool = False, poweruptype: str | None = None
    ) -> None:
        """Generic powerup drop."""
        if standard_points:
            points = self.map.powerup_spawn_points
            for i in range(len(points)):
                bs.timer(
                    1.0 + i * 0.5,
                    bs.WeakCall(
                        self._drop_powerup, i, poweruptype if i == 0 else None
                    ),
                )
        else:
            point = (
                self._powerup_center[0]
                + random.uniform(
                    -1.0 * self._powerup_spread[0],
                    1.0 * self._powerup_spread[0],
                ),
                self._powerup_center[1],
                self._powerup_center[2]
                + random.uniform(
                    -self._powerup_spread[1], self._powerup_spread[1]
                ),
            )

            # Drop one random one somewhere.
            PowerupBox(
                position=point,
                poweruptype=PowerupBoxFactory.get().get_random_powerup_type(
                    excludetypes=self._excluded_powerups
                ),
            ).autoretain()

    def do_end(self, outcome: str, delay: float = 0.0) -> None:
        """End the game with the specified outcome."""
        if outcome == 'defeat':
            self.fade_to_red()
        score: int | None
        if self._wavenum >= 2:
            score = self._score
            fail_message = None
        else:
            score = None
            fail_message = babase.Lstr(resource='reachWave2Text')
        self.end(
            {
                'outcome': outcome,
                'score': score,
                'fail_message': fail_message,
                'playerinfos': self.initialplayerinfos,
            },
            delay=delay,
        )

    def _update_waves(self) -> None:

        # If we have no living bots, go to the next wave.
        assert self._bots is not None
        if (
                self._can_end_wave
                and not self._bots.have_living_bots()
                and not self._game_over
        ):
            self._can_end_wave = False
            self._time_bonus_timer = None
            self._time_bonus_text = None
            base_delay = 0.0

            # Reward time bonus.
            if self._time_bonus > 0:
                bs.timer(0, babase.Call(self._cashregistersound.play))
                bs.timer(
                    base_delay,
                    bs.WeakCall(self._award_time_bonus, self._time_bonus),
                )
                base_delay += 1.0

            # Reward flawless bonus.
            if self._wavenum > 0:
                have_flawless = False
                for player in self.players:
                    if player.is_alive() and not player.has_been_hurt:
                        have_flawless = True
                        bs.timer(
                            base_delay,
                            bs.WeakCall(self._award_flawless_bonus, player),
                        )
                    player.has_been_hurt = False  # reset
                if have_flawless:
                    base_delay += 1.0

            self._wavenum += 1

            # Short celebration after waves.
            if self._wavenum > 1:
                self.celebrate(0.5)
            bs.timer(base_delay, bs.WeakCall(self._start_next_wave))

    def _award_completion_bonus(self) -> None:
        self._cashregistersound.play()
        for player in self.players:
            try:
                if player.is_alive():
                    assert self.initialplayerinfos is not None
                    self.stats.player_scored(
                        player,
                        int(100 / len(self.initialplayerinfos)),
                        scale=1.4,
                        color=(0.6, 0.6, 1.0, 1.0),
                        title=babase.Lstr(resource='completionBonusText'),
                        screenmessage=False,
                    )
            except Exception:
                babase.print_exception()

    def _award_time_bonus(self, bonus: int) -> None:
        self._cashregistersound.play()
        PopupText(
            babase.Lstr(
                value='+${A} ${B}',
                subs=[
                    ('${A}', str(bonus)),
                    ('${B}', babase.Lstr(resource='timeBonusText')),
                ],
            ),
            color=(1, 1, 0.5, 1),
            scale=1.0,
            position=(0, 3, -1),
        ).autoretain()
        self._score += self._time_bonus
        self._update_scores()

    def _award_flawless_bonus(self, player: Player) -> None:
        self._cashregistersound.play()
        try:
            if player.is_alive():
                assert self._flawless_bonus is not None
                self.stats.player_scored(
                    player,
                    self._flawless_bonus,
                    scale=1.2,
                    color=(0.6, 1.0, 0.6, 1.0),
                    title=babase.Lstr(resource='flawlessWaveText'),
                    screenmessage=False,
                )
        except Exception:
            babase.print_exception()

    def _start_time_bonus_timer(self) -> None:
        self._time_bonus_timer = bs.Timer(
            1.0, bs.WeakCall(self._update_time_bonus), repeat=True
        )

    def _update_player_spawn_info(self) -> None:

        # If we have no living players lets just blank this.
        assert self._spawn_info_text is not None
        assert self._spawn_info_text.node
        if not any(player.is_alive() for player in self.teams[0].players):
            self._spawn_info_text.node.text = ''
        else:
            text: str | babase.Lstr = ''
            for player in self.players:
                if not player.is_alive():
                    rtxt = babase.Lstr(
                        resource='onslaughtRespawnText',
                        subs=[
                            ('${PLAYER}', player.getname()),
                            ('${WAVE}', str(player.respawn_wave)),
                        ],
                    )
                    text = babase.Lstr(
                        value='${A}${B}\n',
                        subs=[
                            ('${A}', text),
                            ('${B}', rtxt),
                        ],
                    )
            self._spawn_info_text.node.text = text

    def _respawn_players_for_wave(self) -> None:
        # Respawn applicable players.
        if self._wavenum > 1 and not self.is_waiting_for_continue():
            for player in self.players:
                if (
                        not player.is_alive()
                        and player.respawn_wave == self._wavenum
                ):
                    self.spawn_player(player)
        self._update_player_spawn_info()

    def _setup_wave_spawns(self, wave: Wave) -> None:
        tval = 0.0
        dtime = 0.2
        if self._wavenum == 1:
            spawn_time = 3.973
            tval += 0.5
        else:
            spawn_time = 2.648

        bot_angle = wave.base_angle
        self._time_bonus = 0
        self._flawless_bonus = 0
        for info in wave.entries:
            if info is None:
                continue
            if isinstance(info, Delay):
                spawn_time += info.duration
                continue
            if isinstance(info, Spacing):
                bot_angle += info.spacing
                continue
            bot_type_2 = info.bottype
            if bot_type_2 is not None:
                assert not isinstance(bot_type_2, str)
                self._time_bonus += bot_type_2.points_mult * 20
                self._flawless_bonus += bot_type_2.points_mult * 5

            if self.map.name == 'Doom Shroom':
                tval += dtime
                spacing = info.spacing
                bot_angle += spacing * 0.5
                if bot_type_2 is not None:
                    tcall = bs.WeakCall(
                        self.add_bot_at_angle, bot_angle, bot_type_2, spawn_time
                    )
                    bs.timer(tval, tcall)
                    tval += dtime
                bot_angle += spacing * 0.5
            else:
                assert bot_type_2 is not None
                spcall = bs.WeakCall(
                    self.add_bot_at_point, bot_type_2, spawn_time
                )
                bs.timer(tval, spcall)

        # We can end the wave after all the spawning happens.
        bs.timer(
            tval + spawn_time - dtime + 0.01,
            bs.WeakCall(self._set_can_end_wave),
        )

    def _start_next_wave(self) -> None:

        # This can happen if we beat a wave as we die.
        # We don't wanna respawn players and whatnot if this happens.
        if self._game_over:
            return

        self._respawn_players_for_wave()
        wave = self._generate_random_wave()
        self._setup_wave_spawns(wave)
        self._update_wave_ui_and_bonuses()
        bs.timer(0.4, babase.Call(self._new_wave_sound.play))

    def _update_wave_ui_and_bonuses(self) -> None:
        self.show_zoom_message(
            babase.Lstr(
                value='${A} ${B}',
                subs=[
                    ('${A}', babase.Lstr(resource='waveText')),
                    ('${B}', str(self._wavenum)),
                ],
            ),
            scale=1.0,
            duration=1.0,
            trail=True,
        )

        # Reset our time bonus.
        tbtcolor = (1, 1, 0, 1)
        tbttxt = babase.Lstr(
            value='${A}: ${B}',
            subs=[
                ('${A}', babase.Lstr(resource='timeBonusText')),
                ('${B}', str(self._time_bonus)),
            ],
        )
        self._time_bonus_text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'v_attach': 'top',
                    'h_attach': 'center',
                    'h_align': 'center',
                                'vr_depth': -30,
                                'color': tbtcolor,
                                'shadow': 1.0,
                                'flatness': 1.0,
                                'position': (0, -60),
                                'scale': 0.8,
                                'text': tbttxt,
                },
            )
        )

        bs.timer(5.0, bs.WeakCall(self._start_time_bonus_timer))
        wtcolor = (1, 1, 1, 1)
        wttxt = babase.Lstr(
            value='${A} ${B}',
            subs=[
                ('${A}', babase.Lstr(resource='waveText')),
                ('${B}', str(self._wavenum) + ('')),
            ],
        )
        self._wave_text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'v_attach': 'top',
                    'h_attach': 'center',
                    'h_align': 'center',
                                'vr_depth': -10,
                                'color': wtcolor,
                                'shadow': 1.0,
                                'flatness': 1.0,
                                'position': (0, -40),
                                'scale': 1.3,
                                'text': wttxt,
                },
            )
        )

    def _bot_levels_for_wave(self) -> list[list[type[SpazBot]]]:
        level = self._wavenum
        bot_types = [
            BomberBot,
            BrawlerBot,
            TriggerBot,
            ChargerBot,
            BomberBotPro,
            BrawlerBotPro,
            TriggerBotPro,
            BomberBotProShielded,
            ExplodeyBot,
            ChargerBotProShielded,
            StickyBot,
            BrawlerBotProShielded,
            TriggerBotProShielded,
        ]
        if level > 5:
            bot_types += [
                ExplodeyBot,
                TriggerBotProShielded,
                BrawlerBotProShielded,
                ChargerBotProShielded,
            ]
        if level > 7:
            bot_types += [
                ExplodeyBot,
                TriggerBotProShielded,
                BrawlerBotProShielded,
                ChargerBotProShielded,
            ]
        if level > 10:
            bot_types += [
                TriggerBotProShielded,
                TriggerBotProShielded,
                TriggerBotProShielded,
                TriggerBotProShielded,
            ]
        if level > 13:
            bot_types += [
                TriggerBotProShielded,
                TriggerBotProShielded,
                TriggerBotProShielded,
                TriggerBotProShielded,
            ]
        bot_levels = [
            [b for b in bot_types if b.points_mult == 1],
            [b for b in bot_types if b.points_mult == 2],
            [b for b in bot_types if b.points_mult == 3],
            [b for b in bot_types if b.points_mult == 4],
        ]

        # Make sure all lists have something in them
        if not all(bot_levels):
            raise RuntimeError('Got empty bot level')
        return bot_levels

    def _add_entries_for_distribution_group(
            self,
            group: list[tuple[int, int]],
            bot_levels: list[list[type[SpazBot]]],
            all_entries: list[Spawn | Spacing | Delay | None],
    ) -> None:
        entries: list[Spawn | Spacing | Delay | None] = []
        for entry in group:
            bot_level = bot_levels[entry[0] - 1]
            bot_type = bot_level[random.randrange(len(bot_level))]
            rval = random.random()
            if rval < 0.5:
                spacing = 10.0
            elif rval < 0.9:
                spacing = 20.0
            else:
                spacing = 40.0
            split = random.random() > 0.3
            for i in range(entry[1]):
                if split and i % 2 == 0:
                    entries.insert(0, Spawn(bot_type, spacing=spacing))
                else:
                    entries.append(Spawn(bot_type, spacing=spacing))
        if entries:
            all_entries += entries
            all_entries.append(Spacing(40.0 if random.random() < 0.5 else 80.0))

    def _generate_random_wave(self) -> Wave:
        level = self._wavenum
        bot_levels = self._bot_levels_for_wave()

        target_points = level * 3 - 2
        min_dudes = min(1 + level // 3, 10)
        max_dudes = min(10, level + 1)
        max_level = (
            4 if level > 6 else (3 if level > 3 else (2 if level > 2 else 1))
        )
        group_count = 3
        distribution = self._get_distribution(
            target_points, min_dudes, max_dudes, group_count, max_level
        )
        all_entries: list[Spawn | Spacing | Delay | None] = []
        for group in distribution:
            self._add_entries_for_distribution_group(
                group, bot_levels, all_entries
            )
        angle_rand = random.random()
        if angle_rand > 0.75:
            base_angle = 130.0
        elif angle_rand > 0.5:
            base_angle = 210.0
        elif angle_rand > 0.25:
            base_angle = 20.0
        else:
            base_angle = -30.0
        base_angle += (0.5 - random.random()) * 20.0
        wave = Wave(base_angle=base_angle, entries=all_entries)
        return wave

    def add_bot_at_point(
            self, spaz_type: type[SpazBot], spawn_time: float = 1.0
    ) -> None:
        """Add a new bot at a specified named point."""
        if self._game_over:
            return

        def _getpt() -> Sequence[float]:
            point = self.map.get_def_points(
                'ffa_spawn')[self._next_ffa_start_index]
            self._next_ffa_start_index = (
                self._next_ffa_start_index + 1) % len(
                self.map.get_def_points('ffa_spawn')
            )
            x_range = (-0.5, 0.5) if point[3] == 0.0 else (-point[3], point[3])
            z_range = (-0.5, 0.5) if point[5] == 0.0 else (-point[5], point[5])
            point = (
                point[0] + random.uniform(*x_range),
                point[1],
                point[2] + random.uniform(*z_range),
            )
            return point
        pointpos = _getpt()

        assert self._bots is not None
        self._bots.spawn_bot(spaz_type, pos=pointpos, spawn_time=spawn_time)

    def add_bot_at_angle(
            self, angle: float, spaz_type: type[SpazBot], spawn_time: float = 1.0
    ) -> None:
        """Add a new bot at a specified angle (for circular maps)."""
        if self._game_over:
            return
        angle_radians = angle / 57.2957795
        xval = math.sin(angle_radians) * 1.06
        zval = math.cos(angle_radians) * 1.06
        point = (xval / 0.125, 2.3, (zval / 0.2) - 3.7)
        assert self._bots is not None
        self._bots.spawn_bot(spaz_type, pos=point, spawn_time=spawn_time)

    def _update_time_bonus(self) -> None:
        self._time_bonus = int(self._time_bonus * 0.93)
        if self._time_bonus > 0 and self._time_bonus_text is not None:
            assert self._time_bonus_text.node
            self._time_bonus_text.node.text = babase.Lstr(
                value='${A}: ${B}',
                subs=[
                    ('${A}', babase.Lstr(resource='timeBonusText')),
                    ('${B}', str(self._time_bonus)),
                ],
            )
        else:
            self._time_bonus_text = None

    def _start_updating_waves(self) -> None:
        self._wave_update_timer = bs.Timer(
            2.0, bs.WeakCall(self._update_waves), repeat=True
        )

    def _update_scores(self) -> None:
        score = self._score
        assert self._scoreboard is not None
        self._scoreboard.set_team_value(self.teams[0], score, max_score=None)

    def handlemessage(self, msg: Any) -> Any:

        if isinstance(msg, PlayerSpazHurtMessage):
            msg.spaz.getplayer(Player, True).has_been_hurt = True
            self._a_player_has_been_hurt = True

        elif isinstance(msg, bs.PlayerScoredMessage):
            self._score += msg.score
            self._update_scores()

        elif isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)  # Augment standard behavior.
            player = msg.getplayer(Player)
            self._a_player_has_been_hurt = True

            # Make note with the player when they can respawn:
            if self._wavenum < 10:
                player.respawn_wave = max(2, self._wavenum + 1)
            elif self._wavenum < 15:
                player.respawn_wave = max(2, self._wavenum + 2)
            else:
                player.respawn_wave = max(2, self._wavenum + 3)
            bs.timer(0.1, self._update_player_spawn_info)
            bs.timer(0.1, self._checkroundover)

        elif isinstance(msg, SpazBotDiedMessage):
            pts, importance = msg.spazbot.get_death_points(msg.how)
            if msg.killerplayer is not None:
                target: Sequence[float] | None
                if msg.spazbot.node:
                    target = msg.spazbot.node.position
                else:
                    target = None

                killerplayer = msg.killerplayer
                self.stats.player_scored(
                    killerplayer,
                    pts,
                    target=target,
                    kill=True,
                    screenmessage=False,
                    importance=importance,
                )
                self._dingsound.play(
                    volume=0.6) if importance == 1 else self._dingsoundhigh.play(volume=0.6)

            # Normally we pull scores from the score-set, but if there's
            # no player lets be explicit.
            else:
                self._score += pts
            self._update_scores()
        else:
            super().handlemessage(msg)

    def _handle_uber_kill_achievements(self, msg: SpazBotDiedMessage) -> None:

        # Uber mine achievement:
        if msg.spazbot.last_attacked_type == ('explosion', 'land_mine'):
            self._land_mine_kills += 1
            if self._land_mine_kills >= 6:
                self._award_achievement('Gold Miner')

        # Uber tnt achievement:
        if msg.spazbot.last_attacked_type == ('explosion', 'tnt'):
            self._tnt_kills += 1
            if self._tnt_kills >= 6:
                bs.timer(
                    0.5, bs.WeakCall(self._award_achievement, 'TNT Terror')
                )

    def _handle_pro_kill_achievements(self, msg: SpazBotDiedMessage) -> None:

        # TNT achievement:
        if msg.spazbot.last_attacked_type == ('explosion', 'tnt'):
            self._tnt_kills += 1
            if self._tnt_kills >= 3:
                bs.timer(
                    0.5,
                    bs.WeakCall(
                        self._award_achievement, 'Boom Goes the Dynamite'
                    ),
                )

    def _handle_rookie_kill_achievements(self, msg: SpazBotDiedMessage) -> None:
        # Land-mine achievement:
        if msg.spazbot.last_attacked_type == ('explosion', 'land_mine'):
            self._land_mine_kills += 1
            if self._land_mine_kills >= 3:
                self._award_achievement('Mine Games')

    def _handle_training_kill_achievements(
            self, msg: SpazBotDiedMessage
    ) -> None:
        # Toss-off-map achievement:
        if msg.spazbot.last_attacked_type == ('picked_up', 'default'):
            self._throw_off_kills += 1
            if self._throw_off_kills >= 3:
                self._award_achievement('Off You Go Then')

    def _set_can_end_wave(self) -> None:
        self._can_end_wave = True

    def end_game(self) -> None:
        # Tell our bots to celebrate just to rub it in.
        assert self._bots is not None
        self._bots.final_celebrate()
        self._game_over = True
        self.do_end('defeat', delay=2.0)
        bs.setmusic(None)

    def on_continue(self) -> None:
        for player in self.players:
            if not player.is_alive():
                self.spawn_player(player)

    def _checkroundover(self) -> None:
        """Potentially end the round based on the state of the game."""
        if self.has_ended():
            return
        if not any(player.is_alive() for player in self.teams[0].players):
            # Allow continuing after wave 1.
            if self._wavenum > 1:
                self.continue_or_end_game()
            else:
                self.end_game()

# ba_meta export plugin


class CustomOnslaughtLevel(babase.Plugin):
    def on_app_running(self) -> None:
        babase.app.classic.add_coop_practice_level(
            bs._level.Level(
                'Onslaught Football',
                gametype=OnslaughtFootballGame,
                settings={
                    'map': 'Football Stadium',
                    'Epic Mode': False,
                },
                preview_texture_name='footballStadiumPreview',
            )
        )
        babase.app.classic.add_coop_practice_level(
            bs._level.Level(
                'Onslaught Football Epic',
                gametype=OnslaughtFootballGame,
                settings={
                    'map': 'Football Stadium',
                    'Epic Mode': True,
                },
                preview_texture_name='footballStadiumPreview',
            )
        )
