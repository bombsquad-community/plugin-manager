# ba_meta require api 7
import ba
import _ba
import bastd

import urllib.request
import json
import os
import asyncio

from typing import Union, Optional

_env = _ba.env()

INDEX_META = "https://raw.githubusercontent.com/bombsquad-community/mod-manager/main/index.json"
HEADERS = {
    "User-Agent": _env["user_agent_string"],
}
PLUGIN_DIRECTORY = _env["python_directory_user"]
PLUGIN_ENTRYPOINT = "Main"


async def send_network_request(request):
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, urllib.request.urlopen, request)
    return response


class Category:
    def __init__(self, name, base_download_url, meta_url):
        self.name = name
        self.base_download_url = base_download_url
        self.meta_url = meta_url
        self._plugins = None

    async def get_plugins(self):
        if self._plugins is None:
            request = urllib.request.Request(
                self.meta_url,
                headers=HEADERS
            )
            response = await send_network_request(request)
            plugins_info = json.loads(response.read())
            self._plugins = ([Plugin(plugin_info, self.base_download_url)
                             for plugin_info in plugins_info.items()])
        return self._plugins

    async def refresh(self):
        self._plugins = {}
        return await self.get_plugins()


class CategoryAll(Category):
    def __init__(self, plugins={}):
        super().__init__(name="All", base_download_url=None, meta_url=None)
        self._plugins = plugins


class Plugin:
    def __init__(self, plugin, base_download_url):
        self.name, self.info = plugin
        self.install_path = os.path.join(PLUGIN_DIRECTORY, f"{self.name}.py")
        self.download_url = f"{base_download_url}/{self.name}.py"
        self.entry_point = f"{self.name}.{PLUGIN_ENTRYPOINT}"

    @property
    def installed(self):
        return os.path.isfile(self.install_path)

    @property
    def enabled(self):
        try:
            return ba.app.config["Plugins"][self.entry_point]["enabled"]
        except KeyError:
            return False

    async def install(self):
        response = await send_network_request(self.download_url)
        with open(self.install_path, "wb") as fout:
            fout.write(response.read())
        self.enable()

    def uninstall(self):
        os.remove(self.install_path)

    def _set_status(self, to_enable=True):
        if self.entry_point not in ba.app.config["Plugins"]:
            ba.app.config["Plugins"][self.entry_point] = {}
        ba.app.config["Plugins"][self.entry_point]["enabled"] = to_enable

    def enable(self):
        self._set_status(to_enable=True)
        ba.app.config.apply_and_commit()

    def disable(self):
        self._set_status(to_enable=False)
        ba.app.config.commit()


class PluginWindow(ba.Window):
    def __init__(self, plugin, origin_widget):
        uiscale = ba.app.ui.uiscale
        b_color = (0.6, 0.53, 0.63)
        b_text_color = (0.75, 0.7, 0.8)
        s = 1.1 if uiscale is ba.UIScale.SMALL else 1.27 if ba.UIScale.MEDIUM else 1.57
        width = 360 * s
        height = 100 + 100 * s
        color = (1, 1, 1)
        text_scale = 0.7 * s
        self._transition_out = 'out_scale'
        transition = 'in_scale'
        scale_origin = origin_widget.get_screen_space_center()
        self._root_widget = ba.containerwidget(size=(width, height),
                                               parent=_ba.get_special_widget(
                                                   'overlay_stack'),
                                               # on_outside_click_call=self._ok,
                                               transition=transition,
                                               scale=(2.1 if uiscale is ba.UIScale.SMALL else 1.5
                                                      if uiscale is ba.UIScale.MEDIUM else 1.0),
                                               scale_origin_stack_offset=scale_origin)
        pos = height * 0.8
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.49, pos), size=(0, 0),
                      h_align='center', v_align='center', text=plugin.name,
                      scale=text_scale * 1.25, color=color,
                      maxwidth=width * 0.9)
        pos -= 25
        # author =
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.49, pos),
                      size=(0, 0),
                      h_align='center',
                      v_align='center',
                      text='by ' + plugin.info["authors"][0]["name"],
                      scale=text_scale * 0.8,
                      color=color, maxwidth=width * 0.9)
        pos -= 35
        # status = ba.textwidget(parent=self._root_widget,
        #                        position=(width * 0.49, pos), size=(0, 0),
        #                        h_align='center', v_align='center',
        #                        text=status_text, scale=text_scale * 0.8,
        #                        color=color, maxwidth=width * 0.9)
        pos -= 25
        # info =
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.49, pos), size=(0, 0),
                      h_align='center', v_align='center',
                      text=plugin.info["description"],
                      scale=text_scale * 0.6, color=color,
                      maxwidth=width * 0.95)
        b3_color = (0.8, 0.15, 0.35)
        # b3_color = (0.15, 0.80, 0.35)
        pos = height * 0.1
        button_size = (80 * s, 40 * s)
        if plugin.installed:
            if plugin.enabled:
                button1_label = "Disable"
                button1_action = plugin.disable
            else:
                button1_label = "Enable"
                button1_action = plugin.enable
            button2_label = "Uninstall"
            button2_action = plugin.uninstall
        else:
            button1_label = "Install"
            loop = asyncio.get_event_loop()
            button1_action = ba.Call(loop.create_task, plugin.install())
            # button1_action = asyncio.run, plugin.install
        button3_label = "OK"

        # button1 =
        ba.buttonwidget(parent=self._root_widget,
                        position=(width * 0.1, pos),
                        size=button_size,
                        on_activate_call=button1_action,
                        color=b_color,
                        textcolor=b_text_color,
                        button_type='square',
                        text_scale=1,
                        label=button1_label)

        if plugin.installed:
            # button2 =
            ba.buttonwidget(parent=self._root_widget,
                            position=(width * 0.4, pos),
                            size=button_size,
                            on_activate_call=button2_action,
                            color=b3_color,
                            textcolor=b_text_color,
                            button_type='square',
                            text_scale=1,
                            label=button2_label)

        button3 = ba.buttonwidget(parent=self._root_widget,
                                  position=(width * 0.7, pos),
                                  size=button_size,
                                  on_activate_call=self.button3_action,
                                  autoselect=True,
                                  button_type='square',
                                  text_scale=1,
                                  label=button3_label)
        ba.containerwidget(edit=self._root_widget,
                           on_cancel_call=button3.activate)
        ba.containerwidget(edit=self._root_widget, selected_child=button3)
        ba.containerwidget(edit=self._root_widget, start_button=button3)

    def button3_action(self) -> None:
        return None


class PluginManager:
    def __init__(self):
        self.request_headers = HEADERS
        self._index = {}

    # @property
    # def index(self):
    #     if not self._index:
    #         loop = asyncio.get_event_loop()
    #         self._index = loop.create_task(self.plugin_index())
    #     return self._index

    # def plugin_index(self):
    #     loop = asyncio.get_event_loop()
    #     loop.create_task(self.plugin_index())

    async def get_index(self):
        if not self._index:
            request = urllib.request.Request(
                INDEX_META,
                headers=HEADERS
            )
            response = await send_network_request(request)
            self._index = json.loads(response.read())
        return self._index

    async def refresh(self):
        self._index = {}
        return await self.get_index()


class PluginManagerWindow(ba.Window, PluginManager):
    def __init__(self, transition: str = "in_right", origin_widget: ba.Widget = None):
        PluginManager.__init__(self)
        self.categories = {}
        self.category_selection_button = None
        self.selected_category = None

        # ba._asyncio._asyncio_event_loop.create_task(self.setup_plugin_categories())
        ba._asyncio._asyncio_event_loop.create_task(self.plugin_index())

        uiscale = ba.app.ui.uiscale

        self._width = 650
        self._height = (380 if uiscale is ba.UIScale.SMALL
                        else 420 if uiscale is ba.UIScale.MEDIUM
                        else 500)
        top_extra = 20 if uiscale is ba.UIScale.SMALL else 0

        if origin_widget:
            self._transition_out = "out_scale"
            self._scale_origin = origin_widget.get_screen_space_center()
            transition = "in_scale"

        self._root_widget = ba.containerwidget(
            size=(self._width, self._height + top_extra),
            transition=transition,
            toolbar_visibility="menu_minimal",
            scale_origin_stack_offset=self._scale_origin,
            parent=_ba.get_special_widget("overlay_stack"),
            scale=(1.9 if uiscale is ba.UIScale.SMALL
                   else 1.5 if uiscale is ba.UIScale.MEDIUM
                   else 1.0),
            stack_offset=(0, -25) if uiscale is ba.UIScale.SMALL else (0, 0)
        )

        self._back_button = back_button = ba.buttonwidget(
                parent=self._root_widget,
                position=(53 + (100 if uiscale is ba.UIScale.SMALL else 0), self._height - 60),
                size=(60, 60),
                scale=0.8,
                label=ba.charstr(ba.SpecialChar.BACK),
                autoselect=True,
                button_type='backSmall',
                on_activate_call=self._back)

        ba.containerwidget(edit=self._root_widget, cancel_button=back_button)

        ba.textwidget(
            parent=self._root_widget,
            position=(-10, self._height - 50),
            size=(self._width, 25),
            text="Community Plugin Manager",
            color=ba.app.ui.title_color,
            scale=1.05,
            h_align="center",
            v_align="center",
            maxwidth=270,
        )

        self._loading_text = ba.textwidget(
            parent=self._root_widget,
            position=(-10, self._height - 150),
            size=(self._width, 25),
            text="Loading...",
            color=ba.app.ui.title_color,
            scale=0.7,
            h_align="center",
            v_align="center",
            maxwidth=270,
        )

        self._scrollwidget = ba.scrollwidget(parent=self._root_widget,
                                             size=(420, 340),
                                             position=(160, 40))
        self._columnwidget = ba.columnwidget(parent=self._scrollwidget,
                                             border=2,
                                             margin=0)

        # name = ba.textwidget(parent=self._columnwidget,
        #                      size=(410, 30),
        #                      selectable=True, always_highlight=True,
        #                      color=(1,1,1),
        #                      on_select_call=lambda: None,
        #                      text="ColorScheme",
        #                      on_activate_call=lambda: None,
        #                      h_align='left', v_align='center',
        #                      maxwidth=420)

        # v = (self._height - 75) if uiscale is ba.UIScale.SMALL else (self._height - 59)

        # h = 40
        # b_textcolor = (0.75, 0.7, 0.8)
        # b_color = (0.6, 0.53, 0.63)

        # s = 1.0 if uiscale is ba.UIScale.SMALL else 1.27 if uiscale is ba.UIScale.MEDIUM else 1.57
        # b_size = (90, 60 * s)
        # v -= 63 * s

        # self.reload_button = ba.buttonwidget(parent=self._root_widget,
        #                                      position=(h, v), size=b_size,
        #                                      on_activate_call=self._refresh,
        #                                      label="Reload List",
        #                                      button_type="square",
        #                                      color=b_color,
        #                                      textcolor=b_textcolor,
        #                                      autoselect=True, text_scale=0.7)
        # v -= 63 * s
        # self.info_button = ba.buttonwidget(parent=self._root_widget,
        #                                    position=(h, v), size=b_size,
        #                                    on_activate_call=self._get_info,
        #                                    label="Mod Info",
        #                                    button_type="square", color=b_color,
        #                                    textcolor=b_textcolor,
        #                                    autoselect=True, text_scale=0.7)
        # v -= 63 * s
        # self.sort_button = ba.buttonwidget(parent=self._root_widget,
        #                                    position=(h, v), size=b_size,
        #                                    on_activate_call=self._sort,
        #                                    label="Sort\nAlphabetical",
        #                                    button_type="square", color=b_color,
        #                                    textcolor=b_textcolor,
        #                                    text_scale=0.7, autoselect=True)
        # v -= 63 * s
        # self.settings_button = ba.buttonwidget(parent=self._root_widget,
        #                                        position=(h, v), size=b_size,
        #                                        on_activate_call=self._settings,
        #                                        label="Settings",
        #                                        button_type="square",
        #                                        color=b_color,
        #                                        textcolor=b_textcolor,
        #                                        autoselect=True, text_scale=0.7)
        # self.column_pos_y = self._height - 75 - self.tab_height
        # self._scroll_width = self._width - 180
        # self._scroll_height = self._height - 120 - self.tab_height
        # self._scrollwidget = ba.scrollwidget(parent=self._root_widget, size=(
        # self._scroll_width, self._scroll_height), position=(
        # 140, self.column_pos_y - self._scroll_height + 10))
        # self._columnwidget = ba.columnwidget(parent=self._scrollwidget,
        #                                      border=2, margin=0)
        # self._mod_selected = None
        # self._refresh()

    def _back(self) -> None:
        from bastd.ui.settings.allsettings import AllSettingsWindow
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            AllSettingsWindow(transition='in_left').get_root_widget())

    async def setup_plugin_categories(self, plugin_index):
        self.categories["All"] = None
        requests = []
        for plugin_category in plugin_index["plugin_categories"]:
            category = Category(
                plugin_category["display_name"],
                plugin_category["base_download_url"],
                plugin_category["meta"],
            )
            self.categories[plugin_category["display_name"]] = category
            request = category.get_plugins()
            requests.append(request)
        categories = await asyncio.gather(*requests)

        all_plugins = []
        for plugins in categories:
            all_plugins.extend(plugins)
        self.categories["All"] = CategoryAll(plugins=all_plugins)

    async def plugin_index(self):
        index = await super().get_index()
        await asyncio.gather(
            self.draw_settings_icon(),
            self.setup_plugin_categories(index),
        )
        self._loading_text.delete()
        await self.select_category("All")
        await self.draw_search_bar()

    async def draw_category_selection_button(self, label=None):
        # uiscale = ba.app.ui.uiscale
        # v = (self._height - 75) if uiscale is ba.UIScale.SMALL else (self._height - 105)
        v = 395
        h = 440
        # the next 2 lines belong in 1 line
        # # s = 1.0 if uiscale is ba.UIScale.SMALL else
        # # 1.27 if uiscale is ba.UIScale.MEDIUM else 1.57
        # s = 1.75
        # b_size = (90, 60 * s)
        b_size = (150, 30)
        b_textcolor = (0.75, 0.7, 0.8)
        b_color = (0.6, 0.53, 0.63)

        if label is None:
            label = self.selected_category
        label = f"Category: {label}"

        if self.category_selection_button is not None:
            self.category_selection_button.delete()

        # loop = asyncio.get_event_loop()
        self.category_selection_button = ba.buttonwidget(parent=self._root_widget,
                                                         position=(h, v),
                                                         size=b_size,
                                                         # on_activate_call=ba.Call(loop.create_
                                                         # task, self.show_categories()),
                                                         on_activate_call=self.show_categories,
                                                         label=label,
                                                         button_type="square",
                                                         color=b_color,
                                                         textcolor=b_textcolor,
                                                         autoselect=True,
                                                         text_scale=0.6)

    async def draw_search_bar(self):
        # TODO
        ba.textwidget(parent=self._root_widget,
                      position=(200, 395),
                      scale=0.7,
                      # selectable=True,
                      always_highlight=True,
                      color=(0.4, 0.4, 0.4),
                      # on_select_call=lambda: None,
                      text="<Implement plugin search>",
                      on_activate_call=lambda: None,
                      h_align='left',
                      v_align='center',
                      maxwidth=420)

    async def draw_settings_icon(self):
        controller_button = ba.buttonwidget(parent=self._root_widget,
                                            autoselect=True,
                                            position=(600, 70),
                                            size=(30, 30),
                                            button_type="square",
                                            label="",
                                            on_activate_call=lambda: None)
        ba.imagewidget(parent=self._root_widget,
                       position=(600, 70),
                       size=(30, 30),
                       color=(0.8, 0.95, 1),
                       texture=ba.gettexture("settingsIcon"),
                       draw_controller=controller_button)

    async def draw_plugin_names(self):
        # uiscale = ba.app.ui.uiscale
        # v = (self._height - 75) if uiscale is ba.UIScale.SMALL else (self._height - 105)
        # h = 440
        # next 2 lines belong in 1 line
        # # s = 1.0 if uiscale is ba.UIScale.SMALL else
        # # 1.27 if uiscale is ba.UIScale.MEDIUM else 1.57
        # s = 1.75
        # # b_size = (90, 60 * s)
        # b_size = (150, 30)
        # b_textcolor = (0.75, 0.7, 0.8)
        # b_color = (0.6, 0.53, 0.63)

        for plugin in self._columnwidget.get_children():
            plugin.delete()

        plugins = await self.categories[self.selected_category].get_plugins()
        for plugin in plugins:
            ba.textwidget(parent=self._columnwidget,
                          size=(410, 30),
                          selectable=True,
                          always_highlight=True,
                          color=(1, 1, 1),
                          on_select_call=lambda: None,
                          text=plugin.name,
                          on_activate_call=ba.Call(PluginWindow, plugin, self._root_widget),
                          h_align='left',
                          v_align='center',
                          maxwidth=420)

    def show_categories(self):
        uiscale = ba.app.ui.uiscale
        # On each new entry, change position to y -= 40.
        # value = bastd.ui.popup.PopupMenuWindow(
        bastd.ui.popup.PopupMenuWindow(
            # position=(200, 40),
            position=(200, 0),
            scale=(2.3 if uiscale is ba.UIScale.SMALL else
                   1.65 if uiscale is ba.UIScale.MEDIUM else 1.23),
            choices=self.categories.keys(),
            current_choice=self.selected_category,
            delegate=self)

    async def select_category(self, category):
        self.selected_category = category
        await self.draw_category_selection_button(label=category)
        await self.draw_plugin_names()

    def popup_menu_selected_choice(self, window, choice):
        loop = asyncio.get_event_loop()
        loop.create_task(self.select_category(choice))

    def popup_menu_closing(self, window):
        pass

    async def refresh(self):
        pass


class NewAllSettingsWindow(ba.Window):
    def __init__(self,
                 transition: str = "in_right",
                 origin_widget: ba.Widget = None):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        import threading

        # Preload some modules we use in a background thread so we won"t
        # have a visual hitch when the user taps them.
        threading.Thread(target=self._preload_modules).start()

        ba.set_analytics_screen("Settings Window")
        scale_origin: Optional[tuple[float, float]]
        if origin_widget is not None:
            self._transition_out = "out_scale"
            scale_origin = origin_widget.get_screen_space_center()
            transition = "in_scale"
        else:
            self._transition_out = "out_right"
            scale_origin = None
        uiscale = ba.app.ui.uiscale
        width = 900 if uiscale is ba.UIScale.SMALL else 670
        x_inset = 75 if uiscale is ba.UIScale.SMALL else 0
        height = 435
        self._r = "settingsWindow"
        top_extra = 20 if uiscale is ba.UIScale.SMALL else 0

        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(width, height + top_extra),
            transition=transition,
            toolbar_visibility="menu_minimal",
            scale_origin_stack_offset=scale_origin,
            scale=(1.75 if uiscale is ba.UIScale.SMALL else
                   1.35 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -8) if uiscale is ba.UIScale.SMALL else (0, 0)))

        if ba.app.ui.use_toolbars and uiscale is ba.UIScale.SMALL:
            self._back_button = None
            ba.containerwidget(edit=self._root_widget,
                               on_cancel_call=self._do_back)
        else:
            self._back_button = btn = ba.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(40 + x_inset, height - 55),
                size=(130, 60),
                scale=0.8,
                text_scale=1.2,
                label=ba.Lstr(resource="backText"),
                button_type="back",
                on_activate_call=self._do_back)
            ba.containerwidget(edit=self._root_widget, cancel_button=btn)

        ba.textwidget(parent=self._root_widget,
                      position=(0, height - 44),
                      size=(width, 25),
                      text=ba.Lstr(resource=self._r + ".titleText"),
                      color=ba.app.ui.title_color,
                      h_align="center",
                      v_align="center",
                      maxwidth=130)

        if self._back_button is not None:
            ba.buttonwidget(edit=self._back_button,
                            button_type="backSmall",
                            size=(60, 60),
                            label=ba.charstr(ba.SpecialChar.BACK))

        v = height - 80
        v -= 145

        basew = 200
        baseh = 160

        x_offs = x_inset + (105 if uiscale is ba.UIScale.SMALL else
                            72) - basew  # now unused
        x_offs2 = x_offs + basew - 7
        x_offs3 = x_offs + 2 * (basew - 7)
        x_offs4 = x_offs + 3 * (basew - 7)
        x_offs5 = x_offs2 + 0.5 * (basew - 7)
        x_offs6 = x_offs5 + (basew - 7)

        def _b_title(x: float, y: float, button: ba.Widget,
                     text: Union[str, ba.Lstr]) -> None:
            ba.textwidget(parent=self._root_widget,
                          text=text,
                          position=(x + basew * 0.47, y + baseh * 0.22),
                          maxwidth=basew * 0.7, size=(0, 0),
                          h_align="center",
                          v_align="center",
                          draw_controller=button,
                          color=(0.7, 0.9, 0.7, 1.0))

        ctb = self._controllers_button = ba.buttonwidget(parent=self._root_widget,
                                                         autoselect=True,
                                                         position=(x_offs2, v),
                                                         size=(basew, baseh),
                                                         button_type="square",
                                                         label="",
                                                         on_activate_call=self._do_controllers)
        if ba.app.ui.use_toolbars and self._back_button is None:
            bbtn = _ba.get_special_widget("back_button")
            ba.widget(edit=ctb, left_widget=bbtn)
        _b_title(x_offs2, v, ctb,
                 ba.Lstr(resource=self._r + ".controllersText"))
        imgw = imgh = 130
        ba.imagewidget(parent=self._root_widget,
                       position=(x_offs2 + basew * 0.49 - imgw * 0.5, v + 35),
                       size=(imgw, imgh),
                       texture=ba.gettexture("controllerIcon"),
                       draw_controller=ctb)

        gfxb = self._graphics_button = ba.buttonwidget(parent=self._root_widget,
                                                       autoselect=True,
                                                       position=(x_offs3, v),
                                                       size=(basew, baseh),
                                                       button_type="square",
                                                       label="",
                                                       on_activate_call=self._do_graphics)
        if ba.app.ui.use_toolbars:
            pbtn = _ba.get_special_widget("party_button")
            ba.widget(edit=gfxb, up_widget=pbtn, right_widget=pbtn)
        _b_title(x_offs3, v, gfxb, ba.Lstr(resource=self._r + ".graphicsText"))
        imgw = imgh = 110
        ba.imagewidget(parent=self._root_widget,
                       position=(x_offs3 + basew * 0.49 - imgw * 0.5, v + 42),
                       size=(imgw, imgh),
                       texture=ba.gettexture("graphicsIcon"),
                       draw_controller=gfxb)

        abtn = self._audio_button = ba.buttonwidget(parent=self._root_widget,
                                                    autoselect=True,
                                                    position=(x_offs4, v),
                                                    size=(basew, baseh),
                                                    button_type="square",
                                                    label="",
                                                    on_activate_call=self._do_audio)
        _b_title(x_offs4, v, abtn, ba.Lstr(resource=self._r + ".audioText"))
        imgw = imgh = 120
        ba.imagewidget(parent=self._root_widget,
                       position=(x_offs4 + basew * 0.49 - imgw * 0.5 + 5, v + 35),
                       size=(imgw, imgh),
                       color=(1, 1, 0), texture=ba.gettexture("audioIcon"),
                       draw_controller=abtn)
        v -= (baseh - 5)

        avb = self._advanced_button = ba.buttonwidget(parent=self._root_widget,
                                                      autoselect=True,
                                                      position=(x_offs5, v),
                                                      size=(basew, baseh),
                                                      button_type="square",
                                                      label="",
                                                      on_activate_call=self._do_advanced)
        _b_title(x_offs5, v, avb, ba.Lstr(resource=self._r + ".advancedText"))
        imgw = imgh = 120
        ba.imagewidget(parent=self._root_widget,
                       position=(x_offs5 + basew * 0.49 - imgw * 0.5 + 5,
                                 v + 35),
                       size=(imgw, imgh),
                       color=(0.8, 0.95, 1),
                       texture=ba.gettexture("advancedIcon"),
                       draw_controller=avb)

        mmb = self._modmgr_button = ba.buttonwidget(parent=self._root_widget,
                                                    autoselect=True,
                                                    position=(x_offs6, v),
                                                    size=(basew, baseh),
                                                    button_type="square",
                                                    label="",
                                                    on_activate_call=self._do_modmanager)
        _b_title(x_offs6, v, avb, ba.Lstr(value="Plugin Manager"))
        imgw = imgh = 120
        ba.imagewidget(parent=self._root_widget,
                       position=(x_offs6 + basew * 0.49 - imgw * 0.5 + 5,
                                 v + 35),
                       size=(imgw, imgh),
                       color=(0.8, 0.95, 1),
                       texture=ba.gettexture("heart"),
                       draw_controller=mmb)

        self._restore_state()

    # noinspection PyUnresolvedReferences
    @staticmethod
    def _preload_modules() -> None:
        """Preload modules we use (called in bg thread)."""
        # import bastd.ui.mainmenu as _unused1
        # import bastd.ui.settings.controls as _unused2
        # import bastd.ui.settings.graphics as _unused3
        # import bastd.ui.settings.audio as _unused4
        # import bastd.ui.settings.advanced as _unused5

    def _do_back(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.mainmenu import MainMenuWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            MainMenuWindow(transition="in_left").get_root_widget())

    def _do_controllers(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.controls import ControlsSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition="out_left")
        ba.app.ui.set_main_menu_window(ControlsSettingsWindow(
            origin_widget=self._controllers_button).get_root_widget())

    def _do_graphics(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.graphics import GraphicsSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition="out_left")
        ba.app.ui.set_main_menu_window(GraphicsSettingsWindow(
            origin_widget=self._graphics_button).get_root_widget())

    def _do_audio(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.audio import AudioSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition="out_left")
        ba.app.ui.set_main_menu_window(AudioSettingsWindow(
            origin_widget=self._audio_button).get_root_widget())

    def _do_advanced(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.advanced import AdvancedSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition="out_left")
        ba.app.ui.set_main_menu_window(AdvancedSettingsWindow(
            origin_widget=self._advanced_button).get_root_widget())

    def _do_modmanager(self) -> None:
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition="out_left")
        ba.app.ui.set_main_menu_window(PluginManagerWindow(
            origin_widget=self._advanced_button).get_root_widget())

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._controllers_button:
                sel_name = "Controllers"
            elif sel == self._graphics_button:
                sel_name = "Graphics"
            elif sel == self._audio_button:
                sel_name = "Audio"
            elif sel == self._advanced_button:
                sel_name = "Advanced"
            elif sel == self._modmgr_button:
                sel_name = "Mod Manager"
            elif sel == self._back_button:
                sel_name = "Back"
            else:
                raise ValueError(f"unrecognized selection \"{sel}\"")
            ba.app.ui.window_states[type(self)] = {"sel_name": sel_name}
        except Exception:
            ba.print_exception(f"Error saving state for {self}.")

    def _restore_state(self) -> None:
        try:
            sel_name = ba.app.ui.window_states.get(type(self),
                                                   {}).get("sel_name")
            sel: Optional[ba.Widget]
            if sel_name == "Controllers":
                sel = self._controllers_button
            elif sel_name == "Graphics":
                sel = self._graphics_button
            elif sel_name == "Audio":
                sel = self._audio_button
            elif sel_name == "Advanced":
                sel = self._advanced_button
            elif sel_name == "Mod Manager":
                sel = self._modmgr_button
            elif sel_name == "Back":
                sel = self._back_button
            else:
                sel = self._controllers_button
            if sel is not None:
                ba.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            ba.print_exception(f"Error restoring state for {self}.")


# ba_meta export plugin
class EntryPoint(ba.Plugin):
    def on_app_running(self) -> None:
        """Called when the app is being launched."""
        from bastd.ui.settings import allsettings
        allsettings.AllSettingsWindow = NewAllSettingsWindow
        asyncio.set_event_loop(ba._asyncio._asyncio_event_loop)
        # loop = asyncio.get_event_loop()
        # loop.create_task(do())
        # pm = PluginManager()
        # pm.plugin_index()

    def on_app_pause(self) -> None:
        """Called after pausing game activity."""
        print("pause")

    def on_app_resume(self) -> None:
        """Called after the game continues."""
        print("resume")

    def on_app_shutdown(self) -> None:
        """Called before closing the application."""
        print("shutdown")
