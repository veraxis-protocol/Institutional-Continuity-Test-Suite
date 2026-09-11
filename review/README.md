# Review

ICTS asks institutions to trust a test. That obligates ICTS to be reviewed adversarially, and
to report review status accurately even when the answer is unflattering.

## Status

```
Blind independent review gate: NOT SATISFIED
```

Reviews of v0.1.0, v0.1.1, and v0.1.2 have been conducted and drove real repairs. None of
them meets the independence condition, so none of them satisfies the gate.

Obtaining **one truly blind review of v0.1.2** is a current technical gate.

## Contents

- [`BLIND_REVIEW_PROTOCOL.md`](BLIND_REVIEW_PROTOCOL.md) — the public protocol for conducting
  a blind independent review of a frozen ICTS candidate.

Policy governing how review status may be reported is in
[`../governance/REVIEW_POLICY.md`](../governance/REVIEW_POLICY.md).

## Why prior reviews do not count

A review counts as blind/independent only when the reviewing context did not participate in
designing the candidate and did not read prior reviews before sealing its first-pass
findings. Prior ICTS reviews were conducted in contexts that had design exposure, prior-review
exposure, or both.

Such a review is still worth doing — it is how the v0.1.0 → v0.1.2 repairs were found — but
it is labelled `PRE-INDEPENDENCE_TECHNICAL_AUDIT` and does not satisfy the gate.

## What a review is not allowed to do

- It may not silently modify the candidate under review.
- It may not delete, downgrade, or reword away red findings.
- It may not claim a gate that the evidence in the reviewed package does not support.

## Deliberately absent

Raw review transcripts and session artifacts are **not** committed here. Prior review content
is not normative material, and publishing it as if it were part of the specification would
confuse what ICTS actually requires with what one reviewer happened to say.

What belongs in this repository is the protocol, the policy, and accurate status. Findings
that are accepted enter a future version through
[`../governance/EXTERNAL_CHANGE_PROCESS.md`](../governance/EXTERNAL_CHANGE_PROCESS.md).
