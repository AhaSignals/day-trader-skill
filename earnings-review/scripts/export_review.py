"""Import an upstream facts.py JSON export and render a local, source-linked report.

No model calls, network retrieval or changes to the input file.
"""
import argparse
import copy
import hashlib
import html
import json
from pathlib import Path
from urllib.parse import urlsplit
from run import activate
activate()
from ahasignals_pit.earnings_review import review_earnings_export, clock

METRICS = ('revenue','cost_of_revenue','gross_profit','operating_income','net_income','eps_diluted','gross_margin','operating_margin','net_margin','revenue_yoy','net_income_yoy','eps_yoy','operating_cash_flow','free_cash_flow')
CSS = '''body{font:16px/1.65 system-ui,sans-serif;background:#f7f8f5;color:#111714;margin:0}main{max-width:1080px;margin:auto;padding:44px 24px}h1{font-size:clamp(28px,5vw,44px);line-height:1.15;letter-spacing:-.03em}h2{font-size:22px}a{color:#087653}section,article{background:white;padding:24px;border-radius:18px;margin:20px 0;box-shadow:0 12px 32px #102c2908}header p{max-width:760px}.meta,small{color:#5b665f}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.6 monospace}code{overflow-wrap:anywhere}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}td,th{text-align:left;padding:12px;border-bottom:1px solid #d7ded9;vertical-align:top}td:last-child{min-width:170px}.SUPPORTED{color:#087653}.CORRECTION_REQUIRED{color:#9a3e28}.UNKNOWN{color:#53636b}summary,button,input{min-height:44px}summary{cursor:pointer}button{background:#087653;color:white;border:0;border-radius:10px;padding:10px 16px;font:inherit;cursor:pointer}input{font:inherit;max-width:100%}label{display:block;margin:15px 0}a:focus-visible,summary:focus-visible,button:focus-visible,input:focus-visible{outline:3px solid #087653;outline-offset:3px}.number{font-family:monospace}footer{margin:32px 0;color:#5b665f}@media(max-width:600px){main{padding:24px 14px}article,section{padding:18px}}'''


def strict_load(raw):
    if len(raw)>2000000: raise ValueError('Export exceeds 2 MB')
    def pairs(items):
        result={}
        for k,v in items:
            if k in result: raise ValueError('Duplicate JSON key')
            result[k]=v
        return result
    def invalid(x): raise ValueError('Non-finite value')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)


def review(payload,cutoff,source=None,mode='disclosure-reconstruction',analysis=''):
    clock(cutoff)
    if isinstance(payload,dict) and 'result' in payload: payload=[payload]
    if not isinstance(payload,list) or not 1<=len(payload)<=20: raise ValueError('Expected upstream JSON array or one export object')
    count=0
    issuers=set()
    for entry in payload:
        if not isinstance(entry,dict) or not isinstance(entry.get('result'),dict): raise ValueError('Missing result object')
        cik=str(entry['result'].get('cik','')).zfill(10)
        if cik in issuers: raise ValueError('Use one export per CIK; combine its rows first')
        issuers.add(cik)
        rows=entry['result'].get('rows')
        if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows): raise ValueError('Missing rows')
        if not isinstance(entry['result'].get('ttm',{}),dict): raise ValueError('Invalid TTM')
        count+=len(rows)
    if count>100: raise ValueError('At most 100 rows')
    engine_payload=copy.deepcopy(payload)
    for entry in engine_payload:
        entry['result'].pop('ttm_provenance',None)
        for row in entry['result']['rows']: row.pop('metric_provenance',None)
    result=review_earnings_export(engine_payload,cutoff,source,mode,analysis)
    result['reviewedInputSha256']=result['inputSha256']
    result['inputSha256']=hashlib.sha256(json.dumps(payload,ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    checks=result['checks']
    # No upgraded trust from imported metadata. These labels describe the provider's
    # extraction path, independently of the pinned engine's numeric verdict.
    for entry in payload:
        data=entry['result'];cik=str(data.get('cik','')).zfill(10)
        for n,row in enumerate(data['rows']):
            prov=row.get('metric_provenance',{})
            if not isinstance(prov,dict): raise ValueError('Invalid metric provenance')
            for metric in METRICS:
                if row.get(metric) is None: continue
                matched=[c for c in checks if str(c.get('cik','')).zfill(10)==cik and c.get('row')==n and c.get('metric')==metric]
                if not matched:
                    check={'cik':cik,'row':n,'metric':metric,'suppliedValue':row[metric],'start':row.get('start'),'end':row.get('end'),'status':'UNKNOWN','reason':'METRIC_OR_CONTEXT_NOT_REVIEWED'}
                    checks.append(check);matched=[check]
                for check in matched:
                    check['providerProvenance']=prov.get(metric,{'kind':'unknown','reason':'Legacy export has no metric-level provenance; row-level derived flag is not sufficient'})
                    check['provenanceTrust']='IMPORTED_METADATA_NOT_INDEPENDENTLY_VERIFIED'
        ttm_prov=data.get('ttm_provenance',{})
        if not isinstance(ttm_prov,dict): raise ValueError('Invalid TTM provenance')
        for check in checks:
            metric=check.get('metric','')
            if check.get('cik')==cik and metric.startswith('ttm.'):
                check.update(period='TTM',providerProvenance=ttm_prov.get(metric[4:],{'kind':'unknown'}),provenanceTrust='IMPORTED_METADATA_NOT_INDEPENDENTLY_VERIFIED')
    result['status']='CORRECTION_REQUIRED' if any(c['status']=='CORRECTION_REQUIRED' for c in checks) else 'UNKNOWN' if any(c['status']=='UNKNOWN' for c in checks) or not checks else 'SUPPORTED'
    result['analysisStatus']='NOT_FULLY_VERIFIED'
    result['summary']={k:sum(c['status']==k for c in checks) for k in ('SUPPORTED','CORRECTION_REQUIRED','UNKNOWN')}
    result['unresolved']='%d checks remain UNKNOWN. Cash attribution and investment conclusions remain unverified.' % result['summary']['UNKNOWN']
    return result


def esc(value): return html.escape(str(value) if value is not None else '-',quote=True)

def source_link(source):
    url=source.get('sourceUrl','');u=urlsplit(url)
    if u.scheme=='https' and u.hostname in ('www.sec.gov','sec.gov') and not u.username and not u.password and u.port in (None,443):
        return '<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">Open reviewed filing</a>'
    return 'No reviewed source link'


def render(result):
    cards=[]
    for c in result['checks']:
        p=c.get('providerProvenance',{});p=p if isinstance(p,dict) else {}
        source=c.get('source',{});source=source if isinstance(source,dict) else {}
        metric=c.get('metric','Unknown field')
        title=esc({'eps_diluted':'Diluted EPS','ttm.eps_diluted':'Trailing 12-month diluted EPS','operating_income':'Operating income','net_income':'Net income','revenue':'Revenue','operating_margin':'Operating margin','net_margin':'Net margin','operating_cash_flow':'Operating cash flow'}.get(metric,metric.replace('_',' ').capitalize()))
        period=esc(c.get('period') or str(c.get('start','?'))+' → '+str(c.get('end','?')))
        badge=c['status'] if c.get('status') in ('SUPPORTED','CORRECTION_REQUIRED','UNKNOWN') else 'UNKNOWN'
        cards.append('<article><h2>'+title+' <small>'+esc(c.get('cik',''))+'</small></h2><p class="meta">'+period+'</p><p class="'+badge+'"><strong>'+badge+'</strong> · '+esc(c.get('reason'))+'</p><div class="scroll"><table><tr><th>Imported value</th><th>Source-supported value</th><th>Unit</th></tr><tr><td class="number">'+esc(c.get('suppliedValue'))+'</td><td class="number">'+esc(c.get('expectedValue'))+'</td><td>'+esc(c.get('unit') or p.get('unit'))+'</td></tr></table></div><p>Provider origin: <strong>'+esc(p.get('kind','unknown'))+'</strong> - imported metadata, not independent verification.</p><p>'+source_link(source)+'<br>'+esc(source.get('location'))+'</p><details><summary>Formula, source inputs and evidence clocks</summary><pre>'+esc(json.dumps({'providerProvenance':p,'reviewedSource':source,'reviewedFacts':c.get('sourceFacts',[])},ensure_ascii=False,indent=2))+'</pre></details></article>')
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><title>Earnings export review | AhaSignals</title><style>'+CSS+'</style></head><body><main><header><p class="meta">AhaSignals · Earnings review</p><h1>Which figures can you keep?</h1><p class="'+esc(result['status'])+'"><strong>'+esc(result['status'])+'</strong></p><p>'+esc(' · '.join(k+': '+str(v) for k,v in result['summary'].items()))+'</p><p>Cutoff: '+esc(result['cutoff'])+'<br>Evidence: '+esc(result['evidenceLevel'])+'</p><p>Whole analysis: NOT_FULLY_VERIFIED. Offline annotations are not a fresh original-source check. Missing provenance stays unknown.</p></header><section><h2>Source-supported numerical statements</h2><pre>'+esc(result.get('revisedAnalysis','No supported replacement available.'))+'</pre><p>'+esc(result['unresolved'])+'</p></section>'+''.join(cards)+'<footer>AI-assisted single-operator research. No independent financial assurance or investment advice. This report does not authorize a trade. Only selected reviewed CoreWeave Q2 2025 contexts are covered.</footer></main></body></html>'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--cutoff',required=True);p.add_argument('--out',required=True);p.add_argument('--source');a=p.parse_args()
    raw=Path(a.input).read_bytes();r=review(strict_load(raw),a.cutoff,Path(a.source).read_bytes() if a.source else None)
    r['exportBytesSha256']=hashlib.sha256(raw).hexdigest()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    (out/'review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'review.html').write_text(render(r),encoding='utf-8')
    print('Open review.html. Input unchanged; no model or network calls.')

if __name__=='__main__':
    try:main()
    except Exception:raise SystemExit('Invalid export/cutoff or existing output. Use a new directory; no model or network called.')
