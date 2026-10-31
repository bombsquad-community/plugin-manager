# ba_meta require api 9
# BsGloves - Infinity Boxing Gloves (BombSquad 1.7.62 only)
# Original author: EXTRAX8

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.spaz import Spaz

if TYPE_CHECKING:
    from typing import Any

plugman = {
    'filename': 'BsGloves.py',
    'version': '1.4.0',
    'authors': ['EXTRAX8'],
    'description': 'Infinity Boxing Gloves (BombSquad 1.7.62 only).',
}

SUPPORTED_VERSION = '1.7.62'
CONFIG_KEY = 'BsGloves Enabled'
SERVER_TAGS = ('extrax8', 'infinity', 'gloves')


def _engine_version() -> str:
    """Return the running engine version string, or '' if unknown."""
    env = babase.app.env
    for name in ('engine_version', 'version'):
        value = getattr(env, name, None)
        if isinstance(value, str) and value:
            return value
    return ''


def _is_supported() -> bool:
    return _engine_version() == SUPPORTED_VERSION


def _is_enabled() -> bool:
    return bool(babase.app.config.get(CONFIG_KEY, True))


def _is_safe_environment() -> bool:
    """True when offline/local, or on a server that allows the gloves."""
    try:
        info = None
        getter = getattr(bs, 'get_connection_to_host_info_2', None)
        if getter is not None:
            info = getter()
        else:
            old = getattr(bs, 'get_connection_to_host_info', None)
            if old is not None:
                info = old()
        if not info:
            return True  # not connected to a remote host
        name = (getattr(info, 'name', None)
                or (info.get('name') if isinstance(info, dict) else '')
                or '')
        name = str(name).lower()
        return any(tag in name for tag in SERVER_TAGS)
    except Exception:
        return False


def _active() -> bool:
    return _is_enabled() and _is_safe_environment()


def _apply_patches() -> None:
    """Patch the engine classes in place so every importer is affected."""
    if getattr(Spaz, '_bsgloves_patched', False):
        return

    orig_equip = Spaz.equip_boxing_gloves
    orig_init = PlayerSpaz.__init__

    def equip_boxing_gloves(self: Spaz, *args: Any, **kwargs: Any) -> Any:
        result = orig_equip(self, *args, **kwargs)
        if _active():
            # Cancel the wear-off timers so the gloves never expire.
            for attr in ('_boxing_gloves_wear_off_timer',
                         '_boxing_gloves_wear_off_flash_timer'):
                if hasattr(self, attr):
                    setattr(self, attr, None)
        return result

    def player_init(self: PlayerSpaz, *args: Any, **kwargs: Any) -> None:
        orig_init(self, *args, **kwargs)
        if _active():
            self.equip_boxing_gloves()

    Spaz.equip_boxing_gloves = equip_boxing_gloves  # type: ignore
    PlayerSpaz.__init__ = player_init  # type: ignore
    Spaz._bsgloves_patched = True  # type: ignore


class _SettingsWindow:
    """Small settings popup: status line, toggle button, close button."""

    def __init__(self) -> None:
        width, height = 450, 250
        uiscale = bui.app.ui_v1.uiscale
        scale = (2.0 if uiscale is bui.UIScale.SMALL else
                 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0)
        self._root = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            size=(width, height),
            transition='in_scale',
            scale=scale,
        )
        bui.textwidget(
            parent=self._root,
            position=(width * 0.5, height - 40),
            size=(0, 0),
            text='BsGloves Settings - EXTRAX8',
            scale=1.2,
            color=(0.2, 1.0, 0.6),
            h_align='center',
            v_align='center',
        )
        safe = _is_safe_environment()
        bui.textwidget(
            parent=self._root,
            position=(width * 0.5, height - 80),
            size=(0, 0),
            text=('Environment: allowed' if safe
                  else 'Environment: blocked on this server'),
            scale=0.8,
            color=(0.4, 1.0, 0.4) if safe else (1.0, 0.4, 0.4),
            h_align='center',
            v_align='center',
        )
        self._toggle = bui.buttonwidget(
            parent=self._root,
            position=(width * 0.5 - 100, height - 150),
            size=(200, 45),
            label='',
            on_activate_call=self._on_toggle,
        )
        self._refresh()
        close = bui.buttonwidget(
            parent=self._root,
            position=(width * 0.5 - 60, 20),
            size=(120, 40),
            label='CLOSE',
            on_activate_call=self._close,
        )
        bui.containerwidget(edit=self._root, cancel_button=close)

    def _refresh(self) -> None:
        on = _is_enabled()
        bui.buttonwidget(
            edit=self._toggle,
            label='DISABLE MOD' if on else 'ENABLE MOD',
            color=(0.2, 0.6, 0.9) if on else (0.5, 0.5, 0.5),
        )

    def _on_toggle(self) -> None:
        cfg = babase.app.config
        cfg[CONFIG_KEY] = not _is_enabled()
        cfg.commit()
        self._refresh()
        if _is_enabled():
            bui.screenmessage('Endless Boxing Gloves activated!',
                              color=(0, 1, 0))
        else:
            bui.screenmessage('BsGloves paused.', color=(1, 0, 0))

    def _close(self) -> None:
        bui.containerwidget(edit=self._root, transition='out_scale')


# ba_meta export babase.Plugin
class InfinityGlovesPlugin(babase.Plugin):
    """Infinity Boxing Gloves, restricted to BombSquad 1.7.62."""

    def on_app_running(self) -> None:
        if not _is_supported():
            found = _engine_version() or 'unknown'
            bui.screenmessage(
                f'BsGloves supports only {SUPPORTED_VERSION} '
                f'(found {found}). Mod disabled.',
                color=(1, 0.3, 0.3))
            return
        _apply_patches()

    def has_settings_ui(self) -> bool:
        return True

    def show_settings_ui(self, source_widget: Any) -> None:
        if not _is_supported():
            bui.screenmessage(f'BsGloves supports only {SUPPORTED_VERSION}.',
                              color=(1, 0.3, 0.3))
            return
        _SettingsWindow()


# created by EXTRAX8
# ModeVersion: 1.4.0
# BsVersion: 1.7.62 only
