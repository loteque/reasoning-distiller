# Rupi Lifecycle Agent Design Contract

Status: **Proposed normative design contract**

Contract: `reasoning-distiller-rupi-lifecycle-design/1`

Depends on:

- `reasoning-distiller-ril-human-agent-design/1`;
- `reasoning-distiller-installer/1`;
- `reasoning-distiller-project-bootstrap-result/1`;
- accepted RIL operator, role, Steward-authorization, activation, status, repair, workflow, and shared-orchestration contracts.

Implementation status: **not authorized by this design artifact alone.** Implementation follows `RUPI_PRIMITIVE_CONFORMANCE_PLAN.md`.

## 1. Purpose

Rupi is the ephemeral Human ↔ Agent lifecycle adapter for installing, configuring, updating, recovering, and checking the readiness of Reasoning Distiller in a project.

Rupi exists to make Reasoning Distiller lifecycle operations feel like one continuous guided experience while preserving the accepted primitive-first architecture.

Rupi is not a Steward, operator, authority holder, installer implementation, semantic agent, admission agent, or durable project role.

The name `Rupi` is the product name. Possible acronym expansions are informal only and carry no contract meaning.

## 2. Primitive-first governing rule

Every consequential Rupi action MUST map to exactly one accepted deterministic primitive or one accepted shared-orchestration operation.

Rupi MAY:

- inspect primitive results;
- explain project state;
- identify blockers;
- prepare and present exact primitive inputs or proposals;
- bind narrow Human ↔ Agent intent under the accepted Human ↔ Agent contract;
- invoke an accepted primitive after its authority and preconditions are satisfied;
- sequence already accepted primitives into a prospectively disclosed bounded lifecycle flow;
- produce non-authoritative progress/checkpoint presentations;
- return control to the normal Reasoning Distiller interaction surface.

Rupi MUST NOT:

- implement an alternate version of a primitive;
- reproduce part of a primitive in adapter logic in order to make a decision that belongs to the primitive;
- infer authority from project state, conversation, repository ownership, installation ownership, or agent identity;
- merge multiple protected authority operations into one hidden action;
- create semantic authority, admission authority, operator authority, Steward authorization, or activation by implication;
- mutate canonical knowledge as lifecycle setup work;
- treat a progress presentation as normative evidence or authority;
- silently continue across a protected ceremony or materiality boundary.

If a desired Rupi action has no existing primitive mapping, implementation MUST stop and classify the gap before adding adapter behavior.

A new primitive is allowed only when it supplies genuinely missing semantics and does not duplicate an accepted primitive. If the missing behavior is a proper subset/refactoring of behavior already implemented inside a primitive, the existing primitive SHOULD be refactored to expose the missing reusable surface while preserving its existing API and governance semantics where practical.

## 3. Ephemeral lifecycle

Rupi has no durable agent identity or durable authority state.

A Rupi invocation starts by reconstructing current project state from accepted primitive surfaces. It ends when:

- the requested lifecycle objective is satisfied;
- the next step requires a Human authority ceremony or new intent not yet supplied;
- an accepted primitive reports a blocker;
- material information requires interruption;
- the work crosses out of lifecycle management into normal Reasoning Distiller semantic or admission processing.

Reinvoking Rupi MUST resume from authoritative project state, not from chat memory or a Rupi-private progress file.

## 4. Lifecycle truth

Rupi MUST NOT implement its own authoritative lifecycle state machine.

When Reasoning Distiller is installed sufficiently for the status primitive to run, Rupi SHALL use `ril_status.classify_status(project_root)` as the authoritative lifecycle/readiness classification surface.

Rupi MAY map status outcomes into human-friendly wording, but it MUST NOT change the meaning, precedence, blocker, or required next action returned by the status primitive.

Before installation, when installed runtime status is not available, Rupi MAY use narrowly bounded runner observations necessary to locate a target and selected release. Those observations do not become project lifecycle authority.

After every successful consequential lifecycle mutation, Rupi SHOULD re-run the status primitive before deciding the next lifecycle step.

## 5. Existing primitive mapping

The following mappings are normative for Rupi R1.

| Lifecycle action | Governing primitive/surface | Rupi authority |
| --- | --- | --- |
| classify installed/project readiness | `ril_status.classify_status()` | read-only presentation |
| install verified package | `rd_install.install()` | none beyond disclosed invocation intent |
| update verified package | `rd_install.install()` | same installer primitive; no separate updater |
| recover interrupted install transaction | `recover_interrupted_transaction()` | none beyond disclosed recovery intent |
| bootstrap project-owned RD state | `rd_bootstrap.bootstrap()` | none beyond disclosed bootstrap intent |
| plan initial protected root | `plan_initial_operator()` | non-authoritative proposal preparation |
| approve initial protected root | `approve_initial_operator()` | exact Human protected ceremony required |
| establish initial protected root | `apply_initial_operator()` | primitive-governed mutation |
| plan Steward scope assignment | `plan_authorization_change()` | non-authoritative proposal preparation |
| approve Steward scope assignment | `approve_authorization_change()` | exact Human confirmation required |
| apply Steward scope assignment | `apply_authorization_change()` | primitive-governed mutation |
| create explicit invocation activation | `make_explicit_activation()` | creates evidence, not authorization |
| validate activation | `validate_activation()` | read-only validation |
| ordinary projection repair | `ril_repair.repair_domain()` / `repair_all()` | primitive-governed repair only |
| bind conversational intent | `ril_human_agent.bind_contextual_intent()` | no independent authority |
| disclose bounded chain | `ril_human_agent.disclose_bounded_chain()` | presentation only |
| present exact proposal | `ril_human_agent.present_proposal()` | presentation only |
| protected ceremony stop | `ril_human_agent.protected_ceremony_boundary()` | mandatory control return |
| structured final handoff | `ril_human_agent.control_return()` | presentation only |

Rupi MUST NOT call `rd_steward_setup.py` for current RIL authority initialization. Current RIL status and activation semantics are governed by the event-sourced Steward authorization primitives. The legacy setup utility is not a substitute authority path.

## 6. Missing primitive surfaces permitted for R1

R1 permits exactly two installer-related primitive extraction/refactoring gaps before Rupi implementation.

### 6.1 Verified release bundle

A read-only reusable primitive SHALL expose the installer’s existing release validation behavior without duplicating it.

Suggested contract: `reasoning-distiller-release-verification/1`.

It SHALL validate, using the same underlying code used by installation:

- manifest schema and semantics;
- exact archive transport SHA-256;
- manifest/archive file-set equality;
- archive path safety;
- file modes;
- file digests;
- release version/source/content identity coherence available from the supplied bundle.

It MUST perform no installation mutation and no network I/O.

Rupi MUST NOT independently reproduce these checks.

### 6.2 Installation transition plan

A read-only reusable primitive SHALL expose the installer’s existing pre-mutation transition classification.

Suggested contract: `reasoning-distiller-install-transition-plan/1`.

It SHALL classify at least:

- `FRESH_INSTALL`;
- `NO_CHANGE`;
- `UPDATE`;
- `DOWNGRADE_REQUIRES_AUTHORIZATION`;
- `IDENTITY_COLLISION`;
- `MANAGED_DRIFT`;
- `RECOVERY_REQUIRED`;
- `INCOMPATIBLE`.

The final installer mutation MUST use the same underlying preflight/transition logic immediately before mutation. Rupi MUST NOT treat a stale plan as permission to bypass installer revalidation.

This planning primitive creates execution visibility, not authority.

## 7. Continuous install → bootstrap handoff

The Human UX SHOULD present installation and initial project setup as one continuous experience.

The primitive architecture MUST remain separated.

Canonical flow:

```text
verified release bundle
    ↓
installation transition plan
    ↓
rd_install.install
    ↓
ril_status.classify_status
    ↓
BOOTSTRAP_PROJECT if required
    ↓
rd_bootstrap.bootstrap
    ↓
ril_status.classify_status
    ↓
ESTABLISH_INITIAL_OPERATOR if required for requested capability
    ↓
protected authority ceremony
```

`rd_install.py` MUST NOT bootstrap project-owned state.

`rd_bootstrap.bootstrap()` MUST NOT create operator, Steward, activation, semantic, admission, or canonical state.

The continuity belongs to Rupi presentation/orchestration, not to collapsed primitive semantics.

## 8. Requested lifecycle goal

Rupi MUST distinguish the user’s requested lifecycle goal from all possible future Reasoning Distiller capabilities.

Examples include:

- install framework only;
- install and bootstrap project;
- complete first-use authority setup;
- make reconciliation capability ready;
- make admission capability ready;
- update to an exact release;
- recover an interrupted installation;
- inspect lifecycle readiness.

A step MAY be globally useful without being required for the currently requested goal.

Rupi MUST label future steps as one of:

- `required_next`: required to satisfy the current requested lifecycle goal;
- `capability_required`: required before a named optional/future capability can be used;
- `optional_later`: useful but not currently required.

Rupi MUST NOT present every possible authority configuration as mandatory installation work.

## 9. Readiness vocabulary

Rupi presentation MAY use the following non-authoritative readiness labels when directly derived from primitive results:

- `FRAMEWORK_INSTALLED`;
- `PROJECT_BOOTSTRAPPED`;
- `AUTHORITY_INITIALIZED`;
- `RECONCILIATION_READY`;
- `ADMISSION_READY`;
- `READY` for the explicitly requested lifecycle goal.

These labels MUST NOT replace or override the accepted `ril_status` lifecycle and blocker values.

In particular, `FRAMEWORK_INSTALLED` MUST NOT be presented as equivalent to full project readiness.

## 10. Rupi checkpoint presentation

Rupi SHALL provide concise progress visibility after meaningful lifecycle checkpoints.

Suggested presentation contract: `reasoning-distiller-rupi-checkpoint/1`.

A checkpoint is non-authoritative and SHOULD contain:

- requested lifecycle goal;
- completed operations, each identified by its primitive/result;
- current primitive-derived lifecycle/readiness summary;
- exactly identified required next action when one exists;
- capability-required future steps;
- optional later steps;
- active Human/authority/materiality boundary, if any;
- durable artifacts created by the underlying primitives;
- operations not completed.

A checkpoint MUST NOT:

- claim authority;
- create workflow intent by itself;
- claim an operation succeeded without the governing primitive result;
- manufacture percentage-complete progress;
- hide a blocker behind a generic success message.

Preferred human presentation is compact, for example:

```text
Completed
  Reasoning Distiller vX.Y.Z installed and verified.

Required next
  Bootstrap Reasoning Distiller project state.

Optional later
  Configure reconciliation authority.

Boundary
  None. Rupi can continue within the disclosed setup chain.
```

## 11. Bounded chaining and conversational intent

Rupi inherits the accepted Human ↔ Agent bounded-chain semantics.

A user request such as `install and set up Reasoning Distiller` MAY be converted into a proposed bounded lifecycle chain only after Rupi makes the chain explicit.

One affirmation MAY bind an explicitly disclosed closed set of ordinary lifecycle operations when the Human ↔ Agent contract permits it.

Protected ceremonies remain independently required even when their existence was prospectively disclosed.

Rupi MUST NOT infer:

- initial operator identity;
- root-operator establishment confirmation;
- Steward assignment target;
- Steward authorization confirmation;
- downgrade authorization;
- materiality acknowledgement;
- admission or reconciliation semantic decisions.

## 12. First-use authority setup

Rupi SHALL guide first-use authority initialization through the existing RIL primitives.

### 12.1 Initial root

```text
status: INITIAL_OPERATOR_REQUIRED
    ↓
collect explicit stable operator ID
    ↓
plan_initial_operator
    ↓
present exact immutable proposal
    ↓
protected ceremony: ESTABLISH_ROOT_OPERATOR
    ↓
approve_initial_operator
    ↓
apply_initial_operator
    ↓
status
```

The approving Human identity MUST satisfy the governing initial-operator primitive. Rupi cannot infer or substitute it.

### 12.2 Steward scopes

Each requested Steward scope remains its own primitive transition:

```text
plan_authorization_change
    ↓
present exact proposal
    ↓
Human confirmation: STEWARD_AUTHORIZATION_CHANGE
    ↓
approve_authorization_change
    ↓
apply_authorization_change
    ↓
status
```

`semantic_reconciliation` and `admission` MAY both be prospectively disclosed as a closed setup goal, but each scope receives its own proposal, approval, and apply result.

Steward authorization does not create activation.

## 13. Installation and update

Fresh installation and update use the same deterministic installer primitive.

Rupi MUST NOT create a distinct update mutation implementation.

Update flow:

```text
inspect installed identity
    ↓
retrieve/select exact release in runner layer
    ↓
verified release bundle primitive
    ↓
installation transition plan
    ↓
present exact transition
    ↓
obtain any required bounded intent
    ↓
rd_install.install
    ↓
ril_status.classify_status
    ↓
checkpoint / configuration follow-up
```

Remote release discovery and retrieval are runner-layer observations. They do not authorize installation and MUST NOT be folded into `rd_install.py`, which remains network-independent.

Downgrades remain rejected by default and require the installer’s existing explicit downgrade option plus user intent appropriate to the requested transition.

Project knowledge, authority, canonical state, evidence, and integration remain outside installer ownership.

## 14. Recovery and resume

Rupi MUST be resumable from durable project state.

It SHALL NOT persist a private lifecycle progress database as authoritative state.

If an installer recovery journal exists, the governing installer recovery primitive determines recovery behavior.

If RIL authoritative histories are valid but projections are missing/stale, ordinary repair primitives determine repair behavior.

If authoritative history is invalid or an exceptional recovery boundary is returned, Rupi MUST stop and surface that boundary. It MUST NOT invent recovery semantics.

After recovery/repair, Rupi re-inspects state through accepted status surfaces and continues only if the requested bounded lifecycle goal still permits continuation.

## 15. Termination and handoff

Rupi terminates when lifecycle setup/maintenance for the requested goal is complete.

Rupi MUST hand off rather than continue into ordinary semantic processing merely because setup made that processing possible.

Examples:

- candidate reconciliation belongs to an appropriately activated reconciliation Steward;
- candidate admission belongs to an appropriately activated admission Steward;
- ordinary RIL operations belong to the normal CLI or Human ↔ Agent adapter.

A final Rupi control return SHOULD identify:

- what lifecycle work completed;
- what was not completed;
- durable artifacts created by governing primitives;
- readiness for requested capabilities;
- the next non-Rupi interaction surface.

## 16. Security and authority invariants

Rupi conformance MUST prove all of the following:

1. Rupi has no independent mutation primitive.
2. Rupi has no durable authority merely by being invoked.
3. Rupi cannot infer protected operator identity.
4. Rupi cannot auto-establish the root operator.
5. Rupi cannot auto-authorize Steward scopes.
6. Rupi cannot turn Steward authorization into activation.
7. Rupi cannot bypass installer drift, identity, compatibility, downgrade, or recovery checks.
8. Rupi cannot mutate project-owned state as installer work.
9. Rupi cannot mutate package-managed state as bootstrap/authority work.
10. Rupi cannot use `rd_steward_setup.py` as an alternate authority path.
11. Rupi cannot treat a checkpoint as authority or normative lifecycle state.
12. Rupi cannot silently proceed from lifecycle setup into reconciliation/admission.
13. Every claimed successful operation is backed by the exact governing primitive result.
14. Reinvocation reconstructs progress from authoritative state and is not dependent on prior conversation.

## 17. Non-goals

R1 does not define:

- a new installer;
- a new updater;
- a package retrieval protocol;
- a release publication protocol;
- new semantic reconciliation rules;
- new admission rules;
- new authority-grant semantics;
- a generic all-purpose Reasoning Distiller agent;
- autonomous project governance;
- automatic operator identity resolution without accepted authentication evidence.

## 18. Acceptance boundary

Acceptance of this design authorizes the Rupi architecture, primitive mappings, and conformance requirements only.

Implementation MUST begin with the primitive extraction/conformance gates. The Rupi adapter itself MUST NOT be implemented before the two permitted installer primitive gaps are proven to reuse the installer’s existing semantic logic rather than duplicate it.
