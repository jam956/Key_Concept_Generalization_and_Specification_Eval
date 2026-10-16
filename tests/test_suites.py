import unittest
from kce_eval.suite import plan,ROOT
class SuiteTests(unittest.TestCase):
    def test_encoding_is_only_kce(self):
        profile,fixtures=plan('encoding')
        self.assertEqual(len(fixtures),6)
        self.assertTrue(all(f['track']=='kce' for _,f in fixtures))
        self.assertNotIn('target_generation',profile['dimensions'])
    def test_decoding_is_predefined_article_and_missing_assets_fail_explicitly(self):
        import json,tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'suites').mkdir()
            profile=json.loads((ROOT/'suites/decoding.json').read_text())
            (root/'suites/decoding.json').write_text(json.dumps(profile))
            with self.assertRaisesRegex(ValueError,'Missing fixture'):plan('decoding',root)
