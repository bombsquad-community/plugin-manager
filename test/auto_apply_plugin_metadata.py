import ast
import json
import sys


def update_plugin_json(plugin_info, category):
    name = next(iter(plugin_info))
    details = plugin_info[name]

    with open(f"plugins{category}.json", 'r+') as file:
        data = json.load(file)
        try:
            # Check if plugin is already in the json
            data['plugins'][name]
            plugman_version = int(next(iter(data["plugins"][name]["versions"])).replace('.', ''))
            current_version = int(next(iter(details["versions"])).replace('.', ''))
            # `or` In case another change was made on the plugin while still on pr
            if current_version > plugman_version or current_version == plugman_version:
                data[name][details]["versions"][next(iter(details["versions"]))] = None
            elif current_version < plugman_version:
                raise Exception('Version cant be lower than the previous')
        except KeyError:
            data["plugins"][name] = details
        file.seek(0)
        json.dump(data, file, indent=2, ensure_ascii=False)
        # Ensure old content is removed
        file.truncate()


def extract_ba_plugman(plugins: str) -> dict | list:
    for plugin in plugins:
        if "plugins/" in plugin:
            # Split the path and get the part after 'plugins/'
            parts = plugin.split("plugins/")[1].split("/")
            category = parts[0]  # First part after plugins/

            with open(plugin, "r") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    # Check if the assignment matches our variable name
                    if len(node.targets) == 1 and getattr(node.targets[0], "id", None) == 'ba_plugman':
                        # Convert AST node to a Python object safely
                        # return ast.literal_eval(node.value)
                        update_plugin_json(ast.literal_eval(node.value), category)
                        break
                    else:
                        raise ValueError(f"Variable ba_plugman not found.")


if __name__ == "__main__":
    plugins = sys.argv
    extract_ba_plugman(plugins)
