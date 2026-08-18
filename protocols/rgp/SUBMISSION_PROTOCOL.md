# RGP Submission Protocol

## Status

This document defines the durable handoff contract between RGP producers, including the Reasoning Distiller, and the Project Engineering Steward.

The protocol governs candidate submission and Steward disposition. It does not grant canonical admission, alter RGP semantics, redefine PEMS/COVE representation contracts, or transfer ownership of canonical project memory.

## Purpose

The Distiller and other RGP producers must be able to submit symbolic reasoning for durable project-memory consideration without writing directly to canonical PEMS/COVE state.

The protocol therefore separates three artifacts and responsibilities:

```text
RGP producer
    ↓
immutable candidate submission
    ↓
Project Engineering Steward
    ↓
immutable disposition
    ↓
canonical PEMS/2 mutation, when admitted
```

Candidate production, Steward admission, and canonical persistence are distinct operations.

## Repository Surface

All durable RGP-to-Steward submissions for this project live on branch:

```text
project-chat-handoff
```

Candidate submissions are written under:

```text
docs/handoff/rgp/submissions/
```

Steward dispositions are written under:

```text
docs/handoff/rgp/dispositions/
```

These artifacts are immutable once committed. Corrections or changed candidate graphs require a new submission ID and a new file. Steward reconsideration requires a new disposition artifact that explicitly references the prior disposition it supersedes.

The Reasoning Distiller and other RGP producers must not write directly to:

```text
docs/project-chat-handoff.cove.json
docs/project-chat-handoff.json
```

Those remain Steward-owned canonical-memory surfaces.

## Submission Identity

Every candidate package has one immutable `submission_id`.

Recommended form:

```text
RGP-YYYYMMDDTHHMMSS±ZZZZ-NNN
```

Example:

```text
RGP-20260816T153000-0700-001
```

The spelling is an identifier convention only. Semantics must not be inferred from the identifier beyond identity.

A `submission_id` permanently identifies one exact semantic candidate package. Retrying delivery of the same package reuses the same ID. If the candidate graph changes, the producer must mint a new submission ID.

## Candidate Submission Envelope

A submission is a JSON document with this shape:

```json
{
  "submission_id": "RGP-20260816T153000-0700-001",
  "producer": {
    "role": "reasoning-distiller",
    "instance": "optional producer/runtime identifier"
  },
  "created_at": "2026-08-16T15:30:00-07:00",
  "rgp_version": "rgp/1",
  "status": "candidate",
  "source_context": {
    "summary": "Short human-readable description of why this candidate exists.",
    "refs": ["opaque-context-reference"]
  },
  "candidate_graph": {
    "records": [],
    "relations": []
  },
  "validation": {
    "status": "passed",
    "validator": "rgp-validator/1",
    "validated_at": "2026-08-16T15:30:01-07:00"
  }
}
```

### Required fields

- `submission_id`
- `producer.role`
- `created_at`
- `rgp_version`
- `status`
- `candidate_graph`
- `validation.status`
- `validation.validator`

### Allowed status

Candidate submissions always use:

```text
candidate
```

Admission lifecycle is never encoded by changing the candidate file.

### `source_context`

`source_context` is optional operational context for the Steward. It explains why the package exists and may point to task, chat, commit, issue, or other coordination references.

It is not proposition provenance and must not become a second evidence system. RGP proposition/relation provenance remains authoritative for semantic grounding.

### `candidate_graph`

`candidate_graph` must conform to the declared RGP major version and contain only candidate identities such as `temp_id` until Steward reconciliation assigns or reuses canonical identities.

### `validation`

A candidate intended for ordinary Steward reconciliation must have passed deterministic RGP validation before submission.

A structurally invalid graph must not be disguised as a candidate admission request. If invalid output must be preserved for evaluation, store it as an evaluation artifact outside the submission queue.

## Submission Invariants

A valid submission must satisfy all of the following:

1. `submission_id` is unique to one exact candidate package.
2. `rgp_version` is explicit.
3. unknown RGP major versions are not guessed or coerced.
4. `status` is `candidate`.
5. the candidate graph passed the declared validator.
6. the submission file is immutable after commit.
7. retries of the identical package reuse the same submission ID.
8. changed candidate semantics require a new submission ID.
9. submission metadata does not override RGP provenance.
10. submission does not imply PEMS admission, truth, lifecycle state, or normative authority.

## Steward Disposition Envelope

The Steward records reconciliation/admission outcome separately from the candidate submission.

A disposition is a JSON document with this conceptual shape:

```json
{
  "disposition_id": "RGPD-20260816T154200-0700-001",
  "submission_id": "RGP-20260816T153000-0700-001",
  "created_at": "2026-08-16T15:42:00-07:00",
  "steward": "project-engineering-steward",
  "disposition": "admitted",
  "record_map": {
    "r1": "proposition:stable-id",
    "r2": "decision:stable-id"
  },
  "relation_map": {},
  "reason_codes": ["IDENTITY_RECONCILED", "PROVENANCE_RESOLVED"],
  "canonical_commit": "optional commit SHA when canonical persistence occurred"
}
```

### Disposition values

```text
admitted
provisional
rejected
```

The disposition describes what happened to the candidate package under Steward policy. It does not change the semantic kind of any RGP proposition.

### `record_map`

When reconciliation assigns or reuses canonical identities, `record_map` maps candidate `temp_id` values to canonical PEMS/2 record IDs.

For `provisional` or `rejected` submissions, mappings may be omitted unless stable identities were intentionally reserved under an accepted policy.

### `relation_map`

Use `relation_map` only when canonical PEMS relation identity is explicit and a candidate relation requires mapping. Omit when no mapping is needed.

### `reason_codes`

`reason_codes` are machine-readable Steward disposition explanations. They supplement, but do not replace, provenance or RGP semantics.

The reason-code vocabulary is Steward/admission policy, not RGP ontology.

### `canonical_commit`

Include `canonical_commit` only when canonical PEMS/COVE persistence actually occurred and the commit is known.

Do not include a planned or expected commit.

## Disposition Immutability and Reconsideration

A disposition file is immutable once committed.

If later evidence changes the Steward outcome, create a new disposition with:

```json
{
  "supersedes_disposition": "prior-disposition-id"
}
```

Do not edit historical disposition files.

Reconsidering a disposition does not require changing the original candidate submission.

## Idempotency

The semantic idempotency key for candidate delivery is:

```text
submission_id
```

The Steward must not create duplicate canonical effects for repeated processing of the same submission.

Processing rules:

```text
same submission_id + identical committed candidate
    → return/reuse existing disposition or continue an incomplete safe transaction

same submission_id + different candidate bytes/semantics
    → hard error: submission identity collision

new submission_id + semantically duplicate graph
    → normal Steward reconciliation; reuse canonical identities where appropriate
```

Repository commit SHA may be used operationally to prove exact submitted bytes, but semantic idempotency remains anchored to `submission_id`.

## Transaction Boundary

Steward admission of connected reasoning must be transactional with respect to required graph integrity.

The Steward must not persist a canonical result that:

- leaves required premise references dangling;
- admits a derived proposition while silently dropping constitutive premises;
- rewrites only one endpoint of a required relation;
- loses required provenance;
- causes canonical semantic identity collision;
- applies `supersedes` lifecycle mutation without accepted authority/policy.

A submission may receive a mixed internal reconciliation analysis, but its durable disposition must accurately represent whether the required candidate subgraph was admitted, remained provisional, or was rejected under the accepted admission policy.

## Producer Responsibilities

An RGP producer must:

- produce candidate RGP, not canonical PEMS mutations;
- validate the candidate graph before ordinary submission;
- preserve opaque provenance IDs;
- keep `source_context` separate from proposition provenance;
- mint a new submission ID when candidate semantics change;
- write submissions only in the RGP-owned submission namespace;
- never overwrite a committed submission;
- never claim Steward admission before a disposition exists.

## Steward Responsibilities

The Project Engineering Steward must:

- treat each submission as a proposal to canonical memory;
- verify submission identity and declared RGP compatibility;
- reconcile source/provenance references according to accepted PEMS/2 policy;
- reconcile candidate semantic identities against canonical memory;
- preserve proposition kinds and graph meaning;
- classify the submission as admitted, provisional, or rejected;
- persist an immutable disposition;
- apply canonical PEMS/2/COVE mutation only when admission policy permits;
- preserve historical candidate/disposition auditability;
- make repeated processing idempotent.

## Failure Conditions

The Steward must stop and surface, rather than guess, when:

- a submission ID is reused for different candidate semantics;
- the RGP major version is unsupported;
- validation evidence is missing or claims a validator/version that cannot be accepted;
- required provenance cannot be resolved under policy;
- canonical identity reconciliation is ambiguous;
- graph admission would violate premise/relation integrity;
- canonical PEMS/COVE persistence would lose history, provenance, or determinism;
- authority-sensitive supersession or conflict resolution lacks accepted authority.

## Relationship to RGP and PEMS/2

This protocol is a handoff/coordination contract.

It does not add RGP proposition kinds, RGP relations, or provenance roles.

It does not define PEMS/2 record shapes or COVE encoding.

Conceptually:

```text
RGP
    defines candidate reasoning meaning

RGP Submission Protocol
    transports immutable candidate packages and immutable Steward outcomes

PEMS/2
    represents admitted durable project-memory semantics

COVE
    encodes canonical project memory
```

Keep these contracts independently versioned and independently evolvable.