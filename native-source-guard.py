import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path('candidate').resolve();proof=Path('proof').resolve();proof.mkdir(exist_ok=True)
head='db28ae5a69c091f370c2b46e3ae8446f3a11dce8';tree='1e0ed0f40eccd902e96fffc58b1312e19c9f0b9e'
def git(*args):return subprocess.check_output(['git',*args],cwd=root)
assert git('rev-parse','HEAD').decode().strip()==head
assert git('rev-parse','HEAD^{tree}').decode().strip()==tree
manifest=proof/'frozen-gitblobs.json'
if sys.argv[1]=='create':
 files={}
 for entry in git('ls-tree','-r','-z',head).split(b'\0'):
  if not entry:continue
  meta,path=entry.split(b'\t',1);mode,kind,oid=meta.decode().split();assert kind=='blob'
  raw=git('cat-file','blob',oid);files[os.fsdecode(path)]={'mode':mode,'oid':oid,'sha256':hashlib.sha256(raw).hexdigest()}
 manifest.write_text(json.dumps({'head':head,'tree':tree,'files':files},indent=2))
j=json.loads(manifest.read_text());assert j['head']==head and j['tree']==tree
for name,record in j['files'].items():
 p=root/name;raw=os.fsencode(os.readlink(p)) if record['mode']=='120000' else p.read_bytes()
 assert hashlib.sha256(raw).hexdigest()==record['sha256'],name
assert not git('diff','HEAD','--name-only').strip()
print('Frozen Gitblob guard PASS',len(j['files']))
