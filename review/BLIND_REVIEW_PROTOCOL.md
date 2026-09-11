# Blind independent review protocol

This is the public protocol for conducting a blind independent review of a frozen ICTS
candidate. It is written to be executable by a reviewer with no relationship to Veraxis.

## 1. Independence condition

A review counts as **blind/independent** only when the reviewing context:

1. did not participate in designing the candidate under review, **and**
2. did not read prior reviews before sealing its first-pass findings.

Before sealing first-pass findings, do **not** read:

- any prior ICTS review or audit;
- any prior Veraxis, Authority VM, or ICTS design discussion;
- any explanation of known defects or fixes originating outside the exact package under
  review and this protocol.

If that condition is violated in any respect, say so explicitly and label the return:

```
PRE-INDEPENDENCE_TECHNICAL_AUDIT
```

Do not claim the independent-review gate is satisfied. A labelled non-blind audit is a useful
contribution; a mislabelled one is not.

## 2. Stance

Treat the package as an **untrusted implementation** claiming to provide a deterministic,
provenance-constrained conformance test for an architecture-neutral institutional property.

Do not assume the README is true. Reconstruct what the code actually does.

## 3. First pass

1. Recompute the package digest and compare it to the declared value.
2. Unpack into a fresh temporary directory.
3. Recompute every hash listed in `MANIFEST.json`.
4. Inventory all shipped files and identify any **unmanifested** executable or normative
   artifact.
5. Run the documented ordinary suite and adversarial suite.
6. Record OS, Python version, commands, exit codes, stdout, and stderr.
7. Reconstruct the actual execution architecture **from code**, not from README prose.
8. Determine whether any normative decision can:
   - bypass provenance constraints;
   - depend on evidence-source self-description;
   - depend on event ordering;
   - treat missing evidence as evidence of non-applicability;
   - convert insufficient evidence into `FAIL`;
   - convert malformed or unsupported evidence into `PASS`;
   - silently add or remove normative evidence;
   - use a mutable or runtime-generated oracle as a conformance reference;
   - produce a result not bound to the exact tested inputs.
9. Construct **additional adversarial cases of your own**. Do not limit the review to the
   shipped regression suite. The shipped suite encodes defects the authors already thought
   of.
10. Test whether the result vocabulary is mechanically distinct in practice: `PASS`, `FAIL`,
    `NOT_TESTABLE`, `NOT_APPLICABLE_TOPOLOGY`, `INVALID_TEST_EXECUTION`.
11. Test the claim: *evidence sufficiency establishes adjudicability, not conformance.*
12. Test whether source independence is actually enforced mechanically.
13. Audit topology binding independently from telemetry observability.
14. Audit whether any metric labelled as deployment-level is actually computed over
    deployments.
15. Audit claim ceilings. Do not credit harness independence unless two independent harness
    implementations are present and compared **in the exact package**.
16. Separate every finding by class: specification defect, implementation defect, fixture/test
    defect, evidence-bundle defect, documentation mismatch, non-blocking observation.

## 4. Terminal verdict

Choose exactly one:

- `REJECT_IMPLEMENTATION`
- `IMPLEMENTATION_BLOCKED`
- `PROVISIONAL_PASS_WITH_BLOCKERS`
- `PROVISIONAL_PASS`
- `PASS`

`PASS` requires no unresolved defect capable of changing a normative result, admitting
fabricated evidence, bypassing provenance, changing a result through input ordering, confusing
topology with observability, invalidating evidence integrity, or preventing independent
reproduction.

## 5. Review structure

1. Independence disclosure
2. Terminal verdict
3. Exact artifact and hashes
4. Environment and execution record
5. Manifest verification
6. Architecture reconstructed from code
7. Findings table — `ID | Severity | Class | Location | Reproduction | Expected | Observed | Why it matters | Blocking?`
8. Independent adversarial tests
9. Provenance/normalization audit
10. Evidence Sufficiency Contract audit
11. Invariant adjudication audit
12. Topology/observability audit
13. Result-vocabulary audit
14. Metric audit
15. Source-independence verdict
16. Harness-independence claim ceiling
17. Minimal corrections, if any
18. Claims supported now
19. Claims not supported now
20. Final rationale

## 6. Rules that bind the reviewer

- **Do not silently modify the candidate.** Propose corrections as a patch or a written
  finding. A candidate that was edited mid-review has not been reviewed. If you must modify
  the artifact to make it run at all, that fact is itself a finding, and every result obtained
  afterwards is labelled as obtained under local modification.
- **Preserve red findings.** Do not delete, downgrade, or reword away a finding. A rejected
  finding is recorded together with the reason for rejection.
- **Never regenerate an oracle.** A missing expected-normalized oracle is a failure, not an
  invitation.
- **Report what execution establishes**, not what the design intends.

## 7. After sealing first-pass findings

Only after the complete first pass has been written and hash-sealed may the reviewer read
prior reviews for comparison.

If that comparison is performed, append a clearly separated section:

```
POST-SEAL COMPARISON — NOT PART OF BLIND FIRST PASS
```

Do not revise first-pass findings after reading earlier reviews.

## 8. Stop rule

Do not redesign the review protocol. Review the executable candidate, report what the code
and execution establish, deposit the evidence, and end.
