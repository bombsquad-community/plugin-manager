"""===========MAX_PLAYERS==========="""

# ba_meta require api 7
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations
from typing import TYPE_CHECKING

import ba
import _ba
from ba._session import Session
from ba._coopsession import CoopSession, TEAM_COLORS, TEAM_NAMES
from ba._multiteamsession import MultiTeamSession
from bastd.ui.gather import GatherWindow
from bastd.ui.popup import PopupWindow

if TYPE_CHECKING:
    from typing import List, Any, Optional, Sequence


cfg = ba.app.config
cmp = {'coop_max_players': 4,
       'teams_max_players': 8,
       'ffa_max_players': 8}

lang = ba.app.lang.language
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
                 parent: ba.Widget,
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
        self.nametext = ba.textwidget(
            parent=parent,
            position=(position[0], position[1]),
            size=(100, 30),
            text=text,
            maxwidth=150,
            color=(0.8, 0.8, 0.8, 1.0),
            h_align='left',
            v_align='center',
            scale=textscale)
        self.valuetext = ba.textwidget(
            parent=parent,
            position=(position[0]+150, position[1]),
            size=(60, 28),
            editable=False,
            color=(0.3, 1.0, 0.3, 1.0),
            h_align='right',
            v_align='center',
            text=str(value),
            padding=2)
        self.minusbutton = ba.buttonwidget(
            parent=parent,
            position=(position[0]+240, position[1]),
            size=(28, 28),
            label='-',
            autoselect=True,
            on_activate_call=ba.Call(self._down),
            repeat=True)
        self.plusbutton = ba.buttonwidget(
            parent=parent,
            position=(position[0]+290, position[1]),
            size=(28, 28),
            label='+',
            autoselect=True,
            on_activate_call=ba.Call(self._up),
            repeat=True)

    def _up(self) -> None:
        self._value = min(self._maxval, self._value + self._increment)
        self._update_display()

    def _down(self) -> None:
        self._value = max(self._minval, self._value - self._increment)
        self._update_display()

    def _update_display(self) -> None:
        ba.textwidget(edit=self.valuetext, text=str(self._value))
        cfg['Config Max Players'][self._config] = self._value
        cfg.apply_and_commit()


class SettingsMaxPlayers(PopupWindow):

    def __init__(self):
        # pylint: disable=too-many-locals
        uiscale = ba.app.ui.uiscale
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

        self._cancel_button = ba.buttonwidget(
            parent=self.root_widget,
            position=(25, self._height - 40),
            size=(50, 50),
            scale=0.58,
            label='',
            color=bg_color,
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=ba.gettexture('crossOut'),
            iconscale=1.2)
        ba.containerwidget(edit=self.root_widget,
                           cancel_button=self._cancel_button)

        ba.textwidget(
            parent=self.root_widget,
            position=(self._width * 0.5, self._height - 30),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.8,
            text=title_text,
            maxwidth=200,
            color=ba.app.ui.title_color)

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
            ba.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._transition_out()


def __init__(self) -> None:
    """Instantiate a co-op mode session."""
    # pylint: disable=cyclic-import
    from ba._campaign import getcampaign
    from bastd.activity.coopjoin import CoopJoinActivity

    _ba.increment_analytics_count('Co-op session start')
    app = _ba.app

    # If they passed in explicit min/max, honor that.
    # Otherwise defer to user overrides or defaults.
    if 'min_players' in app.coop_session_args:
        min_players = app.coop_session_args['min_players']
    else:
        min_players = 1
    if 'max_players' in app.coop_session_args:
        max_players = app.coop_session_args['max_players']
    else:
        max_players = app.config.get(
            'Coop Game Max Players',
            cfg['Config Max Players']['coop_max_players'])

    # print('FIXME: COOP SESSION WOULD CALC DEPS.')
    depsets: Sequence[ba.DependencySet] = []

    Session.__init__(self,
                     depsets,
                     team_names=TEAM_NAMES,
                     team_colors=TEAM_COLORS,
                     min_players=min_players,
                     max_players=max_players)

    # Tournament-ID if we correspond to a co-op tournament (otherwise None)
    self.tournament_id: Optional[str] = (
        app.coop_session_args.get('tournament_id'))

    self.campaign = getcampaign(app.coop_session_args['campaign'])
    self.campaign_level_name: str = app.coop_session_args['level']

    self._ran_tutorial_activity = False
    self._tutorial_activity: Optional[ba.Activity] = None
    self._custom_menu_ui: List[Dict[str, Any]] = []

    # Start our joining screen.
    self.setactivity(_ba.newactivity(CoopJoinActivity))

    self._next_game_instance: Optional[ba.GameActivity] = None
    self._next_game_level_name: Optional[str] = None
    self._update_on_deck_game_instances()


def get_max_players(self) -> int:
    """Return max number of ba.Players allowed to join the game at once."""
    if self.use_teams:
        return _ba.app.config.get(
            'Team Game Max Players',
            cfg['Config Max Players']['teams_max_players'])
    return _ba.app.config.get(
        'Free-for-All Max Players',
        cfg['Config Max Players']['ffa_max_players'])


GatherWindow.__old_init__ = GatherWindow.__init__


def __gather_init__(self,
                    transition: Optional[str] = 'in_right',
                    origin_widget: ba.Widget = None):
    self.__old_init__(transition, origin_widget)

    def _do_max_players():
        SettingsMaxPlayers()
    self._max_players_button = ba.buttonwidget(
        parent=self._root_widget,
        position=(self._width*0.72, self._height*0.91),
        size=(220, 60),
        scale=1.0,
        color=(0.6, 0.0, 0.9),
        icon=ba.gettexture('usersButton'),
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
        ba.app.ui.window_states[type(self)] = {
            'sel_name': sel_name,
        }
    except Exception:
        ba.print_exception(f'Error saving state for {self}.')


def _restore_state(self) -> None:
    from efro.util import enum_by_value
    try:
        for tab in self._tabs.values():
            tab.restore_state()

        sel: Optional[ba.Widget]
        winstate = ba.app.ui.window_states.get(type(self), {})
        sel_name = winstate.get('sel_name', None)
        assert isinstance(sel_name, (str, type(None)))
        current_tab = self.TabID.ABOUT
        gather_tab_val = ba.app.config.get('Gather Tab')
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
        ba.containerwidget(edit=self._root_widget, selected_child=sel)
    except Exception:
        ba.print_exception('Error restoring gather-win state.')

# ba_meta export plugin


class MaxPlayersPlugin(ba.Plugin):

    def has_settings_ui(self) -> bool:
        return True

    def show_settings_ui(self, source_widget: ba.Widget | None) -> None:
        SettingsMaxPlayers()

    if 'Config Max Players' in ba.app.config:
        old_config = ba.app.config['Config Max Players']
        for setting in cmp:
            if setting not in old_config:
                ba.app.config['Config Max Players'].update({setting: cmp[setting]})
        remove_list = []
        for setting in old_config:
            if setting not in cmp:
                remove_list.append(setting)
        for element in remove_list:
            ba.app.config['Config Max Players'].pop(element)
    else:
        ba.app.config['Config Max Players'] = cmp
    ba.app.config.apply_and_commit()

    CoopSession.__init__ = __init__
    MultiTeamSession.get_max_players = get_max_players
    GatherWindow.__init__ = __gather_init__
    GatherWindow._save_state = _save_state
    GatherWindow._restore_state = _restore_state
