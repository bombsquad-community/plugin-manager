"""Disco Light Mod: V1.0
Made by Cross Joy"""

# If anyone who wanna help me on giving suggestion/ fix bugs/ creating PR,
# Can visit my github https://github.com/CrossJoy/Bombsquad-Modding

# You can contact me through discord:
# My Discord Id: Cross Joy#0721
# My BS Discord Server: https://discord.gg/JyBY6haARJ


# ----------------------------------------------------------------------------
# Add disco light into the game, so you can
# play with your friends under the colorful light. :)

# type '/disco' in your chat box to activate or
# type '/disco off' to deactivate the disco light.


# Coop and multiplayer compatible.
# Work on any 1.7 ver.

# Note:
# The plugin commands only works on the host with the plugin activated.
# Other clients/players can't use the commands.
# ----------------------------------------------------------------------------

# ba_meta require api 7


from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import _ba
from ba import _gameutils
import random

from ba import animate

if TYPE_CHECKING:
    from typing import Sequence, Union

# Check game ver.


def is_game_version_lower_than(version):
    """
    Returns a boolean value indicating whether the current game
    version is lower than the passed version. Useful for addressing
    any breaking changes within game versions.
    """
    game_version = tuple(map(int, ba.app.version.split(".")))
    version = tuple(map(int, version.split(".")))
    return game_version < version


if is_game_version_lower_than("1.7.7"):
    ba_internal = _ba
else:
    ba_internal = ba.internal


# Activate disco light.
def start():
    activity = _ba.get_foreground_host_activity()

    with ba.Context(activity):
        partyLight(True)
        rainbow(activity)


# Deactivate disco light.
def stop():
    activity = _ba.get_foreground_host_activity()

    with ba.Context(activity):
        partyLight(False)
        stop_rainbow(activity)


# Create and animate colorful spotlight.
def partyLight(switch=True):
    from ba._nodeactor import NodeActor
    x_spread = 10
    y_spread = 5
    positions = [[-x_spread, -y_spread], [0, -y_spread], [0, y_spread],
                 [x_spread, -y_spread], [x_spread, y_spread],
                 [-x_spread, y_spread]]
    times = [0, 2700, 1000, 1800, 500, 1400]

    # Store this on the current activity, so we only have one at a time.
    activity = _ba.getactivity()
    activity.camera_flash_data = []  # type: ignore
    for i in range(6):
        r = random.choice([0.5, 1])
        g = random.choice([0.5, 1])
        b = random.choice([0.5, 1])
        light = NodeActor(
            _ba.newnode('light',
                        attrs={
                            'position': (positions[i][0], 0, positions[i][1]),
                            'radius': 1.0,
                            'lights_volumes': False,
                            'height_attenuated': False,
                            'color': (r, g, b)
                        }))
        sval = 1.87
        iscale = 1.3
        tcombine = _ba.newnode('combine',
                               owner=light.node,
                               attrs={
                                   'size': 3,
                                   'input0': positions[i][0],
                                   'input1': 0,
                                   'input2': positions[i][1]
                               })
        assert light.node
        tcombine.connectattr('output', light.node, 'position')
        xval = positions[i][0]
        yval = positions[i][1]
        spd = 1.0 + random.random()
        spd2 = 1.0 + random.random()
        animate(tcombine,
                'input0', {
                    0.0: xval + 0,
                    0.069 * spd: xval + 10.0,
                    0.143 * spd: xval - 10.0,
                    0.201 * spd: xval + 0
                },
                loop=True)
        animate(tcombine,
                'input2', {
                    0.0: yval + 0,
                    0.15 * spd2: yval + 10.0,
                    0.287 * spd2: yval - 10.0,
                    0.398 * spd2: yval + 0
                },
                loop=True)
        animate(light.node,
                'intensity', {
                    0.0: 0,
                    0.02 * sval: 0,
                    0.05 * sval: 0.8 * iscale,
                    0.08 * sval: 0,
                    0.1 * sval: 0
                },
                loop=True,
                offset=times[i])
        if not switch:
            _ba.timer(0.1,
                      light.node.delete)
        activity.camera_flash_data.append(light)  # type: ignore


# Create RGB tint.
def rainbow(self) -> None:
    """Create RGB tint."""
    c_existing = self.globalsnode.tint
    cnode = _ba.newnode('combine',
                        attrs={
                            'input0': c_existing[0],
                            'input1': c_existing[1],
                            'input2': c_existing[2],
                            'size': 3
                        })

    _gameutils.animate(cnode, 'input0',
                       {0.0: 1.0, 1.0: 1.0, 2.0: 1.0, 3.0: 1.0,
                        4.0: 0.2, 5.0: 0.1, 6.0: 0.5,
                        7.0: 1.0}, loop=True)

    _gameutils.animate(cnode, 'input1',
                       {0.0: 0.2, 1.0: 0.2, 2.0: 0.5, 3.0: 1.0,
                        4.0: 1.0, 5.0: 0.1, 6.0: 0.3,
                        7.0: 0.2}, loop=True)

    _gameutils.animate(cnode, 'input2',
                       {0.0: 0.2, 1.0: 0.2, 2.0: 0.0, 3.0: 0.0,
                        4.0: 0.2, 5.0: 1.0, 6.0: 1.0,
                        7.0: 0.2}, loop=True)

    cnode.connectattr('output', self.globalsnode, 'tint')


# Revert to the original map tint.
def stop_rainbow(self):
    """Revert to the original map tint."""
    c_existing = self.globalsnode.tint
    map_name = self.map.getname()
    tint = check_map_tint(map_name)

    cnode = _ba.newnode('combine',
                        attrs={
                            'input0': c_existing[0],
                            'input1': c_existing[1],
                            'input2': c_existing[2],
                            'size': 3
                        })

    _gameutils.animate(cnode, 'input0', {0: c_existing[0], 1.0: tint[0]})
    _gameutils.animate(cnode, 'input1', {0: c_existing[1], 1.0: tint[1]})
    _gameutils.animate(cnode, 'input2', {0: c_existing[2], 1.0: tint[2]})

    cnode.connectattr('output', self.globalsnode, 'tint')


# Check map name
def check_map_tint(map_name):
    if map_name in 'Hockey Stadium':
        tint = (1.2, 1.3, 1.33)
    elif map_name in 'Football Stadium':
        tint = (1.3, 1.2, 1.0)
    elif map_name in 'Bridgit':
        tint = (1.1, 1.2, 1.3)
    elif map_name in 'Big G':
        tint = (1.1, 1.2, 1.3)
    elif map_name in 'Roundabout':
        tint = (1.0, 1.05, 1.1)
    elif map_name in 'Monkey Face':
        tint = (1.1, 1.2, 1.2)
    elif map_name in 'Zigzag':
        tint = (1.0, 1.15, 1.15)
    elif map_name in 'The Pad':
        tint = (1.1, 1.1, 1.0)
    elif map_name in 'Lake Frigid':
        tint = (0.8, 0.9, 1.3)
    elif map_name in 'Crag Castle':
        tint = (1.15, 1.05, 0.75)
    elif map_name in 'Tower D':
        tint = (1.15, 1.11, 1.03)
    elif map_name in 'Happy Thoughts':
        tint = (1.3, 1.23, 1.0)
    elif map_name in 'Step Right Up':
        tint = (1.2, 1.1, 1.0)
    elif map_name in 'Doom Shroom':
        tint = (0.82, 1.10, 1.15)
    elif map_name in 'Courtyard':
        tint = (1.2, 1.17, 1.1)
    elif map_name in 'Rampage':
        tint = (1.2, 1.1, 0.97)
    elif map_name in 'Tip Top':
        tint = (0.8, 0.9, 1.3)
    else:
        tint = (1, 1, 1)

    return tint


# Get the original game codes.
old_fcm = ba_internal.chatmessage


# New chat func to add some commands to activate/deactivate the disco light.
def new_chat_message(msg: Union[str, ba.Lstr], clients: Sequence[int] = None,
                     sender_override: str = None):
    old_fcm(msg, clients, sender_override)
    if msg == '/disco':
        start()
    if msg == '/disco off':
        stop()


# Replace new chat func to the original game codes.
ba_internal.chatmessage = new_chat_message
if not ba_internal.is_party_icon_visible():
    ba_internal.set_party_icon_always_visible(True)


# ba_meta export plugin
class ByCrossJoy(ba.Plugin):
    def __init__(self): pass
