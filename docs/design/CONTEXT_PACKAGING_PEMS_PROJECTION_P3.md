# P3 PEMS Projection Implementation Note

Status: **P3 implementation candidate note, non-governance artifact**

## Bound basis

- live-main basis inspected before implementation: `58b99891e116b5a06dd603810c2b98ea83e328c3`
- governing plan: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- exact closed P2 semantic base: `f8177ce3d4d5b1c7edf7d3c0088db3d658b12072`
- P1d closure descriptor contract: `reasoning-distiller-pems2-closure-descriptor/1`
- bound PEMS/2 schema Git blob: `cd7683d704e8aef2842a0c1b25b453fb1dbc8030`
- bound PEMS/2 semantic-validator Git blob: `d615bf2e95d3721b0ca312075cc0c39522f0a896`

The durable repository evidence at commits
`200fc6fe8f3095583ac9d2269644c2227319d065` and
`4b66998b53cc5d41955508ed7eefa52d2c73658f` records, respectively,
`P2_INDEPENDENT_REVIEW_PASS` and `P2_STEWARD_RECONCILIATION_ACCEPTED`. The
Steward artifact explicitly authorizes a fresh implementation Engineer to begin
P3 only from the exact P2 semantic base above. This note does not recreate or
broaden that authority decision.

## Implemented P3 scope

`context_packaging/pems_projection.py` implements only the P3 projection gate:

1. consume exact request selectors and P2 `ResolvedSource` canonical snapshots;
2. bind the profile to the package-owned P1d closure descriptor by contract,
   semantic, Git-blob identity, and raw SHA-256;
3. verify the exact PEMS schema and semantic-validator Git blobs named by that
   descriptor;
4. parse strict UTF-8 JSON and validate the complete canonical PEMS/2 source;
5. seed closure from exact selected record/relation IDs plus the frozen root
   project rule;
6. apply only frozen `include_transitively`, `preserve_external_reference`, and
   `reject` descriptor outcomes;
7. apply only the frozen derived-proposition inverse structural rule;
8. terminate cycles by `(namespace, id)` and retain every deterministic
   request-selector / PEMS-closure cause;
9. reject missing IDs, undefined closure rules, schema/semantic invalidity, and
   explicit projection bounds without truncation;
10. validate the complete selected PEMS/2 projection under both package-owned
    validators before returning success.

P3 retains source PEMS record/relation order and deep-copies selected objects. It
does not rewrite semantic fields, provenance, lifecycle, relation endpoints, or
canonical state.

### Depth and aggregate limit mechanics

For this implementation, explicit selectors and descriptor root rules are depth
zero. Each required transitive or structural closure edge adds one. A target
already reached at a shallower depth is not rejected merely because another
valid cause reaches it through a longer path.

`max_records`, `max_relations`, and `max_bytes` bound the complete projection set
across selected canonical snapshots. `max_depth` bounds each snapshot closure.
`max_bytes` is measured with the frozen P1c RFC 8785 / `jcs/1` behavior. None of
these limits truncate required closure.

## Reproducible cause boundary

P3 returns a deterministic cause tuple for each included `(namespace, semantic
id)`. Cause kinds are restricted to the already frozen later-ledger vocabulary
needed here:

- `request_selector`
- `pems_closure`

Cause IDs are injective structured JSON strings prefixed with `p3:`. P3 does not
construct the P5 context-pack inclusion ledger.

## Explicit exclusions

This candidate does **not** implement or claim:

- P4 COVE encoding or round-trip validation;
- P5 canonical context-pack construction, digests, receipts, or persistence;
- P6 renderer integration;
- P7 production `rd-distill` integration;
- source discovery or mutable rebinding;
- profile-eligibility decisions;
- canonical admission, mutation, reconciliation, or standing creation;
- role registration, authorization, or RIL activation.

A passing P3 test suite would be implementation evidence only. It would not be
independent review, Steward reconciliation, admission, authority, or activation.
