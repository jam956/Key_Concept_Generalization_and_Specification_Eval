"""Predefined encoding/decoding profiles. Planning is the default; inference is explicit."""
import argparse
import json
from pathlib import Path
from .engine import load,validate_fixture,run

ROOT=Path(__file__).resolve().parents[1]
def plan(name,root=ROOT):
    profile=load(Path(root)/'suites'/(name+'.json'))
    fixtures=[]
    for relative in profile['fixture_paths']:
        path=(Path(root)/relative).resolve()
        if not path.is_relative_to(Path(root).resolve()):raise ValueError('Suite fixture escapes repository')
        if not path.is_file():raise ValueError('Missing fixture '+relative+'; export the optional Kissinger fixture as documented')
        f=validate_fixture(load(path))
        expected='kce' if name=='encoding' else 'article'
        if f['track']!=expected:raise ValueError('Wrong track in governing suite')
        fixtures.append((path,f))
    return profile,fixtures

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('suite',choices=['encoding','decoding']);p.add_argument('--execute',action='store_true');p.add_argument('--backend',choices=['command','ollama']);p.add_argument('--model');p.add_argument('--out',type=Path);p.add_argument('--command-json');a=p.parse_args()
    profile,fixtures=plan(a.suite)
    if not a.execute:
        print(json.dumps({'profile':profile,'resolved_fixtures':[str(path.relative_to(ROOT)) for path,_ in fixtures],'inference_performed':False},indent=2));return
    if not a.backend or not a.model or a.out is None:p.error('Execution needs backend, model and out')
    failed=False
    for _,fixture in fixtures:
        path,receipt=run(fixture,backend=a.backend,model=a.model,out=a.out,command=json.loads(a.command_json) if a.command_json else None)
        print(json.dumps({'result':str(path),'status':receipt['status']}));failed=failed or receipt['status']!='success'
    if failed:raise SystemExit(1)
if __name__=='__main__':main()
