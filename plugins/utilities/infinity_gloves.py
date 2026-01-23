# ba_meta require api 9
# mod actualizado por: SOMBR1
# mod updated by: SOMBR1
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import bascenev1lib
import babase
import bascenev1 as bs
from bascenev1lib.actor import playerspaz

if TYPE_CHECKING:
    from typing import Sequence

plugman = dict(
    plugin_name="infinity_gloves",
    description="this plugin give you infinity gloves (isn't mine)",
    external_url="",
    authors=[
        {"name": "SOMBR1 & ATD", "email": "anasdhaoidi001@gmail.com", "discord": ""},
    ],
    version="1.0.0",
)


class NewPlayerSpaz(playerspaz.PlayerSpaz):

    def __init__(self,
                 player: bascenev1.Player,
                 color: Sequence[float] = (1.0, 1.0, 1.0),
                 highlight: Sequence[float] = (0.5, 0.5, 0.5),
                 character: str = 'Spaz',
                 powerups_expire: bool = True):
        super().__init__(player=player,
                         color=color,
                         highlight=highlight,
                         character=character,
                         powerups_expire=powerups_expire)
        self.equip_boxing_gloves()

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PowerupMessage):
            if msg.poweruptype == 'punch':
                self.equip_boxing_gloves()
                self.node.handlemessage('flash')
                if msg.sourcenode:
                    msg.sourcenode.handlemessage(bs.PowerupAcceptMessage())
            else:
                return super().handlemessage(msg)
        else:
            return super().handlemessage(msg)


# ba_meta export babase.Plugin
class InfinityGlovesPlugin(babase.Plugin):
    playerspaz.PlayerSpaz = NewPlayerSpaz
