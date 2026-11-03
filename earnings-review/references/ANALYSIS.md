# Review your own analysis

Use `scripts/analysis_review.py` from this Skill directory. Requires Python 3.9+.
No provider API, token or network is used. These commands operate on local files.

```sh
python3 scripts/analysis_review.py prepare --input analysis.txt --cutoff 2026-11-04T00:00:00Z --out claims.json
```

Use your actual research cutoff. The new JSON preserves your text and starts with
an empty claims array. A host assistant or user proposes the mappings below;
`prepare` does not extract claims or run a language model. With no mappings,
the entire analysis remains unreviewed. Inspect every proposed mapping before
relying on numerical results.

```json
{
  "analysis": "CoreWeave Q2 2025 consolidated operating income was USD 19.209 million.",
  "cutoff": "2026-11-04T00:00:00Z",
  "claims": [{
    "id": "claim-1",
    "quote": "CoreWeave Q2 2025 consolidated operating income was USD 19.209 million.",
    "cik": "0001769628", "start": "2025-04-01", "end": "2025-06-30",
    "metric": "operating_income", "value": "19209000", "unit": "USD",
    "scope": "consolidated", "derived": false
  }]
}
```

Quotes must occur exactly once and cannot overlap. Preserve the analysis exactly;
do not paraphrase it to pass text binding. Money must have USD/US$/$ notation;
explicit million/billion scales are converted. Percentages need % or percent.
Unsupported wording, ambiguous amounts, qualified statements and other metrics
remain UNKNOWN. This is a conservative binding check, not a general NLP parser.

Issuer, period, scope and metric mappings are supplied by the user/agent. Matching
a number in a quote does not independently prove its semantic mapping. Reports
always retain `USER_OR_AGENT_PROPOSED`, `NOT_INDEPENDENTLY_VERIFIED` semantics and
`NOT_FULLY_VERIFIED` for the entire analysis. Do not omit these labels. Causal
arguments and investment conclusions are not verified. This design exposes the
mapping instead of silently trusting an LLM extraction.

```sh
python3 scripts/analysis_review.py review --input claims.json --out review-results
```

Open `review-results/review.md` and `review.json`. Each claim has its original
excerpt, conditional numeric result, source-supported replacement, source link,
context and clocks. Unmapped text is retained separately. No inputs are overwritten.
To re-extract the reviewed original, use the existing explicit collector and pass
`--source source/source.html`; see EARNINGS-REVIEW.md. Changed source bytes fail
closed. Offline results say REVIEWED_ANNOTATIONS_ONLY. Original filings are never
included in the distributable archive.

## English / 中文 assistant prompt

> Use the earnings-review Skill. Preserve my attached analysis verbatim. Propose
> one exact quote and explicit issuer/period/metric/unit/scope mapping per numerical
> claim; show me ambiguous mappings. Run the mapped claims using the tool. Return
> supported figures, necessary numerical corrections and unverified arguments.
> Do not call the entire analysis verified, and do not turn review into trading.

> 请使用 earnings-review Skill，完整保留我附上的分析。逐项提出原文摘录、公司、
> 期间、指标、单位与合并/分部口径映射，明确标出歧义。运行核验后，分别给出
> 可保留数字、应修正数字、仍未核验的推论。不要因部分数字正确而批准整篇分析。

## API and MCP

`python3 scripts/analysis_review.py mcp` exposes the six existing read-only tools
plus `review_analysis_claims`. It uses the same unchanged ahasignals-pit 0.5.0
wheel as the export CLI. The new adapter is versioned separately from that wheel.
`python3 scripts/analysis_review.py tool-schema` prints the JSON tool definition.
For an API app, use `name`, `description`, and `inputSchema` (as function parameters)
in your provider's function declaration, then pass returned arguments to
`review(arguments["packet"])` in your own local application. Only allow this named
review function; do not execute model-generated shell commands. API model calls
can incur charges and are not required or executed by these examples.

Do not assume a web chatbot has local files, Python or MCP. Without those tools,
run the local command and attach the reports. A stdio server is not a public HTTP
MCP endpoint; no hosted endpoint or platform marketplace acceptance is claimed.
