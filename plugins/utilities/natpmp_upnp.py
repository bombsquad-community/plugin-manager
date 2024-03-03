# ba_meta require api 8

import babase
import bauiv1 as bui
import bascenev1 as bs

import shutil
import hashlib
import threading
import ast
import time
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
    upnpy_path = Path(f"{install_path}/upnp.tar.gz")
    nat_pmp_path = Path(f"{install_path}/natpmp.tar.gz")
    upnpy_file_path = Path(f"{install_path}/upnpy")
    nat_pmp_file_path = Path(f"{install_path}/natpmp")
    nat_pmp_source_dir = Path(f"{install_path}/NAT-PMP-1.3.2/natpmp")
    upnpy_source_dir = Path(f"{install_path}/UPnPy-1.1.8/upnpy")
    if (
        not Path(f"{nat_pmp_file_path}/__init__.py").exists()
        and not Path(f"{upnpy_file_path}/__init__.py").exists()
    ):  # YouKnowDev
        nat_pmp_url = "https://files.pythonhosted.org/packages/dc/0c/28263fb4a623e6718a179bca1f360a6ae38f0f716a6cacdf47e15a5fa23e/NAT-PMP-1.3.2.tar.gz"
        upnpy_url = "https://files.pythonhosted.org/packages/80/66/d4e721ff8766ea3e78730574669f6feeb71e438a8c2d7a62b2c3456a5c12/UPnPy-1.1.8.tar.gz"
        try:
            # fix issue where the file delete themselves
            try:
                shutil.rmtree(nat_pmp_file_path)
                shutil.rmtree(upnpy_file_path)
            except:
                pass
            nat_pmp_filename, headers = urlretrieve(nat_pmp_url, filename=nat_pmp_path)
            upnpy_filename, headers = urlretrieve(upnpy_url, filename=upnpy_path)
            with open(nat_pmp_filename, "rb") as f:
                content = f.read()
                assert (
                    hashlib.md5(content).hexdigest()
                    == "7e5faa22acb0935f75664e9c4941fda4"
                )
            with open(upnpy_filename, "rb") as f:
                content = f.read()
                assert (
                    hashlib.md5(content).hexdigest()
                    == "b33ad0b38e39af258e2c8f38813abf7b"
                )
            shutil.unpack_archive(nat_pmp_filename, install_path)
            shutil.unpack_archive(upnpy_filename, install_path)
            remove(upnpy_path)
            remove(nat_pmp_path)
            shutil.copytree(nat_pmp_source_dir, nat_pmp_file_path)
            shutil.copytree(upnpy_source_dir, upnpy_file_path)
            shutil.rmtree(Path(f"{install_path}/NAT-PMP-1.3.2"))
            shutil.rmtree(Path(f"{install_path}/UPnPy-1.1.8"))
        except Exception as e:
            if type(e) == shutil.Error:
                shutil.rmtree(Path(f"{install_path}/NAT-PMP-1.3.2"))
                shutil.rmtree(Path(f"{install_path}/UPnPy-1.1.8"))
            else:
                pass

        # Patch to natpmp to work without netifaces
        with open(f"{nat_pmp_file_path}/__init__.py", "r") as f:
            lines = f.readlines()
            # Define the new function as a string
            new_function = '''
# Plucked from https://github.com/tenable/upnp_info/blob/d20a1fda8ca4877d61b89fe7126077a3a5f0b322/upnp_info.py#L23
def get_gateway_addr():
    """Returns the gateway ip of the router if upnp service is available"""
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

        with open(f"{nat_pmp_file_path}/__init__.py", "w") as f:
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
    # Try to add UDP port using NAT-PMP
    import socket
    import natpmp
    from natpmp import NATPMPUnsupportedError, NATPMPNetworkError

    try:
        natpmp.map_port(
            natpmp.NATPMP_PROTOCOL_UDP,
            43210,
            43210,
            0,
            gateway_ip=natpmp.get_gateway_addr(),
        )
        if confirm_port():
            babase.screenmessage(
                "You are now joinable from the internet", (0.2, 1, 0.2)
            )
    except (NATPMPUnsupportedError, NATPMPNetworkError):
        import upnpy
        from upnpy.exceptions import SOAPError
        from urllib.error import HTTPError 

        upnp = upnpy.UPnP()
        devices = upnp.discover()
        
        if devices == []:
            babase.screenmessage(
                "Please enable upnp service on your router", (1.00, 0.15, 0.15)
            )
            # bui.getsound('shieldDown').play() -> RuntimeError : Sound creation failed
            return
        

        local_ip = (
            (
                [
                    ip
                    for ip in socket.gethostbyname_ex(socket.gethostname())[2]
                    if not ip.startswith("127.")
                ]
                or [
                    [
                        (s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close())
                        for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]
                    ][0][1]
                ]
            )
            + ["no IP found"]
        )[0]
        try:
            for upnp_dev in devices:
                for service in upnp_dev.services:
                    if service in WAN_SERVICE_NAMES:
                        service = upnp_dev[service]
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
                                    babase.pushcall(
                                        bui.getsound("error").play(), from_other_thread=True
                                    )
                                return
                        except SOAPError:
                            if not confirm_port():
                                return
                        service.AddPortMapping(
                            NewRemoteHost="",
                            NewExternalPort=BS_PORT,
                            NewProtocol="UDP",
                            NewInternalPort=BS_PORT,
                            NewInternalClient=str(local_ip),
                            NewEnabled="1",
                            NewPortMappingDescription="Bombsquad",
                            NewLeaseDuration=0,
                        )
                        if confirm_port():
                            babase.screenmessage(
                                "You are now joinable from the internet", (0.2, 1, 0.2)
                            )
                            bui.getsound("shieldUp").play()
        except (SOAPError, HTTPError):
            babase.screenmessage('You will need to manualy add the port at the router :(')
            


@threaded
def delete_port_mapping():
    import upnpy
    from upnpy.exceptions import SOAPError

    upnp = upnpy.UPnP()
    devices = upnp.discover()
    
    if devices == []:
        return
    
    try:
        for upnp_dev in devices:
            for service in upnp_dev.services:
                if service in WAN_SERVICE_NAMES:
                    service = upnp_dev[service]
                    service.DeletePortMapping(NewRemoteHost="", NewExternalPort=BS_PORT, NewProtocol="UDP")
    except:
        pass


# ba_meta export babase.Plugin
class Joinable(babase.Plugin):
    def on_app_running(self) -> None:
        get_modules()
        if confirm_port():
            return
        else:
            add_port_mapping()
            
    def on_app_shutdown(self) -> None:
        delete_port_mapping()

    def on_app_pause(self) -> None:
        delete_port_mapping()

    def on_app_resume(self) -> None:
        add_port_mapping()
