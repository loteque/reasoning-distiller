# Greenfield First Invocation Trial

Status: **EXECUTION SPECIFICATION — awaiting observed run**

## Motivation

The Greenfield Consumer Trial proved that an accepted release can be retrieved, installed, and deterministically bootstrap the minimum project-owned state. The next boundary is whether that initialized project can perform its first production invocation without hidden scaffolding or generic-repository fallback.

This trial asks:

> Can a freshly initialized consumer add explicit evidence, construct a valid invocation request from documented contracts, prepare an activation bundle, preserve raw candidate bytes, and persist a valid immutable RGP submission using only the installed accepted release?

This trial tests production invocation mechanics, not model quality or provider transport. The model/provider boundary is represented by a fixed raw candidate fixture whose provenance is restricted to the explicit evidence source. A later live-model trial may test provider activation separately.

## Selected release

- release: `0.3.0`
- tag: `v0.3.0`
- source commit: `146f828efd258c5d964414f0118a64f2f77ed300`
- content identity: `sha256:f5effb355ad8021e07b1053a125b44f13114579601496ed6014fc600f8e32db8`
- transport SHA-256: `2cac56f03b692b5443813c61be7ca37c0ea6ee1fd2649ac0b93f9ffe919cca0e`

## Initial state

The measured repository starts with only `README.md` and `.gitignore`, then follows the accepted-release install and `rd-bootstrap` path before the invocation portion begins.

The initialized project must contain only the bootstrap-defined project state:

```text
project-knowledge/
├── project.json
├── evidence/
├── invocations/
└── submissions/
```

No PEMS, COVE, canonical state, Steward authority, or admission state may be pre-created.

## Measured procedure

1. Retrieve and verify the exact accepted `v0.3.0` release read-only.
2. Install it into `.reasoning-distiller/` using the released deterministic installer.
3. Run installed `runtime/rd_bootstrap.py` and verify `PASS`.
4. Add one explicit project-owned evidence file under `project-knowledge/evidence/`.
5. Compute its SHA-256 and construct a `reasoning-distiller-invocation/1` request using only bootstrap-defined paths and the public production invocation contract.
6. Run installed `rd_distill.py prepare` and persist the activation bundle outside semantic project state.
7. Verify the activation bundle contains the exact fixed evidence and source registry and does not broaden the evidence set.
8. Supply a fixed raw `rgp/1` candidate fixture representing the provider boundary.
9. Run installed `rd_distill.py finalize`.
10. Verify the exact raw candidate bytes were preserved at the configured immutable path.
11. Verify the immutable submission exists, has `status: candidate`, and validates under the installed RGP validator.
12. Replay the same finalize operation and verify idempotence.
13. Verify no canonical, PEMS, COVE, authority, reconciliation, or admission state was created or modified.
14. Preserve run evidence and emit PASS/FAIL.

## PASS criteria

PASS requires:

| Property | Required proof |
|---|---|
| accepted release | exact release identities verified |
| install | deterministic installer returns PASS |
| bootstrap | installed bootstrap returns PASS |
| explicit evidence | evidence exists only in project-owned evidence path |
| invocation construction | request conforms to `reasoning-distiller-invocation/1` |
| activation boundary | prepared bundle contains only fixed evidence/registry/context |
| installed runtime | prepare/finalize use `.reasoning-distiller/runtime/rd_distill.py` |
| raw preservation | stored raw bytes equal provider-boundary bytes exactly |
| RGP validation | candidate submission validates under installed validator |
| immutable submission | submission created once and exact replay is idempotent |
| authority boundary | no reconciliation/admission/canonical authority acquired |
| repository isolation | generic source repository is unnecessary after release retrieval |

## FAIL conditions

The trial fails if invocation construction requires undocumented project scaffolding, evidence paths cannot be derived from bootstrap/public contracts, the installed runtime reaches into framework source, raw bytes are repaired or changed, invalid provenance is accepted, existing outputs are overwritten, or canonical/authority/admission state is created by the Distiller path.

## Interpretation

A PASS closes the first-invocation mechanics boundary for a greenfield consumer. It does **not** establish that a real model/provider can be activated correctly, that model output is semantically good, or that Steward reconciliation/admission is configured. Those remain later gates.
