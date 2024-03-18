# ba_meta require api 8

import babase
import bauiv1 as bui
import bascenev1 as bs

import shutil
import platform
import os
import hashlib
import zipfile
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
    install_path = Path(f"{getcwd()}/ba_data/python")  # For the guys like me on windows
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
            "url": "https://files.pythonhosted.org/packages/71/39/171f1c67cd00715f190ba0b100d606d440a28c93c7714febeca8b79af85e/six-1.16.0.tar.gz",
            "md5": "a7c927740e4964dd29b72cebfc1429bb",
            "folder": "six.py",
        },
        "requests": {
            "url": "https://files.pythonhosted.org/packages/9d/be/10918a2eac4ae9f02f6cfe6414b7a155ccd8f7f9d4380d62fd5b955065c3/requests-2.31.0.tar.gz",
            "md5": "941e175c276cd7d39d098092c56679a4",
            "folder": "requests",
        },
        "charset_normalizer": {
            "url": "https://files.pythonhosted.org/packages/63/09/c1bc53dab74b1816a00d8d030de5bf98f724c52c1635e07681d312f20be8/charset-normalizer-3.3.2.tar.gz",
            "md5": "0a4019908d9e50ff13138e8a794d9e2b",
            "folder": "charset_normalizer",
        },
        "idna": {
            "url": "https://files.pythonhosted.org/packages/bf/3f/ea4b9117521a1e9c50344b909be7886dd00a519552724809bb1f486986c2/idna-3.6.tar.gz",
            "md5": "70f4beef4feb196ac64b75a93271f53c",
            "folder": "idna",
        },
        "urllib3": {
            "url": "https://files.pythonhosted.org/packages/7a/50/7fd50a27caa0652cd4caf224aa87741ea41d3265ad13f010886167cfcc79/urllib3-2.2.1.tar.gz",
            "md5": "872f7f43af1b48e7c116c7542ab39fab",
            "folder": "urllib3",
        },
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
            "url": "https://files.pythonhosted.org/packages/fe/71/700f9baa762fee6dd63db8b16d78aeb4fc27aa2866c7b1c69c93c1e715e9/lxml-5.1.0-cp311-cp311-win32.whl",
            "md5": "a9486faba8dd3c4caa8c20a0f699958b",
            "folder": "lxml",
        }
    elif "Darwin" and "arm64" in system:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/bc/7e/4c66526e9b4f9c46afd7b2fef4482857d38752f2ee7cbb218816c5468251/lxml-5.1.0-cp311-cp311-macosx_11_0_arm64.whl",
            "md5": "4bed29fe8026c333c2d5030ecc8d85d9",
            "folder": "lxml",
        }
    elif "Darwin" and "x86_64" in system:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/f9/dc/9819d678570f5f348de134b54b93fcf52584d7afff875cd7122117932f53/lxml-5.1.0-cp311-cp311-macosx_10_9_x86_64.whl",
            "md5": "d9ac00081b68951622009c900caaf715",
            "folder": "lxml",
        }
    elif "glibc" and "x86_64" in system:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/1f/09/df0101e6d7be06fca545c0f7417d03d69679ff280d892a406469086780a4/lxml-5.1.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
            "md5": "2c4dfc402f879dafc020ef7a79dc36d3",
            "folder": "lxml",
        }
    elif "glibc" and "aarch64" in system:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/f9/cf/d56019b06cde5ea5cbc7b984ccb7da1620bc132287b7ada6e86fed6f89a0/lxml-5.1.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
            "md5": "e21b6ac73e89d9c9a34c7dd4e79351cc",
            "folder": "lxml",
        }
    elif not "glibc" and "x86_64" in system:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/14/60/8a188be2c9acf3d4c4168a16e3500cf1f1fe3cbd490895127251cb542b0b/lxml-5.1.0-cp311-cp311-musllinux_1_1_x86_64.whl",
            "md5": "48cd2be61449641adc10e61d0130cbef",
            "folder": "lxml",
        }
    elif not "glibc" and "aarch64" in system:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/ce/fa/fa0366c08a061592d4dde52c7952a8b122135f0ac29762163e898b6f2dc1/lxml-5.1.0-cp311-cp311-musllinux_1_1_aarch64.whl",
            "md5": "b087cb7cb571cda85bb895e1d9f4b004",
            "folder": "lxml",
        }
    else:
        packages["lxml"] = {
            "url": "https://files.pythonhosted.org/packages/ad/9b/422a58938cab0b855bdc708d37a645a980734042d468550071462b9ea57b/lxml-5.1.0-cp311-cp311-manylinux_2_12_i686.manylinux2010_i686.manylinux_2_17_i686.manylinux2014_i686.whl",
            "md5": "32f402f2d304869a4fd91fc695aa367e",
            "folder": "lxml",
        }

    for package, details in packages.items():
        parsed_url = urlparse(details["url"])
        path = unquote(parsed_url.path)
        filename = os.path.basename(path)

        if details["url"].endswith(".whl"):
            file_format = "whl"
            folder_name = '-'.join(filename.split('-')[:2])
        elif details["url"].endswith(".tar.gz"):
            file_format = "tar.gz"
            folder_name = filename.rsplit('.', 2)[0]
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
                shutil.unpack_archive(package_filename, install_path)
                extracted_package_files = Path(f"{install_path}/{folder_name}")
                for root, dirs, files in os.walk(extracted_package_files):
                    for dir in dirs:
                        subfolder = os.path.join(root, dir)
                        if subfolder.endswith(details["folder"]):
                            shutil.copytree(subfolder, f"{install_path}/{details['folder']}")
                if details["folder"] == "six.py":
                    shutil.copy(Path(f"{install_path}/{folder_name}/six.py"),
                                f"{install_path}/six.py")
                shutil.rmtree(Path(f"{install_path}/{folder_name}"))
            except shutil.ReadError as e:
                with zipfile.ZipFile(package_filename, 'r') as zip_ref:
                    zip_ref.extractall(install_path)
                shutil.rmtree(Path(f"{install_path}/lxml-5.1.0.dist-info"))
            remove(package_path)
        else:
            return

    # Patch to natpmp to work without netifaces
    with open(Path(f"{install_path}\\natpmp\\__init__.py"), "r") as f:
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

    with open(Path(f"{install_path}\\natpmp\\__init__.py"), "w") as f:
        f.writelines(lines)

    add_port_mapping()


@threaded
def confirm_port():
    time.sleep(5)
    with urlopen("https://legacy.ballistica.net/bsAccessCheck") as resp:
        resp = resp.read().decode()
        resp = ast.literal_eval(resp)
        return resp["accessible"]


@threaded
def add_port_mapping():
    if confirm_port():
        return
    # Try to add UDP port using NAT-PMP
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
        if confirm_port():
            babase.screenmessage(
                "You are now joinable from the internet", (0.2, 1, 0.2)
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
            bui.getsound('shieldDown').play()  # -> RuntimeError : Sound creation failed
            return
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # connect() for UDP doesn't send packets
            s.connect(('10.0.0.0', 0))
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
                                NewRemoteHost="", NewExternalPort=BS_PORT, NewProtocol="UDP"
                            )
                            if result and not confirm_port():
                                if babase.do_once():
                                    babase.screenmessage(
                                        "Oops seems like your network doesn't support upnp",
                                        (1.0, 0.15, 0.15),
                                    )
                                return
                        except (SOAPError):
                            if confirm_port():
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
        except (SOAPError, HTTPError, UnicodeDecodeError):
            babase.screenmessage("You will need to manualy port forward at the router :(")


# ba_meta export babase.Plugin
class Joinable(babase.Plugin):
    def on_app_running(self) -> None:
        try:
            get_modules()
            if confirm_port():
                return
            else:
                add_port_mapping()
        except:
            pass

    def on_app_resume(self) -> None:
        add_port_mapping()
