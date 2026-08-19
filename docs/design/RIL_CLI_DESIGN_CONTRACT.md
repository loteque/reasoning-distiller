# R16A — `ril` CLI Design Contract

Status: **Normative design contract — accepted**

Contract: `reasoning-distiller-ril-cli-design/1`

Public command: `ril`

Depends on: accepted R1–R15 primitive and orchestration contracts.

Implementation status: **not authorized by acceptance alone; implementation follows the R16 UX design gates.**

## Purpose

The `ril` CLI is a human- and automation-facing adapter over the proven Reasoning Distiller primitives and R15 orchestration layer.

The CLI SHALL provide a Unix-like, Git-influenced interface while preserving the authority boundaries, immutable evidence, deterministic behavior, and protocol semantics established by R1–R15.

The CLI is an adapter, not a new semantic or authority layer.

No CLI convenience may manufacture authority, synthesize approval or Steward activation, reinterpret a normative proposal, invisibly collapse a required authority boundary, mutate canonical PEMS/COVE outside admission, modify RGP/PEMS/COVE contracts, or introduce a new source of authoritative state.

## Design principles

### Resource-oriented topology

The command hierarchy SHALL be organized primarily around stable Reasoning Distiller domain resources, supplemented by a small number of lifecycle operations.

### Git-like discoverability

The CLI SHALL favor one stable executable (`ril`), concise domain nouns, explicit subcommands, hierarchical help, project-root discovery, abbreviated immutable references where unambiguous, and incremental discoverability. Git compatibility is not a goal; the resemblance is ergonomic, not normative.

### Interactive ceremony, never hidden authority

Interactive commands MAY guide a human through `plan → review → explicit confirmation → approval → apply`, but every authority boundary SHALL remain visible. Resulting proposal, approval, evidence, and mutation artifacts SHALL be equivalent to executing the corresponding explicit primitive stages independently.

### Presentation is not semantics

Human-readable, JSON, and quiet output are alternative presentations of the same operation/result semantics. Presentation mode MUST NOT alter authority requirements, primitive selection, mutation behavior, validation, or result meaning.

## Root and bootstrap

Bare `ril` SHALL be a read-only, project-aware orientation surface summarizing lifecycle state, the highest-priority blocker or condition, relevant project state, a suggested next command, and abbreviated help. It SHALL perform no mutation.

`ril status` SHALL expose the composite lifecycle/status classifier. Human-readable output is the ordinary interactive representation; structured output SHALL expose the complete deterministic status result.

Installation and initialization remain distinct:

```text
ril install
ril init
```

`ril install` targets the current repository/directory context by default, with an explicit target permitted. It SHALL NOT imply initialization.

`ril init` performs minimal deterministic project initialization only. It SHALL NOT implicitly establish a root operator, import project roles, authorize or activate a Steward, reconcile, admit, or perform other authority-bearing setup.

## Project discovery

Commands requiring an initialized project SHALL search upward from the current working directory for the enclosing RIL project root. An explicit global override SHALL be supported:

```text
ril --project <path> ...
```

The explicit target takes precedence. Structured output SHALL identify the resolved project root.

## Operator commands

```text
ril operator
ril operator list
ril operator show <operator>
ril operator add <operator>
ril operator update <operator>
ril operator disable <operator>
ril operator enable <operator>
ril operator set-root <operator>
ril operator transfer-root <operator>
```

Bare `ril operator` is a read-only operator-domain dashboard.

`set-root` is legal only when no protected root exists. `transfer-root` is legal only after a root exists and invokes the stronger protected-root transfer ceremony. `set-root` MUST NOT act as an alternate spelling for transfer.

Operator capabilities are properties of operators and SHALL NOT form a separate CLI resource family in R16A.

## Role commands

```text
ril role
ril role list
ril role show <role>
ril role submission
ril role submission list
ril role submission create <file|->
ril role submission show <submission>
ril role submission apply ...
```

Role submissions are first-class inspectable resources. Creation accepts a file or standard input and both normalize to the same normative role-submission representation.

Incremental submission is the default. Snapshot semantics require explicit intent:

```text
ril role submission create roles.json --snapshot
```

Package-provided and forbidden protocol roles remain governed by existing primitive contracts.

### Future Role Directive support

R16A does not define Role Directive Markdown parsing as CLI semantics. A future capability SHOULD provide one validated conversion mechanism for Role Directive Markdown → normative role-submission JSON and may support both explicit conversion and direct Markdown ingestion. The converter MUST NOT invent missing role semantics.

## Steward commands

```text
ril steward
ril steward set-reconciliation <role>
ril steward clear-reconciliation
ril steward set-admission <role>
ril steward clear-admission
```

Bare `ril steward` is a read-only dashboard showing available public authority scopes, current assignments, assigned-role availability/status, relevant blockers, and abbreviated help.

The public CLI term `reconciliation` maps to normative internal scope `semantic_reconciliation`; stored and structured protocol artifacts retain normative identifiers.

A `set-*` operation MUST NOT imply that invocation alone grants authority. Required proposal and approval boundaries remain operative.

## Candidate, reconciliation, and admission

```text
ril candidate
ril candidate list
ril candidate show <candidate>

ril reconciliation
ril reconciliation run <candidate> --activation <file|->
ril reconciliation show <disposition|candidate>

ril admission
ril admission run <candidate> --activation <file|->
ril admission show <receipt|candidate>
```

Candidates are first-class inspectable resources independent of later reconciliation or admission.

Bare reconciliation and admission commands are read-only dashboards. Reconciliation and admission consume explicit activation evidence. Activation SHALL NOT be inferred from the shell user, operator, session, or Steward assignment, and SHALL NOT be exposed as a persistent switch.

Admission SHALL NOT implicitly perform storage verification.

Disposition and receipt artifacts have canonical typed identities, while candidate-oriented lookup is permitted as a convenience only when the associated result resolves uniquely.

## Canon

The human-facing name for admitted canonical project knowledge is **Canon**:

```text
ril canon
ril canon verify
```

Bare `ril canon` is a read-only canonical-state dashboard. `ril canon verify` invokes the accepted storage-verification semantics. `canon` is CLI vocabulary only and does not rename PEMS, COVE, or their normative contracts.

## Repair and recovery

```text
ril repair
ril recover
ril recover plan ...
```

`repair` represents ordinary deterministic repair/reconstruction of derived projections from valid authoritative history.

`recover` represents exceptional recovery when authoritative history itself is invalid. Bare `ril recover` is a read-only/guided dashboard; `ril recover plan` constructs the applicable recovery proposal/evidence. Recovery reuses the universal approval/application ceremony rather than defining a second authority mechanism.

## Proposal, approval, and application

```text
ril proposal
ril proposal list
ril proposal show <proposal>

ril approval
ril approval list
ril approval show <approval>

ril approve <proposal> [--auth <file|->]
ril apply <proposal> --approval <approval>
```

Proposals and approvals are globally inspectable artifacts, not replacements for semantic domain commands.

`ril approve` is the explicit cross-domain human authorization act. It creates the appropriate approval artifact and SHALL NOT apply the mutation. `--auth` supplies authentication/identity evidence without causing the CLI to invent authentication-provider semantics.

`ril apply` is semantically thin. It dispatches the proposal to the appropriate proven operation without modifying the proposal, broadening its scope, manufacturing approval, or changing authority requirements.

## Interactive mutation behavior

Interactive mutation commands MAY guide the complete ceremony. Before approval, RIL SHALL provide a layered preview containing a concise human-readable summary/diff, the canonical proposal reference, and a means to inspect the complete normative proposal. The friendly representation is never the authoritative object being approved.

Interactive ceremony is allowed; hidden authority is not.

## Non-interactive behavior

A non-interactive mutation SHALL advance only as far as existing authority permits. Reaching a valid approval boundary is a successful intermediate protocol state, e.g. `status: PASS`, `outcome: APPROVAL_REQUIRED`, with the proposal reference and next action exposed. RIL MUST NOT manufacture missing approval.

## Confirmation safety

Confirmation is risk-sensitive. Ordinary operations MAY use concise explicit interactive confirmation. Protected or exceptional operations SHALL retain stronger ceremonies required by their normative contracts, including protected-root transfer and exceptional recovery. The resulting approval artifact MUST satisfy the exact underlying primitive contract.

## References and identifiers

Immutable artifacts SHALL use typed content-addressed references, including:

```text
proposal:<id>
approval:<id>
candidate:<id>
submission:<id>
disposition:<id>
receipt:<id>
```

Typed references prevent cross-type interpretation. Persisted artifacts and structured output retain complete canonical identity.

Git-style unique-prefix abbreviation SHALL be supported for resolution. A prefix resolves only within its declared artifact type and only when exactly one artifact matches. Ambiguous or missing references fail explicitly. Abbreviated references are never persisted identities.

Friendly operator and role identifiers MAY be used in human-facing commands. The adapter MAY canonicalize them to normative identifiers such as `operator:alice`; resolution is strict, and ambiguity/nonexistence fails rather than being guessed. Normative artifacts and structured output use canonical identities.

## Inspection and collection conventions

Bare resource commands answer “what is happening in this domain?” Identified-object `show` commands inspect one object.

Collection resources expose deterministic `list` operations where useful, including operators, roles, role submissions, candidates, proposals, and approvals. Domain/singleton dashboards do not require redundant `list` commands. `ril history` is intrinsically an aggregate collection view.

Where semantically applicable, collection/history surfaces use a small consistent filtering vocabulary, initially including `--status`, `--operator`, `--role`, and `--candidate`. R16A does not introduce a general query language.

## History

```text
ril history
ril history show <event>
```

History is strictly read-only and derives its view from existing authoritative histories and immutable evidence. It SHALL NOT become an independent audit authority.

History preserves authoritative domain-local ordering. RIL MUST NOT invent a global cross-domain chronology or sequence number for presentation. Existing content bindings may be used to show cross-domain relationships.

## Output modes

Applicable commands SHALL support:

```text
--human
--json
--quiet
```

Interactive TTY use defaults to human-readable presentation. `--json` exposes the complete deterministic adapter result. `--quiet` emits the minimum primary useful value, such as a canonical typed reference or concise state token. Presentation mode SHALL NOT change semantics.

## Exit status

Exit `0` means RIL successfully processed the request, including legitimate intermediate outcomes such as `APPROVAL_REQUIRED`.

Nonzero means processing failed, including invalid input, contract violation, unsafe state, unresolved/ambiguous reference, conflicting authoritative state, or execution failure.

Rich protocol state belongs in operation results rather than a proliferation of shell exit codes.

## Help

Both conventional and Git-like forms SHALL be supported:

```text
ril --help
ril help
ril operator --help
ril help operator
ril operator set-root --help
ril help operator set-root
```

Help answers how a command is used; bare resource dashboards answer what is happening in the domain.

## Command stability and aliases

Commands in this accepted contract are the canonical R16A vocabulary. R16A defines no convenience aliases. Future aliases may be added from demonstrated usage, but MUST map exactly to one canonical command and MUST NOT introduce independent semantics or weaken authority/validation boundaries.

## Canonical topology

```text
ril
├── status
├── install
├── init
├── operator
│   ├── list
│   ├── show <operator>
│   ├── add <operator>
│   ├── update <operator>
│   ├── disable <operator>
│   ├── enable <operator>
│   ├── set-root <operator>
│   └── transfer-root <operator>
├── role
│   ├── list
│   ├── show <role>
│   └── submission
│       ├── list
│       ├── create <file|->
│       ├── show <submission>
│       └── apply ...
├── steward
│   ├── set-reconciliation <role>
│   ├── clear-reconciliation
│   ├── set-admission <role>
│   └── clear-admission
├── candidate
│   ├── list
│   └── show <candidate>
├── reconciliation
│   ├── run <candidate> --activation <file|->
│   └── show <disposition|candidate>
├── admission
│   ├── run <candidate> --activation <file|->
│   └── show <receipt|candidate>
├── canon
│   └── verify
├── repair
├── recover
│   └── plan ...
├── proposal
│   ├── list
│   └── show <proposal>
├── approval
│   ├── list
│   └── show <approval>
├── approve <proposal> [--auth <file|->]
├── apply <proposal> --approval <approval>
├── history
└── help ...
```

Bare domain commands described by this contract remain part of the topology even where the tree emphasizes their subcommands.

## Non-goals

R16A does not redesign R1–R15 primitives; introduce new protocol authority; create Architect or RGP Engineer authority; permit RGP/PEMS/COVE contract mutation; define authentication providers; infer Steward activation from operator/session identity; implement Role Directive Markdown semantics; create a global history sequence; collapse reconciliation and admission; automatically verify after admission; make storage paths part of public artifact identity; or define Human↔Agent conversational behavior.

Human↔Agent interaction belongs to R16B.

## Acceptance condition

R16A is **accepted**. Its implementation gate requires that every command map to an accepted R1–R15 primitive/orchestrator behavior or be explicitly read-only presentation/resolution; no command introduce new authority or protocol semantics; interactive and non-interactive authority boundaries remain explicit; and reference, output, exit, discovery, and help semantics remain conformant with this contract.

R16B Human↔Agent Interaction Design SHALL be performed against the same authority and interaction boundaries before the UX implementation slices are finalized.