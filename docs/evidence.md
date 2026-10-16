# Evidence and citation model

Evidence is a first-class record, not a footnote string. Each record stores the claim, source title and URL, publisher, publication date when available, retrieval time, relevant excerpt, evidence type, confidence, verification status, and semantic classification.

Classifications are:

- `sourced_fact`: directly supported by the cited source
- `calculated_result`: computed from declared inputs
- `analyst_inference`: interpretation based on cited evidence
- `unavailable_information`: explicitly not found in reviewed public sources

Material report claims carry evidence UUIDs. The report links to `/api/v1/evidence/{id}` and the verifier checks that each non-unavailable material claim references an accepted record that appears in the report. Failed claims are downgraded to unavailable information before persistence.

The final evidence ledger also links the original source. Source excerpts are rendered as text, not raw HTML. External page content cannot satisfy a claim merely by appearing in conversation history.

Coverage represents the proportion of planned research supported by reviewed evidence. Confidence is the mean confidence of persisted evidence records. Both are bounded from zero to one and are labelled calculated results.

