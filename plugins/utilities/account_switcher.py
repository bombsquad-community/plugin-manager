"""                             Plugin by LoupGarou a.k.a Loup/Soup   
                                 Discord → loupgarou_
Switch between multiple accounts in easily

Feel free to let me know if you use this plugin,i love to hear that :)

Message me in discord if you find some bug
Use this code for your experiments or plugin but please dont rename this plugin and distribute with your name
"""

# ba_meta require api 9

from __future__ import annotations
import babase
import bauiv1 as bui
from bauiv1lib.confirm import ConfirmWindow
from bauiv1lib.account.settings import AccountSettingsWindow
from os import listdir, path, mkdir, remove
from shutil import copy, rmtree
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional

UI_SCALE = 2.0 if (babase.app.ui_v1.uiscale == babase.UIScale.SMALL) else 1.0

ACCOUNT_FILES = ['.bsac2', '.bsuuid', 'config.json', '.config_prev.json']
plus = babase.app.plus
env = babase.app.env
USER_DIR = path.dirname(env.config_file_path)
ACCOUNTS_DIR = path.join(USER_DIR, 'account_switcher_profiles')

if not path.exists(ACCOUNTS_DIR):
    mkdir(ACCOUNTS_DIR)


def print_msg(text: str, color=(0.3, 1, 0.3)):
    bui.screenmessage(text, color=color)


class AccountSwitcherUI(bui.Window):
    def __init__(self):
        # Base dimensions; the final size is controlled by the scale property.
        self._width = 600
        self._height = 400

        self._root_widget = bui.containerwidget(
            size=(self._width, self._height),
            scale=UI_SCALE,  # Apply the global scale here
            transition='in_right',
            stack_offset=(0, 0)
        )

        # Standard back/close button
        self._back_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(40, self._height - 60),
            size=(40, 40),
            scale=1.0,
            label=babase.charstr(babase.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self._close,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=self._back_button)

        # Title
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 40),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text='Account Switcher',
            scale=1.5,
            color=(0.8, 0.8, 0.9),
        )

        content_height = self._height - 80
        content_y = 20

        # Buttons stacked on the right
        btn_col_width = 180
        btn_col_x = self._width - btn_col_width - 20
        btn_width = 160
        btn_height = 60
        btn_x = btn_col_x + (btn_col_width - btn_width) * 0.5
        v_pos = content_y + content_height - btn_height
        v_step = btn_height + 10

        bui.buttonwidget(
            parent=self._root_widget,
            position=(btn_x, v_pos),
            size=(btn_width, btn_height),
            label='Save Current',
            on_activate_call=self.save_current_account,
        )
        v_pos -= v_step

        bui.buttonwidget(
            parent=self._root_widget,
            position=(btn_x, v_pos),
            size=(btn_width, btn_height),
            label='Add New Account',
            on_activate_call=self.add_new_account,
        )
        v_pos -= v_step

        bui.buttonwidget(
            parent=self._root_widget,
            position=(btn_x, v_pos),
            size=(btn_width, btn_height),
            label='Load Selected',
            on_activate_call=self.load_selected_account,
        )
        v_pos -= v_step

        bui.buttonwidget(
            parent=self._root_widget,
            position=(btn_x, v_pos),
            size=(btn_width, btn_height),
            label='Delete Selected',
            on_activate_call=self.delete_selected_account,
        )

        # List box on the left
        self.list_width = btn_col_x - 30
        list_x = 20

        scroll = bui.scrollwidget(
            parent=self._root_widget,
            position=(list_x, content_y),
            size=(self.list_width, content_height),
        )
        bui.containerwidget(edit=scroll, claims_left_right=True)

        self._list = bui.columnwidget(
            parent=scroll,
            background=False,
            border=0,
        )

        self._selected_profile: Optional[str] = None
        self._profile_widgets: list[bui.Widget] = []

        self._refresh_account_list()

    def _close(self) -> None:
        bui.containerwidget(edit=self._root_widget, transition='out_right')

    def _refresh_account_list(self):
        for widget in self._profile_widgets:
            widget.delete()
        self._profile_widgets = []

        profiles = sorted(listdir(ACCOUNTS_DIR))
        for prof in profiles:
            text_widget = bui.textwidget(
                parent=self._list,
                text=prof,
                size=(self.list_width, 30),
                color=(1, 1, 1),
                selectable=True,
                click_activate=True,
                max_chars=40,
                corner_scale=1.2,
            )
            self._profile_widgets.append(text_widget)
            bui.textwidget(
                edit=text_widget, on_activate_call=babase.Call(
                    self.on_select_profile, prof, text_widget)
            )

    def on_select_profile(self, profile_name: str, selected_widget: bui.Widget):
        self._selected_profile = profile_name
        for widget in self._profile_widgets:
            bui.textwidget(edit=widget, color=(1, 1, 1))
        bui.textwidget(edit=selected_widget, color=(1, 1, 0.2))

    def get_current_account(self) -> Optional[str]:
        if plus.get_v1_account_state() == 'signed_in':
            return plus.get_v1_account_display_string()
        return None

    def save_current_account(self):
        name = self.get_current_account()
        if not name:
            print_msg("No account signed in!", color=(1, 0, 0))
            return

        account_folder = path.join(ACCOUNTS_DIR, name)
        if not path.exists(account_folder):
            mkdir(account_folder)

        for fname in ACCOUNT_FILES:
            src = path.join(USER_DIR, fname)
            if path.exists(src):
                try:
                    copy(src, path.join(account_folder, fname))
                except IOError as e:
                    print_msg(f"Error saving {fname}: {e}", color=(1, 0, 0))

        print_msg(f"Saved current account as '{name}'")
        self._refresh_account_list()

    def add_new_account(self) -> None:
        def do_action():
            self.save_current_account()
            for fname in ACCOUNT_FILES:
                file_path = path.join(USER_DIR, fname)
                if path.exists(file_path):
                    remove(file_path)
            print_msg('Account files removed.')

        ConfirmWindow(
            text='This will save your current login and then shutdown the game.\nAre you sure?',
            action=lambda: self.lock_call_exit(do_action),
            ok_text='Confirm & Logout',
            cancel_is_selected=True,
        )

    def lock_call_exit(self, callable_action):
        babase.suppress_config_and_state_writes()
        callable_action()
        babase.apptimer(1.5, babase.quit)

    def load_selected_account(self):
        if not self._selected_profile:
            print_msg("No account selected to load!", color=(1, 0, 0))
            return
        account_folder = path.join(ACCOUNTS_DIR, self._selected_profile)

        self.save_current_account()

        def do_switch():
            for fname in ACCOUNT_FILES:
                dest = path.join(USER_DIR, fname)
                src = path.join(account_folder, fname)
                if path.exists(dest):
                    remove(dest)
                if path.exists(src):
                    copy(src, dest)
            print_msg(f"Loaded account {self._selected_profile}")

        ConfirmWindow(
            text=f"Load account {self._selected_profile}?\nGame will shut down.",
            action=lambda: self.lock_call_exit(do_switch),
            cancel_is_selected=True,
        )

    def delete_selected_account(self):
        if not self._selected_profile:
            print_msg("No account selected to delete!", color=(1, 0, 0))
            return
        account_folder = path.join(ACCOUNTS_DIR, self._selected_profile)

        def do_delete():
            if path.exists(account_folder):
                rmtree(account_folder)
            print_msg(f"Deleted account '{self._selected_profile}'", color=(1, 0.5, 0.5))
            self._selected_profile = None
            self._refresh_account_list()

        ConfirmWindow(
            text=f"Delete account '{self._selected_profile}' permanently?",
            action=do_delete,
            cancel_is_selected=True,
        )


# --- Monkey-Patching ---
_original_account_settings_init = AccountSettingsWindow.__init__
_original_on_adapter_sign_in_result = AccountSettingsWindow._on_adapter_sign_in_result


def new_account_settings_init(self, *args, **kwargs):
    _original_account_settings_init(self, *args, **kwargs)
    button_width = 350
    # Use a lambda to create an instance of the class when the button is pressed.
    bui.buttonwidget(
        parent=self._subcontainer,
        position=((self._sub_width - button_width) * 0.5, -25),
        size=(button_width, 60),
        label='Switch Accounts...',
        on_activate_call=lambda: AccountSwitcherUI()
    )


def new_on_adapter_sign_in_result(self, result: str) -> None:
    # First, call the original method to ensure default behavior runs.
    _original_on_adapter_sign_in_result(self, result)
    print(result)
    # Now, "capture" the result with our custom logic.
    if result == 'success':
        print_msg('Sign-in Successful!', color=(0, 1, 0))
        # You could add other logic here, like automatically saving the new account.
    elif result != 'cancel':  # Don't show a message on user cancellation.
        print_msg(f'Sign-in failed: {result}', color=(1, 0, 0))

# ba_meta export babase.Plugin


class EntryPoint(babase.Plugin):
    def on_app_running(self):
        # Apply both monkey-patches when the app runs.
        AccountSettingsWindow.__init__ = new_account_settings_init
        AccountSettingsWindow._on_adapter_sign_in_result = new_on_adapter_sign_in_result

    def has_settings_ui(self):
        return True

    def show_settings_ui(self, button=None):
        AccountSwitcherUI()
