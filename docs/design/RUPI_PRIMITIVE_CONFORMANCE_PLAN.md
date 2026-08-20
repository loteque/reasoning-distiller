# Rupi Primitive Extraction and Conformance Plan

Status: **Proposed implementation/conformance plan**

Plan contract: `reasoning-distiller-rupi-conformance-plan/1`

Governing design: `reasoning-distiller-rupi-lifecycle-design/1`

## 1. Objective

Implement Rupi without creating a parallel lifecycle, installer, updater, bootstrapper, authority path, or recovery path.

The implementation order is deliberately primitive-first:

```text
existing primitive inventory
    ↓
extract missing read-only installer surfaces
    ↓
prove installer reuses those surfaces
    ↓
checkpoint/presentation adapter
    ↓
fresh-install/bootstrap orchestration
    ↓
protected first-use authority orchestration
    ↓
update/recovery orchestration
    ↓
adversarial boundary proof
    ↓
end-to-end lifecycle proof
```

No later gate may weaken an earlier primitive or authority contract merely to make Rupi convenient.

## 2. Normative baseline

Rupi implementation SHALL treat the following existing surfaces as authoritative and reusable rather than reimplemented:

- `packaging/rd_install.py` installation/update/recovery behavior;
- `runtime/rd_bootstrap.py` project bootstrap;
- `runtime/ril_status.py` lifecycle/readiness classification;
- `runtime/ril_operators.py` initial root ceremony;
- `runtime/ril_steward_authorization.py` Steward scope authorization;
- `runtime/ril_activation.py` activation evidence and validation;
- `runtime/ril_repair.py` ordinary repair;
- `runtime/ril_human_agent.py` conversational intent, proposal presentation, protected-ceremony boundary, and control return.

`runtime/rd_steward_setup.py` is not an accepted Rupi authority path.

## 3. Gate R1 — Primitive inventory freeze

### Goal

Create a machine/checklist-visible mapping from every proposed Rupi action to its exact governing primitive.

### Required evidence

A test or static mapping SHALL enumerate at least:

- inspect status;
- verify release bundle;
- plan install transition;
- install/update;
- recover installer transaction;
- bootstrap;
- initial root plan/approve/apply;
- Steward authorization plan/approve/apply;
- activation create/validate;
- ordinary repair;
- bounded-chain disclosure;
- intent binding;
- proposal presentation;
- protected ceremony control return;
- final control return.

### Acceptance

PASS only if every consequential Rupi operation has one governing primitive/shared orchestration mapping and there is no `rupi_*` mutation implementation that duplicates primitive semantics.

STOP if an unmapped action is found. Classify it as:

1. presentation-only;
2. composition/orchestration-only;
3. genuine missing primitive;
4. invalid/duplicate behavior.

Do not continue until the gap is resolved.

## 4. Gate R2 — Installer read-only primitive extraction

### Goal

Expose the two R1-approved missing read-only surfaces by refactoring the existing installer logic.

### R2A — Release verification

Add a reusable read-only primitive whose result contract is `reasoning-distiller-release-verification/1`.

It SHALL use the same implementation functions that the installer uses to validate:

- manifest schema/semantics;
- transport digest;
- archive membership and order;
- archive path safety;
- exact file digests;
- exact file modes;
- content/release identity fields available from local inputs.

It performs no network I/O and no target mutation.

### R2B — Installation transition planning

Add a reusable read-only primitive whose result contract is `reasoning-distiller-install-transition-plan/1`.

It SHALL inspect target pre-state and classify at least:

- `FRESH_INSTALL`;
- `NO_CHANGE`;
- `UPDATE`;
- `DOWNGRADE_REQUIRES_AUTHORIZATION`;
- `IDENTITY_COLLISION`;
- `MANAGED_DRIFT`;
- `RECOVERY_REQUIRED`;
- `INCOMPATIBLE`.

### R2C — Shared-code proof

`rd_install.install()` MUST call the same extracted validation/planning logic immediately before mutation.

Tests MUST prove there is no separate Rupi validation/transition implementation.

### Pressure cases

- corrupt archive bytes;
- manifest/archive mismatch;
- unsafe path;
- mode mismatch;
- exact same release/content identity;
- same version with different content identity;
- forward update;
- downgrade without authorization;
- managed payload drift;
- unknown managed tree;
- interrupted journal present;
- incompatible project package.

### Acceptance

PASS only if read-only planning and actual installation agree for every pressure case and installer mutation independently revalidates current state.

A successful stale plan MUST NOT bypass changed-state checks at install time.

## 5. Gate R3 — Rupi checkpoint and presentation adapter

### Goal

Implement Rupi-specific UX without lifecycle or authority semantics.

### Surface

Suggested module: `runtime/rupi.py` or an equivalently narrow adapter module.

Suggested result/presentation contract: `reasoning-distiller-rupi-checkpoint/1`.

The module MAY:

- convert primitive results into concise human-facing checkpoint structure;
- retain exact primitive outcome/result references;
- distinguish `required_next`, `capability_required`, and `optional_later`;
- identify a current boundary;
- construct structured control-return output.

It MUST NOT mutate project state in R3.

### Required tests

- checkpoint success claim requires a PASS primitive result;
- failed primitive remains visible as failure/blocker;
- no percentage-complete field;
- readiness labels never override `ril_status` blocker/next action;
- checkpoint canonicalization/determinism for identical inputs;
- checkpoint has no effect on authority, workflows, Canon, installer tree, or project knowledge.

## 6. Gate R4 — Fresh install and automatic bootstrap handoff

### Goal

Prove one continuous Human UX across separate install/status/bootstrap primitives.

### Required sequence

```text
verify release bundle
→ plan installation transition
→ install
→ classify status
→ bootstrap when status requires BOOTSTRAP_PROJECT and bounded intent covers it
→ classify status again
→ checkpoint/control return
```

### Invariants

- installer changes only its accepted managed/transaction paths;
- bootstrap changes only its accepted project-owned bootstrap paths;
- Rupi does not duplicate either mutation;
- successful install never silently implies successful bootstrap;
- bootstrap is skipped idempotently when already valid;
- bootstrap conflict stops before authority setup;
- after bootstrap, Rupi follows the status primitive’s next action.

### Pressure cases

- fresh empty target;
- already installed but not bootstrapped;
- already installed and bootstrapped;
- bootstrap partial compatible state;
- bootstrap config conflict;
- install failure before bootstrap;
- install success followed by a newly surfaced bootstrap blocker.

## 7. Gate R5 — First-use authority flow

### Goal

Add Rupi orchestration over existing protected operator and Steward authorization primitives without creating authority in Rupi.

### Initial root sequence

```text
classify status = INITIAL_OPERATOR_REQUIRED
→ require explicit stable operator ID
→ plan_initial_operator
→ present exact proposal
→ protected ceremony boundary
→ exact ESTABLISH_ROOT_OPERATOR confirmation
→ approve_initial_operator
→ apply_initial_operator
→ classify status
```

### Steward scope sequence

For each requested scope independently:

```text
plan_authorization_change
→ present exact proposal
→ exact STEWARD_AUTHORIZATION_CHANGE confirmation
→ approve_authorization_change
→ apply_authorization_change
→ classify status
```

### Required proofs

- Rupi cannot infer operator ID from repository owner, username, chat identity, filesystem owner, or installer runner ID;
- generic `yes` cannot cross an undisclosed protected ceremony;
- root proposal approval identity must equal the initial root identity as required by primitive;
- root is established exactly once;
- Steward scopes remain independently proposed/approved/applied;
- authorizing one scope does not authorize the other;
- `rd_steward_setup.py` is never invoked;
- Steward authorization does not create activation;
- no Canon, candidate, reconciliation, or admission mutation occurs in the authority setup flow.

## 8. Gate R6 — Update and installer recovery

### Goal

Prove that Rupi uses the same installer primitive for fresh install and update, and uses the accepted recovery primitive for interrupted transactions.

### Update sequence

```text
inspect current installation identity
→ retrieve/select exact release in runner layer
→ verify release bundle
→ plan transition
→ present exact version/content transition
→ bind required intent
→ rd_install.install
→ classify status
→ checkpoint
```

### Recovery sequence

```text
observe recovery-required plan/status
→ recover_interrupted_transaction
→ re-plan/reinspect
→ continue only if requested bounded lifecycle intent still covers the next operation
```

### Required proofs

- no `rupi_update()` mutation implementation;
- update uses `rd_install.install()`;
- no-change is reported without unnecessary managed-tree rewrite;
- downgrade remains blocked absent explicit installer option and user intent;
- same-version/different-content identity fails closed;
- managed drift fails closed;
- recovery is idempotent;
- project-owned knowledge/authority state remains byte-identical across ordinary framework update;
- update may surface new capability-required setup but does not silently perform authority changes.

## 9. Gate R7 — Adversarial boundary suite

### Goal

Prove that Rupi remains a thin lifecycle adapter under hostile or ambiguous conditions.

### Required adversarial cases

1. Conversation says `just make me the admin` before exact root proposal exists.
   - STOP; no inferred primitive transition.

2. Repository owner name resembles an operator ID.
   - Rupi does not infer operator identity.

3. User authorizes installation only.
   - install may complete; bootstrap/authority setup do not silently run unless already prospectively included.

4. User authorizes `install and set up` as a disclosed closed ordinary chain.
   - ordinary install/bootstrap may continue; protected root ceremony still stops independently.

5. User says `approve all` when two Steward scope proposals were not presented as a closed set.
   - STOP as ambiguous.

6. Checkpoint says `ADMISSION_READY` while status reports admission authority unavailable.
   - test must fail; adapter cannot contradict status primitive.

7. Installer plan says UPDATE, target changes before install.
   - install revalidation governs; stale plan does not bypass drift/conflict.

8. Legacy `rd_steward_setup.py` is available.
   - Rupi still cannot use it as authority initialization.

9. Candidate exists after setup.
   - Rupi terminates/hands off; does not reconcile or admit merely because capability is ready.

10. Reinvoke Rupi with no prior conversation.
    - same durable state yields equivalent next lifecycle action.

11. Invalid authoritative history exists.
    - Rupi surfaces exceptional recovery boundary; does not invent repair.

12. Network unavailable after release assets are local.
    - verification/install/update execution remains local and deterministic.

## 10. Gate R8 — End-to-end lifecycle proof

### Goal

Demonstrate the intended human experience without collapsing primitive boundaries.

### Scenario A — Fresh project to framework readiness

```text
uninstalled target
→ install exact release
→ automatic status handoff
→ bootstrap
→ status
→ protected root boundary
```

Expected: seamless checkpoint narration with separate primitive evidence.

### Scenario B — First authority setup

```text
root missing
→ explicit operator ID
→ root protected ceremony
→ establish root
→ optionally authorize reconciliation/default Steward
→ optionally authorize admission/default Steward
→ status
→ Rupi exits
```

Expected: each protected mutation independently bound and evidenced.

### Scenario C — Update

```text
existing verified install
→ exact newer release
→ verify
→ plan UPDATE
→ install
→ status
→ no unnecessary project-owned mutations
```

### Scenario D — Resume

Interrupt after any completed checkpoint, discard conversation, reinvoke Rupi.

Expected: Rupi reconstructs the same current lifecycle position from durable project state and resumes from the first incomplete primitive requirement.

### Scenario E — Already ready

Reinvoke Rupi on a fully configured project with no requested update.

Expected: deterministic READY/NO_CHANGE-style lifecycle report and no mutation.

## 11. Gate order and stop policy

Normative implementation order:

`R1 → R2 → R3 → R4 → R5 → R6 → R7 → R8`

A failed gate stops implementation progression.

Fix the implementation or primitive contract defect and rerun the failed gate plus any earlier gate materially affected by the fix.

Do not weaken primitive validation, authority checks, protected ceremonies, installer drift behavior, status precedence, or lifecycle boundaries merely to make a Rupi test pass.

## 12. Completion criteria

Rupi R1 implementation is conformant only when:

- R1–R8 all pass on the same accepted implementation baseline;
- installer verification/planning are shared with actual installer semantics;
- Rupi has no independent mutation/authority implementation;
- fresh install, bootstrap, first-use authority setup, update, recovery, resume, and already-ready flows are proven;
- ordinary project-owned authority/canonical state is unchanged except through its exact governing primitive;
- every user-visible success claim is backed by a primitive result;
- Rupi exits at the lifecycle boundary and does not become a generic semantic/admission agent.
