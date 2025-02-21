# Ported to api 8 by brostos using baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs
from bascenev1lib.actor.spazbot import SpazBot
from bascenev1lib.actor.powerupbox import PowerupBoxFactory

if TYPE_CHECKING:
    pass


# ba_meta export plugin
class BotsCanAcceptPowerupsPlugin(babase.Plugin):
    def on_app_running(self) -> None:
        SpazBot.oldinit = SpazBot.__init__

        def __init__(self) -> None:
            self.oldinit()
            pam = PowerupBoxFactory.get().powerup_accept_material
            materials = self.node.materials
            materials = list(materials)
            materials.append(pam)
            materials = tuple(materials)
            self.node.materials = materials
            roller_materials = self.node.roller_materials
            roller_materials = list(roller_materials)
            roller_materials.append(pam)
            roller_materials = tuple(roller_materials)
            self.node.roller_materials = roller_materials
            extras_material = self.node.extras_material
            extras_material = list(extras_material)
            extras_material.append(pam)
            extras_material = tuple(extras_material)
            self.node.extras_material = extras_material
        SpazBot.__init__ = __init__
