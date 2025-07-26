import babase
import bauiv1 as bui
import bauiv1lib.party
from babase._mgen.enums import SpecialChar

ICONS = [babase.charstr(i) for i in SpecialChar]


class MPW(bauiv1lib.party.PartyWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bui.buttonwidget(
            parent=self._root_widget,
            size=(50, 35),
            label='',
            button_type='square',
            position=(self._width - 70, -5),
            icon=bui.gettexture('logo'),
            on_activate_call=self._on_button_press
        )

    def _on_button_press(self):
        self._win = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            size=(150, 300),
            color=(0.5, 0.5, 0.5),
            transition='in_scale',
            scale=1.0,
            on_outside_click_call=self._close
        )

        self._scroll = bui.scrollwidget(
            parent=self._win,
            size=(110, 270),
            position=(20, 15),
        )
        self._column = bui.columnwidget(
            parent=self._scroll,
            size=(110, 270),
        )
        for ICON in ICONS:
            bui.textwidget(
                parent=self._column,
                size=(110, 50),
                text=ICON,
                color=(0.8, 0.8, 0.8),
                click_activate=True,
                always_highlight=True,
                h_align='left',
                v_align='center',
                maxwidth=110,
                selectable=True,
                on_activate_call=lambda icon=ICON: self._add(icon)
            )

    def _add(self, icon):
        oldtext = sendtext = bui.textwidget(query=self._text_field)
        bui.textwidget(edit=self._text_field, text=f'{oldtext} {icon}')

    def _close(self):
        bui.containerwidget(edit=self._win, transition='out_scale')

# ba_meta require api 9
# ba_meta export babase.Plugin


class byYelllow(babase.Plugin):
    def __init__(self):
        bauiv1lib.party.PartyWindow = MPW
