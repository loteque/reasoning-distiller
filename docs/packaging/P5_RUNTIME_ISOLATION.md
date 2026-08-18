# P5 — Runtime Isolation

Status: **PASS**

P5 proves that an installed Reasoning Distiller is operational from project-local files only after package retrieval and installation.

## Required property

> With the generic `reasoning-distiller` repository unavailable and Python network access blocked, packaged runtime behavior continues to operate from `.reasoning-distiller/`.

Source repository references are allowed only in `.reasoning-distiller/.installation/` provenance/update metadata and as inert schema identifiers such as JSON Schema `$id`. Runtime files may not contain executable repository locators, remote `$ref` dependencies, old embedded-framework paths, remote schema fetches, or fallback paths into the source repository.

## Proofs

`tests/test_runtime_isolation_p5.py` builds and installs a package into a temporary project, then:

- audits the installed tree with `packaging/audit_runtime_isolation.py`;
- proves provenance metadata may retain source/update locators;
- proves inert schema identifiers are not treated as working references;
- proves a repository locator inserted into runtime code is rejected;
- runs the installed RGP validator with Python network calls blocked;
- runs the installed PEMS/2 backend contract suite with Python network calls blocked;
- runs the installed guarded-admission pressure suite with Python network calls blocked;
- deletes the retrieved package artifacts and proves the installed runtime still works.

The runtime subprocesses execute from the consumer project workspace and address only `.reasoning-distiller/` paths. `PYTHONPATH` contains only a `sitecustomize.py` network blocker; source-repository paths are not added.

## Audit contract

`reasoning-distiller-runtime-isolation-audit/1`

The audit excludes `.installation/` from repository-reference scanning because that directory is explicitly provenance/update metadata, not runtime resolution. JSON Schema `$id` values are treated as inert identifiers; other repository-bearing JSON values remain auditable. Symlinks anywhere in the installed tree are rejected.

## Exit proof

P5 passed with:

1. dedicated runtime-isolation suite: PASS;
2. deterministic installer P3 suite: PASS;
3. journaled recovery P4 suite: PASS;
4. Extraction Parity: PASS;
5. Package Contract: PASS;
6. installed runtime audit: zero working-reference violations.

Passing P5 authorizes P6 consumer migration to replace the voxel-engine transitional cross-repository runtime checkout with a project-local package installation.
