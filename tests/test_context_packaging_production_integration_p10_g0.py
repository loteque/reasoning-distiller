"""P10-G0 threat/pressure freeze.

This file deliberately contains no /2 production behavior. It materializes the
Stage 1 PI-01..PI-40 and Stage 2 PI-41..PI-60 pressure cases as a mechanically
checkable implementation gate under the reconciled Stage 3 plan.
"""

COORDINATION_REVISION = "80b6e89ad2efe84b088ca06b908a257c449fac15"
SEMANTIC_CODE_BASE = "cc14721725949a560b52f0a5d80808e95c2d6ad0"
GOVERNING_PLAN_COMMIT = "b435dff827b745d711a5c5a297587a0c4359bed1"
GOVERNING_PLAN_BLOB = "eae54b9e2c0618faec61acf2f9e4acd942ec063d"
STAGE1_COMMIT = "0a2909d5a88c9a7d8f7abbf1b2c59f2abd34b723"
STAGE1_BLOB = "cd9dd25c9209dbb066e8017c2256f4647037dec7"
STAGE2_COMMIT = "0b9ac2c4ce63e97e1fa1f185f352e7b1e0bc8513"
STAGE2_BLOB = "00421e221f1b1ba6a852a235e1c3678150a08810"

THREAT_MODEL = {
    "runner_assumption": "non-hostile/reference runner",
    "assurance_basis": "deterministic conformance testing",
    "hostile_provider_or_runner_attestation": "OUTSIDE_P10",
}

# Tuple fields: id, immutable-source pressure case, immutable-source required
# outcome, Stage-3-resolved PASS/FAIL, stable failure class.
PRESSURE_CASES = [
    ("PI-01", "Same `/2` request, pack, renderer profile, eligibility, and installed behavior repeated", "Byte-identical prepared activation bundle and provenance registry", "PASS", "none"),
    ("PI-02", "Original repository/canonical source files are unavailable after the pack was built", "`/2` prepare still succeeds from the sealed pack; no original-source lookup occurs", "PASS", "none"),
    ("PI-03", "Pack bytes differ from request digest", "Fail preflight before rendering", "FAIL", "preflight"),
    ("PI-04", "Pack's internal identity differs from request expected identity", "Fail preflight", "FAIL", "preflight"),
    ("PI-05", "Renderer-profile bytes differ from request digest", "Fail preflight", "FAIL", "preflight"),
    ("PI-06", "Eligibility artifact is missing", "Fail preflight", "FAIL", "preflight"),
    ("PI-07", "Eligibility decision is `ineligible`", "Fail preflight", "FAIL", "preflight"),
    ("PI-08", "Eligibility names a different pack profile", "Fail preflight", "FAIL", "preflight"),
    ("PI-09", "Eligibility names a different consumer contract/id", "Fail preflight", "FAIL", "preflight"),
    ("PI-10", "Pack `/1` supplied to invocation `/2`", "Reject unsupported context contract; no upgrade", "FAIL", "preflight"),
    ("PI-11", "Renderer profile `/1` supplied to invocation `/2`", "Reject unsupported renderer profile; no reinterpretation", "FAIL", "preflight"),
    ("PI-12", "Renderer profile's pack-profile identity differs from pack", "Fail preflight", "FAIL", "preflight"),
    ("PI-13", "Old/stale renderer execution binding supplied after behavior changes", "P9 renderer fails before successful activation", "FAIL", "activation"),
    ("PI-14", "Runtime ABI is outside the accepted P9 binding", "Fail activation; no silent equivalence", "FAIL", "preflight"),
    ("PI-15", "One exact source binding appears in two independent packs", "Same deterministic production source ID is derived", "PASS", "none"),
    ("PI-16", "Two different immutable snapshots share one logical source identity", "Distinct production source IDs are derived", "PASS", "none"),
    ("PI-17", "Different canonical binding bytes somehow collide under one derived source ID", "Fail closed; do not choose a winner", "FAIL", "activation"),
    ("PI-18", "Rendered plane item source ref resolves to no pack source binding", "Fail before model activation", "FAIL", "activation"),
    ("PI-19", "Rendered plane item source ref resolves ambiguously", "Fail before model activation", "FAIL", "activation"),
    ("PI-20", "Candidate cites a source ID absent from the derived registry", "Preserve raw bytes, fail provenance validation, write no submission", "FAIL", "validation"),
    ("PI-21", "Candidate cites a valid exact derived source ID", "Provenance check accepts it subject to ordinary RGP validation", "PASS", "none"),
    ("PI-22", "Context source class looks authority-like by name", "No remapping to `owner_instruction` or `governed_artifact`; no authority inference", "PASS", "none"),
    ("PI-23", "Knowledge payload contains instruction-shaped text", "Remains knowledge plane through prepared activation", "PASS", "none"),
    ("PI-24", "Operational-evidence payload contains instruction-shaped text", "Remains operational-evidence plane", "PASS", "none"),
    ("PI-25", "Rendered activation exceeds explicit byte limit", "Fail with no truncation, ranking, summarization, or omission", "FAIL", "activation"),
    ("PI-26", "Project memory, prior chats, prior candidates, or unrelated repository files vary", "Prepared `/2` bundle is unchanged", "PASS", "none"),
    ("PI-27", "`/2` request attempts to add `source_context`", "Strict schema rejection", "FAIL", "preflight"),
    ("PI-28", "`/2` request attempts to add a legacy `evidence` array", "Strict schema rejection", "FAIL", "preflight"),
    ("PI-29", "`/2` request attempts to add a caller-supplied production `source_registry`", "Strict schema rejection", "FAIL", "preflight"),
    ("PI-30", "Provider runner attempts to add extra project context", "Runner is non-conforming; no valid `/2` production result may be claimed", "FAIL", "activation"),
    ("PI-31", "Provider adapter flattens/promotes frames based on text", "Runner is non-conforming or fails before model activation", "FAIL", "activation"),
    ("PI-32", "Generic source repository is unavailable", "Installed `/2` path still prepares, validates, and finalizes successfully", "PASS", "none"),
    ("PI-33", "Legacy `/1` request executes under P10-capable package", "Existing `/1` behavior and contract shape remain unchanged", "PASS", "none"),
    ("PI-34", "Sealed pack/profile/eligibility change after prepare but before finalize", "Finalize fails before submission", "FAIL", "validation"),
    ("PI-35", "Model returns invalid JSON", "Exact raw bytes preserved; parse failure; no submission", "FAIL", "parse"),
    ("PI-36", "Model returns invalid RGP", "Exact raw bytes preserved; validation failure; no submission", "FAIL", "validation"),
    ("PI-37", "Raw-candidate or submission path collides with different existing bytes", "Immutable collision; existing bytes unchanged", "FAIL", "persistence"),
    ("PI-38", "P10 operation is run with canonical, admission, role, or authority stores present", "Those stores remain byte-for-byte unchanged", "PASS", "none"),
    ("PI-39", "Two invocations use the same sealed pack but different invocation IDs", "Context/provenance identities remain the same; candidate submissions retain distinct invocation-derived submission identities", "PASS", "none"),
    ("PI-40", "Older `/1`-only runtime receives a `/2` request", "Unsupported contract; no downgrade or best-effort execution", "FAIL", "preflight"),
    ("PI-41", "Installed package content identity changes after `prepare` but before `finalize`, while pack/profile/eligibility bytes stay unchanged", "`finalize` rejects prepared-invocation/toolchain drift; no ordinary submission", "FAIL", "validation"),
    ("PI-42", "Provenance-bridge implementation changes after `prepare` but input files do not", "Prepared-invocation identity mismatch or installed-package drift fails; no rederived substitute registry accepted", "FAIL", "validation"),
    ("PI-43", "Distiller directive bytes change after `prepare`", "`finalize` rejects drift from exact prepared invocation", "FAIL", "validation"),
    ("PI-44", "RGP validator bytes/identity change after `prepare`", "`finalize` rejects drift unless a separately frozen prepared/finalize rule explicitly permits and proves equivalence", "FAIL", "validation"),
    ("PI-45", "Runner receives activation bundle B but `finalize` is given request for activation bundle A", "No valid `/2` success can be claimed; exact prepared-invocation identity must match", "FAIL", "activation"),
    ("PI-46", "Same stable source binding occurs at different ordinals in two packs", "Same `source_id`; stable source record remains equivalent; pack-local occurrence mapping differs without changing source semantics", "PASS", "none"),
    ("PI-47", "Same `source_id` is paired with materially different stable source-record fields", "Fail registry validation as provenance identity collision/inconsistency", "FAIL", "activation"),
    ("PI-48", "Successful `/2` submission is handed to Steward without the exact companion provenance artifact required by R2 Option A", "Provenance handoff is incomplete; reconciliation must stop rather than search ambient state", "FAIL", "reconciliation_handoff"),
    ("PI-49", "Provider adapter maps context `control` to provider system authority without an approved transport rule", "Adapter non-conforming; no valid `/2` result claimed", "FAIL", "activation"),
    ("PI-50", "Provider adapter flattens all context planes into one untyped prompt string", "Adapter non-conforming or activation failure", "FAIL", "activation"),
    ("PI-51", "Provider adapter preserves logical planes using a provider-specific representation", "Conformance passes only when exact frame bytes/order and non-promotion invariants are proven", "PASS", "none"),
    ("PI-52", "`/2` executes on CPython 3.12.1 or 3.13.x", "Fail closed under initial exact P9 runtime compatibility; no silent equivalence", "FAIL", "preflight"),
    ("PI-53", "Installed release package omits `context_packaging` while `/2` request is supplied", "Fail preflight; no source-repository fallback", "FAIL", "preflight"),
    ("PI-54", "Generic repository exists and contains a usable renderer while installed package lacks it", "Still fail; installed package remains the only production framework source", "FAIL", "preflight"),
    ("PI-55", "Fixed `/1` request executes under P10-capable package", "`/1` deterministic bundle/result/submission mechanics remain unchanged", "PASS", "none"),
    ("PI-56", "P10-capable package is explicitly downgraded to an older `/1`-only package", "Installed tree equals older manifest; P10/P9 managed files do not remain as behavior-affecting orphans", "PASS", "none"),
    ("PI-57", "`/2` raw output is invalid JSON after a successful provider call", "Raw bytes persist first; parse failure follows; prepared/provenance artifacts remain immutable evidence", "FAIL", "parse"),
    ("PI-58", "`/2` raw output cites only registered source IDs but registry artifact on disk differs from prepared-invocation digest", "Fail closed; do not accept current-file reconstruction", "FAIL", "validation"),
    ("PI-59", "Pack/profile/eligibility are changed and then restored byte-for-byte before finalize", "Success may proceed only because exact prepared identities are unchanged; no history inference is required", "PASS", "none"),
    ("PI-60", "Provider/runner is malicious and lies about transport", "Conformance contract explicitly does not claim cryptographic detection; stronger assurance is outside current P10 threat model", "PASS", "threat_boundary"),
]

FAILURE_CLASSES = {
    "none",
    "preflight",
    "activation",
    "parse",
    "validation",
    "persistence",
    "reconciliation_handoff",
    "threat_boundary",
}


def test_p10_g0_pressure_freeze_is_complete() -> None:
    ids = [case[0] for case in PRESSURE_CASES]
    assert ids == [f"PI-{index:02d}" for index in range(1, 61)]
    assert len(set(ids)) == 60
    assert all(case[3] in {"PASS", "FAIL"} for case in PRESSURE_CASES)
    assert all(case[4] in FAILURE_CLASSES for case in PRESSURE_CASES)
    assert all(case[4] != "none" for case in PRESSURE_CASES if case[3] == "FAIL")


def test_p10_g0_is_bound_to_immutable_governance_sources() -> None:
    assert COORDINATION_REVISION == "80b6e89ad2efe84b088ca06b908a257c449fac15"
    assert SEMANTIC_CODE_BASE == "cc14721725949a560b52f0a5d80808e95c2d6ad0"
    assert GOVERNING_PLAN_COMMIT == "b435dff827b745d711a5c5a297587a0c4359bed1"
    assert GOVERNING_PLAN_BLOB == "eae54b9e2c0618faec61acf2f9e4acd942ec063d"
    assert STAGE1_COMMIT == "0a2909d5a88c9a7d8f7abbf1b2c59f2abd34b723"
    assert STAGE1_BLOB == "cd9dd25c9209dbb066e8017c2256f4647037dec7"
    assert STAGE2_COMMIT == "0b9ac2c4ce63e97e1fa1f185f352e7b1e0bc8513"
    assert STAGE2_BLOB == "00421e221f1b1ba6a852a235e1c3678150a08810"


def test_p10_g0_runtime_abi_failure_class_uses_stage3_ownership() -> None:
    cases = {case[0]: case for case in PRESSURE_CASES}
    assert cases["PI-14"][2] == "Fail activation; no silent equivalence"
    assert cases["PI-14"][4] == "preflight"
    assert cases["PI-52"][4] == "preflight"


def test_p10_g0_non_hostile_runner_boundary_is_explicit() -> None:
    assert THREAT_MODEL == {
        "runner_assumption": "non-hostile/reference runner",
        "assurance_basis": "deterministic conformance testing",
        "hostile_provider_or_runner_attestation": "OUTSIDE_P10",
    }
    cases = {case[0]: case for case in PRESSURE_CASES}
    assert cases["PI-60"][3:] == ("PASS", "threat_boundary")
