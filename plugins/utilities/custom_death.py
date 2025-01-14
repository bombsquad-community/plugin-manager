# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
from bascenev1lib.actor.spaz import Spaz

if TYPE_CHECKING:
    from typing import Any


Spaz.oldhandlemessage = Spaz.handlemessage


def handlemessage(self, msg: Any) -> Any:
    if isinstance(msg, bs.DieMessage):
        if self.node:
            self.node.color_texture = bs.gettexture('bonesColor')
            self.node.color_mask_texture = bs.gettexture('bonesColorMask')
            self.node.head_mesh = bs.getmesh('bonesHead')
            self.node.torso_mesh = bs.getmesh('bonesTorso')
            self.node.pelvis_mesh = bs.getmesh('bonesPelvis')
            self.node.upper_arm_mesh = bs.getmesh('bonesUpperArm')
            self.node.forearm_mesh = bs.getmesh('bonesForeArm')
            self.node.hand_mesh = bs.getmesh('bonesHand')
            self.node.upper_leg_mesh = bs.getmesh('bonesUpperLeg')
            self.node.lower_leg_mesh = bs.getmesh('bonesLowerLeg')
            self.node.toes_mesh = bs.getmesh('bonesToes')
            self.node.style = 'bones'
        self.oldhandlemessage(msg)
    else:
        return self.oldhandlemessage(msg)


# ba_meta export plugin
class CustomDeath(babase.Plugin):
    Spaz.handlemessage = handlemessage
