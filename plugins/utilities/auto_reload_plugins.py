# ba_meta require api 8
import babase
import bauiv1 as bui
import os
import asyncio

EVENT_LOOP = babase._asyncio._asyncio_event_loop


async def get_details_for_active_plugins(ignored_plugins=[]):
    plugins_directory = babase.app.env.python_directory_user
    plugins = {}
    for plugin in babase.app.plugins.active_plugins:
        plugin_name = f"{plugin.__module__}.py"
        entry_point = f"{plugin.__module__}.{plugin.__class__.__name__}"
        plugin_path = os.path.join(plugins_directory, plugin_name)
        if os.path.exists(plugin_path) and plugin_name not in ignored_plugins:
            if plugin_name not in plugins:
                plugins[plugin_name] = {
                    "last_modified_time": os.path.getmtime(plugin_path),
                    "entry_points": [],
                }
                plugins[plugin_name]["entry_points"].append(entry_point)
    return plugins


async def reload_plugin(entry_point):
    plugin_class = babase._general.getclass(entry_point, babase.Plugin)
    loaded_plugin_instance = plugin_class()
    loaded_plugin_instance.on_app_running()

    plugin_spec = babase.PluginSpec(class_path=entry_point, loadable=True)
    plugin_spec.enabled = True
    plugin_spec.plugin = loaded_plugin_instance
    bui.app.plugins.plugin_specs[entry_point] = plugin_spec

    plugin_to_remove_from_active_plugins = None
    for plugin in bui.app.plugins.active_plugins:
        existing_entry_point = f"{plugin.__module__}.{plugin.__class__.__name__}"
        if existing_entry_point == entry_point:
            plugin_to_remove_from_active_plugins = plugin
            break

    if plugin_to_remove_from_active_plugins is not None:
        bui.app.plugins.active_plugins.remove(plugin_to_remove_from_active_plugins)

    bui.app.plugins.active_plugins.append(plugin_spec.plugin)


async def reload_on_plugin_changes(ignored_plugins=[]) -> None:
    # Wait for all plugins to be loaded.
    # TODO: There should be a better way to do this.
    await asyncio.sleep(5)

    plugins_directory = babase.app.env.python_directory_user
    plugins = await get_details_for_active_plugins(
        ignored_plugins=ignored_plugins,
    )
    while True:
        await asyncio.sleep(2)
        for plugin in os.listdir(plugins_directory):
            if plugin in plugins and plugin not in ignored_plugins:
                plugin_details = plugins[plugin]
                plugin_path = os.path.join(plugins_directory, plugin)
                last_modified_time = os.path.getmtime(plugin_path)
                if last_modified_time > plugin_details["last_modified_time"]:
                    plugin_details["last_modified_time"] = last_modified_time
                    for entry_point in plugin_details["entry_points"]:
                        await reload_plugin(entry_point)
                    babase.screenmessage(f"Reloaded {plugin}")


# ba_meta export plugin
class EntryPoint(babase.Plugin):
    def on_app_running(self) -> None:
        asyncio.set_event_loop(EVENT_LOOP)
        this_plugin_name = os.path.basename(__file__)
        EVENT_LOOP.create_task(
            reload_on_plugin_changes(
                ignored_plugins=[this_plugin_name],
            )
        )
