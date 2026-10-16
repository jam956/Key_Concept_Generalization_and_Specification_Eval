import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from io import BytesIO, StringIO
from contextlib import redirect_stdout
from kce_eval.__main__ import main
from kce_eval.engine import atomic_new, canonical, digest, prompt, review_template, run, score, summarize


class EngineTests(unittest.TestCase):
    def fixture(self, track='target'):
        return {'id':'case-1','family':'boundary','split':'test','track':track,'input':{'source_text':'A valve closes only above threshold.', 'target_task':'Apply to queues.'}, 'rubric':{'reference_answer':'SECRET_REFERENCE_999'}, 'reference_answers':['ALSO_PRIVATE'], 'control_markers':['PRIVATE_CANARY_7288']}

    def receipt(self, text='Queues pause above the threshold.'):
        with tempfile.TemporaryDirectory() as d:
            command = [sys.executable,'-c','import json,sys; request=json.load(sys.stdin); print(json.dumps({"generated_text":sys.argv[1]}))',text]
            path, result = run(self.fixture(),backend='command',command=command,model='fake',out=d)
            self.assertEqual(json.loads(path.read_text()),result)
            return result

    def review(self, result):
        value = review_template(result)
        value['reviewer'] = 'human-test'
        for key in value['judgments']:
            value['judgments'][key] = {'score':0 if key == 'control_block_leakage' else 3,'reason':'Reviewed against source conditions.','evidence_quotes':['Queues']}
        return value

    def test_prompt_allowlist(self):
        value = canonical(prompt(self.fixture()))
        self.assertNotIn('SECRET_REFERENCE',value)
        self.assertNotIn('ALSO_PRIVATE',value)
        self.assertNotIn('rubric',value)
        self.assertIn('PRIVATE_CANARY',value)
        self.assertNotIn('reference_answers',value)

    def test_fake_subprocess_and_failure_receipt(self):
        r = self.receipt()
        self.assertEqual(r['status'],'success')
        self.assertIsNone(r['timing']['time_to_first_text_seconds'])
        with tempfile.TemporaryDirectory() as d:
            path, failed = run(self.fixture(),backend='command',command=[sys.executable,'-c','import sys; print("unusable"); sys.stderr.write("private error"); sys.exit(7)'],model='fake',out=d)
            self.assertTrue(path.exists())
            self.assertEqual(failed['status'],'process_failure')
            self.assertNotIn('stderr',failed)
            self.assertEqual(failed['stderr_sha256'],digest('private error'))
            self.assertEqual(failed['raw_response'],'unusable\n')

    def test_parse_and_schema_failures_not_repaired(self):
        for content, expected in [('```json {} ```','parse_failure'),('{}','schema_failure'),('{"generated_text":7}','schema_failure')]:
            with tempfile.TemporaryDirectory() as d:
                _, r = run(self.fixture(),backend='command',command=[sys.executable,'-c','import sys; print(sys.argv[1])',content],model='fake',out=d)
                self.assertEqual(r['status'],expected)

    def test_null_is_unassessed(self):
        r = self.receipt(); review = self.review(r)
        review['judgments']['source_fidelity'] = None
        s = score(r,review)
        self.assertFalse(s['complete']); self.assertFalse(s['critical_gate_pass'])
        self.assertIsNone(s['dimensions']['source_fidelity']['score'])
        self.assertIsNone(summarize([s])['dimensions']['target/source_fidelity']['mean'])

    def test_review_integrity_guards(self):
        r = self.receipt(); good = self.review(r)
        mutations = [lambda v:v.update(run_id='wrong'),lambda v:v.update(fixture_sha256='wrong'),lambda v:v['judgments'].pop('source_fidelity'),lambda v:v['judgments']['source_fidelity'].update(score=True),lambda v:v['judgments']['source_fidelity'].update(reason=''),lambda v:v['judgments']['source_fidelity'].update(evidence_quotes=['fabricated text']),lambda v:v.update(critical_errors=[{'kind':'leak','evidence_quote':'fabricated text'}]),lambda v:v['judgments']['control_block_leakage'].update(score=1,evidence_quotes=[])]
        for mutate in mutations:
            bad = copy.deepcopy(good); mutate(bad)
            with self.assertRaises(ValueError): score(r,bad)
        tampered = copy.deepcopy(r); tampered['raw_response'] = 'changed'
        with self.assertRaises(ValueError): score(tampered,good)
        tampered = copy.deepcopy(r); tampered['fixture']['rubric']['reference_answer'] = r['raw_response']
        with self.assertRaises(ValueError): score(tampered,good)

    def test_critical_errors_retained_and_dimension_means_separate(self):
        r = self.receipt(); review = self.review(r)
        review['critical_errors'] = [{'kind':'unsupported transfer','evidence_quote':'Queues'}]
        s = score(r,review)
        self.assertEqual(s['critical_errors'],review['critical_errors'])
        self.assertFalse(s['critical_gate_pass'])
        summary = summarize([s])
        self.assertEqual(summary['dimensions']['target/control_block_leakage']['mean'],0)
        self.assertEqual(summary['dimensions']['target/source_fidelity']['mean'],3)
        self.assertNotIn('aggregate_score',summary)

    def test_control_marker_only_public_field(self):
        r = self.receipt('Ontology regime remains ordinary prose.')
        self.assertEqual(r['mechanical_checks']['control_markers_in_generated_text'],[])
        r = self.receipt('PRIVATE_CANARY_7288')
        self.assertEqual(r['mechanical_checks']['control_markers_in_generated_text'],['PRIVATE_CANARY_7288'])
        self.assertEqual(review_template(r)['judgments']['control_block_leakage'],None)

    def test_escaped_generated_quotes_supported(self):
        r = self.receipt('Queues say "wait"\nthen pause.')
        review = self.review(r)
        review['judgments']['source_fidelity']['evidence_quotes'] = ['"wait"\nthen']
        self.assertTrue(score(r,review)['complete'])

    def test_ollama_url_guard(self):
        for url in ('http://127.0.0.1:80@evil/api/chat', 'http://evil:11434/api/chat', 'http://localhost/api/chat', 'http://localhost:99999/api/chat', 'http://user@localhost:11434/api/chat'):
            with tempfile.TemporaryDirectory() as d, self.assertRaises(ValueError):
                run(self.fixture(), backend='ollama', model='fake', out=d, url=url)

    def test_ollama_envelope_checks_and_metadata(self):
        base = {'model':'actual-model', 'done':True, 'done_reason':'stop', 'eval_count':22, 'load_duration':123, 'message':{'role':'assistant', 'content':json.dumps({'generated_text':'Queues pause.'})}}
        variants = [(base, 'success')]
        for change in ({'done':False}, {'done_reason':'length'}, {'message':dict(base['message'], tool_calls=[{'function':{'name':'x'}}])}, {'message':dict(base['message'], thinking='PRIVATE_CHAIN')}):
            variants.append((dict(base, **change), 'envelope_failure'))
        for envelope, status in variants:
            with tempfile.TemporaryDirectory() as d, patch('kce_eval.engine.urllib.request.urlopen', return_value=BytesIO(json.dumps(envelope).encode())) as mocked:
                path, result = run(self.fixture(), backend='ollama', model='fake', out=d)
                self.assertEqual(result['status'],status)
                self.assertTrue(path.exists())
                self.assertEqual(result['ollama_metadata']['model'],'actual-model')
                self.assertEqual(result['ollama_metadata']['eval_count'],22)
                self.assertNotIn('PRIVATE_CHAIN',canonical(result))
                sent = json.loads(mocked.call_args.args[0].data)
                self.assertEqual(sent['options'], {'temperature':0.2,'seed':417,'num_ctx':16384,'num_predict':1800})
                self.assertEqual(sent['format'],'json')

    def test_summary_rejects_mixed_models(self):
        result = self.receipt()
        first = score(result,self.review(result))
        second = copy.deepcopy(first)
        second['model_config']['model'] = 'other-model'
        with self.assertRaises(ValueError): summarize([first,second])

    def test_failed_review_cannot_inflate_semantic_means(self):
        successful = self.receipt()
        good_review = self.review(successful)
        good_review['judgments']['source_fidelity']['score'] = 1
        failed = copy.deepcopy(successful)
        failed['run_id'] = 'failed-run'
        failed['status'] = 'process_failure'
        failed_review = self.review(failed)
        failed_score = score(failed,failed_review)
        self.assertEqual(failed_score['dimensions']['source_fidelity']['score'],3)
        summary = summarize([score(successful,good_review),failed_score])
        dimension = summary['dimensions']['target/source_fidelity']
        self.assertEqual(dimension['mean'],1)
        self.assertEqual(dimension['assessed'],1)
        self.assertEqual(dimension['excluded_failed_runs'],1)
        self.assertEqual(summary['excluded_failed_runs'],1)
        self.assertEqual(summary['reviewed_run_status_counts'],{'success':1,'process_failure':1})

    def test_cli_counts_unreviewed_failures(self):
        failed = self.receipt()
        failed['status'] = 'parse_failure'
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            atomic_new(root/'results'/'one'/'run.json',failed)
            (root/'reviews').mkdir()
            output = StringIO()
            with redirect_stdout(output):
                code = main(['summarize',str(root/'results'),str(root/'reviews')])
            self.assertEqual(code,0)
            summary = json.loads(output.getvalue())
            self.assertEqual(summary['all_run_status_counts'],{'parse_failure':1})
            self.assertEqual(summary['unreviewed_run_status_counts'],{'parse_failure':1})
            self.assertEqual(summary['runs_without_review'],1)

    def test_atomic_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'receipt.json'; atomic_new(p,{'first':1})
            with self.assertRaises(FileExistsError): atomic_new(p,{'second':2})
            self.assertEqual(json.loads(p.read_text()),{'first':1})

if __name__ == '__main__': unittest.main()
