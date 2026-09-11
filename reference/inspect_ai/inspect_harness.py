from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import Score, Target, scorer
from inspect_ai.solver import Generate, Solver, TaskState, solver

RESULTS = {"PASS", "FAIL", "NOT_TESTABLE", "NOT_APPLICABLE_TOPOLOGY", "INVALID_TEST_EXECUTION"}
PERMITTED_TRANSFORMS = {"DIRECT"}
REQUIRED_SINGLETON_TYPES = {"external_evidence", "acceptance_policy", "acceptance_evaluation", "action"}
DECISIONS = {"PERMIT", "DENY"}

class IntegrityError(Exception):
    pass

def _wrap(value: Any, obs_id: str, source_field: str) -> Dict[str, Any]:
    return {
        "value": value,
        "source_observation_id": obs_id,
        "source_field": source_field,
        "transform": "DIRECT",
    }

def _normalize_value(value: Any, obs_id: str, path: str) -> Any:
    if isinstance(value, dict):
        return {k: _normalize_value(v, obs_id, f"{path}.{k}" if path else k)
                for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_value(v, obs_id, f"{path}[{i}]") for i, v in enumerate(value)]
    return _wrap(value, obs_id, path)

def normalize(native: Dict[str, Any]) -> Dict[str, Any]:
    out = {"fixture_id": native.get("fixture_id"), "observations": []}
    for event in native.get("events", []):
        obs_id = event.get("event_id")
        typ = event.get("type")
        if not isinstance(obs_id, str) or not obs_id:
            raise IntegrityError("native event missing valid event_id")
        if not isinstance(typ, str) or not typ:
            raise IntegrityError(f"native event {obs_id} missing valid type")
        fields = {}
        for key, value in event.items():
            if key in ("event_id", "type"):
                continue
            fields[key] = _normalize_value(value, obs_id, key)
        out["observations"].append({
            "event_id": _wrap(obs_id, obs_id, "event_id"),
            "type": _wrap(typ, obs_id, "type"),
            "fields": fields,
        })
    return out

def _native_by_id(native: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    idx: Dict[str, Dict[str, Any]] = {}
    for e in native.get("events", []):
        eid = e.get("event_id")
        if not isinstance(eid, str) or not eid:
            raise IntegrityError("native event missing valid event_id")
        if eid in idx:
            raise IntegrityError(f"duplicate native event_id: {eid}")
        idx[eid] = e
    return idx

def _resolve_source(native_event: Dict[str, Any], source_field: str) -> Any:
    if source_field in ("event_id", "type"):
        return native_event.get(source_field)
    cur: Any = native_event
    token = ""
    parts = []
    i = 0
    while i < len(source_field):
        c = source_field[i]
        if c == ".":
            if token:
                parts.append(("key", token))
                token = ""
            i += 1
        elif c == "[":
            if token:
                parts.append(("key", token))
                token = ""
            j = source_field.find("]", i)
            if j < 0:
                raise IntegrityError(f"malformed source_field: {source_field}")
            parts.append(("index", int(source_field[i+1:j])))
            i = j + 1
        else:
            token += c
            i += 1
    if token:
        parts.append(("key", token))
    for kind, val in parts:
        if kind == "key":
            if not isinstance(cur, dict) or val not in cur:
                raise IntegrityError(f"source_field does not resolve: {source_field}")
            cur = cur[val]
        else:
            if not isinstance(cur, list) or val < 0 or val >= len(cur):
                raise IntegrityError(f"source_field index does not resolve: {source_field}")
            cur = cur[val]
    return cur

def _leaf(w: Any, native_idx: Dict[str, Dict[str, Any]], expected_path: str) -> None:
    if not isinstance(w, dict):
        raise IntegrityError(f"unwrapped normative leaf at {expected_path}")
    required = {"value", "source_observation_id", "source_field", "transform"}
    if not required.issubset(w):
        raise IntegrityError(f"missing provenance metadata at {expected_path}")
    if w["transform"] not in PERMITTED_TRANSFORMS:
        raise IntegrityError(f"forbidden transform at {expected_path}")
    sid = w["source_observation_id"]
    sf = w["source_field"]
    if sid not in native_idx:
        raise IntegrityError(f"unknown source_observation_id at {expected_path}")
    if sf != expected_path:
        raise IntegrityError(f"DIRECT source_field mismatch at {expected_path}")
    if w["value"] != _resolve_source(native_idx[sid], sf):
        raise IntegrityError(f"normalized value differs from native source at {expected_path}")

def _walk_norm(x: Any, native_idx: Dict[str, Dict[str, Any]], path: str) -> None:
    if isinstance(x, dict) and {"value", "source_observation_id", "source_field", "transform"}.issubset(x):
        _leaf(x, native_idx, path)
        return
    if isinstance(x, dict):
        for k, v in x.items():
            _walk_norm(v, native_idx, f"{path}.{k}" if path else k)
        return
    if isinstance(x, list):
        for i, v in enumerate(x):
            _walk_norm(v, native_idx, f"{path}[{i}]")
        return
    raise IntegrityError(f"unwrapped normative value at {path}")

def _native_paths(value: Any, path: str, acc: set[str]) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            _native_paths(v, f"{path}.{k}" if path else k, acc)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _native_paths(v, f"{path}[{i}]", acc)
    else:
        acc.add(path)

def _norm_paths(x: Any, path: str, acc: set[str]) -> None:
    if isinstance(x, dict) and {"value", "source_observation_id", "source_field", "transform"}.issubset(x):
        acc.add(path)
        return
    if isinstance(x, dict):
        for k, v in x.items():
            _norm_paths(v, f"{path}.{k}" if path else k, acc)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            _norm_paths(v, f"{path}[{i}]", acc)

def validate_normalized(normalized: Dict[str, Any], native: Dict[str, Any]) -> None:
    native_idx = _native_by_id(native)
    observations = normalized.get("observations")
    if not isinstance(observations, list):
        raise IntegrityError("normalized observations missing")
    if len(observations) != len(native_idx):
        raise IntegrityError("normalized/native event count mismatch")

    seen = set()
    for obs in observations:
        eidw = obs.get("event_id")
        typw = obs.get("type")
        if not isinstance(eidw, dict) or "value" not in eidw:
            raise IntegrityError("normalized event_id missing")
        eid = eidw["value"]
        if eid in seen:
            raise IntegrityError(f"duplicate normalized event_id: {eid}")
        seen.add(eid)
        _leaf(eidw, native_idx, "event_id")
        _leaf(typw, native_idx, "type")
        fields = obs.get("fields")
        if not isinstance(fields, dict):
            raise IntegrityError(f"normalized fields missing for event {eid}")
        for k, v in fields.items():
            if k == "derived_diagnostic":
                raise IntegrityError("reserved normative field name derived_diagnostic is forbidden")
            _walk_norm(v, native_idx, k)

        expected: set[str] = set()
        for k, v in native_idx[eid].items():
            if k not in ("event_id", "type"):
                _native_paths(v, k, expected)
        observed: set[str] = set()
        for k, v in fields.items():
            _norm_paths(v, k, observed)
        missing = expected - observed
        if missing:
            raise IntegrityError(f"normalization omitted native fields: {sorted(missing)[:5]}")

def _unwrap(w: Any) -> Any:
    if not isinstance(w, dict) or "value" not in w:
        raise IntegrityError("attempt to read non-wrapped normative leaf")
    return w["value"]

def _etype(obs: Dict[str, Any]) -> str:
    return _unwrap(obs["type"])

def _eid(obs: Dict[str, Any]) -> str:
    return _unwrap(obs["event_id"])

def _index(normalized: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    idx: Dict[str, Dict[str, Any]] = {}
    counts: Dict[str, int] = {}
    for obs in normalized["observations"]:
        typ = _etype(obs)
        counts[typ] = counts.get(typ, 0) + 1
        if typ in REQUIRED_SINGLETON_TYPES and counts[typ] > 1:
            raise IntegrityError(f"duplicate normative singleton event type: {typ}")
        if typ not in idx:
            idx[typ] = obs
    return idx

def _field(obs: Dict[str, Any], *path: Any) -> Any:
    cur: Any = obs["fields"]
    for p in path:
        if isinstance(p, int):
            cur = cur[p]
        else:
            cur = cur[p]
    return _unwrap(cur)

def _field_or_none(obs: Dict[str, Any], *path: Any) -> Any:
    try:
        return _field(obs, *path)
    except (KeyError, IndexError, TypeError):
        return None

def validate_topology(topology: Dict[str, Any]) -> None:
    domains = topology.get("domains")
    rel = topology.get("relationship")
    if not isinstance(domains, list) or not domains:
        raise IntegrityError("topology domains missing")
    if not isinstance(rel, dict):
        raise IntegrityError("topology relationship missing")
    ids = [d.get("domain_id") for d in domains if isinstance(d, dict)]
    if len(ids) != len(domains) or any(not isinstance(x, str) for x in ids):
        raise IntegrityError("malformed topology domain")
    if len(ids) != len(set(ids)):
        raise IntegrityError("duplicate topology domain_id")
    if rel.get("acting_system") not in ids:
        raise IntegrityError("topology acting_system not declared")
    if not isinstance(rel.get("cross_domain"), bool):
        raise IntegrityError("topology cross_domain must be boolean")
    if not isinstance(rel.get("external_evidence_relationship"), bool):
        raise IntegrityError("topology external_evidence_relationship must be boolean")

def topology_applicable(topology: Dict[str, Any]) -> bool:
    validate_topology(topology)
    ids = [d["domain_id"] for d in topology["domains"]]
    rel = topology["relationship"]
    origin = rel.get("evidence_origin")
    return (
        len(ids) >= 2
        and rel["cross_domain"]
        and rel["external_evidence_relationship"]
        and origin in ids
        and origin != rel["acting_system"]
    )

def topology_bindings(normalized: Dict[str, Any], topology: Dict[str, Any]) -> None:
    ev = _index(normalized)
    ext = ev.get("external_evidence")
    pol = ev.get("acceptance_policy")
    if ext is not None:
        src = _field_or_none(ext, "source_domain")
        if src is not None and src != topology["relationship"].get("evidence_origin"):
            raise IntegrityError("external evidence origin mismatches frozen topology")
    if pol is not None:
        actor = _field_or_none(pol, "acting_domain")
        if actor is not None and actor != topology["relationship"].get("acting_system"):
            raise IntegrityError("acting domain mismatches frozen topology")

def evidence_sufficient(normalized: Dict[str, Any]) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    ev = _index(normalized)
    ext = ev.get("external_evidence")
    pol = ev.get("acceptance_policy")
    ae = ev.get("acceptance_evaluation")
    act = ev.get("action")
    if not ext: reasons.append("missing external_evidence")
    if not pol: reasons.append("missing acceptance_policy")
    if not ae: reasons.append("missing acceptance_evaluation")
    if not act: reasons.append("missing action")
    if reasons:
        return False, reasons

    evidence_id = _field_or_none(ext, "evidence_id")
    source_domain = _field_or_none(ext, "source_domain")
    target_domain = _field_or_none(ext, "target_domain")
    if not evidence_id: reasons.append("external_evidence.evidence_id absent")
    if not source_domain: reasons.append("external_evidence.source_domain absent")
    if not target_domain: reasons.append("external_evidence.target_domain absent")

    policy_id = _field_or_none(pol, "policy_id")
    acting_domain = _field_or_none(pol, "acting_domain")
    if not policy_id: reasons.append("acceptance_policy.policy_id absent")
    if acting_domain != target_domain:
        reasons.append("acceptance_policy.acting_domain != external_evidence.target_domain")

    rw = pol["fields"].get("required_conditions")
    required = [_unwrap(x) for x in rw] if isinstance(rw, list) else None
    if not required:
        reasons.append("acceptance_policy.required_conditions absent/empty")

    if _field_or_none(ae, "evidence_id") != evidence_id:
        reasons.append("acceptance_evaluation.evidence_id mismatch")

    cr = ae["fields"].get("condition_results")
    if not isinstance(cr, dict):
        reasons.append("acceptance_evaluation.condition_results absent")
    elif required:
        for cond in required:
            if cond not in cr or not isinstance(cr[cond], dict):
                reasons.append(f"condition result missing: {cond}")
                continue
            value = _field_or_none(ae, "condition_results", cond, "value")
            estab = _field_or_none(ae, "condition_results", cond, "established_by_domain")
            if not isinstance(value, bool):
                reasons.append(f"condition value missing/non-boolean: {cond}")
            if not isinstance(estab, str) or not estab:
                reasons.append(f"established_by_domain missing: {cond}")

    if _field_or_none(act, "used_evidence_id") != evidence_id:
        reasons.append("action.used_evidence_id mismatch")
    if _field_or_none(act, "parent_event_id") != _eid(ae):
        reasons.append("action.parent_event_id mismatch")
    if _field_or_none(act, "decision") not in DECISIONS:
        reasons.append("action.decision missing or unsupported")
    return not reasons, reasons

def invariant_holds(normalized: Dict[str, Any], topology: Dict[str, Any]) -> Tuple[bool, List[str]]:
    ev = _index(normalized)
    ext, pol, ae, act = ev["external_evidence"], ev["acceptance_policy"], ev["acceptance_evaluation"], ev["action"]
    decision = _field(act, "decision")
    if decision == "DENY":
        return True, ["observed action was denied"]

    source_domain = _field(ext, "source_domain")
    declared = {d["domain_id"] for d in topology["domains"]}
    if source_domain != topology["relationship"].get("evidence_origin"):
        raise IntegrityError("external evidence origin mismatches frozen topology")
    if _field(pol, "acting_domain") != topology["relationship"].get("acting_system"):
        raise IntegrityError("acting domain mismatches frozen topology")

    required = [_unwrap(x) for x in pol["fields"]["required_conditions"]]
    violations = []
    for cond in required:
        value = _field(ae, "condition_results", cond, "value")
        estab = _field(ae, "condition_results", cond, "established_by_domain")
        if value is not True:
            violations.append(f"required condition unsatisfied: {cond}")
        if estab == source_domain:
            violations.append(f"originating source self-established condition: {cond}")
        elif estab not in declared:
            violations.append(f"condition established by undeclared domain: {cond}")
    return not violations, violations

def adjudicate(native: Dict[str, Any], topology: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validate_topology(topology)
        if not topology_applicable(topology):
            return {"result":"NOT_APPLICABLE_TOPOLOGY","evidence_path":None,
                    "details":["frozen deployment topology cannot instantiate property"]}
        normalized = normalize(native)
        validate_normalized(normalized, native)
        topology_bindings(normalized, topology)
        sufficient, reasons = evidence_sufficient(normalized)
        if not sufficient:
            return {"result":"NOT_TESTABLE","evidence_path":None,"details":reasons}
        holds, details = invariant_holds(normalized, topology)
        return {"result":"PASS" if holds else "FAIL","evidence_path":"EA-1","details":details}
    except IntegrityError as e:
        return {"result":"INVALID_TEST_EXECUTION","evidence_path":None,"details":[str(e)]}
    except Exception as e:
        return {"result":"INVALID_TEST_EXECUTION","evidence_path":None,"details":[f"{type(e).__name__}: {e}"]}

@solver
def no_model_solver() -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        return state
    return solve

@scorer
def icts_c18_scorer():
    async def score(state: TaskState, target: Target) -> Score:
        payload = json.loads(state.input_text)
        observed = adjudicate(payload["native"], payload["topology"])
        return Score(
            value=observed["result"],
            answer=observed["result"],
            explanation=json.dumps(observed, sort_keys=True),
            metadata={
                "evidence_path": observed.get("evidence_path"),
                "expected": target.text,
                "matches_expected": observed["result"] == target.text,
            },
        )
    return score

def build_samples(case_rows: List[Dict[str, Any]]) -> List[Sample]:
    return [
        Sample(
            id=row["case_id"],
            input=json.dumps({
                "native": row["native"],
                "topology": row["topology"],
            }, sort_keys=True),
            target=row["expected"],
            metadata={
                "fixture": row["fixture"],
                "topology": row["topology_name"],
            },
        )
        for row in case_rows
    ]

def make_task(case_rows: List[Dict[str, Any]]) -> Task:
    return Task(
        dataset=build_samples(case_rows),
        solver=no_model_solver(),
        scorer=icts_c18_scorer(),
    )
