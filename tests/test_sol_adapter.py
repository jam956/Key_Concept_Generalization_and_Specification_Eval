import contextlib
import importlib.util
import io
import json
from pathlib import Path
import types
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('sol_adapter',Path(__file__).resolve().parents[1]/'adapters/sol_cli.py')
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)

class AdapterTests(unittest.TestCase):
    def run_case(self,events,returncode=0):
        def subprocess_run(cmd,**kwargs):
            self.assertFalse(kwargs['shell']);self.assertIn('--ephemeral',cmd)
            Path(cmd[cmd.index('-o')+1]).write_text('{"generated_text":"A test utterance."}')
            return types.SimpleNamespace(returncode=returncode,stdout='\n'.join(json.dumps(e) for e in events))
        request=json.dumps({'model':'test-only','messages':[{'role':'user','content':'fixture'}]})
        output=io.StringIO()
        with patch.object(M.sys,'stdin',io.StringIO(request)),patch.object(M.subprocess,'run',side_effect=subprocess_run),contextlib.redirect_stdout(output):M.main()
        return output.getvalue()
    def test_stateless_completion_is_forwarded_without_extra_output(self):
        self.assertEqual(json.loads(self.run_case([{'type':'turn.completed'}]))['generated_text'],'A test utterance.')
    def test_tools_or_missing_completion_cannot_become_accepted_response(self):
        for events in [[],[{'type':'turn.failed'}],[{'type':'item.completed','item':{'type':'command_execution'}},{'type':'turn.completed'}]]:
            with self.assertRaises(RuntimeError):self.run_case(events)

if __name__=='__main__':unittest.main()
