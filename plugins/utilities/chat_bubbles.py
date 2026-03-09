# ba_meta require api 9
# This plugin only works with BombSquad 1.7.49+
from __future__ import annotations

from typing import TYPE_CHECKING, override

import babase
import bascenev1 as bs
import random
import string
import unicodedata

if TYPE_CHECKING:
    from typing import Any

plugman = dict(
    plugin_name="chat_bubbles",
    description="Adds whatever the players say above their character, includes a few other features too!",
    external_url="",
    authors=[
        {"name": "DinoWattz", "email": "", "discord": ""}
    ],
    version="1.0.0",
)

# Prints chat messages to the console as "[Character's Name] Player 1/Player 2: Hello World!"
PRINT_CHAT_MESSAGES = True
BUBBLE_DURATION: float = 4.7  # 4.7 matches the default onscreen message duration
SPEAK_VOLUME = 1.5
SHOUT_VOLUME = 3.0

CELEBRATE_MESSAGE = [(bs.CelebrateMessage, {"duration": 1.0})]

# Easter egg triggers, sounds, and messages flag
# If adding new ones, make sure to test them in-game
EASTER_EGGS = [
    {
        "triggers": {
            "hi", "hello", "hey", "hiya", "yo", "sup", "heya", "howdy",
            "greetings", "salutations", "ahoy", "ahoyhoy", "bonjour",
            "hola", "ciao", "ola", "oi", "eae", "salve",
                    "bye", "goodbye", "see ya", "see you", "cya",
                    "adios", "chau", "chao", "tchau",
                    "adeus", "ate mais", "falou", "flw"
        },
        "node_messages": [("celebrate_r", 1000)],
    },
    {
        "triggers": {"aaa"},
        "sound": "spazFall01",
        "messages": CELEBRATE_MESSAGE,
    },
    {
        "triggers": {"aaaa"},
        "sound": "zoeFall01",
        "messages": CELEBRATE_MESSAGE,
    },
    {
        "triggers": {"aaaaa"},
        "sound": "kronkFall",
        "messages": CELEBRATE_MESSAGE,
    },
    {
        "triggers": {"potato"},
        "sound": "kronk2",
        "messages": CELEBRATE_MESSAGE,
    },
    {
        "triggers": {"dau", "tau", "d'oh", "doh"},
        "sound": "kronk3",
        "messages": CELEBRATE_MESSAGE,
    },
    {
        "triggers": {"drau", "trau", "d'roh", "droh"},
        "sound": "bunny2",
        "messages": CELEBRATE_MESSAGE,
    },
    {
        "triggers": {"hahaha", "hahahaha",
                     "hahahah", "hahahahah", "lol",
                     "nahahah", "kakaka", "kakakaka", "kkk", "kkkk",
                     "jajaja", "jajajaja", "jajajajaa"},
        "sound": "mel05",
        "messages": CELEBRATE_MESSAGE,
    },
    {
        "triggers": {"ha", "hah", "ja", "ka"},
        "sound": "mel06",
        "messages": CELEBRATE_MESSAGE,
    },
    {
        "triggers": {"merry christmas", "merry krismas", "merry xmas", "feliz natal", "feliz navidad"},
        "sound": "santa02",
        "messages": CELEBRATE_MESSAGE,
    },
    {
        "triggers": {"hohoho", "ho ho ho", "ho-ho-ho"},
        "sound": "santa05",
        "messages": CELEBRATE_MESSAGE,
    },
    {
        "triggers": {"gg", "good game", "que pro", "q pro"},
        "sound": "achievement",
        "messages": CELEBRATE_MESSAGE,
    },
    {
        "triggers": {"boo", "bad game", "que noob", "q noob"},
        "sound": "boo",
        "messages": CELEBRATE_MESSAGE,
    },
    # ↓ Node messages are like this ↓
    {
        "triggers": {"0", "zero"},
        "sound": "boxingBell",
        "node_messages": [("celebrate_l", 1000)],
    },
    {
        "triggers": {"1", "one"},
        "sound": "announceOne",
        "node_messages": [("celebrate_r", 1000)],
    },
    {
        "triggers": {"2", "two"},
        "sound": "announceTwo",
        "node_messages": [("celebrate_r", 1000)],
    },
    {
        "triggers": {"3", "three"},
        "sound": "announceThree",
        "node_messages": [("celebrate_r", 1000)],
    },
    {
        "triggers": {"4", "four"},
        "sound": "announceFour",
        "node_messages": [("celebrate_r", 1000)],
    },
    {
        "triggers": {"5", "five"},
        "sound": "announceFive",
        "node_messages": [("celebrate_r", 1000)],
    },
    {
        "triggers": {"6", "six"},
        "sound": "announceSix",
        "node_messages": [("celebrate_r", 1000)],
    },
    {
        "triggers": {"7", "seven"},
        "sound": "announceSeven",
        "node_messages": [("celebrate_r", 1000)],
    },
    {
        "triggers": {"8", "eight"},
        "sound": "announceEight",
        "node_messages": [("celebrate_r", 1000)],
    },
    {
        "triggers": {"9", "nine"},
        "sound": "announceNine",
        "node_messages": [("celebrate_r", 1000)],
    },
    {
        "triggers": {"10", "ten"},
        "sound": "announceTen",
        "node_messages": [("celebrate_r", 1000)],
    },
    {
        "triggers": {"xd"},
        "sound": "santaDeath",
        "node_messages": [("knockout", 100)],
    },
    # ↓ Easter eggs without actor/node messages ↓
    {
        "triggers": {"huh", "huhh", "huhhh", "huhhhh", "humph", "hmph", "hum", "humm"},
        "sound": "agent1",
    },
    {
        "triggers": {"hoh", "hohh", "hohhh", "hohhhh", "ohh"},
        "sound": "agent3",
    },
    {
        "triggers": {"eff"},
        "sound": "zoeEff",
    },
    {
        "triggers": {"ow", "oww", "oow"},
        "sound": "zoeOw",
    },
    {
        "triggers": {"pipipi", "bibibi"},
        "sound": "mel07",
    },
    {
        "triggers": {"oh yeah", "oh yea", "oohh yeah", "oohh yea"},
        "sound": "yeah",
    },
    {
        "triggers": {"woo"},
        "sound": "woo2",
    },
    {
        "triggers": {"wooo"},
        "sound": "woo",
    },
    {
        "triggers": {"woo yeah", "woo yea"},
        "sound": "woo3",
    },
    {
        "triggers": {"ooh"},
        "sound": "ooh",
    },
    {
        "triggers": {"wow"},
        "sound": "wow",
    },
    {
        "triggers": {"gasp"},
        "sound": "gasp",
    },
    {
        "triggers": {"ahh", "aah"},
        "sound": "aww",
    },
    {
        "triggers": {"nice"},
        "sound": "nice",
    },
    # ↑ Default easter egg list ends here ↑
]

# Chat bubble functionality


def create_bubble(player: bs.SessionPlayer, text: str, name: str):
    msg = normalize_message(text)
    is_caps = len(text) > 1 and text.isupper()
    handled = False
    bubble_created = False

    activityplayer: bs.Player | None = getattr(player, 'activityplayer', None)

    def _fallback_logic():
        nonlocal handled, activityplayer
        color = (1, 1, 0.4)
        image_icon = {'texture': bs.gettexture("cuteSpaz"), 'tint_texture': bs.gettexture(
            "cuteSpaz"), 'tint_color': (1.0, 1.0, 1.0), 'tint2_color': (1.0, 1.0, 1.0)}

        if activityplayer:
            normal_highlight = bs.normalized_color(
                bs.safecolor(player.highlight, target_intensity=1.15))
            saturated_highlight = bs.normalized_color(
                bs.safecolor(player.highlight, target_intensity=0.75))
            color = saturated_highlight if is_caps else normal_highlight
            image_icon = activityplayer.get_icon()

        bs.broadcastmessage(f"{name}: {text}",
                            color=color,
                            top=True,
                            image=image_icon)

        for egg in EASTER_EGGS:
            if msg in egg["triggers"]:
                if egg.get("sound"):
                    sound = bs.getsound(egg["sound"])
                    sound.play(SHOUT_VOLUME if is_caps else SPEAK_VOLUME)
                    handled = True
                    break
        if not handled and activityplayer:
            assert bs.app.classic is not None
            handled = True
            character = activityplayer.character
            char = bs.app.classic.spaz_appearances[character]
            if is_caps:
                attack_sounds = [bs.getsound(s) for s in char.attack_sounds]
                if attack_sounds and isinstance(attack_sounds, (list, tuple)) and len(attack_sounds) > 0:
                    sound = random.choice(attack_sounds)
                    sound.play(SHOUT_VOLUME)
            else:
                pickup_sounds = [bs.getsound(s) for s in char.pickup_sounds]
                if pickup_sounds and isinstance(pickup_sounds, (list, tuple)) and len(pickup_sounds) > 0:
                    sound = random.choice(pickup_sounds)
                    sound.play(SPEAK_VOLUME)

    if activityplayer is None:
        # No valid activityplayer: play sound if possible (lobby/non-in-game)
        _fallback_logic()
        return

    bubbles = activityplayer.customdata.setdefault('chat_bubbles', [])
    actor_list = []

    # Support for both actor and ghost_actor (from the Ghost Players plugin)
    if getattr(activityplayer, 'actor', None):
        actor_list.append(activityplayer.actor)
    if hasattr(activityplayer, 'customdata') and activityplayer.customdata.get('ghost_actor'):
        actor_list.append(activityplayer.customdata['ghost_actor'])

    if actor_list:
        for actor in actor_list:
            if actor and actor.is_alive() and actor.node:
                assert actor is not None
                char_node = actor.node
                activity = actor.getactivity()
                if activity is None or getattr(activity, 'expired', False):
                    continue

                with activity.context:
                    # Calculate scale based on text length
                    base_scale = 0.015
                    min_scale = 0.009
                    scale = max(base_scale - 0.0003 * max(len(text) - 20, 0), min_scale)
                    y_offset = 1.2 + 0.25 * len(bubbles)

                    mnode = bs.newnode('math', owner=char_node, attrs={
                        'input1': (0, y_offset, 0),
                        'operation': 'add'
                    })
                    char_node.connectattr('torso_position', mnode, 'input2')

                    normal_highlight = bs.normalized_color(
                        bs.safecolor(player.highlight, target_intensity=1.15))
                    saturated_highlight = bs.normalized_color(
                        bs.safecolor(player.highlight, target_intensity=0.75))
                    bubble_color = saturated_highlight if is_caps else normal_highlight

                    textnode = bs.newnode('text',
                                          owner=char_node,
                                          attrs={
                                              'text': text,
                                              'color': bubble_color,
                                              'shadow': 0.5,
                                              'flatness': 0.5,
                                              'scale': scale,
                                              'h_align': 'center',
                                              'v_align': 'bottom',
                                              'in_world': True,
                                              'opacity': 1.0,
                                          })

                    mnode.connectattr('output', textnode, 'position')

                    focus = Plugin.Focus(owner=textnode).autoretain()
                    textnode.connectattr('position', focus.node, 'position')

                    # Adjust bubble duration for slow-motion activities
                    bubble_duration = BUBBLE_DURATION
                    if hasattr(activity, 'slow_motion') and activity.slow_motion:
                        bubble_duration = max(0.5, bubble_duration / 3)

                    # Play sound for all triggers (easter eggs and normal)
                    def _play_chat_sound(actor, sound, volume):
                        if actor.is_alive():
                            actor._safe_play_sound(sound, volume)
                        else:
                            sound.play(volume)

                    # Easter egg sound/message
                    for egg in EASTER_EGGS:
                        if msg in egg['triggers']:
                            # Sound selection logic
                            sound = None
                            if egg.get('sound'):
                                sound = bs.getsound(egg['sound'])
                            else:
                                # Default to character sounds if no specific sound is set
                                if is_caps:
                                    attack_sounds = getattr(char_node, 'attack_sounds', None)
                                    if attack_sounds and isinstance(attack_sounds, (list, tuple)) and len(attack_sounds) > 0:
                                        sound = random.choice(attack_sounds)
                                else:
                                    pickup_sounds = getattr(char_node, 'pickup_sounds', None)
                                    if pickup_sounds and isinstance(pickup_sounds, (list, tuple)) and len(pickup_sounds) > 0:
                                        sound = random.choice(pickup_sounds)

                            if sound:
                                _play_chat_sound(
                                    actor, sound, SHOUT_VOLUME if is_caps else SPEAK_VOLUME)

                            # Animation logic
                            if egg.get('messages') and actor.is_alive() and hasattr(actor, 'handlemessage'):
                                for msg_class, msg_kwargs in egg.get('messages', []):
                                    msg_kwargs = msg_kwargs or {}
                                    actor.handlemessage(msg_class(**msg_kwargs))

                            if egg.get('node_messages') and actor.is_alive() and actor.node.exists():
                                for node_args in egg.get('node_messages', []):
                                    actor.node.handlemessage(*node_args)

                            handled = True
                            break

                    if not handled:
                        if is_caps:
                            attack_sounds = getattr(char_node, 'attack_sounds', None)
                            if attack_sounds and isinstance(attack_sounds, (list, tuple)) and len(attack_sounds) > 0:
                                sound = random.choice(attack_sounds)
                                _play_chat_sound(actor, sound, SHOUT_VOLUME)
                            if actor.is_alive() and hasattr(actor, 'handlemessage'):
                                actor.handlemessage(bs.CelebrateMessage(duration=1.0))
                        else:
                            pickup_sounds = getattr(char_node, 'pickup_sounds', None)
                            if pickup_sounds and isinstance(pickup_sounds, (list, tuple)) and len(pickup_sounds) > 0:
                                sound = random.choice(pickup_sounds)
                                _play_chat_sound(actor, sound, SPEAK_VOLUME)

                    bubbles.append((textnode, mnode))
                    bubble_created = True
                    while len(bubbles) > 3:
                        old_textnode, old_mnode = bubbles.pop(0)
                        if old_textnode is not None and hasattr(old_textnode, 'exists') and old_textnode.exists():
                            old_textnode.delete()
                        if old_mnode is not None and hasattr(old_mnode, 'exists') and old_mnode.exists():
                            old_mnode.delete()
                    update_bubble_offsets(bubbles)

                    fade_time = max(0.1, bubble_duration - 0.5)
                    bs.animate(textnode, 'opacity', {fade_time: 1.0, bubble_duration: 0.0})
                    bs.timer(bubble_duration, textnode.delete)
                    bs.timer(bubble_duration, mnode.delete)

                    def cleanup():
                        if hasattr(activityplayer, 'customdata'):
                            if 'chat_bubbles' in activityplayer.customdata:
                                activityplayer.customdata['chat_bubbles'] = [
                                    b for b in activityplayer.customdata['chat_bubbles'] if b[0] != textnode
                                ]
                    bs.timer(bubble_duration, cleanup)

    if not bubble_created:
        # No valid actor found: play sound if possible
        _fallback_logic()
        return


def update_bubble_offsets(bubbles):
    for i, (tnode, mnode) in enumerate(reversed(bubbles)):
        y_offset = 1.2 + 0.25 * i
        if mnode is not None and hasattr(mnode, 'exists') and mnode.exists():
            mnode.input1 = (0, y_offset, 0)

# Tools


def normalize_message(text):
    msg = text.strip().lower()
    msg = msg.translate(str.maketrans('', '', string.punctuation))
    msg = ''.join(
        c for c in unicodedata.normalize('NFD', msg)
        if unicodedata.category(c) != 'Mn'
    )

    return msg

# ba_meta export babase.Plugin


class Plugin(babase.Plugin):
    def on_app_running(self) -> None:
        # Hook into chat message filtering
        # We're delaying until the app runs and using a timer so it's more likely to work with other chat plugins (please don't make a chat plugin/filter that is delayed like this).
        bs.apptimer(0.001, bs.WeakCallStrict(self.apply_patch))

    def apply_patch(self):
        import bascenev1._hooks as _hooks

        _org_filter_chat_message = _hooks.filter_chat_message

        def _chat_bubbles_hook(msg: str, client_id: int, *args, **kwargs) -> str | None:
            org_msg = _org_filter_chat_message(msg, client_id, *args, **kwargs)

            if org_msg is None:
                # The original message has been ignored, so we should ignore it as well
                return org_msg

            # Chat bubble sorcery
            try:
                roster = bs.get_game_roster()
                session = bs.get_foreground_host_session()
                if session is None:
                    # Probably couldn't find a session because we are a client
                    return org_msg
                sessionplayers = session.sessionplayers

                player_list = []
                matched = False
                dead_bubble = False
                character: str | None = None

                with session.context:
                    for player in sessionplayers:
                        if player.inputdevice.client_id == client_id and player.in_game:
                            player_list.append(player)
                            continue
                    if player_list:
                        # Get combined name for multiple players on same client
                        name = ''
                        created_bubble = False

                        for player in player_list:
                            if name == '':
                                name = player.getname()
                            else:
                                name = name + '/' + player.getname()

                        # Create chat bubble
                        for player in player_list:
                            activityplayer: bs.Player = player.activityplayer
                            # We have a session player but not an activity player
                            if not activityplayer:
                                if not dead_bubble:
                                    create_bubble(player, org_msg, name)
                                    created_bubble = dead_bubble = True
                                continue
                            # We have a dead activity player
                            if not activityplayer.is_alive() and not dead_bubble:
                                create_bubble(player, org_msg, name)
                                created_bubble = dead_bubble = True
                                character = activityplayer.character if character is None else character
                            # elif we have an alive activity player
                            elif activityplayer.is_alive():
                                create_bubble(player, org_msg, name)
                                created_bubble = True
                                character = activityplayer.character if character is None else character

                        if created_bubble:
                            matched = True
                            if PRINT_CHAT_MESSAGES:
                                print(f"[{character}] {name}: {org_msg}")
                        else:
                            bs.logging.warning(
                                "Failed to create a chat bubble, using non-session player method now.")
                    # Non-session players (in lobby or just spectating, this only works for servers)
                    if not matched and not dead_bubble:
                        for client in roster:
                            if client['client_id'] == client_id:
                                name = client.get('display_string')
                                create_bubble(None, org_msg, name)

                                matched = True
                                if PRINT_CHAT_MESSAGES:
                                    print(f"[{character}] {name}: {org_msg}")
                                break
            except Exception as e:
                bs.logging.exception(f"Error in chat bubble hook: {e}")

            return org_msg

        _hooks.filter_chat_message = _chat_bubbles_hook
        bs.reload_hooks()

        print("[ChatBubbles] Plugin initialized.")

    class Focus(bs.Actor):
        def __init__(
            self,
            *,
            owner: bs.Node | None = None,
        ):
            super().__init__()

            self._focusnode_material = bs.Material()
            self._focusnode_material.add_actions(
                actions=('modify_node_collision', 'collide', False),
            )

            if getattr(owner, 'owner', None):
                assert owner is not None
                area_of_interest = False if getattr(
                    owner.owner, 'is_area_of_interest', False) else True
            else:
                area_of_interest = False if getattr(owner, 'is_area_of_interest', False) else True

            # I'm tired of this area_of_interest nonsense, it never works right
            # area_of_interest = False
            # actually it might work now that we don't spawn bubbles for dead players.

            self.node = bs.newnode(
                'prop',
                delegate=self,
                owner=owner,
                attrs={
                    'body': 'sphere',
                            'body_scale': 0.0,
                            'shadow_size': 0.0,
                            'gravity_scale': 0.0,
                            'is_area_of_interest': area_of_interest,
                            'materials': (self._focusnode_material,),
                },
            )

        @override
        def handlemessage(self, msg: Any) -> Any:
            assert not self.expired
            if isinstance(msg, bs.DieMessage):
                if self.node:
                    self.node.delete()
            else:
                super().handlemessage(msg)
