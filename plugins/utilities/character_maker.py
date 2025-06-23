# Released under the MIT License. See LICENSE for details.

# ba_meta require api 9


'''
Character Builder/Maker by Mr.Smoothy
Plugin helps to mix character models and textures in interactive way.

Watch tutorial : https://youtu.be/q0KxY1hfMPQ
Join discord: https://discord.gg/ucyaesh for help
https://bombsquad-community.web.app/home

> create team playlist and add character maker mini game 
> Use export command to save character
> Character will be saved in CustomCharacter folder inside Bombsquad Mods folder


Characters can be used offline or online
for online you need to share character file with  server owners.

*For server owners:_
     You might know what to do with that file, 
     Still , 
          refer code after line 455 in this file , add it as a plugin to import characters from json file.

*For modders:-
     You can add more models and texture , check line near 400 and add asset names ,  you can also modify sounds and icon in json file (optional)  .

To share your character with friends ,
     send them character .json file and tell them to put file in same location i.e mods/CustomCharacter  or for PC appdata/Local/Bombsquad/Mods/CustomCharacter
     this plugin should be installed on their device too.

Dont forget to share your creativity with me ,
send your character screenshot discord: mr.smoothy#5824  https://discord.gg/ucyaesh

Register your character in above discord server , so other server owners can add your characters.


Released on 28 May 2021 
Update 2 june : use import <character-name>
Update 29 July 2023: updated to API 8 , multiplayer support
'''

from typing import Sequence
import _babase
import babase
import bauiv1 as bui
from bascenev1lib.actor.spazappearance import *
from bascenev1lib.actor.text import Text
from bascenev1lib.actor.image import Image
import bauiv1lib.mainmenu

import os
import copy
import json

GAME_USER_DIRECTORY = _babase.env()["python_directory_user"]
CUSTOM_CHARACTERS = os.path.join(GAME_USER_DIRECTORY, "CustomCharacters")
os.makedirs(CUSTOM_CHARACTERS, exist_ok=True)


SPAZ_PRESET = {
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
    "toes_mesh": "neoSpazToes",
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


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self):
        self.score = 0


# ba_meta export bascenev1.GameActivity
class CharacterBuilder(bs.TeamGameActivity[Player, Team]):
    """A game type based on acquiring kills."""

    name = 'Character Maker'
    description = 'Create your own custom Characters'

    # Print messages when players die since it matters here.
    announce_player_deaths = True

    @classmethod
    def get_available_settings(cls, sessiontype):
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
                default=1.0,
            ),
            bs.BoolSetting('Epic Mode', default=False),
        ]

        if issubclass(sessiontype, bs.FreeForAllSession):
            settings.append(
                bs.BoolSetting('Allow Negative Scores', default=False))

        return settings

    @classmethod
    def supports_session_type(cls, sessiontype):
        return (issubclass(sessiontype, bs.DualTeamSession)
                or issubclass(sessiontype, bs.FreeForAllSession))

    @classmethod
    def get_supported_maps(cls, sessiontype):
        return ['Rampage']

    def __init__(self, settings):
        super().__init__(settings)

        self.initialize_meshs()
        self._score_to_win = None
        self._dingsound = bs.getsound('dingSmall')
        self._epic_mode = bool(settings['Epic Mode'])
        self._kills_to_win_per_player = int(
            settings['Kills to Win Per Player'])
        self._time_limit = float(settings['Time Limit'])
        self._allow_negative_scores = bool(
            settings.get('Allow Negative Scores', False))

        self._punch_image = Image(
            bs.gettexture('buttonPunch'),
            position=(345, 200),
            scale=(50, 50),
            color=(0.9, 0.9, 0, 0.9)
        )
        self._punch_text = Text(
            "Model+",
            scale=0.7,
            shadow=0.5,
            flatness=0.5,
            color=(0.9, 0.9, 0, 0.9),
            position=(263, 190))

        self._grab_image = Image(
            bs.gettexture('buttonPickUp'),
            position=(385, 240),
            scale=(50, 50),
            color=(0, 0.7, 0.9)
        )
        self._grab_text = Text(
            "Component-",
            scale=0.7,
            shadow=0.5,
            flatness=0.5,
            color=(0, 0.7, 1, 0.9),
            position=(340, 265))

        self._jump_image = Image(
            bs.gettexture('buttonJump'),
            position=(385, 160),
            scale=(50, 50),
            color=(0.2, 0.9, 0.2, 0.9)
        )
        self._jump_text = Text(
            "Component+",
            scale=0.7,
            shadow=0.5,
            flatness=0.5,
            color=(0.2, 0.9, 0.2, 0.9),
            position=(340, 113))

        self._bomb_image = Image(
            bs.gettexture('buttonBomb'),
            position=(425, 200),
            scale=(50, 50),
            color=(0.9, 0.2, 0.2, 0.9)
        )
        self._bomb_text = Text(
            "Model-",
            scale=0.7,
            shadow=0.5,
            flatness=0.5,
            color=(0.9, 0.2, 0.2, 0.9),
            position=(452, 190))

        self._host = Text(
            "Originally created by \ue020HeySmoothy\nhttps://youtu.be/q0KxY1hfMPQ\nhttps://youtu.be/3l2dxWEhrzE\n\nModified for multiplayer by \ue047Nyaa! :3",
            flash=False,
            maxwidth=0,
            scale=0.65,
            shadow=0.5,
            flatness=0.5,
            h_align=Text.HAlign.RIGHT,
            v_attach=Text.VAttach.BOTTOM,
            h_attach=Text.HAttach.RIGHT,
            color=(1.0, 0.4, 0.95, 0.8),
            position=(-2, 82))
        self._discord = Text(
            "Join discord.gg/ucyaesh to provide feedback or to use this Character Maker offline!",
            flash=False,
            maxwidth=0,
            scale=0.85,
            shadow=0.5,
            flatness=0.5,
            h_align=Text.HAlign.CENTER,
            v_attach=Text.VAttach.BOTTOM,
            h_attach=Text.HAttach.CENTER,
            color=(1.0, 0.4, 0, 1),
            position=(0, 110))
        self._website = Text(
            "check mods folder to get JSON character file ever exported from here!",
            flash=False,
            maxwidth=0,
            scale=0.85,
            shadow=0.5,
            flatness=0.5,
            h_align=Text.HAlign.CENTER,
            v_attach=Text.VAttach.BOTTOM,
            h_attach=Text.HAttach.CENTER,
            color=(0.2, 0.9, 1.0, 1),
            position=(0, 150))
        self._commands = Text(
            "Commands:\n\n\t1. /info\n\t2. /export <character-name>\n\t3. /import <character-name>\n\t",
            flash=False,
            maxwidth=0,
            scale=0.8,
            shadow=0.5,
            flatness=0.5,
            h_align=Text.HAlign.LEFT,
            v_attach=Text.VAttach.TOP,
            h_attach=Text.HAttach.LEFT,
            color=(0.3, 0.9, 0.3, 0.8),
            position=(30, -112))
        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = bs.MusicType.MARCHING

    def get_instance_description(self):
        return ''

    def get_instance_description_short(self):
        return ''

    def on_team_join(self, team: Team):
        if self.has_begun():
            pass

    def on_begin(self):
        super().on_begin()

    def nextBodyPart(self, spaz):
        spaz.bodyindex = (spaz.bodyindex+1) % len(self.cache.keys())
        try:
            spaz.bodypart.delete()
        except AttributeError:
            pass
        part = list(self.cache.keys())[spaz.bodyindex]
        spaz.bodypart = bs.newnode(
            'text',
            owner=spaz.node,
            attrs={
                'text': str(part),
                'in_world': True,
                'color': (1, 1, 1),
                'scale': 0.011,
                'shadow': 0.5,
                'flatness': 0.5,
                'h_align': 'center', })
        math = bs.newnode('math',
                          owner=spaz.node,
                          attrs={
                              'input1': (0, 1.7, 0.5),
                              'operation': 'add',
                          })
        spaz.node.connectattr('position', math, 'input2')
        math.connectattr('output', spaz.bodypart, 'position')
        bs.getsound('deek').play()

    def prevBodyPart(self, spaz):
        spaz.bodyindex = (spaz.bodyindex-1) % len(self.cache.keys())
        try:
            spaz.bodypart.delete()
        except AttributeError:
            pass
        part = list(self.cache.keys())[spaz.bodyindex]
        spaz.bodypart = bs.newnode(
            'text',
            owner=spaz.node,
            attrs={
                'text': str(part),
                'in_world': True,
                'color': (1, 1, 1),
                'scale': 0.011,
                'shadow': 0.5,
                'flatness': 0.5,
                'h_align': 'center', })
        math = bs.newnode('math',
                          owner=spaz.node,
                          attrs={
                              'input1': (0, 1.7, 0.5),
                              'operation': 'add',
                          })
        spaz.node.connectattr('position', math, 'input2')
        math.connectattr('output', spaz.bodypart, 'position')
        bs.getsound('deek').play()

    def nextModel(self, spaz):
        try:
            spaz.newmesh.delete()
        except AttributeError:
            pass
        part = list(self.cache.keys())[spaz.bodyindex]
        spaz.meshindex = (spaz.meshindex+1) % len(self.cache[part])
        mesh = self.cache[part][spaz.meshindex]
        spaz.newmesh = bs.newnode(
            'text',
            owner=spaz.node,
            attrs={
                'text': str(mesh),
                'in_world': True,
                'color': (1, 1, 1),
                'scale': 0.011,
                'shadow': 0.5,
                'flatness': 0.5,
                'h_align': 'center'
            })
        math = bs.newnode('math',
                          owner=spaz.node,
                          attrs={
                              'input1': (0, -0.6, 0.5),
                              'operation': 'add',
                          })
        spaz.node.connectattr('position', math, 'input2')
        math.connectattr('output', spaz.newmesh, 'position')
        if part == "main_color":
            self.setColor(spaz, mesh)
        elif part == "highlight_color":
            self.setHighlight(spaz, mesh)
        else:
            self.setModel(spaz, part, mesh)
        bs.getsound('click01').play()

    def prevModel(self, spaz):
        try:
            spaz.newmesh.delete()
        except AttributeError:
            pass
        part = list(self.cache.keys())[spaz.bodyindex]
        spaz.meshindex = (spaz.meshindex-1) % len(self.cache[part])
        mesh = self.cache[part][spaz.meshindex]
        spaz.newmesh = bs.newnode(
            'text',
            owner=spaz.node,
            attrs={
                'text': str(mesh),
                'in_world': True,
                'color': (1, 1, 1),
                'scale': 0.011,
                'shadow': 0.5,
                'flatness': 0.5,
                'h_align': 'center'
            })
        math = bs.newnode('math',
                          owner=spaz.node,
                          attrs={
                              'input1': (0, -0.6, 0.5),
                              'operation': 'add',
                          })
        spaz.node.connectattr('position', math, 'input2')
        math.connectattr('output', spaz.newmesh, 'position')
        if part == "main_color":
            self.setColor(spaz, mesh)
        elif part == "highlight_color":
            self.setHighlight(spaz, mesh)
        else:
            self.setModel(spaz, part, mesh)
        bs.getsound('click01').play()

    def setColor(self, spaz, color):
        spaz.node.color = color

    def setHighlight(self, spaz, highlight):
        spaz.node.highlight = highlight

    def setModel(self, spaz, bodypart, meshname):
        if bodypart == 'head':
            spaz.node.head_mesh = bs.getmesh(meshname)
        elif bodypart == 'torso':
            spaz.node.torso_mesh = bs.getmesh(meshname)
        elif bodypart == 'pelvis':
            spaz.node.pelvis_mesh = bs.getmesh(meshname)
        elif bodypart == 'upper_arm':
            spaz.node.upper_arm_mesh = bs.getmesh(meshname)
        elif bodypart == 'forearm':
            spaz.node.forearm_mesh = bs.getmesh(meshname)
        elif bodypart == 'hand':
            spaz.node.hand_mesh = bs.getmesh(meshname)
        elif bodypart == 'upper_leg':
            spaz.node.upper_leg_mesh = bs.getmesh(meshname)
        elif bodypart == 'lower_leg':
            spaz.node.lower_leg_mesh = bs.getmesh(meshname)
        elif bodypart == 'toes_mesh':
            spaz.node.toes_mesh = bs.getmesh(meshname)
        elif bodypart == 'style':
            spaz.node.style = meshname
        elif bodypart == 'color_texture':
            spaz.node.color_texture = bs.gettexture(meshname)
        elif bodypart == 'color_mask':
            spaz.node.color_mask_texture = bs.gettexture(meshname)

    def spawn_player(self, player):
        spaz = self.spawn_player_spaz(player)
        spaz.bodyindex = 0
        spaz.meshindex = 0
        spaz.bodypart = bs.newnode(
            'text',
            owner=spaz.node,
            attrs={
                'text': "<Choose Component>",
                'in_world': True,
                'scale': 0.011,
                'color': (1, 0.4, 0.9, 1),
                'h_align': 'center',
                'shadow': 0.7,
                'flatness': 0.5,
            })
        math = bs.newnode('math',
                          owner=spaz.node,
                          attrs={
                              'input1': (0, 1.7, 0.5),
                              'operation': 'add',
                          })
        spaz.node.connectattr('position', math, 'input2')
        math.connectattr('output', spaz.bodypart, 'position')
        spaz.newmesh = bs.newnode(
            'text',
            owner=spaz.node,
            attrs={
                'text': "<Choose Model/Tex>",
                'in_world': True,
                'scale': 0.011,
                'color': (1, 0.4, 0.9, 1),
                'h_align': 'center',
                'shadow': 0.7,
                'flatness': 0.5,
            })
        math = bs.newnode('math',
                          owner=spaz.node,
                          attrs={
                              'input1': (0, -0.6, 0.5),
                              'operation': 'add',
                          })
        spaz.node.connectattr('position', math, 'input2')
        math.connectattr('output', spaz.newmesh, 'position')

        # Let's reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up.
        # spaz.connect_controls_to_player(enable_punch=False,
        #                                 enable_jump=False,
        #                                 enable_bomb=False,
        #                                 enable_pickup=False)

        intp = babase.InputType
        player.assigninput(intp.JUMP_PRESS, lambda: self.nextBodyPart(spaz))
        player.assigninput(intp.PICK_UP_PRESS, lambda: self.prevBodyPart(spaz))
        player.assigninput(intp.PUNCH_PRESS, lambda: self.nextModel(spaz))
        player.assigninput(intp.BOMB_PRESS, lambda: self.prevModel(spaz))
        # Also lets have them make some noise when they die.
        spaz.play_big_death_sound = True
        return spaz

    def handlemessage(self, msg):
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            player = msg.getplayer(Player)
            self.respawn_player(player)
        else:
            return super().handlemessage(msg)
        return None

    def _update_scoreboard(self):
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score,
                                            self._score_to_win)

    def end_game(self):
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)

    def initialize_meshs(self):
        self.cache = {
            "head": ["bomb", "landMine", "wing", "eyeLid", "impactBomb"],
            "hand": ["hairTuft3", "bomb", "powerup"],
            "torso": ["bomb", "landMine", "bomb"],
            "pelvis": ["hairTuft4", "bomb"],
            "upper_arm": ["wing", "locator", "bomb"],
            "forearm": ["flagPole", "bomb"],
            "upper_leg": ["bomb"],
            "lower_leg": ["bomb"],
            "toes_mesh": ["bomb"],
            "style": ["spaz", "female", "ninja", "kronk", "mel", "pirate", "santa", "frosty", "bones", "bear", "penguin", "ali", "cyborg", "agent", "pixie", "bunny"],
            "color_texture": ["kronk", "egg1", "egg2", "egg3", "achievementGotTheMoves", "bombColor", "crossOut", "explosion", "rgbStripes", "powerupCurse", "powerupHealth", "impactBombColorLit"],
            "color_mask": ["egg1", "egg2", "egg3", "bombColor", "crossOutMask", "fontExtras3"],
            "main_color": [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)],
            "highlight_color": [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)],
        }
        chars = ["neoSpaz", "zoe", "ninja", "kronk", "mel", "jack", "santa", "frosty",
                 "bones", "bear", "penguin", "ali", "cyborg", "agent", "wizard", "pixie", "bunny"]

        for char in chars:
            self.cache["head"].append(char + "Head")
            self.cache["hand"].append(char + "Hand")
            self.cache["torso"].append(char + "Torso")
            if char not in ['mel', "jack", "santa"]:
                self.cache["pelvis"].append(char + "Pelvis")
            self.cache["upper_arm"].append(char + "UpperArm")
            self.cache["forearm"].append(char + "ForeArm")
            self.cache["upper_leg"].append(char + "UpperLeg")
            self.cache["lower_leg"].append(char + "LowerLeg")
            self.cache["toes_mesh"].append(char + "Toes")
            self.cache["color_mask"].append(char + "ColorMask")
            if char != "kronk":
                self.cache["color_texture"].append(char + "Color")


def mesh_to_string(mesh):
    return str(mesh)[17:-2]


def texture_to_string(texture):
    return str(texture)[20:-2]


def spaz_to_json(spaz):
    spaz_json = copy.deepcopy(SPAZ_PRESET)
    spaz_json['head'] = mesh_to_string(spaz.node.head_mesh)
    spaz_json['hand'] = mesh_to_string(spaz.node.hand_mesh)
    spaz_json['torso'] = mesh_to_string(spaz.node.torso_mesh)
    spaz_json['pelvis'] = mesh_to_string(spaz.node.pelvis_mesh)
    spaz_json['upper_arm'] = mesh_to_string(spaz.node.upper_arm_mesh)
    spaz_json['forearm'] = mesh_to_string(spaz.node.forearm_mesh)
    spaz_json['upper_leg'] = mesh_to_string(spaz.node.upper_leg_mesh)
    spaz_json['lower_leg'] = mesh_to_string(spaz.node.lower_leg_mesh)
    spaz_json['toes_mesh'] = mesh_to_string(spaz.node.toes_mesh)
    spaz_json['style'] = spaz.node.style
    spaz_json['color_mask'] = texture_to_string(spaz.node.color_mask_texture)
    spaz_json['color_texture'] = texture_to_string(spaz.node.color_texture)
    return spaz_json


def import_character(name, spaz):
    if not name:
        bs.screenmessage("Inavlid character name")
        return
    character = None
    for appearance_name, appearance_character in bs.app.classic.spaz_appearances.items():
        if name.lower() == appearance_name.lower():
            character = appearance_character
            break
    if not character:
        return (False, name)
    activity = bs.get_foreground_host_activity()
    with activity.context:
        spaz.node.head_mesh = bs.getmesh(character.head_mesh)
        spaz.node.hand_mesh = bs.getmesh(character.hand_mesh)
        spaz.node.torso_mesh = bs.getmesh(character.torso_mesh)
        spaz.node.pelvis_mesh = bs.getmesh(character.pelvis_mesh)
        spaz.node.upper_arm_mesh = bs.getmesh(character.upper_arm_mesh)
        spaz.node.forearm_mesh = bs.getmesh(character.forearm_mesh)
        spaz.node.upper_leg_mesh = bs.getmesh(character.upper_leg_mesh)
        spaz.node.lower_leg_mesh = bs.getmesh(character.lower_leg_mesh)
        spaz.node.toes_mesh = bs.getmesh(character.toes_mesh)
        spaz.node.style = character.style
        spaz.node.color_mask_texture = bs.gettexture(character.color_mask_texture)
        spaz.node.color_texture = bs.gettexture(character.color_texture)
    return (True, appearance_name)


def export_character(name, spaz):
    default_characters = tuple(bs.app.classic.spaz_appearances.keys())[:30]
    os.makedirs(CUSTOM_CHARACTERS, exist_ok=True)
    character_file = name + ".json"
    for saved_character_file in os.listdir(CUSTOM_CHARACTERS):
        if character_file.lower() == saved_character_file.lower():
            return (False, os.path.splitext(saved_character_file)[0])
        for default_character in default_characters:
            if name.lower() == default_character.lower():
                return (False, default_character)
    spaz_json = spaz_to_json(spaz)
    with open(os.path.join(CUSTOM_CHARACTERS, character_file), "w") as fout:
        json.dump(spaz_json, fout, indent=4)
    register_character_json(name, spaz_json)
    return (True, name)


def register_character_json(name, character):
    appearance = Appearance(name)
    appearance.color_texture = character['color_texture']
    appearance.color_mask_texture = character['color_mask']
    appearance.default_color = (0.6, 0.6, 0.6)
    appearance.default_highlight = (0, 1, 0)
    appearance.icon_texture = character['icon_texture']
    appearance.icon_mask_texture = character['icon_mask_texture']
    appearance.head_mesh = character['head']
    appearance.torso_mesh = character['torso']
    appearance.pelvis_mesh = character['pelvis']
    appearance.upper_arm_mesh = character['upper_arm']
    appearance.forearm_mesh = character['forearm']
    appearance.hand_mesh = character['hand']
    appearance.upper_leg_mesh = character['upper_leg']
    appearance.lower_leg_mesh = character['lower_leg']
    appearance.toes_mesh = character['toes_mesh']
    appearance.jump_sounds = character['jump_sounds']
    appearance.attack_sounds = character['attack_sounds']
    appearance.impact_sounds = character['impact_sounds']
    appearance.death_sounds = character['death_sounds']
    appearance.pickup_sounds = character['pickup_sounds']
    appearance.fall_sounds = character['fall_sounds']
    appearance.style = character['style']


cm = bs.chatmessage


def _new_chatmessage(msg: str | babase.Lstr, *args, **kwargs):
    activity = bs.get_foreground_host_activity()
    if not activity:
        cm(msg, *args, **kwargs)
        return

    is_a_command = any(msg.startswith(command) for command in ("/export", "/import", "/info"))
    if not is_a_command:
        cm(msg, *args, **kwargs)
        return

    player = get_player(msg, activity)
    if not player:
        cm("no player exists in game, try adding client id at last of command", *args, **kwargs)
        cm(msg, *args, **kwargs)
        return

    if msg.startswith("/export"):
        if len(msg.split(" ")) > 1:
            success, character_name = export_character(" ".join(msg.split(" ")[1:]), player.actor)
            if success:
                bs.screenmessage(
                    'Exported character "{}"'.format(character_name),
                    color=(0, 1, 0)
                )
                bui.getsound("gunCocking").play()
            else:
                bs.screenmessage(
                    'Character "{}" already exists'.format(character_name),
                    color=(1, 0, 0)
                )
                bui.getsound("error").play()
        else:
            cm("Enter name of character, Usage: /export <character_name>", *args, **kwargs)
    elif msg.startswith("/import"):
        if len(msg.split(" ")) > 1:
            success, character_name = import_character(" ".join(msg.split(" ")[1:]), player.actor)
            if success:
                bs.screenmessage(
                    'Imported character "{}"'.format(character_name),
                    color=(0, 1, 0)
                )
                bui.getsound("gunCocking").play()
            else:
                bs.screenmessage(
                    'Character "{}" doesn\'t exist'.format(character_name),
                    color=(1, 0, 0)
                )
                bui.getsound("error").play()
        else:
            cm("Usage: /import <character_name>", *args, **kwargs)
    elif msg.startswith("/info"):
        spaz_json = spaz_to_json(player.actor)
        del spaz_json["jump_sounds"]
        del spaz_json["attack_sounds"]
        del spaz_json["impact_sounds"]
        del spaz_json["death_sounds"]
        del spaz_json["pickup_sounds"]
        del spaz_json["fall_sounds"]
        spaz_str = ""
        for key, value in spaz_json.items():
            spaz_str += "{}: {}\n".format(key, value)
        bs.screenmessage(spaz_str, color=(1, 1, 1))

    cm(msg, *args, **kwargs)


bs.chatmessage = _new_chatmessage


def get_player(msg, activity):
    client_id = -1
    words = msg.split(" ")
    last_word = words[-1]
    if last_word.isdigit():
        client_id = int(last_word)
    for player in activity.players:
        player_client_id = player.sessionplayer.inputdevice.client_id
        if client_id == player_client_id:
            return player


# ba_meta export babase.Plugin
class bySmoothy(babase.Plugin):
    def __init__(self):
        _babase.import_character = import_character
        _babase.export_character = export_character
        _babase.spaz_to_json = spaz_to_json
        character_files = os.listdir(CUSTOM_CHARACTERS)
        for character_file in character_files:
            if character_file.lower().endswith(".json"):
                name, _ = os.path.splitext(character_file)
                with open(os.path.join(CUSTOM_CHARACTERS, character_file), "r") as fin:
                    character = json.load(fin)
                register_character_json(name, character)
