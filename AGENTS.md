# Evaluation contracts

Keep overgeneralization, undergeneralization, target generation and control leakage separate. Do not turn ordinal pilot judgments into a general intelligence score or an asserted percentage of concepts understood.

Fixtures contain model input and reviewer-only annotations. Prompt construction must use an explicit allowlist and never reveal rubrics or reference answers to the tested model. A submitted draft cannot serve as its own reference.

Preserve all attempts, runtime failure states, exact prompts and response hashes. Failed runs and missing reviews cannot inflate semantic averages. Reviews must bind to the correct response and quote actual evidence; automatic canary flags are not semantic grades.

Use read-only source access and work-scoped exports. Keep original databases, private source text, credentials and machine-specific paths out of tracked files. Do not publish candidate annotations as validated truth. Full model calls must be explicit; normal tests use mocks.

Run `python3 -m unittest discover -s tests -v` and `python3 -m kce_eval validate fixtures` after relevant changes. Add a regression for changed scoring or provenance behavior. Use independent held-out and human-calibrated evaluation before making predictive claims.
