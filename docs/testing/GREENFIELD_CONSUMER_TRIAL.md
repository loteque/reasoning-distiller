# Greenfield Consumer Trial — Execution Record

Status: **STOPPED_PRODUCT_FINDING — GFCT-001 observed; remediation implemented and awaiting accepted release retest**

Specification: `docs/testing/CONSUMER_TRIALS.md`, Trial B.

Observed run: `https://github.com/loteque/reasoning-distiller/actions/runs/32173742147`
Run head: `3d2af6a81dbddfe682d12a410105a1614786caea`
Conclusion: workflow `success`; measured product disposition `STOPPED_PRODUCT_FINDING`.

## Motivation

This trial tests whether a new repository with no Reasoning Distiller integration knowledge can move from public installation instructions to a first valid candidate submission without developer history, hidden scaffolding, or invented project conventions.

The trial is intentionally allowed to stop at the first undefined bootstrap requirement. Such a stop is a product finding, not permission to add ad hoc project structure during the measured run.

## Selected release for observed run

| Property | Value |
|---|---|
| Release | `0.2.0` |
| Tag | `v0.2.0` |
| Source commit | `c7daed110e58627d0ab2566298cc433615ee4452` |
| Content identity | `sha256:75736b1b8522f568cf172058ea97b8216501d4faaf2d4fa32ff7056181c42add` |
| Transport SHA-256 | `d5273f9181e286c592db21e636c67b8dfb3f3a3dc39608cf34e6f66557a477e1` |

## Observed execution

The measured run began from a fresh Git repository containing only `README.md` and `.gitignore`. It retrieved and verified the exact accepted `v0.2.0` release, installed it successfully into `.reasoning-distiller/`, and then attempted to proceed using only the public product documentation.

At that point the production invocation contract required project-owned evidence, a source registry, a raw-candidate path, and a submission path, but no public project-bootstrap procedure defined how to establish that initial state. The harness correctly stopped rather than inventing scaffolding.

The run recorded:

```text
status: STOPPED_PRODUCT_FINDING
installation: PASS
bootstrap: UNDEFINED
first_blocking_finding: GFCT-001
invocation_attempted: false
```

The working-tree boundary at the stop was also correct: only `.reasoning-distiller/` had been added. No `project-knowledge/`, authority state, canonical state, or transaction residue was improvised.

## Finding GFCT-001

Classification: **blocking product bootstrap gap**.

> Public installation succeeds, but no public bootstrap procedure defines the minimum project-owned state required to construct the first `rd-distill` invocation.

## Remediation

GFCT-001 now has an implemented remediation on `main`:

- normative contract: `docs/operations/PROJECT_BOOTSTRAP_CONTRACT.md`;
- reference primitive: `runtime/rd_bootstrap.py`;
- logical operation: `rd-bootstrap`;
- project contract: `reasoning-distiller-project/1`;
- bootstrap contract: `reasoning-distiller-project-bootstrap/1`;
- bootstrap result contract: `reasoning-distiller-project-bootstrap-result/1`;
- conformance suite: `tests/test_project_bootstrap.py`;
- CI workflow: `.github/workflows/project-bootstrap.yml`.

Observed Project Bootstrap conformance run `32184602312` completed successfully against implementation tip `7b9b12e7d57317111c017b4b144d83ed1d5e5736`. Durable machine-readable PASS evidence is stored in `docs/operations/PROJECT_BOOTSTRAP_STATUS.json`.

The remediation intentionally creates only the minimum project-owned structure:

```text
project-knowledge/
├── project.json
├── evidence/
├── invocations/
└── submissions/
```

It does not create project facts, canonical state, PEMS/COVE storage, Steward identity, role authority, reconciliation state, or admission authorization.

## Release/retest gate

GFCT-001 is **not closed by implementation alone**. Closure requires:

1. an accepted deterministic release containing `runtime/rd_bootstrap.py`;
2. verification that the release package contains the bootstrap primitive and existing production invocation runtime;
3. a new Greenfield Consumer Trial from a fresh empty repository using that accepted release;
4. successful documented bootstrap before first invocation;
5. continuation until either a valid immutable candidate submission is reached or a new independently identified product finding blocks progress.

The release-acceptance workflow is prepared for `v0.3.0`, source commit `146f828efd258c5d964414f0118a64f2f77ed300`, and explicitly verifies the bootstrap payload before publication.

## Future orchestration boundary

`rd-bootstrap` remains a bounded initialization primitive. The intended future public orchestration interface is `rd_init`, which may inspect project state and coordinate install/bootstrap/evidence/distillation/Steward/admission/storage operations without inheriting the authorities of those operations.
