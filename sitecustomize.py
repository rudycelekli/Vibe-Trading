"""Qualification socket confinement; loaded in every Python test subprocess."""
import ipaddress,json,os,socket
from pathlib import Path
roots=[Path(p).resolve() for p in json.loads(os.environ.get('QUALIFICATION_UNIX_ROOTS','[]'))]
def loopback(host):
    if isinstance(host,bytes):host=host.decode('ascii')
    if host=='localhost':return True
    try:return ipaddress.ip_address(host).is_loopback
    except ValueError:return False

def admit(sock,address):
    if sock.family==socket.AF_UNIX:
        path=Path(os.fsdecode(address)).resolve()
        if not any(path==root or root in path.parents for root in roots):raise RuntimeError('qualification denies unowned Unix socket')
    elif sock.family not in (socket.AF_INET,socket.AF_INET6) or not isinstance(address,tuple) or not loopback(address[0]):raise RuntimeError('qualification denies external network')
_original_connect=socket.socket.connect
_original_connect_ex=socket.socket.connect_ex
_original_sendto=socket.socket.sendto
_original_getaddrinfo=socket.getaddrinfo
def connect(self,address):
    admit(self,address)
    return _original_connect(self,address)
def connect_ex(self,address):
    admit(self,address)
    return _original_connect_ex(self,address)
def sendto(self,data,*args):
    admit(self,args[-1])
    return _original_sendto(self,data,*args)
def getaddrinfo(host,*args,**kwargs):
    if host is not None and not loopback(host):raise RuntimeError('qualification denies external DNS')
    return _original_getaddrinfo(host,*args,**kwargs)
socket.socket.connect=connect
socket.socket.connect_ex=connect_ex
socket.socket.sendto=sendto
socket.getaddrinfo=getaddrinfo
