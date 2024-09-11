# BY Yelllow (dis : @y.lw)

import babase
import bauiv1 as bui
import bascenev1 as bs

ACHIEVEMENTS = bui.app.classic.ach.achievements


def unlock_all_achievements():
    if bui.app.plus.get_v1_account_state() != 'signed_in':
        return bui.screenmessage(bui.Lstr(resource='notSignedInErrorText'), color=(1, 0, 0))

    UNLOCKED = False
    for num, achievement in enumerate(ACHIEVEMENTS, start=1):
        if not achievement.complete:
            bui.app.plus.add_v1_account_transaction(
                {'type': 'ACHIEVEMENT', 'name': achievement.name})
            achievement.set_complete()
            bui.screenmessage(f"- Unlocked ({achievement.name})", color=(1, 1, 0))
            UNLOCKED = True

    if UNLOCKED:
        bui.screenmessage("Unlocked All Achievements !", color=(0, 1, 0))


def _have_pro():
    return True

# ba_meta require api 8
# ba_meta export plugin


class ByYelllow(babase.Plugin):
    def on_app_running(self) -> None:
        bs.app.classic.accounts.have_pro = _have_pro
        self.timer = bs.AppTimer(5, unlock_all_achievements)
