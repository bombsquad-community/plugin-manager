# ba_meta require api 9
"""
Friend Manager
~~~~~~~~~~~~~~
Add players you meet in online parties to a persistent friend list, see
their known profile names, and get notified when they join a party with you.

Usage:
    1. In any party (e.g. the Advanced Party Window), click/tap a player's
       name to open their menu.
    2. Select "Add Friend" (or "View Profile" if already a friend).
    3. Open the full list anytime from Settings -> the "Friends" button.
"""

from __future__ import annotations
import babase
import bauiv1 as bui
import bascenev1 as bs
import bauiv1lib.popup
import bauiv1lib.settings.allsettings
import bauiv1lib.party
import json
import os
import datetime

plugman = dict(
    plugin_name="friend_manager",
    description=(
        "Build a real friend list while playing online! Click any player's "
        "name in a party to add them as a friend - their account ID and every "
        "profile name they've played under gets saved automatically, so you'll "
        "recognize them even if they switch profiles later. Get notified when "
        "a friend joins your party. Find your full friend list anytime from "
        "Settings -> Friends."
    ),
    external_url="",
    authors=[{"name": "ItzHacker101", "email": "", "discord": ""}],
    version="1.0.1",
)


# ----------------------------------------------------------------------------
# Data layer
# ----------------------------------------------------------------------------

class FriendManager:
    """Stores and persists the friend list as a local JSON file."""

    friends: dict = {}
    _file_path: str | None = None

    @classmethod
    def _get_file_path(cls) -> str:
        if cls._file_path is None:
            try:
                base_dir = babase.app.env.python_directory_user
            except Exception:
                base_dir = os.path.dirname(os.path.abspath(__file__))

            # Keep our data in its own folder (not loose in the mods root)
            # so the whole "friend_manager_data" folder can simply be copied
            # to another device/install and friends will carry over.
            data_dir = os.path.join(base_dir, "friend_manager_data")
            try:
                os.makedirs(data_dir, exist_ok=True)
            except Exception:
                data_dir = base_dir  # fall back rather than crash

            cls._file_path = os.path.join(data_dir, "friend_list.json")
        return cls._file_path

    @classmethod
    def load(cls):
        path = cls._get_file_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                cls.friends = data if isinstance(data, dict) else {}
            except Exception as e:
                print(f"[FriendManager] Error loading friend list: {e}")
                cls.friends = {}

    @classmethod
    def save(cls):
        path = cls._get_file_path()
        try:
            tmp_path = path + ".tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(cls.friends, f, indent=4, ensure_ascii=False)
            os.replace(tmp_path, path)  # atomic-ish write
        except Exception as e:
            print(f"[FriendManager] Error saving friend list: {e}")

    @classmethod
    def add(cls, pb_id: str, v2_name: str, profiles: list, is_stable_id: bool):
        if not pb_id:
            return
        profiles = [p for p in (profiles or []) if p]
        now = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

        if pb_id in cls.friends:
            entry = cls.friends[pb_id]
            existing = entry.setdefault("profiles", [])
            for p in profiles:
                if p not in existing:
                    existing.append(p)
            if v2_name:
                entry["v2_name"] = v2_name
            entry["last_seen"] = now
            entry["stable_id"] = is_stable_id
        else:
            cls.friends[pb_id] = {
                "v2_name": v2_name or "Unknown",
                "profiles": profiles,
                "added": now,
                "last_seen": now,
                "stable_id": is_stable_id,
            }
        cls.save()

    @classmethod
    def remove(cls, pb_id: str):
        if pb_id in cls.friends:
            del cls.friends[pb_id]
            cls.save()


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _safe_roster() -> list:
    """get_game_roster() can raise or return None outside an active session."""
    try:
        roster = bs.get_game_roster()
        return roster if roster else []
    except Exception:
        return []


def _resolve_player(entry: dict) -> tuple[str, str, list, bool]:
    """
    Pulls a pb_id, display name, profile-name list, and an "is this ID
    actually stable" flag out of a roster entry.

    account_id (the V2 account hash) is the only truly stable identifier.
    If a player isn't signed into a V2 account, there's no persistent ID
    the game gives us at all - in that case we fall back to their current
    display name, but flag it as unstable so the UI can warn about it
    instead of silently pretending it's reliable.
    """
    client_id = entry.get('client_id')
    account_id = entry.get('account_id')
    v2_name = entry.get('display_string') or 'Unknown'
    is_stable = bool(account_id)
    pb_id = account_id or v2_name or f"client_{client_id}"
    profiles = [pl.get('name') for pl in entry.get('players', []) if pl.get('name')]
    return pb_id, v2_name, profiles, is_stable


def _format_relative_time(timestamp_str: str) -> str:
    """Turns '2026-06-19 10:42' into something like 'Yesterday' or '3h ago'."""
    if not timestamp_str:
        return "Unknown"
    try:
        then = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
    except Exception:
        return timestamp_str

    delta = datetime.datetime.now() - then
    seconds = delta.total_seconds()

    if seconds < 0:
        return then.strftime("%Y-%m-%d")
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        m = int(seconds // 60)
        return f"{m} minute{'s' if m != 1 else ''} ago"
    if seconds < 86400:
        h = int(seconds // 3600)
        return f"{h} hour{'s' if h != 1 else ''} ago"
    days = delta.days
    if days == 1:
        return "Yesterday"
    if days < 7:
        return f"{days} days ago"
    if days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    return then.strftime("%Y-%m-%d")


# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------

class FriendProfileWindow(bui.Window):
    def __init__(self, pb_id: str):
        self.pb_id = pb_id
        self.data = FriendManager.friends.get(pb_id, {})
        self._width = 450
        self._height = 440
        uiscale = bui.app.ui_v1.uiscale

        super().__init__(root_widget=bui.containerwidget(
            size=(self._width, self._height),
            transition='in_scale',
            scale=1.5 if uiscale is babase.UIScale.SMALL else 1.2
        ))

        self._back_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(20, self._height - 60),
            size=(50, 50),
            label=bui.charstr(bui.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self._back
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=self._back_btn)

        bui.textwidget(parent=self._root_widget, position=(self._width / 2, self._height - 40),
                       text="🪪 Friend Profile", h_align='center', v_align='center',
                       scale=1.3, color=(0.4, 1.0, 0.4))

        v = self._height - 100
        bui.textwidget(parent=self._root_widget, position=(self._width / 2, v),
                       text=f"Name: {self.data.get('v2_name', 'Unknown')}",
                       h_align='center', scale=1.1)
        v -= 28
        bui.textwidget(parent=self._root_widget, position=(self._width / 2, v),
                       text=f"ID: {self.pb_id}", h_align='center', scale=0.55,
                       color=(0.7, 0.7, 0.7))
        v -= 24
        added = self.data.get('added', 'Unknown')
        last_seen_raw = self.data.get('last_seen', added)
        bui.textwidget(parent=self._root_widget, position=(self._width / 2, v),
                       text=f"Friends since {added}  |  Last seen {_format_relative_time(last_seen_raw)}",
                       h_align='center', scale=0.55, color=(0.6, 0.6, 0.6))
        v -= 26

        if not self.data.get('stable_id', True):
            bui.textwidget(parent=self._root_widget, position=(self._width / 2, v),
                           text="⚠️ Not signed into a V2 account - ID may change later",
                           h_align='center', scale=0.55, color=(1.0, 0.7, 0.2))
            v -= 26

        bui.textwidget(parent=self._root_widget, position=(self._width / 2, v),
                       text="Known Profiles:", h_align='center', color=(0.4, 0.8, 1.0))

        v -= 20
        self._scroll = bui.scrollwidget(parent=self._root_widget, position=(40, 90),
                                        size=(self._width - 80, v - 100))
        self._column = bui.columnwidget(parent=self._scroll)

        profiles = self.data.get('profiles') or []
        if profiles:
            for prof in profiles:
                bui.textwidget(parent=self._column, text=f"• {prof}", h_align='left',
                               scale=0.8, size=(self._width - 100, 25))
        else:
            bui.textwidget(parent=self._column, text="No known profile names yet.",
                           h_align='left', scale=0.7, color=(0.6, 0.6, 0.6),
                           size=(self._width - 100, 25))

        self._remove_btn = bui.buttonwidget(
            parent=self._root_widget, position=(self._width / 2 - 100, 20), size=(200, 50),
            label="🗑️ Remove Friend", color=(0.8, 0.2, 0.2), textcolor=(1, 1, 1),
            on_activate_call=self._confirm_remove)
        self._confirm_armed = False
        self._confirm_timer = None

    def _confirm_remove(self):
        # Two-step confirm: first tap arms it, second tap (within 3s) removes.
        if not self._confirm_armed:
            self._confirm_armed = True
            if self._remove_btn and self._remove_btn.exists():
                bui.buttonwidget(edit=self._remove_btn, label="⚠️ Tap again to confirm")
            self._confirm_timer = babase.AppTimer(3.0, babase.CallStrict(self._disarm))
            return
        self._disarm()
        self._remove()

    def _disarm(self):
        self._confirm_armed = False
        if self._remove_btn and self._remove_btn.exists():
            bui.buttonwidget(edit=self._remove_btn, label="🗑️ Remove Friend")

    def _remove(self):
        name = self.data.get('v2_name', 'Friend')
        FriendManager.remove(self.pb_id)
        bui.screenmessage(f"🗑️ {name} removed from friends.", color=(1, 0.4, 0.4))
        self._back()

    def _back(self):
        if self._root_widget and self._root_widget.exists():
            bui.containerwidget(edit=self._root_widget, transition='out_scale')


class FriendListWindow(bui.Window):
    def __init__(self, origin_widget=None):
        self._width = 650
        self._height = 450
        uiscale = bui.app.ui_v1.uiscale

        offset = origin_widget.get_screen_space_center() if origin_widget else (0, 0)

        super().__init__(root_widget=bui.containerwidget(
            size=(self._width, self._height),
            transition='in_scale',
            scale=1.4 if uiscale is babase.UIScale.SMALL else 1.0,
            scale_origin_stack_offset=offset
        ))

        self._back_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(40, self._height - 65),
            size=(60, 60),
            label=bui.charstr(bui.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self._back
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=self._back_btn)

        self._title_text = bui.textwidget(
            parent=self._root_widget, position=(self._width * 0.5, self._height - 40),
            size=(0, 0), text="📋 Friends List", h_align='center', v_align='center',
            scale=1.3, color=(0.4, 1.0, 0.4))

        self._scroll = bui.scrollwidget(parent=self._root_widget, position=(40, 40),
                                        size=(self._width - 80, self._height - 110))
        self._column = bui.columnwidget(parent=self._scroll)
        self._refresh()

    def _refresh(self):
        for child in self._column.get_children():
            child.delete()

        if self._title_text and self._title_text.exists():
            bui.textwidget(edit=self._title_text,
                           text=f"📋 Friends List ({len(FriendManager.friends)})")

        if not FriendManager.friends:
            bui.textwidget(parent=self._column,
                           text="No friends added yet.\n"
                                "Click a player's name in a party to add one!",
                           h_align='left', scale=0.8, color=(0.6, 0.6, 0.6),
                           size=(self._width - 140, 60))
            return

        online_ids = {_resolve_player(entry)[0] for entry in _safe_roster()}

        sorted_friends = sorted(
            FriendManager.friends.items(),
            key=lambda kv: kv[1].get('v2_name', '').lower()
        )

        for pb_id, data in sorted_friends:
            is_online = pb_id in online_ids
            row = bui.containerwidget(
                parent=self._column, size=(self._width - 100, 60), background=True,
                color=(0.25, 0.4, 0.25) if is_online else (0.25, 0.25, 0.25))
            bui.textwidget(parent=row, position=(15, 32), size=(0, 0),
                           text=data.get('v2_name', 'Unknown'), scale=0.9,
                           h_align='left', v_align='center', color=(1, 1, 1))
            status = "🟢 Online now" if is_online else \
                f"Last seen: {_format_relative_time(data.get('last_seen'))}"
            bui.textwidget(parent=row, position=(15, 12), size=(0, 0), text=status,
                           scale=0.5, h_align='left', v_align='center',
                           color=(0.4, 1.0, 0.4) if is_online else (0.6, 0.6, 0.6))

            bui.buttonwidget(parent=row, position=(self._width - 240, 10), size=(120, 40),
                             label="👤 Profile", color=(0.2, 0.6, 0.8), textcolor=(1, 1, 1),
                             on_activate_call=babase.CallPartial(FriendProfileWindow, pb_id))

    def _back(self):
        if self._root_widget and self._root_widget.exists():
            bui.containerwidget(edit=self._root_widget, transition='out_scale')


# ----------------------------------------------------------------------------
# Background polling: keeps friend data fresh + notifies when a friend joins
# ----------------------------------------------------------------------------

_previously_online_friend_ids: set[str] = set()
_auto_update_first_run = True


def auto_update_friends():
    global _previously_online_friend_ids, _auto_update_first_run

    roster = _safe_roster()
    if not roster:
        return

    now = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    current_online_friend_ids = set()
    updated = False

    for entry in roster:
        try:
            pb_id, v2_name, profiles, is_stable = _resolve_player(entry)
        except Exception:
            continue

        if pb_id not in FriendManager.friends:
            continue

        current_online_friend_ids.add(pb_id)
        friend = FriendManager.friends[pb_id]

        if v2_name and v2_name != friend.get('v2_name'):
            friend['v2_name'] = v2_name
            updated = True

        existing = friend.setdefault('profiles', [])
        for pr in profiles:
            if pr not in existing:
                existing.append(pr)
                updated = True

        friend['last_seen'] = now
        friend['stable_id'] = is_stable
        updated = True

        # Notify only for friends who *newly* appeared since the last check
        # (and never on the very first scan after launch, to avoid spamming
        # "joined" messages for people already in the party when you start).
        if not _auto_update_first_run and pb_id not in _previously_online_friend_ids:
            bui.screenmessage(f"👋 Your friend {v2_name} just joined the party!",
                              color=(0.3, 0.9, 1.0))
            try:
                bui.getsound('shieldUp').play()
            except Exception:
                pass

    _previously_online_friend_ids = current_online_friend_ids
    _auto_update_first_run = False

    if updated:
        FriendManager.save()


# ----------------------------------------------------------------------------
# Monkey patches
# ----------------------------------------------------------------------------

def apply_friend_manager_patches():
    # 1. Inject a "Friends" button into the settings window.
    _old_allsettings_init = bauiv1lib.settings.allsettings.AllSettingsWindow.__init__

    def _new_allsettings_init(self, transition='in_right', origin_widget=None):
        _old_allsettings_init(self, transition, origin_widget)

        def inject_btn():
            if self._root_widget and self._root_widget.exists():
                try:
                    w = getattr(self, '_width', 800)
                    bui.buttonwidget(
                        parent=self._root_widget,
                        position=(w - 180, 40),
                        size=(140, 50),
                        label="👥 Friends",
                        color=(0.2, 0.6, 0.2),
                        textcolor=(1, 1, 1),
                        scale=0.9,
                        on_activate_call=babase.CallPartial(
                            lambda widget: FriendListWindow(origin_widget=widget),
                            self._root_widget)
                    )
                except Exception as e:
                    print(f"[FriendManager] Couldn't inject Friends button: {e}")

        babase.apptimer(0.05, inject_btn)

    bauiv1lib.settings.allsettings.AllSettingsWindow.__init__ = _new_allsettings_init

    # 2. Remember which client_id was clicked in the party window, so the
    #    popup-menu patch below knows which player it's dealing with.
    _old_on_party_member_press = bauiv1lib.party.PartyWindow._on_party_member_press

    def _pre_party_member_press(self, client_id: int, is_host: bool, widget: bui.Widget):
        self._friendmgr_target_id = client_id
        _old_on_party_member_press(self, client_id, is_host, widget)

    bauiv1lib.party.PartyWindow._on_party_member_press = _pre_party_member_press

    # 3. Patch the popup menu that appears for a clicked player, adding our
    #    "Add Friend" / "View Profile" entry.
    _old_popup_init = bauiv1lib.popup.PopupMenuWindow.__init__

    def _new_popup_init(self, *args, **kwargs):
        choices = kwargs.get('choices')
        choices_from_kwargs = 'choices' in kwargs
        if choices is None and len(args) > 1:
            choices = args[1]

        choices_display = kwargs.get('choices_display')
        choices_display_from_kwargs = 'choices_display' in kwargs
        if choices_display is None and len(args) > 8:
            choices_display = args[8]

        delegate = kwargs.get('delegate')
        if delegate is None and len(args) > 3:
            delegate = args[3]

        # The presence of this attribute (set by _pre_party_member_press just
        # above) is itself the signal that this popup belongs to a player row.
        client_id = getattr(delegate, '_friendmgr_target_id', None)
        if delegate is not None and hasattr(delegate, '_friendmgr_target_id'):
            delattr(delegate, '_friendmgr_target_id')

        if client_id is not None and delegate is not None and choices is not None:
            pb_id = None
            v2_name = "Unknown"
            profiles: list = []
            is_stable = False

            for entry in _safe_roster():
                if entry.get('client_id') == client_id:
                    pb_id, v2_name, profiles, is_stable = _resolve_player(entry)
                    break

            if pb_id:
                choices = list(choices)
                if choices_display is None:
                    choices_display = [babase.Lstr(value=c) for c in choices]
                else:
                    choices_display = list(choices_display)

                if pb_id in FriendManager.friends:
                    choices.append('friendmgr_view_profile')
                    choices_display.append(babase.Lstr(value='👤 View Profile'))
                else:
                    choices.append('friendmgr_add_friend')
                    choices_display.append(babase.Lstr(value='➕ Add Friend'))

                if choices_from_kwargs:
                    kwargs['choices'] = choices
                elif len(args) > 1:
                    args = list(args)
                    args[1] = choices
                    args = tuple(args)
                else:
                    kwargs['choices'] = choices

                if choices_display_from_kwargs:
                    kwargs['choices_display'] = choices_display
                elif len(args) > 8:
                    args = list(args)
                    args[8] = choices_display
                    args = tuple(args)
                else:
                    kwargs['choices_display'] = choices_display

                self._friendmgr_target_id = client_id

                cls = delegate.__class__
                if not getattr(cls, '_friendmgr_patched', False):
                    orig_choice = cls.popup_menu_selected_choice

                    def _new_choice(self_del, popup_win, choice):
                        target_cid = getattr(popup_win, '_friendmgr_target_id', None)

                        if choice in ('friendmgr_add_friend', 'friendmgr_view_profile') \
                                and target_cid is not None:
                            for entry in _safe_roster():
                                if entry.get('client_id') == target_cid:
                                    p_pb_id, p_v2, p_profiles, p_stable = _resolve_player(entry)
                                    if choice == 'friendmgr_add_friend':
                                        FriendManager.add(p_pb_id, p_v2, p_profiles, p_stable)
                                        bui.screenmessage(
                                            f"✅ {p_v2} added to your friends!",
                                            color=(0, 1, 0))
                                        try:
                                            bui.getsound('shieldUp').play()
                                        except Exception:
                                            pass
                                    else:
                                        FriendProfileWindow(p_pb_id)
                                    return
                            return

                        orig_choice(self_del, popup_win, choice)

                    cls.popup_menu_selected_choice = _new_choice
                    cls._friendmgr_patched = True

        _old_popup_init(self, *args, **kwargs)

    bauiv1lib.popup.PopupMenuWindow.__init__ = _new_popup_init


# ba_meta export babase.Plugin
class FriendManagerPlugin(babase.Plugin):
    def on_app_running(self):
        FriendManager.load()
        babase.apptimer(1.0, babase.CallStrict(self.delayed_startup))

    def delayed_startup(self):
        try:
            apply_friend_manager_patches()
            bui.screenmessage("🤝 Friend Manager activated!", color=(0.2, 1.0, 0.2))
            try:
                bui.getsound('shieldUp').play()
            except Exception:
                pass
        except Exception as e:
            print(f"[FriendManager] Setup error: {e}")

        self._timer = babase.AppTimer(5.0, babase.CallStrict(auto_update_friends), repeat=True)
