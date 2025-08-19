# crafted by brostos
import json

plugin_category = ["maps", "minigames", "utilities"]
plugin_names_by_category = {}

for category in plugin_category:
    with open(f"{category}.json", "r+") as file:
        data = json.load(file)
        plugins = data["plugins"]
        plugin_names_by_category[category] = list(plugins.keys())

        for plugin in plugin_names_by_category[category]:
            latest_version = int(next(iter(plugins[plugin]["versions"])).replace(".", ""))
            current_version = ".".join(str(latest_version + 1))
            plugins[plugin]["versions"][current_version] = None
            # Ensure latest version appears first
            plugins[plugin]["versions"] = dict(
                sorted(plugins[plugin]["versions"].items(), reverse=True)
            )
            # json.dump(plugins, indent=2)
            file.seek(0)
            json.dump(data, file, indent=2, ensure_ascii=False)
            # Ensure old content is removed
            file.truncate()
    print(f"All {category} version have been upgraded")
