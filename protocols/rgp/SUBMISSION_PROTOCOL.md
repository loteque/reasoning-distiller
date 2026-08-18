# RGP Submission Protocol

## Status

This document defines the generic durable handoff contract between RGP producers, including the Reasoning Distiller, and a project-authorized Steward.

The protocol governs immutable candidate submission and immutable Steward disposition. It does not grant canonical admission, alter RGP semantics, select a canonical backend, or transfer ownership of project knowledge.

## Core flow

```text
RGP producer
    ↓
immutable candidate submission
    ↓
project-authorized Steward
    ↓
semantic reconciliation + immutable disposition
    ↓
project canonical mutation, when admitted
```

Candidate production, semantic reconciliation, admission, and canonical persistence are distinct operations.

## Project surface

A consuming Project Knowledge Package identifies the project-owned locations for candidate submissions, transactions, dispositions, evidence, policy, authority, and canonical state.

This protocol defines artifact semantics and immutability. It does **not** hard-code repository names, branch names, filesystem paths, canonical backend paths, or role assignments.

RGP producers must not write directly to a project's canonical knowledge merely because they can produce a structurally valid candidate.

## Submission identity

Every candidate package has one immutable `submission_id`.

Recommended form:

```text
RGP-YYYYMMDDTHHMMSS±ZZZZ-NNN
```

Identifier spelling is an identity convention only. Semantics must not be inferred from it.

A `submission_id` permanently identifies one exact semantic candidate package. Retrying delivery of the same package reuses the same ID. If candidate semantics change, the producer must mint a new submission ID.

## Candidate submission envelope

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

Required fields:

- `submission_id`
- `producer.role`
- `created_at`
- `rgp_version`
- `status`
- `candidate_graph`
- `validation.status`
- `validation.validator`

Candidate submissions always use `status: candidate`. Admission lifecycle is never encoded by mutating the candidate file.

`source_context` is optional operational context. It is not proposition provenance and must not become a second evidence system.

`candidate_graph` must conform to the declared RGP major version and use candidate identities until Steward reconciliation assigns or reuses canonical identities.

A candidate intended for ordinary Steward reconciliation must pass deterministic RGP validation before submission. Invalid output preserved for evaluation belongs outside the project submission queue.

## Submission invariants

1. `submission_id` is unique to one exact candidate package.
2. `rgp_version` is explicit.
3. unknown RGP major versions are not guessed or coerced.
4. `status` is `candidate`.
5. the candidate graph passed the declared validator.
6. the submission artifact is immutable after persistence.
7. retries of the identical package reuse the same submission ID.
8. changed candidate semantics require a new submission ID.
9. submission metadata does not override RGP provenance.
10. submission does not imply admission, truth, lifecycle state, or normative authority.

## Steward disposition envelope

The Steward records reconciliation/admission outcome separately from the candidate submission.

```json
{
  "disposition_id": "RGPD-20260816T154200-0700-001",
  "submission_id": "RGP-20260816T153000-0700-001",
  "created_at": "2026-08-16T15:42:00-07:00",
  "steward": "project-steward",
  "disposition": "admitted",
  "record_map": {
    "r1": "canonical-record-id"
  },
  "relation_map": {},
  "reason_codes": ["IDENTITY_RECONCILED", "PROVENANCE_RESOLVED"],
  "canonical_commit": "optional immutable canonical-write identity"
}
```

Disposition values are:

```text
admitted
provisional
rejected
```

A disposition describes what happened to the candidate under project Steward policy. It does not change RGP proposition kinds.

`record_map` maps candidate identities to project canonical identities when reconciliation establishes them. `relation_map` is used only when the project's canonical model gives relations explicit identities. `reason_codes` are project/admission policy, not RGP ontology.

Include a canonical-write identifier only when persistence actually occurred and the immutable identity is known.

## Disposition immutability and reconsideration

A disposition is immutable once persisted. Later reconsideration creates a new disposition with an explicit `supersedes_disposition` reference. Historical candidate and disposition artifacts are never edited to simulate a different past outcome.

## Idempotency

The semantic idempotency key for candidate delivery is `submission_id`.

```text
same submission_id + identical candidate
    → reuse prior disposition or continue an incomplete safe transaction

same submission_id + different candidate bytes/semantics
    → hard error: submission identity collision

new submission_id + semantically duplicate graph
    → normal Steward reconciliation; reuse canonical identities when appropriate
```

A repository commit, object digest, or other immutable storage identity may prove exact submitted bytes, but semantic idempotency remains anchored to `submission_id`.

## Transaction boundary

Steward admission of connected reasoning must preserve graph integrity. The governed path must not persist a canonical result that:

- leaves required premise references dangling;
- admits a derived proposition while silently dropping constitutive premises;
- rewrites only one endpoint of a required relation;
- loses required provenance;
- creates canonical semantic identity collision;
- applies authority-sensitive lifecycle mutation without accepted project authority/policy.

## Producer responsibilities

An RGP producer must:

- produce candidate RGP, not canonical mutations;
- validate the candidate before ordinary submission;
- preserve opaque provenance IDs;
- keep operational context separate from proposition provenance;
- mint a new submission ID when candidate semantics change;
- persist only to the project-designated submission surface;
- never overwrite a committed submission;
- never claim Steward admission before a disposition exists.

## Steward responsibilities

A project-authorized Steward must:

- treat each submission as a proposal to canonical knowledge;
- verify submission identity and RGP compatibility;
- resolve provenance according to project policy;
- reconcile candidate semantic identities against canonical knowledge;
- preserve proposition kinds and graph meaning;
- classify the submission as admitted, provisional, or rejected;
- persist an immutable disposition;
- authorize canonical mutation only when project policy permits;
- preserve historical auditability;
- make repeated processing idempotent.

The generic Steward role contract does not itself grant project authority; the Project Knowledge Package supplies actual authority assignments.

## Failure conditions

The governed path stops and surfaces rather than guesses when:

- a submission ID is reused for different candidate semantics;
- the RGP major version is unsupported;
- validation evidence is missing or unacceptable;
- required provenance cannot be resolved under project policy;
- canonical identity reconciliation is ambiguous;
- graph admission would violate premise/relation integrity;
- canonical persistence would lose history, provenance, or required determinism;
- authority-sensitive conflict or supersession lacks accepted project authority.

## Contract separation

```text
RGP
    defines candidate reasoning meaning

RGP Submission Protocol
    transports immutable candidate packages and Steward outcomes

Project Knowledge Package
    supplies project-owned locations, rules, authority, evidence, and canonical-backend configuration

Canonical backend
    represents and persists admitted project knowledge
```

Keep these contracts independently versioned and independently evolvable.
