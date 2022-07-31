# This plugin for Bombsquad allows players to create any custom RGB
# colorscheme to override the game's default colorscheme.
# Inspired by Smoothy's pink and dark colorscheme plugins!

# Enable the plugin and enter "colorscheme" without quotes in
# Settings -> Advanced -> Enter Code
# to bring up the colorscheme UI.

# ba_meta require api 7
import _ba
import ba

from bastd.ui.colorpicker import ColorPicker

original_buttonwidget = ba.buttonwidget
original_containerwidget = ba.containerwidget
original_checkboxwidget = ba.checkboxwidget

original_add_transaction = _ba.add_transaction
# We set this later so we store the overridden method in case the
# player is using pro-unlocker plugins that override the
# `ba.app.accounts.have_pro` method.
original_have_pro = None


class ColorScheme:
    """
    Apply a colorscheme to the game. Can also be invoked directly
    through the BombSquad's in-game console. See examples for more
    details.

    Parameters
    ----------
    color: `tuple`
        A tuple consisting of (R,G,B) channel values where each channel
        is a float ranging between 0 to 1.

    highlight: `tuple`
        A tuple consisting of (R,G,B) channel values where each channel
        is a float ranging between 0 to 1.

    Examples
    --------
    + Apply dark colorscheme:

        >>> import _ba
        >>> dark = _ba.ColorScheme((0.2,0.2,0.2), (0.8,0.8,0.8))
        >>> dark.apply()
        # Reset back to game's default colorscheme
        >>> dark.disable()

    + Colorscheme that modifies only the main colors:

        >>> import _ba
        >>> bluey = _ba.ColorScheme(color=(0.1,0.3,0.6))
        >>> bluey.apply()
        # Reset back to game's default colorscheme
        >>> bluey.disable()

    + Colorscheme that modifies only the highlight colors:

        >>> import _ba
        >>> reddish = _ba.ColorScheme(highlight=(0.8,0.35,0.35))
        >>> reddish.apply()
        # Reset back to game's default colorscheme
        >>> reddish.disable()

    + Revert back to game's default colorscheme irrespective of
      whatever colorscheme is active at the moment:

        >>> import _ba
        >>> _ba.ColorScheme.disable()
    """

    def __init__(self, color=None, highlight=None):
        self.color = color
        self.highlight = highlight

    def _custom_buttonwidget(self, *args, **kwargs):
        assert self.highlight is not None
        kwargs["color"] = self.highlight
        return original_buttonwidget(*args, **kwargs)

    def _custom_containerwidget(self, *args, **kwargs):
        assert self.color is not None
        kwargs["color"] = self.color
        return original_containerwidget(*args, **kwargs)

    def _custom_checkboxwidget(self, *args, **kwargs):
        assert self.highlight is not None
        kwargs["color"] = self.highlight
        return original_checkboxwidget(*args, **kwargs)

    def _apply_color(self):
        if self.color is None:
            raise TypeError("Expected color to be an (R,G,B) tuple.")
        ba.containerwidget = self._custom_containerwidget

    def _apply_highlight(self):
        if self.highlight is None:
            raise TypeError("Expected highlight to be an (R,G,B) tuple.")
        ba.buttonwidget = self._custom_buttonwidget
        ba.checkboxwidget = self._custom_checkboxwidget

    def apply(self):
        if self.color:
            self._apply_color()
        if self.highlight:
            self._apply_highlight()

    @staticmethod
    def _disable_color():
        ba.buttonwidget = original_buttonwidget
        ba.checkboxwidget = original_checkboxwidget

    @staticmethod
    def _disable_highlight():
        ba.containerwidget = original_containerwidget

    @classmethod
    def disable(cls):
        cls._disable_color()
        cls._disable_highlight()


class ColorSchemeWindow(ba.Window):
    def __init__(self, default_colors=((0.41, 0.39, 0.5), (0.5, 0.7, 0.25))):
        self._default_colors = default_colors
        self._color, self._highlight = ba.app.config.get("ColorScheme", (None, None))

        self._last_color = self._color
        self._last_highlight = self._highlight

        # Let's set the game's default colorscheme before opening the Window.
        # Otherwise the colors in the Window are tinted as per the already
        # applied custom colorscheme thereby making it impossible to visually
        # differentiate between different colors.
        ColorScheme.disable()

        # A hack to let players select any RGB color value through the UI,
        # otherwise this is limited only to pro accounts.
        ba.app.accounts_v1.have_pro = lambda: True

        self.draw_ui()

    def draw_ui(self):
        # Most of the stuff here for drawing the UI is referred from the
        # game's bastd/ui/profile/edit.py, and so there could be some
        # cruft here due to my oversight.
        uiscale = ba.app.ui.uiscale
        self._width = width = 480.0 if uiscale is ba.UIScale.SMALL else 380.0
        self._x_inset = x_inset = 40.0 if uiscale is ba.UIScale.SMALL else 0.0
        self._height = height = (
            275.0
            if uiscale is ba.UIScale.SMALL
            else 288.0
            if uiscale is ba.UIScale.MEDIUM
            else 300.0
        )
        spacing = 40
        self._base_scale = (
            2.05
            if uiscale is ba.UIScale.SMALL
            else 1.5
            if uiscale is ba.UIScale.MEDIUM
            else 1.0
        )
        top_extra = 15 if uiscale is ba.UIScale.SMALL else 15

        super().__init__(
            root_widget=ba.containerwidget(
                size=(width, height + top_extra),
                transition="in_right",
                scale=self._base_scale,
                stack_offset=(0, 15) if uiscale is ba.UIScale.SMALL else (0, 0),
            )
        )

        cancel_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(52 + x_inset, height - 60),
            size=(155, 60),
            scale=0.8,
            autoselect=True,
            label=ba.Lstr(resource="cancelText"),
            on_activate_call=self._cancel,
        )
        ba.containerwidget(edit=self._root_widget, cancel_button=cancel_button)

        save_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(width - (177 + x_inset), height - 110),
            size=(155, 60),
            autoselect=True,
            scale=0.8,
            label=ba.Lstr(resource="saveText"),
        )
        ba.widget(edit=save_button, left_widget=cancel_button)
        ba.buttonwidget(edit=save_button, on_activate_call=self.save)
        ba.widget(edit=cancel_button, right_widget=save_button)
        ba.containerwidget(edit=self._root_widget, start_button=save_button)

        reset_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(width - (177 + x_inset), height - 60),
            size=(155, 60),
            color=(0.2, 0.5, 0.6),
            autoselect=True,
            scale=0.8,
            label=ba.Lstr(resource="settingsWindowAdvanced.resetText"),
        )
        ba.widget(edit=reset_button, left_widget=reset_button)
        ba.buttonwidget(edit=reset_button, on_activate_call=self.reset)
        ba.widget(edit=cancel_button, right_widget=reset_button)
        ba.containerwidget(edit=self._root_widget, start_button=reset_button)

        v = height - 65.0
        v -= spacing * 3.0
        b_size = 80
        b_offs = 75

        self._color_button = ba.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(self._width * 0.5 - b_offs - b_size * 0.5, v - 50),
            size=(b_size, b_size),
            color=self._last_color or self._default_colors[0],
            label="",
            button_type="square",
        )
        ba.buttonwidget(
            edit=self._color_button, on_activate_call=ba.Call(self._pick_color, "color")
        )
        ba.textwidget(
            parent=self._root_widget,
            h_align="center",
            v_align="center",
            position=(self._width * 0.5 - b_offs, v - 65),
            size=(0, 0),
            draw_controller=self._color_button,
            text=ba.Lstr(resource="editProfileWindow.colorText"),
            scale=0.7,
            color=ba.app.ui.title_color,
            maxwidth=120,
        )

        self._highlight_button = ba.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(self._width * 0.5 + b_offs - b_size * 0.5, v - 50),
            size=(b_size, b_size),
            color=self._last_highlight or self._default_colors[1],
            label="",
            button_type="square",
        )

        ba.buttonwidget(
            edit=self._highlight_button,
            on_activate_call=ba.Call(self._pick_color, "highlight"),
        )
        ba.textwidget(
            parent=self._root_widget,
            h_align="center",
            v_align="center",
            position=(self._width * 0.5 + b_offs, v - 65),
            size=(0, 0),
            draw_controller=self._highlight_button,
            text=ba.Lstr(resource="editProfileWindow.highlightText"),
            scale=0.7,
            color=ba.app.ui.title_color,
            maxwidth=120,
        )

    def _pick_color(self, tag):
        if tag == "color":
            initial_color = self._color or self._default_colors[0]
        elif tag == "highlight":
            initial_color = self._highlight or self._default_colors[1]
        else:
            raise ValueError("Unexpected color picker tag: {}".format(tag))
        ColorPicker(
            parent=None,
            position=(0, 0),
            initial_color=initial_color,
            delegate=self,
            tag=tag,
        )

    def _cancel(self):
        if self._last_color and self._last_highlight:
            colorscheme = ColorScheme(self._last_color, self._last_highlight)
            colorscheme.apply()
        # Good idea to revert this back now so we do not break anything else.
        ba.app.accounts_v1.have_pro = original_have_pro
        ba.containerwidget(edit=self._root_widget, transition="out_right")

    def reset(self, transition_out=True):
        if transition_out:
            ba.playsound(ba.getsound("gunCocking"))
        ba.app.config["ColorScheme"] = (None, None)
        # Good idea to revert this back now so we do not break anything else.
        ba.app.accounts_v1.have_pro = original_have_pro
        ba.app.config.commit()
        ba.containerwidget(edit=self._root_widget, transition="out_right")

    def save(self, transition_out=True):
        if transition_out:
            ba.playsound(ba.getsound("gunCocking"))
        colorscheme = ColorScheme(
            self._color or self._default_colors[0],
            self._highlight or self._default_colors[1],
        )
        colorscheme.apply()
        # Good idea to revert this back now so we do not break anything else.
        ba.app.accounts_v1.have_pro = original_have_pro
        ba.app.config["ColorScheme"] = (
            self._color or self._default_colors[0],
            self._highlight or self._default_colors[1],
        )
        ba.app.config.commit()
        ba.containerwidget(edit=self._root_widget, transition="out_right")

    def _set_color(self, color):
        self._color = color
        if self._color_button:
            ba.buttonwidget(edit=self._color_button, color=color)

    def _set_highlight(self, color):
        self._highlight = color
        if self._highlight_button:
            ba.buttonwidget(edit=self._highlight_button, color=color)

    def color_picker_selected_color(self, picker, color):
        # The `ColorPicker` calls this method in the delegate once a color
        # is selected from the `ColorPicker` Window.
        if not self._root_widget:
            return
        tag = picker.get_tag()
        if tag == "color":
            self._set_color(color)
        elif tag == "highlight":
            self._set_highlight(color)
        else:
            raise ValueError("Unexpected color picker tag: {}".format(tag))

    def color_picker_closing(self, picker):
        # The `ColorPicker` expects this method to exist in the delegate,
        # so here it is!
        pass


class CustomTransactions:
    def __init__(self):
        self.custom_transactions = {}

    def _handle(self, transaction, *args, **kwargs):
        transaction_code = transaction.get("code")
        transaction_fn = self.custom_transactions.get(transaction_code)
        if transaction_fn is not None:
            return transaction_fn(transaction, *args, **kwargs)
        return original_add_transaction(transaction, *args, **kwargs)

    def add(self, transaction_code, transaction_fn):
        self.custom_transactions[transaction_code] = transaction_fn

    def enable(self):
        _ba.add_transaction = self._handle


def colorscheme_transaction(transaction, *args, **kwargs):
    # We store whether the player is a pro account or not since we
    # temporarily attempt to bypass the limitation where only pro
    # accounts can set custom RGB color values, and we restore this
    # value back later on.

    # Also, we attempt to store this value here (and not in the
    # beginning) since the player might be using other dedicated
    # pro-unlocker plugins which may attempt to override the game
    # method early on in the beginning, therefore, leading us to a
    # race-condition and we may not correctly store whether the player
    # has pro-unlocked or not if our plugin runs before the dedicated
    # pro-unlocker plugin has been applied.
    global original_have_pro
    original_have_pro = ba.app.accounts_v1.have_pro

    ColorSchemeWindow()


def load_colorscheme():
    color, highlight = ba.app.config.get("ColorScheme", (None, None))
    if color and highlight:
        colorscheme = ColorScheme(color, highlight)
        colorscheme.apply()


def load_plugin():
    # Allow access to changing colorschemes manually through the in-game
    # console.
    _ba.ColorScheme = ColorScheme
    # Adds a new advanced code entry named "colorscheme" which can be
    # entered through Settings -> Advanced -> Enter Code, allowing
    # colorscheme modification through a friendly UI.
    custom_transactions = CustomTransactions()
    custom_transactions.add("colorscheme", colorscheme_transaction)
    custom_transactions.enable()
    # Load any previously saved colorscheme.
    load_colorscheme()


# ba_meta export plugin
class Main(ba.Plugin):
    def __init__(self):
        if _ba.env().get("build_number", 0) >= 20258:
            load_plugin()
        else:
            print("ColorScheme.py only runs with BombSquad versions 1.7.0 or higher.")
