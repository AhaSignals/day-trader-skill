# Metric provenance and JSON import validation

Validated locally on 2026-11-04. No paid model calls, broker calls or manually
dispatched Actions runs. These are deterministic software tests, not a model
accuracy benchmark or evidence of external adoption.

## Reproduce

From the repository root:

```sh
python3 -m unittest discover -s tests -q
python3 -m unittest discover -s earnings-review/scripts -p 'test_*.py' -q
python3 earnings-review/scripts/selftest.py
python3 earnings-review/scripts/export_review.py --input earnings-review/examples/wrong-export.json --cutoff 2026-11-04T00:00:00Z --out wrong-review
python3 earnings-review/scripts/review_ui.py
```

323 repository tests and 24 adapter/UI tests passed. The official MCP SDK
subprocess check (`scripts/mcp-smoke.mjs`, with `MCP_SDK_ROOT` pointing to an
existing SDK installation) exercised seven read-only tools, three outcomes and
tampered-source rejection. MCP export/HTML report parity is also tested.

The browser flow was exercised with all three example buttons, an actual JSON
file chooser import of the synthetic Q4 fixture, and JSON report download.
The local endpoint rejects cross-origin requests, invalid Host/session tokens,
duplicate JSON keys, oversized input and duplicate issuer entries. It does not
fetch arbitrary URLs, execute uploaded instructions or write imported files.

## Expected outcomes

| Input | Outcome | Boundary |
|---|---|---|
| `correct-export.json` | SUPPORTED | Selected numerical facts only |
| `wrong-export.json` | CORRECTION_REQUIRED | Q2 operating income USD 19.209m, margin 1.6% |
| `insufficient-export.json` | UNKNOWN | Operating income does not establish cash flow |
| `provenance/synthetic-q4-export.json` | UNKNOWN | Synthetic company; reported revenue, approximate derived EPS |

The EPS fixture uses synthetic numbers, not financial evidence. Upstream
issue 20 and PR 24 are credited in `earnings-review/references/IMPORT.md`.
Metric metadata imported from a provider is not independent verification.
EPS derived by subtracting quarterly values from annual EPS is approximate
because weighted-average share counts can differ.

## Preserved artifacts

The bundled PyPI engine remains `ahasignals-pit 0.5.0`, SHA-256:
`5c4bf054dd123e63e7e7cea73aeeced533c4575fc516b531a700b2d58dc3663d`.

Microsoft: ten checks and four historical queries retain result SHA-256:
`8fd96626ebb9eb1011d41ba41b99e2084f0d7f335aef2c2b931bef30c9f925ca`.
No old evidence, filing dates, reviews or releases were overwritten.
The HTML report and Skill adapter add presentation/provenance metadata; they
do not expand the pinned evidence coverage. Unknown issuers, periods and EPS
facts remain unknown. Full prose meaning and investment conclusions are not
automatically verified.

Portable archives are built by `scripts/package_review.py`, which inspects
expanded archive and wheel bytes for public identity and credential patterns.
Verify the versioned download against its published `SHA256SUMS`.
