# ba_meta require api 9

# @BsRush_Mod
# کپی با ذکر منبع آزاد

from __future__ import annotations
from bascenev1lib.mainmenu import MainMenuSession
from bascenev1._map import Map
import random
import bauiv1 as bui
import bascenev1 as bs
import babase
from typing import TYPE_CHECKING, cast

plugman = dict(
    plugin_name="floating_star",
    description="Get floating stars with colorful text",
    external_url="",
    authors=[
        {"name": "BsRush_Mod", "email": "", "discord": ""},
    ],
    version="1.0.0",
)


if TYPE_CHECKING:
    from typing import Any, Sequence, Callable, List, Dict, Tuple, Optional, Union

# ==============================================================================#

# تنظیمات متن
TEXT_CONTENT = "\ue00cBsRush Mod\ue00c"
TEXT_SIZE = 0.01
TEXT_COLOR = (1, 1, 1)

# ba_meta export plugin


class UwUuser(babase.Plugin):
    Map._old_init = Map.__init__

    def _new_init(self, vr_overlay_offset: Optional[Sequence[float]] = None) -> None:
        self._old_init(vr_overlay_offset)
        in_game = not isinstance(bs.get_foreground_host_session(), MainMenuSession)
        if not in_game:
            return

        def path():

            shield1 = bs.newnode("shield", attrs={
                'color': (1, 1, 1),
                'position': (-5.750, 4.3515026107, 2.0),
                'radius': 1.4
            })

            bs.animate_array(shield1, 'color', 3, {
                0: (random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9]),
                    random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9]),
                    random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])),
                0.2: (2, 0, 2),
                0.4: (2, 2, 0),
                0.6: (0, 2, 0),
                0.8: (0, 2, 2)
            }, loop=True)

            flash1 = bs.newnode("flash", attrs={
                'position': (0, 0, 0),
                'size': 0.6,
                'color': (1, 1, 1)
            })
            shield1.connectattr('position', flash1, 'position')

            text_node1 = bs.newnode('text',
                                    attrs={
                                        'text': TEXT_CONTENT,
                                        'in_world': True,
                                        'shadow': 1.0,
                                        'flatness': 1.0,
                                        'color': TEXT_COLOR,
                                        'scale': TEXT_SIZE,
                                        'h_align': 'center'
                                    }
                                    )

            text_math1 = bs.newnode('math',
                                    attrs={
                                        'input1': (0, 1.2, 0),
                                        'operation': 'add'
                                    }
                                    )
            shield1.connectattr('position', text_math1, 'input2')
            text_math1.connectattr('output', text_node1, 'position')

            bs.animate_array(text_node1, 'color', 3, {
                0: (1, 0, 0),      # قرمز
                0.2: (1, 1, 0),    # زرد
                0.4: (0, 1, 0),    # سبز
                0.6: (0, 1, 1),    # آبی روشن
                0.8: (1, 0, 1),    # بنفش
            }, loop=True)

            bs.animate_array(shield1, 'position', 3, {
                0: (-10, 3, -5),
                5: (10, 6, -5),
                10: (-10, 3, 5),
                15: (10, 6, 5),
                20: (-10, 3, -5)
            }, loop=True)

            shield2 = bs.newnode("shield", attrs={
                'color': (1, 1, 1),
                'position': (5.750, 4.3515026107, -2.0),
                'radius': 1.4
            })

            bs.animate_array(shield2, 'color', 3, {
                0: (random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9]),
                    random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9]),
                    random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])),
                0.2: (0, 2, 2),
                0.4: (2, 0, 2),
                0.6: (2, 2, 0),
                0.8: (0, 2, 0)
            }, loop=True)

            flash2 = bs.newnode("flash", attrs={
                'position': (0, 0, 0),
                'size': 0.6,
                'color': (1, 1, 1)
            })
            shield2.connectattr('position', flash2, 'position')

            text_node2 = bs.newnode('text',
                                    attrs={
                                        'text': TEXT_CONTENT,
                                        'in_world': True,
                                        'shadow': 1.0,
                                        'flatness': 1.0,
                                        'color': TEXT_COLOR,
                                        'scale': TEXT_SIZE,
                                        'h_align': 'center'
                                    }
                                    )

            text_math2 = bs.newnode('math',
                                    attrs={
                                        'input1': (0, 1.2, 0),
                                        'operation': 'add'
                                    }
                                    )
            shield2.connectattr('position', text_math2, 'input2')
            text_math2.connectattr('output', text_node2, 'position')

            bs.animate_array(text_node2, 'color', 3, {
                0: (1, 0, 1),      # بنفش
                0.2: (0, 1, 1),    # آبی روشن
                0.4: (0, 1, 0),    # سبز
                0.6: (1, 1, 0),    # زرد
                0.8: (1, 0, 0),    # قرمز
            }, loop=True)

            bs.animate_array(shield2, 'position', 3, {
                0: (10, 6, 5),
                5: (-10, 3, 5),
                10: (10, 6, -5),
                15: (-10, 3, -5),
                20: (10, 6, 5)
            }, loop=True)

        bs.timer(0.1, path)

    Map.__init__ = _new_init
