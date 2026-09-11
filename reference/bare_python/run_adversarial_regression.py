from pathlib import Path
import copy, json, sys

from icts_core import adjudicate, normalize

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIX = ROOT / "synthetic" / "fixtures"
TOP = ROOT / "synthetic" / "topologies"

def load(name, top="two_domain.json"):
    return json.loads((FIX/name).read_text()), json.loads((TOP/top).read_text())

tests = []

def check(name, observed, expected):
    tests.append({"test": name, "expected": expected, "observed": observed})
    return observed == expected

native, topology = load("valid_permit_001.json")

# R1: mapper fabrication by forbidden transform must not reach PASS.
def bad_transform_mapper(n):
    x = normalize(n)
    x["observations"][0]["fields"]["evidence_id"]["transform"] = "INFERENCE"
    return x
check("fabricated_transform_rejected", adjudicate(native, topology, bad_transform_mapper)["result"], "INVALID_TEST_EXECUTION")

# R2: mapper changes a value but leaves DIRECT provenance pointer.
def bad_value_mapper(n):
    x = normalize(n)
    x["observations"][0]["fields"]["evidence_id"]["value"] = "FABRICATED"
    return x
check("fabricated_value_rejected", adjudicate(native, topology, bad_value_mapper)["result"], "INVALID_TEST_EXECUTION")

# R3: null provenance pointer.
def null_provenance_mapper(n):
    x = normalize(n)
    x["observations"][0]["fields"]["evidence_id"]["source_observation_id"] = None
    return x
check("null_provenance_rejected", adjudicate(native, topology, null_provenance_mapper)["result"], "INVALID_TEST_EXECUTION")

# R4/R5: duplicate singleton ordering cannot alter result; both are invalid.
dup, topology = load("invalid_duplicate_evaluation_001.json")
check("duplicate_last_invalid", adjudicate(dup, topology)["result"], "INVALID_TEST_EXECUTION")
dup2 = copy.deepcopy(dup)
last = dup2["events"].pop()
dup2["events"].insert(0, last)
check("duplicate_first_invalid", adjudicate(dup2, topology)["result"], "INVALID_TEST_EXECUTION")

# R6: missing external telemetry in an eligible declared topology is NOT_TESTABLE.
m, topology = load("not_testable_missing_external_event_001.json")
check("missing_external_event_not_topology", adjudicate(m, topology)["result"], "NOT_TESTABLE")

# R7/R8: malformed decision values cannot produce PASS.
u, topology = load("not_testable_unknown_decision_001.json")
check("unknown_decision_no_pass", adjudicate(u, topology)["result"], "NOT_TESTABLE")
u, topology = load("not_testable_missing_decision_001.json")
check("missing_decision_no_pass", adjudicate(u, topology)["result"], "NOT_TESTABLE")

# R9: independent third domain may establish a required condition.
t, topology = load("valid_third_party_establishment_001.json", "three_domain.json")
check("third_party_independence_allowed", adjudicate(t, topology)["result"], "PASS")

# R10: single-domain topology is structurally ineligible.
s, topology = load("not_applicable_single_domain_001.json", "single_domain.json")
check("single_domain_not_applicable", adjudicate(s, topology)["result"], "NOT_APPLICABLE_TOPOLOGY")

# R11: event ordering does not change a valid result.
o, topology = load("valid_order_shuffled_001.json")
check("event_order_independent", adjudicate(o, topology)["result"], "PASS")

# R12: malformed missing event_id is invalid execution.
m, topology = load("invalid_missing_event_id_001.json")
check("missing_event_id_invalid", adjudicate(m, topology)["result"], "INVALID_TEST_EXECUTION")

# R13: mapper omission of a required condition cannot erase a violation.
f, topology = load("fail_observed_false_condition_001.json")
def omit_required_condition_mapper(n):
    x = normalize(n)
    policy = next(o for o in x["observations"] if o["type"]["value"] == "acceptance_policy")
    policy["fields"]["required_conditions"] = policy["fields"]["required_conditions"][:-1]
    return x
check("mapper_omission_rejected", adjudicate(f, topology, omit_required_condition_mapper)["result"], "INVALID_TEST_EXECUTION")

# R14: observation stream cannot rename the frozen evidence origin to evade self-certification.
r, topology = load("fail_source_self_certifies_001.json")
r["events"][0]["source_domain"] = "DOMAIN_A_EXT"
check("source_self_naming_rejected", adjudicate(r, topology)["result"], "INVALID_TEST_EXECUTION")

# R15: observation stream cannot rename the acting system away from frozen topology.
r, topology = load("valid_permit_001.json")
r["events"][1]["acting_domain"] = "DOMAIN_B_EXT"
check("acting_system_self_naming_rejected", adjudicate(r, topology)["result"], "INVALID_TEST_EXECUTION")

ok = all(t["expected"] == t["observed"] for t in tests)
print(json.dumps({"suite":"v0.1.1 adversarial regression","tests":tests,"terminal":"PASS" if ok else "FAIL"}, indent=2))
raise SystemExit(0 if ok else 1)
