import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

from kce_eval.engine import atomic_new, review_template, run
from kce_eval.report import main, render_report, write_report


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fixture = {'id': 'report-case', 'family': 'test', 'split': 'test', 'track': 'target',
                   'input': {'source_text': '<script>source()</script>'}, 'rubric': {}}
        text = 'Queues say "wait"\n<script>alert(1)</script> & pause.'
        command = [sys.executable, '-c', 'import json,sys; print(json.dumps({"generated_text":sys.argv[1]}))', text]
        self.path, self.receipt = run(fixture, backend='command', model='mock', command=command, out=self.root)
        self.review = review_template(self.receipt)
        self.review['reviewer'] = '<img src=x onerror=alert(1)>'
        for name in self.review['judgments']:
            self.review['judgments'][name] = {'score': 0 if name == 'control_block_leakage' else 3,
                                           'reason': '<b>source checked</b>', 'evidence_quotes': ['"wait"\n<script>']}

    def test_output_first_and_exact_evidence(self):
        html = render_report(self.receipt, self.review)
        self.assertLess(html.index('id="model-output"'), html.index('id="scores"'))
        self.assertIn('Exact raw model response', html)
        self.assertIn('href="#decoded-output"', html)
        self.assertIn('Surrounding output context', html)
        self.assertIn('Critical gate: pass', html)
        self.assertIn('Model request wall time', html)
        self.assertNotIn('<script>', html)
        self.assertNotIn('<img ', html)
        self.assertNotIn('<b>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('&quot;wait&quot;', html)

    def test_unreviewed_and_null_are_not_pass(self):
        html = render_report(self.receipt)
        self.assertIn('Not scored', html)
        self.assertIn('(null)', html)
        self.assertNotIn('Critical gate: pass', html)
        self.review['judgments']['source_fidelity'] = None
        html = render_report(self.receipt, self.review)
        self.assertIn('Not scored</strong> (null)', html)
        self.assertIn('Critical gate: not passed', html)

    def test_rejects_tamper_and_mismatched_review_before_publish(self):
        tampered = copy.deepcopy(self.receipt)
        tampered['raw_response'] += 'tamper'
        with self.assertRaises(ValueError):
            render_report(tampered)
        for field in ('run_id', 'fixture_id', 'fixture_sha256', 'response_sha256'):
            review = copy.deepcopy(self.review)
            review[field] = 'wrong'
            review_path = self.root / (field + '.json')
            atomic_new(review_path, review)
            output = self.root / (field + '.html')
            with self.assertRaises(ValueError):
                write_report(self.path, output, review_path)
            self.assertFalse(output.exists())
        self.review['judgments']['source_fidelity']['evidence_quotes'] = ['made up']
        with self.assertRaises(ValueError):
            render_report(self.receipt, self.review)

    def test_cli_and_exclusive_output(self):
        output = self.root / 'report.html'
        self.assertEqual(main([str(self.path), '--output', str(output)]), 0)
        original = output.read_text()
        with self.assertRaises(FileExistsError):
            write_report(self.path, output)
        self.assertEqual(output.read_text(), original)

    def test_kce_json_and_failed_raw_output(self):
        fixture = copy.deepcopy(self.receipt['fixture'])
        fixture['track'] = 'kce'
        response = {'governing_concept': 'Bounded rule', 'odro': dict.fromkeys(('ontology', 'dynamics', 'regime', 'outcome'), 'valid'), 'limits': ['only under threshold']}
        _, receipt = run(fixture, backend='command', model='mock', out=self.root,
                         command=[sys.executable, '-c', 'import sys; print(sys.argv[1])', json.dumps(response)])
        html = render_report(receipt)
        self.assertIn('Parsed KCE JSON', html)
        self.assertIn('governing_concept', html)
        _, failed = run(fixture, backend='command', model='mock', out=self.root,
                        command=[sys.executable, '-c', 'print("<bad>raw</bad>")'])
        html = render_report(failed)
        self.assertIn('parse_failure', html)
        self.assertIn('&lt;bad&gt;raw&lt;/bad&gt;', html)
        self.assertNotIn('Critical gate: pass', html)


if __name__ == '__main__':
    unittest.main()
