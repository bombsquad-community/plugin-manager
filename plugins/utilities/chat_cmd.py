# Ported by brostos to api 8
# Tool used to make porting easier.(https://github.com/bombsquad-community/baport)
"""python 3.9 | chatcmd for a beutiful game  - BombSquad OwO"""
# modded by IM_NOT_PRANAV#7874

# biggggggg thankssssssssssssss to FireFighter1037 for helping everything

# -*- coding: utf-8 -*-
# Ported by brostos to api 8
# ba_meta require api 8

import threading
import time
from bascenev1 import get_foreground_host_activity, get_foreground_host_session, get_game_roster, get_chat_messages, chatmessage as cmsg
from bauiv1 import set_party_icon_always_visible, screenmessage as smsg
import babase
import bauiv1 as bui
import bascenev1 as bs
from bauiv1lib import mainmenu

# our prefix that what we starts cmds with
px = '/'

# main class


class _cmds:

    def _process_cmd():
        try:
            messages = get_chat_messages()
            if len(messages) > 1:
                lastmsg = messages[len(messages)-1]

                m = lastmsg.split(' ')[1]
                if m.startswith(px):
                    return _cmds._handle()
                else:
                    pass
        except:
            pass

    def _handle():
        messages = get_chat_messages()
        if len(messages) > 1:
            lastmsg = messages[len(messages)-1]

            m = lastmsg.split(' ')[1]  # cmd
            n = lastmsg.split(' ')[2:]  # aguments

            roster = get_game_roster()
            session = get_foreground_host_session()
            session_players = session.sessionplayers

            activity = get_foreground_host_activity()
            activity_players = activity.players

            if m == px:
                cmsg(px+'help for help')

            elif m == px+'help':
                if n == []:
                    cmsg('===========================================')
                    cmsg(f' {px}help 1 - for page 1 | simple commands')
                    cmsg(f' {px}help 2 - for page 2 | all or number of list cmds')
                    cmsg(f' {px}help 3 - for page 3 | Other useful cmds')
                    cmsg('===========================================')
                elif n[0] == '1':
                    cmsg('============================')
                    cmsg(f' {px}help 1 page 1 |')
                    cmsg(f' {px}help 1 page 2 |')
                    cmsg('============================')
                    if n[1] in ['page', 'Page', ]:
                        if n[2] == '1':
                            cmsg('============== Help 1, Page 1 ==============')
                            cmsg(f' your command prefix is or all commands starts with - {px}')
                            cmsg(f' {px}list or {px}l -- to see ids of players and execute commands')
                            cmsg(f' {px}uniqeid or {px}id -- to see accountid/uniqeid of player')
                            cmsg(f' {px}quit or {px}restart -- to restart the game')
                            cmsg(f' {px}mute/unmute -- to mute chat for everyone in your game')
                        elif n[2] == '2':
                            cmsg('============== Help 1, Page 2 ==============')
                            cmsg(f' {px}pause -- to pause everyone in your game')
                            cmsg(f' {px}nv or {px}night -- to make night in your game')
                            cmsg(f' {px}dv or {px}day -- to make night in your game')
                            cmsg(f' {px}camera_mode -- to rotate camera, repat to off')
                            cmsg('===========================================')
                elif n[0] == '2':
                    cmsg('============================')
                    cmsg(f' {px}help 2 page 1 |')
                    cmsg(f' {px}help 2 page 2 |')
                    cmsg(f' {px}help 2 page 3 |')
                    cmsg('============================')
                    if n[1] in ['page', 'Page']:
                        if n[2] == '1':
                            cmsg('============== Help 2 Page 1 ==============')
                            cmsg(f' {px}kill all or {px}kill number of list | kills the player')
                            cmsg(f' {px}heal all or {px}heal number of list | heals the players')
                            cmsg(f' {px}freeze all or {px}freeze number of list | freeze the player')
                            cmsg(
                                f' {px}unfreeze/thaw all or {px}unfreeze/thaw number of list | unfreeze the player')
                            cmsg(f' {px}gloves all or {
                                 px}gloves number of list | give gloves to player')
                            cmsg('============================')
                        elif n[2] == '2':
                            cmsg('============== Help 2 Page 2 ==============')
                            cmsg(f' {px}shield all or {
                                 px}shield number of list | give shield the player')
                            cmsg(
                                f' {px}fall all or {px}fall number of list | teleport in down and fall up the player')
                            cmsg(f' {px}curse all or {px}curse number of list | curse the player')
                            cmsg(
                                f' {px}creepy all or {px}creepy number of list | make creepy actor of player')
                            cmsg(f' {px}inv all or {px}inv number of list | makes invisible player')
                            cmsg(
                                f' {px}celebrate all or {px}celebrate number of list | celebrate action to the player')
                            cmsg('============================')
                        elif n[2] == '3':
                            cmsg('============== Help 2 Page 3 ==============')
                            cmsg(f' {px}gm all or {
                                 px}gm number of list | give bs gods like powers to player')
                            cmsg(
                                f' {px}sp all or {px}sp number of list | give superrrrrrr damages when punch to player')
                            cmsg(f' {px}sleep all or {px}sleep number of list | sleep up the player')
                            cmsg(f' {px}fly all or {px}fly number of list | fly up the player ')
                            cmsg(f' {px}hug number of list | hugup the player')
                            cmsg('============================')

                elif n[0] == '3':
                    cmsg('============================')
                    cmsg(f" {px}d_bomb bombType | changes default bomb | do {
                         px}d_bomb help for bomb names ")
                    cmsg(f' {px}dbc (number of bombs) | changes default count of player')
                    cmsg('============================')

            elif m in [px+'list', px+'l', px+'clientids', px+'ids', px+'playerids']:
                cmsg('======= Indexs ======')
                for i in session_players:
                    cmsg(i.getname()+' -->  '+str(session_players.index(i))+'\n')
                if not roster == []:
                    for i in roster:
                        cmsg(f'======For {px}kick only======')
                    cmsg(str(i['players'][0]['nam_full'])+'   -   '+str(i['client_id']))

            elif m in [px+'uniqeid', px+'id', px+'pb-id', px+'pb', px+'accountid']:
                if n == []:
                    cmsg(f'use: {px}uniqeid number of list')
                else:
                    try:
                        id = session_players[int(n[0])]
                        cmsg(id.getname()+"'s accountid is "+id.get_v1_account_id())
                    except:
                        cmsg('could not found player')

            elif m in [px+'quit', px+'restart']:
                babase.quit()

            elif m in [px+'mute', px+'mutechat']:
                cfg = babase.app.config
                cfg['Chat Muted'] = True
                cfg.apply_and_commit()
                cmsg('muted')
                smsg(f'chat muted use {px}unmute and click on send to unmute')

            elif m in [px+'unmute', px+'unmutechat']:
                cfg = babase.app.config
                cfg['Chat Muted'] = False
                cfg.apply_and_commit()
                cmsg('un_muted')
                smsg('chat un_muted')

            elif m in [px+'end', px+'next']:
                if n == []:
                    try:
                        activity.end_game()
                        cmsg('Game ended Hope you scored great')
                    except:
                        cmsg('Game already ended')

            elif m in [px+'dv', px+'day']:
                if activity.globalsnode.tint == (1.0, 1.0, 1.0):
                    cmsg(f'alwardy {px}dv is on, do {px}nv for night')
                else:
                    activity.globalsnode.tint = (1.0, 1.0, 1.0)
                    cmsg('day mode on!')

            elif m in [px+'nv', px+'night']:
                if activity.globalsnode.tint == (0.5, 0.7, 1.0):
                    cmsg(f'alwardy {px}nv is on, do {px}dv for day')
                else:
                    activity.globalsnode.tint = (0.5, 0.7, 1.0)
                    cmsg('night mode on!')

            elif m in [px+'sm', px+'slow', px+'slowmo']:
                if n == []:
                    if not activity.globalsnode.slow_motion:
                        activity.globalsnode.slow_motion = True
                        cmsg('Game in Epic Mode Now')
                    else:
                        activity.globalsnode.slow_motion = False
                        cmsg('Game in normal mode now ')

            elif m in [px+'pause', px+'pausegame']:
                if n == []:
                    if not activity.globalsnode.paused:
                        activity.globalsnode.paused = True
                        cmsg('Game Paused')
                    else:
                        activity.globalsnode.paused = False
                        cmsg('Game un paused')

            elif m in [px+'cameraMode', px+'camera_mode', px+'rotate_camera']:
                if n == []:
                    if not activity.globalsnode.camera_mode == 'rotate':
                        activity.globalsnode.camera_mode = 'rotate'
                        cmsg('camera mode is rotate now')
                    else:
                        activity.globalsnode.camera_mode = 'follow'
                        cmsg('camera mode is normal now')

            elif m in [px+'remove', px+'rm']:
                if n == []:
                    cmsg(f'{px}remove all or {px}remove number in list')
                elif n[0] == 'all':
                    for i in session_players:
                        i.remove_from_game()
                        cmsg('Removed All')
                else:
                    try:
                        r = session_players[int(n[0])]
                        r.remove_from_game()
                        cmsg('Removed')  # cant use getname() activity alwrady finish
                    except:
                        cmsg('could not found player')
            elif m in [px+'inv', px+'invisible']:
                if n == []:
                    cmsg(f'help: {px}inv all or {px}inv number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        body = i.actor.node
                        if not body.torso_mesh == None:
                            body.head_mesh = None
                            body.torso_mesh = None
                            body.upper_arm_mesh = None
                            body.forearm_mesh = None
                            body.pelvis_mesh = None
                            body.hand_mesh = None
                            body.toes_mesh = None
                            body.upper_leg_mesh = None
                            body.lower_leg_mesh = None
                            body.style = 'cyborg'
                            cmsg('All invisible now Dont get cought')
                        else:
                            cmsg('alwardy invisible')
                else:
                    body = activity_players[int(n[0])].actor.node
                    is_name = session_players[int(n[0])].getname()
                    if not body.torso_mesh == None:
                        body.head_mesh = None
                        body.torso_mesh = None
                        body.upper_arm_mesh = None
                        body.forearm_mesh = None
                        body.pelvis_mesh = None
                        body.hand_mesh = None
                        body.toes_mesh = None
                        body.upper_leg_mesh = None
                        body.lower_leg_mesh = None
                        body.style = 'cyborg'
                        cmsg(is_name+' using invisiblelity ')
                    else:
                        cmsg('alwardy invisible')

            elif m in [px+'hl', px+'headless']:
                if n == []:
                    cmsg(f'help: {px}spaz all or {px}spaz number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        body = i.actor.node
                        if not body.head_mesh == None:
                            body.head_mesh = None
                            body.style = 'cyborg'
                            cmsg('headless ? xD')
                        else:
                            cmsg('alwardy headless are you really headless?')
                else:
                    body = activity_players[int(n[0])].actor.node
                    is_name = session_players[int(n[0])].getname()
                    if not body.head_mesh == None:
                        body.head_mesh = None
                        body.style = 'cyborg'
                        cmsg(is_name+'is headless now xD')
                    else:
                        cmsg('alwardy headless are you really headless?')

            elif m in [px+'creepy', px+'creep']:
                if n == []:
                    cmsg(f'use: {px}creepy all or {px}creepy number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        body = i.actor.node
                        body.head_mesh = None
                        body.handlemessage(bs.PowerupMessage(poweruptype='punch'))
                        body.handlemessage(bs.PowerupMessage(poweruptype='shield'))
                        cmsg('dont creep out childs all will be scared')
                else:
                    try:
                        body = activity_players[int(n[0])].actor.node
                        body.head_mesh = None
                        body.handlemessage(bs.PowerupMessage(poweruptype='punch'))
                        body.handlemessage(bs.PowerupMessage(poweruptype='shield'))
                        cmsg('dont creep out childs all will be scared')
                    except:
                        cmsg('could not found player to make')

            elif m in [px+'kill', px+'die']:
                if n == []:
                    cmsg(f'Use: {px}kill all or {px}kill number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        i.actor.node.handlemessage(bs.DieMessage())
                        cmsg('Killed all')
                else:
                    is_name = session_players[int(n[0])].getname()
                    activity_players[int(n[0])].actor.node.handlemessage(bs.DieMessage())
                    cmsg('Killed '+is_name)

            elif m in [px+'heal', px+'heath']:
                if n == []:
                    cmsg(f'Use: {px}heal all or {px}heal number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        i.actor.node.handlemessage(bs.PowerupMessage(poweruptype='health'))
                        cmsg('Heald all')
                else:
                    is_name = session_players[int(n[0])].getname()
                    activity_players[int(n[0])].actor.node.handlemessage(
                        bs.PowerupMessage(poweruptype='health'))
                    cmsg('Heald '+is_name)

            elif m in [px+'curse', px+'cur']:
                if n == []:
                    cmsg(f'Use: {px}curse all or {px}curse number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        i.actor.node.handlemessage(bs.PowerupMessage(poweruptype='curse'))
                        cmsg('Cursed all')
                else:
                    is_name = session_players[int(n[0])].getname()
                    activity_players[int(n[0])].actor.node.handlemessage(
                        bs.PowerupMessage(poweruptype='curse'))
                    cmsg('Cursed '+is_name)

            elif m in [px+'sleep']:
                if n == []:
                    cmsg(f'Use: {px}sleep all or {px}sleep number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        i.actor.node.handlemessage('knockout', 8000)
                        cmsg('Sleep all its Night :)')
                else:
                    is_name = session_players[int(n[0])].getname()
                    activity_players[int(n[0])].actor.node.handlemessage('knockout', 8000)
                    cmsg(is_name+' sleeped now')

            elif m in [px+'sp', px+'superpunch']:
                if n == []:
                    cmsg(f'Use: {px}sp/superpunch all or {px}sp/superpunch number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        if not i.actor._punch_power_scale == 15:
                            i.actor._punch_power_scale = 15
                            i.actor._punch_cooldown = 0
                            cmsg('Everyone enjoy your Super punches')
                        else:
                            i.actor._punch_power_scale = 1.2
                            i.actor._punch_cooldown = 400
                            cmsg('Super punches off now')
                else:
                    try:
                        if not activity_players[int(n[0])].actor._punch_power_scale == 15:
                            is_name = session_players[int(n[0])].getname()
                            activity_players[int(n[0])].actor._punch_power_scale = 15
                            activity_players[int(n[0])].actor._punch_cooldown = 0
                            cmsg(is_name+' using super punches get away from him')
                        else:
                            activity_players[int(n[0])].actor._punch_power_scale = 1.2
                            activity_players[int(n[0])].actor._punch_cooldown = 400
                            cmsg(':( ')
                    except:
                        pass

            elif m in [px+'gloves', px+'punch']:
                if n == []:
                    cmsg(f'Use: {px}gloves all or {px}gloves number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        i.actor.node.handlemessage(bs.PowerupMessage(poweruptype='punch'))
                        cmsg('Free Gloves enjoy all')
                else:
                    is_name = session_players[int(n[0])].getname()
                    activity_players[int(n[0])].actor.node.handlemessage(
                        bs.PowerupMessage(poweruptype='punch'))
                    cmsg(is_name+' using gloves')

            elif m in [px+'shield', px+'protect']:
                if n == []:
                    cmsg(f'Use: {px}shield all or {px}shield number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        i.actor.node.handlemessage(bs.PowerupMessage(poweruptype='shield'))
                        cmsg('Everyone enjoy free shield :)')
                else:
                    is_name = session_players[int(n[0])].getname()
                    activity_players[int(n[0])].actor.node.handlemessage(
                        bs.PowerupMessage(poweruptype='shield'))
                    cmsg(is_name+' using shield')

            elif m in [px+'freeze', px+'ice']:
                if n == []:
                    cmsg(f'Use: {px}freeze all or {px}freeze number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        i.actor.node.handlemessage(bs.FreezeMessage())
                        cmsg('Freezed all')
                else:
                    is_name = session_players[int(n[0])].getname()
                    activity_players[int(n[0])].actor.node.handlemessage(bs.FreezeMessage())
                    cmsg('Un freezed '+is_name)

            elif m in [px+'unfreeze', px+'thaw']:
                if n == []:
                    cmsg(f'Use: {px}unfreeze/thaw all or {px}unfreeze/thaw number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        i.actor.node.handlemessage(bs.ThawMessage())
                        cmsg('Un freezed all ')
                else:
                    is_name = session_players[int(n[0])].getname()
                    activity_players[int(n[0])].actor.node.handlemessage(bs.ThawMessage())
                    cmsg('Un freezed '+is_name)

            elif m in [px+'fall']:
                if n == []:
                    cmsg(f'Use: {px}fall all or {px}fall number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        i.actor.node.handlemessage(bs.StandMessage())
                        cmsg('Felt everyone')
                else:
                    is_name = session_players[int(n[0])].getname()
                    activity_players[int(n[0])].actor.node.handlemessage(bs.StandMessage())
                    cmsg(is_name+' got felt')

            elif m in [px+'celebrate', px+'celeb']:
                if n == []:
                    cmsg(f'Use: {px}celebrate all or {px}celebrate number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        i.actor.node.handlemessage(bs.CelebrateMessage())
                        cmsg('Celebrate all :)')
                else:
                    is_name = session_players[int(n[0])].getname()
                    activity_players[int(n[0])].actor.node.handlemessage(bs.CelebrateMessage())
                    cmsg(is_name+' is celebrating bt why?')

            elif m in [px+'fly']:
                if n == []:
                    cmsg(f'Use: {px}fly all or {px}fly number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        if not i.actor.node.fly == True:
                            i.actor.node.fly = True
                            cmsg('fly all dont go out ok')
                        else:
                            i.actor.node.fly = False
                            cmsg('flying mode off')
                else:
                    try:
                        is_name = session_players[int(n[0])].getname()
                        if not activity_players[int(n[0])].actor.node.fly == True:
                            activity_players[int(n[0])].actor.node.fly = True
                            cmsg(is_name+' is flying')
                        else:
                            activity_players[int(n[0])].actor.node.fly = False
                            cmsg('fly off :(')
                    except:
                        cmsg('player not found')
                        pass

            elif m in [px+'gm', px+'godmode']:
                if n == []:
                    cmsg(f'Use: {px}gm all or {px}gm number of list')
                elif n[0] == 'all':
                    for i in activity_players:
                        if not i.actor.node.hockey == True:
                            i.actor.node.hockey = True
                            i.actor.node.invincible = True
                            i.actor._punch_power_scale = 7
                            cmsg('Gmed all ')
                        else:
                            i.actor.node.hockey = False
                            i.actor.node.invincible = False
                            i.actor._punch_power_scale = 1.2
                            cmsg('Un gmed all')
                else:
                    try:
                        is_name = session_players[int(n[0])].getname()
                        if not activity_players[int(n[0])].actor.node.hockey == True:
                            activity_players[int(n[0])].actor.node.hockey = True
                            activity_players[int(n[0])].actor.node.invincible = True
                            activity_players[int(n[0])].actor._punch_power_scale = 7
                            cmsg('Gmed  '+is_name)
                        else:
                            activity_players[int(n[0])].actor.node.hockey = False
                            activity_players[int(n[0])].actor.node.invincible = False
                            activity_players[int(n[0])].actor._punch_power_scale = 1.2
                            cmsg('un gmed  '+is_name)
                    except:
                        cmsg('could not found player')
            elif m in [px+'d_bomb', px+'default_bomb']:
                if n == []:
                    cmsg(
                        f'Use: {px}d_bomb/default_bomb all or {px}d_bomb number of list, type {px}d_bomb help for help')
                elif n[0] == 'help':
                    cmsg("bombtypes - ['ice', 'impact', 'land_mine', 'normal', 'sticky','tnt']")
                elif n[0] in ['ice', 'impact',  'land_mine', 'normal', 'sticky', 'tnt']:
                    for i in activity_players:
                        i.actor.bomb_type = n[0]
                        cmsg('default bomb type - '+str(n[0])+' now')
                else:
                    cmsg('unkwon bombtype , type {px}d_bomb help for help')

            elif m in [px+'d_bomb_count', px+'default_bomb_count', px+'dbc']:
                if n == []:
                    cmsg(
                        f'Use: {px}d_bomb_count/default_bomb/dbc all or {px}d_bomb_count/default_bomb_count/dbc number of list')
                else:
                    try:
                        for i in activity_players:
                            i.actor.set_bomb_count(int(n[0]))
                            cmsg('default bomb count is '+(str(n[0]))+' now')
                    except:
                        cmsg('Must use number to use')
            elif m in [px+'credits']:
                if n == []:
                    cmsg(u'\U0001F95A created by Nazz \U0001F95A')
                    cmsg(u'\U0001F95A Nazz are past/present/future \U0001F95A')
                    cmsg(u'\U0001F95A everything is Nazz \U0001F95A')


class NewMainMenuWindow(mainmenu.MainMenuWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Display chat icon, but if user open/close gather it may disappear
        bui.set_party_icon_always_visible(True)

# bs.timer(0.05, _update, repeat=True)


def same():
    # bs.timer(0.5, _cmds._process_cmd, True)
    _cmds._process_cmd()
# ba_meta export babase.Plugin


class _enableee(babase.Plugin):
    timer = bs.AppTimer(0.5, same, repeat=True)

    def on_app_running(self):
        mainmenu.MainMenuWindow = NewMainMenuWindow
