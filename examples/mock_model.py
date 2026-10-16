"""Deterministic adapter smoke only; never a real model or benchmark score."""
import json
import sys

request=json.load(sys.stdin)
task=json.loads(request['messages'][-1]['content'])
if task['track']=='kce':
    value={'governing_concept':'Mock transport demonstration, not an extraction.','odro':{'ontology':'Unknown: mock.','dynamics':'Unknown: mock.','regime':'Unknown: mock.','outcome':'Unknown: mock.'},'limits':['No model inference occurred.']}
else:value={'generated_text':'Mock transport demonstration. No model inference occurred.'}
print(json.dumps(value))
