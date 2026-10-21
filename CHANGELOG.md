## Plugin Manager (dd-mm-yyyy)

<!-- line length=80 columns -->

### 1.2.2 (21-10-2026)

- Plugins can set min_engine_build in their plugman dict; older game
  builds stay on the newest version of the plugin they can run
- Plugins with no version that runs on this game build are hidden, and
  an installed version newer than the build supports is replaced with
  one it does

### 1.2.1 (21-10-2026)

- Fixed the settings window stretching across the screen on large
  UI in BombSquad 1.8.4+
- Fixed charstr() deprecation warnings in the console on
  BombSquad 1.8+
- Added min_engine_build to index.json, so future releases that
  need a newer game aren't installed on older builds by auto-update
- Auto-update always downloads a release from its own commit,
  so it no longer fails while GitHub's cache of main is out of date
- Auto-update never downgrades, so builds ahead of the
  latest release are left alone
- A broken settings window patch no longer stops the
  plugin manager from loading or updating itself
- Self-update now starts before any optional startup step,
  and a failing step no longer hides or blocks the others
- After 3 failed self-updates in a row, the plugin manager
  tells you to reinstall it by hand
- Added a `ba.user.pluginmanager` logger: updates and
  failures show in the dev console, where its level can be changed

### 1.2.0 (17-10-2026)

- Updated plugman for 1.8+ versions which now use docUI setting window
- Older BombSquad versions (before 1.8) keep the classic settings window patch, so auto-updating doesn't break them
- Added a github field to json files in plugins/ directory

### 1.1.13 (23-08-2026)

- Changelog window hard-wraps its bullets across several source lines

### 1.1.12 (23-08-2026)

- Fixed request timeouts being reported as an unhandled error instead of
  a connection problem, which left the plugin manager stuck on a spinner
- Response bodies are now read on the network threadpool rather than on
  the main thread, so a slow server no longer freezes the game
- Index and changelog setup no longer deadlock after a failed fetch
- Fixed the plugin manager failing to load or refresh on networks where
  one of GitHub's edge servers is unreachable; all of the published
  addresses are now tried instead of a single one
- The DNS block workaround now corrects name resolution rather than
  replacing the HTTP and TLS stack, so ordinary requests take the
  standard code path
- Fixed the changelog window erroring out after the settings window had
  been opened

### 1.1.11 (09-08-2026)

- Switched to babase.app.asyncio_loop and babase.app.threadpool
  for concurrent execution
- A new threadpool to avoid blocking the babase.app.threadpool
  which is for short parallel tasks
- Added a shutdown task to shutdown our threadpool

### 1.1.10 (12-06-2026)

- Fix for older bs versions using `EXPORT_CLASS_NAME_SHORTCUTS` import

### 1.1.9 (11-06-2026)

- Fix for bs 1.7.63

### 1.1.8 (23-02-2026)

- Fix for bs 1.7.61 build no 22714

### 1.1.7 (15-02-2026)

- Added function to fill form details for plugin bug report button
- Added a new plugin bug report yaml template

### 1.1.6 (26-01-2026)

- Fix UI scaling for more window

### 1.1.5 (26-01-2026)

- Various UI bugfixes and improvements
- Optimized PluginWindow displays
- Added a compact MoreWindow
- Better support for arrow control overall
- Cleaned up old stuffs in code

### 1.1.4 (09-08-2025)

- Cleaning up the code.
- UI now works again for other scales if used from dev console.
- Added a new feature to move through plugins.
- Fixed popups getting stuck in background.
- Missing version CHANGELOG no longer causes error

### 1.1.3 (06-04-2025)

- Hot Fix

### 1.1.2 (06-04-2025)

- Small UI fixes.

### 1.1.1 (09-02-2025)

- Added bomb spinner widget for loading animation.

### 1.1.0 (23-01-2025)

- Updated to bombsquad api 9.

### 1.0.23 (13-01-2025)

- Fixed a bug which wasn't letting older versions run Plugin Manager.

### 1.0.22 (07-08-2024)

- Fixed a few Errors and UI Bugs.

### 1.0.21 (20-05-2024)

- Fixed an error related with notification of new plugins.

### 1.0.20 (13-05-2024)

- Now compatible with BS version 1.7.35+.
- Updated build_number and version attributes to latest.
- FIX: Changelog for all version was shown after refreshing.

### 1.0.19 (05-05-2024)

- Fixed an issue where changelogs were not displayed.
- Changed the Authors text color to be seen more easily.

### 1.0.18 (28-04-2024)

- Fixed errors which were caused due to no internet connection.

### 1.0.17 (22-04-2024)

- Added ChangeLog Window to view latest changes.

### 1.0.16 (22-04-2024)

- Fix for error caused when disable button was missing

### 1.0.15 (22-04-2024)

- Plugins can now be viewed in A-Z and Z-A order.
- Added 'Installed' category to show Installed plugins.

### 1.0.14 (21-04-2024)

- Displaying All Author Names and their Info for plugins.

### 1.0.13 (20-04-2024)

- Improvements to the new plugins notification.

### 1.0.12 (20-04-2024)

- Limited the "x new plugins are available" screen message to only show maximum 2 plugins.

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
