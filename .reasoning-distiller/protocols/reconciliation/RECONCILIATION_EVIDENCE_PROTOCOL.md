# RGP Reconciliation Evidence Protocol

## Status

This is an additive companion to the RGP Submission Protocol. It never mutates an existing immutable candidate submission or Steward disposition.

It defines the evidence package required when a project-authorized Steward must independently reconcile a candidate against a specific project canonical snapshot without relying on producer assertions or mutable branch state.

## Principle

A candidate submission carries semantic RGP content. A reconciliation evidence bundle carries immutable evidence required to evaluate that candidate against a project knowledge snapshot.

The bundle is evidence, not authority. It does not change candidate semantics and does not grant admission.

## Project surface

The consuming Project Knowledge Package identifies the project-owned evidence location and canonical backend/configuration. This protocol does not hard-code repository, branch, path, or backend names.

Once persisted, an evidence bundle is immutable. Corrections or additional evidence require a new `evidence_id` and an explicit reference to the earlier bundle.

## Envelope

```json
{
  "evidence_id": "RGPE-20260816T170000-0700-001",
  "submission_id": "RGP-20260816T152100-0700-001",
  "created_at": "2026-08-16T17:00:00-07:00",
  "submission_snapshot": {
    "repository": "owner/repository",
    "commit": "<immutable-commit>",
    "path": "<project-submission-path>",
    "blob_sha": "<git-blob-sha>"
  },
  "canonical_snapshot": {
    "backend": "<backend-id>",
    "repository": "owner/repository",
    "commit": "<immutable-canonical-snapshot>",
    "artifacts": ["<project-canonical-artifact>"]
  },
  "contracts": [],
  "provenance_resolution_inputs": [],
  "identity_reconciliation_inputs": [],
  "validation_surfaces": []
}
```

Repository/commit/path fields illustrate one immutable locator strategy. A project may use another immutable locator accepted by its policy and backend contract.

## Required evidence classes

### Submission snapshot

Identify the exact candidate bytes with an immutable locator. The Steward must be able to verify that the evidence refers to the same immutable candidate package being reconciled.

### Canonical snapshot

Identify the exact canonical state against which reconciliation is requested. Mutable names alone are insufficient.

A Steward may choose a newer canonical snapshot at processing time, but reconciliation must then be repeated against that snapshot and the disposition must identify it.

### Contracts

List every normative contract required to interpret the candidate and project canonical state. Contract references must resolve to immutable versions accepted by project policy.

Typical classes include:

- RGP protocol/schema and validator;
- RGP Submission Protocol;
- project Steward admission policy;
- Project Knowledge Package contract;
- selected canonical-backend contracts and deterministic persistence rules.

The protocol does not require PEMS/COVE or any other specific backend.

### Provenance resolution inputs

For every external RGP provenance identifier, provide an immutable locator sufficient for the Steward to inspect the evidence and determine whether the project's canonical source model already represents it.

Producer-supplied candidate canonical matches are non-authoritative hints.

```json
{
  "rgp_source_id": "opaque RGP provenance ID",
  "locator": {
    "repository": "owner/repository",
    "commit": "immutable commit",
    "path": "path/to/evidence"
  },
  "candidate_canonical_source_ids": []
}
```

### Identity reconciliation inputs

For each candidate record, provide deterministic search material without asserting the result:

- candidate record ID;
- proposition kind;
- exact statement;
- known canonical IDs that appear semantically similar, when available;
- why those IDs were selected as search candidates.

Only a project-authorized Steward may establish reuse versus creation.

### Validation surfaces

Identify immutable validator/schema artifacts and deterministic procedures needed to validate:

- RGP graph structure;
- submission/evidence envelopes;
- selected canonical backend state;
- deterministic proof/round-trip behavior required by that backend.

A claimed pass is evidence but does not replace the Steward's ability to independently inspect or rerun the accepted validation surface.

## Completeness invariant

A reconciliation evidence bundle is admission-ready only when a fresh authorized Steward can, from the bundle and referenced immutable artifacts alone:

1. acquire the exact candidate;
2. acquire the exact canonical state being reconciled;
3. interpret all relevant contracts;
4. inspect every required external provenance source;
5. search/reconcile every candidate semantic identity;
6. verify graph integrity;
7. determine the canonical transaction required by an admitted disposition;
8. validate the resulting canonical representation using the selected backend.

If any step requires trusting an unreferenced producer assertion or mutable project state, the bundle is incomplete.

## Immutable audit chain

The original candidate submission is never edited to add reconciliation evidence. A prior disposition is never edited after persistence. Reconsideration consumes the original artifacts plus new immutable evidence and creates a new disposition that explicitly supersedes the prior outcome.

```text
candidate submission
      ↓
initial disposition
      ↓
additional immutable evidence
      ↓
new Steward reconciliation
      ↓
superseding disposition
      ↓
canonical transaction, if admitted
```

## Producer boundary

An RGP producer or Engineer may assemble immutable evidence and candidate reconciliation hints. It must not:

- claim that a hinted canonical identity is authoritative;
- create or bind project canonical identities on the Steward's behalf;
- mutate project canonical knowledge;
- overwrite a prior Steward disposition;
- describe evidence preparation as admission.

The purpose of the evidence bundle is to make independent Steward judgment possible, not unnecessary.
