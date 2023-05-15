# ba_meta require api 7
from typing import Sequence
import ba
import _ba
import random
from bastd.actor.spaz import Spaz
from bastd.actor.scoreboard import Scoreboard


class Player(ba.Player['Team']):
    """Our player type for this game."""


class Team(ba.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        super().__init__()
        self.score = 1


class ChooseingSpazHitMessage:
    def __init__(self, hitter: Player) -> None:
        self.hitter = hitter


class ChooseingSpazDieMessage:
    def __init__(self, killer: Player) -> None:
        self.killer = killer


class ChooseingSpaz(Spaz):
    def __init__(
            self,
            pos: Sequence[float],
            color: Sequence[float] = (1.0, 1.0, 1.0),
            highlight: Sequence[float] = (0.5, 0.5, 0.5),
    ):
        super().__init__(color, highlight, "Spaz", None, True, True, False, False)
        self.last_player_attacked_by = None
        self.stand(pos)
        self.loc = ba.newnode(
            'locator',
            attrs={
                'shape': 'circleOutline',
                'position': pos,
                'color': color,
                'opacity': 1,
                'draw_beauty': False,
                'additive': True,
            },
        )
        self.node.connectattr("position", self.loc, "position")
        ba.animate_array(self.loc, "size", 1, keys={0: [0.5,], 1: [2,], 1.5: [0.5]}, loop=True)

    def handlemessage(self, msg):
        if isinstance(msg, ba.FreezeMessage):
            return

        if isinstance(msg, ba.PowerupMessage):
            if not (msg.poweruptype == "health"):
                return

        super().handlemessage(msg)

        if isinstance(msg, ba.HitMessage):
            self.handlemessage(ba.PowerupMessage("health"))

            player = msg.get_source_player(Player)
            if self.is_alive():
                self.activity.handlemessage(ChooseingSpazHitMessage(player))
            self.last_player_attacked_by = player

        elif isinstance(msg, ba.DieMessage):
            player = self.last_player_attacked_by

            if msg.how.value != ba.DeathType.GENERIC.value:
                self._dead = True
                self.activity.handlemessage(ChooseingSpazDieMessage(player))

            self.loc.delete()

    def stand(self, pos=(0, 0, 0), angle=0):
        self.handlemessage(ba.StandMessage(pos, angle))

    def recolor(self, color, highlight=(1, 1, 1)):
        self.node.color = color
        self.node.highlight = highlight
        self.loc.color = color


class ChooseBilbord(ba.Actor):
    def __init__(self, player: Player, delay=0.1) -> None:
        super().__init__()

        icon = player.get_icon()
        self.scale = 100

        self.node = ba.newnode(
            'image',
            delegate=self,
            attrs={
                "position": (60, -125),
                'texture': icon['texture'],
                'tint_texture': icon['tint_texture'],
                'tint_color': icon['tint_color'],
                'tint2_color': icon['tint2_color'],
                'opacity': 1.0,
                'absolute_scale': True,
                'attach': "topLeft"
            },
        )

        self.name_node = ba.newnode(
            'text',
            owner=self.node,
            attrs={
                'position': (60, -185),
                'text': ba.Lstr(value=player.getname()),
                'color': ba.safecolor(player.team.color),
                'h_align': 'center',
                'v_align': 'center',
                'vr_depth': 410,
                'flatness': 1.0,
                'h_attach': 'left',
                'v_attach': 'top',
                'maxwidth': self.scale
            },
        )

        ba.animate_array(self.node, "scale", keys={
                         0 + delay: [0, 0], 0.05 + delay: [self.scale, self.scale]}, size=1)
        ba.animate(self.name_node, "scale", {0 + delay: 0, 0.07 + delay: 1})

    def handlemessage(self, msg):
        super().handlemessage(msg)
        if isinstance(msg, ba.DieMessage):
            ba.animate_array(self.node, "scale", keys={0: self.node.scale, 0.05: [0, 0]}, size=1)
            ba.animate(self.name_node, "scale", {0: self.name_node.scale, 0.07: 0})

            def __delete():
                self.node.delete()
                self.name_node.delete()

            ba.timer(0.2, __delete)

# ba_meta export game


class LastPunchStand(ba.TeamGameActivity[Player, Team]):
    name = "Last Punch Stand"
    description = "Last one punchs the choosing spaz wins"
    tips = [
        'keep punching the choosing spaz to be last punched player at times up!',
        'you can not frezz the choosing spaz',
        "evry time you punch the choosing spaz, you will get one point",
    ]

    default_music = ba.MusicType.TO_THE_DEATH

    available_settings = [
        ba.FloatSetting("min time limit (in seconds)", 50.0, min_value=30.0),
        ba.FloatSetting("max time limit (in seconds)", 160.0, 60),

    ]

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._min_timelimit = settings["min time limit (in seconds)"]
        self._max_timelimit = settings["max time limit (in seconds)"]
        if (self._min_timelimit > self._max_timelimit):
            self._max_timelimit = self._min_timelimit

        self._choosing_spaz_defcolor = (0.5, 0.5, 0.5)
        self.choosing_spaz = None
        self.choosed_player = None
        self.times_uped = False
        self.scoreboard = Scoreboard()

    def times_up(self):
        self.times_uped = True

        for player in self.players:
            if self.choosed_player and (player.team.id != self.choosed_player.team.id):
                player.actor._cursed = True
                player.actor.curse_explode()

        self.end_game()

    def __get_spaz_bot_spawn_point(self):
        if len(self.map.tnt_points) > 0:
            return self.map.tnt_points[random.randint(0, len(self.map.tnt_points)-1)]
        else:
            return (0, 6, 0)

    def spaw_bot(self):
        "spawns a choosing bot"

        self.choosing_spaz = ChooseingSpaz(self.__get_spaz_bot_spawn_point())
        self.choose_bilbord = None

    def on_begin(self) -> None:
        super().on_begin()
        time_limit = random.randint(self._min_timelimit, self._max_timelimit)
        self.spaw_bot()
        ba.timer(time_limit, self.times_up)

        self.setup_standard_powerup_drops(False)

    def end_game(self) -> None:
        results = ba.GameResults()
        for team in self.teams:
            if self.choosed_player and (team.id == self.choosed_player.team.id):
                team.score += 100
            results.set_team_score(team, team.score)
        self.end(results=results)

    def change_choosed_player(self, hitter: Player):
        if hitter:
            self.choosing_spaz.recolor(hitter.color, hitter.highlight)
            self.choosed_player = hitter
            hitter.team.score += 1
            self.choose_bilbord = ChooseBilbord(hitter)
            self.hide_score_board()
        else:
            self.choosing_spaz.recolor(self._choosing_spaz_defcolor)
            self.choosed_player = None
            self.choose_bilbord = None
            self.show_score_board()

    def show_score_board(self):
        self.scoreboard = Scoreboard()
        for team in self.teams:
            self.scoreboard.set_team_value(team, team.score)

    def hide_score_board(self):
        self.scoreboard = None

    def _watch_dog_(self):
        "checks if choosing spaz exists"
        # choosing spaz wont respawn if death type if generic
        # this becuse we dont want to keep respawn him when he dies because of losing referce
        # but sometimes "choosing spaz" dies naturaly and his death type is generic! so it wont respawn back again
        # thats why we have this function; to check if spaz exits in the case that he didnt respawned

        if self.choosing_spaz:
            if self.choosing_spaz._dead:
                self.spaw_bot()
        else:
            self.spaw_bot()

    def handlemessage(self, msg):
        super().handlemessage(msg)

        if isinstance(msg, ChooseingSpazHitMessage):
            hitter = msg.hitter
            if self.choosing_spaz.node and hitter:
                self.change_choosed_player(hitter)

        elif isinstance(msg, ChooseingSpazDieMessage):
            self.spaw_bot()
            self.change_choosed_player(None)

        elif isinstance(msg, ba.PlayerDiedMessage):
            player = msg.getplayer(Player)
            if not (self.has_ended() or self.times_uped):
                self.respawn_player(player, 0)

            if self.choosed_player and (player.getname(True) == self.choosed_player.getname(True)):
                self.change_choosed_player(None)

        self._watch_dog_()
