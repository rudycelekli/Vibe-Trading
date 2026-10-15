import json,os,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
root=Path('candidate').resolve();proof=Path('proof').resolve();proof.mkdir(exist_ok=True)
owned=proof/'owned-temp';owned.mkdir(exist_ok=True)
base='29aa084fb7866087c612ddd55ef5449824374e22';head='db28ae5a69c091f370c2b46e3ae8446f3a11dce8';results=[]
def guard():subprocess.run([sys.executable,'harness/native-source-guard.py','verify'],check=True)
def run(name,args):
 t=time.monotonic();r=subprocess.run(args,cwd=root,env={**os.environ,'PYTHONPATH':os.pathsep.join([str(Path('harness').resolve()),str(root/'agent')]),'TMPDIR':str(owned),'QUALIFICATION_UNIX_ROOTS':json.dumps([str(root),str(proof)])},capture_output=True,text=True,timeout=900);(proof/(name+'.log')).write_text(r.stdout+r.stderr);results.append({'name':name,'status':r.returncode,'seconds':time.monotonic()-t,'command':args});return r
files=['agent/backtest/loaders/base.py','agent/backtest/loaders/local_loader.py'];saved={f:(root/f).read_bytes() for f in files};before=False
guard()
try:
 for f in files:(root/f).write_bytes(subprocess.check_output(['git','show',base+':'+f],cwd=root))
 r=run('before', [sys.executable,'-m','pytest','agent/tests/test_local_loader_source_revision.py','-k','rewritten or deleted or wal','-q','--junitxml='+str(proof/'before.xml')])
 xml=ET.parse(proof/'before.xml');cases=xml.findall('.//testcase')
 expected={**{f'test_rewritten_local_source_invalidates_persisted_bars[{kind}]':('assert [10.0] == [20]',':69: AssertionError') for kind in ['csv','parquet','duckdb']},**{f'test_deleted_local_source_does_not_replay_previous_bars[{kind}]':('assert {',':90: AssertionError') for kind in ['csv','parquet','duckdb']},'test_duckdb_wal_revision_participates_in_source_identity':('assert revision(entry) != before',':105: AssertionError')}
 before=r.returncode==1 and len(cases)==7 and {c.get('name') for c in cases}==set(expected)
 for c in cases:
  failure=c.find('failure');text='' if failure is None else ''.join(failure.itertext());tokens=expected.get(c.get('name'),())
  before=before and failure is not None and c.find('error') is None and failure.get('type')=='AssertionError' and all(token in text for token in tokens)
 assert before,'Expected seven exact stale-source assertions; inspect before.xml'

finally:
 for f,raw in saved.items():(root/f).write_bytes(raw)
guard()
local=['agent/tests/test_local_loader_source_revision.py','agent/tests/test_local_loader_cache_identity.py','agent/tests/test_local_loader.py','agent/tests/test_local_loader_interval_case.py','agent/tests/test_local_loader_end_day.py']
run('local', [sys.executable,'-m','pytest',*local,'-q']);guard()
callers=[]
for f in (root/'agent/tests').rglob('*.py'):
 if any(word in f.read_text() for word in ['loader_cache_get','loader_cache_put','cached_loader_fetch']):callers.append(str(f.relative_to(root)))
run('callers',[sys.executable,'-m','pytest',*sorted(callers),'-q']);guard()
run('safety',['bash','tools/ci_grep_gates.sh']);run('env',[sys.executable,'-m','pytest','tools/test_ci_env_var_gate.py','-q']);guard()
run('syntax',[sys.executable,'-m','py_compile',*files,'agent/tests/test_local_loader_source_revision.py']);guard()
status='PASS' if before and all(x['status']==0 for x in results if x['name']!='before') else 'FAIL'
(proof/'receipt.json').write_text(json.dumps({'status':status,'head':head,'before_causal_valid':before,'results':results,'source_unchanged':True,'python':sys.version},indent=2));sys.exit(status!='PASS')
