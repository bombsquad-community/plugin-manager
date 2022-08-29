[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/bombsquad-community/plugin-manager/Flake8)](https://github.com/bombsquad-community/plugin-manager/actions)

# plugin-manager

A plugin manager for the game - [Bombsquad](https://www.froemling.net/apps/bombsquad).


## Features

- [x] Fully open-source plugin manager, as well as all the plugins you'll find in this repository.
- [x] Ability to add 3rd party plugin sources (use them at your own risk, since they may not be audited!).
- [x] Only deal with plugins and plugin updates targetting your game's current API version.
- [x] Search installable plugins from this repository, as well as 3rd party sources.
- [x] Setting to enable or disable auto-updates for plugin manager as well plugins.
- [x] Setting to immediately enable installed plugins/minigames without having to restart game.
- [x] Ability to launch a plugin's settings directly from the plugin manager window.
- [x] Check out a plugin's source code before you even install it.
- [ ] Sync installed plugins with workspaces.
- [ ] Sort plugins by popularity, downloads, rating or some other metric.


## Installation

- Either download [plugin_manager.py](https://raw.githubusercontent.com/bombsquad-community/plugin-manager/main/plugin_manager.py)
  to your mods directory (check it out by going into your game's Settings -> Advanced -> Show Mods Folder) or directly add
  it to your workspace!


## Contributing

### Submitting a Plugin
- In order for a plugin to get accepted to this official repository, it must target the general game audience and be
  completely open and readable, not be encoded or encrypted in any form.
- If your plugin doesn't target the general game audience, you can put your plugins in a GitHub repository and then
  your plugins can be installed through the custom source option in-game.
  See [3rd party plugin sources](#3rd-party-plugin-sources) for more information.
- New plugins are accepted through a [pull request](../../compare). Add your plugin in the minigames, utilities, or
  the category directory you feel is the most relevant to the type of plugin you're submitting, [here](plugins).
  Then add an entry to the category's JSON metadata file (check out existing entries to know what all fields are required).
  Plugin manager will also show and execute the settings icon if your `ba.Plugin` export class has a method named
  `on_plugin_manager_prompt`; check out the
  [colorscheme](https://github.com/bombsquad-community/plugin-manager/blob/f24f0ca5ded427f6041795021f1af2e6a08b6ce9/plugins/utilities/colorscheme.py#L419-L420)
  plugin for an example and it's behaviour when the settings icon is tapped on via the plugin manager in-game.

### Updating a Plugin
- Make a [pull request](../../compare) with whatever changes you'd like to make to an existing plugin, and add a new
  version entry in your plugin category's JSON metadata file.

## 3rd Party Plugin Sources
- In case your plugin doesn't sit well with our guidelines or you wouldn't want your plugin to be here for some reason,
  you can create your own GitHub repository and put all your plugins in there.
- Check out https://github.com/rikkolovescats/sahilp-plugins for an example. You can choose to show up plugins from this
  repository in your plugin manager by adding `rikkolovescats/sahilp-plugins` as a custom source through the category
  selection popup window in-game.


## Tests

Metadata tests are automatically executed whenever a pull request is opened and a commit is pushed. You can also run them
locally by installing test dependencies with:

```bash
$ pip install -r test/pip_reqs.txt
```

and then executing the following in the project's root directory:

```bash
$ python -m unittest discover
```

## License

- [Plugin manager's source code](plugin_manager.py) is licensed under the MIT license. See [LICENSE](LICENSE) for more
  information.
- Any plugins you submit here are automatically assumed to be licensed under the MIT license, i.e. unless you explicitly
  specify a different license while submitting a plugin.
