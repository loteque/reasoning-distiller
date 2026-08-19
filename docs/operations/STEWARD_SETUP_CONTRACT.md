# Steward Setup and Authorization Contract

Status: **Normative v1 operational contract**

Contracts:

- `reasoning-distiller-steward-setup/1`
- `reasoning-distiller-steward-setup-result/1`
- `reasoning-distiller-steward-authorization/1`

## Purpose

The Steward Setup operation helps a consuming project establish an explicit, project-owned Steward authorization without allowing Reasoning Distiller installation, bootstrap, orchestration, or the generic Steward role definition to manufacture authority.

The reference primitive is:

```text
.reasoning-distiller/runtime/rd_steward_setup.py
```

The intended future public interface is:

```text
rd_init steward
```

`rd_init steward` may present this contract as an interactive setup wizard. The underlying authorization semantics remain identical.

## Core invariant

> The setup mechanism may persist Steward authority only as the direct expression of an explicit project-owner authorization decision. It MUST NOT infer, default, escalate, or silently grant authority.

Generic role availability is capability, not authority.

## Preconditions

The target project MUST already contain:

```text
.reasoning-distiller/
project-knowledge/project.json
```

The setup operation MUST NOT install the framework or bootstrap the project implicitly.

## Two-stage setup

Setup separates proposal from authorization:

```text
plan
  -> validate target and requested holder/scopes
  -> emit proposed authorization
  -> no project mutation

apply
  -> repeat validation
  -> require explicit confirmation token
  -> persist exact authorization once
```

Reference usage:

```bash
python .reasoning-distiller/runtime/rd_steward_setup.py plan \
  --target . \
  --authority-holder "project:steward-primary" \
  --scope semantic_reconciliation

python .reasoning-distiller/runtime/rd_steward_setup.py apply \
  --target . \
  --authority-holder "project:steward-primary" \
  --scope semantic_reconciliation \
  --confirm AUTHORIZE_STEWARD
```

No authority scope has a default value. At least one explicit scope is required.

## Initial scopes

V1 recognizes only:

- `semantic_reconciliation`
- `admission`

These scopes are independent. A project may authorize reconciliation without admission.

Unknown scopes fail closed.

## Persisted state

On successful `apply`, the operation creates:

```text
project-knowledge/governance/
└── steward-authorization.json
```

Canonical JSON semantic content:

```json
{
  "contract": "reasoning-distiller-steward-authorization/1",
  "role": "steward",
  "authority_holder": "project:steward-primary",
  "scopes": ["semantic_reconciliation"]
}
```

Scopes are sorted canonically. No timestamp is required for semantic identity.

The authorization record is project-owned governance state. It is not package-managed framework state and is not canonical PEMS/COVE knowledge.

## Explicit confirmation

`apply` MUST require the exact confirmation token:

```text
AUTHORIZE_STEWARD
```

Absence or mismatch MUST produce `CONFIRMATION_REQUIRED` with no mutation.

The confirmation token alone is insufficient: holder and scopes must also be supplied explicitly in the same operation.

Interactive UIs MAY use a human confirmation question instead of requiring the literal CLI token, but the resulting operation must record the same explicit holder/scopes and must not preselect authority scopes.

## Existing state

| State | Result |
|---|---|
| no authorization exists | write exact authorization; `PASS / CREATED` |
| exact same authorization exists | no mutation; `PASS / ALREADY_AUTHORIZED` |
| different authorization exists | `FAIL / AUTHORIZATION_CONFLICT` |
| governance path has wrong node type/symlink | `FAIL / PATH_CONFLICT` |

V1 does not edit, merge, revoke, or escalate existing authorization. Those require separate explicit governance operations.

## Result examples

Plan:

```json
{
  "contract": "reasoning-distiller-steward-setup-result/1",
  "status": "PASS",
  "outcome": "PLAN",
  "proposed_authorization": {
    "contract": "reasoning-distiller-steward-authorization/1",
    "role": "steward",
    "authority_holder": "project:steward-primary",
    "scopes": ["semantic_reconciliation"]
  }
}
```

Applied:

```json
{
  "contract": "reasoning-distiller-steward-setup-result/1",
  "status": "PASS",
  "outcome": "CREATED",
  "authorization_path": "project-knowledge/governance/steward-authorization.json"
}
```

## Authority boundaries

The setup operation has only narrow filesystem authority to persist an explicit owner authorization record.

It does not itself possess:

- semantic reconciliation authority;
- admission authority;
- PEMS/COVE mutation authority;
- authority to select the project owner;
- authority to expand scopes later.

The persisted record is evidence that the project has explicitly designated a holder and scopes. A Steward invocation must still prove that it is operating as the designated holder under project rules.

## Determinism and safety

For fixed target state, holder, scopes, and confirmation, the operation MUST produce the same semantic authorization or the same failure classification.

It MUST NOT:

- use network access;
- infer a holder from usernames, environment variables, repository ownership, or installed roles;
- default either authority scope;
- modify `.reasoning-distiller/`;
- create PEMS/COVE or canonical state;
- overwrite an existing different authorization;
- follow symlinks out of project-owned governance paths.

## Relationship to Steward reconciliation trial

The Steward Handoff/Reconciliation Trial may proceed only after a consuming project has a valid explicit Steward authorization whose scopes include `semantic_reconciliation`.

If `admission` is absent, reconciliation may produce a disposition but MUST stop before admission.
