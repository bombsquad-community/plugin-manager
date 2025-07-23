import ast
import json
import sys
from ast import Call, Dict, Name, Constant, keyword


def update_plugin_json(plugin_info, category):
    name = plugin_info["plugin_name"]

    with open(f"plugins/{category}/{category}.json", "r+") as file:
        data = json.load(file)
        try:
            # Check if plugin is already in the json
            plugin = data["plugins"][name]
            plugman_version = int(plugin["version"].replace(".", ""))
            current_version = int(plugin_info["version"].replace(".", ""))
            # `or` In case another change was made on the plugin while still on pr
            if current_version > plugman_version or current_version == plugman_version:
                plugin["versions"][plugin_info["version"]] = None
                # Ensure latest version appears first
                plugin["versions"] = dict(
                    sorted(plugin["versions"].items(), reverse=True)
                )
                plugin["description"] = plugin_info["description"]
                plugin["external_url"] = plugin_info["external_url"]
                plugin["authors"] = [
                    {
                        "name": ", ".join(plugin_info["author"]),
                        "discord": plugin_info["discord"],
                        "email": plugin_info["email"],
                    }
                ]
            elif current_version < plugman_version:
                raise Exception("Version cant be lower than the previous")
        except KeyError:
            data["plugins"][name] = {
                "description": plugin_info["description"],
                "external_url": plugin_info["external_url"],
                "authors": [
                    {
                        "name": ", ".join(plugin_info["author"]),
                        "discord": plugin_info["discord"],
                        "email": plugin_info["email"],
                    }
                ],
                "versions": {plugin_info["version"]: None},
            }

        file.seek(0)
        json.dump(data, file, indent=2, ensure_ascii=False)
        # Ensure old content is removed
        file.truncate()


def extract_plugman(plugins: str) -> dict:
    for plugin in plugins:
        if "plugins/" in plugin:
            # Split the path and get the part after 'plugins/'
            parts = plugin.split("plugins/")[1].split("/")
            category = parts[0]  # First part after plugins/
    with open(plugin, "r") as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "plugman":
                if isinstance(node.value, ast.Dict):
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
                        result[kw.arg] = ast.literal_eval(kw.value)
                    return result, category

    raise ValueError(
        "Variable plugman not found in the file or has unsupported format."
    )


if __name__ == "__main__":
    plugins = sys.argv
    print(plugins)  # Debugging (╯°□°）╯
    update_plugin_json(*extract_plugman(plugins))
