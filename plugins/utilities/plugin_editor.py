# ba_meta require api 8

# Made by Vishal / Vishuuu / Vishal338
# Made for everyone who uses it.
# Let's you edit Plugins which are in your device.
# Doesn't work for workspaces.
# Safety Point: Don't mess with the code
# or you might lose all your plugins.

from __future__ import annotations

import os
from typing import TYPE_CHECKING, assert_never

import babase as ba
import bascenev1 as bs
import bauiv1 as bui
from bauiv1lib import popup
from bauiv1lib.confirm import ConfirmWindow
from bauiv1lib.settings.plugins import PluginWindow, Category
import bauiv1lib.settings.plugins as plugs

if TYPE_CHECKING:
    pass


class EditModWindow(bui.Window):
    """Window for viewing/editing plugins."""

    def __init__(
        self,
        transition: str = 'in_right',
        origin_widget: bui.Widget | None = None,
        plugin: str | None = None,
        view_type: str | None = None,
    ):
        # pylint: disable=too-many-statements
        app = bui.app

        # If they provided an origin-widget, scale up from that.
        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 870.0 if uiscale is bui.UIScale.SMALL else 670.0
        self._x_inset = 100 if uiscale is bui.UIScale.SMALL else 0
        self._height = (
            390.0
            if uiscale is bui.UIScale.SMALL
            else 450.0 if uiscale is bui.UIScale.MEDIUM else 520.0
        )
        top_extra = 10 if uiscale is bui.UIScale.SMALL else 0
        self._theme = ba.app.config.get('Plugin Editor Theme', 'default')

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + top_extra),
                transition=transition,
                toolbar_visibility='menu_minimal',
                scale_origin_stack_offset=scale_origin,
                color=(0.13, 0.13, 0.13) if self._theme == 'dark' else None,
                scale=(
                    2.06
                    if uiscale is bui.UIScale.SMALL
                    else 1.4 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, -25) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            )
        )

        self._scroll_width = self._width - (100 + 2 * self._x_inset)
        self._scroll_height = self._height - 115.0
        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 724.0

        Plugin_Name = 'plugin_editor'
        self._plugin = plugin
        self._view_type = view_type if view_type is not None else 'view'
        self._lines = []
        self._original_lines = []
        self._widgets = []
        self._selected_line_widget: ba.Widget | None = None
        self._saving = False
        self._shown = False
        self._plug_path = ba.env()['python_directory_user']
        self._same_plug = __file__ in (self._plug_path + '\\' + self._plugin + '.py',
                                       self._plug_path + '/' + self._plugin + '.py')
        self._plug_exists = os.path.exists(self._plug_path + os.sep + self._plugin + '.py')

        if self._theme == 'dark':
            self._tint = bs.get_foreground_host_activity().globalsnode.tint
            bs.get_foreground_host_activity().globalsnode.tint = (0.4, 0.4, 0.4)
        assert app.classic is not None
        if app.ui_v1.use_toolbars and uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self._do_back
            )
            self._back_button = None
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(53 + self._x_inset, self._height - 60),
                size=(140, 60),
                scale=0.8,
                autoselect=True,
                label=bui.Lstr(resource='backText'),
                button_type='back',
                on_select_call=bui.Call(self._update_line_num),
                on_activate_call=bui.Call(self._back_button_clicked)
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        if not self._same_plug and self._plug_exists:
            self._line_num = bui.textwidget(
                parent=self._root_widget,
                position=(
                    self._width * (0.25 if bui.app.ui_v1.uiscale is bui.UIScale.SMALL
                                   else 0.175),
                    self._height - 60),
                size=(120, 30),
                text='1',
                color=(0.75, 0.7, 0.8),
                h_align='center',
                v_align='center',
                selectable=True,
                always_highlight=True,
                editable=True,
            )

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 41),
            size=(0, 0),
            text=bui.Lstr(value=(self._plugin + '.py')),
            color=app.ui_v1.title_color,
            maxwidth=170,
            h_align='center',
            v_align='center',
        )

        if self._same_plug:
            bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5, self._height * 0.6),
                size=(0, 0),
                text=bui.Lstr(value=f'You can\'t {self._view_type} the Editor, you PSYCHO!'),
                color=(0.7, 0.8, 0.7),
                h_align='center',
                v_align='center',
            )
            if Plugin_Name != self._plugin:
                bui.textwidget(
                    parent=self._root_widget,
                    position=(self._width * 0.5, self._height * 0.5),
                    size=(0, 0),
                    text=bui.Lstr(value='You tryna change the file name? HAHAHA!'),
                    color=(0.7, 0.8, 0.7),
                    h_align='center',
                    v_align='center',
                )

        if self._back_button is not None:
            bui.buttonwidget(
                edit=self._back_button,
                button_type='backSmall',
                size=(60, 60),
                label=bui.charstr(bui.SpecialChar.BACK),
            )

        if not self._same_plug:
            if self._plug_exists:
                plug_code = open(self._plug_path + os.sep + self._plugin + '.py', 'r')
                self._plug_lines = plug_code.readlines()
                plug_code.close()
            else:
                bui.textwidget(
                    parent=self._root_widget,
                    position=(self._width * 0.5, self._height * 0.6),
                    size=(0, 0),
                    text=bui.Lstr(value='Either this is a Workspace Plugin or I can\'t find this.'),
                    color=(0.7, 0.8, 0.7),
                    h_align='center',
                    v_align='center',
                )
                return
            self._shown = True
            if self._view_type == 'edit':
                self._add_line_button = bui.buttonwidget(
                    parent=self._root_widget,
                    position=(self._width * 0.5 + 100, self._height - 60),
                    button_type='square',
                    size=(30, 30),
                    label='+',
                    on_activate_call=bui.Call(self._add_line),
                )
                self._remove_line_button = bui.buttonwidget(
                    parent=self._root_widget,
                    position=(self._width * 0.5 + 145, self._height - 60),
                    button_type='square',
                    size=(30, 30),
                    label='-',
                    color=(1, 0, 0),
                    on_activate_call=bui.Call(self._remove_line),
                )
                self._save_button = bui.buttonwidget(
                    parent=self._root_widget,
                    position=(self._width * 0.5 + 190, self._height - 60),
                    size=(80, 30),
                    label='Save',
                    on_activate_call=lambda: ConfirmWindow(
                        action=self._save_button_clicked
                    ),
                )
                bui.widget(
                    edit=self._save_button,
                    right_widget=self._save_button,
                    up_widget=self._save_button
                )

            self._scrollwidget = bui.scrollwidget(
                parent=self._root_widget,
                position=(50 + self._x_inset, 50),
                simple_culling_v=20.0,
                highlight=False,
                size=(self._scroll_width, self._scroll_height),
                selection_loops_to_parent=True,
                claims_left_right=True,
            )
            bui.widget(edit=self._scrollwidget, right_widget=self._scrollwidget)

            self._longest_len = 0
            for line in self._plug_lines:
                line = line[0:len(line)-(1 if line[len(line)-1] == '\n' else 0)]
                self._lines.append(line)
                if self._longest_len < len(line):
                    self._longest_len = len(line)
            self._original_lines = self._lines.copy()

            plug_line_height = 18
            sub_width = self._scroll_width
            sub_height = (len(self._lines) + 1) * plug_line_height
            self._subcontainer = bui.containerwidget(
                parent=self._scrollwidget,
                size=(sub_width, sub_height),
                background=False,
            )

            bui.widget(
                edit=self._back_button,
                right_widget=self._line_num,
                down_widget=(
                    self._subcontainer if self._selected_line_widget is None else
                    self._selected_line_widget
                )
            )
            bui.widget(
                edit=self._line_num,
                up_widget=self._line_num,
                down_widget=(
                    self._subcontainer if self._selected_line_widget is None else
                    self._selected_line_widget
                )
            )
            if self._view_type == 'edit':
                bui.widget(
                    edit=self._add_line_button,
                    up_widget=self._add_line_button,
                    down_widget=(
                        self._subcontainer if self._selected_line_widget is None else
                        self._selected_line_widget
                    )
                )
                bui.widget(
                    edit=self._remove_line_button,
                    up_widget=self._remove_line_button,
                    down_widget=(
                        self._subcontainer if self._selected_line_widget is None else
                        self._selected_line_widget
                    )
                )

            self._show_lines()
            self._timer = bui.AppTimer(0.1, self._update_line_num, repeat=True)

    def _show_lines(self) -> None:

        sub_height = (len(self._lines) + 1) * 18
        bui.containerwidget(edit=self._subcontainer,
                            size=(self._scroll_width, sub_height))

        self._widgets = []
        y_num = 18 * (len(self._lines) - 1) + 10
        for num, line in enumerate(self._lines):
            bui.textwidget(
                parent=self._subcontainer,
                position=(23, y_num + 9),
                size=(0, 0),
                scale=0.5,
                text=str(num+1),
                h_align='right',
                v_align='center',
            )
            abc = bui.textwidget(
                parent=self._subcontainer,
                position=(-151, y_num),
                size=(880, 18),
                color=(1.2, 1.2, 1.2),
                scale=0.6,
                text=line,
                selectable=True,
                maxwidth=527,
                h_align='left',
                v_align='center',
                always_highlight=True,
            )
            bui.widget(
                edit=abc,
                left_widget=self._back_button,
                right_widget=self._add_line_button if self._view_type == 'edit' else abc,
            )

            def edit_them(obj):
                if self._view_type == 'edit':
                    self._un_editable_all()
                    try:
                        bui.textwidget(edit=obj, editable=True)
                    except:
                        pass
                    self._save_code()
                self._selected_line_widget = obj
                try:
                    bui.textwidget(edit=self._line_num,
                                   text=str(self._widgets.index(obj)+1)
                                   )
                except:
                    pass

            bui.textwidget(edit=abc,
                           on_select_call=bui.Call(edit_them, abc),
                           on_activate_call=bui.Call(edit_them, abc))
            y_num -= 18
            self._widgets.append(abc)

    def _un_editable_all(self) -> None:
        for line in self._widgets:
            bui.textwidget(edit=line, editable=False)

    def _remove_line(self) -> None:
        if self._selected_line_widget is None:
            bui.screenmessage('Line is not selected.')
            return
        index = self._widgets.index(self._selected_line_widget)
        self._lines.pop(index)
        if len(self._lines) == 0:
            self._lines.append('')
        self._clear_scroll_widget()
        self._show_lines()
        bui.containerwidget(
            edit=self._subcontainer,
            selected_child=self._widgets[index-1 if index > 0 else 0]
        )
        self._selected_line_widget = self._widgets[index-1 if index > 0 else 0]

    def _add_line(self) -> None:
        if self._selected_line_widget is None:
            bui.screenmessage('Line is not selected.')
            return
        index = self._widgets.index(self._selected_line_widget)
        spaces = ''
        for ch in self._lines[index]:
            if ch != ' ':
                break
            spaces += ch
        if self._lines[index][-1:] == ':':
            spaces += '    '
        self._lines.insert(index+1, spaces)
        self._clear_scroll_widget()
        self._show_lines()
        bui.containerwidget(
            edit=self._subcontainer,
            selected_child=self._widgets[index+1]
        )
        self._selected_line_widget = self._widgets[index+1]

    def _save_code(self) -> None:
        for num, widget in enumerate(self._widgets):
            self._lines[num] = bui.textwidget(parent=self._subcontainer, query=widget)

    def _save_button_clicked(self) -> None:
        if self._saving:
            return
        self._saving = True
        self._save_code()
        file = open(self._plug_path + os.sep + self._plugin + '.py', 'w')
        file.writelines([line + '\n' for line in self._lines])
        file.close()
        bui.screenmessage(self._plugin + '.py Saved')
        self._saving = False
        self._do_back()

    def _update_line_num(self) -> None:
        try:
            index = int(bui.textwidget(query=self._line_num))
            if self._widgets[index-1] != self._selected_line_widget:
                bui.containerwidget(
                    edit=self._subcontainer,
                    selected_child=self._widgets[index-1],
                    visible_child=self._widgets[index-1]
                )
                self._selected_line_widget = self._widgets[index-1]
        except (IndexError, ValueError, AttributeError):
            pass

    def _clear_scroll_widget(self) -> None:
        existing_widgets = self._subcontainer.get_children()
        if existing_widgets:
            for i in existing_widgets:
                i.delete()

    def _back_button_clicked(self) -> None:
        if self._view_type == 'edit' and not self._same_plug and self._shown:
            ConfirmWindow(action=self._do_back)
        else:
            self._do_back()

    def _do_back(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.plugins import PluginWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        self._timer = None
        if self._theme == 'dark':
            bs.get_foreground_host_activity().globalsnode.tint = self._tint
        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            PluginWindow(transition='in_left').get_root_widget(),
            from_window=self._root_widget,
        )


class Plugin_Window(PluginWindow):
    def __init__(
        self,
        transition: str = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        self._info = []
        self._popup_type = None
        PluginWindow.__init__(self, transition, origin_widget)

    def _show_category_options(self) -> None:
        self._popup_type = 'category'
        PluginWindow._show_category_options(self)

    def _show_plugins(self) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        plugspecs = bui.app.plugins.plugin_specs
        plugstates: dict[str, dict] = bui.app.config.setdefault('Plugins', {})
        assert isinstance(plugstates, dict)

        plug_line_height = 50
        sub_width = self._scroll_width
        num_enabled = 0
        num_disabled = 0

        plugspecs_sorted = sorted(plugspecs.items())

        bui.textwidget(
            edit=self._no_plugins_installed_text,
            text='',
        )

        for _classpath, plugspec in plugspecs_sorted:
            # counting number of enabled and disabled plugins
            # plugstate = plugstates.setdefault(plugspec[0], {})
            if plugspec.enabled:
                num_enabled += 1
            else:
                num_disabled += 1

        if self._category is Category.ALL:
            sub_height = len(plugspecs) * plug_line_height
            bui.containerwidget(
                edit=self._subcontainer, size=(self._scroll_width, sub_height)
            )
        elif self._category is Category.ENABLED:
            sub_height = num_enabled * plug_line_height
            bui.containerwidget(
                edit=self._subcontainer, size=(self._scroll_width, sub_height)
            )
        elif self._category is Category.DISABLED:
            sub_height = num_disabled * plug_line_height
            bui.containerwidget(
                edit=self._subcontainer, size=(self._scroll_width, sub_height)
            )
        else:
            # Make sure we handle all cases.
            assert_never(self._category)

        num_shown = 0
        for classpath, plugspec in plugspecs_sorted:
            plugin = plugspec.plugin
            enabled = plugspec.enabled

            if self._category is Category.ALL:
                show = True
            elif self._category is Category.ENABLED:
                show = enabled
            elif self._category is Category.DISABLED:
                show = not enabled
            else:
                assert_never(self._category)

            if not show:
                continue

            item_y = sub_height - (num_shown + 1) * plug_line_height
            check = bui.checkboxwidget(
                parent=self._subcontainer,
                text=bui.Lstr(value=classpath),
                autoselect=True,
                value=enabled,
                maxwidth=self._scroll_width - 200,
                position=(10, item_y),
                size=(self._scroll_width - 40, 50),
                on_value_change_call=bui.Call(
                    self._check_value_changed, plugspec
                ),
                textcolor=(
                    (0.8, 0.3, 0.3)
                    if (plugspec.attempted_load and plugspec.plugin is None)
                    else (
                        (0.6, 0.6, 0.6)
                        if plugspec.plugin is None
                        else (0, 1, 0)
                    )
                ),
            )
            # noinspection PyUnresolvedReferences
            button = bui.buttonwidget(
                parent=self._subcontainer,
                label=bui.Lstr(resource='mainMenu.settingsText'),
                autoselect=True,
                size=(100, 40),
                position=(sub_width - 130, item_y + 6),
            )
            # noinspection PyUnresolvedReferences
            bui.buttonwidget(
                edit=button,
                on_activate_call=bui.Call(
                    self._show_menu,
                    button,
                    (plugin.show_settings_ui if plugin is not None and plugin.has_settings_ui() else None),
                    plugin,
                    classpath
                ),
            )

            # Allow getting back to back button.
            if num_shown == 0:
                bui.widget(
                    edit=check,
                    up_widget=self._back_button,
                    left_widget=self._back_button,
                    right_widget=button,
                )
                bui.widget(edit=button, up_widget=self._back_button)

            # Make sure we scroll all the way to the end when using
            # keyboard/button nav.
            bui.widget(edit=check, show_buffer_top=40, show_buffer_bottom=40)
            num_shown += 1

        bui.textwidget(
            edit=self._num_plugins_text,
            text=str(num_shown),
        )

        if num_shown == 0:
            bui.textwidget(
                edit=self._no_plugins_installed_text,
                text=bui.Lstr(resource='noPluginsInstalledText'),
            )

    def _show_menu(self, button, func, plugin, classpath) -> None:
        choices = ['view', 'edit', 'settings'
                   ] if plugin is not None and plugin.has_settings_ui() else ['view', 'edit']
        choices_display = [
            bui.Lstr(value='View Code'),
            bui.Lstr(value='Edit Code'),
            bui.Lstr(value='Settings'),
        ] if plugin is not None and plugin.has_settings_ui() else [
            bui.Lstr(value='View Code'),
            bui.Lstr(value='Edit Code')
        ]
        popup.PopupMenuWindow(
            position=button.get_screen_space_center(),
            choices=choices,
            choices_display=choices_display,
            current_choice='settings',
            width=100,
            delegate=self,
            scale=(
                2.3
                if bui.app.ui_v1.uiscale is bui.UIScale.SMALL
                else 1.65 if bui.app.ui_v1.uiscale is bui.UIScale.MEDIUM else 1.23
            ),
        )
        self._info = [button, func, classpath]
        self._popup_type = 'options'

    def popup_menu_selected_choice(
        self, popup_window: popup.PopupMenuWindow, choice: str
    ) -> None:
        """Called when a choice is selected in the popup."""
        del popup_window  # unused
        if self._popup_type == 'category':
            self._category = Category(choice)
            self._clear_scroll_widget()
            self._show_plugins()
            bui.buttonwidget(
                edit=self._category_button,
                label=bui.Lstr(resource=self._category.resource),
            )
        elif self._popup_type == 'options':
            self._abc(self._info[0], self._info[1], self._info[2], choice)

    def _abc(self, button, func, plugin, view_mode: str) -> None:
        # pylint: disable=cyclic-import
        if view_mode == 'view' or view_mode == 'edit':
            # no-op if our underlying widget is dead or on its way out.
            if not self._root_widget or self._root_widget.transitioning_out:
                return

            self._save_state()
            bui.containerwidget(edit=self._root_widget, transition='out_left')
            assert bui.app.classic is not None
            bui.app.ui_v1.set_main_menu_window(
                EditModWindow(
                    transition='in_right',
                    plugin=plugin.split('.')[0],
                    view_type=view_mode
                ).get_root_widget(),
                from_window=self._root_widget,
            )
        elif view_mode == 'settings':
            func(button)


class PluginEditorSettingsWindow(popup.PopupWindow):
    def __init__(self, origin_widget):
        self.scale_origin = origin_widget.get_screen_space_center()
        bui.getsound('swish').play()
        _uiscale = bui.app.ui_v1.uiscale
        s = 1.65 if _uiscale is ba.UIScale.SMALL else 1.39 if _uiscale is ba.UIScale.MEDIUM else 1.67
        width = 400 * s
        height = width * 0.5
        color = (1, 1, 1)
        text_scale = 0.7 * s
        self._transition_out = 'out_scale'
        transition = 'in_scale'

        self._root_widget = bui.containerwidget(size=(width, height),
                                                on_outside_click_call=self._back,
                                                transition=transition,
                                                scale=(1.5 if _uiscale is ba.UIScale.SMALL else 1.5
                                                       if _uiscale is ba.UIScale.MEDIUM else 1.0),
                                                scale_origin_stack_offset=self.scale_origin)

        bui.textwidget(parent=self._root_widget,
                       position=(width * 0.49, height * 0.87), size=(0, 0),
                       h_align='center', v_align='center', text='Plugin Editor Settings',
                       scale=text_scale * 1.25, color=bui.app.ui_v1.title_color,
                       maxwidth=width * 0.9)

        back_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.1, height * 0.8),
            size=(60, 60),
            scale=0.8,
            label=ba.charstr(ba.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self._back)

        bui.containerwidget(edit=self._root_widget, cancel_button=back_button)

        bui.textwidget(parent=self._root_widget,
                       position=(width * 0.32, height * 0.5),
                       size=(0, 0),
                       h_align='center',
                       v_align='center',
                       text='Theme :',
                       scale=text_scale * 1.15,
                       color=bui.app.ui_v1.title_color
                       )

        popup.PopupMenu(
            parent=self._root_widget,
            position=(width * 0.42, height * 0.5 - 30),
            button_size=(200.0, 60.0),
            width=100.0,
            choices=[
                'default',
                'dark',
            ],
            choices_display=[
                bui.Lstr(value='Default'),
                bui.Lstr(value='Dark'),
            ],
            current_choice=ba.app.config.get('Plugin Editor Theme', 'default'),
            on_value_change_call=self._set_theme,
        )

    def _set_theme(self, val: str) -> None:
        if ba.app.config.get('Plugin Editor Theme', 'default') != val:
            cfg = bui.app.config
            cfg['Plugin Editor Theme'] = val
            cfg.apply_and_commit()
            bui.screenmessage(
                bui.Lstr(value=f'Editor Theme changed to {val.title()}'),
                color=(0.0, 1.0, 0.0),
            )

    def _back(self) -> None:
        bui.getsound('swish').play()
        bui.containerwidget(edit=self._root_widget, transition='out_scale')


# ba_meta export plugin
class ByVishuuu(ba.Plugin):
    """A plugin to edit plugins."""

    def __init__(self) -> None:
        plugs.PluginWindow = Plugin_Window

    def has_settings_ui(self):
        return True

    def show_settings_ui(self, source_widget):
        PluginEditorSettingsWindow(source_widget)
