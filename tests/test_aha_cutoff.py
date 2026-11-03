import copy
import importlib.util
from pathlib import Path
import unittest
s=importlib.util.spec_from_file_location('aha_facts',Path(__file__).parents[1]/'trader-analyst/facts.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class CutoffTests(unittest.TestCase):
    def setUp(self):
        self.f={'start':'2025-04-01','end':'2025-06-30','form':'10-Q','filed':'2025-08-01','val':100,'accn':'old','fy':2025,'fp':'Q2'}
        self.cf={'facts':{'us-gaap':{'Revenues':{'units':{'USD':[self.f]}}}}}
    def test_later_comparison_does_not_change_old_result(self):
        old=m.periods(self.cf['facts']['us-gaap']['Revenues']['units']['USD'])
        self.cf['facts']['us-gaap']['Revenues']['units']['USD'].append(dict(self.f,val=150,filed='2026-08-01',accn='new'))
        saved=copy.deepcopy(self.cf)
        filtered,_=m.filed_before(self.cf,{},'2025-08-02')
        self.assertEqual(m.periods(filtered['facts']['us-gaap']['Revenues']['units']['USD']),old)
        self.assertEqual(self.cf,saved)
        self.assertEqual(m.periods(self.cf['facts']['us-gaap']['Revenues']['units']['USD'])[(self.f['start'],self.f['end'])]['val'],150)
    def test_same_day_unknown_invalid_and_links_excluded(self):
        facts=self.cf['facts']['us-gaap']['Revenues']['units']['USD']
        facts.extend([dict(self.f,filed=x) for x in ['',None,'2025-02-30','2025-08-02','2025-08-03']])
        sub={'filings':{'recent':{'filingDate':['2025-08-03','2025-08-01'],'form':['10-Q','10-Q'],'accessionNumber':['new','old']}}}
        cf,ss=m.filed_before(self.cf,sub,'2025-08-02')
        self.assertEqual(len(cf['facts']['us-gaap']['Revenues']['units']['USD']),1)
        self.assertEqual(ss['filings']['recent']['accessionNumber'],['old'])
    def test_invalid_boundary(self):
        for d in ['2025-02-30','2025-08-02T12:00:00Z','2025-8-2',None]:
            with self.assertRaises(m.FactsError):m.filed_before({}, {},d)
