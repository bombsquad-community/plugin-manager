# Released under the MIT License. See LICENSE for details.
# ba_meta require api 9

from __future__ import annotations
from typing import TYPE_CHECKING
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.spazfactory import SpazFactory
import babase
import bauiv1 as bui
import bascenev1 as bs
import os
import _babase
if TYPE_CHECKING:
    from typing import Sequence

DECIMAL_LIMIT = 7


PlayerSpaz.supershit = PlayerSpaz.__init__


def ShitInit(self,
             player: bs.Player,
             *,
             color: Sequence[float] = (1.0, 1.0, 1.0),
             highlight: Sequence[float] = (0.5, 0.5, 0.5),
             character: str = 'Spaz',
             powerups_expire: bool = True) -> None:
    self.supershit(player,
                   color=color,
                   highlight=highlight,
                   character=character,
                   powerups_expire=powerups_expire)
    self.offt = bs.newnode('math', owner=self.node, attrs={
                           'input1': (1.2, 1.8, -0.7), 'operation': 'add'})
    self.node.connectattr('torso_position', self.offt, 'input2')
    self.txt = bs.newnode('text', owner=self.node, attrs={'text': '3.0', 'in_world': True, 'text': '0', 'shadow': 1.0, 'color': (
        1, 0, 0), 'flatness': 0.5, 'scale': 0.01, 'h_align': 'right'})
    p = self.node.position
    self.xyz = 0
    self.txt.text = "X: " + str(p[0]) + "\nY: " + str(p[1]) + "\nZ: " + str(p[2])
    self.offt.connectattr('output', self.txt, 'position')

    def update():
        p = self.node.position
        is_moving = abs(self.node.move_up_down) >= 0.01 or abs(self.node.move_left_right) >= 0.01
        if is_moving:
            self.xyz = (p[0], p[1], p[2])
            self.txt.text = "X: " + str(round(self.xyz[0], DECIMAL_LIMIT)) + "\nY: " + str(
                round(self.xyz[1], DECIMAL_LIMIT)) + "\nZ: " + str(round(self.xyz[2], DECIMAL_LIMIT))
    bs.timer(0.1, update, repeat=True)


def replaceable_punch(self) -> None:
    """
    Called to 'press punch' on this spaz;
    used for player or AI connections.
    """
    if not self.node or self.frozen or self.node.knockout > 0.0:
        return
    index = 0
    path_aid = _babase.env()['python_directory_user'] + '/Saved XYZ'
    path, dirs, files = next(os.walk(path_aid))
    index += len(files)
    c27 = str(index + 1)
    with open(path_aid + '/coords' + c27 + '.txt', 'w') as gg:
        gg.write("X: " + str(round(self.xyz[0], DECIMAL_LIMIT)) + "\nY: " + str(round(self.xyz[1], DECIMAL_LIMIT)) + "\nZ: " + str(round(self.xyz[2], DECIMAL_LIMIT)) +
                 '\n\n' + '(' + str(round(self.xyz[0], DECIMAL_LIMIT)) + ', ' + str(round(self.xyz[1], DECIMAL_LIMIT)) + ', ' + str(round(self.xyz[2], DECIMAL_LIMIT)) + ')')
        bui.screenmessage("Coordinates saved in: " + "BombSquad/Saved XYZ/" + "coords" + c27)
    if _babase.app.classic.platform == 'android':
        _babase.android_media_scan_file(path_aid)
    t_ms = bs.time() * 1000
    assert isinstance(t_ms, int)
    if t_ms - self.last_punch_time_ms >= self._punch_cooldown:
        if self.punch_callback is not None:
            self.punch_callback(self)
        self._punched_nodes = set()  # Reset this.
        self.last_punch_time_ms = t_ms
        self.node.punch_pressed = True
        if not self.node.hold_node:
            bs.timer(
                0.1,
                bs.WeakCall(self._safe_play_sound,
                            SpazFactory.get().swish_sound, 0.8))
    self._turbo_filter_add_press('punch')

# ba_meta export babase.Plugin


class ragingspeedhorn(babase.Plugin):
    try:
        oath = _babase.env()['python_directory_user'] + '/Saved XYZ'
        os.makedirs(oath, exist_ok=False)
    except:
        pass
    PlayerSpaz.on_punch_press = replaceable_punch
    PlayerSpaz.__init__ = ShitInit
    PlayerSpaz.xyz = 0
