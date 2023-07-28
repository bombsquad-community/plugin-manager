"""Practice Tools Mod: V2.0
Made by Cross Joy"""

# If anyone who want to help me on giving suggestion/ fix bugs/ creating PR,
# Can visit my github https://github.com/CrossJoy/Bombsquad-Modding

# You can contact me through discord:
# My Discord Id: Cross Joy#0721
# My BS Discord Server: https://discord.gg/JyBY6haARJ

# Some support will be much appreciated. :')
# Support link: https://www.buymeacoffee.com/CrossJoy

# ----------------------------------------------------------------------------
# V2.0 update
# - Updated to API 8 (1.7.20+)

# V1.2 update
# - Added New Bot: Bomber Lite and Brawler Lite.
# - Added New Setting: Epic Mode Toggle.
# - Added immunity to curse if invincible.
# - Fixed Power Up mini billboard will not removed after debuff.
# - Fixed Power Up landmine count will not removed after debuff.
# - Fixed the config (Bot Picker, Count, Radius and Power Up Picker) will set to default when exit the practice tab.

# V1.1 update
# - Fixed Charger Bot Pro bot spawn with shield.
# - Fixed selecting Bruiser bot is not working.
# - Added screen message when pressing spawn/clear/debuff button.
# ----------------------------------------------------------------------------
# Powerful and comprehensive tools for practice purpose.

# Features:
# - Spawn any bot anywhere.
# - Can spawn power up by your own.
# - Bomb radius visualizer. (Thx Mikirog for some of the codes :D )
# - Bomb Countdown.
# and many more

# Go explore the tools yourself.:)

# Practice tabs can be access through party window.
# Coop and local multiplayer compatible.
# Work on any 1.7+ ver.

# FAQ:
# Can I use it to practice with friends?
# - Yes, but you are the only one can access the practice window.

# Does it work when I join a public server?
# - Not possible.

# Can I use it during Coop game?
# - Yes, it works fine.
# ----------------------------------------------------------------------------

from __future__ import annotations

import math
import random
import weakref
from enum import Enum
from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
import bascenev1lib
import bauiv1 as bui
import bauiv1lib as buil
from babase import app, Plugin
from bascenev1lib.actor.powerupbox import PowerupBox
from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.actor import spawner
from bascenev1lib.actor.spazbot import (SpazBotSet, SpazBot, BrawlerBot,
                                        TriggerBot,
                                        ChargerBot, StickyBot, ExplodeyBot,
                                        BouncyBot,
                                        BomberBotPro, BrawlerBotPro,
                                        TriggerBotPro,
                                        ChargerBotPro, BomberBotProShielded,
                                        BrawlerBotProShielded,
                                        TriggerBotProShielded,
                                        ChargerBotProShielded, BomberBotLite,
                                        BrawlerBotLite)
from bascenev1lib.mainmenu import MainMenuSession
from bauiv1lib import popup
from bauiv1lib.party import PartyWindow as OriginalPartyWindow
from bauiv1lib.tabs import TabRow

if TYPE_CHECKING:
    from typing import Any, Sequence, Callable, Optional

version = '2.0'

try:
    if babase.app.config.get("bombCountdown") is None:
        babase.app.config["bombCountdown"] = False
    else:
        babase.app.config.get("bombCountdown")
except:
    babase.app.config["bombCountdown"] = False

try:
    if babase.app.config.get("bombRadiusVisual") is None:
        babase.app.config["bombRadiusVisual"] = False
    else:
        babase.app.config.get("bombRadiusVisual")
except:
    babase.app.config["bombRadiusVisual"] = False

try:
    if babase.app.config.get("stopBots") is None:
        babase.app.config["stopBots"] = False
    else:
        babase.app.config.get("stopBots")
except:
    babase.app.config["stopBots"] = False

try:
    if babase.app.config.get("immortalDummy") is None:
        babase.app.config["immortalDummy"] = False
    else:
        babase.app.config.get("immortalDummy")
except:
    babase.app.config["immortalDummy"] = False

try:
    if babase.app.config.get("invincible") is None:
        babase.app.config["invincible"] = False
    else:
        babase.app.config.get("invincible")
except:
    babase.app.config["invincible"] = False

bui.set_party_icon_always_visible(True)


class PartyWindow(bui.Window):
    _redefine_methods = ['__init__']

    def __init__(self, *args, **kwargs):
        getattr(self, '__init___old')(*args, **kwargs)

        self.bg_color = (.5, .5, .5)

        self._edit_movements_button = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(360, self._height - 47),
            # (self._width - 80, self._height - 47)
            size=(100, 50),
            label='Practice',
            autoselect=True,
            button_type='square',
            on_activate_call=bs.Call(doTestButton, self),
            color=self.bg_color,
            iconscale=1.2)


def redefine(obj: object, name: str, new: callable,
             new_name: str = None) -> None:
    if not new_name:
        new_name = name + '_old'
    if hasattr(obj, name):
        setattr(obj, new_name, getattr(obj, name))
    setattr(obj, name, new)


def redefine_class(original_cls: object, cls: object) -> None:
    for method in cls._redefine_methods:
        redefine(original_cls, method, getattr(cls, method))


def main(plugin: Plugin) -> None:
    print(f'Plugins Tools v{plugin.__version__}')
    app.practice_tool = plugin
    redefine_class(OriginalPartyWindow, PartyWindow)


# ba_meta require api 8
# ba_meta export plugin
class Practice(Plugin):
    __version__ = '2.0'

    def on_app_running(self) -> None:
        """Plugin start point."""

        if app.build_number < 20427:
            bui.screenmessage(
                'ok',
                color=(.8, .1, .1))
            raise RuntimeError(
                'sad')

        return main(self)

    def new_bomb_init(func):
        def setting(*args, **kwargs):
            func(*args, **kwargs)

            bomb_type = args[0].bomb_type
            fuse_bomb = ('land_mine', 'tnt', 'impact')

            if babase.app.config.get("bombRadiusVisual"):
                args[0].radius_visualizer = bs.newnode('locator',
                                                       owner=args[0].node,
                                                       # Remove itself when the bomb node dies.
                                                       attrs={
                                                           'shape': 'circle',
                                                           'color': (1, 0, 0),
                                                           'opacity': 0.05,
                                                           'draw_beauty': False,
                                                           'additive': False
                                                       })
                args[0].node.connectattr('position', args[0].radius_visualizer,
                                         'position')

                bs.animate_array(args[0].radius_visualizer, 'size', 1, {
                    0.0: [0.0],
                    0.2: [args[0].blast_radius * 2.2],
                    0.25: [args[0].blast_radius * 2.0]
                })

                args[0].radius_visualizer_circle = bs.newnode(
                    'locator',
                    owner=args[
                        0].node,
                    # Remove itself when the bomb node dies.
                    attrs={
                        'shape': 'circleOutline',
                        'size': [
                            args[
                                0].blast_radius * 2.0],
                        # Here's that bomb's blast radius value again!
                        'color': (
                            1, 1, 0),
                        'draw_beauty': False,
                        'additive': True
                    })
                args[0].node.connectattr('position',
                                         args[0].radius_visualizer_circle,
                                         'position')

                bs.animate(
                    args[0].radius_visualizer_circle, 'opacity', {
                        0: 0.0,
                        0.4: 0.1
                    })

                if bomb_type == 'tnt':
                    args[0].fatal = bs.newnode('locator',
                                               owner=args[0].node,
                                               # Remove itself when the bomb node dies.
                                               attrs={
                                                   'shape': 'circle',
                                                   'color': (
                                                       0.7, 0, 0),
                                                   'opacity': 0.10,
                                                   'draw_beauty': False,
                                                   'additive': False
                                               })
                    args[0].node.connectattr('position',
                                             args[0].fatal,
                                             'position')

                    bs.animate_array(args[0].fatal, 'size', 1, {
                        0.0: [0.0],
                        0.2: [args[0].blast_radius * 2.2 * 0.7],
                        0.25: [args[0].blast_radius * 2.0 * 0.7]
                    })

            if babase.app.config.get(
                    "bombCountdown") and bomb_type not in fuse_bomb:
                color = (1.0, 1.0, 0.0)
                count_bomb(*args, count='3', color=color)
                color = (1.0, 0.5, 0.0)
                bs.timer(1, bs.Call(count_bomb, *args, count='2', color=color))
                color = (1.0, 0.15, 0.15)
                bs.timer(2, bs.Call(count_bomb, *args, count='1', color=color))

        return setting

    bascenev1lib.actor.bomb.Bomb.__init__ = new_bomb_init(
        bascenev1lib.actor.bomb.Bomb.__init__)


Spaz._pm2_spz_old = Spaz.__init__


def _init_spaz_(self, *args, **kwargs):
    self._pm2_spz_old(*args, **kwargs)
    self.bot_radius = bs.newnode('locator',
                                 owner=self.node,
                                 # Remove itself when the bomb node dies.
                                 attrs={
                                     'shape': 'circle',
                                     'color': (0, 0, 1),
                                     'opacity': 0.0,
                                     'draw_beauty': False,
                                     'additive': False
                                 })
    self.node.connectattr('position',
                          self.bot_radius,
                          'position')

    self.radius_visualizer_circle = bs.newnode(
        'locator',
        owner=self.node,
        # Remove itself when the bomb node dies.
        attrs={
            'shape': 'circleOutline',
            'size': [(self.hitpoints_max - self.hitpoints) * 0.0048],
            # Here's that bomb's blast radius value again!
            'color': (0, 1, 1),
            'draw_beauty': False,
            'additive': True
        })

    self.node.connectattr('position', self.radius_visualizer_circle,
                          'position')

    self.curse_visualizer = bs.newnode('locator',
                                       owner=self.node,
                                       # Remove itself when the bomb node dies.
                                       attrs={
                                           'shape': 'circle',
                                           'color': (1, 0, 0),
                                           'size': (0.0, 0.0, 0.0),
                                           'opacity': 0.05,
                                           'draw_beauty': False,
                                           'additive': False
                                       })
    self.node.connectattr('position', self.curse_visualizer,
                          'position')

    self.curse_visualizer_circle = bs.newnode(
        'locator',
        owner=self.node,
        # Remove itself when the bomb node dies.
        attrs={
            'shape': 'circleOutline',
            'size': [3 * 2.0],
            # Here's that bomb's blast radius value again!
            'color': (
                1, 1, 0),
            'opacity': 0.0,
            'draw_beauty': False,
            'additive': True
        })
    self.node.connectattr('position',
                          self.curse_visualizer_circle,
                          'position')

    self.curse_visualizer_fatal = bs.newnode('locator',
                                             owner=self.node,
                                             # Remove itself when the bomb node dies.
                                             attrs={
                                                 'shape': 'circle',
                                                 'color': (
                                                     0.7, 0, 0),
                                                 'size': (0.0, 0.0, 0.0),
                                                 'opacity': 0.10,
                                                 'draw_beauty': False,
                                                 'additive': False
                                             })
    self.node.connectattr('position',
                          self.curse_visualizer_fatal,
                          'position')

    def invincible() -> None:
        for i in bs.get_foreground_host_activity().players:
            try:
                if i.node:
                    if babase.app.config.get("invincible"):
                        i.actor.node.invincible = True
                    else:
                        i.actor.node.invincible = False
            except:
                pass

    bs.timer(1.001, bs.Call(invincible))


Spaz.__init__ = _init_spaz_

Spaz.super_curse = Spaz.curse


def new_cursed(self):
    if self.node.invincible:
        return
    self.super_curse()
    if babase.app.config.get("bombRadiusVisual"):
        bs.animate_array(self.curse_visualizer, 'size', 1, {
            0.0: [0.0],
            0.2: [3 * 2.2],
            0.5: [3 * 2.0],
            5.0: [3 * 2.0],
            5.1: [0.0],
        })

        bs.animate(
            self.curse_visualizer_circle, 'opacity', {
                0: 0.0,
                0.4: 0.1,
                5.0: 0.1,
                5.1: 0.0,
            })

        bs.animate_array(self.curse_visualizer_fatal, 'size', 1, {
            0.0: [0.0],
            0.2: [2.2],
            0.5: [2.0],
            5.0: [2.0],
            5.1: [0.0],
        })


Spaz.curse = new_cursed

Spaz.super_handlemessage = Spaz.handlemessage


def bot_handlemessage(self, msg: Any):
    if isinstance(msg, bs.PowerupMessage):
        if msg.poweruptype == 'health':
            if babase.app.config.get("bombRadiusVisual"):
                if self._cursed:
                    bs.animate_array(self.curse_visualizer, 'size', 1, {
                        0.0: [3 * 2.0],
                        0.2: [0.0],
                    })

                    bs.animate(
                        self.curse_visualizer_circle, 'opacity', {
                            0.0: 0.1,
                            0.2: 0.0,
                        })

                    bs.animate_array(self.curse_visualizer_fatal, 'size', 1, {
                        0.0: [2.0],
                        0.2: [0.0],
                    })

                bs.animate_array(self.bot_radius, 'size', 1, {
                    0.0: [0],
                    0.25: [0]
                })
                bs.animate(self.bot_radius, 'opacity', {
                    0.0: 0.00,
                    0.25: 0.0
                })

                bs.animate_array(self.radius_visualizer_circle, 'size', 1, {
                    0.0: [0],
                    0.25: [0]
                })

                bs.animate(
                    self.radius_visualizer_circle, 'opacity', {
                        0.0: 0.00,
                        0.25: 0.0
                    })

    self.super_handlemessage(msg)

    if isinstance(msg, bs.HitMessage):
        if self.hitpoints <= 0:
            bs.animate(self.bot_radius, 'opacity', {
                0.0: 0.00
            })
            bs.animate(
                self.radius_visualizer_circle, 'opacity', {
                    0.0: 0.00
                })
        elif babase.app.config.get('bombRadiusVisual'):

            bs.animate_array(self.bot_radius, 'size', 1, {
                0.0: [(self.hitpoints_max - self.hitpoints) * 0.0045],
                0.25: [(self.hitpoints_max - self.hitpoints) * 0.0045]
            })
            bs.animate(self.bot_radius, 'opacity', {
                0.0: 0.00,
                0.25: 0.05
            })

            bs.animate_array(self.radius_visualizer_circle, 'size', 1, {
                0.0: [(self.hitpoints_max - self.hitpoints) * 0.0045],
                0.25: [(self.hitpoints_max - self.hitpoints) * 0.0045]
            })

            bs.animate(
                self.radius_visualizer_circle, 'opacity', {
                    0.0: 0.00,
                    0.25: 0.1
                })


Spaz.handlemessage = bot_handlemessage


def count_bomb(*args, count, color):
    text = bs.newnode('math', owner=args[0].node,
                      attrs={'input1': (0, 0.7, 0),
                             'operation': 'add'})
    args[0].node.connectattr('position', text, 'input2')
    args[0].spaztext = bs.newnode('text',
                                  owner=args[0].node,
                                  attrs={
                                      'text': count,
                                      'in_world': True,
                                      'color': color,
                                      'shadow': 1.0,
                                      'flatness': 1.0,
                                      'scale': 0.012,
                                      'h_align': 'center',
                                  })

    args[0].node.connectattr('position', args[0].spaztext,
                             'position')
    bs.animate(args[0].spaztext, 'scale',
               {0: 0, 0.3: 0.03, 0.5: 0.025, 0.8: 0.025, 1.0: 0.0})


def doTestButton(self):
    if isinstance(bs.get_foreground_host_session(), MainMenuSession):
        bui.screenmessage('Join any map to start using it.', color=(.8, .8, .1))
        return

    bui.containerwidget(edit=self._root_widget, transition='out_left')
    bs.Call(PracticeWindow())


# ---------------------------------------------------------------


class NewBotSet(SpazBotSet):

    def __init__(self):
        """Create a bot-set."""

        # We spread our bots out over a few lists so we can update
        # them in a staggered fashion.
        super().__init__()

    def start_moving(self) -> None:
        """Start processing bot AI updates so they start doing their thing."""
        self._bot_update_timer = bui.AppTimer(
            0.05, bs.WeakCall(self._update), repeat=True
        )

    def _update(self) -> None:

        # Update one of our bot lists each time through.
        # First off, remove no-longer-existing bots from the list.
        try:
            bot_list = self._bot_lists[self._bot_update_list] = ([
                b for b in self._bot_lists[self._bot_update_list] if b
            ])
        except Exception:
            bot_list = []
            babase.print_exception('Error updating bot list: ' +
                                   str(self._bot_lists[
                                       self._bot_update_list]))
        self._bot_update_list = (self._bot_update_list +
                                 1) % self._bot_list_count

        # Update our list of player points for the bots to use.
        player_pts = []
        for player in bs.getactivity().players:
            assert isinstance(player, bs.Player)
            try:
                # TODO: could use abstracted player.position here so we
                # don't have to assume their actor type, but we have no
                # abstracted velocity as of yet.
                if player.is_alive():
                    assert isinstance(player.actor, Spaz)
                    assert player.actor.node
                    player_pts.append(
                        (bs.Vec3(player.actor.node.position),
                         bs.Vec3(
                             player.actor.node.velocity)))
            except Exception:
                babase.print_exception('Error on bot-set _update.')

        for bot in bot_list:
            if not babase.app.config.get('stopBots'):
                bot.set_player_points(player_pts)
                bot.update_ai()

    def clear(self) -> None:
        """Immediately clear out any bots in the set."""
        # Don't do this if the activity is shutting down or dead.
        activity = bs.getactivity(doraise=False)
        if activity is None or activity.expired:
            return

        for i, bot_list in enumerate(self._bot_lists):
            for bot in bot_list:
                bot.handlemessage(bs.DieMessage(immediate=True))
            self._bot_lists[i] = []

    def spawn_bot(
            self,
            bot_type: type[SpazBot],
            pos: Sequence[float],
            spawn_time: float = 3.0,
            on_spawn_call: Callable[[SpazBot], Any] | None = None) -> None:
        """Spawn a bot from this set."""

        spawner.Spawner(
            pt=pos,
            spawn_time=spawn_time,
            send_spawn_message=False,
            spawn_callback=bs.Call(
                self._spawn_bot, bot_type, pos, on_spawn_call
            ),
        )
        self._spawning_count += 1

    def _spawn_bot(self, bot_type: type[SpazBot], pos: Sequence[float],
                   on_spawn_call: Callable[[SpazBot], Any] | None) -> None:
        spaz = bot_type().autoretain()
        bs.getsound('spawn').play(position=pos)
        assert spaz.node
        spaz.node.handlemessage('flash')
        spaz.node.is_area_of_interest = False
        spaz.handlemessage(bs.StandMessage(pos, random.uniform(0, 360)))
        self.add_bot(spaz)
        self._spawning_count -= 1
        if on_spawn_call is not None:
            on_spawn_call(spaz)


class DummyBotSet(NewBotSet):

    def _update(self) -> None:

        try:
            # Update one of our bot lists each time through.
            # First off, remove no-longer-existing bots from the list.
            try:
                bot_list = self._bot_lists[self._bot_update_list] = ([
                    b for b in self._bot_lists[self._bot_update_list] if b
                ])
            except Exception:
                babase.print_exception('Error updating bot list: ' +
                                       str(self._bot_lists[
                                           self._bot_update_list]))
            self._bot_update_list = (self._bot_update_list +
                                     1) % self._bot_list_count

        except:
            pass


class DummyBot(SpazBot):
    character = 'Bones'

    def __init__(self):
        super().__init__()
        if babase.app.config.get('immortalDummy'):
            bs.timer(0.2, self.immortal,
                     repeat=True)

    def immortal(self):
        self.hitpoints = self.hitpoints_max = 10000
        try:
            bs.emitfx(
                position=self.node.position,
                count=20,
                emit_type='fairydust')
        except:
            pass


class NewChargerBotPro(ChargerBotPro):
    default_shields = False


# -------------------------------------------------------------------

class PracticeTab:
    """Defines a tab for use in the gather UI."""

    def __init__(self, window: PracticeWindow) -> None:
        self._window = weakref.ref(window)

    @property
    def window(self) -> PracticeWindow:
        """The GatherWindow that this tab belongs to."""
        window = self._window()
        if window is None:
            raise bs.NotFoundError("PracticeTab's window no longer exists.")
        return window

    def on_activate(
        self,
        parent_widget: bs.Widget,
        tab_button: bs.Widget,
        region_width: float,
        region_height: float,
        scroll_widget: bs.Widget,
        extra_x: float,
    ) -> bs.Widget:
        """Called when the tab becomes the active one.

        The tab should create and return a container widget covering the
        specified region.
        """
        raise RuntimeError('Should not get here.')

    def on_deactivate(self) -> None:
        """Called when the tab will no longer be the active one."""

    def save_state(self) -> None:
        """Called when the parent window is saving state."""

    def restore_state(self) -> None:
        """Called when the parent window is restoring state."""


def _check_value_change(setting: int, widget: bs.Widget,
                        value: str) -> None:
    bui.textwidget(edit=widget,
                   text=bs.Lstr(resource='onText') if value else bs.Lstr(
                       resource='offText'))

    if setting == 0:
        if value:
            babase.app.config["stopBots"] = True
        else:
            babase.app.config["stopBots"] = False
    elif setting == 1:
        if value:
            babase.app.config["immortalDummy"] = True
        else:
            babase.app.config["immortalDummy"] = False


class BotsPracticeTab(PracticeTab):
    """The about tab in the practice UI"""

    def __init__(self, window: PracticeWindow
                 ) -> None:

        super().__init__(window)
        activity = bs.get_foreground_host_activity()
        with activity.context:
            try:
                if not activity.bot1 or not activity.bot2:
                    activity.bot1 = DummyBotSet()
                    activity.bot2 = NewBotSet()
            except:
                activity.bot1 = DummyBotSet()
                activity.bot2 = NewBotSet()
        bot_index, count, radius = self.load_settings()
        self._container: bs.Widget | None = None
        self.count = count
        self.radius = radius
        self.radius_array = (['Small', 'Medium', 'Big'])
        self.parent_widget = None
        self.bot1 = activity.bot1
        self.bot2 = activity.bot2
        self.activity = bs.get_foreground_host_activity()
        self.image_array = (
            ['bonesIcon', 'neoSpazIcon', 'kronkIcon', 'neoSpazIcon',
             'kronkIcon',
             'zoeIcon', 'ninjaIcon', 'melIcon', 'jackIcon', 'bunnyIcon',
             'neoSpazIcon', 'kronkIcon', 'zoeIcon', 'ninjaIcon',
             'neoSpazIcon', 'kronkIcon', 'zoeIcon', 'ninjaIcon'])
        self.bot_array_name = (
            ['Dummy', 'Bomber Lite', 'Brawler Lite', 'Bomber', 'Brawler',
             'Trigger', 'Charger', 'Sticky',
             'Explodey', 'Bouncy', 'Pro Bomber',
             'Pro Brawler', 'Pro Trigger', 'Pro Charger',
             'S.Pro Bomber', 'S.Pro Brawler',
             'S.Pro Trigger', 'S.Pro Charger'])

        self.setting_name = (['Stop Bots', 'Immortal Dummy'])
        self.config = (['stopBots', 'immortalDummy'])

        self.bot_array = (
            [DummyBot, BomberBotLite, BrawlerBotLite, SpazBot, BrawlerBot,
             TriggerBot,
             ChargerBot, StickyBot, ExplodeyBot, BouncyBot,
             BomberBotPro, BrawlerBotPro, TriggerBotPro, NewChargerBotPro,
             BomberBotProShielded, BrawlerBotProShielded,
             TriggerBotProShielded, ChargerBotProShielded])

        self._icon_index = bot_index

    def on_activate(
        self,
        parent_widget: bs.Widget,
        tab_button: bs.Widget,
        region_width: float,
        region_height: float,
        scroll_widget: bs.Widget,
        extra_x: float,
    ) -> bui.Widget:

        b_size_2 = 100
        spacing_h = -50
        mask_texture = bui.gettexture('characterIconMask')
        spacing_v = 60

        self.parent_widget = parent_widget

        self._scroll_width = region_width * 0.8
        self._scroll_height = region_height * 0.6
        self._scroll_position = ((region_width - self._scroll_width) * 0.5,
                                 (region_height - self._scroll_height) * 0.5)

        self._sub_width = self._scroll_width
        self._sub_height = 200

        self.container_h = 600
        bots_height = self.container_h - 50

        self._subcontainer = bui.containerwidget(
            parent=scroll_widget,
            size=(self._sub_width, self.container_h),
            background=False,
            selection_loops_to_parent=True)

        bui.textwidget(parent=self._subcontainer,
                       position=(self._sub_width * 0.5,
                                 bots_height),
                       size=(0, 0),
                       color=(1.0, 1.0, 1.0),
                       scale=1.3,
                       h_align='center',
                       v_align='center',
                       text='Spawn Bot',
                       maxwidth=200)

        tint1, tint2, color = self.check_color()

        self._bot_button = bot = bui.buttonwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(self._sub_width * 0.5 - b_size_2 * 0.5,
                      bots_height + spacing_h * 3),
            on_activate_call=self._bot_window,
            size=(b_size_2, b_size_2),
            label='',
            color=color,
            tint_texture=(bui.gettexture(
                self.image_array[self._icon_index] + 'ColorMask')),
            tint_color=tint1,
            tint2_color=tint2,
            texture=bui.gettexture(self.image_array[self._icon_index]),
            mask_texture=mask_texture)

        bui.textwidget(
            parent=self._subcontainer,
            h_align='center',
            v_align='center',
            position=(self._sub_width * 0.5,
                      bots_height + spacing_h * 4 + 10),
            size=(0, 0),
            draw_controller=bot,
            text='Bot Type',
            scale=1.0,
            color=bui.app.ui_v1.title_color,
            maxwidth=130)

        bui.textwidget(parent=self._subcontainer,
                       position=(
                           self._sub_width * 0.005,
                           bots_height
                           + spacing_h * 7),
                       size=(100, 30),
                       text='Count',
                       h_align='left',
                       color=(0.8, 0.8, 0.8),
                       v_align='center',
                       maxwidth=200)
        self.count_text = txt = bui.textwidget(parent=self._subcontainer,
                                               position=(
                                                   self._sub_width * 0.85 - spacing_v * 2,
                                                   bots_height
                                                   + spacing_h * 7),
                                               size=(0, 28),
                                               text=str(self.count),
                                               editable=False,
                                               color=(0.6, 1.0, 0.6),
                                               maxwidth=150,
                                               h_align='center',
                                               v_align='center',
                                               padding=2)
        self.button_bot_left = btn1 = bui.buttonwidget(
            parent=self._subcontainer,
            position=(
                self._sub_width * 0.85 - spacing_v - 14,
                bots_height
                + spacing_h * 7),
            size=(28, 28),
            label='-',
            autoselect=True,
            on_activate_call=self.decrease_count,
            repeat=True)
        self.button_bot_right = btn2 = bui.buttonwidget(
            parent=self._subcontainer,
            position=(
                self._sub_width * 0.85 - 14,
                bots_height
                + spacing_h * 7),
            size=(28, 28),
            label='+',
            autoselect=True,
            on_activate_call=self.increase_count,
            repeat=True)

        bui.textwidget(parent=self._subcontainer,
                       position=(
                           self._sub_width * 0.005,
                           bots_height
                           + spacing_h * 8),
                       size=(100, 30),
                       text='Spawn Radius',
                       h_align='left',
                       color=(0.8, 0.8, 0.8),
                       v_align='center',
                       maxwidth=200)

        self.radius_text = txt = bui.textwidget(parent=self._subcontainer,
                                                position=(
                                                    self._sub_width * 0.85 - spacing_v * 2,
                                                    bots_height
                                                    + spacing_h * 8),
                                                size=(0, 28),
                                                text=self.radius_array[
                                                    self.radius],
                                                editable=False,
                                                color=(0.6, 1.0, 0.6),
                                                maxwidth=50,
                                                h_align='center',
                                                v_align='center',
                                                padding=2)
        self.button_bot_left = btn1 = bui.buttonwidget(
            parent=self._subcontainer,
            position=(
                self._sub_width * 0.85 - spacing_v - 14,
                bots_height
                + spacing_h * 8),
            size=(28, 28),
            label='-',
            autoselect=True,
            on_activate_call=self.decrease_radius,
            repeat=True)
        self.button_bot_right = btn2 = bui.buttonwidget(
            parent=self._subcontainer,
            position=(
                self._sub_width * 0.85 - 14,
                bots_height
                + spacing_h * 8),
            size=(28, 28),
            label='+',
            autoselect=True,
            on_activate_call=self.increase_radius,
            repeat=True)

        self.button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(
                self._sub_width * 0.25 - 40,
                bots_height
                + spacing_h * 6),
            size=(80, 50),
            autoselect=True,
            button_type='square',
            label='Spawn',
            on_activate_call=self.do_spawn_bot)

        self.button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(
                self._sub_width * 0.75 - 40,
                bots_height
                + spacing_h * 6),
            size=(80, 50),
            autoselect=True,
            button_type='square',
            color=(1, 0.2, 0.2),
            label='Clear',
            on_activate_call=self.clear_bot)

        i = 0
        for name in self.setting_name:
            bui.textwidget(parent=self._subcontainer,
                           position=(self._sub_width * 0.005,
                                     bots_height + spacing_h * (9 + i)),
                           size=(100, 30),
                           text=name,
                           h_align='left',
                           color=(0.8, 0.8, 0.8),
                           v_align='center',
                           maxwidth=200)
            value = babase.app.config.get(self.config[i])
            txt2 = bui.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.8 - spacing_v / 2,
                          bots_height +
                          spacing_h * (9 + i)),
                size=(0, 28),
                text=bs.Lstr(resource='onText') if value else bs.Lstr(
                    resource='offText'),
                editable=False,
                color=(0.6, 1.0, 0.6),
                maxwidth=50,
                h_align='right',
                v_align='center',
                padding=2)
            bui.checkboxwidget(parent=self._subcontainer,
                               text='',
                               position=(self._sub_width * 0.8 - 15,
                                         bots_height +
                                         spacing_h * (9 + i)),
                               size=(30, 30),
                               autoselect=False,
                               textcolor=(0.8, 0.8, 0.8),
                               value=value,
                               on_value_change_call=bs.Call(
                                   _check_value_change,
                                   i, txt2))
            i += 1

        return self._subcontainer

    def _bot_window(self) -> None:
        BotPicker(
            parent=self.parent_widget,
            delegate=self)

    def increase_count(self):
        if self.count < 10:
            self.count += 1

            bui.textwidget(edit=self.count_text,
                           text=str(self.count))
        self.save_settings()

    def decrease_count(self):
        if self.count > 1:
            self.count -= 1

            bui.textwidget(edit=self.count_text,
                           text=str(self.count))
        self.save_settings()

    def increase_radius(self):
        if self.radius < 2:
            self.radius += 1

            bui.textwidget(edit=self.radius_text,
                           text=self.radius_array[self.radius])
        self.save_settings()

    def decrease_radius(self):
        if self.radius > 0:
            self.radius -= 1

            bui.textwidget(edit=self.radius_text,
                           text=self.radius_array[self.radius])
        self.save_settings()

    def clear_bot(self):
        bs.screenmessage('Cleared', color=(1, 0.1, 0.1))
        activity = bs.get_foreground_host_activity()
        with activity.context:
            self.bot1.clear()
            self.bot2.clear()

    def do_spawn_bot(self, clid: int = -1) -> None:
        bs.screenmessage('Spawned', color=(0.2, 1, 0.2))
        activity = bs.get_foreground_host_activity()
        with activity.context:
            for i in bs.get_foreground_host_activity().players:
                if i.sessionplayer.inputdevice.client_id == clid:
                    if i.node:
                        bot_type = self._icon_index
                        for a in range(self.count):
                            x = (random.randrange
                                 (-10, 10) / 10) * math.pow(self.radius + 1, 2)
                            z = (random.randrange
                                 (-10, 10) / 10) * math.pow(self.radius + 1, 2)
                            pos = (i.node.position[0] + x,
                                   i.node.position[1],
                                   i.node.position[2] + z)
                            if bot_type == 0:
                                self.bot1.spawn_bot(self.bot_array[0],
                                                    pos=pos,
                                                    spawn_time=1.0)
                            else:
                                self.bot2.spawn_bot(self.bot_array[bot_type],
                                                    pos=pos,
                                                    spawn_time=1.0)
                    break

    def on_bots_picker_pick(self, character: str) -> None:
        """A bots has been selected by the picker."""
        if not self.parent_widget:
            return

        # The player could have bought a new one while the picker was u
        self._icon_index = self.bot_array_name.index(
            character) if character in self.bot_array_name else 0
        self._update_character()

    def _update_character(self, change: int = 0) -> None:
        if self._bot_button:
            tint1, tint2, color = self.check_color()

            bui.buttonwidget(
                edit=self._bot_button,
                texture=bui.gettexture(self.image_array[self._icon_index]),
                tint_texture=(bui.gettexture(
                    self.image_array[self._icon_index] + 'ColorMask')),
                color=color,
                tint_color=tint1,
                tint2_color=tint2)
        self.save_settings()

    def load_settings(self):
        try:
            if babase.app.config.get("botsSpawnSetting") is None:
                babase.app.config["botsSpawnSetting"] = (0, 1, 0)
                bot_index, count, radius = babase.app.config.get(
                    "botsSpawnSetting")
            else:
                bot_index, count, radius = babase.app.config.get(
                    "botsSpawnSetting")
        except:
            babase.app.config["botsSpawnSetting"] = (0, 1, 0)
            bot_index, count, radius = babase.app.config.get("botsSpawnSetting")
        values = bot_index, count, radius
        return values

    def save_settings(self):
        babase.app.config["botsSpawnSetting"] = (self._icon_index, self.count,
                                                 self.radius)
        babase.app.config.commit()

    def check_color(self):
        if self.bot_array_name[self._icon_index] in (
            'Pro Bomber', 'Pro Brawler',
            'Pro Trigger', 'Pro Charger',
            'S.Pro Bomber', 'S.Pro Brawler',
                'S.Pro Trigger', 'S.Pro Charger'):
            tint1 = (1.0, 0.2, 0.1)
            tint2 = (0.6, 0.1, 0.05)
        elif self.bot_array_name[self._icon_index] in 'Bouncy':
            tint1 = (1, 1, 1)
            tint2 = (1.0, 0.5, 0.5)
        elif self.bot_array_name[self._icon_index] in ('Brawler Lite',
                                                       'Bomber Lite'):
            tint1 = (1.2, 0.9, 0.2)
            tint2 = (1.0, 0.5, 0.6)
        else:
            tint1 = (0.6, 0.6, 0.6)
            tint2 = (0.1, 0.3, 0.1)

        if self.bot_array_name[self._icon_index] in (
            'S.Pro Bomber', 'S.Pro Brawler',
                'S.Pro Trigger', 'S.Pro Charger'):
            color = (1.3, 1.2, 3.0)
        else:
            color = (1.0, 1.0, 1.0)

        colors = tint1, tint2, color
        return colors


class PowerUpPracticeTab(PracticeTab):
    """The about tab in the practice UI"""

    def __init__(self, window: PracticeWindow) -> None:
        super().__init__(window)
        self._container: bs.Widget | None = None
        self.count = 1
        self.parent_widget = None
        self.activity = bs.get_foreground_host_activity()

        self.power_list = (['Bomb', 'Curse', 'Health', 'IceBombs',
                            'ImpactBombs', 'LandMines', 'Punch',
                            'Shield', 'StickyBombs'])

        self.power_list_type_name = (
            ['Tripple Bombs', 'Curse', 'Health', 'Ice Bombs',
             'Impact Bombs', 'Land Mines', 'Punch',
             'Shield', 'Sticky Bombs'])

        self.power_list_type = (
            ['triple_bombs', 'curse', 'health', 'ice_bombs',
             'impact_bombs', 'land_mines', 'punch',
             'shield', 'sticky_bombs'])
        self._icon_index = self.load_settings()

        self.setting_name = (['Bomb Countdown', 'Bomb Radius Visualizer'])
        self.config = (['bombCountdown', 'bombRadiusVisual'])

    def on_activate(
        self,
        parent_widget: bs.Widget,
        tab_button: bs.Widget,
        region_width: float,
        region_height: float,
        scroll_widget: bs.Widget,
        extra_x: float,
    ) -> bs.Widget:

        b_size_2 = 100
        spacing_h = -50
        spacing_v = 60

        self.parent_widget = parent_widget

        self._scroll_width = region_width * 0.8
        self._scroll_height = region_height * 0.6
        self._scroll_position = ((region_width - self._scroll_width) * 0.5,
                                 (region_height - self._scroll_height) * 0.5)

        self._sub_width = self._scroll_width
        self._sub_height = 200

        self.container_h = 450
        power_height = self.container_h - 50

        self._subcontainer = bui.containerwidget(
            parent=scroll_widget,
            size=(self._sub_width, self.container_h),
            background=False,
            selection_loops_to_parent=True)

        bui.textwidget(parent=self._subcontainer,
                       position=(self._sub_width * 0.5,
                                 power_height),
                       size=(0, 0),
                       color=(1.0, 1.0, 1.0),
                       scale=1.3,
                       h_align='center',
                       v_align='center',
                       text='Spawn Power Up',
                       maxwidth=200)

        self._power_button = bot = bui.buttonwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(self._sub_width * 0.5 - b_size_2 * 0.5,
                      power_height + spacing_h * 3),
            on_activate_call=self._power_window,
            size=(b_size_2, b_size_2),
            label='',
            color=(1, 1, 1),
            texture=bui.gettexture('powerup' +
                                   self.power_list[
                                       self._icon_index]))

        bui.textwidget(
            parent=self._subcontainer,
            h_align='center',
            v_align='center',
            position=(self._sub_width * 0.5,
                      power_height + spacing_h * 4 + 10),
            size=(0, 0),
            draw_controller=bot,
            text='Power Up Type',
            scale=1.0,
            color=bui.app.ui_v1.title_color,
            maxwidth=300)

        self.button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(
                self._sub_width * 0.25 - 40,
                power_height
                + spacing_h * 6),
            size=(80, 50),
            autoselect=True,
            button_type='square',
            label='Spawn',
            on_activate_call=self.get_powerup)

        self.button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(
                self._sub_width * 0.75 - 40,
                power_height
                + spacing_h * 6),
            size=(80, 50),
            autoselect=True,
            button_type='square',
            color=(1, 0.2, 0.2),
            label='Debuff',
            on_activate_call=self.debuff)

        i = 0
        for name in self.setting_name:
            bui.textwidget(parent=self._subcontainer,
                           position=(self._sub_width * 0.005,
                                     power_height + spacing_h * (7 + i)),
                           size=(100, 30),
                           text=name,
                           h_align='left',
                           color=(0.8, 0.8, 0.8),
                           v_align='center',
                           maxwidth=200)
            value = babase.app.config.get(self.config[i])
            txt2 = bui.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.8 - spacing_v / 2,
                          power_height +
                          spacing_h * (7 + i)),
                size=(0, 28),
                text=bs.Lstr(resource='onText') if value else bs.Lstr(
                    resource='offText'),
                editable=False,
                color=(0.6, 1.0, 0.6),
                maxwidth=400,
                h_align='right',
                v_align='center',
                padding=2)
            bui.checkboxwidget(parent=self._subcontainer,
                               text='',
                               position=(self._sub_width * 0.8 - 15,
                                         power_height +
                                         spacing_h * (7 + i)),
                               size=(30, 30),
                               autoselect=False,
                               textcolor=(0.8, 0.8, 0.8),
                               value=value,
                               on_value_change_call=bs.Call(
                                   self._check_value_change,
                                   i, txt2))
            i += 1

        return self._subcontainer

    def debuff(self):
        bs.screenmessage('Debuffed', color=(1, 0.1, 0.1))
        activity = bs.get_foreground_host_activity()
        with activity.context:
            for i in activity.players:
                Spaz._gloves_wear_off(i.actor)
                Spaz._multi_bomb_wear_off(i.actor)
                Spaz._bomb_wear_off(i.actor)
                i.actor.node.mini_billboard_1_end_time = 0
                i.actor.node.mini_billboard_2_end_time = 0
                i.actor.node.mini_billboard_3_end_time = 0
                i.actor._multi_bomb_wear_off_flash_timer = None
                i.actor._boxing_gloves_wear_off_flash_timer = None
                i.actor._bomb_wear_off_flash_timer = None
                Spaz.set_land_mine_count(i.actor, min(0, 0))
                i.actor.shield_hitpoints = 1

    def get_powerup(self, clid: int = -1) -> None:
        bs.screenmessage('Spawned', color=(0.2, 1, 0.2))
        activity = bs.get_foreground_host_activity()
        with activity.context:
            for i in activity.players:
                if i.sessionplayer.inputdevice.client_id == clid:
                    if i.node:
                        x = (random.choice([-7, 7]) / 10)
                        z = (random.choice([-7, 7]) / 10)
                        pos = (i.node.position[0] + x,
                               i.node.position[1],
                               i.node.position[2] + z)
                        PowerupBox(position=pos,
                                   poweruptype=self.power_list_type
                                   [self._icon_index]).autoretain()

    def _power_window(self) -> None:
        PowerPicker(
            parent=self.parent_widget,
            delegate=self)

    def on_power_picker_pick(self, power: str) -> None:
        """A power up has been selected by the picker."""
        if not self.parent_widget:
            return

        # The player could have bought a new one while the picker was u
        self._icon_index = self.power_list.index(
            power) if power in self.power_list else 0
        self._update_power()

    def _update_power(self, change: int = 0) -> None:
        if self._power_button:
            bui.buttonwidget(
                edit=self._power_button,
                texture=(bui.gettexture('powerup' +
                                        self.power_list[
                                            self._icon_index])))
        self.save_settings()

    def _check_value_change(self, setting: int, widget: bs.Widget,
                            value: str) -> None:
        bui.textwidget(edit=widget,
                       text=bs.Lstr(resource='onText') if value else bs.Lstr(
                           resource='offText'))

        activity = bs.get_foreground_host_activity()
        with activity.context:
            if setting == 0:
                if value:
                    babase.app.config["bombCountdown"] = True
                else:
                    babase.app.config["bombCountdown"] = False
            elif setting == 1:
                if value:
                    babase.app.config["bombRadiusVisual"] = True
                else:
                    babase.app.config["bombRadiusVisual"] = False

    def load_settings(self):
        try:
            if babase.app.config.get("powerSpawnSetting") is None:
                babase.app.config["powerSpawnSetting"] = 0
                power_index = babase.app.config.get("powerSpawnSetting")
            else:
                power_index = babase.app.config.get(
                    "powerSpawnSetting")
        except:
            babase.app.config["powerSpawnSetting"] = 0
            power_index = babase.app.config.get("powerSpawnSetting")
        values = power_index
        return values

    def save_settings(self):
        babase.app.config["powerSpawnSetting"] = self._icon_index
        babase.app.config.commit()


class OthersPracticeTab(PracticeTab):
    """The about tab in the practice UI"""

    def __init__(self, window: PracticeWindow) -> None:
        super().__init__(window)
        self._container: bs.Widget | None = None
        self.count = 1
        self.parent_widget = None
        self.activity = bs.get_foreground_host_activity()
        self.setting_name = (['Pause On Window', 'Invincible', 'Epic Mode'])
        self.config = (['pause', 'invincible'])

    def on_activate(
        self,
        parent_widget: bs.Widget,
        tab_button: bs.Widget,
        region_width: float,
        region_height: float,
        scroll_widget: bs.Widget,
        extra_x: float,
    ) -> bs.Widget:
        spacing_v = 60
        spacing_h = -50

        self.parent_widget = parent_widget

        self._scroll_width = region_width * 0.8
        self._scroll_height = region_height * 0.6
        self._scroll_position = ((region_width - self._scroll_width) * 0.5,
                                 (region_height - self._scroll_height) * 0.5)

        self._sub_width = self._scroll_width

        self.container_h = 300
        other_height = self.container_h - 50

        self._subcontainer = bui.containerwidget(
            parent=scroll_widget,
            size=(self._sub_width, self.container_h),
            background=False,
            selection_loops_to_parent=True)

        bui.textwidget(parent=self._subcontainer,
                       position=(self._sub_width * 0.5,
                                 other_height),
                       size=(0, 0),
                       color=(1.0, 1.0, 1.0),
                       scale=1.3,
                       h_align='center',
                       v_align='center',
                       text='Others',
                       maxwidth=200)

        i = 0
        for name in self.setting_name:
            bui.textwidget(parent=self._subcontainer,
                           position=(self._sub_width * 0.005,
                                     other_height + spacing_h * (2 + i)),
                           size=(100, 30),
                           text=name,
                           h_align='left',
                           color=(0.8, 0.8, 0.8),
                           v_align='center',
                           maxwidth=200)
            if name == 'Epic Mode':
                activity = bs.get_foreground_host_activity()
                value = activity.globalsnode.slow_motion
            else:
                value = babase.app.config.get(self.config[i])
            txt2 = bui.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.8 - spacing_v / 2,
                          other_height +
                          spacing_h * (2 + i)),
                size=(0, 28),
                text=bs.Lstr(resource='onText') if value else bs.Lstr(
                    resource='offText'),
                editable=False,
                color=(0.6, 1.0, 0.6),
                maxwidth=400,
                h_align='right',
                v_align='center',
                padding=2)
            bui.checkboxwidget(parent=self._subcontainer,
                               text='',
                               position=(self._sub_width * 0.8 - 15,
                                         other_height +
                                         spacing_h * (2 + i)),
                               size=(30, 30),
                               autoselect=False,
                               textcolor=(0.8, 0.8, 0.8),
                               value=value,
                               on_value_change_call=bs.Call(
                                   self._check_value_change,
                                   i, txt2))
            i += 1

        return self._subcontainer

    def _check_value_change(self, setting: int, widget: bs.Widget,
                            value: str) -> None:
        bui.textwidget(edit=widget,
                       text=bs.Lstr(resource='onText') if value else bs.Lstr(
                           resource='offText'))

        activity = bs.get_foreground_host_activity()
        with activity.context:
            if setting == 0:
                if value:
                    babase.app.config["pause"] = True
                    self.activity.globalsnode.paused = True
                else:
                    babase.app.config["pause"] = False
                    self.activity.globalsnode.paused = False
            elif setting == 1:
                if value:
                    babase.app.config["invincible"] = True
                else:
                    babase.app.config["invincible"] = False
                for i in bs.get_foreground_host_activity().players:
                    try:
                        if i.node:
                            if babase.app.config.get("invincible"):
                                i.actor.node.invincible = True
                            else:
                                i.actor.node.invincible = False
                    except:
                        pass
            elif setting == 2:
                activity = bs.get_foreground_host_activity()
                if value:
                    activity.globalsnode.slow_motion = True
                else:
                    activity.globalsnode.slow_motion = False


class PracticeWindow(bui.Window):
    class TabID(Enum):
        """Our available tab types."""

        BOTS = 'bots'
        POWERUP = 'power up'
        OTHERS = 'others'

    def __del__(self):
        bui.set_party_icon_always_visible(True)
        self.activity.globalsnode.paused = False

    def __init__(self,
                 transition: Optional[str] = 'in_right'):

        self.activity = bs.get_foreground_host_activity()
        bui.set_party_icon_always_visible(False)
        if babase.app.config.get("pause"):
            self.activity.globalsnode.paused = True
        uiscale = bui.app.ui_v1.uiscale
        self.pick = 0
        self._width = 500

        self._height = (578 if uiscale is babase.UIScale.SMALL else
                        670 if uiscale is babase.UIScale.MEDIUM else 800)
        extra_x = 100 if uiscale is babase.UIScale.SMALL else 0
        self.extra_x = extra_x

        self._transitioning_out = False

        b_size_2 = 100

        spacing_h = -50
        spacing = -450
        spacing_v = 60
        self.container_h = 500
        v = self._height - 115.0
        v -= spacing_v * 3.0

        super().__init__(root_widget=bui.containerwidget(
            size=(self._width, self._height),
            transition=transition,
            scale=(1.3 if uiscale is babase.UIScale.SMALL else
                   0.97 if uiscale is babase.UIScale.MEDIUM else 0.8),
            stack_offset=(0, -10) if uiscale is babase.UIScale.SMALL else (
                240, 0) if uiscale is babase.UIScale.MEDIUM else (330, 20)))

        self._sub_height = 200

        self._scroll_width = self._width * 0.8
        self._scroll_height = self._height * 0.6
        self._scroll_position = ((self._width - self._scroll_width) * 0.5,
                                 (self._height - self._scroll_height) * 0.5)

        self._scrollwidget = bui.scrollwidget(parent=self._root_widget,
                                              size=(self._scroll_width,
                                                    self._scroll_height),
                                              color=(0.55, 0.55, 0.55),
                                              highlight=False,
                                              position=self._scroll_position)

        bui.containerwidget(edit=self._scrollwidget,
                            claims_left_right=True)

        # ---------------------------------------------------------

        x_offs = 100 if uiscale is babase.UIScale.SMALL else 0

        self._current_tab: PracticeWindow.TabID | None = None
        extra_top = 20 if uiscale is babase.UIScale.SMALL else 0
        self._r = 'gatherWindow'

        tabdefs: list[tuple[PracticeWindow.TabID, str]] = [
            (self.TabID.BOTS, 'Bots')
        ]
        if bui.app.plus.get_v1_account_misc_read_val(
            'enablePublicParties', True
        ):
            tabdefs.append(
                (
                    self.TabID.POWERUP,
                    'Power Ups')
            )
        tabdefs.append(
            (self.TabID.OTHERS, 'Others')
        )

        condensed = uiscale is not babase.UIScale.LARGE
        t_offs_y = (
            0 if not condensed else 25 if uiscale is babase.UIScale.MEDIUM else 17
        )

        tab_buffer_h = (320 if condensed else 250) + 2 * x_offs

        self._sub_width = self._width * 0.8

        # On small UI, push our tabs up closer to the top of the screen to
        # save a bit of space.
        tabs_top_extra = 42 if condensed else 0
        self._tab_row = TabRow(
            self._root_widget,
            tabdefs,
            pos=(
                self._width * 0.5 - self._sub_width * 0.5,
                self._height * 0.79),
            size=(self._sub_width, 50),
            on_select_call=bui.WeakCall(self._set_tab),
        )

        # Now instantiate handlers for these tabs.
        tabtypes: dict[PracticeWindow.TabID, type[PracticeTab]] = {
            self.TabID.BOTS: BotsPracticeTab,
            self.TabID.POWERUP: PowerUpPracticeTab,
            self.TabID.OTHERS: OthersPracticeTab,
        }
        self._tabs: dict[PracticeWindow.TabID, PracticeTab] = {}
        for tab_id in self._tab_row.tabs:
            tabtype = tabtypes.get(tab_id)
            if tabtype is not None:
                self._tabs[tab_id] = tabtype(self)

        if bui.app.ui_v1.use_toolbars:
            bui.widget(
                edit=self._tab_row.tabs[tabdefs[-1][0]].button,
                right_widget=babase.get_special_widget('party_button'),
            )
            if uiscale is babase.UIScale.SMALL:
                bui.widget(
                    edit=self._tab_row.tabs[tabdefs[0][0]].button,
                    left_widget=babase.get_special_widget('back_button'),
                )

        # -----------------------------------------------------------

        self.back_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(self._width * 0.15 - 30,
                      self._height * 0.95 - 30),
            size=(60, 60),
            scale=1.1,
            label=bui.charstr(bui.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self.close)
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        bui.textwidget(parent=self._root_widget,
                       position=(self._width * 0.5,
                                 self._height * 0.95),
                       size=(0, 0),
                       color=bui.app.ui_v1.title_color,
                       scale=1.5,
                       h_align='center',
                       v_align='center',
                       text='Practice Tools',
                       maxwidth=400)

        self.info_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(self._width * 0.8 - 30,
                      self._height * 0.15 - 30),
            on_activate_call=self._info_window,
            size=(60, 60),
            label='')

        bui.imagewidget(
            parent=self._root_widget,
            position=(self._width * 0.8 - 25,
                      self._height * 0.15 - 25),
            size=(50, 50),
            draw_controller=self.info_button,
            texture=bui.gettexture('achievementEmpty'),
            color=(1.0, 1.0, 1.0))

        self._tab_container: bui.Widget | None = None

        self._restore_state()

        # # -------------------------------------------------------

    def _info_window(self):
        InfoWindow(
            parent=self._root_widget)

    def _button(self) -> None:
        bui.buttonwidget(edit=None,
                         color=(0.2, 0.4, 0.8))

    def close(self) -> None:
        """Close the window."""
        bui.containerwidget(edit=self._root_widget, transition='out_right')

    def _set_tab(self, tab_id: TabID) -> None:
        if self._current_tab is tab_id:
            return
        prev_tab_id = self._current_tab
        self._current_tab = tab_id

        # We wanna preserve our current tab between runs.
        cfg = babase.app.config
        cfg['Practice Tab'] = tab_id.value
        cfg.commit()

        # Update tab colors based on which is selected.
        self._tab_row.update_appearance(tab_id)

        if prev_tab_id is not None:
            prev_tab = self._tabs.get(prev_tab_id)
            if prev_tab is not None:
                prev_tab.on_deactivate()

        # Clear up prev container if it hasn't been done.
        if self._tab_container:
            self._tab_container.delete()

        tab = self._tabs.get(tab_id)
        if tab is not None:
            self._tab_container = tab.on_activate(
                self._root_widget,
                self._tab_row.tabs[tab_id].button,
                self._width,
                self._height,
                self._scrollwidget,
                self.extra_x,
            )
            return

    def _restore_state(self) -> None:
        from efro.util import enum_by_value

        try:
            for tab in self._tabs.values():
                tab.restore_state()

            sel: bui.Widget | None
            winstate = bui.app.ui_v1.window_states.get(type(self), {})
            sel_name = winstate.get('sel_name', None)
            assert isinstance(sel_name, (str, type(None)))
            current_tab = self.TabID.BOTS
            gather_tab_val = babase.app.config.get('Practice Tab')
            try:
                stored_tab = enum_by_value(self.TabID, gather_tab_val)
                if stored_tab in self._tab_row.tabs:
                    current_tab = stored_tab
            except ValueError:
                pass
            self._set_tab(current_tab)
            if sel_name == 'back':
                sel = self.back_button
            elif sel_name == 'TabContainer':
                sel = self._tab_container
            elif isinstance(sel_name, str) and sel_name.startswith('Tab:'):
                try:
                    sel_tab_id = enum_by_value(
                        self.TabID, sel_name.split(':')[-1]
                    )
                except ValueError:
                    sel_tab_id = self.TabID.BOTS
                sel = self._tab_row.tabs[sel_tab_id].button
            else:
                sel = self._tab_row.tabs[current_tab].button
            bui.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            babase.print_exception('Error restoring gather-win state.')


org_begin = bs._activity.Activity.on_begin


def new_begin(self):
    """Runs when game is began."""
    org_begin(self)
    bui.set_party_icon_always_visible(True)


bs._activity.Activity.on_begin = new_begin


class BotPicker(popup.PopupWindow):
    """Popup window for selecting bots to spwan."""

    def __init__(self,
                 parent: bui.Widget,
                 position: tuple[float, float] = (0.0, 0.0),
                 delegate: Any = None,
                 scale: float | None = None,
                 offset: tuple[float, float] = (0.0, 0.0),
                 selected_character: str | None = None):
        del parent  # unused here
        uiscale = bui.app.ui_v1.uiscale
        if scale is None:
            scale = (1.85 if uiscale is babase.UIScale.SMALL else
                     1.65 if uiscale is babase.UIScale.MEDIUM else 1.23)

        self._delegate = delegate
        self._transitioning_out = False

        count = 16

        columns = 3
        rows = int(math.ceil(float(count) / columns))

        button_width = 100
        button_height = 100
        button_buffer_h = 10
        button_buffer_v = 15

        self._width = (10 + columns * (button_width + 2 * button_buffer_h) *
                       (1.0 / 0.95) * (1.0 / 0.8))
        self._height = self._width * (0.8
                                      if uiscale is babase.UIScale.SMALL else 1.06)

        self._scroll_width = self._width * 0.8
        self._scroll_height = self._height * 0.8
        self._scroll_position = ((self._width - self._scroll_width) * 0.5,
                                 (self._height - self._scroll_height) * 0.5)

        # creates our _root_widget
        popup.PopupWindow.__init__(self,
                                   position=position,
                                   size=(self._width, self._height),
                                   scale=scale,
                                   bg_color=(0.5, 0.5, 0.5),
                                   offset=offset,
                                   focus_position=self._scroll_position,
                                   focus_size=(self._scroll_width,
                                               self._scroll_height))

        self._scrollwidget = bui.scrollwidget(parent=self.root_widget,
                                              size=(self._scroll_width,
                                                    self._scroll_height),
                                              color=(0.55, 0.55, 0.55),
                                              highlight=False,
                                              position=self._scroll_position)

        bui.containerwidget(edit=self._scrollwidget, claims_left_right=True)

        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 5 + rows * (button_height +
                                       2 * button_buffer_v) + 100
        self._subcontainer = bui.containerwidget(parent=self._scrollwidget,
                                                 size=(self._sub_width,
                                                       self._sub_height),
                                                 background=False)

        mask_texture = bui.gettexture('characterIconMask')

        bot_list = (['bones', 'neoSpaz', 'kronk', 'neoSpaz', 'kronk', 'zoe',
                     'ninja', 'mel', 'jack', 'bunny',
                     'neoSpaz', 'kronk', 'zoe',
                     'ninja',
                     'neoSpaz', 'kronk', 'zoe',
                     'ninja'])
        bot_list_type = (
            ['Dummy', 'Bomber Lite', 'Brawler Lite', 'Bomber', 'Brawler',
             'Trigger',
             'Charger', 'Sticky', 'Explodey', 'Bouncy',
             'Pro Bomber', 'Pro Brawler', 'Pro Trigger',
             'Pro Charger', 'S.Pro Bomber', 'S.Pro Brawler',
             'S.Pro Trigger', 'S.Pro Charger'])

        index = 0
        for y in range(rows):
            for x in range(columns):

                if bot_list_type[index] in ('Pro Bomber', 'Pro Brawler',
                                            'Pro Trigger', 'Pro Charger',
                                            'S.Pro Bomber', 'S.Pro Brawler',
                                            'S.Pro Trigger', 'S.Pro Charger'):
                    tint1 = (1.0, 0.2, 0.1)
                    tint2 = (0.6, 0.1, 0.05)
                elif bot_list_type[index] in 'Bouncy':
                    tint1 = (1, 1, 1)
                    tint2 = (1.0, 0.5, 0.5)
                elif bot_list_type[index] in ('Brawler Lite',
                                              'Bomber Lite'):
                    tint1 = (1.2, 0.9, 0.2)
                    tint2 = (1.0, 0.5, 0.6)
                else:
                    tint1 = (0.6, 0.6, 0.6)
                    tint2 = (0.1, 0.3, 0.1)

                if bot_list_type[index] in ('S.Pro Bomber', 'S.Pro Brawler',
                                            'S.Pro Trigger', 'S.Pro Charger'):
                    color = (1.3, 1.2, 3.0)
                else:
                    color = (1.0, 1.0, 1.0)
                pos = (x * (button_width + 2 * button_buffer_h) +
                       button_buffer_h, self._sub_height - (y + 1) *
                       (button_height + 2 * button_buffer_v) + 12)
                btn = bui.buttonwidget(
                    parent=self._subcontainer,
                    button_type='square',
                    position=(pos[0],
                              pos[1]),
                    size=(button_width, button_height),
                    autoselect=True,
                    texture=bui.gettexture(bot_list[index] + 'Icon'),
                    tint_texture=bui.gettexture(
                        bot_list[index] + 'IconColorMask'),
                    mask_texture=mask_texture,
                    label='',
                    color=color,
                    tint_color=tint1,
                    tint2_color=tint2,
                    on_activate_call=bui.Call(self._select_character,
                                              character=bot_list_type[index]))
                bui.widget(edit=btn, show_buffer_top=60, show_buffer_bottom=60)

                name = bot_list_type[index]
                bui.textwidget(parent=self._subcontainer,
                               text=name,
                               position=(pos[0] + button_width * 0.5,
                                         pos[1] - 12),
                               size=(0, 0),
                               scale=0.5,
                               maxwidth=button_width,
                               draw_controller=btn,
                               h_align='center',
                               v_align='center',
                               color=(0.8, 0.8, 0.8, 0.8))

                index += 1
                if index >= len(bot_list):
                    break
            if index >= len(bot_list):
                break

    def _select_character(self, character: str) -> None:
        if self._delegate is not None:
            self._delegate.on_bots_picker_pick(character)
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._transition_out()


class PowerPicker(popup.PopupWindow):
    """Popup window for selecting power up."""

    def __init__(self,
                 parent: bui.Widget,
                 position: tuple[float, float] = (0.0, 0.0),
                 delegate: Any = None,
                 scale: float | None = None,
                 offset: tuple[float, float] = (0.0, 0.0),
                 selected_character: str | None = None):
        del parent  # unused here

        if scale is None:
            uiscale = bui.app.ui_v1.uiscale
            scale = (1.85 if uiscale is babase.UIScale.SMALL else
                     1.65 if uiscale is babase.UIScale.MEDIUM else 1.23)

        self._delegate = delegate
        self._transitioning_out = False

        count = 7

        columns = 3
        rows = int(math.ceil(float(count) / columns))

        button_width = 100
        button_height = 100
        button_buffer_h = 10
        button_buffer_v = 15

        self._width = (10 + columns * (button_width + 2 * button_buffer_h) *
                       (1.0 / 0.95) * (1.0 / 0.8))
        self._height = self._width * (0.8
                                      if uiscale is babase.UIScale.SMALL else 1.06)

        self._scroll_width = self._width * 0.8
        self._scroll_height = self._height * 0.8
        self._scroll_position = ((self._width - self._scroll_width) * 0.5,
                                 (self._height - self._scroll_height) * 0.5)

        # creates our _root_widget
        popup.PopupWindow.__init__(self,
                                   position=position,
                                   size=(self._width, self._height),
                                   scale=scale,
                                   bg_color=(0.5, 0.5, 0.5),
                                   offset=offset,
                                   focus_position=self._scroll_position,
                                   focus_size=(self._scroll_width,
                                               self._scroll_height))

        self._scrollwidget = bui.scrollwidget(parent=self.root_widget,
                                              size=(self._scroll_width,
                                                    self._scroll_height),
                                              color=(0.55, 0.55, 0.55),
                                              highlight=False,
                                              position=self._scroll_position)

        bui.containerwidget(edit=self._scrollwidget, claims_left_right=True)

        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 5 + rows * (button_height +
                                       2 * button_buffer_v) + 100
        self._subcontainer = bui.containerwidget(parent=self._scrollwidget,
                                                 size=(self._sub_width,
                                                       self._sub_height),
                                                 background=False)

        power_list = (['Bomb', 'Curse', 'Health', 'IceBombs',
                       'ImpactBombs', 'LandMines', 'Punch',
                       'Shield', 'StickyBombs'])

        power_list_type = (['Tripple Bomb', 'Curse', 'Health', 'Ice Bombs',
                            'Impact Bombs', 'Land Mines', 'Punch',
                            'Shield', 'Sticky Bombs'])

        index = 0
        for y in range(rows):
            for x in range(columns):
                pos = (x * (button_width + 2 * button_buffer_h) +
                       button_buffer_h, self._sub_height - (y + 1) *
                       (button_height + 2 * button_buffer_v) + 12)
                btn = bui.buttonwidget(
                    parent=self._subcontainer,
                    button_type='square',
                    position=(pos[0],
                              pos[1]),
                    size=(button_width, button_height),
                    autoselect=True,
                    texture=bui.gettexture('powerup' + power_list[index]),
                    label='',
                    color=(1, 1, 1),
                    on_activate_call=bui.Call(self._select_power,
                                              power=power_list[index]))
                bui.widget(edit=btn, show_buffer_top=60, show_buffer_bottom=60)

                name = power_list_type[index]
                bui.textwidget(parent=self._subcontainer,
                               text=name,
                               position=(pos[0] + button_width * 0.5,
                                         pos[1] - 12),
                               size=(0, 0),
                               scale=0.5,
                               maxwidth=button_width,
                               draw_controller=btn,
                               h_align='center',
                               v_align='center',
                               color=(0.8, 0.8, 0.8, 0.8))

                index += 1
                if index >= len(power_list):
                    break
            if index >= len(power_list):
                break

    def _select_power(self, power: str) -> None:
        if self._delegate is not None:
            self._delegate.on_power_picker_pick(power)
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._transition_out()


class InfoWindow(popup.PopupWindow):
    """Popup window for Infos."""

    def __init__(self,
                 parent: bs.Widget,
                 position: tuple[float, float] = (0.0, 0.0),
                 delegate: Any = None,
                 scale: float | None = None,
                 offset: tuple[float, float] = (0.0, 0.0),
                 selected_character: str | None = None):
        del parent  # unused here

        if scale is None:
            uiscale = bui.app.ui_v1.uiscale
            scale = (1.85 if uiscale is babase.UIScale.SMALL else
                     1.65 if uiscale is babase.UIScale.MEDIUM else 1.23)

        self._delegate = delegate
        self._transitioning_out = False

        self._width = 600
        self._height = self._width * (0.6
                                      if uiscale is babase.UIScale.SMALL else 0.795)

        # creates our _root_widget
        popup.PopupWindow.__init__(self,
                                   position=position,
                                   size=(self._width, self._height),
                                   scale=scale,
                                   bg_color=(0.5, 0.5, 0.5),
                                   offset=offset,
                                   focus_size=(self._width,
                                               self._height))

        bui.textwidget(parent=self.root_widget,
                       position=(self._width * 0.5,
                                 self._height * 0.9),
                       size=(0, 0),
                       color=bui.app.ui_v1.title_color,
                       scale=1.3,
                       h_align='center',
                       v_align='center',
                       text='About',
                       maxwidth=200)

        text = ('Practice Tools Mod\n'
                'Made By Cross Joy\n'
                'version v' + version + '\n'
                '\n'
                'Thx to\n'
                'Mikirog for the Bomb radius visualizer mod.\n'
                )

        lines = text.splitlines()
        line_height = 16
        scale_t = 0.56

        voffs = 0
        i = 0
        for line in lines:
            i += 1
            if i <= 3:
                color = (1.0, 1.0, 1.0, 1.0)
            else:
                color = (0.4, 1.0, 1.4, 1.0)

            bui.textwidget(
                parent=self.root_widget,
                padding=4,
                color=color,
                scale=scale_t,
                flatness=1.0,
                size=(0, 0),
                position=(self._width * 0.5, self._height * 0.8 + voffs),
                h_align='center',
                v_align='top',
                text=line)
            voffs -= line_height

        text_spacing = 70

        self.button_discord = bui.buttonwidget(
            parent=self.root_widget,
            position=(
                self._width * 0.25 - 40, self._height * 0.2 - 40),
            size=(80, 80),
            autoselect=True,
            button_type='square',
            color=(0.447, 0.537, 0.854),
            label='',
            on_activate_call=self._discord)
        bui.imagewidget(
            parent=self.root_widget,
            position=(self._width * 0.25 - 25,
                      self._height * 0.2 - 25),
            size=(50, 50),
            draw_controller=self.button_discord,
            texture=bui.gettexture('discordLogo'),
            color=(5, 5, 5))
        bui.textwidget(
            parent=self.root_widget,
            position=(self._width * 0.25,
                      self._height * 0.2 + text_spacing),
            size=(0, 0),
            scale=0.75,
            draw_controller=self.button_discord,
            text='Join us. :D',
            h_align='center',
            v_align='center',
            maxwidth=150,
            color=(0.447, 0.537, 0.854))

        self.button_github = bui.buttonwidget(
            parent=self.root_widget,
            position=(
                self._width * 0.5 - 40, self._height * 0.2 - 40),
            size=(80, 80),
            autoselect=True,
            button_type='square',
            color=(0.129, 0.122, 0.122),
            label='',
            on_activate_call=self._github)
        bui.imagewidget(
            parent=self.root_widget,
            position=(self._width * 0.5 - 25,
                      self._height * 0.2 - 25),
            size=(50, 50),
            draw_controller=self.button_github,
            texture=bui.gettexture('githubLogo'),
            color=(1, 1, 1))
        bui.textwidget(
            parent=self.root_widget,
            position=(self._width * 0.5,
                      self._height * 0.2 + text_spacing),
            size=(0, 0),
            scale=0.75,
            draw_controller=self.button_github,
            text='Found Bugs?',
            h_align='center',
            v_align='center',
            maxwidth=150,
            color=(0.129, 0.122, 0.122))

        self.button_support = bui.buttonwidget(
            parent=self.root_widget,
            position=(
                self._width * 0.75 - 40, self._height * 0.2 - 40),
            size=(80, 80),
            autoselect=True,
            button_type='square',
            color=(0.83, 0.69, 0.21),
            label='',
            on_activate_call=self._support)
        bui.imagewidget(
            parent=self.root_widget,
            position=(self._width * 0.75 - 25,
                      self._height * 0.2 - 25),
            size=(50, 50),
            draw_controller=self.button_support,
            texture=bui.gettexture('heart'),
            color=(1, 1, 1))
        bui.textwidget(
            parent=self.root_widget,
            position=(self._width * 0.75,
                      self._height * 0.2 + text_spacing),
            size=(0, 0),
            scale=0.75,
            draw_controller=self.button_support,
            text='Support uwu.',
            h_align='center',
            v_align='center',
            maxwidth=150,
            color=(0.83, 0.69, 0.21))

    def _discord(self):
        bui.open_url('https://discord.gg/JyBY6haARJ')

    def _github(self):
        bui.open_url('https://github.com/CrossJoy/Bombsquad-Modding')

    def _support(self):
        bui.open_url('https://www.buymeacoffee.com/CrossJoy')

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._transition_out()
