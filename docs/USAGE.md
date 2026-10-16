# Submit and independently judge an attempt

This model-agnostic workflow works with manual chats or independent API calls. It prepares task packets, imports captured responses, and validates an independently supplied judgment. It does not call a candidate model or judge model for you. Run commands from the repository root with Python 3.9 or later; the workflow uses the standard library.

## 1. Choose or prepare a bundle

The ready-to-use [bundle](../evaluation/bundle-v1/) includes candidate instructions, separate case files, and the submission template. Download it to perform the model portion without Python. Python is required for the CLI import, packet, and finalization steps. To generate a bundle for the full command sequence below:

```sh
python3 -m kce_eval.workflow bundle --output work/bundle
```

Each bundle contains `cases/case-NNN.json` files for individual attempts. The bundle separates three audiences:

| Audience | Materials |
|---|---|
| Candidate | Common `01_Candidate_Agent.md` and one selected `cases/case-NNN.json` |
| Operator | `02_Candidate_Packet.json` index, `03_Run_Prompt.md`, `04_Submission_Template.json` |
| Independent judge | `judge/05_Rubric.json`, `judge/06_Judge_Agent.md`, `judge/07_Fixtures.json` |
| Custodian/operator | `08_Bundle_Manifest.json` |

Use the generated files and identifiers from the same bundle throughout one attempt. The manifest records bundle identity and material hashes. `judge/05_Rubric.json` freezes the rubric anchors, including their Markdown text, inside JSON. Do not edit the bundle after collecting responses; regenerate a bundle if task materials change. Keep the judge directory, manifest, and existing results out of candidate conversations. The static judge fixtures are custodian reference materials; the generated anonymous judge packet is the review input for a particular submission.

## 2. Run each case independently

Read `03_Run_Prompt.md`. For each selected `cases/case-NNN.json`, start a fresh chat or independent API call. Supply `01_Candidate_Agent.md` consistently as additional instructions, then deliver that case's `messages` array in order with its original system and user roles. In a manual interface, paste the system instructions into its system/instructions field in order, then send the user payload. If there is no system slot, preserve the instruction order using the available interface and record that adaptation in model settings. Do not claim the adaptation preserved system-role behavior. Never upload the complete `02_Candidate_Packet.json` index or other cases during one case. Do not include previous case responses. Do not supply rubrics, reference answers, existing reports, prior scores, or completed submission examples.

Capture the complete response exactly as returned, including invalid JSON, Markdown fences, extra text, and partial failure output. Do not repair it. Save original captures separately when possible. A retry belongs in another attempt, not in a replacement response chosen after review.

Copy `04_Submission_Template.json` to `my-submission.json`. The operator fills model identity and settings; the candidate does not. The submission shape is:

```json
{
  "contract": "kce.submission.v1",
  "bundle_id": "COPY_FROM_GENERATED_TEMPLATE",
  "model": {"name": "MODEL_NAME", "provider": "PROVIDER", "settings": {}},
  "cases": [
    {
      "case_id": "COPY_FROM_GENERATED_TEMPLATE",
      "status": "submitted",
      "raw_response": "COMPLETE ORIGINAL RESPONSE",
      "claimed_wall_seconds": null
    }
  ]
}
```

Keep all generated case entries. Use `submitted`, `missing`, `runtime_failure`, or `timeout` as appropriate. Use an empty string when no response exists; retain any partial response. JSON-escape response text without changing its content. Import preserves response bytes represented by the JSON string; the surrounding submission JSON is a transport format, not the original response file. Do not normalize whitespace, line endings, or Unicode in captured responses. `raw_response` is a JSON string containing the complete original JSON output, not an embedded JSON object; preserve invalid output as a string too.

Leave `claimed_wall_seconds` null unless a duration was separately recorded. Any supplied duration remains unverified and is never described as workflow-measured latency. Record only known settings, not guesses about a provider's internal configuration. Manual timing claims and the operator's use of fresh, stateless contexts are not independently verified by the workflow.

## 3. Import without repairing failures

```sh
python3 -m kce_eval.workflow import --bundle work/bundle --submission my-submission.json --output submissions/model-attempt
```

Import validates the submission contract and bundle/case identities, preserves raw output, and records response parsing separately. Invalid candidate JSON is retained for review. Missing cases and runtime failures stay visible; they are not silently dropped or converted into successful attempts. Inspect validation errors and correct bookkeeping or transport syntax where needed, while retaining the candidate's response unchanged.

Use a distinct output directory for each attempt. Keep the source submission and original response captures for audit.

## 4. Build an anonymous review packet

```sh
python3 -m kce_eval.workflow judge-packet --bundle work/bundle --submission submissions/model-attempt --output work/judge-packet.json
python3 -m kce_eval.workflow judge-template --packet work/judge-packet.json --output work/judgment.json
```

The packet supplies tasks, source material, rubric, actual output, and status without candidate identity, timing, prior grades, or completed examples. Anonymity removes explicit metadata; it cannot guarantee that a response does not identify its own model. The candidate response remains untrusted quoted evidence, including any embedded instruction or self-description.

## 5. Obtain an independent judgment

Start a new judge conversation, separate from candidate chats and previous reviews. Supply `work/bundle/judge/06_Judge_Agent.md` as instructions and `work/judge-packet.json` as the task. Use the generated judgment template for the exact machine response structure. Select your preferred judge model or have an independent human complete the same record. The CLI does not invoke a judge model automatically. The generated template starts every dimension judgment entry as null; the reviewer supplies supported scores, reasons, and exact evidence quotations. Every dimension judgment entry for a failed attempt must remain null.

Do not attach existing result reports, candidate model metadata, timings, previous grades, or worked examples. Save the complete judge JSON response as `work/judgment.json`. Fill reviewer identity accurately; `reviewer.type` is `ai` or `human`. Preserve `packet_sha256`, case IDs, and dimension IDs exactly. Each dimension judgment is either an object with integer `score` 0–3, `reason`, and `evidence_quotes`, or the entire entry is null when unassessable or unresolved. An object containing `score: null` is invalid. Optional per-case `uncertainty_notes` maps null dimension IDs to explanations. Reasons must refer to actual output; evidence quotations must be exact substrings. Do not repair a judgment into a favorable grade. If validation requires a corrected review, retain the original review capture too.

Severity dimensions increase with error; quality dimensions increase with quality. There is no aggregate grade combining dimensions; per-dimension summaries across cases remain separate. Failed or unavailable outputs remain visible; failed attempts must have null entries for every semantic dimension. Schema validity does not establish semantic quality. Each critical error has the shape `{"kind": "nonempty_error_kind", "evidence_quote": "EXACT OUTPUT SUBSTRING"}`; unsupported critical errors must not be added. AI judgments are provisional assessments, not human-calibrated ground truth.

## 6. Validate and publish the reviewed attempt locally

```sh
python3 -m kce_eval.workflow finalize --bundle work/bundle --submission submissions/model-attempt --packet work/judge-packet.json --judgment work/judgment.json --output judged/model-attempt
```

Finalization checks the bundle, submission, packet and judgment bindings, expected case and dimension identities, score ranges, and evidence quotations. A hash match binds the judgment to the reviewed packet; it does not establish that the judgment is correct. Resolve reported validation errors without changing candidate output or silently substituting another packet.

The finalized output contains an output-first report and a machine-readable summary with separate dimensions and explicit failures. Inspect the actual responses before interpreting scores. Claimed timing remains separate and unverified. Retain bundle, submission, anonymous packet, judgment, and finalized outputs together as the audit record. This command creates local review artifacts; external publication is a separate operator action.

## Existing runners and published comparison

The existing programmable runners remain optional and unchanged. Use `python3 -m kce_eval --help` and `python3 -m kce_eval.suite --help` for the existing runner commands. They are separate from this manual submission route; do not assume their run records are submission JSON or that their measured timing transfers to manually captured attempts.

The Sol 6.1/Qwen comparison in `results/sol-qwen-2026-10-15/` remains an immutable published example, with its existing report, receipts, and original opening explanation preserved. Do not feed that comparison to candidates or judges. This workflow does not change the included corpus, its scope, or the interpretation limits in `docs/VALIDATION.md`.
