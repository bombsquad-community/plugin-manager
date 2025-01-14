# Made by your friend: Freaku

# • Icon Keyboard •
# Make your chats look even more cooler!
# Make sure "Always Use Internal Keyboard" is ON
# Double tap the space to change between keyboards...
# Tap bottom-left bomb button to cycle through different icons


# ba_meta require api 9

import bauiv1
import babase
from babase import charstr

list_of_icons = [i for i in babase.SpecialChar]
list_of_icons = [charstr(i) for i in list_of_icons]
list_of_icons.reverse()

for i in range(26 - (len(list_of_icons) % 26)):
    list_of_icons.append('‎')


class IconKeyboard(babase.Keyboard if hasattr(babase, 'Keyboard') else bauiv1.Keyboard):
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


# ba_meta export plugin
class byFreaku(babase.Plugin):
    def __init__(self):
        babase.app.meta.scanresults.exports['babase.Keyboard' if hasattr(
            babase, 'Keyboard') else 'bauiv1.Keyboard'].append(__name__+'.IconKeyboard')
