# RIL R14 PEMS/COVE Storage Verification Contract

Status: **Normative primitive contract**

Contract: `reasoning-distiller-storage-verification/1`

Governing design: [`../design/RD_INIT_DESIGN_CONTRACT.md`](../design/RD_INIT_DESIGN_CONTRACT.md) and [`../design/RIL_ARCHITECTURE_SYNTHESIS.md`](../design/RIL_ARCHITECTURE_SYNTHESIS.md).

## Purpose

R14 verifies that the current admitted canonical PEMS/COVE pair is internally consistent, conforms to the package-owned PEMS/2 contract, is encoded deterministically under the package COVE/1 representation, and is backed by immutable admission evidence.

Verification is **read-only**. It grants no authority, performs no reconciliation or admission, repairs no state, and never rewrites canonical storage.

## Authoritative locations

For a project root, R14 inspects:

```text
project-knowledge/canonical/pems2.jcs.json
project-knowledge/canonical/cove1.jcs.json
project-knowledge/admission/receipts/*.json
```

Both canonical files MUST exist together. A missing pair is `NO_ADMITTED_STATE`; a one-sided pair is `INCOMPLETE_CANONICAL_PAIR`.

Canonical paths, files, receipt directories, and matching receipts MUST be ordinary non-symlink filesystem objects.

## Verification invariants

A PASS requires all of the following:

1. canonical PEMS parses as JSON and uses `semantic: pems/2`;
2. PEMS bytes are the deterministic bytes produced by the package admission serializer after normalization;
3. PEMS validates against the package-owned `backends/pems-cove/pems-v2.schema.json`;
4. package PEMS semantic/integrity validation succeeds, including project identity, provenance references, relation endpoints, derived-premise requirements, and canonical contradiction ordering;
5. canonical COVE parses as JSON and is byte-canonical;
6. COVE is exactly the deterministic package encoding of the canonical PEMS document using the tuple `cove/1 | pems/2 | jcs/1`;
7. decoding COVE reproduces the canonical PEMS document exactly;
8. at least one immutable `reasoning-distiller-admission-receipt/1` records the exact SHA-256 hashes of the current canonical PEMS and COVE bytes.

R14 does not reinterpret, fork, weaken, or replace PEMS/COVE validation rules. It consumes package-owned validators and serializers.

## Result contract

Results use:

```text
reasoning-distiller-storage-verification-result/1
```

Success:

```json
{
  "contract": "reasoning-distiller-storage-verification-result/1",
  "status": "PASS",
  "outcome": "VERIFIED"
}
```

The success result also reports deterministic PEMS/COVE SHA-256 values, matched receipt paths, and the package PEMS integrity proof.

Failure is fail-closed and identifies a machine-readable outcome such as:

```text
NO_ADMITTED_STATE
INCOMPLETE_CANONICAL_PAIR
CANONICAL_PATH_CONFLICT
INVALID_PEMS_JSON
NONCANONICAL_PEMS_BYTES
PEMS_SCHEMA_INVALID
PEMS_INTEGRITY_INVALID
INVALID_COVE_JSON
NONCANONICAL_COVE_BYTES
COVE_MISMATCH
COVE_ROUNDTRIP_FAILED
ADMISSION_RECEIPT_MISSING
ADMISSION_RECEIPT_INVALID
ADMISSION_RECEIPT_MISMATCH
```

## No mutation

The verifier MUST NOT create directories, repair projections, rewrite canonical files, rewrite receipts, append history, or otherwise modify project state. Repeated verification of unchanged state MUST return the same result.

## Gate

R14 is accepted only when conformance tests prove positive verification, schema/integrity enforcement, canonical byte enforcement, COVE exactness/round-trip, receipt binding, unsafe-path rejection, deterministic retry, and byte-for-byte read-only behavior.

## R14 V2 recovered-provenance amendment

This section is normative for the Mode A V1 canonical-recovery design governed by `RIL_CANONICAL_PEMS_COVE_RECOVERY_CONTRACT.md`. It versions the **result semantics** to `reasoning-distiller-storage-verification-result/2`; it does not weaken or fork any package PEMS/COVE content-validation rule.

### Purpose and authoritative provenance

R14 V2 verifies the current canonical PEMS/COVE pair independent of how that valid pair obtained standing. The current pair must satisfy one of exactly two positive provenance classes:

- `VERIFIED_ADMITTED`, backed by an exact immutable ordinary `reasoning-distiller-admission-receipt/1` matching the current pair;
- `VERIFIED_RECOVERED`, backed by an exact immutable `reasoning-distiller-canonical-recovery-completion/1` matching the current pair and a complete recovery provenance chain.

R14 V2 therefore additionally inspects, when recovered provenance is claimed:

```text
project-knowledge/recovery/canonical-pems-cove/active.json
project-knowledge/recovery/canonical-pems-cove/generations/<generation>/
```

Any active, malformed, unsafe, unknown-contract, or indeterminate recovery barrier prevents a positive normal verification result. A recovered PASS requires the completed generation evidence to bind the exact current pair and requires the barrier state permitted by the recovery contract for that verification phase.

A recovery completion record is never an admission receipt. Existing admission receipts remain immutable historical claims and are not rewritten, relabeled, or upgraded by recovery.

### Shared content invariants

Both positive provenance classes require the same current-state checks:

1. canonical PEMS parses as strict JSON and uses `semantic: pems/2`;
2. PEMS bytes equal exact package normalization/serialization bytes;
3. PEMS validates against the exact package-owned current PEMS/2 schema;
4. package PEMS semantic/integrity validation succeeds, including project identity, provenance references, relation endpoints, derived-premise requirements, and contradiction ordering;
5. canonical COVE parses as JSON and is byte-canonical;
6. COVE is exactly the deterministic package encoding of current PEMS using `cove/1 | pems/2 | jcs/1`;
7. COVE decoding reproduces current PEMS exactly;
8. the selected provenance artifact and its complete required chain bind the exact current PEMS/COVE SHA-256 values.

Content validation is package-owned and identical across provenance classes. Provenance selection MUST NOT alter normalization, schema, semantic/integrity, COVE, or round-trip acceptance.

### `reasoning-distiller-storage-verification-result/2`

A positive V2 result SHALL contain at least:

- `contract`: exactly `reasoning-distiller-storage-verification-result/2`;
- `status`: exactly `PASS`;
- `outcome`: exactly `VERIFIED_ADMITTED` or `VERIFIED_RECOVERED`;
- `provenance_class`: exactly `VERIFIED_ADMITTED` or `VERIFIED_RECOVERED`, equal to `outcome`;
- exact canonical PEMS SHA-256;
- exact canonical COVE SHA-256;
- exact provenance artifact path or paths;
- exact SHA-256 digest for every provenance artifact used to establish the positive class;
- package PEMS integrity proof/identity required by the implementation contract.

For `PASS/VERIFIED_ADMITTED`, at least one exact ordinary admission receipt must record the current pair hashes.

For `PASS/VERIFIED_RECOVERED`, one exact immutable canonical-recovery completion record must bind the current pair hashes, recovery-plan digest, root-approval digest, preserved-evidence inventory digest, equivalence-proof digest, recovery generation, and terminal provenance class `VERIFIED_RECOVERED`. The referenced recovery artifacts must validate under `RIL_CANONICAL_PEMS_COVE_RECOVERY_CONTRACT.md`.

Downstream consumers may accept `VERIFIED_RECOVERED` only where their own governing contract explicitly permits that class.

### V2 failure behavior

All existing fail-closed content outcomes remain applicable. V2 additionally fails closed when recovered provenance is claimed but the recovery chain is absent, malformed, conflicting, incomplete, unsafe, or does not bind the exact current pair. Implementations SHALL expose stable machine-readable recovery-provenance failures and MUST NOT fall back from a failed recovered-provenance proof to fabricated ordinary admission standing.

### No mutation and locking boundary

R14 V2 remains byte-for-byte read-only. Supported live canonical reads MUST use the shared canonical-store shared-lock and barrier boundary frozen by `RIL_CANONICAL_PEMS_COVE_RECOVERY_CONTRACT.md`. A read-only verifier MUST NOT create a lock file as a side effect of verification.

### V2 conformance additions

R14 V2 is not complete until conformance proves at least:

1. ordinary admitted state still returns `PASS/VERIFIED_ADMITTED` only with exact matching immutable admission evidence;
2. completed recovered state returns `PASS/VERIFIED_RECOVERED` only with exact matching immutable recovery completion evidence and complete provenance chain;
3. both positive classes execute identical PEMS/COVE content checks;
4. malformed or missing recovered provenance prevents `VERIFIED_RECOVERED`;
5. a recovery completion record is never accepted as an admission receipt;
6. active, malformed, or indeterminate recovery barriers fail closed;
7. verification remains byte-for-byte read-only;
8. exact unchanged verification is deterministic.

This amendment does not authorize canonical recovery, ordinary admission, authority mutation, or P3.
