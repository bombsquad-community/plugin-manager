# VolleyPunch ? ig i'll name it like that

# Made by Learn.py
# but this was def inspired by some freaky guy


# ba_meta require api 9

from __future__ import annotations

from typing import TYPE_CHECKING

import babase, _babase
import math, random
import bascenev1 as bs
import bauiv1 as bui
import math
import time
import babase
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.powerupbox import PowerupBoxFactory
from bascenev1lib.actor.bomb import BombFactory
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence, Dict, Type, List, Optional, Union


plugman = dict(
    plugin_name="VolleyPunch",
    description="Have fun with your friends in this new volley game !",
    external_url="https://github.com/Scriptz1/Learn.py-Installer/blob/main/volleypunch.py",
    authors=[
        {"name": "Learn.py", "email": "phillipians36@gmail.com", "discord": "Learning .py"},
    ],
    version="1.0.0",
)

class PuckDiedMessage:
    """Inform something that a puck has died."""

    def __init__(self, puck: Puck):
        self.puck = puck


class Puck(bs.Actor):
    def __init__(self, position: Sequence[float] = (0.0, 1.0, 0.0)):
        super().__init__()
        shared = SharedObjects.get()
        activity = self.getactivity()

        # Spawn just above the provided point.
        self._spawn_pos = (position[0], position[1] + 1.05, position[2])
        self.last_players_to_touch: Dict[int, Player] = {}
        self.scored = False

        self.touches = 0
        assert activity is not None
        assert isinstance(activity, VolleyBallGame)
        pmats = [shared.object_material, activity.puck_material]

        # so this is the volleyball we gonna mesh with today
        self.node = bs.newnode('prop',
                               delegate=self,
                               attrs={
                                   'mesh': activity.puck_mesh,
                                   'color_texture': activity.puck_tex,
                                   'body': 'sphere',
                                   'reflection': 'soft',
                                   'reflection_scale': [0.2],
                                   'shadow_size': 0.3,
                                   'mesh_scale': activity.ball_size,
                                   'body_scale': 1.07,
                                   'gravity_scale': 1,
                                   'is_area_of_interest': True,
                                   'position': self._spawn_pos,
                                   'materials': pmats
                               })




    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            assert self.node
            self.node.delete()
            activity = self._activity()
            if activity and not msg.immediate:
                activity.handlemessage(PuckDiedMessage(self))

        # If we go out of bounds, move back to where we started.
        # copied that stuff from hockey game ngl
        elif isinstance(msg, bs.OutOfBoundsMessage):
            assert self.node
            self.node.position = self._spawn_pos

        elif isinstance(msg, bs.HitMessage):
            assert self.node
            assert msg.force_direction is not None
            self.node.handlemessage(
                'impulse', msg.pos[0], msg.pos[1], msg.pos[2], msg.velocity[0],
                msg.velocity[1], msg.velocity[2], 1.0 * msg.magnitude,
                1.0 * msg.velocity_magnitude, msg.radius, 0,
                msg.force_direction[0], msg.force_direction[1],
                msg.force_direction[2])

            # If this hit came from a player, log them as the last to touch us.
            s_player = msg.get_source_player(Player)
            if s_player is not None:
                activity = self._activity()
                if activity:
                    if s_player in activity.players:
                        self.last_players_to_touch[s_player.team.id] = s_player
        else:
            super().handlemessage(msg)


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export bascenev1.GameActivity
class VolleyBallGame(bs.TeamGameActivity[Player, Team]):
    name = 'VolleyPunch'
    description = 'Punch the Volleyball !'
    available_settings = [
        bs.IntSetting(
            'Score to Win',
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
            default=1.0,
        ),
        bs.FloatSetting(
            'Ball size (m)',
            min_value=0.15,
            default=0.25,
            max_value=0.35,
            increment=0.05,
        ),
        bs.FloatChoiceSetting(
            'Ball Average Speed',
            choices=[
                ('Slower', 0.9899),
                ('Normal', 1.0),
            ],
            default=1.0,
        ),
        bs.BoolSetting('Epic Mode', False),
        bs.BoolSetting('Enable Credits', True),
    ]
    default_music = bs.MusicType.HOCKEY

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return ['Football Stadium']

    def __init__(self, settings: dict):
        super().__init__(settings)
        shared = SharedObjects.get()
        self._scoreboard = Scoreboard()
        self._cheer_sound = bs.getsound('cheer')
        self._chant_sound = bs.getsound('crowdChant')
        self.one_sound = bs.getsound('announceOne')
        self.two_sound = bs.getsound('announceTwo')
        self.three_sound = bs.getsound('announceThree') # unused.. yet
        self._swipsound = bs.getsound('swip')
        self._whistle_sound = bs.getsound('refWhistle')
        self.puck_mesh = bs.getmesh('shield')
        self.puck_tex = bs.gettexture('ouyaUButton')
        self._puck_sound = bs.getsound('metalHit')
        self.puck_material = bs.Material()
        self.puck_material.add_actions(actions=(('modify_part_collision',
                                                 'friction', 4)))
        self.puck_material.add_actions(conditions=('they_have_material',
                                                   shared.pickup_material),
                                       actions=('modify_part_collision',
                                                'collide', True))
        self.puck_material.add_actions(
            conditions=(
                ('we_are_younger_than', 100),
                'and',
                ('they_have_material', shared.object_material),
            ),
            actions=('modify_node_collision', 'collide', False),
        )
        self.puck_material.add_actions(conditions=('they_have_material',
                                                   shared.footing_material),
                                       actions=('impact_sound',
                                                self._puck_sound, 0.2, 5))

        # Keep track of which player last touched the puck
        self.puck_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(('call', 'at_connect',
                      self._handle_puck_player_collide),
                     ('modify_part_collision', 'physical', False)))

        # We want the puck to kill powerups; not get stopped by them
        self.puck_material.add_actions(
            conditions=('they_have_material',
                        PowerupBoxFactory.get().powerup_material),
            actions=(('modify_part_collision', 'physical', False),
                     ('message', 'their_node', 'at_connect', bs.DieMessage())))
        self._score_region_material = bs.Material()
        self._score_region_material.add_actions(
            conditions=('they_have_material', self.puck_material),
            actions=(('modify_part_collision', 'collide',
                      True), ('modify_part_collision', 'physical', False),
                     ('call', 'at_connect', self._handle_score)))

        self._fake_wall_material = bs.Material() #i'll fix this. trust

        self._net_wall_material = bs.Material()
        self._net_material = bs.Material()
        self._net_wall_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True)

            ))
        self._net_material.add_actions(
            conditions=('they_have_material', shared.object_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
                ('modify_part_collision',
                 'friction', -10),
                ('call', 'at_connect', self.slow_down)))




        self._puck_spawn_pos: Optional[Sequence[float]] = None
        self._score_regions: Optional[List[bs.NodeActor]] = None
        self._puck: Optional[Puck] = None
        self._score_to_win = int(settings['Score to Win'])
        self._time_limit = float(settings['Time Limit'])
        self.credit_text = bool(settings['Enable Credits']) # i did the freaku credit thing
        self._epic_mode = bool(settings['Epic Mode'])


        # the ball is too fast for the players and the map is soo huge its a good poc - brostos
        self.ball_size = float(settings['Ball size (m)'])
        self.ball_speed = float(settings['Ball Average Speed'])


        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (bs.MusicType.EPIC if self._epic_mode else
                              bs.MusicType.TO_THE_DEATH)
        self.s : list = []
        self.w : list = []
        self.n : list = []
        self.last_interaction_time = -9999
        self.smashed = -9999
        self.interactions_timer = None
        self.curve = True
        self.difficulty = 0.5
        self.smasher = None
        self.commentary_text = None
        self._text_task = None  # Référence pour annuler l'animation en cours
        self._clear_timer = None  # Référence pour le timer de disparition
        self.touches_indicator = None
        self.guide = None
        self.curving = False

    def get_instance_description(self) -> Union[str, Sequence]:
        if self._score_to_win == 1:
            return 'Score a goal.'
        return 'Score ${ARG1} goals.', self._score_to_win

    def get_instance_description_short(self) -> Union[str, Sequence]:
        if self._score_to_win == 1:
            return 'score a goal'
        return 'score ${ARG1} goals', self._score_to_win

    def on_begin(self) -> None:
        super().on_begin()

        self.setup_standard_time_limit(self._time_limit)
        self._puck_spawn_pos = (-4, 1 ,0) if random.random() < 0.5 else (4, 1, 0)
        self._spawn_puck()

        # Set up the two score regions.
        self._score_regions = []
        self.commentary_text = bs.newnode(
                'text',
                attrs=dict(
                    text='',
                    scale=0.012,
                    position=(0, 3.1, -5.8),
                    in_world=True,
                    flatness=1,
                    shadow=0,
                    color=(1,1,1,0.5),
                    h_align= 'center',
                    v_align= 'top',
                    h_attach= 'center',
                    v_attach= 'top',
                ))
        self.touches_indicator = bs.newnode(
                'text',
                attrs=dict(
                    text='',
                    scale=0.025,
                    position=(0, 3, -5.8),
                    in_world=True,
                    flatness=1,
                    shadow=0,
                    color=(1,1,1,0.5),
                    h_align= 'center',
                    v_align= 'top',
                    h_attach= 'center',
                    v_attach= 'top',
                ))
        self.guide = bs.newnode(
                'text',
                attrs=dict(
                    text='PUNCH TO TAP THE BALL \nPICKUP TO CUFF \nBOMB TO GLIDE / DIVE \nJUMP UNDER A MID AIR BALL WITH THE BAR FILLED TO SMASH \nTHE ULT BAR FILLS AS YOU PLAY',
                    scale=0.005,
                    position=(0, 2.7, -5.8),
                    in_world=True,
                    flatness=1,
                    shadow=0,
                    color=(1,1,1,0.5),
                    h_align= 'center',
                    v_align= 'top',
                    h_attach= 'center',
                    v_attach= 'top',
                ))
        bs.animate_array(self.guide, 'color',4, {0: (1,1,1,0.5), 1: (1,1,1,1), 2: (1,1,1,0.5)}, loop=True)
        self.interactions_timer = bs.Timer(1 / 120, self.interactions, repeat=True)  # time, function, repeat
        self._score_regions.append(
            bs.NodeActor(
                bs.newnode('region',
                           attrs={
                               'position': (9, 0, 0),
                               'scale': (17.3, 0.002, 12),
                               'type': 'box',
                               'materials': [self._score_region_material]
                           })))
        self._score_regions.append(
            bs.NodeActor(
                bs.newnode('region',
                           attrs={
                               'position': (-9, 0, 0),
                               'scale': (17.3, 0.002, 20),
                               'type': 'box',
                               'materials': [self._score_region_material]
                           })))
        self._update_scoreboard()
        self._chant_sound.play()
        if self.credit_text:
            t = bs.newnode('text',
                           attrs={'text': "Created by Learn.py",
                                  'scale': 0.7,
                                  'position': (0, 0),
                                  'shadow': 0.5,
                                  'flatness': 1.2,
                                  'color': (1, 1, 1),
                                  'h_align': 'center',
                                  'v_attach': 'bottom'})

        #Create the net and regions.
        mat = bs.Material() # spam this whenever u want a material THEN add some properties
        mat.add_actions(actions=('modify_part_collision',
                             'collide', False))
        net = bs.newnode(
            'prop',
            attrs={
                'body': 'puck',
                'body_scale': 0,
                'position': (0,0,0),
                'mesh_scale': 1,
                'mesh': bs.getmesh('volleyball_net'),
                'color_texture': bs.gettexture('black'),
                'reflection': 'soft',
                'reflection_scale': [1.5],
                'sticky': False,
                'shadow_size': 0.2,
                'gravity_scale': 0,
                'materials': [mat],
            },
        )


        self.s.append(bs.NodeActor(bs.newnode('region', attrs={'position': (0, 2.4, 0), 'scale': (
            0.8, 6, 20), 'type': 'box', 'materials': (self._fake_wall_material, )})))

        self.w.append(bs.NodeActor(bs.newnode('region', attrs={'position': (0, 0, 0), 'scale': (
            0.6, 10, 20), 'type': 'box', 'materials': (self._net_wall_material, )})))
        self.n.append(bs.NodeActor(bs.newnode('region', attrs={'position': (0, 0, 0), 'scale': (
            0.6, 2.75, 20), 'type': 'box', 'materials': (self._net_material, )})))
        self.n.append(bs.NodeActor(bs.newnode('region', attrs={'position': (0, 0, -5.9), 'scale': (
            20, 20, 0.8), 'type': 'box', 'materials': (self._net_wall_material, self._net_material )})))
        self.n.append(bs.NodeActor(bs.newnode('region', attrs={'position': (0, 0, 5.9), 'scale': (
            20, 20, 0.8), 'type': 'box', 'materials': (self._net_wall_material, self._net_material )})))

    def slow_down(self):
        if not self._puck:
            return
        puck_node = self._puck.node
        mult = 0.88
        v = puck_node.velocity
        puck_node.velocity = (v[0] * mult, v[1] * mult, v[2] * mult)

    def write(self, text, color):
        """types"""
        if hasattr(self, '_timers'):
            for t in self._timers:
                t = None
        self._timers = []

        if not text:
            return

        self.commentary_text.color = color
        total_chars = len(text)

        interval = 0.9 / max(total_chars, 1)

        for i in range(1, total_chars + 1):
            def show(index=i):
                if self.commentary_text.exists():
                    self.commentary_text.text = text[:index]

            self._timers.append(bs.Timer(interval * i, show, repeat=False))

        def start_clear():
            for i in range(total_chars, -1, -1):
                def hide(index=i):
                    if self.commentary_text.exists():
                        self.commentary_text.text = text[:index]

                self._timers.append(bs.Timer(0.9 + 3.0 + (0.015 * (total_chars - i)), hide, repeat=False))

        start_clear()

    def vignette(self, final_color, longer):
        """Aesthetic reasons."""
        glb = bs.getactivity().globalsnode
        base_color = (0.57,0.57,0.57)
        bs.animate_array(glb, 'vignette_outer', 3, {0: base_color, 0.1: (final_color[0] / 1.2, final_color[1] / 1.2, final_color[2] / 1.2), (1 if longer else 0.5): base_color})

    def interactions(self):
        """Some personalized stuff and my deepest secrets.
           I don't know why, but I feel SoK may like this."""
        if self._puck is None:
            return

        vel = self._puck.node.velocity
        # apply the mult
        self._puck.node.velocity = (
            vel[0],
            vel[1] * self.ball_speed,
            vel[2]
        )

        green = bs.gettexture('ouyaOButton')
        yellow = bs.gettexture('ouyaYButton')
        red = bs.gettexture('ouyaAButton')
        blue = bs.gettexture('ouyaUButton')

        # If it passes the middle.. green.
        puck_node = self._puck.node
        pos = puck_node.position
        x_diff = abs(pos[0])

        if x_diff < 0.25 or self.curve:
            puck_node.color_texture = blue
            self._puck.touches = 0

        if pos[1] < 2.6 and (bs.time() - self.last_interaction_time > 0.5):
            mult = 0.935
            v = puck_node.velocity
            puck_node.velocity = (v[0] * mult, v[1] * mult, v[2] * mult)

        self.save_text = random.choice([
            "dived to the rescue!",
            "kept the ball alive!",
            "flew in to save the day!",
            "is too fast for the floor!",
            "bounced it back just in time!",
            "kept the dream alive!",
            "barely missed the ground!",
            "saved the rally!",
            "made a clutch save!",
            "refused to let it drop!",
            "pulled a superman save!",
            "made a desperate save!",
            "proved the floor is not an option!",
            "landed a miracle touch!",
            "saved the point!",
            "pulled off a heroic dive!",
            "stretched to the limit!",
            "barely kept it up!",
            "showed reflexes of a cat!",
            "denied the floor!",
            "made a clutch save!",
            "is staying in the game!",
            "pulled an epic recovery!",
            "reacted in the nick of time!",
            "won't let the ball drop!",
            "is pure hustle!",
            "made an impossible save!",
            "is defying gravity!",
            "made sure the ground stays empty!",
            "saved it!",
            "pulled off last-second magic!",
            "is floating to save it!",
            "is too clutch to fail!",
            "got the ball back in the air!",
            "is denying the dirt!",
            "saved it by a hair!",
            "is fighting for every ball!",
            "is pure energy!",
            "never gives up!",
            "keeps it in play!",
            "saved it barely!",
            "kept the floor clean!",
            "is pure determination!",
            "pulled a miraculous save!",
            "denied the game over!",
            "is still alive!",
            "is keeping the rally going!",
            "made an out-of-reach save!",
            "made a ninja-like save!",
            "bounced back from trouble!"])
        self.hit_text = random.choice([
            "sent it over!",
            "cleared the net!",
            "powered it across!",
            "nailed a deep shot!",
            "bounced it into their zone!",
            "launched an attack!",
            "sent a rocket over!",
            "is dominating the net!",
            "found the open spot!",
            "placed it perfectly!",
            "smashed it back!",
            "is applying the pressure!",
            "sent them scrambling!",
            "over the net it goes!",
            "hit a beauty!",
            "is controlling the court!",
            "forced a tough return!",
            "keeps the pressure high!",
            "landed a sweet strike!",
            "sent it deep!",
            "is playing aggressively!",
            "hit a laser beam!",
            "made a solid connection!",
            "is taking charge!",
            "sent a tricky shot over!",
            "is firing back!",
            "put it right on target!",
            "sent the ball flying!",
            "beat the defense!",
            "is crushing it!",
            "nailed that serve return!",
            "showed off some power!",
            "sent a high arc over!",
            "is making moves!",
            "kept them on their toes!",
            "delivered a powerful hit!",
            "is pushing the pace!",
            "found the gap!",
            "sent a curveball over!",
            "is looking sharp!",
            "hit it with precision!",
            "made them work for it!",
            "is owning the net!",
            "sent a heavy strike!",
            "is dictating the play!",
            "put it out of reach!",
            "landed the perfect hit!",
            "is on fire!",
            "sent a swift strike!",
            "is forcing errors!"
        ])
        self.control_text = random.choice([
            "is showing off sweet control!",
            "has the ball on a string!",
            "handles it with grace!",
            "shows off some nice touch!",
            "keeps it close and tight!",
            "is demonstrating perfect poise!",
            "has ice in their veins!",
            "is keeping it under control!",
            "shows a velvet touch!",
            "is masterfully handling the ball!",
            "keeps the ball glued to them!",
            "is displaying total composure!",
            "makes it look so easy!",
            "is controlling the pace!",
            "shows off pure finesse!",
            "has the ball perfectly placed!",
            "is staying cool under pressure!",
            "has incredible ball handling!",
            "is maneuvering with ease!",
            "keeps the ball within reach!",
            "shows off some fancy footwork!",
            "is keeping the ball calm!",
            "has the softest touch!",
            "is dictating the rhythm!",
            "keeps it balanced and steady!",
            "is showing high-level control!",
            "has the situation handled!",
            "is playing with surgical precision!",
            "keeps the ball in their zone!",
            "shows off expert handling!",
            "is keeping it smooth!",
            "has the ball right where they want it!",
            "demonstrates a gentle touch!",
            "is keeping the game slow!",
            "shows off calm concentration!",
            "has everything under control!",
            "is moving with grace!",
            "keeps the ball softly hovering!",
            "shows off true talent!",
            "is maintaining perfect flow!",
            "has a magical touch!",
            "is playing it smart!",
            "keeps the ball very close!",
            "shows off professional control!",
            "is handling the pressure well!",
            "has a very steady hand!",
            "is keeping it precise!",
            "shows off masterful technique!",
            "is keeping the ball in check!",
            "has the perfect feel for it!"
        ])
        if self.touches_indicator is not None and self.touches_indicator.exists():
            self.touches_indicator.position = (self._puck.node.position[0], self._puck.node.position[1] + 0.35,
                                               self._puck.node.position[2])
        else:
            self.touches_indicator = bs.newnode(
                'text',
                attrs=dict(
                    text='',
                    scale=0.025,
                    position=(0, 3, -5.8),
                    in_world=True,
                    flatness=1,
                    shadow=0,
                    color=(1, 1, 1, 0.5),
                    h_align='center',
                    v_align='top',
                    h_attach='center',
                    v_attach='top',
                ))



        everything = bs.getnodes()
        everyone = []
        closest_distance = 9999
        closest_player = None

        # i won't explain what "curve" is... look by yourself
        if not self.curve and not self._puck.scored:
            if bs.time() < self.smashed:
                random_pos = (random.uniform(0.1, 0.7) + self._puck.node.position[0],self._puck.node.position[1],random.uniform(0.1, 0.7) + self._puck.node.position[2])
                e = bs.newnode(
                    'explosion',
                    attrs={
                        'position': random_pos,
                        'color': self.smasher.color,
                        'radius': random.uniform(0.1, 0.7),
                        'big': False,
                    }
                )
                bs.timer(1, e.delete)
                self.smasher.getdelegate(object).percentage /= 1.1
            else:
                ball_tex = self._puck.node.color_texture

                texture_to_name = {
                    green: 'green',
                    yellow: 'yellow',
                    red: 'red',
                    blue: 'blue'
                }

                colors = {
                    'green': (0.6, 1, 0.6),
                    'yellow': (1, 0.3, 0),
                    'red': (1, 0, 0),
                    'blue': (0.6, 0.6, 1)
                }

                color_name = texture_to_name.get(ball_tex)
                color = colors.get(color_name)

                e = bs.newnode(
                    'explosion',
                    attrs={
                        'position': self._puck.node.position,
                        'color': color,
                        'radius': 0.1,
                        'big': False,
                    }
                )
                indicator_color = (*color, 0.5)
                bs.timer(1, e.delete)
                self.touches_indicator.color = indicator_color
                self.touches_indicator.text = str(3 - self._puck.touches)

        for human in everything: # doesn't make much sense, but I hope u understand I want players nodes.
            if human.getnodetype() == "spaz":
                everyone.append(human)

        for player_node in everyone:
            if not player_node.exists(): # why wouldn't u exist at first
                continue


            distance = math.dist(player_node.position, self._puck.node.position) # not wanting to do that Euclidean thingy
            player_node.hold_node = None
            player_node.getdelegate(object).impact_scale = 0
            if distance < closest_distance:
                closest_player = player_node # him, the closest one
                closest_distance = distance # his distance with the volleyball

        good : bool = (self._puck.touches < 3 and
                       bs.time() - self.last_interaction_time > 0.4 and
                       not self._puck.scored)
        # bs.time() is the current bombsquad time :) bs for bombsquad.


        delegate = closest_player.getdelegate(object)
        now = bs.time()
        can_jump = (delegate.last_jump_time_ms > delegate._jump_cooldown and closest_player.position[1] < 1)

        if closest_player.jump_pressed and can_jump:
            ppos = closest_player.position
            delegate.last_jump_time_ms = int(bs.time() * 1000)
            closest_player.handlemessage(
                'kick_back',
                ppos[0],
                ppos[1],
                ppos[2],
                0,
                1,
                0,
                50,  # small force
            )


        punched = now < delegate.punched
        pickup = now < delegate.pickup
        bombed = now < delegate.bombed
        curved = now < delegate.curved


        if closest_player and closest_distance < 4 and good: # SO if broski is the nearest AND broski is near enough...
            player = spaz = delegate
            ball = self._puck.node  # ball node
            you = closest_player.position  # already a node
            in_air = (you[1] > 0.8)
            if closest_distance < (1.35 if not in_air else 1.6) and (closest_player.punch_pressed or punched): # Ball goes where you look but always tries to go to the other side. (tell me if u guys want it to go totally where you're looking at)
                self.difficulty += 0.6 / 75
                e = bs.newnode(
                    'explosion',
                    attrs={
                        'position': self._puck.node.position,
                        'color': closest_player.color,
                        'radius': 0.8,
                        'big': False,
                    }
                )
                bs.timer(1, e.delete)
                self.last_interaction_time = bs.time()
                self._puck.touches += 1
                self.curve = False
                if self._puck.touches == 2:
                    spaz.percentage = min(spaz.percentage + 8, 100)
                    ball.color_texture = yellow
                    self.two_sound.play()
                elif self._puck.touches == 3:
                    spaz.percentage = min(spaz.percentage + 12, 100)
                    ball.color_texture = red
                    self.one_sound.play()
                else:
                    ball.color_texture = green
                bs.getsound("impactHard").play() # This is for the sound, you probably didn't know that!



                sight = (bs.Vec3(you) - bs.Vec3(closest_player.position_forward)).normalized() * (12 if delegate.percentage < 95 else 30) # Sight factor
                speed = 6 if delegate.percentage < 95 else 20 # bar full

                if curved:
                    start_pos = ball.position
                    end_pos = (sight[0] * 2, -1, -sight[2])
                    duration = 1.1
                    fps = 144
                    total_steps = int(duration * fps)
                    curved_time = bs.time() + 0.15
                    self.curving = True

                    z_offset = -4.0 if sight[0] < 0 else 4.0

                    def move_to_point(step):
                        if not ball.exists(): return
                        if ball.position[1] < 1 and bs.time() > curved_time: return
                        if not self.curving: return


                        t = step / total_steps

                        x = start_pos[0] + (end_pos[0] - start_pos[0]) * t
                        y = start_pos[1] + (end_pos[1] - start_pos[1]) * t
                        z = start_pos[2] + (end_pos[2] - start_pos[2]) * t

                        y += math.sin(t * math.pi) * 3.0

                        # Ajout de la courbe latérale
                        z += math.sin(t * math.pi) * z_offset

                        # --- LIMITE SUR L'AXE Z ---
                        # On force z à rester entre -5 et 5
                        z = max(-5.0, min(5.0, z))
                        # --------------------------

                        ball.position = (x, y, z)

                        if step < total_steps:
                            bs.timer(1 / fps, lambda: move_to_point(step + 1))

                    move_to_point(0)
                else:
                    # normal
                    self.curving = False
                    if in_air and delegate.percentage > 95:
                        if closest_player.position[0] < 0:
                            vel = (12 * 1.6, 0, sight[2]) * speed
                        else:
                            vel = (-12 * 1.6, 0, sight[2]) * speed
                    else:
                        if closest_player.position[0] < 0:
                            vel = (4.8 * 1.6, 0, sight[2]) * speed
                        else:
                            vel = (-4.8 * 1.6, 0, sight[2]) * speed

                    # smth
                    dist_from_middle = math.dist(you, (0, 2, 0))
                    height = (max(dist_from_middle * 2.75, 7) * 0.8)
                    if in_air and delegate.percentage > 95:
                        height = -4 * 2 / dist_from_middle

                    ball.velocity = (vel[0], height, vel[2])
                if in_air and delegate.percentage > 95:
                    audio = random.choice(['explosion01','explosion02','explosion03','explosion04','explosion05'])
                    bs.getsound(audio).play()
                    self.smashed = bs.time() + 1
                    self.smasher = closest_player
                    self.vignette(closest_player.color, False)
                    delegate.on_punch_press()
                    delegate.on_punch_release()
                    self.write(
                        f'{player.name.upper()} SMASHED THE BALL !' if random.random() < 0.5 else f'{player.name} hit the ball with all his might !', closest_player.color)
                else:
                    self.write(
                        f'{player.name} {self.hit_text}', closest_player.color)

                #prettiness here
                ppos = you
                f = (bs.Vec3(ball.position) - bs.Vec3(you)).normalized()
                closest_player.handlemessage(
                    'kick_back',
                    ppos[0],
                    ppos[1],
                    ppos[2],
                    f[0],
                    f[1],
                    f[2],
                    400,  # small force
                )
            if closest_distance < 1.35 and (closest_player.pickup_pressed or pickup): # Ball goes straight up in the air. idk what it is called.
                self.write(
                    f'{player.name} {self.control_text}', closest_player.color)
                y_diff = abs(self._puck.node.position[1] - closest_player.position[1])

                if y_diff < 1:
                    self.difficulty += 0.6 / 75
                    self.last_interaction_time = bs.time()
                    self.curve = False


                    self._puck.touches += 1

                    ball = self._puck.node
                    if self._puck.touches == 2:
                        spaz.percentage = min(spaz.percentage + 4, 100)
                        ball.color_texture = yellow
                        self.two_sound.play()
                    elif self._puck.touches == 3:
                        spaz.percentage = min(spaz.percentage + 6, 100)
                        ball.color_texture = red
                        self.one_sound.play()
                    else:
                        ball.color_texture = green

                    closest_player.handlemessage('celebrate', 400)
                    bs.getsound("impactMedium").play()
                    e = bs.newnode(
                        'explosion',
                        attrs={
                            'position': self._puck.node.position,
                            'color': closest_player.color,
                            'radius': 0.5,
                            'big': True,
                        }
                    )
                    bs.timer(1, e.delete)

                    direction = (bs.Vec3(you) - bs.Vec3(closest_player.position_forward)).normalized()
                    ball.velocity = (-you[0] * 0.04, 12.8, direction[2] * 0.1)
            if closest_player.bomb_pressed and not delegate.gliding or bombed and not delegate.gliding: # gliding.. variant coming soon
                self.write(
                    f'{player.name} {self.save_text}', closest_player.color)
                delegate.gliding = True
                ppos = you
                f = (bs.Vec3(ball.position) - bs.Vec3(you)).normalized()
                distance = math.dist(ball.position, you)
                closest_player.handlemessage(
                    'kick_back',
                    ppos[0],
                    ppos[1],
                    ppos[2],
                    f[0],
                    0,
                    f[2],
                    1000 - (500/distance),  # tiny force
                )
                closest_player.handlemessage('knockout', 100)
                print(1)
                spaz.pickup = now + 0.8

                bs.getsound("impactHard").play(volume=0.5)
                e = bs.newnode(
                    'explosion',
                    attrs={
                        'position': you,
                        'color': (0, 0.3, 0.5),
                        'radius': 1.1,
                        'big': False,
                    }
                )
                bs.timer(1, e.delete)
                bs.timer(0.6, lambda: setattr(delegate, 'gliding', False))

                # variant soon







    def on_team_join(self, team: Team) -> None:
        self._update_scoreboard()

    def _handle_puck_player_collide(self) -> None:
        collision = bs.getcollision()
        try:
            puck = collision.sourcenode.getdelegate(Puck, True)
            player = collision.opposingnode.getdelegate(PlayerSpaz,
                                                        True).getplayer(
                                                            Player, True)
        except bs.NotFoundError:
            return

        puck.last_players_to_touch[player.team.id] = player

    def _kill_puck(self) -> None:
        self._puck = None
        self.curve = True

    def _handle_score(self) -> None:
        assert self._puck is not None
        assert self._score_regions is not None

        # Our puck might stick around for a second or two
        # we don't want it to be able to score again
        # to not be getting a corrupted score.
        if self._puck.scored:
            return
        E = bs.newnode(
            'explosion',
            attrs={
                'position': self._puck.node.position,
                'color': (0,0,0),
                'radius': .1,
                'big': True,
            }
        )
        bs.timer(1, E.delete)
        bs.animate(self.touches_indicator, 'scale', {0: 0, 2.65: 0, 3: 0.025})
        self.touches_indicator.text = '0'
        if self.smashed > 0:
            self._puck.node.sticky = True
        self.smashed = -9999

        region = bs.getcollision().sourcenode
        index = 0
        for index in range(len(self._score_regions)):
            if region == self._score_regions[index].node:
                break

        for team in self.teams:
            if team.id == index:
                team.score += 1

                # Puck Spawn
                if team.id == 0:  # left side scored
                    self._puck_spawn_pos = (5, 0.7, 0)
                elif team.id == 1:  # right side scored
                    self._puck_spawn_pos = (-5, 0.7, 0)
                else:  # what the heck
                    self._puck_spawn_pos = (0, 0.7, 0)

                for player in team.players:
                    if player.actor:
                        player.actor.handlemessage(bs.CelebrateMessage(2.0)) # yay we scored
                        player.actor.percentage = min(player.actor.percentage + 15, 100)
                        # dont mind this ;(
                        scorch = bs.newnode(
                            'scorch',
                            attrs={
                                'position': self._puck.node.position,
                                'size': 1.4,
                                'color': player.actor.node.color,
                                'big': True,
                            },
                        )
                        bs.animate(scorch, 'presence', {3.000: 1, 7.000: 0})
                        bs.timer(7, scorch.delete)
                        self.vignette(player.actor.node.color, longer=True)

                # End game if we won.
                if team.score >= self._score_to_win:
                    self.end_game()

        self._cheer_sound.play()

        self._puck.scored = True

        # Kill the puck (it'll respawn itself shortly).
        bs.animate(self._puck.node, 'mesh_scale', {0: 0.25, 0.4 : 0}) # Animation ! 0 sec = 0.25 of size in our case
        bs.timer(0.7, self._kill_puck)

        bs.cameraflash(duration=7.0)
        self._update_scoreboard()

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.interactions_timer = None
        self.end(results=results)

    def on_transition_in(self) -> None:
        super().on_transition_in()

    def _update_scoreboard(self) -> None:
        winscore = self._score_to_win
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score, winscore)

    # overriding the default character spawning..
    def spawn_player(self, player: Player) -> bs.Actor:
        spaz = self.spawn_player_spaz(player)
        spaz.bomb_count = 0 # No bombs for yall bahaha
        # Now we want to make that your punches are useless too
        # But we will need the button to work so let's put the damage to 0 and some custom stuff
        spaz._punch_power_scale = 0
        spaz.impact_scale = 0
        spaz.check_timer = 0

        spaz.pickup = 0
        spaz.punched = 0
        spaz.bombed = 0
        spaz.curved = 0

        spaz.can_curve = False


        spaz.last_angle = 0
        spaz.total_rotation = 0.0
        spaz.rotation_direction = 0  # 0: neutre, 1: clockwise, -1: not clockwise

        spaz.gliding = False
        spaz.smashed = False
        spaz.percentage = 0
        spaz._jump_cooldown = 2000
        spaz.name = spaz.node.name
        spaz.bar = bs.newnode(
            'shield',
            owner=spaz.node,
            attrs={
                'position': spaz.node.position,
                'radius': .01,
                'color': (0, 0, 0),
            }
        )
        spaz.node.connectattr('position', spaz.bar, 'position')
        spaz.bar.always_show_health_bar = True
        spaz.node.name = '' # bahaha but you'll sspazuseful

        def check():
            if spaz.node.exists():
                # Controls part
                now = bs.time()

                if spaz.node.punch_pressed:
                    spaz.punched = now + 0.25
                elif spaz.node.pickup_pressed:
                    spaz.pickup = now + 0.40
                elif spaz.node.bomb_pressed:
                    spaz.bombed = now + 0.20
                elif spaz.node.jump_pressed and spaz.percentage > 95:
                    spaz.punched = now + 0.50

                if spaz.percentage > 95:
                    spaz.node.name = 'SMASH'
                else:
                    spaz.node.name = ''


                spaz.bar.hurt = min(1.0 - float(spaz.percentage) / 100, 1)

                # Curved ball part

                pos = spaz.node.position
                fwd = spaz.node.position_forward

                dx = fwd[0] - pos[0]
                dz = fwd[2] - pos[2]

                length = math.sqrt(dx * dx + dz * dz)
                if length > 0.0001:
                    dx /= length
                    dz /= length

                spaz.angle = math.degrees(math.atan2(-dx, -dz)) # trust

        # checks if u turn ! Not in the game yet !
        def check_270_rotation():
            now = bs.time()
            current_angle = spaz.angle

            delta = current_angle - spaz.last_angle
            if delta > 180: delta -= 360
            if delta < -180: delta += 360

            current_dir = 1 if delta > 0 else -1

            if spaz.rotation_direction != 0 and current_dir != spaz.rotation_direction:
                spaz.total_rotation = 0

            spaz.rotation_direction = current_dir

            spaz.total_rotation += abs(delta)

            if spaz.total_rotation >= 250:
                spaz.curved = now + 0.40
                spaz.total_rotation = 0

            spaz.last_angle = current_angle




        spaz.check_timer1 = bs.Timer(1/30, check, repeat=True)
        #spaz.check_timer2 = bs.Timer(1/30, check_270_rotation, repeat=True)

        #spaz.node.hold_node = spaz.node ... nevermind

        # By the way when you have a node but want his player just do
        # player = node.getdelegate(object)
        # i dont know why you'll need it but here it is

        return spaz

    def handlemessage(self, msg: Any) -> Any:

        # Respawn dead players if they're still in the game.
        # Because if we don't.. they won't like our game ;(
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior...
            super().handlemessage(msg)
            self.respawn_player(msg.getplayer(Player))

        # Respawn dead pucks.
        elif isinstance(msg, PuckDiedMessage):
            if not self.has_ended():
                bs.timer(2, self._spawn_puck) # 2 secs to breathe bahahaha
        else:
            super().handlemessage(msg)


    def _spawn_puck(self) -> None:
        self._swipsound.play()
        self._whistle_sound.play()
        assert self._puck_spawn_pos is not None
        self._puck = Puck(position=self._puck_spawn_pos)
        self.timer = bs.Timer(1 / 144, self.lock_it, repeat=True) # 144 ?.. yes
    def lock_it(self):
        if self._puck is None:
            return
        if self.curve:
            self._puck.node.position = self._puck_spawn_pos
        else:
            self._puck.node.shadow_size = min(self._puck.node.position[1] * 0.3, 2)


# ba_meta export babase.Plugin
class justlearn(babase.Plugin):
    def __init__(self):
        self.installer = ModInstaller()
        self.installer.run_full_install()


class ModInstaller:
    def __init__(self) -> None:
        self.python_user = _babase.env()["python_directory_user"]
        self.files = self.python_user + '/VolleyBallMap/'
        self.app_dir = _babase.env()["python_directory_app"] + '/'
        self.data_dir = self.app_dir + '../'
        self.meshes_dir = self.data_dir + 'meshes/'
        self.platform = _babase.app.classic.platform

    def run_full_install(self) -> None:
        import os
        import urllib.request
        import shutil
        import babase

        target_path = os.path.join(self.files, 'volleyball_net.bob')
        destination_path = os.path.join(self.meshes_dir, 'volleyball_net.bob')

        if os.path.exists(destination_path):
            return

        def _do_install():
            try:
                if not os.path.exists(self.files):
                    os.makedirs(self.files)

                url = "https://raw.githubusercontent.com/Scriptz1/Learn.py-Installer/main/volleyball_net.bob"
                urllib.request.urlretrieve(url, target_path)
                shutil.copy(target_path, destination_path)

                bui.screenmessage("Installation worked !", color=(0, 1, 0.3))
                bui.getsound('ding').play()

            except Exception as e:
                print(f"DEBUG ERROR: {e}")
                bui.screenmessage("Installation Failed!", color=(1, 0, 0))
                bui.getsound('kronk2').play()


        bs.apptimer(2.5, _do_install)