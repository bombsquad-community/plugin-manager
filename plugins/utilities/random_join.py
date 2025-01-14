# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import _babase
import babase
import bauiv1 as bui
import bascenev1 as bs
import random
from bauiv1lib.gather.publictab import PublicGatherTab, PartyEntry, PingThread
if TYPE_CHECKING:
    from typing import Callable

ClassType = TypeVar('ClassType')
MethodType = TypeVar('MethodType')


def override(cls: ClassType) -> Callable[[MethodType], MethodType]:
    def decorator(newfunc: MethodType) -> MethodType:
        funcname = newfunc.__code__.co_name
        if hasattr(cls, funcname):
            oldfunc = getattr(cls, funcname)
            setattr(cls, f'_old_{funcname}', oldfunc)

        setattr(cls, funcname, newfunc)
        return newfunc

    return decorator

# Can this stuff break mro? (P.S. yes, so we're not using super() anymore).
# Although it gives nice auto-completion.
# And anyways, why not just GatherPublicTab = NewGatherPublicTab?
# But hmm, if we imagine someone used `from blah.blah import Blah`, using
# `blah.Blah = NewBlah` AFTERWARDS would be meaningless.


class NewPublicGatherTab(PublicGatherTab, PingThread):

    @override(PublicGatherTab)
    def _build_join_tab(self, region_width: float,
                        region_height: float,
                        oldfunc: Callable = None) -> None:
        # noinspection PyUnresolvedReferences
        self._old__build_join_tab(region_width, region_height)

        # Copy-pasted from original function.
        c_width = region_width
        c_height = region_height - 20
        sub_scroll_height = c_height - 125
        sub_scroll_width = 830
        v = c_height - 35
        v -= 60

        self._random_join_button = bui.buttonwidget(
            parent=self._container,
            label='random',
            size=(90, 45),
            position=(710, v + 10),
            on_activate_call=bs.WeakCall(self._join_random_server),
        )
        bui.widget(edit=self._random_join_button, up_widget=self._host_text,
                   left_widget=self._filter_text)

        # We could place it somewhere under plugin settings which is kind of
        # official way to customise plugins. Although it's too deep:
        # Gather Window -> Main Menu -> Settings -> Advanced -(scroll)->
        # Plugins -(scroll probably)-> RandomJoin Settings.
        self._random_join_settings_button = bui.buttonwidget(
            parent=self._container,
            icon=bui.gettexture('settingsIcon'),
            size=(40, 40),
            position=(820, v + 13),
            on_activate_call=bs.WeakCall(self._show_random_join_settings),
        )

    @override(PublicGatherTab)
    def _show_random_join_settings(self) -> None:
        RandomJoinSettingsPopup(
            origin_widget=self._random_join_settings_button)

    @override(PublicGatherTab)
    def _get_parties_list(self) -> list[PartyEntry]:
        if (self._parties_sorted and
            (randomjoin.maximum_ping == 9999 or
             # Ensure that we've pinged at least 10%.
             len([p for k, p in self._parties_sorted
                  if p.ping is not None]) > len(self._parties_sorted) / 10)):
            randomjoin.cached_parties = [p for k, p in self._parties_sorted]
        return randomjoin.cached_parties

    @override(PublicGatherTab)
    def _join_random_server(self) -> None:
        name_prefixes = set()
        parties = [p for p in self._get_parties_list() if
                   (p.size >= randomjoin.minimum_players
                    and p.size < p.size_max and (randomjoin.maximum_ping == 9999
                                                 or (p.ping is not None
                                                     and p.ping <= randomjoin.maximum_ping)))]

        if not parties:
            bui.screenmessage('No suitable servers found; wait',
                              color=(1, 0, 0))
            bui.getsound('error').play()
            return

        for party in parties:
            name_prefixes.add(party.name[:6])

        random.choice(list(name_prefixes))

        party = random.choice(
            [p for p in parties if p.name[:6] in name_prefixes])

        bs.connect_to_party(party.address, party.port)


class RandomJoinSettingsPopup(bui.Window):
    def __init__(self, origin_widget: bui.Widget) -> None:
        c_width = 600
        c_height = 400
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(root_widget=bui.containerwidget(
            scale=(
                1.8
                if uiscale is babase.UIScale.SMALL
                else 1.55
                if uiscale is babase.UIScale.MEDIUM
                else 1.0
            ),
            scale_origin_stack_offset=origin_widget.get_screen_space_center(),
            stack_offset=(0, -10)
            if uiscale is babase.UIScale.SMALL
            else (0, 15)
            if uiscale is babase.UIScale.MEDIUM
            else (0, 0),
            size=(c_width, c_height),
            transition='in_scale',
        ))

        bui.textwidget(
            parent=self._root_widget,
            size=(0, 0),
            h_align='center',
            v_align='center',
            text='Random Join Settings',
            scale=1.5,
            color=(0.6, 1.0, 0.6),
            maxwidth=c_width * 0.8,
            position=(c_width * 0.5, c_height - 60),
        )

        v = c_height - 120
        bui.textwidget(
            parent=self._root_widget,
            size=(0, 0),
            h_align='right',
            v_align='center',
            text='Maximum ping',
            maxwidth=c_width * 0.3,
            position=(c_width * 0.4, v),
        )
        self._maximum_ping_edit = bui.textwidget(
            parent=self._root_widget,
            size=(c_width * 0.3, 40),
            h_align='left',
            v_align='center',
            text=str(randomjoin.maximum_ping),
            editable=True,
            description='Maximum ping (ms)',
            position=(c_width * 0.6, v - 20),
            autoselect=True,
            max_chars=4,
        )
        v -= 60
        bui.textwidget(
            parent=self._root_widget,
            size=(0, 0),
            h_align='right',
            v_align='center',
            text='Minimum players',
            maxwidth=c_width * 0.3,
            position=(c_width * 0.4, v),
        )
        self._minimum_players_edit = bui.textwidget(
            parent=self._root_widget,
            size=(c_width * 0.3, 40),
            h_align='left',
            v_align='center',
            text=str(randomjoin.minimum_players),
            editable=True,
            description='Minimum number of players',
            position=(c_width * 0.6, v - 20),
            autoselect=True,
            max_chars=4,
        )
        v -= 60

        # Cancel button.
        self.cancel_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            label=babase.Lstr(resource='cancelText'),
            size=(180, 60),
            color=(1.0, 0.2, 0.2),
            position=(40, 30),
            on_activate_call=self._cancel,
            autoselect=True,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        # Save button.
        self.savebtn = btn = bui.buttonwidget(
            parent=self._root_widget,
            label=babase.Lstr(resource='saveText'),
            size=(180, 60),
            position=(c_width - 200, 30),
            on_activate_call=self._save,
            autoselect=True,
        )
        bui.containerwidget(edit=self._root_widget, start_button=btn)

    def _save(self) -> None:
        errored = False
        minimum_players: int | None = None
        maximum_ping: int | None = None
        try:
            minimum_players = int(
                bui.textwidget(query=self._minimum_players_edit))
        except ValueError:
            bui.screenmessage('"Minimum players" should be integer',
                              color=(1, 0, 0))
            bui.getsound('error').play()
            errored = True
        try:
            maximum_ping = int(
                bui.textwidget(query=self._maximum_ping_edit))
        except ValueError:
            bui.screenmessage('"Maximum ping" should be integer',
                              color=(1, 0, 0))
            bui.getsound('error').play()
            errored = True
        if errored:
            return

        assert minimum_players is not None
        assert maximum_ping is not None

        if minimum_players < 0:
            bui.screenmessage('"Minimum players" should be at least 0',
                              color=(1, 0, 0))
            bui.getsound('error').play()
            errored = True

        if maximum_ping <= 0:
            bui.screenmessage('"Maximum ping" should be greater than 0',
                              color=(1, 0, 0))
            bui.getsound('error').play()
            bui.screenmessage('(use 9999 as dont-care value)',
                              color=(1, 0, 0))
            errored = True

        if errored:
            return

        randomjoin.maximum_ping = maximum_ping
        randomjoin.minimum_players = minimum_players

        randomjoin.commit_config()
        bui.getsound('shieldUp').play()
        self._transition_out()

    def _cancel(self) -> None:
        bui.getsound('shieldDown').play()
        self._transition_out()

    def _transition_out(self) -> None:
        bui.containerwidget(edit=self._root_widget, transition='out_scale')


class RandomJoin:
    def __init__(self) -> None:
        self.cached_parties: list[PartyEntry] = []
        self.maximum_ping: int = 9999
        self.minimum_players: int = 2
        self.load_config()

    def load_config(self) -> None:
        cfg = babase.app.config.get('Random Join', {
            'maximum_ping': self.maximum_ping,
            'minimum_players': self.minimum_players,
        })
        try:
            self.maximum_ping = cfg['maximum_ping']
            self.minimum_players = cfg['minimum_players']
        except KeyError:
            bui.screenmessage('Error: RandomJoin config is broken, resetting..',
                              color=(1, 0, 0), log=True)
            bui.getsound('error').play()
            self.commit_config()

    def commit_config(self) -> None:
        babase.app.config['Random Join'] = {
            'maximum_ping': self.maximum_ping,
            'minimum_players': self.minimum_players,
        }
        babase.app.config.commit()


randomjoin = RandomJoin()


# ba_meta require api 9
# ba_meta export babase.Plugin
class RandomJoinPlugin(babase.Plugin):
    def on_app_running(self) -> None:
        # I feel bad that all patching logic happens not here.
        pass
