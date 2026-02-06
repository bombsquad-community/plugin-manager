# ba_meta require api 9

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs
from bascenev1lib.actor.spaz import Spaz

if TYPE_CHECKING:
    pass

plugman = dict(
    plugin_name="custom_hits",
    description="when someone hited rainbow text whit effect will appear",
    external_url="",
    authors=[
        {"name": "ATD", "email": "anasdhaoidi001@gmail.com", "discord": ""},
    ],
    version="1.0.1",
)

####################################

first_damage = (u'\ue042TRY AGAIN?\ue042', (0, 1, 0), '6')
second_damage = (u'\ue048GOOD!\ue048', (0, 1, 1), '2')
third_damage = (u'\ue041NICE!\ue041', (0.8, 0.4, 1), '3')
fourth_damage = (u'\ue049UPPS\ue049', (1, 1, 0), '4')
five_damage = (u'\ue043DEATH!\ue043', (1, 0, 0), '5')


def custom_effects(pos: float, effect: str = None) -> None:
    if effect == '1':
        bs.emitfx(
            position=pos,
            count=3,
            scale=0.1,
            spread=0.1,
            chunk_type='rock')
    elif effect == '2':
        bs.emitfx(
            position=pos,
            count=70,
            scale=2,
            spread=0.8,
            chunk_type='spark')
    elif effect == '3':
        bs.emitfx(
            position=pos,
            count=6,
            scale=0.3,
            spread=0.4,
            chunk_type='splinter')
    elif effect == '4':
        bs.emitfx(
            position=pos,
            count=50,
            scale=3.0,
            spread=0.9,
            chunk_type='ice')
    elif effect == '5':
        bs.emitfx(
            position=pos,
            count=80,
            scale=3.0,
            spread=1.5,
            chunk_type='metal')
    elif effect == '6':
        bs.emitfx(
            position=pos,
            count=30,
            scale=1.2,
            spread=0.8,
            chunk_type='slime')

####################################

# ba_meta export babase.Plugin


class CustomHitsPlugin(babase.Plugin):

    def on_punched(self, damage: int) -> None:
        pos = self.node.position

        def custom_text(msg: str, color: float) -> None:
            text = bs.newnode(
                'text',
                attrs={
                    'text': msg,
                    'color': color,
                    'in_world': True,
                    'h_align': 'center',
                    'shadow': 0.5,
                    'flatness': 1.0})
            bs.animate_array(text, 'position', 3, {
                0.0: (pos[0], pos[1] + 1.2, pos[2]),
                2.0: (pos[0], pos[1] + 1.7, pos[2])
            })
            bs.animate(text, 'opacity', {
                0.8: 1.0,
                2.0: 0.0
            })
            bs.animate(text, 'scale', {
                0: 0,
                0.1: 0.017,
                0.15: 0.014,
                2.0: 0.016
            })
            bs.animate_array(text, 'color', 3, {
                0.0: (0, 0, 0),  # Black
                0.2: (2.55, 2.55, 2.55),  # White
                0.4: (2, 0, 0),  # Red
                0.6: (0, 2.55, 0),  # Lime
                0.8: (0, 0, 2.55),  # Blue
                1.0: (2.55, 2.55, 0),  # Yellow
                1.2: (0, 2.55, 2.55),  # Cyan / Aqua
                1.4: (2.55, 0, 2.55),  # Magenta / Fuchsia
                1.6: (1.92, 1.92, 1.92),  # Silver
                1.8: (1.28, 1.28, 1.28),  # Gray
                2.0: (1.28, 0, 0),  # Maroon
                2.2: (1.28, 1.28, 0),  # Olive
                2.4: (0, 1.28, 0),  # Green
                2.6: (1.28, 0, 1.28),  # Purple
                2.8: (0, 1.28, 1.28),  # Teal
                3.0: (0, 0, 1.28),  # Navy
                3.2: (1.5, 0.5, 0),  # Orange
                3.4: (1.8, 0.5, 1.6),  # Pink
                3.6: (0.5, 0.5, 0.5),  # Gray
            }, loop=True)
            bs.timer(2.0, text.delete)
        if damage < 200:
            custom_text(first_damage[0], first_damage[1])
            custom_effects(pos, first_damage[2])
        elif damage < 500:
            custom_text(second_damage[0], second_damage[1])
            custom_effects(pos, second_damage[2])
        elif damage < 800:
            custom_text(third_damage[0], third_damage[1])
            custom_effects(pos, third_damage[2])
        elif damage < 1000:
            custom_text(fourth_damage[0], fourth_damage[1])
            custom_effects(pos, fourth_damage[2])
        else:
            custom_text(five_damage[0], five_damage[1])
            custom_effects(pos, five_damage[2])
    Spaz.on_punched = on_punched
