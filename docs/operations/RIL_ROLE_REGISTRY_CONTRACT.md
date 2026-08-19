# RIL Role Registry Contract

Status: **Normative v1 primitive contract**

Implements architecture gate **R6** from `docs/design/RIL_ARCHITECTURE_SYNTHESIS.md`.

Contracts:

- `reasoning-distiller-role-registry/1`
- `reasoning-distiller-role-submission/1`

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

## Approval

Mutating role-registry proposals require explicit human approval from an active operator holding:

```text
rd:role_registry
```

Approval uses the common `reasoning-distiller-approval/1` contract and confirmation value:

```text
ROLE_REGISTRY_CHANGE
```

Agents may prepare proposals and relay approval artifacts but may not originate human approval.

## Apply

Apply MUST:

1. validate canonical submission and proposal semantics;
2. validate proposal/approval exact binding;
3. validate operator registry/history health;
4. require an active approving operator with `rd:role_registry`;
5. validate role registry/history/projection health;
6. persist immutable submission/proposal/approval evidence;
7. append exactly one role-registry mutation event;
8. deterministically update the current projection.

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

## Registry state

A project role entry records:

- canonical role definition;
- `status`: `available` or `disabled`;
- `origin`: `project`;
- `protected`: `false`;
- sorted `sources` provenance list.

The package-provided default Steward is `origin: package`, `protected: true`, `status: available`.

## Conformance gate

R6 PASS requires tests proving at least:

1. default Steward exists without an authority grant;
2. package role cannot be submitted, changed, scoped, or disabled;
3. plan is deterministic and mutation-free;
4. incremental ADD works only after valid human/operator approval;
5. identical incremental submission is `NO_CHANGE`;
6. changed role definition is approval-gated UPDATE;
7. disabled role may be explicitly re-enabled by a later submission;
8. scoped snapshot disables only absent project roles inside declared scope;
9. roles outside snapshot scope remain unchanged;
10. `rd:*` consumer capabilities are rejected;
11. forbidden Architect/RGP Engineer protocol-governance roles are rejected;
12. unauthorized/disabled approvers fail closed;
13. conflicting role or operator projection/history fails closed;
14. submission/proposal/approval evidence is preserved;
15. no Steward authorization, reconciliation, admission, PEMS, COVE, or canonical state is created.
