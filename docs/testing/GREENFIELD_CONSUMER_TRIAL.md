# Greenfield Consumer Trial — Execution Record

Status: **PASS — GFCT-001 closed by accepted release retest**

Specification: `docs/testing/CONSUMER_TRIALS.md`, Trial B.

Original finding run: `https://github.com/loteque/reasoning-distiller/actions/runs/32173742147`
Accepted-release retest: `https://github.com/loteque/reasoning-distiller/actions/runs/32194985309`
Retest head: `1ed15868cdc503a20ab7a35caf469f93c9748ac0`
Conclusion: workflow `success`; measured product disposition `PASS`.

## Motivation

This trial tests whether a new repository with no Reasoning Distiller integration knowledge can move from public installation instructions into valid project-owned Reasoning Distiller state without developer history, hidden scaffolding, or invented project conventions.

The original run was intentionally allowed to stop at the first undefined bootstrap requirement. That stop produced GFCT-001 and drove the Project Bootstrap Contract.

## Original finding

The original `v0.2.0` run began from a fresh Git repository containing only `README.md` and `.gitignore`. Public installation succeeded, but no public project-bootstrap procedure defined the minimum project-owned state needed for the first invocation.

Observed disposition:

```text
status: STOPPED_PRODUCT_FINDING
installation: PASS
bootstrap: UNDEFINED
first_blocking_finding: GFCT-001
invocation_attempted: false
```

GFCT-001:

> Public installation succeeds, but no public bootstrap procedure defines the minimum project-owned state required to construct the first `rd-distill` invocation.

## Remediation

The remediation consists of:

- `docs/operations/PROJECT_BOOTSTRAP_CONTRACT.md`;
- `runtime/rd_bootstrap.py`;
- `reasoning-distiller-project/1`;
- `reasoning-distiller-project-bootstrap/1`;
- `reasoning-distiller-project-bootstrap-result/1`;
- `tests/test_project_bootstrap.py`;
- `.github/workflows/project-bootstrap.yml`.

Project Bootstrap conformance run `32184602312` passed before release acceptance.

The accepted `v0.3.0` release is pinned to source commit `146f828efd258c5d964414f0118a64f2f77ed300` with:

| Property | Value |
|---|---|
| Release | `0.3.0` |
| Tag | `v0.3.0` |
| Content identity | `sha256:f5effb355ad8021e07b1053a125b44f13114579601496ed6014fc600f8e32db8` |
| Transport SHA-256 | `2cac56f03b692b5443813c61be7ca37c0ea6ee1fd2649ac0b93f9ffe919cca0e` |

Release-acceptance run `32194616352` passed and verified that the package contains both `runtime/rd_distill.py` and `runtime/rd_bootstrap.py`.

## Accepted-release retest

Run `32194985309` created a fresh repository with only `README.md` and `.gitignore`, retrieved `v0.3.0` read-only, verified the release digest, and installed it into `.reasoning-distiller/` using only release installer assets.

The measured run then invoked only:

```text
.reasoning-distiller/runtime/rd_bootstrap.py
```

The first bootstrap returned:

```text
status: PASS
outcome: CREATED
project_contract: reasoning-distiller-project/1
```

and created exactly the intended minimum project-owned structure:

```text
project-knowledge/
├── project.json
├── evidence/
├── invocations/
└── submissions/
```

A second bootstrap returned `PASS / ALREADY_BOOTSTRAPPED`, proving idempotence.

The run also verified that bootstrap created no PEMS, COVE, canonical state, admission state, or authority state and left no installer transaction residue.

Measured retest disposition:

```text
status: PASS
installation: PASS
bootstrap: PASS
bootstrap_idempotence: PASS
authority_boundary: PASS
GFCT-001: CLOSED_BY_ACCEPTED_RELEASE_RETEST
invocation_attempted: false
next_boundary: explicit evidence and first invocation construction
```

## Disposition

GFCT-001 is **closed**.

The Greenfield Consumer Trial has now proven the production path through project initialization:

```text
empty repository
  → accepted release retrieval
  → deterministic install
  → installed-only project bootstrap
  → idempotent project-owned initialization
```

This PASS does not yet prove first invocation construction or candidate submission. Those are intentionally the next measured boundary rather than being silently folded into bootstrap.

## Next boundary

The next greenfield gate is:

```text
initialized project
  → explicit evidence
  → documented invocation construction
  → rd-distill
  → raw candidate preservation
  → immutable candidate submission
```

If invocation construction requires undocumented project knowledge or ad hoc scaffolding, that must be recorded as a new product finding rather than treated as part of GFCT-001.

## Future orchestration boundary

`rd-bootstrap` remains a bounded initialization primitive. The intended future public orchestration interface is `rd_init`, which may inspect project state and coordinate install/bootstrap/evidence/distillation/Steward/admission/storage operations without inheriting the authorities of those operations.
