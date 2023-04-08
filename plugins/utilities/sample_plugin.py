# ba_meta require api 7

import ba

# ba_meta export plugin

class Main(ba.Plugin):

    def on_app_running(self):

        ba.screenmessage("Hi! I am a sample plugin!")

    def has_settings_ui(self):

        return True

    def show_settings_ui(self, source_widget):

        ba.screenmessage("You tapped my settings!")
