# Import an earnings export

Requires Python 3.9+; no model API, subscription or key is needed for the offline examples.
From the extracted `earnings-review` folder, start the local browser interface:

```sh
python3 scripts/review_ui.py
```

On Windows use `py -3 scripts/review_ui.py` if `python3` is unavailable. Windows is
not yet tested on a Windows host. Open the printed `http://127.0.0.1:PORT` URL.
Set your actual research cutoff, choose the JSON file produced by the upstream
`facts.py --json`, and select **Review my export**. A JSON array or one export
object is accepted. No manual claim mapping is required for this structured input.
The three example buttons use constructed CoreWeave Q2 2025 inputs. They are
software checks, not recorded model errors. No live filing retrieval happens.

The report shows imported and source-supported values, formulas, source locations,
and evidence clocks. Download HTML or JSON. Files are processed in memory on this
computer; closing the terminal stops the server. The local app is not a public MCP
endpoint and does not grant a text-only chatbot access to local files.

Command-line equivalent:

```sh
python3 scripts/export_review.py --input examples/wrong-export.json --cutoff 2026-11-04T00:00:00Z --out my-review
```

Open `my-review/review.html`. Use a new output directory. For the other two
examples substitute `correct-export.json` and `insufficient-export.json`. Expected
statuses: SUPPORTED, CORRECTION_REQUIRED, UNKNOWN respectively. If you separately
retain the exact reviewed original locally, `--source FILE` re-extracts and binds
it through the existing Python engine; it never fetches a supplied URL.

## Reading provenance

The research edition's `facts.py` adds `metric_provenance` per row and
`ttm_provenance` for TTM values:

- `reported`: selected SEC companyfacts value, with its concept, unit, period,
  accession and filing date. This is a provider label, not independent verification.
- `derived`: a calculation with formula and source inputs, such as a margin.
- `approximate`: Q4 EPS subtraction or summed quarterly EPS; weighted-average
  share counts can differ. Do not present these as directly reported EPS.
- `unknown`: missing or unsupported provenance. Legacy JSON has no metric-level
  origin metadata; the reviewer does not invent it from a row's `derived` flag.

These labels never grant SUPPORTED. Only the unchanged pinned review engine's
covered evidence can support or correct a numeric value. Imported metadata can
be forged. Unsupported EPS, growth, TTM, companies and periods remain UNKNOWN.
A row's filing date is not per-metric provenance or an intraday availability clock.
Historical filing-date filters cannot recover absent versions from today's data.

`examples/provenance/synthetic-q4-export.json` isolates the EPS flag regression:
reported revenue and net income, but Q4 EPS = FY - Q1 - Q2 - Q3. It contains
synthetic numbers, no real company or filing evidence, and must remain UNKNOWN.

## Verification

```sh
python3 scripts/selftest.py
python3 scripts/test_analysis_review.py
python3 scripts/test_export_review.py
```

The Microsoft test requires the same old-cutoff SHA-256 before and after the
later segment disclosure: `8fd96626ebb9eb1011d41ba41b99e2084f0d7f335aef2c2b931bef30c9f925ca`.
No investment thesis or trading permission is approved by these checks.

## Upstream credit

The EPS-only row flag gap was reported in upstream
[issue 20](https://github.com/Jakeschincariol/day-trader-skill/issues/20);
[PR 24](https://github.com/Jakeschincariol/day-trader-skill/pull/24) proposes a row-level fix.
This independent research fork also records per-metric formulas and inputs,
marks subtraction-derived EPS as approximate, and exposes the metadata in reports.
It does not claim to have discovered the upstream issue.

## Same export through MCP

Run `python3 scripts/analysis_review.py mcp` in a local MCP host and call
`review_earnings_export` with `payload` (the upstream array) and `cutoff`.
This Skill adapter adds the same metric provenance and unsupported-field display
as the HTML report. `mode` and optional `sourceText` preserve the shared engine
checks. The unchanged PyPI core alone does not add this presentation metadata.
