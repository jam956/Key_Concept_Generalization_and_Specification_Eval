"""Optional command adapter; requires a separately authenticated Codex CLI."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

def main():
    request=json.load(sys.stdin)
    model=request['model'];messages=request['messages']
    if not isinstance(model,str) or not model.strip() or not isinstance(messages,list):raise ValueError('Invalid command-adapter request')
    with tempfile.TemporaryDirectory(prefix='kce-eval-isolated-') as folder:
        out=Path(folder)/'last.txt'
        cmd=['codex','exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','-C',folder,'-m',model,'-c','model_reasoning_effort="low"','-s','read-only','--json','-o',str(out),'-']
        body='Execute the final request in the serialized conversation. Do not use tools, files, network, inherited memory or other context. Return only the requested JSON result; do not disclose private reasoning.\n'+json.dumps(messages,ensure_ascii=False)
        result=subprocess.run(cmd,input=body,text=True,capture_output=True,timeout=110,shell=False)
        if result.returncode:raise RuntimeError('SOL CLI returned a failure; no content accepted')
        completed=False
        for line in result.stdout.splitlines():
            try:event=json.loads(line)
            except ValueError:continue
            if event.get('type')=='turn.completed':completed=True
            if event.get('type') in ('turn.failed','error'):raise RuntimeError('SOL CLI turn failed')
            if event.get('item',{}).get('type') in ('command_execution','mcp_tool_call','web_search'):raise RuntimeError('SOL used prohibited tools')
        if not completed or not out.exists():raise RuntimeError('SOL CLI completion unavailable')
        text=out.read_text();json.loads(text)
        print(text)

if __name__=='__main__':
    try:main()
    except Exception as error:
        print(type(error).__name__+': adapter failed; no model response accepted',file=sys.stderr)
        raise SystemExit(1)
