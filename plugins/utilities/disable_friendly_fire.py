# ba_meta require api 9
from __future__ import annotations
from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
import bascenev1lib
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    pass


class BombPickupMessage:
    """ message says that someone pick up the dropped bomb """


# for bs.FreezeMessage
freeze: bool = True

# ba_meta export babase.Plugin


class Plugin(babase.Plugin):

    # there are two ways to ignore our team player hits
    # either change playerspaz handlemessage or change spaz handlemessage
    def playerspaz_new_handlemessage(func: fuction) -> fuction:
        def wrapper(*args, **kwargs):
            global freeze

            # only run if session is dual team
            if isinstance(args[0].activity.session, bs.DualTeamSession):
                # when spaz got hurt by any reason this statement is runs.
                if isinstance(args[1], bs.HitMessage):
                    our_team_players: list[type(args[0]._player)]

                    # source_player
                    attacker = args[1].get_source_player(type(args[0]._player))

                    # our team payers
                    our_team_players = args[0]._player.team.players.copy()

                    if len(our_team_players) > 0:

                        # removing our self
                        our_team_players.remove(args[0]._player)

                        # if we honding teammate or if we have a shield,  do hit.
                        for player in our_team_players:
                            if player.actor.exists() and args[0]._player.actor.exists():
                                if args[0]._player.actor.node.hold_node == player.actor.node or args[0]._player.actor.shield:
                                    our_team_players.remove(player)
                                    break

                        if attacker in our_team_players:
                            freeze = False
                            return None
                        else:
                            freeze = True

                # if ice_bomb blast hits any spaz this statement runs.
                elif isinstance(args[1], bs.FreezeMessage):
                    if not freeze:
                        freeze = True  # use it and reset it
                        return None

            # orignal unchanged code goes here
            func(*args, **kwargs)

        return wrapper

    # replace original fuction to modified function
    bascenev1lib.actor.playerspaz.PlayerSpaz.handlemessage = playerspaz_new_handlemessage(
        bascenev1lib.actor.playerspaz.PlayerSpaz.handlemessage)

    # let's add a message when bomb is pick by player
    def bombfact_new_init(func: function) -> function:
        def wrapper(*args):

            func(*args)  # original code

            args[0].bomb_material.add_actions(
                conditions=('they_have_material', SharedObjects.get().pickup_material),
                actions=('message', 'our_node', 'at_connect', BombPickupMessage()),
            )
        return wrapper

    # you get the idea
    bascenev1lib.actor.bomb.BombFactory.__init__ = bombfact_new_init(
        bascenev1lib.actor.bomb.BombFactory.__init__)

    def bomb_new_handlemessage(func: function) -> function:
        def wrapper(*args, **kwargs):
            # only run if session is dual team
            if isinstance(args[0].activity.session, bs.DualTeamSession):
                if isinstance(args[1], BombPickupMessage):
                    # get the pickuper and assign the pickuper to the source_player(attacker) of bomb blast
                    for player in args[0].activity.players:
                        if player.actor.exists():
                            if player.actor.node.hold_node == args[0].node:
                                args[0]._source_player = player
                                break

            func(*args, **kwargs)  # original

        return wrapper

    bascenev1lib.actor.bomb.Bomb.handlemessage = bomb_new_handlemessage(
        bascenev1lib.actor.bomb.Bomb.handlemessage)
