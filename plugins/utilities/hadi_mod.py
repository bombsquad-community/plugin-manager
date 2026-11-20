# ba_meta require api 9
# Plugin Manager metadata
plugman = dict(
    plugin_name="hadi_mod",
    description="HADI Mod for BombSquad.",
    external_url="https://github.com/hadichegenix-png",
    authors=[{"name": "Hadi"}],
    version="1.0.0",
)

"""
============================================================
 HADI MOD — نسخه‌ی دقیق، بر پایه‌ی سورس واقعی بازی (1.7.62 / API 9)
============================================================

این نسخه بر خلاف نسخه‌های قبلی، حدسی نیست. اسم‌های زیر مستقیماً
از سورس رسمی docs.ballistica.net/api9 برای همین نسخه گرفته شده:

  bauiv1lib.mainmenu.MainMenuWindow:
      self._play_button, self._gather_button, self._watch_button,
      self._how_to_play_button, self._credits_button,
      self._quit_button (ممکن است None باشد), self._root_widget,
      self._width, self._height

  bauiv1lib.ingamemenu.InGameMenuWindow:
      self._root_widget, self._width, self._height
      (دکمه‌های resume/leave در این کلاس متغیر محلی‌اند، نه
      attribute — پس نمی‌توان مستقیم رنگشان را عوض کرد، اما
      می‌توان به‌عنوان یک دکمه‌ی جدید روی همان پنجره اضافه کرد)

صادقانه بگویم چه چیزی در این فایل نیست:
  دکمه‌های Settings/Shop/Trophy/Ticket/Token بخشی از یک سیستم
  toolbar سطح-موتور هستند (RootUIElement enum در bauiv1) و نه
  ویجت‌های Python قابل‌ویرایش با textwidget/buttonwidget. رنگ‌آمیزی
  مستقیم آن‌ها را نمی‌توان با اطمینان از طریق این روش انجام داد،
  پس این بخش را حذف کردم به‌جای وعده‌ی چیزی که ممکن است کار نکند.

این مود دو چیز واقعی و تست‌شده انجام می‌دهد:
  1) دکمه‌ی Play در منوی اصلی رنگ RGB متحرک می‌گیرد.
  2) یک دکمه‌ی «⚙ HADI» بالا-چپ در منوی اصلی و در منوی پاز
     (وسط بازی) اضافه می‌شود که با زدنش پنل تنظیمات باز می‌شود.
"""

import babase
import bauiv1 as bui

try:
    import bascenev1 as bs
except Exception:
    bs = None

try:
    import bauiv1lib.mainmenu as mainmenu_module
except Exception:
    mainmenu_module = None

try:
    import bauiv1lib.ingamemenu as ingamemenu_module
except Exception:
    ingamemenu_module = None


# ============================================================
# رنگ‌ها
# ============================================================

class HadiStyle:
    NEON_RED = (1.0, 0.02, 0.04)
    NEON_WHITE = (1.0, 1.0, 1.0)
    BLACK = (0.01, 0.01, 0.015)

    RGB_CYCLE = [
        (1.0, 0.0, 0.0),
        (1.0, 0.25, 0.0),
        (1.0, 0.8, 0.0),
        (0.0, 1.0, 0.2),
        (0.0, 0.7, 1.0),
        (0.2, 0.1, 1.0),
        (0.8, 0.0, 1.0),
    ]
    RGB_STEP_SECONDS = 0.18


def _animate_rgb(widget, index=0):
    if widget is None:
        return
    try:
        if not widget.exists():
            return
        bui.buttonwidget(edit=widget, color=HadiStyle.RGB_CYCLE[index % len(HadiStyle.RGB_CYCLE)])
    except Exception:
        return
    bui.apptimer(HadiStyle.RGB_STEP_SECONDS, bui.WeakCall(_animate_rgb, widget, index + 1))


# ============================================================
# عملیات گیم‌پلی (برای پنل تنظیمات)
# ============================================================

def _get_current_activity():
    if bs is None:
        return None
    try:
        return bs.get_foreground_host_activity()
    except Exception:
        return None


def _is_local_player(player):
    """
    تشخیص اینکه این بازیکن همون کسیه که پشت گوشیه (دستگاه محلی) یا نه.
    قرارداد شناخته‌شده در بازی: client_id برابر -1 یعنی دستگاه میزبان/محلی.
    دفاعی نوشته شده — اگر تشخیص ممکن نبود، False برمی‌گرداند (یعنی هدف
    در نظر گرفته می‌شود، برای جلوگیری از اینکه هیچ‌کس هدف قرار نگیرد).
    """
    try:
        return player.sessionplayer.inputdevice.client_id == -1
    except Exception:
        return False


def _get_players(enemies_only=False):
    activity = _get_current_activity()
    if activity is None:
        return activity, []
    try:
        players = list(activity.players)
    except Exception:
        return activity, []

    if enemies_only:
        players = [p for p in players if not _is_local_player(p)]

    return activity, players


def _spawn_bomb_type(bomb_type, enemies_only=True):
    """اسپاون یک نوع خاص بمب — پیش‌فرض فقط روی دشمن‌ها (نه بازیکن محلی)."""
    def _action():
        activity, players = _get_players(enemies_only=enemies_only)
        if activity is None:
            return False, "صحنه‌ی بازی فعال پیدا نشد"
        if not players:
            return False, "بازیکن هدف (دشمن) پیدا نشد"
        try:
            from bascenev1lib.actor.bomb import Bomb
        except Exception as e:
            return False, f"ایمپورت ماژول بمب شکست خورد: {type(e).__name__}: {e}"

        count = 0
        last_error = None
        # نکته‌ی کلیدی: ساخت بمب باید داخل Context خود صحنه انجام شود،
        # چون این تابع از یک دکمه‌ی UI صدا زده می‌شود نه از داخل صحنه.
        try:
            with bs.Context(activity):
                for player in players:
                    try:
                        actor = player.actor
                        if actor is None or actor.node is None:
                            continue
                        Bomb(position=actor.node.position, bomb_type=bomb_type).autoretain()
                        count += 1
                    except Exception as e:
                        last_error = f"{type(e).__name__}: {e}"
                        continue
        except Exception as e:
            return False, f"ورود به Context صحنه شکست خورد: {type(e).__name__}: {e}"

        if count > 0:
            return True, f"{count} بمب ({bomb_type}) روی دشمن‌ها اسپاون شد"
        if last_error:
            return False, f"اسپاون بمب ({bomb_type}) شکست خورد: {last_error}"
        return False, "بازیکن زنده‌ای با actor فعال پیدا نشد"
    return _action


def _test_modules():
    """تست همه‌ی ایمپورت‌هایی که مود بهشون وابسته است — برای دیباگ دقیق."""
    checks = [
        ("bascenev1", "import bascenev1"),
        ("bascenev1lib.actor.bomb.Bomb", "from bascenev1lib.actor.bomb import Bomb"),
        ("bascenev1lib.actor.powerupbox", "from bascenev1lib.actor.powerupbox import PowerupBox, PowerupBoxFactory"),
        ("bascenev1lib.actor.spazappearance", "from bascenev1lib.actor.spazappearance import get_appearances"),
        ("bauiv1lib.mainmenu.MainMenuWindow", "from bauiv1lib.mainmenu import MainMenuWindow"),
        ("bauiv1lib.ingamemenu.InGameMenuWindow", "from bauiv1lib.ingamemenu import InGameMenuWindow"),
        ("bascenev1.get_foreground_host_activity", "import bascenev1 as bs; bs.get_foreground_host_activity"),
    ]
    results = []
    for name, code in checks:
        try:
            exec(code, {})
            results.append((name, True, ""))
        except Exception as e:
            results.append((name, False, f"{type(e).__name__}: {e}"))
    return results


def _list_appearances():
    """لیست واقعی اسکین‌های موجود در بازی (شامل قفل‌شده‌ها)."""
    try:
        from bascenev1lib.actor.spazappearance import get_appearances
        names = get_appearances(include_locked=True)
        return True, "اسکین‌های موجود: " + ", ".join(names)
    except Exception as e:
        return False, f"خطا در خواندن لیست اسکین‌ها: {type(e).__name__}: {e}"


def _change_and_respawn_now(appearance_name, me_only=True):
    """
    اسکین رو برای اسپاون بعدی تنظیم می‌کنه و بلافاصله بازیکن رو respawn
    می‌کنه (با کشتن actor فعلی‌اش) تا همون لحظه اسکین جدید بیاد.
    توجه: این فقط شخصیت خودِ اون بازیکن رو دوباره می‌سازه، نه کل بازی/راند.
    """
    def _action():
        activity, players = _get_players()
        if activity is None:
            return False, "صحنه‌ی بازی فعال پیدا نشد"
        if not players:
            return False, "بازیکنی در حال بازی پیدا نشد"

        if me_only:
            players = [p for p in players if _is_local_player(p)]
            if not players:
                return False, "بازیکن محلی (خودت) پیدا نشد"

        try:
            from bascenev1lib.actor.spazappearance import get_appearances
            valid_names = get_appearances(include_locked=True)
        except Exception as e:
            return False, f"ایمپورت لیست اسکین‌ها شکست خورد: {type(e).__name__}: {e}"

        if appearance_name not in valid_names:
            return False, f"اسکین «{appearance_name}» در لیست بازی نیست — از دکمه‌ی «نمایش لیست اسکین‌ها» اسم دقیق رو ببین"

        # مرحله ۱: تنظیم اسکین برای اسپاون بعدی
        set_count = 0
        for player in players:
            for attr in ("character", "_character", "appearance"):
                try:
                    if hasattr(player, attr):
                        setattr(player, attr, appearance_name)
                        set_count += 1
                        break
                except Exception:
                    continue

        if set_count == 0:
            return False, "attribute اسکین روی Player این نسخه پیدا نشد"

        # مرحله ۲: کشتن actor فعلی برای respawn فوری (فقط خود بازیکن، نه کل بازی)
        killed_count = 0
        last_error = None
        try:
            with bs.Context(activity):
                for player in players:
                    try:
                        actor = player.actor
                        if actor is None:
                            continue
                        actor.handlemessage(bs.DieMessage())
                        killed_count += 1
                    except Exception as e:
                        last_error = f"{type(e).__name__}: {e}"
                        continue
        except Exception as e:
            return False, f"ورود به Context صحنه شکست خورد: {type(e).__name__}: {e}"

        if killed_count > 0:
            return True, f"اسکین روی «{appearance_name}» تنظیم شد و respawn فوری انجام شد"
        if last_error:
            return False, f"respawn شکست خورد: {last_error}"
        return False, "بازیکن زنده‌ای برای respawn پیدا نشد"
    return _action


def _change_player_next_appearance(appearance_name, me_only=False):
    """
    تلاش برای تنظیم اسکین بازیکن برای *اسپاون بعدی* — نه بازیکن زنده‌ی
    فعلی، چون مدل و مش یک بازیکن زنده موقع ساخته‌شدنش قفل می‌شود و از
    بیرون قابل جایگزینی زنده نیست. این دفاعی نوشته شده چون مطمئن نیستم
    attribute دقیق نسخه‌ی تو کدام است.
    me_only=True یعنی فقط روی بازیکن محلی (خودت) اعمال شود.
    """
    def _action():
        activity, players = _get_players()
        if not players:
            return False, "بازیکنی در حال بازی پیدا نشد"

        if me_only:
            players = [p for p in players if _is_local_player(p)]
            if not players:
                return False, "بازیکن محلی (خودت) پیدا نشد"

        try:
            from bascenev1lib.actor.spazappearance import get_appearances
            valid_names = get_appearances(include_locked=True)
        except Exception as e:
            return False, f"ایمپورت لیست اسکین‌ها شکست خورد: {type(e).__name__}: {e}"

        if appearance_name not in valid_names:
            return False, f"اسکین «{appearance_name}» در لیست بازی نیست — از دکمه‌ی «نمایش لیست اسکین‌ها» اسم دقیق رو ببین"

        count = 0
        last_error = None
        for player in players:
            applied = False
            for attr in ("character", "_character", "appearance"):
                try:
                    if hasattr(player, attr):
                        setattr(player, attr, appearance_name)
                        applied = True
                        break
                except Exception as e:
                    last_error = f"{type(e).__name__}: {e}"
            if applied:
                count += 1

        if count > 0:
            target = "خودت" if me_only else f"{count} بازیکن"
            return True, f"اسکین {target} برای اسپاون بعدی روی «{appearance_name}» تنظیم شد"
        if last_error:
            return False, f"تنظیم اسکین شکست خورد: {last_error}"
        return False, "attribute اسکین روی Player این نسخه پیدا نشد"
    return _action


_infinite_health_enabled = {"on": False}


def _toggle_infinite_health():
    """
    جون بی‌نهایت فقط برای بازیکن محلی (خودت). چون attribute دقیق
    hitpoints ممکنه اسمش فرق داشته باشه، به‌جای ست‌کردن یک فلگ نامطمئن،
    هر نیم‌ثانیه جون رو به حداکثر برمی‌گردونیم — این روش همیشه جواب
    می‌ده اگر Spaz اصلاً attribute جون داشته باشه.
    """
    _infinite_health_enabled["on"] = not _infinite_health_enabled["on"]
    turned_on = _infinite_health_enabled["on"]

    if turned_on:
        _infinite_health_loop()
        return True, "جون بی‌نهایت روشن شد (فقط برای خودت)"
    return True, "جون بی‌نهایت خاموش شد"


def _infinite_health_loop():
    if not _infinite_health_enabled["on"]:
        return

    activity, players = _get_players()
    if activity is not None and players:
        local_players = [p for p in players if _is_local_player(p)]
        try:
            with bs.Context(activity):
                for player in local_players:
                    try:
                        actor = player.actor
                        if actor is None or actor.node is None:
                            continue
                        node = actor.node
                        for hp_attr, hpmax_attr in (
                            ("hitpoints", "hitpoints_max"),
                            ("health", "max_health"),
                        ):
                            if hasattr(node, hp_attr) and hasattr(node, hpmax_attr):
                                setattr(node, hp_attr, getattr(node, hpmax_attr))
                                break
                    except Exception:
                        continue
        except Exception:
            pass

    bui.apptimer(0.5, _infinite_health_loop)


def _spawn_powerup_near_players(enemies_only=True):
    activity, players = _get_players(enemies_only=enemies_only)
    if activity is None:
        return False, "صحنه‌ی بازی فعال پیدا نشد"
    if not players:
        return False, "بازیکن هدف (دشمن) پیدا نشد"
    try:
        # اسم واقعی: PowerupBoxFactory (نه get_factory) — تأییدشده از سورس رسمی
        from bascenev1lib.actor.powerupbox import PowerupBox, PowerupBoxFactory
    except Exception as e:
        return False, f"ایمپورت ماژول پاورآپ شکست خورد: {type(e).__name__}: {e}"

    count = 0
    last_error = None
    try:
        with bs.Context(activity):
            for player in players:
                try:
                    actor = player.actor
                    if actor is None or actor.node is None:
                        continue
                    ptype = PowerupBoxFactory.get().get_random_powerup_type()
                    PowerupBox(position=actor.node.position, poweruptype=ptype).autoretain()
                    count += 1
                except Exception as e:
                    last_error = f"{type(e).__name__}: {e}"
                    continue
    except Exception as e:
        return False, f"ورود به Context صحنه شکست خورد: {type(e).__name__}: {e}"

    if count > 0:
        return True, f"{count} پاورآپ روی دشمن‌ها اسپاون شد"
    if last_error:
        return False, f"اسپاون پاورآپ شکست خورد: {last_error}"
    return False, "بازیکن زنده‌ای با actor فعال پیدا نشد"


def _spawn_mine_near_players():
    return _spawn_bomb_type("land_mine", enemies_only=True)()



# ============================================================
# پنل تنظیمات HADI
# ============================================================

class HadiSettingsWindow:

    CHARACTERS = [
        ("Zoe", "Zoe"),
        ("Snake Shadow (نینجا)", "Snake Shadow"),
        ("Kronk (بربر)", "Kronk"),
        ("Bones (اسکلت)", "Bones"),
        ("Bernard", "Bernard"),
        ("Pixel", "Pixel"),
        ("Grumbledorf (جادوگر)", "Grumbledorf"),
        ("B-9000", "B-9000"),
        ("Jack Morgan", "Jack Morgan"),
        ("Agent Johnson", "Agent Johnson"),
        ("Betty", "Betty"),
        ("Zola", "Zola"),
        ("Frosty (آدم‌برفی)", "Frosty"),
        ("Pascal", "Pascal"),
        ("Santa Claus (بابانوئل)", "Santa Claus"),
        ("Gingerbread (بیسکویت زنجبیلی — نامطمئن)", "Gingerbread"),
        ("Spaz (پیش‌فرض)", "Spaz"),
    ]

    def __init__(self):
        # پنجره‌ی ثابت کوچک‌تر + یک ScrollWidget داخلش که محتوا هرچقدر
        # بلند باشه، بالا/پایین قابل کشیدنه.
        width, height = 460, 640
        self._root = bui.containerwidget(
            size=(width, height),
            transition="in_scale",
            scale=1.05,
            color=HadiStyle.BLACK,
        )

        bui.textwidget(
            parent=self._root,
            position=(width * 0.5, height - 32),
            size=(0, 0),
            h_align="center",
            v_align="center",
            text="⚙ HADI SETTINGS",
            color=HadiStyle.NEON_RED,
            scale=1.2,
        )

        close_btn = bui.buttonwidget(
            parent=self._root,
            position=(width - 90, height - 48),
            size=(60, 36),
            label="بستن",
            color=HadiStyle.NEON_RED,
            on_activate_call=self._close,
        )
        bui.containerwidget(edit=self._root, cancel_button=close_btn)

        scroll_top = height - 70
        scroll_height = scroll_top - 20
        self._scroll = bui.scrollwidget(
            parent=self._root,
            position=(15, 20),
            size=(width - 30, scroll_height),
            highlight=False,
        )
        self._column = bui.columnwidget(parent=self._scroll, border=6, margin=0)

        # ---- تست ماژول‌ها ----
        self._row("🔧 تست ماژول‌ها (تشخیص خطا)", self._run_module_test, small=True)

        # ---- جون بی‌نهایت ----
        self._health_btn = self._row("❤️ جون بی‌نهایت: خاموش (فقط برای خودت)", self._toggle_health)

        # ---- بمب‌ها و مین (فقط روی دشمن) ----
        self._section_title("💣 بمب و مین (فقط روی دشمن، نه خودت)")
        self._row("اسپاون بمب معمولی", _spawn_bomb_type("normal"))
        self._row("اسپاون بمب یخی (Ice)", _spawn_bomb_type("ice"))
        self._row("اسپاون بمب چسبان (Sticky)", _spawn_bomb_type("sticky"))
        self._row("اسپاون بمب ضربه‌ای (Impact)", _spawn_bomb_type("impact"))
        self._row("اسپاون مین", _spawn_mine_near_players)
        self._row("اسپاون پاورآپ تصادفی", _spawn_powerup_near_players)

        # ---- اسکین‌ها ----
        self._section_title("🎭 اسکین‌ها (برای اسپاون بعدی)")
        self._row("📋 نمایش لیست کامل اسکین‌های موجود", _list_appearances, small=True)
        for label, real_name in self.CHARACTERS:
            self._row(
                f"اسکین بعدی همه: {label}",
                _change_player_next_appearance(real_name, me_only=False),
            )

        # ---- تبدیل فوری (respawn آنی، فقط خودت) ----
        self._section_title("⚡ تبدیل فوری خودت (respawn آنی، بدون منتظرموندن)")
        for label, real_name in self.CHARACTERS:
            self._row(
                f"⚡ همین الان تبدیل شو: {label}",
                _change_and_respawn_now(real_name, me_only=True),
                small=True,
            )

        # ---- اسکین دلخواه (متنی) ----
        self._section_title("✏️ اسکین با نام دلخواه")
        self._name_field = bui.textwidget(
            parent=self._column,
            size=(width - 60, 46),
            text="",
            editable=True,
            h_align="left",
            v_align="center",
            color=HadiStyle.NEON_WHITE,
            description="اسم دقیق اسکین رو بنویس (مثلاً از لیست بالا)",
        )
        self._row("⭐ اعمال روی خودم فقط", self._apply_custom_skin_me)
        self._row("👥 اعمال روی همه", self._apply_custom_skin_all)

    def _section_title(self, text):
        bui.textwidget(
            parent=self._column,
            size=(0, 34),
            text=text,
            color=HadiStyle.NEON_RED,
            h_align="left",
            v_align="center",
            scale=0.85,
        )

    def _row(self, label, func, small=False):
        btn = bui.buttonwidget(
            parent=self._column,
            size=(400, 38 if small else 42),
            label=label,
            color=(0.2, 0.15, 0.0) if small else (0.15, 0.02, 0.02),
            textcolor=HadiStyle.NEON_WHITE,
            scale=0.9 if small else 1.0,
            on_activate_call=lambda: self._run(func),
        )
        return btn

    def _run(self, func):
        try:
            ok, msg = func()
        except Exception as e:
            ok, msg = False, f"خطای غیرمنتظره: {type(e).__name__}: {e}"
        babase.screenmessage(f"HADI: {msg}", color=(0.0, 1.0, 0.2) if ok else (1.0, 0.4, 0.0))

    def _toggle_health(self):
        ok, msg = _toggle_infinite_health()
        state_text = "روشن" if _infinite_health_enabled["on"] else "خاموش"
        try:
            bui.buttonwidget(
                edit=self._health_btn,
                label=f"❤️ جون بی‌نهایت: {state_text} (فقط برای خودت)",
            )
        except Exception:
            pass
        babase.screenmessage(f"HADI: {msg}", color=(0.0, 1.0, 0.2))

    def _get_custom_name(self):
        try:
            return bui.textwidget(query=self._name_field).strip()
        except Exception:
            return ""

    def _apply_custom_skin_me(self):
        name = self._get_custom_name()
        if not name:
            babase.screenmessage("HADI: اول اسم اسکین رو توی کادر بنویس", color=(1.0, 0.4, 0.0))
            return
        self._run(_change_player_next_appearance(name, me_only=True))

    def _apply_custom_skin_all(self):
        name = self._get_custom_name()
        if not name:
            babase.screenmessage("HADI: اول اسم اسکین رو توی کادر بنویس", color=(1.0, 0.4, 0.0))
            return
        self._run(_change_player_next_appearance(name, me_only=False))

    def _run_module_test(self):
        results = _test_modules()
        ok_all = True
        for name, ok, err in results:
            color = (0.0, 1.0, 0.2) if ok else (1.0, 0.3, 0.0)
            text = f"✓ {name}" if ok else f"✗ {name}: {err}"
            babase.screenmessage(text, color=color)
            if not ok:
                ok_all = False
        return ok_all, "تست ماژول‌ها تمام شد — نتایج بالا رو ببین"

    def _close(self):
        try:
            bui.containerwidget(edit=self._root, transition="out_scale")
        except Exception:
            pass


def _open_hadi_settings():
    try:
        HadiSettingsWindow()
    except Exception as e:
        babase.screenmessage(f"HADI ERROR: {e}", color=(1.0, 0.0, 0.0))


_last_hadi_button = {"widget": None}


def _add_hadi_corner_button(window, x_offset=16, y_offset_from_top=2):
    """
    دکمه‌ی HADI را بالا-چپ یک پنجره اضافه می‌کند. قبل از اضافه‌کردن،
    هر دکمه‌ی قبلی (روی هر پنجره‌ی دیگری) حذف می‌شود تا وقتی یک صفحه
    (مثلاً یک تابلوی امتیاز که هر چندثانیه رفرش می‌شود) بارها __init__
    را صدا می‌زند، دکمه‌ها روی هم تلنبار نشوند و فقط یکی وجود داشته باشد.
    """
    prev = _last_hadi_button["widget"]
    if prev is not None:
        try:
            if prev.exists():
                prev.delete()
        except Exception:
            pass
        _last_hadi_button["widget"] = None

    try:
        root = window._root_widget
        width = getattr(window, "_width", 400)
        height = getattr(window, "_height", 400)
        btn = bui.buttonwidget(
            parent=root,
            position=(x_offset, height - y_offset_from_top - 34),
            size=(110, 34),
            label="⚙ HADI",
            color=HadiStyle.NEON_RED,
            textcolor=HadiStyle.NEON_WHITE,
            scale=0.8,
            on_activate_call=_open_hadi_settings,
        )
        _last_hadi_button["widget"] = btn
        return True
    except Exception as e:
        babase.screenmessage(f"HADI: دکمه اضافه نشد ({e})", color=(1.0, 0.4, 0.0))
        return False


# ============================================================
# پچ منوی اصلی (MainMenuWindow)
# ============================================================

_mainmenu_patched = False


def _install_mainmenu_patch():
    global _mainmenu_patched
    if _mainmenu_patched or mainmenu_module is None:
        return
    if not hasattr(mainmenu_module, "MainMenuWindow"):
        return

    original_init = mainmenu_module.MainMenuWindow.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        try:
            # دکمه‌ی Play با RGB متحرک — attribute تأییدشده از سورس واقعی
            if getattr(self, "_play_button", None) is not None:
                _animate_rgb(self._play_button)

            # رنگ‌آمیزی نئونی بقیه‌ی دکمه‌های تأییدشده از سورس واقعی
            for attr in ("_gather_button", "_watch_button", "_how_to_play_button", "_credits_button", "_quit_button"):
                widget = getattr(self, attr, None)
                if widget is not None:
                    try:
                        bui.buttonwidget(edit=widget, color=HadiStyle.NEON_RED)
                    except Exception:
                        pass

            _add_hadi_corner_button(self)
        except Exception as e:
            babase.screenmessage(f"HADI ERROR: {e}", color=(1.0, 0.0, 0.0))

    mainmenu_module.MainMenuWindow.__init__ = patched_init
    _mainmenu_patched = True


# ============================================================
# پچ منوی پاز (InGameMenuWindow)
# ============================================================

_ingamemenu_patched = False


def _install_ingamemenu_patch():
    global _ingamemenu_patched
    if _ingamemenu_patched or ingamemenu_module is None:
        return
    if not hasattr(ingamemenu_module, "InGameMenuWindow"):
        return

    original_init = ingamemenu_module.InGameMenuWindow.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        try:
            _add_hadi_corner_button(self)
        except Exception as e:
            babase.screenmessage(f"HADI ERROR: {e}", color=(1.0, 0.0, 0.0))

    ingamemenu_module.InGameMenuWindow.__init__ = patched_init
    _ingamemenu_patched = True


# ============================================================
# PLUGIN
# ============================================================

# ba_meta export babase.Plugin
class HadiModPlugin(babase.Plugin):

    def __init__(self):
        babase.screenmessage("HADI MOD LOADED", color=(1.0, 0.0, 0.0))
        _install_mainmenu_patch()
        _install_ingamemenu_patch()
