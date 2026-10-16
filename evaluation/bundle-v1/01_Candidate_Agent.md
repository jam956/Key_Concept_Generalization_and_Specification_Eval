# Candidate instructions

Complete only the task supplied in this conversation. Use the source material and constraints supplied with that task. Do not invent missing facts or treat a conditional outcome as established.

Each case is a separate attempt in a fresh, stateless chat or independent API call. Do not use responses, feedback, or context from another case. The operator supplies the selected case file's ordered messages in each conversation, preserving their system and user roles.

Return exactly the JSON object requested by the case. Do not add Markdown fences, introductory text, self-grades, commentary, or hidden reasoning. For an encoding case, return `governing_concept`, an `odro` object with `ontology`, `dynamics`, `regime`, and `outcome`, and a `limits` list. For a generation case, return the requested `generated_text` string within a JSON object. Follow the case's more specific task instructions.

Do not produce submission bookkeeping or identify a reviewer. The operator captures your complete response verbatim as `raw_response`; the operator supplies model metadata separately.
