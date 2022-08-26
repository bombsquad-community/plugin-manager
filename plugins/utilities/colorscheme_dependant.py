# ba_meta require api 7
import ba
import colorscheme

# ba_meta export plugin
class Main(ba.Plugin):
    def on_plugin_manager_prompt(self):
        ba.screenmessage("we're good if u see the colorscheme window!")
        colorscheme.launch_colorscheme_selection_window()
