# KCE: Can an AI carry an idea into a new situation?

An AI can write a convincing explanation and still miss the idea that makes it useful. It may repeat the details of an example, turn a conditional observation into a universal rule, or invent facts when applying the lesson elsewhere.

This project explores a practical question: **can a model identify a useful concept, preserve its limits, and apply a supplied concept to a different situation?** It provides short reading exercises, a Kissinger-based analytical writing exercise, a review rubric, and tools for recording and comparing the results.

It is for people building AI assistants, studying conceptual transfer, or simply curious about what survives when a model moves from an example to an idea and back again.

**Start here:** [read the sample responses and reviews](examples/sample-report.md), or [try the evaluation with your own model](docs/USAGE.md).

## Why this exists

Consider a technician who can diagnose a broken pump but needs someone else's permission to enter the workshop. Increasing the technician's skill does not, by itself, remove that access dependency.

The useful idea is the relationship between capability and control of a necessary step. That relationship can help explain a different situation: a neighborhood council may train its own technicians while still depending on a supplier to unlock a meter.

There are several ways a model can lose the lesson. “Skill never creates independence” goes beyond the evidence. Retelling the pump story leaves the reader to work out what transfers. An account that invents a hostile gatekeeper changes the explanation by adding an unsupported motive.

We built this evaluation to make those differences visible. If conceptual representations are to support reusable skills or memory, we need to inspect what they preserve, what they discard, and what happens when a model uses them.

## The idea behind KCE

**KCE means Key Concept Elevation:** moving from a particular example to a reusable concept while retaining the conditions that make it applicable.

The evaluation asks a model to express that concept using four fields, abbreviated **O/D/R/O**:

| Field | Plain-language question |
|---|---|
| Ontology | What kinds of things or relationships are involved? |
| Dynamics | What happens, changes, or maintains the relationship? |
| Regime | Under what conditions does it hold? |
| Outcome | What follows, or could follow, under those conditions? |

The model also states the concept's limits. The aim is a useful abstraction whose claims can be checked against its source. The four fields make that checking easier; filling them in does not establish that the model is right.

## What the evaluation asks a model to do

There are two main exercises:

| Exercise | Task | What reviewers look for |
|---|---|---|
| **Encoding: example to concept** | Read a short passage and identify its governing concept, O/D/R/O structure, and limits. | Does the answer preserve the relationship, avoid unsupported generalization, and remain faithful to the source? |
| **Decoding: concept to new expression** | Use a supplied analytical framework and new fictional facts to write a four-to-six-paragraph article. | Does the article apply the framework coherently, preserve its conditions, use the supplied facts accurately, and keep task instructions out of the finished prose? |

These exercises are assessed separately. The writing model receives a prepared framework; it does not have to use its own earlier extraction. This helps distinguish difficulty identifying a concept from difficulty applying one. It also means the current evaluation does **not** demonstrate an automatic end-to-end extraction-and-transfer system.

Supplementary exercises explore application through other forms of writing and action proposals.

## Where Kissinger fits

The article exercise uses an analytical framework drawn from annotations of Henry Kissinger's *Strains on the Alliance* (1963). The model receives that framework alongside fictional facts about a river-energy negotiation and writes an article about the new situation.

The question is whether the model can use the supplied relationships and qualifications to organize a fresh analysis. Historical facts from the source must not become invented facts about the fictional negotiation. The exercise does not establish that the model has acquired Kissinger's thinking or can reproduce his work generally.

The repository includes a [standalone retrieval database](data/kissinger/kissinger-eval.sqlite) covering 28 works: 206 analytical operators, 78 routes, and 155 source-derived sentence vectors, with related concept and invariant records. The current article exercise uses one work's framework. The annotations are provisional interpretations, not validated answer keys.

Original source spans, document pointers, historical generated drafts and scores, and six lesson vectors derived from earlier transfer tests were excluded from this extraction. Conceptual summaries and analytical expressions remain, and some wording may overlap the original works. See [corpus scope and verification](docs/KISSINGER_DATABASE.md), the [extraction receipt](data/kissinger/kissinger-eval.receipt.json), and the [retrieval verification](data/kissinger/kissinger-eval.consumer-verification.json).

## See an example

The [Sol 6.1 and Qwen sample report](examples/sample-report.md) shows six encoding cases and one article case per model. It presents the complete responses before the scores, followed by evidence and explanations for each judgment.

All 14 recorded calls completed. Reviews were performed separately with model identity and timing masked. They are provisional AI judgments, not human-calibrated grades. The models also used different backends and decoding settings; the report records those differences. Treat it as a worked example of the evaluation, rather than a general model ranking.

## Try it with a model

The [evaluation bundle](evaluation/bundle-v1/) supports manual chats or independent API calls. You can collect model responses without writing code. Python is needed for the optional command-line workflow that imports responses, prepares review materials, and validates the resulting review.

1. **Run each case separately.** Give the model the common candidate instructions and one case's ordered messages in a fresh conversation or independent API call. Record any interface adaptations.
2. **Keep the original response.** Enter every case into the submission template, preserving failures and incomplete or invalid output. Record the model and known settings.
3. **Arrange a separate review.** Use the tools to prepare an anonymous review packet for a fresh judge model or an independent human reviewer.
4. **Inspect the report.** Validate the review and read the actual responses alongside the separate scores and supporting quotations.

Keep rubrics, reference answers, sample reports, and previous grades out of candidate conversations. Reviewers receive the generated review packet, without prior results or explicit candidate identity and timing. Manual timing and use of independent contexts are recorded claims, not independently verified measurements.

The [step-by-step guide](docs/USAGE.md) provides the exact files and commands. The submission workflow prepares and validates material locally; you run the candidate and reviewer separately.

## How to read the results

The evaluation keeps different failures separate:

- **Overgeneralization:** the answer claims more than the source supports.
- **Undergeneralization:** the answer fails to recover a useful relationship from the example.
- **Source fidelity:** the answer preserves the supplied facts and qualifications.
- **Structural transfer:** the new writing carries the supplied relationship into the new situation.
- **Generation quality:** the writing fulfills its task and is coherent for its intended reader.
- **Control-block leakage:** instructions or test markers appear in the reader-facing prose.

Reviewers use 0–3 scales. Higher severity scores mean more error; higher quality scores mean better performance. **There is no combined score.** Missing judgments remain unscored, failures remain visible, and failed runs are excluded from semantic averages. Reviews must bind to the relevant outputs and support their judgments with exact quotations. Automated marker checks flag possible leakage for review; they do not determine semantic quality.

See the [scoring rubric](docs/RUBRIC.md) for examples, scale definitions, and critical-error rules.

## For developers

The core tools require **Python 3.9+**, use the standard library, and need no installation. From the repository root, these commands check the implementation and fixtures and show the planned exercises without calling models:

```sh
python3 -m unittest discover -s tests -v
python3 -m kce_eval validate fixtures
python3 -m kce_eval validate data/kissinger/kissinger-standalone-article.json
python3 -m kce_eval.suite encoding
python3 -m kce_eval.suite decoding
```

The suite commands execute model calls only when explicitly requested with `--execute`. To inspect one model prompt, with reviewer-only material excluded:

```sh
python3 -m kce_eval prompt fixtures/capacity_council.json
```

See the [submission guide](docs/USAGE.md) for the manual workflow and optional programmable runners. The [GitHub Actions example](docs/github-actions-workflow.example.yml) is a contract-check template, not an active workflow. The original mixed database and local working runs remain excluded from Git; the sample report preserves the recorded outputs, judgments, and timings in a portable form.

## What we hope to learn next

This is a small diagnostic pilot. It can reveal where a particular response loses a condition, stays too close to an example, or introduces unsupported information. It does not yet establish a model's general reasoning ability or predict performance across unrelated tasks. The exercises do not automatically run the Noetic Cortex or reveal a model's hidden internal reasoning.

Stronger conclusions require repeated trials, independent human calibration, and genuinely held-out cases. The visible validation cases are available for inspection, so they are not a private holdout. See the [validation plan and limitations](docs/VALIDATION.md) and [related research](docs/RESEARCH.md).

The purpose is to make conceptual transfer easier to examine: show the source, inspect the extracted idea, read its new expression, and identify exactly where meaning survives or changes.
