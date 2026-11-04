import unittest
from _load import load
facts=load('trader-analyst','facts')


def fixture():
    def point(start,end,val,form='10-Q'):
        return dict(start=start,end=end,val=val,filed='2026-02-01',form=form,fy=2025,fp='FY' if form=='10-K' else 'Q',accn='0000000000-26-000001')
    eps=[point('2025-01-01','2025-03-31',1),point('2025-04-01','2025-06-30',2),point('2025-07-01','2025-09-30',3),point('2025-01-01','2025-12-31',10,'10-K')]
    return {'cik':0,'entityName':'Synthetic provenance fixture; not financial evidence','facts':{'us-gaap':{
        'Revenues':{'units':{'USD':[point('2025-10-01','2025-12-31',100,'10-K')]}},
        'NetIncomeLoss':{'units':{'USD':[point('2025-10-01','2025-12-31',10,'10-K')]}},
        'EarningsPerShareDiluted':{'units':{'USD/shares':eps}}}}}

class Provenance(unittest.TestCase):
    def test_eps_only_derived(self):
        r=facts.analyse(fixture())['rows'][0];p=r['metric_provenance']
        self.assertTrue(r['derived']);self.assertEqual(r['eps_diluted'],4)
        self.assertEqual(p['revenue']['kind'],'reported');self.assertEqual(p['eps_diluted']['kind'],'approximate')
        self.assertEqual([x['val'] for x in p['eps_diluted']['sources']],[10,1,2,3])
        self.assertEqual(p['eps_diluted']['formula'],'FY - Q1 - Q2 - Q3')
        self.assertEqual(p['net_margin']['kind'],'derived');self.assertEqual(p['operating_income']['kind'],'unknown')
        self.assertIn('weighted-average',p['eps_diluted']['note'])
    def test_reported_eps_wins(self):
        cf=fixture();a=cf['facts']['us-gaap']['EarningsPerShareDiluted']['units']['USD/shares']
        a.append(dict(a[-1],start='2025-10-01',val=3.9))
        r=facts.analyse(cf)['rows'][0]
        self.assertFalse(r['derived']);self.assertEqual(r['eps_diluted'],3.9);self.assertEqual(r['metric_provenance']['eps_diluted']['kind'],'reported')
    def test_gap_refuses_q4(self):
        cf=fixture();cf['facts']['us-gaap']['EarningsPerShareDiluted']['units']['USD/shares'][1]['start']='2025-04-03'
        self.assertIsNone(facts.analyse(cf)['rows'][0]['eps_diluted'])
    def test_wrong_unit_not_substituted(self):
        cf=fixture();node=cf['facts']['us-gaap']['Revenues']['units'];node['EUR']=node.pop('USD')
        self.assertIsNone(facts.analyse(cf)['rows'][0]['revenue'])
    def test_filed_cutoff_excludes_input(self):
        cf=fixture();filtered,_=facts.filed_before(cf,{},'2026-02-01')
        with self.assertRaises(facts.FactsError):facts.analyse(filtered)
