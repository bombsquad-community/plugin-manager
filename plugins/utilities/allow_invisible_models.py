# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 9
import babase
import bascenev1 as bs

original_getmesh = bs.getmesh


def get_mesh_gracefully(mesh):
    if mesh is not None:
        return original_getmesh(mesh)


# ba_meta export plugin
class Main(babase.Plugin):
    def on_app_running(self):
        bs.getmesh = get_mesh_gracefully
