"""New Duel / Created by: byANG3L"""

# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs
import _babase
import random
from bascenev1lib.actor.bomb import Bomb
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.onscreentimer import OnScreenTimer

if TYPE_CHECKING:
    pass

lang = bs.app.lang.language
if lang == 'Spanish':
    name = 'Infección'
    description = '¡Se está extendiendo!'
    instance_description = '¡Evite la propagación!'
    mines = 'Minas'
    enable_bombs = 'Habilitar Bombas'
    extra_mines = 'Seg/Mina Extra'
    max_infected_size = 'Tamaño Máx. de Infección'
    max_size_increases = 'Incrementar Tamaño Cada'
    infection_spread_rate = 'Velocidad de Infección'
    faster = 'Muy Rápido'
    fast = 'Rápido'
    normal = 'Normal'
    slow = 'Lento'
    slowest = 'Muy Lento'
    insane = 'Insano'
else:
    name = 'Infection'
    description = "It's spreading!"
    instance_description = 'Avoid the spread!'
    mines = 'Mines'
    enable_bombs = 'Enable Bombs'
    extra_mines = 'Sec/Extra Mine'
    max_infected_size = 'Max Infected Size'
    max_size_increases = 'Max Size Increases Every'
    infection_spread_rate = 'Infection Spread Rate'
    faster = 'Faster'
    fast = 'Fast'
    normal = 'Normal'
    slow = 'Slow'
    slowest = 'Slowest'
    insane = 'Insane'


def ba_get_api_version():
    return 6


def ba_get_levels():
    return [babase._level.Level(
        name,
        gametype=Infection,
        settings={},
        preview_texture_name='footballStadiumPreview')]


class myMine(Bomb):
    # reason for the mine class is so we can add the death zone
    def __init__(self,
                 pos: Sequence[float] = (0.0, 1.0, 0.0)):
        Bomb.__init__(self, position=pos, bomb_type='land_mine')
        showInSpace = False
        self.died = False
        self.rad = 0.3
        self.zone = bs.newnode(
            'locator',
            attrs={
                'shape': 'circle',
                'position': self.node.position,
                'color': (1, 0, 0),
                'opacity': 0.5,
                'draw_beauty': showInSpace,
                'additive': True})
        bs.animate_array(
            self.zone,
            'size',
            1,
            {0: [0.0], 0.05: [2*self.rad]})

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            if not self.died:
                self.getactivity().mine_count -= 1
                self.died = True
                bs.animate_array(
                    self.zone,
                    'size',
                    1,
                    {0: [2*self.rad], 0.05: [0]})
                self.zone = None
            super().handlemessage(msg)
        else:
            super().handlemessage(msg)


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.survival_seconds: Optional[int] = None
        self.death_time: Optional[float] = None


class Team(bs.Team[Player]):
    """Our team type for this game."""


# ba_meta export bascenev1.GameActivity
class Infection(bs.TeamGameActivity[Player, Team]):
    """A game type based on acquiring kills."""

    name = name
    description = description

    # Print messages when players die since it matters here.
    announce_player_deaths = True
    allow_mid_activity_joins = False

    @classmethod
    def get_available_settings(
            cls, sessiontype: Type[bs.Session]) -> List[babase.Setting]:
        settings = [
            bs.IntSetting(
                mines,
                min_value=5,
                default=10,
                increment=5,
            ),
            bs.BoolSetting(enable_bombs, default=True),
            bs.IntSetting(
                extra_mines,
                min_value=1,
                default=10,
                increment=1,
            ),
            bs.IntSetting(
                max_infected_size,
                min_value=4,
                default=6,
                increment=1,
            ),
            bs.IntChoiceSetting(
                max_size_increases,
                choices=[
                    ('10s', 10),
                    ('20s', 20),
                    ('30s', 30),
                    ('1 Minute', 60),
                ],
                default=20,
            ),
            bs.IntChoiceSetting(
                infection_spread_rate,
                choices=[
                    (slowest, 0.01),
                    (slow, 0.02),
                    (normal, 0.03),
                    (fast, 0.04),
                    (faster, 0.05),
                    (insane, 0.08),
                ],
                default=0.03,
            ),
            bs.BoolSetting('Epic Mode', default=False),
        ]
        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return (issubclass(sessiontype, bs.CoopSession)
                or issubclass(sessiontype, bs.MultiTeamSession))

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return ['Doom Shroom', 'Rampage', 'Hockey Stadium',
                'Crag Castle', 'Big G', 'Football Stadium']

    def __init__(self, settings: dict):
        super().__init__(settings)
        self.mines: List = []
        self._update_rate = 0.1
        self._last_player_death_time = None
        self._start_time: Optional[float] = None
        self._timer: Optional[OnScreenTimer] = None
        self._epic_mode = bool(settings['Epic Mode'])
        self._max_mines = int(settings[mines])
        self._extra_mines = int(settings[extra_mines])
        self._enable_bombs = bool(settings[enable_bombs])
        self._max_size = int(settings[max_infected_size])
        self._max_size_increases = float(settings[max_size_increases])
        self._growth_rate = float(settings[infection_spread_rate])

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (bs.MusicType.EPIC if self._epic_mode else
                              bs.MusicType.SURVIVAL)

    def get_instance_description(self) -> Union[str, Sequence]:
        return instance_description

    def get_instance_description_short(self) -> Union[str, Sequence]:
        return instance_description

    def on_begin(self) -> None:
        super().on_begin()
        self._start_time = bs.time()
        self.mine_count = 0
        bs.timer(self._update_rate,
                 bs.WeakCall(self._mine_update),
                 repeat=True)
        bs.timer(self._max_size_increases*1.0,
                 bs.WeakCall(self._max_size_update),
                 repeat=True)
        bs.timer(self._extra_mines*1.0,
                 bs.WeakCall(self._max_mine_update),
                 repeat=True)
        self._timer = OnScreenTimer()
        self._timer.start()

        # Check for immediate end (if we've only got 1 player, etc).
        bs.timer(5.0, self._check_end_game)

    def on_player_join(self, player: Player) -> None:
        if self.has_begun():
            assert self._timer is not None
            player.survival_seconds = self._timer.getstarttime()
            bs.broadcastmessage(
                babase.Lstr(resource='playerDelayedJoinText',
                            subs=[('${PLAYER}', player.getname(full=True))]),
                color=(0, 1, 0),
            )
            return
        self.spawn_player(player)

    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        self._check_end_game()

    def _max_mine_update(self) -> None:
        self._max_mines += 1

    def _max_size_update(self) -> None:
        self._max_size += 1

    def _mine_update(self) -> None:
        # print self.mineCount
        # purge dead mines, update their animantion, check if players died
        for m in self.mines:
            if not m.node:
                self.mines.remove(m)
            else:
                # First, check if any player is within the current death zone
                for player in self.players:
                    if not player.actor is None:
                        if player.actor.is_alive():
                            p1 = player.actor.node.position
                            p2 = m.node.position
                            diff = (babase.Vec3(p1[0]-p2[0],
                                                0.0,
                                                p1[2]-p2[2]))
                            dist = (diff.length())
                            if dist < m.rad:
                                player.actor.handlemessage(bs.DieMessage())
                # Now tell the circle to grow to the new size
                if m.rad < self._max_size:
                    bs.animate_array(
                        m.zone, 'size', 1,
                        {0: [m.rad*2],
                         self._update_rate: [(m.rad+self._growth_rate)*2]})
                    # Tell the circle to be the new size.
                    # This will be the new check radius next time.
                    m.rad += self._growth_rate
        # make a new mine if needed.
        if self.mine_count < self._max_mines:
            pos = self.getRandomPowerupPoint()
            self.mine_count += 1
            self._flash_mine(pos)
            bs.timer(0.95, babase.Call(self._make_mine, pos))

    def _make_mine(self, posn: Sequence[float]) -> None:
        m = myMine(pos=posn)
        m.arm()
        self.mines.append(m)

    def _flash_mine(self, pos: Sequence[float]) -> None:
        light = bs.newnode('light',
                           attrs={
                               'position': pos,
                               'color': (1, 0.2, 0.2),
                               'radius': 0.1,
                               'height_attenuated': False
                           })
        bs.animate(light, 'intensity', {0.0: 0, 0.1: 1.0, 0.2: 0}, loop=True)
        bs.timer(1.0, light.delete)

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, int(team.survival_seconds))
        self.end(results=results, announce_delay=0.8)

    def _flash_player(self, player: Player, scale: float) -> None:
        assert isinstance(player.actor, PlayerSpaz)
        assert player.actor.node
        pos = player.actor.node.position
        light = bs.newnode('light',
                           attrs={
                               'position': pos,
                               'color': (1, 1, 0),
                               'height_attenuated': False,
                               'radius': 0.4
                           })
        bs.timer(0.5, light.delete)
        bs.animate(light, 'intensity', {0: 0, 0.1: 1.0 * scale, 0.5: 0})

    def handlemessage(self, msg: Any) -> Any:

        if isinstance(msg, bs.PlayerDiedMessage):

            # Augment standard behavior.
            super().handlemessage(msg)

            death_time = bs.time()
            msg.getplayer(Player).death_time = death_time

            if isinstance(self.session, bs.CoopSession):
                # Teams will still show up if we check now.. check in
                # the next cycle.
                babase.pushcall(self._check_end_game)

                # Also record this for a final setting of the clock.
                self._last_player_death_time = death_time
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

    def spawn_player(self, player: PlayerType) -> bs.Actor:
        spaz = self.spawn_player_spaz(player)

        # Let's reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up.
        spaz.connect_controls_to_player(enable_punch=False,
                                        enable_bomb=self._enable_bombs,
                                        enable_pickup=False)

        # Also lets have them make some noise when they die.
        spaz.play_big_death_sound = True
        return spaz

    def spawn_player_spaz(self,
                          player: PlayerType,
                          position: Sequence[float] = (0, 0, 0),
                          angle: float = None) -> PlayerSpaz:
        """Create and wire up a bs.PlayerSpaz for the provided bs.Player."""
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        position = self.map.get_ffa_start_position(self.players)
        name = player.getname()
        color = player.color
        highlight = player.highlight

        light_color = babase._math.normalized_color(color)
        display_color = _babase.safecolor(color, target_intensity=0.75)
        spaz = PlayerSpaz(color=color,
                          highlight=highlight,
                          character=player.character,
                          player=player)

        player.actor = spaz
        assert spaz.node

        # If this is co-op and we're on Courtyard or Runaround, add the
        # material that allows us to collide with the player-walls.
        # FIXME: Need to generalize this.
        if isinstance(self.session, bs.CoopSession) and self.map.getname() in [
                'Courtyard', 'Tower D'
        ]:
            mat = self.map.preloaddata['collide_with_wall_material']
            assert isinstance(spaz.node.materials, tuple)
            assert isinstance(spaz.node.roller_materials, tuple)
            spaz.node.materials += (mat, )
            spaz.node.roller_materials += (mat, )

        spaz.node.name = name
        spaz.node.name_color = display_color
        spaz.connect_controls_to_player()

        # Move to the stand position and add a flash of light.
        spaz.handlemessage(
            bs.StandMessage(
                position,
                angle if angle is not None else random.uniform(0, 360)))
        self._spawn_sound.play(1, position=spaz.node.position)
        light = bs.newnode('light', attrs={'color': light_color})
        spaz.node.connectattr('position', light, 'position')
        bs.animate(light, 'intensity', {0: 0, 0.25: 1, 0.5: 0})
        bs.timer(0.5, light.delete)
        return spaz

    def getRandomPowerupPoint(self) -> None:
        # So far, randomized points only figured out for mostly rectangular maps.
        # Boxes will still fall through holes, but shouldn't be terrible problem (hopefully)
        # If you add stuff here, need to add to "supported maps" above.
        # ['Doom Shroom', 'Rampage', 'Hockey Stadium', 'Courtyard', 'Crag Castle', 'Big G', 'Football Stadium']
        myMap = self.map.getname()
        # print(myMap)
        if myMap == 'Doom Shroom':
            while True:
                x = random.uniform(-1.0, 1.0)
                y = random.uniform(-1.0, 1.0)
                if x*x+y*y < 1.0:
                    break
            return ((8.0*x, 2.5, -3.5+5.0*y))
        elif myMap == 'Rampage':
            x = random.uniform(-6.0, 7.0)
            y = random.uniform(-6.0, -2.5)
            return ((x, 5.2, y))
        elif myMap == 'Hockey Stadium':
            x = random.uniform(-11.5, 11.5)
            y = random.uniform(-4.5, 4.5)
            return ((x, 0.2, y))
        elif myMap == 'Courtyard':
            x = random.uniform(-4.3, 4.3)
            y = random.uniform(-4.4, 0.3)
            return ((x, 3.0, y))
        elif myMap == 'Crag Castle':
            x = random.uniform(-6.7, 8.0)
            y = random.uniform(-6.0, 0.0)
            return ((x, 10.0, y))
        elif myMap == 'Big G':
            x = random.uniform(-8.7, 8.0)
            y = random.uniform(-7.5, 6.5)
            return ((x, 3.5, y))
        elif myMap == 'Football Stadium':
            x = random.uniform(-12.5, 12.5)
            y = random.uniform(-5.0, 5.5)
            return ((x, 0.32, y))
        else:
            x = random.uniform(-5.0, 5.0)
            y = random.uniform(-6.0, 0.0)
            return ((x, 8.0, y))

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
                longest_life = max(longest_life,
                                   player.death_time - start_time)

            # Submit the score value in milliseconds.
            results.set_team_score(team, int(1000.0 * longest_life))

        self.end(results=results)
