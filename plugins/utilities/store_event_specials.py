"""
This is free and unencumbered software released into the public domain.
Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.
In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
For more information, please refer to <http://unlicense.org/>
"""

# ba_meta require api 9

from typing import List, Dict, Any

import babase
import bauiv1 as bui

original_get_store_layout = bui.app.classic.store.get_store_layout


def add_special_characters(layout:
                           Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    special_characters = [
        'characters.bunny',
        'characters.taobaomascot',
        'characters.santa'
    ]
    for character in special_characters:
        if character not in layout['characters'][0]['items']:
            layout['characters'][0]['items'].append(character)


def add_special_minigames(layout:
                          Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    special_minigames = [
        'games.easter_egg_hunt',
    ]
    for minigame in special_minigames:
        if minigame not in layout['minigames'][0]['items']:
            layout['minigames'][0]['items'].append(minigame)


def modified_get_store_layout() -> Dict[str, List[Dict[str, Any]]]:
    layout = original_get_store_layout()
    add_special_characters(layout)
    add_special_minigames(layout)
    return layout


# ba_meta export plugin
class Main(babase.Plugin):
    def on_app_running(self) -> None:
        bui.app.classic.store.get_store_layout = modified_get_store_layout
