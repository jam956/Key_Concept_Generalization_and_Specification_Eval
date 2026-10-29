# KCE and the Kissinger corpus: steering an LLM's attention

Large language models can extract concepts, change perspective, follow an analytical framework, and adapt their writing to a particular voice. Having those capabilities does not mean they will apply them reliably. Even with a suitable problem, a fluent response can lose a crucial condition, settle on a familiar interpretation, or adopt an author's mannerisms while missing the structure of the argument.

This repository explores a way to make those abilities more deliberate: **give the model a structured account of what to attend to, which relationships to follow, and how to carry them into a new piece of writing.**  Includes a normalized corpus of Henry Kissinger's political analysis, exercises for applying and extracting conceptual structures, and a rubric for grading the resulting output.

The aim is to make attention steering inspectable and testable. Can an LLM use an explicit cognitive framework to guide its analysis and expression? Where does it preserve that framework, and where does it drift?

**Explore the [example scorecard and complete responses: Sol 6.1 versus Qwen 3.8 27B](examples/sample-report.md), or [try the evaluation with another model](docs/USAGE.md).**

## Why this exists

This work grew out of developing Alex, an AI collaborator intended to carry useful methods between tasks. That requires more than remembering facts or producing agreeable, polished language. The model needs to recognize which relationships matter, preserve the conditions under which a method applies, and express the result appropriately for the present situation.

Frontier models can already perform many of these cognitive transformations. The engineering question is how to call on those capabilities consistently and how to judge whether they were actually applied.

A broad instruction such as “write like Kissinger” leaves the model to choose what that means. A structured representation can specify a more particular route: begin with a shared aspiration, examine the tensions it conceals, distinguish the parties' positions, and develop a proposal only after establishing the diagnosis. It can also state when a move is inappropriate. A claim of inevitability, for example, needs supporting facts.  Such were features of Kissinger's writing style which this repository attempts to emulate.

That is the attention-steering approach explored here. The context supplied to the model describes relationships, analytical moves, their ordering, and their limits. These can guide how a response develops as its focus moves from one concern to another. The evaluation lets readers inspect and grade the model's use of that guidance. Establishing an advantage over simpler prompts would require a matched comparison; the current example compares models using the supplied framework.

## The Kissinger corpus

The included database is a normalized description of analytical and expressive patterns identified across **28 of Henry Kissinger's works**. It records concepts, analytical operators, argument routes, and sentence-level structures, with the aim of making aspects of his reasoning and writing style available for use on new material.

Here, an **operator** is a describable move in an argument, such as showing how a successful policy creates a new difficulty. A **route** connects such moves into a progression. Style includes how attention develops: when competing perspectives enter, how a technical issue becomes a political question, and when the analysis has earned a conclusion.

The intention is to reproduce aspects of that analytical and writing style through explicit contextual guidance. The records are interpretations of the source material, so their faithfulness and usefulness remain open to examination.

The current article exercise draws on the framework extracted from *Strains on the Alliance* (1963). The model receives that framework alongside fictional facts about a river-energy negotiation and writes a four-to-six-paragraph article. For example, a technically workable infrastructure plan may leave unresolved who has authority to approve it. The model must develop the political significance of the supplied facts while preserving what remains unknown.

The corpus covers more works than this single exercise tests. Its inclusion supports inspection and future experiments; the present results do not establish faithful reproduction of Kissinger's writing across the whole corpus.

## O/D/R/O: making the guidance explicit

The broader cognitive framework uses **O/D/R/O** to describe the shape of a concept or transformation:

| Field | What it makes explicit |
|---|---|
| **Ontology** | The kinds of entities, roles, or relationships involved. |
| **Dynamics** | What acts, changes, or maintains a relationship. |
| **Regime** | The conditions and constraints under which it applies. |
| **Outcome** | The consequence that follows or could follow under those conditions. |

For example, developing technical competence does not necessarily remove dependence on another party who controls a required access point. The condition matters: if another viable access route becomes available, that particular dependency may change.

This structure helps carry a relationship between situations while retaining its boundaries. In the writing exercise, the supplied context also includes analytical operators, their connections, argument routes, and transfer limits. Together, these provide a more explicit account of the intended analytical movement than an author's name alone.

This repository evaluates selected uses of that approach. It is one application of the larger [cognitive-skills framework](https://github.com/jam956/cognitive-skills-framework) developed alongside the Alex persona and Noetic Cortex.

## KCE is one of the transformations being tested

**KCE—Key Concept Elevation—**moves from a specific example to a reusable concept while preserving the conditions that make it useful. It is one cognitive transformation within the broader framework.

The evaluation separates two tasks so that their strengths and failures can be examined independently:

| Exercise | What the model does | What the review examines |
|---|---|---|
| **Encoding: example to concept** | Extracts a governing concept, its O/D/R/O structure, and its limits from a short passage. | Unsupported generalization, failure to recover the useful relationship, and fidelity to the source. |
| **Decoding: framework to expression** | Applies a supplied Kissinger analytical framework to new fictional facts in an article. | Quality of writing, transfer of the supplied structure, factual fidelity, and leakage of task instructions into the prose. |

The article model receives a prepared framework; it does not use its own preceding extraction. The present setup therefore tests extraction and application separately. Supplementary exercises explore application through other forms of writing and action proposals.

The rubric grades observable outputs. It does not measure internal attention weights, and these exercises do not automatically execute the full Noetic Cortex.

## Example scorecard: Sol 6.1 and Qwen 3.8 27B

The [included scorecard and sample report](examples/sample-report.md) show **Sol 6.1 versus Qwen 3.8 27B with thinking disabled**. Sol used low reasoning effort; Qwen used the installed Q4_K_M quantized model in nonreasoning mode. The report records the different backends and settings.

Each model completed six encoding exercises and one supplied-framework article exercise: 14 recorded calls in total. Read the complete responses first, then the separate scores, supporting quotations, review explanations, and timings. This makes it possible to examine what a grade refers to and disagree with the reviewer where warranted.

Reviews were performed separately with model identity and timing masked. They remain provisional AI judgments, not human-calibrated grades. This is a worked example of how to assess the framework's application, rather than a general ranking of the two models.

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

## Corpus contents and provenance

The [standalone Kissinger database](data/kissinger/kissinger-eval.sqlite) is a 7.47 MiB extraction containing 28 works, 206 analytical operators, 78 routes, and 155 source-derived sentence vectors, with related concept and invariant records. The annotations are provisional interpretations, not validated answer keys.

Original source spans, document pointers, historical generated drafts and scores, and six lesson vectors derived from earlier transfer tests were excluded. Conceptual summaries and analytical expressions remain, and some wording may overlap the original works. See [corpus scope and verification](docs/KISSINGER_DATABASE.md), the [extraction receipt](data/kissinger/kissinger-eval.receipt.json), and the [retrieval verification](data/kissinger/kissinger-eval.consumer-verification.json).

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

This is a small diagnostic pilot. It can reveal where a particular response loses a condition, stays too close to an example, or introduces unsupported information. It does not yet establish a model's general reasoning ability or predict performance across unrelated tasks. 

Stronger conclusions require repeated trials, independent human calibration, and genuinely held-out cases. The visible validation cases are available for inspection, so they are not a private holdout. See the [validation plan and limitations](docs/VALIDATION.md) and [related research](docs/RESEARCH.md).

The purpose is to make structured attention steering and cognitive transformation easier to examine: describe the intended analytical movement, supply it to a model, inspect the resulting expression, and grade how faithfully it was applied.  For fun, one may give the LLM a political science article and ask it to write a rebuttal using the Kissinger database as a guide and see what comes out.
