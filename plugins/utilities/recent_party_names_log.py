# ba_meta require api 9

"""
    This plugin keeps the track of party names you recently interacted with.
    and Allows you to view/filter of those names for easy search. 
    (by adding a recent button in gather public tab)

    Helps when you forgot to add a party in favorite list which you recently enjoy the most.
"""

from __future__ import annotations
from typing import override
from collections import OrderedDict

import bauiv1 as bui
from bauiv1lib import popup
from bauiv1lib.gather import publictab

#-------- PLUGIN MANAGER DEFINATION -----------------

__version__ = "1.0.1"
__author__ = "shailesh"

plugman = dict(
    plugin_name="recent_party_names_log",
    description=__doc__,
    external_url="https://youtu.be/EyQWRstNmzc?si=lrf4zS0r7Kj8Ngd4",
    authors=[
        {
            "name": __author__,
            "email": "shaileshgabu11@gmail.com",
            "discord": "shailesh_gabu_11",
            "github": "Shailesh051211"
        },
    ],
    version=__version__,
)
#--------------------------------------------------


MAX_RECENTS = 50
RECENT_PARTY_CONGIF_KEY = "GS:Party History"

# ba_meta export babase.Plugin
class plg(bui.Plugin):

    party_log = OrderedDict()
    if isinstance(bui.app.config.get(RECENT_PARTY_CONGIF_KEY), list):
        party_log = OrderedDict(bui.app.config[RECENT_PARTY_CONGIF_KEY])

    def _new_build_join_tab(func):
        def wrapper(*args, **kwargs):
            """ extented original function to add recent button """

            c_width, c_height = args[1], args[2]
            btn_width, btn_height = 100, 50
            recent_button = bui.buttonwidget(
                id="GS|recent_button",
                parent=args[0]._container,
                position=(
                    c_width * 0.86,
                    c_height - btn_height - 25
                ),
                size=(btn_width, btn_height),
                label="Recents",
                left_widget=args[0]._host_text,
            )

            call = lambda: RecentPartiesWindow(recent_button, args[0])
            bui.buttonwidget(edit=recent_button, on_activate_call=call)
            bui.widget(edit=args[0]._host_text, right_widget=recent_button)

            return func(*args, **kwargs)
        return wrapper

    publictab.PublicGatherTab._build_join_tab = (
        _new_build_join_tab(publictab.PublicGatherTab._build_join_tab)
    )

    def new_on_public_party_activate(func):
        def wrapper(*args, **kwargs):

            plg._add_party(args[1])

            return func(*args, **kwargs)
        return wrapper

    publictab.PublicGatherTab.on_public_party_activate = (
        new_on_public_party_activate(
            publictab.PublicGatherTab.on_public_party_activate
        )
    )

    def _add_party(party: publictab.PartyEntry) -> None:

        key = party.address
        # remove if its already exists
        plg.party_log.pop(key, None)
        # re/new add
        plg.party_log[key] = party.name

        if len(plg.party_log) > MAX_RECENTS:
            plg.party_log.popitem(last=False) # oldest remove

        bui.app.config[RECENT_PARTY_CONGIF_KEY] = list(plg.party_log.items())
        bui.app.config.commit()


class RecentPartiesWindow(popup.PopupWindow):

    def __init__(
        self,
        origin: bui.Widget,
        public_gather_tab: publictab.PublicGatherTab,
    ):

        self._public_gather_tab = public_gather_tab
        self._transitioning_out = False

        uiscale = bui.app.ui_v1.uiscale

        vs_width, vs_height = bui.get_virtual_screen_size()
        self._width = vs_width * 0.6
        self._height = vs_height

        # original popup pop's up too high for MEDIUM and HIGH
        # so, lets downgrade it and centralized
        focus_position = (0.0, 0.0)
        if uiscale is not bui.UIScale.SMALL:
            focus_position = (
                vs_width/2 - self._width/2,
                vs_height/2 - self._height * 0.30
            )

        super().__init__(
            position=origin.get_screen_space_center(),
            size=(self._width, self._height),
            scale=(
                1.0 if uiscale is bui.UIScale.SMALL
                else 0.7 if uiscale is bui.UIScale.MEDIUM
                else 0.65
            ),
            focus_position=focus_position,
            bg_color=(0.40, 0.40, 0.55),
            darken_behind=False # Too Dark
        )
        # title
        bui.textwidget(
            parent=self.root_widget,
            position=(self._width * 0.5, self._height * 0.95),
            size=(0, 0),
            scale=1.3,
            color=(0.8, 0.9, 1.0),
            text="Recently Interacted Parties",
            h_align="center",
            v_align="center"
        )
        # close
        self._close_btn = bui.buttonwidget(
            parent=self.root_widget,
            position=(self._width * 0.1, self._height * 0.92),
            size=(40, 40),
            label=bui.SpecialChar.CLOSE.value,
            on_activate_call=self.on_popup_cancel
        )
        bui.containerwidget(
            edit=self.root_widget, cancel_button=self._close_btn
        )

        self._scrollwidth = self._width * 0.85
        self._scrollheight = self._height * 0.8

        scrollxpos = self._width * 0.5 - self._scrollwidth * 0.5
        scrollypos = self._height * 0.5 - self._scrollheight * 0.5
        self._scrollwidget = bui.scrollwidget(
            parent=self.root_widget,
            position=(scrollxpos, scrollypos),
            size=(self._scrollwidth, self._scrollheight),
            border_opacity=0.8,
            highlight=False,
        )
        self._subcontainer: bui.Widget | None = None
        self._draw_subcontainer()

    def _draw_subcontainer(self) -> None:

        if len(plg.party_log) == 0:
            bui.textwidget(
                parent=self.root_widget,
                size=(0, 0),
                position=(self._width/2, self._height/2),
                text="No recent parties interaction",
                color=(0.9, 0.9, 1.0, 0.6),
                h_align="center",
                v_align="center"
            )
            return

        ypad = 10
        row_height = 50

        filter_btns = []
        remove_btns = []

        subwidth = self._scrollwidth
        subheight = row_height * len(plg.party_log) + ypad * 2
        if self._subcontainer is None:
            self._subcontainer = bui.containerwidget(
                parent=self._scrollwidget,
                size=(subwidth, subheight),
                background=False,
            )
        else:
            bui.containerwidget(
                edit=self._subcontainer,
                size=(subwidth, subheight)
            )

        btn_height = row_height * 0.8
        btn_ypad = row_height - btn_height
        ypos = subheight - ypad - row_height
        for address, name in reversed(plg.party_log.items()):
            # Pary Name
            bui.textwidget(
                parent=self._subcontainer,
                position=(15, ypos),
                size=(0, row_height),
                scale=1.2,
                maxwidth=subwidth * 0.66,
                text=name,
                h_align="left",
                v_align="center",
            )
            # Filter
            filter_btns.append(
                bui.buttonwidget(
                  parent=self._subcontainer,
                  position=(subwidth * 0.69, ypos + btn_ypad),
                  size=(80, btn_height),
                  label="Filter",
                  color=(0.3, 0.3, 0.9),
                  on_activate_call=bui.CallStrict(self._do_filter, name)
                )
            )
            # Remove
            remove_btns.append(
                bui.buttonwidget(
                  parent=self._subcontainer,
                  position=(subwidth * 0.82, ypos + btn_ypad),
                  size=(100, btn_height),
                  label="Remove",
                  color=(0.7, 0.3, 0.3),
                  on_activate_call=bui.CallStrict(self._ask_remove, address)
                )
            )
            ypos -= row_height

        # buttons navigation for pc
        bui.widget(
            edit=self._close_btn,
            right_widget=filter_btns[0], down_widget=filter_btns[0]
        )
        btnslen = len(filter_btns)
        for index in range(btnslen):
            # For filter
            up_widget = self._close_btn if index == 0 else filter_btns[index-1]
            left_widget = right_widget = remove_btns[index]
            down_widget = None if index == btnslen - 1 else filter_btns[index+1]
            bui.widget(
                edit=filter_btns[index],
                up_widget=up_widget, down_widget=down_widget,
                left_widget=left_widget, right_widget=right_widget
            )
            # For remove
            up_widget = self._close_btn if index == 0 else remove_btns[index-1]
            left_widget = right_widget = filter_btns[index]
            down_widget = None if index == btnslen - 1 else remove_btns[index+1]
            bui.widget(
                edit=remove_btns[index],
                up_widget=up_widget, down_widget=down_widget,
                left_widget=left_widget, right_widget=right_widget
            )

    def _do_filter(self, name: str) -> None:
        self.on_popup_cancel()
        bui.textwidget(
            edit=self._public_gather_tab._filter_text,
            text=name
        )

    def _ask_remove(self, key: str) -> None:
        from bauiv1lib import confirm

        confirm.ConfirmWindow(
            f'Remove "{plg.party_log[key]}"?',
            lambda: self._do_remove(key),
            width=450, height=150,
        )

    def _do_remove(self, key: str) -> None:

        plg.party_log.pop(key)
        bui.app.config[RECENT_PARTY_CONGIF_KEY] = list(plg.party_log.items())
        bui.app.config.commit()
        bui.getsound("shieldDown").play()
        self._re_build_subcontainer()

    def _re_build_subcontainer(self) -> None:
        for child in self._subcontainer.get_children():
            child.delete()
        self._draw_subcontainer()

    @override
    def on_popup_cancel(self) -> None:

        if not self.root_widget or self._transitioning_out:
            return

        if not self._transitioning_out:
            self._transitioning_out = True

        bui.getsound("swish").play()
        bui.containerwidget(edit=self.root_widget, transition="out_scale")
