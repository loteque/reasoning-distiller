# P1d PEMS/2 Closure Descriptor Contract

Status: **Normative P1d closure-semantics freeze**

Contract:

- `reasoning-distiller-pems2-closure-descriptor/1`

Governing plan:

- commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- artifact: `docs/proposals/context-packaging/FINAL_PLAN.md`
- blob: `8474d2da42f863f0a190fd80292085176d3f97f0`

P1c prerequisite evidence:

- immutable P1c candidate: `ec5fe4c6c7e8678c3ead0ac629d97d04022b914c`
- supplied Steward disposition: `P1C_STEWARD_REMEDIATION_ACCEPTED`
- execution disposition: `P1C_CONFORMANCE_EXECUTION_PASS`
- durable evidence head: `c1598b04fc1c0734437455fcde53b56f8cd3bed5`
- evidence-manifest blob: `0f50bb7b7e96a13311e86c881cdf74a92df44479`

Implementation gate: **P1d PEMS closure only**.

This contract freezes the exhaustive PEMS/2 reference descriptor required before a
projection implementation exists. It does not implement source resolution,
projection, profile eligibility, COVE encoding, persistence, rendering,
production integration, canonical mutation, reconciliation, admission,
authorization, or activation. It does not edit P1c byte/digest/schema semantics.

## 1. Bound PEMS/2 surface

This descriptor is bound to the package-owned PEMS/2 artifacts inspected for
this gate:

- schema `backends/pems-cove/pems-v2.schema.json`, Git blob
  `cd7683d704e8aef2842a0c1b25b453fb1dbc8030`;
- semantic validator `backends/pems-cove/validate_pems2_contract.py`, Git blob
  `d615bf2e95d3721b0ca312075cc0c39522f0a896`.

The machine-readable descriptor is:

- `protocols/rgp/pems2-context-closure-v1.json`

A later change to the PEMS schema or to reference-bearing semantics requires a
new closure-descriptor version or an explicitly reviewed compatible revision.
A builder must never apply this descriptor to a structurally different PEMS
reference surface merely because the document still says `pems/2`.

The P1c fixture
`tests/fixtures/context-packaging-p1c-closure-descriptor-identity.json` remains
exactly what P1c says it is: an identity-only fixture containing no P1d rules.
P1d does not rewrite it.

## 2. Exactly three reference outcomes

Every reference recognized by this descriptor has exactly one closure outcome:

1. `include_transitively`
   - the field has a defined internal PEMS graph target namespace;
   - every referenced target is required in the projection and is processed
     recursively under this descriptor;
   - missing required targets fail closed.

2. `preserve_external_reference`
   - the value is a locator or identity outside the PEMS graph;
   - the value is copied unchanged with its containing PEMS item;
   - closure must not dereference it, fetch it, validate external authority from
     it, or convert it into another context-pack source.

3. `reject`
   - the field is reference-bearing but this descriptor version cannot ground a
     deterministic supported reference meaning from the bound contract;
   - the builder fails with the rule's stable failure code before producing a
     projection.

There is no "ignore", "best effort", "model decides", "copy and hope", or
implicit fourth outcome.

A field may be explicitly present in the exhaustive descriptor and still be
`reject`. Exhaustive enumeration does not authorize P1d to invent a namespace
that the bound PEMS/2 contract does not establish.

Absent optional fields contribute no edge. `null` contributes no edge only where
the exact bound PEMS/2 schema permits `null`.

## 3. Identifier declarations are not references

`record.id` declares a record identity and `relation.id` declares a relation
identity. They are exhaustively accounted for in the descriptor's
`identifier_definitions` section, but they do not themselves create closure
edges.

This distinction prevents the closure implementation from treating an item's
own identity as an accidental self-reference while still making descriptor
coverage auditable.

## 4. Internal PEMS graph references

The descriptor marks the following supported reference classes
`include_transitively`.

### Document and common record references

- root `project_id` -> record; the existing PEMS validator requires the target
  kind to be `project`;
- record `supersedes[]` -> records;
- record `superseded_by[]` -> records;
- record provenance `primary[]`, `corroborating[]`, `context[]`, and `untyped[]`
  -> records; the existing PEMS validator requires those targets to be
  `source_observation`.

Record supersession traversal is directional exactly as stored. If an included
record contains either record supersession field, that explicit reference is
followed. P1d does not infer additional record supersession from time, lifecycle,
or inverse lookup.

### Kind-specific record references

- `chat.data.project_id`;
- `chat.data.active_role_id`;
- `role.data.directive_source_id`;
- `database_column.data.table_id`;
- `pull_request.data.head_branch_id`;
- `validation.data.target_id`;
- `continuation.data.chat_id`;
- `continuation.data.active_role_id`;
- `continuation.data.blocker_ids[]`;
- `continuation.data.pending_owner_decision_ids[]`;
- `continuation.data.high_value_record_ids[]`;
- `source_observation.data.source_id`, whose target kind is already required by
  the package-owned validator to be `source`;
- `proposition.data.about_ids[]`.

Except for target-kind requirements already enforced by the bound PEMS
validator, P1d does not add new target-kind validation. It freezes reachability,
not a new PEMS ontology.

### Relation references with grounded namespaces

- `relation.from` -> record;
- `relation.to` -> record;
- relation provenance `primary[]`, `corroborating[]`, `context[]`, and
  `untyped[]` -> `source_observation` records under the existing validator.

The exact bound semantic validator rejects relation identities used as
`relation.from`/`relation.to`, and rejects non-`source_observation` identities in
relation provenance. The P1d conformance suite probes those behaviors rather
than accepting the descriptor's own namespace labels as its oracle.

## 5. Relation supersession is exhaustively enumerated and rejected

The bound JSON Schema exposes both:

- `relation.supersedes[]`;
- `relation.superseded_by[]`.

Both are structurally `idArray` fields, so omitting them would violate the P1d
exhaustiveness requirement. But the exact bound schema does not distinguish
record IDs from relation IDs for either field, and the exact bound semantic
validator does not resolve or validate either relation-supersession field.

The conformance suite demonstrates that otherwise-valid PEMS/2 documents remain
accepted by the bound validator when either relation-supersession field contains
a record ID and also when it contains a relation ID. That observation does not
prove that both meanings are allowed. It proves that this P1d evidence set does
not establish a unique target namespace.

Accordingly descriptor version 1 assigns both fields the explicit rule:

```text
reject -> UNDEFINED_CLOSURE_RULE
```

No `target_namespace` is attached to either rule. P1d therefore makes no
relation-supersession namespace claim, performs no traversal through those
fields, and does not reinterpret them as external references. A future supported
meaning requires separately grounded PEMS semantics and a reviewed compatible
descriptor revision or new descriptor version.

This is fail-closed behavior, not an omitted rule.

## 6. External references remain inert PEMS data

The descriptor explicitly marks known non-graph identifiers and locators
`preserve_external_reference`, including repository identities, paths and safe
locators, branch commit identities, pull-request identity components,
environment-variable external references, adjustment authority targets, source
identity locators, source-observation evidence locators, note/owner-instruction
identities, and captured fingerprints.

These fields survive byte-for-value in the selected PEMS object because their
containing record survives. They do **not** authorize the closure stage to read
another file, query GitHub, resolve a secret, accept an owner instruction,
establish authority, or introduce another pack source.

Graph closure follows defined PEMS graph identities. External locators remain
provenance/content and never enter the closure work queue.

## 7. Derived propositions require one explicit inverse structural rule

The package-owned PEMS semantic validator requires every included derived
proposition to have `derived_from` premise structure. That requirement cannot be
satisfied by following only fields contained inside the proposition, because the
reference is stored on relation objects.

For an included record with:

```text
kind == "proposition"
data.epistemic_role == "derived"
```

P1d therefore defines exactly one inverse structural rule:

```text
include every canonical relation where
  relation.kind == "derived_from"
  and relation.from == selected_proposition.id
```

Zero matches fail semantic validation. Every matching relation is included,
rather than choosing a "best" premise relation. The ordinary relation rules then
include its endpoints and provenance.

No other inbound relation is pulled merely because one or both endpoints are
included. In particular, including a normal record does not automatically
include every `supports`, `references`, `contradicts`, `depends_on`, or other
incident relation. Such eager reverse traversal would broaden selection beyond
the minimum graph required by the frozen semantics.

## 8. Traversal and fixed-point semantics

Closure begins only from exact request-selected record IDs and relation IDs.
There is no fuzzy lookup or relevance substitution.

The closure result is the least fixed point of:

- the exact seeds;
- all `include_transitively` rules encountered on included objects; and
- the derived-proposition structural rule above.

An encountered explicit `reject` rule terminates the build with its stable
failure rather than adding an edge.

Traversal order may differ internally, but the set result must not. A visited
identity is the pair `(namespace, id)`, where namespace is `record` or
`relation`. Cycles therefore terminate deterministically without truncating a
valid cycle.

When multiple selectors or closure paths reach the same item, the item is
included once. The outer packaging inclusion ledger must retain every
deterministic inclusion cause as already required by the governing design; P1d
does not write those causes into PEMS provenance.

External references never enter the work queue.

## 9. Failure semantics

The following failures are frozen for P1d:

- exact request-selected record/relation absent:
  `SELECTED_SEMANTIC_ID_MISSING`;
- a required internal closure target absent:
  `SELECTED_SEMANTIC_ID_MISSING`;
- encountered reference semantics without an exact P1d rule:
  `UNDEFINED_CLOSURE_RULE`;
- encountered relation `supersedes[]` or `superseded_by[]`, whose target
  namespace is not established by the bound PEMS/2 contract:
  `UNDEFINED_CLOSURE_RULE`;
- required derived-premise structure absent or the closed document violates
  bound PEMS semantic invariants:
  `PEMS_SEMANTIC_INVALID`;
- closure exceeds the profile's later-enforced projection limit:
  `CLOSURE_LIMIT_EXCEEDED`.

The closure algorithm never truncates to satisfy a limit.

## 10. Post-closure validity

A future P3 projection implementation must validate the complete selected PEMS
document under both the exact package-owned PEMS/2 JSON Schema and semantic
validator before claiming success.

Closure may include existing canonical records and relations. It must not repair
them, rewrite proposition text, manufacture relations, infer supersession,
change lifecycle state, reclassify provenance, mutate canonical state, or admit
new knowledge.

## 11. Independent conformance requirements for this freeze

`tests/test_context_packaging_pems_closure_p1d.py` mechanically checks that:

- the bound PEMS schema and validator Git-blob identities have not drifted;
- every frozen descriptor rule has one of the three allowed outcomes;
- the exact bound schema is walked independently of descriptor rule IDs:
  - the record `allOf` dispatch table derives kind-specific data schemas;
  - nested object references such as provenance, identity locators, and evidence
    locators are traversed;
  - ID-array, `_id`/`_ids`, structural endpoint, and locator/identity-shaped
    scalar leaves are discovered from the schema;
  - the resulting field keys must equal the descriptor field keys exactly;
- `record.id` and `relation.id` are definitions, not closure references;
- executable probes against the exact bound semantic validator independently
  establish its record-endpoint, provenance, root-project, and source-kind
  constraints;
- executable probes demonstrate that the bound validator accepts both record-ID
  and relation-ID values in relation supersession fields, so P1d must not claim
  a target namespace for them;
- both relation supersession fields are explicit `reject` rules with
  `UNDEFINED_CLOSURE_RULE` and no `target_namespace`;
- P0 closure pressure cases PC-09 through PC-12, PC-19, PC-20, plus PC-36 and
  PC-38 remain represented by the frozen pressure suite;
- removing a required rule converts a supported reference into
  `UNDEFINED_CLOSURE_RULE`;
- an unknown future ID-bearing reference fails closed;
- a missing internal target fails rather than being omitted;
- external locators are preserved but never traversed;
- derived propositions have the one explicitly allowed inverse structural rule;
- the P1c identity-only closure fixture remains out of P1d semantics.

The conformance suite does not treat a hand-written list of descriptor rule IDs
as proof of exhaustiveness. Descriptor coverage and namespace claims must be
challenged from the independently inspected bound schema/validator behavior.

Passing this suite is evidence only for the P1d contract freeze. It is not
evidence that a P2 resolver, P3 projection implementation, P4 COVE adapter, P1e
eligibility policy, or any later gate exists or is authorized.
