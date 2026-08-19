# R16B-D2 — Operational Provenance Design Contract

Status: **Normative dependency design contract — accepted**

Contract: `reasoning-distiller-provenance/1`

Depends on: accepted R1–R15 primitive/orchestration contracts, amended R16A `reasoning-distiller-ril-cli-design/1`, accepted R16B-D1 `reasoning-distiller-workflow-design/1`, and draft R16B `reasoning-distiller-ril-human-agent-design/1`.

Implementation status: **not authorized by this document alone.**

## Purpose

This contract resolves R16B dependency D2 by defining durable operational provenance for agent, automation, tool, and human-interface execution context without introducing a new authority source or changing the identity of existing normative artifacts.

## Core distinction

Normative artifacts establish what happened. Provenance records observational operational context about how, by what runtime, or through what interface it happened.

Provenance MUST NOT grant or substitute for operator authentication, proposal approval, Steward authorization or activation, reconciliation judgment, admission authority, protocol mutation authority, or workflow-control authority.

## Provenance artifact

Operational provenance is represented as an immutable content-addressed typed artifact:

```text
provenance:<id>
```

Its canonical payload includes the exact durable subject it describes:

```text
provenance:<id>
  contract: reasoning-distiller-provenance/1
  subject: <canonical typed reference>
  producer:
    kind: agent | human-interface | automation | tool
    identity: <optional identifier>
  runtime:
    provider: <optional>
    model: <optional>
    agent: <optional>
    session: <optional>
    run: <optional>
  software:
    ril_version: <optional>
    adapter_version: <optional>
    tool_versions: <optional>
  environment: <bounded non-secret metadata>
  extensions: <namespaced optional metadata>
```

The subject binding is part of provenance meaning and therefore part of the provenance content hash.

## Subject-owned binding

The binding SHALL live in the provenance object, not in the normative subject artifact and not in a separate provenance-binding artifact.

Conceptually:

```text
disposition:abc
      ↑
      │ subject
provenance:def
```

Existing normative artifacts SHALL NOT be rehashed or rewritten merely to add, correct, replace, or enrich optional provenance.

No separate `provenance-binding:<id>` artifact is required by this contract.

## Identity and replacement

`provenance:<id>` is the hash of the complete canonical provenance payload, including its subject.

A provenance artifact is immutable. Correction, enrichment, or rebinding creates a new provenance artifact with a new identity. Implementations MUST NOT mutate provenance in place.

A replacement provenance record MAY identify a prior provenance artifact through a non-authoritative relationship such as `supersedes:` when preserving correction history is useful.

Old provenance artifacts may remain preserved as historical observations.

## Non-anchor invariant

Nothing normative may depend on stability of a provenance artifact identity.

A provenance ID MUST NOT become an authority token, approval dependency, activation dependency, workflow authority dependency, or required identity component of an otherwise independently identified normative artifact merely because provenance exists.

Consumers MUST NOT assume one eternal provenance ID for a subject.

Where multiple provenance observations exist, applicability/currentness is determined by the applicable provenance policy and immutable relationships, never by treating provenance as normative subject state.

## Requiredness

Provenance is optional unless an individual primitive contract explicitly makes a particular provenance fact normative input for that primitive.

Missing optional provenance MUST NOT invalidate otherwise valid normative protocol evidence.

Invalid supplied provenance is rejected as provenance; it does not retroactively invalidate an independently valid subject merely because optional provenance could not be attached.

## Producer boundary

Adapters and runtimes MAY construct provenance payloads describing facts available to them. The accepted provenance primitive validates canonical structure and subject binding before durable storage.

Producer identity is descriptive. A claimed model, provider, agent, runtime, session, tool, or interface identity does not itself establish trust or authority.

## Multiple provenance observations

A subject MAY have multiple provenance artifacts. This supports distinct producer, execution, transport, interface, diagnostic, or corrected observations without mutating the subject.

Identical canonical provenance content, including identical subject, naturally resolves to the same content-addressed identity.

## Metadata and privacy boundary

Provenance MUST NOT become credential or secret storage.

Sensitive values SHOULD be omitted or represented by safe references/digests where a durable correlation is necessary and permitted.

Environment metadata SHALL be bounded and non-secret. Namespaced extension fields MAY be used for future runtimes and adapters, but unknown extensions cannot acquire authority semantics.

Wall-clock timestamps MAY be recorded as informational metadata but are not required normative ordering fields. Authoritative ordering continues to come from accepted domain-local histories.

## Relationship to authority evidence

Authentication evidence and activation evidence remain separate normative concepts.

For example, a reconciliation disposition may have provenance describing the executing runtime, but its semantic authority derives from the accepted reconciliation primitive and valid Steward activation, not from provenance.

Likewise, provenance about a human-interface action does not replace authenticated operator evidence where authentication is required.

## Workflow integration

Workflow events MAY be subjects of provenance artifacts. Agent/runtime provenance can therefore describe workflow execution and diagnostics without altering the workflow event's normative identity or advancing either workflow head.

Provenance itself is not a workflow event and does not alter workflow lifecycle, condition, bounded intent, authority, `history_head`, or `normative_head` merely by being recorded.

## Canon boundary

Operational provenance is not Canon and MUST NOT become canonical PEMS/COVE knowledge merely by being stored or referenced.

## Inspection

`provenance:<id>` is a durable typed reference and therefore satisfies the R16A direct-inspection invariant through:

```text
ril show provenance:<id>
```

A dedicated top-level provenance collection/list family is not required by D2. Provenance is ordinarily discovered through subject/evidence expansion and indexed subject lookup where implemented.

Where a subject inspector supports layered inspection, applicable provenance is a natural directly bound or expanded evidence target under the R16A depth semantics. Inspection remains read-only and MUST NOT manufacture missing provenance.

## History and ordering

Provenance may be correlated from history views, but provenance timestamps or runtime identifiers MUST NOT be used to invent a global cross-domain chronology.

## Reconciliation findings

D2 was reconciled against accepted R1–R15, amended R16A, accepted D1, and draft R16B.

Result: **SEMANTIC PASS.**

The design preserves all existing authority boundaries, content-addressed normative artifact identities, the Canon boundary, domain-local history ordering, and workflow semantics.

The initially considered separate `provenance-binding` artifact is intentionally rejected. Because provenance identities are observational and MUST NOT be normative identity anchors, placing the exact subject binding inside the provenance payload is simpler and makes each provenance artifact self-contained without forcing existing normative subjects to be rehashed.

## D2 resolution status

R16B dependency D2 is **RESOLVED**.
