# Self-Consumption Isolation Trial — Execution Record

Status: **PASS**

Specification: `docs/testing/CONSUMER_TRIALS.md`, Trial A.

Observed run: `https://github.com/loteque/reasoning-distiller/actions/runs/32140801260`
Run head: `296faea85d0468057da8f8168c69d8ed401b8a87`
Job: `self-consumption` (`95722723481`)
Conclusion: `success`
Artifact: `self-consumption-isolation-32140801260` (`9325780172`)
Artifact digest: `sha256:827344dd66e6b8f41d51f19b6475cbbf9ebd269bc56456dbb25458b2ae8ca96f`

## Motivation

This trial pressure-tests the boundary between the Reasoning Distiller development source tree and a project-local installation of its accepted release. Success requires consumer operations to continue while the adjacent source framework directories are physically unavailable.

## Selected release

| Property | Value |
|---|---|
| Release | `0.2.0` |
| Tag | `v0.2.0` |
| Source commit | `c7daed110e58627d0ab2566298cc433615ee4452` |
| Content identity | `sha256:75736b1b8522f568cf172058ea97b8216501d4faaf2d4fa32ff7056181c42add` |
| Transport SHA-256 | `d5273f9181e286c592db21e636c67b8dfb3f3a3dc39608cf34e6f66557a477e1` |

## Observed execution

Every measured harness step completed successfully. The run:

1. began from a clean checkout with no `.reasoning-distiller/` tree;
2. retrieved the seven `v0.2.0` release assets with read-only repository permission;
3. verified release version, release source commit, content identity, and archive transport SHA-256;
4. self-installed `v0.2.0` into `.reasoning-distiller/` using the released deterministic installer;
5. created project-owned fixed evidence and an invocation request outside the managed tree;
6. successfully ran installed `.reasoning-distiller/runtime/rd_distill.py prepare`;
7. supplied a controlled provider-boundary raw RGP candidate grounded in that evidence;
8. moved source `agents/`, `admission/`, `backends/`, `protocols/`, `runtime/`, `schemas/`, and `validators/` out of the repository workspace and verified those source paths were absent;
9. while source was denied, successfully repeated installed `prepare` and ran installed `finalize`;
10. byte-compared the preserved raw candidate with the provider-boundary output;
11. verified invocation result `PASS`, candidate status, producer role, unchanged candidate graph, and absence of canonical mutation;
12. audited `.reasoning-distiller/` and observed `PASS` with zero runtime-isolation violations;
13. restored source only after the measured isolation operation and verified the remaining working-tree additions were the local installation and project-owned trial material;
14. emitted the durable run artifact.

The controlled provider-boundary output tests the product invocation boundary and source isolation; it is not a reasoning-quality evaluation and does not claim to test a particular hosted model provider.

## PASS criteria disposition

| Property | Result |
|---|---|
| Release installation | PASS |
| Installed identity | PASS |
| Runtime locality | PASS |
| Source isolation | PASS |
| Invocation | PASS |
| Raw preservation | PASS |
| Immutable candidate submission | PASS |
| Distiller authority stop / no canonical mutation | PASS |
| Source/project ownership boundary | PASS |
| Runtime-reference audit | PASS — zero violations |

## Durable run evidence

The workflow artifact contains:

- trial base SHA;
- installer result;
- invocation result;
- runtime-isolation audit;
- final Git status;
- invocation request;
- activation bundle;
- byte-preserved raw candidate;
- immutable submission;
- installed `INSTALLATION.json`;
- installed `MANIFEST.json`.

Artifact ID `9325780172` was uploaded by the successful run with digest `sha256:827344dd66e6b8f41d51f19b6475cbbf9ebd269bc56456dbb25458b2ae8ca96f` and expiry reported by GitHub as 2026-11-16. This execution record preserves the durable identities and disposition even after ephemeral artifact expiry.

## Finding SCIT-001 — installation documentation staleness

Classification: **documentation defect; does not invalidate source-isolation PASS**.

`INSTALLING.md` is structurally version-generic but its human worked example still names `v0.1.1` and its old digest. The measured harness intentionally did not repair this before execution. The accepted release tested here is `v0.2.0`.

Required follow-up: update installation documentation so the worked example cannot misleadingly pin an obsolete accepted release. Prefer deriving the example from a clearly labeled example/version placeholder or explicitly pointing users to the current accepted release metadata rather than requiring documentation edits for every release.

## Final disposition

**PASS.** Accepted `v0.2.0` can self-install and execute the production invocation boundary entirely from `.reasoning-distiller/` while the adjacent framework source roots are unavailable. The run provides direct evidence that the packaged runtime does not require the development source tree for the tested consumer operation.

This trial does not replace the Greenfield Consumer Trial. The next consumer-adoption gate remains Trial B, which tests the product-to-new-project/bootstrap boundary.
