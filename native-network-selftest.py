import importlib.util,json,os,socket,tempfile
from pathlib import Path
with tempfile.TemporaryDirectory(prefix='owned-native-') as owned:
 os.environ['QUALIFICATION_UNIX_ROOTS']=json.dumps([owned]);calls=[]
 originals={name:getattr(socket.socket,name) for name in ['connect','connect_ex','sendto']};dns=socket.getaddrinfo
 for name in originals:setattr(socket.socket,name,lambda *args,**kwargs:calls.append(args))
 socket.getaddrinfo=lambda *args,**kwargs:calls.append(args)
 spec=importlib.util.spec_from_file_location('guard',Path(__file__).with_name('sitecustomize.py'));guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
 def denied(action):
  try:action()
  except RuntimeError:pass
  else:raise AssertionError('external or unowned target accepted')
 for host in ['203.0.113.1','example.com','127.evil.test','::ffff:203.0.113.1']:
  for method in ['connect','connect_ex']:
   with socket.socket() as client:denied(lambda:getattr(client,method)((host,443)))
  with socket.socket(type=socket.SOCK_DGRAM) as client:denied(lambda:client.sendto(b'x',(host,443)))
  denied(lambda:socket.getaddrinfo(host,443))
 for method in ['connect','connect_ex']:
  with socket.socket(socket.AF_UNIX) as client:denied(lambda:getattr(client,method)('/unowned.sock'))
 with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as client:denied(lambda:client.sendto(b'x','/unowned.sock'))
 assert calls==[],calls
 # Restore underlying transports while retaining guard wrappers for real admission.
 for name,original in originals.items():setattr(guard,'_original_'+name,original)
 guard._original_getaddrinfo=dns
 with socket.socket() as server:
  server.bind(('127.0.0.1',0));server.listen(2)
  for method in ['connect','connect_ex']:
   with socket.socket() as client:
    result=getattr(client,method)(server.getsockname());assert result in (None,0)
    connection,_=server.accept();connection.close()
 with socket.socket(socket.AF_UNIX) as server:
  path=str(Path(owned)/'owned.sock');server.bind(path);server.listen(1)
  with socket.socket(socket.AF_UNIX) as client:
   client.connect(path);connection,_=server.accept();connection.close()
 with socket.socket(type=socket.SOCK_DGRAM) as server:
  server.bind(('127.0.0.1',0));server.settimeout(2)
  with socket.socket(type=socket.SOCK_DGRAM) as client:assert client.sendto(b'x',server.getsockname())==1
  assert server.recv(1)==b'x'
 assert socket.getaddrinfo('localhost',1)
 print('No-transport external rejection + real owned TCP/Unix/UDP admission PASS')
