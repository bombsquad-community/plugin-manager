# ba_meta require api 7
import ba

original_getmodel = ba.getmodel


def get_model_gracefully(model):
    if model is not None:
        return original_getmodel(model)


# ba_meta export plugin
class Main(ba.Plugin):
    def on_app_running(self):
        ba.getmodel = get_model_gracefully
