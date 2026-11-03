# Earnings review Skill 0.2.0

Keep the original analysis. Check mapped numbers against filing evidence. Return
source-linked corrections and explicit unknowns.

[Walkthrough](references/ANALYSIS.md) · [Coverage](references/EARNINGS-REVIEW.md) ·
[Website](https://ahasignals.com/guides/earnings-review-skill/)

## Free, offline examples

Requires Python 3.9+. No pip install, model key, brokerage or network needed.

```sh
python3 scripts/selftest.py
python3 scripts/test_analysis_review.py
python3 scripts/analysis_review.py review --input examples/analysis/wrong.json --out wrong-review
```

Replace `wrong` with `correct` or `insufficient`, using a new output directory.
Expected first numeric results: CORRECTION_REQUIRED, SUPPORTED, UNKNOWN.
Examples are constructed test inputs from reviewed CoreWeave Q2 2025 facts;
they are not observed upstream/model mistakes. These are software tests, not a
model-accuracy benchmark. Offline evidence is REVIEWED_ANNOTATIONS_ONLY.

For your own analysis, follow [ANALYSIS.md](references/ANALYSIS.md). A user or
assistant explicitly maps exact excerpts to numeric claims. The program checks
text/number binding and the selected source context. Full semantics, unmapped
arguments and investment conclusions remain unverified. Coverage is finite.
Native day-trader-skill JSON remains supported through `scripts/run.py review-export`.

## Shared engine

The unchanged bundled wheel is ahasignals-pit 0.5.0. This release adds a portable
analysis-mapping adapter, not a new PyPI core version. Local MCP:
`python3 scripts/analysis_review.py mcp`. Seven read-only tools, including
`review_analysis_claims`. Microsoft replay remains unchanged.

The matching fork is [AhaSignals/day-trader-skill](https://github.com/AhaSignals/day-trader-skill).
Software MIT; annotations CC BY 4.0. No original filings in the bundle. Independent,
AI-assisted single-operator research; no endorsement, investment advice or
independent assurance. Host support and model quality require separate validation.
