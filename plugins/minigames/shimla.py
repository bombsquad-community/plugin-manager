# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# Released under the MIT License. See LICENSE for details.
#
"""DeathMatch game and support classes."""

# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.game.deathmatch import DeathMatchGame, Player
from bascenev1lib.gameutils import SharedObjects
if TYPE_CHECKING:
    from typing import Any, Sequence, Dict, Type, List, Optional, Union

# ba_meta export bascenev1.GameActivity


class ShimlaGame(DeathMatchGame):
    name = 'Shimla'

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return ['Creative Thoughts']

    def __init__(self, settings: dict):
        super().__init__(settings)
        shared = SharedObjects.get()
        self.lifts = {}
        self._real_wall_material = bs.Material()
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
        self._lift_material = bs.Material()
        self._lift_material.add_actions(

            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True)

            ))
        self._lift_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(('call', 'at_connect', self._handle_lift),),
        )
        self._lift_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(('call', 'at_disconnect', self._handle_lift_disconnect),),
        )

    def on_begin(self):
        bs.getactivity().globalsnode.happy_thoughts_mode = False
        super().on_begin()

        self.make_map()
        bs.timer(2, self.disable_fly)

    def disable_fly(self):
        activity = bs.get_foreground_host_activity()

        for players in activity.players:
            players.actor.node.fly = False

    def spawn_player_spaz(
        self,
        player: Player,
        position: Sequence[float] | None = None,
        angle: float | None = None,
    ) -> PlayerSpaz:
        """Intercept new spazzes and add our team material for them."""
        spaz = super().spawn_player_spaz(player, position, angle)

        spaz.connect_controls_to_player(enable_punch=True,
                                        enable_bomb=True,
                                        enable_pickup=True,
                                        enable_fly=False,
                                        enable_jump=True)
        spaz.fly = False
        return spaz

    def make_map(self):
        shared = SharedObjects.get()
        bs.get_foreground_host_activity()._map.leftwall.materials = [
            shared.footing_material, self._real_wall_material]

        bs.get_foreground_host_activity()._map.rightwall.materials = [
            shared.footing_material, self._real_wall_material]

        bs.get_foreground_host_activity()._map.topwall.materials = [
            shared.footing_material, self._real_wall_material]

        self.floorwall1 = bs.newnode('region', attrs={'position': (-10, 5, -5.52), 'scale':
                                                      (15, 0.2, 2), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})
        self.floorwall2 = bs.newnode('region', attrs={'position': (10, 5, -5.52), 'scale': (
            15, 0.2, 2), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})

        self.wall1 = bs.newnode('region', attrs={'position': (0, 11, -6.90), 'scale': (
            35.4, 20, 1), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})
        self.wall2 = bs.newnode('region', attrs={'position': (0, 11, -4.14), 'scale': (
            35.4, 20, 1), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})

        bs.newnode('locator', attrs={'shape': 'box', 'position': (-10, 5, -5.52), 'color': (
            0, 0, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (15, 0.2, 2)})

        bs.newnode('locator', attrs={'shape': 'box', 'position': (10, 5, -5.52), 'color': (
            0, 0, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (15, 0.2, 2)})
        self.create_lift(-16.65, 8)

        self.create_lift(16.65, 8)

        self.create_static_step(0, 18.29)
        self.create_static_step(0, 7)

        self.create_static_step(13, 17)
        self.create_static_step(-13, 17)
        self.create_slope(8, 15, True)
        self.create_slope(-8, 15, False)
        self.create_static_step(5, 15)
        self.create_static_step(-5, 15)

        self.create_static_step(13, 12)
        self.create_static_step(-13, 12)
        self.create_slope(8, 10, True)
        self.create_slope(-8, 10, False)
        self.create_static_step(5, 10)
        self.create_static_step(-5, 10)

    def create_static_step(self, x, y):

        shared = SharedObjects.get()

        bs.newnode('region', attrs={'position': (x, y, -5.52), 'scale': (5.5, 0.1, 6),
                   'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})
        bs.newnode('locator', attrs={'shape': 'box', 'position': (x, y,  -5.52), 'color': (
            1, 1, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (5.5, 0.1, 2)})

    def create_lift(self, x, y):
        shared = SharedObjects.get()
        color = (0.7, 0.6, 0.5)

        floor = bs.newnode('region', attrs={'position': (x, y, -5.52), 'scale': (
            1.8, 0.1, 2), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material, self._lift_material]})

        cleaner = bs.newnode('region', attrs={'position': (x, y, -5.52), 'scale': (
            2, 0.3, 2), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})

        lift = bs.newnode('locator', attrs={'shape': 'box', 'position': (
            x, y,  -5.52), 'color': color, 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (1.8, 3.7, 2)})

        _tcombine = bs.newnode('combine',
                               owner=floor,
                               attrs={
                                   'input0': x,
                                   'input2': -5.5,
                                   'size': 3
                               })
        mnode = bs.newnode('math',
                           owner=lift,
                           attrs={
                               'input1': (0, 2, 0),
                               'operation': 'add'
                           })
        _tcombine.connectattr('output', mnode, 'input2')

        _cleaner_combine = bs.newnode('combine',
                                      owner=cleaner,
                                      attrs={
                                          'input1': 5.6,
                                          'input2': -5.5,
                                          'size': 3
                                      })
        _cleaner_combine.connectattr('output', cleaner, 'position')
        bs.animate(_tcombine, 'input1', {
            0: 5.1,
        })
        bs.animate(_cleaner_combine, 'input0', {
            0: -19 if x < 0 else 19,
        })

        _tcombine.connectattr('output', floor, 'position')
        mnode.connectattr('output', lift, 'position')
        self.lifts[floor] = {"state": "origin", "lift": _tcombine,
                             "cleaner": _cleaner_combine, 'leftLift': x < 0}

    def _handle_lift(self):
        region = bs.getcollision().sourcenode
        lift = self.lifts[region]

        def clean(lift):
            bs.animate(lift["cleaner"], 'input0', {
                0: -19 if lift["leftLift"] else 19,
                2: -16 if lift["leftLift"] else 16,
                4.3: -19 if lift["leftLift"] else 19
            })
        if lift["state"] == "origin":
            lift["state"] = "transition"
            bs.animate(lift["lift"], 'input1', {
                0: 5.1,
                1.3: 5.1,
                6: 5+12,
                9: 5+12,
                15: 5.1
            })
            bs.timer(16, babase.Call(lambda lift: lift.update({'state': 'end'}), lift))
            bs.timer(12, babase.Call(clean, lift))

    def _handle_lift_disconnect(self):
        region = bs.getcollision().sourcenode
        lift = self.lifts[region]
        if lift["state"] == 'end':
            lift["state"] = "origin"

    def create_slope(self, x, y, backslash):
        shared = SharedObjects.get()

        for i in range(0, 21):
            bs.newnode('region', attrs={'position': (x, y, -5.52), 'scale': (0.2, 0.1, 6),
                       'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})
            bs.newnode('locator', attrs={'shape': 'box', 'position': (x, y,  -5.52), 'color': (
                1, 1, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (0.2, 0.1, 2)})
            if backslash:
                x = x+0.1
                y = y+0.1
            else:
                x = x-0.1
                y = y+0.1


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


class CreativeThoughts(bs.Map):
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
            'mesh': bs.getmesh('alwaysLandLevel'),
            'bottom_mesh': bs.getmesh('alwaysLandLevelBottom'),
            'bgmesh': bs.getmesh('alwaysLandBG'),
            'collision_mesh': bs.getcollisionmesh('alwaysLandLevelCollide'),
            'tex': bs.gettexture('alwaysLandLevelColor'),
            'bgtex': bs.gettexture('alwaysLandBGColor'),
            'vr_fill_mound_mesh': bs.getmesh('alwaysLandVRFillMound'),
            'vr_fill_mound_tex': bs.gettexture('vrFillMound')
        }
        return data

    @classmethod
    def get_music_type(cls) -> bs.MusicType:
        return bs.MusicType.FLYING

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, -3.7, 2.5))
        shared = SharedObjects.get()
        self._fake_wall_material = bs.Material()
        self._real_wall_material = bs.Material()
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
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': bs.gettexture("rampageBGColor")
            })

        self.leftwall = bs.newnode('region', attrs={'position': (-17.75152479, 13, -5.52), 'scale': (
            0.1, 15.5, 2), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})
        self.rightwall = bs.newnode('region', attrs={'position': (17.75, 13, -5.52), 'scale': (
            0.1, 15.5, 2), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})
        self.topwall = bs.newnode('region', attrs={'position': (0, 21.0, -5.52), 'scale': (
            35.4, 0.2, 2), 'type': 'box', 'materials': [shared.footing_material, self._real_wall_material]})
        bs.newnode('locator', attrs={'shape': 'box', 'position': (-17.75152479, 13, -5.52), 'color': (
            0, 0, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (0.1, 15.5, 2)})
        bs.newnode('locator', attrs={'shape': 'box', 'position': (17.75, 13, -5.52), 'color': (
            0, 0, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (0.1, 15.5, 2)})
        bs.newnode('locator', attrs={'shape': 'box', 'position': (0, 21.0, -5.52), 'color': (
            0, 0, 0), 'opacity': 1, 'draw_beauty': True, 'additive': False, 'size': (35.4, 0.2, 2)})

        gnode = bs.getactivity().globalsnode
        gnode.happy_thoughts_mode = True
        gnode.shadow_offset = (0.0, 8.0, 5.0)
        gnode.tint = (1.3, 1.23, 1.0)
        gnode.ambient_color = (1.3, 1.23, 1.0)
        gnode.vignette_outer = (0.64, 0.59, 0.69)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        gnode.vr_near_clip = 1.0
        self.is_flying = True

        # throw out some tips on flying
        txt = bs.newnode('text',
                         attrs={
                             'text': babase.Lstr(resource='pressJumpToFlyText'),
                             'scale': 1.2,
                             'maxwidth': 800,
                             'position': (0, 200),
                             'shadow': 0.5,
                             'flatness': 0.5,
                             'h_align': 'center',
                             'v_attach': 'bottom'
                         })
        cmb = bs.newnode('combine',
                         owner=txt,
                         attrs={
                             'size': 4,
                             'input0': 0.3,
                             'input1': 0.9,
                             'input2': 0.0
                         })
        bs.animate(cmb, 'input3', {3.0: 0, 4.0: 1, 9.0: 1, 10.0: 0})
        cmb.connectattr('output', txt, 'color')
        bs.timer(10.0, txt.delete)


try:
    bs._map.register_map(CreativeThoughts)
except:
    pass
