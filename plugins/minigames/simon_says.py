# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# SimonSays
# you had really better do what Simon says...
# ba_meta require api 8
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Union, Sequence

from bascenev1 import _gameutils
import babase
import bauiv1 as bui
import bascenev1 as bs
import random


class CustomText(bs.Actor):
    """Text that pops up above a position to denote something special.

    category: Gameplay Classes
    """

    def __init__(self,
                 text: Union[str, babase.Lstr],
                 position: Sequence[float] = (0.0, 0.0, 0.0),
                 color: Sequence[float] = (1.0, 1.0, 1.0, 1.0),
                 random_offset: float = 0.5,
                 duration: float = 1.5,
                 offset: Sequence[float] = (0.0, 0.0, 0.0),
                 scale: float = 1.0):
        super().__init__()
        if len(color) == 3:
            color = (color[0], color[1], color[2], 1.0)
        pos = (position[0] + offset[0] + random_offset *
               (0.5 - random.random()), position[1] + offset[0] +
               random_offset * (0.5 - random.random()), position[2] +
               offset[0] + random_offset * (0.5 - random.random()))
        self.node = bs.newnode('text',
                               attrs={
                                   'text': text,
                                   'in_world': True,
                                   'shadow': 1.0,
                                   'flatness': 1.0,
                                   'h_align': 'center'}, delegate=self)
        lifespan = duration
        bs.animate(
            self.node, 'scale', {
                0: 0.0,
                lifespan * 0.11: 0.020 * 0.7 * scale,
                lifespan * 0.16: 0.013 * 0.7 * scale,
                lifespan * 0.25: 0.014 * 0.7 * scale
            })
        self._tcombine = bs.newnode('combine',
                                    owner=self.node,
                                    attrs={
                                        'input0': pos[0],
                                        'input2': pos[2],
                                        'size': 3
                                    })
        bs.animate(self._tcombine, 'input1', {
            0: pos[1] + 1.5,
            lifespan: pos[1] + 2.0
        })
        self._tcombine.connectattr('output', self.node, 'position')
        # fade our opacity in/out
        self._combine = bs.newnode('combine',
                                   owner=self.node,
                                   attrs={
                                       'input0': color[0],
                                       'input1': color[1],
                                       'input2': color[2],
                                       'size': 4
                                   })
        for i in range(4):
            bs.animate(
                self._combine, 'input' + str(i), {
                    0.13 * lifespan: color[i],
                    0.18 * lifespan: 4.0 * color[i],
                    0.22 * lifespan: color[i]})
        bs.animate(self._combine, 'input3', {
            0: 0,
            0.1 * lifespan: color[3],
            0.7 * lifespan: color[3],
            lifespan: 0})
        self._combine.connectattr('output', self.node, 'color')
        self._die_timer = bs.Timer(
            lifespan, bs.WeakCall(self.handlemessage, bs.DieMessage()))

    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        else:
            super().handlemessage(msg)


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.score = 0
        self.dead: bool = False


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0

# ba_meta export bascenev1.GameActivity


class SimonSays(bs.TeamGameActivity[Player, Team]):
    name = "Simon Says"
    description = "You have to better do what Simon says!"

    @classmethod
    def get_available_settings(cls, sessiontype: Type[bs.Session]) -> List[babase.Setting]:
        settings = [
            bs.BoolSetting("Epic Mode", default=False),
            bs.BoolSetting("Enable Jumping", default=False),
            bs.BoolSetting("Enable Punching", default=False),
            bs.BoolSetting("Enable Picking Up", default=False),
            bs.IntChoiceSetting("Timer Speed",
                                choices=[("Snaily", 1200),
                                         ("Slow", 900),
                                         ("Normal", 655),
                                         ("Fast", 544),
                                         ("Turbo", 460)], default=655),

            bs.FloatChoiceSetting("Text Duration",
                                  choices=[("Slow", 2.5),
                                           ("Normal", 1.5),
                                           ("Mediocre", 1.0),
                                           ("Quick", 0.75)], default=1.5)]
        return settings

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return ["Courtyard"]

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.FreeForAllSession)

    def __init__(self, settings: dict):
        super().__init__(settings)
        self.settings = settings
        self._is_slow_motion = bool(settings['Epic Mode'])
        self.speed = float(settings['Timer Speed'])
        self.lifespan = float(settings['Text Duration'])
        self.round_num = 0
        self.string = ""
        self.now = 0
        self.simon = False
        self.ended = False
        self.counter_loop = None
        self.time = 5000
        self._r1 = 2
        self.ct_text = bs.newnode('text', attrs={
            'in_world': True,
            'text': '......',
            'shadow': 1.0,
            'color': (1.0, 1.0, 1.0),
            'flatness': 0.5,
            'position': (-5.627144702, 3.3275475, -9.572879116),
            'scale': 0.05})
        self.n1 = bs.newnode('locator', attrs={'shape': 'circle', 'position': (-4, 0, -6),
                                               'color': (1, 0, 0), 'opacity': 0.5,
                                               'draw_beauty': True, 'additive': True})
        self.n2 = bs.newnode('locator', attrs={'shape': 'circle', 'position': (0, 0, -6),
                                               'color': (0, 1, 0), 'opacity': 0.5,
                                               'draw_beauty': True, 'additive': True})
        self.n3 = bs.newnode('locator', attrs={'shape': 'circle', 'position': (4, 0, -6),
                                               'color': (0, 0, 1), 'opacity': 0.5,
                                               'draw_beauty': True, 'additive': True})
        self.n4 = bs.newnode('locator', attrs={'shape': 'circle', 'position': (-4, 0, -2),
                                               'color': (1, 1, 0), 'opacity': 0.5,
                                               'draw_beauty': True, 'additive': True})
        self.n5 = bs.newnode('locator', attrs={'shape': 'circle', 'position': (0, 0, -2),
                                               'color': (0, 1, 1), 'opacity': 0.5,
                                               'draw_beauty': True, 'additive': True})
        self.n6 = bs.newnode('locator', attrs={'shape': 'circle', 'position': (4, 0, -2),
                                               'color': (1, 0, 1), 'opacity': 0.5,
                                               'draw_beauty': True, 'additive': True})
        self.n7 = bs.newnode('locator', attrs={'shape': 'circle', 'position': (-4, 0, 2),
                                               'color': (.5, .5, .5), 'opacity': 0.5,
                                               'draw_beauty': True, 'additive': True})
        self.n8 = bs.newnode('locator', attrs={'shape': 'circle', 'position': (0, 0, 2),
                                               'color': (.5, .325, 0), 'opacity': 0.5,
                                               'draw_beauty': True, 'additive': True})
        self.n9 = bs.newnode('locator', attrs={'shape': 'circle', 'position': (4, 0, 2),
                                               'color': (1, 1, 1), 'opacity': 0.5,
                                               'draw_beauty': True, 'additive': True})
        self.options = ["red", "green", "blue", "yellow", "teal", "purple", "gray", "orange",
                        "white", "top", "bottom", "middle row", "left", "right", "center column", "outside"]
        self.default_music = bs.MusicType.FLAG_CATCHER

    def get_instance_description(self) -> str:
        return 'Follow the commands... but only when \"Simon says!"'

    def on_player_join(self, player: Player) -> None:
        if self.has_begun():
            bs.broadcastmessage(
                babase.Lstr(resource='playerDelayedJoinText',
                            subs=[('${PLAYER}', player.getname(full=True))]),
                color=(0, 1, 0),)
            return
        else:
            self.spawn_player(player)

    def on_begin(self) -> None:
        super().on_begin()
        s = self.settings
        _gameutils.animate_array(self.n1, 'size', 1, {0: [0.0], 0.2: [self._r1*2.0]})
        _gameutils.animate_array(self.n2, 'size', 1, {0: [0.0], 0.2: [self._r1*2.0]})
        _gameutils.animate_array(self.n3, 'size', 1, {0: [0.0], 0.2: [self._r1*2.0]})
        _gameutils.animate_array(self.n4, 'size', 1, {0: [0.0], 0.2: [self._r1*2.0]})
        _gameutils.animate_array(self.n5, 'size', 1, {0: [0.0], 0.2: [self._r1*2.0]})
        _gameutils.animate_array(self.n6, 'size', 1, {0: [0.0], 0.2: [self._r1*2.0]})
        _gameutils.animate_array(self.n7, 'size', 1, {0: [0.0], 0.2: [self._r1*2.0]})
        _gameutils.animate_array(self.n8, 'size', 1, {0: [0.0], 0.2: [self._r1*2.0]})
        _gameutils.animate_array(self.n9, 'size', 1, {0: [0.0], 0.2: [self._r1*2.0]})
        for team in self.teams:
            team.score = 0
        for player in self.players:
            player.score = 0
        # check for immediate end if theres only 1 player
        if len(self.players) == 1:
            bs.timer(4000/1000, bs.Call(self.check_end))
        bs.timer(6000/1000, self.call_round)

    def spawn_player(self, player: PlayerT) -> bs.Actor:
        assert player
        spaz = self.spawn_player_spaz(player, position=(
            0 + random.uniform(-3.6, 3.6), 2.9, -2 + random.uniform(-3.6, 3.6)))
        assert spaz.node
        spaz.connect_controls_to_player(
            enable_bomb=False,
            enable_run=True,
            enable_punch=self.settings["Enable Punching"],
            enable_pickup=self.settings["Enable Picking Up"],
            enable_jump=self.settings["Enable Jumping"])

    def call_round(self) -> None:
        if self.ended:
            return
        self.round_num += 1
        self.num = random.randint(0, 15)
        self.numa = self.num
        self.simon = random.choice([True, False])
        false_prefix = random.choices(['Simon say r', 'Simon said r', 'Simon r',
                                      'Simons says r', 'Simons r', 'R'], weights=[35, 45, 45, 39, 49, 100])[0]
        if self.numa < 9:
            if not self.simon:
                line = false_prefix + "un to the " + self.options[self.numa] + " circle!"
            else:
                line = "Run to the " + self.options[self.numa] + " circle!"

        elif self.numa < 15:
            if not self.simon:
                line = false_prefix + "un to the " + self.options[self.numa] + "!"
            else:
                line = "Run to the " + self.options[self.numa] + "!"

        else:
            if not self.simon:
                line = false_prefix + "un outside of the circles!"
            else:
                line = "Run outside of the circles!"

        if self.simon:
            line = "Simon says " + line[0].lower() + line[1:]
        self.text = CustomText(line,
                               position=(0, 5, -4),
                               color=(0.68, 0.95, 1.12),
                               random_offset=0.5,
                               offset=(0, 0, 0),
                               duration=self.lifespan,
                               scale=2.0).autoretain()
        self.now = 6

        def dummy_check():
            self.string = "...."
            self.check_round()

        def set_counter():
            self.now = self.now - 1
            if self.now == 0:
                self.string = "0"
                self.ct_text.text = self.string
                self.counter_loop = None
                bs.timer(1/1000, dummy_check)
            else:
                self.ct_text.text = str(self.now)
            bs.getsound('tick').play()
        self.counter_loop = bs.Timer(self.speed/1000, set_counter, repeat=True)

    def check_round(self) -> None:
        if self.ended:
            return
        for player in self.players:
            if player.is_alive():
                safe = True if self.options[self.numa] in self.in_circle(
                    player.actor.node.position_center) else False
                if ((self.simon and safe == False) or ((not self.simon) and safe == True)):
                    player.team.score = self.round_num
                    player.actor.handlemessage(bs.DieMessage())
        bs.timer(1633/1000, self.call_round)

    def in_circle(self, pos) -> None:
        circles = []
        x = pos[0]
        z = pos[2]
        if (x + 4) ** 2 + (z + 6) ** 2 < 4:
            circles.append("red")
        elif (x) ** 2 + (z + 6) ** 2 < 4:
            circles.append("green")
        elif (x - 4) ** 2 + (z + 6) ** 2 < 4:
            circles.append("blue")
        elif (x + 4) ** 2 + (z + 2) ** 2 < 4:
            circles.append("yellow")
        elif (x) ** 2 + (z + 2) ** 2 < 4:
            circles.append("teal")
        elif (x - 4) ** 2 + (z + 2) ** 2 < 4:
            circles.append("purple")
        elif (x + 4) ** 2 + (z - 2) ** 2 < 4:
            circles.append("gray")
        elif (x) ** 2 + (z - 2) ** 2 < 4:
            circles.append("orange")
        elif (x - 4) ** 2 + (z - 2) ** 2 < 4:
            circles.append("white")
        else:
            circles.append("outside")
        if x < -2:
            circles.append("left")
        if x > 2:
            circles.append("right")
        if x > -2 and x < 2:
            circles.append("center column")
        if z > 0:
            circles.append("bottom")
        if z < -4:
            circles.append("top")
        if z < 0 and z > -4:
            circles.append("middle row")
        return circles

    def handlemessage(self, msg) -> None:
        if isinstance(msg, bs.PlayerDiedMessage):
            msg.getplayer(Player).dead = True
            self.check_end()
        else:
            super().handlemessage(msg)

    def end_game(self) -> None:
        self.ended = True
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)

    def check_end(self):
        i = 0
        for player in self.players:
            if player.is_alive() and not player.dead:
                i += 1
        if isinstance(self.session, bs.CoopSession):
            if i <= 0:
                bs.timer(0.6, bs.Call(self.end_game))
        else:
            if i <= 2:
                bs.timer(0.6, bs.Call(self.end_game))


# ba_meta export plugin
class plugin(babase.Plugin):
    def __init__(self):
        ## Campaign support ##
        babase.app.classic.add_coop_practice_level(bs.Level(
            name='Simon Says',
            gametype=SimonSays,
            settings={},
            preview_texture_name='courtyardPreview'))
