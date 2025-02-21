# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs
from bascenev1lib.actor.bomb import Bomb
from bascenev1lib.actor.onscreentimer import OnScreenTimer

if TYPE_CHECKING:
    from typing import Any, Sequence


lang = bs.app.lang.language

if lang == 'Spanish':
    name = 'Lluvia de Meteoritos v2'
    bomb_type = 'Tipo de Bomba'
    ice = 'hielo'
    sticky = 'pegajosa'
    impact = 'insta-bomba'
    land_mine = 'mina terrestre'
    random_bomb = 'aleatoria'
    normal_rain = 'Lluvia Normal'
    frozen_rain = 'Lluvia Congelada'
    sticky_rain = 'Lluvia Pegajosa'
    impact_rain = 'Lluvia de Impacto'
    mine_rain = 'Lluvia de Minas'
    tnt_rain = 'Lluvia de TNT'
    random_rain = 'Lluvia Aleatoria'
else:
    name = 'Meteor Shower v2'
    bomb_type = 'Bomb Type'
    ice = 'ice'
    sticky = 'sticky'
    impact = 'impact'
    land_mine = 'land mine'
    random_bomb = 'random'
    normal_rain = 'Normal Rain'
    frozen_rain = 'Frozen Rain'
    sticky_rain = 'Sticky Rain'
    impact_rain = 'Impact Rain'
    mine_rain = 'Mine Rain'
    tnt_rain = 'TNT Rain'
    random_rain = 'Random Rain'


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        super().__init__()
        self.death_time: float | None = None


class Team(bs.Team[Player]):
    """Our team type for this game."""


# ba_meta export bascenev1.GameActivity
class MeteorShowerv2Game(bs.TeamGameActivity[Player, Team]):
    """Minigame involving dodging falling bombs."""

    name = name
    description = 'Dodge the falling bombs.'
    scoreconfig = bs.ScoreConfig(
        label='Survived', scoretype=bs.ScoreType.MILLISECONDS, version='B'
    )

    # Print messages when players die (since its meaningful in this game).
    announce_player_deaths = True

    # Don't allow joining after we start
    # (would enable leave/rejoin tomfoolery).
    allow_mid_activity_joins = False

    @classmethod
    def get_available_settings(
            cls, sessiontype: type[bs.Session]
    ) -> list[babase.Setting]:
        settings = [
            bs.IntChoiceSetting(
                bomb_type,
                choices=[
                    ('normal', 0),
                    (ice, 1),
                    (sticky, 2),
                    (impact, 3),
                    (land_mine, 4),
                    ('tnt', 5),
                    (random_bomb, 6)
                ],
                default=0,
            ),
            bs.BoolSetting('Epic Mode', default=False),
        ]
        return settings

    # We're currently hard-coded for one map.
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Rampage']

    # We support teams, free-for-all, and co-op sessions.
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return (
            issubclass(sessiontype, bs.DualTeamSession)
            or issubclass(sessiontype, bs.FreeForAllSession)
            or issubclass(sessiontype, bs.CoopSession)
        )

    def __init__(self, settings: dict):
        super().__init__(settings)
        btype = int(settings[bomb_type])
        if btype == 0:
            newbtype = 'normal'
        elif btype == 1:
            newbtype = 'ice'
        elif btype == 2:
            newbtype = 'sticky'
        elif btype == 3:
            newbtype = 'impact'
        elif btype == 4:
            newbtype = 'land_mine'
        elif btype == 5:
            newbtype = 'tnt'
        else:
            newbtype = 'random'
        self._bomb_type = newbtype
        self._epic_mode = settings.get('Epic Mode', False)
        self._last_player_death_time: float | None = None
        self._meteor_time = 2.0
        self._timer: OnScreenTimer | None = None

        # Some base class overrides:
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.SURVIVAL
        )
        if self._epic_mode:
            self.slow_motion = True

    def on_begin(self) -> None:
        super().on_begin()

        # Drop a wave every few seconds.. and every so often drop the time
        # between waves ..lets have things increase faster if we have fewer
        # players.
        delay = 5.0 if len(self.players) > 2 else 2.5
        if self._epic_mode:
            delay *= 0.25
        bs.timer(delay, self._decrement_meteor_time, repeat=True)

        # Kick off the first wave in a few seconds.
        delay = 3.0
        if self._epic_mode:
            delay *= 0.25
        bs.timer(delay, self._set_meteor_timer)

        self._timer = OnScreenTimer()
        self._timer.start()

        # Check for immediate end (if we've only got 1 player, etc).
        bs.timer(5.0, self._check_end_game)

    def on_player_leave(self, player: Player) -> None:
        # Augment default behavior.
        super().on_player_leave(player)

        # A departing player may trigger game-over.
        self._check_end_game()

    # overriding the default character spawning..
    def spawn_player(self, player: Player) -> bs.Actor:
        spaz = self.spawn_player_spaz(player)

        # Let's reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up.
        spaz.connect_controls_to_player(
            enable_punch=False, enable_bomb=False, enable_pickup=False
        )

        # Also lets have them make some noise when they die.
        spaz.play_big_death_sound = True
        return spaz

    # Various high-level game events come through this method.
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):

            # Augment standard behavior.
            super().handlemessage(msg)

            curtime = bs.time()

            # Record the player's moment of death.
            # assert isinstance(msg.spaz.player
            msg.getplayer(Player).death_time = curtime

            # In co-op mode, end the game the instant everyone dies
            # (more accurate looking).
            # In teams/ffa, allow a one-second fudge-factor so we can
            # get more draws if players die basically at the same time.
            if isinstance(self.session, bs.CoopSession):
                # Teams will still show up if we check now.. check in
                # the next cycle.
                babase.pushcall(self._check_end_game)

                # Also record this for a final setting of the clock.
                self._last_player_death_time = curtime
            else:
                bs.timer(1.0, self._check_end_game)

        else:
            # Default handler:
            return super().handlemessage(msg)
        return None

    def _check_end_game(self) -> None:
        living_team_count = 0
        for team in self.teams:
            for player in team.players:
                if player.is_alive():
                    living_team_count += 1
                    break

        # In co-op, we go till everyone is dead.. otherwise we go
        # until one team remains.
        if isinstance(self.session, bs.CoopSession):
            if living_team_count <= 0:
                self.end_game()
        else:
            if living_team_count <= 1:
                self.end_game()

    def _set_meteor_timer(self) -> None:
        bs.timer(
                (1.0 + 0.2 * random.random()) * self._meteor_time,
            self._drop_bomb_cluster,
        )

    def _drop_bomb_cluster(self) -> None:

        # Random note: code like this is a handy way to plot out extents
        # and debug things.
        loc_test = False
        if loc_test:
            bs.newnode('locator', attrs={'position': (8, 6, -5.5)})
            bs.newnode('locator', attrs={'position': (8, 6, -2.3)})
            bs.newnode('locator', attrs={'position': (-7.3, 6, -5.5)})
            bs.newnode('locator', attrs={'position': (-7.3, 6, -2.3)})

        # Drop several bombs in series.
        delay = 0.0
        for _i in range(random.randrange(1, 3)):
            # Drop them somewhere within our bounds with velocity pointing
            # toward the opposite side.
            pos = (
                -7.3 + 15.3 * random.random(),
                11,
                -5.57 + 2.1 * random.random(),
            )
            dropdir = -1.0 if pos[0] > 0 else 1.0
            vel = (
                (-5.0 + random.random() * 30.0) * dropdir,
                random.uniform(-3.066, -4.12),
                0,
            )
            bs.timer(delay, babase.Call(self._drop_bomb, pos, vel))
            delay += 0.1
        self._set_meteor_timer()

    def _drop_bomb(
            self, position: Sequence[float], velocity: Sequence[float]
    ) -> None:
        if self._bomb_type == 'tnt':
            bomb_type = random.choice(['tnt', 'tnt', 'tnt', 'tnt', 'impact'])
        elif self._bomb_type == 'land_mine':
            bomb_type = random.choice([
                'land_mine', 'land_mine', 'land_mine', 'land_mine', 'impact'])
        elif self._bomb_type == 'random':
            bomb_type = random.choice([
                'normal', 'ice', 'sticky', 'impact', 'land_mine', 'tnt'])
        else:
            bomb_type = self._bomb_type
        Bomb(position=position,
             velocity=velocity,
             bomb_type=bomb_type).autoretain()

    def _decrement_meteor_time(self) -> None:
        self._meteor_time = max(0.01, self._meteor_time * 0.9)

    def end_game(self) -> None:
        cur_time = bs.time()
        assert self._timer is not None
        start_time = self._timer.getstarttime()

        # Mark death-time as now for any still-living players
        # and award players points for how long they lasted.
        # (these per-player scores are only meaningful in team-games)
        for team in self.teams:
            for player in team.players:
                survived = False

                # Throw an extra fudge factor in so teams that
                # didn't die come out ahead of teams that did.
                if player.death_time is None:
                    survived = True
                    player.death_time = cur_time + 1

                # Award a per-player score depending on how many seconds
                # they lasted (per-player scores only affect teams mode;
                # everywhere else just looks at the per-team score).
                score = int(player.death_time - self._timer.getstarttime())
                if survived:
                    score += 50  # A bit extra for survivors.
                self.stats.player_scored(player, score, screenmessage=False)

        # Stop updating our time text, and set the final time to match
        # exactly when our last guy died.
        self._timer.stop(endtime=self._last_player_death_time)

        # Ok now calc game results: set a score for each team and then tell
        # the game to end.
        results = bs.GameResults()

        # Remember that 'free-for-all' mode is simply a special form
        # of 'teams' mode where each player gets their own team, so we can
        # just always deal in teams and have all cases covered.
        for team in self.teams:

            # Set the team score to the max time survived by any player on
            # that team.
            longest_life = 0.0
            for player in team.players:
                assert player.death_time is not None
                longest_life = max(longest_life, player.death_time - start_time)

            # Submit the score value in milliseconds.
            results.set_team_score(team, int(1000.0 * longest_life))

        self.end(results=results)


# ba_meta export plugin
class MeteorShowerv2Coop(babase.Plugin):
    def on_app_running(self) -> None:
        babase.app.classic.add_coop_practice_level(
            bs._level.Level(
                normal_rain,
                gametype=MeteorShowerv2Game,
                settings={bomb_type: 0},
                preview_texture_name='rampagePreview',
            )
        )
        babase.app.classic.add_coop_practice_level(
            bs._level.Level(
                frozen_rain,
                gametype=MeteorShowerv2Game,
                settings={bomb_type: 1},
                preview_texture_name='rampagePreview',
            )
        )
        babase.app.classic.add_coop_practice_level(
            bs._level.Level(
                sticky_rain,
                gametype=MeteorShowerv2Game,
                settings={bomb_type: 2},
                preview_texture_name='rampagePreview',
            )
        )
        babase.app.classic.add_coop_practice_level(
            bs._level.Level(
                impact_rain,
                gametype=MeteorShowerv2Game,
                settings={bomb_type: 3},
                preview_texture_name='rampagePreview',
            )
        )
        babase.app.classic.add_coop_practice_level(
            bs._level.Level(
                mine_rain,
                gametype=MeteorShowerv2Game,
                settings={bomb_type: 4},
                preview_texture_name='rampagePreview',
            )
        )
        babase.app.classic.add_coop_practice_level(
            bs._level.Level(
                tnt_rain,
                gametype=MeteorShowerv2Game,
                settings={bomb_type: 5},
                preview_texture_name='rampagePreview',
            )
        )
        babase.app.classic.add_coop_practice_level(
            bs._level.Level(
                random_rain,
                gametype=MeteorShowerv2Game,
                settings={bomb_type: 6},
                preview_texture_name='rampagePreview',
            )
        )
