# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
TopMsg v1.1.2 - Chat top right

When chat is muted, shows chat messages top right.
Prevents spam and flooding screen.
Does not repeat messages.
"""

from babase import app, Plugin
from bascenev1 import (
    get_chat_messages as gcm,
    broadcastmessage as push,
    apptimer as z
)

# ba_meta require api 9
# ba_meta export babase.Plugin


class byBordd(Plugin):
    def __init__(s): return (setattr(s, 'la', None), z(5, s.ear))[1]

    def ear(s):
        a = gcm()
        if a and s.la != a[-1]:
            if app.config.resolve('Chat Muted'):
                push(a[-1], (1, 1, 1), True)
            s.la = a[-1]
        z(0.1, s.ear)
