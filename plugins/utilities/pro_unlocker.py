# ba_meta require api 8
import bascenev1 as bs
import _baplus
import babase


def is_game_version_lower_than(version):
    """
    Returns a boolean value indicating whether the current game
    version is lower than the passed version. Useful for addressing
    any breaking changes within game versions.
    """
    game_version = tuple(map(int, babase.app.version.split(".")))
    version = tuple(map(int, version.split(".")))
    return game_version < version


if is_game_version_lower_than("1.7.20"):
    original_get_purchased = _baplus.get_purchased
else:
    assert bs.app.plus is not None
    original_get_purchased = bs.app.plus.get_purchased


def get_purchased(item):
    if item.startswith('characters.') or item.startswith('icons.'):
        return original_get_purchased(item)
    return True


# ba_meta export plugin
class Unlock(babase.Plugin):
    def on_app_running(self):
        babase.app.classic.accounts.have_pro = lambda: True
        if is_game_version_lower_than("1.7.20"):
            _baplus.get_purchased = get_purchased
        else:
            assert bs.app.plus is not None
            bs.app.plus.get_purchased = get_purchased
