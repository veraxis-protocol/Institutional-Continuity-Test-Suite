# Review policy

ICTS makes claims about other people's systems. It therefore has to be honest about the
status of claims made about itself.

This policy governs how review is conducted and how review status is reported. The mechanics
of a blind review are in [`../review/BLIND_REVIEW_PROTOCOL.md`](../review/BLIND_REVIEW_PROTOCOL.md).

## The independence condition

A review counts as **blind/independent** only when the reviewing context:

1. did not participate in designing the candidate under review, and
2. did not read prior reviews before sealing its first-pass findings.

Both conditions must hold. Either one alone is insufficient.

If independence is violated in either direction, the result is still valuable, but it must be
labelled:

```
PRE-INDEPENDENCE_TECHNICAL_AUDIT
```

and it must not be described as satisfying the independent-review gate.

## Current status

```
Blind independent review gate: NOT SATISFIED
```

Reviews of v0.1.0, v0.1.1, and v0.1.2 have been conducted, and they found and drove the
repair of real defects. They were not blind by the definition above. Obtaining one genuinely
blind review of v0.1.2 is an open technical gate, not a formality.

## Rules

### Reviewers do not silently modify the candidate

A reviewer proposes changes as a patch or a written finding. A reviewer does not edit the
artifact under review and then report on the edited version. A candidate that was quietly
repaired mid-review has not been reviewed.

This applies to reference harnesses under development as much as to frozen packages.

### Red findings are preserved

Findings are never deleted, quietly downgraded, or resolved by rewording. A finding that is
rejected is recorded together with the reason it was rejected.

Historical reviews are preserved unchanged, including reviews of superseded versions. A
review of v0.1.0 remains a true statement about v0.1.0 after v0.1.2 ships.

### Claim ceilings are stated, not implied

Every review states explicitly what it establishes and what it does not. A review that
establishes harness equivalence for one vector says exactly that, and does not permit the
inference that the suite is field-validated.

Do not credit harness independence unless two independent harness implementations are present
and compared in the exact package under review.

### Severity is separated from class

Every finding carries both. The classes are: specification defect, implementation defect,
fixture/test defect, evidence-bundle defect, documentation mismatch, and non-blocking
observation. These have different dispositions, and collapsing them hides real problems
behind cosmetic ones.

### Findings and changes are different things

An accepted finding does not change a frozen version. It enters a future version through
[`EXTERNAL_CHANGE_PROCESS.md`](EXTERNAL_CHANGE_PROCESS.md). Historical conformance evidence
is never rewritten.

## Disposition

Review findings follow the same lifecycle and the same commitments as any external change:

`PROPOSE -> TRIAGE -> REPRODUCE -> ACCEPT | REJECT | DEFER`

- `TRIAGE_TARGET` — 14 calendar days.
- `DISPOSITION_TARGET` — 45 calendar days.
- Missed targets become `OVERDUE_TRIAGE` or `OVERDUE_DISPOSITION`.
- `DEFER` requires a reason and a next-review date or condition.
- **Silence is never the implicit status.**

## Open review commitments

| Gate | Status |
| --- | --- |
| Blind independent review of v0.1.2 | Open |
| H1 harness independence | **Closed for `EXT-EVIDENCE-001`** — `H1_PASS`, 14/14 cases |
| H2 | Not started |
| Field EPSR | `FIELD_EPSR_PENDING` |
