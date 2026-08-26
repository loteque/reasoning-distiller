# P10 Release-Candidate Evidence R3

Status: **PASS — ENGINEER RELEASE-CANDIDATE EVIDENCE**

This record is Engineer execution evidence for post-P10 integration and release preparation. It is not release authorization, a release publication, admission, canonical-state mutation, or authority mutation.

## Bound identities

Repository: `loteque/reasoning-distiller`

Coordination control:

- `main@80b6e89ad2efe84b088ca06b908a257c449fac15`

Closed P10 basis:

- semantic candidate: `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e`
- candidate tree: `81178c5efdc8f1419a068c61a92c0571b28f69fc`
- Engineer evidence: `ff09627f8e83abc60f430b378bed342cbeaceb79`
- Engineer evidence run: `32933482638`
- independent review: `53928833ff2735c08615c966c91e50f08322b4df`
- independent disposition: `P10_G9_INDEPENDENT_REVIEW_PASS`
- Steward closure: `631906e33c701d8a1eb6257b29d2402b23c9de28`
- Steward disposition: `P10_STEWARD_RECONCILIATION_ACCEPTED`

Landed packaged-PEMS runtime-isolation remediation:

- implementation candidate: `824c812ed6ffe79b6a9afe7bfc9c1f6eab656a27`
- candidate tree: `799e59a6de6e8f8ffecd41c0b81df9ec6e60e3c4`

Integration sequence:

- previously blocked integration: `b7c36e2fc8c9b09d899f4468e660e70a1d31a2c6`
- integration after exact landed remediation: `97dcca6a86354de4e0daf0a1c55205a0143e20a8`
- final integration after extraction-parity repair: `440b1d237814ec968e8afaf91612de1ce706a199`
- final clean RC source: `79f253d2053b03223da524f6f50c218728018248`
- final clean RC source tree: `b68022e16b0519ec2d73e16cef3f82c58be251d0`

The clean-source transformation from the final integration removes only `.reasoning-distiller/**`.

## Exact integration seams

### Landed runtime-isolation remediation

The delta from the blocked integration to `97dcca6a86354de4e0daf0a1c55205a0143e20a8` is exactly:

- `packaging/audit_runtime_isolation.py`
- `schemas/resources/context-packaging-v1-resource-registry.json`
- `tests/test_p10_packaged_pems_runtime_isolation_remediation.py`

Those three files are byte-identical to the landed remediation candidate `824c812ed6ffe79b6a9afe7bfc9c1f6eab656a27`.

The closed P10 semantic paths, including `schemas/context-pack.schema.json`, remain byte-identical to closed P10 candidate `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e`.

### Extraction-parity repair

Live `main` already had a stale Extraction Parity failure because `docs/extraction/copied-artifacts.json` still required byte identity between the evolved framework-owned Distiller directive and its historical extracted source blob.

The delta from `97dcca6a86354de4e0daf0a1c55205a0143e20a8` to final integration `440b1d237814ec968e8afaf91612de1ce706a199` changes only:

- `docs/extraction/copied-artifacts.json`

For the `agents/distiller/DIRECTIVE.md` entry only, `bytes_must_match_during_parity` changes from `true` to `false`. Historical source repository, branch, commit, source path, source blob SHA `d578841d64da93f0883686eda80f00fde53d5f66`, and classification `framework` remain unchanged. Every other copied-artifact parity flag remains unchanged.

No packaged runtime file or closed P10 semantic byte is changed by this extraction-parity repair.

## R3 execution evidence

Evidence workflow:

- branch: `evidence/p10-release-candidate-r2-20260826`
- workflow commit: `0115070b8eb41a071a62a52af02d00d578c6424b`
- workflow: `.github/workflows/p10-release-candidate-r3-evidence.yml`
- GitHub Actions run: `32958809163`
- job: `98146361029`
- conclusion: **SUCCESS**
- runtime implementation: `cpython`
- runtime version: `3.12.0`
- runtime cache tag: `cpython-312`

The run established PASS evidence for:

1. exact clean-source commit/tree identity and absence of `.reasoning-distiller/`;
2. exact closed-P10 semantic byte identity;
3. exact three-file landed runtime-isolation remediation seam;
4. exact one-file extraction-parity repair and preserved historical provenance;
5. clean-source transformation deleting only `.reasoning-distiller/**`;
6. release-workflow coverage for the `context_packaging` managed root;
7. package builder, package contract, and installer-runner contract suites;
8. two byte-identical deterministic RC package builds;
9. deterministic installer and recovery suites;
10. runtime-isolation suite, including frozen packaged PEMS-reference closure, missing-registry fail-closed behavior, and PEMS-byte-drift fail-closed behavior;
11. production-invocation suite;
12. current context-packaging regression suite on exact CPython 3.12.0;
13. explicit reproduction of the accepted PS-19 historical-classification mismatch and the superseded P5 `pack_builder.py` blob assertion rather than silently ignoring them;
14. extraction-parity release checks, including fixture validation, project-package validation, framework isolation, retained copied-artifact/corpus integrity checks, RGP validation, PEMS/COVE validation, and admission pressure checks;
15. exact R3 evidence report generation and evidence-artifact upload.

Current context-packaging regression result in R3 was `269 passed, 2 skipped, 2 deselected, 162 subtests passed`; the two deselected historical assertions were independently exercised as explicit witnesses in the same successful job.

## Exact RC package identity

- test-only RC version: `0.0.0-p10-rc3`
- source commit: `79f253d2053b03223da524f6f50c218728018248`
- source tree: `b68022e16b0519ec2d73e16cef3f82c58be251d0`
- file count: `99`
- content identity: `sha256:91e66afc72228a6d9038e3cf825dba41e97d7ce46023fcc470dbeee306e7deb4`
- transport SHA-256: `4fa53c1c4afb3ba07eb365158b4ec5e2a8090284aa485d07b0e35abcfa323cde`

R3 built the package twice and verified byte identity of archive, manifest, and detached digest.

Evidence artifact:

- artifact name: `p10-release-candidate-evidence-r3`
- artifact ID: `9603058509`
- artifact ZIP SHA-256: `4090c95f34a74f913fd3e9e9528e4c101d2a7869254f69be774e6550c388e971`

## Release boundary

At the completion of this Engineer evidence run:

- live `main` remains `80b6e89ad2efe84b088ca06b908a257c449fac15`;
- official `release-source` remains `1d781baf8be8f21d25eb85ddc340f1d2bc93922b`;
- no release version was selected for publication;
- no immutable release tag was created;
- no GitHub release was published;
- no official release assets were published;
- no merge to `main` occurred;
- no admission occurred;
- no canonical/project-knowledge mutation occurred;
- no role, authorization, or activation mutation occurred.

The validated clean source and R3 evidence satisfy this bounded Engineer release-preparation work unit. The repository's P8 operator release procedure still requires a separately authorized release operation to choose an intended release version, independently rebuild/compare the canonical content identity and transport digest, create the immutable version tag, publish release assets, and record durable release evidence. This Engineer record does not perform or authorize those steps.
