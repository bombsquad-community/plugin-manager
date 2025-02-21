# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)

# ba_meta require api 8
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

import babase
import bauiv1 as bui
import bascenev1 as bs
from bascenev1lib.game.elimination import EliminationGame, Player
from bascenev1lib.actor.spazfactory import SpazFactory
import random

if TYPE_CHECKING:
    from typing import Any, Sequence


CHARACTER = 'Spaz'

# ba_meta export bascenev1.GameActivity


class TheSpazGame(EliminationGame):
    name = 'TheSpazGame'
    description = 'Enemy Spaz AmongUs. Kill them all'
    scoreconfig = bs.ScoreConfig(
        label='Survived', scoretype=bs.ScoreType.SECONDS, none_is_winner=True
    )

    announce_player_deaths = False

    allow_mid_activity_joins = False

    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[babase.Setting]:
        settings = [
            bs.IntSetting(
                'Lives Per Player',
                default=1,
                min_value=1,
                max_value=10,
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
                    ('Shorter', 0.15)
                ],
                default=1.0,
            ),
            bs.BoolSetting('Epic Mode', default=False),
        ]
        if issubclass(sessiontype, bs.DualTeamSession):
            settings.append(bs.BoolSetting('Solo Mode', default=False))
            settings.append(
                bs.BoolSetting('Balance Total Lives', default=False)
            )
        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession) or issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return bs.app.classic.getmaps('melee')

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

    def spawn_player(self, player: Player) -> bs.Actor:
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
