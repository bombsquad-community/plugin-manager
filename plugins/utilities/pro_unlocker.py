# ba_meta require api 7
import _ba
import ba


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
    original_get_purchased = _ba.get_purchased
else:
    original_get_purchased = ba.internal.get_purchased


def get_purchased(item):
    if item.startswith('characters.') or item.startswith('icons.'):
        return original_get_purchased(item)
    return True


# ba_meta export plugin
class Unlock(ba.Plugin):
    def on_app_running(self):
        ba.app.accounts_v1.have_pro = lambda: True
        if is_game_version_lower_than("1.7.7"):
            _ba.get_purchased = get_purchased
        else:
            ba.internal.get_purchased = get_purchased
