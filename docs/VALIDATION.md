# Validation plan, not a validated claim

## Measurement boundary

The provisional construct is source-bounded generalization: replacing incidental identities with functional relations while retaining conditions, actor distinctions, direction and qualified outcomes. Overgeneralization adds scope/certainty or removes necessary conditions. Undergeneralization retains incidental bindings or fails to extract a useful relation. A merely vague label can also lose the invariant; classify the exact error from evidence rather than forcing one mutually exclusive label. Both severities may be nonzero in one answer. Appropriate abstention and preserving a necessary particular are not automatically undergeneralization.

Keep extraction, supplied-framework generation, and end-to-end generation distinct. The separate target/article fixtures avoid making generation performance a mechanical consequence of the model's own extraction. Record control-block leakage independently from fidelity and writing quality. Compare schemas and runtime success separately from semantic judgments.

## Calibrate before ranking

1. Freeze fixtures, accepted alternatives and grading rules before collecting a comparison. Label original starter annotations provisional.
2. Use at least two reviewers on a calibration subset. Blind model identity for adjudication where feasible, record disagreements, and assess ordinal agreement. Do not present an LLM judge's confidence as calibrated probability.
3. Keep new private holdout passages and relation families outside the repository. Public development and validation splits are for reproducibility, not a claim of contamination-free evaluation.
4. Test paraphrase, changed-condition, superficially similar/different-relation and different-surface/same-relation cases. Reserve topic and relation families across development and evaluation.
5. Preserve exact model/runtime identity, quantization, thinking/effort, budget, prompt variant, retries, tool availability, and cold/warm conditions. Repeat fresh runs; keep failed attempts rather than reporting only repaired successes.

## Establish predictive value prospectively

Define a downstream outcome independently: human-reviewed success on new article construction or actual Cortex conversation, including correction and agency requirements. Pre-register whether overgeneralization and undergeneralization rates are expected to predict each outcome. These are hypotheses, not built-in truths.

Collect several distinct model families and sizes, not only Qwen and SOL. Fit predictions on development models/topics and test on held-out model families and task families. Compare against simple baselines such as model size, format validity, output length and generation-only scores. Test whether KCE measurements add predictive information beyond those baselines. A within-model prompt intervention is a separate causal experiment from between-model correlation.

Report failure-specific associations, uncertainty and calibration, not only a favorable rank correlation. Model variants and repeated outputs are clustered observations; do not inflate sample size by treating many responses from two models as many independent models. Keep wording and rubric updates versioned. No predictive score or 90% claim is asserted by this starter suite.
