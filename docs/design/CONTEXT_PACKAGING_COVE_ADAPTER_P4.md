# Context Packaging P4 COVE Adapter Implementation Note

Status: **P4 implementation note, non-canonical and non-admission**

This note records the exact bounded implementation basis for the P4 COVE adapter. It does not create a new COVE semantic, authorize production integration, or mutate canonical state.

## Governing basis

- Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- Closed P3 semantic base: `197956138e6181ed9f9aae1d6a40b9f5084695a8`
- P3 Steward reconciliation evidence: `653d9aff48641e59e5e0b60eed41aa2caa0bb375`

P4 exposes exactly one supported semantic tuple:

```text
cove/1 | pems/2 | jcs/1
```

The structural COVE behavior is not redefined here. The adapter reuses the package-owned encoder/decoder frozen by the implementation evidence at:

- path: `admission/apply_admission_transaction.py`
- Git blob: `0f0117a7770f1928e41bd76082d9a572102e823a`

The adapter verifies that immutable Git-blob identity before loading the behavior. A changed source artifact therefore fails closed instead of silently changing the P4 encoding contract.

COVE bytes use the already-frozen package `jcs/1` semantics exposed by the P3 context-packaging implementation. P4 does not adopt the historical admission helper's sorted-JSON helper as a new JCS definition.

## P4 guarantees

For the supported tuple, `encode_cove_pems`:

1. accepts a PEMS/2 object without normalization or semantic rewriting;
2. invokes the exact frozen package-owned COVE structural encoder;
3. decodes the generated envelope and requires exact PEMS equality;
4. serializes the envelope as `jcs/1` bytes; and
5. encodes a second time and requires byte-identical output.

`decode_cove_pems` accepts only canonical bytes for that deterministic package encoding. It rejects unsupported tuple values, alternate envelope members, non-canonical byte spellings, and structurally different encodings of the same PEMS object. A successful decode is re-encoded and re-decoded before returning the exact PEMS value.

The P4 conformance gate directly checks the frozen source blob, exact semantic round trip, source-encoder parity, insertion-order independence, unsupported-tuple rejection, malleability rejection, and repeated-byte determinism.

## Explicit exclusions

P4 does not implement or authorize P5 pack construction, persistence, rendering, production integration, admission, reconciliation, canonical mutation, role mutation, authorization mutation, or activation creation. The inherited P1b PS-19/schema-harness debt and Extraction Parity Distiller-directive baseline observation remain separate repository-wide follow-up concerns and are neither fixed nor erased by this work.
