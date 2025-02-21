# ba_meta require api 8
import bascenev1 as bs
import _baplus
import babase


original_get_purchased = _baplus.get_purchased


def get_purchased(item):
    if item.startswith('characters.') or item.startswith('icons.'):
        return original_get_purchased(item)
    return True


# ba_meta export plugin
class Unlock(babase.Plugin):
    def on_app_running(self):
        babase.app.classic.accounts.have_pro = lambda: True
        _baplus.get_purchased = get_purchased
