# ba_meta require api 9

plugman = dict(
    plugin_name="forest_v2",
    description="A better looking land with some trees\nNew mini games added so you can play more on this update forest",
    external_url="",
    authors=[
        {"name": "Startingbat", "email": "", "discord": "startingbat"},
    ],
    version="1.0.0",
)

from __future__ import annotations
from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1 import _map
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.maps import *

if TYPE_CHECKING:
    pass


class ForestMapData:
    points = {}
    boxes = {}

    boxes['area_of_interest_bounds'] = (
        (0.0, 1.185751251, 0.4326226188) + (0.0, 0.0, 0.0) + (29.8180273, 11.57249038, 18.89134176)
    )
    boxes['edge_box'] = (
        (-0.103873591, 0.4133341891, 0.4294651013)
        + (0.0, 0.0, 0.0)
        + (22.48295719, 1.290242794, 8.990252454)
    )
    boxes['map_bounds'] = (
        (0.0, 1.185751251, 0.4326226188) + (0.0, 0.0, 0.0) + (42.09506485, 22.81173179, 29.76723155)
    )
    points['ffa_spawn1'] = (-2.0, -2.0, -4.373674593) + (
        8.895057015,
        1.0,
        0.444350722,
    )
    points['ffa_spawn2'] = (-2.0, -2.0, 2.076288941) + (
        8.895057015,
        1.0,
        0.444350722,
    )

    points['flag_default'] = (-2.5, -3.0, -2.0)
    points['powerup_spawn1'] = (-6.0, -2.6, -1.25)
    points['powerup_spawn2'] = (1.0, -2.6, -1.25)
    points['spawn1'] = (-10.0, -2.0, -2.0) + (0.5, 1.0, 3.2)
    points['spawn2'] = (5.0, -2.0, -2.0) + (0.5, 1.0, 3.2)
    points['race_point1'] = (0.5901776337, -2.6, 1.543598704) + (
        0.2824957007,
        3.950514538,
        2.292534365,
    )
    points['race_point2'] = (4.7526567, -2.6, 1.09551316) + (
        0.2824957007,
        3.950514538,
        2.392880724,
    )
    points['race_point3'] = (7.450800117, -2.6, -2.248040576) + (
        2.167067932,
        3.950514538,
        0.2574992262,
    )
    points['race_point4'] = (5.064768438, -2.6, -5.820463576) + (
        0.2824957007,
        3.950514538,
        2.392880724,
    )
    points['race_point5'] = (0.5901776337, -2.6, -6.165424036) + (
        0.2824957007,
        3.950514538,
        2.156382533,
    )
    points['race_point6'] = (-3.057459058, -2.6, -6.114179652) + (
        0.2824957007,
        3.950514538,
        2.323773344,
    )
    points['race_point7'] = (-5.814316926, -2.6, -2.248040576) + (
        2.0364457,
        3.950514538,
        0.2574992262,
    )
    points['race_point8'] = (-2.958397223, -2.6, 1.360005754) + (
        0.2824957007,
        3.950514538,
        2.529692681,
    )
    points['flag1'] = (-10.25842, -2.6673191, -2.2210996)
    points['flag2'] = (5.2464933, -3.2587945, -1.6802032)
    points['tnt1'] = (-0.08421587483, 0.9515026107, -0.7762602271)


class ForestMap(bs.Map):

    defs = ForestMapData()
    name = 'Forest'

    @classmethod
    def get_play_types(cls) -> list[str]:
        return ['melee', 'keep_away', 'team_flag', 'race']

    @classmethod
    def get_preview_texture_name(cls) -> list[str]:
        return 'natureBackgroundColor'

    @classmethod
    def on_preload(cls) -> any:
        data: dict[str, any] = {
            'mesh': bs.getmesh('natureBackground'),
            'tex': bs.gettexture('natureBackgroundColor'),
            'mesh2': bs.getmesh('trees'),
            'tex2': bs.gettexture('treesColor'),
            'collision_mesh': bs.getcollisionmesh('natureBackgroundCollide'),
            'mesh_bg': bs.getmesh('thePadBG'),
            'mesh_bg_tex': bs.gettexture('black'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()

        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'collision_mesh': self.preloaddata['collision_mesh'],
                'materials': [shared.footing_material],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bg'],
                'lighting': False,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        self.trees = bs.newnode(
            'prop',
            attrs={
                'mesh': self.preloaddata['mesh2'],
                'body': 'box',
                'mesh_scale': 0.6,
                'density': 999999,  # Very high density to make it immovable
                'damping': 999999,
                'position': (-2, 9, -5),
                'color_texture': self.preloaddata['tex2'],
            },
        )

        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.0, 1.10, 1.15)
        gnode.ambient_color = (0.9, 1.3, 1.1)
        gnode.shadow_ortho = True
        gnode.shadow_offset = (0, 0, -5.0)
        gnode.vignette_outer = (0.76, 0.76, 0.76)
        gnode.vignette_inner = (0.95, 0.95, 0.99)

    def is_point_near_edge(self, point: bs.Vec3, running: bool = False) -> bool:
        xpos = point.x
        zpos = point.z
        x_adj = xpos * 0.125
        z_adj = (zpos + 3.7) * 0.2
        if running:
            x_adj *= 1.4
            z_adj *= 1.4
        return x_adj * x_adj + z_adj * z_adj > 1.0


# ba_meta export plugin
class StartingbatYT(bs.Plugin):
    _map.register_map(ForestMap)
