# Context Packaging P5 Pure Pack Builder Implementation Note

Status: **P5 implementation note, non-canonical and non-admission**

This note records the bounded implementation basis for the P5 pure deterministic context-pack builder. It does not authorize persistence, rendering, production integration, reconciliation, admission, authority mutation, activation creation, or canonical-state mutation.

## Governing basis

- Coordination control ref: `main`
- Coordination revision inspected before implementation: `40241e24ecca2dacf0848ee28cf1ddc1410d15f1`
- Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- Immediate semantic predecessor: P4 candidate `c5e265aa2c572b6156c987bfa75e3740c097f2ec`
- P4 parent: `197956138e6181ed9f9aae1d6a40b9f5084695a8`
- Frozen P1c bytes/digests/toolchain contract:
  `docs/design/CONTEXT_PACKAGING_BYTES_DIGESTS_TOOLCHAIN_CONTRACT.md`
- Frozen P1b context-pack schema blob:
  `4b240a5698294ce1a217ad758b4031830740fc29`

The coordination branch and semantic candidate chain are intentionally distinct. P5 extends the exact P4 semantic candidate rather than rebasing reviewed P1-P4 semantics onto coordination-only commits.

## P5 builder contract

The implementation exposes:

```text
reasoning-distiller-context-pack-builder/1
```

through `context_packaging.pack_builder.PACK_BUILDER_CONTRACT`.

`build_context_pack` consumes only:

1. exact raw profile bytes plus the corresponding validated profile object;
2. exact raw request bytes plus the corresponding validated request object;
3. P2 `ResolvedSource` values;
4. P3 `ProjectedKnowledge` values and their deterministic causes;
5. the already-frozen P4 COVE behavior when `cove/1` output is requested; and
6. explicit behavior-defining toolchain component identities supplied by the caller.

The builder does not discover sources, choose a profile, decide governed eligibility, validate canonical admission, or inspect ambient session/model state.

## Canonical output

Successful P5 build materializes the frozen P1b `reasoning-distiller-context-pack/1` shape with:

- canonical `source_registry`;
- separated `control_plane`;
- separated `knowledge_plane`;
- separated `operational_evidence_plane`;
- outer `inclusion_ledger`;
- exact `toolchain.components`;
- the P1c non-circular `identity` structure;
- RFC 8785 `jcs/1` final serialized bytes; and
- a separate `reasoning-distiller-context-pack-receipt/1` build receipt.

Opaque control and operational-evidence source bytes are Base64 encoded without text decoding or newline normalization. Their `raw_sha256` values cover the original bytes.

Knowledge remains the exact P3 PEMS/2 projection. When COVE output is requested, P5 delegates encoding to the P4 adapter and carries the resulting canonical COVE bytes without redefining its semantics.

## Selection provenance

The outer ledger preserves deterministic causes independently of PEMS semantic provenance:

- control and operational-evidence source inclusion records the exact profile slot ID;
- every knowledge snapshot records the explicit request-selected immutable snapshot ID;
- each selected PEMS semantic item records all P3 `request_selector` and `pems_closure` causes;
- multiple causes are preserved and canonically ordered;
- missing semantic-item provenance fails closed rather than emitting an uncaused packed item.

P5 does not deduplicate across planes by textual similarity.

## Plane and identity failure posture

P5 fails closed when:

- a P2 source does not match the exact reference supplied to P5;
- resolved bytes no longer match their frozen source digest;
- one logical source is classified into more than one plane;
- a requested canonical snapshot has no one-to-one P3 projection;
- P3 provenance names an absent semantic item or leaves a selected semantic item without a deterministic cause;
- required toolchain roles are missing, duplicated, or inconsistent with the frozen closure/JCS/builder contracts;
- P4 COVE encoding cannot preserve the supported tuple;
- canonical pack item or byte limits are exceeded; or
- a repeated canonicalization/identity pass does not reproduce byte-identical output.

No new P1b failure code is introduced.

## Digest construction

P5 implements the exact P1c domains and framing:

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

The manifest is formed before top-level `identity` insertion and excludes only the payload bodies frozen by P1c. The payload-set digest covers the exact carried payloads. The final pack identity hashes a separately typed identity-preimage object that contains no `pack_identity_sha256`.

The final serialized-pack digest is a raw SHA-256 over the complete canonical pack bytes and appears only in the out-of-band build receipt.

## Toolchain boundary

The pure builder does not fetch or mutate toolchain artifacts. The caller supplies immutable component identities and exact raw digests. P5 validates:

- exact required role coverage;
- no duplicate role;
- PEMS closure component cross-binding to the profile;
- `jcs_serializer.contract == "jcs/1"`; and
- `pack_builder.contract == "reasoning-distiller-context-pack-builder/1"`.

COVE requires an explicit `cove_adapter` component only when COVE behavior participates in the pack.

This keeps filesystem/source acquisition outside the semantic builder while still making replay behavior visible in the pack identity.

## Explicit exclusions

P5 introduces no:

- persistence adapter or filesystem write;
- cache behavior;
- renderer;
- `rd-distill` integration;
- source discovery;
- model relevance or ranking;
- profile-governance decision;
- canonical PEMS/COVE mutation;
- reconciliation or admission;
- role registration;
- authority or authorization mutation; or
- activation creation.

P6 persistence and later gates remain separate work units.

## Known unrelated reds

P5 neither repairs nor erases the previously identified non-P4-local reds:

- inherited P1b PS-19 classifier mismatch;
- runtime-isolation/schema issue; and
- extraction-parity Distiller-directive issue.

Candidate-bound P5 evidence must keep those observations separate from the P5-local disposition.
