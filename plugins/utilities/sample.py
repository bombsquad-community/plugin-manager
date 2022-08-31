# ba_meta require api 7
import ba


# ba_meta export plugin
class Main(ba.Plugin):
    def on_app_running(self):
        ba.screenmessage("go to sleep zz")
