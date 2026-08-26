# P1e Governed Consumer / Profile Eligibility Contract

Status: **Normative P1e governed-consumer eligibility freeze**

Contract:

- `reasoning-distiller-context-profile-eligibility-interface/1`

Governing plan:

- commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- artifact: `docs/proposals/context-packaging/FINAL_PLAN.md`
- blob: `8474d2da42f863f0a190fd80292085176d3f97f0`

P1d prerequisite basis:

- immutable P1d candidate: `945ff72ccee87310642ff78c4b4c8e01c46fb551`
- observed candidate-bound GitHub Actions run: `32631944866`
- observed suite result: `11/11 PASS`
- supplied handoff disposition: `P1D_STEWARD_RECONCILIATION_ACCEPTED`

The supplied disposition above is recorded as handoff provenance only. This P1e artifact does not create Steward authority, RIL activation, reconciliation, admission, or canonical standing. The approved final plan independently authorizes sequential implementation of P1a through P1e before P2.

Implementation gate: **P1e Consumer / Profile Eligibility only**.

This contract freezes the interface by which a governed consumer accepts an exact profile eligibility binding. It gives semantic meaning to the P1b `reasoning-distiller-context-profile-eligibility/1` wire shape without changing that schema. It does not implement source resolution, read profile bytes, evaluate project policy, execute a policy registry, project PEMS, encode COVE, build or persist a pack, render activation material, change production `rd-distill`, mutate canonical state, reconcile, admit, authorize, or activate.

## 1. Frozen P1b wire basis

P1e is layered on the reviewed P1b schemas already bound by P1c. These exact schema blobs remain unchanged:

| Schema | Git blob |
|---|---|
| `schemas/context-profile-eligibility.schema.json` | `ad8ba5839136fe7e1080d1d7e26ca351202864dc` |
| `schemas/context-pack-request.schema.json` | `602391284019ab680bd419c7d007e7af3cfeef53` |
| `schemas/context-pack-failure.schema.json` | `10195c52df81156a954eb9b5acee5a4f1b26f576` |

P1e MUST NOT edit those bytes while claiming compatibility with the P1c freeze. A later wire-schema revision requires its own reviewed schema basis.

The P1b request keeps `eligibility` optional at the generic wire level. P1e does not turn that field into a globally required schema member. Instead, a governed consumer declares outside the request that profile eligibility is required for its invocation boundary. A request cannot opt itself out of that consumer requirement.

## 2. Separation of validation and eligibility

Profile validation and profile eligibility are separate operations.

The context-pack primitive may validate:

- profile schema;
- request schema;
- declared contract compatibility;
- exact profile identity fields supplied by the request.

It MUST NOT decide that a valid profile is eligible for a governed workflow.

Eligibility belongs to the consuming project/workflow policy boundary. That boundary supplies an explicit eligibility binding or policy result. Repository placement, filename, role label, newest version, model choice, task wording, semantic similarity, ambient memory, or hidden reasoning MUST NOT establish eligibility.

A profile remains a deterministic recipe. It is not authority.

## 3. Governed-consumer input interface

For P1e conformance, the governed-consumer acceptance operation receives only these explicit semantic inputs:

```text
requested_profile
eligibility_binding
expected_consumer
required_policy_evidence
```

`requested_profile` is exactly the P1b request profile reference:

```text
(profile_id, profile_version, raw_sha256)
```

`eligibility_binding` is either absent or a schema-valid
`reasoning-distiller-context-profile-eligibility/1` value.

`expected_consumer` is the exact structured tuple:

```text
(consumer_contract, consumer_id, immutable_policy_snapshot_id)
```

It is supplied by the governed consumer/workflow boundary. It is not derived from the request, repository, model, role text, or profile contents.

`required_policy_evidence` is either absent or the exact immutable policy-result identity required by that consumer:

```text
(contract, immutable_snapshot_id, raw_sha256)
```

A consumer that does not require one particular policy-result identity may omit this comparison input, but the eligibility binding itself still MUST carry `policy_evidence` because P1b requires it.

There is no P1e input for repository path, filename, role label, task similarity, model choice, prompt text, chat memory, assistant recollection, hidden reasoning, or implicit current state.

## 4. Exact acceptance predicate

A governed consumer accepts a profile eligibility binding if and only if every condition below holds.

### 4.1 Binding presence

If eligibility is required and `eligibility_binding` is absent, fail:

```text
ELIGIBILITY_BINDING_MISSING
stage = eligibility
```

No default profile, repository profile, newest profile, role-selected profile, or model-selected profile may substitute for the missing binding.

### 4.2 Exact consumer binding

The binding's:

```text
consumer.consumer_contract
consumer.consumer_id
consumer.immutable_policy_snapshot_id
```

MUST equal the three `expected_consumer` values exactly.

Any mismatch fails:

```text
PROFILE_INELIGIBLE
stage = eligibility
```

The consumer tuple is coordination identity for the policy boundary. It does not create role registration, authorization, activation, reconciliation, admission, or canonical standing.

### 4.3 Exact profile binding

The binding's:

```text
profile.profile_id
profile.profile_version
profile.raw_sha256
```

MUST identify the same exact requested profile as `requested_profile`.

`profile_id` and `profile_version` compare as exact strings.

SHA-256 values compare using the hexadecimal representation normalization already frozen by P1a: the `sha256:` prefix and 64 hexadecimal digits are required, and hexadecimal letter case is normalized for comparison only. P1e adds no Unicode normalization, path normalization, case folding of opaque identifiers, semantic equivalence, or fuzzy matching.

Any mismatch fails:

```text
PROFILE_INELIGIBLE
stage = eligibility
```

P1e does not read profile bytes and therefore does not independently prove that `profile.raw_sha256` matches a profile artifact. That source-byte validation belongs to the applicable profile/request validation boundary before semantic packaging.

### 4.4 Policy-result identity

`eligibility_binding.policy_evidence` is an immutable identity for the consumer-supplied policy result or governing binding. The generic context-pack primitive MUST NOT discover, fetch, execute, interpret, repair, or select that policy result.

If `required_policy_evidence` is supplied by the governed consumer, the binding's policy-evidence tuple MUST match it exactly, using the same SHA-256 representation normalization described above.

A mismatch fails:

```text
PROFILE_INELIGIBLE
stage = eligibility
```

The P1e interface does not define one universal project policy engine, registry, repository path, or policy-result contract. Those remain consuming-project/workflow concerns.

### 4.5 Decision

Only:

```text
decision = eligible
```

passes the eligibility decision.

A schema-valid:

```text
decision = ineligible
```

fails:

```text
PROFILE_INELIGIBLE
stage = eligibility
```

`reason_code` is diagnostic data owned by the producer of the eligibility binding. Its text MUST NOT override the structured decision or any exact identity mismatch.

## 5. Structural validation boundary

P1e consumes only a binding that has already passed the frozen P1b eligibility schema.

Malformed eligibility bytes remain a P1b structural-validation failure. P1e does not redefine malformed objects into a new semantic meaning, tolerate unknown fields, or reinterpret them as policy hints.

In particular, fields such as these are not P1e semantics:

```text
trusted
authorized
activated
role_label
repository_path
latest
model_choice
task_similarity
```

If inserted into the closed P1b binding, they are rejected structurally because the schema has `additionalProperties: false`.

## 6. Failure semantics

P1e uses only the already-frozen P1b failure vocabulary needed by this gate:

| Condition | Failure code | Stage |
|---|---|---|
| Governed consumer requires eligibility but binding is absent | `ELIGIBILITY_BINDING_MISSING` | `eligibility` |
| Consumer identity mismatch | `PROFILE_INELIGIBLE` | `eligibility` |
| Requested profile identity mismatch | `PROFILE_INELIGIBLE` | `eligibility` |
| Required policy-evidence identity mismatch | `PROFILE_INELIGIBLE` | `eligibility` |
| Binding decision is `ineligible` | `PROFILE_INELIGIBLE` | `eligibility` |

P1e introduces no new runtime failure code and does not revise P1b failure-schema bytes.

## 7. Digest and replay boundary

P1e introduces no new digest domain.

The P1c canonical request digest already covers the complete validated request object. Therefore, when a request contains `eligibility`, that binding is already part of the canonical request value hashed under the existing `context-pack-request` domain.

P1e MUST NOT:

- create an `eligibility` digest domain;
- substitute the P1c canonical profile digest for the P1b `profile.raw_sha256` field;
- silently strip eligibility from the canonical request before hashing;
- mutate the request in order to make a binding pass.

The P1b profile raw digest and the P1c canonical profile digest retain their distinct meanings.

## 8. Pure reference operation

A conforming P1e reference acceptance operation is read-only and deterministic.

For fixed explicit inputs it returns exactly one of:

```text
eligible
ELIGIBILITY_BINDING_MISSING
PROFILE_INELIGIBLE
```

It performs no file reads, network access, repository lookup, source resolution, policy lookup, model call, semantic search, cache mutation, pack mutation, canonical mutation, or RIL operation.

The operation is intentionally smaller than P2. It checks whether an already supplied eligibility binding is acceptable to an already identified governed consumer for an already identified requested profile.

## 9. Conformance requirements

P1e conformance MUST demonstrate at least:

1. the exact P1b eligibility, request, and failure schema blobs are unchanged;
2. an exact eligible binding for the expected consumer and requested profile is accepted;
3. a missing required binding fails `ELIGIBILITY_BINDING_MISSING`;
4. `decision = ineligible` fails `PROFILE_INELIGIBLE`;
5. each consumer tuple mismatch fails `PROFILE_INELIGIBLE`;
6. each requested-profile tuple mismatch fails `PROFILE_INELIGIBLE`;
7. equivalent hexadecimal letter case in SHA-256 spelling compares equal;
8. an explicitly required policy-evidence mismatch fails `PROFILE_INELIGIBLE`;
9. `reason_code` cannot override an ineligible decision or identity mismatch;
10. closed-world schema validation rejects inference-like fields rather than treating them as eligibility hints;
11. the reference evaluator exposes no repository, role, model, task-similarity, ambient-memory, or resolver input channel;
12. P2 source resolution and every later gate remain unimplemented by the P1e change set.

## 10. Exit criterion and boundary

P1e is frozen when the conformance requirements above pass against an immutable candidate and review accepts the interface.

The resulting interface establishes only this statement:

> A governed consumer can deterministically verify that an explicitly supplied, structurally valid eligibility binding names the exact consumer, exact requested profile, required immutable policy-result identity when one is specified, and an `eligible` decision.

It does not establish that a repository profile is eligible merely because it exists. It does not create authority or activation. It does not validate canonical standing. It does not begin P2.

After P1e review closure, the next implementation gate in the approved plan is P2 Resolver. P2 MUST NOT begin merely because a P1e implementation candidate exists or its local tests pass.
