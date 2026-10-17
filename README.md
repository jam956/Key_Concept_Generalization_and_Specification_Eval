# KCE generalization evaluation

For agentic AI systems to reuse knowledge reliably, they must move in two directions: turn specific examples into bounded concepts, then apply those concepts to new specifics without losing the conditions that make them true. Fluent output alone does not establish that transfer. A generalization can discard a necessary constraint; a retelling can preserve details without identifying what transfers.  New unestablished information (hallucination) should not be introduced to force a desired position.  This repository assesses a model’s ability to navigate this cognitive skill.  

A trained technician who needs someone else to unlock a workshop illustrates a transferable distinction: capability does not confer control of required access. Applied to an archive, the same distinction means that being able to verify a record does not grant authority to release it. The details change; the governing relationship and its limits must survive.

This repository examines whether that relationship survives both steps. **KCE—Key Concept Elevation—**extracts a governing concept from a specific passage. **ODRO—ontology, dynamics, regime, outcome—**records what is involved, how it changes, the applicable constraints, and the possible result.

The tests assess extraction and generation separately. Generation uses a supplied conceptual framework, so this pilot does not establish automatic round-trip transfer. It is a small diagnostic study, not a calibrated benchmark.

## Sample report

[**Read the sample report: Sol 6.1 and Qwen**](examples/sample-report.md).

The sample contains six encoding cases and one article case per model: complete outputs first, then separate scores, evidence and recorded timings. All 14 calls completed. Reviews were performed separately with model identity and timing masked; they remain provisional AI judgments, not human-calibrated grades. Use this as a report example, not an answer key for candidates or judges.

## Evaluate any model through a submission

Download the [ready-to-use evaluation bundle](evaluation/bundle-v1/) and follow the [submission and independent review instructions](docs/USAGE.md). Each candidate case uses a fresh chat or independent API call with the selected case file's ordered messages. The model portion can be performed manually without Python. The optional CLI imports captured responses, prepares an anonymous judge packet, and validates an independently obtained judgment; it does not call models.

Responses appear before separate dimension scores. Failures remain visible. Manual timing and statelessness claims are not independently verified. Keep existing results and prior grades out of candidate and judge chats.

1. **Run the candidate:** use the bundle’s common candidate instructions and one `cases/case-NNN.json` at a time in a fresh chat. Preserve that case’s ordered system/user messages.
2. **Submit the outputs:** copy `04_Submission_Template.json`, fill model settings and every case’s exact raw response, and retain failures. Import it with the commands in [USAGE](docs/USAGE.md).
3. **Use a separate judge:** generate the anonymous judge packet, then give a fresh judge only that packet and `06_Judge_Agent.md`. Keep example reports, prior grades and model metadata out of the judge context.
4. **Finalize the report:** capture the judge’s JSON and run finalization to check ownership, score ranges and evidence quotes. Read the outputs before the separate scores.

The full [step-by-step guide](docs/USAGE.md) includes submission JSON, copyable import/judging commands, uncertainty handling and the final report files. Run `python3 -m kce_eval.workflow --help` for command help. All workflow commands are offline preparation/validation; you choose and run the candidate and judge models separately.

## What the two evaluations measure

| Evaluation | Model receives | Model produces | Separate dimensions |
|---|---|---|---|
| **Encoding** | A bounded passage | Governing concept, ODRO, limits | Overgeneralization severity; undergeneralization severity; source fidelity |
| **Decoding** | A supplied Kissinger analytical framework and new fictional facts | A four-to-six-paragraph article | Generation quality; structural transfer; source fidelity; control-block leakage |

Encoding asks whether the model preserves the relationship and its scope. Decoding asks whether it can realize a supplied structure in coherent, situation-specific writing without importing unsupported history or exposing control instructions. The supplied-framework condition keeps extraction errors separate from writing errors.

The repository also includes supplementary target-generation fixtures. These tracks do **not** automatically execute the full Noetic Cortex, perform autonomous graph retrieval, or measure a model's hidden internal reasoning.

## Quick start: no model calls

Requires **Python 3.9+**. Run from the repository root; the core uses only the standard library and needs no installation.

```sh
python3 -m unittest discover -s tests -v
python3 -m kce_eval validate fixtures
python3 -m kce_eval validate data/kissinger/kissinger-standalone-article.json
python3 -m kce_eval.suite encoding
python3 -m kce_eval.suite decoding
```

The suite commands show the planned fixtures unless `--execute` is supplied. To inspect an exact model prompt:

```sh
python3 -m kce_eval prompt fixtures/capacity_council.json
```

Reviewer rubrics and reference answers are excluded from model prompts.

## Review, score and inspect a new run

```sh
python3 -m kce_eval review-template runs/qwen-encoding/RUN_ID/run.json --output reviews/qwen-encoding/RUN_ID.json
# Fill in reviewer identity, scores, reasons and exact output quotations.
python3 -m kce_eval score runs/qwen-encoding/RUN_ID/run.json reviews/qwen-encoding/RUN_ID.json
python3 -m kce_eval summarize runs/qwen-encoding reviews/qwen-encoding
python3 -m kce_eval.report runs/qwen-encoding/RUN_ID/run.json --review reviews/qwen-encoding/RUN_ID.json --output reviewed-run.html
```

Replace `RUN_ID` with the UUID directory created by the run. The HTML report shows the output before the dimension scores and supporting evidence.

| Score type | 0 | 3 |
|---|---|---|
| Severity: overgeneralization, undergeneralization, leakage | No error | Severe error |
| Quality: fidelity, generation, structural transfer | Absent or contradictory | Faithful and useful |

There is **no combined score**. Missing judgments remain unscored; failed runs stay visible and are excluded from semantic means. Reviews must match run/output hashes and quote actual output. Control-marker detection supplies review flags, not automatic semantic grades. Critical errors remain explicit; a critical-gate pass is not an intelligence certification or a quality threshold.

See the [scoring rubric](docs/RUBRIC.md) for dimension anchors, examples and critical-error rules.

## Included Kissinger corpus

[`data/kissinger/kissinger-eval.sqlite`](data/kissinger/kissinger-eval.sqlite) is a **7.47 MiB standalone extraction** containing 28 works, 206 analytical operators, 78 routes, 155 source-derived sentence vectors, and the necessary shared concept and invariant nodes.

Source spans, document pointers, historical generated drafts/scores and six transfer-test-derived lesson vectors are excluded. Conceptual summaries and analytical expressions remain; this is not a guarantee of no wording overlap with original works. Candidate annotations are not validated gold.

The current article fixture uses the framework from **Strains on the Alliance (1963)** and new fictional river-energy facts. It does not test all 28 works or establish author-wide emulation ability. Database integrity, graph references, route sequences and framework retrieval were checked against the original before publication.

- [Corpus scope, extraction and verification](docs/KISSINGER_DATABASE.md)
- [Database extraction receipt](data/kissinger/kissinger-eval.receipt.json)
- [Consumer retrieval verification](data/kissinger/kissinger-eval.consumer-verification.json)

The original mixed database and local working runs remain excluded from Git. The recorded results are portable publication copies: repository-absolute adapter paths were made relative, while exact prompts, outputs, timing and judgments were preserved.

## Interpretation and next steps

The results can help locate a failure: losing a qualifier, remaining too close to an example, importing unsupported facts, failing to realize a framework, or leaking control material. They do not establish a general cognitive ability or predictive validity. Repeated trials, independent human calibration and a genuinely held-out set are needed before stronger claims. Visible validation families differ from development families, but are not a private holdout.

Read [validation limits and design](docs/VALIDATION.md) and [related research](docs/RESEARCH.md).

The [GitHub Actions template](docs/github-actions-workflow.example.yml) runs local-style contract checks without model calls. It is included as a template rather than an active workflow because the publishing credential lacks workflow permission.
