import unittest
from kce_eval.engine import summarize

class RateTests(unittest.TestCase):
    def test_error_frequency_uses_assessed_successes_and_never_mix_dimensions(self):
        def entry(over,under,status='success'):
            return {'model_config':{'model':'mock'},'run_status':status,'track':'kce','complete':False,'critical_gate_pass':False,'dimensions':{'overgeneralization':{'kind':'severity','score':over},'undergeneralization':{'kind':'severity','score':under}}}
        result=summarize([entry(0,2),entry(1,0),entry(None,None),entry(3,3,'process_failure')])
        over=result['dimensions']['kce/overgeneralization'];under=result['dimensions']['kce/undergeneralization']
        self.assertEqual(over['case_error_rate'],0.5);self.assertEqual(under['case_error_rate'],0.5)
        self.assertEqual(over['mean'],0.5);self.assertEqual(under['mean'],1)
        self.assertEqual(over['unassessed'],1);self.assertEqual(over['excluded_failed_runs'],1)

if __name__=='__main__':unittest.main()
