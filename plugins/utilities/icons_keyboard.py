# Made by your friend: Freaku

# • Icon Keyboard •
# Make your chats look even more cooler!
# Make sure "Always Use Internal Keyboard" is ON
# Double tap the space to change between keyboards...


# ba_meta require api 8

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
from babase import charstr as uwu

if TYPE_CHECKING:
    from typing import Any, Optional, Dict, List, Tuple, Type, Iterable


# ba_meta export keyboard
class IconKeyboard_byFreaku(babase.Keyboard):
    """Keyboard go brrrrrrr"""
    name = 'Icons by \ue048Freaku'
    chars = [(uwu(babase.SpecialChar.TICKET),
              uwu(babase.SpecialChar.CROWN),
              uwu(babase.SpecialChar.DRAGON),
              uwu(babase.SpecialChar.SKULL),
              uwu(babase.SpecialChar.HEART),
              uwu(babase.SpecialChar.FEDORA),
              uwu(babase.SpecialChar.HAL),
              uwu(babase.SpecialChar.YIN_YANG),
              uwu(babase.SpecialChar.EYE_BALL),
              uwu(babase.SpecialChar.HELMET),
              uwu(babase.SpecialChar.OUYA_BUTTON_U)),
             (uwu(babase.SpecialChar.MUSHROOM),
             uwu(babase.SpecialChar.NINJA_STAR),
             uwu(babase.SpecialChar.VIKING_HELMET),
             uwu(babase.SpecialChar.MOON),
             uwu(babase.SpecialChar.SPIDER),
             uwu(babase.SpecialChar.FIREBALL),
             uwu(babase.SpecialChar.MIKIROG),
             uwu(babase.SpecialChar.OUYA_BUTTON_O),
             uwu(babase.SpecialChar.LOCAL_ACCOUNT),
             uwu(babase.SpecialChar.LOGO)),
             (uwu(babase.SpecialChar.TICKET),
             uwu(babase.SpecialChar.FLAG_INDIA),
             uwu(babase.SpecialChar.OCULUS_LOGO),
             uwu(babase.SpecialChar.STEAM_LOGO),
             uwu(babase.SpecialChar.NVIDIA_LOGO),
             uwu(babase.SpecialChar.GAME_CENTER_LOGO),
             uwu(babase.SpecialChar.GOOGLE_PLAY_GAMES_LOGO),
             uwu(babase.SpecialChar.EXPLODINARY_LOGO))]
    nums = []
    pages: Dict[str, Tuple[str, ...]] = {}
