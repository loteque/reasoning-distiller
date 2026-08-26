# P5 Pure Pack Build Remediation on Closed `/2` Amendment

Status: **implementation candidate basis**

Repository: `loteque/reasoning-distiller`

Bound evidence:

- coordination control: `main@40241e24ecca2dacf0848ee28cf1ddc1410d15f1`
- governing plan: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- closed P4 semantic base: `c5e265aa2c572b6156c987bfa75e3740c097f2ec`
- prior P5 candidate: `a8a0592a69b325d411b36bbc97deadee796c3fd7`
- P5 independent review: `0df24253d653725686a616e3cb4ddbd581a4bd13`
- closed `/2` amendment candidate: `8abe0fb4f96f12fa6ed9503a99753d93442cdf0e`
- amendment independent review: `b12c22ce13af3fc1297059e226ee0e0e82a4b120`
- amendment Steward closure: `86bbf7a812e26a2e785f51d1d70e0dfd16d605f2`

## Scope

This candidate remediates P5 only. It does not begin P6 persistence, admission,
canonical mutation, rendering, production integration, authority mutation, or
successor activation.

The closed amendment is consumed as an immutable prerequisite. Its accepted
schema, bytes/digests/toolchain, builder-behavior, pressure-case, independent
review, and Steward-closure artifacts are not edited by this remediation.

## Remediation

1. The public pure builder explicitly dispatches matching `/1` and `/2`
   profile/request families and fails closed on cross-family combinations.
2. `/2` is the full-domain P5 path. Knowledge semantic-item provenance is keyed
   by `(canonical_snapshot_ref, namespace, id)` and emitted as
   `pems_ref {namespace,id}`. Record and relation IDs may therefore share the
   same opaque string without conflation.
3. `/1` remains a legacy-compatible family and is never auto-upgraded. Its
   scalar `semantic_id` representation remains unable to encode a
   record/relation same-string collision, which continues to fail closed rather
   than guessing a namespace.
4. Every SHA-256 spelling copied into builder-owned canonical pack structure is
   normalized to lowercase before identity construction. This includes source
   registry/snapshot-reference digests, standing evidence, COVE identities,
   operational validation-result identities, toolchain component digests, and
   generated payload/receipt/identity digests.
5. Snapshot matching preserves the P2 case-insensitive SHA-256 identity
   semantics, so equivalent digest spelling cannot create a P5-only identity
   split.
6. `/2` toolchain validation requires the immutable PEMS schema bytes frozen by
   the closed amendment:
   `git-blob:cd7683d704e8aef2842a0c1b25b453fb1dbc8030`,
   raw SHA-256
   `sha256:b08e592ab7c10092ff381fe8057cac63ccb7aaa077b52532f5ee609c6fd279c3`.

## Compatibility shape

The prior `/1` implementation is preserved byte-for-byte as
`context_packaging/pack_builder_v1.py`. The public `pack_builder.py` is the P5
family dispatcher plus `/2` implementation and canonical output finalizer.

This split is implementation structure only. It creates no canonical `/1` to
`/2` migration operation and does not change any accepted `/1` schema bytes.

## Required evaluation

Candidate evaluation must cover:

- exact P5 tests, including record/relation same-string identity;
- lowercase SHA-256 output and case-equivalent source/toolchain probes;
- cross-family rejection and explicit `/1` no-upgrade behavior;
- `/2` schema validation using the frozen immutable PEMS resource;
- COVE/P4 integration;
- unaffected P1-P4 regression suites;
- the three inherited P5-review reds as separately classified evidence.

A passing implementation test run is not independent review, Steward
reconciliation, P6 authorization, admission, or canonical standing.
