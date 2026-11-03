"""Reviewed, deliberately narrow compatibility case. MIT; AhaSignals."""
from adapter import AXIS, CONCEPT

CIK = '0000789019'
OLD = '0001193125-25-256321'
NEW = '0001193125-26-436133'
OLD_CUTOFF = '2025-11-01T00:00:00Z'
OLD_MEMBERS = ['ProductivityAndBusinessProcessesMember', 'IntelligentCloudMember', 'MorePersonalComputingMember']
NEW_MEMBERS = ['AgentsAndInfraMember', 'DevicesAndConsumerMember']


def context(member=None, year=2025):
    return dict(start=f'{year}-07-01', end=f'{year}-09-30',
                dimensions=[] if member is None else [{'axis': AXIS, 'member': 'msft:' + member}])


def expected(member=None, year=2025):
    return dict(cik=CIK, taxonomy='us-gaap', concept=CONCEPT, unit='USD', **context(member, year))


FILINGS = [
    dict(accession=OLD, document='msft-20250930.htm', reportDate='2025-09-30',
         requests=[context()] + [context(m) for m in OLD_MEMBERS],
         reviewedValues=[77673000000, 33020000000, 30897000000, 13756000000]),
    dict(accession=NEW, document='msft-20260930.htm', reportDate='2026-09-30',
         requests=[context()] + [context(m) for m in NEW_MEMBERS] +
                  [context(year=2026)] + [context(m, 2026) for m in NEW_MEMBERS],
         reviewedValues=[77673000000, 61672000000, 16001000000, 92279000000, 76795000000, 15484000000]),
]
