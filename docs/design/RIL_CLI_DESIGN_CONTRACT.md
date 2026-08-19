# R16A — `ril` CLI Design Contract

Status: **Normative design contract — accepted, amended for R16B-D1 integration**

Contract: `reasoning-distiller-ril-cli-design/1`

Public command: `ril`

Depends on: accepted R1–R15 primitive and orchestration contracts; accepted R16B-D1 durable workflow design where workflow commands are concerned.

Implementation status: **not authorized by acceptance alone; implementation follows the R16 UX design gates.**

## Purpose

The `ril` CLI is a human- and automation-facing adapter over the proven Reasoning Distiller primitives and orchestration layer.

The CLI SHALL provide a Unix-like, Git-influenced interface while preserving established authority boundaries, immutable evidence, deterministic behavior, and protocol semantics.

The CLI is an adapter, not a new semantic or authority layer. No CLI convenience may manufacture authority, synthesize approval or Steward activation, reinterpret normative artifacts, invisibly collapse a required authority boundary, mutate canonical PEMS/COVE outside admission, modify RGP/PEMS/COVE contracts, or introduce a new source of authoritative state.

## Design principles

### Resource-oriented topology

The hierarchy SHALL be organized primarily around stable domain resources, supplemented by a small number of lifecycle operations.

### Git-like discoverability

The CLI SHALL favor one stable executable (`ril`), concise domain nouns, explicit hyphenated subcommands, hierarchical help, project-root discovery, abbreviated immutable references where unambiguous, and incremental discoverability. Git compatibility is ergonomic, not normative.

### Interactive ceremony, never hidden authority

Interactive commands MAY guide a human through required ceremonies, but every authority boundary SHALL remain visible. Friendly representations are never substitutes for the exact normative objects being authorized.

### Presentation is not semantics

Human-readable, JSON, and quiet output are alternative presentations. Presentation mode MUST NOT alter authority requirements, primitive selection, mutation behavior, validation, result meaning, or requested inspection depth.

## Root, bootstrap, and project discovery

Bare `ril` SHALL be a read-only, project-aware orientation surface summarizing lifecycle state, the highest-priority blocker or condition, relevant project state, a suggested next command, and abbreviated help. It SHALL perform no mutation.

`ril status` SHALL expose the composite lifecycle/status classifier.

```text
ril install
ril init
```

`ril install` targets the current repository/directory context by default, with an explicit target permitted. It SHALL NOT imply initialization. `ril init` performs minimal deterministic project initialization only and SHALL NOT implicitly establish root, import roles, authorize/activate a Steward, reconcile, admit, or perform other authority-bearing setup.

Commands requiring an initialized project SHALL search upward from the current working directory for the enclosing RIL project root. An explicit override SHALL be supported:

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

Bare `ril operator` is read-only. `set-root` is legal only when no protected root exists. `transfer-root` is legal only after root exists and invokes the stronger protected-root transfer ceremony. Operator capabilities remain properties of operators rather than a separate resource family.

## Role commands

```text
ril role
ril role list
ril role show <role>
ril role submission
ril role submission list
ril role submission create <file|-> [--snapshot]
ril role submission show <submission>
ril role submission apply ...
```

Role submissions are first-class inspectable resources. File and stdin input normalize to the same normative representation. Incremental submission is default; snapshot semantics require `--snapshot`.

Future Role Directive Markdown support remains conversion into normative role-submission representation and MUST NOT invent missing role semantics.

## Steward commands

```text
ril steward
ril steward set-reconciliation <role>
ril steward clear-reconciliation
ril steward set-admission <role>
ril steward clear-admission
```

Bare `ril steward` is a read-only dashboard. Public `reconciliation` maps to normative internal scope `semantic_reconciliation`; stored/structured protocol artifacts retain normative identifiers. A `set-*` operation MUST NOT imply that invocation alone grants authority.

## Candidate, reconciliation, admission, and Canon

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

ril canon
ril canon verify
```

Candidates are first-class resources. Bare reconciliation/admission commands are read-only dashboards. Reconciliation and admission consume explicit activation evidence; activation SHALL NOT be inferred from shell user, operator, session, or assignment and SHALL NOT be a persistent switch. Admission SHALL NOT implicitly perform storage verification.

Disposition and receipt artifacts have canonical typed identities; candidate-oriented lookup is a convenience only when uniquely resolvable.

`Canon` is human-facing CLI vocabulary for admitted canonical project knowledge and does not rename PEMS, COVE, or their normative contracts. `canon verify` invokes accepted storage-verification semantics.

## Repair and recovery

```text
ril repair
ril recover
ril recover plan ...
```

`repair` is ordinary deterministic reconstruction of derived projections from valid authoritative history. `recover` is exceptional recovery when authoritative history itself is invalid. Recovery reuses universal approval/application ceremony rather than defining new authority.

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

Proposals and approvals are globally inspectable artifacts. `ril approve` creates the appropriate approval artifact and SHALL NOT apply mutation. `--auth` supplies authentication/identity evidence without inventing provider semantics. `ril apply` dispatches the exact proposal to the appropriate proven operation without modifying or broadening it or manufacturing authority.

## Workflow commands

Durable workflows are first-class CLI resources:

```text
ril workflow
ril workflow list [--all]
ril workflow show <workflow> [--depth=0|1|2]
ril workflow create [<file|->] [--auth <file|->]
ril workflow continue <workflow>
ril workflow cancel <workflow> [--auth <file|->]
ril workflow revise <workflow> [<file|->] [--auth <file|->]
ril workflow acknowledge <workflow> <workflow-event> [--auth <file|->]
```

Bare `ril workflow` is a read-only context-sensitive dashboard distinguishing visible workflows from workflows actionable by the authenticated operator, including applicable protected-root workflow-control overrides. `workflow list` defaults to OPEN workflows; `--all` includes terminal history.

### Creation

The canonical workflow-definition format is structured input. `create <file>`, `create -`, and naked interactive `create` all construct the same canonical creation payload. Interactive construction is a guided constructor, not a second workflow language.

The exact canonical creation payload is previewed and authentication binds to that payload. For ordinary `operator-driven` creation, authenticated assent is sufficient. Creation with `execution: auto-advance` additionally requires conspicuous prospective acknowledgement that future in-scope consequential operations may occur without another continuation request once independent authority requirements are satisfied. Non-interactive auto-advance creation requires a correspondingly explicit acknowledgement; a generic confirmation shortcut is insufficient.

Successful creation returns a compact control-return receipt identifying the workflow, requester, execution mode, lifecycle, condition, and current next boundary/action. `--quiet` returns the complete canonical workflow reference.

### Continue

`workflow continue` advances an already-authorized bounded workflow until the next meaningful control boundary, which may include completion, approval/activation/evidence wait, unresolved/blocking state, materiality pause, or execution failure. It may traverse multiple consequential stages only where each stage independently satisfies its normative requirements.

`continue` consumes satisfied prerequisites; it MUST NOT manufacture or silently enter ceremonies for missing approval, activation, acknowledgement, authentication, or other authority. Reaching such a boundary without progression is a valid evaluation outcome.

An `auto-advance` workflow may also be manually continued by a permitted continuation operator or protected root. Expected-head concurrency prevents duplicate authoritative progression.

Normal output summarizes material consequential progression and the final control boundary. Operations performed and operations not performed MUST be unmistakable.

### Cancellation

Requester self-cancellation uses ordinary explicit confirmation after displaying remaining intent and irreversible consequence. Protected root cancellation of another operator's workflow requires the stronger exact-reference override ceremony; non-interactive invocation requires the corresponding explicit protected override mechanism rather than generic `--yes`.

Cancellation is an exact-state transition. If normative workflow state advances after review, cancellation fails stale and does not automatically retry. It never rewrites intervening history or reverses completed operations.

### Revision

`workflow revise` mirrors creation input:

```text
ril workflow revise <workflow> revised-workflow.json
ril workflow revise <workflow> -
ril workflow revise <workflow>
```

Interactive revision may begin from the predecessor definition for editing convenience, but always constructs and authenticates a complete immutable successor. Authentication is followed by explicit confirmation that successor creation will permanently supersede the predecessor.

Revision atomically creates the successor and appends predecessor supersession. The authenticated successor payload binds the exact predecessor normative state/head. If predecessor state advances before commit, the entire revision fails stale: no successor is created and no supersession occurs. RIL MUST NOT automatically rebase authenticated intent.

### Materiality acknowledgement

Acknowledgement binds to the exact immutable pause event:

```text
ril workflow acknowledge workflow:abc workflow-event:def
```

The primitive validates event membership/type, continued applicability, and acknowledgement permission/root override. Acknowledgement restores sufficiently informed intent but is not itself a continuation request. An operator-driven workflow becomes eligible for a later explicit `continue`; an auto-advance workflow becomes autonomously eligible again according to its existing mode.

Intervening informational extension events do not invalidate an otherwise current acknowledgement. Later normative events that acknowledge, invalidate, terminate, or otherwise change pause applicability do.

### Workflow heads and concurrency

Workflow history distinguishes:

```text
history_head    = most recently appended workflow event
normative_head  = most recent core event affecting workflow semantics
```

All events remain in one immutable linear history. Informational extension events advance `history_head` but not `normative_head`; the workflow primitive serializes informational appends without requiring the writer to predict `history_head`.

Normative core transitions bind the expected `normative_head` plus exact authoritative external state/artifacts material to that transition, then append after the current physical `history_head`. Informational observations therefore cannot accidentally alter normative concurrency.

At workflow inspection depth 0, `Head` means `normative_head`. At depth 1 or greater, both heads are named explicitly.

## Interactive and non-interactive mutation behavior

Interactive mutation commands MAY guide complete ceremonies. Before approval, RIL SHALL provide a layered preview with concise human-readable summary/diff, canonical proposal reference, and a means to inspect the complete normative proposal. Friendly representation is never authoritative.

A non-interactive mutation SHALL advance only as far as existing authority permits. Reaching a valid approval boundary is a successful intermediate protocol state, with proposal reference and next action exposed. RIL MUST NOT manufacture missing approval.

Confirmation is risk-sensitive. Ordinary operations MAY use concise explicit confirmation. Protected/exceptional operations retain stronger ceremonies required by their contracts.

## References and identifiers

Immutable artifacts use typed content-addressed references, including at least:

```text
proposal:<id>
approval:<id>
candidate:<id>
submission:<id>
disposition:<id>
receipt:<id>
workflow:<id>
workflow-event:<id>
```

Persisted artifacts and structured output retain complete canonical identity.

Git-style unique-prefix abbreviation is supported within a declared/expected artifact type and only when exactly one artifact matches. Abbreviations are never persisted identities.

Where command position supplies the required resource type, contextual bare IDs/prefixes MAY be accepted as input. Resolution occurs only within that required type and ambiguity fails. Generic inspection never infers a type from a bare ID.

Contextual shorthand is input convenience only. Singular `show` and `--json` output identify durable artifacts with complete canonical typed references. Dashboards, lists, and compact control-return receipts MAY display unambiguous abbreviated typed references. `--quiet`, when its primary result is a durable artifact, emits the complete canonical typed reference.

Friendly operator/role identifiers MAY be accepted and strictly canonicalized to normative identities.

## Generic typed-reference inspection

Every durable typed reference an operator may be required to identify in a normative command SHALL have a canonical inspection path.

R16A provides a generic route:

```text
ril show <typed-reference> [--depth=<supported-depth>]
```

The typed reference dispatches to exactly the same authoritative inspector used by the corresponding resource-specific `show` where one exists. Generic inspection is not superior to resource-oriented inspection; both are canonical routes to the same object semantics.

`ril show` requires a typed reference. It MUST NOT infer resource type from global uniqueness of a bare identifier. Candidate-oriented or other domain convenience lookups remain domain-specific and are not generalized through `ril show`.

## Inspection depth

`--depth` is a standard capability for singular inspection surfaces with meaningful layered inspection. It is not mandatory on every `show`, and collection/dashboard surfaces do not gain depth merely for syntactic uniformity.

Standard semantic bands are:

```text
depth 0 — authoritative primary view
          enough to identify and understand the object itself

depth 1 — directly bound context
          immediate provenance, history, relationships, or evidence
          explaining the primary view

depth 2 — expanded evidence
          resolution/expansion of authoritative references surfaced
          by directly bound context where meaningful
```

A resource supports only the meaningful prefix of this scale (`0`, `0|1`, or `0|1|2`). Unsupported depth fails explicitly and reports the supported range; it is never silently clamped. Help advertises depth only where supported and states the maximum supported depth.

Depth is cumulative: `--depth=N` means inspect through level N. Omitted depth always means depth 0, independent of presentation mode. Higher depth adds authoritative context/evidence and MUST NOT change object semantics.

Depth expansion is strictly read-only. It MUST NOT generate, repair, refresh, or mutate authoritative state. Missing referenced evidence is surfaced as an integrity/availability fact at the depth where encountered; RIL MUST NOT fabricate expansion. Repeated/cyclic references are detected and represented by reference rather than traversed indefinitely.

The scale is contract-bounded rather than arbitrary recursive graph depth. Machine-readable depth-capable inspection exposes both requested depth and maximum supported depth.

`--depth` belongs to singular inspection. `list`, aggregate `history`, and bare dashboards remain bounded collection/orientation operations using applicable filters rather than evidence expansion.

## History

```text
ril history
ril history show <event>
```

History is strictly read-only and derives its aggregate view from existing authoritative histories and immutable evidence. It SHALL NOT become independent audit authority and SHALL NOT invent a global cross-domain chronology or sequence number. Existing domain-local ordering and content bindings are preserved.

Where a history event has a durable typed identity, `ril history show <event>` and `ril show <typed-history-event-reference>` are equivalent inspection routes to the same authoritative object.

## Output modes

Applicable commands support mutually exclusive presentation modes:

```text
--human
--json
--quiet
```

If none is specified, human-readable presentation is the default in both TTY and non-TTY contexts. TTY detection MAY govern prompting, paging, and terminal decoration, but redirection MUST NOT silently change representation.

`--json` exposes the complete deterministic adapter result **at the requested inspection depth**. It does not implicitly expand evidence. `--quiet` emits the minimum primary useful value and is depth-0 only; explicit `--depth=1` or `--depth=2` with `--quiet` is invalid.

Presentation and inspection depth are orthogonal except for that quiet/depth restriction.

## Canonical option placement

The documented canonical grammar places global/project/presentation options before the resource/operation and operation-specific options after command arguments:

```text
ril [global-options] workflow show <workflow> [--depth=N]
ril [global-options] show <typed-reference> [--depth=N]
```

For example:

```text
ril --project ./repo --json workflow show abc --depth=2
```

`--depth` is accepted only by commands explicitly declaring depth capability. Parser acceptance of additional equivalent option placements, if ever provided, does not create additional canonical grammar.

## Exit status

Exit `0` means RIL successfully processed the request, including legitimate intermediate outcomes such as `APPROVAL_REQUIRED` or a workflow already resting at a valid control boundary. Nonzero means processing failed, including invalid input, contract violation, unsafe state, unresolved/ambiguous reference, conflicting authoritative state, stale normative concurrency, or execution failure. Rich protocol state belongs in operation results rather than proliferating shell exit codes.

## Help

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

Commands in this accepted contract are canonical R16A vocabulary. R16A defines no convenience aliases. Future aliases MUST map exactly to one canonical command and MUST NOT introduce independent semantics or weaken authority/validation boundaries.

## Canonical topology

```text
ril
├── status
├── install
├── init
├── show <typed-reference> [--depth=<supported-depth>]
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
│       ├── create <file|-> [--snapshot]
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
├── workflow
│   ├── list [--all]
│   ├── show <workflow> [--depth=0|1|2]
│   ├── create [<file|->] [--auth <file|->]
│   ├── continue <workflow>
│   ├── cancel <workflow> [--auth <file|->]
│   ├── revise <workflow> [<file|->] [--auth <file|->]
│   └── acknowledge <workflow> <workflow-event> [--auth <file|->]
├── proposal
│   ├── list
│   └── show <proposal>
├── approval
│   ├── list
│   └── show <approval>
├── approve <proposal> [--auth <file|->]
├── apply <proposal> --approval <approval>
├── history
│   └── show <event>
└── help ...
```

Bare domain commands described by this contract remain part of the topology even where the tree emphasizes subcommands.

## Reconciliation of the R16B-D1 amendment

The workflow CLI amendment and inspection-grammar normalization were reconciled against accepted R1–R15, the previously accepted R16A authority boundaries, and accepted R16B-D1 workflow semantics.

Result: **PASS.**

The amendment adds adapter coverage for accepted workflow primitive operations; it does not add workflow authority. `continue` cannot manufacture missing prerequisites; workflow creation/revision authentication binds exact durable intent; cancellation/revision/acknowledgement preserve exact-state concurrency; auto-advance remains prospectively disclosed and independently authority-gated; informational workflow events cannot affect normative semantics.

The standardized `--depth`/`ril show` grammar is inspection-only and introduces no new authoritative state. `ril history` remains aggregate read-only history and is distinct from resource evidence expansion.

R16B-D1 integration finding I1 is therefore resolved at the CLI design-contract level.

## Non-goals

R16A does not redesign primitive semantics; introduce new protocol authority; create Architect or RGP Engineer authority; permit RGP/PEMS/COVE contract mutation; define authentication providers; infer Steward activation from operator/session identity; implement Role Directive Markdown semantics; create a global history sequence; collapse reconciliation and admission; automatically verify after admission; make storage paths public artifact identity; prescribe auto-advance deployment architecture; or finalize Human↔Agent conversational behavior.

Human↔Agent interaction belongs to R16B.

## Acceptance condition

R16A remains **accepted as amended**. Its implementation gate requires that every command map to an accepted primitive/orchestrator/workflow behavior or be explicitly read-only presentation/resolution; no command introduce new authority or protocol semantics; interactive and non-interactive authority boundaries remain explicit; and reference, depth, output, exit, discovery, concurrency, and help semantics remain conformant with this contract.

R16B Human↔Agent Interaction Design SHALL continue against these amended adapter and authority boundaries before UX implementation slices are finalized.
