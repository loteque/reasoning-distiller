# Self-Consumption Isolation Trial — Execution Record

Status: **EXECUTION REQUESTED — disposition not yet recorded**

Specification: `docs/testing/CONSUMER_TRIALS.md`, Trial A.

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

## Execution harness

`.github/workflows/self-consumption-isolation.yml` performs the measured run from a clean checkout. It:

1. retrieves the seven `v0.2.0` release assets read-only;
2. verifies release, source, content, and transport identities;
3. arranges only the documented installer bootstrap layout;
4. self-installs into `.reasoning-distiller/` with the released `rd_install.py`;
5. creates minimal project-owned fixed evidence and an invocation request outside the managed tree;
6. runs installed `rd-distill prepare`;
7. supplies a controlled provider-boundary raw RGP candidate whose proposition is directly grounded in the fixed evidence;
8. physically relocates source `agents/`, `admission/`, `backends/`, `protocols/`, `runtime/`, `schemas/`, and `validators/` outside the repository workspace;
9. repeats installed `prepare` and runs installed `finalize` while those source paths are unavailable;
10. byte-compares preserved raw candidate output with provider output;
11. verifies an immutable candidate submission and no canonical mutation;
12. audits the installed tree for executable source-repository references;
13. restores source directories only to measure the final Git working-tree boundary;
14. emits the installation, invocation, audit, identity, and diff evidence as a workflow artifact.

The controlled provider-boundary output tests the product invocation boundary and source isolation; it is not a reasoning-quality evaluation and does not claim to test a particular hosted model provider.

## Documentation finding identified before disposition

`INSTALLING.md` is structurally version-generic but its human example still names `v0.1.1` and its old digest. The trial harness does not alter that document during the measured run. This is a documentation-staleness finding to classify after the trial; it is not silently repaired as part of execution.

## Disposition rule

Do not mark this record PASS from harness construction alone. PASS requires observed successful execution of every harness assertion and preserved run evidence. Any failed assertion is a trial failure/product finding under `CONSUMER_TRIALS.md`.
