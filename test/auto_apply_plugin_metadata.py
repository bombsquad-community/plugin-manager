import sys
import json
import ast
import get_latest

DEBUG = True


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def get_latest_version(plugin_name, category):
    filepaths = {
        "minigames": "plugins/minigames.json",
        "utilities": "plugins/utilities.json",
        "maps": "plugins/maps.json",
        "plugman": "index.json",
    }

    try:
        if category != "plugman":
            return get_latest.get_latest_plugin_version(plugin_name, filepaths[category])
        return get_latest.get_latest_plugman_version()

    except Exception as e:
        raise e


def update_plugman_json(version):
    with open("index.json", "r+") as file:
        data = json.load(file)
        plugman_version = int(get_latest_version("plugin_manager", "plugman").replace(".", ""))
        current_version = int(version["version"].replace(".", ""))

        if current_version > plugman_version:
            with open("index.json", "r+") as file:
                data = json.load(file)
                data[current_version] = None
                data["versions"] = dict(sorted(data["versions"].items(), reverse=True))


def update_plugin_json(plugin_info, category):
    name = plugin_info["plugin_name"]

    with open(f"plugins/{category}.json", "r+") as file:
        data = json.load(file)
        try:
            # Check if plugin is already in the json
            plugin = data["plugins"][name]
            plugman_version = int(get_latest_version(name, category).replace(".", ""))
            current_version = int(plugin_info["version"].replace(".", ""))
            # Ensure the version is always greater from the already released version
            if current_version > plugman_version:
                plugin["versions"][plugin_info["version"]] = None
                # Ensure latest version appears first
                plugin["versions"] = dict(sorted(plugin["versions"].items(), reverse=True))
                plugin["description"] = plugin_info["description"]
                plugin["external_url"] = plugin_info["external_url"]
                plugin["authors"] = plugin_info["authors"]
            elif current_version <= plugman_version:
                raise Exception("Version cant be lower or equal than the previous version.")
        except KeyError:
            data["plugins"][name] = {
                "description": plugin_info["description"],
                "external_url": plugin_info["external_url"],
                "authors": plugin_info["authors"],
                "versions": {plugin_info["version"]: None},
            }

        file.seek(0)
        json.dump(data, file, indent=2, ensure_ascii=False)
        # Ensure old content is removed
        file.truncate()


def extract_plugman(plugins):
    for plugin in plugins:
        if "plugins/" in plugin:

            debug_print(plugin)
            try:
                # Split the path and get the part after 'plugins/'
                parts = plugin.split("plugins/")[1].split("/")
                file_name_no_extension = plugin.split("/")[-1].replace(".py", "")
                category = parts[0]  # First part after plugins/
            except ValueError:
                if "plugin_manager" in plugin:
                    continue
            with open(plugin, "r") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    target = node.targets[0]
                    if isinstance(target, ast.Name) and target.id == "plugman":
                        if isinstance(node.value, ast.Dict):
                            # i dont want to support multiple formats for now
                            # because its harder to parse and maintain
                            # ill leave this here for now, though not supported
                            # Standard dictionary format {key: value}
                            return ast.literal_eval(node.value)
                        elif (
                            isinstance(node.value, ast.Call)
                            and isinstance(node.value.func, ast.Name)
                            and node.value.func.id == "dict"
                        ):
                            # dict() constructor format
                            result = {}
                            for kw in node.value.keywords:
                                if kw.arg == "plugin_name":
                                    plugin_name = ast.literal_eval(kw.value)
                                    # some basic validation specific to plugin manager
                                    if (plugin_name != plugin_name.lower()):
                                        raise ValueError(
                                            "Plugin name in plugman must be in snakecase.")
                                    if (plugin_name != file_name_no_extension):
                                        raise ValueError(
                                            "Plugin name in plugman does not match the file name.")
                                result[kw.arg] = ast.literal_eval(kw.value)
                            if category:
                                update_plugin_json(result, category=category)
                            else:
                                update_plugman_json(result)
            # raise ValueError("Variable plugman not found in the file or has unsupported format.")


if __name__ == "__main__":
    plugins = sys.argv[1].split('\n')
    debug_print(plugins)
    extract_plugman(plugins)
