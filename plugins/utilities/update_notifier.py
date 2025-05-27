# ba_meta require api 9

#! Crafted by brostos

from platform import machine
import threading
import time
import urllib.request
import re

import babase
import bauiv1 as bui
import bascenev1 as bs


def threaded(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(
            target=func, args=args, kwargs=kwargs, name=func.__name__
        )
        thread.start()

    return wrapper


def play_sound(sound):
    with bs.get_foreground_host_activity().context:
        bs.getsound(sound).play()


@threaded
def fetch_update():
    url = 'https://ballistica.net/downloads'
    try:
        response = urllib.request.urlopen(url)
        web_content = response.read().decode('utf-8')
    except:
        return

    match = re.search(r'<td class="onlydesktop">(\d+)</td>', web_content)
    if match:
        latest_build_number = match.group(1)
        current_build_number = babase.app.env.engine_build_number
        if latest_build_number == current_build_number:
            return

    pattern = r'<a\s+href=["\']([^"\']+\.(?:apk|tar\.gz|dmg|zip))["\']'

    # Find all matches in the HTML content
    matches = re.findall(pattern, web_content)

    download_links = []

    for link in matches:
        # Skip navigation links
        if link.startswith(('?', '/', 'old/')):
            continue

        # Create full URL if needed
        if not link.startswith('http'):
            full_url = url + link
        else:
            full_url = link

        download_links.append(full_url)

    build = babase.app.env.gui
    bs_platform = babase.app.classic.platform
    mash = machine().lower()
    if bs_platform.lower() == 'linux':
        if mash in ("x86_64", "amd64"):
            bs_platform = "Linux_x86_64"
        elif mash in ("aarch64", "arm64"):
            bs_platform = "Linux_Arm64"
    if not build and bs_platform == "mac":
        if mash in ("x86_64", "amd64"):
            bs_platform = "Mac_x86_64"
        elif mash in ("aarch64", "arm64"):
            bs_platform = "Mac_Arm64"

    for link in download_links:
        link_lower = link.lower()
        extension = link.replace('https://files.ballistica.net/bombsquad/builds/', '')
        if build:
            if not ('server' in link_lower) and bs_platform.lower() in link_lower:
                app = bui.app
                subplatform = app.classic.subplatform
                if subplatform == "google":
                    return

                babase.screenmessage(
                    "A new BombSquad version is available...\nRedirecting to download page", (0.21, 1.0, 0.20))
                sound_sequence = [
                    ("drumRoll", 0),
                    ("fanfare", 0),
                    ("ding", 0),
                    ("gasp", 2),
                    ("aww", 0),
                    ("ooh", 0),
                    ("yeah", 0),
                    ("nice", 2)
                ]

                for sound, delay in sound_sequence:
                    if delay > 0:
                        time.sleep(delay)
                    babase.pushcall(babase.Call(play_sound, sound), from_other_thread=True)
                time.sleep(1)
                bui.open_url(f'https://ballistica.net/downloads#:~:text={extension}')
        elif not build:
            if ('server' in link_lower) and bs_platform.lower() in link_lower:
                GREEN = "\033[32m"
                LIGHT_BLUE = "\033[94m"
                RESET = "\033[0m"
                try:
                    print(f"{GREEN}A new BombSquad version is available...Redirecting to download page{RESET}")
                    time.sleep(4)
                    bui.open_url(f'https://ballistica.net/downloads#:~:text={extension}')
                except:
                    print(
                        f"{GREEN}Download the latest version using this official link-> {LIGHT_BLUE}{link}{RESET}")


# ba_meta export babase.Plugin
class bybrostos(babase.Plugin):
    def on_app_running(self):
        fetch_update()
