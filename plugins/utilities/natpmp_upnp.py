# ba_meta require api 9
# crafted by brostos
#! Try patching upnpclient to use defusedxml replacement for lxml for more device support
import babase
import bauiv1 as bui
import bascenev1 as bs

import shutil
import platform
import os
import hashlib
import zipfile
import tarfile
import threading
import ast
import time
from urllib.parse import urlparse, unquote
from pathlib import Path
from os import remove, getcwd
from urllib.request import urlretrieve, urlopen


# Plucked from https://github.com/ethereum/upnp-port-forward/blob/master/upnp_port_forward/
WAN_SERVICE_NAMES = (
    "WANIPConn1",
    "WANIPConnection.1",  # Nighthawk C7800
    "WANPPPConnection.1",  # CenturyLink C1100Z
    "WANPPPConn1",  # Huawei B528s-23a
)
BS_PORT = bs.get_game_port()


def threaded(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(
            target=func, args=args, kwargs=kwargs, name=func.__name__
        )
        thread.start()

    return wrapper


@threaded
def get_modules() -> None:
    if babase.app.classic.platform == "mac":
        install_path = bs.app.env.python_directory_app
    else:
        install_path = Path(
            f"{getcwd()}/ba_data/python"
        )  # For the guys like me on windows
    packages = {
        "upnp-client": {
            "url": "https://files.pythonhosted.org/packages/dd/69/4d38d9fa757c328df93e7037eb8c1da8ca48e62828c23ba3c421e9335e30/upnpclient-1.0.3.tar.gz",
            "md5": "f936c8de89705555f6bd736a66d3af5d",
            "folder": "upnpclient",
        },
        "python-dateutil": {
            "url": "https://files.pythonhosted.org/packages/66/c0/0c8b6ad9f17a802ee498c46e004a0eb49bc148f2fd230864601a86dcf6db/python-dateutil-2.9.0.post0.tar.gz",
            "md5": "81cb6aad924ef40ebfd3d62eaebe47c6",
            "folder": "dateutil",
        },
        "six": {
            "url": "https://files.pythonhosted.org/packages/94/e7/b2c673351809dca68a0e064b6af791aa332cf192da575fd474ed7d6f16a2/six-1.17.0.tar.gz",
            "md5": "a0387fe15662c71057b4fb2b7aa9056a",
            "folder": "six.py",
        },
        "requests": {
            "url": "https://files.pythonhosted.org/packages/63/70/2bf7780ad2d390a8d301ad0b550f1581eadbd9a20f896afe06353c2a2913/requests-2.32.3.tar.gz",
            "md5": "fa3ee5ac3f1b3f4368bd74ab530d3f0f",
            "folder": "requests",
        },
        "idna": {
            "url": "https://files.pythonhosted.org/packages/f1/70/7703c29685631f5a7590aa73f1f1d3fa9a380e654b86af429e0934a32f7d/idna-3.10.tar.gz",
            "md5": "28448b00665099117b6daa9887812cc4",
            "folder": "idna",
        },
        #! Api 9 already has urllib3 module
        # "urllib3": {
        #     "url": "https://files.pythonhosted.org/packages/7a/50/7fd50a27caa0652cd4caf224aa87741ea41d3265ad13f010886167cfcc79/urllib3-2.2.1.tar.gz",
        #     "md5": "872f7f43af1b48e7c116c7542ab39fab",
        #     "folder": "urllib3",
        # },
        "ifaddr": {
            "url": "https://files.pythonhosted.org/packages/e8/ac/fb4c578f4a3256561548cd825646680edcadb9440f3f68add95ade1eb791/ifaddr-0.2.0.tar.gz",
            "md5": "b1cac02b5dc354d68dd6d853bc9565a7",
            "folder": "ifaddr",
        },
        "NAT-PMP": {
            "url": "https://files.pythonhosted.org/packages/dc/0c/28263fb4a623e6718a179bca1f360a6ae38f0f716a6cacdf47e15a5fa23e/NAT-PMP-1.3.2.tar.gz",
            "md5": "7e5faa22acb0935f75664e9c4941fda4",
            "folder": "natpmp",
        },
    }

    system = platform.platform()

    if "Windows" in system:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/36/88/684d4e800f5aa28df2a991a6a622783fb73cf0e46235cfa690f9776f032e/lxml-5.3.0-cp312-cp312-win32.whl",
            "md5": "a5579cb068a3fbfb5989fbeb4024c599",
            "folder": "lxml",
        }
        packages["charset_normalizer"] = {
            "url": "https://files.pythonhosted.org/packages/b2/21/2b6b5b860781a0b49427309cb8670785aa543fb2178de875b87b9cc97746/charset_normalizer-3.4.1-cp312-cp312-win32.whl",
            "md5": "babec153025b1270d6a2fd76e2c3772f",
            "folder": "charset_normalizer",
        }
    elif "Darwin" in system and "arm64" in system:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/eb/6d/d1f1c5e40c64bf62afd7a3f9b34ce18a586a1cccbf71e783cd0a6d8e8971/lxml-5.3.0-cp312-cp312-macosx_10_9_universal2.whl",
            "md5": "0200ca09c13892c80b47cf4c713786ed",
            "folder": "lxml",
        }
        packages["charset_normalizer"] = {
            "url": "https://files.pythonhosted.org/packages/0a/9a/dd1e1cdceb841925b7798369a09279bd1cf183cef0f9ddf15a3a6502ee45/charset_normalizer-3.4.1-cp312-cp312-macosx_10_13_universal2.whl",
            "md5": "572c9f4f64469518d6a6b4c15710201a",
            "folder": "charset_normalizer",
        }
    elif "Darwin" in system and "x86_64" in system:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/bd/83/26b1864921869784355459f374896dcf8b44d4af3b15d7697e9156cb2de9/lxml-5.3.0-cp312-cp312-macosx_10_9_x86_64.whl",
            "md5": "96b82c1e6d24472af28c48d9bb21605e",
            "folder": "lxml",
        }
        packages["charset_normalizer"] = {
            "url": "https://files.pythonhosted.org/packages/0a/9a/dd1e1cdceb841925b7798369a09279bd1cf183cef0f9ddf15a3a6502ee45/charset_normalizer-3.4.1-cp312-cp312-macosx_10_13_universal2.whl",
            "md5": "572c9f4f64469518d6a6b4c15710201a",
            "folder": "charset_normalizer",
        }
    elif "glibc" in system and "x86_64" in system:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/0a/6e/94537acfb5b8f18235d13186d247bca478fea5e87d224644e0fe907df976/lxml-5.3.0-cp312-cp312-manylinux_2_28_x86_64.whl",
            "md5": "d63bf3d33e46a3b0262176b1a815b4b0",
            "folder": "lxml",
        }
        packages["charset_normalizer"] = {
            "url": "https://files.pythonhosted.org/packages/3e/a2/513f6cbe752421f16d969e32f3583762bfd583848b763913ddab8d9bfd4f/charset_normalizer-3.4.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
            "md5": "1edb315f82fa657b8ee5d564117e057c",
            "folder": "charset_normalizer",
        }
    elif "glibc" in system and "aarch64" in system:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/88/69/6972bfafa8cd3ddc8562b126dd607011e218e17be313a8b1b9cc5a0ee876/lxml-5.3.0-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
            "md5": "663ccdccd076b26b5607901799c671be",
            "folder": "lxml",
        }
        packages["charset_normalizer"] = {
            "url": "https://files.pythonhosted.org/packages/d3/8c/90bfabf8c4809ecb648f39794cf2a84ff2e7d2a6cf159fe68d9a26160467/charset_normalizer-3.4.1-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
            "md5": "d2e8c76665fb9fb013882d4052f46b95",
            "folder": "charset_normalizer",
        }
    elif not "glibc" in system and "x86_64" in system:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/7d/ed/e6276c8d9668028213df01f598f385b05b55a4e1b4662ee12ef05dab35aa/lxml-5.3.0-cp312-cp312-musllinux_1_2_x86_64.whl",
            "md5": "659bdaee4672e8409b277b570e3e3e39",
            "folder": "lxml",
        }
        packages["charset_normalizer"] = {
            "url": "https://files.pythonhosted.org/packages/13/0e/9c8d4cb99c98c1007cc11eda969ebfe837bbbd0acdb4736d228ccaabcd22/charset_normalizer-3.4.1-cp312-cp312-musllinux_1_2_x86_64.whl",
            "md5": "7a60860d64616d5a0af22d034963ab11",
            "folder": "charset_normalizer",
        }
    elif not "glibc" in system and "aarch64" in system:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/8d/e8/4b15df533fe8e8d53363b23a41df9be907330e1fa28c7ca36893fad338ee/lxml-5.3.0-cp312-cp312-musllinux_1_2_aarch64.whl",
            "md5": "3ec71cd198cc28525f4c1d65d41a7689",
            "folder": "lxml",
        }
        packages["charset_normalizer"] = {
            "url": "https://files.pythonhosted.org/packages/7c/5f/6d352c51ee763623a98e31194823518e09bfa48be2a7e8383cf691bbb3d0/charset_normalizer-3.4.1-cp312-cp312-musllinux_1_2_aarch64.whl",
            "md5": "ed3a63cc79137f316ee386cd7aaea7e6",
            "folder": "charset_normalizer",
        }
    else:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/e0/d2/e9bff9fb359226c25cda3538f664f54f2804f4b37b0d7c944639e1a51f69/lxml-5.3.0-cp312-cp312-manylinux_2_12_i686.manylinux2010_i686.manylinux_2_17_i686.manylinux2014_i686.whl",
            "md5": "ecfccadd587adb67ca54a24977e1a436",
            "folder": "lxml",
        }
        packages["charset_normalizer"] = {
            "url": "https://files.pythonhosted.org/packages/74/94/8a5277664f27c3c438546f3eb53b33f5b19568eb7424736bdc440a88a31f/charset_normalizer-3.4.1-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl",
            "md5": "9bdbf872c3bdbcb7191d5cdf3176c38a",
            "folder": "charset_normalizer",
        }

    for package, details in packages.items():
        parsed_url = urlparse(details["url"])
        path = unquote(parsed_url.path)
        filename = os.path.basename(path)

        if details["url"].endswith(".whl"):
            file_format = "whl"
            folder_name = "-".join(filename.split("-")[:2])
        elif details["url"].endswith(".tar.gz"):
            file_format = "tar.gz"
            folder_name = filename.rsplit(".", 2)[0]
        package_path = os.path.join(install_path, f"{package}.{file_format}")
        package_path = Path(f"{install_path}/{package}.{file_format}")
        package_source_dir = Path(f"{install_path}/{details['folder']}")

        if not Path(f"{package_source_dir}/__init__.py").exists():
            try:
                shutil.rmtree(package_source_dir)
            except:
                pass

            package_filename, headers = urlretrieve(
                details["url"], filename=package_path
            )

            with open(package_filename, "rb") as f:
                content = f.read()
                assert hashlib.md5(content).hexdigest() == details["md5"]
            try:
                shutil.unpack_archive(package_filename, install_path, format='gztar')
                extracted_package_files = Path(f"{install_path}/{folder_name}")
                for root, dirs, files in os.walk(extracted_package_files):
                    for dir in dirs:
                        subfolder = os.path.join(root, dir)
                        if subfolder.endswith(details["folder"]):
                            shutil.copytree(
                                subfolder, f"{install_path}/{details['folder']}"
                            )
                if details["folder"] == "six.py":
                    shutil.copy(
                        Path(f"{install_path}/{folder_name}/six.py"),
                        f"{install_path}/six.py",
                    )
                try:
                    shutil.rmtree(Path(f"{install_path}/{folder_name}"))
                except FileNotFoundError:
                    pass
            except shutil.ReadError as e:
                with zipfile.ZipFile(package_filename, "r") as zip_ref:
                    zip_ref.extractall(install_path)
                try:
                    # ! Remember to update accordingly
                    shutil.rmtree(Path(f"{install_path}/lxml-5.3.0.dist-info"))
                except:
                    shutil.rmtree(Path(f"{install_path}/charset_normalizer-3.4.1.dist-info"))  # !
            remove(package_path)
        else:
            return
    # Patch to natpmp to work without netifaces
    with open(Path(f"{install_path}/natpmp/__init__.py"), "r") as f:
        lines = f.readlines()
        # Define the new function as a string
        new_function = '''
# Plucked from https://github.com/tenable/upnp_info/blob/d20a1fda8ca4877d61b89fe7126077a3a5f0b322/upnp_info.py#L23
def get_gateway_addr():
    """
    Returns the gateway ip of the router if upnp service is available
    """
    try:
        locations = set()
        location_regex = re.compile("location:[ ]*(.+)"+ chr(13) + chr(10), re.IGNORECASE)
        ssdpDiscover = (
            "M-SEARCH * HTTP/1.1"+ chr(13) + chr(10)
            + "HOST: 239.255.255.250:1900"+ chr(13) + chr(10)
            + 'MAN: "ssdp:discover"'+ chr(13) + chr(10)
            + "MX: 1"+ chr(13) + chr(10)
            + "ST: ssdp:all"+ chr(13) + chr(10)
            + chr(13) + chr(10)
        )

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(ssdpDiscover.encode("ASCII"), ("239.255.255.250", 1900))
        sock.settimeout(3)
        try:
            while True:
                data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
                location_result = location_regex.search(data.decode("ASCII"))
                if location_result and (location_result.group(1) in locations) == False:
                    locations.add(location_result.group(1))
        except socket.error:
            sock.close()
        if locations:
            for location in locations:
                parsed_url = urlparse(location)
                if parsed_url.path.endswith("xml"):
                    gateway_ip_address = parsed_url.netloc.split(':')[0]
                    return gateway_ip_address
    except:
        pass
            
'''
        # Replace the function
        lines[224:229] = new_function
        lines[21] = "import socket\nimport re\nfrom urllib.parse import urlparse"

    with open(Path(f"{install_path}/natpmp/__init__.py"), "w") as f:
        f.writelines(lines)

    add_port_mapping()


def play_sound(sound):
    with bs.get_foreground_host_activity().context:
        bs.getsound(sound).play()


accessible_online = None


@threaded
def confirm_port():
    global accessible_online
    time.sleep(5)
    with urlopen("https://legacy.ballistica.net/bsAccessCheck") as resp:
        resp = resp.read().decode()
        resp = ast.literal_eval(resp)
        accessible_online = resp["accessible"]
        # return resp["accessible"]


@threaded
def add_port_mapping():
    if accessible_online:
        return
    # Try to add UDP port using NAT-PMP
    try:
        import socket
        import natpmp
        from natpmp import NATPMPUnsupportedError, NATPMPNetworkError

        try:
            natpmp.map_port(
                natpmp.NATPMP_PROTOCOL_UDP,
                BS_PORT,
                BS_PORT,
                14400,
                gateway_ip=natpmp.get_gateway_addr(),
            )
            if accessible_online:
                babase.screenmessage(
                    "You are now joinable from the internet", (0.2, 1, 0.2)
                )
                babase.pushcall(
                    babase.Call(play_sound, "shieldUp"), from_other_thread=True
                )
        except (NATPMPUnsupportedError, NATPMPNetworkError):
            import upnpclient
            from upnpclient.soap import SOAPError
            from urllib.error import HTTPError

            devices = upnpclient.discover()

            if devices == []:
                babase.screenmessage(
                    "Please enable upnp service on your router", (1.00, 0.15, 0.15)
                )
                babase.pushcall(
                    babase.Call(play_sound, "shieldDown"), from_other_thread=True
                )
                return
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # connect() for UDP doesn't send packets
                s.connect(("10.0.0.0", 0))
                local_ip = s.getsockname()[0]
                s.close()
            except:
                pass
            try:
                for upnp_dev in devices:
                    for service in upnp_dev.services:
                        if service.name in WAN_SERVICE_NAMES:
                            try:
                                result = service.GetSpecificPortMappingEntry(
                                    NewRemoteHost="",
                                    NewExternalPort=BS_PORT,
                                    NewProtocol="UDP",
                                )
                                if result["NewEnabled"] and not accessible_online:
                                    if babase.do_once():
                                        babase.screenmessage(
                                            "Oops seems like your network doesn't support upnp",
                                            (1.0, 0.15, 0.15),
                                        )
                                        babase.pushcall(
                                            babase.Call(play_sound, "shieldDown"),
                                            from_other_thread=True,
                                        )
                                    return
                            except SOAPError:
                                if accessible_online:
                                    return
                            service.AddPortMapping(
                                NewRemoteHost="0.0.0.0",
                                NewExternalPort=BS_PORT,
                                NewProtocol="UDP",
                                NewInternalPort=BS_PORT,
                                NewInternalClient=local_ip,
                                NewEnabled="1",
                                NewPortMappingDescription="Bombsquad",
                                NewLeaseDuration=14400,
                            )
                            babase.pushcall(
                                babase.Call(play_sound, "shieldUp"),
                                from_other_thread=True,
                            )
            except (SOAPError, HTTPError, UnicodeDecodeError):
                babase.screenmessage(
                    "You will need to manualy port forward at the router :("
                )
                babase.pushcall(babase.Call(play_sound, "error"), from_other_thread=True,)
    except ModuleNotFoundError:
        pass


# ba_meta export babase.Plugin
class Joinable(babase.Plugin):
    def on_app_running(self) -> None:
        # try:
        confirm_port()
        if accessible_online:
            return
        else:
            try:
                import upnpclient
                add_port_mapping()
            except ImportError:
                try:
                    install_path = Path(f"{getcwd()}/ba_data/python")
                    shutil.rmtree(f"{install_path}/upnpy")
                    shutil.rmtree(f"{install_path}/natpmp")
                except FileNotFoundError:
                    get_modules()

    def on_app_resume(self) -> None:
        confirm_port()
        add_port_mapping()
