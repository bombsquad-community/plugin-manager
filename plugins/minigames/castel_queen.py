# Released under the MIT License. See LICENSE for details.
#
"""
CastelQueen - Carry the Queen alone or with your team.
Author:  Mr.Smoothy
Discord: https://discord.gg/ucyaesh
Youtube: https://www.youtube.com/c/HeySmoothy
Website: https://bombsquad-community.web.app
Github:  https://github.com/bombsquad-community
"""
# ba_meta require api 7
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import _ba

from bastd.gameutils import SharedObjects
from bastd.actor.playerspaz import PlayerSpaz
from bastd.game.keepaway import KeepAwayGame, FlagState, Player
from bastd.actor import spaz
if TYPE_CHECKING:
    from typing import Any, Sequence, Dict, Type, List, Optional, Union

# ba_meta export game


class ChooseQueen(KeepAwayGame):
    name = 'FCUK The Queen'
    description = 'Carry the queen for a set length of time'

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return issubclass(sessiontype, ba.DualTeamSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ['Creative Thoughts']

    def get_instance_description(self) -> str | Sequence:
        return 'FCUK the queen for ${ARG1} seconds.', self._hold_time

    def get_instance_description_short(self) -> str | Sequence:
        return 'FCUK the queen for ${ARG1} seconds', self._hold_time

    def __init__(self, settings: dict):
        super().__init__(settings)
        shared = SharedObjects.get()
        self.lifts = {}
        self._room_wall_material = ba.Material()
        self._room_wall_material.add_actions(
            actions=(
                ('modify_part_collision', 'collide', False),
                ('modify_part_collision', 'physical', False)
            ))
        self._queen_material = ba.Material()
        self._queen_material.add_actions(
            conditions=('they_have_material', self._room_wall_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True)
            ))
        self._queen_material.add_actions(
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True)
            ))
        self._room_wall_material.add_actions(
            conditions=('they_have_material', self._queen_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True)
            ))
        self._real_wall_material = ba.Material()
        self._real_wall_material.add_actions(
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True)
            ))

        self._real_wall_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True)

            ))

    def on_begin(self):
        ba.getactivity().globalsnode.happy_thoughts_mode = True
        super().on_begin()
        self.make_map()

    def _spawn_flag(self) -> None:
        ba.playsound(self._swipsound)
        self._flash_flag_spawn()
        assert self._flag_spawn_pos is not None
        shared = SharedObjects.get()
        self._flag = spaz.Spaz((0, 0, 0), character="Pixel").autoretain()
        self._flag.handlemessage(ba.StandMessage((0, 14.63, -5.52), 93))
        self._flag.node.hold_position_pressed = True
        self._flag.node.materials = (self._queen_material, shared.object_material)
        # self._flag.node.extras_material= tuple(list(self._flag.node.extras_material).append(self._queen_materia))
        self._flag.hitpoints = 5000
        self._flag.hitpoints_max = 5000

        self._flag_state = FlagState.NEW
        self._flag_light = ba.newnode(
            'light',
            owner=self._flag.node,
            attrs={'intensity': 0.2, 'radius': 0.3, 'color': (0.2, 0.2, 0.2)},
        )
        assert self._flag.node
        self._flag.node.connectattr('position', self._flag_light, 'position')
        self._update_flag_state()

    def _update_flag_state(self) -> None:
        if not self._flag.node.exists():
            self._spawn_flag()
        for team in self.teams:
            team.holdingflag = False
        self._holding_players = []
        for player in self.players:
            holdingflag = False
            try:
                assert isinstance(player.actor, (PlayerSpaz, type(None)))
                if (
                    player.actor
                    and player.actor.node
                    and player.actor.node.hold_node
                ):
                    holdingflag = (
                        player.actor.node.hold_node == self._flag.node
                    )
            except Exception:
                ba.print_exception('Error checking hold flag.')
            if holdingflag:
                self._holding_players.append(player)
                player.team.holdingflag = True

        holdingteams = set(t for t in self.teams if t.holdingflag)
        prevstate = self._flag_state
        assert self._flag is not None
        assert self._flag_light
        assert self._flag.node
        if len(holdingteams) > 1:
            self._flag_state = FlagState.CONTESTED
            self._scoring_team = None
        elif len(holdingteams) == 1:
            holdingteam = list(holdingteams)[0]
            self._flag_state = FlagState.HELD
            self._scoring_team = holdingteam
        else:
            self._flag_state = FlagState.UNCONTESTED
            self._scoring_team = None

        if self._flag_state != prevstate:
            ba.playsound(self._swipsound)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            self.respawn_player(msg.getplayer(Player))
        elif isinstance(msg, (ba.PickedUpMessage, ba.DroppedMessage)):
            self._update_flag_state()
        else:
            super().handlemessage(msg)

    def make_map(self):
        shared = SharedObjects.get()
        _ba.get_foreground_host_activity()._map.leftwall.materials = [
            shared.footing_material, self._real_wall_material]

        _ba.get_foreground_host_activity()._map.rightwall.materials = [
            shared.footing_material, self._real_wall_material]

        _ba.get_foreground_host_activity()._map.topwall.materials = [
            shared.footing_material, self._real_wall_material]

        self.floorwall1 = ba.newnode('region', attrs={'position': (-10, 5, -5.52), 'scale':
                                                      (15, 0.2, 2), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})
        self.floorwall2 = ba.newnode('region', attrs={'position': (10, 5, -5.52), 'scale': (
            15, 0.2, 2), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})

        self.wall1 = ba.newnode('region', attrs={'position': (0, 11, -6.90), 'scale': (
            35.4, 20, 1), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})
        self.wall2 = ba.newnode('region', attrs={'position': (0, 11, -4.14), 'scale': (
            35.4, 20, 1), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})

        ba.newnode('locator', attrs={'shape': 'box', 'position': (-10, 5, -5.52), 'color': (
            0, 0, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (15, 0.2, 2)})

        ba.newnode('locator', attrs={'shape': 'box', 'position': (10, 5, -5.52), 'color': (
            0, 0, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (15, 0.2, 2)})

        self.create_static_step(0, 14.29)
        #    upper right
        self.create_static_step(11, 16)
        self.create_slope(8, 16, False)
        self.create_static_step(3, 18)

        # lower right
        self.create_static_step(11, 12)
        self.create_slope(6, 10, True)
        self.create_static_step(3, 10)

        #    upper left
        self.create_static_step(-11, 16)
        self.create_slope(-8, 16, True)
        self.create_static_step(-3, 18)

        # lower left
        self.create_static_step(-11, 12)
        self.create_slope(-6, 10, False)
        self.create_static_step(-3, 10)

        # create queen personal room
        self.room_wall_left = ba.newnode('region', attrs={'position': (-3.633, 16.63, -5.52), 'scale':
                                                          (2, 4, 5), 'type': 'box', 'materials': [shared.footing_material, self._room_wall_material]})
        self.room_wall_right = ba.newnode('region', attrs={'position': (3.533, 16.63, -5.52), 'scale':
                                                           (2, 4, 5), 'type': 'box', 'materials': [shared.footing_material, self._room_wall_material]})

    def create_static_step(self, x, y):
        shared = SharedObjects.get()
        ba.newnode('region', attrs={'position': (x, y, -5.52), 'scale': (5.5, 0.1, 6),
                   'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})
        ba.newnode('locator', attrs={'shape': 'box', 'position': (x, y,  -5.52), 'color': (
            1, 1, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (5.5, 0.1, 2)})

    def create_slope(self, x, y, backslash):
        shared = SharedObjects.get()

        for _ in range(0, 21):
            ba.newnode('region', attrs={'position': (x, y, -5.52), 'scale': (0.2, 0.1, 6),
                       'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})
            ba.newnode('locator', attrs={'shape': 'box', 'position': (x, y,  -5.52), 'color': (
                1, 1, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (0.2, 0.1, 2)})
            if backslash:
                x = x + 0.1
                y = y + 0.1
            else:
                x = x - 0.1
                y = y + 0.1


class mapdefs:
    points = {}
    # noinspection PyDictCreation
    boxes = {}
    boxes['area_of_interest_bounds'] = (-1.045859963, 12.67722855,
                                        -5.401537075) + (0.0, 0.0, 0.0) + (
                                            42.46156851, 20.94044653, 0.6931564611)
    points['ffa_spawn1'] = (-9.295167711, 8.010664315,
                            -5.44451005) + (1.555840357, 1.453808816, 0.1165648888)
    points['ffa_spawn2'] = (7.484707127, 8.172681752, -5.614479365) + (
        1.553861796, 1.453808816, 0.04419853907)
    points['ffa_spawn3'] = (9.55724115, 11.30789446, -5.614479365) + (
        1.337925849, 1.453808816, 0.04419853907)
    points['ffa_spawn4'] = (-11.55747023, 10.99170684, -5.614479365) + (
        1.337925849, 1.453808816, 0.04419853907)
    points['ffa_spawn5'] = (-1.878892369, 9.46490571, -5.614479365) + (
        1.337925849, 1.453808816, 0.04419853907)
    points['ffa_spawn6'] = (-0.4912812943, 5.077006397, -5.521672101) + (
        1.878332089, 1.453808816, 0.007578097856)
    points['flag1'] = (-11.75152479, 8.057427485, -5.52)
    points['flag2'] = (9.840909039, 8.188634282, -5.52)
    points['flag3'] = (-0.2195258696, 5.010273907, -5.52)
    points['flag4'] = (-0.04605809154, 12.73369108, -5.52)
    points['flag_default'] = (-0.04201942896, 12.72374492, -5.52)
    boxes['map_bounds'] = (-0.8748348681, 9.212941713, -5.729538885) + (
        0.0, 0.0, 0.0) + (42.09666006, 26.19950145, 7.89541168)
    points['powerup_spawn1'] = (1.160232442, 6.745963662, -5.469115985)
    points['powerup_spawn2'] = (-1.899700206, 10.56447241, -5.505721177)
    points['powerup_spawn3'] = (10.56098871, 12.25165669, -5.576232453)
    points['powerup_spawn4'] = (-12.33530337, 12.25165669, -5.576232453)
    points['spawn1'] = (-9.295167711, 8.010664315,
                        -5.44451005) + (1.555840357, 1.453808816, 0.1165648888)
    points['spawn2'] = (7.484707127, 8.172681752,
                        -5.614479365) + (1.553861796, 1.453808816, 0.04419853907)
    points['spawn_by_flag1'] = (-9.295167711, 8.010664315, -5.44451005) + (
        1.555840357, 1.453808816, 0.1165648888)
    points['spawn_by_flag2'] = (7.484707127, 8.172681752, -5.614479365) + (
        1.553861796, 1.453808816, 0.04419853907)
    points['spawn_by_flag3'] = (-1.45994593, 5.038762459, -5.535288724) + (
        0.9516389866, 0.6666414677, 0.08607244075)
    points['spawn_by_flag4'] = (0.4932087091, 12.74493212, -5.598987003) + (
        0.5245740665, 0.5245740665, 0.01941146064)


class CreativeThoughts(ba.Map):
    """Freaking map by smoothy."""

    defs = mapdefs

    name = 'Creative Thoughts'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return [
            'melee', 'keep_away', 'team_flag'
        ]

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'alwaysLandPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('alwaysLandLevel'),
            'bottom_model': ba.getmodel('alwaysLandLevelBottom'),
            'bgmodel': ba.getmodel('alwaysLandBG'),
            'collide_model': ba.getcollidemodel('alwaysLandLevelCollide'),
            'tex': ba.gettexture('alwaysLandLevelColor'),
            'bgtex': ba.gettexture('alwaysLandBGColor'),
            'vr_fill_mound_model': ba.getmodel('alwaysLandVRFillMound'),
            'vr_fill_mound_tex': ba.gettexture('vrFillMound')
        }
        return data

    @classmethod
    def get_music_type(cls) -> ba.MusicType:
        return ba.MusicType.FLYING

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, -3.7, 2.5))
        shared = SharedObjects.get()
        self._fake_wall_material = ba.Material()
        self._real_wall_material = ba.Material()
        self._fake_wall_material.add_actions(
            conditions=(('they_are_younger_than', 9000), 'and',
                        ('they_have_material', shared.player_material)),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True)

            ))
        self._real_wall_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True)

            ))
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['bgmodel'],
                'lighting': False,
                'background': True,
                'color_texture': ba.gettexture("rampageBGColor")
            })

        self.leftwall = ba.newnode('region', attrs={'position': (-17.75152479, 13, -5.52), 'scale': (
            0.1, 15.5, 2), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})
        self.rightwall = ba.newnode('region', attrs={'position': (17.75, 13, -5.52), 'scale': (
            0.1, 15.5, 2), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})
        self.topwall = ba.newnode('region', attrs={'position': (0, 21.0, -5.52), 'scale': (
            35.4, 0.2, 2), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})
        ba.newnode('locator', attrs={'shape': 'box', 'position': (-17.75152479, 13, -5.52), 'color': (
            0, 0, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (0.1, 15.5, 2)})
        ba.newnode('locator', attrs={'shape': 'box', 'position': (17.75, 13, -5.52), 'color': (
            0, 0, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (0.1, 15.5, 2)})
        ba.newnode('locator', attrs={'shape': 'box', 'position': (0, 21.0, -5.52), 'color': (
            0, 0, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (35.4, 0.2, 2)})

        gnode = ba.getactivity().globalsnode
        gnode.happy_thoughts_mode = True
        gnode.shadow_offset = (0.0, 8.0, 5.0)
        gnode.tint = (1.3, 1.23, 1.0)
        gnode.ambient_color = (1.3, 1.23, 1.0)
        gnode.vignette_outer = (0.64, 0.59, 0.69)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        gnode.vr_near_clip = 1.0
        self.is_flying = True

        # throw out some tips on flying
        txt = ba.newnode('text',
                         attrs={
                             'text': ba.Lstr(resource='pressJumpToFlyText'),
                             'scale': 1.2,
                             'maxwidth': 800,
                             'position': (0, 200),
                             'shadow': 0.5,
                             'flatness': 0.5,
                             'h_align': 'center',
                             'v_attach': 'bottom'
                         })
        cmb = ba.newnode('combine',
                         owner=txt,
                         attrs={
                             'size': 4,
                             'input0': 0.3,
                             'input1': 0.9,
                             'input2': 0.0
                         })
        ba.animate(cmb, 'input3', {3.0: 0, 4.0: 1, 9.0: 1, 10.0: 0})
        cmb.connectattr('output', txt, 'color')
        ba.timer(10.0, txt.delete)


try:
    ba._map.register_map(CreativeThoughts)
except:
    pass
