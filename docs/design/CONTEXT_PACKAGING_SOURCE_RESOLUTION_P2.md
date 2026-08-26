# P2 Read-Only Immutable Source Resolution

Status: **candidate P2 implementation note**

Governing plan:

- commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- artifact: `docs/proposals/context-packaging/FINAL_PLAN.md`
- blob: `8474d2da42f863f0a190fd80292085176d3f97f0`

Implementation basis:

- live-main basis observed before implementation: `58b99891e116b5a06dd603810c2b98ea83e328c3`
- closed P1e semantic candidate: `e6e9d318724a2d13e3b820f8208bdb623d61e482`
- P1a source-identity contract blob: `210d67f62dd0db8bedfc4d291c9b4a64f6bd17ef`
- P1b source-binding schema blob: `e5d5bc005f7a3dcd4f2f788dd08d49f3b57d4a1e`
- P1b request schema blob: `602391284019ab680bd419c7d007e7af3cfeef53`
- P1b profile schema blob: `8a363d376d20375de6c985c342437e856805a69b`
- P1b failure schema blob: `10195c52df81156a954eb9b5acee5a4f1b26f576`

This note describes the P2 implementation. It does not amend the P1 protocol
freeze, create project authority, establish canonical standing, admit project
knowledge, or authorize production `rd-distill` integration.

## 1. Scope

P2 implements only the read-only immutable source-resolution gate.

The implementation:

1. consumes the explicit P1b request bindings and the selected governed profile;
2. validates the P1a logical/snapshot conflict rules needed at resolution time;
3. validates explicit slot, standing, knowledge-snapshot, and consistency
   references against the supplied binding set;
4. invokes a caller-supplied adapter for the exact requested source class and
   immutable binding;
5. rejects missing, mutable, unsafe, ambiguous, rebound, stale,
   digest-mismatched, conflicting, or inconsistent sources;
6. enforces `max_bindings`, `max_single_source_bytes`, and
   `max_total_source_bytes` in the source-resolution measurement domain; and
7. returns verified raw bytes plus their original complete bindings for later
   gates.

P2 performs no PEMS selector evaluation or closure, no COVE encoding, no
canonical pack construction, no persistence, no rendering, no authority
validation, no reconciliation/admission, and no production evidence discovery.

## 2. Exact-address adapter boundary

Source classes require different immutable address mechanisms. Repository
objects, package snapshots, canonical backends, and operational-evidence stores
cannot be collapsed into a generic filesystem-path heuristic without violating
P1a.

P2 therefore uses class-specific read-only adapters.

An adapter receives only:

```text
(complete_requested_binding, effective_byte_limit)
```

It does not receive a branch name, search root, ambient session state, role
label, "latest" selector, model callback, or repository enumeration result from
the resolver.

An adapter returns one `AdapterResult` status:

```text
resolved
missing
unsafe
mutable
ambiguous
limit_exceeded
```

For `resolved`, the adapter must return:

- the complete binding it actually resolved; and
- the exact raw source bytes.

The resolver passes a deep copy of the requested binding across the adapter
boundary and compares the returned binding against the untouched request.
Hexadecimal commit/digest spelling is compared case-insensitively only where
the P1 contracts already permit that normalization. Canonical
`standing_evidence` retains the P1 mathematical-set semantics. A changed
canonical repository relationship is a changed returned binding even though
that relationship is not part of the canonical snapshot fingerprint.

This prevents a mutable adapter from silently rewriting the resolver's request
object and then claiming the rewritten identity was requested.

## 3. Filesystem and backend safety

Filesystem safety is an adapter obligation because the generic P1 binding does
not define one universal local path mapping.

A filesystem-backed adapter must resolve only the exact immutable binding and
must report `unsafe` for conditions including a symlink traversal, unsafe
locator, or equivalent inability to prove that the acquired object is the
addressed immutable source.

A backend adapter must report `mutable` when only a mutable alias can be
resolved and `ambiguous` when the exact immutable address does not identify one
source. It must not choose the newest, first, closest, or model-preferred
candidate.

P2 treats these statuses as failures. The generic resolver does not search for
a replacement.

## 4. Failure precedence

P2 emits only the frozen
`reasoning-distiller-context-pack-failure/1` vocabulary with
`stage = "source_resolution"`.

The implementation uses the following resolution mappings:

| Condition | Frozen failure code |
|---|---|
| exact immutable source unavailable or adapter reports mutable | `IMMUTABLE_SNAPSHOT_UNAVAILABLE` |
| repository/package adapter reports unsafe or ambiguous | `CONTROL_SOURCE_INVALID` |
| safely acquired repository/package/operational bytes mismatch `raw_sha256` | `SOURCE_DIGEST_MISMATCH` |
| canonical PEMS bytes mismatch `pems_sha256` | `CANONICAL_STATE_STALE` |
| canonical standing absent | `CANONICAL_BINDING_UNPROVEN` |
| canonical address/fingerprint or same-address binding conflict | `CANONICAL_BINDING_CONFLICT` |
| operational-evidence identity or adapter result invalid | `OPERATIONAL_EVIDENCE_IDENTITY_INVALID` |
| one logical key names multiple classes | `SOURCE_CLASS_CONFLICT` |
| one logical source has conflicting fingerprints without explicit allowed multiplicity | `LOGICAL_SOURCE_CONFLICT` |
| explicit cross-source predicate is false or cannot be proven | `CROSS_SOURCE_CONSISTENCY_UNPROVEN` |
| required control slot has no source | `MISSING_REQUIRED_CONTROL` |
| required operational-evidence slot has no source | `MISSING_REQUIRED_OPERATIONAL_EVIDENCE` |
| a source-resolution bound is exceeded | `PACK_LIMIT_EXCEEDED` with `stage = "source_resolution"` and an explicit `source_resolution.<metric>` diagnostic |

The last mapping does not merge source-resolution and canonical-pack limits.
P1b froze no dedicated source-limit failure code. The stage and diagnostic make
the already accepted R8 measurement-domain distinction explicit without
changing the frozen wire vocabulary.

For the PC-07 combined pressure case, path/symlink/ambiguity is a control
safety failure. If exact safe bytes are acquired and only the digest differs,
the later P1c digest contract's more specific `SOURCE_DIGEST_MISMATCH` mapping
applies.

## 5. No implicit discovery

Every source used by P2 must already appear in `request.source_bindings`.

The resolver does not synthesize a source when:

- a required profile slot is unbound;
- a slot binding references an absent snapshot;
- a knowledge selection references an absent canonical snapshot;
- accepted canonical standing is absent;
- a consistency requirement references an absent snapshot; or
- an adapter cannot resolve the exact immutable address.

An exact duplicate complete binding is coalesced to one acquisition. Duplicate
entries still count toward `max_bindings`; coalescing does not authorize a
different snapshot and does not change request bytes.

## 6. Conflict and standing checks

P2 preserves the P1a distinction between logical source identity and immutable
snapshot identity.

For each logical `(namespace, source_id)`:

- multiple source classes fail;
- conflicting immutable fingerprints fail unless the profile permits explicit
  snapshot multiplicity and the request names that exact logical source in
  `multiple_snapshot_sources`.

For canonical state:

- the canonical address is
  `(project_id, backend_type, backend_contract, backend_config_identity,
  immutable_snapshot_id)`;
- the canonical fingerprint includes the P1a PEMS identity, optional COVE
  identity, and standing-evidence set;
- the same canonical address with different fingerprints fails; and
- every selected canonical binding must have an exact accepted-standing
  condition supplied by the request.

The resolver validates standing read-only. It does not create, repair, infer,
or admit standing.

## 7. Cross-source consistency

P2 implements only the two P1b predicates:

`same_project_identity`
: both referenced exact snapshots expose the same non-empty `project_id`.

`canonical_declares_repository_snapshot`
: the left exact snapshot is canonical state, the right exact snapshot is
repository control, and the canonical binding's explicit
`repository_relationship` matches the repository identity and commit.

No path/name similarity, canonical placement, role prose, or model judgment is
accepted as consistency evidence.

## 8. Byte verification and budgets

Repository control, package control, and operational evidence are verified as:

```text
"sha256:" + lowercase_hex(SHA256(exact_raw_bytes))
```

against the binding's `raw_sha256`.

Canonical state is verified against `pems_sha256` using the exact acquired PEMS
bytes.

No UTF-8 decoding, newline conversion, Unicode normalization, text-mode
translation, or COVE transformation occurs before these checks.

The adapter receives an effective byte bound so it can stop an unbounded read.
`limit_exceeded` fails rather than truncating or summarizing.

## 9. Pressure-case coverage

The P2 suite directly exercises the governing resolver properties represented
by the frozen pressure cases, including:

- PC-06 exact immutable commit resolution after a mutable branch moves;
- PC-07 missing/unsafe/ambiguous/digest-invalid control behavior;
- canonical stale-byte rejection corresponding to the P1 canonical-state
  pressure cases; and
- canonical binding and cross-source consistency conflict rejection.

Additional executable cases cover anti-rebinding, absent explicit references,
source-resolution budgets, package and operational-evidence acquisition,
canonical-standing failure, and duplicate-binding acquisition coalescing.

## 10. P2 boundary

Successful P2 resolution yields only verified bindings and raw bytes.

P3 remains responsible for exact PEMS selection, semantic closure, and
package-owned PEMS validation. P2 success is not P3 success, pack success,
canonical admission, role activation, or production Distiller authorization.
