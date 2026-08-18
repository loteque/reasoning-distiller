# RGP Reconciliation Evidence Protocol

## Status

This is an additive companion to `SUBMISSION_PROTOCOL.md`. It does not mutate an existing immutable candidate submission or Steward disposition.

It defines the evidence package required when a Steward must independently reconcile a candidate against canonical PEMS/2 without relying on producer assertions or mutable branch state.

## Principle

A candidate submission carries semantic RGP content. A reconciliation evidence bundle carries immutable evidence needed to evaluate that candidate against a specific canonical-memory snapshot.

The bundle is evidence, not authority. It does not change candidate semantics and does not grant admission.

## Repository Surface

Evidence bundles live under:

```text
docs/handoff/rgp/evidence/
```

Recommended filename:

```text
<SUBMISSION_ID>.evidence.json
```

Once committed, an evidence bundle is immutable. Corrections or additional evidence require a new evidence artifact with a distinct `evidence_id` and an explicit reference to the earlier bundle.

## Envelope

```json
{
  "evidence_id": "RGPE-20260816T170000-0700-001",
  "submission_id": "RGP-20260816T152100-0700-001",
  "created_at": "2026-08-16T17:00:00-07:00",
  "submission_snapshot": {
    "repository": "loteque/gdscript-voxel-engine",
    "commit": "<commit-containing-submission>",
    "path": "docs/handoff/rgp/submissions/<submission>.json",
    "blob_sha": "<git-blob-sha>"
  },
  "canonical_snapshot": {
    "repository": "loteque/gdscript-voxel-engine",
    "branch": "project-chat-handoff",
    "commit": "<canonical-snapshot-commit>",
    "pems_path": "docs/project-chat-handoff.json",
    "cove_path": "docs/project-chat-handoff.cove.json"
  },
  "contracts": [],
  "provenance_resolution_inputs": [],
  "identity_reconciliation_inputs": [],
  "validation_surfaces": []
}
```

## Required Evidence Classes

### Submission snapshot

Must identify the exact committed candidate bytes by repository, commit, path, and blob SHA. The Steward must be able to verify that the evidence bundle refers to the same immutable candidate package it is disposing.

### Canonical snapshot

Must identify the exact canonical PEMS/2/COVE commit against which reconciliation is requested. Branch names alone are insufficient because they are mutable.

The Steward may choose a newer canonical snapshot at processing time, but if it does so the disposition must record that newer commit and reconciliation must be repeated against it.

### Contracts

List every normative contract required to interpret the candidate and canonical state. Each contract reference must include an immutable commit plus path, or another immutable identifier accepted by project policy.

At minimum for ordinary RGP-to-PEMS/2 admission this includes:

- RGP protocol/schema and validator contract;
- RGP Submission Protocol;
- Steward RGP admission extension;
- PEMS/2 schema/semantic contract;
- COVE contract and deterministic representation rules used for persistence.

### Provenance resolution inputs

For every external RGP provenance identifier, provide an immutable locator sufficient for the Steward to independently inspect the evidence and determine whether a canonical PEMS source/source-observation already represents it.

The producer may provide candidate canonical matches as hints, but those hints are explicitly non-authoritative.

Each entry should include:

```json
{
  "rgp_source_id": "opaque RGP provenance ID",
  "locator": {
    "repository": "owner/repo",
    "commit": "immutable commit",
    "path": "path/to/file"
  },
  "candidate_canonical_source_ids": []
}
```

When the RGP provenance ID already is a canonical PEMS source/source-observation ID, record that fact and include the canonical snapshot containing it.

### Identity reconciliation inputs

For each candidate record, provide deterministic search material without asserting the result:

- `temp_id`;
- proposition kind;
- exact statement;
- any known canonical IDs that appear semantically similar;
- why those IDs were selected as search candidates.

A candidate canonical ID is a hint. Only the Steward may establish reuse versus creation.

### Validation surfaces

Identify immutable validator/schema artifacts and commands or deterministic procedures needed to validate:

- RGP graph structure;
- submission/evidence envelopes;
- PEMS/2 state;
- COVE representation;
- deterministic PEMS/COVE equivalence or round-trip behavior.

A claimed `passed` result is useful evidence but does not replace the Steward's ability to rerun or independently inspect the validation surface.

## Completeness Invariant

An evidence bundle is admission-ready only when a fresh Steward activation can, from the bundle and referenced immutable artifacts alone:

1. acquire the exact candidate;
2. acquire the exact canonical state being reconciled;
3. interpret all relevant contracts;
4. inspect every required external provenance source;
5. search/reconcile every candidate semantic identity;
6. verify graph integrity;
7. determine the canonical mutation required by an admitted disposition;
8. validate the resulting PEMS/2/COVE representation.

If any of these requires trusting an unreferenced producer assertion or mutable branch head, the bundle is incomplete.

## Relationship to Existing Immutable Artifacts

The original candidate submission is never edited to add reconciliation evidence.

The original Steward disposition is never edited after provisional disposition.

A later Steward reconsideration consumes the original submission plus one or more evidence bundles and creates a new disposition artifact with `supersedes_disposition` pointing to the prior disposition.

This preserves the audit chain:

```text
candidate submission
      ↓
initial provisional disposition
      ↓
additional immutable evidence
      ↓
new Steward reconciliation
      ↓
superseding disposition
      ↓
canonical mutation, if admitted
```

## Producer Boundary

The RGP Engineer may assemble immutable evidence and candidate reconciliation hints. It must not:

- claim that a hinted PEMS identity is authoritative;
- create canonical source/source-observation identities;
- mutate canonical PEMS/COVE;
- overwrite a provisional Steward disposition;
- describe an evidence bundle as admission.

The purpose of the evidence bundle is to make independent Steward judgment possible, not unnecessary.