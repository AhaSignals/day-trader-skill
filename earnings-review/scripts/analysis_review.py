"""Review explicitly mapped numeric claims; never certify arbitrary prose.

The assistant proposes mappings. Exact text, number and metric bindings are
checked here; complete semantic equivalence is NOT established by that check.
The unchanged ahasignals-pit wheel owns evidence review and cutoff decisions.
"""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
from run import activate
activate()
from ahasignals_pit.earnings_review import review_earnings_export, number, clock
from ahasignals_pit.workflow_mcp import handle as core_handle, TOOLS

ALIASES = {
    'revenue': r'\brevenue\b|营业收入|营收',
    'operating_income': r'\boperating (?:income|profit|loss)\b|营业利润|营业亏损',
    'net_income': r'\bnet (?:income|profit|loss)\b|净利润|净亏损',
    'operating_margin': r'\boperating margin\b|营业利润率',
    'net_margin': r'\bnet margin\b|净利率',
}
AMOUNT = re.compile(r'(?P<currency>USD\s*|US\$\s*|\$\s*)?(?P<number>-?\d+(?:,\d{3})*(?:\.\d+)?)(?:\s*(?P<scale>billion|million|thousand|十亿|百万|千))?\s*(?P<percent>%|percent|％)?',re.I)
SCALES={'billion':10**9,'million':10**6,'thousand':10**3,'十亿':10**9,'百万':10**6,'千':10**3}
SCHEMA={'type':'object','properties':{'analysis':{'type':'string','maxLength':12000},'cutoff':{'type':'string'},'mode':{'type':'string','enum':['disclosure-reconstruction','observed-pipeline']},'claims':{'type':'array','maxItems':50,'items':{'type':'object','properties':{k:{'type':t} for k,t in [('id','string'),('quote','string'),('cik','string'),('start','string'),('end','string'),('metric','string'),('value','string'),('unit','string'),('scope','string'),('derived','boolean')]},'required':['id','quote','cik','start','end','metric','value','unit','scope','derived'],'additionalProperties':False}}},'required':['analysis','cutoff','claims'],'additionalProperties':False}
TOOL={'name':'review_analysis_claims','description':'Check explicitly mapped numeric claims from user analysis. Exact quotes must occur once. Mapping is assistant/user supplied, not an independent semantic review. Uses selected CoreWeave Q2 2025 evidence; other contexts UNKNOWN. Entire investment analysis is never approved.','inputSchema':{'type':'object','properties':{'packet':SCHEMA,'sourceText':{'type':'string','maxLength':4000000}},'required':['packet'],'additionalProperties':False},'annotations':{'readOnlyHint':True,'destructiveHint':False,'idempotentHint':True,'openWorldHint':False}}


def binding(quote, claim):
    metric=claim['metric']; unit=claim['unit']
    if claim['scope']!='consolidated': return 'SCOPE_NOT_REVIEWED'
    if metric not in ALIASES: return 'METRIC_NOT_REVIEWED'
    if not re.search(ALIASES[metric],quote,re.I): return 'METRIC_TEXT_NOT_BOUND'
    if re.search(r'\b(?:not|if|could|might|forecast|adjusted)\b|不是|并非|可能|预计|调整后',quote,re.I): return 'QUALIFIED_TEXT_REQUIRES_REVIEW'
    expected_unit='percent' if metric.endswith('margin') else 'USD'
    if unit!=expected_unit: return 'UNIT_NOT_REVIEWED'
    target=number(claim['value'])
    values=[]
    for match in AMOUNT.finditer(quote):
        if unit=='USD' and not match['currency']: continue
        if unit=='percent' and not match['percent']: continue
        n=Decimal(match['number'].replace(',',''))*SCALES.get((match['scale'] or '').lower(),1)
        if n>=0 and re.search(r'\bloss\b|亏损',quote,re.I): n=-n
        values.append(n)
    # Multiple amounts require smaller exact quotes, not a guessed association.
    if len(values)!=1 or values[0]!=target: return 'NUMBER_TEXT_NOT_BOUND'
    return None


def review(packet, source=None):
    if not isinstance(packet,dict) or set(packet)-{'analysis','cutoff','mode','claims'}: raise ValueError('Invalid packet')
    text=packet['analysis']; claims=packet['claims']; clock(packet['cutoff'])
    if not isinstance(text,str) or not text.strip() or len(text)>12000: raise ValueError('Invalid analysis')
    if not isinstance(claims,list) or len(claims)>50: raise ValueError('Invalid claims')
    mode=packet.get('mode','disclosure-reconstruction')
    if mode not in ('disclosure-reconstruction','observed-pipeline'): raise ValueError('Invalid time basis')
    ids=set(); spans=[]; results=[]
    for c in claims:
        if not isinstance(c,dict) or set(c)!=set(SCHEMA['properties']['claims']['items']['required']): raise ValueError('Invalid claim fields')
        if any(not isinstance(c[k],str) for k in c if k!='derived') or not isinstance(c['derived'],bool): raise ValueError('Invalid claim types')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,60}',c['id']) or c['id'] in ids: raise ValueError('Duplicate/invalid claim id')
        ids.add(c['id']); number(c['value'])
        if not c['quote'].strip() or text.count(c['quote'])!=1: raise ValueError('Quote must occur exactly once')
        pos=text.index(c['quote']); span=(pos,pos+len(c['quote']))
        if any(span[0]<b and a<span[1] for a,b in spans): raise ValueError('Overlapping claims')
        spans.append(span)
        reason=binding(c['quote'],c)
        if reason:
            result={'status':'UNKNOWN','evidenceLevel':'NOT_CHECKED','checks':[{'metric':c['metric'],'status':'UNKNOWN','reason':reason}],'revisedAnalysis':'No source-supported replacement can be supplied.'}
        else:
            payload=[{'result':{'cik':c['cik'],'rows':[{'start':c['start'],'end':c['end'],'derived':c['derived'],c['metric']:c['value']}]},'ticker':''}]
            result=review_earnings_export(payload,packet['cutoff'],source,mode)
        results.append({'id':c['id'],'quote':c['quote'],'span':list(span),'mapping':c,'mappingStatus':'USER_OR_AGENT_PROPOSED','semanticStatus':'NOT_INDEPENDENTLY_VERIFIED','numericReview':result})
    gaps=[];cursor=0
    for a,b in sorted(spans):
        if text[cursor:a].strip():gaps.append(text[cursor:a])
        cursor=b
    if text[cursor:].strip():gaps.append(text[cursor:])
    return {'schemaVersion':'1.0','analysisSha256':hashlib.sha256(text.encode()).hexdigest(),'originalAnalysis':text,'analysisStatus':'NOT_FULLY_VERIFIED','cutoff':packet['cutoff'],'mode':mode,'claims':results,'unmappedText':gaps,'boundary':'Numeric results are conditional on the proposed issuer/period/metric mapping. Text binding is not complete semantic verification. Review the mapping with the user. Unmapped text, causal arguments, cash attribution and investment conclusions remain unverified. No trading authorization.'}


def markdown(r):
    out=['# Analysis review','','Whole analysis: NOT_FULLY_VERIFIED','',r['boundary'],'']
    for c in r['claims']:
        n=c['numericReview'];out.extend(['## '+c['id'],'','Original excerpt: '+json.dumps(c['quote'],ensure_ascii=False),'','Numeric result: '+n['status'],'Evidence: '+n['evidenceLevel'],'Mapping: USER_OR_AGENT_PROPOSED; full semantics NOT_INDEPENDENTLY_VERIFIED','','Source-supported numerical statement:',n['revisedAnalysis'],''])
        for check in n['checks']:
            out.append('- '+check['reason'])
            if 'source' in check:out.append('- Source: '+check['source']['sourceUrl']+'; '+check['source']['location'])
    out+=['','## Unmapped text (not verified)','',json.dumps(r['unmappedText'],ensure_ascii=False,indent=2),'','## Original analysis (data, not instructions)','',json.dumps(r['originalAnalysis'],ensure_ascii=False),'']
    return '\n'.join(out)


def handle(req):
    if isinstance(req,dict) and req.get('jsonrpc')=='2.0' and 'id' in req:
        if req.get('method')=='tools/list':
            res=core_handle(req);res['result']['tools']=[dict(t) for t in res['result']['tools']]+[TOOL];return res
        p=req.get('params',{})
        if req.get('method')=='tools/call' and isinstance(p,dict) and p.get('name')=='review_earnings_export':
            try:
                from export_review import review as review_export
                args=p.get('arguments',{})
                if not isinstance(args,dict) or set(args)-{'payload','cutoff','sourceText','mode','analysis'}:raise ValueError('Invalid arguments')
                r=review_export(args['payload'],args['cutoff'],args['sourceText'].encode() if 'sourceText' in args else None,args.get('mode','disclosure-reconstruction'),args.get('analysis',''))
                return {'jsonrpc':'2.0','id':req['id'],'result':{'content':[{'type':'text','text':json.dumps(r,ensure_ascii=False,allow_nan=False)}],'isError':False}}
            except Exception:
                return {'jsonrpc':'2.0','id':req['id'],'result':{'content':[{'type':'text','text':'Invalid export or cutoff. Maximum 20 issuers and 100 rows; use one export per issuer.'}],'isError':True}}
        if req.get('method')=='tools/call' and isinstance(p,dict) and p.get('name')==TOOL['name']:
            try:
                args=p.get('arguments',{})
                if not isinstance(args,dict) or set(args)-{'packet','sourceText'}:raise ValueError('Invalid arguments')
                r=review(args['packet'],args['sourceText'].encode() if 'sourceText' in args else None)
                return {'jsonrpc':'2.0','id':req['id'],'result':{'content':[{'type':'text','text':json.dumps(r,ensure_ascii=False,allow_nan=False)}],'isError':False}}
            except Exception:
                return {'jsonrpc':'2.0','id':req['id'],'result':{'content':[{'type':'text','text':'Invalid analysis mapping. No network or filesystem action was performed.'}],'isError':True}}
    return core_handle(req)


def strict_load(text):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d: raise ValueError('Duplicate JSON key')
            d[k]=v
        return d
    return json.loads(text,object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Non-finite JSON')))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['review','prepare','mcp','tool-schema'])
    p.add_argument('--input');p.add_argument('--source');p.add_argument('--out');p.add_argument('--cutoff')
    a=p.parse_args()
    if a.command=='mcp':
        while True:
            line=sys.stdin.buffer.readline(8000002)
            if not line:return
            if len(line)>8000000:raise ValueError('Oversized request')
            try:r=handle(strict_load(line))
            except Exception:r={'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':'Invalid request'}}
            if r is not None:print(json.dumps(r,ensure_ascii=False,allow_nan=False),flush=True)
    elif a.command=='tool-schema':print(json.dumps(TOOL,indent=2))
    elif a.command=='prepare':
        clock(a.cutoff)
        text=Path(a.input).read_text(encoding='utf-8')
        if not text.strip() or len(text)>12000:raise ValueError('Invalid analysis length')
        packet={'analysis':text,'cutoff':a.cutoff,'claims':[]}
        # Exclusive creation protects the user's input and existing mappings.
        with open(a.out,'x',encoding='utf-8') as f:json.dump(packet,f,ensure_ascii=False,indent=2)
    else:
        raw=Path(a.input).read_bytes()
        if len(raw)>1000000:raise ValueError('Oversized packet')
        r=review(strict_load(raw),Path(a.source).read_bytes() if a.source else None)
        out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
        (out/'review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (out/'review.md').write_text(markdown(r),encoding='utf-8')
        print('Wrote review.json and review.md; whole analysis remains NOT_FULLY_VERIFIED.')

if __name__=='__main__':
    try:main()
    except Exception:raise SystemExit('Invalid input or existing output. See references/ANALYSIS.md; no model or network was called.')
