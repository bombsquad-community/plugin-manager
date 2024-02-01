# Ported to api 8 by brostos using baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 8

# - - - - - - - - - - - - - - - - - - - - -
# - Fat-Pigs! by Zacker Tz || Zacker#5505 -
# - Version 0.01 :v                       -
# - - - - - - - - - - - - - - - - - - - - -

from __future__ import annotations

from typing import TYPE_CHECKING

import random
import babase
import bauiv1 as bui
import bascenev1 as bs
from bascenev1lib.actor.bomb import Bomb
from bascenev1lib.actor.onscreentimer import OnScreenTimer
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard

if TYPE_CHECKING:
    from typing import Any, Union, Sequence, Optional

# - - - - - - - Mini - Settings - - - - - - - - - - - - - - - - #

zkBombs_limit = 3  # Number of bombs you can use | Default = 3
zkPunch = False   # Enable/Disable punchs  | Default = False
zkPickup = False   # Enable/Disable pickup  | Default = False

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0

# ba_meta export bascenev1.GameActivity


class FatPigs(bs.TeamGameActivity[Player, Team]):
    """A game type based on acquiring kills."""

    name = 'Fat-Pigs!'
    description = 'Survive...'

    # Print messages when players die since it matters here.
    announce_player_deaths = True

    @classmethod
    def get_available_settings(
            cls, sessiontype: type[bs.Session]) -> list[babase.Setting]:
        settings = [
            bs.IntSetting(
                'Kills to Win Per Player',
                min_value=1,
                default=5,
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
                default=0.25,
            ),
            bs.BoolSetting('Epic Mode', default=False),
        ]

        # In teams mode, a suicide gives a point to the other team, but in
        # free-for-all it subtracts from your own score. By default we clamp
        # this at zero to benefit new players, but pro players might like to
        # be able to go negative. (to avoid a strategy of just
        # suiciding until you get a good drop)
        if issubclass(sessiontype, bs.FreeForAllSession):
            settings.append(
                bs.BoolSetting('Allow Negative Scores', default=False))

        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return (issubclass(sessiontype, bs.DualTeamSession)
                or issubclass(sessiontype, bs.FreeForAllSession))

    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Courtyard', 'Rampage', 'Monkey Face', 'Lake Frigid', 'Step Right Up']

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._meteor_time = 2.0
        self._score_to_win: Optional[int] = None
        self._dingsound = bs.getsound('dingSmall')
        self._epic_mode = bool(settings['Epic Mode'])
      #  self._text_credit = bool(settings['Credits'])
        self._kills_to_win_per_player = int(
            settings['Kills to Win Per Player'])
        self._time_limit = float(settings['Time Limit'])
        self._allow_negative_scores = bool(
            settings.get('Allow Negative Scores', False))

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (bs.MusicType.EPIC if self._epic_mode else
                              bs.MusicType.TO_THE_DEATH)

    def get_instance_description(self) -> Union[str, Sequence]:
        return 'Crush ${ARG1} of your enemies.', self._score_to_win

    def get_instance_description_short(self) -> Union[str, Sequence]:
        return 'kill ${ARG1} enemies', self._score_to_win

    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self._update_scoreboard()

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
     #   self.setup_standard_powerup_drops()
        # Ambiente
        gnode = bs.getactivity().globalsnode
        gnode.tint = (0.8, 1.2, 0.8)
        gnode.ambient_color = (0.7, 1.0, 0.6)
        gnode.vignette_outer = (0.4, 0.6, 0.4)  # C
     #   gnode.vignette_inner = (0.9, 0.9, 0.9)

        # Base kills needed to win on the size of the largest team.
        self._score_to_win = (self._kills_to_win_per_player *
                              max(1, max(len(t.players) for t in self.teams)))
        self._update_scoreboard()

        delay = 5.0 if len(self.players) > 2 else 2.5
        if self._epic_mode:
            delay *= 0.25
        bs.timer(delay, self._decrement_meteor_time, repeat=False)

        # Kick off the first wave in a few seconds.
        delay = 3.0
        if self._epic_mode:
            delay *= 0.25
        bs.timer(delay, self._set_meteor_timer)

      #  self._timer = OnScreenTimer()
       # self._timer.start()

        # Check for immediate end (if we've only got 1 player, etc).
        bs.timer(5.0, self._check_end_game)

        t = bs.newnode('text',
                       attrs={'text': "Minigame by Zacker Tz",
                              'scale': 0.7,
                              'position': (0.001, 625),
                              'shadow': 0.5,
                              'opacity': 0.7,
                              'flatness': 1.2,
                              'color': (0.6, 1, 0.6),
                              'h_align': 'center',
                              'v_attach': 'bottom'})

    def spawn_player(self, player: Player) -> bs.Actor:
        spaz = self.spawn_player_spaz(player)

        # Let's reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up.
        spaz.connect_controls_to_player(enable_punch=zkPunch,
                                        enable_bomb=True,
                                        enable_pickup=zkPickup)

        spaz.bomb_count = zkBombs_limit
        spaz._max_bomb_count = zkBombs_limit
        spaz.bomb_type_default = 'sticky'
        spaz.bomb_type = 'sticky'

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

    def _set_meteor_timer(self) -> None:
        bs.timer((1.0 + 0.2 * random.random()) * self._meteor_time,
                 self._drop_bomb_cluster)

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
            pos = (-7.3 + 15.3 * random.random(), 11,
                   -5.5 + 2.1 * random.random())
            dropdir = (-1.0 if pos[0] > 0 else 1.0)
            vel = ((-5.0 + random.random() * 30.0) * dropdir, -4.0, 0)
            bs.timer(delay, babase.Call(self._drop_bomb, pos, vel))
            delay += 0.1
        self._set_meteor_timer()

    def _drop_bomb(self, position: Sequence[float],
                   velocity: Sequence[float]) -> None:
        Bomb(position=position, velocity=velocity, bomb_type='sticky').autoretain()

    def _decrement_meteor_time(self) -> None:
        self._meteor_time = max(0.01, self._meteor_time * 0.9)

    def handlemessage(self, msg: Any) -> Any:

        if isinstance(msg, bs.PlayerDiedMessage):

            # Augment standard behavior.
            super().handlemessage(msg)

            player = msg.getplayer(Player)
            self.respawn_player(player)

            killer = msg.getkillerplayer(Player)
            if killer is None:
                return None

            # Handle team-kills.
            if killer.team is player.team:

                # In free-for-all, killing yourself loses you a point.
                if isinstance(self.session, bs.FreeForAllSession):
                    new_score = player.team.score - 1
                    if not self._allow_negative_scores:
                        new_score = max(0, new_score)
                    player.team.score = new_score

                # In teams-mode it gives a point to the other team.
                else:
                    self._dingsound.play()
                    for team in self.teams:
                        if team is not killer.team:
                            team.score += 1

            # Killing someone on another team nets a kill.
            else:
                killer.team.score += 1
                self._dingsound.play()

                # In FFA show scores since its hard to find on the scoreboard.
                if isinstance(killer.actor, PlayerSpaz) and killer.actor:
                    killer.actor.set_score_text(str(killer.team.score) + '/' +
                                                str(self._score_to_win),
                                                color=killer.team.color,
                                                flash=True)

            self._update_scoreboard()

            # If someone has won, set a timer to end shortly.
            # (allows the dust to clear and draws to occur if deaths are
            # close enough)
            assert self._score_to_win is not None
            if any(team.score >= self._score_to_win for team in self.teams):
                bs.timer(0.5, self.end_game)

        else:
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

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score,
                                            self._score_to_win)

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)
