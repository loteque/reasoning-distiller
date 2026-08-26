# Deterministic Context Packaging Bytes, Digests, and Toolchain Contract

Status: **Normative P1c bytes/digests/toolchain freeze**

Contract:

- `reasoning-distiller-context-pack-bytes-digests-toolchain/1`

Governing plan:

- commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- artifact: `docs/proposals/context-packaging/FINAL_PLAN.md`
- blob: `8474d2da42f863f0a190fd80292085176d3f97f0`

P1b basis:

- reviewed candidate commit: `cffc2c27da64f052380a1a5a26a42bb7621b0335`
- review disposition supplied to this activation: `P1B_REVIEW_PASS`

Implementation gate: **P1c Bytes / Digests / Toolchain only**.

This contract freezes the byte representation, canonical serialization boundary, named digest domains and exact preimages, whole-pack receipt rule, builder-owned canonical ordering, and behavior-defining toolchain identity required by P1c. It is intentionally layered on the reviewed P1b schemas without editing or reinterpreting their wire fields.

It does **not** implement a resolver, PEMS closure, governed profile eligibility, projection, COVE behavior, persistence, rendering, production `rd-distill` integration, canonical mutation, reconciliation, admission, or role/authority state. P1d and later gates retain their own authority and scope.

## 1. P1b schema freeze boundary

P1c is bound to the following exact P1b schema blobs:

| Schema | Git blob |
|---|---|
| `schemas/context-pack-failure.schema.json` | `10195c52df81156a954eb9b5acee5a4f1b26f576` |
| `schemas/context-pack-receipt.schema.json` | `b8ef42aec266acd87c5a0b45740e7122c30114e5` |
| `schemas/context-pack-request.schema.json` | `602391284019ab680bd419c7d007e7af3cfeef53` |
| `schemas/context-pack-result.schema.json` | `7a3566b3b4db97119ea88d75c2b5622d151ba3a4` |
| `schemas/context-pack.schema.json` | `4b240a5698294ce1a217ad758b4031830740fc29` |
| `schemas/context-profile-eligibility.schema.json` | `ad8ba5839136fe7e1080d1d7e26ca351202864dc` |
| `schemas/context-profile.schema.json` | `8a363d376d20375de6c985c342437e856805a69b` |
| `schemas/context-source-binding.schema.json` | `e5d5bc005f7a3dcd4f2f788dd08d49f3b57d4a1e` |

P1c conformance MUST fail if those bytes drift while claiming this P1c contract. A later intentional schema revision requires a new reviewed basis and cannot inherit this P1c identity silently.

P1c gives executable meaning to the P1b fields already reserved for identity and receipts. It does not add hidden members to those schemas.

In particular:

- `profile.raw_sha256` and `request.raw_sha256` remain exact raw-source-byte digests;
- `identity.profile_sha256` and `identity.request_sha256` are the distinct canonical, domain-separated digests defined below;
- source-binding `raw_sha256` and `pems_sha256` fields remain exact original-byte digests under their P1a/P1b meanings;
- `identity.pack_identity_sha256` is not a hash of bytes containing itself;
- `serialized_pack_sha256` remains out-of-band in the P1b receipt.

## 2. Exact source-byte representation

Opaque control and operational-evidence payloads in a JSON/JCS pack use RFC 4648 standard Base64.

The frozen representation is:

- standard alphabet `A-Z a-z 0-9 + /`;
- required `=` padding when the final quantum is incomplete;
- no whitespace;
- no line wrapping;
- no URL-safe `-` or `_` alphabet;
- ASCII only;
- empty input encodes as the empty string.

A decoder claiming this contract MUST reject any encoding whose decoded bytes, when re-encoded under the rules above, do not reproduce the exact input string.

The digest associated with an opaque payload is SHA-256 of the **original bytes before Base64 encoding**.

No UTF-8 decoding, newline conversion, Unicode normalization, locale conversion, text-mode file handling, or host-specific character translation enters raw source identity.

Consequently these byte strings are different identities even if a text editor renders them similarly:

```text
b"line\n"
b"line\r\n"
```

A `media_type` is metadata. It does not authorize text decoding or alter raw identity.

## 3. Raw SHA-256 representation

A raw byte digest is:

```text
sha256:<64 lowercase hexadecimal digits>
```

with:

```text
raw_sha256(B) = "sha256:" || lowercase_hex(SHA256(B))
```

The hash input is exactly `B`, with no domain prefix.

This bare raw-byte hash is used where the field explicitly denotes exact source or serialized bytes, including:

- P1a/P1b `raw_sha256` source fields;
- canonical source `pems_sha256`;
- COVE payload `raw_sha256`;
- toolchain component `raw_sha256`;
- receipt `serialized_pack_sha256`.

P1b schemas accept uppercase hexadecimal for compatibility. A builder emitting a new canonical P1c pack MUST emit lowercase hexadecimal. P1c does not rewrite historical input bytes merely to normalize spelling.

## 4. Canonical JSON serialization

`jcs/1` means RFC 8785 JSON Canonicalization Scheme.

When P1c says `JCS(X)`, it means the exact UTF-8 bytes produced by RFC 8785 for the parsed JSON value `X`.

Canonical output has:

- no UTF-8 BOM;
- no trailing newline;
- no insignificant whitespace;
- RFC 8785 object-member ordering;
- RFC 8785 string escaping and Unicode handling;
- RFC 8785 number serialization.

Duplicate object member names, non-finite numbers, invalid Unicode, or any input that cannot be represented under the selected `jcs/1` contract fail before canonical identity is claimed.

JCS sorts object members. It does not reorder arrays. P1c therefore separately freezes the builder-owned array ordering below.

### 4.1 Input-document arrays

P1c MUST NOT silently reinterpret the semantic order of arrays inside profile, request, or PEMS documents.

Canonical profile and request digests use their validated parsed values as supplied. Their arrays retain their presented order unless an earlier governing contract already defines a particular collection as order-insensitive.

The P1a source-identity contract already defines canonical `standing_evidence` as a mathematical set. P1c therefore canonicalizes that set by:

1. comparing each complete evidence identity by `JCS(evidence_identity)`;
2. removing duplicate identical identities;
3. sorting surviving identities by ascending JCS bytes.

No other new set semantics are invented here.

## 5. Domain-separated digest framing

Protocol-specific canonical digests use:

- contract: `reasoning-distiller-context-digest/1`;
- hash primitive: SHA-256;
- fixed magic bytes;
- explicit domain length;
- explicit body length.

For ASCII domain `D` and body bytes `B`, the exact preimage is:

```text
UTF8("reasoning-distiller-context-digest/1") ||
0x00 ||
U16BE(len(ASCII(D))) ||
ASCII(D) ||
U64BE(len(B)) ||
B
```

`U16BE` and `U64BE` are unsigned big-endian integers of exactly 2 and 8 bytes.

The resulting digest is:

```text
domain_sha256(D, B) =
  "sha256:" || lowercase_hex(SHA256(preimage(D, B)))
```

The length framing is normative. Delimiter concatenation is not an equivalent implementation.

Frozen domains are:

```text
context-profile
context-pack-request
canonical-state-binding
selected-pems-projection
cove-payload-set
context-pack-manifest
context-pack-payload-set
context-pack-identity
```

A domain name is part of the hash preimage. The same body under two domains MUST produce two different protocol identities except for a cryptographic collision.

## 6. Canonical profile digest

The P1b request/profile identity contains a raw profile-byte digest:

```text
profile.raw_sha256 = raw_sha256(exact_profile_source_bytes)
```

The P1c pack identity additionally contains:

```text
identity.profile_sha256 =
  domain_sha256("context-profile", JCS(validated_profile_object))
```

These values have different purposes and are not interchangeable.

Formatting-only changes to the raw profile bytes may change `profile.raw_sha256` while leaving `identity.profile_sha256` unchanged if they parse to the same JCS value.

Value changes change the canonical digest.

## 7. Canonical request digest

The P1b pack request identity contains:

```text
request.raw_sha256 = raw_sha256(exact_request_source_bytes)
```

The P1c pack identity additionally contains:

```text
identity.request_sha256 =
  domain_sha256("context-pack-request", JCS(validated_request_object))
```

P1c does not silently sort request arrays before this digest. A request whose array presentation changes is a different canonical request value unless an earlier contract already defines normalization for that specific collection.

## 8. Canonical-state-binding digest

For every canonical-state binding actually represented by a knowledge-plane item, form the P1a/P1b canonical-state binding value and canonicalize its `standing_evidence` set as defined in Section 4.1.

Then:

```text
canonical_binding_sha256(binding) =
  domain_sha256(
    "canonical-state-binding",
    JCS(canonicalized_binding)
  )
```

`identity.canonical_state_binding_sha256s` contains exactly one digest for each knowledge-plane item, in the same canonical knowledge-item order defined in Section 13.

The digest covers the complete canonical-state binding, not merely the logical source key or `pems_sha256`.

A knowledge item without one exact matching canonical-state binding fails. P1c does not perform canonical-standing acceptance; it only freezes the identity of the already validated binding supplied by the P1a/P1b boundary.

## 9. Selected PEMS projection digest

P1b permits more than one explicitly addressed canonical snapshot. Therefore the singular field `selected_pems_sha256` is the identity of the complete selected PEMS projection set, not an assertion that only one knowledge item exists.

Construct:

```json
{
  "contract": "reasoning-distiller-selected-pems-projection/1",
  "items": [
    {
      "canonical_snapshot_ref": "<the exact structured object>",
      "semantic": "pems/2",
      "serializer": "jcs/1",
      "pems": "<the exact selected PEMS object>"
    }
  ]
}
```

The `items` array uses the canonical knowledge-item order in Section 13.

Then:

```text
identity.selected_pems_sha256 =
  domain_sha256(
    "selected-pems-projection",
    JCS(selected_pems_projection_object)
  )
```

P1c does not define PEMS graph closure or internal PEMS record/relation ordering. P1d/P3 own those rules. This digest binds whatever exact valid PEMS objects those later gates emit.

## 10. Optional COVE payload-set digest

If no knowledge item contains `cove_payload`, the P1b optional field `identity.cove_payload_sha256` MUST be absent.

If one or more knowledge items contain COVE payloads, construct:

```json
{
  "contract": "reasoning-distiller-cove-payload-set/1",
  "items": [
    {
      "canonical_snapshot_ref": "<the exact structured object>",
      "cove_payload": "<the complete P1b cove_payload object including Base64 data>"
    }
  ]
}
```

Items use the same canonical knowledge-item order and include only knowledge items that actually carry COVE.

Then:

```text
identity.cove_payload_sha256 =
  domain_sha256(
    "cove-payload-set",
    JCS(cove_payload_set_object)
  )
```

The inner `cove_payload.raw_sha256` remains the bare SHA-256 of decoded COVE payload bytes. The outer digest binds the deterministic multi-item set, source association, tuple metadata, Base64 representation, and raw digest together.

P4 still owns COVE encode/decode behavior and round-trip validation.

## 11. Canonical manifest digest

The canonical manifest is derived from the canonical pack **before `identity` is inserted**.

Start with the complete canonical pack value and:

1. remove the top-level `identity` member;
2. in every control-plane item, remove only `payload.data`;
3. in every knowledge-plane item, remove only `pems`;
4. when a knowledge item has `cove_payload`, remove only `cove_payload.data`;
5. in every operational-evidence item, remove only `payload.data`;
6. retain every remaining member unchanged.

The manifest therefore retains:

- pack contract;
- profile/request raw identities;
- optional eligibility metadata;
- complete source registry;
- plane structure and source references;
- payload encoding, raw digest, and media metadata;
- knowledge semantic/serializer metadata;
- COVE tuple metadata and raw digest when present;
- inclusion ledger;
- complete toolchain identity.

Then:

```text
identity.manifest_sha256 =
  domain_sha256(
    "context-pack-manifest",
    JCS(manifest_object)
  )
```

Payload bodies are intentionally outside this digest. Their exact bytes remain bound through the payload-set digest.

## 12. Payload-set digest

Construct the payload-set object:

```json
{
  "contract": "reasoning-distiller-context-pack-payload-set/1",
  "control": [
    {
      "source_ref": "<exact control source ref>",
      "payload": "<complete P1b payload object including Base64 data>"
    }
  ],
  "knowledge": [
    {
      "canonical_snapshot_ref": "<exact canonical snapshot ref>",
      "pems": "<exact selected PEMS object>",
      "cove_payload": "<complete COVE payload object when present>"
    }
  ],
  "operational_evidence": [
    {
      "source_ref": "<exact operational evidence source ref>",
      "payload": "<complete P1b payload object including Base64 data>"
    }
  ]
}
```

Arrays use the corresponding canonical plane-item order in Section 13.

Then:

```text
identity.payload_set_sha256 =
  domain_sha256(
    "context-pack-payload-set",
    JCS(payload_set_object)
  )
```

Plane metadata such as operational validation status belongs to the manifest. Exact carried bytes belong to the payload set.

A coherent builder MUST separately enforce that each payload's `raw_sha256` matches its decoded bytes and the applicable source binding. P1c does not turn an intentionally inconsistent fixture into a valid source.

## 13. Builder-owned canonical ordering

RFC 8785 does not sort arrays. To make canonical pack bytes independent of host iteration order, a P1c builder MUST emit builder-owned arrays in the following order.

Byte comparisons below are unsigned lexicographic comparisons of the referenced UTF-8 JCS byte strings.

### 13.1 Source registry

Source-class rank is:

```text
0 repository_control
1 package_control
2 canonical_state
3 operational_evidence
```

Sort by:

```text
(source_class_rank, JCS(canonicalized_complete_source_binding))
```

Canonical-state `standing_evidence` is normalized as Section 4.1 requires.

### 13.2 Plane items

Sort:

```text
control_plane.items
  by JCS(source_ref)

knowledge_plane.items
  by JCS(canonical_snapshot_ref)

operational_evidence_plane.items
  by JCS(source_ref)
```

### 13.3 Inclusion ledger

Plane rank is:

```text
0 control
1 knowledge
2 operational_evidence
```

Within each ledger entry, cause rank is:

```text
0 profile_slot
1 request_selector
2 pems_closure
```

Sort causes by:

```text
(cause_rank, UTF8(cause_id))
```

Sort ledger entries by:

```text
(plane_rank, JCS(subject))
```

P1c does not deduplicate distinct deterministic causes.

### 13.4 Toolchain components

Role rank is:

```text
0 pems_schema
1 pems_validator
2 closure_descriptor
3 cove_adapter
4 jcs_serializer
5 pack_builder
```

Sort components by:

```text
(role_rank, JCS(component))
```

Duplicate role entries are invalid under the P1c builder contract even though P1b's structural schema alone does not express uniqueness.

### 13.5 Identity arrays

`identity.canonical_state_binding_sha256s` follows `knowledge_plane.items` order exactly.

No digest array is sorted independently from the objects it identifies.

## 14. Canonical pack identity digest

After computing:

- `profile_sha256`;
- `request_sha256`;
- `canonical_state_binding_sha256s`;
- `selected_pems_sha256`;
- optional `cove_payload_sha256`;
- `manifest_sha256`;
- `payload_set_sha256`;

construct:

```json
{
  "contract": "reasoning-distiller-context-pack-identity-preimage/1",
  "profile_sha256": "...",
  "request_sha256": "...",
  "canonical_state_binding_sha256s": ["..."],
  "selected_pems_sha256": "...",
  "cove_payload_sha256": "... optional ...",
  "manifest_sha256": "...",
  "payload_set_sha256": "..."
}
```

This object contains **no** `pack_identity_sha256` field.

Then:

```text
identity.pack_identity_sha256 =
  domain_sha256(
    "context-pack-identity",
    JCS(pack_identity_preimage_object)
  )
```

Finally insert the completed P1b `identity` object into the pack.

This construction makes self-reference impossible by type and preimage definition. An implementation MUST NOT hash a partially serialized pack and substitute placeholders for the digest field.

## 15. Final serialized pack and out-of-band receipt

The canonical serialized pack bytes are:

```text
serialized_pack_bytes = JCS(complete_pack_with_identity)
```

The P1b build receipt is out of band:

```text
serialized_pack_sha256 =
  raw_sha256(serialized_pack_bytes)
```

The receipt's `pack_identity_sha256` MUST equal the pack's `identity.pack_identity_sha256`.

The receipt itself is not embedded in `serialized_pack_bytes` and is not in any pack digest preimage.

For a P1b `build` receipt:

```json
{
  "contract": "reasoning-distiller-context-pack-receipt/1",
  "request_id": "...",
  "operation": "build",
  "result": "built",
  "pack_identity_sha256": "...",
  "serialized_pack_sha256": "..."
}
```

For P1b `persist`, the same two identities are carried with the persistence result and artifact locator.

P1c freezes these receipt identity semantics only. P6 owns storage behavior, collision handling, caller-selected locations, and `written` / `no_change` execution rules.

## 16. Toolchain identity

A P1c successful pack binds the behavior-defining toolchain through the existing P1b `toolchain.components` structure.

Each component contains:

- `role`;
- `contract`;
- `immutable_identity`;
- `raw_sha256`.

`raw_sha256` is the bare SHA-256 of the exact behavior-defining artifact bytes represented by the component.

`immutable_identity` MUST select an immutable artifact state under the applicable owning contract. A mutable branch, package name without immutable content identity, path-only locator, `latest`, installed-location path, or model/runtime label is insufficient.

### 16.1 Required roles

For PEMS-only output, exactly one component is required for each role:

```text
pems_schema
pems_validator
closure_descriptor
jcs_serializer
pack_builder
```

When any knowledge item carries `cove_payload`, exactly one additional component is required:

```text
cove_adapter
```

A `cove_adapter` component is not emitted merely because COVE support exists somewhere in the installation. It is bound when COVE behavior actually participates in the pack.

### 16.2 Closure-descriptor cross-binding

The `closure_descriptor` toolchain component MUST match the profile's exact closure descriptor:

```text
component.contract
  == profile.knowledge.closure_descriptor.contract

component.immutable_identity
  == profile.knowledge.closure_descriptor.immutable_snapshot_id

component.raw_sha256
  == profile.knowledge.closure_descriptor.raw_sha256
```

This freezes the behavior identity used by later P1d/P3 work without defining closure semantics here.

### 16.3 JCS component

The `jcs_serializer` component MUST declare:

```text
contract = "jcs/1"
```

Its immutable identity and raw digest MUST bind the exact package-owned contract or implementation artifact relied on for replay.

### 16.4 Package content identities

The governing plan permits a package content identity to replace individual implementation identities only when a normative package contract guarantees that the content identity immutably binds every relevant behavior artifact.

The reviewed P1b schema nevertheless requires each component's `raw_sha256`. Under this P1c/P1b combination, a package content identity may be used as `immutable_identity` where valid, but it does not remove the required component `raw_sha256` fields.

A future schema may encode a different optimization only through an explicit reviewed version change.

### 16.5 Toolchain replay mismatch

Changing any behavior-defining component identity or raw digest changes the manifest digest and therefore the pack identity.

A replay claiming the same pack identity while using a different undeclared toolchain is invalid.

Compatibility between different toolchains, if ever allowed, requires an explicit compatibility contract/result. It is not inferred from successful execution or equal output bytes.

## 17. Renderer identity boundary

The reviewed P1b context-pack `toolchainComponent.role` enum does not contain a renderer role, and P1c does not change that schema.

This is intentional for the P1c pack boundary: no rendering has occurred.

P9 MUST bind the renderer contract/implementation in the rendering result or later reviewed artifact that actually performs rendering. P1c MUST NOT smuggle a renderer identity into a P1b toolchain field under another role name.

## 18. Failure posture

P1c is a protocol freeze, not a runtime failure-code expansion.

A conforming future implementation fails closed when it cannot establish any identity required here, including:

- non-canonical Base64;
- payload digest mismatch;
- unsupported/non-JCS JSON value;
- missing exact canonical-state binding for a knowledge item;
- duplicate required toolchain role;
- missing required toolchain role;
- COVE payload without COVE adapter identity;
- closure descriptor/toolchain mismatch;
- mutable or unverifiable toolchain identity;
- inability to reproduce a frozen digest preimage.

Where P1b already freezes a runtime failure code, that code remains controlling. P1c does not silently add a new wire code to `context-pack-failure.schema.json`.

## 19. Pressure-case bindings

This gate directly freezes behavior needed by:

### PC-05

Same request/profile, immutable sources, and behavior identities MUST reproduce identical canonical pack bytes and digests.

The fixture contains a complete deterministic pack vector with exact expected profile, request, canonical-binding, selected-PEMS, manifest, payload-set, pack-identity, and serialized-pack digests.

### PC-35

The whole-pack identity field MUST NOT occur in its own digest preimage.

This contract makes the identity preimage a separately typed object with no `pack_identity_sha256` member. The only digest over the final complete pack bytes is `serialized_pack_sha256`, stored out of band in the receipt.

### PC-36

A changed PEMS validator, closure descriptor, COVE adapter, JCS serializer, or pack-builder identity MUST be visible.

The toolchain is part of the manifest. Toolchain change therefore changes `manifest_sha256` and `pack_identity_sha256` even when payload bytes are unchanged.

## 20. Conformance artifacts

P1c conformance is materialized by:

- `tests/fixtures/context-packaging-bytes-digests-toolchain-p1c.json`
- `tests/test_context_packaging_bytes_digests_toolchain_p1c.py`

The fixture freezes:

- governing-plan identity;
- reviewed P1b basis and schema blobs;
- Base64 vectors and rejection cases;
- JCS vectors;
- byte-level digest framing vectors;
- exact raw and canonical profile/request identities;
- canonical-state-binding identity;
- complete pack identity vector;
- final serialized-pack digest;
- out-of-band build receipt.

The test suite mechanically verifies the P1b schema blobs before evaluating P1c vectors. This prevents P1c from passing by silently changing P1b schema semantics underneath itself.

## 21. P1c exit criterion

P1c is complete only when all of the following hold:

1. P1b schema blobs remain exactly the reviewed candidate bytes.
2. RFC 4648 padded standard Base64 vectors pass and non-canonical forms fail.
3. RFC 8785 canonical serialization vectors pass.
4. Domain framing reproduces exact preimage bytes and expected SHA-256 values.
5. Raw profile/request identities remain distinct from canonical profile/request identities.
6. Canonical-state-binding identity is deterministic and honors P1a standing-evidence set semantics.
7. Selected-PEMS identity supports one or multiple explicitly addressed snapshots without collapsing them.
8. Manifest and payload-set digest domains are mechanically separate.
9. Pack identity excludes itself by construction.
10. Final serialized-pack digest is computed only after pack identity is complete and is carried out of band.
11. Required toolchain roles are exact, unique, and behavior-binding.
12. Toolchain changes alter manifest and pack identity.
13. Same frozen inputs reproduce the exact fixture pack bytes and digests.
14. No resolver, closure implementation, eligibility policy, persistence, renderer, production integration, canonical mutation, reconciliation, admission, authorization, or activation mutation is introduced.

Passing P1c authorizes no later gate by itself. It only supplies the frozen byte/identity substrate required before P1d and subsequent implementation work.
