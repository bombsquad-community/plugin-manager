# Released under the MIT License. See LICENSE for details.
# initially made for gosquad server.
#
"""Elimination mini-game."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import weakref
import logging
import random
import enum
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.bomb import Bomb

if TYPE_CHECKING:
    from typing import Any, Sequence


class Icon(bs.Actor):
    """Creates in in-game icon on screen."""

    def __init__(
        self,
        player: Player,
        position: tuple[float, float],
        scale: float,
        *,
        show_lives: bool = True,
        show_death: bool = True,
        name_scale: float = 1.0,
        name_maxwidth: float = 115.0,
        flatness: float = 1.0,
        shadow: float = 1.0,
    ):
        super().__init__()

        self._player = weakref.ref(player)  # Avoid ref loops.
        self._show_lives = show_lives
        self._show_death = show_death
        self._name_scale = name_scale
        self._outline_tex = bs.gettexture('characterIconMask')

        icon = player.get_icon()
        self.node = bs.newnode(
            'image',
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
                'attach': 'bottomCenter',
            },
        )
        self._name_text = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': bs.Lstr(value=player.getname()),
                'color': bs.safecolor(player.team.color),
                'h_align': 'center',
                'v_align': 'center',
                'vr_depth': 410,
                'maxwidth': name_maxwidth,
                'shadow': shadow,
                'flatness': flatness,
                'h_attach': 'center',
                'v_attach': 'bottom',
            },
        )
        if self._show_lives:
            self._lives_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': 'x0',
                    'color': (1, 1, 0.5),
                    'h_align': 'left',
                    'vr_depth': 430,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'h_attach': 'center',
                    'v_attach': 'bottom',
                },
            )
        self.set_position_and_scale(position, scale)

    def set_position_and_scale(
        self, position: tuple[float, float], scale: float
    ) -> None:
        """(Re)position the icon."""
        assert self.node
        self.node.position = position
        self.node.scale = [70.0 * scale]
        self._name_text.position = (position[0], position[1] + scale * 52.0)
        self._name_text.scale = 1.0 * scale * self._name_scale
        if self._show_lives:
            self._lives_text.position = (
                position[0] + scale * 10.0,
                position[1] - scale * 43.0,
            )
            self._lives_text.scale = 1.0 * scale

    def update_for_lives(self) -> None:
        """Update for the target player's current lives."""
        player = self._player()
        if player:
            lives = player.lives
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
            bs.animate(
                self.node,
                'opacity',
                {
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
                    0.55: 0.2,
                },
            )
            player = self._player()
            lives = player.lives if player else 0
            if lives == 0:
                bs.timer(0.6, self.update_for_lives)

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            self.node.delete()
            return None
        return super().handlemessage(msg)


class BombType(enum.Enum):
    DEFAULT = 0
    NORMAL = 1
    STICKY = 2
    TRIGGER = 3
    ICE = 4

    @property
    def as_str(self) -> str:
        return {
            BombType.DEFAULT: "default",
            BombType.NORMAL: "normal",
            BombType.STICKY: "sticky",
            BombType.TRIGGER: "impact",
            BombType.ICE: "ice",
        }[self]

    @staticmethod
    def from_int(value: int) -> "BombType":
        return BombType(value)


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.lives = 0
        self.icons: list[Icon] = []


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.survival_seconds: int | None = None
        self.spawn_order: list[Player] = []


# ba_meta export bascenev1.GameActivity
class EliminationGame(bs.TeamGameActivity[Player, Team]):
    """Game type where last player(s) left alive win."""

    name = 'Gosquad Elimination'
    description = 'Elimination game big bombs meteor shower.'
    scoreconfig = bs.ScoreConfig(
        label='Survived', scoretype=bs.ScoreType.SECONDS, none_is_winner=True
    )
    # Show messages when players die since it's meaningful here.
    announce_player_deaths = True

    allow_mid_activity_joins = False

    @override
    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[bs.Setting]:
        settings = [
            bs.IntSetting(
                'Lives Per Player',
                default=3,
                min_value=1,
                max_value=10,
                increment=1,
            ),
            bs.IntChoiceSetting(
                'Time Limit',
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
            bs.FloatChoiceSetting(
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
            bs.BoolSetting('Epic Mode', default=True),
            bs.BoolSetting('Enable Speed', default=False),
            bs.BoolSetting('Boxing Gloves', default=True),
            bs.BoolSetting('Equip Shield', default=False),
            bs.BoolSetting('Meteor Shower', default=True),
            bs.IntChoiceSetting(
                'Meteor Delay',
                choices=[
                    ('None', 0),
                    ('15 Seconds', 15),
                    ('30 Seconds', 30),
                    ('45 Seconds', 45),
                    ('1 Minutes', 60),
                    ('1.5 Minutes', 90),
                    ('2 Minutes', 120),

                ],
                default=0,
            ),
            bs.IntChoiceSetting(
                'Bomb Count',
                choices=[
                    ('Default', 0),
                    ('1', 1),
                    ('2', 2),
                    ('3', 3),
                    ('4', 4),
                    ('5', 5),
                    ('6', 6),
                ],
                default=0,
            ),
            bs.IntChoiceSetting(
                'Bomb Type',
                choices=[
                    ('Default', 0),
                    ('Normal', 1),
                    ('Sticky', 2),
                    ('Trigger', 3),
                    ('Ice', 4),
                ],
                default=0,
            ),
            bs.BoolSetting('Revive Eliminated Players', default=True),
        ]
        if issubclass(sessiontype, bs.DualTeamSession):
            settings.append(bs.BoolSetting('Solo Mode', default=False))
            settings.append(
                bs.BoolSetting('Balance Total Lives', default=False)
            )
        return settings

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession) or issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        assert bs.app.classic is not None
        return bs.app.classic.getmaps('melee')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._start_time: float | None = None
        self._vs_text: bs.Actor | None = None
        self._round_end_timer: bs.Timer | None = None
        self._epic_mode = bool(settings['Epic Mode'])
        self._lives_per_player = int(settings['Lives Per Player'])
        self._time_limit = float(settings['Time Limit'])
        self._balance_total_lives = bool(
            settings.get('Balance Total Lives', False)
        )
        self._solo_mode = bool(settings.get('Solo Mode', False))
        self._enable_speed = bool(settings.get('Enable Speed', False))
        self._boxing_gloves = bool(settings.get('Boxing Gloves', False))
        self._equip_shield = bool(settings.get('Equip Shield', False))
        self._meteor_shower = bool(settings.get('Meteor Shower', False))
        self._meteor_start_time = float(settings['Meteor Delay'])
        self._bomb_count = int(settings['Bomb Count'])
        bomb_type_raw = BombType.from_int(settings.get('Bomb Type', 0))
        self._bomb_type = str(bomb_type_raw.as_str)
        self._revive_eliminated = bool(settings.get('Revive Eliminated Players', True))

        self._bomb_time = 3.0
        self._bomb_scale = 0.1
        self._add_player_timer: bs.Timer | None = None
        # add-player phase flag should be false to activate revival later
        self._add_player_phase = not self._revive_eliminated

        # Base class overrides:
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.SURVIVAL
        )

    @override
    def get_instance_description(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        return (
            'Last team standing wins.'
            if isinstance(self.session, bs.DualTeamSession)
            else 'Last one standing wins.'
        )

    @override
    def get_instance_description_short(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        return (
            'last team standing wins'
            if isinstance(self.session, bs.DualTeamSession)
            else 'last one standing wins'
        )

    @override
    def on_player_join(self, player: Player) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        player.lives = self._lives_per_player

        if self._solo_mode:
            player.team.spawn_order.append(player)
            self._update_solo_mode()
        else:
            # Create our icon and spawn.
            player.icons = [Icon(player, position=(0, 50), scale=0.8)]
            if player.lives > 0:
                self.spawn_player(player)

        # Don't waste time doing this until begin.
        if self.has_begun():
            self._update_icons()

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self._start_time = bs.time()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()
        if self._solo_mode:
            self._vs_text = bs.NodeActor(
                bs.newnode(
                    'text',
                    attrs={
                        'position': (0, 105),
                        'h_attach': 'center',
                        'h_align': 'center',
                        'maxwidth': 200,
                        'shadow': 0.5,
                        'vr_depth': 390,
                        'scale': 0.6,
                        'v_attach': 'bottom',
                        'color': (0.8, 0.8, 0.3, 1.0),
                        'text': bs.Lstr(resource='vsText'),
                    },
                )
            )

        # If balance-team-lives is on, add lives to the smaller team until
        # total lives match.
        if (
            isinstance(self.session, bs.DualTeamSession)
            and self._balance_total_lives
            and self.teams[0].players
            and self.teams[1].players
        ):
            if self._get_total_team_lives(
                self.teams[0]
            ) < self._get_total_team_lives(self.teams[1]):
                lesser_team = self.teams[0]
                greater_team = self.teams[1]
            else:
                lesser_team = self.teams[1]
                greater_team = self.teams[0]
            add_index = 0
            while self._get_total_team_lives(
                lesser_team
            ) < self._get_total_team_lives(greater_team):
                lesser_team.players[add_index].lives += 1
                add_index = (add_index + 1) % len(lesser_team.players)

        self._update_icons()
        if self._meteor_shower:
            bs.timer(self._meteor_start_time, self._initiate_bomb)

        # We could check game-over conditions at explicit trigger points,
        # but lets just do the simple thing and poll it.
        bs.timer(1.0, self._update, repeat=True)

    def _update_solo_mode(self) -> None:
        # For both teams, find the first player on the spawn order list with
        # lives remaining and spawn them if they're not alive.
        for team in self.teams:
            # Prune dead players from the spawn order.
            team.spawn_order = [p for p in team.spawn_order if p]
            for player in team.spawn_order:
                assert isinstance(player, Player)
                if player.lives > 0:
                    if not player.is_alive():
                        self.spawn_player(player)
                    break

    def _update_icons(self) -> None:
        # pylint: disable=too-many-branches

        # In free-for-all mode, everyone is just lined up along the bottom.
        if isinstance(self.session, bs.FreeForAllSession):
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
            if self._solo_mode:
                # First off, clear out all icons.
                for player in self.players:
                    player.icons = []

                # Now for each team, cycle through our available players
                # adding icons.
                for team in self.teams:
                    if team.id == 0:
                        xval = -60
                        x_offs = -78
                    else:
                        xval = 60
                        x_offs = 78
                    is_first = True
                    test_lives = 1
                    while True:
                        players_with_lives = [
                            p
                            for p in team.spawn_order
                            if p and p.lives >= test_lives
                        ]
                        if not players_with_lives:
                            break
                        for player in players_with_lives:
                            player.icons.append(
                                Icon(
                                    player,
                                    position=(xval, (40 if is_first else 25)),
                                    scale=1.0 if is_first else 0.5,
                                    name_maxwidth=130 if is_first else 75,
                                    name_scale=0.8 if is_first else 1.0,
                                    flatness=0.0 if is_first else 1.0,
                                    shadow=0.5 if is_first else 1.0,
                                    show_death=is_first,
                                    show_lives=False,
                                )
                            )
                            xval += x_offs * (0.8 if is_first else 0.56)
                            is_first = False
                        test_lives += 1
            # Non-solo mode.
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

    def _get_spawn_point(self, player: Player) -> bs.Vec3 | None:
        del player  # Unused.

        # In solo-mode, if there's an existing live player on the map, spawn at
        # whichever spot is farthest from them (keeps the action spread out).
        if self._solo_mode:
            living_player = None
            living_player_pos = None
            for team in self.teams:
                for tplayer in team.players:
                    if tplayer.is_alive():
                        assert tplayer.node
                        ppos = tplayer.node.position
                        living_player = tplayer
                        living_player_pos = ppos
                        break
            if living_player:
                assert living_player_pos is not None
                player_pos = bs.Vec3(living_player_pos)
                points: list[tuple[float, bs.Vec3]] = []
                for team in self.teams:
                    start_pos = bs.Vec3(self.map.get_start_position(team.id))
                    points.append(
                        ((start_pos - player_pos).length(), start_pos)
                    )
                # Hmm.. we need to sort vectors too?
                points.sort(key=lambda x: x[0])
                return points[-1][1]
        return None

    def _initiate_bomb(self) -> None:
        delay = 1.0
        bs.timer(delay, self._decrement_bomb_time, repeat=True)
        bs.timer(delay, self._increment_bomb_scale, repeat=True)

        # Kick off the first wave in a few seconds.
        self._set_bomb_timer()

    def _set_bomb_timer(self) -> None:
        bs.timer(self._bomb_time, self._drop_bomb_cluster)

    def _drop_bomb_cluster(self) -> None:
        # Random note: code like this is a handy way to plot out extents
        # and debug things.
        loc_test = False
        if loc_test:
            bs.newnode('locator', attrs={'position': (0.0, 20.0, -20.0)})

        # Drop a single bomb.
        # Drop them somewhere within our bounds with velocity pointing
        # toward the opposite side.
        # I took this specific calculation from a work of byAngel.
        # Credit goes to him.
        if self.map.getname() == 'Hockey Stadium':
            pos = (random.randrange(-11, 12), 6, random.randrange(-4, 5))
        elif self.map.getname() == 'Football Stadium':
            pos = (random.randrange(-10, 11), 6, random.randrange(-5, 6))
        elif self.map.getname() == 'The Pad':
            pos = (random.randrange(-3, 4), 10, random.randrange(-8, 4))
        elif self.map.getname() == 'Doom Shroom':
            pos = (random.randrange(-7, 8), 8, random.randrange(-7, 1))
        elif self.map.getname() == 'Lake Frigid':
            pos = (random.randrange(-7, 8), 8, random.randrange(-7, 3))
        elif self.map.getname() == 'Tower D':
            pos = (random.randrange(-7, 8), 8, random.randrange(-5, 5))
        elif self.map.getname() == 'Step Right Up':
            pos = (random.randrange(-7, 8), 10, random.randrange(-8, 3))
        elif self.map.getname() == 'Courtyard':
            pos = (random.randrange(-7, 8), 10, random.randrange(-6, 4))
        elif self.map.getname() == 'Rampage':
            pos = (random.randrange(-7, 8), 11, random.randrange(-5, -2))
        else:
            pos = (random.randrange(-7, 8), 6, random.randrange(-5, 6))

        dropdir = (-1.0 if pos[0] > 0 else 1.0)
        vel = ((-5.0 + random.random() * 30.0) * dropdir, -4.0, 0)

        self._drop_bomb(pos, vel)
        self._set_bomb_timer()

    def _drop_bomb(
            self, position: Sequence[float], velocity: Sequence[float]
    ) -> None:
        bomb_type = random.choice([
            'land_mine', 'land_mine', 'tnt', 'tnt',
            'impact', 'sticky', 'normal',
        ])
        bomb = Bomb(
            position=position,
            velocity=velocity,
            bomb_type=bomb_type,
            blast_radius=3.0 if bomb_type == 'impact' else self._bomb_scale,
        ).autoretain()

        if bomb_type != 'impact':
            bs.animate(bomb.node, 'mesh_scale', {
                0.0: 0.2,
                0.7: 0.2,
                1.0: self._bomb_scale}
            )

        if bomb_type == 'land_mine':
            bs.timer(1.2, bomb.arm)

    def _decrement_bomb_time(self) -> None:
        self._bomb_time = max(2.0, self._bomb_time * 0.8)

    def _increment_bomb_scale(self) -> None:
        self._bomb_scale = min(8.0, self._bomb_scale * 1.2)

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        """Spawn a player (override)."""
        actor = self.spawn_player_spaz(player, self._get_spawn_point(player))
        if not self._solo_mode:
            bs.timer(0.3, bs.CallStrict(self._print_lives, player))

        if self._boxing_gloves:
            actor.equip_boxing_gloves()
        if self._equip_shield:
            actor.equip_shields()

        actor.node.hockey = self._enable_speed
        actor.bomb_count = actor.bomb_count if self._bomb_count == 0 else self._bomb_count
        bomb_type = actor.bomb_type if self._bomb_type == 'default' else self._bomb_type
        actor.bomb_type = bomb_type
        actor.bomb_type_default = bomb_type

        # If we have any icons, update their state.
        for icon in player.icons:
            icon.handle_player_spawned()
        return actor

    def _print_lives(self, player: Player) -> None:
        from bascenev1lib.actor import popuptext

        # We get called in a timer so it's possible our player has left/etc.
        if not player or not player.is_alive() or not player.node:
            return

        popuptext.PopupText(
            'x' + str(player.lives - 1),
            color=(1, 1, 0, 1),
            offset=(0, -0.8, 0),
            random_offset=0.0,
            scale=1.8,
            position=player.node.position,
        ).autoretain()

    @override
    def on_player_leave(self, player: Player) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        super().on_player_leave(player)
        player.icons = []

        # Remove us from spawn-order.
        if self._solo_mode:
            if player in player.team.spawn_order:
                player.team.spawn_order.remove(player)

        # Update icons in a moment since our team will be gone from the
        # list then.
        bs.timer(0, self._update_icons)

        # If the player to leave was the last in spawn order and had
        # their final turn currently in-progress, mark the survival time
        # for their team.
        if self._get_total_team_lives(player.team) == 0:
            assert self._start_time is not None
            player.team.survival_seconds = int(bs.time() - self._start_time)

    def _get_total_team_lives(self, team: Team) -> int:
        return sum(player.lives for player in team.players)

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            player: Player = msg.getplayer(Player)

            player.lives -= 1
            if player.lives < 0:
                logging.exception(
                    "Got lives < 0 in Elim; this shouldn't happen. solo: %s",
                    self._solo_mode,
                )
                player.lives = 0

            # If we have any icons, update their state.
            for icon in player.icons:
                icon.handle_player_died()

            # Play big death sound on our last death
            # or for every one in solo mode.
            if self._solo_mode or player.lives == 0:
                SpazFactory.get().single_player_death_sound.play()

            # If we hit zero lives, we're dead (and our team might be too).
            if player.lives == 0:
                # If the whole team is now dead, mark their survival time.
                if self._get_total_team_lives(player.team) == 0:
                    assert self._start_time is not None
                    player.team.survival_seconds = int(
                        bs.time() - self._start_time
                    )
            else:
                # Otherwise, in regular mode, respawn.
                if not self._solo_mode:
                    self.respawn_player(player)

            # In solo, put ourself at the back of the spawn order.
            if self._solo_mode:
                try:
                    player.team.spawn_order.remove(player)
                    player.team.spawn_order.append(player)
                except:
                    pass

    def _update(self) -> None:
        if self._solo_mode:
            # For both teams, find the first player on the spawn order
            # list with lives remaining and spawn them if they're not alive.
            for team in self.teams:
                # Prune dead players from the spawn order.
                team.spawn_order = [p for p in team.spawn_order if p]
                for player in team.spawn_order:
                    assert isinstance(player, Player)
                    if player.lives > 0:
                        if not player.is_alive():
                            self.spawn_player(player)
                            self._update_icons()
                        break

        # If we're down to 1 or fewer living teams, start a timer to end
        # the game (allows the dust to settle and draws to occur if deaths
        # are close enough).
        if len(self._get_living_teams()) < 2:
            self._round_end_timer = bs.Timer(0.5, self.end_game)

        # Start the 120s timer when only 2 players remain.
        # Do this only with minimum 5 players.
        if len(self._get_living_players()) == 2:
            if len(self.players) >= 5 and not self._add_player_phase:
                self._add_player_phase = True
                bs.broadcastmessage(
                    "Be ready! ⚔️ 2 random eliminated players may rejoin the game in 2 minutes.",
                    color=(1, 0.7, 0.1)
                )
                self._add_player_timer = bs.BaseTimer(
                    120, bs.WeakCallStrict(self._revive_random_players))

    def _get_living_teams(self) -> list[Team]:
        return [
            team
            for team in self.teams
            if len(team.players) > 0
            and any(player.lives > 0 for player in team.players)
        ]

    def _get_living_players(self) -> list[Player]:
        return [
            player for player in self.players if player.lives > 0
        ]

    def _revive_random_players(self) -> None:
        # Cancel if game already ended
        if self.has_ended():
            return

        eliminated_players = [p for p in self.players if p.exists() and p.lives <= 0]
        if not eliminated_players:
            bs.broadcastmessage("No eliminated players available.", color=(0.7, 0.7, 0.7))
            return

        # Pick up to 2 random eliminated players
        revived = random.sample(eliminated_players, min(2, len(eliminated_players)))
        for player in revived:
            player.lives = 1
            self.spawn_player(player)
            for icon in player.icons:
                icon.update_for_lives()
                assert icon.node, icon._name_text
                icon._name_text.opacity = 1.0
                icon.node.color = (1, 1, 1)
                icon.node.opacity = 1.0
            bs.broadcastmessage(f"{player.getname(full=True)} rejoined the game!", color=(0, 1, 0))

        self._update_icons()
        self._add_player_phase = False  # Allow the event to trigger again later if desired

    @override
    def end_game(self) -> None:
        """End the game."""
        if self.has_ended():
            return
        results = bs.GameResults()
        self._vs_text = None  # Kill our 'vs' if its there.
        for team in self.teams:
            results.set_team_score(team, team.survival_seconds)
        self.end(results=results)
