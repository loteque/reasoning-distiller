# RIL Orchestrator Composition Contract

Status: **R15 normative contract**

Contract: `reasoning-distiller-orchestrator-request/1`

Result contract: `reasoning-distiller-orchestrator-result/1`

## Purpose

R15 introduces a composition-only lifecycle orchestrator above the proven R1-R14 primitives. It is not a new authority domain and MUST NOT contain protocol, admission, reconciliation, approval, or registry semantics of its own.

The orchestrator exists so later UX adapters can issue one stable request shape while all substantive behavior remains in lower primitives.

## Request

A request is exactly:

```json
{
  "contract": "reasoning-distiller-orchestrator-request/1",
  "action": "STATUS",
  "arguments": {}
}
```

No extra request fields are permitted. Each action has an exact argument set. Unknown actions or argument fields fail closed.

## Composition rules

1. The orchestrator MUST delegate to an existing R1-R14 primitive.
2. It MUST NOT synthesize approvals, activation evidence, role identities, operator identities, reconciliation assessments, admission plans, or recovery evidence.
3. It MUST NOT infer missing arguments from project state.
4. It MUST NOT reinterpret a lower primitive result.
5. Mutations, when requested, occur only inside the delegated primitive.
6. Read-only delegated actions remain read-only.
7. The orchestrator MAY wrap a lower result with routing metadata, but the delegated result MUST be preserved exactly under `result`.
8. The orchestrator itself creates no durable project artifact.

## Actions

R15 exposes composition routes for lifecycle inspection and the primitive families needed by the future CLI/agent adapters:

- `STATUS` -> R9 `classify_status`
- `VERIFY_STORAGE` -> R14 `verify_storage`
- `REPAIR_ALL` / `REPAIR_DOMAIN` -> R10 ordinary repair
- `RECONCILE` -> R12 reconciliation
- `ADMIT` -> R13 admission
- initial-operator plan/approve/apply -> R4
- operator-management plan/approve/apply -> R5
- root-transfer plan/approve/apply -> R5
- role-submission plan/approve/apply -> R6
- Steward-authorization plan/approve/apply -> R7

The orchestrator does not collapse plan/approve/apply ceremonies into one action.

## Result

Every accepted route returns:

```json
{
  "contract": "reasoning-distiller-orchestrator-result/1",
  "status": "PASS",
  "action": "STATUS",
  "primitive": "ril_status.classify_status",
  "result": {}
}
```

Routing/validation failures return `status: FAIL`, an `outcome`, and optional `detail`. Lower primitive PASS/FAIL remains inside `result`; orchestrator routing success does not turn a delegated failure into success semantically.

## Conformance gate

R15 passes only if tests prove:

- exact request/argument validation;
- unknown action rejection;
- exact lower-result preservation;
- no default authority/evidence synthesis;
- no hidden mutation for read-only routes;
- mutation routes call only the selected primitive once;
- plan/approve/apply remain separate;
- storage verification remains downstream of admission rather than folded into it.
