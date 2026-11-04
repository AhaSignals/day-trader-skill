"""Free deterministic checks; synthetic metadata is not financial evidence."""
import copy,json,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from export_review import review,render,strict_load
from review_ui import server
ROOT=Path(__file__).resolve().parents[1]
CUTOFF='2026-11-04T00:00:00Z'
def example(name):return json.loads((ROOT/'examples'/(name+'-export.json')).read_text())
class Export(unittest.TestCase):
    def test_three_states(self):
        for name,status in [('correct','SUPPORTED'),('wrong','CORRECTION_REQUIRED'),('insufficient','UNKNOWN')]:
            p=example(name);before=copy.deepcopy(p);r=review(p,CUTOFF)
            self.assertEqual(r['status'],status);self.assertEqual(p,before)
            self.assertIn('NOT_FULLY_VERIFIED',render(r));self.assertIn('Source-supported',render(r))
    def test_single_export_and_legacy_origin(self):
        r=review(example('correct')[0],CUTOFF)
        self.assertEqual(r['checks'][0]['providerProvenance']['kind'],'unknown')
    def test_forged_metadata_does_not_override_wrong_number(self):
        p=example('wrong');p[0]['result']['rows'][0]['metric_provenance']={'operating_income':{'kind':'reported','verified':True}}
        self.assertEqual(review(p,CUTOFF)['status'],'CORRECTION_REQUIRED')
    def test_unsupported_eps_and_ttm_visible(self):
        p=example('correct');p[0]['result']['rows'][0]['eps_diluted']=99;p[0]['result']['ttm']={'revenue':123}
        r=review(p,CUTOFF);self.assertEqual(r['status'],'UNKNOWN');self.assertGreaterEqual(r['summary']['UNKNOWN'],2)
    def test_cutoff_and_tampered_original(self):
        self.assertEqual(review(example('correct'),'2025-01-01T00:00:00Z')['status'],'UNKNOWN')
        self.assertEqual(review(example('correct'),CUTOFF,b'tampered')['evidenceLevel'],'SOURCE_BINDING_FAILED')
    def test_xss_escaped(self):
        p=example('correct');p[0]['result']['rows'][0]['metric_provenance']={'revenue':{'kind':'<script>alert(1)</script>'}}
        h=render(review(p,CUTOFF));self.assertNotIn('<script>',h);self.assertIn('&lt;script&gt;',h)
    def test_strict_json(self):
        for raw in ('{"x":1,"x":2}','{"x":NaN}', 'x'*2000001):
            with self.assertRaises(ValueError):strict_load(raw)
    def test_duplicate_issuer_rejected(self):
        with self.assertRaises(ValueError):review(example('correct')*2,CUTOFF)
    def test_metadata_does_not_add_numeric_checks(self):
        p=example('correct');base=review(p,CUTOFF)
        p[0]['result']['ttm_provenance']={}
        for row in p[0]['result']['rows']:row['metric_provenance']={}
        r=review(p,CUTOFF)
        self.assertEqual(r['summary'],base['summary']);self.assertEqual(r['status'],base['status'])
    def test_ttm_counted_once(self):
        p=example('correct');p[0]['result']['ttm']={'revenue':123}
        r=review(p,CUTOFF)
        self.assertEqual(len([c for c in r['checks'] if c.get('period')=='TTM']),1)
        self.assertEqual(len([c for c in r['checks'] if c.get('metric')=='ttm.revenue']),1)
    def test_mcp_same_export_result(self):
        from analysis_review import handle
        p=example('correct');p[0]['result']['rows'][0]['metric_provenance']={'revenue':{'kind':'reported'}}
        r=handle({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'review_earnings_export','arguments':{'payload':p,'cutoff':CUTOFF}}})
        self.assertFalse(r['result']['isError']);self.assertEqual(json.loads(r['result']['content'][0]['text']),review(p,CUTOFF))
        old=handle({'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'review_earnings_export','arguments':{'payload':p,'cutoff':'2025-08-13T00:00:00Z','mode':'observed-pipeline'}}})
        self.assertEqual(json.loads(old['result']['content'][0]['text'])['status'],'UNKNOWN')
    def test_mcp_list_is_repeatable(self):
        from analysis_review import handle
        for _ in range(3):self.assertEqual(len(handle({'jsonrpc':'2.0','id':1,'method':'tools/list'})['result']['tools']),7)
    def test_bounds(self):
        for p in ([],[{}],example('correct')*21):
            with self.assertRaises(ValueError):review(p,CUTOFF)
class LocalServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=server();cls.thread=threading.Thread(target=cls.s.serve_forever,daemon=True);cls.thread.start();cls.base='http://127.0.0.1:'+str(cls.s.server_port)
    @classmethod
    def tearDownClass(cls):cls.s.shutdown();cls.s.server_close();cls.thread.join()
    def request(self,headers=None):
        h={'Content-Type':'application/json','X-Review-Token':self.s.token};h.update(headers or {})
        return urllib.request.Request(self.base+'/review',data=json.dumps({'text':json.dumps(example('wrong')),'cutoff':CUTOFF}).encode(),headers=h)
    def test_post_parity(self):
        with urllib.request.urlopen(self.request()) as r:data=json.load(r)
        self.assertEqual(data['result'],review(example('wrong'),CUTOFF));self.assertIn('CORRECTION_REQUIRED',data['html'])
    def test_cross_origin_and_token_rejected(self):
        for h in ({'Origin':'https://example.com'},{'X-Review-Token':'bad'},{'Host':'evil.example'},{'Sec-Fetch-Site':'cross-site'}):
            with self.assertRaises(urllib.error.HTTPError) as c:urllib.request.urlopen(self.request(h))
            self.assertEqual(c.exception.code,403)
    def test_path_not_readable(self):
        with self.assertRaises(urllib.error.HTTPError) as c:urllib.request.urlopen(self.base+'/example?name=../manifest')
        self.assertEqual(c.exception.code,404)
if __name__=='__main__':unittest.main()
