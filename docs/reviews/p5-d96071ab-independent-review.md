# P5 Independent Review: Remediated Pure Pack Build

Disposition: **P5_INDEPENDENT_REVIEW_PASS**

## Bound review basis

- Repository: `loteque/reasoning-distiller`
- Coordination control ref: `main`
- Coordination revision independently resolved before review: `40241e24ecca2dacf0848ee28cf1ddc1410d15f1`
- Coordination revision re-resolved immediately before this review write: `40241e24ecca2dacf0848ee28cf1ddc1410d15f1`
- Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- Closed P4 semantic base: `c5e265aa2c572b6156c987bfa75e3740c097f2ec`
- Prior P5 candidate: `a8a0592a69b325d411b36bbc97deadee796c3fd7`
- Prior P5 review: `0df24253d653725686a616e3cb4ddbd581a4bd13`
- Prior disposition: `P5_INDEPENDENT_REVIEW_CHANGES_REQUIRED`
- Closed `/2` amendment candidate: `8abe0fb4f96f12fa6ed9503a99753d93442cdf0e`
- Amendment independent review: `b12c22ce13af3fc1297059e226ee0e0e82a4b120`
- Amendment Steward closure: `86bbf7a812e26a2e785f51d1d70e0dfd16d605f2`
- Remediated P5 semantic candidate: `d96071ab833179948e5f9526cdb63c15c6451ff4`
- Direct parent: `8abe0fb4f96f12fa6ed9503a99753d93442cdf0e`
- Implementation branch re-resolved during review: `implement/context-packaging-p5-remediation-v2` was identical to `d96071ab833179948e5f9526cdb63c15c6451ff4`.
- Durable Engineer execution evidence: `866683e8b6779513d5d4424693e997e5417ad57d`
- Active review role: independent Reasoning Graph Protocol Engineer, P5 review/evidence only.

The current Engineer directive and chat-transition contract were read from the live coordination revision before consequential review work. This review does not establish Steward authority, admission authority, canonical standing, registration, authorization, or successor activation.

## Independent reconstruction

The P5 exit criterion remains a pure deterministic pack build: materialize canonical separated planes, source registry, inclusion ledger, toolchain identity, and digest structure without persistence side effects, with deterministic causes and identities, fail-closed plane conflicts, and byte-identical repeated builds.

The prior independent review identified two P5-local blockers:

1. newly emitted canonical pack structure preserved uppercase SHA-256 spellings despite the frozen P1c requirement that canonical builder output use lowercase hexadecimal; and
2. the `/1` outer-ledger scalar `semantic_id` could not represent a P1d/P3-valid record/relation same-string ID collision, causing P5 to reject a valid namespaced projection.

The closed `/2` amendment resolved the protocol prerequisite without changing P1d/P3 semantics: canonical `/2` semantic subjects use exact `source_ref` plus structural `pems_ref {namespace,id}`, matching identity `(JCS(canonical_snapshot_ref), namespace, id)`; `/1` and `/2` families are explicitly dispatched; cross-family combinations fail closed; no public `/1` to `/2` migration exists; and the successor bytes/digests/toolchain contract retains lowercase canonical SHA-256 emission.

## Candidate inspection

The remediated candidate is exactly one commit above the closed amendment basis. Its semantic diff is limited to:

- `context_packaging/__init__.py`;
- `context_packaging/pack_builder.py`;
- added `context_packaging/pack_builder_v1.py`;
- `tests/test_context_packaging_pack_builder_p5.py`; and
- `docs/design/CONTEXT_PACKAGING_PURE_PACK_BUILDER_P5_REMEDIATION.md`.

No schema, P1d/P3 semantic contract, persistence, renderer, admission, production-integration, authority, or canonical-state file is changed by this candidate.

The preserved `/1` implementation blob is `b0e806e966598e6d819b6d52c643efa23cdb6ef9`, the same former P5 builder blob frozen by the amendment transition sentinel. Public dispatch accepts matching `/1` and `/2` profile/request families, rejects cross-family combinations, and keeps `/1` output as `/1`; it does not infer or synthesize a namespace for legacy scalar provenance.

The `/2` builder groups semantic provenance by exact `(namespace, semantic_id)` tuples, validates complete coverage against the distinct record and relation namespaces, and emits `pems_ref {namespace,id}`. Thus a record and relation sharing the string `shared` remain distinct subjects rather than colliding or being guessed apart.

Before final canonical identity construction, the builder normalizes SHA-256 spellings in builder-owned canonical source identities, standing evidence, COVE identities, operational validation-result identities, carried payload digest fields, and toolchain component identities. Generated domain-separated and raw digests already use lowercase hexadecimal. Case-equivalent source identity remains matched through the pre-existing P2 normalization semantics.

The `/2` toolchain path also binds the amendment-frozen immutable PEMS resource blob `cd7683d704e8aef2842a0c1b25b453fb1dbc8030` and raw SHA-256 `sha256:b08e592ab7c10092ff381fe8057cac63ccb7aaa077b52532f5ee609c6fd279c3`.

## Exact-candidate execution inspection

This review independently inspected the workflow definition, workflow status, step status, and raw job log for Engineer run `32710342275`, job `97380182844`, rather than treating the Engineer manifest alone as sufficient review evidence.

The workflow checked out `d96071ab833179948e5f9526cdb63c15c6451ff4` directly in detached-HEAD state and asserted:

- `HEAD == d96071ab833179948e5f9526cdb63c15c6451ff4`;
- `HEAD^ == 8abe0fb4f96f12fa6ed9503a99753d93442cdf0e`;
- `/2` dispatcher/builder blob `c7a87dae852de2cb58393fa3bc6dd9241a2155f0`;
- preserved `/1` builder blob `b0e806e966598e6d819b6d52c643efa23cdb6ef9`;
- P5 test blob `5fd7fc17a01877f4add060357a6b28ee0eb0e096`;
- package export blob `a70ce6a24ab64efb8171bd95c7907fa22b7de63f`; and
- remediation-note blob `0e23bb010f61b0765f63d3db291444bd3088478d`.

Observed exact-candidate results:

- exact P5 suite: **17 passed**;
- unaffected P0-P4 plus closed `/2` amendment regressions: **119 passed, 160 subtests passed, 1 deselected**;
- explicit lowercase SHA-256 pressure probe: **PASS**, including byte-equivalence under uppercase-vs-lowercase source digest spelling;
- explicit namespaced same-string record/relation provenance probe: **PASS**;
- no additional P5-local failure was observed in the standing repository-wide unit suite.

The P5 suite itself covers deterministic reordering, namespaced record/relation collision, preservation of all causes, source/toolchain/validation-result lowercase digest behavior, exact raw-byte carriage, cross-family rejection, `/1` no-upgrade behavior, legacy collision fail-closed behavior, COVE/P4 integration, raw profile/request binding, byte limits, `/2` schema validation with the immutable PEMS resource, and absence of persistence/filesystem-write APIs in the builder sources.

A separate fresh review workflow was not necessary to establish candidate behavior because the existing candidate-bound workflow checked out the immutable candidate itself, and this review independently inspected its exact commands and raw outputs in addition to source and contract inspection.

## Original blocker dispositions

### Blocker 1: canonical SHA-256 spelling

**REMEDIATED.**

The implementation now normalizes builder-owned SHA-256 spellings before canonical pack identity construction. The exact-candidate P5 tests cover source, toolchain, and operational validation-result spellings, and the separate pressure probe demonstrated that an uppercase `pems_sha256` input produces the same serialized canonical pack bytes as the lowercase-equivalent input while emitting lowercase canonical output.

This satisfies the frozen P1c and `/2` successor rule without changing underlying source bytes.

### Blocker 2: namespaced PEMS selection provenance

**REMEDIATED on the closed `/2` basis.**

The governed amendment supplied the required lossless wire representation. The candidate consumes that basis exactly: same-string record/relation IDs are keyed and emitted as separate `pems_ref` subjects, with complete deterministic cause coverage. The exact-candidate pressure probe emitted both `('record', 'shared')` and `('relation', 'shared')`.

The legacy `/1` family remains `/1` and fails closed for the unrepresentable collision rather than guessing a namespace. No canonical `/1` to `/2` migration was introduced.

## Transition sentinel classification

The one deselected amendment-era test is correctly classified as `EXPECTED_AMENDMENT_TO_P5_TRANSITION_SENTINEL`.

That test's sole purpose is to assert that the protocol amendment itself did not mutate the then-current P5 runtime: it hard-codes expected `context_packaging/pack_builder.py` blob `b0e806e966598e6d819b6d52c643efa23cdb6ef9`.

The P5 remediation necessarily changes the public P5 builder to blob `c7a87dae852de2cb58393fa3bc6dd9241a2155f0`, while preserving the old `/1` implementation byte-for-byte at `context_packaging/pack_builder_v1.py` as `b0e806e966598e6d819b6d52c643efa23cdb6ef9`. The raw workflow log reproduced exactly that one assertion mismatch and no semantic amendment regression after excluding the now-expired transition assertion.

The sentinel therefore records a completed phase transition, not a P5-local defect.

## Inherited reds preserved separately

The three previously identified non-P5-local reds reproduce unchanged and remain outside this P5 disposition:

1. `P1B_PS19_CLASSIFIER_MISMATCH`: P1b negative fixture PS-19 still expects `UNKNOWN_SEMANTICS_FIELD` but observes `PLANE_CLASSIFICATION_CONFLICT`; exact run result `1 failed, 4 passed`.
2. `LEGACY_V1_RUNTIME_ISOLATION_MUTABLE_SCHEMA_REFERENCE`: runtime isolation still identifies the historical `/1` `schemas/context-pack.schema.json` PEMS `$ref` to `github.com/loteque/reasoning-distiller`; the candidate changes no schema file, and the closed `/2` path uses the immutable resource registry instead.
3. `EXTRACTION_PARITY_DISTILLER_DIRECTIVE_MISMATCH`: corpus integrity still expects Distiller directive blob `d578841d64da93f0883686eda80f00fde53d5f66` but observes `81291456b127015b813af4eda4046397b4815037`; the candidate changes neither the Distiller directive nor extraction manifest.

These were already present before this remediation, are outside the candidate's five-file diff, and do not invalidate the P5-local pass.

## Independent-review disposition

`P5_INDEPENDENT_REVIEW_PASS`

Both prior P5-local blockers are remediated against the closed `/2` amendment basis. Exact-candidate execution is green for the P5 suite and the unaffected P0-P4/amendment regression set, with the amendment-era transition sentinel correctly isolated and the three inherited reds preserved separately. No new P5-local blocking finding was identified.

This review closes only the independent-review work unit. It does **not** itself close P5, perform Steward reconciliation, authorize P6, begin persistence, admission, canonical mutation, rendering, production integration, mutate authority, or activate a successor role.

The next governed work, if selected, is a fresh Project Steward activation that independently establishes whatever Steward authority/activation the live contracts require and reconciles exact P5 candidate `d96071ab833179948e5f9526cdb63c15c6451ff4` against this independent-review evidence. No P6 work begins from this review.