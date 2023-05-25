# ba_meta require api 7
from random import choice, randint
from typing import Any, Union

# pylint: disable=import-error
import _ba
import ba
from bastd.ui.playlist.browser import PlaylistBrowserWindow

DEFAULT_TEAM_COLORS = ((0.1, 0.25, 1.0), (1.0, 0.25, 0.2))
DEFAULT_TEAM_NAMES = ("Blue", "Red")


# More or less copied from game code
# I have no idea what I'm doing here
class RandomPlaySessionMixin(ba.MultiTeamSession, ba.Session):
    def __init__(self, playlist) -> None:
        """Set up playlists and launches a ba.Activity to accept joiners."""
        # pylint: disable=cyclic-import
        from bastd.activity.multiteamjoin import MultiTeamJoinActivity

        app = _ba.app
        _cfg = app.config

        super(ba.MultiTeamSession, self).__init__(
            [],
            team_names=DEFAULT_TEAM_NAMES,
            team_colors=DEFAULT_TEAM_COLORS,
            min_players=1,
            max_players=self.get_max_players(),
        )

        self._series_length = app.teams_series_length
        self._ffa_series_length = app.ffa_series_length

        self._tutorial_activity_instance = None
        self._game_number = 0

        # Our faux playlist
        self._playlist = playlist

        self._current_game_spec: dict[str, Any] | None = None
        self._next_game_spec: dict[str, Any] = self._playlist.pull_next()
        self._next_game: type[ba.GameActivity] = self._next_game_spec["resolved_type"]

        self._instantiate_next_game()
        self.setactivity(_ba.newactivity(MultiTeamJoinActivity))


# Classes for Teams autopilot and FFA autopilot
# I think they have to be separate in order to comply with `ba.GameActivity.supports_session_type()`
class RandFreeForAllSession(ba.FreeForAllSession, RandomPlaySessionMixin):
    def __init__(self):
        playlist = RandomPlaylist(ba.FreeForAllSession)
        super(ba.FreeForAllSession, self).__init__(playlist)


class RandDualTeamSession(ba.DualTeamSession, RandomPlaySessionMixin):
    def __init__(self):
        playlist = RandomPlaylist(ba.DualTeamSession)
        super(ba.DualTeamSession, self).__init__(playlist)


# The faux playlist that just picks games at random
class RandomPlaylist:
    sessiontype: ba.Session
    all_games: list[ba.GameActivity]
    usable_games: list[ba.GameActivity]

    last_game: ba.GameActivity

    def __init__(self, sessiontype):
        self.sessiontype = sessiontype
        self.usable_games = [
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
            if game == self.last_game:
                # Don't repeat the same game twice
                if has_only_one_game:
                    # ...but don't freeze the game when there's only one game
                    break
            else:
                break

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
    sessiontype: type[ba.Session],
    transition: str | None = "in_right",
    origin_widget: ba.Widget | None = None,
):
    width = 800
    height = 650

    ui_scale = ba.app.ui.uiscale
    y_offset = -100 if ui_scale is ba.UIScale.SMALL else 0
    x_offset = 50 if ui_scale is ba.UIScale.SMALL else 0

    self.old__init__(sessiontype, transition, origin_widget)
    # pylint: disable=protected-access
    self._quick_game_button = ba.buttonwidget(
        parent=self._root_widget,
        position=(width - 120 * 2 + x_offset, height - 132 + y_offset),
        autoselect=True,
        size=(120, 60),
        scale=1.1,
        text_scale=1.2,
        label="Random games",
        on_activate_call=game_starter_factory(sessiontype),
        color=(0.54, 0.52, 0.67),
        textcolor=(0.7, 0.65, 0.7),
    )


# Returns a function that starts the game
def game_starter_factory(sessiontype: type[ba.Session]):
    session: Union[RandFreeForAllSession, RandDualTeamSession] = None

    if issubclass(sessiontype, ba.FreeForAllSession):
        session = RandFreeForAllSession
    elif issubclass(sessiontype, ba.DualTeamSession):
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
            _ba.unlock_all_input()
            _ba.new_host_session(session)

        _ba.fade_screen(False, time=0.25, endcall=has_faded)
        _ba.lock_all_input()
        ba.app.meta.load_exported_classes(ba.GameActivity, do_start)

    return on_run


# ba_meta export plugin
class RandomPlayPlugin(ba.Plugin):
    """
    A plugin that allows you to play randomly generated FFA or Teams matches by selecting a random minigame and map for each round.
    This eliminates the need to set up long playlists to enjoy all your BombSquad content.
    """

    def __init__(self):
        PlaylistBrowserWindow.old__init__ = PlaylistBrowserWindow.__init__
        PlaylistBrowserWindow.__init__ = patched__init__
