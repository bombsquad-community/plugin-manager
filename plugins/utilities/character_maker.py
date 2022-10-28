# Released under the MIT License. See LICENSE for details.


'''
Character Builder/Maker by Mr.Smoothy
Plugin helps to mix character models and textures in interactive way.

Watch tutorial : https://www.youtube.com/c/HeySmoothy
Join discord: https://discord.gg/ucyaesh for help
https://github.com/imayushsaini/Bombsquad-Ballistica-Modded-Server/

> create team playlist and add character maker mini game 
> Use export command to save character
> Character will be saved in CustomCharacter folder inside Bombsquad Mods folder

*Only one player in that mini game supported ...

Characters can be used offline or online
for online you need to share character file with  server owners.

*For server owners:_
     You might know what to do with that file, 
     Still , 
          refer code after line 455 in this file , add it as a plugin to import characters from json file.

*For modders:-
     You can add more models and texture , check line near 400 and add asset names ,  you can also modify sounds and icon in json file (optional)  .

To share your character with friends ,
     send them character .json file and tell them to put file in same location i.e Bombsquad/CustomCharacter  or for PC appdata/Local/Bombsquad/Mods/CustomCharacter
     this plugin should be installed on their device too

Dont forget to share your creativity with me ,
send your character screenshot discord: mr.smoothy#5824  https://discord.gg/ucyaesh

Register your character in above discord server , so other server owners can add your characters.


Released on 28 May 2021 


Update 2 june : use import <character-name>
'''


# ba_meta require api 7


from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import _ba
from bastd.actor.playerspaz import PlayerSpaz
from bastd.actor.scoreboard import Scoreboard

if TYPE_CHECKING:
    from typing import Any, Type, List, Dict, Tuple, Union, Sequence, Optional

import os
import json
from bastd.actor.spazappearance import *
spazoutfit = {
    "color_mask": "neoSpazColorMask",
    "color_texture": "neoSpazColor",
    "head": "neoSpazHead",
    "hand": "neoSpazHand",
    "torso": "neoSpazTorso",
    "pelvis": "neoSpazTorso",
    "upper_arm": "neoSpazUpperArm",
    "forearm": "neoSpazForeArm",
    "upper_leg": "neoSpazUpperLeg",
    "lower_leg": "neoSpazLowerLeg",
    "toes_model": "neoSpazToes",
    "jump_sounds": ['spazJump01', 'spazJump02', 'spazJump03', 'spazJump04'],
    "attack_sounds": ['spazAttack01', 'spazAttack02', 'spazAttack03', 'spazAttack04'],
    "impact_sounds": ['spazImpact01', 'spazImpact02', 'spazImpact03', 'spazImpact04'],
    "death_sounds": ['spazDeath01'],
    "pickup_sounds": ['spazPickup01'],
    "fall_sounds": ['spazFall01'],
    "icon_texture": "neoSpazIcon",
    "icon_mask_texture": "neoSpazIconColorMask",
    "style": "spaz"
}
character = None


class Player(ba.Player['Team']):
    """Our player type for this game."""


class Team(ba.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export game
class CharacterBuilder(ba.TeamGameActivity[Player, Team]):
    """A game type based on acquiring kills."""

    name = 'Character Maker'
    description = 'Create your own custom Characters'

    # Print messages when players die since it matters here.
    announce_player_deaths = True

    @classmethod
    def get_available_settings(
            cls, sessiontype: Type[ba.Session]) -> List[ba.Setting]:
        settings = [
            ba.IntSetting(
                'Kills to Win Per Player',
                min_value=1,
                default=5,
                increment=1,
            ),
            ba.IntChoiceSetting(
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

        if issubclass(sessiontype, ba.FreeForAllSession):
            settings.append(
                ba.BoolSetting('Allow Negative Scores', default=False))

        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return (issubclass(sessiontype, ba.DualTeamSession)
                or issubclass(sessiontype, ba.FreeForAllSession))

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ['Rampage']

    def __init__(self, settings: dict):

        super().__init__(settings)

        self.initdic()
        _ba.set_party_icon_always_visible(True)
        self._score_to_win: Optional[int] = None
        self._dingsound = ba.getsound('dingSmall')
        self._epic_mode = bool(settings['Epic Mode'])
        self._kills_to_win_per_player = int(
            settings['Kills to Win Per Player'])
        self._time_limit = float(settings['Time Limit'])
        self._allow_negative_scores = bool(
            settings.get('Allow Negative Scores', False))
        self.bodyindex = 0
        self.modelindex = 0
        self.youtube = ba.newnode(
            'text',
            attrs={
                'text': "youtube.com/c/HeySmoothy",
                'in_world': True,
                'scale': 0.02,
                'color': (1, 0, 0, 0.4),
                'h_align': 'center',
                'position': (0, 4, -1.9)
            })
        self.discordservere = ba.newnode(
            'text',
            attrs={
                'text': "discord.gg/ucyaesh",
                'in_world': True,
                'scale': 0.02,
                'color': (0.12, 0.3, 0.6, 0.4),
                'h_align': 'center',
                'position': (-3, 2.7, -1.9)
            })
        # self.discord= ba.newnode(
        #                 'text',
        #                 attrs={
        #                     'text': "mr.smoothy#5824",
        #                     'in_world': True,
        #                     'scale': 0.02,
        #                     'color': (01.2, 0.3, 0.7, 0.4),
        #                     'h_align': 'center',
        #                     'position': (4,2.7,-1.9)
        #                 })
        # Base class overrides.
        self.bodypart = ba.newnode(
            'text',
            attrs={
                'text': "<Choose Body Part>",
                'in_world': True,
                'scale': 0.02,
                'color': (1, 1, 0, 1),
                'h_align': 'center',
                'position': (-4, 6, -4)
            })
        self.newmodel = ba.newnode(
            'text',
            attrs={
                'text': "<Choose model/tex>",
                'in_world': True,
                'scale': 0.02,
                'color': (1, 1, 0, 1),
                'h_align': 'center',
                'position': (6, 6, -4)
            })
        self.slow_motion = self._epic_mode
        self.default_music = (ba.MusicType.EPIC if self._epic_mode else
                              ba.MusicType.TO_THE_DEATH)

    def get_instance_description(self) -> Union[str, Sequence]:
        return ''

    def get_instance_description_short(self) -> Union[str, Sequence]:
        return ''

    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            pass

    def on_begin(self) -> None:
        super().on_begin()

    def nextBodyPart(self):
        self.bodyindex = (self.bodyindex+1) % len(self.dic.keys())
        self.bodypart.delete()
        PART = list(self.dic.keys())[self.bodyindex]
        self.bodypart = ba.newnode(
            'text',
            attrs={
                'text': PART,
                'in_world': True,
                'scale': 0.02,
                'color': (1, 1, 1, 1),
                'h_align': 'center',
                'position': (-4, 6, -4)
            })

    def prevBodyPart(self):
        self.bodyindex = (self.bodyindex-1) % len(self.dic.keys())
        self.bodypart.delete()
        PART = list(self.dic.keys())[self.bodyindex]
        self.bodypart = ba.newnode(
            'text',
            attrs={
                'text': PART,
                'in_world': True,
                'scale': 0.02,
                'color': (1, 1, 1, 1),
                'h_align': 'center',
                'position': (-4, 6, -4)
            })

    def nextModel(self):

        self.newmodel.delete()
        PART = list(self.dic.keys())[self.bodyindex]
        self.modelindex = (self.modelindex+1) % len(self.dic[PART])
        model = self.dic[PART][self.modelindex]
        self.newmodel = ba.newnode(
            'text',
            attrs={
                'text': model,
                'in_world': True,
                'scale': 0.02,
                'color': (1, 1, 1, 1),
                'h_align': 'center',
                'position': (6, 6, -4)
            })

        self.setModel(PART, model)

    def prevModel(self):

        self.newmodel.delete()
        PART = list(self.dic.keys())[self.bodyindex]
        self.modelindex = (self.modelindex-1) % len(self.dic[PART])
        model = self.dic[PART][self.modelindex]
        self.newmodel = ba.newnode(
            'text',
            attrs={
                'text': model,
                'in_world': True,
                'scale': 0.02,
                'color': (1, 1, 1, 1),
                'h_align': 'center',
                'position': (6, 6, -4)
            })
        self.setModel(PART, model)

    def setModel(self, bodypart, modelname):
        global spazoutfit
        body = _ba.get_foreground_host_activity().players[0].actor.node
        if bodypart == 'head':
            body.head_model = ba.getmodel(modelname)
        elif bodypart == 'torso':
            body.torso_model = ba.getmodel(modelname)
        elif bodypart == 'pelvis':
            body.pelvis_model = ba.getmodel(modelname)
        elif bodypart == 'upper_arm':
            body.upper_arm_model = ba.getmodel(modelname)
        elif bodypart == 'forearm':
            body.forearm_model = ba.getmodel(modelname)
        elif bodypart == 'hand':
            body.hand_model = ba.getmodel(modelname)
        elif bodypart == 'upper_leg':
            body.upper_leg_model = ba.getmodel(modelname)
        elif bodypart == 'lower_leg':
            body.lower_leg_model = ba.getmodel(modelname)
        elif bodypart == 'toes_model':
            body.toes_model = ba.getmodel(modelname)
        elif bodypart == 'style':
            body.style = modelname
        elif bodypart == 'color_texture':
            body.color_texture = ba.gettexture(modelname)
        elif bodypart == 'color_mask':
            body.color_mask_texture = ba.gettexture(modelname)
        spazoutfit[bodypart] = modelname

    def spawn_player(self, player: Player) -> ba.Actor:
        global character
        if character != None:
            player.character = character

        self.setcurrentcharacter(player.character)

        spaz = self.spawn_player_spaz(player)

        # Let's reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up.
        spaz.connect_controls_to_player(enable_punch=False,
                                        enable_jump=False,
                                        enable_bomb=False,
                                        enable_pickup=False)
        intp = ba.InputType
        player.assigninput(intp.JUMP_PRESS, self.nextBodyPart)
        player.assigninput(intp.PICK_UP_PRESS, self.prevBodyPart)
        player.assigninput(intp.PUNCH_PRESS, self.nextModel)
        player.assigninput(intp.BOMB_PRESS, self.prevModel)
        # Also lets have them make some noise when they die.
        spaz.play_big_death_sound = True
        return spaz

    def handlemessage(self, msg: Any) -> Any:

        if isinstance(msg, ba.PlayerDiedMessage):

            # Augment standard behavior.
            super().handlemessage(msg)

            player = msg.getplayer(Player)
            self.respawn_player(player)

        else:
            return super().handlemessage(msg)
        return None

    def setcurrentcharacter(self, charname):
        global spazoutfit
        char = ba.app.spaz_appearances[charname]
        spazoutfit['head'] = char.head_model
        spazoutfit['hand'] = char.hand_model
        spazoutfit['torso'] = char.torso_model
        spazoutfit['pelvis'] = char.pelvis_model
        spazoutfit['upper_arm'] = char.upper_arm_model
        spazoutfit['forearm'] = char.forearm_model
        spazoutfit['upper_leg'] = char.upper_leg_model
        spazoutfit['lower_leg'] = char.lower_leg_model
        spazoutfit['toes_model'] = char.toes_model
        spazoutfit['style'] = char.style
        spazoutfit['color_mask'] = char.color_mask_texture
        spazoutfit['color_texture'] = char.color_texture

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score,
                                            self._score_to_win)

    def end_game(self) -> None:
        results = ba.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)

    def initdic(self):
        self.dic = {"head": ["bomb", "landMine", "trees", "wing", "eyeLid", "impactBomb"],
                    "hand": ["hairTuft3", "bomb", "powerup"],
                    "torso": ["bomb", "landMine", "bomb"],
                    "pelvis": ["hairTuft4", "bomb"],
                    "upper_arm": ["wing", "locator", "bomb"],
                    "forearm": ["flagPole", "bomb"],
                    "upper_leg": ["bomb"],
                    "lower_leg": ["bomb"],
                    "toes_model": ["bomb"],
                    "style": ["spaz", "female", "ninja", "kronk", "mel", "pirate", "santa", "frosty", "bones", "bear", "penguin", "ali", "cyborg", "agent", "pixie", "bunny"],
                    "color_texture": ["kronk", "egg1", "egg2", "egg3", "achievementGotTheMoves", "bombColor", "crossOut", "explosion", "rgbStripes", "powerupCurse", "powerupHealth", "impactBombColorLit"],
                    "color_mask": ["egg1", "egg2", "egg3", "bombColor", "crossOutMask", "fontExtras3"]

                    }
        chars = ["neoSpaz", "zoe", "ninja", "kronk", "mel", "jack", "santa", "frosty",
                 "bones", "bear", "penguin", "ali", "cyborg", "agent", "wizard", "pixie", "bunny"]
        for char in chars:
            self.dic["head"].append(char+"Head")
            self.dic["hand"].append(char+"Hand")
            self.dic["torso"].append(char+"Torso")
            if char not in ['mel', "jack", "santa"]:
                self.dic["pelvis"].append(char+"Pelvis")
            self.dic["upper_arm"].append(char+"UpperArm")
            self.dic["forearm"].append(char+"ForeArm")
            self.dic["upper_leg"].append(char+"UpperLeg")
            self.dic["lower_leg"].append(char+"LowerLeg")
            self.dic["toes_model"].append(char+"Toes")
            self.dic["color_mask"].append(char+"ColorMask")
            if char != "kronk":
                self.dic["color_texture"].append(char+"Color")


cm = _ba.chatmessage


def _new_chatmessage(msg: str | ba.Lstr, clients: Sequence[int] | None = None, sender_override: str | None = None):
    if msg.split(" ")[0] == "export":
        if len(msg.split(" ")) > 1:
            savecharacter(msg.split(" ")[1])
        else:
            _ba.screenmessage("Enter name of character")
    elif msg.split(" ")[0] == "import":
        importcharacter(msg[7:])

    else:
        cm(msg, clients, sender_override)


_ba.chatmessage = _new_chatmessage


def savecharacter(name):
    path = os.path.join(_ba.env()["python_directory_user"], "CustomCharacters" + os.sep)
    if not os.path.isdir(path):
        os.makedirs(path)
    if _ba.get_foreground_host_activity() != None:

        with open(path+name+".json", 'w') as f:
            json.dump(spazoutfit, f, indent=4)
            registercharacter(name, spazoutfit)
        ba.playsound(ba.getsound("gunCocking"))
        _ba.screenmessage("Character Saved")
    else:
        _ba.screenmessage("Works offline with Character Maker")


def importcharacter(name):
    if name in ba.app.spaz_appearances:
        global character
        character = name
        try:
            _ba.get_foreground_host_activity().players[0].actor.node.handlemessage(ba.DieMessage())
            _ba.screenmessage("Imported")
        except:
            _ba.screenmessage("works offline with character maker")

    else:
        _ba.screenmessage("invalid name check typo \n name is case sensitive")


def registercharacter(name, char):
    t = Appearance(name.split(".")[0])
    t.color_texture = char['color_texture']
    t.color_mask_texture = char['color_mask']
    t.default_color = (0.6, 0.6, 0.6)
    t.default_highlight = (0, 1, 0)
    t.icon_texture = char['icon_texture']
    t.icon_mask_texture = char['icon_mask_texture']
    t.head_model = char['head']
    t.torso_model = char['torso']
    t.pelvis_model = char['pelvis']
    t.upper_arm_model = char['upper_arm']
    t.forearm_model = char['forearm']
    t.hand_model = char['hand']
    t.upper_leg_model = char['upper_leg']
    t.lower_leg_model = char['lower_leg']
    t.toes_model = char['toes_model']
    t.jump_sounds = char['jump_sounds']
    t.attack_sounds = char['attack_sounds']
    t.impact_sounds = char['impact_sounds']
    t.death_sounds = char['death_sounds']
    t.pickup_sounds = char['pickup_sounds']
    t.fall_sounds = char['fall_sounds']
    t.style = char['style']


# ba_meta export plugin
class HeySmoothy(ba.Plugin):

    def __init__(self):
        _ba.set_party_icon_always_visible(True)

        path = os.path.join(_ba.env()["python_directory_user"], "CustomCharacters" + os.sep)
        if not os.path.isdir(path):
            os.makedirs(path)
        files = os.listdir(path)
        for file in files:
            with open(path+file, 'r') as f:
                character = json.load(f)
                registercharacter(file, character)
