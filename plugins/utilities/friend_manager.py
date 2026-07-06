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
import threading
import urllib.request
import urllib.parse

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
    authors=[{"name": "KIRA", "email": "", "discord": ""}],
    version="1.0.0",
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
    """Return the current party roster with the richest account data available.

    BombSquad exposes roster data at two layers:

    ``babase.app.classic.game_roster``
        The *classic-layer* roster maintained by the lobby/party subsystem.
        This is what ``bauiv1lib.party.PartyWindow`` (and community plugins
        such as ``advanced_party_window.py``) use internally.  Each entry
        includes a ``'pbid'`` field containing the player's V2 account ID
        for signed-in players — exactly what we need for stable identification.

    ``bascenev1.get_game_roster()``
        The *scene-layer* roster available only while a game scene is active.
        It lacks the ``'pbid'`` field and may only have V1-style account IDs
        or nothing at all.

    We always try the classic-layer roster first and fall back to the
    scene-layer roster if the former is unavailable (e.g. during a game).
    """
    try:
        classic = babase.app.classic
        if classic is not None:
            roster = getattr(classic, 'game_roster', None)
            if isinstance(roster, list) and roster:
                return roster
        return bs.get_game_roster() or []
    except Exception:
        return []


def _resolve_player(entry: dict) -> tuple[str, str, list, bool]:
    """Extract (pb_id, display_name, profile_names, is_stable) from a roster entry.

    The V2 account ID (``pb-UUID``) is the *ideal* stable identifier, but
    BombSquad also exposes V1-style IDs (``Google:xxx``, ``Apple:xxx``,
    ``Device:xxx``) which are equally persistent across renames.  We accept
    any non-empty account string that is distinct from the player's display
    name — that guard prevents us from accidentally using the display name
    itself as the key (which is exactly the bug we're trying to avoid).

    BombSquad 1.7.x exposes the account ID through several channels; we probe
    all of them in priority order and take the first usable result:

    Priority 1 — top-level entry fields
        ``account_id``, ``v2_account_id``, ``pb_id``

    Priority 2 — per-player dict fields
        ``account_id``, ``v2_account_id``, ``pb_id``

    Priority 3 — spec_string (format ``'X:some-id'``, take part after ``:``)
        e.g. ``'P:pb-UUID'`` → ``'pb-UUID'``

    If nothing is found the player is flagged as unstable and their current
    display name is used as the key (⚠️ shown in the UI).

    Note: ``babase.app.plus.accounts.primary.accountid`` only returns the
    *local* player's own ID; it cannot be used for remote roster entries.
    """
    v2_name = entry.get('display_string') or 'Unknown'
    client_id = entry.get('client_id', 0)
    account_id = ''

    def _accept(val: object) -> str:
        """Return ``val`` if it looks like a real account ID, else ''."""
        if not isinstance(val, str):
            return ''
        val = val.strip()
        # Reject empty strings, and reject anything that equals the display
        # name (which would just recreate the original "name-as-key" bug).
        if not val or val == v2_name:
            return ''
        # Reject client_N fallback keys we may have generated ourselves.
        if val.startswith('client_'):
            return ''
        return val

    # ── Priority 1: top-level fields ──────────────────────────────────────────
    # 'pbid' is the field name used by babase.app.classic.game_roster and by
    # community plugins such as advanced_party_window.py — try it first.
    for field in ('pbid', 'account_id', 'v2_account_id', 'pb_id'):
        account_id = _accept(entry.get(field))
        if account_id:
            break

    # ── Priority 2 & 3: scan each player dict ─────────────────────────────────
    if not account_id:
        for player in entry.get('players', []):
            # Direct field — 'pbid' first, then legacy names
            for field in ('pbid', 'account_id', 'v2_account_id', 'pb_id'):
                account_id = _accept(player.get(field))
                if account_id:
                    break
            if account_id:
                break
            # spec_string: 'P:pb-UUID' or 'G:GoogleID' etc.
            spec = player.get('spec_string') or ''
            if isinstance(spec, str) and ':' in spec:
                account_id = _accept(spec.split(':', 1)[1])
            if account_id:
                break

    is_stable = bool(account_id)
    pb_id = account_id if is_stable else (v2_name or f'client_{client_id}')
    profiles = [
        pl.get('name') for pl in entry.get('players', []) if pl.get('name')
    ]
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
# Firebase REST helpers
# All network calls run on daemon threads so the game thread is never blocked.
# Results are marshalled back via babase.pushcall(from_other_thread=True).
# ----------------------------------------------------------------------------

#: Firebase Realtime Database root for this plugin's rating data.
_FIREBASE_DB_URL = (
    'https://rating-system-c7adc-default-rtdb'
    '.asia-southeast1.firebasedatabase.app'
)
#: Top-level key under which ratings are stored.
_RATING_KEY = 'friend_manager_v1'


def _get_account_id() -> str | None:
    """Return the primary V2 account-ID string, or None if unavailable.

    The account ID is the only stable, persistent identifier for a player
    across sessions and device reinstalls.  See:
    https://efroemling.github.io/ballistica/babase.html#babase.AccountV2Handle.accountid
    """
    try:
        plus = babase.app.plus
        if plus is None:
            return None
        primary = plus.accounts.primary
        if primary is None:
            return None
        with primary:
            return primary.accountid
    except Exception:
        return None


def _firebase_get(
    path: str,
    callback: object,   # (data: dict | None, error: str | None) -> None
) -> None:
    """GET ``path`` from the Firebase Realtime DB and call ``callback`` on the
    game thread when done.  ``path`` must start with ``/``.
    """
    url = f'{_FIREBASE_DB_URL}{path}'

    def _run() -> None:
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            babase.pushcall(lambda: callback(data, None),
                            from_other_thread=True)
        except Exception as exc:
            babase.pushcall(lambda: callback(None, str(exc)),
                            from_other_thread=True)

    threading.Thread(target=_run, daemon=True).start()


def _firebase_put(
    path: str,
    value: object,
    callback: object,   # (result: object | None, error: str | None) -> None
) -> None:
    """PUT ``value`` (JSON-serialisable) to ``path`` in the Firebase Realtime
    DB and call ``callback`` on the game thread when done.
    """
    url = f'{_FIREBASE_DB_URL}{path}'

    def _run() -> None:
        try:
            body = json.dumps(value).encode('utf-8')
            req = urllib.request.Request(url, data=body, method='PUT')
            req.add_header('Content-Type', 'application/json; charset=utf-8')
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode('utf-8'))
            babase.pushcall(lambda: callback(result, None),
                            from_other_thread=True)
        except Exception as exc:
            babase.pushcall(lambda: callback(None, str(exc)),
                            from_other_thread=True)

    threading.Thread(target=_run, daemon=True).start()


def _firebase_key(account_id: str) -> str:
    """Sanitise an account-ID for use as a Firebase Realtime DB key.

    Firebase keys may not contain  ``.  $  #  [  ]  /``.
    BombSquad V2 account IDs look like ``pb-UUID`` where UUID contains
    only hyphens and hex digits — hyphens are permitted in Firebase keys,
    so only dots and dollar signs need escaping in practice.
    """
    return account_id.replace('.', '_').replace('$', '_').replace('#', '_')


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


class FriendManagerRatingWindow(bui.Window):
    """Firebase-backed 5-star rating popup for the Friend Manager plugin.

    Each player is identified by their V2 account ID, so the one-rating-per-
    user rule is enforced on the client side without needing Firebase Auth.
    Ratings are stored at ``/{_RATING_KEY}/ratings/{account_key}`` as an
    integer 1-5.  The window fetches all ratings on open to compute a live
    average and a total-rater count.

    Maintainer note
    ---------------
    Firebase Realtime DB REST is used instead of the JS SDK because BombSquad
    plugins run in CPython with no DOM / browser context.  The DB rules should
    allow public read and authenticated-or-valid write; for simplicity during
    development ``".read": true, ".write": true`` is sufficient, but production
    should tighten this to prevent tampering.
    """

    _RATINGS_PATH = f'/{_RATING_KEY}/ratings'
    _ISSUES_URL = 'https://github.com/bombsquad-community/plugin-manager/issues'

    def __init__(self, origin_widget: bui.Widget | None = None):
        width, height = 460, 390
        uiscale = bui.app.ui_v1.uiscale
        self._selected_stars: int = 0
        self._submitted: bool = False
        self._account_id: str | None = _get_account_id()
        self._star_btns: list[bui.Widget] = []

        super().__init__(root_widget=bui.containerwidget(
            size=(width, height),
            transition='in_scale',
            scale=1.5 if uiscale is babase.UIScale.SMALL else 1.1,
            scale_origin_stack_offset=(
                origin_widget.get_screen_space_center()
                if origin_widget else (0, 0)
            ),
        ))

        # ── Title ─────────────────────────────────────────────────────────────
        bui.textwidget(
            parent=self._root_widget,
            position=(width / 2, height - 34),
            size=(0, 0),
            text='⭐  Rate Friend Manager',
            h_align='center', v_align='center',
            scale=1.05, color=(1.0, 0.88, 0.25),
        )

        # ── Community rating stats (live, loaded in background) ───────────────
        bui.textwidget(
            parent=self._root_widget,
            position=(width / 2, height - 68),
            size=(0, 0),
            text='Community rating',
            h_align='center', v_align='center',
            scale=0.62, color=(0.5, 0.5, 0.5),
        )
        self._stats_text = bui.textwidget(
            parent=self._root_widget,
            position=(width / 2, height - 100),
            size=(0, 0),
            text='⏳  Loading…',
            h_align='center', v_align='center',
            scale=0.82, color=(0.6, 0.6, 0.6),
        )

        # ── Stars display (community average, filled bar) ─────────────────────
        # Rendered as a read-only visual once stats load; stars stay in their
        # starting grey state until we get actual data.
        self._avg_stars_text = bui.textwidget(
            parent=self._root_widget,
            position=(width / 2, height - 130),
            size=(0, 0),
            text='',
            h_align='center', v_align='center',
            scale=1.0, color=(1.0, 0.82, 0.0),
        )

        # Divider
        bui.imagewidget(
            parent=self._root_widget,
            position=(30, height - 152),
            size=(width - 60, 1),
            texture=bui.gettexture('white'),
            color=(0.25, 0.25, 0.25),
        )

        # ── "Your rating" section ─────────────────────────────────────────────
        bui.textwidget(
            parent=self._root_widget,
            position=(width / 2, height - 174),
            size=(0, 0),
            text='Your rating',
            h_align='center', v_align='center',
            scale=0.72, color=(0.75, 0.75, 0.75),
        )

        # Interactive star buttons
        star_w = 56
        star_gap = 6
        total_sw = 5 * star_w + 4 * star_gap
        sx = (width - total_sw) / 2
        sy = height - 245

        for i in range(5):
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(sx + i * (star_w + star_gap), sy),
                size=(star_w, star_w),
                label='★',
                color=(0.28, 0.28, 0.28),
                textcolor=(0.4, 0.4, 0.4),
                on_activate_call=babase.CallPartial(self._on_star_tap, i + 1),
                enable_sound=True,
            )
            self._star_btns.append(btn)

        # ── Submit / status button ────────────────────────────────────────────
        self._submit_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(width / 2 - 80, sy - 58),
            size=(160, 44),
            label='Select stars above',
            color=(0.22, 0.22, 0.22),
            textcolor=(0.5, 0.5, 0.5),
            on_activate_call=self._submit,
        )

        # ── Bug report / feature request button ───────────────────────────────
        bui.buttonwidget(
            parent=self._root_widget,
            position=(width / 2 - 130, 54),
            size=(260, 36),
            label='🐛  Report a Bug / 💡 Feature Request',
            color=(0.15, 0.28, 0.45),
            textcolor=(0.65, 0.8, 1.0),
            on_activate_call=self._open_issues,
        )

        # ── Close button ──────────────────────────────────────────────────────
        close_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(width / 2 - 45, 14),
            size=(90, 34),
            label='Close',
            color=(0.28, 0.28, 0.28),
            textcolor=(0.7, 0.7, 0.7),
            on_activate_call=self._close,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=close_btn)

        # ── Kick off background data fetch ────────────────────────────────────
        _firebase_get(self._RATINGS_PATH + '.json', self._on_data_loaded)

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _avg_star_str(avg: float) -> str:
        """Build a ★/☆ string like ★★★★☆ for a given average (0-5)."""
        filled = int(round(avg))
        return '★' * filled + '☆' * (5 - filled)

    def _on_data_loaded(
        self, data: dict | None, error: str | None
    ) -> None:
        """Called on the game thread once Firebase returns the ratings map."""
        if not (self._root_widget and self._root_widget.exists()):
            return

        if error or not isinstance(data, dict):
            bui.textwidget(
                edit=self._stats_text,
                text='⚠️  Could not load ratings',
                color=(0.9, 0.4, 0.4),
            )
            return

        ratings = [v for v in data.values()
                   if isinstance(v, (int, float)) and 1 <= v <= 5]
        count = len(ratings)
        avg = sum(ratings) / count if count else 0.0

        bui.textwidget(
            edit=self._stats_text,
            text=f'{avg:.1f} / 5.0  •  {count:,} rating{"s" if count != 1 else ""}',
            color=(1.0, 0.88, 0.3),
        )
        bui.textwidget(
            edit=self._avg_stars_text,
            text=self._avg_star_str(avg),
        )

        # Pre-fill the player's own rating if they've voted before
        if self._account_id:
            key = _firebase_key(self._account_id)
            existing = data.get(key)
            if isinstance(existing, (int, float)) and 1 <= int(existing) <= 5:
                stars = int(existing)
                self._set_stars(stars)
                self._selected_stars = stars
                self._submitted = True
                bui.buttonwidget(
                    edit=self._submit_btn,
                    label='Update Rating',
                    color=(0.18, 0.42, 0.65),
                    textcolor=(1, 1, 1),
                )

    def _on_star_tap(self, stars: int) -> None:
        self._selected_stars = stars
        self._set_stars(stars)
        # Enable submit button
        bui.buttonwidget(
            edit=self._submit_btn,
            label='Update Rating' if self._submitted else 'Submit Rating',
            color=(0.22, 0.52, 0.22),
            textcolor=(1, 1, 1),
        )

    def _set_stars(self, stars: int) -> None:
        """Highlight the first ``stars`` buttons, dim the rest."""
        for i, btn in enumerate(self._star_btns):
            if i < stars:
                bui.buttonwidget(edit=btn,
                                 color=(0.78, 0.58, 0.0),
                                 textcolor=(1.0, 0.88, 0.0))
            else:
                bui.buttonwidget(edit=btn,
                                 color=(0.28, 0.28, 0.28),
                                 textcolor=(0.4, 0.4, 0.4))

    def _submit(self) -> None:
        if not self._selected_stars:
            bui.screenmessage(
                'Tap a star to choose your rating first.',
                color=(1.0, 0.7, 0.2),
            )
            return
        if not self._account_id:
            bui.screenmessage(
                'Sign in to a BombSquad account to rate.',
                color=(1.0, 0.5, 0.2),
            )
            return

        key = _firebase_key(self._account_id)
        path = f'{self._RATINGS_PATH}/{key}.json'
        bui.buttonwidget(
            edit=self._submit_btn,
            label='Submitting…',
            color=(0.3, 0.3, 0.3),
            textcolor=(0.55, 0.55, 0.55),
        )
        _firebase_put(path, self._selected_stars, self._on_submit_done)

    def _on_submit_done(
        self, result: object, error: str | None
    ) -> None:
        """Called on the game thread once Firebase confirms the write."""
        if not (self._root_widget and self._root_widget.exists()):
            return

        if error:
            bui.screenmessage(f'Submit failed: {error}', color=(1, 0.3, 0.3))
            bui.buttonwidget(
                edit=self._submit_btn,
                label='Retry',
                color=(0.65, 0.22, 0.18),
                textcolor=(1, 1, 1),
            )
            return

        self._submitted = True
        bui.buttonwidget(
            edit=self._submit_btn,
            label='✓ Rating saved!',
            color=(0.2, 0.5, 0.2),
            textcolor=(1, 1, 1),
        )
        bui.screenmessage(
            f"Thanks for your {self._selected_stars}★ rating!",
            color=(0.3, 1.0, 0.45),
        )
        # Refresh community stats after our new vote is counted
        _firebase_get(self._RATINGS_PATH + '.json', self._on_data_loaded)

    def _open_issues(self) -> None:
        """Open the plugin's GitHub Issues page in the system browser."""
        try:
            babase.open_url(self._ISSUES_URL)
        except Exception as exc:
            print(f'[FriendManager] Could not open URL: {exc}')

    def _close(self) -> None:
        if self._root_widget and self._root_widget.exists():
            bui.containerwidget(edit=self._root_widget, transition='out_scale')


class FriendHelpWindow(bui.Window):
    """Step-by-step guide for the Friends system, opened from FriendListWindow."""

    def __init__(self, origin_widget: bui.Widget | None = None):
        width, height = 480, 430
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(root_widget=bui.containerwidget(
            size=(width, height),
            transition='in_scale',
            scale=1.5 if uiscale is babase.UIScale.SMALL else 1.15,
            scale_origin_stack_offset=(
                origin_widget.get_screen_space_center()
                if origin_widget else (0, 0)
            ),
        ))

        # ── Title ────────────────────────────────────────────────────────────
        bui.textwidget(
            parent=self._root_widget,
            position=(width / 2, height - 35),
            size=(0, 0),
            text='ℹ️  How to Use Friends',
            h_align='center', v_align='center',
            scale=1.05, color=(0.4, 1.0, 0.4),
        )

        # ── Scrollable content (columnwidget auto-stacks children top→bottom)
        scroll = bui.scrollwidget(
            parent=self._root_widget,
            position=(18, 68),
            size=(width - 36, height - 118),
        )
        col = bui.columnwidget(parent=scroll, border=6, margin=0)

        # Each section: (heading_text, [list of bullet lines])
        sections = [
            (
                '➕  Adding a Friend',
                [
                    '1. Join any online party.',
                    '2. Click a player\'s name in the party list.',
                    '3. Choose  ➕ Add Friend  from the pop-up menu.',
                    '4. Their account ID + every profile name they\'ve',
                    '   used is saved automatically.',
                ],
            ),
            (
                '👤  Viewing a Profile',
                [
                    'Open  Settings → Friends  to see your full list.',
                    'Tap  👤 Profile  on any row to see their details:',
                    'known usernames, date added, last seen time,',
                    'and whether their ID is stable (V2 account).',
                ],
            ),
            (
                '🔔  Join Notifications',
                [
                    'While in a session, the plugin polls the party',
                    'every 5 seconds.  When a friend joins AFTER you',
                    'a toast message and sound play automatically.',
                    'Friends already present when you joined are',
                    'silently set as the baseline — no spam.',
                ],
            ),
            (
                '⚠️  ID Stability Warning',
                [
                    'Players signed into a V2 account get a stable',
                    'persistent ID.  Others get a fallback ID from',
                    'their display name — marked ⚠️ in their profile.',
                    'Unstable IDs may break if they change their name.',
                ],
            ),
            (
                '🗑️  Removing a Friend',
                [
                    'Open their Profile and tap  🗑️ Remove Friend.',
                    'The button asks for a second tap within 3 s to',
                    'confirm — prevents accidental removals.',
                ],
            ),
            (
                '💾  Backup & Transfer',
                [
                    'Friend data is stored in:',
                    '  <mods>/friend_manager_data/friend_list.json',
                    'Copy that folder to any device/install and your',
                    'friends list carries over automatically.',
                ],
            ),
        ]

        cw = width - 60   # content width inside scroll
        for i, (heading, bullets) in enumerate(sections):
            # Gap between sections (skip before first)
            if i > 0:
                bui.textwidget(parent=col, size=(cw, 10), text='')

            # Section heading
            bui.textwidget(
                parent=col,
                size=(cw, 28),
                text=heading,
                h_align='left', v_align='center',
                scale=0.8, color=(0.45, 0.85, 1.0),
            )

            # Bullet lines — one textwidget per line avoids size-guess issues
            for line in bullets:
                bui.textwidget(
                    parent=col,
                    size=(cw, 20),
                    text=line,
                    h_align='left', v_align='center',
                    scale=0.65, color=(0.75, 0.75, 0.75),
                )

        # ── Close button ─────────────────────────────────────────────────────
        ok_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(width / 2 - 130, 18),
            size=(120, 42),
            label='Got it!',
            color=(0.2, 0.55, 0.2),
            textcolor=(1, 1, 1),
            on_activate_call=self._close,
        )
        # Bug report / feature request — opens the plugin-manager issue tracker
        bui.buttonwidget(
            parent=self._root_widget,
            position=(width / 2 + 2, 18),
            size=(230, 42),
            label='🐛  Report a Bug / 💡 Feature',
            color=(0.15, 0.25, 0.42),
            textcolor=(0.65, 0.82, 1.0),
            on_activate_call=self._open_issues,
        )
        bui.containerwidget(
            edit=self._root_widget,
            start_button=ok_btn,
            cancel_button=ok_btn,
        )

    def _open_issues(self) -> None:
        """Open the community plugin-manager issue tracker in the system browser."""
        try:
            babase.open_url(
                'https://github.com/bombsquad-community/plugin-manager/issues'
            )
        except Exception as exc:
            print(f'[FriendManager] Could not open URL: {exc}')

    def _close(self) -> None:
        if self._root_widget and self._root_widget.exists():
            bui.containerwidget(edit=self._root_widget, transition='out_scale')


class FriendListWindow(bui.Window):
    def __init__(self, origin_widget: bui.Widget | None = None):
        self._width = 680
        self._height = 480
        self._origin_widget = origin_widget
        uiscale = bui.app.ui_v1.uiscale

        super().__init__(root_widget=bui.containerwidget(
            size=(self._width, self._height),
            transition='in_scale',
            scale=1.35 if uiscale is babase.UIScale.SMALL else 1.0,
            scale_origin_stack_offset=(
                origin_widget.get_screen_space_center()
                if origin_widget else (0, 0)
            ),
        ))

        # ── Back button ──────────────────────────────────────────────────────
        self._back_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(16, self._height - 65),
            size=(60, 55),
            label=bui.charstr(bui.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self._back,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=self._back_btn)

        # ── Title — centred in the space between the back btn and toolbar ───────
        # The available horizontal space is x=76..482 (width-198).  We anchor
        # at x=260 (middle of that zone) and cap width at 300 px so the count
        # suffix never bleeds into the toolbar buttons even at large font sizes.
        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(279, self._height - 36),
            size=(0, 0),
            text='👥  Friends',
            h_align='center', v_align='center',
            scale=1.1, color=(0.4, 1.0, 0.4),
            maxwidth=300,
        )

        # ── Toolbar row (right side of header) ───────────────────────────────
        # Rate button — opens the Firebase-backed 5-star rating popup
        self._rate_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width - 198, self._height - 63),
            size=(55, 48),
            label='⭐',
            color=(0.4, 0.32, 0.06),
            textcolor=(1, 1, 1),
            on_activate_call=self._show_rating,
        )
        # Refresh button — re-checks roster and online status on demand
        self._refresh_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width - 135, self._height - 63),
            size=(55, 48),
            label='🔄',
            color=(0.2, 0.4, 0.2),
            textcolor=(1, 1, 1),
            on_activate_call=self._refresh,
        )
        # Help button — opens FriendHelpWindow
        self._help_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width - 72, self._height - 63),
            size=(55, 48),
            label='ℹ️',
            color=(0.2, 0.35, 0.5),
            textcolor=(1, 1, 1),
            on_activate_call=self._show_help,
        )

        # ── Scrollable friend list ────────────────────────────────────────────
        self._scroll = bui.scrollwidget(
            parent=self._root_widget,
            position=(24, 44),
            size=(self._width - 48, self._height - 114),
        )
        self._column = bui.columnwidget(parent=self._scroll)
        self._refresh()

    # -------------------------------------------------------------------------

    def _refresh(self) -> None:
        """Rebuild the friend list, update title counts, sort online first."""
        for child in self._column.get_children():
            child.delete()

        total = len(FriendManager.friends)
        online_ids = {_resolve_player(e)[0] for e in _safe_roster()}
        online = sum(1 for pid in FriendManager.friends if pid in online_ids)

        # Live title — kept compact so it never overflows into the toolbar.
        # Format: "Friends (58)"  or  "Friends ● 1/58"
        if self._title_text and self._title_text.exists():
            if total == 0:
                title = '👥  Friends'
            elif online:
                title = f'👥  Friends  ●  {online}/{total}'
            else:
                title = f'👥  Friends  ({total})'
            bui.textwidget(edit=self._title_text, text=title)

        if not FriendManager.friends:
            self._draw_empty_state()
            return

        # Online friends first, then alphabetical by display name
        sorted_friends = sorted(
            FriendManager.friends.items(),
            key=lambda kv: (
                kv[0] not in online_ids,
                kv[1].get('v2_name', '').lower(),
            ),
        )

        row_w = self._width - 60   # row width inside scroll
        for pb_id, data in sorted_friends:
            is_online = pb_id in online_ids
            is_stable = data.get('stable_id', True)
            name = data.get('v2_name', 'Unknown')
            warn = '' if is_stable else ' ⚠️'

            row = bui.containerwidget(
                parent=self._column,
                size=(row_w, 64),
                background=True,
                color=(0.15, 0.32, 0.15) if is_online else (0.18, 0.18, 0.18),
            )

            # Name (+ unstable-ID warning badge).
            # size=(0,0) + v_align='center' makes position the text's centre
            # point, avoiding the bounding-box offset that pushed text to the
            # top of the row when size height was non-zero.
            bui.textwidget(
                parent=row,
                position=(14, 43),
                size=(0, 0),
                text=name + warn,
                scale=0.88,
                h_align='left', v_align='center',
                color=(1, 1, 0.85) if is_online else (1, 1, 1),
                maxwidth=row_w - 250,
            )

            # Status line — centred at y=19, leaving clean space below name
            status = ('🟢  In party with you'
                      if is_online else
                      f"Last seen: {_format_relative_time(data.get('last_seen'))}")
            bui.textwidget(
                parent=row,
                position=(14, 19),
                size=(0, 0),
                text=status,
                scale=0.52,
                h_align='left', v_align='center',
                color=(0.35, 1.0, 0.35) if is_online else (0.5, 0.5, 0.5),
            )

            # Profile button
            bui.buttonwidget(
                parent=row,
                position=(row_w - 232, 14),
                size=(108, 36),
                label='👤  Profile',
                color=(0.18, 0.45, 0.72),
                textcolor=(1, 1, 1),
                on_activate_call=babase.CallPartial(FriendProfileWindow, pb_id),
            )

            # Quick-remove button (arms on first tap, fires on second)
            rm_btn: list[bui.Widget] = []    # mutable cell for the closure
            armed:  list[bool] = [False]
            timer:  list[object] = [None]

            def _on_remove(
                _pid: str = pb_id,
                _name: str = name,
                _btn: list = rm_btn,
                _armed: list = armed,
                _timer: list = timer,
            ) -> None:
                if not _armed[0]:
                    _armed[0] = True
                    if _btn and _btn[0].exists():
                        bui.buttonwidget(edit=_btn[0], label='✓ Sure?',
                                         color=(0.85, 0.2, 0.2))

                    def _disarm() -> None:
                        _armed[0] = False
                        if _btn and _btn[0].exists():
                            bui.buttonwidget(edit=_btn[0], label='🗑️',
                                             color=(0.55, 0.15, 0.15))
                    _timer[0] = babase.AppTimer(3.0, babase.CallStrict(_disarm))
                else:
                    FriendManager.remove(_pid)
                    bui.screenmessage(f'🗑️  {_name} removed.', color=(1, 0.4, 0.4))
                    self._refresh()

            rb = bui.buttonwidget(
                parent=row,
                position=(row_w - 116, 14),
                size=(100, 36),
                label='🗑️',
                color=(0.55, 0.15, 0.15),
                textcolor=(1, 1, 1),
                on_activate_call=_on_remove,
            )
            rm_btn.append(rb)

    def _draw_empty_state(self) -> None:
        """Shown when no friends have been added yet."""
        # Use columnwidget so each text line stacks cleanly
        col = bui.columnwidget(parent=self._column, border=20, margin=0)

        bui.textwidget(
            parent=col,
            size=(self._width - 110, 34),
            text='No friends added yet!',
            h_align='center', v_align='center',
            scale=0.95, color=(0.65, 0.65, 0.65),
        )
        bui.textwidget(parent=col, size=(self._width - 110, 14), text='')

        steps = [
            '  How to add your first friend:',
            '',
            '  1.  Join any online party.',
            '  2.  Click a player\'s name in the party list.',
            '  3.  Choose  ➕ Add Friend  from the menu.',
            '',
            '  Their account ID and all profile names they\'ve used',
            '  are saved automatically.  You\'ll be notified the next',
            '  time they join your party.',
            '',
            '  Tap  ℹ️  (top-right) for the full guide.',
        ]
        for line in steps:
            bui.textwidget(
                parent=col,
                size=(self._width - 110, 22),
                text=line,
                h_align='left', v_align='center',
                scale=0.7,
                color=(0.45, 0.45, 0.45) if not line.strip() else (0.6, 0.6, 0.6),
            )

    def _show_rating(self) -> None:
        FriendManagerRatingWindow(origin_widget=self._rate_btn)

    def _show_help(self) -> None:
        FriendHelpWindow(origin_widget=self._help_btn)

    def _back(self) -> None:
        if self._root_widget and self._root_widget.exists():
            bui.containerwidget(edit=self._root_widget, transition='out_scale')


# ----------------------------------------------------------------------------
# Background polling: keeps friend data fresh + notifies when a friend joins
# ----------------------------------------------------------------------------

_previously_online_friend_ids: set[str] = set()

# Tracks whether we have taken a "baseline" snapshot of the current party.
# Starts False; becomes True after the first roster check that finds any
# players (including non-friends), so that joining a full party mid-session
# never spams "X joined" for people who were already there.
_baseline_taken: bool = False


def _notify(message: str, color: tuple = (0.3, 0.9, 1.0)) -> None:
    """Show a screen-message toast and play a soft notification sound.

    Wraps ``bui.screenmessage`` so all friend notifications are styled
    consistently and sound failures never surface as uncaught exceptions.
    """
    bui.screenmessage(message, color=color)
    try:
        bui.getsound('shieldUp').play()
    except Exception:
        pass


def auto_update_friends() -> None:
    """Poll the current party roster; update friend data and fire join toasts.

    Called every 5 seconds by the plugin's AppTimer.  Safe to call at any
    time — silently returns when there is no active session / roster.

    Key ID-migration logic
    ----------------------
    Existing friends may have been stored under their *display name* (an
    unstable key) because ``account_id`` was not available when they were
    first added.  Whenever we now see a player with a stable ``pb-UUID``
    account ID we check whether they are already present under an unstable
    name key and — if so — transparently migrate that entry to the stable
    key.  This resolves the "rename = new friend" bug for all 58 existing
    friends the moment each of them next joins a session.
    """
    global _previously_online_friend_ids, _baseline_taken

    roster = _safe_roster()

    # If there is no roster we still want to mark the baseline as taken the
    # moment the timer first fires, so that transitioning from "lobby" to
    # "in a party" doesn't trigger spurious notifications for friends who
    # were already there before the session loaded.
    if not roster:
        _baseline_taken = True
        return

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    current_online_friend_ids: set[str] = set()
    updated = False

    for entry in roster:
        try:
            pb_id, v2_name, profiles, is_stable = _resolve_player(entry)
        except Exception:
            continue

        # ── ID-migration: old name-keyed → new stable account-ID key ──────────
        # When a stable pb_id is resolved for a player we don't yet have under
        # that key, search unstable entries whose stored name or known profiles
        # overlap with this player's current display name.  If we find a match
        # we atomically rename the dict key so future lookups use the stable ID,
        # the ⚠️ badge disappears, and renames no longer create duplicates.
        if is_stable and pb_id not in FriendManager.friends:
            for old_key in list(FriendManager.friends.keys()):
                old_data = FriendManager.friends.get(old_key, {})
                if old_data.get('stable_id', True):
                    continue  # already stable — don't touch
                # Match if the old key, the stored v2_name, or any known
                # profile equals the player's current display string.
                old_names = {
                    old_key,
                    old_data.get('v2_name', ''),
                    *old_data.get('profiles', []),
                }
                if v2_name in old_names:
                    migrated = FriendManager.friends.pop(old_key)
                    migrated['stable_id'] = True
                    migrated['v2_name'] = v2_name
                    FriendManager.friends[pb_id] = migrated
                    FriendManager.save()
                    updated = False  # already saved above
                    _notify(
                        f'🔄  {v2_name} — ID updated to stable',
                        color=(0.55, 0.85, 1.0),
                    )
                    break

        if pb_id not in FriendManager.friends:
            continue

        current_online_friend_ids.add(pb_id)
        friend = FriendManager.friends[pb_id]

        # Keep the stored display name and profile list current.
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

        # Fire a notification only for friends who *newly* joined since
        # the last check AND after the baseline snapshot has been taken.
        if _baseline_taken and pb_id not in _previously_online_friend_ids:
            display = v2_name or friend.get('v2_name', 'A friend')
            _notify(f'👋  {display} just joined the party!', color=(0.3, 0.9, 1.0))

    _previously_online_friend_ids = current_online_friend_ids
    _baseline_taken = True   # snapshot taken — notifications now active

    if updated:
        FriendManager.save()


# ----------------------------------------------------------------------------
# Monkey patches
# ----------------------------------------------------------------------------

def apply_friend_manager_patches() -> None:
    """Apply all monkey-patches needed by the friend manager.

    Patches applied
    ---------------
    1. ``NewAllSettingsWindow.__init__``
         Adds a "Friends" button as the 3rd column in row 2, alongside
         Advanced and Plugin Manager.  To make room, every row-2 widget
         created by the original init is shifted left by ``x_dif`` so that
         row 2 aligns with the row-1 column grid.  This is done by
         temporarily intercepting ``bui.buttonwidget`` / ``bui.textwidget``
         / ``bui.imagewidget`` during ``_old_init`` — no changes to
         ``plugin_manager.py`` are required.  When ``friend_manager`` is
         absent the settings layout is completely unchanged.
    2. ``NewAllSettingsWindow._save_state`` / ``_restore_state``
         Teach the window to remember when "Friends" is the selected button
         so the selection is preserved across close/re-open cycles.
    3. ``PartyWindow._on_party_member_press``
         Stores the clicked ``client_id`` so the popup menu can reference it.
    4. ``PopupMenuWindow.__init__``
         Injects "Add Friend" and "View Profile" entries into party-member
         context menus.
    """
    import bauiv1lib.settings.allsettings as _allsettings

    # At runtime plugin_manager.py has already replaced AllSettingsWindow
    # with NewAllSettingsWindow, so this reference targets the live class.
    _target_cls = _allsettings.AllSettingsWindow
    _old_init = _target_cls.__init__
    _old_save = _target_cls._save_state
    _old_restore = _target_cls._restore_state

    # ------------------------------------------------------------------
    # 1. Patch __init__ — shift row-2 buttons left, add Friends in col 3
    # ------------------------------------------------------------------
    def _new_allsettings_init(
        self, transition: str = 'in_right', origin_widget: bui.Widget | None = None
    ) -> None:
        # Mirror the layout constants used by NewAllSettingsWindow so that
        # the Friends button and the repositioned row-2 buttons align to
        # the same column grid as row 1.
        uiscale = bui.app.ui_v1.uiscale
        small = uiscale is babase.UIScale.SMALL
        height = 490
        x_inset = 125 if small else 105
        basew = 280 if small else 230
        baseh = 170

        x_offs = x_inset + (105 if small else 72) - basew
        x_dif = (basew - 7) / 2   # 136.5 (SMALL) or 111.5 (normal)
        v_row1 = height - 265       # 225 — upper boundary of row 2

        # Column x-positions for row 2 after the shift (match row 1):
        #   col1 ≈  86.5 / 58.5   (Advanced)
        #   col2 ≈ 359.5 / 281.5  (Plugin Manager)
        #   col3 ≈ 632.5 / 504.5  (Friends — new)
        col1 = x_offs + 1 * (basew - 7) - x_dif
        col2 = x_offs + 2 * (basew - 7) - x_dif
        col3 = x_offs + 3 * (basew - 7) - x_dif
        v_row2 = v_row1 - (baseh - 5)  # 60

        # Track every widget created in row 2 (y < v_row1 = 225) so we can
        # shift them after _old_init finishes.  Widgets from super().__init__
        # that are later deleted will have widget.exists() == False and are
        # skipped harmlessly during the repositioning pass.
        _row2: list[tuple[str, bui.Widget, float, float]] = []
        _bw0 = bui.buttonwidget
        _tw0 = bui.textwidget
        _iw0 = bui.imagewidget

        def _bw(*a: object, **kw: object) -> bui.Widget:
            w = _bw0(*a, **kw)
            pos = kw.get('position')
            if pos is not None and 'edit' not in kw and pos[1] < v_row1:
                _row2.append(('button', w, pos[0], pos[1]))
            return w

        def _tw(*a: object, **kw: object) -> bui.Widget:
            w = _tw0(*a, **kw)
            pos = kw.get('position')
            if (pos is not None
                    and 'edit' not in kw
                    and 'query' not in kw
                    and pos[1] < v_row1):
                _row2.append(('text', w, pos[0], pos[1]))
            return w

        def _iw(*a: object, **kw: object) -> bui.Widget:
            w = _iw0(*a, **kw)
            pos = kw.get('position')
            if pos is not None and 'edit' not in kw and pos[1] < v_row1:
                _row2.append(('image', w, pos[0], pos[1]))
            return w

        bui.buttonwidget = _bw  # type: ignore[assignment]
        bui.textwidget = _tw  # type: ignore[assignment]
        bui.imagewidget = _iw  # type: ignore[assignment]
        try:
            _old_init(self, transition, origin_widget)
        finally:
            # Restore originals even if _old_init raises.
            bui.buttonwidget = _bw0  # type: ignore[assignment]
            bui.textwidget = _tw0  # type: ignore[assignment]
            bui.imagewidget = _iw0  # type: ignore[assignment]

        # Shift every live row-2 widget left by x_dif so they align with
        # the row-1 column grid, freeing a clean 3rd slot for Friends.
        for kind, widget, old_x, old_y in _row2:
            if not widget.exists():
                continue
            new_pos = (old_x - x_dif, old_y)
            try:
                if kind == 'button':
                    bui.buttonwidget(edit=widget, position=new_pos)
                elif kind == 'text':
                    bui.textwidget(edit=widget, position=new_pos)
                else:
                    bui.imagewidget(edit=widget, position=new_pos)
            except Exception as exc:
                print(f'[FriendManager] widget shift failed ({kind}): {exc}')

        # After the shift, Plugin Manager is directly below Graphics (col2),
        # so fix its gamepad up-navigation target accordingly.
        try:
            pmb = getattr(self, '_plugman_button', None)
            if pmb is not None and pmb.exists():
                bui.buttonwidget(edit=pmb, up_widget=self._graphics_button)
        except Exception:
            pass

        # --- Friends button (col 3, row 2) ---------------------------------
        # Follows the same structure as Advanced and Plugin Manager above:
        # a square button, a _b_title-style label, and a 120×120 icon.
        fb = self._friends_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(col3, v_row2),
            size=(basew, baseh),
            button_type='square',
            label='',
            up_widget=self._audio_button,
            on_activate_call=self._do_friends,
        )

        # Label — identical parameters to _b_title in NewAllSettingsWindow.
        bui.textwidget(
            parent=self._root_widget,
            text=bui.Lstr(value='Friends'),
            position=(col3 + basew * 0.47, v_row2 + baseh * 0.22),
            maxwidth=basew * 0.7,
            size=(0, 0),
            h_align='center',
            v_align='center',
            draw_controller=fb,
            color=(0.7, 0.9, 0.7, 1.0),
        )

        # Icon — 'achievementSharingIsCaring' has full-colour opaque artwork
        # so no colour tint is applied (same approach as controllerIcon and
        # graphicsIcon in NewAllSettingsWindow).
        imgw = imgh = 120
        bui.imagewidget(
            parent=self._root_widget,
            position=(col3 + basew * 0.49 - imgw * 0.5 + 5, v_row2 + 35),
            size=(imgw, imgh),
            texture=bui.gettexture('usersButton'),
            draw_controller=fb,
        )

    _target_cls.__init__ = _new_allsettings_init

    # ------------------------------------------------------------------
    # Navigation handler for the Friends button
    # ------------------------------------------------------------------
    def _do_friends(self) -> None:
        if not self.main_window_has_control():
            return
        FriendListWindow(origin_widget=self._friends_button)

    _target_cls._do_friends = _do_friends

    # ------------------------------------------------------------------
    # _save_state — remember Friends selection across close/re-open
    # ------------------------------------------------------------------
    def _new_save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            fb = getattr(self, '_friends_button', None)
            if fb is not None and sel == fb:
                assert bui.app.classic is not None
                bui.app.ui_v1.window_states[type(self)] = {'sel_name': 'Friends'}
                return
        except Exception:
            pass
        _old_save(self)

    _target_cls._save_state = _new_save_state

    # ------------------------------------------------------------------
    # _restore_state — restore Friends selection on re-open
    # ------------------------------------------------------------------
    def _new_restore_state(self) -> None:
        try:
            assert bui.app.classic is not None
            sel_name = bui.app.ui_v1.window_states.get(type(self), {}).get('sel_name')
            fb = getattr(self, '_friends_button', None)
            if sel_name == 'Friends' and fb is not None:
                bui.containerwidget(edit=self._root_widget, selected_child=fb)
                return
        except Exception:
            pass
        _old_restore(self)

    _target_cls._restore_state = _new_restore_state

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
                                        _notify(
                                            f'✅  {p_v2} added to your friends!',
                                            color=(0.2, 1.0, 0.2),
                                        )
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

    def delayed_startup(self) -> None:
        try:
            apply_friend_manager_patches()
        except Exception as exc:
            # Patching failed — log and bail out.  The Friends button won't
            # appear in Settings, but no other game functionality is harmed.
            print(f'[FriendManager] Patch error: {exc}')
            return

        # Start the background poller (every 5 s).  Storing it on self keeps
        # the AppTimer alive for the lifetime of the plugin instance.
        self._timer = babase.AppTimer(
            5.0, babase.CallStrict(auto_update_friends), repeat=True,
        )
