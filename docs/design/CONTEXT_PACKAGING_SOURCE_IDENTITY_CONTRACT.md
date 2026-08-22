# Deterministic Context Packaging Source Identity Contract

Status: **Normative P1a source-identity freeze**

Contract:

- `reasoning-distiller-context-source-identity/1`

Governing plan:

- commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- artifact: `docs/proposals/context-packaging/FINAL_PLAN.md`
- blob: `8474d2da42f863f0a190fd80292085176d3f97f0`

Implementation gate: **P1a Source Identity only**.

This contract freezes source identity, canonical-standing binding, operational-evidence identity, conflict, and cross-source consistency semantics required by P1a. It does not freeze the P1b profile/request/pack/result/failure schemas, P1c digest preimages, P1d PEMS closure descriptor, P1e profile eligibility interface, a P2 resolver, a renderer, persistence, production `rd-distill` integration, canonical mutation, reconciliation, admission, or role/authority state.

## 1. Core identity model

A source identity has two distinct layers:

1. **logical source identity** identifies the stable source being referred to; and
2. **immutable snapshot identity** identifies the exact source state consumed by one build.

These identities MUST NOT be collapsed.

A logical source identity is explicit coordination data. It is never inferred from a path, filename, role label, prose contents, repository position, newest version, or model judgment.

An immutable snapshot identity MUST be sufficient for the applicable resolver to select exactly one source state. Mutable branch names, unversioned URLs, path-only references, labels such as `canonical`, and content self-description are not immutable snapshot identities.

Exact content identity is always bound to the original source bytes. P1a requires an observed SHA-256 digest of those bytes as part of an immutable binding. P1c owns digest-domain separation, canonical preimages, serializer rules, and receipt construction.

## 2. Logical source identity

The generic logical source identity is the structured tuple:

```text
(logical_namespace, logical_source_id)
```

Both values are explicit and non-empty.

The tuple is the identity. Implementations MUST NOT define logical identity by delimiter-concatenating the two strings. If a later wire format serializes this tuple into one scalar value, that encoding must be independently frozen, injective, and unambiguous; ordinary delimiter joining is insufficient because tuple components may themselves contain the delimiter.

`source_class` is a separate semantic classification supplied by the contracted input. V1 P1a freezes these classes:

- `repository_control`
- `package_control`
- `canonical_state`
- `operational_evidence`

A logical source has exactly one source class inside one deterministic request/build boundary. Reusing the same structured logical identity under a different source class is a source-class conflict; the implementation does not reinterpret the source from path or contents.

A structured source reference used by P1a conformance is:

```text
(source_class, logical_namespace, logical_source_id)
```

It is likewise compared structurally and MUST NOT be defined by delimiter concatenation.

`logical_namespace` prevents unrelated projects, repositories, or governed domains from colliding merely because they reuse a short identifier.

`logical_source_id` is an opaque stable identifier inside that namespace. Implementations MUST compare it exactly and MUST NOT derive authority, canonical standing, or plane assignment from its spelling.

Two items with different logical keys remain distinct even when their raw bytes are identical. Textual similarity and equal content digests are not deduplication rules across logical sources or planes.

## 3. Control source identity

### 3.1 Repository-bound control

A V1 `repository_control` binding proves an exact repository artifact only when it contains all of the following semantic components:

- explicit logical source key;
- repository identity in `owner/name` form;
- exact 40-hex Git commit identity;
- exact repository-relative artifact path;
- SHA-256 digest of the original artifact bytes.

The commit is the immutable repository snapshot. The path locates an artifact within that snapshot; the path alone is not identity and conveys no authority.

A branch name such as `main` may be used by an upstream coordinator to discover a commit before the deterministic boundary, but the resolved binding presented to context packaging MUST contain the exact commit. Silent rebinding to a moved branch is forbidden.

Repository placement or path spelling does not establish source class. A file under a directory named `canonical`, `authority`, `roles`, or similar remains whatever explicit source class the binding declares, subject to the consuming contract's independent validation.

### 3.2 Package-bound control

A V1 `package_control` binding is available for an exact control artifact whose owning project/package contract provides an immutable package snapshot identity. It MUST semantically identify:

- explicit logical source identity;
- project/package identity;
- package contract;
- immutable package snapshot/content identity;
- exact artifact locator or artifact ID inside that immutable package snapshot;
- SHA-256 digest of the original artifact bytes.

An installed directory, package name, version label, or mutable configuration path is not sufficient by itself. If the owning package contract cannot prove an immutable package snapshot, the artifact must be bound through another supported immutable form, such as `repository_control`, or fail closed. Package presence does not grant profile eligibility, role authority, activation, or canonical standing.

## 4. Canonical-state binding

Knowledge-plane input requires a V1 `canonical_state` binding. A PEMS-looking path, schema-valid PEMS object, correct PEMS content digest, request label, or self-description is insufficient to establish admitted canonical standing.

A canonical-state binding MUST semantically identify:

- project identity;
- explicit canonical logical source key;
- canonical backend type and backend contract;
- immutable backend configuration identity;
- immutable canonical snapshot identity;
- semantic tuple containing `pems/2` and the serializer identity used for the snapshot;
- exact PEMS content digest and, when COVE is bound, the exact COVE content digest and tuple;
- one or more immutable standing-evidence bindings sufficient under the consuming project/backend contract to prove that the snapshot is the admitted canonical state being consumed;
- any explicit relationship to a repository/control snapshot required by a selected consistency constraint.

The standing-evidence binding is project/backend supplied. This generic contract does not define one repository-local admission receipt as universal proof of canonical standing.

For P1a conformance, standing-evidence **identity** is distinct from standing-evidence **acceptance**. A standing-evidence item is immutably identified by:

```text
(contract, immutable_snapshot_id, raw_sha256)
```

but a correctly shaped item does not prove its own acceptance. A successful canonical-state conformance case MUST also be accompanied by an explicit accepted project/backend standing condition supplied by the consuming project/backend validation boundary. That condition identifies the structured canonical source reference and the exact canonical immutable-snapshot fingerprint it accepted. The packer/conformance evaluator MUST NOT synthesize this condition from the binding's fields or self-description.

If an accepted project/backend condition for the same canonical source reference names a different immutable fingerprint, the binding is conflicting rather than accepted. If no accepted condition exists, canonical standing is unproven.

The packer or future resolver may validate an existing binding read-only. It MUST NOT create standing evidence, infer admission from placement, repair canonical state, admit PEMS/COVE, or rewrite the binding to make it pass.

If required standing evidence or its accepted project/backend condition is absent, ambiguous, stale, conflicting, or unverifiable, canonical standing is unproven or conflicting and the operation fails closed.

## 5. Operational-evidence identity

A V1 `operational_evidence` binding carries an exact governed artifact. It MUST identify:

- explicit operational-evidence logical source key;
- artifact contract/type;
- immutable artifact snapshot identity;
- SHA-256 digest of the original artifact bytes;
- one of the frozen validation-status values below.

Frozen V1 status values are:

```text
carried_unvalidated
shape_and_digest_validated
accepted_validation_result
```

`carried_unvalidated` means only that exact artifact bytes are carried.

`shape_and_digest_validated` means a separately defined non-authority validation has established the declared shape/content identity. It does not mean the artifact is authorized or activated.

`accepted_validation_result` means the binding additionally carries the immutable identity of a separately produced accepted validation result, including its validator/result contract and exact result bytes digest. It does not mean context packaging performed the authority-bearing operation.

No status may be inferred from artifact presence, path, role name, prose, or a boolean such as `trusted`, `authorized`, or `activated`. Downstream RIL primitives retain every validation or revalidation requirement imposed by their own contracts.

## 6. Immutable snapshot fingerprints

For conflict comparison inside P1a, each source binding has a semantic immutable-snapshot fingerprint.

For `repository_control`, the fingerprint is the exact tuple:

```text
(repository, normalized_commit, path, normalized_raw_sha256)
```

For `package_control`, the fingerprint is the exact tuple:

```text
(project_id, package_contract, immutable_package_snapshot_id,
 artifact_locator, normalized_raw_sha256)
```

For `canonical_state`, the fingerprint is the exact tuple:

```text
(project_id, backend_type, backend_contract, backend_config_identity,
 immutable_snapshot_id, pems_semantic, serializer, normalized_pems_sha256,
 optional_cove_tuple_and_sha256, standing_evidence_identity_set)
```

When present, `optional_cove_tuple_and_sha256` is exactly:

```text
(cove_semantic, pems_semantic, serializer, normalized_cove_sha256)
```

The standing-evidence component is a mathematical set of normalized standing-evidence identities. Ordering and duplicate presentation of an identical evidence identity do not change the canonical fingerprint. A changed evidence identity does change it.

For `operational_evidence`, the fingerprint is the exact tuple:

```text
(artifact_contract, immutable_snapshot_id, normalized_raw_sha256,
 validation_status, optional_validation_result_identity)
```

where the optional validation-result identity is:

```text
(result_contract, validator_contract, immutable_snapshot_id,
 normalized_raw_sha256)
```

Only hexadecimal representation normalization frozen by Section 11 is applied to commit and SHA-256 fields. Every other component remains exact.

P1c may add canonical digest identities over frozen serialized forms. It MUST NOT change which semantic components distinguish P1a snapshots without a versioned amendment.

## 7. Logical-source conflicts

Within one deterministic request/build boundary, bindings sharing one structured logical source identity MUST use the same `source_class`. Different classes for one logical identity are a source-class conflict and MUST fail closed.

Bindings sharing one structured logical source identity and source class MUST resolve to one immutable snapshot fingerprint unless the explicit contracted intent models multiple snapshots for that exact logical source.

The default multiplicity is one snapshot.

If two bindings share a logical key and have different immutable fingerprints while multiple snapshots are not explicitly modeled, the result is a logical-source conflict and MUST fail closed. The implementation MUST NOT pick newest, first, last, path-local, highest version, or model-preferred state.

When multiple snapshots are explicitly modeled, each immutable fingerprint remains separately addressable. Permission to model several snapshots is selection intent only; it grants no canonical or authority standing.

## 8. Cross-source consistency

Cross-source consistency is never inferred merely because individually valid bindings exist.

A governed profile/request may require explicit predicates between named structured source references. P1a freezes these V1 predicate semantics:

### `same_project_identity`

Both referenced bindings expose a project identity and those identities compare exactly. Missing project identity makes the predicate unproven.

### `canonical_declares_repository_snapshot`

The referenced canonical-state binding contains an explicit declared repository relationship consisting of exact repository identity plus exact 40-hex commit, and that tuple equals the referenced repository-control snapshot's repository and normalized commit.

A missing declaration, mutable branch label, unequal repository, or unequal commit makes the predicate unproven.

Unknown predicate names are unsupported and therefore unproven. The packer/resolver MUST NOT invent project-specific ancestry, temporal, naming, or path relationships.

If a required consistency predicate is unproven, the operation fails closed. A profile that does not require a relationship does not gain one implicitly.

## 9. Classification and plane boundary

Source class and plane use remain explicit semantic facts.

- `repository_control` and `package_control` are eligible only for explicitly selected control material under later profile/request contracts.
- `canonical_state` is the only P1a source class that can establish the source side of knowledge-plane canonical standing, and only with a valid canonical-state binding plus accepted project/backend standing condition.
- `operational_evidence` remains operational evidence regardless of whether its text resembles a directive or whether a validation result was accepted.

P1a does not itself select sources into planes. P1b/P1e inputs later carry the explicit selection/profile intent. P2 performs read-only resolution. No P1a rule upgrades one class into another.

## 10. Fail-closed conformance semantics

P1a conformance fixtures use stable gate-local classifications to pin the semantic boundary. These are not the P1b runtime failure wire schema.

Required gate-local failures include:

- `SOURCE_IDENTITY_INVALID`
- `UNSUPPORTED_SOURCE_CLASS`
- `SOURCE_CLASS_CONFLICT`
- `IMMUTABLE_SNAPSHOT_UNAVAILABLE`
- `CONTROL_SOURCE_INVALID`
- `CANONICAL_BINDING_UNPROVEN`
- `CANONICAL_BINDING_CONFLICT`
- `OPERATIONAL_EVIDENCE_IDENTITY_INVALID`
- `LOGICAL_SOURCE_CONFLICT`
- `CROSS_SOURCE_CONSISTENCY_UNPROVEN`

P1b owns the eventual runtime result/failure contracts and may map these conformance meanings into frozen wire codes without weakening the semantics above.

## 11. Deterministic comparison rules

P1a identity checks use exact structural comparisons only.

- logical keys and source references are tuples, not delimiter-joined strings;
- Git commit identities are lowercase or uppercase hex representations of exactly 20 bytes; implementations compare the normalized lowercase hex value, not a branch name;
- SHA-256 content identities are `sha256:` followed by exactly 64 hexadecimal digits; implementations compare the normalized lowercase hexadecimal representation;
- standing-evidence identity collections are sets after the permitted digest normalization, so presentation order and duplicate identical entries are non-semantic;
- repository, path, contract, namespace, logical ID, project ID, backend ID, immutable snapshot ID, semantic-version, and serializer strings are compared exactly after only the representation normalization explicitly frozen by their owning contract;
- no Unicode normalization, case folding of opaque strings, path canonicalization, fuzzy matching, semantic equivalence, or model judgment is introduced by P1a.

Filesystem safety, symlink handling, and actual source acquisition belong to P2. P1a freezes what identity must be proven, not how the resolver obtains bytes.

## 12. P1b, P1c, and P2 boundaries

P1a intentionally leaves these later gates untouched:

- **P1b** freezes JSON Schemas and runtime result/failure envelopes, including closed-world unknown-field rejection.
- **P1c** freezes Base64 payload representation, JCS/canonical serialization, named digest domains and preimages, receipts, and toolchain identity.
- **P2** implements read-only acquisition/resolution, filesystem safety, backend availability handling, and verifies real source bytes against the frozen identities.

P1a conformance fixtures are machine-checkable semantic examples. Their structured Python tuples and accepted-standing conditions are gate-local test representations, not wire-protocol schemas and not a production resolver.

## 13. P0 pressure-case preservation

P1a conformance MUST mechanically retain the exact frozen P0 pressure text and required outcomes for the P1a-owned facets of:

- PC-03 admitted canonical standing;
- PC-06 immutable repository commit identity;
- PC-07 invalid control-source identity;
- PC-16 exact control artifact without authority creation;
- PC-22 unsupported ambient/session source class;
- PC-24 carried operational evidence without authority creation;
- PC-27 explicit cross-source relationship failure;
- PC-31 shape-valid PEMS without accepted canonical standing;
- PC-32 canonical binding/snapshot conflict;
- PC-42 logical-source snapshot conflict;
- PC-43 carried operational evidence without inferred validator acceptance;
- PC-45 equal content under distinct source identities.

The conformance test loads `tests/fixtures/context-packaging-pressure-cases-v1.json`, checks those source-pressure and required-outcome strings exactly, and binds each to a P1a semantic case with a compatible PASS/failure result. P0 cases whose decisive behavior is actual acquisition, source disappearance, filesystem behavior, rendering, serialization, or later request-schema semantics remain preserved in P0 and are not falsely claimed as completed by P1a.

## 14. Conformance gate

P1a is complete only when machine-checkable evidence demonstrates at least:

1. repository controls require exact commit plus raw-byte digest;
2. package controls require an immutable package snapshot/content identity plus exact artifact bytes digest;
3. mutable branch/path-only/package-name-only identity fails;
4. structured logical identities and source references cannot collide through delimiter concatenation;
5. canonical-looking paths and valid PEMS bytes do not prove canonical standing;
6. a complete backend/project canonical-state binding succeeds only when an independent accepted project/backend standing condition matches its exact immutable fingerprint;
7. canonical fingerprints include the optional COVE tuple/digest and normalized standing-evidence identity set exactly as frozen;
8. operational evidence preserves exact artifact identity and explicit validation status without creating authority;
9. logical identity, source classification, and immutable snapshot identity remain distinct;
10. conflicting source classes for one logical identity fail closed;
11. conflicting snapshots for one logical source fail unless multiple snapshots were explicitly modeled;
12. equal bytes under different logical identities remain distinct;
13. required cross-source relationships pass only from explicit exact evidence;
14. missing, mismatched, or unsupported required relationships fail closed;
15. the relevant frozen P0 pressure cases and required outcomes are mechanically preserved;
16. no P1a operation performs reconciliation, admission, canonical mutation, authority mutation, or production evidence integration.
