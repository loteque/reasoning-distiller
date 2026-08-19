# RIL Role Registry Contract

Status: **Normative v1 primitive contract — amended for R17 authority grants**

Implements architecture gate **R6** from `docs/design/RIL_ARCHITECTURE_SYNTHESIS.md`.

Contracts:

- `reasoning-distiller-role-registry/1`
- `reasoning-distiller-role-submission/1`
- common `reasoning-distiller-proposal/1`
- common `reasoning-distiller-approval/1|2`

Depends on accepted R17 `reasoning-distiller-authority-grant/1` for bounded delegated approval.

## Purpose

Provide a deterministic project-owned registry of durable role definitions that may later be selected for authority.

Registry membership grants no Steward, reconciliation, admission, protocol-governance, or invocation authority.

## Default package role

A valid registry always begins from this package-owned semantic state:

```text
steward:default
```

The default Steward is:

- package-provided;
- always available;
- immutable to consumer role mutations;
- excluded from operating-entity submissions;
- excluded from snapshot scope/disable semantics;
- never authorized merely by being registered.

## Project role identity

Project roles are durable role definitions with project-global `role_id` values. Ephemeral chats, agent runs, or role instances are not registry identities.

A project role definition contains:

```json
{
  "role_id": "gameplay-engineer",
  "title": "Gameplay Engineer",
  "description": "Implements gameplay systems.",
  "capabilities": ["project:gameplay"]
}
```

Consumer submissions MUST NOT claim `rd:*` capabilities. Package protocol-governance capability is not consumer-extensible.

Consumer-side Architect and RGP Engineer protocol-governance roles are forbidden. v1 rejects the reserved role identities/titles `architect`, `project-architect`, `rgp-engineer`, and `reasoning-graph-protocol-engineer` (and matching reserved titles). Equivalent protocol-governance authority remains forbidden regardless of name.

## Submission

An operating entity submits a canonical artifact:

```json
{
  "contract": "reasoning-distiller-role-submission/1",
  "mode": "incremental",
  "source": "active-chat",
  "scope": null,
  "roles": []
}
```

or:

```json
{
  "contract": "reasoning-distiller-role-submission/1",
  "mode": "snapshot",
  "source": "active-chat",
  "scope": {"role_ids": ["gameplay-engineer", "qa-engineer"]},
  "roles": []
}
```

`incremental` submissions do not affect absent roles.

`snapshot` submissions MUST declare an explicit `role_ids` scope. Present role IDs MUST be within that scope. Absent project roles in the declared scope are proposed for disable. Package-provided role IDs are forbidden in both submission roles and snapshot scope.

## Planning

Planning is mutation-free and classifies the exact required transition:

```text
unknown submitted role            → ADD
same available definition/source  → NO_CHANGE
changed definition/source         → UPDATE
same disabled role reappears      → REENABLE
changed disabled role reappears   → UPDATE (available result)
absent available scoped role      → DISABLE
```

Mutating classifications are collected into one atomic proposal bound to the current registry digest.

If no mutations are required, planning returns `PASS/NO_CHANGE` and no approval is needed.

## R17 grant-matching schema

Role-registry mutation is the first R1-R7 administrative operation class explicitly declared grant-delegable.

Canonical delegation metadata:

```text
operation_class: role-registry.change
delegable: true
```

The authority-relevant target view of an exact proposal is derived deterministically from its complete atomic change set:

```text
role_ids
  = sorted unique set of every project role_id added, updated,
    disabled, or reenabled by the proposal

mutation_kinds
  = sorted unique subset of [ADD, UPDATE, DISABLE, REENABLE]

submission_mode
  = incremental | snapshot
```

Package-provided roles and forbidden protocol-governance roles are never valid grant targets because they remain invalid proposal targets under this contract.

Supported R17 target selectors:

```text
field: role_id
match: exact | one-of
```

A selector over `role_id` must cover **every** member of the proposal's derived `role_ids` set. A proposal affecting any unlisted role is `OUTSIDE_GRANT`.

Supported R17 constraints:

```text
field: mutation_kinds
predicate: subset-of
value: <finite subset of ADD|UPDATE|DISABLE|REENABLE>

field: role_ids
predicate: max-count
value: <positive integer>

field: submission_mode
predicate: eq | one-of
value/values: incremental|snapshot
```

No other proposal field or predicate is authority-grant-matchable in v1. Unsupported selectors/constraints fail closed.

The grant validator evaluates the complete atomic role-registry proposal. It MUST NOT split a proposal into grant-covered and non-covered mutations, rewrite the proposal, or infer that a role is equivalent to another role.

An authority grant does not waive the existing prohibition on `rd:*` consumer capabilities or forbidden Architect/RGP Engineer governance roles.

## Approval

Mutating role-registry proposals require a valid exact approval. Two authority bases are accepted:

1. direct human approval from an active operator holding `rd:role_registry`; or
2. a valid R17 grant-derived `reasoning-distiller-approval/2` issued for `operation_class: role-registry.change` under an ACTIVE workflow-bound authority grant whose grantor was authorized to establish that prospective authority.

Direct approval uses confirmation value:

```text
ROLE_REGISTRY_CHANGE
```

For direct approval, the approving operator MUST be active and hold `rd:role_registry`.

For grant creation that includes `role-registry.change`, the grant-creation primitive MUST establish that the authenticated grantor is active and holds `rd:role_registry` at grant creation. Grant use later does not turn an agent into that operator and does not bypass any proposal/state validation.

Agents may prepare proposals and request deterministic grant evaluation but may not originate direct human approval or expand grant scope.

## Apply

Apply MUST:

1. validate canonical submission and proposal semantics;
2. validate proposal/approval exact binding;
3. validate the approval authority basis under the common mutation substrate;
4. validate operator registry/history health;
5. for direct approval, require an active approving operator with `rd:role_registry`;
6. for grant-derived approval, validate the immutable grant issuance evidence and this contract's delegability declaration;
7. validate role registry/history/projection health;
8. persist immutable submission/proposal/approval evidence;
9. append exactly one role-registry mutation event;
10. deterministically update the current projection.

Apply-time proposal basis/current-state validation remains mandatory regardless of approval authority basis.

Retry with the same already-consumed approval follows the common mutation substrate semantics.

## Storage

Project-owned role state:

```text
project-knowledge/roles/
├── events/
├── current.json
├── submissions/
├── proposals/
└── approvals/
```

Evidence filenames use the canonical artifact SHA-256 hex payload and `.json`. Existing evidence bytes MUST match exactly; conflicting same-name evidence fails closed.

Authority-grant definitions/events remain owned by the R17 grant primitive rather than the role registry.

## Registry state

A project role entry records:

- canonical role definition;
- `status`: `available` or `disabled`;
- `origin`: `project`;
- `protected`: `false`;
- sorted `sources` provenance list.

The package-provided default Steward is `origin: package`, `protected: true`, `status: available`.

## R17 non-authority boundary

Grant-delegable role-registry mutation means only that a human operator with `rd:role_registry` may prospectively authorize a deterministic bounded subset of otherwise ordinary role-registry changes inside one immutable workflow.

It does not permit an authority grant to:

- create `rd:*` capabilities;
- create or assign Steward authority;
- create protected/package roles;
- mutate authority grants;
- expand workflow scope;
- reinterpret a proposal beyond the published grant-matching schema.

## Conformance gate

R6/R17 PASS requires tests proving at least:

1. default Steward exists without an authority grant;
2. package role cannot be submitted, changed, scoped, or disabled;
3. plan is deterministic and mutation-free;
4. direct incremental ADD works only after valid operator approval;
5. identical incremental submission is `NO_CHANGE`;
6. changed role definition is approval-gated UPDATE;
7. disabled role may be explicitly re-enabled by a later submission;
8. scoped snapshot disables only absent project roles inside declared scope;
9. roles outside snapshot scope remain unchanged;
10. `rd:*` consumer capabilities are rejected;
11. forbidden Architect/RGP Engineer protocol-governance roles are rejected;
12. unauthorized/disabled direct approvers fail closed;
13. a valid bounded `role-registry.change` authority grant may issue exact grant-derived approval without fresh proposal-specific assent;
14. a proposal touching one ungranted role is wholly `OUTSIDE_GRANT` rather than partially applied;
15. unsupported grant predicates fail closed;
16. grant-derived approval cannot bypass stale proposal basis or conflicting role/operator history;
17. conflicting role or operator projection/history fails closed;
18. submission/proposal/approval evidence is preserved;
19. no Steward authorization, reconciliation, admission, PEMS, COVE, or canonical state is created.
