# ba_meta require api 9
from __future__ import annotations

import babase
import bascenev1 as bs

from bascenev1lib.actor.spaz import Spaz

plugman = dict(
    plugin_name="sleep_on_afk",
    description="Staying idle for 40 seconds will make your character fall asleep, they need rest too..",
    external_url="",
    authors=[
        {"name": "DinoWattz", "email": "", "discord": ""}
    ],
    version="1.0.0",
)

INGAME_TIME = 40  # (in seconds)

# Spaz Changes


def _afk_sleep_knockout(self, value: float) -> None:
    if not self.node:
        return
    if not self.is_alive() and hasattr(self.getplayer(self), 'sessionplayer'):
        current_activity = self.getactivity()
        player = self.getplayer(self).sessionplayer
        # Pop timer data if the player is dead
        if current_activity.customdata.get(str(player.id) + '_knockoutTimer') is not None:
            current_activity.customdata.pop(str(player.id) + '_knockoutTimer')
            return

    self.node.handlemessage('knockout', value)


Spaz._afk_sleep_knockout = _afk_sleep_knockout  # type: ignore

# Idle Checker


def idle_start(activity: bs.Activity):
    activity.customdata['afk_timer'] = bs.Timer(
        0.5, bs.CallStrict(idle_check, activity), repeat=True)


def idle_check(current_activity: bs.Activity):
    current_session = current_activity.session
    wait_time = INGAME_TIME if not current_activity.slow_motion else round(INGAME_TIME / 3)
    current = bs.time() * 1000
    if not current_session:
        return
    for player in current_session.sessionplayers:
        if (
            not player.exists()
            or not player.in_game
            or not getattr(player, 'activityplayer', None)
            or not getattr(player.activityplayer, 'actor', None)
            or not getattr(player.activityplayer.actor, 'node', None)
            or not player.activityplayer.is_alive()
            or not player.activityplayer.actor.node
            or not player.activityplayer.actor.node.exists()
            and not getattr(player.activityplayer.actor.node, 'invincible', False)
        ):
            continue

        player_actor = player.activityplayer.actor
        player_node = player_actor.node
        player_data = player.activityplayer.customdata
        player_turbo_times = player_actor._turbo_filter_times

        if player_node.move_up_down != 0.0 or player_node.move_left_right != 0.0:
            player_data['last_input'] = current
        elif player_turbo_times:
            highest_turbo_time = player_turbo_times.get(
                max(player_turbo_times, key=player_turbo_times.get))
            if highest_turbo_time > player_data.get('last_input', current):
                player_data.update({'last_input': highest_turbo_time})
        player_data['last_input'] = player_data.get('last_input', current)

        last_input = max(0, player_data['last_input'])
        afk_time = int((current - last_input) / 1000)

        # print(player_data)
        # print(last_input)
        # print(current)
        # print(player.getname() + ": " + str(afk_time))
        # print(wait_time)

        if afk_time >= wait_time:
            current_activity.customdata[str(player.id) + '_knockoutTimer'] = bs.Timer(
                0.1, bs.WeakCallStrict(player_actor._afk_sleep_knockout, 100.0), repeat=True)

            # Make the player's node not an area of interest if it was one
            if not getattr(player_actor, '_previous_is_area_of_interest', False):
                player_actor._previous_is_area_of_interest = player_node.is_area_of_interest

            if player_actor._previous_is_area_of_interest:
                player_node.is_area_of_interest = False

        elif current_activity.customdata.get(str(player.id) + '_knockoutTimer') is not None:
            current_activity.customdata.pop(str(player.id) + '_knockoutTimer')

            # Restore the player's node area of interest if necessary
            if getattr(player_actor, '_previous_is_area_of_interest', False):
                player_node.is_area_of_interest = True

            if hasattr(player_actor, "_previous_is_area_of_interest"):
                delattr(player_actor, "_previous_is_area_of_interest")


# Setup new activity
org_on_begin = bs.Activity.on_begin


def patched_on_begin(self, *args, **kwargs):
    idle_start(self)

    return org_on_begin(self, *args, **kwargs)


bs.Activity.on_begin = patched_on_begin

# ba_meta export babase.Plugin


class Plugin(babase.Plugin):
    pass
