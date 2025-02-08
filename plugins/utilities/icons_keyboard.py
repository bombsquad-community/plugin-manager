# Made by your friend: Freaku

# • Icon Keyboard •
# Make your chats look even more cooler!
# Make sure "Always Use Internal Keyboard" is ON
# Double tap the space to change between keyboards...
# Tap bottom-left bomb button to cycle through different icons


# ba_meta require api 9

import bauiv1
from babase import SpecialChar
from babase import charstr

list_of_icons = [i for i in SpecialChar]
list_of_icons = [charstr(i) for i in list_of_icons]
list_of_icons.reverse()

for i in range(26 - (len(list_of_icons) % 26)):
    list_of_icons.append('‎')


# ba_meta export bauiv1.Keyboard
class IconKeyboard(bauiv1.Keyboard):
    """Keyboard go brrrrrrr"""
    name = 'Icons by \ue048Freaku'
    chars = [(list_of_icons[0:10]),
             (list_of_icons[10:19]),
             (list_of_icons[19:26])]
    nums = ['‎' for i in range(26)]
    pages = {
        f'icon{i//26+1}': tuple(list_of_icons[i:i+26])
        for i in range(26, len(list_of_icons), 26)
    }