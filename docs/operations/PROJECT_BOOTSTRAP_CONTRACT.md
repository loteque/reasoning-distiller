# Project Bootstrap Contract

Status: **Normative v1 operational contract**

Contracts:

- `reasoning-distiller-project-bootstrap/1`
- `reasoning-distiller-project-bootstrap-result/1`
- `reasoning-distiller-project/1`

## Purpose

Bootstrap deterministically creates the minimum **project-owned** structure needed to begin using an installed Reasoning Distiller. It resolves Greenfield Consumer Trial finding GFCT-001 without inventing project knowledge, governance, or authority.

The reference primitive is `runtime/rd_bootstrap.py`. Its logical operation is `rd-bootstrap`.

`rd-bootstrap` is intentionally a primitive. The intended future public orchestration command is **`rd_init`**, which will inspect environment/state and coordinate the complete lifecycle while preserving the authority boundaries of the operations it invokes.

```text
rd_init (future orchestrator)
  ├─ inspect environment/state
  ├─ install/update when explicitly permitted
  ├─ rd-bootstrap
  ├─ evidence readiness
  ├─ invocation preparation
  ├─ rd-distill
  ├─ Steward handoff/reconciliation
  ├─ authorized PEMS/COVE admission
  └─ backend verification/storage
```

Coordination does not confer authority. `rd_init` MUST NOT inherit Distiller, Steward, reconciliation, or admission authority.

## Bootstrap operation

Normal reference invocation:

```bash
python .reasoning-distiller/runtime/rd_bootstrap.py --target /path/to/project
```

The target MUST already contain an installed `.reasoning-distiller/` directory. Bootstrap does not install or modify the generic framework.

## Created project state

For an uninitialized project, bootstrap creates exactly this minimum structure:

```text
project-knowledge/
├── project.json
├── evidence/
├── invocations/
└── submissions/
```

`project.json` is canonical JSON with this semantic content:

```json
{
  "contract": "reasoning-distiller-project/1",
  "paths": {
    "evidence": "project-knowledge/evidence",
    "invocations": "project-knowledge/invocations",
    "submissions": "project-knowledge/submissions"
  }
}
```

The bootstrap contract deliberately does **not** create canonical knowledge, PEMS/COVE stores, admission state, authority directories, role assignments, source facts, evidence, or a Steward identity. Those require separate project decisions/contracts.

## Ownership

`.reasoning-distiller/` is package-managed generic framework state.

`project-knowledge/` is project-owned state. `rd-bootstrap` has narrow authority to create only the v1 bootstrap paths above when they are absent and safe to create.

Directory creation is not authority creation.

## Determinism

For the same target state and arguments, bootstrap MUST produce the same semantic project configuration or the same failure classification.

Bootstrap MUST NOT:

- use network access;
- inspect arbitrary project source to infer configuration;
- select roles or grant authority;
- generate project facts or evidence;
- create canonical/admitted knowledge;
- modify `.reasoning-distiller/`;
- overwrite conflicting files;
- migrate unknown project layouts;
- use timestamps as semantic configuration.

## Existing state

Behavior is fail-closed:

| State | Result |
|---|---|
| no bootstrap paths exist | create exact v1 structure; `PASS` / `CREATED` |
| exact v1 structure/config already exists | no mutation; `PASS` / `ALREADY_BOOTSTRAPPED` |
| partial compatible structure with no conflicting content | create only missing v1 paths; `PASS` / `COMPLETED` |
| `project.json` exists with different bytes/semantics | `FAIL` / `PROJECT_CONFIG_CONFLICT` |
| required path exists as wrong node type | `FAIL` / `PATH_CONFLICT` |
| `.reasoning-distiller/` missing | `FAIL` / `INSTALLATION_MISSING` |
| unsafe/unresolvable target | `FAIL` / `TARGET_INVALID` |

Unknown state is never rearranged or repaired automatically.

## Result

Success example:

```json
{
  "contract": "reasoning-distiller-project-bootstrap-result/1",
  "status": "PASS",
  "outcome": "CREATED",
  "project_contract": "reasoning-distiller-project/1",
  "created": [
    "project-knowledge/evidence",
    "project-knowledge/invocations",
    "project-knowledge/project.json",
    "project-knowledge/submissions"
  ]
}
```

Failure example:

```json
{
  "contract": "reasoning-distiller-project-bootstrap-result/1",
  "status": "FAIL",
  "reason_code": "PROJECT_CONFIG_CONFLICT",
  "detail": "project-knowledge/project.json already exists with different content"
}
```

The CLI exits `0` for PASS, `2` for expected contract/preflight/conflict failures, and `1` for unexpected internal failures.

## Security and filesystem rules

All created paths MUST resolve beneath the target root. Bootstrap MUST reject symlink/path escapes affecting managed bootstrap paths. Existing conflicting nodes MUST remain untouched on failure.

Bootstrap SHOULD preflight all conflicts before writing so expected failures are mutation-free.

## Relationship to first invocation

After bootstrap, a project has stable locations for evidence, invocation artifacts, and immutable candidate submissions. Bootstrap does not fabricate an invocation request or evidence. Those remain explicit inputs to the production invocation contract.

The Greenfield Consumer Trial should next test:

```text
empty repo
  → install accepted release containing rd_bootstrap.py
  → rd-bootstrap
  → add explicit evidence
  → construct invocation request from documented paths
  → rd-distill
  → immutable candidate submission
```

If request construction remains an undocumented usability gap, record a new product finding rather than expanding bootstrap ad hoc.

## Future `rd_init`

`rd_init` should eventually be an idempotent state-machine orchestrator. A likely lifecycle is:

```text
UNINSTALLED → INSTALLED → INITIALIZED → EVIDENCE_READY
→ CANDIDATE_READY → RECONCILED → ADMITTED → READY
```

It may emit operational provenance such as `rd_initialized`, but such events are not canonical project knowledge.

`rd_init` must determine what operation is needed from observable state and then invoke the appropriate bounded primitive/authority. It must never collapse those authority boundaries into itself.
