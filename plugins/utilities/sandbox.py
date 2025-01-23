import babase as ba
import _babase as _ba  # music control
import bauiv1lib.mainmenu as mm
import bauiv1 as bui
import bascenev1 as bs
from bascenev1 import broadcastmessage as push, get_foreground_host_activity as ga
from bauiv1lib import popup  # Pickers
from typing import Any, cast, Sequence, Optional, Callable  # UI control
import math  # floating name
from bauiv1lib.colorpicker import ColorPicker
import random  # random attrs
from bascenev1lib.actor.spazbot import SpazBot, SpazBotSet
from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.actor.bomb import Bomb, BombFactory
import weakref  # get map (bot)
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.popuptext import PopupText  # my unfunny popups
from bauiv1lib.tabs import TabRow  # BOTS and USERS
from bascenev1lib.actor.powerupbox import PowerupBox
from bascenev1lib.actor.bomb import TNTSpawner
from os import listdir as ls


def error(real):  # not fake
    bui.getsound('error').play()
    with ga().context:
        img = bs.gettexture("ouyaAButton")
    push(real, color=(1, 0, 0), top=Nice.top_msg, image=img)


def ding(fake):  # fake
    if Nice.do_ding:
        bui.getsound('ding').play()
    with ga().context:
        img = bs.gettexture("ouyaOButton")
    push(fake, color=(0, 1, 0), top=Nice.top_msg, image=img)


def var(s, v=None):
    cfg = bui.app.config
    if v is None:
        try:
            return cfg['sb_'+s]
        except:
            return 0
    else:
        cfg['sb_'+s] = v
        cfg.commit()


class Nice(mm.MainMenuWindow):
    # config, trash code ik
    def_attrs = [False, "Spaz", 2.0, 0.0, 1.0, 0.4, (1, 1, 1), 3, "normal", False, False,
                 (1, 1, 1), 0.5, False, 0.0, False, False, 9.0, 5.0, 1.0, 0.7, True, False,
                 False, False, False, False, '$', (1, 1, 1)]
    a = var('do_ding')
    do_ding = a if isinstance(a, bool) else True
    a = var('while_control')
    while_control = a if isinstance(a, bool) else True
    lite_mode = var('lite_mode')
    animate_camera = var('animate_camera')
    top_msg = var('top_msg')
    notify_bot_ded = var('notify_bot_ded')
    pause_when_bots = var('pause_when_bots')
    drop_indox = 9
    drop_cords = (69123, 0, 0)
    tweak_dux = None
    tweak_2d = False
    tweakz_dux = None
    LTWAC = (0.9, 0.9, 0.9)
    lmao_teams = []
    pending = []  # pending effects on bot from load_window
    pending2 = []  # same but for drops
    toxic_bots = []
    next_team_id = 2
    team_to_nuke = None
    ga_tint = (1.30, 1.20, 1)
    indox = 0  # spawn_window's character image order
    val_attrs = def_attrs.copy()

    # my dumb positioning
    soff = (0, 0)
    howoff = 400
    _pos = 0
    _anim_out = 'out_right'
    _anim_outv = 'out_left'
    anim_in = 'in_right'
    anim_inv = 'in_left'
    center_pos = (0, 140)
    scale = 1.3

    # objects
    node_gravity_scale = 1.0
    node_sticky = False
    node_reflect = False
    node_reflect2 = False
    node_reflection_scale = [1.2]
    brobordd = None

    def pause(s, b):
        try:
            ga().globalsnode.paused = b
        except AttributeError:
            pass  # i am not the host

    def __init__(s, call_sand=True):
        try:
            for i in ga().players:
                if i.sessionplayer.inputdevice.client_id == -1:
                    s.brobordd = i
                    break
        except:
            pass  # not the host.
        s.thex = 0.0
        s.they = 0.0
        s.spaz_not_fly = Spaz.on_jump_press
        s.auto_spawn_on_random = False
        s.random_peace = False
        s._height = 300
        s._width = 500
        global root_widget, old_ga, nood
        if Nice.pause_when_bots:
            with ga().context:
                bs.timer(0, bs.Call(s.pause, True))
        if str(ga()) != old_ga:
            s.on_ga_change()
        if call_sand:
            root_widget = s._rw = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                                      size=(s._width, s._height),
                                                      color=cola,
                                                      transition=s.anim_in,
                                                      stack_offset=s.soff,
                                                      scale=s.scale)

        def pos():
            s._pos = 0 if s._pos else 1
            if s._pos:
                pos_left()
            else:
                pos_right()

        def pos_left():
            s._anim_out = 'out_left'
            s._anim_outv = 'out_right'
            s.anim_in = 'in_left'
            s.anim_inv = 'in_right'
            s.soff = (-s.howoff, 0)
            bui.containerwidget(edit=s._rw,
                                transition=None,
                                position=(0, 150),
                                stack_offset=(-s.howoff, 0))
            bui.containerwidget(edit=s._rw, transition='in_left')
            bui.buttonwidget(edit=s._LR, label='Right')
            bui.buttonwidget(edit=s.center_btn, position=(395, 250))

        def pos_right():
            s._anim_out = 'out_right'
            s._anim_outv = 'out_left'
            s.anim_in = 'in_right'
            s.anim_inv = 'in_left'
            s.soff = (s.howoff, 0)
            bui.containerwidget(edit=s._rw,
                                transition=None,
                                position=(930, 140),
                                stack_offset=(s.howoff, 0))
            bui.containerwidget(edit=s._rw, transition='in_right')
            bui.buttonwidget(edit=s._LR, label='Left')
            bui.buttonwidget(edit=s.center_btn, position=(30, 250))

        s._LR = bui.buttonwidget(
            parent=root_widget,
            size=(50, 15),
            label='Left',
            scale=s.scale,
            button_type='square',
            position=(395, 30),
            color=colb,
            textcolor=wht,
            on_activate_call=bs.Call(pos))

        bui.textwidget(parent=root_widget,
                       color=(0.1, 0.7, 1),
                       text='Sandbox',
                       position=(200, 250))

        bui.buttonwidget(parent=root_widget,
                         label='Spawn',
                         size=(130, 50),
                         color=colb,
                         icon=bui.gettexture("cuteSpaz"),
                         iconscale=s.scale,
                         textcolor=wht,
                         button_type='square',
                         position=(40, 185),
                         on_activate_call=bs.Call(s.spawn_window))

        bui.buttonwidget(parent=root_widget,
                         label='Control',
                         size=(130, 50),
                         color=colb,
                         icon=bui.gettexture("controllerIcon"),
                         iconscale=s.scale,
                         textcolor=wht,
                         button_type='square',
                         position=(180, 185),
                         on_activate_call=bs.Call(s.control_window))

        bui.buttonwidget(parent=root_widget,
                         label='Tune',
                         color=colb,
                         icon=bui.gettexture("settingsIcon"),
                         iconscale=s.scale,
                         size=(130, 50),
                         textcolor=wht,
                         button_type='square',
                         position=(320, 185),
                         on_activate_call=bs.Call(s.config_window))

        bui.buttonwidget(parent=root_widget,
                         label='Modify',
                         color=colb,
                         size=(130, 50),
                         icon=bui.gettexture("advancedIcon"),
                         iconscale=s.scale,
                         textcolor=wht,
                         button_type='square',
                         position=(40, 125),
                         on_activate_call=bs.Call(s.mod_window))

        bui.buttonwidget(parent=root_widget,
                         label='Effect',
                         size=(130, 50),
                         color=colb,
                         icon=bui.gettexture("graphicsIcon"),
                         iconscale=s.scale,
                         textcolor=wht,
                         button_type='square',
                         position=(180, 125),
                         on_activate_call=bs.Call(s.effect_window))

        bui.buttonwidget(parent=root_widget,
                         label='Listen',
                         size=(130, 50),
                         color=colb,
                         icon=bui.gettexture("audioIcon"),
                         iconscale=s.scale,
                         textcolor=wht,
                         button_type='square',
                         position=(320, 125),
                         on_activate_call=bs.Call(s.listen_window))

        bui.buttonwidget(parent=root_widget,
                         label='Deploy',
                         size=(130, 50),
                         color=colb,
                         icon=bui.gettexture("star"),
                         iconscale=s.scale,
                         textcolor=wht,
                         button_type='square',
                         position=(40, 65),
                         on_activate_call=bs.Call(s.drop_window))

        bui.buttonwidget(parent=root_widget,
                         label='Tweak',
                         size=(130, 50),
                         color=colb,
                         icon=bui.gettexture("menuIcon"),
                         iconscale=s.scale,
                         textcolor=wht,
                         button_type='square',
                         position=(180, 65),
                         on_activate_call=bs.Call(s.tweak_window))

        bacc = bui.buttonwidget(
            parent=root_widget,
            size=(50, 15),
            label='Back',
            scale=s.scale,
            button_type='square',
            position=(30, 30),
            color=colb,
            textcolor=wht,
            on_activate_call=bs.Call(s.back))
        bui.containerwidget(edit=root_widget, cancel_button=bacc)

        s.center_btn = bui.buttonwidget(
            parent=root_widget,
            size=(50, 15),
            label='Center',
            scale=s.scale,
            button_type='square',
            position=(30, 250),  # (395, 250) if left
            color=colb,
            textcolor=wht,
            on_activate_call=bs.Call(s.center))

        bui.buttonwidget(parent=root_widget,
                         label='More',
                         size=(130, 50),
                         color=colb,
                         icon=bui.gettexture("storeIcon"),
                         iconscale=s.scale,
                         textcolor=wht,
                         button_type='square',
                         position=(320, 65),
                         on_activate_call=bs.Call(s.lol_window))

    def center(s):
        if s.soff == (0, 0):
            error("Sandbox is already centered what are u doing")
            return
        s.soff = (0, 0)
        bui.containerwidget(edit=s._rw, transition=None)
        bui.containerwidget(edit=s._rw, position=(s.center_pos[0] + s.howoff, s.center_pos[1]))
        bui.containerwidget(edit=s._rw, stack_offset=s.soff)
        bui.containerwidget(edit=s._rw, transition='in_scale')

    def back(s, wosh=False):
        s.kill(wosh, root_widget)
        s.pause(False)

    def kill(s, wosh=False, who=None, keep_hl=False, anim=True, rev=False):
        try:
            bui.containerwidget(edit=who, transition=(
                s._anim_out if not rev else s._anim_outv) if anim else None)
        except:
            pass
        if wosh:
            bui.getsound('swish').play()
        if not keep_hl:
            s.hl3(None, False)

    def lol_window(s):
        if ga() is None:
            push("no MORE for you bud,\nyou are not the host.", color=(1, 1, 0))
            return
        s.lol_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                           size=(500, 240),
                                           stack_offset=s.soff,
                                           color=cola,
                                           transition=s.anim_in,
                                           scale=s.scale)

        bui.textwidget(parent=s.lol_widget,
                       color=(0.1, 0.7, 1),
                       text='More',
                       position=(210, 190))

        bui.buttonwidget(parent=s.lol_widget,
                         label='Gather',
                         size=(130, 50),
                         color=colb,
                         icon=bui.gettexture("achievementTeamPlayer"),
                         iconscale=s.scale,
                         textcolor=wht,
                         button_type='square',
                         position=(40, 125),
                         on_activate_call=bs.Call(s.lol_teams_window))

        bui.buttonwidget(parent=s.lol_widget,
                         label='Epic',
                         size=(130, 50),
                         color=colb,
                         icon=bui.gettexture("nextLevelIcon"),
                         iconscale=s.scale,
                         textcolor=wht,
                         button_type='square',
                         position=(180, 125),
                         on_activate_call=bs.Call(s.epic_window))

        bui.buttonwidget(parent=s.lol_widget,
                         label='Tint',
                         size=(130, 50),
                         color=colb,
                         icon=bui.gettexture("achievementRunaround"),
                         iconscale=s.scale,
                         textcolor=wht,
                         button_type='square',
                         position=(320, 125),
                         on_activate_call=bs.Call(s.light_window))

        bui.buttonwidget(parent=s.lol_widget,
                         label='Dim',
                         size=(130, 50),
                         color=colb,
                         icon=bui.gettexture("shadow"),
                         iconscale=s.scale,
                         textcolor=wht,
                         button_type='square',
                         position=(40, 65),
                         on_activate_call=bs.Call(s.dim_window))

        bui.buttonwidget(parent=s.lol_widget,
                         label='Load',
                         size=(130, 50),
                         color=colb,
                         icon=bui.gettexture("inventoryIcon"),
                         iconscale=s.scale,
                         textcolor=wht,
                         button_type='square',
                         position=(180, 65),
                         on_activate_call=bs.Call(s.load_window))

        bui.buttonwidget(parent=s.lol_widget,
                         label='About',
                         size=(130, 50),
                         color=colb,
                         icon=bui.gettexture("heart"),
                         iconscale=s.scale,
                         textcolor=wht,
                         button_type='square',
                         position=(320, 65),
                         on_activate_call=bs.Call(s.about_window))

        bacc = bui.buttonwidget(
            parent=s.lol_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, s.lol_widget))
        bui.containerwidget(edit=s.lol_widget, cancel_button=bacc)

        bui.textwidget(parent=s.lol_widget,
                       color=(0.7, 0.7, 0.7),
                       scale=s.scale/3,
                       text="* Not advanced enough? tweak 'globals' at Tweak menu,\n   it holds the activity node which is basically everything.",
                       position=(180, 30))

    def about_window(s):
        about_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                           size=(500, 450),
                                           stack_offset=s.soff,
                                           color=cola,
                                           transition=s.anim_in,
                                           scale=s.scale)

        txt = "SandBox v1.2 BETA\nThe mod which does almost everything in the game.\n\n" \
              "Made this mod for myself to test future mods freely, though you are\n" \
              "free to use it too!\n\nSorry if you found any bugs, I did my best to fix all existing bugs\n" \
              "and excepted a lot of lines, if I found more bugs I'm gonna fix them asap.\n\n" \
              "Coded using Galaxy A14 (4/64) using GNU Nano on Termux!" \
              "\n\nBig thanks to:\nYOU for trying this mod!"

        s.about_preview_text = bui.textwidget(parent=about_widget,
                                              text=txt,
                                              scale=s.scale,
                                              maxwidth=450,
                                              position=(30, 350))

        bui.textwidget(parent=about_widget,
                       color=(0.1, 0.7, 1),
                       text='About',
                       position=(200, 400),
                       maxwidth=150)

        bacc = bui.buttonwidget(
            parent=about_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, about_widget))
        bui.containerwidget(edit=about_widget, cancel_button=bacc)

    def load_window(s):
        if Nice.pause_when_bots:
            error("Cannot use Load Window while game is paused")
            return
        s.load_dux = None
        load_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                          size=(500, 300),
                                          stack_offset=s.soff,
                                          color=cola,
                                          transition=s.anim_in,
                                          scale=s.scale)

        s.load_preview_text = bui.textwidget(parent=load_widget,
                                             text='',
                                             size=(50, 50),
                                             scale=s.scale/1.4,
                                             maxwidth=200,
                                             position=(280, 175))

        bui.textwidget(parent=load_widget,
                       color=(0.1, 0.7, 1),
                       text='Load',
                       position=(200, 250),
                       maxwidth=150)

        bui.buttonwidget(
            parent=load_widget,
            size=(70, 30),
            label='Load',
            button_type='square',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(370, 30),
            on_activate_call=bs.Call(s.do_load))

        load_scroll = bui.scrollwidget(parent=load_widget,
                                       position=(30, 80),
                                       claims_up_down=False,
                                       claims_left_right=True,
                                       autoselect=True,
                                       size=(250, 150))

        load_sub = bui.containerwidget(parent=load_scroll,
                                       background=False,
                                       size=(190, len(load_name)*26),
                                       color=(0.3, 0.3, 0.3),
                                       scale=s.scale)

        bacc = bui.buttonwidget(
            parent=load_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, load_widget))
        bui.containerwidget(edit=load_widget, cancel_button=bacc)
        bui.textwidget(edit=s.load_preview_text, text="Preset Name")

        for i in range(len(load_name)):
            j = len(load_name)-1-i
            bui.textwidget(parent=load_sub,
                           scale=s.scale/2,
                           text=(load_name[j]),
                           h_align='left',
                           v_align='center',
                           color=(1, 1, 1),
                           on_activate_call=bs.Call(s.load_preview, j),
                           selectable=True,
                           autoselect=True,
                           click_activate=True,
                           size=(180, 29),
                           position=(-30, (20 * i)))

    def load_preview(s, i):
        bui.textwidget(edit=s.load_preview_text, text=load_name[i])
        s.load_dux = i

    def do_load(s):
        i = s.load_dux
        if i is None:
            error("Select a preset or get out.")
            return
        s.load_preset(i)
        ding(f"Loaded '{load_name[i]}'")

    def load_preset(s, i):
        if not i:  # Beboo
            Nice.indox = 9
            Nice.val_attrs[1] = "B-9000"
            Nice.val_attrs[6] = (1, 0, 0)
            Nice.val_attrs[7] = 0
            Nice.val_attrs[11] = (0.6, 0, 0)
            Nice.val_attrs[12] = 0.6  # punchiness
            Nice.val_attrs[13] = True
            Nice.val_attrs[17] = 99
            Nice.val_attrs[18] = 0
            Nice.val_attrs[20] = 0
            Nice.val_attrs[22] = True
            Nice.val_attrs[23] = True  # host
            Nice.val_attrs[24] = True
            Nice.val_attrs[25] = True
            Nice.val_attrs[26] = True  # your bots
            Nice.val_attrs[27] = "Beboo"
            Nice.val_attrs[28] = (0.7, 0, 0)
            Nice.pending = ["sp", "speed", "toxic", "constant_heal"]
            s.spawn_window()
        elif i == 1:  # Kronk Buddy
            Nice.indox = 1
            Nice.val_attrs[1] = "Kronk"
            Nice.val_attrs[6] = (0, 1, 1)
            Nice.val_attrs[7] = 0
            Nice.val_attrs[11] = (0, 0, 1)
            Nice.val_attrs[12] = 0.6
            Nice.val_attrs[13] = True
            Nice.val_attrs[17] = 99
            Nice.val_attrs[18] = 0
            Nice.val_attrs[20] = 0
            Nice.val_attrs[22] = True
            Nice.val_attrs[24] = True
            Nice.val_attrs[25] = True
            Nice.val_attrs[27] = "Kronko Buddo"
            Nice.val_attrs[28] = (0, 0, 0.7)
            s.spawn_window()
        elif i == 3:  # Infinitely Cursed Jack
            Nice.indox = 5
            Nice.val_attrs[0] = True  # bouncy
            Nice.val_attrs[1] = "Jack Morgan"
            Nice.val_attrs[6] = (1, 1, 0)
            Nice.val_attrs[7] = 0
            Nice.val_attrs[11] = (1, 1, 0)
            Nice.val_attrs[12] = 0
            Nice.val_attrs[13] = True
            Nice.val_attrs[17] = 99
            Nice.val_attrs[18] = 0
            Nice.val_attrs[20] = 0
            Nice.val_attrs[22] = False  # start invincible
            Nice.val_attrs[23] = True  # host
            Nice.val_attrs[24] = True  # players
            Nice.val_attrs[25] = True  # bots
            Nice.val_attrs[26] = True  # your bots
            Nice.val_attrs[27] = "Jackie KMS"
            Nice.val_attrs[28] = (1, 1, 0)
            Nice.pending = ["infinite_curse"]
            s.spawn_window()
        elif i == 2:  # Flying Pixel
            Nice.indox = 10
            Nice.val_attrs[0] = True  # bouncy
            Nice.val_attrs[1] = "Pixel"
            Nice.val_attrs[6] = (1, 0, 1)
            Nice.val_attrs[7] = 0
            Nice.val_attrs[11] = (1, 0, 1)
            Nice.val_attrs[12] = 0
            Nice.val_attrs[13] = True
            Nice.val_attrs[17] = 99
            Nice.val_attrs[18] = 0
            Nice.val_attrs[20] = 0
            Nice.val_attrs[22] = True  # start invincible
            Nice.val_attrs[23] = True  # host
            Nice.val_attrs[24] = True  # players
            Nice.val_attrs[25] = True  # bots
            Nice.val_attrs[26] = True  # your bots
            Nice.val_attrs[27] = "Pixie"
            Nice.val_attrs[28] = (1, 0, 1)
            Nice.pending = ["constant_jump", "constant_heal"]
            s.spawn_window()
        elif i == 4:  # Big Shiny TNT
            Nice.pending2 = ["big_bomb"]
            Nice.drop_indox = 9
            s.drop_window()
        elif i == 5:  # Long fuse bomb
            Nice.pending2 = ["long_fuse"]
            Nice.drop_indox = 17
            s.drop_window()
        elif i == 6:  # Huge safe mine
            Nice.pending2 = ["big_bomb"]
            Nice.drop_indox = 10
            s.drop_window()

    def dim_window(s):
        s.dim_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                           size=(300, 250),
                                           color=cola,
                                           stack_offset=s.soff,
                                           transition=s.anim_in,
                                           scale=s.scale)

        bui.buttonwidget(parent=s.dim_widget,
                         size=(200, 50),
                         label="Inner",
                         textcolor=wht,
                         scale=s.scale,
                         color=colb,
                         position=(20, 125),
                         on_activate_call=s.switch_dim)

        bui.textwidget(parent=s.dim_widget,
                       color=(0.1, 0.7, 1),
                       text='Which Vignette?',
                       scale=s.scale,
                       h_align='center',
                       v_align='center',
                       position=(125, 200))

        bui.buttonwidget(parent=s.dim_widget,
                         size=(200, 50),
                         label="Outer",
                         scale=s.scale,
                         color=colb,
                         textcolor=wht,
                         position=(20, 60),
                         on_activate_call=bs.Call(s.switch_dim, 1))

        bacc = bui.buttonwidget(
            parent=s.dim_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, s.dim_widget))
        bui.containerwidget(edit=s.dim_widget, cancel_button=bacc)

    def switch_dim(s, t=0):
        s.kill(True, s.dim_widget)
        title = "Outer" if t else "Inner"
        title = title+"  Vignette"
        s.switch_dim_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                                  size=(300, 250),
                                                  color=cola,
                                                  stack_offset=s.soff,
                                                  transition=s.anim_in,
                                                  scale=s.scale)

        bui.textwidget(parent=s.switch_dim_widget,
                       color=(0.1, 0.7, 1),
                       text=title,
                       scale=s.scale,
                       h_align='center',
                       v_align='center',
                       position=(125, 200))

        p = ga().globalsnode
        p = p.vignette_outer if t else p.vignette_inner
        x = bui.textwidget(
            parent=s.switch_dim_widget,
            text=str(p[0])[:5],
            editable=True,
            size=(200, 25),
            h_align='center',
            v_align='center',
            position=(55, 150))
        y = bui.textwidget(
            parent=s.switch_dim_widget,
            size=(200, 25),
            text=str(p[1])[:5],
            editable=True,
            h_align='center',
            v_align='center',
            position=(55, 120))
        z = bui.textwidget(
            parent=s.switch_dim_widget,
            size=(200, 25),
            text=str(p[2])[:5],
            editable=True,
            h_align='center',
            v_align='center',
            position=(55, 90))

        bui.buttonwidget(
            parent=s.switch_dim_widget,
            size=(60, 20),
            label='Set',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(200, 30),
            on_activate_call=bs.Call(s.collect_dim, x, y, z, t))

        def back(s):
            s.kill(True, s.switch_dim_widget, keep_hl=True)
            s.dim_window()
        bacc = bui.buttonwidget(
            parent=s.switch_dim_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(back, s))
        bui.containerwidget(edit=s.switch_dim_widget, cancel_button=bacc)

    def gettext(s, w):
        return cast(str, bui.textwidget(query=w))

    def collect_dim(s, x, y, z, outer):
        n = ga().globalsnode
        t1 = s.gettext(x)
        t2 = s.gettext(y)
        t3 = s.gettext(z)
        emp = "X" if not t1 else "Y" if not t2 else "Z" if not z else None
        if emp:
            error(f"{emp} value cannot be empty!")
            return
        try:
            v = eval(f"({t1}, {t2}, {t3})")
        except Exception as e:
            error(str(e))
            return
        if outer:
            n.vignette_outer = v
        else:
            n.vignette_inner = v
        s.kill(True, s.switch_dim_widget)
        ding("Dim updated!")

    def epic_window(s):
        s.epic_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                            size=(300, 200),
                                            color=cola,
                                            stack_offset=s.soff,
                                            transition=s.anim_in,
                                            scale=s.scale)

        bui.textwidget(parent=s.epic_widget,
                       color=(0.1, 0.7, 1),
                       text='Epic',
                       scale=s.scale,
                       h_align='center',
                       v_align='center',
                       position=(125, 150))

        s.epic_pick = bui.buttonwidget(parent=s.epic_widget,
                                       size=(200, 50),
                                       label="Make Fast" if ga().globalsnode.slow_motion else "Make Epic",
                                       textcolor=wht,
                                       color=cola,
                                       scale=s.scale,
                                       position=(20, 75),
                                       on_activate_call=s.switch_epic)

        bacc = bui.buttonwidget(
            parent=s.epic_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, s.epic_widget))
        bui.containerwidget(edit=s.epic_widget, cancel_button=bacc)

    def switch_epic(s):
        b = not ga().globalsnode.slow_motion
        ga().globalsnode.slow_motion = b
        s.do_your_thing(b)
        bui.buttonwidget(edit=s.epic_pick, label=("Make Fast" if b else "Make Epic"))

    def light_window(s):
        s.light_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                             size=(300, 250),
                                             color=cola,
                                             stack_offset=s.soff,
                                             transition=s.anim_in,
                                             scale=s.scale)

        bui.textwidget(parent=s.light_widget,
                       color=(0.1, 0.7, 1),
                       text='Tint',
                       scale=s.scale,
                       h_align='center',
                       v_align='center',
                       position=(125, 200))

        global light_pick
        tent = ga().globalsnode.tint
        ntent = s.negate(tent)
        light_pick = bui.buttonwidget(parent=s.light_widget,
                                      size=(200, 50),
                                      label="Change Color",
                                      textcolor=wht,
                                      scale=s.scale,
                                      position=(20, 125),
                                      on_activate_call=bs.Call(PickerLight, tent))
        bui.buttonwidget(edit=light_pick, color=tent, textcolor=ntent)

        bui.buttonwidget(
            parent=s.light_widget,
            size=(60, 20),
            label='/ 1.1',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(200, 70),
            on_activate_call=bs.Call(s.mult))

        bui.buttonwidget(
            parent=s.light_widget,
            size=(60, 20),
            label='x 1.1',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 70),
            on_activate_call=bs.Call(s.mult, 1))

        bui.buttonwidget(
            parent=s.light_widget,
            size=(60, 20),
            label='Set',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(200, 30),
            on_activate_call=bs.Call(s.collect_light))

        bacc = bui.buttonwidget(
            parent=s.light_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, s.light_widget))
        bui.containerwidget(edit=s.light_widget, cancel_button=bacc)

    def mult(s, i=0):
        c = Nice.ga_tint
        x = 1.1 if i else (1/(1.1))
        Nice.ga_tint = c = (c[0]*x, c[1]*x, c[2]*x)
        bui.buttonwidget(edit=light_pick, color=c)
        bui.buttonwidget(edit=light_pick, textcolor=Nice.negate(Nice, c))
        bui.buttonwidget(edit=light_pick, on_activate_call=bs.Call(PickerLight, c))

    def collect_light(s):
        ding("Success!")
        s.kill(True, s.light_widget)
        ga().globalsnode.tint = Nice.ga_tint

    def lol_teams_window(s):
        s.LTW = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                    size=(300, 250),
                                    color=cola,
                                    stack_offset=s.soff,
                                    transition=s.anim_in,
                                    scale=s.scale)
        bui.buttonwidget(parent=s.LTW,
                         size=(200, 50),
                         label="Add",
                         textcolor=wht,
                         scale=s.scale,
                         color=colb,
                         icon=bui.gettexture("powerupHealth"),
                         position=(20, 125),
                         on_activate_call=s.lol_teams_window_add)

        bui.textwidget(parent=s.LTW,
                       color=(0.1, 0.7, 1),
                       text='What To Do?',
                       scale=s.scale,
                       h_align='center',
                       v_align='center',
                       position=(125, 200))

        bui.buttonwidget(parent=s.LTW,
                         size=(200, 50),
                         label="Nuke",
                         scale=s.scale,
                         color=colb,
                         icon=bui.gettexture("powerupCurse"),
                         textcolor=wht,
                         position=(20, 60),
                         on_activate_call=bs.Call(s.lol_teams_window_nuke))

        bacc = bui.buttonwidget(
            parent=s.LTW,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, s.LTW))
        bui.containerwidget(edit=s.LTW, cancel_button=bacc)

    def lol_teams_window_nuke(s):
        s.LTWN = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                     size=(500, 300),
                                     stack_offset=s.soff,
                                     color=cola,
                                     transition=s.anim_in,
                                     scale=s.scale)

        bui.textwidget(parent=s.LTWN,
                       color=(0.1, 0.7, 1),
                       text='Nuke',
                       position=(200, 250),
                       maxwidth=250)

        bui.buttonwidget(
            parent=s.LTWN,
            size=(70, 30),
            label='Nuke',
            button_type='square',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(370, 30),
            on_activate_call=bs.Call(s.do_nuke))

        LTWNS = bui.scrollwidget(parent=s.LTWN,
                                 position=(30, 80),
                                 claims_up_down=False,
                                 claims_left_right=True,
                                 autoselect=True,
                                 size=(300, 150))

        s.LTWN_sub = bui.containerwidget(parent=LTWNS,
                                         background=False,
                                         size=(300, len(Nice.lmao_teams)*26),
                                         color=(0.3, 0.3, 0.3),
                                         scale=s.scale)
        s.LTWNP = bui.textwidget(parent=s.LTWN,
                                 text='Team Name',
                                 size=(50, 50),
                                 scale=s.scale/1.4,
                                 maxwidth=115,
                                 color=wht,
                                 position=(340, 175))

        bacc = bui.buttonwidget(
            parent=s.LTWN,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, s.LTWN))
        bui.containerwidget(edit=s.LTWN, cancel_button=bacc)

        s.LTWN_load_teams()

    def LTWN_load_teams(s):
        for w in s.LTWN_sub.get_children():
            w.delete()
        for i in range(len(Nice.lmao_teams)):
            i = len(Nice.lmao_teams)-1-i
            t = Nice.lmao_teams[i]
            bui.textwidget(parent=s.LTWN_sub,
                           scale=s.scale/2,
                           text=t.name,
                           h_align='left',
                           v_align='center',
                           color=t.color,
                           on_activate_call=bs.Call(s.LTWN_prev, i),
                           selectable=True,
                           autoselect=True,
                           click_activate=True,
                           size=(180, 29),
                           position=(-30, (20 * i)))

    def LTWN_prev(s, i):
        t = Nice.lmao_teams[i]
        s.team_to_nuke = t
        bui.textwidget(edit=s.LTWNP, text=t.name, color=t.color)

    def do_nuke(s):
        if len(Nice.lmao_teams) < 1:
            error("Remove what u blind?")
            return
        if s.team_to_nuke is None:
            error("Select a team")
            return
        t = s.team_to_nuke
        s.team_to_nuke = None
        ga().remove_team(t)
        ding(f"Removed '{t.name}'")
        Nice.lmao_teams.remove(t)
        bui.containerwidget(edit=s.LTWN_sub, size=(300, len(Nice.lmao_teams)*26))
        s.LTWN_load_teams()

    def lol_teams_window_add(s):
        s.LTWA = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                     size=(450, 230),
                                     stack_offset=s.soff,
                                     color=cola,
                                     transition=s.anim_in,
                                     scale=s.scale)
        bacc = bui.buttonwidget(
            parent=s.LTWA,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, s.LTWA))
        bui.containerwidget(edit=s.LTWA, cancel_button=bacc)

        bui.textwidget(parent=s.LTWA,
                       color=(0.1, 0.7, 1),
                       text='Add',
                       position=(200, 180))

        bui.textwidget(parent=s.LTWA,
                       color=wht,
                       text="Team Name:",
                       scale=s.scale/1.6,
                       position=(30, 160),
                       h_align="left",
                       maxwidth=400)

        s.LTWA_box = bui.textwidget(parent=s.LTWA,
                                    editable=True,
                                    description="Enter team name:",
                                    position=(30, 130),
                                    size=(400, 30),
                                    h_align="left",
                                    maxwidth=400)

        bui.textwidget(parent=s.LTWA,
                       color=wht,
                       text="Team Color:",
                       scale=s.scale/1.6,
                       position=(30, 100),
                       h_align="left",
                       maxwidth=400)

        global LTWAB
        LTWAB = bui.buttonwidget(
            parent=s.LTWA,
            size=(70, 30),
            label='Pick',
            button_type="square",
            textcolor=s.negate(Nice.LTWAC),
            position=(30, 70),
            color=Nice.LTWAC,
            on_activate_call=bs.Call(PickerLol, Nice.LTWAC))

        s.LTWA_ran = bui.buttonwidget(
            parent=s.LTWA,
            size=(60, 20),
            color=cola,
            scale=s.scale,
            label='Random',
            textcolor=wht,
            button_type="square",
            position=(340, 70),
            on_activate_call=bs.Call(s.LTWA_random))

        bui.buttonwidget(
            parent=s.LTWA,
            size=(60, 20),
            label='Done',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(340, 30),
            on_activate_call=bs.Call(s.lol_teams_window_done))

    def negate(s, c): return (1-c[0], 1-c[1], 1-c[2])

    def LTWA_random(s):
        global LTWAB
        r = random.choice(random_team)
        Nice.LTWAC = r[1]
        bui.textwidget(edit=s.LTWA_box, text=r[0])
        bui.buttonwidget(edit=LTWAB, color=r[1], textcolor=s.negate(r[1]))

    def lol_teams_window_done(s):
        LTN = cast(str, bui.textwidget(query=s.LTWA_box))
        if not LTN:
            error("Enter a team name or just leave a space there")
            return
        team = bs.SessionTeam(Nice.next_team_id, name=LTN, color=Nice.LTWAC)
        Nice.lmao_teams.append(team)
        ga().add_team(team)
        Nice.next_team_id += 1
        s.kill(True, s.LTWA)
        ding(f"'{LTN}' was added!")

    def tweak_window(s):
        if ga() is None:
            push("You don't meet the minimum requirements\nto use BorddTweaker: BEING THE HOST.", color=(1, 1, 0))
            return
        p = s.brobordd.node.position
        with ga().context:
            nuds = bs.getnodes()
        s.nodes = []
        s.nodes_2d = []
        # fill up both 3D and 2D nodes
        for i in nuds:
            try:
                pos = i.position
            except:
                continue
            try:
                obj = i.getdelegate(object)
            except:
                obj = None
            if len(pos) == 3:
                s.nodes.append([])
                s.nodes[-1].append(pos)
                s.nodes[-1].append(i), s.nodes[-1].append(obj)
            elif len(pos) == 2:
                s.nodes_2d.append([])
                s.nodes_2d[-1].append(pos)
                s.nodes_2d[-1].append(i)
                s.nodes_2d[-1].append(obj)
        s.nodes.append([])
        s.nodes[-1].append((0, 0, 0))
        s.nodes[-1].append(ga().globalsnode), s.nodes[-1].append(None)
        # sort by closest (3D only)
        s.nodes = sorted(s.nodes, key=lambda k: math.dist(p, k[0]))
        # fill up 3D names and pics
        s.tweak_name = []
        s.tweak_texture = []
        for n in range(len(s.nodes)):
            obj = " ~" if s.nodes[n][2] is not None else ""
            try:
                s.tweak_name.append(str(s.nodes[n][1].getnodetype())+f" {n}"+obj)
            except:
                s.tweak_name.append(f"idk {n}"+obj)
            try:
                t = str(s.nodes[n][1].color_texture)
                on = t.find('"')
                off = t.find('"', on+1)
                s.tweak_texture.append(bui.gettexture(t[on+1:off]))
            except:
                try:
                    t = str(s.nodes[n][1].texture)
                    on = t.find('"')
                    off = t.find('"', on+1)
                    s.tweak_texture.append(bui.gettexture(t[on+1:off]))
                except:
                    try:
                        s.tweak_texture.append(str(s.nodes[n][1].text))
                    except:
                        s.tweak_texture.append(bui.gettexture("tv"))
            try:
                thing = s.what_is(s.nodes[n][1].mesh)
            except:
                continue
            s.tweak_name[-1] = s.tweak_name[-1]+thing
        # fill up 2D names and pics too
        s.tweak_name_2d = []
        s.tweak_texture_2d = []
        for n in range(len(s.nodes_2d)):
            obj = " ~" if s.nodes_2d[n][2] is not None else ""
            try:
                s.tweak_name_2d.append(str(s.nodes_2d[n][1].getnodetype())+f" {n}"+obj)
            except:
                s.tweak_name_2d.append(f"idk {n}"+obj)
            try:
                t = str(s.nodes_2d[n][1].color_texture)
                on = t.find('"')
                off = t.find('"', on+1)
                s.tweak_texture_2d.append(bui.gettexture(t[on+1:off]))
            except:
                try:
                    t = str(s.nodes_2d[n][1].texture)
                    on = t.find('"')
                    off = t.find('"', on+1)
                    s.tweak_texture_2d.append(bui.gettexture(t[on+1:off]))
                except:
                    try:
                        s.tweak_texture_2d.append(str(s.nodes_2d[n][1].text))
                    except:
                        s.tweak_texture_2d.append(bui.gettexture("tv"))
            try:
                thing = s.what_is(s.nodes_2d[n][1].mesh)
            except:
                continue
            s.tweak_name_2d[-1] = s.tweak_name_2d[-1]+thing

        s.tweak_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                             size=(500, 300),
                                             stack_offset=s.soff,
                                             color=cola,
                                             transition=s.anim_in,
                                             scale=s.scale)

        s.tweak_preview_image = bui.buttonwidget(parent=s.tweak_widget,
                                                 label='',
                                                 size=(50, 50),
                                                 position=(300, 175),
                                                 button_type='square',
                                                 color=colb,
                                                 mask_texture=bui.gettexture('characterIconMask'))

        s.tweak_preview_text = bui.textwidget(parent=s.tweak_widget,
                                              text='',
                                              size=(50, 50),
                                              scale=s.scale/1.4,
                                              maxwidth=115,
                                              position=(365, 175))

        s.tweak_preview_text2 = bui.textwidget(parent=s.tweak_widget,
                                               text='',
                                               size=(50, 50),
                                               scale=s.scale/1.8,
                                               maxwidth=115,
                                               position=(360, 155))

        bui.textwidget(parent=s.tweak_widget,
                       color=(0.1, 0.7, 1),
                       text='Tweak',
                       position=(300, 240),
                       maxwidth=150)

        bui.buttonwidget(
            parent=s.tweak_widget,
            size=(70, 30),
            label='Select',
            button_type='square',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(370, 30),
            on_activate_call=bs.Call(s.do_tweak))

        tweak_scroll = bui.scrollwidget(parent=s.tweak_widget,
                                        position=(30, 80),
                                        claims_up_down=False,
                                        claims_left_right=True,
                                        autoselect=True,
                                        size=(250, 150))

        s.tweak_sub = bui.containerwidget(parent=tweak_scroll,
                                          background=False,
                                          color=(0.3, 0.3, 0.3),
                                          scale=s.scale)

        tabdefs = [('3d', '3D Nodes'), ('2d', "2D Nodes")]

        s.tweak_tab = TabRow(
            s.tweak_widget,
            tabdefs,
            pos=(30, 230),
            size=(250, 0),
            on_select_call=s.switch_tweak_tab)

        # the right order
        s.tweak_tab.update_appearance('3d')
        s.cola_fill(s.tweak_widget)
        s.load_tweak_nodes()

        bacc = bui.buttonwidget(
            parent=s.tweak_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, s.tweak_widget))
        bui.containerwidget(edit=s.tweak_widget, cancel_button=bacc)

        bui.textwidget(
            parent=s.tweak_widget,
            size=(60, 20),
            text='~ has an object, 3d sorted by how close node is.',
            scale=s.scale/2,
            color=wht,
            maxwidth=250,
            position=(19, 60))

    def what_is(s, t):
        t = str(t).split('"')[1]
        for i in what_is_arr:
            if i[0] == t:
                return f" ({i[1]})"
        return ""

    def switch_tweak_tab(s, t):
        s.tweak_tab.update_appearance(t)
        s.cola_fill(s.tweak_widget)
        s.load_tweak_nodes(t == '3d')

    def load_tweak_nodes(s, t=True):
        # selected index is s.tweak_dux
        tn = s.tweak_name if t else s.tweak_name_2d
        alex = s.nodes if t else s.nodes_2d
        # clean up
        for c in s.tweak_sub.get_children():
            c.delete()
        bui.textwidget(edit=s.tweak_preview_text, text="Node Type")
        bui.buttonwidget(edit=s.tweak_preview_image, texture=bui.gettexture("tv"), color=(1, 1, 1))
        bui.containerwidget(edit=s.tweak_sub, size=(190, len(alex)*25.6))
        s.tweak_dux = None
        s.tweak_2d = False

        for i in range(len(alex)):
            bui.textwidget(parent=s.tweak_sub,
                           scale=s.scale/2,
                           text=(tn[i]),
                           h_align='left',
                           v_align='center',
                           color=(1, 1, 1),
                           on_activate_call=bs.Call(s.tweak_preview, i, t),
                           selectable=True,
                           autoselect=True,
                           click_activate=True,
                           size=(180, 29),
                           position=(-30, (20 * len(alex)) - (20 * i) - 30))

    def tweak_preview(s, i, b):
        s.tweak_dux = i
        s.tweak_2d = not b
        tn = s.tweak_name if b else s.tweak_name_2d
        tt = s.tweak_texture if b else s.tweak_texture_2d
#        nud = s.nodes[i] if b else s.nodes_2d[i]
#        try: s.draw_locator(nud[1].position)
#        except Exception as e: error(str(e))
        bui.textwidget(edit=s.tweak_preview_text, text=tn[s.tweak_dux])
        k = tt[s.tweak_dux]
        bui.textwidget(edit=s.tweak_preview_text2, text="")
        if isinstance(k, str):
            bui.textwidget(edit=s.tweak_preview_text2,
                           text=tt[s.tweak_dux], color=s.get_type_color("str"))
            bui.buttonwidget(edit=s.tweak_preview_image,
                             texture=bui.gettexture("tv"), color=(1, 1, 1))
        else:
            bui.buttonwidget(edit=s.tweak_preview_image, texture=tt[s.tweak_dux], color=(1, 1, 1))

    def connect_dots(s, pos1, pos2):
        spacing = 5
        x1, y1 = pos1
        x2, y2 = pos2
        # Calculate the distance between pos1 and pos2
        distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        # Calculate the number of dots needed
        num_dots = int(distance / spacing)
        # Calculate the step for each coordinate
        x_step = (x2 - x1) / num_dots
        y_step = (y2 - y1) / num_dots
        # Generate the dots
        dots = []
        for i in range(num_dots):
            dot_x = x1 + i * x_step
            dot_y = y1 + i * y_step
            dots.append((dot_x, dot_y))
        return dots

    def draw_char(s, char, pos, color=(0, 1, 1)):
        with ga().context:
            n = bs.newnode("text", attrs={
                           "text": char,
                           "flatness": 1.0,
                           "scale": 1,
                           "position": pos,
                           "color": color
                           })
            s.royna.append(n)
            return n

    def draw_locator(s, pos, pos2=(0, 0)):
        try:
            for node in s.royna:
                node.delete()
        except:
            pass
        s.royna = []
        dots = s.connect_dots(pos, pos2)
        s.draw_char(char="B", pos=pos, color=(1, 0, 0))
        s.draw_char(char="A", pos=pos2, color=(1, 0, 0))
        for i in range(len(dots)):
            n = s.draw_char(char="O", pos=dots[i])
            s.royna.append(n)

    def do_tweak(s):
        b = s.tweak_2d
        i = s.tweak_dux
        try:
            node = s.nodes_2d[i] if b else s.nodes[i]  # list of 3
        except TypeError:
            error("Select a node dum dum")
            return
        name = s.tweak_name_2d[i] if b else s.tweak_name[i]
        s.tweakz_current_name = name
        s.tweakz_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                              size=(500, 300),
                                              stack_offset=s.soff,
                                              color=cola,
                                              transition=s.anim_in,
                                              scale=s.scale)

        s.tweakz_preview_text = bui.textwidget(parent=s.tweakz_widget,
                                               text='',
                                               size=(50, 50),
                                               scale=s.scale/1.4,
                                               maxwidth=170,
                                               position=(290, 175))

        s.tweakz_preview_text2 = bui.textwidget(parent=s.tweakz_widget,
                                                text='',
                                                size=(50, 50),
                                                scale=s.scale/1.8,
                                                maxwidth=170,
                                                position=(290, 150))

        bui.textwidget(parent=s.tweakz_widget,
                       color=(0.1, 0.7, 1),
                       text=f'Tweak {name}',
                       position=(300, 240),
                       maxwidth=150)

        bui.buttonwidget(
            parent=s.tweakz_widget,
            size=(70, 30),
            label='Tweak',
            button_type='square',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(370, 30),
            on_activate_call=s.tweak_this)

        bui.buttonwidget(
            parent=s.tweakz_widget,
            size=(70, 30),
            label='Call',
            button_type='square',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(260, 30),
            on_activate_call=s.call_this)

        tweakz_scroll = bui.scrollwidget(parent=s.tweakz_widget,
                                         position=(30, 80),
                                         claims_up_down=False,
                                         claims_left_right=True,
                                         autoselect=True,
                                         size=(250, 150))

        s.tweakz_sub = bui.containerwidget(parent=tweakz_scroll,
                                           background=False,
                                           color=(0.3, 0.3, 0.3),
                                           scale=s.scale)

        tabdefs = [('node', 'Node'), ('obj', "Object")]

        s.tweakz_tab = TabRow(
            s.tweakz_widget,
            tabdefs,
            pos=(30, 230),
            size=(250, 0),
            on_select_call=bs.Call(s.switch_tweakz_tab, node))

        # the right order
        s.tweakz_tab.update_appearance('node')
        s.cola_fill(s.tweakz_widget)
        s.load_tweakz_nodes(node)

        bacc = bui.buttonwidget(
            parent=s.tweakz_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, s.tweakz_widget))
        bui.containerwidget(edit=s.tweakz_widget, cancel_button=bacc)

    def switch_tweakz_tab(s, node, t):
        s.tweakz_tab.update_appearance(t)
        s.cola_fill(s.tweakz_widget)
        s.load_tweakz_nodes(node, t == 'node')
        bui.textwidget(edit=s.tweak_preview_text2, text="")

    def load_tweakz_nodes(s, node, t=True):
        # selected index is s.tweakz_dux
        alex = node
        s.tweakz_current_node = node
        s.tweakz_is_node = t
        tn = []
        typez = []
        value = []
        col = []
        blex = alex[1 if t else 2]
        for i in dir(blex):
            tn.append(i)
            try:
                attr = getattr(blex, i) if i not in [
                    # gay
                    "punch_position", "punch_velocity", "punch_momentum_linear"] else (0, 0, 0)
            except:
                attr = None
            typez.append(str(type(attr).__name__))
            value.append(attr)
        if alex[2] is None and not t:
            tn.append("No object lol")
        s.tweakz_name = tn
        s.tweakz_type = typez
        s.tweakz_value = value
        # clean up
        for c in s.tweakz_sub.get_children():
            c.delete()
        bui.textwidget(edit=s.tweakz_preview_text, text="Attribute")
        bui.textwidget(edit=s.tweakz_preview_text2, text="Type")
        bui.containerwidget(edit=s.tweakz_sub, size=(190, len(tn)*25.9))
        s.tweakz_dux = None
        for i in range(len(typez)):
            t = typez[i]
            col.append(s.get_type_color(t))
        col.append((0.1, 0.1, 1))
        typez.append("byBordd")

        for i in range(len(tn)):
            bui.textwidget(parent=s.tweakz_sub,
                           scale=s.scale/2,
                           text=(tn[i]),
                           color=col[i],
                           h_align='left',
                           v_align='center',
                           on_activate_call=bs.Call(s.tweakz_preview, i, t),
                           selectable=True,
                           autoselect=True,
                           click_activate=True,
                           size=(210, 29),
                           position=(-30, (20 * len(tn)) - (20 * i) - 30))

    def get_type_color(s, t):
        c = (1, 0.5, 0)  # unknown orange
        if t == "str":
            c = (0, 0.6, 0)  # green
        elif t == "float":
            c = (0, 1, 1)  # cyan
        elif t == "tuple":
            c = (1, 0.6, 1)  # light pink
        elif t == "bool":
            c = (1, 1, 0)  # yellow
        elif t == "NoneType":
            c = (0.4, 0.4, 0.4)  # grey
        elif t == "Texture":
            c = (0.6, 0, 0.8)  # purple
        return c

    def tweakz_preview(s, i, b):
        s.tweakz_dux = i
        tn = s.tweakz_name
        typez = s.tweakz_type
        bui.textwidget(edit=s.tweakz_preview_text, text=tn[i])
        bui.textwidget(edit=s.tweakz_preview_text2, text=typez[i])
        bui.textwidget(edit=s.tweakz_preview_text2, color=s.get_type_color(typez[i]))

    def tweak_this(s):
        i = s.tweakz_dux
        mode = 0
        try:
            name = s.tweakz_current_name.split(" ")[0]+"."+s.tweakz_name[i]
        except TypeError:
            error("Select an attribute bruh")
            return
        try:
            value = s.tweakz_value[i]
        except IndexError:
            error("Tweak no object? are you high?")
            return
        typ = s.tweakz_type[i]
        if typ == "NoneType":
            error("Can't modify NoneType,\nidk what type should it be.")
            return
        if str(value).startswith("<"):
            if not typ == "Texture":
                error(f"{name} is not tweakable!")
                return
            mode = 1  # texture picker
        if typ == "tuple" and str(value).startswith("(<"):
            error("This tuple is not tweakable!")
            return
        s.TTW = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                    size=(450, 200),
                                    stack_offset=s.soff,
                                    color=cola,
                                    transition=s.anim_in,
                                    scale=s.scale)

        bui.textwidget(parent=s.TTW,
                       color=(0.1, 0.7, 1),
                       text=f"Tweak {name}",
                       position=(205, 150),
                       h_align="center",
                       maxwidth=400)

        bui.textwidget(parent=s.TTW,
                       color=s.get_type_color(typ),
                       text=typ,
                       scale=s.scale/1.6,
                       position=(205, 127),
                       h_align="center",
                       maxwidth=400)

        bui.textwidget(parent=s.TTW,
                       color=wht,
                       text="Default old value since the tweak window was opened:",
                       scale=s.scale/1.6,
                       position=(205, 100),
                       h_align="center",
                       maxwidth=400)

        if not mode:
            s.tweakz_box = bui.textwidget(parent=s.TTW,
                                          text=str(value),
                                          editable=True,
                                          position=(30, 75),
                                          size=(400, 30),
                                          h_align="center",
                                          maxwidth=400)
        elif mode == 1:
            global THE_TB
            s.tweakz_box = THE_TB = bui.textwidget(parent=s.TTW,
                                                   text=str(value).split('"')[1],
                                                   position=(30, 75),
                                                   size=(400, 30),
                                                   editable=True,
                                                   h_align="center",
                                                   maxwidth=400)
            bui.buttonwidget(parent=s.TTW,
                             label="Pick Texture",
                             color=cola,
                             textcolor=wht,
                             position=(150, 35),
                             size=(150, 30),
                             on_activate_call=TexturePicker)
        bui.textwidget(edit=s.tweakz_box, color=s.get_type_color(typ))

        bui.buttonwidget(
            parent=s.TTW,
            size=(60, 20),
            label='Cancel',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, s.TTW))

        bui.buttonwidget(
            parent=s.TTW,
            size=(60, 20),
            label='Set',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(340, 30),
            on_activate_call=bs.Call(s.gather_tweakz, s.tweakz_name[i], typ, mode))

    def gather_tweakz(s, name, typ, mode):
        value = cast(str, bui.textwidget(query=s.tweakz_box))
        v = None  # parsed value
        node = s.tweakz_current_node
        if not value:
            error("If you won't enter something THEN U CAN PRESS CANCEL.")
        # my nice yet stupid validator
        elif typ == "bool" and value.lower() in ["true", "false"]:
            v = value.lower() == 'true'
        elif typ == "bool":
            error("bool must be True or False, not '{}'".format(value))
            return
        elif typ == "float":
            try:
                v = float(value)
            except:
                error("float must be a number (decimal), not '{}'".format(value))
                return
        elif typ == "int":
            try:
                v = int(value)
            except:
                error("int must be a number (no decimals), not '{}'".format(value))
                return
        elif typ == "tuple":
            try:
                e = eval(value)
                v = e if type(e) is tuple else bro
            except:
                error(
                    f"tuple must be a goddamn tuple, not '{value}'\nlike this: (1.23, 1.91, 0.69)")
                return
        elif typ == "str":
            v = value  # string anything u like
        elif typ == "Texture":
            if value not in all_texture:
                error(f"Unknown texture '{value}', \nuse 'white', 'black' or 'null' for empty ones")
                return
            with ga().context:
                v = bs.gettexture(value)
        # apply value to node
        try:
            with ga().context:
                setattr(node[1 if s.tweakz_is_node else 2], name, v)
        except Exception as e:
            error(str(e) if str(e).strip() else f"No error info, repr(e): \n{repr(e)}")
        else:
            ding(f"Tweaked!")
        s.kill(True, s.TTW)

    def call_this(s):
        i = s.tweakz_dux
        try:
            name = s.tweakz_name[s.tweakz_dux]
        except TypeError:
            error("You better call a doctor instead,\nno attribute is selected")
            return
        try:
            attr = getattr(s.tweakz_current_node[1 if s.tweakz_is_node else 2], name)
        except AttributeError as e:
            error("Node no longer exists\nwhat are you doing here?" if "No object lol" not in str(
                e) else "Sure, equip a brain first")
            return
        s.CTW = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                    size=(450, 200),
                                    stack_offset=s.soff,
                                    color=cola,
                                    transition=s.anim_in,
                                    scale=s.scale)

        bui.textwidget(parent=s.CTW,
                       color=(0.1, 0.7, 1),
                       text=f"Call {name}",
                       position=(205, 150),
                       h_align="center",
                       maxwidth=400)

        bui.buttonwidget(
            parent=s.CTW,
            size=(60, 20),
            label='Cancel',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, s.CTW))

        bui.buttonwidget(
            parent=s.CTW,
            size=(60, 20),
            label='Call',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(340, 30),
            on_activate_call=bs.Call(s.do_call_this, attr, name))

        s.call_this_box = bui.textwidget(parent=s.CTW,
                                         color=(0.1, 0.7, 1),
                                         text="",
                                         description="Leave blank to call with no args, args example:\n14.2, True, 'Yes', ...\nenter",
                                         editable=True,
                                         position=(30, 75),
                                         size=(400, 30),
                                         h_align="center",
                                         maxwidth=400)

        bui.textwidget(parent=s.CTW,
                       color=wht,
                       text="Enter arguments separated by a comma (optional):",
                       scale=s.scale/1.6,
                       position=(205, 100),
                       h_align="center",
                       maxwidth=400)

    def do_call_this(s, attr, name):
        t = cast(str, bui.textwidget(query=s.call_this_box))
        if t != "":
            args = t.split(",")
            try:
                args = [eval(a.strip()) for a in args]
            except Exception as e:
                error(str(e))
                return
        else:
            args = []
        try:
            with ga().context:
                out = attr(*args)
            ding(
                f"Success! calling '{name}' (dumped to terminal)\nwith arguments {args}\noutputted: {out}")
            s.kill(True, s.CTW)
        except Exception as e:
            error(str(e) if str(e).strip() else f"No error info, repr(e): \n{repr(e)}")
        else:
            print(f"SandBox.ByBordd: calling '{name}' outputted: \n{out}")

    def drop_window(s):
        if ga() is None:
            push("Drop? looks like you dropped your brain somewhere,\nyou are not the host.", color=(1, 1, 0))
            return
        s.drop_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                            size=(500, 300),
                                            stack_offset=s.soff,
                                            color=cola,
                                            transition=s.anim_in,
                                            scale=s.scale)

        bui.textwidget(parent=s.drop_widget,
                       color=(0.1, 0.7, 1),
                       text='Deploy',
                       position=(210, 250),
                       maxwidth=250)

        Nice.drop_view = bui.buttonwidget(parent=s.drop_widget,
                                          label='',
                                          size=(100, 100),
                                          position=(40, 120),
                                          button_type='square',
                                          color=(1, 1, 1),
                                          texture=bui.gettexture(drop_texture[Nice.drop_indox]),
                                          mask_texture=bui.gettexture('characterIconMask'),
                                          on_activate_call=bs.Call(Picker, 69))

        s.drop_where = bui.buttonwidget(parent=s.drop_widget,
                                        label='',  # Where To Deploy?
                                        color=cola,
                                        textcolor=wht,
                                        size=(150, 100),
                                        position=(170, 120),
                                        button_type='square',
                                        on_activate_call=s.where_to_drop)
        s.update_cords_view(69)

        bui.buttonwidget(parent=s.drop_widget,
                         label='Edit\nAttrs',
                         color=cola,
                         textcolor=wht,
                         size=(100, 100),
                         position=(350, 120),
                         button_type='square',
                         on_activate_call=s.edit_drop_attrs)

        bui.buttonwidget(parent=s.drop_widget,
                         label='Locate position',
                         size=(120, 25),
                         position=(180, 85),
                         color=colb,
                         textcolor=wht,
                         button_type='square',
                         on_activate_call=bs.Call(s.show_in_game, 0, 69))

        bui.buttonwidget(parent=s.drop_widget,
                         label='Draw a line',
                         size=(120, 25),
                         position=(180, 50),
                         button_type='square',
                         color=colb,
                         textcolor=wht,
                         on_activate_call=bs.Call(s.show_in_game, 1, 69))

        Nice.drop_name = bui.textwidget(parent=s.drop_widget,
                                        text=drop_name[Nice.drop_indox],
                                        h_align='center',
                                        v_align='center',
                                        position=(65, 85))

        def back(): s.kill(True, s.drop_widget, True); Nice.pending2 = []
        bacc = bui.buttonwidget(
            parent=s.drop_widget,
            size=(60, 20),
            label='Back',
            textcolor=wht,
            scale=s.scale,
            color=colb,
            position=(30, 30),
            on_activate_call=back)
        bui.containerwidget(edit=s.drop_widget, cancel_button=bacc)

        bui.buttonwidget(
            parent=s.drop_widget,
            size=(100, 40),
            label='Drop',
            color=colb,
            scale=s.scale,
            textcolor=wht,
            position=(350, 30),
            on_activate_call=bs.Call(s.do_drop))

    def edit_drop_attrs(s):
        s.edit_drop_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                                 size=(300, 350),
                                                 stack_offset=s.soff,
                                                 color=cola,
                                                 transition=s.anim_in,
                                                 scale=s.scale)

        bui.textwidget(parent=s.edit_drop_widget,
                       color=(0.1, 0.7, 1),
                       text='Edit Attributes',
                       position=(70, 300),
                       maxwidth=250)

        bui.textwidget(parent=s.edit_drop_widget,
                       color=wht,
                       position=(30, 250),
                       size=(150, 30),
                       text="gravity_scale",
                       click_activate=True,
                       selectable=True,
                       on_activate_call=bs.Call(s.welp, -1))

        bui.textwidget(parent=s.edit_drop_widget,
                       color=wht,
                       position=(30, 220),
                       size=(150, 30),
                       text="sticky",
                       click_activate=True,
                       selectable=True,
                       on_activate_call=bs.Call(s.welp, -2))

        bui.textwidget(parent=s.edit_drop_widget,
                       color=wht,
                       position=(30, 190),
                       size=(150, 30),
                       text="reflection='powerup'",
                       maxwidth=190,
                       click_activate=True,
                       selectable=True,
                       on_activate_call=bs.Call(s.welp, -3))

        bui.textwidget(parent=s.edit_drop_widget,
                       color=wht,
                       position=(30, 160),
                       size=(150, 30),
                       text="reflection='soft'",
                       maxwidth=190,
                       click_activate=True,
                       selectable=True,
                       on_activate_call=bs.Call(s.welp, -4))

        bui.textwidget(parent=s.edit_drop_widget,
                       color=wht,
                       position=(30, 130),
                       size=(150, 30),
                       text="reflection_scale",
                       maxwidth=190,
                       click_activate=True,
                       selectable=True,
                       on_activate_call=bs.Call(s.welp, -5))

        s.drop_attr1 = bui.textwidget(parent=s.edit_drop_widget,
                                      color=wht,
                                      position=(220, 250),
                                      editable=True,
                                      size=(70, 30),
                                      text=str(Nice.node_gravity_scale),
                                      description="Default: 1.0, More: Heavier, Less: Lighter, Enter")

        bui.checkboxwidget(parent=s.edit_drop_widget,
                           value=s.node_sticky,
                           text="",
                           color=colb,
                           scale=s.scale/1.3,
                           on_value_change_call=bs.Call(s.check_drop_attrs, 0),
                           position=(225, 220))

        s.drop_radio1 = bui.checkboxwidget(parent=s.edit_drop_widget,
                                           value=s.node_reflect,
                                           text="",
                                           color=colb,
                                           scale=s.scale/1.3,
                                           on_value_change_call=bs.Call(s.check_drop_attrs, 1),
                                           position=(225, 190))

        s.drop_radio2 = bui.checkboxwidget(parent=s.edit_drop_widget,
                                           value=s.node_reflect2,
                                           text="",
                                           color=colb,
                                           scale=s.scale/1.3,
                                           on_value_change_call=bs.Call(s.check_drop_attrs, 2),
                                           position=(225, 160))

        s.drop_attr2 = bui.textwidget(parent=s.edit_drop_widget,
                                      color=wht,
                                      position=(220, 130),
                                      editable=True,
                                      size=(70, 30),
                                      text=str(Nice.node_reflection_scale[0]),
                                      description="Default: 1.2, More: more shiny! while Less: more plain, Enter")

        bacc = bui.buttonwidget(
            parent=s.edit_drop_widget,
            size=(60, 20),
            label='Back',
            textcolor=wht,
            scale=s.scale,
            color=colb,
            position=(30, 30),
            on_activate_call=bs.Call(s.collect_drop_attrs))
        bui.containerwidget(edit=s.edit_drop_widget, cancel_button=bacc)

        bui.buttonwidget(
            parent=s.edit_drop_widget,
            size=(60, 20),
            label='Help',
            color=colb,
            textcolor=wht,
            scale=s.scale,
            position=(200, 30),
            on_activate_call=bs.Call(s.welp, 69123))

    def collect_drop_attrs(s):
        t1 = cast(str, bui.textwidget(query=s.drop_attr1))
        t2 = cast(str, bui.textwidget(query=s.drop_attr2))
        try:
            v1 = float(t1)
        except:
            error(f"Invalid gravity_scale value '{t1}'\nrequired value: float\nexample: 6.89")
            return
        try:
            v2 = float(t2)
        except:
            error(f"Invalid reflection_scale value '{t2}'\nrequired value: float\nexample: 6.89")
            return
        s.kill(True, s.edit_drop_widget, True)
        Nice.node_gravity_scale = v1
        Nice.node_reflection_scale = [float(cast(str, bui.textwidget(query=s.drop_attr2)))]

    def check_drop_attrs(s, i, b):
        if not i:
            Nice.node_sticky = b
        if i == 1:
            Nice.node_reflect = b
            bui.checkboxwidget(edit=s.drop_radio2, value=False)
            Nice.node_reflect2 = False
        if i == 2:
            Nice.node_reflect2 = b
            bui.checkboxwidget(edit=s.drop_radio1, value=False)
            Nice.node_reflect = False

    def do_drop(s):
        p = Nice.drop_cords
        if p[0] == 69123:
            error("No position provided")
            return
        i = Nice.drop_indox
        powerup = Nice.drop_indox < 9
        bui.getsound("spawn").play()
        with ga().context:
            n = None
            if powerup:
                b = powerup_name[i]
                n = PowerupBox(position=p, poweruptype=b).autoretain()
                n = n.node
            else:
                bss = 1.0
                br = 2.0
                if "big_bomb" in Nice.pending2:
                    bss = 2.5
                    br = 12.5
                if i == 9:  # TNT
                    n = Bomb(position=p, bomb_type='tnt', bomb_scale=bss,
                             blast_radius=br).autoretain()
                    n = n.node
                if i == 10:  # Peaceful Mine
                    n = Bomb(position=p, bomb_type='land_mine',
                             bomb_scale=bss, blast_radius=br).autoretain()
                    n = n.node
                if i == 11:  # Lit Mine
                    n = Bomb(position=p, bomb_type='land_mine', bomb_scale=bss,
                             blast_radius=br).autoretain()
                    n.arm()  # returns None
                    n = n.node
                if i > 11 and i < 17:  # Eggs
                    from bascenev1lib.gameutils import SharedObjects
                    shared = SharedObjects.get()
                    num = i - 11
                    tex = f"eggTex{i - 11}" if i < 15 else "white" if i < 16 else "empty"
                    n = bs.newnode('prop',
                                   delegate=s,
                                   attrs={
                                       'mesh': bs.getmesh("egg"),
                                       'color_texture': bs.gettexture(tex),
                                       'body': 'capsule',
                                       'reflection': 'soft',
                                       'mesh_scale': 0.5,
                                       'body_scale': 0.6,
                                       'density': 4.0,
                                       'reflection_scale': [0.15],
                                       'shadow_size': 0.6,
                                       'position': p,
                                       'materials': [shared.object_material, bs.Material()],
                                   },
                                   )
                if i > 16 and i < 21:
                    n = Bomb(position=p, bomb_type=bomb_type[i - 17]).autoretain()
                    n = n.node
            # apply configs
            n.gravity_scale = Nice.node_gravity_scale
            n.sticky = Nice.node_sticky
            if Nice.node_reflect:
                n.reflection = 'powerup'
            elif Nice.node_reflect2:
                n.reflection = 'soft'
            n.reflection_scale = Nice.node_reflection_scale
            if "long_fuse" in Nice.pending2:
                n.fuse_length = 5

    def where_to_drop(s):
        s.where_drop_widget = s.DW = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                                         size=(300, 250),
                                                         color=cola,
                                                         stack_offset=s.soff,
                                                         transition=s.anim_in,
                                                         scale=s.scale)
        bui.buttonwidget(parent=s.DW,
                         size=(200, 50),
                         label="Current Position",
                         textcolor=wht,
                         scale=s.scale,
                         color=colb,
                         position=(20, 125),
                         on_activate_call=bs.Call(s.use_my_pos, 69))

        bui.textwidget(parent=s.DW,
                       color=(0.1, 0.7, 1),
                       text='Where to deploy?',
                       scale=s.scale,
                       h_align='center',
                       v_align='center',
                       position=(125, 200))

        bui.buttonwidget(parent=s.DW,
                         size=(200, 50),
                         label="Custom Position",
                         scale=s.scale,
                         color=colb,
                         textcolor=wht,
                         position=(20, 60),
                         on_activate_call=bs.Call(s.custom_drop_window))

        bacc = bui.buttonwidget(
            parent=s.DW,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, s.DW))
        bui.containerwidget(edit=s.DW, cancel_button=bacc)

    # custom position
    def custom_drop_window(s):
        s.kill(True, s.DW)
        custom_drop_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                                 size=(300, 250),
                                                 color=cola,
                                                 stack_offset=s.soff,
                                                 transition=s.anim_in,
                                                 scale=s.scale)
        bui.textwidget(parent=custom_drop_widget,
                       color=(0.1, 0.7, 1),
                       text='Custom Position',
                       scale=s.scale,
                       h_align='center',
                       v_align='center',
                       position=(125, 200))
        txt = str(Nice.drop_cords[0])
        x = bui.textwidget(
            parent=custom_drop_widget,
            text=txt if txt != '69123' else "0",
            editable=True,
            size=(200, 25),
            h_align='center',
            v_align='center',
            position=(55, 150))
        y = bui.textwidget(
            parent=custom_drop_widget,
            size=(200, 25),
            text=str(Nice.drop_cords[1]),
            editable=True,
            h_align='center',
            v_align='center',
            position=(55, 120))
        z = bui.textwidget(
            parent=custom_drop_widget,
            size=(200, 25),
            text=str(Nice.drop_cords[2]),
            editable=True,
            h_align='center',
            v_align='center',
            position=(55, 90))

        def collect(s):
            w = x
            a = []
            for i in range(3):
                try:
                    a.append(float(cast(str, bui.textwidget(query=w))))
                except:
                    error("Invalid "+("Z" if w == z else "Y" if w == y else "X")+" Cordinate!")
                    return
                w = z if i else y
            s.kill(True, custom_drop_widget)
            bui.getsound('gunCocking').play()
            Nice.drop_cords = tuple(a)
            s.update_cords_view(69)

        def back(s):
            s.kill(True, custom_drop_widget)
            s.where_to_drop()

        bui.buttonwidget(
            parent=custom_drop_widget,
            size=(60, 20),
            label='Set',
            color=colb,
            textcolor=wht,
            scale=s.scale,
            position=(190, 30),
            on_activate_call=bs.Call(collect, s))

        bacc = bui.buttonwidget(
            parent=custom_drop_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            textcolor=wht,
            color=colb,
            position=(30, 30),
            on_activate_call=bs.Call(back, s))
        bui.containerwidget(edit=custom_drop_widget, cancel_button=bacc)

    def spawn_window(s):
        if ga() is None:
            push('Spawning requires you to be the host!', color=(1, 1, 0))
            return
        global spawn_widget, nice_name, nice_view, cords_view, title_node
        spawn_widget = s._sw = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                                   size=(500, 300),
                                                   color=cola,
                                                   stack_offset=s.soff,
                                                   transition=s.anim_in,
                                                   scale=s.scale)
        bui.textwidget(parent=spawn_widget,
                       color=(0.1, 0.7, 1),
                       text='Spawn',
                       position=(200, 250),
                       maxwidth=250)

        nice_view = bui.buttonwidget(parent=spawn_widget,
                                     label='',
                                     size=(100, 100),
                                     position=(30, 120),
                                     button_type='square',
                                     color=(1, 1, 1),
                                     texture=bui.gettexture(bot_texture[Nice.indox]+'Icon'),
                                     mask_texture=bui.gettexture('characterIconMask'),
                                     on_activate_call=Picker)

        bui.buttonwidget(edit=nice_view, tint_texture=bui.gettexture(
            bot_texture[bot_name.index(Nice.val_attrs[1])]+'IconColorMask'))
        bui.buttonwidget(
            edit=nice_view, tint_color=Nice.val_attrs[6], tint2_color=Nice.val_attrs[11])

        cords_view = bui.buttonwidget(parent=spawn_widget,
                                      label='Where To\nSpawn?',
                                      color=colb,
                                      textcolor=wht,
                                      size=(180, 100),
                                      position=(150, 120),
                                      button_type='square',
                                      on_activate_call=bs.Call(s.cords_window))

        attr_view = bui.buttonwidget(parent=spawn_widget,
                                     label='Edit\nAttrs',
                                     color=colb,
                                     size=(100, 100),
                                     textcolor=wht,
                                     position=(350, 120),
                                     button_type='square',
                                     on_activate_call=bs.Call(s.attr_window))

        try:
            if cords[0] != 69123:
                s.update_cords_view()
        except TypeError:
            error('No coordinates set')

        nice_name = bui.textwidget(parent=spawn_widget,
                                   text=bot_name[Nice.indox],
                                   h_align='center',
                                   v_align='center',
                                   position=(50, 85))

        bui.buttonwidget(parent=spawn_widget,
                         label='Locate position',
                         size=(120, 25),
                         position=(180, 85),
                         color=colb,
                         textcolor=wht,
                         button_type='square',
                         on_activate_call=bs.Call(s.show_in_game))

        bui.buttonwidget(parent=spawn_widget,
                         label='Draw a line',
                         size=(120, 25),
                         position=(180, 50),
                         button_type='square',
                         color=colb,
                         textcolor=wht,
                         on_activate_call=bs.Call(s.show_in_game, 1))

        def back(s):
            s.kill(True, spawn_widget)
            Nice.pending = []
        bacc = bui.buttonwidget(
            parent=spawn_widget,
            size=(60, 20),
            label='Back',
            textcolor=wht,
            scale=s.scale,
            color=colb,
            position=(30, 30),
            on_activate_call=bs.Call(back, s))
        bui.containerwidget(edit=s._sw, cancel_button=bacc)

        bui.buttonwidget(
            parent=spawn_widget,
            size=(100, 40),
            label='Spawn',
            color=colb,
            scale=s.scale,
            textcolor=wht,
            position=(350, 30),
            on_activate_call=bs.Call(s.do_spawn))

    """Button, my little wrappie"""
    def Button(s):
        def lmao(self):
            Nice()
            self._resume()

        def openBox(self):
            bui.buttonwidget(edit=self.sbox, icon=bui.gettexture('chestOpenIcon'))
            bs.apptimer(0.6, bs.Call(closeBox, self))

        def closeBox(self):
            if self.sbox.exists():
                bui.buttonwidget(edit=self.sbox, icon=bui.gettexture('chestIcon'))

        def wrap(self=mm.MainMenuWindow._refresh_in_game, *args, **kwargs):
            r = s(self, *args, **kwargs)
            h = 125
            v = self._height - 60.0
            self.sbox = bui.buttonwidget(
                color=colb,
                parent=self._root_widget,
                position=(-100, self._height),
                size=(100, 50),
                scale=1.0,
                textcolor=wht,
                label="Sandbox",
                icon=bui.gettexture('chestIcon'),
                iconscale=0.8,
                on_select_call=bs.Call(openBox, self),
                on_activate_call=bs.Call(lmao, self))
            return r
        return wrap

    # coordinates
    def cords_window(s):
        global cords_widget
        cords_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                           size=(300, 250),
                                           color=cola,
                                           stack_offset=s.soff,
                                           transition=s.anim_in,
                                           scale=s.scale)
        bui.buttonwidget(parent=cords_widget,
                         size=(200, 50),
                         label="Current Position",
                         textcolor=wht,
                         scale=s.scale,
                         color=colb,
                         position=(20, 125),
                         on_activate_call=bs.Call(s.use_my_pos))

        bui.textwidget(parent=cords_widget,
                       color=(0.1, 0.7, 1),
                       text='Where to spawn?',
                       scale=s.scale,
                       h_align='center',
                       v_align='center',
                       position=(125, 200))

        bui.buttonwidget(parent=cords_widget,
                         size=(200, 50),
                         label="Custom Position",
                         scale=s.scale,
                         color=colb,
                         textcolor=wht,
                         position=(20, 60),
                         on_activate_call=bs.Call(s.custom_window))

        bacc = bui.buttonwidget(
            parent=cords_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, cords_widget))
        bui.containerwidget(edit=cords_widget, cancel_button=bacc)

    # custom position
    def custom_window(s):
        s.kill(True, cords_widget)
        global cords
        try:
            txt = str(cords[0]) if cords[0] != 69123 else "0"
        except TypeError:
            cords = (0, 0, 0)
            txt = "0"
        custom_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                            size=(300, 250),
                                            color=cola,
                                            stack_offset=s.soff,
                                            transition=s.anim_in,
                                            scale=s.scale)
        bui.textwidget(parent=custom_widget,
                       color=(0.1, 0.7, 1),
                       text='Custom Position',
                       scale=s.scale,
                       h_align='center',
                       v_align='center',
                       position=(125, 200))

        x = bui.textwidget(
            parent=custom_widget,
            text=txt,
            editable=True,
            size=(200, 25),
            h_align='center',
            v_align='center',
            position=(55, 150))
        y = bui.textwidget(
            parent=custom_widget,
            size=(200, 25),
            text=str(cords[1]),
            editable=True,
            h_align='center',
            v_align='center',
            position=(55, 120))
        z = bui.textwidget(
            parent=custom_widget,
            size=(200, 25),
            text=str(cords[2]),
            editable=True,
            h_align='center',
            v_align='center',
            position=(55, 90))

        def collect(s):
            global cords
            w = x
            a = []
            for i in range(3):
                try:
                    a.append(float(cast(str, bui.textwidget(query=w))))
                except:
                    error("Invalid "+("Z" if w == z else "Y" if w == y else "X")+" Cordinate!")
                    return
                w = z if i else y
            s.kill(True, custom_widget)
            bui.getsound('gunCocking').play()
            cords = tuple(a)
            s.update_cords_view()

        def back(s):
            s.kill(True, custom_widget)
            s.cords_window()

        bui.buttonwidget(
            parent=custom_widget,
            size=(60, 20),
            label='Set',
            color=colb,
            textcolor=wht,
            scale=s.scale,
            position=(190, 30),
            on_activate_call=bs.Call(collect, s))

        bacc = bui.buttonwidget(
            parent=custom_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            textcolor=wht,
            color=colb,
            position=(30, 30),
            on_activate_call=bs.Call(back, s))
        bui.containerwidget(edit=custom_widget, cancel_button=bacc)

    def attr_window(s):
        global attr_widget
        attr_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                          size=(400, 500),
                                          color=cola,
                                          stack_offset=(-s.soff[0], -s.soff[1]),
                                          transition=s.anim_inv,
                                          scale=s.scale)

        attr_scroll = bui.scrollwidget(parent=attr_widget,
                                       position=(30, 80),
                                       claims_up_down=False,
                                       claims_left_right=True,
                                       autoselect=True,
                                       size=(350, 370))

        bui.textwidget(parent=attr_widget,
                       color=(0.1, 0.7, 1),
                       text='Edit Attributes',
                       scale=s.scale,
                       h_align='center',
                       v_align='center',
                       position=(180, 460))

        bacc = bui.buttonwidget(
            parent=attr_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 45),
            on_activate_call=s.gather)
        bui.containerwidget(edit=attr_widget, cancel_button=bacc)

        bui.buttonwidget(
            parent=attr_widget,
            size=(60, 20),
            label='Help',
            color=colb,
            textcolor=wht,
            scale=s.scale,
            position=(290, 45),
            on_activate_call=bs.Call(s.welp, 69123))

        bui.buttonwidget(
            parent=attr_widget,
            size=(80, 20),
            label='Random',
            textcolor=wht,
            scale=s.scale,
            color=colb,
            position=(150, 45),
            on_activate_call=bs.Call(s.gather, True))

        bui.checkboxwidget(
            parent=attr_widget,
            size=(200, 20),
            position=(40, 20),
            text="Ran auto spawn",
            color=cola,
            textcolor=(1, 1, 1),
            scale=s.scale/2,
            value=s.auto_spawn_on_random,
            on_value_change_call=bs.Call(s.tick, 0))

        bui.checkboxwidget(
            parent=attr_widget,
            size=(200, 20),
            position=(220, 20),
            text="Ran peace",
            color=cola,
            textcolor=(1, 1, 1),
            scale=s.scale/2,
            value=s.random_peace,
            on_value_change_call=bs.Call(s.tick, 1))

        # -> no = 23
        # -> cw = 595 (+26)
        # -> cb = 440 (+20)
        # -> tw = 435 (+19)
        cw = 757
        cb = 560
        tw = 553

        et = tw
        attr_sub = bui.containerwidget(parent=attr_scroll,
                                       background=False,
                                       size=(190, cw),
                                       color=(0.3, 0.3, 0.3),
                                       scale=s.scale)
        global ins
        ins = []
        for i in range(len(attrs)):
            bui.textwidget(parent=attr_sub,
                           text=attrs[i],
                           scale=s.scale/2,
                           h_align='left',
                           v_align='center',
                           on_activate_call=bs.Call(s.welp, i),
                           selectable=True,
                           autoselect=True,
                           click_activate=True,
                           size=(180, 29),
                           position=(-30, tw - (20 * i)))
            a = Nice.val_attrs[i]
            if isinstance(a, bool):
                l = bui.checkboxwidget(parent=attr_sub,
                                       value=a,
                                       text="",
                                       color=colb,
                                       scale=s.scale/2,
                                       on_value_change_call=bs.Call(s.check, i),
                                       position=(180, cb - (20 * i)))
            elif isinstance(a, tuple) or i == 6 or i == 11 or i == 28:
                k = Nice.val_attrs[i]
                l = bui.buttonwidget(parent=attr_sub,
                                     label=f"{str(a[0]+0.01)[:3]} {str(a[1]+0.01)
                                                                   [:3]}, {str(a[2]+0.01)[:3]}",
                                     scale=s.scale,
                                     size=(30, 12),
                                     color=k,
                                     textcolor=(1-k[0], 1-k[1], 1-k[2]),  # invert
                                     on_activate_call=bs.Call(NicePick, s, a, i),
                                     position=(180, cb - (20 * i)))
            else:
                l = bui.textwidget(parent=attr_sub,
                                   text=str(a),
                                   scale=s.scale/2,
                                   h_align='left',
                                   v_align='center',
                                   editable=True,
                                   color=(1, 1, 1),
                                   size=(150, 25),
                                   position=(150, et - (20 * i)))
            ins.append(l)

    # on back press
    def gather(s, ran=False, close=True):
        global nice_view
        for i in range(len(ins)):
            if bui.Widget.get_widget_type(ins[i]) == 'text':
                v = cast(str, bui.textwidget(query=ins[i]))
                t = type_attrs[i]
                if t == 'float':
                    if ran:
                        v = random.uniform(0.0, 9.9)
                        bui.textwidget(edit=ins[i], text=str(v)[:3])
                    else:
                        try:
                            v = float(v)
                        except ValueError:
                            error(
                                f"{attrs[i]}: Invalid value '{v}'\nRequired type: float, Given type: {type(v).__name__}\nExample of float: 3.141592 (decimal number)")
                            return
                elif t == 'int':
                    if ran:
                        v = random.randrange(0, 7)
                        bui.textwidget(edit=ins[i], text=str(v))
                    else:
                        try:
                            v = int(v)
                        except ValueError:
                            error(
                                f"{attrs[i]}: Invalid value '{v}'\nRequired type: int, Given type: {type(v)}\nExample of int: 68 (number)")
                            return
                else:
                    # print (f"checking={v} v_in_bot_name={v in bot_name} not_i={not i} i={i}")
                    if not v in bot_name and i == 1:
                        if ran:
                            v = random.choice(bot_name)
                            s.spawn(bot_name.index(v))  # update preview
                            bui.textwidget(edit=ins[i], text=str(v))
                        else:
                            error(f"character: Invalid character '{v}'")
                            if v in w_bot_name:
                                push(
                                    f"Did you mean '{bot_name[w_bot_name.index(v)]}'?", color=(0, 0.6, 1))
                            return
                    elif i == 1:
                        if ran:
                            v = random.choice(bot_name)
                        try:
                            s.spawn(bot_name.index(v))  # update preview
                        except TypeError:
                            Nice.spawn(Nice, bot_name.index(v))
                        bui.textwidget(edit=ins[i], text=str(v))
                    elif not v in bomb_type and i == 8:
                        if ran:
                            v = random.choice(bomb_type)
                            bui.textwidget(edit=ins[i], text=str(v))
                        else:
                            error(f"default_bomb_type: Invalid bomb type '{v}'")
                            if v in w_bomb_type:
                                push(
                                    f"Did you mean '{bomb_type[w_bomb_type.index(v)]}'?", color=(0, 0.6, 1))
                            return
                    elif v in bomb_type and ran and i == 8:
                        v = random.choice(bomb_type)
                        bui.textwidget(edit=ins[i], text=str(v))
                Nice.val_attrs[i] = v
            if bui.Widget.get_widget_type(ins[i]) == 'checkbox' and ran:
                v = random.choice([True, False]) if not s.random_peace else False
                bui.checkboxwidget(edit=ins[i], value=v)
                Nice.val_attrs[i] = v
            elif bui.Widget.get_widget_type(ins[i]) == 'button' and ran:
                a = []
                for r in range(3):
                    a.append(random.uniform(0.0, 1.0))
                a = (float(a[0]), float(a[1]), float(a[2]))
                bui.buttonwidget(edit=ins[i], label=f"{str(a[0]+0.01)[:3]} {str(a[1]+0.01)[:3]}, {str(a[2]+0.01)[:3]}", color=(
                    a[0], a[1], a[2]), textcolor=(1-a[0], 1-a[1], 1-a[2]))
                Nice.val_attrs[i] = a
                bui.buttonwidget(edit=nice_view, tint_texture=bui.gettexture(
                    bot_texture[bot_name.index(Nice.val_attrs[1])]+'IconColorMask'))
                bui.buttonwidget(
                    edit=nice_view, tint_color=Nice.val_attrs[6], tint2_color=Nice.val_attrs[11])
        if not ran and close:
            s.kill(True, attr_widget, rev=True)
        elif ran:
            bui.getsound('cashRegister2').play()
            if s.auto_spawn_on_random:
                s.do_spawn()

    def control_window(s):
        if ga() is None:
            push('How control and you are not the host?', color=(1, 1, 0))
            return
        global control_widget, lmao, lmao_bots, old_ga, preview_image, preview_text, dux, preview_text2, preview_text3, start_stop, preview_text4, currently_txt, currently_dux, control_ones, fresh, bomb_control
        try:
            a = bomb_control
        except NameError:
            bomb_control = False
        fresh = True

        control_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                             size=(500, 300),
                                             stack_offset=s.soff,
                                             color=cola,
                                             transition=s.anim_in,
                                             scale=s.scale)
        try:
            p1 = lmao[currently_dux]
            p2 = lmao_bots[currently_dux].character
            lol = bui.gettexture(bot_texture[bot_name.index(p2)]+"Icon")
        except NameError:
            p1 = 'Name'
            p2 = 'Character'
            lol = None
        preview_image = bui.buttonwidget(parent=control_widget,
                                         label='',
                                         size=(50, 50),
                                         position=(300, 175),
                                         button_type='square',
                                         color=(1, 1, 1),
                                         texture=lol,
                                         mask_texture=bui.gettexture('characterIconMask'),
                                         on_activate_call=bs.Call(push, 'Set the skin in modify menu'))

        preview_text = bui.textwidget(parent=control_widget,
                                      text=p1,
                                      size=(50, 50),
                                      scale=s.scale/1.3,
                                      position=(365, 175))

        preview_text2 = bui.textwidget(parent=control_widget,
                                       text=p2,
                                       size=(50, 50),
                                       scale=s.scale/1.7,
                                       position=(360, 155))

        # '{100 * (1 - lmao_bots[0].node.hurt)}%'
        preview_text3 = bui.textwidget(parent=control_widget,
                                       text='',
                                       size=(50, 50),
                                       scale=s.scale/1.7,
                                       position=(295, 125))

        try:
            test = currently_txt
        except NameError:
            test = 'Control started\nnow tap a bot'
        preview_text4 = bui.textwidget(parent=control_widget,
                                       text='Press start\nto start controlling' if not on_control else test,
                                       size=(50, 50),
                                       scale=s.scale/1.7,
                                       position=(295, 85))

        bui.textwidget(parent=control_widget,
                       color=(0.1, 0.7, 1),
                       text='Control',
                       position=(200, 250),
                       maxwidth=250)

        start_stop = bui.buttonwidget(
            parent=control_widget,
            size=(70, 30),
            label='Stop' if on_control else 'Start',
            icon=bui.gettexture('ouyaAButton' if on_control else 'ouyaOButton'),
            iconscale=0.5,
            button_type='square',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(370, 30),
            on_activate_call=bs.Call(s.start_or_stop))  # , True))

        control_scroll = bui.scrollwidget(parent=control_widget,
                                          position=(30, 80),
                                          claims_up_down=False,
                                          claims_left_right=True,
                                          autoselect=True,
                                          size=(250, 150))

        control_sub = bui.containerwidget(parent=control_scroll,
                                          background=False,
                                          size=(190, len(lmao)*26),
                                          color=(0.3, 0.3, 0.3),
                                          scale=s.scale)

        bacc = bui.buttonwidget(
            parent=control_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, control_widget))
        bui.containerwidget(edit=control_widget, cancel_button=bacc)

        bui.checkboxwidget(
            parent=control_widget,
            size=(300, 20),
            color=cola,
            text='Bomb to switch control',
            value=bomb_control,
            scale=s.scale/2,
            position=(120, 35),
            textcolor=(1, 1, 1),
            on_value_change_call=s.check_bomb)

        if len(lmao) == 0 or str(ga()) != old_ga:
            bui.textwidget(parent=control_sub,
                           text='no bots',
                           h_align='center',
                           v_align='center',
                           size=(60, 29),
                           position=(60, -62))
        control_ones = []
        for i in range(len(lmao)):
            try:
                alive = lmao_bots[i].node.hurt < 1
            except IndexError:
                s.kill(True, control_widget)
                push('Wait for that bot to spawn first')
                return
            except AttributeError:
                alive = False
            da_one = bui.textwidget(parent=control_sub,
                                    scale=s.scale/2,
                                    text=(lmao[i] if alive else f"{lmao[i]} (dead)"),
                                    h_align='left',
                                    v_align='center',
                                    color=((1, 1, 1) if alive else (0.6, 0.6, 0.6)),
                                    on_activate_call=bs.Call(s.preview, i, alive),
                                    selectable=True,
                                    autoselect=True,
                                    click_activate=True,
                                    size=(180, 29),
                                    position=(-30, (20 * i)))
            control_ones.append(da_one)
        try:
            control_ones[currently_dux].activate()
        except NameError:
            pass

    def check_bomb(s, b):
        global bomb_control
        bomb_control = b

    def preview(s, i, alive, mod=0):
        global preview_image, preview_text, lmao, dux, lmao_bots, lmao_chars, preview_text2, preview_text3, drux, val_attrs2, val_arr, on_control, currently_dux, effect_dux
        global effect_widget, mod_widget, control_widget, lmao_chars2, lmao2, effect_dux2
        # special case
        if i == 69123:
            bui.textwidget(edit=preview_text, text='All bots', color=(1, 1, 1))
            bui.textwidget(edit=preview_text2, text='real', color=(0.8, 0.8, 0.8))
            bui.buttonwidget(edit=preview_image, texture=bui.gettexture(
                "achievementSharingIsCaring"), tint_texture=None, mask_texture=None)
            s.select_all_bots = True
            return
        s.select_all_bots = False
        try:
            bui.checkboxwidget(edit=s.select_all, value=False)
        except:
            pass
        drux = i
        _lmao_chars = lmao_chars if mod != 3 else lmao_chars2
        _lmao = lmao if mod != 3 else lmao2
        _lmao_bots = lmao_bots if mod != 3 else lmao_players
        bui.textwidget(edit=preview_text, text=_lmao[i], color=(
            (1, 1, 1) if alive else (0.6, 0.6, 0.6)))
        bui.textwidget(edit=preview_text2, text=_lmao_chars[i], color=(
            (0.8, 0.8, 0.8) if alive else (0.4, 0.4, 0.4)))
        bui.buttonwidget(edit=preview_image, tint_texture=bui.gettexture(
            bot_texture[bot_name.index(_lmao_chars[i])]+'IconColorMask'))
        if mod != 3:
            bui.buttonwidget(edit=preview_image,
                             tint_color=val_arr[drux][6], tint2_color=val_arr[drux][11])
        if alive:
            try:
                if not on_control:
                    s.hl3(i)
            except AttributeError:
                error('this bot is dead, reopen window')
                alive = False
                # TODO array containing lmao bot text ins so we can live change
        else:
            s.hl3(None, False)
        try:
            hurt = _lmao_bots[i].node.hurt if mod != 3 else _lmao_bots[i].actor.node.hurt
        except AttributeError:
            pass  # bot is GONE
        try:
            hp_txt = f'HP: {"%.2f" % (100 * (1 - hurt))}%'
        except AttributeError:
            hp_txt = 'HP: 0.00%'
        except NameError:
            hp_txt = 'HP: 0.00% (gone)'
        bui.textwidget(edit=preview_text3, text=hp_txt, color=(
            (0.8, 0.8, 0.8) if alive else (0.4, 0.4, 0.4)))
        dux = i
        if not mod:
            currently_dux = i
        elif mod == 2:
            effect_dux = i
        elif mod == 3:
            effect_dux2 = i
        bot = _lmao_bots[dux]
        char = _lmao_chars[dux]
        skin = bot_texture[bot_name.index(char)]  # neoSpaz
        icon = bui.gettexture(skin+'Icon')  # texture: neoSpazIcon
        bui.buttonwidget(edit=preview_image, texture=icon, color=(
            (1, 1, 1) if alive else (0.6, 0.6, 0.6)))
        if mod or on_control:
            s.assign()

    def start_or_stop(s):
        global on_control, start_stop, lmao, fresh, currently_dux, lmao_bots
        try:
            KO = lmao_bots[currently_dux].node.hurt == 1
        except NameError:
            error("Start your brain first")
            return
        except AttributeError:
            KO = True
        if KO:
            error(f"{lmao[currently_dux]} is dead.")
            return
        fresh = False
        if not len(lmao):
            error('it literally says no bots bruh\nuse spawn menu')
            return
        on_control = b = not on_control
        bui.buttonwidget(edit=start_stop, label='Stop' if b else 'Start')
        bui.buttonwidget(edit=start_stop, icon=bui.gettexture(
            'ouyaAButton' if b else 'ouyaOButton'))
        if b:
            if random.choice([1, 0, 0]):
                push('You can switch control by selecting another bot')
            s.reset_bright_bots()
        KO = False
        s.assign()

    def assign(s):  # bool):
        global on_control, lmao, dux, start_stop, preview_text4, currently_txt, currently_dux, control_widget, preview_text2, old_dux, control_ones, fresh, allow_assign, alive_bots, alive_arr
        try:
            if control_widget.exists():
                allow_assign = True
            if not allow_assign:
                return
            allow_assign = False  # for outside control
        except NameError:
            return  # coming from modify widget lol
        for i in ga().players:
            if i.sessionplayer.inputdevice.client_id == -1:
                i.resetinput()  # clean up previous control
                with ga().context:
                    i.actor.connect_controls_to_player()
                if not on_control:
                    push('Stopped control for good', color=(0.4, 0.1, 0.2))
                    try:
                        s.draw()
                    except:
                        s.draw(s)
                    old_dux = None
                    try:
                        bui.textwidget(edit=preview_text4, text="Press start\nto start controlling")
                    except NameError:
                        pass  # modify again
                    except RuntimeError:
                        pass  # bot died, outside UI control
                    i.actor.node.invincible = False
                    return
                try:
                    s.update_alive_bots()
                    a = lmao_bots[currently_dux].node.hurt
                except TypeError:
                    push('now select a bot to control', color=(0, 0.5, 0))
                    return
                except AttributeError:
                    error(f'{lmao[dux]} is dead, controlling nothing')
                    on_control = False
                    s.assign()
                    bui.buttonwidget(edit=start_stop, label='Start',
                                     icon=bui.gettexture("ouyaOButton"))
                    return
                if cast(str, bui.textwidget(query=preview_text4)) == 'Character':
                    push('good, now select a bot to control', color=(0, 0.5, 0))
                    return
                if Nice.while_control:
                    i.actor.node.invincible = True
                try:
                    if currently_dux == old_dux and not fresh:
                        push('pressed on an already controlled bot')
                        s.start_or_stop()
                        return
                    elif fresh:
                        fresh = False
                except NameError:
                    pass
                old_dux = currently_dux
                ding(f'Now controlling {lmao[currently_dux]}')
                s.pls_move()
                currently_txt = f"Now controlling\n{lmao[currently_dux]}"
                s.draw(currently_txt)
                bui.textwidget(edit=preview_text4, text=currently_txt)
                s.hl2(lmao_bots[currently_dux].node, True)

                # start colntrol from here
                i.assigninput(ba.InputType.UP_DOWN, bs.Call(s.set_x))
                i.assigninput(ba.InputType.LEFT_RIGHT, bs.Call(s.set_y))
                i.assigninput(ba.InputType.PICK_UP_PRESS, bs.Call(s.key, 0))
                i.assigninput(ba.InputType.BOMB_PRESS, bs.Call(s.key, 3))
                i.assigninput(ba.InputType.PUNCH_PRESS, bs.Call(s.key, 1))
                i.assigninput(ba.InputType.JUMP_PRESS, bs.Call(s.key, 2))
                break  # i have nothing to do w other players left

    def draw(s, what=None, where=(650, 600), color=(0, 1, 1)):
        global nood
        for i in nood:
            i.delete()
        if what is None:
            return
        n = []
        t = what.split('\n')
        p = where
        c = color
        for i in range(len(t)):
            with ga().context:
                n = bs.newnode("text", attrs={
                               "text": t[i],
                               "flatness": 1.0,
                               "h_align": "left",
                               "v_attach": "bottom",
                               "scale": 0.8,
                               "position": (p[0], p[1] - (i * 25)),
                               "color": (c[0]-(i*0.25), c[1]-(i*0.3), c[2]-(i*0.1))
                               })
            nood.append(n)

    def config_window(s):
        if ga() is None:
            push('Sure, ask the HOST that is obv not YOU', color=(1, 1, 0))
            return
        global config_widget, epic_config
        config_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                            size=(500, 350),
                                            stack_offset=s.soff,
                                            color=cola,
                                            transition=s.anim_in,
                                            scale=s.scale)

        bui.textwidget(parent=config_widget,
                       color=(0.1, 0.7, 1),
                       text='Tune',
                       position=(205, 303))

        bui.checkboxwidget(parent=config_widget,
                           color=cola,
                           text="Invincible while controlling bots",
                           textcolor=(1, 1, 1),
                           value=Nice.while_control,
                           on_value_change_call=bs.Call(s.conf, 0),
                           scale=s.scale/1.3,
                           position=(30, 268))

        bui.checkboxwidget(parent=config_widget,
                           color=cola,
                           text="Notify when my bots die",
                           textcolor=(1, 1, 1),
                           value=Nice.notify_bot_ded,
                           on_value_change_call=bs.Call(s.conf, 1),
                           scale=s.scale/1.3,
                           position=(30, 233))

        bui.checkboxwidget(parent=config_widget,
                           color=cola,
                           text="Pause the game when using this",
                           textcolor=(1, 1, 1),
                           value=Nice.pause_when_bots,
                           on_value_change_call=bs.Call(s.conf, 2),
                           scale=s.scale/1.3,
                           position=(30, 198))

        epic_config = bui.checkboxwidget(parent=config_widget,
                                         color=cola,
                                         text="Show screen messages on top right",
                                         textcolor=(1, 1, 1),
                                         value=Nice.top_msg,
                                         on_value_change_call=bs.Call(s.conf, 3),
                                         scale=s.scale/1.3,
                                         position=(30, 163))
#        s.do_your_thing(ga().globalsnode.slow_motion, False)

        bui.checkboxwidget(parent=config_widget,
                           color=cola,
                           text="Lite mode (keep off unless lags)",
                           textcolor=(1, 1, 1),
                           value=Nice.lite_mode,
                           on_value_change_call=bs.Call(s.conf, 4),
                           scale=s.scale/1.3,
                           position=(30, 128))

        bui.checkboxwidget(parent=config_widget,
                           color=cola,
                           text="Rotate camera on control (cool)",
                           textcolor=(1, 1, 1),
                           value=Nice.animate_camera,
                           on_value_change_call=bs.Call(s.conf, 5),
                           scale=s.scale/1.3,
                           position=(30, 93))

        bui.checkboxwidget(parent=config_widget,
                           color=cola,
                           text="Play ding sound on success",
                           textcolor=(1, 1, 1),
                           value=Nice.do_ding,
                           on_value_change_call=bs.Call(s.conf, 6),
                           scale=s.scale/1.3,
                           position=(30, 58))

        bacc = bui.buttonwidget(
            parent=config_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, config_widget))
        bui.containerwidget(edit=config_widget, cancel_button=bacc)

    def conf(s, i, b):
        if not i:
            Nice.while_control = b
            var('while_control', b)
        elif i == 1:
            Nice.notify_bot_ded = b
            var('notify_bot_ded', b)
        elif i == 2:
            Nice.pause_when_bots = b
            var('pause_when_bots', b)
            s.pause(b)
            ding('Applied now!')
        elif i == 3:
            Nice.top_msg = b
            var('top_msg', b)
        elif i == 4:
            Nice.lite_mode = b
            var('lite_mode', b)
        elif i == 5:
            Nice.animate_camera = b
            var('animate_camera', b)
        elif i == 6:
            Nice.do_ding = b
            var('do_ding', b)

    """do your thing, a dumb node extractor that i coded myself
       simply extracts titles and changes based on game
       eg. Epic Hockey <-> Hockey"""
    def do_your_thing(s, b):
        import json
        global title, virgin, epic_config, title_node
        epic = "Epic " if b else ""

        def fade(node, i):
            try:
                t = title_node[i].text = f"{epic}{title[i]}"
            except:
                pass
            bs.animate(node, 'opacity', {0.0: 0.0, 0.15: 1.0})
        with ga().context:
            if virgin:
                virgin = False  # defined outside as True
                title = []
                title_node = []
                # lets grab those nodes! (sus)
                for n in bs.getnodes()[::-1]:
                    if hasattr(n, 'text'):
                        if 'ARG' in n.text:
                            continue
                        if 'gameNames' not in n.text:
                            continue
                        try:
                            try:
                                title.append(json.loads(n.text)['s'][0][1]['t'][1])
                            except:
                                try:
                                    title.append(json.loads(n.text)['t'][1])
                                except:
                                    continue
                            title_node.append(n)
                        except:
                            pass  # i swear it cusses about int and stuff i had to shut it up
            for i in range(len(title_node)):
                if not title_node[i].exists():
                    continue
                try:
                    bs.animate(title_node[i], 'opacity', {0.0: 1.0, 0.1: 0.0})
                except:
                    return  # what are we doing here
                bs.timer(0.08, bs.Call(fade, title_node[i], i))

    def mod_window(s):
        if ga() is None:
            push('Listen, only game host can modify', color=(1, 1, 0))
            return
        global mod_widget, lmao, lmao_bots, old_ga, preview_image, preview_text, dux, preview_text2, dux2, preview_text3, do_tp
        dux = None

        mod_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                         size=(500, 300),
                                         stack_offset=s.soff,
                                         color=cola,
                                         transition=s.anim_in,
                                         scale=s.scale)

        preview_image = bui.buttonwidget(parent=mod_widget,
                                         label='',
                                         size=(50, 50),
                                         position=(300, 175),
                                         button_type='square',
                                         color=colb,
                                         mask_texture=bui.gettexture('characterIconMask'),
                                         on_activate_call=bs.Call(push, 'Press modify to set the skin and stuff'))

        preview_text = bui.textwidget(parent=mod_widget,
                                      text='',
                                      size=(50, 50),
                                      scale=s.scale/1.3,
                                      position=(365, 175))

        preview_text2 = bui.textwidget(parent=mod_widget,
                                       text='',
                                       size=(50, 50),
                                       scale=s.scale/1.7,
                                       position=(360, 155))

        preview_text3 = bui.textwidget(parent=mod_widget,
                                       text='',
                                       size=(50, 50),
                                       scale=s.scale/1.7,
                                       position=(295, 125))

        bui.textwidget(parent=mod_widget,
                       color=(0.1, 0.7, 1),
                       text='Modify',
                       position=(200, 250),
                       maxwidth=250)

        bui.buttonwidget(
            parent=mod_widget,
            size=(70, 30),
            label='Modify',
            button_type='square',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(370, 30),
            on_activate_call=bs.Call(s.do_modify))

        mod_scroll = bui.scrollwidget(parent=mod_widget,
                                      position=(30, 80),
                                      claims_up_down=False,
                                      claims_left_right=True,
                                      autoselect=True,
                                      size=(250, 150))

        mod_sub = bui.containerwidget(parent=mod_scroll,
                                      background=False,
                                      size=(190, len(lmao)*26),
                                      color=(0.3, 0.3, 0.3),
                                      scale=s.scale)

        bacc = bui.buttonwidget(
            parent=mod_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, mod_widget))
        bui.containerwidget(edit=mod_widget, cancel_button=bacc)

        bui.buttonwidget(edit=preview_image, texture=None, color=(1, 1, 1))
        bui.textwidget(edit=preview_text, text='Name')
        bui.textwidget(edit=preview_text2, text='Character')

        if len(lmao) == 0 or str(ga()) != old_ga:
            bui.textwidget(parent=mod_sub,
                           text='no bots',
                           h_align='center',
                           v_align='center',
                           size=(60, 29),
                           position=(60, -62))
            return

        # selected index is dux
        for i in range(len(lmao)):
            try:
                alive = lmao_bots[i].node.hurt < 1
            except IndexError:
                s.kill(True, mod_widget)
                push('Wait for that bot to spawn first')
                return
            except AttributeError:
                alive = False
            bui.textwidget(parent=mod_sub,
                           scale=s.scale/2,
                           text=(lmao[i] if alive else f"{lmao[i]} (dead)"),
                           h_align='left',
                           v_align='center',
                           color=((1, 1, 1) if alive else (0.6, 0.6, 0.6)),
                           on_activate_call=bs.Call(s.preview, i, alive, 1),
                           selectable=True,
                           autoselect=True,
                           click_activate=True,
                           size=(180, 29),
                           position=(-30, (20 * i)))

    def tp_check(s, b):
        global do_tp
        do_tp = b

    def do_modify(s):
        global mid_widget, indox2, nice2_name, nice2_view, cords2_view, lmao, dux, lmao_bots, max_digits, val_attrs2, val_arr, drux, cords2, dp_tp

        try:
            name = lmao[dux]
        except TypeError:
            error('You what bro?')
            return
        try:
            a = bot_texture[bot_name.index(val_arr[drux][1])]
        except TypeError:
            error('It\'s dead.')
            return
        mid_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                         size=(500, 300),
                                         stack_offset=s.soff,
                                         color=cola,
                                         transition=s.anim_in,
                                         scale=s.scale)

        bui.textwidget(parent=mid_widget,
                       color=(0.1, 0.7, 1),
                       text=f'Modify {name}',
                       position=(150, 250),
                       maxwidth=250)

        nice2_view = bui.buttonwidget(parent=mid_widget,
                                      label='',
                                      size=(100, 100),
                                      position=(30, 120),
                                      button_type='square',
                                      color=(1, 1, 1),
                                      texture=bui.gettexture(
                                          bot_texture[bot_name.index(lmao_chars[dux])]+'Icon'),
                                      mask_texture=bui.gettexture('characterIconMask'),
                                      on_activate_call=bs.Call(Picker, 1))

        # Apply bot's stuff to mod preset (clean up)
        cap = bot_name.index(lmao_chars[drux])
        good_name = bot_name[cap]
        va = val_arr[drux]
        va[1] = good_name

        bui.buttonwidget(edit=nice2_view, tint_texture=bui.gettexture(
            bot_texture[bot_name.index(val_arr[drux][1])]+'IconColorMask'))
        bui.buttonwidget(
            edit=nice2_view, tint_color=val_arr[drux][6], tint2_color=val_arr[drux][11])

        try:
            pus = lmao_bots[dux].node.position
        except AttributeError:
            error(f'{lmao[dux]} is dead.')
            return
        m = max_digits
        cords2_view = bui.buttonwidget(parent=mid_widget,
                                       label=f'changed via\nupdate_cords_view',
                                       color=colb,
                                       textcolor=wht,
                                       size=(180, 100),
                                       position=(150, 120),
                                       button_type='square',
                                       on_activate_call=bs.Call(s.cords2_window))

        attr_view = bui.buttonwidget(parent=mid_widget,
                                     label='Edit\nAttrs',
                                     color=colb,
                                     size=(100, 100),
                                     textcolor=wht,
                                     position=(350, 120),
                                     button_type='square',
                                     on_activate_call=bs.Call(s.do_modify2))

        s.update_cords_view(True)

        nice2_name = bui.textwidget(parent=mid_widget,
                                    text=good_name,
                                    h_align='center',
                                    v_align='center',
                                    position=(50, 85))

        bui.buttonwidget(parent=mid_widget,
                         label='Locate position',
                         size=(120, 25),
                         position=(180, 85),
                         color=colb,
                         textcolor=wht,
                         button_type='square',
                         on_activate_call=bs.Call(s.show_in_game, 0, True))

        bui.buttonwidget(parent=mid_widget,
                         label='Draw a line',
                         size=(120, 25),
                         position=(180, 50),
                         button_type='square',
                         color=colb,
                         textcolor=wht,
                         on_activate_call=bs.Call(s.show_in_game, 1, True))

        bacc = bui.buttonwidget(
            parent=mid_widget,
            size=(60, 20),
            label='Back',
            textcolor=wht,
            scale=s.scale,
            color=colb,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, mid_widget, True))
        bui.containerwidget(edit=mid_widget, cancel_button=bacc)

        bui. buttonwidget(
            parent=mid_widget,
            size=(100, 40),
            label='Apply',
            color=colb,
            scale=s.scale,
            textcolor=wht,
            position=(350, 30),
            on_activate_call=s.apply_mods)

        bui.checkboxwidget(
            parent=mid_widget,
            size=(70, 30),
            text="Teleport",
            value=do_tp,
            color=cola,
            textcolor=(1, 1, 1),
            on_value_change_call=bs.Call(s.tp_check),
            scale=s.scale/1.5,
            position=(340, 90))

        val_attrs2 = val_arr[dux].copy()  # reset to default temp
        indox2 = bot_name.index(val_attrs2[1])

    def do_modify2(s):
        global dux, lmao_bots, mud_widget, val_attrs2
        try:
            if lmao_bots[dux].node.hurt >= 1:
                error(f'{lmao[dux]} is dead.')
                return
        except TypeError:
            error('You what bro?')
            return
        mud_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                         size=(400, 500),
                                         color=cola,
                                         stack_offset=s.soff,
                                         transition=s.anim_in,
                                         scale=s.scale)

        mud_scroll = bui.scrollwidget(parent=mud_widget,
                                      position=(30, 80),
                                      claims_up_down=False,
                                      claims_left_right=True,
                                      autoselect=True,
                                      size=(350, 370))

        bui.textwidget(parent=mud_widget,
                       color=(0.1, 0.7, 1),
                       text='Edit attributes',
                       scale=s.scale,
                       h_align='center',
                       v_align='center',
                       position=(180, 460))

        bacc = bui.buttonwidget(
            parent=mud_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=s.gather2)
        bui.containerwidget(edit=mud_widget, cancel_button=bacc)

        bui.buttonwidget(
            parent=mud_widget,
            size=(60, 20),
            label='Help',
            color=colb,
            textcolor=wht,
            scale=s.scale,
            position=(290, 30),
            on_activate_call=bs.Call(s.welp, 69123))

        bui.buttonwidget(
            parent=mud_widget,
            size=(80, 20),
            label='Random',
            textcolor=wht,
            scale=s.scale,
            color=colb,
            position=(150, 30),
            on_activate_call=bs.Call(s.gather2, True))

        # -> no = 23
        # -> cw = 595 (+26)
        # -> cb = 440 (+20)
        # -> tw = 435 (+19)
        cw = 757
        cb = 560
        tw = 553

        et = tw
        mud_sub = bui.containerwidget(parent=mud_scroll,
                                      background=False,
                                      size=(190, cw),
                                      color=(0.3, 0.3, 0.3),
                                      scale=s.scale)
        global ins2
        ins2 = []
        for i in range(len(attrs)):
            bui.textwidget(parent=mud_sub,
                           text=attrs[i],
                           scale=s.scale/2,
                           h_align='left',
                           v_align='center',
                           on_activate_call=bs.Call(
                               s.welp, i) if i not in not_editable else bs.Call(s.welp, i, nah=True),
                           selectable=True,
                           autoselect=True,
                           color=(1, 1, 1) if i not in not_editable else (0.6, 0.6, 0.6),
                           click_activate=True,
                           size=(180, 29),
                           position=(-30, tw - (20 * i)))
            a = val_attrs2[i]
            if isinstance(a, bool):
                l = bui.checkboxwidget(parent=mud_sub,
                                       value=a,
                                       text="",
                                       color=colb,
                                       scale=s.scale/2,
                                       on_value_change_call=bs.Call(
                                           s.check, i, mod=True) if i not in not_editable else bs.Call(s.welp, i, ignore=True),
                                       position=(180, cb - (20 * i)))
            elif isinstance(a, tuple) or i == 6 or i == 11 or i == 28:
                k = val_attrs2[i]
                l = bui.buttonwidget(parent=mud_sub,
                                     label=f"{str(a[0]+0.01)[:3]} {str(a[1]+0.01)
                                                                   [:3]}, {str(a[2]+0.01)[:3]}",
                                     scale=s.scale,
                                     size=(30, 12),
                                     color=k,
                                     textcolor=(1-k[0], 1-k[1], 1-k[2]),  # invert
                                     on_activate_call=bs.Call(NicePick2, s, a, i),
                                     position=(180, cb - (20 * i)))
            else:
                l = bui.textwidget(parent=mud_sub,
                                   text=str(a),
                                   scale=s.scale/2,
                                   h_align='left',
                                   v_align='center',
                                   editable=True,
                                   color=(1, 1, 1),
                                   size=(150, 25),
                                   position=(150, et - (20 * i)))
            ins2.append(l)

    def gather2(s, ran=False):
        global val_attrs2, nice2_view, mud_widget, drux
        for i in range(len(ins2)):
            if bui.Widget.get_widget_type(ins2[i]) == 'text':
                v = cast(str, bui.textwidget(query=ins2[i]))
                t = type_attrs[i]
                if t == 'float':
                    if ran:
                        v = random.uniform(0.0, 9.9)
                        bui.textwidget(edit=ins2[i], text=str(v)[:3])
                    else:
                        try:
                            v = float(v)
                        except ValueError:
                            error(
                                f"{attrs[i]}: Invalid value '{v}'\nRequired type: float, Given type: {type(v).__name__}\nExample of float: 3.141592 (decimal number)")
                            return
                elif t == 'int':
                    if ran:
                        v = random.randrange(0, 7)
                        bui.textwidget(edit=ins2[i], text=str(v))
                    else:
                        try:
                            v = int(v)
                        except ValueError:
                            error(
                                f"{attrs[i]}: Invalid value '{v}'\nRequired type: int, Given type: {type(v)}\nExample of int: 68 (number)")
                            return
                else:
                    # print (f"checking={v} v_in_bot_name={v in bot_name} not_i={not i} i={i}")
                    if not v in bot_name and i == 1:
                        if ran:
                            v = random.choice(bot_name)
                            s.spawn(bot_name.index(v))  # update preview
                            bui.textwidget(edit=ins2[i], text=str(v))
                        else:
                            error(f"character: Invalid character '{v}'")
                            if v in w_bot_name:
                                push(
                                    f"Did you mean '{bot_name[w_bot_name.index(v)]}'?", color=(0, 0.6, 1))
                            return
                    elif i == 1:
                        if ran:
                            v = random.choice(bot_name)
                        s.spawn(bot_name.index(v), True)  # update preview
                        bui.textwidget(edit=ins2[i], text=str(v))
                    elif not v in bomb_type and i == 8:
                        if ran:
                            v = random.choice(bomb_type)
                            bui.textwidget(edit=ins2[i], text=str(v))
                        else:
                            error(f"default_bomb_type: Invalid bomb type '{v}'")
                            if v in w_bomb_type:
                                push(
                                    f"Did you mean '{bomb_type[w_bomb_type.index(v)]}'?", color=(0, 0.6, 1))
                            return
                    elif v in bomb_type and ran and i == 8:
                        v = random.choice(bomb_type)
                        bui.textwidget(edit=ins2[i], text=str(v))
                val_attrs2[i] = v
            if bui.Widget.get_widget_type(ins2[i]) == 'checkbox' and ran:
                v = random.choice([True, False])
                bui.checkboxwidget(edit=ins2[i], value=v)
                val_attrs2[i] = v
            elif bui.Widget.get_widget_type(ins2[i]) == 'button' and ran:
                a = []
                for r in range(3):
                    a.append(random.uniform(0.0, 1.0))
                a = (float(a[0]), float(a[1]), float(a[2]))
                bui.buttonwidget(edit=ins2[i], label=f"{str(a[0]+0.01)[:3]} {str(a[1]+0.01)[:3]}, {str(a[2]+0.01)[:3]}", color=(
                    a[0], a[1], a[2]), textcolor=(1-a[0], 1-a[1], 1-a[2]))
                val_attrs2[i] = a
#                bui.buttonwidget(edit=nice2_view, tint_texture=bui.gettexture(val_attrs2[1]+'IconColorMask'))
                bui.buttonwidget(edit=nice2_view, tint_texture=bui.gettexture(
                    bot_texture[bot_name.index(val_attrs2[1])]+'IconColorMask'))
                bui.buttonwidget(
                    edit=nice2_view, tint_color=val2_attrs[6], tint2_color=val2_attrs[11])
        if not ran:
            s.kill(True, mud_widget, True)
        else:
            bui.getsound('cashRegister2').play()

    def cords2_window(s):
        global cords2_widget
        cords2_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                            size=(300, 250),
                                            color=cola,
                                            stack_offset=s.soff,
                                            transition=s.anim_in,
                                            scale=s.scale)
        bui.buttonwidget(parent=cords2_widget,
                         size=(200, 50),
                         label="Current Position",
                         textcolor=wht,
                         scale=s.scale,
                         color=colb,
                         position=(20, 125),
                         on_activate_call=bs.Call(s.use_my_pos, True))

        bui.textwidget(parent=cords2_widget,
                       color=(0.1, 0.7, 1),
                       text='Teleport to:',
                       scale=s.scale,
                       h_align='center',
                       v_align='center',
                       position=(125, 200))

        bui.buttonwidget(parent=cords2_widget,
                         size=(200, 50),
                         label="Custom Position",
                         scale=s.scale,
                         color=colb,
                         textcolor=wht,
                         position=(20, 60),
                         on_activate_call=bs.Call(s.custom2_window))

        bacc = bui.buttonwidget(
            parent=cords2_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, cords2_widget, True))
        bui.containerwidget(edit=cords2_widget, cancel_button=bacc)

    def custom2_window(s):
        s.kill(True, cords2_widget, True)
        global cords2
        try:
            txt = str(cords2[0]) if cords2[0] != 69123 else "0"
        except TypeError:
            cords2 = (0, 0, 0)
            txt = "0"
        custom2_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                             size=(300, 250),
                                             color=cola,
                                             stack_offset=s.soff,
                                             transition=s.anim_in,
                                             scale=s.scale)
        bui.textwidget(parent=custom2_widget,
                       color=(0.1, 0.7, 1),
                       text='Custom Position',
                       scale=s.scale,
                       h_align='center',
                       v_align='center',
                       position=(125, 200))

        x = bui.textwidget(
            parent=custom2_widget,
            text=txt,
            editable=True,
            size=(200, 25),
            h_align='center',
            v_align='center',
            position=(55, 150))
        y = bui.textwidget(
            parent=custom2_widget,
            size=(200, 25),
            text=str(cords2[1]),
            editable=True,
            h_align='center',
            v_align='center',
            position=(55, 120))
        z = bui.textwidget(
            parent=custom2_widget,
            size=(200, 25),
            text=str(cords2[2]),
            editable=True,
            h_align='center',
            v_align='center',
            position=(55, 90))

        def collect(s):
            global cords2
            w = x
            a = []
            for i in range(3):
                try:
                    a.append(float(cast(str, bui.textwidget(query=w))))
                except:
                    error("Invalid "+("Z" if w == z else "Y" if w == y else "X")+" Cordinate!")
                    return
                w = z if i else y
            s.kill(True, custom2_widget, True)
            bui.getsound('gunCocking').play()
            cords2 = tuple(a)
            s.update_cords_view(True)

        def back(s):
            s.kill(True, custom2_widget, True)
            s.cords2_window(Nice)

        bui.buttonwidget(
            parent=custom2_widget,
            size=(60, 20),
            label='Set',
            color=colb,
            textcolor=wht,
            scale=s.scale,
            position=(190, 30),
            on_activate_call=bs.Call(collect, s))

        bacc = bui.buttonwidget(
            parent=custom2_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            textcolor=wht,
            color=colb,
            position=(30, 30),
            on_activate_call=bs.Call(back, s))
        bui.containerwidget(edit=custom2_widget, cancel_button=bacc)

    def apply_mods(s):
        global drux, lmao, lmao_bots, val_arr, indox2, val_attts2, cords2, do_tp
        global LAH, LAP, LAB, LAF, testa
        s.kill(True, mid_widget, True)
        new = val_attrs2
        bot = lmao_bots[dux]
        if cords2[0] != 69123 and do_tp:
            bot.node.handlemessage(bs.StandMessage(cords2, 0))
        nice_custom_color = (0.7, 0.7, 0.7)
        bot.bouncy = new[0]
        # skipped character
        bot.charge_dist_max = new[2]
        bot.charge_dist_min = new[3]
        charge_speed_max = new[4]
        charge_speed_min = new[5]
        bot.node.color = new[6]
        bot.set_bomb_count(new[7])
        bot.bomb_type = new[8]
        bot.bomb_type_default = new[8]
        bot.default_boxing_gloves = new[9]
        bot.default_shields = new[10]
        bot.node.highlight = new[11]
        bot.punchiness = new[12]
        bot.run = new[13]
        bot.run_dist_min = new[14]
        bot.demo_mode = new[15]
        bot.static = new[16]
        bot.throw_dist_max = new[17]
        bot.throw_dist_min = new[18]
        bot.throw_rate = new[19]
        bot.throwiness = new[20]
        bot.start_invincible = new[22]
        LAH[dux] = new[23]
        LAP[dux] = new[24]
        LAB[dux] = new[25]
        LAF[dux] = new[26]
        if new[27] == '%':
            testa[dux].text = new[1]
        elif new[27] == '$':
            testa[dux].text = lmao[drux]
        else:
            testa[dux].text = new[27]
        testa[dux].color = new[28]
        t = bot_texture[bot_name.index(bot.character)]
        s.set_char(bot, bot_style[indox2])
        ding(f'Modified {lmao[drux]}!')
        if not on_control:
            s.hl4(bot)
        val_arr[dux] = val_attrs2.copy()  # apply temp to the stored ones

    def set_char(s, bot, char):
        global lmao_bots, lmao_chars, val_arr
        i = lmao_bots.index(bot)
        name = bot_name[bot_style.index(char)]
        lmao_chars[i] = name
        val_arr[i][1] = name
        b = bot.node
        c = bot_texture[bot_style.index(char)]
        with ga().context:
            try:
                pelvis = bs.getmesh(c+'Pelvis')
            except RuntimeError:
                pelvis = bs.getmesh('kronkPelvis')
            head = bs.getmesh(c+'Head')
            torso = bs.getmesh(c+'Torso')
            toes = bs.getmesh(c+'Toes')
            uarm = bs.getmesh(c+'UpperArm')
            uleg = bs.getmesh(c+'UpperLeg')
            farm = bs.getmesh(c+'ForeArm')
            lleg = bs.getmesh(c+'LowerLeg')
            hand = bs.getmesh(c+'Hand')
            b.head_mesh = head
            b.pelvis_mesh = pelvis
            b.torso_mesh = torso
            b.toes_mesh = toes
            b.upper_arm_mesh = uarm
            b.upper_leg_mesh = uleg
            b.forearm_mesh = farm
            b.lower_leg_mesh = lleg
            b.hand_mesh = hand
            b.style = 'spaz' if char in has_no_style else char
            b.color_mask_texture = bs.gettexture(c+'ColorMask')
            b.color_texture = bs.gettexture(c if c in has_no_color else c+'Color')
        s.preview(i, (bot.node.hurt < 1), 1)

    def listen_window(s):
        global listen_widget, music_preview_image, music_preview_text, music_preview_text2, music_dux
        music_dux = 8
        listen_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                            size=(500, 300),
                                            stack_offset=s.soff,
                                            color=cola,
                                            transition=s.anim_in,
                                            scale=s.scale)

        music_preview_image = bui.buttonwidget(parent=listen_widget,
                                               label='',
                                               size=(50, 50),
                                               position=(300, 175),
                                               button_type='square',
                                               color=colb,
                                               mask_texture=bui.gettexture('characterIconMask'))

        music_preview_text = bui.textwidget(parent=listen_widget,
                                            text='',
                                            size=(50, 50),
                                            scale=s.scale/1.4,
                                            maxwidth=115,
                                            position=(365, 175))

        music_preview_text2 = bui.textwidget(parent=listen_widget,
                                             text='',
                                             size=(50, 50),
                                             scale=s.scale/1.7,
                                             maxwidth=115,
                                             position=(360, 155))

        bui.textwidget(parent=listen_widget,
                       color=(0.1, 0.7, 1),
                       text='Listen',
                       position=(200, 250),
                       maxwidth=150)

        bui.buttonwidget(
            parent=listen_widget,
            size=(70, 30),
            label='Listen',
            button_type='square',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(370, 30),
            on_activate_call=bs.Call(s.play_music))

        bui.buttonwidget(
            parent=listen_widget,
            size=(70, 30),
            label='Def',
            button_type='square',
            scale=s.scale,
            icon=bui.gettexture("replayIcon"),
            iconscale=s.scale/2.5,
            color=colb,
            textcolor=wht,
            position=(270, 30),
            on_activate_call=bs.Call(s.play_music, True))

        listen_scroll = bui.scrollwidget(parent=listen_widget,
                                         position=(30, 80),
                                         claims_up_down=False,
                                         claims_left_right=True,
                                         autoselect=True,
                                         size=(250, 150))

        listen_sub = bui.containerwidget(parent=listen_scroll,
                                         background=False,
                                         size=(190, len(music_name)*26),
                                         color=(0.3, 0.3, 0.3),
                                         scale=s.scale)

        bacc = bui.buttonwidget(
            parent=listen_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, listen_widget))
        bui.containerwidget(edit=listen_widget, cancel_button=bacc)

        bui.buttonwidget(edit=music_preview_image, texture=None, color=(1, 1, 1))
        bui.textwidget(edit=music_preview_text, text=music_name[music_dux])
        bui.textwidget(edit=music_preview_text2, text=music_desc[music_dux])
        bui.buttonwidget(edit=music_preview_image, texture=bui.gettexture(music_texture[music_dux]))

        # selected index is music_dux
        for i in range(len(music_name)):
            bui.textwidget(parent=listen_sub,
                           scale=s.scale/2,
                           text=(music_name[i]),
                           h_align='left',
                           v_align='center',
                           color=(1, 1, 1),
                           on_activate_call=bs.Call(s.preview_music, i),
                           selectable=True,
                           autoselect=True,
                           click_activate=True,
                           size=(180, 29),
                           position=(-30, (20 * i)))

    def preview_music(s, i):
        global music_preview_image, music_dux, music_preview_text, music_preview_text2
        global music_widget
        music_dux = i
        bui.textwidget(edit=music_preview_text, text=music_name[i], color=(1, 1, 1))
        bui.textwidget(edit=music_preview_text2, text=music_desc[i], color=(1, 1, 1))
        bui.buttonwidget(edit=music_preview_image, texture=bui.gettexture(music_texture[i]))

    def play_music(s, default=False):
        global music_dux
        try:
            with ga().context:
                bs.setmusic(music_type[music_dux] if not default else ga().default_music)
        except AttributeError:
            if not default:
                bs.set_internal_music(ba.getsimplesound(music_desc[music_dux][:-4]))
                push("You are not the host,\nsound will only play for you\nand it might be lower than usual\nturn sound volume down and music volume up", color=(1, 0, 1))
        if default:
            try:
                push(
                    f"Now playing default music: {music_name[music_type.index(ga().default_music)]}")
            except AttributeError:
                push("Unable to get default music\nsince you are not the host\nit resets next game tho", (1, 1, 0))

    def effect_window(s):
        if ga() is None:
            push('Effect who and how? you are not the host!', color=(1, 1, 0))
            return
        global effect_widget, lmao, lmao_bots, old_ga, preview_image, preview_text, dux, preview_text2, dux2, preview_text3, effect_dux, effect_ones, effect_tab, effect_sub, effect_bots
        effect_bots = True
        effect_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                            size=(500, 290),
                                            stack_offset=s.soff,
                                            color=cola,
                                            transition=s.anim_in,
                                            scale=s.scale)

        try:
            p1 = lmao[effect_dux]
            p2 = lmao_bots[effect_dux].character
            lol = bui.gettexture(bot_texture[bot_name.index(p2)]+"Icon")
        except IndexError:
            p1 = 'Name'
            p2 = 'Character'
            lol = None
        preview_image = bui.buttonwidget(parent=effect_widget,
                                         label='',
                                         size=(50, 50),
                                         position=(300, 175),
                                         button_type='square',
                                         color=(1, 1, 1),
                                         texture=lol,
                                         mask_texture=bui.gettexture('characterIconMask'),
                                         on_activate_call=bs.Call(push, 'what are you trying to achieve'))

        preview_text = bui.textwidget(parent=effect_widget,
                                      text=p1,
                                      size=(50, 50),
                                      scale=s.scale/1.3,
                                      position=(365, 175))

        preview_text2 = bui.textwidget(parent=effect_widget,
                                       text=p2,
                                       size=(50, 50),
                                       scale=s.scale/1.7,
                                       position=(360, 155))

        # '{100 * (1 - lmao_bots[0].node.hurt)}%'
        preview_text3 = bui.textwidget(parent=effect_widget,
                                       text='',
                                       size=(50, 50),
                                       scale=s.scale/1.7,
                                       position=(295, 125))

        bui.textwidget(parent=effect_widget,
                       text='Select who,\nthen press effect',
                       size=(50, 50),
                       scale=s.scale/1.7,
                       position=(295, 85))

        bui.textwidget(parent=effect_widget,
                       color=(0.1, 0.7, 1),
                       text='Effect',
                       position=(300, 240),
                       maxwidth=250)

        bui.buttonwidget(
            parent=effect_widget,
            size=(70, 30),
            label='Effect',
            button_type='square',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(360, 30),
            on_activate_call=bs.Call(s.do_effect))

        effect_scroll = bui.scrollwidget(parent=effect_widget,
                                         position=(30, 80),
                                         claims_up_down=False,
                                         claims_left_right=True,
                                         autoselect=True,
                                         size=(250, 150))
        tabdefs = [('bots', 'Bots'), ('players', "Players")]

        effect_tab = TabRow(
            effect_widget,
            tabdefs,
            pos=(30, 230),
            size=(250, 0),
            on_select_call=s.switch_tab)

        effect_tab.update_appearance('bots')
        effect_sub = bui.containerwidget(parent=effect_scroll,
                                         background=False,
                                         color=(0.3, 0.3, 0.3),
                                         scale=s.scale)
        bacc = bui.buttonwidget(
            parent=effect_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, effect_widget))
        bui.containerwidget(edit=effect_widget, cancel_button=bacc)

        s.cola_fill(effect_widget)

        if len(lmao) == 0 or str(ga()) != old_ga:
            s.inform('No bots', effect_sub)
        else:
            try:
                a = effect_dux
            except NameError:
                a = 0
            effect_ones = s.load(lmao, lmao_bots, effect_widget, effect_sub, a)

    def switch_tab(s, id):
        global effect_tab, effect_sub, effect_widget, preview_image, effect_dux, lmao_players, lmao, lmao_bots, lmao2, lmao_chars2, effect_bots
        effect_tab.update_appearance(id)
        for w in effect_sub.get_children():
            w.delete()
        if id == "bots":
            effect_bots = True
            try:
                a = effect_dux
            except NameError:
                a = 0
            s.load(lmao, lmao_bots, effect_widget, effect_sub, a)
        else:
            effect_bots = False
            s.select_all_bots = False
            lmao_players = ga().players
            lmao2 = []
            lmao_chars2 = []
            for i in lmao_players:
                lmao2.append(i.getname())
                lmao_chars2.append(i.character)
            s.load(lmao2, lmao_players, effect_widget, effect_sub, 0, 3)
        s.cola_fill(effect_widget)

    def load(s, arr, arr2, container, sub, dux=0, mod=2):
        global lmao_bots, lmao_players, preview_image
        bui.containerwidget(edit=sub, size=(190, ((1 if mod == 2 else 0)+len(arr))*26))
        if len(arr) == 0 or str(ga()) != old_ga and mod == 2:
            s.inform('Still\nNo bots', effect_sub)
            return
        ones = []
        for i in range(len(arr)):
            try:
                alive = (arr2[i].node.hurt <
                         1) if arr2[i] in lmao_bots else arr2[i].actor.node.hurt < 1
            except IndexError:
                s.kill(True, widget)
                push('Something is still spawining, try again')
                return
            except AttributeError:
                alive = False
            da_one = bui.textwidget(parent=sub,
                                    scale=s.scale/2,
                                    text=(arr[i] if alive else f"{arr[i]} (dead)"),
                                    h_align='left',
                                    v_align='center',
                                    color=((1, 1, 1) if alive else (0.6, 0.6, 0.6)),
                                    on_activate_call=bs.Call(s.preview, i, alive, mod),
                                    selectable=True,
                                    autoselect=True,
                                    click_activate=True,
                                    size=(180, 29),
                                    position=(-30, (20 * i)))
            ones.append(da_one)
        if mod == 2:
            s.select_all = bui.checkboxwidget(parent=sub,
                                              scale=s.scale/2,
                                              size=(200, 5),
                                              text="Select all",
                                              color=cola,
                                              value=False,
                                              textcolor=wht,
                                              on_value_change_call=s.effect_all_bots,
                                              position=(0, 10+(20 * (len(arr)))))
        try:
            ones[dux].activate()
        except NameError:
            pass
        return ones

    def effect_all_bots(s, b):
        if b:
            s.preview(69123, True)
            s.reset_bright_bots()
        s.select_all_bots = b

    def inform(s, what, where):
        global nukeme
        try:
            nukeme.delete()
        except NameError:
            pass
        for i in where.get_children():
            i.delete()
        nukeme = bui.textwidget(parent=where,
                                text=what,
                                h_align='center',
                                v_align='center',
                                size=(60, 29),
                                position=(60, -62))

    def do_effect(s):
        global effect_dux, lmao_bots, lmao, effect_bots, lmao2, lmao_players, eff_widget, indox2, nice2_name, nice2_view, cords2_view, dux, max_digits, val_attrs2, val_arr, drux, cords2, dp_tp, effect_indox, effect_tip, effect_dux2
        # validate button press
        if not s.select_all_bots:
            _lmao = lmao if effect_bots else lmao2
            _lmao_bots = lmao_bots if effect_bots else lmao_players
            _effect_dux = effect_dux if effect_bots else effect_dux2
            try:
                name = _lmao[_effect_dux]
            except NameError:
                error('Select a bot first' if len(_lmao_bots)
                      else 'When it says no bots\nyet u still click the button??')
                return
            except IndexError:
                pass
            try:
                hurt = _lmao_bots[_effect_dux].node.hurt if effect_bots else _lmao_bots[_effect_dux].actor.node.hurt
                if hurt == 1:
                    error(f'{_lmao[_effect_dux]} is dead.')
                    return
            except:
                try:
                    error(f'{_lmao[_effect_dux]} is dead.')
                    return
                except IndexError:
                    error("No bots")
                    return
        else:
            _lmao = lmao
            _lmao_bots = lmao_bots
            _effect_dux = 69123
            name = "All bots"
        try:
            a = effect_indox
        except NameError:
            effect_indox = 0
        eff_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                         size=(500, 300),
                                         stack_offset=s.soff,
                                         color=cola,
                                         transition=s.anim_in,
                                         scale=s.scale)

        bui.textwidget(parent=eff_widget,
                       color=(0.1, 0.7, 1),
                       text=f'Effect {name}',
                       position=(165, 250),
                       maxwidth=250)

        effect_tip = bui.textwidget(parent=eff_widget,
                                    text=effect_tips[effect_indox],
                                    position=(175, 190),
                                    scale=s.scale/2,
                                    maxwidth=250)

        nice2_view = bui.buttonwidget(parent=eff_widget,
                                      label='',
                                      size=(100, 100),
                                      position=(60, 120),
                                      button_type='square',
                                      color=(1, 1, 1),
                                      texture=bui.gettexture(effect_texture[effect_indox]),
                                      mask_texture=bui.gettexture('characterIconMask'),
                                      on_activate_call=bs.Call(Picker, 2))

        # Apply bot's stuff to mod preset (clean up)
        if not s.select_all_bots:
            good_name = effect_name[_effect_dux]
            if effect_bots:
                va = val_arr[_effect_dux]
            bui.buttonwidget(edit=nice2_view, tint_texture=bui.gettexture(
                effect_texture[_effect_dux]))

        nice2_name = bui.textwidget(parent=eff_widget,
                                    text=effect_name[effect_indox],
                                    h_align='center',
                                    v_align='center',
                                    position=(85, 85))

        bacc = bui.buttonwidget(
            parent=eff_widget,
            size=(60, 20),
            label='Back',
            textcolor=wht,
            scale=s.scale,
            color=colb,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, eff_widget, True))
        bui.containerwidget(edit=eff_widget, cancel_button=bacc)

        bui. buttonwidget(
            parent=eff_widget,
            size=(100, 40),
            label='Apply',
            color=colb,
            scale=s.scale,
            textcolor=wht,
            position=(350, 30),
            on_activate_call=s.apply_effects)

        if s.select_all_bots:
            return
        if effect_bots:
            val_attrs2 = val_arr[_effect_dux].copy()  # reset to default temp
        indox2 = effect_name.index(good_name)

    def apply_effects(s):
        global eff_widget, effect_indox, effect_dux, lmao_bots, lmao, effect_bots, effect_dux
        s.kill(True, eff_widget, True)
        n = effect_indox
        i = effect_dux if effect_bots else effect_dux2
        a = effect_name[n]
        if not s.select_all_bots:
            bots = [lmao_bots[i]] if effect_bots else [lmao_players[i].actor]
            name = lmao[i] if effect_bots else lmao2[i]
        else:
            bots = lmao_bots
            name = "All Bots"
        try:
            em = effect_message[n]
        except IndexError:
            em = None
        with ga().context:
            for bot in bots:
                if em:
                    bot.handlemessage(bs.PowerupMessage(em))
                elif a == 'Shatter':
                    bot.shatter(True)
                elif a == 'Freeze':
                    bot.handlemessage(bs.FreezeMessage())
                elif a == 'Unfreeze':
                    bot.handlemessage(bs.ThawMessage())
                elif a == 'Celebrate':
                    bot.handlemessage(bs.CelebrateMessage())
                elif a == 'Stop Celebrating':
                    bot.handlemessage(bs.CelebrateMessage(duration=0.0001))
                elif a == 'Kill':
                    try:
                        bot.handlemessage(bs.DieMessage())
                    except:
                        pass  # bot is dead or so
                elif a == 'Infinite Curse':
                    if bot._cursed:
                        bot.handlemessage(bs.PowerupMessage('health'))
                    bot.curse()
                    s.spam_curse(bot)
                elif a == 'Super Speed':
                    bot.node.hockey = True
                elif a == 'Normal Speed':
                    bot.node.hockey = False
                elif a == 'Invincible':
                    bot.node.invincible = True
                elif a == 'Beatable':
                    bot.node.invincible = False
                elif a == 'Sleep':
                    bot._knocked = True
                    s.spam_knock(bot)
                elif a == 'Wake Up':
                    bot._knocked = False
                elif a == 'Super Punch':
                    s.give_sp(bot)
                elif a == 'Normal Punch':
                    bot._punch_power_scale = 1.2
                    bot._punch_cooldown = 400
                elif a == 'Fly Jumps':
                    if effect_bots:
                        bot.on_jump_press = s.spaz_bot_fly(bot.on_jump_press)
                    else:
                        lmao_players[i].assigninput(
                            ba.InputType.JUMP_PRESS, bs.Call(s.spaz_fly, bot))
                elif a == 'Normal Jumps':
                    bot.on_jump_press = s.spaz_not_fly
                elif a == 'GodMode Preset':
                    bot.node.hockey = True  # Speed
                    bot._super = True
                    bot.node.invincible = True  # Invincibility
                    s.give_sp(bot)  # Super Punch
                    PopupText("I HAVE THE POWER", position=bot.node.position,
                              random_offset=1).autoretain()
                elif a == "Reset All":
                    push(f'Resetted all effects from {name}')
                    bui.getsound('shieldDown').play()
                    bot.on_jump_press = s.spaz_not_fly
                    bot._cursed = False
                    bot._super = False
                    bot.node.hockey = False
                    bot.node.invincible = False
                    bot._knocked = False
                    bot._punch_power_scale = 1.2
                    bot._punch_cooldown = 400
                    return
            ding(f"Applied '{a}' to {name}")

    def link_text(s, text, bot, color=(1, 1, 1), off=1.5):
        with ga().context:
            try:
                m = bs.newnode('math',
                               owner=bot.node,
                               attrs={'input1': (0, off, 0),
                                      'operation': 'add'})
                bot.node.connectattr('position', m, 'input2')
                test = bs.newnode(
                    'text',
                    owner=bot.node,
                    attrs={'text': text,
                           'in_world': True,
                           'shadow': 1.0,
                           'flatness': 1.0,
                           'color': color,
                           'scale': 0.0,
                           'h_align': 'center'})
                m.connectattr('output', test, 'position')
                bs.animate(test, 'scale', {0: 0.0, 0.5: 0.01})
                return test
            except:
                pass

    def nodetimer(s, time, node):
        with ga().context:
            bs.timer(time, node.delete)

    """Constant Jump - spam jump on bot, combine w fly jumps"""
    def constant_jump(s, bot):
        if not bot.exists():
            return
        p = bot.node.position
        p2 = (p[0], p[1]-0.2, p[2])
        bot.on_jump_press(bot)
        if random.choice([False, False, False, True]):
            PopupText("Hoppie", position=p2, random_offset=0.3, color=(1, 0, 1)).autoretain()
        bs.timer((random.choice([0.1, 0.4, 0.7, 0.1]) if p2[1] <
                 4 else 1.5), bs.Call(s.constant_jump, s, bot))

    """toxic celebrate - when a player dies,
       celebrate the hunt, called from outside Nice."""
    def toxic_celebrate(s):
        for b in Nice.toxic_bots:
            try:
                p = b.node.position
            except:
                return  # bot is dead
            p2 = (p[0], p[1]-0.2, p[2])
#            PopupText(random.choice(toxic_win),position=p2,random_offset=0.3,color=(0,1,1)).autoretain()
            n = s.link_text(s, text=random.choice(toxic_win), bot=b, color=(1, 0, 1), off=2)
            s.nodetimer(s, 1.5, n)

    """Constant Heal - heal bot from time to time"""
    def constant_heal(s, bot):
        with ga().context:
            if not bot.exists():
                return
            p = bot.node.position
            p2 = (p[0], p[1]-0.2, p[2])
            bot.handlemessage(bs.PowerupMessage('health'))
            PopupText("Healed", position=p2, random_offset=0.3, color=(0, 1, 0)).autoretain()
            bs.timer(4, bs.Call(s.constant_heal, s, bot))

    """Make Toxic - makes a bot say toxic stuff.
       only called from outside Nice"""
    def make_toxic(s, bot):
        with ga().context:
            if not bot.exists():
                return
            p = bot.node.position
            if bot.node.hurt > 0.5:
                bot.handlemessage(bs.PowerupMessage('shield'))
            p2 = (p[0], p[1]-0.2, p[2])
#            PopupText(random.choice(toxic),position=p2,random_offset=0.3,color=(1,0,0)).autoretain()
            n = s.link_text(s, text=random.choice(toxic), bot=bot, color=(1, 0, 0))
            s.nodetimer(s, 1.5, n)
            bs.timer(2, bs.Call(s.make_toxic, s, bot))

    def phew(s, pos):
        PopupText("Damage ignored", position=pos, random_offset=0.3).autoretain()

    def give_sp(s, bot): bot._punch_cooldown = 0; bot._punch_power_scale = 15; bot._super = True

    def spam_knock(s, bot):
        with ga().context:
            if not bot.exists() or not bot._knocked:
                return
            bot.node.handlemessage('knockout', 1000)
            p = bot.node.position
            p2 = (p[0], p[1]-0.2, p[2])
            PopupText("z", position=p2, random_offset=0.3).autoretain()
            bs.timer(0.9, bs.Call(s.spam_knock, bot))

    def spam_curse(s, bot):
        with ga().context:
            if not bot.exists() or not bot._cursed:
                return
            bot.handlemessage(bs.PowerupMessage('health'))
            p2 = bot.node.position
            p2 = (p2[0]+0.7, p2[1]-0.3, p2[2])
            PopupText(random.choice(nah_uh), position=p2, random_offset=0.3).autoretain()
            bot.curse()
            def adapter(): Nice.spam_curse(Nice, bot)
            bs.timer(4.5, adapter)

    def update_alive_bots(s):
        global lmao, alive_bots, alive_arr, lmao_bots, currently_dux
        global on_control, move_on
        alive_bots = []
        alive_arr = []
        for p in range(len(lmao)):
            try:
                if lmao_bots[p].node.hurt < 1:
                    alive_bots.append(lmao_bots[p])
                    alive_arr.append(lmao[p])
            except AttributeError:
                continue  # vanished

    # fly override
    def spaz_bot_fly(s, self):
        def wrapper(b):
            is_moving = abs(b.node.move_up_down) >= 0.01 or abs(b.node.move_left_right) >= 0.01
            if not b.node.exists():
                return
            t = ba.apptime()
            b.last_jump_time_ms = -9999
            if t - b.last_jump_time_ms >= b._jump_cooldown:
                b.node.jump_pressed = True
                if b.node.jump_pressed:
                    v = b.node.velocity
                    v1 = v[0]
                    v2 = v[1]
                    v3 = v[2]
                    p = b.node.position
                    p1 = p[0]
                    p2 = p[1]
                    p3 = p[2]
                    r = b.node.run
                    b.node.handlemessage("impulse", p1, 0.0+p2, p3, v1, v2,
                                         v3, 0*r, 0*r, 0, 0, v1, v2, v3)
                    b.node.handlemessage("impulse", p1, 3.6+p2, p3, v1, v2,
                                         v3, 0*r, 0*r, 0, 0, v1, v2, v3)
                    b.node.handlemessage('impulse', p1, p2+0.001, p3, 0,
                                         0.2, 0, 200, 200, 0, 0, 0, 5, 0)
                b.last_jump_time_ms = t
            b._turbo_filter_add_press('jump')
        return wrapper

    def spaz_fly(s, _bot):
        if not _bot.node.exists():
            return
        _bot.node.handlemessage(
            'impulse', _bot.node.position[0], _bot.node.position[1], _bot.node.position[2],
            0.0, 0.0, 0.0, 200.0, 200.0, 0.0, 0.0, 0.0, 1.0, 0.0)

    def cola_fill(s, widget, exclude=[]):
        if hasattr(widget, 'exists') and widget.exists():
            for child in widget.get_children():
                if child.get_widget_type() == 'button' and child not in exclude:
                    bui.buttonwidget(edit=child, color=cola)

    def bombdown(s, b=1):
        global bomb_down
        if b:
            bomb_down = True
            with ga().context:
                bs.timer(0.1, bs.Call(s.bombdown, 0))
        else:
            bomb_down = False

    def key(s, i):
        global lmao_bots, move_on, currently_dux, bomb_control, lmao, currently_txt
        global alive_bots, alive_arr, bomb_down
        try:
            bot = lmao_bots[currently_dux]
        except IndexError:
            push(f"no {currently_dux}")
        with ga().context:
            if i > 2:
                if bomb_control and not bomb_down:
                    s.bombdown()
                    if len(alive_bots) == 1:
                        return  # blud only has 1 bot
                    currently_dux += 1
                    if currently_dux == len(lmao):
                        currently_dux = 0
                    for a in range(len(lmao_bots)):
                        try:
                            if lmao_bots[currently_dux].node.hurt == 1:
                                currently_dux += 1  # dead
                        except AttributeError:
                            currently_dux += 1  # vanished
                    if currently_dux == len(lmao) + 1:
                        currently_dux = 0
                    push(f'Switched control to {lmao[currently_dux]}', color=(0, 1, 1))
                    currently_txt = f"Now controlling\n{lmao[currently_dux]}"
                    s.draw(currently_txt)
                    bui.getsound('gunCocking').play()
                    s.hl2(lmao_bots[currently_dux].node, True)
                    return
                elif bomb_down:
                    push('too fast')
                    return
                bot.on_bomb_press()
                bot.on_bomb_release()
            elif i > 1:
                try:
                    bot.on_jump_press()
                except TypeError:
                    bot.on_jump_press(bot)
                bot.on_jump_release()
            elif i:
                bot.on_punch_press()
                bot.on_punch_release()
            else:
                bot.on_pickup_press()
                bot.on_pickup_release()

    def set_x(s, x): s.thex = x

    def set_y(s, y): s.they = y

    def pls_move(s):
        global lmao_bots, move_on, currently_dux, move_x
        global alive_bots
        if s.thex and s.they:
            try:
                b = lmao_bots[currently_dux]
            except IndexError:
                return  # control was stopped
            except TypeError:
                return  # bot died lmao
            b.on_move_left_right(s.they)
            b.on_move_up_down(s.thex)
            try:
                p = b.node.position
            except:
                #                error("an error occured, falling back and stopping control\nthis is a failsafe.")
                on_control = False
                allow_assign = True
                s.assign()
                return
            if not Nice.lite_mode and Nice.animate_camera:
                try:
                    _ba.set_camera_target(p[0], p[1], p[2])
                except UnboundLocalError:
                    s.draw()
        bs.apptimer(0.01, s.pls_move)

    # s.welp bro lmao
    def welp(s, w, nah=False, ignore=None):
        if ignore:
            nah = ignore
        global attrs
        title = 'Help' if w == 69123 else attrs[w] if w > 0 else node_attrs[-w]
        desc = 'Tap on an attribute to view detailed help about it.\nI wrote this help myself by trying each,\nmay not be 100% accurate tho' if w == 69123 else welps[
            w] if w > 0 else node_welps[-w]
        welp_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                          size=(400, 200 if title not in [
                                                'custom_name', 'gravity_scale'] else 230),
                                          color=cola,
                                          stack_offset=s.soff,
                                          transition=s.anim_in,
                                          scale=s.scale)

        bui.textwidget(parent=welp_widget,
                       color=(0.1, 0.7, 1),
                       text=title,
                       scale=s.scale,
                       h_align='center',
                       v_align='center',
                       position=(170, 150 if title not in ['custom_name', 'gravity_scale'] else 180))

        bui.textwidget(parent=welp_widget,
                       text=desc if not nah else "Attribute is only editable at first spawn,\nyou can remake the bot in that case." +
                       ("\nThis change will be ignored." if ignore else ""),
                       scale=s.scale/2,
                       h_align='center',
                       v_align='center',
                       position=(180, 100))

        bacc = bui.buttonwidget(
            parent=welp_widget,
            size=(60, 20),
            label='Back',
            scale=s.scale,
            color=colb,
            textcolor=wht,
            position=(30, 30),
            on_activate_call=bs.Call(s.kill, True, welp_widget, True))
        bui.containerwidget(edit=welp_widget, cancel_button=bacc)

    # checkbox manager
    def check(s, n, v, mod=False):
        global val_attrs2
        if mod:
            val_attrs2[n] = v
        else:
            Nice.val_attrs[n] = v

    def tick(s, n, v):
        if not n:
            s.auto_spawn_on_random = v
        elif n == 1:
            s.random_peace = v

    # sync selection with attrs
    def spawn(s, i, mod=False):
        global nice_name, nice_view, val_attrs2, nice2_view, nice2_name, indox2, effect_indox, effect_tip
        if mod == 1:
            indox2 = i
        elif mod == 2 or mod == 3:
            effect_indox = i
            bui.textwidget(edit=effect_tip, text=effect_tips[i], scale=0.6)
        elif mod == 69:
            Nice.drop_indox = i
        else:
            Nice.indox = i
        nv = nice_view if not mod else nice2_view if mod != 69 else Nice.drop_view
        va = Nice.val_attrs if not mod else val_attrs2 if mod != 69 else None
        nn = nice_name if not mod else nice2_name if mod != 69 else Nice.drop_name
        try:
            bui.textwidget(edit=nn, text=bot_name[i] if mod not in [
                           2, 3, 69] else effect_name[i] if mod != 69 else drop_name[i])
        except:
            s.spawn(i, 0)
        bui.buttonwidget(edit=nv, texture=bui.gettexture(
            (bot_texture[i]+'Icon') if mod not in [2, 3, 69] else effect_texture[i] if mod != 69 else drop_texture[i]))
        if mod not in [2, 3, 69]:
            bui.buttonwidget(edit=nv, tint_texture=bui.gettexture(bot_texture[i]+'IconColorMask'))
            bui.buttonwidget(edit=nv, tint_color=va[6], tint2_color=va[11])
            va[1] = bot_name[i]

    def on_ga_change(s):
        global old_ga, virgin, lmao, lmao_bots, lmao_players, lmao_bots2, testa
        global LAH, LAP, LAB, LAF, lmao_chars, move_on, on_control, nood
        old_ga = str(ga())
        virgin = True
        print(f"Sandbox.ByBordd: Hewoo! Spawn context is now '{old_ga}'")
        Nice.lmao_teams = []
        Nice.next_team_id = 2
        s.team_to_nuke = None
        lmao = []
        nood = []
        lmao_bots = []
        lmao_players = []
        lmao_bots2 = []
        testa = []
        LAH = []
        LAP = []
        LAB = []
        LAF = []
        lmao_chars = []
        move_on = 0
        on_control = False

    # actual spawn
    def do_spawn(s):
        global cords, prev_idk, bruh, attrs, lmao, old_ga, lmao_bots, indox2
        global move_on, lmao_chars, on_control, busy
        if busy:
            if Nice.pause_when_bots:
                push('Already spawned a bot\nResume first to spawn another\nOr Turn off pause from Config', color=(
                    1, 1, 0))
            else:
                push('too fast', color=(1, 1, 0))
            return

        idk = ga()
        if str(idk) != old_ga:
            on_ga_change()
        with idk.context:
            if cords is None or cords[0] == 69123:
                error("Set a spawn position first")
                return
            busy = True
            for k in ga().players:
                if k.sessionplayer.inputdevice.client_id == -1:
                    p = k
                    lmao.append(random.choice(random_bot_names).replace(
                        '#', str(len(lmao))))  # NO_BOT)
                    CustomBot.set_up(attrs, Nice.val_attrs)
            try:
                p.customdata[lmao[-1]] = CustomBotSet(p)
                p.customdata[lmao[-1]].do_custom()
            except NameError:
                error("You need to be in game to spawn bots")
                busy = False

    # know where the hell are cords
    def show_in_game(s, mode=0, mod=False):
        global cords, lmao_bots, move_on, cords2
        if mod is True:
            co = cords2
        elif mod is False:
            co = cords
        else:
            co = Nice.drop_cords
        if co[0] == 69123:
            error("Set a position first")
            return
        with ga().context:
            if mode:
                me = s.get_my_pos()
                if s.are_close(me, co, 1) == 1:
                    error("Join the goddamn game first")
                    return
                elif s.are_close(me, co, 2) == 2:
                    error("It's right where you're standing dum")
                    return
                elif s.are_close(me, co, 3) == 2:
                    bui.getsound('shieldUp').play()
                    push(f"No need, it's so close", color=(1, 0, 0))
                    return
                ding(f"Drew a line between you and position!")
                if random.randint(1, 10) == 10:
                    push('Tip: wait for some particles to die if line wasn\'t drawn')
                for i in s.draw_line(co, me):
                    bs.emitfx(position=i,
                              scale=2, count=1, spread=0,
                              chunk_type=chunk_types[0 if Nice.lite_mode else 1])
            else:
                ding(f"Particle spawned at position!")
                s.hl(co)

    # hl4 should only be called when hl3 is present
    def hl4(s, bot):
        def w():
            global mod_widget
            return mod_widget.exists()
        old = bot.node.color
        old_off = (old[0]-5, old[1]-5, old[2]-5)
        def hl4_off(bot, old_off): bot.node.color = old_off

        def hl4_on(bot, old):
            if w():
                bot.node.color = old
        # that spaz is goin blinking fr
        if Nice.lite_mode:
            return
        bs.apptimer(0, bs.Call(hl4_on, bot, old))
        bs.apptimer(0.5, bs.Call(hl4_off, bot, old_off))
        bs.apptimer(1, bs.Call(hl4_on, bot, old))
        bs.apptimer(1.5, bs.Call(hl4_off, bot, old_off))
        bs.apptimer(2, bs.Call(hl4_on, bot, old))

    def reset_bright_bots(s):
        global lmao_bots, lmao_players
        # made specially for hl3
        for b in lmao_bots:
            try:
                c = b.node.color
            except:
                continue
            # this nukes all bright colors, they look annoying anyway
            if c[0] >= 5:
                b.node.color = (c[0]-5, c[1]-5, c[2]-5)

        try:
            for b in lmao_players:
                try:
                    c = b.actor.node.color
                except:
                    continue
                if c[0] >= 5:
                    b.actor.node.color = (c[0]-5, c[1]-5, c[2]-5)
        except NameError:
            return

    def hl3(s, i, set=True):
        global lmao_bots, drux, effect_bots, lmao_players
        drux = i
        s.reset_bright_bots()
        if Nice.lite_mode:
            return
        if i is not None:
            try:
                bot = lmao_bots[i].node if effect_bots else lmao_players[i].actor.node
            except IndexError:
                return
            old = bot.color
            if set:
                bot.color = (old[0]+5, old[1]+5, old[2]+5)

    def hl2(s, p, instant=False):
        s.hl3(None)
        if Nice.lite_mode:
            return
        old = p.color
        n = 10
        shade = (old[0]+n, old[1]+n, old[2]+n)
        p.color = shade

        def nah(n):
            n -= 0.01
            shade = (old[0]+n, old[1]+n, old[2]+n)
            p.color = shade
            if old[0] > shade[0]:
                return
            bs.apptimer(0.001, bs.Call(nah, n))
        bs.apptimer(0 if instant else 2, bs.Call(nah, n))

    def hl(s, p):
        v1 = 2
        v2 = 10
        if Nice.lite_mode:
            v1 = 1
            v2 = 3
        with ga().context:
            bs.emitfx(position=p, tendril_type=tendril_types[1],
                      scale=v1, count=v2, spread=0,
                      chunk_type=chunk_types[0])

    # TODO by-id positioning
    def use_my_pos(s, c2=False):
        global cords, cords_widget, cords2_widget, cords2
        if c2 is True:
            cords2 = s.get_my_pos()
        elif c2 is False:
            cords = s.get_my_pos()
        else:
            Nice.drop_cords = s.get_my_pos()
        if s.get_my_pos():
            s.update_cords_view(c2)
        else:
            error('You are not in game')
        s.kill(True, cords2_widget if c2 is True else cords_widget if c2 is False else s.where_drop_widget, c2)
        bui.getsound('gunCocking').play()

    def get_my_pos(s):
        global max_digits
        p = []
        for k in ga().players:
            if k.sessionplayer.inputdevice.client_id == -1:
                for i in k.node.position:
                    p.append(float(str(i)[:max_digits]))

                cords = (float(p[0]), float(p[1]), float(p[2]))
                return cords

    def update_cords_view(s, c2=False):
        global cords_view, cords, cords2_view, cords2
        c = cords2 if c2 is True else cords if c2 != 69 else Nice.drop_cords
        try:
            bui.buttonwidget(edit=cords2_view if c2 is True else cords_view if c2 != 69 else s.drop_where,
                             label=f"X: {c[0]}\nY: {c[1]}\nZ: {c[2]}" if c[0] != 69123 else 'Where To\nTeleport?' if c2 != 69 else "Where To\nDeploy?")
        except TypeError:
            error("Join the game first bruh")

    # math is OP after all
    def draw_line(s, c, me):
        def gd(c, me): return ((c[0] - me[0])**2 + (c[1] - me[1])**2 + (c[2] - me[2])**2)**0.5
        d = gd(c, me)
        n = int(d)
        pol = []
        for i in range(n):
            t = i / (n - 1)
            x = c[0] + t * (me[0] - c[0])
            y = c[1] + t * (me[1] - c[1])
            z = c[2] + t * (me[2] - c[2])
            pol.append((x, y, z))
        return pol

    def are_close(s, p1, p2, sus):
        try:
            d = ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)**0.5
        except TypeError:
            return 1
        if d < sus:
            return 2
        else:
            return 3

    def restore_sp(s, bot):
        if not bot._super:
            return
        if bot._has_boxing_gloves:
            return
        push("Suspected gloves expiration\nrestoring super punch")
        s.give_sp(bot)


class NicePick(bui.Window):
    def __init__(s, t, u, i):
        global hmm
        hmm = i
        ColorPicker(
            parent=bui.get_special_widget('overlay_stack'),
            tag=('color'),
            delegate=s,
            initial_color=u,
            position=(700, 0))

    def _set_color(s, color): pass

    def color_picker_selected_color(s, picker, c):
        global hmm, val_attrs2, ins
        Nice.val_attrs[hmm] = c
        bui.buttonwidget(edit=ins[hmm],
                         label=f"{str(c[0]+0.01)[:3]} {str(c[1]+0.01)[:3]}, {str(c[2]+0.01)[:3]}",
                         color=c,
                         on_activate_call=bs.Call(NicePick, s, c, hmm),
                         textcolor=(1-c[0], 1-c[1], 1-c[2]))
        Nice.gather(Nice, False, False)
        val_attrs2[hmm] = c

    def color_picker_closing(self, picker): pass


class NicePick2(bui.Window):
    def __init__(s, t, u, i):
        global hmm2
        hmm2 = i
        ColorPicker(
            parent=bui.get_special_widget('overlay_stack'),
            tag=('color'),
            delegate=s,
            initial_color=u,
            position=(700, 0))

    def _set_color(s, color): pass

    def color_picker_selected_color(s, picker, c):
        global hmm2, val_attrs2, ins2
        val_attrs2[hmm2] = c
        bui.buttonwidget(
            edit=ins2[hmm2], label=f"{str(c[0]+0.01)[:3]} {str(c[1]+0.01)[:3]}, {str(c[2]+0.01)[:3]}", color=c, textcolor=(1-c[0], 1-c[1], 1-c[2]))
        bui.buttonwidget(edit=ins2[hmm2], on_activate_call=bs.Call(NicePick2, s, c, hmm2))

    def color_picker_closing(self, picker): pass


class PickerLight(bui.Window):
    def __init__(s, u):
        ColorPicker(
            parent=bui.get_special_widget('overlay_stack'),
            tag=('color'),
            delegate=s,
            initial_color=u,
            position=(700, 0))

    def _set_color(s, color): pass

    def color_picker_selected_color(s, picker, c):
        bui.buttonwidget(edit=light_pick, color=c)
        bui.buttonwidget(edit=light_pick, textcolor=Nice.negate(Nice, c))
        bui.buttonwidget(edit=light_pick, on_activate_call=bs.Call(PickerLight, c))
        Nice.ga_tint = c

    def color_picker_closing(self, picker): pass


class PickerLol(bui.Window):
    def __init__(s, u):
        ColorPicker(
            parent=bui.get_special_widget('overlay_stack'),
            tag=('color'),
            delegate=s,
            initial_color=u,
            position=(700, 0))

    def _set_color(s, color): pass

    def color_picker_selected_color(s, picker, c):
        Nice.LTWAC = c
        bui.buttonwidget(edit=LTWAB, color=c)
        bui.buttonwidget(edit=LTWAB, textcolor=Nice.negate(Nice, c))
        bui.buttonwidget(edit=LTWAB, on_activate_call=bs.Call(PickerLol, Nice.LTWAC))

    def color_picker_closing(self, picker): pass


class Picker(popup.PopupWindow):
    def __init__(s, mod=0):
        uiscale = bui.app.ui_v1.uiscale
        scale = (1.9 if uiscale is ba.UIScale.SMALL else 1.6 if uiscale is ba.UIScale.MEDIUM else 1)
        count = len(bot_texture) if mod not in [2, 69] else len(
            effect_texture) if mod != 69 else len(drop_texture)
        columns = 3
        rows = int(math.ceil(float(count) / columns))
        bw = 100
        bh = 100
        bbh = 10
        bbv = 15
        s._width = (10 + columns * (bw + 2 * bbh) * (1.0 / 0.95) * (1.0 / 0.8))
        s._height = s._width * 0.8
        s._sw = s._width * 0.8
        s._sh = s._height * 0.9
        s._sp = ((s._width - s._sw) * 0.5, (s._height - s._sh) * 0.5)
        popup.PopupWindow.__init__(s,
                                   position=(550.0, 0.0),
                                   size=(s._width, s._height),
                                   scale=scale,
                                   bg_color=(0, 0, 0),
                                   focus_position=s._sp,
                                   focus_size=(s._sw, s._sh))
        s._scrollwidget = bui.scrollwidget(parent=s.root_widget,
                                           size=(s._sw, s._sh),
                                           color=(0, 0, 0),
                                           position=s._sp)
        bui.containerwidget(edit=s._scrollwidget, claims_left_right=True)
        s._sub_width = s._sw * 0.95
        s._sub_height = 5 + rows * (bh + 2 * bbv) + 100
        s._subcontainer = bui.containerwidget(parent=s._scrollwidget, size=(
            s._sub_width, s._sub_height), background=False)
        bui.textwidget(parent=s.root_widget,
                       text='Select character (scroll)' if mod != 2 and mod != 69 else 'Select effect (scroll)' if mod != 69 else 'What to deploy? (scroll)',
                       scale=scale/2,
                       position=(130, 364))
        mask_texture = bui.gettexture('characterIconMask')  # good frame
        index = 0
        for y in range(rows):
            for x in range(columns):
                pos = (x * (bw + 2 * bbh) + bbh, s._sub_height - (y + 1) * (bh + 2 * bbv) + 12)
                try:
                    icon = bui.gettexture(bot_texture[index] + 'Icon') if mod not in [2, 69] else bui.gettexture(
                        effect_texture[index]) if mod != 69 else bui.gettexture(drop_texture[index])
                except IndexError:
                    return
                btn = bui.buttonwidget(
                    parent=s._subcontainer,
                    button_type='square',
                    position=(pos[0], pos[1]),
                    size=(bw, bh),
                    autoselect=True,
                    texture=icon,
                    tint_texture=(bui.gettexture(
                        bot_texture[index]+'IconColorMask') if mod not in [2, 69] else None),
                    tint_color=val_attrs2[6] if mod == 1 else None if mod in [
                        2, 69] else Nice.val_attrs[6],
                    tint2_color=val_attrs2[11] if mod == 1 else None if mod in [
                        2, 69] else Nice.val_attrs[11],
                    color=(1, 1, 1),
                    mask_texture=mask_texture,
                    label='',
                    on_activate_call=bs.Call(s.ok, index, mod))
                bui.widget(edit=btn, show_buffer_top=60, show_buffer_bottom=60)
                name = bot_name[index] if mod not in [
                    2, 69] else effect_name[index] if mod != 69 else drop_name[index]
                bui.textwidget(parent=s._subcontainer,
                               text=name,
                               position=(pos[0] + bw * 0.5, pos[1] - 12),
                               size=(0, 0),
                               scale=0.5,
                               maxwidth=bw,
                               draw_controller=btn,
                               h_align='center',
                               v_align='center')
                index += 1
                if index >= len(bot_texture if mod not in [2, 69] else effect_texture if mod != 69 else drop_texture):
                    break  # brb
            if index >= len(bot_texture if mod not in [2, 69] else effect_texture if mod != 69 else drop_texture):
                break  # bye bye

    def ok(s, index, mod=False):
        global effect_bots
        bui.containerwidget(edit=s.root_widget, transition=anim_out)
        if index or index == 0:
            Nice.spawn(Nice, index, mod if effect_bots or mod == 69 else mod + 1)

    def on_popup_cancel(s) -> None:
        bui.getsound('swish').play()
        s.ok(None)


class TexturePicker(popup.PopupWindow):
    def __init__(s):
        scale = Nice.scale
        count = len(all_texture)
        columns = 6
        rows = int(math.ceil(float(count) / columns))
        bw = 100
        bh = 100
        bbh = 10
        bbv = 15
        s._width = (10 + columns * (bw + 2 * bbh) * (1.0 / 0.95) * (1.0 / 0.8))
        s._height = s._width * 0.8
        s._sw = s._width * 0.8
        s._sh = s._height * 0.9
        s._sp = ((s._width - s._sw) * 0.5, (s._height - s._sh) * 0.5)
        popup.PopupWindow.__init__(s,
                                   position=(550.0, 0.0),
                                   size=(s._width, s._height),
                                   scale=scale,
                                   bg_color=(0, 0, 0),
                                   focus_position=s._sp,
                                   focus_size=(s._sw, s._sh))
        s._scrollwidget = bui.scrollwidget(parent=s.root_widget,
                                           size=(s._sw, s._sh),
                                           color=(0, 0, 0),
                                           position=s._sp)
        bui.containerwidget(edit=s._scrollwidget, claims_left_right=True)
        s._sub_width = s._sw * 0.95
        s._sub_height = 5 + rows * (bh + 2 * bbv) + 100
        s._subcontainer = bui.containerwidget(parent=s._scrollwidget, size=(
            s._sub_width, s._sub_height), background=False)
        index = 0
        for y in range(rows):
            for x in range(columns):
                pos = (x * (bw + 2 * bbh) + bbh, s._sub_height - (y + 1) * (bh + 2 * bbv) + 12)
                try:
                    icon = bui.gettexture(all_texture[index])
                except IndexError:
                    return
                btn = bui.buttonwidget(
                    parent=s._subcontainer,
                    button_type='square',
                    position=(pos[0], pos[1]),
                    size=(bw, bh),
                    autoselect=True,
                    texture=icon,
                    color=(1, 1, 1),
                    label='',
                    on_activate_call=bs.Call(s.ok, index))
                bui.widget(edit=btn, show_buffer_top=60, show_buffer_bottom=60)
                name = all_texture[index]
                bui.textwidget(parent=s._subcontainer,
                               text=name,
                               position=(pos[0] + bw * 0.5, pos[1] - 12),
                               size=(0, 0),
                               scale=0.5,
                               maxwidth=bw,
                               draw_controller=btn,
                               h_align='center',
                               v_align='center')
                index += 1
                if index >= len(all_texture):
                    break
            if index >= len(all_texture):
                break  # bye bye

    def ok(s, index):
        global THE_TB
        bui.containerwidget(edit=s.root_widget, transition=anim_out)
        try:
            bui.textwidget(edit=THE_TB, text=all_texture[index])
        except TypeError:
            pass  # NoneType

    def on_popup_cancel(s) -> None:
        bui.getsound('swish').play()
        s.ok(None)


# Initialize Arrays
toxic = ["You can't run too far",
         "You're dead",
         "Keep running noob",
         "Come here you deadmeat",
         "It's about time",
         "Do not resist your death",
         "The instrument of doom",
         "Your death is near",
         "I see your fear, just die",
         "COME HERE",
         "KILL KILL KILL",
         "I'm the OnePunchMan",
         "STOP LET ME KILL U",
         "YOU'RE ALMOST DEAD"]

toxic_win = ["HAHAHHAA",
             "Easy noob",
             "And stay dead",
             "That was easy",
             "HE'S DEAD.",
             "YOU FAILED! HAHAH"]

load_name = ["Beboo The GOAT",
             "Kronk Buddy",
             "Flying Pixel",
             "Suicidal Jack (or not?)",
             "Big Shiny TNT",
             "Liying bomb",
             "Huge Safe Mine"]

random_team = [
    ["Cyan", (0, 1, 1)],
    ["Yellow", (1, 1, 0)],
    ["Winners", (1, 0, 1)],
    ["Zamn", (0.5, 1, 0.5)],
    ["Gang", (0.5, 0.5, 1)],
    ["White", (1, 1, 1)],
    ["Noobs", (0.4, 0.2, 0.1)],
    ["Pros", (0.2, 0.4, 0.1)],
    ["Green", (0, 1, 0)],
    ["Orange", (1, 0.5, 0)],
    ["Purple", (0.5, 0, 0.5)],
    ["Silver", (0.75, 0.75, 0.75)],
    ["Gold", (0.8, 0.6, 0.2)],
    ["Pink", (1, 0.5, 0.5)],
    ["Turquoise", (0, 1, 1)],
    ["Lime", (0.75, 1, 0)],
    ["Maroon", (0.5, 0, 0)],
    ["Teal", (0, 0.5, 0.5)],
    ["Navy", (0, 0, 0.5)],
    ["Magenta", (1, 0, 1)],
    ["Brown", (0.6, 0.3, 0)],
    ["Sky", (0.53, 0.81, 0.92)],
    ["Raptors", (0.9, 0.1, 0.1)],
    ["Sharks", (0.1, 0.1, 0.9)],
    ["Tigers", (1, 0.5, 0)],
    ["Dragons", (0.5, 0, 1)],
    ["Falcons", (0.75, 0.75, 0)],
    ["Wolves", (0.5, 0.5, 0.5)],
    ["Lions", (1, 0.5, 0.5)],
    ["Panthers", (0.1, 0, 0.1)]
]

node_attrs = ['gotta clean this code soon', 'gravity_scale', 'sticky',
              'reflection=\'powerup\'', "reflection='soft'", "reflection_scale"]
node_welps = ["i mean for real", "How likely is it to be pulled by the ground.\ndefault: 1.0, increasing makes it heavier\ndecreasing makes it lighter, it may even fly,\nnegative values cause object to fall up",
              'When checked, object spawns sticky\nwhich sticks to anything lol', "reflect light like powerups do", "reflect light softly like bombs do", "how shiny the reflection can get, default is 1.2\nsetting to something like 40 results in\na very shiny object which looks cool"]
powerup_name = ['triple_bombs', 'curse', 'health', 'ice_bombs',
                'impact_bombs', 'land_mines', 'punch',
                'shield', 'sticky_bombs']
effect_texture = (['powerupBomb', 'powerupCurse', 'powerupHealth', 'powerupIceBombs',
                   'powerupImpactBombs', 'powerupLandMines', 'powerupPunch',
                   'powerupShield', 'powerupStickyBombs', 'graphicsIcon',
                   'bombColorIce', 'touchArrowsActions', 'trophy',
                   'crossOut', 'bonesIcon', 'lock',
                   'achievementGotTheMoves', 'backIcon',
                   'star', 'achievementCrossHair',
                   'achievementOffYouGo', 'achievementFootballShutout',
                   'achievementSuperPunch', 'leftButton',
                   "buttonJump", "downButton"])
effect_texture.append("neoSpazIconColorMask")
effect_texture.append("replayIcon")

effect_name = ["Triple Bombs", "Curse", "Heal", "Ice Bombs", "Impact Bombs", "Land Mines",
               "Gloves", "Energy Shield", "Sticky Bombs", "Shatter", "Freeze",
               "Unfreeze", "Celebrate", "Stop Celebrating", "Kill", "Infinite Curse",
               "Super Speed", "Normal Speed", "Invincible", "Beatable", "Sleep",
               "Wake Up", "Super Punch", "Normal Punch", "Fly Jumps", "Normal Jumps"]
effect_name.append("GodMode Preset")
effect_name.append("Reset All")

effect_tips = ["PowerUp\nSets default_bomb_count\nvalue to 3 for a short while",
               "PowerUp\nCurse the player, making\nthem explode in 5 seconds",
               "PowerUp\nHeal the player, removing\nany curses and wounds!",
               "PowerUp\nSets default_bomb_type\nvalue to ice for a short while",
               "PowerUp\nSets default_bomb_type\nvalue to impact for a short while",
               "PowerUp\nSets land_mine_count\nvalue to 3, decreased on use",
               "PowerUp\nGives the player\nboxing gloves for a short while",
               "PowerUp\nGives the player an\nenergy shield, decays over time",
               "PowerUp\nSets default_bomb_type\nvalue to sticky for a short while",
               "Effect\nShatters the player\ntearing them apart everywhere",
               "Effect\nFreezes the player\nparalyzing them for an amount of time\nand calling FreezeMessage\ndoesn't work on shielded spazes",
               "Effect\nImmediately unfreezes player\nmelting the ice and calling ThawMessage",
               "Emote\nMakes the spaz celebrate forever!",
               "Emote\nMakes the spaz stop celebrating!",
               "Instant Effect\nImmediately kill the spaz\nfor good.",
               "Effect Granter\nApply an infinite curse\non the poor spaz, although\ncurse -> heal -> repeat",
               "Effect Granter\nApply super speed to bot\nsince I couldn't make it run\nbcz me nub",
               "Effect Revoker\nReturn bot speed to normal\nin case you used super speed",
               "Effect Granter\nMake the bot Invincible!\nwhich means it would be immune,\nmaking a weird rod sound upon\nbeing hit",
               "Effect Revoker\nTake the invincibility off the bot\nmaking it valnurable",
               "Effect Granter\nMake the bot have a nap that lasts forever.\nYes, they won't wake up",
               "Effect Revoker\nWake the bot up if it's sleeping or so",
               "Effect Granter\nTurn the bot into OnePunchMan\nin addition to removing\npunch cooldown",
               "Effect Revoker\nRemoves super punch powers from bot",
               "Effect Granter\nGives the bot unlimited jumps\nwhich makes it fly after each",
               "Effect Revoker\nRemoves the fly jumps effect\nwhich returns old jumping behaviour"]
effect_tips.append("Multiple Effect Granter\nGiven effects:\nSuper Punch\nInvincibility\nSpeed")
effect_tips.append("Universal Effect Revoker\nRemoves all effects on bot,\nwho's laughing now?")

effect_message = ["triple_bombs", "curse", "health", "ice_bombs", "impact_bombs",
                  "land_mines", "punch", "shield", "sticky_bombs"]

bot_texture = (['neoSpaz', 'kronk', 'zoe', 'ninja', 'mel', 'jack', 'bunny',
                'agent', 'penguin', 'cyborg', 'pixie', 'frosty', 'wizard',
                'bear', 'ali', 'santa', 'bones'])

bot_name = (['Spaz', 'Kronk', 'Zoe', 'Snake Shadow', 'Mel', 'Jack Morgan', 'Easter Bunny',
             'Agent Johnson', 'Pascal', 'B-9000', 'Pixel', 'Frosty',
             'Grumbledorf', 'Bernard', 'Taobao Mascot', 'Santa Claus', 'Bones'])

bot_style = ["spaz", "kronk", "female", "ninja", "mel", "pirate",
             "bunny", "agent", "penguin", "cyborg", "pixie",
             "frosty", "wizard", "bear", "ali", "santa", "bones"]

w_bot_name = ['Spas', 'Kornk', 'Girl', 'Ninja', 'Cook', 'Jack', 'Rabbit', 'Agent', 'Penguin',
              'Robot', 'Angel', 'Snowman', 'Wizard', 'Bear', 'Santa', 'Skeleton']

indox2 = 0
effect_dux = 0
effect_bots = True
has_no_color = ["kronk"]
has_no_style = ["wizard"]
on_control = False
virgin = True
bomb_down = False
effect_dux2 = 0
drux = 0
cords = (69123, 0, 0)
cords2 = (69123, 0, 0)
chunk_types = ['spark', 'slime', 'ice', 'metal', 'sweat', 'splinter', 'rock']
emit_types = ['flag_stand', 'distortion', 'stickers', 'tendrils']
tendril_types = ['ice', 'smoke', 'thin_smoke']
max_digits = 8
nice_custom_text = '$'
nice_custom_color = (0.7, 0.7, 0.7)
attrs = ["bouncy", "character", "charge_dist_max", "charge_dist_min",
         "charge_speed_max", "charge_speed_min", "color", "default_bomb_count",
         "default_bomb_type", "default_boxing_gloves", "default_shields", "highlight", "punchiness", "run", "run_dist_min",
         "demo_mode", "static", "throw_dist_max", "throw_dist_min", "throw_rate",
         "throwiness", "can_accept_powerups", "start_invincible", 'attack_host', 'attack_players',
         'attack_bots', 'attack_your_bots', 'custom_name', 'custom_name_color']
not_editable = [21, 22]
music_name = ["Char Select", "Chosen One", "Epic", "Epic Race", "Flag Catcher",
              "Flying", "Football", "Forward March", "Grand Romp", "Hockey",
              "Keep Away", "Marching", "Menu", "Onslaught", "Race",
              "Runaway", "Scary", "Scores", "Sports", "Survival",
              "To The Death", "Victory"]

drop_texture = (['powerupBomb', 'powerupCurse', 'powerupHealth', 'powerupIceBombs',
                 'powerupImpactBombs', 'powerupLandMines', 'powerupPunch',
                 'powerupShield', 'powerupStickyBombs', 'tnt',
                 "landMine", "landMineLit", "eggTex1", "eggTex2", "eggTex3", "white", "black",
                 "bombColor", "impactBombColor", "bombStickyColor", "bombColorIce"])
drop_name = ["Triple Bombs", "Curse", "Heal", "Ice Bombs", "Impact Bombs", "Land Mines",
             "Gloves", "Energy Shield", "Sticky Bombs", 'TNT', 'Land Mine',
             "Lit Land Mine", "Striped Egg", "Lined Egg", "Dotted Egg", "White Egg", "Black Egg",
             "Bomb", "Impact Bomb", "Sticky Bomb", "Ice Bomb"]

music_texture = ["neoSpazIcon", "achievementSuperPunch", "tipTopPreview", "bigGPreview", "bridgitPreview",
                 "alwaysLandPreview", "achievementFootballVictory", "cragCastlePreview", "achievementFlawlessVictory", "hockeyStadiumPreview",
                 "thePadPreview", "achievementRunaround", "logo", "doomShroomPreview", "lakeFrigidPreview",
                 "monkeyFacePreview", "powerupCurse", "achievementFootballShutout", "footballStadiumPreview", "rampagePreview",
                 "achievementOnslaught", "achievementMedalLarge"]
music_desc = ["charSelectMusic.ogg", "survivalMusic.ogg", "slowEpicMusic.ogg", "slowEpicMusic.ogg", "flagCatcherMusic.ogg",
              "flyingMusic.ogg", "sportsMusic.ogg", "forwardMarchMusic.ogg", "grandRompMusic.ogg", "sportsMusic.ogg",
              "runAwayMusic.ogg", "whenJohnnyComesMarchingHomeMusic.ogg", "menuMusic.ogg", "runAwayMusic.ogg", "runAwayMusic.ogg",
              "runAwayMusic.ogg", "scaryMusic.ogg", "scoresEpicMusic.ogg", "sportsMusic.ogg", "survivalMusic.ogg",
              "toTheDeathMusic.ogg", "victoryMusic.ogg"]
music_type = [bs.MusicType.CHAR_SELECT,
              bs.MusicType.CHOSEN_ONE,
              bs.MusicType.EPIC,
              bs.MusicType.EPIC_RACE,
              bs.MusicType.FLAG_CATCHER,
              bs.MusicType.FLYING,
              bs.MusicType.FOOTBALL,
              bs.MusicType.FORWARD_MARCH,
              bs.MusicType.GRAND_ROMP,
              bs.MusicType.HOCKEY,
              bs.MusicType.KEEP_AWAY,
              bs.MusicType.MARCHING,
              bs.MusicType.MENU,
              bs.MusicType.ONSLAUGHT,
              bs.MusicType.RACE,
              bs.MusicType.RUN_AWAY,
              bs.MusicType.SCARY,
              bs.MusicType.SCORES,
              bs.MusicType.SPORTS,
              bs.MusicType.SURVIVAL,
              bs.MusicType.TO_THE_DEATH,
              bs.MusicType.VICTORY]
val_attrs2 = Nice.def_attrs.copy()  # for modifying, not creating
val_arr = []
type_attrs = [type(i).__name__ for i in Nice.def_attrs]
lmao = []  # list of bots by string
testa = []  # list of bot floating names
old_ga = str(ga())
LAH = []
LAP = []
LAB = []
LAF = []
ATK = ['attack_host', 'attack_players', 'attack_bots', 'attack_your_bots']
lmao_bots = []
lmao_players = []
lmao_bots2 = []
lmao_chars = []
move_on = 0
dux = None
kon = None
do_tp = True
cola = (0.13, 0.13, 0.13)
colb = cola
wht = (1, 1, 1)
busy = False
# colb = (0.2, 0.2, 0.2)
anim_in = 'in_right'
anim_out = 'out_right'
bomb_type = ['normal', 'impact', 'sticky', 'ice', 'land_mine', 'tnt']
w_bomb_type = ['default', 'black', 'green', 'blue', 'mine', 'box']
welps = ['When checked, the bot randomly jumps around,\nincreasing its damage',
         'The way bot looks, more like of its "skin"\nIt has nothing to do with behavior',
         'How close the bot needs to get to you\nbefore attempting to bomb you',
         'How far the bot needs to get away from you\nbefore attempting to bomb you',
         'The limit of bomb reload speed which the bot\ncan\'t go any faster',
         'The limit of bomb reload speed which the bot\ncan\'t go any slower',
         'The main color of the bot, Has nothing to do\nwith its behaviour',
         'How much bombs the bot is allowed to throw\nin a row before the old ones explode.\nBlud has the triple bomb by default rip',
         'The type of the bomb which the bot throws,\navailable types are\nnormal, sticky, impact, ice, tnt and land_mine',
         'When checked, the bot will spawn with a shield.\nUnfair naa?',
         'When checked, the bot will spawn with gloves.\nClick spawn and start running away.',
         'The side color of bot, covers places which the\ncolor attribute doesn\'t',
         'How likely is the bot to punch, simply\nincrease this enough and it\'s gonna spam punch lol',
         'When checked, the bot is allowed to run,\nincreasing its damage',
         'How far the bot needs to be to start running',
         'I have no idea what is this,\npreviously this was start_cursed but\nI removed it because it was annoying',
         'When checked, the bot will not try to follow you,\ninstead, will try to bomb you from a remote distance.\nSpaz\'es in Rookie Onslaught have this by default.',
         'How far the distance needed by bot\nbefore throwing a bomb\nsimilar to charge, but throw!',
         'How close the distance needed\nso the bot stops throwing',
         'How likely is the bot to spam bombs',
         'How pro the bot can be at predicting your next move\nand throwing a bomb at a place you would be in',
         "When checked, bot can collect powerups!",
         "hen checked, bot spawns invincible for a short while",
         "When checked, the bot attacks the game host,\nother players have another check",
         "When checked, the bot attacks all players\nexcept the host, which has his own check",
         "When checked, the bot attacks other bots,\nexcept its friends, the bots that\nYOU spawned.",
         "When checked, the bot betrays other bots\nthat YOU spawned, for bots that you\ndidn\'t spawn exists another check",
         "Gives the bot a nice name!\nBot mame appears above its head.\nSet to '%' to follow default name,\nset to '$' to follow bot's control codename",
         "The color of bot's custom_name"]

# For Nice.what_is
what_is_arr = [["tnt", "TNT"],
               ["powerup", "PUP"]]

# BotName Builder
random_bot_names = [
    "Gapple#", "iPun#", "BathRom#", "double#", "Times#", "InsertName#", "ShutUp#", "Botty#", "Bottie#", "Clumsy#",
    "Cheeky#", "Phucc#", "Cope#", "Bebo#", "Sike#", "AwMan#", "Putt#", "Nuts#", "Kids#", "Poo#",
    "Bang#", "Sus#", "OnCrack#", "Cadeau#", "Bureau#", "Yasta#", "Eshta#", "YaZmele#", "7abibo#", "Straight#",
    "Egg#", "NotEgg#", "MaybeEgg#", "ProbEgg#", "YouEgg#", "YouNoob#", "Nub#", "HahaNoob#", "LMAO#", "LOL#",
    "Bomb#", "FrBro?#", "ForReal#", "RealOrFake#", "Real#", "Fake#", "UnFake#", "Realn't#", "Bruh#", "Stop#",
    "SnapDrag#", "Exynos#", "Lagsynos#", "GnuNano#", "Lynx#", "How#", "TeachMe#", "Scam#", "Cap#", "ScamSung#",
    "iBot#", "Just#", "I'mNot#", "Run#", "EzNoob#", "GoSleep#", "Pain#", "GalaxyTabA#", "GalaxyA#", "GalaxyS#",
    "GalaxyM#", "ReleasedV#", "MtkGen#", "MediaTek#", "IntelI#", "IndexIs#", "MyOrder#", "Grep#", "KaliLinux#", "Bios#",
    "Ftw#", "Tldr#", "Simp#", "MrSmoth#", "Bordd#", "Geh#", "KillMe#", "Bruda#", "Otg#"
]

# infinite curse pop ups
nah_uh = ["naah uh", "not today", "reset that counter!", "I'm stayin alive",
          "not in mood\nto explood", "Not today,\nthank you.",
          "Let that 1\nbecome a 5", "boomn't, let's\ntry again",
          "Infinite curse\non duty!", "3.. 2.. 1.. repeat!", "this takes forever",
          "nope, try again", "The power of\nthe infinite curse!"]

for i in range(len(nah_uh)):
    nah_uh.append("")  # 50% chance to say nothing


def meow_patch(og):
    def wrapper(self, msg: Any) -> Any:
        #        print(msg)
        if isinstance(msg, bs.DieMessage):
            if msg.how == bs.DeathType.IMPACT and self.node.getdelegate(object) not in Nice.toxic_bots:
                Nice.toxic_celebrate(Nice)
            global on_control
            if msg.how == bs.DeathType.IMPACT and hasattr(self.node.getdelegate(object), 'source_player') and on_control:
                on_control = False
                Nice.assign(Nice)
                push('Control will stop when your corpse vanish LOL', color=(0, 1, 1))
        elif isinstance(msg, bs.ImpactDamageMessage) and hasattr(self.node.getdelegate(object), 'source_player') and self.node.getdelegate(object).node.invincible:
            pos = self.node.getdelegate(object).node.position
            with ga().context:
                bs.timer(0.001, bs.Call(Nice.phew, Nice, pos))
            return
        elif isinstance(msg, bs.PowerupMessage) and msg.poweruptype == 'punch' and hasattr(self.node.getdelegate(object), "_super") and self.node.getdelegate(object)._super:
            if on_control:
                push('Gloves have canceled your Super Punch effect\nDon\'t worry, restoring Super Punch')
            bot = self.node.getdelegate(object)
            with ga().context:
                bs.timer(0.01, bs.Call(Nice.give_sp, Nice, bot))
                bs.timer(20.1, bs.Call(Nice.restore_sp, Nice, bot))
        try:
            return og(self, msg)
        except:
            pass  # safe mines are gay
    return wrapper


Spaz.handlemessage = meow_patch(Spaz.handlemessage)


class CustomBot(SpazBot):
    @classmethod
    def set_up(cls, attrs, val_attrz):
        global LAH, LAP, LAB, LAF, nice_custom_text, nice_custom_color, lmao, lmao_chars, val_arr
        val_arr.append(val_attrz.copy())
        dict = {attrs[i]: val_attrz[i] for i in range(len(attrs))}
        for key, value in dict.items():
            if key == 'character':
                lmao_chars.append(value)
            if key in ATK:
                if key == ATK[0]:
                    LAH.append(value)
                if key == ATK[1]:
                    LAP.append(value)
                if key == ATK[2]:
                    LAB.append(value)
                if key == ATK[3]:
                    LAF.append(value)
            elif key == 'custom_name':
                t = value
                if value == '%':
                    t = val_attrz[attrs.index('character')]
                elif value == '$':
                    t = lmao[-1]  # NO_BOT
                nice_custom_text = t
            elif key == 'custom_name_color':
                nice_custom_color = value
            else:
                setattr(cls, key, value)

    def __init__(self, player) -> None:
        Spaz.__init__(self,
                      color=self.color,
                      highlight=self.highlight,
                      character=self.character,
                      source_player=None,
                      start_invincible=self.start_invincible,
                      can_accept_powerups=self.can_accept_powerups)
        self.update_callback: Optional[Callable[[SpazBot], Any]] = None
        activity = self.activity
        assert isinstance(activity, bs.GameActivity)
        self._map = weakref.ref(activity.map)
        self.last_player_attacked_by: Optional[bs.Player] = None
        self.last_attacked_time = 0.0
        self.last_attacked_type: Optional[Tuple[str, str]] = None
        self.target_point_default: Optional[bs.Vec3] = None
        self.held_count = 0
        self.last_player_held_by: Optional[bs.Player] = None
        self.target_flag: Optional[Flag] = None
        self._charge_speed = 0.5 * (self.charge_speed_min +
                                    self.charge_speed_max)
        self._lead_amount = 0.5
        self._mode = 'wait'
        self._charge_closing_in = False
        self._last_charge_dist = 0.0
        self._running = False
        self._last_jump_time = 0.0

    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, bs.DieMessage):
            if self.node.getnodetype() == 'spaz':
                s = self.node.getdelegate(object)
                if isinstance(s, SpazBot) and s in lmao_bots:
                    try:
                        j = lmao_bots.index(s)
                    except:
                        j = 69123
                    if j != 69123:
                        Nice.update_alive_bots(Nice)
                        global move_on, dux, control_widget, on_control, allow_assign, alive_bots, currently_dux
                        if not s._dead:
                            move_on += 1
                            if Nice.notify_bot_ded:
                                push(f'{lmao[lmao_bots.index(s)]} has died!', color=(1, 0, 1))
                            p = self.node.position  # PEPSI
                            if dux == lmao_bots.index(s) and on_control:
                                push('the bot you are controlling has died LMAO', color=(1, 0.2, 0.7))
                                on_control = False
                                allow_assign = True
                                Nice.assign(Nice)
            wasdead = self._dead
            self._dead = True
            self.hitpoints = 0
            if msg.immediate:
                if self.node:
                    self.node.delete()
            elif self.node:
                self.node.hurt = 1.0
                if self.play_big_death_sound and not wasdead:
                    SpazFactory.get().single_player_death_sound.play()
                self.node.dead = True
                bs.timer(2.0, self.node.delete)  # TODO ragdoll erase time settings
        else:
            return super().handlemessage(msg)


class CustomBotSet(SpazBotSet):
    def __init__(self,
                 source_player: bs.Player = None) -> None:
        self._bot_list_count = 5
        self._bot_add_list = 0
        self._bot_update_list = 0
        self._bot_lists: List[List[SpazBot]] = [
            [] for _ in range(self._bot_list_count)
        ]
        self._spawn_sound = bs.getsound('spawn')
        self._spawning_count = 0
        self._bot_update_timer: Optional[bs.Timer] = None
        self.start_moving_customs()
        self.source_player = source_player

    def do_custom(self) -> None:
        global cords
        self.spawn_bot(CustomBot,
                       cords,
                       0, self.setup_custom)

    def start_moving_customs(self) -> None:
        self._bot_update_timer = bs.Timer(0.05,
                                          bs.WeakCall(self._bupdate),
                                          repeat=True)

    def _spawn_bot(self, bot_type: type[SpazBot], pos: Sequence[float],
                   on_spawn_call: Optional[Callable[[SpazBot], Any]]) -> None:
        spaz = bot_type(self.source_player)
        self._spawn_sound.play(position=pos)
        spaz.node.handlemessage('flash')
        spaz.node.is_area_of_interest = True
        spaz.handlemessage(bs.StandMessage(pos, random.uniform(0, 360)))
        self.add_bot(spaz)
        if on_spawn_call is not None:
            on_spawn_call(spaz)
            global busy
            busy = False

    def _bupdate(self) -> None:
        global LAH, LAP, LAB, LAF, lmao_bots
        nuds = bs.getnodes()
        bot_list = self._bot_lists[self._bot_update_list] = ([
            b for b in self._bot_lists[self._bot_update_list] if b
        ])
        player_pts = []
        not_host = []
        bad_bots = []
        good_bots = []
        host = None
        for n in nuds:
            if n.getnodetype() == 'spaz':
                s = n.getdelegate(object)
                if isinstance(s, SpazBot):
                    if not s in self.get_living_bots():
                        if hasattr(s, 'source_player'):
                            player_pts.append((
                                bs.Vec3(n.position),
                                bs.Vec3(n.velocity)))
                            if s.source_player is self.source_player:
                                good_bots.append(player_pts[-1])
                        else:
                            player_pts.append((
                                bs.Vec3(n.position),
                                bs.Vec3(n.velocity)))
                            bad_bots.append(player_pts[-1])
                elif isinstance(s, PlayerSpaz):
                    player_pts.append((
                        bs.Vec3(n.position),
                        bs.Vec3(n.velocity)))
                    bowl = s.getplayer(bs.Player, True) is self.source_player
                    if bowl:
                        host = player_pts[-1]
                    else:
                        not_host.append(player_pts[-1])

        for bot in bot_list:
            if bot not in lmao_bots:
                lmao_bots.append(bot)
            i = lmao_bots.index(bot)
            if not LAH[i]:
                player_pts.remove(host)
            if not LAP[i]:
                player_pts = [k for k in player_pts if k not in not_host]
            if not LAB[i]:
                player_pts = [k for k in player_pts if k not in bad_bots]
            if not LAF[i]:
                player_pts = [k for k in player_pts if k not in good_bots]
            bot.set_player_points(player_pts)
            bot.update_ai()

        for bot in self.get_living_bots():
            if bot not in lmao_bots2 and bot not in lmao_bots:
                lmao_bots2.append(bot)

    def setup_custom(self, spaz) -> None:
        spaz.source_player = self.source_player
        self.set_custom_text(spaz)
        for i in Nice.pending:
            if i == "sp":
                Nice.give_sp(Nice, spaz)
            if i == "speed":
                spaz.node.hockey = True
            if i == "constant_heal":
                Nice.constant_heal(Nice, spaz)
            if i == "toxic":
                Nice.toxic_bots.append(spaz)
                Nice.make_toxic(Nice, spaz)
            if i == "constant_jump":
                spaz.on_jump_press = Nice.spaz_bot_fly(Nice, spaz.on_jump_press)
                Nice.constant_jump(Nice, spaz)
            if i == "infinite_curse":
                if spaz._cursed:
                    spaz.handlemessage(bs.PowerupMessage('health'))
                spaz.curse()
                Nice.spam_curse(Nice, spaz)

    def set_custom_text(self, spaz) -> None:  # FLOAT
        global nice_custom_text, nice_custom_color, testa
        try:
            m = bs.newnode('math',
                           owner=spaz.node,
                           attrs={'input1': (0, 1.2, 0),
                                  'operation': 'add'})
            spaz.node.connectattr('position', m, 'input2')
            test = spaz._custom_text = bs.newnode(
                'text',
                owner=spaz.node,
                attrs={'text': nice_custom_text,
                       'in_world': True,
                       'shadow': 1.0,
                       'flatness': 1.0,
                       'color': nice_custom_color,
                       'scale': 0.0,
                       'h_align': 'center'})
            m.connectattr('output', spaz._custom_text, 'position')
            bs.animate(spaz._custom_text, 'scale', {0: 0.0, 0.5: 0.01})
            testa.append(test)
        except:
            pass

# ba_meta require api 8
# BroBordd touch grass
# Copyright 2024, solely by BroBordd. All rights reserved.
# ba_meta export plugin


class byBordd(ba.Plugin):
    def __init__(s):
        mm.MainMenuWindow._refresh_in_game = Nice.Button(mm.MainMenuWindow._refresh_in_game)


# All Textures (generated)
all_texture = [i[:-4] for i in ls("ba_data/textures")]
