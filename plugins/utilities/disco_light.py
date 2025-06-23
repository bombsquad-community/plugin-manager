"""Disco Light Mod: V2.1
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
# Work on any 1.7.37+ ver.

# Note:
# The plugin commands only works on the host with the plugin activated.
# Other clients/players can't use the commands.

# v2.1
# - Enhance compatibility with other mods
# - Tint change when /disco off will be more dynamic.

# ----------------------------------------------------------------------------

# ba_meta require api 9


from __future__ import annotations

import bascenev1 as bs
import babase
from bascenev1 import _gameutils
import random

from bascenev1 import animate


class DiscoLight:

    def __init__(self):
        activity = bs.get_foreground_host_activity()
        self.globalnodes = activity.globalsnode.tint

    # Activate disco light.
    def start(self):
        activity = bs.get_foreground_host_activity()
        with activity.context:
            self.partyLight(True)
            self.rainbow(activity)

    # Deactivate disco light.
    def stop(self):
        activity = bs.get_foreground_host_activity()
        with activity.context:
            self.partyLight(False)
            self.stop_rainbow(activity)

    # Create and animate colorful spotlight.
    def partyLight(self, switch=True):
        from bascenev1._nodeactor import NodeActor
        x_spread = 10
        y_spread = 5
        positions = [[-x_spread, -y_spread], [0, -y_spread], [0, y_spread],
                     [x_spread, -y_spread], [x_spread, y_spread],
                     [-x_spread, y_spread]]
        times = [0, 2700, 1000, 1800, 500, 1400]

        # Store this on the current activity, so we only have one at a time.
        activity = bs.getactivity()
        activity.camera_flash_data = []  # type: ignore
        for i in range(6):
            r = random.choice([0.5, 1])
            g = random.choice([0.5, 1])
            b = random.choice([0.5, 1])
            light = NodeActor(
                bs.newnode('light',
                           attrs={
                               'position': (
                                   positions[i][0], 0, positions[i][1]),
                               'radius': 1.0,
                               'lights_volumes': False,
                               'height_attenuated': False,
                               'color': (r, g, b)
                           }))
            sval = 1.87
            iscale = 1.3
            tcombine = bs.newnode('combine',
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
                bs.timer(0.1,
                         light.node.delete)
            activity.camera_flash_data.append(light)  # type: ignore

    # Create RGB tint.
    def rainbow(self, activity) -> None:
        """Create RGB tint."""

        cnode = bs.newnode('combine',
                           attrs={
                               'input0': self.globalnodes[0],
                               'input1': self.globalnodes[1],
                               'input2': self.globalnodes[2],
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

        cnode.connectattr('output', activity.globalsnode, 'tint')

    # Revert to the original map tint.
    def stop_rainbow(self, activity):
        """Revert to the original map tint."""
        c_existing = activity.globalsnode.tint
        # map_name = activity.map.getname()
        tint = self.globalnodes

        cnode = bs.newnode('combine',
                           attrs={
                               'input0': c_existing[0],
                               'input1': c_existing[1],
                               'input2': c_existing[2],
                               'size': 3
                           })

        _gameutils.animate(cnode, 'input0', {0: c_existing[0], 1.0: tint[0]})
        _gameutils.animate(cnode, 'input1', {0: c_existing[1], 1.0: tint[1]})
        _gameutils.animate(cnode, 'input2', {0: c_existing[2], 1.0: tint[2]})

        cnode.connectattr('output', activity.globalsnode, 'tint')


# New chat func to add some commands to activate/deactivate the disco light.
def new_chat_message(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        activity = bs.get_foreground_host_activity()
        with activity.context:
            try:
                if not activity.disco_light:
                    activity.disco_light = DiscoLight()
            except:
                activity.disco_light = DiscoLight()
        if args[0] == '/disco':
            activity.disco_light.start()
        elif args[0] == '/disco off':
            activity.disco_light.stop()

    return wrapper


# ba_meta export babase.Plugin
class ByCrossJoy(babase.Plugin):
    def __init__(self):
        # Replace new chat func to the original game codes.
        bs.chatmessage = new_chat_message(bs.chatmessage)
