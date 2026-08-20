# Rupi R6 Primitive Amendment

Status: Normative amendment for R6 implementation

## Purpose

R6 exposed one interface-shape gap in the accepted installer recovery primitive.

`rd_install.recover_interrupted_transaction()` is already the sole accepted mutation primitive for interrupted installer recovery. It predates the common Reasoning Distiller result convention and reports successful outcomes directly in its `status` field, for example `RESTORED_PREVIOUS`, `RESTORED_EMPTY`, `COMMIT_FINALIZED`, or `CLEAN`.

The accepted Rupi checkpoint contract requires a successful consequential action to be backed by a primitive result with `status = PASS`. Rupi MUST NOT privately reinterpret a legacy result as success.

## Amendment

Add the shared orchestration surface:

`rd_install_recovery.recover_install_transaction`

This surface:

1. receives the accepted recovery primitive as a callable;
2. invokes it exactly once;
3. performs no journal inspection, transition selection, filesystem recovery, rollback, or installer mutation itself;
4. treats a normal primitive return as a successful invocation and preserves the primitive's original `status` value as `outcome`;
5. preserves the raw primitive result as `primitive_result`;
6. returns `reasoning-distiller-install-recovery-result/1` with `status = PASS`;
7. propagates recovery primitive exceptions rather than inventing alternate recovery behavior.

The Rupi action `recover_install_transaction` is therefore mapped to this shared orchestration surface, whose only consequential effect is the one delegated call to `rd_install.recover_interrupted_transaction()`.

## Non-duplication proof obligation

The shared adapter MUST NOT contain installer recovery semantics such as journal parsing, backup selection, managed-root replacement, restoration ordering, or transaction cleanup. Those semantics remain exclusively in `rd_install.recover_interrupted_transaction()`.

## R6 ordering invariant

When transition planning reports `RECOVERY_REQUIRED`, Rupi MUST:

```text
require bounded recovery intent
→ invoke recover_install_transaction
→ require PASS normalized result
→ re-run plan_installation_transition
→ only then consider install_or_update
```

A pre-recovery plan is observational only and can never authorize or select the post-recovery transition.

## Authority boundary

This amendment creates no semantic authority, operator authority, Steward authority, activation, reconciliation, admission, or Canon mutation semantics.
