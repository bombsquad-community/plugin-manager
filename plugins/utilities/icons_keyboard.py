# Made by: Freaku / @[Just] Freak#4999

# • Icon Keyboard •
# Make your chats look even more cooler!
# Make sure "Always Use Internal Keyboard" is ON
# Double tap the space to change between keyboards...


# ba_meta require api 7

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from _ba import charstr as uwu

if TYPE_CHECKING:
    from typing import Any, Optional, Dict, List, Tuple, Type, Iterable


# ba_meta export keyboard
class IconKeyboard_byFreaku(ba.Keyboard):
    """Keyboard go brrrrrrr"""
    name = 'Icons by \ue048Freaku'
    chars = [(uwu(ba.SpecialChar.TICKET),
              uwu(ba.SpecialChar.CROWN),
              uwu(ba.SpecialChar.DRAGON),
              uwu(ba.SpecialChar.SKULL),
              uwu(ba.SpecialChar.HEART),
              uwu(ba.SpecialChar.FEDORA),
              uwu(ba.SpecialChar.HAL),
              uwu(ba.SpecialChar.YIN_YANG),
              uwu(ba.SpecialChar.EYE_BALL),
              uwu(ba.SpecialChar.HELMET),
              uwu(ba.SpecialChar.OUYA_BUTTON_U)),
             (uwu(ba.SpecialChar.MUSHROOM),
             uwu(ba.SpecialChar.NINJA_STAR),
             uwu(ba.SpecialChar.VIKING_HELMET),
             uwu(ba.SpecialChar.MOON),
             uwu(ba.SpecialChar.SPIDER),
             uwu(ba.SpecialChar.FIREBALL),
             uwu(ba.SpecialChar.MIKIROG),
             uwu(ba.SpecialChar.OUYA_BUTTON_O),
             uwu(ba.SpecialChar.LOCAL_ACCOUNT),
             uwu(ba.SpecialChar.LOGO)),
             (uwu(ba.SpecialChar.TICKET),
             uwu(ba.SpecialChar.FLAG_INDIA),
             uwu(ba.SpecialChar.OCULUS_LOGO),
             uwu(ba.SpecialChar.STEAM_LOGO),
             uwu(ba.SpecialChar.NVIDIA_LOGO),
             uwu(ba.SpecialChar.GAME_CENTER_LOGO),
             uwu(ba.SpecialChar.GOOGLE_PLAY_GAMES_LOGO),
             uwu(ba.SpecialChar.ALIBABA_LOGO))]
    nums = []
    pages: Dict[str, Tuple[str, ...]] = {}
