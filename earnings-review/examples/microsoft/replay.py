"""Offline historical cutoff comparison. MIT; AhaSignals. No network calls."""
import argparse
import sys
sys.dont_write_bytecode = True  # Public example directory must remain source-only.
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from ahasignals_pit import audit_batch, select_fact
from profile import CIK, FILINGS, OLD, NEW, OLD_CUTOFF, OLD_MEMBERS, NEW_MEMBERS, expected


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def verify_packet(packet):
    check(packet['case'] == 'filing-cutoff-comparison-v1' and packet['schemaVersion'] == '1.0', 'Case identity')
    check(packet['rawDocumentsRedistributed'] is False, 'Raw redistribution boundary')
    check(len(packet['receipts']) == 2 and len(packet['facts']) == 10, 'Case inventory')
    for spec, receipt in zip(FILINGS, packet['receipts']):
        check(receipt['accession'] == spec['accession'] and receipt['cik'] == CIK, 'Receipt identity')
        check(receipt['form'] == '10-Q' and receipt['reportDate'] == spec['reportDate'], 'Filing period/form')
        check(receipt['sourceUrl'] == f'https://www.sec.gov/Archives/edgar/data/789019/{spec["accession"].replace("-", "")}/{spec["document"]}', 'Source URL')
        facts = [f for f in packet['facts'] if f['accession'] == spec['accession']]
        check([f['value'] for f in facts] == spec['reviewedValues'], 'Reviewed values')
        check(len(facts) == len(spec['requests']), 'Requested inventory')
        for fact, request in zip(facts, spec['requests']):
            check(all(fact[k] == v for k, v in request.items()), 'Literal context changed')
            check(all(fact[k] == receipt[k] for k in ('cik', 'accession', 'sourceUrl', 'acceptedAt', 'observedAt', 'documentSha256')), 'Fact/receipt mismatch')
            check(fact['taxonomy'] == 'us-gaap' and fact['concept'] == expected()['concept'] and fact['unit'] == 'USD', 'Concept/unit')
            # Production audit validates remaining field formats and time order.
    check(len({f['factId'] for f in packet['facts']}) == 10, 'Duplicate fact IDs')


def replay(packet):
    verify_packet(packet)
    facts = packet['facts']
    old = [f for f in facts if f['accession'] == OLD]
    new = [f for f in facts if f['accession'] == NEW]
    current = max(datetime.fromisoformat(r['observedAt'].replace('Z', '+00:00')) for r in packet['receipts']).astimezone(timezone.utc).isoformat()
    checks = []

    def audit(name, candidates, fact, context, cutoff, mode, wanted):
        payload = dict(schemaVersion='1.0', ruleset='sec-financial-facts-v1', mode=mode,
                       dataset={'id': 'filing-cutoff-comparison', 'version': '1'}, facts=deepcopy(candidates),
                       rows=[dict(rowId=name, factId=fact['factId'], cutoff=cutoff, expected=context)])
        result = audit_batch(payload)
        check(result['gate'] == wanted, name + ': unexpected gate ' + result['gate'])
        checks.append(dict(name=name, expectedGate=wanted, report=result))

    audit('historical-consolidated', facts, old[0], expected(), OLD_CUTOFF, 'disclosure-reconstruction', 'PASS')
    audit('historical-segment', facts, old[2], expected(OLD_MEMBERS[1]), OLD_CUTOFF, 'disclosure-reconstruction', 'PASS')
    audit('future-comparative-at-old-cutoff', facts, new[1], expected(NEW_MEMBERS[0]), OLD_CUTOFF, 'disclosure-reconstruction', 'FAIL')
    audit('recent-comparative', facts, new[1], expected(NEW_MEMBERS[0]), current, 'observed-pipeline', 'PASS')
    audit('old-and-new-segments-are-not-interchangeable', facts, new[1], expected(OLD_MEMBERS[1]), current, 'observed-pipeline', 'FAIL')
    audit('late-capture-is-not-historical-observation', facts, old[0], expected(), OLD_CUTOFF, 'observed-pipeline', 'FAIL')
    audit('older-vintage-at-current-cutoff', facts, old[0], expected(), current, 'disclosure-reconstruction', 'FAIL')
    audit('current-quarter', facts, new[3], expected(year=2026), current, 'observed-pipeline', 'PASS')
    missing = deepcopy(old)
    for fact in missing:
        fact['observedAt'] = None
    audit('missing-observation-remains-unknown', missing, missing[0], expected(), current, 'observed-pipeline', 'UNKNOWN')
    missing_acceptance = deepcopy(old)
    for fact in missing_acceptance:
        fact['acceptedAt'] = None
    audit('missing-acceptance-remains-unknown', missing_acceptance, missing_acceptance[0], expected(), current, 'disclosure-reconstruction', 'UNKNOWN')
    before, after = [], []
    for member in [None] + OLD_MEMBERS:
        query = dict(expected(member), cutoff=OLD_CUTOFF, mode='disclosure-reconstruction')
        before.append(select_fact(old, query))
        after.append(select_fact(facts, query))
    check(before == after and all(r['status'] == 'answer' for r in before), 'Historical replay changed')
    future_query = select_fact(facts, dict(expected(NEW_MEMBERS[0]), cutoff=OLD_CUTOFF, mode='disclosure-reconstruction'))
    check(future_query['status'] == 'withheld' and future_query['reason'] == 'source-after-cutoff', 'Future recast leaked')
    check(sum(f['value'] for f in old[1:]) == old[0]['value'] == sum(f['value'] for f in new[1:3]), 'Comparative segment total')
    check(sum(f['value'] for f in new[4:]) == new[3]['value'], 'Current segment total')
    return dict(status='verified', case=packet['case'], packetSha256=digest(packet),
                historicalCutoff=OLD_CUTOFF, currentCaptureCutoff=current,
                checks=checks, historicalResults=before, oldCutoffResultSha256=digest(before),
                afterAppendResultSha256=digest(after), historicalResultCount=len(before),
                futureComparativeQuery=future_query,
                boundary='Exact supplied contexts and clocks only; no full-history, source-authentication, automatic segment comparability or independent assurance claim.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, default=Path(__file__).with_name('packet.json'))
    args = parser.parse_args()
    result = replay(json.loads(args.packet.read_text()))
    print(json.dumps(result, indent=2))
