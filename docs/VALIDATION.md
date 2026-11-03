# Research edition 0.1.0 validation

Date: 2026-11-04. Operator: AhaSignals.

- 318 repository tests passed on Python 3.9.6. This includes the existing
  calculation/risk suites and three new filing-date filter regressions. Repository
  layout/manifest expectations were updated for the research-only install profile;
  the original README checks now exercise the preserved upstream README.
- Eight new analysis-mapping tests passed: correct/wrong/unknown, exact binding,
  units, context, historical cutoffs, tampered original, untrusted unmapped text,
  duplicate JSON/quotes and invalid tool inputs.
- Existing ahasignals-pit core: 76 tests passed on Python 3.12, including the
  locally retained original SEC document and tampered-source tests.
- Actual MCP subprocess via the official SDK: seven read-only tools discovered;
  all three outcomes and tampered-source rejection passed. This is protocol
  interoperability, not a model-agent test.
- The independent Skill was copied into an isolated directory and executed there:
  three legacy outcomes, eight new tests, ten Microsoft replay checks and four
  historical queries passed.
- Original-file review of the wrong analysis example returned
  CORRECTION_REQUIRED / REVIEWED_ORIGINAL_REEXTRACTED. Original bytes remain
  private and are not included in releases. Ordinary offline examples correctly
  report REVIEWED_ANNOTATIONS_ONLY.
- Microsoft historical result SHA-256 before/after later segment disclosures:
  `8fd96626ebb9eb1011d41ba41b99e2084f0d7f335aef2c2b931bef30c9f925ca`.
- Pinned ahasignals-pit 0.5.0 wheel SHA-256 remains
  `5c4bf054dd123e63e7e7cea73aeeced533c4575fc516b531a700b2d58dc3663d`.
- Public-identity check and recursive expanded ZIP/wheel byte checks passed.

Reproduce:

```sh
python3 -m unittest discover -s tests
python3 earnings-review/scripts/selftest.py
python3 earnings-review/scripts/test_analysis_review.py
python3 scripts/package_review.py
```

Optional official SDK check with an already installed SDK:
`MCP_SDK_ROOT=YOUR_EXISTING_NODE_PROJECT node scripts/mcp-smoke.mjs`.
The SDK is only a development check, not required by the Skill.

No model APIs, subscriptions, live orders, Actions dispatch or remote messages
were used for validation. Host-app installs, automatic Skill selection, general
prose understanding and model accuracy are not claimed as tested. The filing-date
filter is date-level reconstruction and cannot recover absent historical data.
