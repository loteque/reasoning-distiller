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
