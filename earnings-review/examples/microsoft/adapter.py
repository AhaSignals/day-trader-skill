"""Bounded filing-specific iXBRL adapter. MIT; AhaSignals.

EdgarTools retrieves the filing; this adapter reads literal tagged contexts,
not standardized labels or a stitched multi-filing financial statement.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
import hashlib
import io
import re
import xml.etree.ElementTree as ET

NS = {'x': 'http://www.xbrl.org/2003/instance',
      'd': 'http://xbrl.org/2006/xbrldi',
      'ix': 'http://www.xbrl.org/2013/inlineXBRL'}
CONCEPT = 'RevenueFromContractWithCustomerExcludingAssessedTax'
AXIS = 'us-gaap:StatementBusinessSegmentsAxis'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def extract(document, receipt, requests):
    """Return exact requested whole-USD revenue facts, or raise; never guess.

    receipt clocks are supplied source evidence, not authenticated timestamps.
    Each request declares start/end/dimensions independently of extracted data.
    Unsupported transformations, units, contexts and conflicts fail closed.
    """
    if not isinstance(document, bytes) or len(document) > 12_000_000:
        raise ValueError('Expected bounded UTF-8 filing bytes')
    if re.search(br'<!\s*(?:DOCTYPE|ENTITY)', document, re.I):
        raise ValueError('DTD/entity declarations are unsupported')
    if sha(document) != receipt['documentSha256']:
        raise ValueError('Filing hash mismatch')
    accession = receipt['accession']
    cik = receipt['cik']
    if not re.fullmatch(r'\d{10}-\d{2}-\d{6}', accession) or not re.fullmatch(r'\d{10}', cik):
        raise ValueError('Invalid filing identity')
    prefix = f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-", "")}/'
    if not receipt['sourceUrl'].startswith(prefix) or '/' in receipt['sourceUrl'][len(prefix):]:
        raise ValueError('URL does not identify the declared filing')
    if not requests or len(requests) > 32:
        raise ValueError('Expected 1..32 exact requests')
    bindings = {}
    for _, pair in ET.iterparse(io.BytesIO(document), events=('start-ns',)):
        prefix, uri = pair
        if prefix in bindings and bindings[prefix] != uri:
            raise ValueError('Rebound namespace prefix is unsupported')
        bindings[prefix] = uri
    if (not re.fullmatch(r'http://fasb.org/us-gaap/\d{4}', bindings.get('us-gaap', ''))
            or bindings.get('iso4217') != 'http://www.xbrl.org/2003/iso4217'
            or bindings.get('ixt') not in ('http://www.xbrl.org/inlineXBRL/transformation/2022-02-16',
                                          'http://www.xbrl.org/inlineXBRL/transformation/2020-02-12',
                                          'http://www.xbrl.org/inlineXBRL/transformation/2015-02-26')
            or not re.fullmatch(r'http://www.microsoft.com/\d{8}', bindings.get('msft', ''))):
        raise ValueError('Unsupported taxonomy/transform namespace binding')
    root = ET.fromstring(document)
    contexts = {}
    units = {}
    for tag, target in [('context', contexts), ('unit', units)]:
        for node in root.findall('.//x:' + tag, NS):
            ident = node.get('id')
            if not ident or ident in target:
                raise ValueError('Missing or duplicate context/unit ID')
            target[ident] = node
    output = []
    for request in requests:
        if set(request) != {'start', 'end', 'dimensions'}:
            raise ValueError('Requests must declare period and dimensions')
        matches = []
        for fact in root.findall('.//ix:nonFraction', NS):
            if fact.get('name') != 'us-gaap:' + CONCEPT:
                continue
            context = contexts.get(fact.get('contextRef'))
            if context is None:
                raise ValueError('Unknown context')
            start = context.findtext('x:period/x:startDate', namespaces=NS)
            end = context.findtext('x:period/x:endDate', namespaces=NS)
            if (start, end) != (request['start'], request['end']):
                continue
            for container in context.findall('.//x:segment', NS) + context.findall('.//x:scenario', NS):
                if any(child.tag != '{' + NS['d'] + '}explicitMember' for child in container):
                    raise ValueError('Unsupported context qualifier')
            if context.findall('.//d:typedMember', NS):
                raise ValueError('Typed dimensions are unsupported')
            dimensions = [{'axis': n.get('dimension'), 'member': n.text}
                          for n in context.findall('.//d:explicitMember', NS)]
            dimensions.sort(key=lambda x: (x['axis'], x['member']))
            if dimensions != sorted(request['dimensions'], key=lambda x: (x['axis'], x['member'])):
                continue
            identifier = context.find('x:entity/x:identifier', NS)
            if identifier is None or identifier.text != cik or identifier.get('scheme') != 'http://www.sec.gov/CIK':
                raise ValueError('Context issuer mismatch')
            unit = units.get(fact.get('unitRef'))
            if unit is None or len(unit) != 1 or unit.findtext('x:measure', namespaces=NS) != 'iso4217:USD':
                raise ValueError('Only simple USD units supported')
            fmt = fact.get('format', '')
            if fmt not in ('ixt:num-dot-decimal', 'ixt:numdotdecimal') or len(fact) or fact.get('nil') or fact.get('{http://www.w3.org/2001/XMLSchema-instance}nil'):
                raise ValueError('Unsupported inline transformation or nil fact')
            text = (fact.text or '').strip()
            if not re.fullmatch(r'(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?', text):
                raise ValueError('Unsupported numeric text')
            scale = int(fact.get('scale', '0'))
            if not -12 <= scale <= 12 or fact.get('sign', '') not in ('', '-'):
                raise ValueError('Unsupported scale or sign')
            if len(text) > 128:
                raise ValueError('Oversize numeric text')
            with localcontext() as ctx:
                ctx.prec = max(32, len(text) + abs(scale) + 2)
                value = Decimal(text.replace(',', '')) * (Decimal(10) ** scale)
            if fact.get('sign') == '-':
                value = value.copy_negate()
            if value != value.to_integral_value() or abs(value) > 2**53 - 1:
                raise ValueError('Value is not safe whole dollars')
            matches.append(dict(factId='filing-' + accession + '-' + fact.get('contextRef'),
                cik=cik, taxonomy='us-gaap', concept=CONCEPT, unit='USD',
                start=start, end=end, dimensions=dimensions, value=int(value),
                accession=accession, acceptedAt=receipt.get('acceptedAt'),
                observedAt=receipt.get('observedAt'), sourceUrl=receipt['sourceUrl'],
                documentSha256=receipt['documentSha256'], contextId=fact.get('contextRef')))
        if not matches:
            raise ValueError('Requested literal context absent')
        if len({f['value'] for f in matches}) != 1:
            raise ValueError('Conflicting facts for exact context')
        # Repeated display of the same fact is not a new observation.
        output.append(min(matches, key=lambda f: f['contextId']))
    if len({f['factId'] for f in output}) != len(output):
        raise ValueError('Duplicate requested context')
    return deepcopy(output)
