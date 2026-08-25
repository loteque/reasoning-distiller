# P8 Independent Review: Authority and Memory Isolation Gate

Disposition: **P8_INDEPENDENT_REVIEW_PASS**

## Bound review basis

- Repository: `loteque/reasoning-distiller`
- Coordination control ref: `main`
- Coordination revision independently resolved before review: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Coordination revision re-resolved before disposition: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- Closed P7 base: `d4557ef183731304401444f42cf62819cae567af`
- Exact P8 candidate: `05d9d7b0141cd7fa5e66dd72533b57e046001247`
- Exact candidate parent: `d4557ef183731304401444f42cf62819cae567af`
- Candidate branch re-resolved before disposition: `implement/context-packaging-p8@05d9d7b0141cd7fa5e66dd72533b57e046001247`
- P8 test path: `tests/test_context_packaging_authority_memory_isolation_p8.py`
- P8 test blob: `4c82429ce24b2efe98c4f76248c091dfd064cea4`
- Engineer evidence commit: `82ce49ad42c67fb4e35724b938ccf1c26e8dce11`
- Engineer evidence PR: `#77`
- Candidate-bound evidence run: `32798111034`
- Independently triggered rerun: run `32798111034`, attempt `2`, PASS
- `source_resolver.py` blob observed by the bound workflow: `11da98c213e783ed4c31f88392eb6a5634c9643e`
- `pack_builder.py` blob observed by the bound workflow: `167602c87ea1766ae9978ed8a67098613e1f96ff`
- P5 fixture blob observed by the bound workflow: `5fd7fc17a01877f4add060357a6b28ee0eb0e096`
- P2 fixture blob observed by the bound workflow: `2d1440909fac27b345a3dcc85be9ce5f2adfc5c9`
- Active role: fresh independent Reasoning Graph Protocol Engineer, P8 review only.

The current Engineer directive, Project chat-transition amendment, and proposal-review method were read from the exact live coordination revision. This review establishes no Steward authority, accepted Steward activation, reconciliation, admission, canonical standing, canonical mutation, authority mutation, or P9+ successor scope.

## Independent reconstruction of the P8 gate

The governing plan makes P8 the authority/memory isolation gate. It requires adversarial exercise of role labels, ambient memory, prior candidates, authority-like knowledge, operational-evidence status, and canonical-standing attacks.

The P8 exit condition is semantic rather than cosmetic: no source may be auto-selected or promoted, and no authority, activation, or canonical standing may be inferred from data that does not itself carry the exact governed evidence required for that status.

The surrounding frozen contracts also preserve the separation between explicit source selection and hidden discovery/relevance, between carried status and inferred authority, and between canonical-looking bytes and accepted canonical standing. P8 does not authorize any mutation surface.

## Candidate inspection

Candidate `05d9d7b0141cd7fa5e66dd72533b57e046001247` is exactly one commit above closed P7 base `d4557ef183731304401444f42cf62819cae567af`.

The candidate delta adds only:

- `tests/test_context_packaging_authority_memory_isolation_p8.py`

No production implementation, schema, authority state, activation state, canonical state, persistence adapter, admission path, or reconciliation path is modified by P8.

The exact P8 test blob is `4c82429ce24b2efe98c4f76248c091dfd064cea4`.

## Adversarial coverage inspection

The P8 suite exercises the frozen pressure-case categories through the real P2 resolver and P5/P7 builder path rather than a replacement P8 implementation.

Observed coverage includes:

1. **Role labels cannot create activation.** Authority-like control bytes and role labels are treated as exact data. When runtime activation evidence is required but absent, resolution/building fails closed rather than treating the label as activation.
2. **Ambient memory is not a source class.** An `ambient_memory` source request is rejected as unsupported rather than discovered, selected, or converted into a supported repository source.
3. **Prior candidates are not silently promoted.** Adding an unselected prior candidate to the available resolved-source set does not place it in the output pack and does not change output bytes for the explicit request.
4. **Authority-like knowledge remains knowledge.** Canonical knowledge containing authority-shaped or instruction-like content remains in the knowledge plane and does not create top-level authority, activation, or canonical standing.
5. **Operational evidence status is carried, not promoted.** Selected evidence preserves its supplied validation/status payload but does not become authority merely because it is operational evidence.
6. **Unvalidated claims remain unvalidated.** A carried operational claim containing words such as accepted, authorized, or activated does not become accepted evidence or authority by semantic resemblance.
7. **Canonical-looking bytes do not prove standing.** Snapshot bytes without accepted canonical standing fail closed with `CANONICAL_BINDING_UNPROVEN` rather than being promoted because their contents or pathname appear canonical.
8. **Pressure-case binding remains explicit.** The suite binds the required P8 pressure-case IDs from the frozen adversarial fixture and separately exercises the corresponding semantic attack classes.

I found no P8-advertised attack category that could create hidden source selection, semantic promotion, authority inference, activation inference, or canonical-standing inference under the inspected candidate behavior.

## Candidate-bound Engineer evidence inspected

The Engineer evidence workflow was inspected rather than accepted from the summary alone. It explicitly:

- checks out exact candidate `05d9d7b0141cd7fa5e66dd72533b57e046001247`;
- verifies exact parent `d4557ef183731304401444f42cf62819cae567af`;
- verifies that the P8 candidate delta is limited to the P8 test module;
- verifies P8 test blob `4c82429ce24b2efe98c4f76248c091dfd064cea4`;
- records the production/helper blobs used by the test path;
- runs the exact P8 suite;
- runs unaffected P0-P7 regressions while preserving known inherited reds separately; and
- reproduces the known PS-19 classifier mismatch separately instead of treating it as PASS evidence.

Engineer evidence run `32798111034` completed successfully.

## Independent execution

This review independently triggered a fresh execution of the already-inspected candidate-bound workflow. GitHub recorded it as run `32798111034`, attempt `2`, and it completed successfully.

Observed attempt-2 results:

- exact candidate check: PASS
- exact parent check: PASS
- exact P8 test blob check: PASS
- P8 pytest suite: **9 passed**
- P8 unittest suite: **9 tests, all PASS**
- unaffected P0-P7 regressions: **156 passed, 2 deselected, 162 subtests passed**
- known PS-19 mismatch reproduced separately: expected `UNKNOWN_SEMANTICS_FIELD`, observed `PLANE_CLASSIFICATION_CONFLICT`

This is a fresh execution of the candidate-bound workflow, not a claim that the review authored a separate independent test harness.

## Repository-wide reds preserved separately

The evidence head also triggers broader repository workflows. Their failures were inspected and are not converted into P8 PASS evidence.

### RIL Test Suite

The repository-wide unittest run executed 573 tests and failed exactly three:

1. **Inherited PS-19 classifier mismatch**: expected `UNKNOWN_SEMANTICS_FIELD`, observed `PLANE_CLASSIFICATION_CONFLICT`.
2. **Inherited P5 implementation-freeze sentinel**: `test_p5_runtime_implementation_is_unchanged_by_amendment` still hard-codes the earlier `pack_builder.py` blob `b0e806e966598e6d819b6d52c643efa23cdb6ef9`, while the closed P7 base already carries `167602c87ea1766ae9978ed8a67098613e1f96ff` after the later reproducibility work.
3. **Inherited runtime-isolation audit red**: `schemas/context-pack.schema.json` contains the previously known repository reference that the audit classifies as a forbidden runtime reference.

All nine P8 tests pass inside this repository-wide run. Because the P8 candidate adds only the P8 test module, none of these three failures originates in the P8 delta.

### Extraction Parity

Extraction Parity passes RGP fixture parity, Project Knowledge Package contract checks, and framework/authority-boundary checks, then fails at the inherited frozen-source integrity check:

- `agents/distiller/DIRECTIVE.md`: expected blob `d578841d64da93f0883686eda80f00fde53d5f66`, observed `81291456b127015b813af4eda4046397b4815037`

This same frozen-blob mismatch was already recorded as an inherited red during the closed P7 review. P8 does not modify the Distiller directive or the extraction-parity corpus.

## Review note

The P8 test names group several frozen pressure-case IDs into semantic families rather than providing a one-test-per-case fixture replay. The suite also checks fixture membership/metadata separately from the production-path attack executions. I do not classify this as a blocker because the governing P8 exit condition is independently exercised across all advertised attack categories through the real resolver/builder behavior, and no missing semantic attack surface was identified.

## Independent review disposition

**P8_INDEPENDENT_REVIEW_PASS**

Candidate `05d9d7b0141cd7fa5e66dd72533b57e046001247` satisfies the independently reconstructed P8 authority/memory isolation gate on the evidence inspected and independently re-executed here.

No P8-local blocking finding was identified. The repository-wide reds remain inherited and separate; this disposition does not claim they are fixed.

## Terminal boundary and bounded handoff

This independent-review activation ends with the P8 disposition. It does not begin P9+, Steward reconciliation, admission, canonical mutation, or authority mutation.

If continuation is selected, the next consequential stage belongs to a **fresh Project Engineering Steward activation scoped only to P8 reconciliation**. That activation must independently establish whatever Steward authority and accepted activation evidence the live repository contracts require, then reconcile exact candidate `05d9d7b0141cd7fa5e66dd72533b57e046001247` against this independent review evidence and Engineer evidence `82ce49ad42c67fb4e35724b938ccf1c26e8dce11`.

This handoff does not itself create Steward authority or accepted activation evidence.
