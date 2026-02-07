#======================== works only if you are host or plugin works on the server created On '2026/02/06'
#========================

# ba_meta require api 9
import bascenev1 as bs
import babase

# ba_meta export babase.Plugin
class ByDrap(bs.Plugin):
    def __init__(self):
        self.container = None
        self.timer = None

    def on_app_running(self):
        self.timer = bs.AppTimer(1.0, bs.WeakCall(self._update_list), repeat=True)

    def has_settings_ui(self):
        return True

    def show_settings_ui(self, source_widget):
        babase.screenmessage("You tapped my settings!")

    def _update_list(self):
        activity = bs.get_foreground_host_activity()
        
        if activity is None:
            if self.container:
                self.container.delete()
                self.container = None
            return

        player_names = []
        for p in activity.players:
            name = p.getname(full=True)
            player_names.append(f" • {name}")
        
        header = "┏━━━━ Players  ━━━━┓\n\n"
        footer = "\n\n┗━━━━━━━━━━━━━━━┛"
        players_str = "\n".join(player_names) if player_names else "  Wait for players..."
        final_text = header + players_str + footer

        with activity.context:
            if self.container is None or not self.container.exists():
                self.container = bs.newnode('text',
                    attrs={
                        'text': final_text,
                        'scale': 0.7,
                        'color': (0.5, 1.0, 0.5),
                        'h_attach': 'right',
                        'v_attach': 'top',
                        'h_align': 'left',
                        'v_align': 'top',
                        'position': (-220, -100),
                        'flatness': 0.0,
                        'shadow': 1.0,
                        'res_scale': 1.5
                    })
            else:
                self.container.text = final_text
