# ba_meta require api 9

import babase
import bauiv1 as bui
import bauiv1lib.party
import bascenev1 as bs
import json
import os

CONFIGS_DIR = os.path.join('.', 'Configs')
if not os.path.exists(CONFIGS_DIR):
    os.makedirs(CONFIGS_DIR)

MSG_PATH = os.path.join(CONFIGS_DIR, 'quick_chat_msgs.json')
DEFAULT_MESSAGES = ['Hi!', 'Let\'s go!', 'GG!', 'Oops!', 'Good luck!', 'Well played!']


def load_messages():
    if not os.path.exists(MSG_PATH):
        save_messages(DEFAULT_MESSAGES)  # <--- creates JSON file with default msgs
        return DEFAULT_MESSAGES
    try:
        with open(MSG_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return DEFAULT_MESSAGES


def save_messages(msgs):
    with open(MSG_PATH, 'w') as f:
        json.dump(msgs, f)


class QuickChatPartyWindow(bauiv1lib.party.PartyWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._quick_chat_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width - 180, self._height - 50),
            size=(150, 60),
            scale=0.7,
            label='Quick Chat',
            button_type='square',
            color=(0, 0, 0),
            textcolor=(1, 1, 1),
            on_activate_call=self._open_quick_chat_menu
        )

    def _open_quick_chat_menu(self):
        messages = load_messages()
        w, h = 400, 300

        root = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'), size=(w, h), transition='in_scale', scale=1.2, color=(
            0, 0, 0), on_outside_click_call=lambda: bui.containerwidget(edit=root, transition='out_scale'))

        self._msg_scroll = bui.scrollwidget(
            parent=root, position=(20, 80), size=(360, 180), color=(0, 0, 0))
        self._msg_col = bui.columnwidget(parent=self._msg_scroll, border=2, margin=0)

        for msg in messages:
            bui.buttonwidget(
                parent=self._msg_col,
                size=(350, 40),
                label=msg,
                textcolor=(1, 1, 1),
                color=(0.4, 0.7, 1),
                on_activate_call=lambda m=msg: self._send_and_close(m, root)
            )

        bui.buttonwidget(
            parent=root,
            position=(20, 20),
            size=(110, 45),
            label='Add',
            color=(0.4, 0.7, 1),
            textcolor=(1, 1, 1),
            on_activate_call=lambda: self._add_message(root)
        )

        bui.buttonwidget(
            parent=root,
            position=(140, 20),
            size=(110, 45),
            label='Remove',
            color=(0.4, 0.7, 1),
            textcolor=(1, 1, 1),
            on_activate_call=lambda: self._remove_message(root)
        )

        bui.buttonwidget(
            parent=root,
            position=(260, 20),
            size=(110, 45),
            label='Close',
            color=(0.4, 0.7, 1),
            textcolor=(1, 1, 1),
            on_activate_call=lambda: bui.containerwidget(edit=root, transition='out_scale')
        )

    def _send_and_close(self, message: str, root_widget):
        bs.chatmessage(message)
        bui.containerwidget(edit=root_widget, transition='out_scale')

    def _add_message(self, parent):
        def save_new():
            new_msg = bui.textwidget(query=txt).strip()
            if new_msg:
                msgs = load_messages()
                msgs.append(new_msg)
                save_messages(msgs)
                bui.screenmessage(f'Added: "{new_msg}"', color=(0, 1, 0))
            bui.containerwidget(edit=win, transition='out_scale')
            bui.containerwidget(edit=parent, transition='out_scale')
            self._open_quick_chat_menu()

        win = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'), size=(300, 140), transition='in_scale',
                                  scale=1.2, color=(0, 0, 0), on_outside_click_call=lambda: bui.containerwidget(edit=win, transition='out_scale'))

        bui.textwidget(parent=win, position=(20, 90), size=(260, 30),
                       text='New Message:', scale=0.9, h_align='left', v_align='center', color=(1, 1, 1))

        txt = bui.textwidget(parent=win, position=(20, 60), size=(260, 30),
                             text='', editable=True, maxwidth=200)

        bui.buttonwidget(parent=win, position=(60, 20), size=(80, 30),
                         label='OK', color=(0.4, 0.7, 1), textcolor=(1, 1, 1), on_activate_call=save_new)

        bui.buttonwidget(parent=win, position=(160, 20), size=(80, 30),
                         label='Cancel', color=(0.4, 0.7, 1), textcolor=(1, 1, 1),
                         on_activate_call=lambda: bui.containerwidget(edit=win, transition='out_scale'))

    def _remove_message(self, parent):
        msgs = load_messages()

        if not msgs:
            bui.screenmessage("No messages to remove.", color=(1, 0, 0))
            return

        h = 50 + len(msgs) * 45
        h = min(h, 300)
        win = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'), size=(300, h), transition='in_scale', scale=1.2, color=(
            0, 0, 0), on_outside_click_call=lambda: bui.containerwidget(edit=win, transition='out_scale'))
        col = bui.columnwidget(parent=win)

        bui.buttonwidget(
            parent=col,
            label=f'Colse',
            size=(260, 40),
            textcolor=(1, 1, 1),
            color=(1, 0.2, 0.2),
            on_activate_call=lambda: bui.containerwidget(edit=win, transition='out_scale')
        )
        for msg in msgs:
            bui.buttonwidget(
                parent=col,
                label=f'Delete: {msg}',
                size=(260, 40),
                textcolor=(1, 1, 1),
                color=(0.4, 0.7, 1),
                on_activate_call=lambda m=msg: self._confirm_delete(m, win, parent)
            )

    def _confirm_delete(self, msg, win, parent):
        msgs = load_messages()
        if msg in msgs:
            msgs.remove(msg)
            save_messages(msgs)
            bui.screenmessage(f'Removed: "{msg}"', color=(1, 0.5, 0))
        bui.containerwidget(edit=win, transition='out_scale')
        bui.containerwidget(edit=parent, transition='out_scale')
        self._open_quick_chat_menu()


# ba_meta export babase.Plugin
class ByANES(babase.Plugin):
    def on_app_running(self):
        bauiv1lib.party.PartyWindow = QuickChatPartyWindow
