# KCE generalization evaluation

A small, inspectable behavioral evaluation of concept extraction and transfer. It records **overgeneralization and undergeneralization separately**, rather than hiding them inside a prose-quality or overall intelligence score. Version 0.1 is an executable pilot framework with provisional original fixtures and a human review rubric. It is not a calibrated benchmark and has no established predictive validity.

## Recorded comparison

[Read the Sol 6.1 / Qwen outputs, then separate scores and timing](results/sol-qwen-2026-10-15/README.md). This is a small, single-attempt pilot with model-masked AI review, not human calibration. Raw responses, portable run receipts, reviews and an offline HTML report are included.

## Two governing evaluations

The primary suite profiles are `suites/encoding.json` and `suites/decoding.json`:

1. **Encoding:** paragraph/section → governing concept → generalized ODRO. Six source-bounded fixtures score overgeneralization and undergeneralization separately.
2. **Decoding:** supplied Kissinger framework/ODRO + bounded new facts → a new article. Use the local work-scoped fixture `data/kissinger/kissinger-standalone-article.json`; generation quality, structural fidelity and leakage remain separate. The extracted framework is a reviewable candidate, not yet a calibrated gold reference.

Inspect either executable plan without inference:

```sh
python3 -m kce_eval.suite encoding
python3 -m kce_eval.suite decoding
```

Run explicitly with `--execute --backend ollama --model MODEL --out runs/MODEL-encoding` (or decoding). A supplied-framework decoding score isolates realization; a later chained condition may use that model’s own encoding, labeled end-to-end. Ordinary conversation fixtures remain supplementary transfer tests. The profiles do not merge scores into one Cortex score.

## Implementation tracks

| Track | Model task | Independently reviewed dimensions |
|---|---|---|
| `kce` | Source passage → governing concept → generalized ontology, dynamics, regime, outcome | Overgeneralization severity, undergeneralization severity, source fidelity |
| `target` | Supplied framework → situation-specific words or action proposal | Target generation, structural transfer, source fidelity, control-block leakage |
| `article` | Supplied argumentative framework + bounded new facts → article | Target generation, structural transfer, source fidelity, control-block leakage |

Generation receives a supplied framework so a poor extraction does not automatically cause a poor generation score. A subsequent end-to-end study can provide the same model's extracted framework instead, labeled as a distinct condition. Individual tracks here do not automatically execute a Cortex agent pipeline or graph search.

The original fixtures expose source sentences, expected relations, acceptable alternatives and contrasting failure modes. Reviewer annotations in `rubric` are never sent to the tested model. Public validation families differ from development families; public validation is not a private uncontaminated holdout. See [RUBRIC.md](docs/RUBRIC.md) and [VALIDATION.md](docs/VALIDATION.md).

## Run locally

Python 3.9+; run from the repository root. Core operation needs only the standard library and no install.

```sh
python3 -m unittest discover -s tests -v
python3 -m kce_eval validate fixtures
python3 -m kce_eval prompt fixtures/capacity_council.json
python3 -m kce_eval run fixtures/capacity_council.json --backend command --command-json '["python3","examples/mock_model.py"]' --model mock-only --out runs/mock
python3 -m kce_eval run fixtures/capacity_council.json --backend ollama --model qwen3.8:27b --think false --out runs/qwen-dev
```

`run` calls the chosen backend; the mock command only tests transport and produces no model assessment. Validation and prompt inspection do not perform inference. Keep results and reviews in separate directories per model and configuration; mixed configurations are rejected during summary. A command adapter also works:

```sh
python3 -m kce_eval run fixtures/capacity_council.json --backend command --command-json '["python3","adapters/sol_cli.py"]' --model gpt-6.1-sol --out runs/sol-dev
```

Command adapters receive one JSON request on stdin (`model`, `messages`, `think`, etc.) and return only model-content text on stdout, not an API envelope. They must return nonzero on runtime/incomplete-response failure. Commands are argument arrays and run without a shell. The supplied optional SOL adapter requires an authenticated Codex CLI, runs an isolated ephemeral call, requests low reasoning effort, and refuses observed tool calls. Model resolution, injected CLI context, JSON mode, output limits, local versus hosted latency and reasoning mode can differ: report those differences rather than claiming equal compute.

Each new run writes an exclusive UUID receipt containing the exact fixture, prompt, configuration, raw response, hashes, timing, and explicit runtime/parse/schema status. Missing first-token timing is `null`, not zero. Fixture annotations are in the host receipt for review, not the inference prompt. Historical Tahoe scores are not imported as current benchmark results.

The initial Ollama adapter records JSON mode and fixed defaults (temperature 0.2, seed 417, 16,384 context tokens, 1,800 predicted tokens). It rejects incomplete or tool-bearing envelopes and nonempty thinking output when nonthinking was requested. Model-reported timing and identity are retained where available; a provider alias is not an independently verified weights fingerprint.

## Review and score

```sh
python3 -m kce_eval review-template runs/qwen-dev/RUN_ID/run.json --output reviews/qwen-dev/review.json
# Fill the template with an identified reviewer, separate 0–3 judgments,
# reasons and exact response evidence; leave unassessed dimensions null.
python3 -m kce_eval score runs/qwen-dev/RUN_ID/run.json reviews/qwen-dev/review.json
python3 -m kce_eval summarize runs/qwen-dev reviews/qwen-dev
```

Severity dimensions use **0 = no error, 3 = severe error**. Quality dimensions use **0 = absent/contradictory, 3 = faithful/useful**. Unassessed is not a passing zero. Reasons and quoted evidence are checked against the response and review/run hashes must agree. Severe errors are recorded explicitly in `critical_errors`; no overall quality average can compensate for them. `critical_gate_pass` means all dimensions were reviewed on a successful run and no critical error was declared—it is not an intelligence certification or automatic threshold on all quality dimensions. Reviewer honesty and semantic consistency still require calibration.

Failed runs may retain diagnostic review notes, but their judgments are excluded from semantic means. All-run and unreviewed failure statuses remain visible in summaries. Missing reviews do not become successful scores.

Severity summaries also give the number and fraction of assessed successful cases with a nonzero error. This is a case-level incidence, not “percent of concepts understood”; failures and unassessed cases have separate counts. Mean 0–3 scores are descriptive ordinal summaries, not calibrated measurements of intelligence.

Unique control canaries are checked only inside public `generated_text`, with findings returned as review flags, not automatic semantic grades. Generic words such as “operator” can be legitimate content and are not silently penalized. Broader instruction or scaffolding leakage is judged in context. Exact overlap alone does not prove copying. There is no self-referential draft-as-reference grader.

## Optional Kissinger database track

The current mixed Expressions database is 345,579,520 bytes (329.57 MiB), with 82 works; it is not only a Kissinger database. The selected work is *Strains on the Alliance* (1963). Use a local database path:

```sh
python3 -m kce_eval.kissinger --database /path/to/expressions.sqlite --output data/private/kissinger-rebuilt-framework.json --article-fixture data/private/kissinger-rebuilt-article.json
python3 -m kce_eval validate data/kissinger/kissinger-standalone-article.json
python3 -m kce_eval run data/kissinger/kissinger-standalone-article.json --backend ollama --model qwen3.8:27b --out runs/qwen-article
```

The exporter opens the original read-only, verifies its schema and before/after hash, selects one work and exports 12 source-extracted sentence vectors plus that work's operators/edges/routes/style summaries. It excludes generated drafts, historical judge scores, transfer-derived vectors, source PDFs and personal machine paths. Candidate extraction status is retained. The article fixture uses synthetic new political facts; it evaluates use of the supplied framework, not whether the model independently learned all of Kissinger's thinking.

New local exports remain ignored by default. This private repository includes the explicitly approved sanitized Kissinger corpus and its framework/article fixture under `data/kissinger/`; the original mixed database is excluded. If later distribution of the original is desired, use a separately reviewed release asset or LFS; ordinary GitHub files are limited to 100 MiB. Source and derived-annotation redistribution should be reviewed before publishing. No remote repository or license is selected by this local scaffold.

## Interpretation

This is useful for diagnosing where a model loses a concept's scope, conditions or specificity, separately from its ability to render a target. It does not measure an inaccessible internal mechanism or establish a broad cognitive ability score. [RESEARCH.md](docs/RESEARCH.md) distinguishes related published benchmarks from the predictive validation this particular eval still needs.

### Read the output before its review

Create an offline, self-contained HTML report from a verified run receipt:

```sh
python -m kce_eval.report results/RUN_ID/run.json --output output-review.html
python -m kce_eval.report results/RUN_ID/run.json --review reviews/RUN_ID.json --output scored-review.html
```

Open the HTML file in a browser. It shows the decoded generated prose (or parsed KCE JSON) and exact raw model response first, followed by separate dimension scores, reasons, exact evidence quotes and their surrounding output context. Runtime status and wall time remain visible. Fixture/source context, model messages and metadata are expandable. Reports contain the source and reviewer-only context, so handle them as work-scoped exports.

Without a review, dimensions are **Not scored (null)** and the critical gate is unassessed. Missing judgments remain unscored. Severity uses 0 good–3 bad; quality uses 0 bad–3 good. There is no aggregate score. Reviews are checked against receipt IDs and hashes and must quote actual output. Invalid receipts or reviews are rejected before creating a report; existing output files are never overwritten. Normal report generation performs no model calls.

## Standalone Kissinger database

The decoding suite uses `data/kissinger/kissinger-standalone-article.json`, retrieved from the sanitized `data/kissinger/kissinger-eval.sqlite`. These approved portable assets are included in this private repository. See [corpus extraction and verification](docs/KISSINGER_DATABASE.md) for scope and rebuilding instructions.

## Optional GitHub Actions

The tested workflow template is included at [`docs/github-actions-workflow.example.yml`](docs/github-actions-workflow.example.yml). It is not installed as an active Actions workflow; the publishing credential does not have workflow scope. Local checks and a clean-checkout verification passed.
