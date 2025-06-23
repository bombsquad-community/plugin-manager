# ba_meta require api 9

###################
# Credits - Droopy#3730. #
###################

# Don't edit  .


from __future__ import annotations
import _babase
import babase
import bauiv1 as bui
from bauiv1lib.ingamemenu import InGameMenuWindow


class Manual_camera_window(bui.MainWindow):
    def __init__(self, origin_widget):
        super().__init__(
            root_widget=bui.containerwidget(
                on_outside_click_call=None,
                size=(0, 0)
            ),
            transition='in_scale',
            origin_widget=origin_widget,
        )
        button_size = (50, 50)
        self._text = bui.textwidget(parent=self._root_widget,
                                    scale=0.65,
                                    color=(0.75, 0.75, 0.75),
                                    text='Cam Position',
                                    size=(0, 0),
                                    position=(500, 185),
                                    h_align='center',
                                    v_align='center')
        self._xminus = bui.buttonwidget(parent=self._root_widget,
                                        size=button_size,
                                        label=babase.charstr(babase.SpecialChar.LEFT_ARROW),
                                        repeat=True,
                                        button_type='square',
                                        autoselect=True,
                                        position=(429, 60),
                                        on_activate_call=babase.Call(self._change_camera_position, 'x-'))
        self._xplus = bui.buttonwidget(parent=self._root_widget,
                                       size=button_size,
                                       label=babase.charstr(babase.SpecialChar.RIGHT_ARROW),
                                       repeat=True,
                                       button_type='square',
                                       autoselect=True,
                                       position=(538, 60),
                                       on_activate_call=babase.Call(self._change_camera_position, 'x'))
        self._yplus = bui.buttonwidget(parent=self._root_widget,
                                       size=button_size,
                                       label=babase.charstr(babase.SpecialChar.UP_ARROW),
                                       repeat=True,
                                       button_type='square',
                                       autoselect=True,
                                       position=(482, 120),
                                       on_activate_call=babase.Call(self._change_camera_position, 'y'))
        self._yminus = bui.buttonwidget(parent=self._root_widget,
                                        size=button_size,
                                        label=babase.charstr(babase.SpecialChar.DOWN_ARROW),
                                        repeat=True,
                                        button_type='square',
                                        autoselect=True,
                                        position=(482, 2),
                                        on_activate_call=babase.Call(self._change_camera_position, 'y-'))
        self.inwards = bui.buttonwidget(parent=self._root_widget,
                                        size=(100, 30),
                                        label='Zoom +',
                                        repeat=True,
                                        button_type='square',
                                        autoselect=True,
                                        position=(-550, -60),
                                        on_activate_call=babase.Call(self._change_camera_position, 'z-'))
        self._outwards = bui.buttonwidget(parent=self._root_widget,
                                          size=(100, 30),
                                          label='Zoom -',
                                          repeat=True,
                                          button_type='square',
                                          autoselect=True,
                                          position=(-550, -100),
                                          on_activate_call=babase.Call(self._change_camera_position, 'z'))
        self.target_text = bui.textwidget(parent=self._root_widget,
                                          scale=0.65,
                                          color=(0.75, 0.75, 0.75),
                                          text='Cam Angle',
                                          size=(0, 0),
                                          position=(-462, 185),
                                          h_align='center',
                                          v_align='center')
        self.target_xminus = bui.buttonwidget(parent=self._root_widget,
                                              size=button_size,
                                              label=babase.charstr(babase.SpecialChar.LEFT_ARROW),
                                              repeat=True,
                                              button_type='square',
                                              autoselect=True,
                                              position=(-538, 60),
                                              on_activate_call=babase.Call(self._change_camera_target, 'x-'))
        self.target_xplus = bui.buttonwidget(parent=self._root_widget,
                                             size=button_size,
                                             label=babase.charstr(babase.SpecialChar.RIGHT_ARROW),
                                             repeat=True,
                                             button_type='square',
                                             autoselect=True,
                                             position=(-429, 60),
                                             on_activate_call=babase.Call(self._change_camera_target, 'x'))
        self.target_yplus = bui.buttonwidget(parent=self._root_widget,
                                             size=button_size,
                                             label=babase.charstr(babase.SpecialChar.UP_ARROW),
                                             repeat=True,
                                             button_type='square',
                                             autoselect=True,
                                             position=(-482, 120),
                                             on_activate_call=babase.Call(self._change_camera_target, 'y'))
        self.target_yminus = bui.buttonwidget(parent=self._root_widget,
                                              size=button_size,
                                              label=babase.charstr(babase.SpecialChar.DOWN_ARROW),
                                              repeat=True,
                                              button_type='square',
                                              autoselect=True,
                                              position=(-482, 2),
                                              on_activate_call=babase.Call(self._change_camera_target, 'y-'))
        self._step_text = bui.textwidget(parent=self._root_widget,
                                         scale=0.85,
                                         color=(1, 1, 1),
                                         text='Step:',
                                         size=(0, 0),
                                         position=(450, -38),
                                         h_align='center',
                                         v_align='center')
        self._text_field = bui.textwidget(
            parent=self._root_widget,
            editable=True,
            size=(100, 40),
            position=(480, -55),
            text='',
            maxwidth=120,
            flatness=1.0,
            autoselect=True,
            v_align='center',
            corner_scale=0.7)
        self._reset = bui.buttonwidget(parent=self._root_widget,
                                       size=(50, 30),
                                       label='Reset',
                                       button_type='square',
                                       autoselect=True,
                                       position=(450, -100),
                                       on_activate_call=babase.Call(self._change_camera_position, 'reset'))
        self._done = bui.buttonwidget(parent=self._root_widget,
                                      size=(50, 30),
                                      label='Done',
                                      button_type='square',
                                      autoselect=True,
                                      position=(520, -100),
                                      on_activate_call=self.main_window_back)
        bui.containerwidget(edit=self._root_widget,
                            cancel_button=self._done)

    def _change_camera_position(self, direction):
        camera = _babase.get_camera_position()
        x = camera[0]
        y = camera[1]
        z = camera[2]

        try:
            increment = float(bui.textwidget(query=self._text_field))
        except:
            increment = 1

        if direction == 'x':
            x += increment
        elif direction == 'x-':
            x -= increment
        elif direction == 'y':
            y += increment
        elif direction == 'y-':
            y -= increment
        elif direction == 'z':
            z += increment
        elif direction == 'z-':
            z -= increment
        elif direction == 'reset':
            _babase.set_camera_manual(False)
            return

        _babase.set_camera_manual(True)
        _babase.set_camera_position(x, y, z)

    def _change_camera_target(self, direction):
        camera = _babase.get_camera_target()
        x = camera[0]
        y = camera[1]
        z = camera[2]

        try:
            increment = float(bui.textwidget(query=self._text_field))
        except:
            increment = 1

        if direction == 'x':
            x += increment
        elif direction == 'x-':
            x -= increment
        elif direction == 'y':
            y += increment
        elif direction == 'y-':
            y -= increment

        _babase.set_camera_manual(True)
        _babase.set_camera_target(x, y, z)


old_refresh_in_game = InGameMenuWindow._refresh_in_game


def my_refresh_in_game(self, *args, **kwargs):
    value = old_refresh_in_game.__get__(self)(*args, **kwargs)
    camera_button = bui.buttonwidget(
        parent=self._root_widget,
        autoselect=True,
        position=(-65, 100),
        size=(70, 50),
        button_type='square',
        label='Manual\nCamera',
        text_scale=1.5)

    bui.buttonwidget(edit=camera_button,
                     on_activate_call=bui.Call(self._manual_camera, camera_button))
    return value


def _manual_camera(self, widget):
    if not self.main_window_has_control():
        return

    self.main_window_replace(Manual_camera_window(origin_widget=widget))

# ba_meta export babase.Plugin


class ByDroopy(babase.Plugin):
    def __init__(self):
        InGameMenuWindow._refresh_in_game = my_refresh_in_game
        InGameMenuWindow._manual_camera = _manual_camera
