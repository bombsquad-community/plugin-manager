"""===========MAX_PLAYERS==========="""

# ba_meta require api 9

from __future__ import annotations
from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs
import _babase
from bascenev1._session import Session
from bascenev1._coopsession import CoopSession, TEAM_COLORS, TEAM_NAMES
from bascenev1._multiteamsession import MultiTeamSession
from bauiv1lib.gather import GatherWindow
from bauiv1lib.popup import PopupWindow

if TYPE_CHECKING:
    from typing import List, Any, Optional, Sequence


cfg = babase.app.config
cmp = {'coop_max_players': 4,
       'teams_max_players': 8,
       'ffa_max_players': 8}

lang = bs.app.lang.language
if lang == 'Spanish':
    title_text = 'Máximo de Jugadores'
    title_short_text = 'Jugadores'
    coop_text = 'Cooperativo'
    teams_text = 'Equipos'
    ffa_text = 'Todos Contra Todos'
else:
    title_text = 'Max Players'
    title_short_text = 'Players'
    coop_text = 'Co-op'
    teams_text = 'Teams'
    ffa_text = 'FFA'


class ConfigNumberEdit:

    def __init__(self,
                 parent: bui.Widget,
                 position: Tuple[float, float],
                 value: int,
                 config: str,
                 text: str):
        self._increment = 1
        self._minval = 1
        self._maxval = 100
        self._value = value
        self._config = config

        textscale = 1.0
        self.nametext = bui.textwidget(
            parent=parent,
            position=(position[0], position[1]),
            size=(100, 30),
            text=text,
            maxwidth=150,
            color=(0.8, 0.8, 0.8, 1.0),
            h_align='left',
            v_align='center',
            scale=textscale)
        self.valuetext = bui.textwidget(
            parent=parent,
            position=(position[0]+150, position[1]),
            size=(60, 28),
            editable=False,
            color=(0.3, 1.0, 0.3, 1.0),
            h_align='right',
            v_align='center',
            text=str(value),
            padding=2)
        self.minusbutton = bui.buttonwidget(
            parent=parent,
            position=(position[0]+240, position[1]),
            size=(28, 28),
            label='-',
            autoselect=True,
            on_activate_call=babase.Call(self._down),
            repeat=True)
        self.plusbutton = bui.buttonwidget(
            parent=parent,
            position=(position[0]+290, position[1]),
            size=(28, 28),
            label='+',
            autoselect=True,
            on_activate_call=babase.Call(self._up),
            repeat=True)

    def _up(self) -> None:
        self._value = min(self._maxval, self._value + self._increment)
        self._update_display()

    def _down(self) -> None:
        self._value = max(self._minval, self._value - self._increment)
        self._update_display()

    def _update_display(self) -> None:
        bui.textwidget(edit=self.valuetext, text=str(self._value))
        cfg['Config Max Players'][self._config] = self._value
        cfg.apply_and_commit()


class SettingsMaxPlayers(PopupWindow):

    def __init__(self):
        # pylint: disable=too-many-locals
        uiscale = bui.app.ui_v1.uiscale
        self._transitioning_out = False
        self._width = 400
        self._height = 220
        bg_color = (0.5, 0.4, 0.6)

        # creates our _root_widget
        PopupWindow.__init__(self,
                             position=(0.0, 0.0),
                             size=(self._width, self._height),
                             scale=1.2,
                             bg_color=bg_color)

        self._cancel_button = bui.buttonwidget(
            parent=self.root_widget,
            position=(25, self._height - 40),
            size=(50, 50),
            scale=0.58,
            label='',
            color=bg_color,
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=bui.gettexture('crossOut'),
            iconscale=1.2)
        bui.containerwidget(edit=self.root_widget,
                            cancel_button=self._cancel_button)

        bui.textwidget(
            parent=self.root_widget,
            position=(self._width * 0.5, self._height - 30),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.8,
            text=title_text,
            maxwidth=200,
            color=bui.app.ui_v1.title_color)

        posx = 33
        posy = self._height

        # co-op
        ConfigNumberEdit(parent=self.root_widget,
                         position=(posx, posy*0.6),
                         value=cfg['Config Max Players']['coop_max_players'],
                         config='coop_max_players',
                         text=coop_text)

        # teams
        ConfigNumberEdit(parent=self.root_widget,
                         position=(posx, posy*0.38),
                         value=cfg['Config Max Players']['teams_max_players'],
                         config='teams_max_players',
                         text=teams_text)

        # ffa
        ConfigNumberEdit(parent=self.root_widget,
                         position=(posx, posy*0.16),
                         value=cfg['Config Max Players']['ffa_max_players'],
                         config='ffa_max_players',
                         text=ffa_text)

    def _on_cancel_press(self) -> None:
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._transition_out()


def __init__(self) -> None:
    """Instantiate a co-op mode session."""
    # pylint: disable=cyclic-import
    getcampaign = bui.app.classic.getcampaign
    from bascenev1lib.activity.coopjoin import CoopJoinActivity

    _babase.increment_analytics_count('Co-op session start')
    app = babase.app
    classic = app.classic

    # If they passed in explicit min/max, honor that.
    # Otherwise defer to user overrides or defaults.
    if 'min_players' in classic.coop_session_args:
        min_players = classic.coop_session_args['min_players']
    else:
        min_players = 1
    if 'max_players' in classic.coop_session_args:
        max_players = classic.coop_session_args['max_players']
    else:
        max_players = app.config.get(
            'Coop Game Max Players',
            cfg['Config Max Players']['coop_max_players'])

    # print('FIXME: COOP SESSION WOULD CALC DEPS.')
    depsets: Sequence[babase.DependencySet] = []

    Session.__init__(self,
                     depsets,
                     team_names=TEAM_NAMES,
                     team_colors=TEAM_COLORS,
                     min_players=min_players,
                     max_players=max_players)

    # Tournament-ID if we correspond to a co-op tournament (otherwise None)
    self.tournament_id: Optional[str] = (
        classic.coop_session_args.get('tournament_id'))

    self.campaign = getcampaign(classic.coop_session_args['campaign'])
    self.campaign_level_name: str = classic.coop_session_args['level']

    self._ran_tutorial_activity = False
    self._tutorial_activity: Optional[babase.Activity] = None
    self._custom_menu_ui: List[Dict[str, Any]] = []

    # Start our joining screen.
    self.setactivity(bs.newactivity(CoopJoinActivity))

    self._next_game_instance: Optional[bs.GameActivity] = None
    self._next_game_level_name: Optional[str] = None
    self._update_on_deck_game_instances()


def get_max_players(self) -> int:
    """Return max number of bs.Players allowed to join the game at once."""
    if self.use_teams:
        return _babase.app.config.get(
            'Team Game Max Players',
            cfg['Config Max Players']['teams_max_players'])
    return _babase.app.config.get(
        'Free-for-All Max Players',
        cfg['Config Max Players']['ffa_max_players'])


GatherWindow.__old_init__ = GatherWindow.__init__


def __gather_init__(self,
                    transition: Optional[str] = 'in_right',
                    origin_widget: bui.Widget = None):
    self.__old_init__(transition, origin_widget)

    def _do_max_players():
        SettingsMaxPlayers()
    self._max_players_button = bui.buttonwidget(
        parent=self._root_widget,
        position=(self._width*0.72, self._height*0.91),
        size=(220, 60),
        scale=1.0,
        color=(0.6, 0.0, 0.9),
        icon=bui.gettexture('usersButton'),
        iconscale=1.5,
        autoselect=True,
        label=title_short_text,
        button_type='regular',
        on_activate_call=_do_max_players)


def _save_state(self) -> None:
    try:
        for tab in self._tabs.values():
            tab.save_state()

        sel = self._root_widget.get_selected_child()
        selected_tab_ids = [
            tab_id for tab_id, tab in self._tab_row.tabs.items()
            if sel == tab.button
        ]
        if sel == self._back_button:
            sel_name = 'Back'
        elif sel == self._max_players_button:
            sel_name = 'Max Players'
        elif selected_tab_ids:
            assert len(selected_tab_ids) == 1
            sel_name = f'Tab:{selected_tab_ids[0].value}'
        elif sel == self._tab_container:
            sel_name = 'TabContainer'
        else:
            raise ValueError(f'unrecognized selection: \'{sel}\'')
        bui.app.ui_v1.window_states[type(self)] = {
            'sel_name': sel_name,
        }
    except Exception:
        babase.print_exception(f'Error saving state for {self}.')


def _restore_state(self) -> None:
    from efro.util import enum_by_value
    try:
        for tab in self._tabs.values():
            tab.restore_state()

        sel: Optional[bui.Widget]
        winstate = bui.app.ui_v1.window_states.get(type(self), {})
        sel_name = winstate.get('sel_name', None)
        assert isinstance(sel_name, (str, type(None)))
        current_tab = self.TabID.ABOUT
        gather_tab_val = babase.app.config.get('Gather Tab')
        try:
            stored_tab = enum_by_value(self.TabID, gather_tab_val)
            if stored_tab in self._tab_row.tabs:
                current_tab = stored_tab
        except ValueError:
            pass
        self._set_tab(current_tab)
        if sel_name == 'Back':
            sel = self._back_button
        elif sel_name == 'Max Players':
            sel = self._back_button
        elif sel_name == 'TabContainer':
            sel = self._tab_container
        elif isinstance(sel_name, str) and sel_name.startswith('Tab:'):
            try:
                sel_tab_id = enum_by_value(self.TabID,
                                           sel_name.split(':')[-1])
            except ValueError:
                sel_tab_id = self.TabID.ABOUT
            sel = self._tab_row.tabs[sel_tab_id].button
        else:
            sel = self._tab_row.tabs[current_tab].button
        bui.containerwidget(edit=self._root_widget, selected_child=sel)
    except Exception:
        babase.print_exception('Error restoring gather-win state.')

# ba_meta export babase.Plugin


class MaxPlayersPlugin(babase.Plugin):

    def has_settings_ui(self) -> bool:
        return True

    def show_settings_ui(self, source_widget: bui.Widget | None) -> None:
        SettingsMaxPlayers()

    if 'Config Max Players' in babase.app.config:
        old_config = babase.app.config['Config Max Players']
        for setting in cmp:
            if setting not in old_config:
                babase.app.config['Config Max Players'].update({setting: cmp[setting]})
        remove_list = []
        for setting in old_config:
            if setting not in cmp:
                remove_list.append(setting)
        for element in remove_list:
            babase.app.config['Config Max Players'].pop(element)
    else:
        babase.app.config['Config Max Players'] = cmp
    babase.app.config.apply_and_commit()

    CoopSession.__init__ = __init__
    MultiTeamSession.get_max_players = get_max_players
    GatherWindow.__init__ = __gather_init__
    GatherWindow._save_state = _save_state
    GatherWindow._restore_state = _restore_state
