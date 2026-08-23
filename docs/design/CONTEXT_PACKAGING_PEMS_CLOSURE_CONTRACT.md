# P1d PEMS/2 Closure Descriptor Contract

Status: **Normative P1d closure-semantics freeze**

Contract: `reasoning-distiller-pems2-closure-descriptor/1`

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

This contract freezes the exhaustive PEMS/2 reference descriptor required before a projection implementation exists. It does not implement source resolution, projection, profile eligibility, COVE encoding, persistence, rendering, production integration, canonical mutation, reconciliation, admission, authorization, or activation. It does not edit P1c byte, digest, schema, or toolchain semantics.

## 1. Bound PEMS/2 evidence

Descriptor version 1 is bound to exactly:

- `backends/pems-cove/pems-v2.schema.json`, Git blob `cd7683d704e8aef2842a0c1b25b453fb1dbc8030`;
- `backends/pems-cove/validate_pems2_contract.py`, Git blob `d615bf2e95d3721b0ca312075cc0c39522f0a896`.

The machine-readable descriptor is `protocols/rgp/pems2-context-closure-v1.json`.

The JSON Schema establishes the complete structural reference surface, but explicitly assigns graph integrity and provenance semantics to semantic validation outside JSON Schema. A field name, `_id` suffix, `_ids` suffix, or structural `idArray` shape therefore does not establish a graph target namespace by itself.

A later change to either bound PEMS artifact or to reference-bearing semantics requires a reviewed compatible revision or a new closure-descriptor version.

## 2. Exactly three outcomes

Every independently discovered reference-bearing field receives exactly one rule:

1. `include_transitively`: the bound semantic validator independently establishes a supported internal PEMS target namespace. The target is required and recursively processed.
2. `preserve_external_reference`: the field is an explicitly defined opaque non-PEMS identity or locator. It is preserved with its containing item and never traversed by closure.
3. `reject`: the field is reference-bearing but its supported graph meaning or target namespace is not established by the bound PEMS evidence. Encountering it fails closed with `UNDEFINED_CLOSURE_RULE`.

There is no implicit inference from spelling, record kind, apparent business meaning, or the descriptor's own labels. Exhaustive enumeration is not permission to invent a namespace.

Absent optional fields contribute no edge. `null` contributes no edge only where the bound schema permits `null`.

## 3. Identifier declarations

`record.id` declares the `record` namespace. `relation.id` declares the `relation` namespace. These are descriptor `identifier_definitions`, not closure edges.

Visited identity is `(namespace, id)`, preventing collision between record and relation identifiers even when their string values happen to match.

## 4. Independently grounded internal references

Descriptor version 1 assigns `include_transitively` only to the families mechanically enforced by the exact bound semantic validator.

### Root project reference

- root `project_id` -> `record`, target kind `project`.

The validator resolves the value through the record index and requires a `project` record.

### Provenance references

For both records and relations:

- `provenance.primary[]`;
- `provenance.corroborating[]`;
- `provenance.context[]`;
- `provenance.untyped[]`.

All target the `record` namespace and target kind `source_observation`. The validator rejects values not present in the source-observation record-ID set.

### Source-observation source reference

- `source_observation.data.source_id` -> `record`, target kind `source`.

The validator resolves this value through the record index and requires a `source` record.

### Relation endpoints

- `relation.from` -> `record`;
- `relation.to` -> `record`.

The validator requires both endpoint strings to resolve through the record index and rejects relation IDs used as endpoints.

These namespace claims are challenged by executable probes against the validator. The descriptor is not used as the oracle for those probes.

## 5. ID-bearing fields with unestablished namespaces

The bound schema exposes additional ID-bearing fields whose target namespace the bound semantic validator does not resolve. Descriptor version 1 exhaustively enumerates them but assigns `reject -> UNDEFINED_CLOSURE_RULE` with no `target_namespace`:

- record `supersedes[]` and `superseded_by[]`;
- `chat.data.project_id` and `chat.data.active_role_id`;
- `role.data.directive_source_id`;
- `database_column.data.table_id`;
- `pull_request.data.head_branch_id`;
- `validation.data.target_id`;
- `continuation.data.chat_id`;
- `continuation.data.active_role_id`;
- `continuation.data.blocker_ids[]`;
- `continuation.data.pending_owner_decision_ids[]`;
- `continuation.data.high_value_record_ids[]`;
- `proposition.data.about_ids[]`;
- relation `supersedes[]` and `superseded_by[]`.

For these fields, the conformance suite must demonstrate that otherwise-valid documents remain accepted by the bound semantic validator when the field carries a record ID and also when it carries a relation ID. That demonstrates absence of a validator-enforced namespace. It does not assert that both meanings are semantically valid.

P1d does not repair this ambiguity by modifying PEMS/2. Changing the PEMS semantic validator or adding new graph-integrity semantics would be a separate semantic change outside this remediation scope.

A future descriptor may traverse one of these fields only after separately governed PEMS evidence establishes its target semantics.

## 6. External references remain inert

Known non-graph identities and locators remain `preserve_external_reference`, including repository identities, paths, safe locators, branch commit identities, pull-request identity components, environment-variable external references, adjustment authority targets, source identity locators, source-observation evidence locators, owner/note identifiers carried as locators, and captured fingerprints.

Preservation does not authorize fetching, secret resolution, authority acceptance, role activation, source expansion, or any other side effect.

## 7. Derived propositions

An included record with `kind == "proposition"` and `data.epistemic_role == "derived"` triggers exactly one inverse structural rule:

```text
include every canonical relation where
  relation.kind == "derived_from"
  and relation.from == selected_proposition.id
```

All matching relations are included. Zero matches reject through PEMS semantic validation. No other inbound relation discovery is permitted merely because an endpoint record is selected.

The included relation is in the `relation` namespace by structural selection of relation objects. Its ordinary endpoint and provenance rules then use the independently grounded rules in section 4.

## 8. Traversal and failures

Closure starts only from exact request-selected record and relation IDs and computes the least fixed point of:

- exact seeds;
- encountered `include_transitively` rules; and
- the derived-proposition structural rule.

`reject` terminates the build before projection emission. External references never enter the work queue. Cycles terminate through visited `(namespace, id)` identity. Multiple causes include an item once while preserving every deterministic inclusion cause in the later outer packaging ledger.

Frozen P1d failure semantics include:

- absent selected or required grounded internal target: `SELECTED_SEMANTIC_ID_MISSING`;
- undefined or ungrounded reference semantics: `UNDEFINED_CLOSURE_RULE`;
- missing required derived-premise structure or other closed-document semantic invalidity: `PEMS_SEMANTIC_INVALID`;
- later projection bound exceeded: `CLOSURE_LIMIT_EXCEEDED`.

Closure never truncates to satisfy a limit.

## 9. Post-closure validity and immutability

A future P3 projection implementation must validate the complete selected PEMS document under both exact bound PEMS/2 artifacts before claiming success.

Closure may select existing canonical records and relations. It must not repair them, rewrite proposition text, manufacture relations, infer supersession, change lifecycle state, reclassify provenance, mutate canonical state, or admit new knowledge.

The P1c fixture `tests/fixtures/context-packaging-p1c-closure-descriptor-identity.json` remains an identity-only P1c artifact and is not rewritten by P1d.

## 10. Independent conformance requirements

`tests/test_context_packaging_pems_closure_p1d.py` must mechanically establish at least:

- the exact schema and validator Git-blob identities have not drifted;
- independent schema walking discovers the complete reference-bearing surface and exactly matches descriptor field keys;
- `record.id` and `relation.id` are identity declarations rather than references;
- every rule is one of the three closed outcomes and only `include_transitively` may carry `target_namespace`;
- executable validator probes establish the grounded root-project, source-observation/source, provenance, and relation-endpoint namespaces;
- executable validator probes demonstrate the absence of namespace enforcement for every field listed in section 5 by accepting both record-ID and relation-ID values in otherwise-valid documents;
- every field in section 5 is an explicit `reject` rule with `UNDEFINED_CLOSURE_RULE` and no `target_namespace`;
- an unknown future ID-bearing field fails closed;
- omitting an otherwise supported grounded rule falls back to `UNDEFINED_CLOSURE_RULE`;
- known external locators remain inert;
- the derived-proposition structural rule is the only inverse relation discovery rule;
- the selected P0 pressure cases remain frozen;
- P1c remains unchanged and P1e plus later implementation/integration gates remain excluded.

The suite must not use the descriptor's own namespace labels as proof that those labels are correct. Passing this suite is evidence only for the P1d freeze. It is not evidence that P1e, P2, P3, COVE integration, production integration, reconciliation, admission, authorization, or activation exists or is authorized.
