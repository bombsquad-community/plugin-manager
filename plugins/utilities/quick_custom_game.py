# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs
import _babase
from bauiv1lib.play import PlayWindow
from bauiv1lib.playlist.addgame import PlaylistAddGameWindow
from bascenev1._freeforallsession import FreeForAllSession
from bascenev1lib.activity.multiteamjoin import MultiTeamJoinActivity

if TYPE_CHECKING:
    pass


lang = bs.app.lang.language

if lang == "Spanish":
    custom_txt = "personalizar..."
else:
    custom_txt = "custom..."


if "quick_game_button" in babase.app.config:
    config = babase.app.config["quick_game_button"]
else:
    config = {"selected": None, "config": None}
    babase.app.config["quick_game_button"] = config
    babase.app.config.commit()


def start_game(session: bs.Session, fadeout: bool = True):
    def callback():
        if fadeout:
            _babase.unlock_all_input()
        try:
            bs.new_host_session(session)
        except Exception:
            from bascenev1lib import mainmenu

            babase.print_exception("exception running session", session)

            # Drop back into a main menu session.
            bs.new_host_session(mainmenu.MainMenuSession)

    if fadeout:
        _babase.fade_screen(False, time=0.25, endcall=callback)
        _babase.lock_all_input()
    else:
        callback()


class SimplePlaylist:
    def __init__(self, settings: dict, gametype: type[bs.GameActivity]):
        self.settings = settings
        self.gametype = gametype

    def pull_next(self) -> None:
        if "map" not in self.settings["settings"]:
            settings = dict(map=self.settings["map"], **self.settings["settings"])
        else:
            settings = self.settings["settings"]
        return dict(resolved_type=self.gametype, settings=settings)


class CustomSession(FreeForAllSession):
    def __init__(self, *args, **kwargs):
        # pylint: disable=cyclic-import
        self.use_teams = False
        self._tutorial_activity_instance = None
        bs.Session.__init__(
            self,
            depsets=[],
            team_names=None,
            team_colors=None,
            min_players=1,
            max_players=self.get_max_players(),
        )

        self._series_length = 1
        self._ffa_series_length = 1

        # Which game activity we're on.
        self._game_number = 0
        self._playlist = SimplePlaylist(self._config, self._gametype)
        config["selected"] = self._gametype.__name__
        config["config"] = self._config
        babase.app.config.commit()

        # Get a game on deck ready to go.
        self._current_game_spec: Optional[Dict[str, Any]] = None
        self._next_game_spec: Dict[str, Any] = self._playlist.pull_next()
        self._next_game: Type[bs.GameActivity] = self._next_game_spec["resolved_type"]

        # Go ahead and instantiate the next game we'll
        # use so it has lots of time to load.
        self._instantiate_next_game()

        # Start in our custom join screen.
        self.setactivity(bs.newactivity(MultiTeamJoinActivity))


class SelectGameWindow(PlaylistAddGameWindow):
    def __init__(self, transition: str = "in_right"):
        class EditController:
            _sessiontype = bs.FreeForAllSession

            def get_session_type(self) -> Type[bs.Session]:
                return self._sessiontype

        self._editcontroller = EditController()
        self._r = "addGameWindow"
        uiscale = bui.app.ui_v1.uiscale
        self._width = 750 if uiscale is babase.UIScale.SMALL else 650
        x_inset = 50 if uiscale is babase.UIScale.SMALL else 0
        self._height = (
            346
            if uiscale is babase.UIScale.SMALL
            else 380
            if uiscale is babase.UIScale.MEDIUM
            else 440
        )
        top_extra = 30 if uiscale is babase.UIScale.SMALL else 20
        self._scroll_width = 210

        self._root_widget = bui.containerwidget(
            size=(self._width, self._height + top_extra),
            transition=transition,
            scale=(
                2.17
                if uiscale is babase.UIScale.SMALL
                else 1.5
                if uiscale is babase.UIScale.MEDIUM
                else 1.0
            ),
            stack_offset=(0, 1) if uiscale is babase.UIScale.SMALL else (0, 0),
        )

        self._back_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(58 + x_inset, self._height - 53),
            size=(165, 70),
            scale=0.75,
            text_scale=1.2,
            label=babase.Lstr(resource="backText"),
            autoselect=True,
            button_type="back",
            on_activate_call=self._back,
        )
        self._select_button = select_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width - (172 + x_inset), self._height - 50),
            autoselect=True,
            size=(160, 60),
            scale=0.75,
            text_scale=1.2,
            label=babase.Lstr(resource="selectText"),
            on_activate_call=self._add,
        )

        if bui.app.ui_v1.use_toolbars:
            bui.widget(
                edit=select_button, right_widget=bui.get_special_widget("party_button")
            )

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 28),
            size=(0, 0),
            scale=1.0,
            text=babase.Lstr(resource=self._r + ".titleText"),
            h_align="center",
            color=bui.app.ui_v1.title_color,
            maxwidth=250,
            v_align="center",
        )
        v = self._height - 64

        self._selected_title_text = bui.textwidget(
            parent=self._root_widget,
            position=(x_inset + self._scroll_width + 50 + 30, v - 15),
            size=(0, 0),
            scale=1.0,
            color=(0.7, 1.0, 0.7, 1.0),
            maxwidth=self._width - self._scroll_width - 150 - x_inset * 2,
            h_align="left",
            v_align="center",
        )
        v -= 30

        self._selected_description_text = bui.textwidget(
            parent=self._root_widget,
            position=(x_inset + self._scroll_width + 50 + 30, v),
            size=(0, 0),
            scale=0.7,
            color=(0.5, 0.8, 0.5, 1.0),
            maxwidth=self._width - self._scroll_width - 150 - x_inset * 2,
            h_align="left",
        )

        scroll_height = self._height - 100

        v = self._height - 60

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(x_inset + 61, v - scroll_height),
            size=(self._scroll_width, scroll_height),
            highlight=False,
        )
        bui.widget(
            edit=self._scrollwidget,
            up_widget=self._back_button,
            left_widget=self._back_button,
            right_widget=select_button,
        )
        self._column: Optional[bui.Widget] = None

        v -= 35
        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=self._back_button,
            start_button=select_button,
        )
        self._selected_game_type: Optional[Type[bs.GameActivity]] = None

        bui.containerwidget(edit=self._root_widget, selected_child=self._scrollwidget)

        self._game_types: list[type[bs.GameActivity]] = []

        # Get actual games loading in the bg.
        babase.app.meta.load_exported_classes(
            bs.GameActivity, self._on_game_types_loaded, completion_cb_in_bg_thread=True
        )

        # Refresh with our initial empty list. We'll refresh again once
        # game loading is complete.
        self._refresh()

        if config["selected"]:
            for gt in self._game_types:
                if gt.__name__ == config["selected"]:
                    self._refresh(selected=gt)
                    self._set_selected_game_type(gt)

    def _refresh(
        self, select_get_more_games_button: bool = False, selected: bool = None
    ) -> None:
        # from babase.internal import get_game_types

        if self._column is not None:
            self._column.delete()

        self._column = bui.columnwidget(parent=self._scrollwidget, border=2, margin=0)

        for i, gametype in enumerate(self._game_types):

            def _doit() -> None:
                if self._select_button:
                    bs.apptimer(0.1, self._select_button.activate)

            txt = bui.textwidget(
                parent=self._column,
                position=(0, 0),
                size=(self._width - 88, 24),
                text=gametype.get_display_string(),
                h_align="left",
                v_align="center",
                color=(0.8, 0.8, 0.8, 1.0),
                maxwidth=self._scroll_width * 0.8,
                on_select_call=babase.Call(self._set_selected_game_type, gametype),
                always_highlight=True,
                selectable=True,
                on_activate_call=_doit,
            )
            if i == 0:
                bui.widget(edit=txt, up_widget=self._back_button)

        self._get_more_games_button = bui.buttonwidget(
            parent=self._column,
            autoselect=True,
            label=babase.Lstr(resource=self._r + ".getMoreGamesText"),
            color=(0.54, 0.52, 0.67),
            textcolor=(0.7, 0.65, 0.7),
            on_activate_call=self._on_get_more_games_press,
            size=(178, 50),
        )
        if select_get_more_games_button:
            bui.containerwidget(
                edit=self._column,
                selected_child=self._get_more_games_button,
                visible_child=self._get_more_games_button,
            )

    def _add(self) -> None:
        _babase.lock_all_input()  # Make sure no more commands happen.
        bs.apptimer(0.1, _babase.unlock_all_input)
        gameconfig = {}
        if config["selected"] == self._selected_game_type.__name__:
            if config["config"]:
                gameconfig = config["config"]
        if "map" in gameconfig:
            gameconfig["settings"]["map"] = gameconfig.pop("map")
        self._selected_game_type.create_settings_ui(
            self._editcontroller.get_session_type(), gameconfig, self._edit_game_done
        )

    def _edit_game_done(self, config: Optional[Dict[str, Any]]) -> None:
        if config:
            CustomSession._config = config
            CustomSession._gametype = self._selected_game_type
            start_game(CustomSession)
        else:
            bui.app.ui_v1.clear_main_menu_window(transition="out_right")
            bui.app.ui_v1.set_main_menu_window(
                SelectGameWindow(transition="in_left").get_root_widget(),
                from_window=None,
            )

    def _back(self) -> None:
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(edit=self._root_widget, transition="out_right")
        bui.app.ui_v1.set_main_menu_window(
            PlayWindow(transition="in_left").get_root_widget(),
            from_window=self._root_widget,
        )


PlayWindow._old_init = PlayWindow.__init__


def __init__(self, *args, **kwargs):
    self._old_init()

    width = 800
    height = 550

    def do_quick_game() -> None:
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        self._save_state()
        bui.containerwidget(edit=self._root_widget, transition="out_left")
        bui.app.ui_v1.set_main_menu_window(
            SelectGameWindow().get_root_widget(), from_window=self._root_widget
        )

    self._quick_game_button = bui.buttonwidget(
        parent=self._root_widget,
        position=(width - 55 - 120, height - 132),
        autoselect=True,
        size=(120, 60),
        scale=1.1,
        text_scale=1.2,
        label=custom_txt,
        on_activate_call=do_quick_game,
        color=(0.54, 0.52, 0.67),
        textcolor=(0.7, 0.65, 0.7),
    )

    self._restore_state()


def states(self) -> None:
    return {
        "Team Games": self._teams_button,
        "Co-op Games": self._coop_button,
        "Free-for-All Games": self._free_for_all_button,
        "Back": self._back_button,
        "Quick Game": self._quick_game_button,
    }


def _save_state(self) -> None:
    swapped = {v: k for k, v in states(self).items()}
    if self._root_widget.get_selected_child() in swapped:
        bui.app.ui_v1.window_states[self.__class__.__name__] = swapped[
            self._root_widget.get_selected_child()
        ]
    else:
        babase.print_exception(f"Error saving state for {self}.")


def _restore_state(self) -> None:
    if not hasattr(self, "_quick_game_button"):
        return  # ensure that our monkey patched init ran
    if self.__class__.__name__ not in bui.app.ui_v1.window_states:
        bui.containerwidget(edit=self._root_widget, selected_child=self._coop_button)
        return
    sel = states(self).get(bui.app.ui_v1.window_states[self.__class__.__name__], None)
    if sel:
        bui.containerwidget(edit=self._root_widget, selected_child=sel)
    else:
        bui.containerwidget(edit=self._root_widget, selected_child=self._coop_button)
        babase.print_exception(f"Error restoring state for {self}.")


# ba_meta export plugin
class QuickGamePlugin(babase.Plugin):
    PlayWindow.__init__ = __init__
    PlayWindow._save_state = _save_state
    PlayWindow._restore_state = _restore_state
