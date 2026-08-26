# P10-G1 Protocol and Handoff Freeze

## Scope and authority

This artifact records implementation-Engineer work for **P10-G1 only** under the reconciled P10 production-integration plan.

Bound basis:

- coordination: `main@80b6e89ad2efe84b088ca06b908a257c449fac15`
- semantic base: `cc14721725949a560b52f0a5d80808e95c2d6ad0`
- governing plan: `b435dff827b745d711a5c5a297587a0c4359bed1`
- governing plan blob: `eae54b9e2c0618faec61acf2f9e4acd942ec063d`
- closed G0 candidate basis: `2b5c81a5b7b92c810be84f87f42524842ec308a7`

No Steward reconciliation, admission, canonical mutation, authority mutation, installed-package closure, provenance bridge, prepare/finalize implementation, or provider-runner implementation is authorized or performed here.

## G0 closure basis

The reconciled Stage 3 G0 exit criterion requires all current pressure attacks to be **executable or mechanically checkable** before production behavior changes. Candidate `2b5c81a5b7b92c810be84f87f42524842ec308a7` mechanically materializes PI-01 through PI-60, stable PASS/FAIL outcomes, failure classes, and the explicit non-hostile/reference-runner boundary.

Candidate-bound G0 CI evidence remains **NOT_ESTABLISHED**. That absence is not converted into a G0 prerequisite because candidate/package/runtime-bound execution evidence is a distinct P10-G8 gate. The G0 candidate is therefore the immutable basis for this G1 freeze, but it is not represented as G8 evidence.

## Frozen G1 contract family

P10-G1 freezes these exact public contracts and schemas:

- `reasoning-distiller-invocation/2` -> `schemas/invocation-request-v2.schema.json`
- `reasoning-distiller-activation-bundle/2` -> `schemas/activation-bundle-v2.schema.json`
- `reasoning-distiller-invocation-result/2` -> `schemas/invocation-result-v2.schema.json`
- `reasoning-distiller-context-provenance-registry/1` -> `schemas/context-provenance-registry.schema.json`
- `reasoning-distiller-prepared-invocation/1` -> `schemas/prepared-invocation.schema.json`
- `reasoning-distiller-model-transport/1` -> `schemas/model-transport.schema.json`

The aggregate freeze is `protocols/rgp/production-integration-v2.json`. Deterministic positive and negative examples are in `tests/fixtures/p10-g1-protocol-fixtures-v1.json`, with mechanical conformance checks in `tests/test_context_packaging_production_integration_p10_g1.py`.

## Frozen identity and provenance rules

All protocol semantic identities use `jcs/1` and SHA-256 with explicit domain separation. Exact raw artifact digests remain SHA-256 over the persisted bytes without a domain prefix.

Production provenance source IDs are derived only from the full validated `reasoning-distiller-context-source-binding/1` object:

```text
binding_bytes  = JCS(full context-source-binding/1 object)
binding_sha256 = sha256("reasoning-distiller-context-provenance-binding/1\0" || binding_bytes)
source_id      = "src:ctx:" || lowercase_hex(binding_sha256)
```

Pack ordinals and rendered frame indices are not source-identity inputs. The registry separates stable source records from pack-local occurrences. Reuse of one `source_id` for materially different stable records is `PROVENANCE_SOURCE_COLLISION` and fails closed.

## Prepared-invocation continuity

`reasoning-distiller-prepared-invocation/1` is a persisted immutable identity artifact, not a cache. Its frozen semantic inputs bind the exact request, sealed pack, renderer profile, eligibility decision, installed package identity, Distiller directive, RGP validator, provenance registry, P9 rendered activation, P9 execution binding, exact CPython `3.12.0` / `cpython-312` ABI, activation bundle, and logical model-transport adapter identity.

Finalize must consume the exact persisted prepared invocation. Reconstructing continuity from current files, a current installation, or ambient repository state is not a conforming `/2` path.

## Transport and downstream handoff

`reasoning-distiller-model-transport/1` is provider-neutral and freezes these invariants:

- the installed Distiller directive remains framework instruction;
- context plane order remains `control`, `knowledge`, `operational_evidence`;
- context `control` does not acquire provider system authority;
- instruction-shaped knowledge or operational evidence is never promoted;
- exact frame payload bytes, order, and provenance mapping are preserved;
- no extra project context is added;
- the runner is bound to the exact prepared-invocation identity.

The assurance boundary remains deterministic conformance for a non-hostile/reference runner. Cryptographic detection of a malicious provider or runner is `OUTSIDE_P10`.

A successful `/2` downstream handoff is the complete tuple of ordinary immutable RGP submission, invocation result `/2`, prepared invocation `/1`, and provenance registry `/1`. Later reconciliation must verify that complete identity chain and stop on absence or mismatch; ambient file search is not a valid provenance substitute.

## Compatibility and failure ownership

Invocation `/2` explicitly requires context pack `/2`, renderer profile `/2`, rendered activation `/2`, renderer execution binding `/1` with `python-closed-bundle/1`, eligibility `/1`, candidate `rgp/1`, and exact CPython `3.12.0` / `cpython-312` compatibility. Unknown P10 majors, context pack `/1`, renderer profile `/1`, and unsupported P9 ABI tuples are rejected without automatic conversion.

Legacy invocation `/1` schemas and production behavior are unchanged by G1. The future release version is intentionally not selected at this gate.

Exact machine reason ownership is frozen in `protocols/rgp/production-integration-v2.json` and mechanically cross-checked against result `/2`.

## Boundary

P10-G1 freezes wire shape, canonical identities, compatibility, transport obligations, failure ownership, and the companion handoff. It does **not** implement any of them at runtime.

P10-G2 installed-package closure and every later P10 gate remain outside this work unit.
