[![CI](https://github.com/bombsquad-community/plugin-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/bombsquad-community/plugin-manager/actions/workflows/ci.yml)

**Important:** If you are on BombSquad version less than 1.7.37 , check below.
- for version 1.7.0 to 1.7.19 (which uses API 7), checkout the [api7](https://github.com/bombsquad-community/plugin-manager/tree/api7) branch.
- for version 1.7.20 to 1.7.36 (which uses API 8), checkout the [api8](https://github.com/bombsquad-community/plugin-manager/tree/api8) branch.

If you have version 1.7.37 or greater (which uses API 9), proceed with the rest of the README here.

-------------------------------

# Plugin Manager

A plugin manager for the game - [BombSquad](https://www.froemling.net/apps/bombsquad). Plugin Manager is a plugin in itself,
which makes further modding of your game more convenient by providing easier access to community created content.

[![DownloadIcon]][DownloadLink]

[DownloadIcon]:https://img.shields.io/badge/Download-5555ff?style=for-the-badge&logoColor=white&logo=DocuSign
[DownloadLinkJSdelivr]:https://cdn.jsdelivr.net/gh/bombsquad-community/plugin-manager/plugin_manager.py
[DownloadLink]:https://github.com/bombsquad-community/plugin-manager/releases/latest/download/plugin_manager.py

![Plugin Manager GIF](https://user-images.githubusercontent.com/106954762/190505304-519c4b91-2461-42b1-be57-655a3fb0cbe8.gif)

## Features

- [x] Completely open-source - both the plugin-manager and all the plugins in this repository.
- [x] Works on all platforms.
- [x] Only deal with plugins and updates targetting your game's current API version.
- [x] Search for plugins.
- [x] Add 3rd party plugin sources (use them at your own risk, since they may not be audited!).
- [x] Enable or disable auto-updates for plugin manager and plugins.
- [x] Immediately enable installed plugins/minigames without having to restart game.
- [x] Launch a plugin's settings directly from the plugin manager window.
- [x] Check out a plugin's source code before installing it.
- [ ] Sync installed plugins with workspaces.
- [ ] Sort plugins by popularity, downloads, rating or some other metric.


## Installation

There are two different ways the plugin manager can be installed:


1. From dev console

   - Enable "Show Dev Console Button" from advance BombSquad settings
   - Paste the following code in dev console
     ```py
     import urllib.request;import _babase;import os;url="https://github.com/bombsquad-community/plugin-manager/releases/latest/download/plugin_manager.py";plugin_path=os.path.join(_babase.env()["python_directory_user"],"plugin_manager.py");file=urllib.request.urlretrieve(url)[0];fl = open(file,'r');f=open(plugin_path, 'w+');f.write(fl.read());fl.close();f.close();print("SUCCESS")
      ```
   - "SUCCESS" will be shown in the console 

2. Another way is to add
   [plugin_manager.py](https://raw.githubusercontent.com/bombsquad-community/plugin-manager/main/plugin_manager.py)
   to your workspace. However, plugin manager self-updates will fail when installed using this way since the game
   will overrwrite the updated plugin manager, with the older version from workspace on the next sync. However, you can
   manually apply updates by copying the latest plugin manager's source code again to your workspace when using this method.

3. [Download plugin_manager.py][DownloadLink] to your mods directory (check it out by going into your game's
   Settings -> Advanced -> Show Mods Folder). This is the recommended way (read next method to know why).
   If you're on a newer version of Android (11 or above) and not rooted, it probably won't be possible to copy
   mods to game's mods folder. In this case, you can connect your Android phone to a computer and push `plugin_manager.py`
   [using `adb`](https://www.xda-developers.com/install-adb-windows-macos-linux/):
   ```bash
   $ adb push plugin_manager.py /sdcard/Android/data/net.froemling.bombsquad/files/mods/plugin_manager.py
   ```

## Usage

- If installed correctly, you'll see the plugin manager button in your game's settings.

<img src="https://user-images.githubusercontent.com/106954762/190507025-f9e0dd12-d91b-4e3e-a347-6998d776a399.png" width="600">

- That's it, you now have access to a variety of community created content waiting for you to install!

## Contributing

### Submitting a Plugin

- In order for a plugin to get accepted to this official repository, it must target the general game audience and be
  completely open and readable, not be encoded or encrypted in any form.
- If your plugin doesn't target the general game audience, you can put your plugin(s) in a GitHub repository and then
  your plugin(s) can be installed through the custom source option in-game.
  See [3rd party plugin sources](#3rd-party-plugin-sources) for more information.
- New plugins are accepted through a [pull request](../../compare). Add your plugin in the minigames, utilities, or
  the category directory you feel is the most relevant to the type of plugin you're submitting, [here](plugins).
  Then add an entry to the category's JSON metadata file.
- Plugin manager will also show and execute the settings icon if your `ba.Plugin` class has methods `has_settings_ui` and `show_settings_ui`; check out the [colorscheme](https://github.com/bombsquad-community/plugin-manager/blob/eb163cf86014b2a057c4a048dcfa3d5b540b7fe1/plugins/utilities/colorscheme.py#L448-L452) plugin for an example.

#### Example:

Let's say you wanna submit this new utility-type plugin named as `sample_plugin.py`:
```python
# ba_meta require api 9
import babase

plugman = dict(
    plugin_name="sample_plugin",
    description="A test plugin for demonstration purposes blah blah.",
    external_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    authors=[
        {"name": "Loup", "email": "loupg450@gmail.com", "discord": "loupgarou_"},
        {"name": "brostos", "email": "", "discord": "brostos"}
    ],
    version="1.0.0",
)

# ba_meta export babase.Plugin
class Main(babase.Plugin):
    def on_app_running(self):
        babase.screenmessage("Hi! I am a sample plugin!")

    def has_settings_ui(self):
        return True

    def show_settings_ui(self, source_widget):
        babase.screenmessage("You tapped my settings!")
```

You'll have to fork this repository and add your `sample_plugin.py` plugin file into the appropriate directory, which for
utility plugin is [plugins/utilities](plugins/utilities). After that, plugin details and version values will automatically be populated through github-actions in [plugins/utilities.json](plugins/utilities.json)(along with formatting your code as per PEP8 style
guide) once you open a pull request.

### Updating a Plugin

- Make a [pull request](../../compare) with whatever changes you'd like to make to an existing plugin, and add a new
  version number in your plugin in the plugman dict.

#### Example

Continuing the example from [Submitting a Plugin](#submitting-a-plugin) section, if you also want to add a new screenmessage
to the `sample_plugin.py` plugin after it has been submitted, edit `sample_plugin.py` with whatever changes you'd like:
```diff
diff --git a/plugins/utilities/sample_plugin.py b/plugins/utilities/sample_plugin.py
index ebb7dcc..da2b312 100644
--- a/plugins/utilities/sample_plugin.py
+++ b/plugins/utilities/sample_plugin.py
@@ -9,7 +9,7 @@
         {"name": "Loup", "email": "loupg450@gmail.com", "discord": "loupgarou_"},
         {"name": "brostos", "email": "", "discord": "brostos"}
     ],
-    version="1.0.0",
+    version="1.1.0",
 )
 
 # ba_meta export babase.Plugin
@@ -21,4 +21,4 @@
         return True
 
     def show_settings_ui(self, source_widget):
-        babase.screenmessage("You tapped my settings!")
+        babase.screenmessage("Hey! This is my new screenmessage!")
```

That's it! Now you can make a [pull request](../../compare) with the updated `sample_plugin.py` file.

## 3rd Party Plugin Sources

- In case your plugin doesn't sit well with our guidelines or you wouldn't want your plugin to be here for some reason,
  you can create your own GitHub repository and put all your plugins in there.
- Check out [bombsquad-community/sample-plugin-source](https://github.com/bombsquad-community/sample-plugin-source) as an example.
  You can choose to show up plugins from this repository in your plugin manager by adding `bombsquad-community/sample-plugin-source`
  as a custom source through the category selection popup window in-game.
- Plugin manager will default to picking up plugins from the `main` branch of the custom source repository. You
  can specify a different branch by suffixing the source URI with `@branchname`, such as `bombsquad-community/sample-plugin-source@experimental`.

  #### Known 3rd Party Plugin Sources

  If you maintain or know of a 3rd party plugin source, let us know and we'll add it below so people can know about it. It
  will also help us to notify the maintainers of any future breaking changes in plugin manager that could affect 3rd party
  plugin sources.

  - [rikkolovescats/sahilp-plugins](https://github.com/rikkolovescats/sahilp-plugins)
  - [Aeliux/arcane](https://github.com/Aeliux/arcane)


## Tests

Metadata tests are automatically executed whenever a pull request is opened and a commit is pushed. You can also run them
locally by installing test dependencies with:

```bash
$ pip install -r test/pip_reqs.txt
```

and then executing the following in the project's root directory:

```bash
$ python -m unittest discover -v
```

## Shout out!

If you've been with the community long enough, you may have known about the amazing
[Mrmaxmeier's mod manager](https://github.com/Mrmaxmeier/BombSquad-Community-Mod-Manager), which unfortunately wasn't
maintained and failed to keep up with the game's latest versions and API changes. Well, this is another attempt to
create something similar, with a hope we as a community can continue to keep it up-to-date with the original game.


## License

- [Plugin manager's source code](plugin_manager.py) is licensed under the MIT license. See [LICENSE](LICENSE) for more
  information.
- Any plugins you submit here are automatically assumed to be licensed under the MIT license, i.e. unless you explicitly
  specify a different license in your plugin's source code. See
  [this plugin](https://github.com/bombsquad-community/plugin-manager/blob/cba1194c68ce550a71d2f3fadd9e1b8cbac4981c/plugins/utilities/store_event_specials.py#L1-L22)
  for an example.
