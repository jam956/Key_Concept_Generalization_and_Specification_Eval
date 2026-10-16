# Run the candidate cases

Operator instructions:

1. Select one `cases/case-NNN.json` file from the bundle. Its `messages` array is the exact case input. Do not upload the complete `02_Candidate_Packet.json` index or other cases to a candidate.
2. For each case, start a new chat with no earlier case history, or make an independent API call with no retained conversation state. Supply `01_Candidate_Agent.md` consistently as additional instructions. Deliver the selected case's `messages` array in order, preserving system and user roles. For manual chat, paste each system instruction in order into the system/instructions field, then send the user payload. If the interface has no system slot, preserve the instruction order in the available interface and record this adaptation in model settings; do not claim exact role equivalence. Use the same chosen model configuration throughout an attempt; record the actual configuration.
3. Capture the complete response verbatim. Do not correct JSON, remove fences, select a favorable excerpt, or replace a failed response with a retry. Record a retry as another submission attempt.
4. In `04_Submission_Template.json`, fill model name, provider, and known settings yourself. For every case, set `status` to `submitted`, `missing`, `runtime_failure`, or `timeout`; put the original response in `raw_response` as a JSON string. Preserve any partial text produced before a failure. An empty response is an empty string.
5. Leave `claimed_wall_seconds` null unless you have a separately recorded duration. A supplied duration is an unverified operator claim; this workflow does not measure it. Do not ask the candidate to supply timing or metadata.
6. Save valid submission JSON and import it using the workflow CLI. Keep the original response captures if available. Import retains submitted response content and records parsing or runtime failures separately.

The candidate receives only the candidate instructions and the current case message. Keep judge materials, reports, prior scores, and completed examples out of every candidate conversation.

The workflow does not independently verify manually claimed timing or whether the operator used fresh, stateless contexts. Keep the original capture record so those claims remain distinguishable from validated output bindings.
