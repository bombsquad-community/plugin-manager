# ba_meta require api 9
# crafted by brostos
#! Fix bug when the previous message is "hello" it will not trigger the wave emote on new round or game
import time

import babase
import bascenev1 as bs

last_len_msg = 0  # Initialize the global variable outside the function


def wave_emote():
    global last_len_msg  # To modify the global variable

    # Check if the players are in game first
    try:
        act_players = bs.get_foreground_host_activity().players
        if not act_players:
            return
    except AttributeError:
        # Except the attribute error if the player is in a server
        return

    # Incase chats are empty or in replay
    try:
        lastmsg = bs.get_chat_messages()[-1]
    except:
        return

    # Perform a check to see if the player is playing|spectating
    for player in act_players:
        try:
            if player.actor.node:
                continue
        except:
            return

    # Check if the message contains "hello"
    if len(bs.get_chat_messages()) != last_len_msg:
        if act_players and "hello" in lastmsg:
            for player in act_players:
                if player.getname() in lastmsg:
                    # Trigger the wave emote
                    player.actor.node.handlemessage("celebrate_r", 1000)

                    last_len_msg = len(bs.get_chat_messages())
                    print(last_len_msg, "last_len_msg")

# ba_meta export babase.Plugin


class brostos(babase.Plugin):
    timer = bs.AppTimer(0.5, wave_emote, repeat=True)
