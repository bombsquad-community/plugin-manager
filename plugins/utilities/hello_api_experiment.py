# ba_meta require api 8
import ba

# ba_meta export plugin


class Main(ba.Plugin):
    def on_app_running(self):
        ba.screenmessage("Wohoo! I'm an API 8 plugin!")
