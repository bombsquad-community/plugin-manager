# ba_meta require api 9

plugman = dict(
    plugin_name="fluffyplaylisteditor",
    description="A simple not-so advanced Playlist Editor",
    external_url="https://discord.com/channels/1001896771347304639/1483463979450896445",
    authors=[
        {"name": "FluffyPal", "email": "", "discord": "fluffypal"}
    ],
    version="1.1.0",
)

### Started: 12 Mar 2026 at night from scratch
# - Learning workflow
# - configuring packages
# - PlaylistEditWindow UI Polishing (I HATE UI POLISHING)

### Continued: 13 Mar 2026
# - PlaylistEditGameWindow UI Polishing (AAAA.. oh, found a bug)
# - Implemented GameEdit configs reset and restore
# - Implemented GameEdit map quick navigation buttons
# - Lazy TypedDict PlaylistType

### Continued: 17 Mar 2026
# - PlaylistEditController logics overwrite
# - Implemented PlaylistEdit duplicate game
# - Refactor filter_playlist
# - Implemented logics to show invalid games/maps in PlaylistEdit
# - Refine GameEdit reset and restore

### Continued: 7 June 2026
# - Fixed map select not recorded on MapSelect
# - Added batch game adding within supported maps


import logging
from copy import deepcopy
from random import choice #, randint, randrange


import bauiv1 as bui
import bascenev1 as bs

import babase
from babase import app, Plugin


#======= PLAYLIST PARENT =======#
from bascenev1._playlist import filter_playlist #, PlaylistType
from bauiv1lib.playlist import PlaylistTypeVars

#======= PLAYLIST BORWSER =======#
# Main Playlist Browser Window For Starting The Playlist
# Then goes to PlaylistCustomizeBrowserWindow if pressing "customize..."
#from bauiv1lib.playlist.browser import PlaylistBrowserWindow

#import bauiv1lib.playlist.customizebrowser
#from bauiv1lib.playlist.customizebrowser import PlaylistCustomizeBrowserWindow

#======= PLAYLIST ADDING/EDITING =======#
## Main packages to modify
#- Game edit window
import bauiv1lib.playlist.edit
from bauiv1lib.playlist.edit import PlaylistEditWindow

#from bauiv1lib.playlist.addgame import PlaylistAddGameWindow

#- Playlist games edit window
import bauiv1lib.playlist.editgame
from bauiv1lib.playlist.editgame import PlaylistEditGameWindow

# Window for adding registered games to the playlist and then goes to PlaylistEditController for editing
# The UI that shows games GameActivities names on the left and desc on the right
# And "Get More Games..." on the bottom
# After selecting the game, we goes to PlaylistEditGameWindow for configuring the game Settings and Map
import bauiv1lib.playlist.editcontroller
from bauiv1lib.playlist.editcontroller import PlaylistEditController

#- Game map select window
#import bauiv1lib.playlist.mapselect
#from bauiv1lib.playlist.mapselect import PlaylistMapSelectWindow


#======= PLAYLIST PLAYING =======#
# This is used when we wanna "play" the playlist
#from bauiv1lib.play import PlayWindow, PlaylistSelectContext

#from bauiv1lib.playoptions import PlayOptionsWindow



#======= UI Packages =======#
from babase import (
    get_virtual_screen_size
)
from bauiv1 import (
    # Window utils
    Window, MainWindowState,
    MainWindow,
    UIScale,

    # Widget utils
    Widget, widget,
    containerwidget,
    scrollwidget,
    columnwidget,
    buttonwidget as original_buttonwidget,
    textwidget,
    imagewidget,
    checkboxwidget,
    get_special_widget,
    # Other
    gettexture,
    Mesh, Texture, Lstr,
)
from bauiv1lib.confirm import ConfirmWindow

#======= Type Hints =======#
#from enum import Enum
from typing import Callable, Sequence, Literal, TypedDict, Any, cast


class UntotalOldTypedPlaylistDict(TypedDict, total=False):
    map: str
    level: str
    resolved_type: type[bs.GameActivity] | None
    is_unowned_map: bool
    is_unowned_game: bool
    is_map_invalid: bool
    is_game_invalid: bool

class OldTypedPlaylistDict(TypedDict):
    map: str
    level: str

class TypedPlaylistDict(UntotalOldTypedPlaylistDict):
    settings: OldTypedPlaylistDict
    type: str

TypedPlaylistType = list[TypedPlaylistDict]

#-------------------------- UI TOOLS --------------------------#
def buttonwidget(
    *,
    edit: Widget | None = None,
    parent: Widget | None = None,
    id: str | None = None,
    size: Sequence[float] | None = None,
    position: Sequence[float] | None = None,
    on_activate_call: Callable | None = None,
    label: str | Lstr | None = None,
    color: Sequence[float] | None = None,
    down_widget: Widget | None = None,
    up_widget: Widget | None = None,
    left_widget: Widget | None = None,
    right_widget: Widget | None = None,
    #texture: Texture | None = None,
    text_scale: float | None = None,
    textcolor: Sequence[float] | None = None,
    enable_sound: bool | None = None,
    mesh_transparent: Mesh | None = None,
    mesh_opaque: Mesh | None = None,
    repeat: bool | None = None,
    scale: float | None = None,
    transition_delay: float | None = None,
    on_select_call: Callable | None = None,
    button_type: str | None = None,
    extra_touch_border_scale: float | None = None,
    selectable: bool | None = None,
    show_buffer_top: float | None = None,
    icon: Texture | None = None,
    iconscale: float | None = None,
    icon_tint: float | None = None,
    icon_color: Sequence[float] | None = None,
    autoselect: bool | None = None,
    mask_texture: Texture | None = None,
    tint_texture: Texture | None = None,
    tint_color: Sequence[float] | None = None,
    tint2_color: Sequence[float] | None = None,
    text_flatness: float | None = None,
    text_res_scale: float | None = None,
    text_literal: bool | None = None,
    opacity: float | None = None,
    better_bg_fit: bool | None = None,
) -> Widget:
    return original_buttonwidget(
        edit=edit,
        parent=parent,
        id=id,
        size=size,
        position=position,
        on_activate_call=on_activate_call,
        label=label,
        color=color,
        down_widget=down_widget,
        up_widget=up_widget,
        left_widget=left_widget,
        right_widget=right_widget,
        texture=gettexture('white'),
        text_scale=text_scale,
        textcolor=textcolor,
        enable_sound=enable_sound,
        mesh_transparent=mesh_transparent,
        mesh_opaque=mesh_opaque,
        repeat=repeat,
        scale=scale,
        transition_delay=transition_delay,
        on_select_call=on_select_call,
        button_type=button_type,
        extra_touch_border_scale=extra_touch_border_scale,
        selectable=selectable,
        show_buffer_top=show_buffer_top,
        icon=icon,
        iconscale=iconscale,
        icon_tint=icon_tint,
        icon_color=icon_color,
        autoselect=autoselect,
        mask_texture=mask_texture,
        tint_texture=tint_texture,
        tint_color=tint_color,
        tint2_color=tint2_color,
        text_flatness=text_flatness,
        text_res_scale=text_res_scale,
        text_literal=text_literal,
        opacity=opacity,
        better_bg_fit=better_bg_fit
    )

def create_container(size: tuple[float, float], **kwargs) -> Widget:
    """Create the main window with overlay."""
    # Container
    p = containerwidget(
        #parent=get_special_widget('overlay_stack'),
        background=False,
        #transition='in_scale',
        size=size,
        **kwargs
    )
    x, y = get_virtual_screen_size()

    # Background
    imagewidget(
        parent=p,
        texture=gettexture('white'),
        size=(x*2, y*2),
        position=(-x*0.5, 0-475),
        opacity=0.55,
        color=(0, 0, 0)
    )

    # Main Container View
    border_size_range = 1.0075
    b = imagewidget(
        texture=gettexture('white'),
        parent=p,
        size=(size[0]*border_size_range, size[1]*border_size_range),
        tilt_scale=6,
        color=tuple(col*1.5 for col in color_theme.get_color('primary'))
    )
    f = imagewidget( # Foreground
        texture=gettexture('white'),
        parent=p,
        size=size,
        color=color_theme.get_color('bg')
    )

    border_size_offset = border_size_range-(border_size_range//border_size_range.real)
    imagewidget(
        edit=b,
        position=tuple(pos*-border_size_offset for pos in f.center)
    )

    return p

def create_confirm(callback: Callable, text: str) -> Callable:
    return lambda: ConfirmWindow(
        text=f"{text}?",
        color=color_theme.get_color('primary'), # pyright: ignore[reportArgumentType]
        action=callback
    )

_SOUND_VOL = 1.2
def play_error_sound():
    bui.getsound('error').play(_SOUND_VOL)

def play_guncocking_sound():
    bui.getsound('gunCocking').play(_SOUND_VOL)

def play_ding_sound():
    bui.getsound('ding').play(_SOUND_VOL)

def play_powerdown_sound():
    bui.getsound('powerdown01').play(_SOUND_VOL)

def play_shield_down_sound():
    bui.getsound('shieldDown').play(_SOUND_VOL)

def play_shield_up_sound():
    bui.getsound('shieldUp').play(_SOUND_VOL)

def play_deek_sound():
    bui.getsound(choice(['deek', 'deek2'])).play(_SOUND_VOL)

def play_click_sound():
    bui.getsound('click01').play(_SOUND_VOL)


class ScreenmessageColors:
    RED = (1, 0, 0)
    GREEN = (0, 1, 0)
    BS_GREEN = (0.6, 1, 0.6)
    BLUE = (0, 0, 1)
    ORANGE = (1, 0.5, 0)
    YELLOW = (1, 1, 0)
    PURPLE = (0.6, 0, 1)
    CYAN = (0, 1, 1)
    MAGENTA = (1, 0, 1)
    WHITE = (1, 1, 1)
    BLACK = (0, 0, 0)
    GRAY = (0.5, 0.5, 0.5)
    PINK = (1, 0.4, 0.7)


_COLOR_TYPE = Literal[
    'bg', 'primary', 'secondary', 'tertiary', 'unknown'
]
class ColorTheme:
    main_color: Sequence[float] = (0.8, 0.8, 0.8)
    colors: dict[_COLOR_TYPE, Sequence[float]] = {
        'bg': tuple(col*0.1 for col in main_color),
        'primary': main_color,
        'secondary': tuple(col*0.2 for col in main_color),
        'tertiary': tuple(col*0.4 for col in main_color),
        'unknown': (main_color[0]*1.2, main_color[1], main_color[2])
    }

    def get_color(self, color: _COLOR_TYPE) -> Sequence[float]:
        return self.colors[color]


color_theme = ColorTheme()


#-------------------------- MAIN --------------------------#
class FluffyPlaylistEditController(PlaylistEditController):
    def __init__(
        self,
        sessiontype: type[bs.Session],
        from_window: MainWindow,
        *,
        existing_playlist_name: str | None = None,
        playlist: TypedPlaylistType | None = None,
        playlist_name: str | None = None,
    ):
        appconfig = bui.app.config

        # Since we may be showing our map list momentarily,
        # lets go ahead and preload all map preview textures.
        if app.classic is not None:
            app.classic.preload_map_preview_media()

        self._sessiontype = sessiontype

        self._editing_game = False
        self._editing_game_type: type[bs.GameActivity] | None = None
        self._pvars = PlaylistTypeVars(sessiontype)
        self._existing_playlist_name = existing_playlist_name
        self._config_name_full = self._pvars.config_name + ' Playlists'

        self._is_batch_add = False
        self._pre_game_add_state: MainWindowState | None = None
        self._pre_game_edit_state: MainWindowState | None = None

        # Make sure config exists.
        if self._config_name_full not in appconfig:
            appconfig[self._config_name_full] = {}

        self._selected_index = 0
        if existing_playlist_name:
            self._name = existing_playlist_name

            # Filter out invalid games.
            self._playlist = new_filter_playlist(
                appconfig[self._pvars.config_name + ' Playlists'][
                    existing_playlist_name
                ],
                sessiontype=sessiontype,
                remove_unowned=False,
                #add_resolved_type=True, # HACK: This would cause json error as we save a Python class which aren't serializable
                name=existing_playlist_name,
                print_exc=False
            )
            self._edit_ui_selection = None
        else:
            if playlist is not None:
                self._playlist = playlist
            else:
                self._playlist = []
            if playlist_name is not None:
                self._name = playlist_name
            else:
                # Find a good unused name.
                i = 1
                while True:
                    self._name = (
                        self._pvars.default_new_list_name.evaluate()
                        + ((' ' + str(i)) if i > 1 else '')
                    )
                    if (
                        self._name
                        not in appconfig[self._pvars.config_name + ' Playlists']
                    ):
                        break
                    i += 1

            # Also we want it to start with 'add' highlighted since its empty
            # and that's all they can do.
            self._edit_ui_selection = 'add_button'

        editwindow = from_window.main_window_replace(
            lambda: FluffyPlaylistEditWindow(editcontroller=self)
        )
        assert editwindow is not None

        # Once we've set our start window, store the back state. We'll
        # skip back to there once we're fully done.
        self._back_state = editwindow.main_window_back_state


    def duplicate_game_pressed(self) -> bool:
        """Duplicate the currently selected game in the playlist and insert it just after."""
        if not self._playlist or self._selected_index is None:
            bs.screenmessage("No game selected to duplicate", ScreenmessageColors.ORANGE)
            play_error_sound()
            return False

        base_entry = self._playlist[self._selected_index]
        new_entry = deepcopy(base_entry)

        ins_index = self._selected_index + 1
        self._playlist.insert(ins_index, new_entry)
        self._selected_index = ins_index
        self._edit_ui_selection = None

        try:
            cls = babase.getclass(new_entry['type'], bs.GameActivity)
            name = cls.getname()
        except (ImportError, AttributeError):
            name = new_entry['type']

        bs.screenmessage(f"Game '{name}' duplicated", ScreenmessageColors.BS_GREEN)
        return True

    def toggle_epic_mode(self) -> bool:
        if not self._playlist or self._selected_index is None:
            bs.screenmessage("No game selected to toggle epic mode", ScreenmessageColors.ORANGE)
            play_error_sound()
            return False

        entry = self._playlist[self._selected_index]
        if (epic_setting := 'Epic Mode') in entry['settings'] and isinstance(entry['settings'][epic_setting], bool):
            self._playlist[self._selected_index]['settings'][epic_setting] = not entry['settings'][epic_setting] # pyright: ignore[reportGeneralTypeIssues]
        else:
            play_error_sound()
            return False
        return True

    def toggle_solo_mode(self) -> bool:
        if not self._playlist or self._selected_index is None:
            bs.screenmessage("No game selected to toggle solo mode", ScreenmessageColors.ORANGE)
            play_error_sound()
            return False

        entry = self._playlist[self._selected_index]
        if (solo_setting := 'Solo Mode') in entry['settings'] and isinstance(entry['settings'][solo_setting], bool):
            self._playlist[self._selected_index]['settings'][solo_setting] = not entry['settings'][solo_setting] # pyright: ignore[reportGeneralTypeIssues]
        else:
            play_error_sound()
            return False
        return True

    def reslove_default_settings_defs(self, settings: OldTypedPlaylistDict) -> list[bs.Setting]:
        default_settings = list[bs.Setting]()
        if (epic_mode := 'Epic Mode') in settings:
            default_settings.append(
                bs.BoolSetting(epic_mode, default=settings[epic_mode])
            )
        if (solo_mode := 'Solo Mode') in settings:
            default_settings.append(
                bs.BoolSetting(solo_mode, default=settings[solo_mode])
            )
        if (time_limit := 'Time Limit') in settings:
            default_settings.append(
                bs.IntChoiceSetting(
                    time_limit,
                    choices=[
                        ('None', 0),
                        ('1 Minute', 60),
                        ('2 Minutes', 120),
                        ('5 Minutes', 300),
                        ('10 Minutes', 600),
                        ('20 Minutes', 1200),
                    ],
                    default=settings[time_limit],
                )
            )
        if (respawn_times := 'Respawn Times') in settings:
            default_settings.append(
                bs.FloatChoiceSetting(
                    respawn_times,
                    choices=[
                        ('Shorter', 0.25),
                        ('Short', 0.5),
                        ('Normal', 1.0),
                        ('Long', 2.0),
                        ('Longer', 4.0),
                    ],
                    default=settings[respawn_times],
                )
            )
        return default_settings

    def edit_game_pressed(self, from_window: MainWindow) -> None:
        if not self._playlist:
            return

        playlist = self._playlist[self._selected_index]
        try:
            cls = babase.getclass(
                playlist['type'],
                subclassof=bs.GameActivity
            )
        except AttributeError as e:
            bs.screenmessage(f'Can\'t edit game: {e}. Maybe try fix it?', ScreenmessageColors.YELLOW)
            play_error_sound()
            return

        except ModuleNotFoundError as e:
            class FakeGameActivity(bs.GameActivity):
                name = playlist['type']
                available_settings = self.reslove_default_settings_defs(playlist['settings'])
            cls = FakeGameActivity

        self._show_edit_ui(
            gametype=cls,
            settings=playlist['settings'], # pyright: ignore[reportArgumentType]
            from_window=from_window,
        )

    def _show_edit_ui( # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        gametype: type[bs.GameActivity],
        settings: TypedPlaylistDict | None,
        from_window: bui.MainWindow,
    ) -> None:
        # pylint: disable=cyclic-import
        if not from_window.main_window_has_control():
            return

        self._editing_game = settings is not None
        self._editing_game_type = gametype
        assert self._sessiontype is not None

        # Jump into an edit window.
        editwindow = from_window.main_window_replace(
            lambda: FluffyPlaylistEditGameWindow(
                gametype,
                self._sessiontype,
                settings,
                completion_call=self._edit_game_done,
            )
        )
        assert editwindow is not None

        # Once we're there, store the back state. We'll use that to jump
        # back out to our current location once the edit is done.
        assert self._pre_game_edit_state is None
        self._pre_game_edit_state = editwindow.main_window_back_state

    def _edit_game_done( # pyright: ignore[reportIncompatibleMethodOverride]
        self, config: TypedPlaylistDict | None, from_window: bui.MainWindow
    ) -> None:
        """Called after finished editing/adding a game"""
        # No-op if provided window isn't in charge.
        if not from_window.main_window_has_control():
            return

        assert bui.app.classic is not None
        if config is None:
            play_powerdown_sound()
        else:
            # Make sure type is in there.
            assert self._editing_game_type is not None
            if self._editing_game:
                playlist = self._playlist[self._selected_index]
                config['type'] = playlist['type']
            else:
                config['type'] = bui.get_type_name(self._editing_game_type)

            if self._editing_game:
                self._playlist[self._selected_index] = deepcopy(config)
            else:
                # Add a new entry to the playlist.
                insert_index = min(
                    len(self._playlist), self._selected_index + 1
                )

                self._selected_index = insert_index
                self._playlist.insert(insert_index, deepcopy(config))

                if self._is_batch_add:
                    for _map in self._get_supported_maps_for_game(config, self._editing_game_type):
                        new_config = deepcopy(config)
                        new_config['map'] = _map
                        new_config['settings']['map'] = _map
                        self._playlist.insert(insert_index, new_config)
                        insert_index += 1


            play_guncocking_sound()

        # If we're adding, jump to before the add started.
        # Otherwise jump to before the edit started.
        assert (
            self._pre_game_edit_state is not None
            or self._pre_game_add_state is not None
        )
        if self._pre_game_add_state is not None:
            from_window.main_window_back_state = self._pre_game_add_state
        elif self._pre_game_edit_state is not None:
            from_window.main_window_back_state = self._pre_game_edit_state

        from_window.main_window_back()
        self._pre_game_edit_state = None
        self._pre_game_add_state = None
        self._is_batch_add = False


    def _get_supported_maps_for_game(self, config: TypedPlaylistDict, gametype: type[bs.GameActivity]):
        assert app.classic is not None
        store = app.classic.store

        valid_maps = set(gametype.get_supported_maps(self._sessiontype))
        to_remove = set(store.get_unowned_maps())

        if config_map := config.get('map') or (config.get('settings', {}) or {}).get('map'):
            to_remove.add(config_map)

        valid_maps -= to_remove

        return sorted(valid_maps)


    def batch_add_game_pressed(self, from_window: MainWindow):
        self._is_batch_add = True
        self.add_game_pressed(from_window)


class FluffyPlaylistEditWindow(PlaylistEditWindow):
    def __init__(
        self,
        editcontroller: FluffyPlaylistEditController,
        transition: str | None = 'in_right',
        origin_widget: Widget | None = None,
    ):
        self._list_widgets: list[Widget] = []
        self._editcontroller = editcontroller
        editcontroller._is_batch_add = False # HACK: Couldn't think of any clean idea :p

        self._r = 'editGameListWindow'
        prev_selection: str | None = self._editcontroller.get_edit_ui_selection()

        ### Container Setup
        uiscale = app.ui_v1.uiscale
        is_small_ui = uiscale is UIScale.SMALL
        # Keep a constant aspect ratio for all UIScale values.
        # Let's use width:height (classic UI aspect) as a reference.
        # We'll use a base width and scale it for each UI scale while maintaining the ratio.
        base_width = 800
        aspect_ratio = 16 / 9
        self._width = base_width * 1.65

        self._height = self._width / aspect_ratio

        # Adjust x_inset proportionally to width
        self.x_inset = x_inset = int(self._width * (0.09 if is_small_ui else 0.02))
        self.yoffs = yoffs = -68 if is_small_ui else -15

        # Round to integers for pixel positions
        self._width = int(self._width)
        self._height = int(self._height)

        MainWindow.__init__(self, # pyright: ignore[reportArgumentType]
            root_widget=create_container(
                size=(self._width, self._height),
                scale=(
                    1.20 if is_small_ui else
                    0.80 if uiscale is UIScale.MEDIUM else
                    0.60
                ),
                toolbar_visibility=(
                    'menu_minimal_no_back'
                    if is_small_ui
                    else 'menu_full'
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        ### Widgets/children
        # Buttons
        self.b_color = b_color = color_theme.get_color('primary')
        self.b_textcolor = b_textcolor = color_theme.get_color('secondary')

        cancel_button = buttonwidget(
            parent=self._root_widget,
            position=(35 + x_inset, self._height - 50 + yoffs),
            scale=0.8,
            size=(175, 60),
            autoselect=True,
            color=(b_color[0]*1.2, *b_color[1:]),
            textcolor=b_textcolor,
            label=bui.Lstr(resource='cancelText'),
            text_scale=1.2,
        )
        save_button = buttonwidget(
            parent=self._root_widget,
            position=(
                self._width - ((225 if is_small_ui else 255) + x_inset),
                self._height - 50 + yoffs
            ),
            scale=0.8,
            size=(190, 60),
            autoselect=True,
            color=(b_color[0], b_color[1]*1.2, b_color[2]),
            textcolor=b_textcolor,
            left_widget=cancel_button,
            label=bui.Lstr(resource='saveText'),
            text_scale=1.2,
        )

        widget(
            edit=save_button,
            right_widget=bui.get_special_widget('squad_button'),
        )

        widget(
            edit=cancel_button,
            left_widget=cancel_button,
            right_widget=save_button,
        )

        v_gap = 60
        h = 40 + x_inset
        r_h = x_inset * (9.45 if is_small_ui else 45.25)

        left_button_v_size = 45
        right_button_v_size = 45

        v = self._height - 172.0 + yoffs
        v *= 1.1
        v -= 2.0
        v -= v_gap
        buttonwidget(
            parent=self._root_widget,
            position=(r_h, v),
            size=(110, right_button_v_size),
            on_activate_call=self._toggle_epic_mode,
            enable_sound=False,
            autoselect=True,
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            text_scale=0.8,
            label="Toggle\nEpic Mode",
        )
        v -= v_gap

        buttonwidget(
            parent=self._root_widget,
            position=(r_h, v),
            size=(110, right_button_v_size),
            on_activate_call=self._toggle_solo_mode,
            enable_sound=False,
            autoselect=True,
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            text_scale=0.8,
            label="Toggle\nSolo Mode",
        )
        v -= v_gap

        v = self._height - 172.0 + yoffs
        v *= 1.1
        v -= 2.0
        v -= v_gap

        add_game_button = buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(110, left_button_v_size),
            on_activate_call=self._add,
            on_select_call=bui.CallPartial(self._set_ui_selection, 'add_button'),
            autoselect=True,
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            text_scale=0.8,
            label=bui.Lstr(resource=f'{self._r}.addGameText'),
        )
        v -= v_gap

        batch_add_game_button = buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(110, left_button_v_size),
            on_activate_call=self._batch_add,
            on_select_call=bui.CallPartial(self._set_ui_selection, 'batch_add_button'),
            autoselect=True,
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            text_scale=0.8,
            label=f"Batch {bui.Lstr(resource=f'{self._r}.addGameText').evaluate()}",
        )
        v -= v_gap

        self._edit_button = edit_game_button = buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(110, left_button_v_size),
            on_activate_call=self._edit,
            on_select_call=bui.CallPartial(self._set_ui_selection, 'editButton'),
            autoselect=True,
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            text_scale=0.8,
            label=bui.Lstr(resource=f'{self._r}.editGameText'),
        )
        v -= v_gap

        remove_game_button = buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(110, left_button_v_size),
            text_scale=0.8,
            on_activate_call=self._remove,
            autoselect=True,
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            label=bui.Lstr(resource=f'{self._r}.removeGameText'),
        )
        v -= v_gap

        # Customs
        duplicate_button = buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(110, left_button_v_size),
            on_activate_call=self._duplicate_selected_game,
            autoselect=True,
            enable_sound=False,
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            text_scale=0.8,
            label="Duplicate\nGame",
        )
        v -= v_gap - 10

        h += 9
        buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(42, 35),
            on_activate_call=self._move_up,
            label=bui.charstr(bui.SpecialChar.UP_ARROW),
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            autoselect=True,
            repeat=True,
        )
        h += 52
        buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(42, 35),
            on_activate_call=self._move_down,
            autoselect=True,
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            label=bui.charstr(bui.SpecialChar.DOWN_ARROW),
            repeat=True,
        )

        # Scroller
        v = self._height - 100 + yoffs
        scroll_height = self._height - (
            250 if is_small_ui else 155
        )
        self._scroll_width = self._width - (205 + (2.5 if is_small_ui else 5.5) * x_inset)

        scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(160 + x_inset, v - scroll_height),
            highlight=False,
            on_select_call=bui.CallStrict(self._set_ui_selection, 'gameList'),
            size=(self._scroll_width, (scroll_height - 15)),
            border_opacity=0.4,
        )
        widget(
            edit=scrollwidget,
            left_widget=add_game_button,
            right_widget=scrollwidget,
        )
        self._columnwidget = columnwidget(
            parent=scrollwidget, border=2, margin=0
        )

        for button in [
            add_game_button, batch_add_game_button, edit_game_button, remove_game_button, duplicate_button
        ]:
            widget(
                edit=button, left_widget=button, right_widget=scrollwidget
            )

        buttonwidget(edit=cancel_button, on_activate_call=self._cancel)
        containerwidget(
            edit=self._root_widget,
            cancel_button=cancel_button,
            selected_child=scrollwidget,
        )

        buttonwidget(edit=save_button, on_activate_call=self._save_press)
        containerwidget(edit=self._root_widget, start_button=save_button)

        # Texts
        textwidget(
            parent=self._root_widget,
            position=(-10, self._height - 50 + yoffs),
            size=(self._width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=app.ui_v1.title_color,
            scale=1.05,
            h_align='center',
            v_align='center',
            maxwidth=270,
        )

        v = self._height - 115.0 + yoffs

        textwidget(
            parent=self._root_widget,
            text=bui.Lstr(resource=f'{self._r}.listNameText'),
            position=(196 + x_inset, v + 31),
            maxwidth=150,
            color=(0.8, 0.8, 0.8, 0.5),
            size=(0, 0),
            scale=0.75,
            h_align='right',
            v_align='center',
        )

        self._text_field = text_field = textwidget(
            parent=self._root_widget,
            position=(210 + x_inset, v + 7),
            size=(self._scroll_width - 53, 43),
            text=self._editcontroller.getname(),
            h_align='left',
            v_align='center',
            max_chars=40,
            maxwidth=380,
            autoselect=True,
            color=(0.9, 0.9, 0.9, 1.0),
            description=bui.Lstr(resource=f'{self._r}.listNameText'),
            editable=True,
            padding=4,
            on_return_press_call=self._save_press_with_sound,
        )
        widget(edit=self._columnwidget, up_widget=text_field)
        widget(edit=cancel_button, down_widget=text_field)
        widget(edit=add_game_button, up_widget=text_field)
        widget(edit=batch_add_game_button, up_widget=add_game_button)

        if prev_selection == 'add_button':
            containerwidget(
                edit=self._root_widget, selected_child=add_game_button
            )
        elif prev_selection == 'batch_add_button':
            containerwidget(
                edit=self._root_widget, selected_child=batch_add_game_button
            )
        elif prev_selection == 'editButton':
            containerwidget(
                edit=self._root_widget, selected_child=edit_game_button
            )
        elif prev_selection == 'gameList':
            containerwidget(
                edit=self._root_widget, selected_child=scrollwidget
            )

        self._refresh()

    def _get_invalid_game_name(self, pentry: TypedPlaylistDict):
        name = pentry['type']
        # A few substitutions for 'Epic', 'Solo' etc. modes.
        # FIXME: Should provide a way for game types to define filters of
        #  their own and should not rely on hard-coded settings names.
        if (solo_mode := 'Solo Mode') in pentry['settings'] and pentry['settings'][solo_mode]:
            name = babase.Lstr(
                resource='soloNameFilterText', subs=[('${NAME}', name)]
            )
        if (epic_mode := 'Epic Mode') in pentry['settings'] and pentry['settings'][epic_mode]:
            name = babase.Lstr(
                resource='epicNameFilterText', subs=[('${NAME}', name)]
            )

        # Resolve map name
        if 'map' in pentry['settings']:
            sval = babase.Lstr(
                value='${NAME} @ ${MAP}',
                subs=[
                    ('${NAME}', name),
                    ('${MAP}', bs.get_map_display_string(
                               bs.get_filtered_map_name(pentry['settings']['map'])),
                    ),
                ],
            )
        elif 'map' in pentry:
            sval = babase.Lstr(
                value='${NAME} @ ${MAP}',
                subs=[
                    ('${NAME}', name),
                    ('${MAP}', bs.get_map_display_string(
                               bs.get_filtered_map_name(pentry['map'])),
                    ),
                ],
            )
        else:
            print('invalid game config - expected map entry under settings')
            sval = babase.Lstr(value='???')

        return sval


    def _duplicate_selected_game(self) -> None:
        if self._editcontroller.duplicate_game_pressed():
            play_guncocking_sound()
            self._refresh()


    def _move_down(self) -> None:
        if len(self._editcontroller.get_playlist()) > 1:
            super()._move_down()

    def _move_up(self) -> None:
        if len(self._editcontroller.get_playlist()) > 1:
            super()._move_up()


    def _toggle_epic_mode(self):
        if self._editcontroller.toggle_epic_mode():
            play_guncocking_sound()
            self._refresh()


    def _toggle_solo_mode(self):
        if self._editcontroller.toggle_solo_mode():
            play_guncocking_sound()
            self._refresh()


    def _refresh(self) -> None:
        # Need to grab this here as rebuilding the list will
        # change it otherwise.
        old_selection_index = self._editcontroller.get_selected_index()

        while self._list_widgets:
            self._list_widgets.pop().delete()
        for index, pentry in enumerate(self._editcontroller.get_playlist()): # pyright: ignore[reportAssignmentType]
            pentry: TypedPlaylistDict
            try:
                cls = babase.getclass(pentry['type'], subclassof=bs.GameActivity)
                desc = cls.get_settings_display_string(pentry) # pyright: ignore[reportArgumentType]
                color = (0.8, 0.8, 0.8, 1.0)
            except Exception:
                #logging.exception('Error in playlist refresh.')
                #desc = "(invalid: '" + pentry['type'] + "')"
                desc = self._get_invalid_game_name(pentry)
                color = color_theme.get_color('unknown')

            txtw = textwidget(
                parent=self._columnwidget,
                size=(self._width - 80, 30),
                on_select_call=bui.CallStrict(self._select, index),
                always_highlight=True,
                color=color,
                padding=0,
                maxwidth=self._scroll_width * 0.93,
                text=desc,
                on_activate_call=self._edit_button.activate,
                v_align='center',
                selectable=True,
            )
            widget(edit=txtw, show_buffer_top=50, show_buffer_bottom=50)

            # Wanna be able to jump up to the text field from the top one.
            if index == 0:
                widget(edit=txtw, up_widget=self._text_field)
            self._list_widgets.append(txtw)
            if old_selection_index == index:
                columnwidget(
                    edit=self._columnwidget,
                    selected_child=txtw,
                    visible_child=txtw,
                )

    def _batch_add(self) -> None:
        # Store list name then tell the session to perform an add.
        self._editcontroller.setname(
            cast(str, bui.textwidget(query=self._text_field))
        )
        self._editcontroller.batch_add_game_pressed(from_window=self)


from bascenev1 import (
    get_filtered_map_name,
    get_map_class,
    get_map_display_string,
)
class FluffyPlaylistEditGameWindow(PlaylistEditGameWindow):

    def __init__(
        self,
        gametype: type[bs.GameActivity],
        sessiontype: type[bs.Session],
        config: TypedPlaylistDict | None,
        completion_call: Callable[[TypedPlaylistDict | None, bui.MainWindow], Any],
        default_selection: str | None = None,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        edit_info: dict[str, Any] | None = None
    ):

        assert app.classic is not None
        store = app.classic.store

        self._scrollwidget: Widget | None = None
        self._subcontainer: Widget | None = None

        self._gametype = gametype
        self._sessiontype = sessiontype

        # If we're within an editing session we get passed edit_info
        # (returning from map selection window, etc).
        if edit_info is not None:
            self._edit_info = edit_info

        # ..otherwise determine whether we're adding or editing a game based
        # on whether an existing config was passed to us.
        else:
            if config is None:
                self._edit_info = {'editType': 'add'}
            else:
                self._edit_info = {'editType': 'edit'}

        self._r = 'gameSettingsWindow'

        self._valid_maps = valid_maps = gametype.get_supported_maps(sessiontype)
        if not valid_maps:
            bui.screenmessage(bui.Lstr(resource='noValidMapsErrorText'))
            raise RuntimeError('No valid maps found.')
        self._valid_maps_owned = [m for m in self._valid_maps if m not in store.get_unowned_maps()]

        self._config = config

        self._settings_defs = gametype.get_available_settings(sessiontype)
        self._completion_call = completion_call

        # If there's a valid map name in the existing config, use that.
        self._map: str | None = None
        # To start with, pick a random map out of the ones we own.
        unowned_maps = store.get_unowned_maps()
        try:
            if (
                config is not None
                and 'map' in config
            ):
                filtered_map_name = get_filtered_map_name(
                    config['map']
                )
                if filtered_map_name not in unowned_maps:
                    self._map = filtered_map_name
            elif (
                config is not None
                and (settings := config.get('settings'))
                and (raw_map := settings.get('map'))
            ):
                filtered_map_name = get_filtered_map_name(raw_map)
                if filtered_map_name not in unowned_maps:
                    self._map = filtered_map_name
            #else:
            #    raise Exception()
        except Exception:
            logging.exception('Error getting map for editor.')

        if not self._map:
            if valid_maps_owned := [m for m in valid_maps if m not in unowned_maps]:
                self._map = choice(valid_maps_owned)
            # Hmmm.. we own none of these maps.. just pick a random un-owned one
            # I guess.. should this ever happen?
            else:
                self._map = choice(valid_maps)

        if config is not None:
            if 'settings' in config:
                self._settings = config['settings']
            else:
                self._settings = config
        else:
            self._settings: OldTypedPlaylistDict = {} # pyright: ignore[reportAttributeAccessIssue]
        self._settings['map'] = self._map

        self._default_settings = deepcopy(self._settings)

        try:
            self.map_tex_name = get_map_class(self._map).get_preview_texture_name()
        except babase.NotFoundError:
            self.map_tex_name = 'null'

        if self.map_tex_name is None:
            raise RuntimeError(f'No map preview tex found for {self._map}.')
        self._choice_selections: dict[str, int] = {}

        ### Container Setup
        uiscale = app.ui_v1.uiscale
        is_small_ui = uiscale is UIScale.SMALL
        # Keep a constant aspect ratio for all UIScale values.
        # Let's use width:height (classic UI aspect) as a reference.
        # We'll use a base width and scale it for each UI scale while maintaining the ratio.
        base_width = 900
        aspect_ratio = 5 / 4
        self._width = width = int(base_width * 1.65)
        self._height = height = int(base_width / aspect_ratio)

        y_extra2 = 50 # For topper widget elements

        # Adjust x_inset proportionally to width
        self.x_inset = int(width * (0.09 if is_small_ui else 0.0225))
        self.yoffs = yoffs = -68 if is_small_ui else -30

        MainWindow.__init__(self,
            root_widget=containerwidget(
                size=(width, height),
                color=color_theme.get_color('bg'),
                scale=(
                    1.10 if is_small_ui else
                    0.80 if uiscale is UIScale.MEDIUM else
                    0.70
                ),
                toolbar_visibility=(
                    'menu_minimal_no_back'
                    if uiscale is UIScale.SMALL
                    else 'menu_full'
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        ### Widgets/children
        b_color = color_theme.get_color('primary')
        b_textcolor = color_theme.get_color('secondary')

        is_add = self._edit_info['editType'] == 'add'
        cancel_button = original_buttonwidget(
            parent=self._root_widget,
            position=(45 + self.x_inset, height - 82 + y_extra2 + yoffs),
            size=(60, 48) if is_add else (180, 65),
            label=(
                bui.charstr(bui.SpecialChar.BACK) if is_add else
                bui.Lstr(resource='cancelText')
            ),
            button_type='backSmall' if is_add else None,
            autoselect=True,
            scale=1.0 if is_add else 0.75,
            text_scale=1.3,
            color=(b_color[0]*1.2, *b_color[1:]),
            textcolor=b_textcolor,
            on_activate_call=bui.CallStrict(self._cancel),
        )
        containerwidget(edit=self._root_widget, cancel_button=cancel_button)

        # Title
        textwidget(
            parent=self._root_widget,
            position=((-20 if is_small_ui else -18), height - 70 + y_extra2 + yoffs),
            size=(width, 25),
            text=gametype.get_display_string(),
            color=bui.app.ui_v1.title_color,
            maxwidth=width*0.35,
            scale=1.1,
            h_align='center',
            v_align='center',
        )

        self.add_button = add_button = original_buttonwidget(
            parent=self._root_widget,
            position=(width - ((255 if is_small_ui else 235) + self.x_inset), height - 82 + y_extra2 + yoffs),
            size=(200, 65),
            scale=0.75,
            text_scale=1.3,
            color=(b_color[0], b_color[1]*1.2, b_color[2]),
            textcolor=b_textcolor,
            label=(
                bui.Lstr(resource=f'{self._r}.addGameText') if is_add else
                bui.Lstr(resource='applyText')
            ),
        )

        base_h_pos = width - ((155 if is_small_ui else 135) + self.x_inset)
        base_v_pos = height * 0.75
        right_buttons_gap = 75

        reset_config_text = "Reset\nSettings"
        original_buttonwidget(
            parent=self._root_widget,
            position=(base_h_pos, base_v_pos - right_buttons_gap),
            size=(200, 100),
            scale=0.75,
            text_scale=1.3,
            color=b_color,
            textcolor=b_textcolor,
            label=reset_config_text,
            on_activate_call=create_confirm(self._reset_settings, reset_config_text.replace('\n', ' ')),
            icon=gettexture('replayIcon'),
            iconscale=1.5
        )
        right_buttons_gap += right_buttons_gap

        restore_config_text = "Restore\nSettings"
        original_buttonwidget(
            parent=self._root_widget,
            position=(base_h_pos, base_v_pos - right_buttons_gap),
            size=(200, 100),
            scale=0.75,
            text_scale=1.3,
            color=b_color,
            textcolor=b_textcolor,
            label=restore_config_text,
            on_activate_call=(
                create_confirm(self._restore_settings, restore_config_text.replace('\n', ' ')) if not is_add else play_error_sound
            ),
            icon=gettexture('leftButton'),
            iconscale=1.5
        )

        self._refresh_settings_items()

        original_buttonwidget(
            edit=add_button, on_activate_call=bui.CallStrict(self._add)
        )
        containerwidget(
            edit=self._root_widget,
            selected_child=add_button,
            start_button=add_button,
        )

        if default_selection == 'map':
            containerwidget(
                edit=self._root_widget, selected_child=self._scrollwidget
            )
            containerwidget(
                edit=self._subcontainer, selected_child=self._map_buttonwidget
            )

    # Tools
    def _reset_settings(self):
        updated = False
        if self._settings:
            for setting in self._settings_defs:
                if (value := setting.default) != (data := self._settings)[setting.name]:
                    data[setting.name] = value
                    updated = True

            if (def_map := self._default_settings['map']) != self._map:
                self._map = def_map
                try:
                    self.map_tex_name = get_map_class(def_map).get_preview_texture_name()
                except babase.NotFoundError:
                    self.map_tex_name = 'null'
                updated = True

        if updated:
            self._refresh_settings_items()
            play_shield_down_sound()
        else:
            play_error_sound()

    def _restore_settings(self):
        updated = False
        # Only update keys which are different, and track if anything actually changed
        for key, value in self._default_settings.items():
            if key not in self._settings or self._settings[key] != value:
                #print(f'key restored: {self._settings[key]} -> {key}')
                self._settings[key] = value
                updated = True

        # Check if map changed, update relevant attrs
        restored_map = get_filtered_map_name(self._settings['map'])
        if self._map != restored_map:
            #print(f'map restored: {self._map} -> {restored_map}')
            self._map = restored_map
            try:
                self.map_tex_name = get_map_class(self._map).get_preview_texture_name()
            except babase.NotFoundError:
                self.map_tex_name = 'null'
            updated = True

        if updated:
            self._refresh_settings_items()
            self._update_map_widget()
            play_ding_sound()
        else:
            play_error_sound()

    def _randomize_map(self):
        valid_maps = self._valid_maps_owned

        # Hmmm.. we own none of these maps.. just pick a random un-owned one
        # I guess.. should this ever happen?
        cur_map = choice(valid_maps)
        self._map = cur_map
        self.map_tex_name = get_map_class(cur_map).get_preview_texture_name()
        self._update_map_widget()

        play_deek_sound()

    def _update_map_widget(self):
        assert self.map_tex_name and self._map
        imagewidget(
            edit=self._map_imagewidget,
            texture=gettexture(self.map_tex_name)
        )
        textwidget(
            edit=self._map_textwidget,
            text=get_map_display_string(self._map)
        )

    def _shift_selected_map(self, index: int):
        """Shift selection in the valid maps list by target (wrap around)"""
        valid_maps = self._valid_maps_owned

        cur_map = self._map; assert cur_map
        try:
            cur_map_index = valid_maps.index(cur_map)
        except ValueError:
            cur_map_index = 0
        new_index = (cur_map_index + index) % len(valid_maps)

        self._map = valid_maps[new_index]
        self.map_tex_name = get_map_class(self._map).get_preview_texture_name()

        self._update_map_widget()
        play_click_sound()

    def _refresh_settings_items(self):
        uiscale = app.ui_v1.uiscale
        is_small_ui = uiscale is UIScale.SMALL

        pbtn = get_special_widget('squad_button')
        widget(edit=self.add_button, right_widget=pbtn, up_widget=pbtn)

        map_height = 100

        scroll_width = self._width - (86 + (3 if is_small_ui else 5.5) * self.x_inset)

        spacing = 47 # Scroller playlist config items spacing
        y_extra = 15 # For scroller widget

        # Calc our total height we'll need
        scroll_height = map_height + 10 # map select and margin
        scroll_height += spacing * len(self._settings_defs)

        if not self._scrollwidget:
            self._scrollwidget = bui.scrollwidget(
                parent=self._root_widget,
                position=(
                    44 + self.x_inset,
                    (95 if uiscale is UIScale.SMALL else 55) + y_extra + self.yoffs,
                ),
                size=(
                    scroll_width,
                    self._height - (166 if uiscale is UIScale.SMALL else 116),
                ),
                highlight=False,
                claims_left_right=True,
                selection_loops_to_parent=True,
                border_opacity=0.4,
            )
        if self._subcontainer:
            for child in self._subcontainer.get_children():
                child.delete()
            self._subcontainer.delete()

        self._subcontainer = containerwidget(
            parent=self._scrollwidget,
            size=(scroll_width, scroll_height),
            background=False,
            claims_left_right=True,
            selection_loops_to_parent=True,
        )

        v = scroll_height - 5
        h = -40

        # Keep track of all the selectable widgets we make so we can wire
        # them up conveniently.
        widget_column: list[list[bui.Widget]] = []

        b_color = color_theme.get_color('primary')
        b_textcolor = color_theme.get_color('secondary')

        textwidget(
            parent=self._subcontainer,
            position=(h + 49, v - 63),
            size=(100, 30),
            maxwidth=110,
            text=bui.Lstr(resource='mapText'),
            h_align='left',
            color=(0.8, 0.8, 0.8, 1.0),
            v_align='center',
        )
        assert self.map_tex_name
        map_tex = gettexture(self.map_tex_name)

        self._map_imagewidget = imagewidget(
            parent=self._subcontainer,
            size=(256 * 0.7, 125 * 0.7),
            position=(h + scroll_width * 0.46, v - 90),
            texture=map_tex,
            mesh_opaque=bui.getmesh('level_select_button_opaque'),
            mesh_transparent=bui.getmesh('level_select_button_transparent'),
            mask_texture=gettexture('mapPreviewMask'),
        )

        self._map_buttonwidget = None
        if len(self._valid_maps_owned) > 1:
            original_buttonwidget( # map_prev
                parent=self._subcontainer,
                position=(h + scroll_width * 0.46 - 50 - 1, v - 63),
                size=(35, 35),
                label='<',
                color=b_color,
                textcolor=b_textcolor,
                autoselect=True,
                on_activate_call=bui.CallPartial(self._shift_selected_map, -1),
                enable_sound=False,
                repeat=True,
            )
            original_buttonwidget( # map_next
                parent=self._subcontainer,
                position=(h + scroll_width * (0.655 if is_small_ui else 0.6225) + 5, v - 63),
                size=(35, 35),
                label='>',
                color=b_color,
                textcolor=b_textcolor,
                autoselect=True,
                on_activate_call=bui.CallPartial(self._shift_selected_map, 1),
                enable_sound=False,
                repeat=True,
            )
            original_buttonwidget(
                parent=self._subcontainer,
                size=(140, 60),
                position=(h + scroll_width * (0.775 if is_small_ui else 0.8), v - 72),
                on_activate_call=bui.CallStrict(self._randomize_map),
                enable_sound=False,
                color=b_color,
                textcolor=b_textcolor,
                scale=0.7,
                label="Randomize",
            )
            # Map select button.
            self._map_buttonwidget = original_buttonwidget(
                parent=self._subcontainer,
                size=(140, 60),
                position=(h + scroll_width * 0.9, v - 72),
                on_activate_call=bui.CallStrict(self._select_map),
                scale=0.7,
                color=b_color,
                textcolor=b_textcolor,
                label=bui.Lstr(resource='mapSelectText'),
            )
            widget_column.append([self._map_buttonwidget])

        assert self._map
        self._map_textwidget = textwidget(
            parent=self._subcontainer,
            position=(h + scroll_width * 0.496, v - 114),
            size=(100, 30),
            flatness=1.0,
            shadow=1.0,
            scale=0.55,
            maxwidth=256 * 0.7 * 0.8,
            text=get_map_display_string(self._map),
            h_align='center',
            color=(0.6, 1.0, 0.6, 1.0),
            v_align='center',
        )
        v -= map_height

        config = self._settings; assert config
        for setting in self._settings_defs:
            value = setting.default
            value_type = type(value)

            # Now, if there's an existing value for it in the config,
            # override with that.
            try:
                if config is not None:
                    if (
                        'settings' in config
                        and (seeting_name := setting.name) in config['settings']
                    ):
                        value = value_type(config['settings'][seeting_name])
                    elif (seeting_name := setting.name) in config:
                        value = value_type(config[seeting_name])
            except Exception:
                logging.exception('Error getting game setting.')

            # Shove the starting value in there to start.
            self._settings[setting.name] = value

            name_translated = self._get_localized_setting_name(setting.name)

            mw1 = 280
            mw2 = 70

            # Handle types with choices specially:
            item_h_pos = h + scroll_width * 0.96
            if isinstance(setting, bs.ChoiceSetting):
                invalid = False
                for choice in setting.choices:
                    if len(choice) != 2:
                        raise ValueError(
                            "Expected 2-member tuples for 'choices'; got: "
                            + repr(choice)
                        )
                    if not isinstance(choice[0], str):
                        raise TypeError(
                            'First value for choice tuple must be a str; got: '
                            + repr(choice)
                        )
                    if not isinstance(choice[1], value_type):
                        invalid = True
                        #raise TypeError(
                        #    'Choice type does not match default value; choice:'
                        #    + repr(choice)
                        #    + '; setting:'
                        #    + repr(setting)
                        #)
                if value_type not in (int, float):
                    raise TypeError(
                        'Choice type setting must have int or float default; '
                        'got: ' + repr(setting)
                    )

                # Start at the choice corresponding to the default if possible.
                self._choice_selections[setting.name] = 0
                for index, choice in enumerate(setting.choices):
                    if choice[1] == value:
                        self._choice_selections[setting.name] = index
                        break

                v -= spacing
                textwidget(
                    parent=self._subcontainer,
                    position=(h + 50, v),
                    size=(100, 30),
                    maxwidth=mw1,
                    text=name_translated,
                    h_align='left',
                    color=(0.8, 0.8, 0.8, 1.0),
                    v_align='center',
                )
                txt = textwidget(
                    parent=self._subcontainer,
                    position=(item_h_pos - 95, v),
                    size=(0, 28),
                    text=self._get_localized_setting_name(
                        setting.choices[self._choice_selections[setting.name]][
                            0
                        ]
                    ),
                    editable=False,
                    color=(0.6, 1.0, 0.6, 1.0),
                    maxwidth=mw2,
                    h_align='right',
                    v_align='center',
                    padding=2,
                )
                btn1 = original_buttonwidget(
                    parent=self._subcontainer,
                    position=(item_h_pos - 50 - 1, v),
                    size=(28, 28),
                    label='<',
                    color=b_color,
                    textcolor=b_textcolor,
                    autoselect=True,
                    on_activate_call=bui.CallStrict(
                        self._choice_inc, setting.name, txt, setting, -1
                    ) if not invalid else lambda: play_error_sound(),
                    repeat=True,
                )
                btn2 = original_buttonwidget(
                    parent=self._subcontainer,
                    position=(item_h_pos + 5, v),
                    size=(28, 28),
                    label='>',
                    color=b_color,
                    textcolor=b_textcolor,
                    autoselect=True,
                    on_activate_call=bui.CallStrict(
                        self._choice_inc, setting.name, txt, setting, 1
                    ) if not invalid else lambda: play_error_sound(),
                    repeat=True,
                )
                widget_column.append([btn1, btn2])

            elif isinstance(setting, (bs.IntSetting, bs.FloatSetting)):
                v -= spacing
                min_value = setting.min_value
                max_value = setting.max_value
                increment = setting.increment
                textwidget(
                    parent=self._subcontainer,
                    position=(h + 50, v),
                    size=(100, 30),
                    text=name_translated,
                    h_align='left',
                    color=(0.8, 0.8, 0.8, 1.0),
                    v_align='center',
                    maxwidth=mw1,
                )
                txt = textwidget(
                    parent=self._subcontainer,
                    position=(item_h_pos - 95, v),
                    size=(0, 28),
                    text=str(value),
                    editable=False,
                    color=(0.6, 1.0, 0.6, 1.0),
                    maxwidth=mw2,
                    h_align='right',
                    v_align='center',
                    padding=2,
                )
                btn1 = original_buttonwidget(
                    parent=self._subcontainer,
                    position=(item_h_pos - 50 - 1, v),
                    size=(28, 28),
                    label='-',
                    color=b_color,
                    textcolor=b_textcolor,
                    autoselect=True,
                    on_activate_call=bui.CallStrict(
                        self._inc,
                        txt,
                        min_value,
                        max_value,
                        -increment,
                        value_type,
                        setting.name,
                    ),
                    repeat=True,
                )
                btn2 = original_buttonwidget(
                    parent=self._subcontainer,
                    position=(item_h_pos + 5, v),
                    size=(28, 28),
                    label='+',
                    color=b_color,
                    textcolor=b_textcolor,
                    autoselect=True,
                    on_activate_call=bui.CallStrict(
                        self._inc,
                        txt,
                        min_value,
                        max_value,
                        increment,
                        value_type,
                        setting.name,
                    ),
                    repeat=True,
                )
                widget_column.append([btn1, btn2])

            elif value_type == bool:
                v -= spacing
                textwidget(
                    parent=self._subcontainer,
                    position=(h + 50, v),
                    size=(100, 30),
                    text=name_translated,
                    h_align='left',
                    color=(0.8, 0.8, 0.8, 1.0),
                    v_align='center',
                    maxwidth=mw1,
                )
                txt = textwidget(
                    parent=self._subcontainer,
                    position=(item_h_pos - 95, v),
                    size=(0, 28),
                    text=(
                        bui.Lstr(resource='onText')
                        if value
                        else bui.Lstr(resource='offText')
                    ),
                    editable=False,
                    color=(0.6, 1.0, 0.6, 1.0),
                    maxwidth=mw2,
                    h_align='right',
                    v_align='center',
                    padding=2,
                )
                cbw = checkboxwidget(
                    parent=self._subcontainer,
                    text='',
                    position=(item_h_pos - 50 - 5, v - 2),
                    size=(200, 30),
                    autoselect=True,
                    color=b_color,
                    textcolor=b_textcolor,
                    value=value,
                    on_value_change_call=bui.CallPartial(
                        self._check_value_change, setting.name, txt
                    ),
                )
                widget_column.append([cbw])

            else:
                raise TypeError(f'Invalid value type: {value_type}.')

        # Ok now wire up the column.
        try:
            prev_widgets: list[Widget] | None = None
            for cwdg in widget_column:
                if prev_widgets is not None:
                    # Wire our rightmost to their rightmost.
                    widget(edit=prev_widgets[-1], down_widget=cwdg[-1])
                    widget(edit=cwdg[-1], up_widget=prev_widgets[-1])

                    # Wire our leftmost to their leftmost.
                    widget(edit=prev_widgets[0], down_widget=cwdg[0])
                    widget(edit=cwdg[0], up_widget=prev_widgets[0])
                prev_widgets = cwdg
        except Exception:
            logging.exception(
                'Error wiring up game-settings-select widget column.'
            )


original_filter_playlist = filter_playlist
def new_filter_playlist(
    playlist: TypedPlaylistDict,
    sessiontype: type[bs.Session],
    *,
    add_resolved_type: bool = False,
    remove_unowned: bool = True,
    mark_unowned: bool = False,
    name: str = '?',
    print_exc: bool = True
) -> TypedPlaylistType:
    """Return a filtered version of a playlist.

    Strips out or replaces invalid or unowned game types, makes sure all
    settings are present, and adds in a 'resolved_type' which is the actual
    type.
    """
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    from bascenev1 import get_filtered_map_name, GameActivity

    assert app.classic is not None

    goodlist = TypedPlaylistType()
    available_maps: list[str] = list(app.classic.maps.keys())
    if (remove_unowned or mark_unowned) and app.classic is not None:
        unowned_maps = app.classic.store.get_unowned_maps()
        unowned_game_types = app.classic.store.get_unowned_game_types()
    else:
        unowned_maps = []
        unowned_game_types = set()

    for entry in deepcopy(playlist): # pyright: ignore[reportAssignmentType]
        entry: TypedPlaylistDict
        # 'map' used to be called 'level' here.
        if 'level' in entry:
            entry['map'] = entry['level']
            del entry['level']

        # We now stuff map into settings instead of it being its own thing.
        if 'map' in entry:
            entry['settings']['map'] = entry['map']
            del entry['map']

        # Update old map names to new ones.
        entry['settings']['map'] = get_filtered_map_name(
            entry['settings']['map']
        )
        if remove_unowned and entry['settings']['map'] in unowned_maps:
            continue

        # Ok, for each game in our list, try to import the module and grab
        # the actual game class. add successful ones to our initial list
        # to present to the user.
        if not isinstance(entry['type'], str):
            raise TypeError('invalid entry format')
        try:
            # Do some type filters for backwards compat.
            if entry['type'] in (
                'Assault.AssaultGame',
                'Happy_Thoughts.HappyThoughtsGame',
                'bsAssault.AssaultGame',
                'bs_assault.AssaultGame',
                'bastd.game.assault.AssaultGame',
            ):
                entry['type'] = 'bascenev1lib.game.assault.AssaultGame'
            if entry['type'] in (
                'King_of_the_Hill.KingOfTheHillGame',
                'bsKingOfTheHill.KingOfTheHillGame',
                'bs_king_of_the_hill.KingOfTheHillGame',
                'bastd.game.kingofthehill.KingOfTheHillGame',
            ):
                entry['type'] = (
                    'bascenev1lib.game.kingofthehill.KingOfTheHillGame'
                )
            if entry['type'] in (
                'Capture_the_Flag.CTFGame',
                'bsCaptureTheFlag.CTFGame',
                'bs_capture_the_flag.CTFGame',
                'bastd.game.capturetheflag.CaptureTheFlagGame',
            ):
                entry['type'] = (
                    'bascenev1lib.game.capturetheflag.CaptureTheFlagGame'
                )
            if entry['type'] in (
                'Death_Match.DeathMatchGame',
                'bsDeathMatch.DeathMatchGame',
                'bs_death_match.DeathMatchGame',
                'bastd.game.deathmatch.DeathMatchGame',
            ):
                entry['type'] = 'bascenev1lib.game.deathmatch.DeathMatchGame'
            if entry['type'] in (
                'ChosenOne.ChosenOneGame',
                'bsChosenOne.ChosenOneGame',
                'bs_chosen_one.ChosenOneGame',
                'bastd.game.chosenone.ChosenOneGame',
            ):
                entry['type'] = 'bascenev1lib.game.chosenone.ChosenOneGame'
            if entry['type'] in (
                'Conquest.Conquest',
                'Conquest.ConquestGame',
                'bsConquest.ConquestGame',
                'bs_conquest.ConquestGame',
                'bastd.game.conquest.ConquestGame',
            ):
                entry['type'] = 'bascenev1lib.game.conquest.ConquestGame'
            if entry['type'] in (
                'Elimination.EliminationGame',
                'bsElimination.EliminationGame',
                'bs_elimination.EliminationGame',
                'bastd.game.elimination.EliminationGame',
            ):
                entry['type'] = 'bascenev1lib.game.elimination.EliminationGame'
            if entry['type'] in (
                'Football.FootballGame',
                'bsFootball.FootballTeamGame',
                'bs_football.FootballTeamGame',
                'bastd.game.football.FootballTeamGame',
            ):
                entry['type'] = 'bascenev1lib.game.football.FootballTeamGame'
            if entry['type'] in (
                'Hockey.HockeyGame',
                'bsHockey.HockeyGame',
                'bs_hockey.HockeyGame',
                'bastd.game.hockey.HockeyGame',
            ):
                entry['type'] = 'bascenev1lib.game.hockey.HockeyGame'
            if entry['type'] in (
                'Keep_Away.KeepAwayGame',
                'bsKeepAway.KeepAwayGame',
                'bs_keep_away.KeepAwayGame',
                'bastd.game.keepaway.KeepAwayGame',
            ):
                entry['type'] = 'bascenev1lib.game.keepaway.KeepAwayGame'
            if entry['type'] in (
                'Race.RaceGame',
                'bsRace.RaceGame',
                'bs_race.RaceGame',
                'bastd.game.race.RaceGame',
            ):
                entry['type'] = 'bascenev1lib.game.race.RaceGame'
            if entry['type'] in (
                'bsEasterEggHunt.EasterEggHuntGame',
                'bs_easter_egg_hunt.EasterEggHuntGame',
                'bastd.game.easteregghunt.EasterEggHuntGame',
            ):
                entry['type'] = (
                    'bascenev1lib.game.easteregghunt.EasterEggHuntGame'
                )
            if entry['type'] in (
                'bsMeteorShower.MeteorShowerGame',
                'bs_meteor_shower.MeteorShowerGame',
                'bastd.game.meteorshower.MeteorShowerGame',
            ):
                entry['type'] = (
                    'bascenev1lib.game.meteorshower.MeteorShowerGame'
                )
            if entry['type'] in (
                'bsTargetPractice.TargetPracticeGame',
                'bs_target_practice.TargetPracticeGame',
                'bastd.game.targetpractice.TargetPracticeGame',
            ):
                entry['type'] = (
                    'bascenev1lib.game.targetpractice.TargetPracticeGame'
                )
        except Exception:
            if print_exc:
                logging.exception('Error in new_filter_playlist.')

        neededsettings = list[bs.Setting]()
        gameclass = None
        try:
            gameclass = babase.getclass(entry['type'], GameActivity)

            if remove_unowned and gameclass in unowned_game_types:
                continue
            if add_resolved_type:
                entry['resolved_type'] = gameclass
            if mark_unowned and gameclass in unowned_game_types:
                entry['is_unowned_game'] = True
            neededsettings = gameclass.get_available_settings(sessiontype)

        except babase.MapNotFoundError:
            if print_exc:
                logging.warning(
                    'Map \'%s\' not found while scanning playlist \'%s\'.',
                    entry['settings']['map'],
                    name,
                )
        except ImportError as e:
            if print_exc:
                logging.warning(
                    'Import failed while scanning playlist \'%s\': %s', name, e
                )
            entry['is_game_invalid'] = True
        # This exception usually happens when we could get the game 'module'
        # but, we couldn't get game's GameActivity class name from `entry['type']`
        except AttributeError as e:
            logging.warning(
                    'Get class failed while scanning playlist \'%s\': %s', name, e
                )
            entry['is_game_invalid'] = True

        # We 'manually' add some of basic ba*.setting(s) to the filter
        # if it exists in raw settings
        if entry['settings']['map'] not in available_maps:
            entry['is_map_invalid'] = True

        if mark_unowned and entry['settings']['map'] in unowned_maps:
            entry['is_unowned_map'] = True

        # Make sure all settings the game defines are present.
        for setting in neededsettings:
            if setting.name not in entry['settings']:
                entry['settings'][setting.name] = setting.default

        goodlist.append(entry)

    return goodlist


def apply_packages():
    bauiv1lib.playlist.editcontroller.PlaylistEditController = FluffyPlaylistEditController # Playlist editor controller for PlaylistEditWindow

    bauiv1lib.playlist.editgame.PlaylistEditGameWindow = FluffyPlaylistEditGameWindow # Playlist Game Editer Window
    bauiv1lib.playlist.edit.PlaylistEditWindow = FluffyPlaylistEditWindow # Playlist Editor Window

    bs.filter_playlist = new_filter_playlist
    bs._playlist.filter_playlist = new_filter_playlist # pyright: ignore[reportAttributeAccessIssue]


# ba_meta export babase.Plugin
class by_FluffyPal(Plugin):
    def on_app_running(self) -> None:
        apply_packages()
