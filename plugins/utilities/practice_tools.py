"""Practice Tools Mod: V1.0
Made by Cross Joy"""

# If anyone who want to help me on giving suggestion/ fix bugs/ creating PR,
# Can visit my github https://github.com/CrossJoy/Bombsquad-Modding

# You can contact me through discord:
# My Discord Id: Cross Joy#0721
# My BS Discord Server: https://discord.gg/JyBY6haARJ

# Some support will be much appreciated. :')
# Support link: https://www.buymeacoffee.com/CrossJoy


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

import random
import weakref
from enum import Enum
from typing import TYPE_CHECKING
import ba, _ba
import ba.internal
import bastd
from bastd.actor.powerupbox import PowerupBox
from bastd.actor.spaz import Spaz
from bastd.actor.spazbot import (SpazBotSet, SpazBot, BrawlerBot, TriggerBot,
                                 ChargerBot, StickyBot, ExplodeyBot, BouncyBot,
                                 BomberBotPro, BrawlerBotPro, TriggerBotPro,
                                 ChargerBotPro, BomberBotProShielded,
                                 BrawlerBotProShielded, TriggerBotProShielded,
                                 ChargerBotProShielded)
from bastd.mainmenu import MainMenuSession
from bastd.ui.party import PartyWindow as OriginalPartyWindow
from ba import app, Plugin
from bastd.ui import popup
from bastd.actor.bomb import Bomb
import math

from bastd.ui.tabs import TabRow

if TYPE_CHECKING:
    from typing import Any, Sequence, Callable, Optional

try:
    if ba.app.config.get("bombCountdown") is None:
        ba.app.config["bombCountdown"] = False
    else:
        ba.app.config.get("bombCountdown")
except:
    ba.app.config["bombCountdown"] = False

try:
    if ba.app.config.get("bombRadiusVisual") is None:
        ba.app.config["bombRadiusVisual"] = False
    else:
        ba.app.config.get("bombRadiusVisual")
except:
    ba.app.config["bombRadiusVisual"] = False

try:
    if ba.app.config.get("stopBots") is None:
        ba.app.config["stopBots"] = False
    else:
        ba.app.config.get("stopBots")
except:
    ba.app.config["stopBots"] = False

try:
    if ba.app.config.get("stopBots") is None:
        ba.app.config["stopBots"] = False
    else:
        ba.app.config.get("stopBots")
except:
    ba.app.config["stopBots"] = False

try:
    if ba.app.config.get("immortalDummy") is None:
        ba.app.config["immortalDummy"] = False
    else:
        ba.app.config.get("immortalDummy")
except:
    ba.app.config["immortalDummy"] = False

try:
    if ba.app.config.get("invincible") is None:
        ba.app.config["invincible"] = False
    else:
        ba.app.config.get("invincible")
except:
    ba.app.config["invincible"] = False

_ba.set_party_icon_always_visible(True)


def is_game_version_lower_than(version):
    """
    Returns a boolean value indicating whether the current game
    version is lower than the passed version. Useful for addressing
    any breaking changes within game versions.
    """
    game_version = tuple(map(int, ba.app.version.split(".")))
    version = tuple(map(int, version.split(".")))
    return game_version < version


if is_game_version_lower_than("1.7.7"):
    ba_internal = _ba
else:
    ba_internal = ba.internal


class PartyWindow(ba.Window):
    _redefine_methods = ['__init__']

    def __init__(self, *args, **kwargs):
        getattr(self, '__init___old')(*args, **kwargs)

        self.bg_color = (.5, .5, .5)

        self._edit_movements_button = ba.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(360, self._height - 47),
            # (self._width - 80, self._height - 47)
            size=(100, 50),
            label='Practice',
            autoselect=True,
            button_type='square',
            on_activate_call=ba.Call(doTestButton, self),
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


# ba_meta require api 7
# ba_meta export plugin
class Practice(Plugin):
    __version__ = '1.0'

    def on_app_running(self) -> None:
        """Plugin start point."""

        if app.build_number < 20427:
            ba.screenmessage(
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

            if ba.app.config.get("bombRadiusVisual"):
                args[0].radius_visualizer = ba.newnode('locator',
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

                ba.animate_array(args[0].radius_visualizer, 'size', 1, {
                    0.0: [0.0],
                    0.2: [args[0].blast_radius * 2.2],
                    0.25: [args[0].blast_radius * 2.0]
                })

                args[0].radius_visualizer_circle = ba.newnode(
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

                ba.animate(
                    args[0].radius_visualizer_circle, 'opacity', {
                        0: 0.0,
                        0.4: 0.1
                    })

                if bomb_type == 'tnt':
                    args[0].fatal = ba.newnode('locator',
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

                    ba.animate_array(args[0].fatal, 'size', 1, {
                        0.0: [0.0],
                        0.2: [args[0].blast_radius * 2.2 * 0.7],
                        0.25: [args[0].blast_radius * 2.0 * 0.7]
                    })

            if ba.app.config.get(
                "bombCountdown") and bomb_type not in fuse_bomb:
                color = (1.0, 1.0, 0.0)
                count_bomb(*args, count='3', color=color)
                color = (1.0, 0.5, 0.0)
                ba.timer(1, ba.Call(count_bomb, *args, count='2', color=color))
                color = (1.0, 0.15, 0.15)
                ba.timer(2, ba.Call(count_bomb, *args, count='1', color=color))

        return setting

    bastd.actor.bomb.Bomb.__init__ = new_bomb_init(
        bastd.actor.bomb.Bomb.__init__)


Spaz._pm2_spz_old = Spaz.__init__


def _init_spaz_(self, *args, **kwargs):
    self._pm2_spz_old(*args, **kwargs)
    self.bot_radius = ba.newnode('locator',
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

    self.radius_visualizer_circle = ba.newnode(
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

    self.curse_visualizer = ba.newnode('locator',
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

    self.curse_visualizer_circle = ba.newnode(
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

    self.curse_visualizer_fatal = ba.newnode('locator',
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
        for i in _ba.get_foreground_host_activity().players:
            try:
                if i.node:
                    if ba.app.config.get("invincible"):
                        i.actor.node.invincible = True
                    else:
                        i.actor.node.invincible = False
            except:
                pass

    ba.timer(1.001, ba.Call(invincible))


Spaz.__init__ = _init_spaz_

Spaz.super_curse = Spaz.curse


def new_cursed(self):
    self.super_curse()
    if ba.app.config.get("bombRadiusVisual"):

        ba.animate_array(self.curse_visualizer, 'size', 1, {
            0.0: [0.0],
            0.2: [3 * 2.2],
            0.5: [3 * 2.0],
            5.0: [3 * 2.0],
            5.1: [0.0],
        })

        ba.animate(
            self.curse_visualizer_circle, 'opacity', {
                0: 0.0,
                0.4: 0.1,
                5.0: 0.1,
                5.1: 0.0,
            })

        ba.animate_array(self.curse_visualizer_fatal, 'size', 1, {
            0.0: [0.0],
            0.2: [2.2],
            0.5: [2.0],
            5.0: [2.0],
            5.1: [0.0],
        })


Spaz.curse = new_cursed

Spaz.super_handlemessage = Spaz.handlemessage


def bot_handlemessage(self, msg: Any):


    if isinstance(msg, ba.PowerupMessage):
        if msg.poweruptype == 'health':
            if ba.app.config.get("bombRadiusVisual"):
                if self._cursed:
                    ba.animate_array(self.curse_visualizer, 'size', 1, {
                        0.0: [3 * 2.0],
                        0.2: [0.0],
                    })

                    ba.animate(
                        self.curse_visualizer_circle, 'opacity', {
                            0.0: 0.1,
                            0.2: 0.0,
                        })

                    ba.animate_array(self.curse_visualizer_fatal, 'size', 1, {
                        0.0: [2.0],
                        0.2: [0.0],
                    })

                ba.animate_array(self.bot_radius, 'size', 1, {
                    0.0: [0],
                    0.25: [0]
                })
                ba.animate(self.bot_radius, 'opacity', {
                    0.0: 0.00,
                    0.25: 0.0
                })

                ba.animate_array(self.radius_visualizer_circle, 'size', 1, {
                    0.0: [0],
                    0.25: [0]
                })

                ba.animate(
                    self.radius_visualizer_circle, 'opacity', {
                        0.0: 0.00,
                        0.25: 0.0
                    })

    self.super_handlemessage(msg)

    if isinstance(msg, ba.HitMessage):
        if self.hitpoints <= 0:
            ba.animate(self.bot_radius, 'opacity', {
                0.0: 0.00
            })
            ba.animate(
                self.radius_visualizer_circle, 'opacity', {
                    0.0: 0.00
                })
        elif ba.app.config.get('bombRadiusVisual'):

            ba.animate_array(self.bot_radius, 'size', 1, {
                0.0: [(self.hitpoints_max - self.hitpoints) * 0.0048],
                0.25: [(self.hitpoints_max - self.hitpoints) * 0.0048]
            })
            ba.animate(self.bot_radius, 'opacity', {
                0.0: 0.00,
                0.25: 0.05
            })

            ba.animate_array(self.radius_visualizer_circle, 'size', 1, {
                0.0: [(self.hitpoints_max - self.hitpoints) * 0.0048],
                0.25: [(self.hitpoints_max - self.hitpoints) * 0.0048]
            })

            ba.animate(
                self.radius_visualizer_circle, 'opacity', {
                    0.0: 0.00,
                    0.25: 0.1
                })



Spaz.handlemessage = bot_handlemessage


def count_bomb(*args, count, color):
    text = ba.newnode('math', owner=args[0].node,
                      attrs={'input1': (0, 0.7, 0),
                             'operation': 'add'})
    args[0].node.connectattr('position', text, 'input2')
    args[0].spaztext = ba.newnode('text',
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
    ba.animate(args[0].spaztext, 'scale',
               {0: 0, 0.3: 0.03, 0.5: 0.025, 0.8: 0.025, 1.0: 0.0})


def doTestButton(self):
    if isinstance(_ba.get_foreground_host_session(), MainMenuSession):
        ba.screenmessage('Join any map to start using it.', color=(.8, .8, .1))
        return

    if ba.app.config.get("disablePractice"):
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.Call(PracticeWindow())
    else:
        ba.screenmessage('Only works on local games.', color=(.8, .8, .1))


# ---------------------------------------------------------------


class NewBotSet(SpazBotSet):

    def __init__(self):
        super().__init__()

    def _update(self) -> None:
            try:
                with ba.Context(_ba.get_foreground_host_activity()):
                    # Update one of our bot lists each time through.
                    # First off, remove no-longer-existing bots from the list.
                    try:
                        bot_list = self._bot_lists[self._bot_update_list] = ([
                            b for b in self._bot_lists[self._bot_update_list] if b
                        ])
                    except Exception:
                        bot_list = []
                        ba.print_exception('Error updating bot list: ' +
                                           str(self._bot_lists[
                                                   self._bot_update_list]))
                    self._bot_update_list = (self._bot_update_list +
                                             1) % self._bot_list_count

                    # Update our list of player points for the bots to use.
                    player_pts = []
                    for player in ba.getactivity().players:
                        assert isinstance(player, ba.Player)
                        try:
                            # TODO: could use abstracted player.position here so we
                            # don't have to assume their actor type, but we have no
                            # abstracted velocity as of yet.
                            if player.is_alive():
                                assert isinstance(player.actor, Spaz)
                                assert player.actor.node
                                player_pts.append(
                                    (ba.Vec3(player.actor.node.position),
                                     ba.Vec3(
                                         player.actor.node.velocity)))
                        except Exception:
                            ba.print_exception('Error on bot-set _update.')

                    for bot in bot_list:
                        if not ba.app.config.get('stopBots'):
                            bot.set_player_points(player_pts)
                            bot.update_ai()

                    ba.app.config["disablePractice"] = True
            except:
                ba.app.config["disablePractice"] = False

    def clear(self) -> None:
        """Immediately clear out any bots in the set."""
        with ba.Context(_ba.get_foreground_host_activity()):
            # Don't do this if the activity is shutting down or dead.
            activity = ba.getactivity(doraise=False)
            if activity is None or activity.expired:
                return

            for i, bot_list in enumerate(self._bot_lists):
                for bot in bot_list:
                    bot.handlemessage(ba.DieMessage(immediate=True))
                self._bot_lists[i] = []

    def spawn_bot(
        self,
        bot_type: type[SpazBot],
        pos: Sequence[float],
        spawn_time: float = 3.0,
        on_spawn_call: Callable[[SpazBot], Any] | None = None) -> None:
        """Spawn a bot from this set."""
        from bastd.actor import spawner
        spawner.Spawner(pt=pos,
                        spawn_time=spawn_time,
                        send_spawn_message=False,
                        spawn_callback=ba.Call(self._spawn_bot, bot_type, pos,
                                               on_spawn_call))
        self._spawning_count += 1

    def _spawn_bot(self, bot_type: type[SpazBot], pos: Sequence[float],
                   on_spawn_call: Callable[[SpazBot], Any] | None) -> None:
        spaz = bot_type().autoretain()
        ba.playsound(ba.getsound('spawn'), position=pos)
        assert spaz.node
        spaz.node.handlemessage('flash')
        spaz.node.is_area_of_interest = False
        spaz.handlemessage(ba.StandMessage(pos, random.uniform(0, 360)))
        self.add_bot(spaz)
        self._spawning_count -= 1
        if on_spawn_call is not None:
            on_spawn_call(spaz)


class DummyBotSet(NewBotSet):

    def _update(self) -> None:

            try:
                with ba.Context(_ba.get_foreground_host_activity()):
                    # Update one of our bot lists each time through.
                    # First off, remove no-longer-existing bots from the list.
                    try:
                        bot_list = self._bot_lists[self._bot_update_list] = ([
                            b for b in self._bot_lists[self._bot_update_list] if b
                        ])
                    except Exception:
                        ba.print_exception('Error updating bot list: ' +
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
        if ba.app.config.get('immortalDummy'):
            ba.timer(0.2, self.immortal,
                     repeat=True)

    def immortal(self):
        self.hitpoints = self.hitpoints_max = 10000
        ba.emitfx(
            position=self.node.position,
            count=20,
            emit_type='fairydust')


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
            raise ba.NotFoundError("PracticeTab's window no longer exists.")
        return window

    def on_activate(
        self,
        parent_widget: ba.Widget,
        tab_button: ba.Widget,
        region_width: float,
        region_height: float,
        scroll_widget: ba.Widget,
        extra_x: float,
    ) -> ba.Widget:
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


def _check_value_change(setting: int, widget: ba.Widget,
                        value: str) -> None:
    ba.textwidget(edit=widget,
                  text=ba.Lstr(resource='onText') if value else ba.Lstr(
                      resource='offText'))

    if setting == 0:
        if value:
            ba.app.config["stopBots"] = True
        else:
            ba.app.config["stopBots"] = False
    elif setting == 1:
        if value:
            ba.app.config["immortalDummy"] = True
        else:
            ba.app.config["immortalDummy"] = False


class BotsPracticeTab(PracticeTab):
    """The about tab in the practice UI"""

    def __init__(self, window: PracticeWindow,
                 bot1=DummyBotSet(), bot2=NewBotSet()) -> None:
        super().__init__(window)
        self._container: ba.Widget | None = None
        self.count = 1
        self.radius = 0
        self.radius_array = (['Small', 'Medium', 'Big'])
        self.parent_widget = None
        self.bot1 = bot1
        self.bot2 = bot2
        self.activity = _ba.get_foreground_host_activity()
        self.image_array = (
            ['bonesIcon', 'neoSpazIcon', 'kronkIcon',
             'zoeIcon', 'ninjaIcon', 'melIcon', 'jackIcon', 'bunnyIcon',
             'neoSpazIcon', 'kronkIcon', 'zoeIcon', 'ninjaIcon',
             'neoSpazIcon', 'kronkIcon', 'zoeIcon', 'ninjaIcon'])
        self.bot_array_name = (
            ['Dummy', 'Bomber', 'Bruiser',
             'Trigger', 'Charger', 'Sticky',
             'Explodey', 'Bouncy', 'Pro Bomber',
             'Pro Brawler', 'Pro Trigger', 'Pro Charger',
             'S.Pro Bomber', 'S.Pro Brawler',
             'S.Pro Trigger', 'S.Pro Charger'])

        self.setting_name = (['Stop Bots', 'Immortal Dummy'])
        self.config = (['stopBots', 'immortalDummy'])

        self.bot_array = (
            [DummyBot, SpazBot, BrawlerBot, TriggerBot,
             ChargerBot, StickyBot, ExplodeyBot, BouncyBot,
             BomberBotPro, BrawlerBotPro, TriggerBotPro, ChargerBotPro,
             BomberBotProShielded, BrawlerBotProShielded,
             TriggerBotProShielded, ChargerBotProShielded])

        self._icon_index = self.bot_array_name.index('Dummy')

    def on_activate(
        self,
        parent_widget: ba.Widget,
        tab_button: ba.Widget,
        region_width: float,
        region_height: float,
        scroll_widget: ba.Widget,
        extra_x: float,
    ) -> ba.Widget:

        b_size_2 = 100
        spacing_h = -50
        mask_texture = ba.gettexture('characterIconMask')
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

        self._subcontainer = ba.containerwidget(
            parent=scroll_widget,
            size=(self._sub_width, self.container_h),
            background=False,
            selection_loops_to_parent=True)

        ba.textwidget(parent=self._subcontainer,
                      position=(self._sub_width * 0.5,
                                bots_height),
                      size=(0, 0),
                      color=(1.0, 1.0, 1.0),
                      scale=1.3,
                      h_align='center',
                      v_align='center',
                      text='Spawn Bot',
                      maxwidth=200)

        self._bot_button = bot = ba.buttonwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(self._sub_width * 0.5 - b_size_2 * 0.5,
                      bots_height + spacing_h * 3),
            on_activate_call=self._bot_window,
            size=(b_size_2, b_size_2),
            label='',
            color=(1, 1, 1),
            tint_texture=(ba.gettexture(
                self.image_array[self._icon_index] + 'ColorMask')),
            tint_color=(0.6, 0.6, 0.6),
            tint2_color=(0.1, 0.3, 0.1),
            texture=ba.gettexture(self.image_array[self._icon_index]),
            mask_texture=mask_texture)

        ba.textwidget(
            parent=self._subcontainer,
            h_align='center',
            v_align='center',
            position=(self._sub_width * 0.5,
                      bots_height + spacing_h * 4 + 10),
            size=(0, 0),
            draw_controller=bot,
            text='Bot Type',
            scale=1.0,
            color=ba.app.ui.title_color,
            maxwidth=130)

        ba.textwidget(parent=self._subcontainer,
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
        self.count_text = txt = ba.textwidget(parent=self._subcontainer,
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
        self.button_bot_left = btn1 = ba.buttonwidget(
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
        self.button_bot_right = btn2 = ba.buttonwidget(
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

        ba.textwidget(parent=self._subcontainer,
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

        self.radius_text = txt = ba.textwidget(parent=self._subcontainer,
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
        self.button_bot_left = btn1 = ba.buttonwidget(
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
        self.button_bot_right = btn2 = ba.buttonwidget(
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

        self.button = ba.buttonwidget(
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

        self.button = ba.buttonwidget(
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
            ba.textwidget(parent=self._subcontainer,
                          position=(self._sub_width * 0.005,
                                    bots_height + spacing_h * (9 + i)),
                          size=(100, 30),
                          text=name,
                          h_align='left',
                          color=(0.8, 0.8, 0.8),
                          v_align='center',
                          maxwidth=200)
            value = ba.app.config.get(self.config[i])
            txt2 = ba.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.8 - spacing_v / 2,
                          bots_height +
                          spacing_h * (9 + i)),
                size=(0, 28),
                text=ba.Lstr(resource='onText') if value else ba.Lstr(
                    resource='offText'),
                editable=False,
                color=(0.6, 1.0, 0.6),
                maxwidth=50,
                h_align='right',
                v_align='center',
                padding=2)
            ba.checkboxwidget(parent=self._subcontainer,
                              text='',
                              position=(self._sub_width * 0.8 - 15,
                                        bots_height +
                                        spacing_h * (9 + i)),
                              size=(30, 30),
                              autoselect=False,
                              textcolor=(0.8, 0.8, 0.8),
                              value=value,
                              on_value_change_call=ba.Call(
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

            ba.textwidget(edit=self.count_text,
                          text=str(self.count))

    def decrease_count(self):
        if self.count > 1:
            self.count -= 1

            ba.textwidget(edit=self.count_text,
                          text=str(self.count))

    def increase_radius(self):
        if self.radius < 2:
            self.radius += 1

            ba.textwidget(edit=self.radius_text,
                          text=self.radius_array[self.radius])

    def decrease_radius(self):
        if self.radius > 0:
            self.radius -= 1

            ba.textwidget(edit=self.radius_text,
                          text=self.radius_array[self.radius])

    def clear_bot(self):
        self.bot1.clear()
        self.bot2.clear()

    def do_spawn_bot(self, clid: int = -1) -> None:
        with ba.Context(self.activity):
            for i in _ba.get_foreground_host_activity().players:
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
            else:
                tint1 = (0.6, 0.6, 0.6)
                tint2 = (0.1, 0.3, 0.1)

            if self.bot_array_name[self._icon_index] in (
                'S.Pro Bomber', 'S.Pro Brawler',
                'S.Pro Trigger', 'S.Pro Charger'):
                color = (1.3, 1.2, 3.0)
            else:
                color = (1.0, 1.0, 1.0)

            ba.buttonwidget(
                edit=self._bot_button,
                texture=ba.gettexture(self.image_array[self._icon_index]),
                tint_texture=(ba.gettexture(
                    self.image_array[self._icon_index] + 'ColorMask')),
                color=color,
                tint_color=tint1,
                tint2_color=tint2)


class PowerUpPracticeTab(PracticeTab):
    """The about tab in the practice UI"""

    def __init__(self, window: PracticeWindow) -> None:
        super().__init__(window)
        self._container: ba.Widget | None = None
        self.count = 1
        self.parent_widget = None
        self.activity = _ba.get_foreground_host_activity()

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
        self._icon_index = self.power_list_type_name.index('Tripple Bombs')

        self.setting_name = (['Bomb Countdown', 'Bomb Radius Visualizer'])
        self.config = (['bombCountdown', 'bombRadiusVisual'])

    def on_activate(
        self,
        parent_widget: ba.Widget,
        tab_button: ba.Widget,
        region_width: float,
        region_height: float,
        scroll_widget: ba.Widget,
        extra_x: float,
    ) -> ba.Widget:

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

        self._subcontainer = ba.containerwidget(
            parent=scroll_widget,
            size=(self._sub_width, self.container_h),
            background=False,
            selection_loops_to_parent=True)

        ba.textwidget(parent=self._subcontainer,
                      position=(self._sub_width * 0.5,
                                power_height),
                      size=(0, 0),
                      color=(1.0, 1.0, 1.0),
                      scale=1.3,
                      h_align='center',
                      v_align='center',
                      text='Spawn Power Up',
                      maxwidth=200)

        self._power_button = bot = ba.buttonwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(self._sub_width * 0.5 - b_size_2 * 0.5,
                      power_height + spacing_h * 3),
            on_activate_call=self._power_window,
            size=(b_size_2, b_size_2),
            label='',
            color=(1, 1, 1),
            texture=ba.gettexture('powerup' +
                                  self.power_list[
                                      self._icon_index]))

        ba.textwidget(
            parent=self._subcontainer,
            h_align='center',
            v_align='center',
            position=(self._sub_width * 0.5,
                      power_height + spacing_h * 4 + 10),
            size=(0, 0),
            draw_controller=bot,
            text='Power Up Type',
            scale=1.0,
            color=ba.app.ui.title_color,
            maxwidth=300)

        self.button = ba.buttonwidget(
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

        self.button = ba.buttonwidget(
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
            ba.textwidget(parent=self._subcontainer,
                          position=(self._sub_width * 0.005,
                                    power_height + spacing_h * (7 + i)),
                          size=(100, 30),
                          text=name,
                          h_align='left',
                          color=(0.8, 0.8, 0.8),
                          v_align='center',
                          maxwidth=200)
            value = ba.app.config.get(self.config[i])
            txt2 = ba.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.8 - spacing_v / 2,
                          power_height +
                          spacing_h * (7 + i)),
                size=(0, 28),
                text=ba.Lstr(resource='onText') if value else ba.Lstr(
                    resource='offText'),
                editable=False,
                color=(0.6, 1.0, 0.6),
                maxwidth=400,
                h_align='right',
                v_align='center',
                padding=2)
            ba.checkboxwidget(parent=self._subcontainer,
                              text='',
                              position=(self._sub_width * 0.8 - 15,
                                        power_height +
                                        spacing_h * (7 + i)),
                              size=(30, 30),
                              autoselect=False,
                              textcolor=(0.8, 0.8, 0.8),
                              value=value,
                              on_value_change_call=ba.Call(
                                  self._check_value_change,
                                  i, txt2))
            i += 1

        return self._subcontainer

    def debuff(self):
        with ba.Context(_ba.get_foreground_host_activity()):
            for i in _ba.get_foreground_host_activity().players:
                Spaz._gloves_wear_off(i.actor)
                Spaz._multi_bomb_wear_off(i.actor)
                Spaz._bomb_wear_off(i.actor)
                i.actor.shield_hitpoints = 1

    def get_powerup(self, clid: int = -1) -> None:
        with ba.Context(_ba.get_foreground_host_activity()):
            for i in _ba.get_foreground_host_activity().players:
                if i.sessionplayer.inputdevice.client_id == clid:
                    if i.node:
                        x = (random.choice([-7, 7]) / 10)
                        z = (random.choice([-7, 7]) / 10)
                        pos = (i.node.position[0] + x,
                               i.node.position[1],
                               i.node.position[2] + z)
                        PowerupBox(position=pos,
                                   poweruptype=
                                   self.power_list_type
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
            ba.buttonwidget(
                edit=self._power_button,
                texture=(ba.gettexture('powerup' +
                                       self.power_list[
                                           self._icon_index])))

    def _check_value_change(self, setting: int, widget: ba.Widget,
                            value: str) -> None:
        ba.textwidget(edit=widget,
                      text=ba.Lstr(resource='onText') if value else ba.Lstr(
                          resource='offText'))

        with ba.Context(self.activity):
            if setting == 0:
                if value:
                    ba.app.config["bombCountdown"] = True
                else:
                    ba.app.config["bombCountdown"] = False
            elif setting == 1:
                if value:
                    ba.app.config["bombRadiusVisual"] = True
                else:
                    ba.app.config["bombRadiusVisual"] = False


class OthersPracticeTab(PracticeTab):
    """The about tab in the practice UI"""

    def __init__(self, window: PracticeWindow) -> None:
        super().__init__(window)
        self._container: ba.Widget | None = None
        self.count = 1
        self.parent_widget = None
        self.activity = _ba.get_foreground_host_activity()
        self.setting_name = (['Pause On Window', 'Invincible'])
        self.config = (['pause', 'invincible'])

    def on_activate(
        self,
        parent_widget: ba.Widget,
        tab_button: ba.Widget,
        region_width: float,
        region_height: float,
        scroll_widget: ba.Widget,
        extra_x: float,
    ) -> ba.Widget:
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

        self._subcontainer = ba.containerwidget(
            parent=scroll_widget,
            size=(self._sub_width, self.container_h),
            background=False,
            selection_loops_to_parent=True)

        ba.textwidget(parent=self._subcontainer,
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
            ba.textwidget(parent=self._subcontainer,
                          position=(self._sub_width * 0.005,
                                    other_height + spacing_h * (2 + i)),
                          size=(100, 30),
                          text=name,
                          h_align='left',
                          color=(0.8, 0.8, 0.8),
                          v_align='center',
                          maxwidth=200)
            value = ba.app.config.get(self.config[i])
            txt2 = ba.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.8 - spacing_v / 2,
                          other_height +
                          spacing_h * (2 + i)),
                size=(0, 28),
                text=ba.Lstr(resource='onText') if value else ba.Lstr(
                    resource='offText'),
                editable=False,
                color=(0.6, 1.0, 0.6),
                maxwidth=400,
                h_align='right',
                v_align='center',
                padding=2)
            ba.checkboxwidget(parent=self._subcontainer,
                              text='',
                              position=(self._sub_width * 0.8 - 15,
                                        other_height +
                                        spacing_h * (2 + i)),
                              size=(30, 30),
                              autoselect=False,
                              textcolor=(0.8, 0.8, 0.8),
                              value=value,
                              on_value_change_call=ba.Call(
                                  self._check_value_change,
                                  i, txt2))
            i += 1

        return self._subcontainer

    def _check_value_change(self, setting: int, widget: ba.Widget,
                            value: str) -> None:
        ba.textwidget(edit=widget,
                      text=ba.Lstr(resource='onText') if value else ba.Lstr(
                          resource='offText'))

        with ba.Context(self.activity):
            if setting == 0:
                if value:
                    ba.app.config["pause"] = True
                    self.activity.globalsnode.paused = True
                else:
                    ba.app.config["pause"] = False
                    self.activity.globalsnode.paused = False
            elif setting == 1:
                if value:
                    ba.app.config["invincible"] = True
                else:
                    ba.app.config["invincible"] = False
                for i in _ba.get_foreground_host_activity().players:
                    try:
                        if i.node:
                            if ba.app.config.get("invincible"):
                                i.actor.node.invincible = True
                            else:
                                i.actor.node.invincible = False
                    except:
                        pass


class PracticeWindow(ba.Window):
    class TabID(Enum):
        """Our available tab types."""

        BOTS = 'bots'
        POWERUP = 'power up'
        OTHERS = 'others'

    def __del__(self):
        _ba.set_party_icon_always_visible(True)
        self.activity.globalsnode.paused = False

    def __init__(self,
                 transition: Optional[str] = 'in_right'):

        self.activity = _ba.get_foreground_host_activity()
        _ba.set_party_icon_always_visible(False)
        if ba.app.config.get("pause"):
            self.activity.globalsnode.paused = True
        uiscale = ba.app.ui.uiscale
        self.pick = 0
        self._width = 500

        self._height = (578 if uiscale is ba.UIScale.SMALL else
                        670 if uiscale is ba.UIScale.MEDIUM else 800)
        extra_x = 100 if uiscale is ba.UIScale.SMALL else 0
        self.extra_x = extra_x

        self._transitioning_out = False

        b_size_2 = 100

        spacing_h = -50
        spacing = -450
        spacing_v = 60
        self.container_h = 500
        v = self._height - 115.0
        v -= spacing_v * 3.0

        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height),
            transition=transition,
            scale=(1.3 if uiscale is ba.UIScale.SMALL else
                   0.97 if uiscale is ba.UIScale.MEDIUM else 0.8),
            stack_offset=(0, -10) if uiscale is ba.UIScale.SMALL else (
                240, 0) if uiscale is ba.UIScale.MEDIUM else (330, 20)))

        self._sub_height = 200

        self._scroll_width = self._width * 0.8
        self._scroll_height = self._height * 0.6
        self._scroll_position = ((self._width - self._scroll_width) * 0.5,
                                 (self._height - self._scroll_height) * 0.5)

        self._scrollwidget = ba.scrollwidget(parent=self._root_widget,
                                             size=(self._scroll_width,
                                                   self._scroll_height),
                                             color=(0.55, 0.55, 0.55),
                                             highlight=False,
                                             position=self._scroll_position)

        ba.containerwidget(edit=self._scrollwidget,
                           claims_left_right=True)

        # ---------------------------------------------------------

        x_offs = 100 if uiscale is ba.UIScale.SMALL else 0

        self._current_tab: PracticeWindow.TabID | None = None
        extra_top = 20 if uiscale is ba.UIScale.SMALL else 0
        self._r = 'gatherWindow'

        tabdefs: list[tuple[PracticeWindow.TabID, str]] = [
            (self.TabID.BOTS, 'Bots')
        ]
        if ba_internal.get_v1_account_misc_read_val(
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

        condensed = uiscale is not ba.UIScale.LARGE
        t_offs_y = (
            0 if not condensed else 25 if uiscale is ba.UIScale.MEDIUM else 17
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
            on_select_call=ba.WeakCall(self._set_tab),
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

        if ba.app.ui.use_toolbars:
            ba.widget(
                edit=self._tab_row.tabs[tabdefs[-1][0]].button,
                right_widget=ba_internal.get_special_widget('party_button'),
            )
            if uiscale is ba.UIScale.SMALL:
                ba.widget(
                    edit=self._tab_row.tabs[tabdefs[0][0]].button,
                    left_widget=ba_internal.get_special_widget('back_button'),
                )

        # -----------------------------------------------------------

        self._back_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(self._width * 0.15 - 30,
                      self._height * 0.95 - 30),
            size=(60, 60),
            scale=1.1,
            label=ba.charstr(ba.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self.close)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5,
                                self._height * 0.95),
                      size=(0, 0),
                      color=ba.app.ui.title_color,
                      scale=1.5,
                      h_align='center',
                      v_align='center',
                      text='Practice Tools',
                      maxwidth=400)

        self.info_button = ba.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(self._width * 0.8 - 30,
                      self._height * 0.15 - 30),
            on_activate_call=self._info_window,
            size=(60, 60),
            label='')

        ba.imagewidget(
            parent=self._root_widget,
            position=(self._width * 0.8 - 25,
                      self._height * 0.15 - 25),
            size=(50, 50),
            draw_controller=self.info_button,
            texture=ba.gettexture('achievementEmpty'),
            color=(1.0, 1.0, 1.0))

        self._tab_container: ba.Widget | None = None

        self._restore_state()

        # # -------------------------------------------------------

    def _info_window(self):
        InfoWindow(
            parent=self._root_widget)

    def _button(self) -> None:
        ba.buttonwidget(edit=None,
                        color=(0.2, 0.4, 0.8))

    def close(self) -> None:
        """Close the window."""
        ba.containerwidget(edit=self._root_widget, transition='out_right')

    def _set_tab(self, tab_id: TabID) -> None:
        if self._current_tab is tab_id:
            return
        prev_tab_id = self._current_tab
        self._current_tab = tab_id

        # We wanna preserve our current tab between runs.
        cfg = ba.app.config
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

            sel: ba.Widget | None
            winstate = ba.app.ui.window_states.get(type(self), {})
            sel_name = winstate.get('sel_name', None)
            assert isinstance(sel_name, (str, type(None)))
            current_tab = self.TabID.BOTS
            gather_tab_val = ba.app.config.get('Practice Tab')
            try:
                stored_tab = enum_by_value(self.TabID, gather_tab_val)
                if stored_tab in self._tab_row.tabs:
                    current_tab = stored_tab
            except ValueError:
                pass
            self._set_tab(current_tab)
            if sel_name == 'Back':
                sel = self._back_button
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
            ba.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            ba.print_exception('Error restoring gather-win state.')


org_begin = ba._activity.Activity.on_begin


def new_begin(self):
    """Runs when game is began."""
    _ba.set_party_icon_always_visible(True)


ba._activity.Activity.on_begin = new_begin


class BotPicker(popup.PopupWindow):
    """Popup window for selecting bots to spwan."""

    def __init__(self,
                 parent: ba.Widget,
                 position: tuple[float, float] = (0.0, 0.0),
                 delegate: Any = None,
                 scale: float | None = None,
                 offset: tuple[float, float] = (0.0, 0.0),
                 selected_character: str | None = None):
        del parent  # unused here
        uiscale = ba.app.ui.uiscale
        if scale is None:
            scale = (1.85 if uiscale is ba.UIScale.SMALL else
                     1.65 if uiscale is ba.UIScale.MEDIUM else 1.23)

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
                                      if uiscale is ba.UIScale.SMALL else 1.06)

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

        self._scrollwidget = ba.scrollwidget(parent=self.root_widget,
                                             size=(self._scroll_width,
                                                   self._scroll_height),
                                             color=(0.55, 0.55, 0.55),
                                             highlight=False,
                                             position=self._scroll_position)

        ba.containerwidget(edit=self._scrollwidget, claims_left_right=True)

        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 5 + rows * (button_height +
                                       2 * button_buffer_v) + 100
        self._subcontainer = ba.containerwidget(parent=self._scrollwidget,
                                                size=(self._sub_width,
                                                      self._sub_height),
                                                background=False)

        mask_texture = ba.gettexture('characterIconMask')

        bot_list = (['bones', 'neoSpaz', 'kronk', 'zoe',
                     'ninja', 'mel', 'jack', 'bunny',
                     'neoSpaz', 'kronk', 'zoe',
                     'ninja',
                     'neoSpaz', 'kronk', 'zoe',
                     'ninja'])
        bot_list_type = (['Dummy', 'Bomber', 'Brawler', 'Trigger',
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
                btn = ba.buttonwidget(
                    parent=self._subcontainer,
                    button_type='square',
                    position=(pos[0],
                              pos[1]),
                    size=(button_width, button_height),
                    autoselect=True,
                    texture=ba.gettexture(bot_list[index] + 'Icon'),
                    tint_texture=ba.gettexture(
                        bot_list[index] + 'IconColorMask'),
                    mask_texture=mask_texture,
                    label='',
                    color=color,
                    tint_color=tint1,
                    tint2_color=tint2,
                    on_activate_call=ba.Call(self._select_character,
                                             character=bot_list_type[index]))
                ba.widget(edit=btn, show_buffer_top=60, show_buffer_bottom=60)

                name = bot_list_type[index]
                ba.textwidget(parent=self._subcontainer,
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
            ba.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._transition_out()


class PowerPicker(popup.PopupWindow):
    """Popup window for selecting power up."""

    def __init__(self,
                 parent: ba.Widget,
                 position: tuple[float, float] = (0.0, 0.0),
                 delegate: Any = None,
                 scale: float | None = None,
                 offset: tuple[float, float] = (0.0, 0.0),
                 selected_character: str | None = None):
        del parent  # unused here

        if scale is None:
            uiscale = ba.app.ui.uiscale
            scale = (1.85 if uiscale is ba.UIScale.SMALL else
                     1.65 if uiscale is ba.UIScale.MEDIUM else 1.23)

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
                                      if uiscale is ba.UIScale.SMALL else 1.06)

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

        self._scrollwidget = ba.scrollwidget(parent=self.root_widget,
                                             size=(self._scroll_width,
                                                   self._scroll_height),
                                             color=(0.55, 0.55, 0.55),
                                             highlight=False,
                                             position=self._scroll_position)

        ba.containerwidget(edit=self._scrollwidget, claims_left_right=True)

        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 5 + rows * (button_height +
                                       2 * button_buffer_v) + 100
        self._subcontainer = ba.containerwidget(parent=self._scrollwidget,
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
                btn = ba.buttonwidget(
                    parent=self._subcontainer,
                    button_type='square',
                    position=(pos[0],
                              pos[1]),
                    size=(button_width, button_height),
                    autoselect=True,
                    texture=ba.gettexture('powerup' + power_list[index]),
                    label='',
                    color=(1, 1, 1),
                    on_activate_call=ba.Call(self._select_power,
                                             power=power_list[index]))
                ba.widget(edit=btn, show_buffer_top=60, show_buffer_bottom=60)

                name = power_list_type[index]
                ba.textwidget(parent=self._subcontainer,
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
            ba.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._transition_out()


class InfoWindow(popup.PopupWindow):
    """Popup window for Infos."""

    def __init__(self,
                 parent: ba.Widget,
                 position: tuple[float, float] = (0.0, 0.0),
                 delegate: Any = None,
                 scale: float | None = None,
                 offset: tuple[float, float] = (0.0, 0.0),
                 selected_character: str | None = None):
        del parent  # unused here

        if scale is None:
            uiscale = ba.app.ui.uiscale
            scale = (1.85 if uiscale is ba.UIScale.SMALL else
                     1.65 if uiscale is ba.UIScale.MEDIUM else 1.23)

        self._delegate = delegate
        self._transitioning_out = False

        self._width = 600
        self._height = self._width * (0.6
                                      if uiscale is ba.UIScale.SMALL else 0.795)

        # creates our _root_widget
        popup.PopupWindow.__init__(self,
                                   position=position,
                                   size=(self._width, self._height),
                                   scale=scale,
                                   bg_color=(0.5, 0.5, 0.5),
                                   offset=offset,
                                   focus_size=(self._width,
                                               self._height))

        ba.textwidget(parent=self.root_widget,
                      position=(self._width * 0.5,
                                self._height * 0.9),
                      size=(0, 0),
                      color=ba.app.ui.title_color,
                      scale=1.3,
                      h_align='center',
                      v_align='center',
                      text='About',
                      maxwidth=200)

        text = ('Practice Tools Mod\n'
                'Made By Cross Joy\n'
                'version 1.0\n'
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

            ba.textwidget(
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

        self.button_discord = ba.buttonwidget(
            parent=self.root_widget,
            position=(
                self._width * 0.25 - 40, self._height * 0.2 - 40),
            size=(80, 80),
            autoselect=True,
            button_type='square',
            color=(0.447, 0.537, 0.854),
            label='',
            on_activate_call=self._discord)
        ba.imagewidget(
            parent=self.root_widget,
            position=(self._width * 0.25 - 25,
                      self._height * 0.2 - 25),
            size=(50, 50),
            draw_controller=self.button_discord,
            texture=ba.gettexture('discordLogo'),
            color=(5, 5, 5))
        ba.textwidget(
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

        self.button_github = ba.buttonwidget(
            parent=self.root_widget,
            position=(
                self._width * 0.5 - 40, self._height * 0.2 - 40),
            size=(80, 80),
            autoselect=True,
            button_type='square',
            color=(0.129, 0.122, 0.122),
            label='',
            on_activate_call=self._github)
        ba.imagewidget(
            parent=self.root_widget,
            position=(self._width * 0.5 - 25,
                      self._height * 0.2 - 25),
            size=(50, 50),
            draw_controller=self.button_github,
            texture=ba.gettexture('githubLogo'),
            color=(1, 1, 1))
        ba.textwidget(
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

        self.button_support = ba.buttonwidget(
            parent=self.root_widget,
            position=(
                self._width * 0.75 - 40, self._height * 0.2 - 40),
            size=(80, 80),
            autoselect=True,
            button_type='square',
            color=(0.83, 0.69, 0.21),
            label='',
            on_activate_call=self._support)
        ba.imagewidget(
            parent=self.root_widget,
            position=(self._width * 0.75 - 25,
                      self._height * 0.2 - 25),
            size=(50, 50),
            draw_controller=self.button_support,
            texture=ba.gettexture('heart'),
            color=(1, 1, 1))
        ba.textwidget(
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
        ba.open_url('https://discord.gg/JyBY6haARJ')

    def _github(self):
        ba.open_url('https://github.com/CrossJoy/Bombsquad-Modding')

    def _support(self):
        ba.open_url('https://www.buymeacoffee.com/CrossJoy')

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            ba.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._transition_out()
