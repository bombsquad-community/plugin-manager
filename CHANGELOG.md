## Plugin Manager (dd-mm-yyyy)

### 1.0.13 (20-04-2024)

- Improvements to the new plugins notification

### 1.0.12 (20-04-2024)

- Limited the "x new plugins are available" screen message to only show maximum 3 plugins.

### 1.0.11 (20-04-2024)

- Fixed positions of a few buttons.

### 1.0.10 (19-04-2024)

- Fixed up a bug in Refreshing Plugins button.

### 1.0.9 (19-04-2024)

- Made the Plugin names look a little cleaner.

### 1.0.8 (11-04-2024)

- Avoid making app-mode related calls while `SceneAppMode` isn't set.

### 1.0.7 (22-02-2024)

- Fix searching in plugin manager with capital letters.

### 1.0.6 (26-12-2023)

- Fixed plugin manager throwing errors on older builds.

### 1.0.5 (11-12-2023)

- Fix a typo.

### 1.0.4 (08-12-2023)

- Fix a few UI warnings related to 1.7.30.
- Fix a memory leak.

### 1.0.3 (06-10-2023)

- Add a compatibility layer for older builds for API deprecation changes that occured in https://github.com/efroemling/ballistica/blob/master/CHANGELOG.md#1727-build-21282-api-8-2023-08-30

### 1.0.2 (01-10-2023)

- Rename deprecated `babase.app.api_version` -> `babase.app.env.api_version`.

### 1.0.1 (30-06-2023)

- Allow specifying branch names in custom sources.

### 1.0.0 (20-06-2023)

- Migrate plugin manager's source code to API 8.

### 0.3.5 (16-06-2023)

- Replace the "Loading..." text with the exception message in case something goes wrong.

### 0.3.4 (14-05-2023)

- Optimize new plugin detection mechanism.

### 0.3.3 (13-05-2023)

- Print the number and names of the client supported plugins which are newly added to the plugin manager.

### 0.3.2 (30-04-2023)

- Fix sometimes same sound would repeat twice when pressing a button.
- Low key attempt to experiment with staging branch by changing current tag in `plugin_manager.py`.
- Assume underscores as spaces when searching for plugins in game.

### 0.3.1 (04-03-2023)

- Resize the plugin window to limit the overlapping of plugin description.

### 0.3.0 (12-02-2023)

- Displays a tutorial button in the plugin window, whenever there is a supported url present in the plugin data.

### 0.2.2 (18-01-2023)

- Auto add new line breaks in long plugin descriptions.
- Fixed an issue where pressing back on the main plugin manager window would play the sound twice.

### 0.2.1 (17-12-2022)

- Add Google DNS as a fallback for Jio ISP DNS blocking resolution of raw.githubusercontent.com domain.

### 0.2.0 (05-12-2022)

- Removed `on_plugin_manager_prompt` and replaced it with the in-game's plugin settings ui

### 0.1.10 (05-12-2022)

- Added Discord and Github textures on buttons

### 0.1.9 (03-12-2022)

- Search now filters on author names and plugin description.

### 0.1.8 (30-11-2022)

- Use HTTPS for all network requests (now that the Android bug has been resolved as of v1.7.11).

### 0.1.7 (03-10-2022)

- Added New Option in settings for Notifying new plugins.
- Added a Discord Button to join Bombsquad's Official Discord server.


### 0.1.6 (15-09-2022)

- Distinguish the settings button with a cyan color (previously was green) in plugin manager window.
- Clean up some internal code.


### 0.1.5 (08-09-2022)

- Plugin files that export classes besides plugin or game, now work.

### 0.1.4 (05-09-2022)

- First public release of plugin manager. 🎉
