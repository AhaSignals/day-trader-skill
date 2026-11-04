# Day Trader Skill - AhaSignals Research Edition

**Check the earnings claims behind your analysis.** Keep correct figures, correct
source-supported numerical errors, and show what remains unknown.

Independent fork of [Jakeschincariol/day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill),
pinned to `3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd`.
Original work by Jake Schincariol and contributors, MIT. This edition's default
plugin installs only the earnings analyst and review skills. Original trading
modules remain in the repository but are not installed by this research profile.
No affiliation or endorsement is implied.

[完整使用指南 / Walkthrough](earnings-review/references/ANALYSIS.md) ·
[Host compatibility](docs/COMPATIBILITY.md) ·
[Validation](docs/VALIDATION.md) ·
[Upstream documentation](docs/UPSTREAM-README.md)

## Three minutes, no key

```sh
git clone https://github.com/AhaSignals/day-trader-skill.git
cd day-trader-skill
python3 earnings-review/scripts/selftest.py
python3 earnings-review/scripts/test_analysis_review.py
python3 earnings-review/scripts/analysis_review.py review --input earnings-review/examples/analysis/wrong.json --out wrong-review
```

Open `wrong-review/review.md`. Requires Python 3.9+; the verified Python wheel is
included. No installation, model call, live retrieval or brokerage is required.

| Example | Proposed numeric claim | Numeric result |
|---|---|---|
| `correct.json` | Q2 operating income USD 19.209m | SUPPORTED |
| `wrong.json` | Q2 operating loss USD 8.261m | CORRECTION_REQUIRED: income USD 19.209m |
| `insufficient.json` | Operating cash flow USD 19.209m | UNKNOWN |

These are constructed inputs based on reviewed CoreWeave Q2 2025 facts, not claims
that upstream or a model produced the errors. The whole analysis always remains
NOT_FULLY_VERIFIED: numeric support does not prove cash attribution or a thesis.

## Review your own analysis

```sh
python3 earnings-review/scripts/analysis_review.py prepare --input analysis.txt --cutoff 2026-11-04T00:00:00Z --out claims.json
```

Use your actual research cutoff. Ask your assistant to propose exact excerpts and
issuer/period/metric/unit mappings following
[ANALYSIS.md](earnings-review/references/ANALYSIS.md). Inspect ambiguous mappings.
Then run:

```sh
python3 earnings-review/scripts/analysis_review.py review --input claims.json --out my-review
```

There is no hidden model call: `prepare` preserves text and creates an empty claim
list. Unmapped text remains visible. Mapping is user/agent supplied, not an
independent semantic verification. The reviewer supports selected CoreWeave
Q2 2025 consolidated metrics; other contexts stay UNKNOWN. Optional original HTML
is hash-bound and re-extracted; offline runs use reviewed annotations only.

## Existing analyst export

```sh
python3 trader-analyst/facts.py CRWV --json > earnings.json
python3 earnings-review/scripts/run.py review-export --input earnings.json --cutoff 2026-11-04T00:00:00Z --out export-review
```

The first command accesses SEC and needs your own `SEC_USER_AGENT` locally. It is
not part of the offline test. Unsupported newer periods stay UNKNOWN.

For historical date-level reconstruction, add `--filed-before YYYY-MM-DD` to
`facts.py`. This excludes filings on and after that date, including future
comparative values, before selecting the latest eligible facts. Unknown dates
are excluded. Filing-date resolution is not intraday acceptance time; today's
snapshot can omit historical versions. This does not establish contemporaneous
capture or complete point-in-time data. Current ticker/name mappings remain
current. Historical mode disallows merging into `--metrics` to avoid mixing bases.

## Install the review Skill

Claude Code research plugin:

```text
/plugin marketplace add AhaSignals/day-trader-skill
/plugin install ahasignals-research@ahasignals-research
```

Other file-based Skill hosts: copy the complete `earnings-review` folder to the
host's documented skills directory, or use `python3 scripts/install_review.py
--dest YOUR_SKILLS_DIRECTORY`. Installation never overwrites an existing skill.
See the compatibility table before claiming a platform is tested.

Local MCP: `python3 earnings-review/scripts/analysis_review.py mcp`.
Use `review_analysis_claims` for mapped prose, `review_earnings_export` for native
JSON. Both reuse the pinned ahasignals-pit 0.5.0 engine. A stdio server is not a
public remote MCP endpoint. Text-only chats can receive locally generated reports.

## Contributors and AI assistance

<a href="https://github.com/codex"><img src="https://avatars.githubusercontent.com/u/267193182?v=4" width="48" height="48" alt="OpenAI Codex contributor avatar" /></a>

**ChatGPT / Codex (OpenAI)** — AI-assisted development, documentation and local
verification of the AhaSignals research edition. Git commits credit the actual
coding agent, Codex. AhaSignals maintains the project and is responsible for its
published claims; this credit does not imply OpenAI sponsorship or endorsement.
Original upstream author and Claude co-author credits remain in the commit history.

## Limits and maintenance

We test software behavior and historical replay locally, not trading profitability
or cross-model accuracy. No paid model calls or Actions schedules are added.
Core review is maintained in the independent
[earnings-review-skill](https://github.com/AhaSignals/earnings-review-skill) project;
the integration snapshot is pinned and hash-checked. Preserve old releases.

[Contribution scope](CONTRIBUTING.md). AhaSignals is an independent research
publisher. AI-assisted single-operator review, no independent financial assurance
or investment advice. Upstream trading code is retained for compatibility, not
certified for live trading by this edition.
