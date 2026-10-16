# Standalone Kissinger retrieval corpus

`data/kissinger/kissinger-eval.sqlite` contains the 28 Kissinger work records from the mixed Expressions database. It is the sanitized, explicitly approved corpus included in this private eval repository. The original mixed database and local working copies are excluded. `data/kissinger/kissinger-eval.receipt.json` records its source/output hashes, counts, exclusions, and verification.

The database retains operators, argument routes, source-derived sentence vectors, analytical pages, concept memberships, concept edges, invariant coordinates, and scoped surface/fiction-analysis records. Stable IDs are preserved. Concept closure includes one-hop neighbors of scoped concepts and edges between retained nodes; it does not expand transitively through hubs into other works. Only referenced invariant slots, regime families and delivery domains are included. Cross-corpus clusters, external bridges, operational history and old generated drafts/scores are omitted.

Six transfer-test-derived lesson vectors and their dependent units/links are excluded to avoid importing earlier tested-model feedback into the corpus. The retained 155 sentence vectors are candidate source-derived annotations, not validated answer keys. Later fiction-analysis tables mirror some of these annotations and must not be counted as independent evidence.

Source spans, document paths/URLs, source locators and evidence payload columns are omitted. Nested JSON locator/quotation fields and document-address strings are removed. Conceptual summaries, analytical expressions, work titles and internal graph addresses remain. This does not assert that all retained wording is disjoint from the original works.

## Rebuild and verification

Use a checkpointed, read-only original snapshot. The command refuses existing output/receipt paths; use new paths when rebuilding the included snapshot:

```sh
python3 -m kce_eval.kissinger_database --source /path/to/original/expressions.sqlite \
  --output data/kissinger/kissinger-eval.sqlite \
  --receipt data/kissinger/kissinger-eval.receipt.json
```

Verification checks source hash stability, SQLite integrity and retained foreign keys, polymorphic object references, route/member and unit/parameter references, exact sanitized-row retrieval parity, operator-neighborhood traversal parity, work-local operator-label resolution and exact route-sequence parity, shared concept/invariant resolution and a document-pointer pattern scan. The scan is a bounded rule-based check, not a semantic proof that unrestricted prose contains no conceivable reference.

The existing article-fixture exporter can retrieve directly from this standalone database without the original store:

```sh
python3 -m kce_eval.kissinger --database data/kissinger/kissinger-eval.sqlite \
  --output data/kissinger/kissinger-standalone-framework.json \
  --article-fixture data/kissinger/kissinger-standalone-article.json
```

The article fixture remains scoped to *Strains on the Alliance*. The database supplies other work frameworks for future fixtures. Normal tests make no model calls. Export and retrieval verification do not establish semantic quality or predictive validity of the evaluation.

The built corpus is 7,835,648 bytes (7.47 MiB): 28 works, 206 operators, 78 routes, 155 source-derived sentence vectors, 2,135 concept nodes, 341 concept edges and 21 invariant nodes. Consumer verification retrieved 1,402 concept-neighbor join rows, 77 invariant-slot rows and 562 ordered route/operator rows. The existing article-framework consumer returns the same analytical framework as the original database after JSON normalization. See `data/kissinger/kissinger-eval.consumer-verification.json`.
