"""Loopback-only JSON import UI. No remote upload, model, trading or source fetch."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
from urllib.parse import urlsplit,parse_qs
from export_review import strict_load, review, render, CSS

ROOT=Path(__file__).resolve().parents[1]
PAGE='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Import an earnings export | AhaSignals</title><style>__CSS__</style><main><header><p>AhaSignals · Local earnings review</p><h1>Import the analysis. Inspect the numbers.</h1><p>Choose the JSON produced by <code>trader-analyst/facts.py --json</code>. Your file is processed on this computer, without an API key or model call.</p></header><section><label>Research cutoff (UTC)<input id="cutoff" value="2026-11-04T00:00:00Z" type="text"></label><p>Set your actual cutoff; the example date is a fixed reproducibility setting.</p><label>Upstream JSON export<input id="file" type="file" accept=".json,application/json"></label><button id="review">Review my export</button><p>Or run a constructed example:</p><button data-example="correct">Correct</button> <button data-example="wrong">Wrong</button> <button data-example="insufficient">Insufficient evidence</button><p id="status" role="status"></p><a id="download" hidden download="review.html">Download the HTML report</a> <a id="json" hidden download="review.json">Download JSON</a></section><div id="result"></div><footer>Selected CoreWeave Q2 2025 numerical evidence only. Imported provenance is not independent verification. Offline annotations are not a fresh source check.</footer></main><script>
const token='__TOKEN__';let raw=null,urls=[];
async function run(text){document.querySelector('#status').textContent='Reviewing locally…';document.querySelector('#result').replaceChildren();document.querySelector('#download').hidden=true;document.querySelector('#json').hidden=true;urls.forEach(URL.revokeObjectURL);urls=[];
try{const res=await fetch('/review',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':token},body:JSON.stringify({text,cutoff:document.querySelector('#cutoff').value})});const r=await res.json();if(!res.ok)throw Error(r.error);document.querySelector('#status').textContent=r.result.status+' - whole analysis is not fully verified';const frame=document.createElement('iframe');frame.title='Source-linked review report';frame.setAttribute('sandbox','allow-popups allow-popups-to-escape-sandbox');frame.srcdoc=r.html;frame.style='width:100%;height:900px;border:0;border-radius:18px';document.querySelector('#result').append(frame);for(const [id,data,type] of [['download',r.html,'text/html'],['json',JSON.stringify(r.result,null,2),'application/json']]){const a=document.getElementById(id);a.href=URL.createObjectURL(new Blob([data],{type}));urls.push(a.href);a.hidden=false;}}
catch(e){document.querySelector('#status').textContent='Cannot review: '+e.message;}}
document.getElementById('review').onclick=async()=>{const f=document.getElementById('file').files[0];if(!f){document.querySelector('#status').textContent='Choose an upstream JSON export first.';return;}if(f.size>2000000){document.querySelector('#status').textContent='Maximum size: 2 MB';return;}await run(await f.text());};
for(const b of document.querySelectorAll('[data-example]')) b.onclick=async()=>{try{const r=await fetch('/example?name='+b.dataset.example);if(!r.ok)throw Error('Example unavailable');await run(await r.text());}catch(e){document.querySelector('#status').textContent=e.message;}};
</script></html>'''

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send(self,status,body,kind='application/json'):
        if isinstance(body,str):body=body.encode('utf-8')
        self.send_response(status);self.send_header('Content-Type',kind+'; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.send_header('Content-Security-Policy',"default-src 'self' blob:; script-src 'unsafe-inline'; style-src 'unsafe-inline'; frame-src 'self' blob:; frame-ancestors 'none'; base-uri 'none'");self.end_headers();self.wfile.write(body)
    def allowed(self):
        host='127.0.0.1:'+str(self.server.server_port)
        return self.headers.get('Host')==host and self.headers.get('Origin','http://'+host)=='http://'+host and self.headers.get('Sec-Fetch-Site','same-origin') not in ('cross-site','same-site')
    def do_GET(self):
        if not self.allowed():return self.send(403,'{"error":"Local origin required"}')
        u=urlsplit(self.path)
        if u.path=='/':return self.send(200,PAGE.replace('__CSS__',CSS).replace('__TOKEN__',self.server.token),'text/html')
        if u.path=='/example':
            name=parse_qs(u.query).get('name',[''])[0]
            if name in ('correct','wrong','insufficient'):return self.send(200,(ROOT/'examples'/ (name+'-export.json')).read_bytes())
        self.send(404,'{"error":"Not found"}')
    def do_POST(self):
        if not self.allowed() or self.headers.get('X-Review-Token')!=self.server.token:return self.send(403,'{"error":"Local origin and session token required"}')
        if self.path!='/review':return self.send(404,'{"error":"Not found"}')
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<=2200000 or self.headers.get('Content-Type')!='application/json':raise ValueError()
            packet=strict_load(self.rfile.read(n))
            if set(packet)!={'text','cutoff'} or not isinstance(packet['text'],str):raise ValueError()
            result=review(strict_load(packet['text']),packet['cutoff'])
            self.send(200,json.dumps({'result':result,'html':render(result)},ensure_ascii=False))
        except Exception:self.send(400,'{"error":"Invalid export or cutoff. Expected upstream facts.py JSON; maximum 100 rows / 2 MB."}')

def server(port=0):
    s=ThreadingHTTPServer(('127.0.0.1',port),Handler);s.token=secrets.token_hex(24);return s

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=0);a=p.parse_args();s=server(a.port)
    print('Open http://127.0.0.1:%d - Ctrl+C to stop. Files stay local.' % s.server_port,flush=True)
    try:s.serve_forever()
    except KeyboardInterrupt:s.server_close()
