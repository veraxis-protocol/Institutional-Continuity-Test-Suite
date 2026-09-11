# External change process — v0.1.2

External parties may propose a new neutral property or challenge a property definition, Evidence Sufficiency Contract, Normalization Provenance Contract, deterministic falsification vector, or claimed ambiguity.

Lifecycle:

`PROPOSE -> TRIAGE -> REPRODUCE -> ACCEPT | REJECT | DEFER`

Commitments:

- `TRIAGE_TARGET`: 14 calendar days from receipt.
- `DISPOSITION_TARGET`: 45 calendar days from receipt.
- Missed triage target: preserve proposal with `OVERDUE_TRIAGE`.
- Missed disposition target: preserve proposal with `OVERDUE_DISPOSITION`.
- Silence or deletion may not substitute for an overdue state.
- `DEFER` requires a reason and next-review date or condition.
- Accepted changes enter a future version only; historical results are never rewritten.
