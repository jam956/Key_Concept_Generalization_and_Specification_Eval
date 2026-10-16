import json
from pathlib import Path
import unittest
from kce_eval.engine import prompt,validate_fixture,validate_response

BASE=Path(__file__).resolve().parents[1]
class FixtureTests(unittest.TestCase):
    def test_original_suite_is_inspectable_and_review_annotations_stay_out_of_prompts(self):
        fixtures=[json.loads(p.read_text()) for p in (BASE/'fixtures').glob('*.json')]
        self.assertGreaterEqual(len(fixtures),9)
        self.assertEqual(len({f['id'] for f in fixtures}),len(fixtures))
        splits={}
        for fixture in fixtures:
            validate_fixture(fixture)
            splits.setdefault(fixture['split'],set()).add(fixture['family'])
            enriched={**fixture,'rubric':{**fixture['rubric'],'private_reference':'DO_NOT_REVEAL_GOLD_43D8'}}
            self.assertNotIn('DO_NOT_REVEAL_GOLD_43D8',json.dumps(prompt(enriched)))
            self.assertIn('[s1]',fixture['input']['source_text'])
        self.assertFalse(splits['dev']&splits['validation'])
        self.assertEqual({f['track'] for f in fixtures},{'kce','target','article'})

if __name__=='__main__':unittest.main()
