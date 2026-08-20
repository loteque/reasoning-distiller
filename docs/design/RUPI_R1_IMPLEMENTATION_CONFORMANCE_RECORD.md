# Rupi R1 Implementation Conformance Record

Status: **CONFORMANT**

Recorded: 2026-08-20

Implementation baseline: `ebc2a6bebfc76790d4fa192c6e7e980428d05d6c`

Base branch baseline: `main@7eaa5138466854bcbb8e1e8c513fbab3467ef5c8`

This record closes the implementation gates defined by the accepted Rupi R1 design artifacts. It records evidence; it does not itself grant project authority, publish a release, authorize installation into another project, authorize canonical admission, or authorize merge of the pull request.

## 1. Accepted design baseline

Acceptance is bound by `RUPI_R1_ACCEPTANCE.md` to these exact reviewed blobs:

- `docs/design/RUPI_LIFECYCLE_AGENT_DESIGN_CONTRACT.md`
  - contract: `reasoning-distiller-rupi-lifecycle-design/1`
  - accepted blob SHA: `e39d1226f2ef4982a2b7fecce085986d1619dcba`
- `docs/design/RUPI_PRIMITIVE_CONFORMANCE_PLAN.md`
  - contract: `reasoning-distiller-rupi-conformance-plan/1`
  - accepted blob SHA: `9bfebcfaf28c0ceab24a2d6fa2b9e745118715fd`

Later edits do not inherit acceptance automatically.

## 2. Gate evidence

| Gate | Result | Verified head | RIL workflow run | Evidence |
| --- | --- | --- | --- | --- |
| R1 Primitive inventory freeze | PASS | `50cf53e01f86e3a5a5649b33b0553247e0ed4a20` | `32416361760` | every consequential Rupi action maps to exactly one governing primitive; legacy Steward setup rejected |
| R2 Installer read-only extraction | PASS | `50cf53e01f86e3a5a5649b33b0553247e0ed4a20` | `32416361760` | release verification and transition planning exposed read-only; `install()` reuses the same internals and revalidates before mutation |
| R3 Checkpoint/presentation adapter | PASS | `3d8f4e61ad0c6f0707f005d1a2bcfc20dbd8769f` | `32416763731` | presentation is non-authoritative, read-only, status-preserving, and primitive-backed |
| R4 Fresh install/bootstrap handoff | PASS | `7bd321b2a1cae2d67290907e926c3fff108764ba` | `32417447604` | install → status → conditional bootstrap → status works without collapsing primitive boundaries |
| R5 First-use authority flow | PASS | `22f3eee3f513329889d98b89a279845d1a316dfd` | `32418142746` | initial root and Steward scopes require exact independent protected ceremonies; no activation/semantic/Canon mutation |
| R6 Update/recovery | PASS | `3ed279ef2bd34c5f91ab34c3d118125a736408c4` | `32418922020` | update reuses installer; recovery is explicit and followed by re-plan; project-owned authority state preserved |
| R7 Adversarial boundaries | PASS | `118830170512d615afc9d972f188264044bc98e5` | `32419541258` | all 12 hostile/ambiguous cases fail closed or preserve the accepted boundary; zero production-code changes required |
| R8 End-to-end lifecycle | PASS | `ebc2a6bebfc76790d4fa192c6e7e980428d05d6c` | `32420025727` | all five full lifecycle scenarios pass; zero production-code changes required |

The final R8 RIL run executed **389 tests** and completed `OK`.

## 3. Final R8 scenarios

The exact implementation baseline passed all required end-to-end scenarios:

1. fresh project → exact release install → bootstrap → protected initial-root boundary;
2. explicit initial root → independently confirmed reconciliation/admission Steward scopes → semantic handoff;
3. verified framework update → project-owned authority state preserved;
4. conversation discarded → lifecycle position reconstructed from durable project state → resume from first incomplete requirement;
5. already-configured project → deterministic no-mutation setup-readiness report while preserving the normal semantic next action from `ril_status`.

Rupi does not invent a second authoritative `READY` state. Setup readiness is presentation for the requested lifecycle goal; `ril_status` remains authoritative for the broader Reasoning Distiller lifecycle.

## 4. Primitive amendments discovered during implementation

Two narrow primitive/API gaps were identified and closed without duplicating existing semantics:

- R5: exact protected Human confirmation binding was added as a distinct non-authoritative primitive because generic contextual affirmation intentionally cannot satisfy protected ceremony evidence.
- R6: installer recovery result normalization was added as a thin adapter over the existing recovery primitive so checkpoint success can use the standard `PASS/outcome` result shape without reimplementing recovery.

Their rationale is recorded in:

- `RUPI_R5_PRIMITIVE_AMENDMENT.md`
- `RUPI_R6_PRIMITIVE_AMENDMENT.md`

No new primitive was required by R7 or R8.

## 5. Final invariants proven

On the verified implementation baseline:

- Rupi is an ephemeral lifecycle adapter, not an authority-bearing role;
- Rupi owns no authoritative lifecycle state separate from accepted durable project state;
- every consequential action remains primitive-backed;
- Rupi has no alternate installer, updater, bootstrapper, authority system, recovery system, reconciliation path, admission path, or Canon mutation path;
- fresh install and update use the same deterministic installer mutation primitive;
- installer planning/verification cannot serve as stale execution permission;
- protected root and Steward authorization remain independent Human ceremonies;
- operator identity and Steward targets are never inferred;
- Steward authorization does not create activation;
- Rupi never routes current authority setup through `rd_steward_setup.py`;
- ordinary update preserves project-owned knowledge and authority state;
- invalid authoritative history stops at the exceptional recovery boundary;
- Rupi exits at the lifecycle boundary instead of continuing into reconciliation or admission;
- user-visible completion claims are backed by accepted primitive results.

## 6. Regression workflows

At the verified implementation baseline, the pull-request checks were all green:

- RIL Test Suite;
- Reasoning Distiller Package Installer;
- Reasoning Distiller Package Contract;
- Reasoning Distiller Production Invocation;
- Reasoning Distiller Runtime Isolation;
- Extraction Parity.

The documentation-only commit containing this record must also receive a green pull-request regression run before PR closeout is considered complete.

## 7. Conclusion

Rupi R1 satisfies the accepted completion criteria for gates `R1 → R8` on implementation baseline `ebc2a6bebfc76790d4fa192c6e7e980428d05d6c`.

The remaining repository workflow is administrative: verify the documentation-only closeout head, update PR metadata to describe the complete R1–R8 scope, then separately authorize any transition from draft/review state and any merge into `main`.
