# ba_meta require api 9
from dataclasses import replace
from random import choice, randint
from typing import Any, Union

# pylint: disable=import-error
import babase
from bascenev1 import (
    Session,
    MultiTeamSession,
    FreeForAllSession,
    DualTeamSession,
    GameActivity,
    newactivity,
    new_host_session,
)

from bauiv1 import Widget, UIScale, buttonwidget
from bascenev1lib.activity.multiteamjoin import MultiTeamJoinActivity

# BombSquad 1.8.0 replaced the classic playlist browser window with a doc-ui
# page. Exactly one of these is set on a build this plugin supports.
try:
    import bauiv1lib.playlist.browserdocui as browserdocui
    import bacommon.docui.v2 as dui2
    from bacommon.docui.routes import PressSound
    from bacommon.langstr import LangStrSpecValue
    PlaylistBrowserWindow = None
except ImportError:
    browserdocui = None
    from bauiv1lib.playlist.browser import PlaylistBrowserWindow

plugman = dict(
    plugin_name="random_play",
    description="Play randomly generated FFA or Teams matches from your installed minigames and maps.",
    external_url="",
    authors=[
        {"name": "silver_volt4", "email": "", "discord": "Silver_Volt4#6502", "github": ""},
    ],
    version="1.2.0",
)

# Session.__init__ dropped its leading depsets argument in 2026.
# (Read off the code object: inspect.signature() would evaluate the
# annotations, which name types the engine only imports for type checking.)
_code = Session.__init__.__code__
_SESSION_TAKES_DEPSETS = "depsets" in _code.co_varnames[:_code.co_argcount]

DEFAULT_TEAM_COLORS = ((0.1, 0.25, 1.0), (1.0, 0.25, 0.2))
DEFAULT_TEAM_NAMES = ("Blue", "Red")


# More or less copied from game code
# I have no idea what I'm doing here
class RandomPlaySessionMixin(MultiTeamSession, Session):
    def __init__(self, playlist) -> None:
        """Set up playlists & launch a bascenev1.Activity to accept joiners."""

        app = babase.app
        classic = app.classic
        assert classic is not None
        _cfg = app.config

        super(MultiTeamSession, self).__init__(
            *([[]] if _SESSION_TAKES_DEPSETS else []),
            team_names=DEFAULT_TEAM_NAMES,
            team_colors=DEFAULT_TEAM_COLORS,
            min_players=1,
            max_players=self.get_max_players(),
        )

        self._series_length: int = classic.teams_series_length
        self._ffa_series_length: int = classic.ffa_series_length

        self._tutorial_activity_instance = None
        self._game_number = 0

        # Our faux playlist
        self._playlist = playlist

        self._current_game_spec: dict[str, Any] | None = None
        self._next_game_spec: dict[str, Any] = self._playlist.pull_next()
        self._next_game: type[GameActivity] = self._next_game_spec["resolved_type"]

        self._instantiate_next_game()
        self.setactivity(newactivity(MultiTeamJoinActivity))


# Classes for Teams autopilot and FFA autopilot
# I think they have to be separate in order to comply with `ba.GameActivity.supports_session_type()`
class RandFreeForAllSession(FreeForAllSession, RandomPlaySessionMixin):
    def __init__(self):
        playlist = RandomPlaylist(FreeForAllSession)
        super(FreeForAllSession, self).__init__(playlist)


class RandDualTeamSession(DualTeamSession, RandomPlaySessionMixin):
    def __init__(self):
        playlist = RandomPlaylist(DualTeamSession)
        super(DualTeamSession, self).__init__(playlist)


# The faux playlist that just picks games at random
class RandomPlaylist:
    sessiontype: Session
    all_games: list[GameActivity]
    usable_games: list[GameActivity]

    last_game: str

    def __init__(self, sessiontype):
        self.sessiontype = sessiontype
        self.usable_games: list[GameActivity] = [
            gt
            for gt in RandomPlaylist.all_games
            if gt.supports_session_type(self.sessiontype)
        ]
        self.last_game = None

    def pull_next(self) -> dict[str, Any]:
        """
        Generate a new game at random.
        """

        has_only_one_game = len(self.usable_games) == 1

        while True:
            game = choice(self.usable_games)
            if game.name == self.last_game:
                # Don't repeat the same game twice
                if has_only_one_game:
                    # ...but don't freeze when there's only one game
                    break
            else:
                break

        self.last_game = game.name
        game_map = choice(game.get_supported_maps(self.sessiontype))
        settings = {
            s.name: s.default for s in game.get_available_settings(self.sessiontype)
        }
        settings["map"] = game_map

        if "Epic Mode" in settings:
            # Throw in an Epic Mode once in a while
            settings["Epic Mode"] = randint(0, 4) == 4

        return {"resolved_type": game, "settings": settings}


# Adapted from plugin quick_custom_game.
# Hope you don't mind.
def patched__init__(
    self,
    sessiontype: type[Session],
    transition: str | None = "in_right",
    origin_widget: Widget | None = None,
    playlist_select_context=None,
):
    width = 800
    height = 650

    ui_scale = babase.app.ui_v1.uiscale

    y_offset = -95 if ui_scale is UIScale.SMALL else -35 if ui_scale is UIScale.MEDIUM else 115
    x_offset = 140 if ui_scale is UIScale.SMALL else 80 if ui_scale is UIScale.MEDIUM else 240

    self.old__init__(sessiontype, transition, origin_widget)
    # pylint: disable=protected-access
    self._quick_game_button = buttonwidget(
        parent=self._root_widget,
        position=(width - 120 * 2 + x_offset, height - 132 + y_offset),
        autoselect=True,
        size=(80, 50),
        scale=0.6 if ui_scale is UIScale.SMALL else 1.15,
        text_scale=1.2,
        label="Random",
        on_activate_call=game_starter_factory(sessiontype),
        color=(0.54, 0.52, 0.67),
        textcolor=(0.7, 0.65, 0.7),
    )

# Returns a function that starts the game


def game_starter_factory(sessiontype: type[Session]):
    session: Union[RandFreeForAllSession, RandDualTeamSession] = None

    if issubclass(sessiontype, FreeForAllSession):
        session = RandFreeForAllSession
    elif issubclass(sessiontype, DualTeamSession):
        session = RandDualTeamSession
    else:
        raise RuntimeError("Can't determine session type")

    def on_run():
        can_start = False

        def do_start(game_list):
            nonlocal can_start
            RandomPlaylist.all_games = game_list
            if not can_start:  # Don't start if the screen fade is still ongoing
                can_start = True
            else:
                start()

        def has_faded():
            nonlocal can_start
            if not can_start:  # Don't start if it's still loading
                can_start = True
            else:
                start()

        def start():
            babase.unlock_all_input()
            new_host_session(session)

        babase.fade_screen(False, time=0.25, endcall=has_faded)
        babase.lock_all_input()
        if babase.app.env.engine_build_number >= 22379:
            # 1.7.40 added the leading export-name argument.
            babase.app.meta.load_exported_classes(
                "bascenev1.GameActivity", GameActivity, do_start
            )
        else:
            babase.app.meta.load_exported_classes(GameActivity, do_start)

    return on_run


_RANDOM_ACTION = "random_play"


if browserdocui is not None:
    class RandomPlaylistBrowserController(browserdocui.PlaylistBrowserController):
        """The playlist browser with a Random button beside Customize."""

        def fulfill_route(self, route):
            response = super().fulfill_route(route)
            # The last row holds the Customize button; clone it so ours
            # matches its size and style.
            row = response.page.rows[-1]
            template = row.buttons[0]
            row.buttons.append(
                replace(
                    template,
                    label=LangStrSpecValue.literal("Random"),
                    action=dui2.Local(
                        immediate_local_action=_RANDOM_ACTION,
                        immediate_local_action_args={"k": route.kind.value},
                    ),
                    widget_id=_RANDOM_ACTION,
                )
            )
            return response

        # Our action isn't in the page's typed action family, so handle it
        # before the typed decoding, which would reject it.
        def get_local_action_press_sound(self, name):
            if name == _RANDOM_ACTION:
                return PressSound.SWISH
            return super().get_local_action_press_sound(name)

        def local_action(self, action):
            if action.name != _RANDOM_ACTION:
                return super().local_action(action)
            if not action.window.main_window_has_control():
                return
            kind = browserdocui.SessionKind(action.args["k"])
            game_starter_factory(kind.sessiontype())()


# ba_meta export babase.Plugin
class RandomPlayPlugin(babase.Plugin):
    """
    A plugin that allows you to play randomly generated FFA or Teams matches by selecting a random minigame and map for each round.
    This eliminates the need to set up long playlists to enjoy all your BombSquad content.
    """

    def __init__(self):
        if browserdocui is not None:
            # The play page imports the controller by name on each press,
            # so rebinding it here is enough. (Private-party select mode
            # uses its own controller and is left alone.)
            browserdocui.PlaylistBrowserController = RandomPlaylistBrowserController
        else:
            PlaylistBrowserWindow.old__init__ = PlaylistBrowserWindow.__init__
            PlaylistBrowserWindow.__init__ = patched__init__
