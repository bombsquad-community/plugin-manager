# ba_meta require api 7
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.actor.spaz import Spaz

if TYPE_CHECKING:
    from typing import Any


Spaz.oldhandlemessage = Spaz.handlemessage
def handlemessage(self, msg: Any) -> Any:
    if isinstance(msg, ba.DieMessage):
        if self.node:
            self.node.color_texture = ba.gettexture('bonesColor')
            self.node.color_mask_texture = ba.gettexture('bonesColorMask')
            self.node.head_model = ba.getmodel('bonesHead')
            self.node.torso_model = ba.getmodel('bonesTorso')
            self.node.pelvis_model = ba.getmodel('bonesPelvis')
            self.node.upper_arm_model = ba.getmodel('bonesUpperArm')
            self.node.forearm_model = ba.getmodel('bonesForeArm')
            self.node.hand_model = ba.getmodel('bonesHand')
            self.node.upper_leg_model = ba.getmodel('bonesUpperLeg')
            self.node.lower_leg_model = ba.getmodel('bonesLowerLeg')
            self.node.toes_model = ba.getmodel('bonesToes')
            self.node.style = 'bones'
        self.oldhandlemessage(msg)
    else:
        return self.oldhandlemessage(msg)


# ba_meta export plugin
class CustomDeath(ba.Plugin):
    Spaz.handlemessage = handlemessage
