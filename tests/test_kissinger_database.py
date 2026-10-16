"""Boundary regression tests: source removal must preserve analytical addresses."""
import unittest
import json
from kce_eval.kissinger_database import clean, POINTER, validate_route_sequences

class SanitizationTests(unittest.TestCase):
    def test_nested_source_payload_removed_without_graph_loss(self):
        original={'subject':'unequal alliance capabilities','source_url':'https://example.org/book.pdf',
                  'nested':{'source_span':'verbatim source prose','quote':'copied passage','invariant_id':'political::coupling_opposition'},
                  'operator_sequence':['work::operator::capacity','work::operator::legitimacy']}
        self.assertEqual(clean(original),{'subject':'unequal alliance capabilities',
            'nested':{'invariant_id':'political::coupling_opposition'},
            'operator_sequence':['work::operator::capacity','work::operator::legitimacy']})
        self.assertIn('source_url',original)

    def test_route_labels_resolve_within_work_not_as_primary_keys(self):
        route={'work_key':'work-a','operator_sequence_json':json.dumps(['diagnose','reframe'])}
        operators=[{'work_key':'work-a','operator_id':'diagnose','operator_key':'work-a::diagnose'},
                   {'work_key':'work-a','operator_id':'reframe','operator_key':'work-a::reframe'}]
        validate_route_sequences([route],operators)
        self.assertEqual(json.loads(route['operator_sequence_json']),['diagnose','reframe'])
        with self.assertRaisesRegex(ValueError,'Unresolved route'):
            validate_route_sequences([route],[dict(r,work_key='work-b') for r in operators])

    def test_document_addresses_removed(self):
        for pointer in ['/Users/example/book.pdf','gdrive://document-id','https://example.org/article','Expressions/project/source.pdf']:
            with self.subTest(pointer=pointer):self.assertEqual(clean(pointer),'')

    def test_meaning_and_stable_graph_addresses_survive(self):
        text='Technical feasibility does not settle political legitimacy.'
        self.assertEqual(clean(text),text)
        self.assertEqual(clean('kissinger_strains_1963::operator::legitimacy'),'kissinger_strains_1963::operator::legitimacy')
        self.assertIsNone(POINTER.search(text))

if __name__=='__main__':unittest.main()
