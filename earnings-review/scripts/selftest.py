"""Offline installed-bundle checks. No model calls or network."""
import json
from pathlib import Path
import runpy
import socket
import sys
from run import activate, ROOT
activate()
socket.socket=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('Network forbidden'))
from ahasignals_pit.earnings_review import review_earnings_export
from ahasignals_pit.workflow_mcp import handle
from importlib.resources import files
for name in ('correct','wrong','insufficient'):
    c=json.loads(files('ahasignals_pit').joinpath('workflow_data/earnings-'+name+'.json').read_text())
    r=review_earnings_export(c['export'],c['cutoff'],analysis=c['analysis'])
    assert r['status']==c['expectedStatus']
    args=dict(payload=c['export'],cutoff=c['cutoff'],analysis=c['analysis'])
    m=handle(dict(jsonrpc='2.0',id=1,method='tools/call',params=dict(name='review_earnings_export',arguments=args)))
    assert not m['result']['isError']
    assert json.loads(m['result']['content'][0]['text'])==r
    print(name+': '+r['status']+' / '+r['evidenceLevel'])
sys.path.insert(0,str(ROOT/'examples/microsoft'))
module=runpy.run_path(str(ROOT/'examples/microsoft/replay.py'))
r=module['replay'](json.loads((ROOT/'examples/microsoft/packet.json').read_text()))
assert r['oldCutoffResultSha256']==r['afterAppendResultSha256']=='8fd96626ebb9eb1011d41ba41b99e2084f0d7f335aef2c2b931bef30c9f925ca'
assert len(r['checks'])==10 and r['historicalResultCount']==4
print('Microsoft: 10 checks, four unchanged historical queries; '+r['oldCutoffResultSha256'])
print('CLI engine/MCP handler parity verified. Deterministic program checks, not a model benchmark.')
