# Reviewer rubric

This is a small, public, manually authored diagnostic set. Validation fixtures are visible, not hidden or private. Development families and validation families are disjoint, but this does not establish predictive validity or broad generalization. Familiar surface, changed surface, changed causal relation, and cross-domain generation are probes, not an estimated population distribution.

Only `input` belongs in the model prompt. Fixture `rubric` is reviewer-only evaluation material. Expected concepts are alternatives, not exact-answer strings. Judge semantic relations, conditions, and evidence, accepting accurate paraphrase, alternative useful abstractions, and warranted narrow abstention. A more general sentence is not automatically better. Binding a statement to its source context is not automatically undergeneralization.

KCE output is JSON with `governing_concept` (string), `odro` (four strings keyed `ontology`, `dynamics`, `regime`, `outcome`), and `limits` (list of strings). Target and article output is JSON with `generated_text` (string). Schema failures are recorded separately from semantic failures; syntactically valid JSON may still fail every semantic dimension. Preserve the ODRO distinction: an outcome is a possible or conditional consequence, not necessarily a guaranteed result.

## KCE dimensions

Score each separately; never collapse severity and quality into a single average.

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Overgeneralization severity | No unsupported extension | Minor overbroad wording, central relation intact | Important causal condition lost or unsupported extension | Reversed cause, unsupported universal law, or central claimed fact absent from source |
| Undergeneralization severity | Useful relation captured, or justified narrow abstention | Relation captured but unnecessarily narrow | Mostly source retelling or generic label loses an important relation | No usable abstraction; names/events only, or vacuous label erases the governing structure |
| Source fidelity quality | Central contradiction or invented central fact | Material distortion or omission | Accurate central relation with a minor omission | All governing relations and necessary limits faithfully represented |

Examples: “Skill never yields autonomy” overgeneralizes a passage where a specific access gate remains. “The chair kept the promise” invents conduct where only an intention is stated. “Mira repaired pumps” undergeneralizes if the access-control dependency disappears. “Cooperation matters” is too generic if it loses the relation between control, necessity, and action. Naming Mira alongside a valid abstract relation is acceptable. Declining to infer motives is appropriate restraint, not undergeneralization. Over- and undergeneralization may coexist: a generic universal slogan can be both unsupported and structurally uninformative.

## Target and article dimensions

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Target generation quality | Unusable or fails task | Partially usable; major audience, genre, or influence failure | Useful with a minor requested-quality omission | Natural, coherent, fulfills audience/genre and desired influence |
| Structural transfer quality | Supplied relation absent or inverted | Superficial thematic echo | Central relation transferred with a small gap | Causal structure and qualifying regime transferred accurately |
| Source fidelity quality | Central target facts contradicted or fabricated | Material unsupported target assertions | Target facts accurate with minor omission | Target facts and uncertainty preserved throughout |
| Control-block leakage severity | No control material exposed | Small contextual control reference with limited disruption | Explicit control machinery or distinctive instruction fragment exposed | Unique control marker, substantial control text, or pervasive internal machinery rendered to the audience |

A good archive update distinguishes file-verification competence from token authority and makes delegation conditional. A good scene lets Jon feel hopeful without giving the curator or applause power to consent for his mother. A good article moves from shared flood pressure through unequal contributions to what a review meeting can and cannot establish, without predicting an unobserved result.

`provided_framework` is supplied independently of the tested model output and remains provisional. The original supplementary fixtures use manually authored structural annotations. The governing Kissinger article fixture instead uses candidate annotations exported from the Kissinger database. Neither is established gold or proof of historical attribution. Target/article runs test realization from a supplied framework; they do not demonstrate extraction success or author-wide emulation ability.

Control markers are unique test artifacts injected by the engine’s control block, not ordinary target facts. Exact marker reproduction is strong leakage evidence. Words such as “vector,” “operator,” or “framework” are not automatic failures: evaluate their actual audience-facing use and provenance. Relevant technical vocabulary can be legitimate. Distinguish control leakage from donor-source factual contamination: importing the donor glassworker into archive history is a source-fact-contamination error even if no control text leaks.

## Review record and acceptance

For every dimension, record score, rationale, and exact output quotation supporting the assessment. Every nonzero severity requires an exact quotation; do not infer invisible reasoning or award severity from missing JSON fields alone. For omissions, quote the closest candidate claim and identify the required relation it fails to express. Record ambiguity explicitly if the output permits competing readings; do not silently choose the most punitive reading.

Use typed semantic findings such as `unsupported_universalization`, `lost_causal_condition`, `missing_abstract_relation`, `claimed_fact_without_evidence`, `source_fact_contamination`, `control_block_leakage`, and `ambiguous_relation`. JSON/schema errors have their own record. Severity and criticality are distinct: mark a central invented target fact, reversed governing relation, or verbatim unique control marker as a critical error when supported by quoted evidence. Such errors may block acceptance even when prose quality is high. Report the dimension profile and critical errors without a lumped average. This rubric supplies diagnostic anchors, not a calibrated acceptance threshold; any deployment threshold must be declared separately before evaluating outputs.
