# Greenfield Consumer Trial — Execution Record

Status: **EXECUTION REQUESTED — disposition not yet observed**

Specification: `docs/testing/CONSUMER_TRIALS.md`, Trial B.

## Motivation

This trial tests whether a new repository with no Reasoning Distiller integration knowledge can move from public installation instructions to a first valid candidate submission without developer history, hidden scaffolding, or invented project conventions.

The trial is intentionally allowed to stop at the first undefined bootstrap requirement. Such a stop is a product finding, not permission to add ad hoc project structure during the measured run.

## Selected release

| Property | Value |
|---|---|
| Release | `0.2.0` |
| Tag | `v0.2.0` |
| Source commit | `c7daed110e58627d0ab2566298cc433615ee4452` |
| Content identity | `sha256:75736b1b8522f568cf172058ea97b8216501d4faaf2d4fa32ff7056181c42add` |
| Transport SHA-256 | `d5273f9181e286c592db21e636c67b8dfb3f3a3dc39608cf34e6f66557a477e1` |

## Initial state

The executable harness creates a fresh temporary Git repository containing only:

```text
README.md
.gitignore
```

No `.reasoning-distiller/`, `project-knowledge/`, source registry, invocation request, role assignment, canonical backend, submission directory, or integration wrapper exists before the measured run.

## Operator-visible documentation

The measured operator is limited to the public entrypoints:

- `README.md`;
- `INSTALLING.md`;
- `docs/operations/PRODUCTION_INVOCATION_CONTRACT.md`;
- the exact accepted release assets.

Framework source is not inspected to determine consumer setup.

## Harness behavior

`.github/workflows/greenfield-consumer-trial.yml`:

1. proves the greenfield initial tree;
2. retrieves and verifies the exact accepted release read-only;
3. follows the documented installer bootstrap layout;
4. installs the package into `.reasoning-distiller/`;
5. verifies release/install identities;
6. attempts to proceed from public documentation toward the first invocation;
7. refuses to invent project-owned scaffolding when the invocation contract requires `evidence`, `source_registry`, `output.raw_candidate_path`, and `output.submission_path` while explicitly leaving project bootstrap undefined;
8. records blocking finding `GFCT-001` and stops before constructing an invocation;
9. proves the only working-tree addition at the stop point is `.reasoning-distiller/`;
10. uploads the initial/final trees, installation evidence, operator-visible docs, finding, and measured disposition.

## Expected first finding

`GFCT-001` is expected if the current public surface remains unchanged:

> Public installation succeeds, but no public bootstrap procedure defines the minimum project-owned state required to construct the first `rd-distill` invocation.

This is not pre-declared as the final disposition. The execution must observe it. If public behavior differs, the run evidence controls.

## Disposition rule

- `PASS` requires reaching a valid immutable candidate submission using only documented project/product mechanisms.
- `STOPPED_PRODUCT_FINDING` is the correct measured disposition when the first required project-owned bootstrap operation is undefined.
- The harness must not manufacture `project-knowledge/`, a source registry, output conventions, authority configuration, or other project scaffolding merely to continue.

If `GFCT-001` is observed, the next engineering step is to define and implement the Project Bootstrap Contract, then rerun Trial B from a fresh greenfield repository.
