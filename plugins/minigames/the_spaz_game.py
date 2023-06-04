
# ba_meta require api 7
"""
TheSpazGame - Mini game where all characters looks identical , identify enemies and kill them.
Author:  Mr.Smoothy
Discord: https://discord.gg/ucyaesh
Youtube: https://www.youtube.com/c/HeySmoothy
Website: https://bombsquad-community.web.app
Github:  https://github.com/bombsquad-community
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.game.elimination import EliminationGame, Player
from bastd.actor.spazfactory import SpazFactory
import random

if TYPE_CHECKING:
    from typing import Any, Sequence


CHARACTER = 'Spaz'

# ba_meta export game


class TheSpazGame(EliminationGame):
    name = 'TheSpazGame'
    description = 'Enemy Spaz AmongUs. Kill them all'
    scoreconfig = ba.ScoreConfig(
        label='Survived', scoretype=ba.ScoreType.SECONDS, none_is_winner=True
    )

    announce_player_deaths = False

    allow_mid_activity_joins = False

    @classmethod
    def get_available_settings(
        cls, sessiontype: type[ba.Session]
    ) -> list[ba.Setting]:
        settings = [
            ba.IntSetting(
                'Lives Per Player',
                default=1,
                min_value=1,
                max_value=10,
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
                    ('Shorter', 0.15)
                ],
                default=1.0,
            ),
            ba.BoolSetting('Epic Mode', default=False),
        ]
        if issubclass(sessiontype, ba.DualTeamSession):
            settings.append(ba.BoolSetting('Solo Mode', default=False))
            settings.append(
                ba.BoolSetting('Balance Total Lives', default=False)
            )
        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: type[ba.Session]) -> bool:
        return issubclass(sessiontype, ba.DualTeamSession) or issubclass(
            sessiontype, ba.FreeForAllSession
        )

    @classmethod
    def get_supported_maps(cls, sessiontype: type[ba.Session]) -> list[str]:
        return ba.getmaps('melee')

    def get_instance_description(self) -> str | Sequence:
        return (
            'Enemy Spaz AmongUs. Kill them all'
        )

    def get_instance_description_short(self) -> str | Sequence:
        return (
            'Enemy Spaz AmongUs. Kill them all'
        )

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._solo_mode = False

    def spawn_player(self, player: Player) -> ba.Actor:
        p = [-6, -4.3, -2.6, -0.9, 0.8, 2.5, 4.2, 5.9]
        q = [-4, -2.3, -0.6, 1.1, 2.8, 4.5]

        x = random.randrange(0, len(p))
        y = random.randrange(0, len(q))
        spaz = self.spawn_player_spaz(player, position=(p[x], 1.8, q[y]))
        spaz.node.color = (1, 1, 1)
        spaz.node.highlight = (1, 0.4, 1)
        self.update_appearance(spaz, character=CHARACTER)
        # Also lets have them make some noise when they die.
        spaz.play_big_death_sound = True
        return spaz

    def update_appearance(self, spaz, character):
        factory = SpazFactory.get()
        media = factory.get_media(character)
        for field, value in media.items():
            setattr(spaz.node, field, value)
        spaz.node.style = factory.get_style(character)
        spaz.node.name = ''
