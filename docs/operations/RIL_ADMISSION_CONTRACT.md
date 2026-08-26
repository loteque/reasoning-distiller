# RIL Admission Contract

Status: **Normative v1 primitive contract**

Implements architecture gate **R13** from `docs/design/RIL_ARCHITECTURE_SYNTHESIS.md`.

Contracts:

- `reasoning-distiller-admission-result/1`
- `reasoning-distiller-admission-receipt/1`
- consumes `reasoning-distiller-reconciliation-disposition/1`
- consumes `reasoning-distiller-role-activation/1`
- consumes package-owned `rgp-pems2-admission-transaction/2`
- writes package-owned PEMS/2 + COVE/1 canonical state

## Purpose

Admission is the only RIL primitive in this slice allowed to mutate canonical PEMS/COVE project knowledge. It remains separate from candidate production and semantic reconciliation.

```text
immutable candidate
      ↓
immutable reconciliation disposition
      ↓ must be COMPATIBLE + RECOMMEND
authorized + activated admission Steward
      ↓
exact PEMS/2 admission transaction
      ↓
canonical PEMS/2 + deterministic COVE/1
      ↓
immutable admission receipt
```

## Preconditions

Admission MUST fail closed unless all of the following hold:

1. the disposition is a normal immutable file beneath `project-knowledge/reconciliation/dispositions/`;
2. it conforms to `reasoning-distiller-reconciliation-disposition/1`;
3. its assessment is `COMPATIBLE` with admission recommendation `RECOMMEND`;
4. the referenced candidate still exists and has the exact reconciled digest;
5. activation evidence validates for the independent `admission` scope;
6. the transaction conforms to `rgp-pems2-admission-transaction/2`;
7. the transaction `expected_base_sha256` exactly matches current normalized canonical PEMS/2;
8. reused/updated identities exist and guarded updates match exact before-state hashes;
9. new record/relation IDs do not collide;
10. resulting graph has unique identities and no dangling/self relations;
11. deterministic COVE encoding round-trips exactly to the resulting PEMS document.

No reconciliation role, recommendation, operator capability, or command invocation may substitute for valid admission activation.

## Canonical storage

R13 owns these canonical paths:

```text
project-knowledge/canonical/pems2.jcs.json
project-knowledge/canonical/cove1.jcs.json
```

When no canonical PEMS exists, admission starts from the package-defined empty PEMS/2 document:

```json
{"semantic":"pems/2","records":[],"relations":[]}
```

PEMS and COVE bytes use deterministic compact sorted-key JSON without a trailing LF, matching the established package admission serializer behavior. COVE identifies tuple `cove/1 | pems/2 | jcs/1` and MUST structurally decode to the exact admitted PEMS object.

## Evidence and receipt

Successful admission durably preserves:

```text
project-knowledge/admission/activation-evidence/<digest>.json
project-knowledge/admission/plans/<digest>.json
project-knowledge/admission/receipts/<candidate-digest>.json
```

The receipt binds candidate, reconciliation disposition, admission activation, exact transaction plan, base PEMS hash, admitted PEMS hash, admitted COVE hash, role ID, and invocation ID.

Evidence and receipts are immutable. A second admission attempt for the same candidate with different authority, plan, disposition, or resulting canonical state MUST fail with `ADMISSION_CONFLICT` or `CANONICAL_STATE_CONFLICT` rather than overwrite prior evidence.

## Update semantics

`rgp-pems2-admission-transaction/2` permits:

- exact reuse of existing record IDs;
- guarded record replacement only when the record is declared reused;
- exact `expected_before_sha256` matching;
- identity preservation (`replacement.id` unchanged);
- record-kind preservation;
- new records with collision-free IDs;
- new relations with collision-free IDs.

The plan is always evaluated against current canonical state immediately before mutation. Stale plans fail.

## Idempotence

Retrying the exact successful admission against the exact resulting canonical state returns `PASS/NO_CHANGE` only when the immutable receipt and canonical PEMS/COVE bytes agree with the originally admitted result.

## Atomicity boundary

R13 preflights disposition, candidate, activation, plan, current canonical PEMS, resulting PEMS, COVE round-trip, and target path types before canonical writes. PEMS and COVE are deterministic derived counterparts of one admission transaction. The immutable receipt is written after canonical bytes and acts as committed admission evidence.

R14 performs independent admitted-state integrity verification and is the next gate.

## Forbidden behavior

R13 MUST NOT:

- perform semantic reconciliation;
- admit a `DEFER` or `DO_NOT_RECOMMEND` disposition;
- silently authorize or activate a Steward;
- change Steward authorization;
- reinterpret RGP/PEMS/COVE contracts;
- mutate the reconciled candidate or disposition;
- overwrite an existing conflicting admission receipt.

## Conformance gate

R13 PASS requires tests proving at least:

1. independent admission authority + activation is required;
2. reconciliation recommendation is required but is not itself authority;
3. candidate identity is rechecked at admission time;
4. exact base hash guarding rejects stale plans;
5. successful admission writes deterministic canonical PEMS and COVE;
6. COVE structurally round-trips to admitted PEMS;
7. new-ID collisions fail closed;
8. guarded record updates preserve identity/kind and exact before state;
9. immutable plan/activation/receipt evidence is preserved;
10. exact retry is idempotent;
11. conflicting second admission is rejected;
12. canonical mutation occurs only through a valid admission path.

## Canonical PEMS/COVE recovery boundary amendment

This section is normative for the accepted Mode A V1 recovery design in `RIL_CANONICAL_PEMS_COVE_RECOVERY_CONTRACT.md` and narrows the phrase “only RIL primitive” above to **only ordinary admission primitive**.

1. R13 remains the sole ordinary admission primitive allowed to mutate canonical PEMS/COVE.
2. `RIL_CANONICAL_PEMS_COVE_RECOVERY_CONTRACT.md` is the sole explicit V1 exceptional mutation path for an already-invalid canonical PEMS/COVE pair.
3. The exception does not weaken any ordinary admission authority, activation, reconciliation, plan, exact-base, validation, receipt, or idempotence requirement.
4. Invalid Canon is never an R13 base. R13 MUST NOT parse-normalize, reinterpret, or repair an invalid canonical base into admissible state.
5. R13 MUST refuse any present `project-knowledge/recovery/canonical-pems-cove/active.json`, including malformed, unsafe-path, unknown-contract, or indeterminate barrier state.
6. Supported R13 canonical I/O MUST use the shared canonical-store exclusive-lock and barrier boundary frozen by the recovery contract before G1 may be considered complete.
7. After a recovery transaction is complete, the barrier is absent, and R14 V2 verifies the exact current pair as `PASS/VERIFIED_RECOVERED`, that valid pair may be used as the base of a later ordinary admission transaction.
8. A later admission over recovered state remains an independent R13 act and still requires a valid admission reconciliation disposition, independent `admission` activation, exact transaction plan, exact-base guard, and new admission receipt.
9. A canonical-recovery completion record is recovery-native provenance. It is never an admission receipt and MUST NOT be relabeled, rewritten, or accepted as one.
10. R13 admission and canonical recovery MUST NOT mutate Canon concurrently.

These recovery-boundary rules do not authorize a real recovery operation and do not authorize or resume P3.
