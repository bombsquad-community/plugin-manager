
# ba_meta require api 7
from __future__ import annotations
from typing import TYPE_CHECKING

import ba
from ba import _map
from bastd.gameutils import SharedObjects
from bastd.maps import *

if TYPE_CHECKING:
    pass


class ForestMapData():
    points = {}
    boxes = {}

    boxes['area_of_interest_bounds'] = (
        (0.0, 1.185751251, 0.4326226188)
        + (0.0, 0.0, 0.0)
        + (29.8180273, 11.57249038, 18.89134176)
    )
    boxes['edge_box'] = (
        (-0.103873591, 0.4133341891, 0.4294651013)
        + (0.0, 0.0, 0.0)
        + (22.48295719, 1.290242794, 8.990252454)
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
    boxes['map_bounds'] = (
        (0.0, 1.185751251, 0.4326226188)
        + (0.0, 0.0, 0.0)
        + (42.09506485, 22.81173179, 29.76723155)
    )
    points['flag_default'] = (-2.5, -3.0, -2.0)
    points['powerup_spawn1'] = (-6.0, -2.6, -1.25)
    points['powerup_spawn2'] = (1.0, -2.6, -1.25)
    points['spawn1'] = (-10.0, -2.0, -2.0) + (0.5, 1.0, 3.2)
    points['spawn2'] = (5.0, -2.0, -2.0) + (0.5, 1.0, 3.2)


class ForestMap(ba.Map):

    defs = ForestMapData()
    name = 'Forest'

    @classmethod
    def get_play_types(cls) -> list[str]:
        return ['melee', 'keep_away']

    @classmethod
    def get_preview_texture_name(cls) -> list[str]:
        return 'natureBackgroundColor'

    @classmethod
    def on_preload(cls) -> any:
        data: dict[str, any] = {
            'model': ba.getmodel('natureBackground'),
            'tex': ba.gettexture('natureBackgroundColor'),
            'collide_model': ba.getcollidemodel('natureBackgroundCollide'),
            'bgmodel': ba.getmodel('thePadBG'),
            'bgtex': ba.gettexture('menuBG')
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()

        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'model': self.preloaddata['model'],
                'color_texture': self.preloaddata['tex'],
                'collide_model': self.preloaddata['collide_model'],
                'materials': [shared.footing_material]
            }
        )
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['bgmodel'],
                'lighting': False,
                'shadow': True,
                'color_texture': self.preloaddata['bgtex']
            }
        )

        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.0, 1.10, 1.15)
        gnode.ambient_color = (0.9, 1.3, 1.1)
        gnode.shadow_ortho = False
        gnode.vignette_outer = (0.76, 0.76, 0.76)
        gnode.vignette_inner = (0.95, 0.95, 0.99)

    def is_point_near_edge(self,
                           point: ba.Vec3,
                           running: bool = False) -> bool:
        xpos = point.x
        zpos = point.z
        x_adj = xpos * 0.125
        z_adj = (zpos + 3.7) * 0.2
        if running:
            x_adj *= 1.4
            z_adj *= 1.4
        return x_adj * x_adj + z_adj * z_adj > 1.0


# ba_meta export plugin
class EnableMe(ba.Plugin):
    _map.register_map(ForestMap)
