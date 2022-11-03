# ba_meta require api 7
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import _ba
from bastd.ui.play import PlayWindow
from bastd.ui.playlist.addgame import PlaylistAddGameWindow
from ba._freeforallsession import FreeForAllSession
from bastd.activity.multiteamjoin import MultiTeamJoinActivity

if TYPE_CHECKING:
    pass


lang = ba.app.lang.language

if lang == 'Spanish':
    custom_txt = 'personalizar...'
else:
    custom_txt = 'custom...'


if 'quick_game_button' in ba.app.config:
    config = ba.app.config['quick_game_button']
else:
    config = {'selected': None, 'config': None}
    ba.app.config['quick_game_button'] = config
    ba.app.config.commit()


def start_game(session: ba.Session, fadeout: bool = True):
    def callback():
        if fadeout:
            _ba.unlock_all_input()
        try:
            _ba.new_host_session(session)
        except Exception:
            from bastd import mainmenu
            ba.print_exception('exception running session', session)

            # Drop back into a main menu session.
            _ba.new_host_session(mainmenu.MainMenuSession)

    if fadeout:
        _ba.fade_screen(False, time=0.25, endcall=callback)
        _ba.lock_all_input()
    else:
        callback()


class SimplePlaylist:

    def __init__(self,
                 settings: dict,
                 gametype: type[ba.GameActivity]):
        self.settings = settings
        self.gametype = gametype

    def pull_next(self) -> None:
        if 'map' not in self.settings['settings']:
            settings = dict(
                map=self.settings['map'], **self.settings['settings'])
        else:
            settings = self.settings['settings']
        return dict(resolved_type=self.gametype, settings=settings)


class CustomSession(FreeForAllSession):

    def __init__(self, *args, **kwargs):
        # pylint: disable=cyclic-import
        self.use_teams = False
        self._tutorial_activity_instance = None
        ba.Session.__init__(self, depsets=[],
                            team_names=None,
                            team_colors=None,
                            min_players=1,
                            max_players=self.get_max_players())

        self._series_length = 1
        self._ffa_series_length = 1

        # Which game activity we're on.
        self._game_number = 0
        self._playlist = SimplePlaylist(self._config, self._gametype)
        config['selected'] = self._gametype.__name__
        config['config'] = self._config
        ba.app.config.commit()

        # Get a game on deck ready to go.
        self._current_game_spec: Optional[Dict[str, Any]] = None
        self._next_game_spec: Dict[str, Any] = self._playlist.pull_next()
        self._next_game: Type[ba.GameActivity] = (
            self._next_game_spec['resolved_type'])

        # Go ahead and instantiate the next game we'll
        # use so it has lots of time to load.
        self._instantiate_next_game()

        # Start in our custom join screen.
        self.setactivity(_ba.newactivity(MultiTeamJoinActivity))


class SelectGameWindow(PlaylistAddGameWindow):

    def __init__(self, transition: str = 'in_right'):
        class EditController:
            _sessiontype = ba.FreeForAllSession

            def get_session_type(self) -> Type[ba.Session]:
                return self._sessiontype

        self._editcontroller = EditController()
        self._r = 'addGameWindow'
        uiscale = ba.app.ui.uiscale
        self._width = 750 if uiscale is ba.UIScale.SMALL else 650
        x_inset = 50 if uiscale is ba.UIScale.SMALL else 0
        self._height = (346 if uiscale is ba.UIScale.SMALL else
                        380 if uiscale is ba.UIScale.MEDIUM else 440)
        top_extra = 30 if uiscale is ba.UIScale.SMALL else 20
        self._scroll_width = 210

        self._root_widget = ba.containerwidget(
            size=(self._width, self._height + top_extra),
            transition=transition,
            scale=(2.17 if uiscale is ba.UIScale.SMALL else
                   1.5 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, 1) if uiscale is ba.UIScale.SMALL else (0, 0))

        self._back_button = ba.buttonwidget(parent=self._root_widget,
                                            position=(58 + x_inset,
                                                      self._height - 53),
                                            size=(165, 70),
                                            scale=0.75,
                                            text_scale=1.2,
                                            label=ba.Lstr(resource='backText'),
                                            autoselect=True,
                                            button_type='back',
                                            on_activate_call=self._back)
        self._select_button = select_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(self._width - (172 + x_inset), self._height - 50),
            autoselect=True,
            size=(160, 60),
            scale=0.75,
            text_scale=1.2,
            label=ba.Lstr(resource='selectText'),
            on_activate_call=self._add)

        if ba.app.ui.use_toolbars:
            ba.widget(edit=select_button,
                      right_widget=_ba.get_special_widget('party_button'))

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height - 28),
                      size=(0, 0),
                      scale=1.0,
                      text=ba.Lstr(resource=self._r + '.titleText'),
                      h_align='center',
                      color=ba.app.ui.title_color,
                      maxwidth=250,
                      v_align='center')
        v = self._height - 64

        self._selected_title_text = ba.textwidget(
            parent=self._root_widget,
            position=(x_inset + self._scroll_width + 50 + 30, v - 15),
            size=(0, 0),
            scale=1.0,
            color=(0.7, 1.0, 0.7, 1.0),
            maxwidth=self._width - self._scroll_width - 150 - x_inset * 2,
            h_align='left',
            v_align='center')
        v -= 30

        self._selected_description_text = ba.textwidget(
            parent=self._root_widget,
            position=(x_inset + self._scroll_width + 50 + 30, v),
            size=(0, 0),
            scale=0.7,
            color=(0.5, 0.8, 0.5, 1.0),
            maxwidth=self._width - self._scroll_width - 150 - x_inset * 2,
            h_align='left')

        scroll_height = self._height - 100

        v = self._height - 60

        self._scrollwidget = ba.scrollwidget(parent=self._root_widget,
                                             position=(x_inset + 61,
                                                       v - scroll_height),
                                             size=(self._scroll_width,
                                                   scroll_height),
                                             highlight=False)
        ba.widget(edit=self._scrollwidget,
                  up_widget=self._back_button,
                  left_widget=self._back_button,
                  right_widget=select_button)
        self._column: Optional[ba.Widget] = None

        v -= 35
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=self._back_button,
                           start_button=select_button)
        self._selected_game_type: Optional[Type[ba.GameActivity]] = None

        ba.containerwidget(edit=self._root_widget,
                           selected_child=self._scrollwidget)

        self._game_types: list[type[ba.GameActivity]] = []

        # Get actual games loading in the bg.
        ba.app.meta.load_exported_classes(ba.GameActivity,
                                          self._on_game_types_loaded,
                                          completion_cb_in_bg_thread=True)

        # Refresh with our initial empty list. We'll refresh again once
        # game loading is complete.
        self._refresh()

        if config['selected']:
            for gt in self._game_types:
                if gt.__name__ == config['selected']:
                    self._refresh(selected=gt)
                    self._set_selected_game_type(gt)

    def _refresh(self,
                 select_get_more_games_button: bool = False,
                 selected: bool = None) -> None:
        # from ba.internal import get_game_types

        if self._column is not None:
            self._column.delete()

        self._column = ba.columnwidget(parent=self._scrollwidget,
                                       border=2,
                                       margin=0)

        for i, gametype in enumerate(self._game_types):

            def _doit() -> None:
                if self._select_button:
                    ba.timer(0.1,
                             self._select_button.activate,
                             timetype=ba.TimeType.REAL)

            txt = ba.textwidget(parent=self._column,
                                position=(0, 0),
                                size=(self._width - 88, 24),
                                text=gametype.get_display_string(),
                                h_align='left',
                                v_align='center',
                                color=(0.8, 0.8, 0.8, 1.0),
                                maxwidth=self._scroll_width * 0.8,
                                on_select_call=ba.Call(
                                    self._set_selected_game_type, gametype),
                                always_highlight=True,
                                selectable=True,
                                on_activate_call=_doit)
            if i == 0:
                ba.widget(edit=txt, up_widget=self._back_button)

        self._get_more_games_button = ba.buttonwidget(
            parent=self._column,
            autoselect=True,
            label=ba.Lstr(resource=self._r + '.getMoreGamesText'),
            color=(0.54, 0.52, 0.67),
            textcolor=(0.7, 0.65, 0.7),
            on_activate_call=self._on_get_more_games_press,
            size=(178, 50))
        if select_get_more_games_button:
            ba.containerwidget(edit=self._column,
                               selected_child=self._get_more_games_button,
                               visible_child=self._get_more_games_button)

    def _add(self) -> None:
        _ba.lock_all_input()  # Make sure no more commands happen.
        ba.timer(0.1, _ba.unlock_all_input, timetype=ba.TimeType.REAL)
        gameconfig = {}
        if config['selected'] == self._selected_game_type.__name__:
            if config['config']:
                gameconfig = config['config']
        if 'map' in gameconfig:
            gameconfig['settings']['map'] = gameconfig.pop('map')
        self._selected_game_type.create_settings_ui(
            self._editcontroller.get_session_type(),
            gameconfig,
            self._edit_game_done)

    def _edit_game_done(self, config: Optional[Dict[str, Any]]) -> None:
        if config:
            CustomSession._config = config
            CustomSession._gametype = self._selected_game_type
            start_game(CustomSession)
        else:
            ba.app.ui.clear_main_menu_window(transition='out_right')
            ba.app.ui.set_main_menu_window(
                SelectGameWindow(transition='in_left').get_root_widget())

    def _back(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            PlayWindow(transition='in_left').get_root_widget())


PlayWindow._old_init = PlayWindow.__init__


def __init__(self, *args, **kwargs):
    self._old_init()

    width = 800
    height = 550

    def do_quick_game() -> None:
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            SelectGameWindow().get_root_widget())

    self._quick_game_button = ba.buttonwidget(
        parent=self._root_widget,
        position=(width - 55 - 120, height - 132),
        autoselect=True,
        size=(120, 60),
        scale=1.1,
        text_scale=1.2,
        label=custom_txt,
        on_activate_call=do_quick_game,
        color=(0.54, 0.52, 0.67),
        textcolor=(0.7, 0.65, 0.7))

    self._restore_state()


def states(self) -> None:
    return {
        'Team Games': self._teams_button,
        'Co-op Games': self._coop_button,
        'Free-for-All Games': self._free_for_all_button,
        'Back': self._back_button,
        'Quick Game': self._quick_game_button
    }


def _save_state(self) -> None:
    swapped = {v: k for k, v in states(self).items()}
    if self._root_widget.get_selected_child() in swapped:
        ba.app.ui.window_states[
            self.__class__.__name__] = swapped[
                self._root_widget.get_selected_child()]
    else:
        ba.print_exception(f'Error saving state for {self}.')


def _restore_state(self) -> None:
    if not hasattr(self, '_quick_game_button'):
        return  # ensure that our monkey patched init ran
    if self.__class__.__name__ not in ba.app.ui.window_states:
        ba.containerwidget(edit=self._root_widget,
                           selected_child=self._coop_button)
        return
    sel = states(self).get(
        ba.app.ui.window_states[self.__class__.__name__], None)
    if sel:
        ba.containerwidget(edit=self._root_widget, selected_child=sel)
    else:
        ba.containerwidget(edit=self._root_widget,
                           selected_child=self._coop_button)
        ba.print_exception(f'Error restoring state for {self}.')


# ba_meta export plugin
class QuickGamePlugin(ba.Plugin):
    PlayWindow.__init__ = __init__
    PlayWindow._save_state = _save_state
    PlayWindow._restore_state = _restore_state
