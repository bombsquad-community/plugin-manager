# Discord : @y.lw

from __future__ import annotations
from typing import Callable, TypeVar
import babase
import bauiv1 as bui
from bauiv1lib.gather.publictab import PublicGatherTab
import bascenev1 as bs

# Global state
is_refreshing = True
hide_full = False
hide_empty = False
only_empty = False

# TypeVars
ClassType = TypeVar('ClassType')
MethodType = TypeVar('MethodType')

def override(cls: ClassType) -> Callable[[MethodType], MethodType]:
    def decorator(new_method: MethodType) -> MethodType:
        method_name = new_method.__code__.co_name
        if hasattr(cls, method_name):
            setattr(cls, f'_original_{method_name}', getattr(cls, method_name))
        setattr(cls, method_name, new_method)
        return new_method
    return decorator

# Enhanced Gather Tab
class EnhancedPublicGatherTab(PublicGatherTab):
    @override(PublicGatherTab)
    def _build_join_tab(self, width: float, height: float) -> None:
        self._original__build_join_tab(width, height)
        self._open_window_button = bui.buttonwidget(
            parent=self._container,
            label='Party Filters',
            size=(120, 45),
            position=(110, height - 115),
            on_activate_call=bs.WeakCall(self._open_window))

    @override(PublicGatherTab)
    def _open_window(self) -> None:
        c_width, c_height = 600, 400
        uiscale = bui.app.ui_v1.uiscale
        scale = 1.8 if uiscale is babase.UIScale.SMALL else 1.55 if uiscale is babase.UIScale.MEDIUM else 1.0
        self.window_root = bui.containerwidget(
            scale=scale,
            stack_offset=(0, -10) if uiscale is babase.UIScale.SMALL else (0, 15),
            size=(c_width, c_height),
            color=(0.5, 0.5, 0.5),
            transition='in_scale',
            on_outside_click_call=bs.WeakCall(self._close_window))

        v_ = 50
        bui.textwidget(
            parent=self.window_root,
            size=(0, 0),
            h_align='center',
            v_align='center',
            text='Party Filters Menu',
            scale=1.5,
            color=(1, 1, 0.7),
            maxwidth=c_width * 0.8,
            position=(c_width * 0.5, c_height - 60))

        bui.buttonwidget(
            parent=self.window_root,
            position=(c_width * 0.1, c_height * 0.8),
            size=(60, 60),
            scale=0.8,
            color=(1, 0.3, 0.3),
            label=babase.charstr(babase.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self._close_window)

        v = c_height - 175
        bui.checkboxwidget(
            parent=self.window_root,
            text='Freeze Party List',
            position=(c_height // 2, v),
            size=(200, 30),
            color=(0.6, 0.6, 0.6),
            autoselect=True,
            textcolor=(0.8, 0.8, 0.8),
            value=not is_refreshing,
            on_value_change_call=bs.WeakCall(self._toggle_refresh))

        v -= v_
        bui.checkboxwidget(
            parent=self.window_root,
            text='Hide Full Parties',
            position=(c_height // 2, v),
            size=(200, 30),
            autoselect=True,
            color=(0.6, 0.6, 0.6),
            textcolor=(0.8, 0.8, 0.8),
            value=hide_full,
            on_value_change_call=bs.WeakCall(self._toggle_full))

        v -= v_
        self._empty_checkbox = bui.checkboxwidget(
            parent=self.window_root,
            text='Hide Empty Parties',
            position=(c_height // 2, v),
            size=(200, 30),
            autoselect=True,
            color=(0.6, 0.6, 0.6),
            textcolor=(0.8, 0.8, 0.8),
            value=hide_empty,
            on_value_change_call=bs.WeakCall(self._toggle_empty))

        v -= v_
        self._only_empty_checkbox = bui.checkboxwidget(
            parent=self.window_root,
            text='Only Empty Parties',
            position=(c_height // 2, v),
            size=(200, 30),
            autoselect=True,
            color=(0.6, 0.6, 0.6),
            textcolor=(0.8, 0.8, 0.8),
            value=only_empty,
            on_value_change_call=bs.WeakCall(self._toggle_only_empty))

    @override(PublicGatherTab)
    def _close_window(self) -> None:
        bui.getsound('shieldDown').play()
        bui.containerwidget(edit=self.window_root, transition='out_scale')

    @override(PublicGatherTab)
    def _toggle_refresh(self, _=None) -> None:
        global is_refreshing
        is_refreshing = not is_refreshing
        bui.screenmessage(f"Refreshing {'Enabled' if is_refreshing else 'Disabled'}", color=(1, 1, 0))

    @override(PublicGatherTab)
    def _toggle_full(self, _=None) -> None:
        global hide_full
        hide_full = not hide_full
        bui.screenmessage(f"{'Hiding' if hide_full else 'Showing'} Full Parties", color=(1, 1, 0))
        self._update_party_rows()

    @override(PublicGatherTab)
    def _toggle_empty(self, _=None) -> None:
        global hide_empty, only_empty
        hide_empty = not hide_empty
        if hide_empty:
            only_empty = False
        bui.screenmessage(f"{'Hiding' if hide_empty else 'Showing'} Empty Parties", color=(1, 1, 0))
        if hide_empty:
                bui.checkboxwidget(edit=self._only_empty_checkbox, value=only_empty)
        self._update_party_rows()

    @override(PublicGatherTab)
    def _toggle_only_empty(self, _=None) -> None:
        global only_empty, hide_empty
        only_empty = not only_empty
        if only_empty:
            hide_empty = False
        bui.screenmessage(f"{'Showing Only Empty' if only_empty else 'Showing All'} Parties", color=(1, 1, 0))
        if only_empty:
                bui.checkboxwidget(edit=self._empty_checkbox, value=hide_empty)
        self._update_party_rows()

    @override(PublicGatherTab)
    def _update_party_rows(self) -> None:
        self._parties_sorted = list(self._parties.items())
        if is_refreshing:
            self._original__update_party_rows()
            if hide_full:
                self._parties_sorted = [
                    p for p in self._parties_sorted if p[1].size < p[1].size_max]
            if hide_empty:
                self._parties_sorted = [p for p in self._parties_sorted if p[1].size > 0]
            if only_empty:
                self._parties_sorted = [p for p in self._parties_sorted if p[1].size == 0]


# ba_meta require api 9
# ba_meta export babase.Plugin
class ByYelllow(babase.Plugin):
    def on_app_running(self) -> None:
        pass  # Bruh
