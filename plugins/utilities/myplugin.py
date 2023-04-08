# Tell the app which of its api versions we are written for. The app's
# meta-scanner will skip this file if this number doesn't match theirs.
# To learn more, see https://ballistica.net/wiki/meta-tag-system
# ba_meta require api 7

import ba

# Tell the app about our Plugin.
# ba_meta export plugin

class MyPlugin(ba.Plugin):
    """My awesome plugin."""

    def on_app_running(self) -> None:
        ba.screenmessage('Hello From MyPlugin!!!')

    