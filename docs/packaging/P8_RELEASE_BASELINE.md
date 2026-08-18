# P8 — Accepted Release Baseline

Status: **ACCEPTANCE CANDIDATE** until the P8 release workflow records PASS.

This document closes the package-distribution implementation sequence defined by `docs/proposals/install-package/FINAL_PLAN.md`.

## Accepted release candidate

| Property | Value |
|---|---|
| Framework release | `0.1.1` |
| Git tag | `v0.1.1` |
| Source commit | `1da88edc000bbd6db78affe8e604ca499f516d55` |
| Package contract | `reasoning-distiller-install-package/1` |
| Installer contract | `reasoning-distiller-installer/1` |
| Content identity | `sha256:a487149caaaf41af70fdf2af6e52b7955a6c3fe14046321649357d21ba7241b4` |
| Transport SHA-256 | `773ab0c9a5946f69ec568aabd9a255569f9511227142baadde077f826aa6cd8a` |
| Project Knowledge Package compatibility | `project-knowledge-package/1` |
| RGP compatibility | `rgp/1` |
| PEMS/COVE compatibility | `pems/2`, `cove/1` |

The release is accepted only when `.github/workflows/p8-release.yml` independently rebuilds the package from the exact source commit, reproduces the declared identities, validates the package contract, creates or verifies the immutable `v0.1.1` tag, publishes the release assets, and writes `docs/packaging/P8_RELEASE_STATUS.json` with `status: PASS`.

## Distribution boundary

A consuming-project agent retrieves release artifacts read-only. The Reasoning Distiller repository never writes the consumer repository.

Release assets:

```text
reasoning-distiller-0.1.1.tar.gz
reasoning-distiller-0.1.1.manifest.json
reasoning-distiller-0.1.1.sha256
rd_install.py
validate_install_package_contract.py
install-package-manifest.schema.json
installation-record.schema.json
```

The first three identify the framework payload. The remaining four are the network-independent installer bootstrap required to validate and install that payload. Bootstrap files are release assets; they are not part of the installed managed framework tree.

## Agent install procedure

The agent performs retrieval using whatever read mechanism is available, then executes installation locally inside the already-authorized target workspace.

```text
1. Select an exact accepted release, never an unpinned branch head.
2. Retrieve all seven release assets into a temporary directory.
3. Verify the archive SHA-256 against the detached `.sha256` file.
4. Place `rd_install.py` and `validate_install_package_contract.py` together under `<tmp>/packaging/`.
5. Place both installer schemas under `<tmp>/schemas/`.
6. Materialize the consuming Project Knowledge Package as JSON when compatibility preflight is desired.
7. Run `python <tmp>/packaging/rd_install.py` with explicit local package, manifest, digest, target, and provenance arguments.
8. Run project integration validation from `.reasoning-distiller/` with network access unavailable where practical.
9. Review the resulting repository diff.
10. Commit or submit the change through the consuming project's normal governance path.
```

Example invocation:

```bash
python /tmp/rd/packaging/rd_install.py \
  --package /tmp/rd/reasoning-distiller-0.1.1.tar.gz \
  --manifest /tmp/rd/reasoning-distiller-0.1.1.manifest.json \
  --transport-sha256 773ab0c9a5946f69ec568aabd9a255569f9511227142baadde077f826aa6cd8a \
  --target "$PROJECT_ROOT" \
  --project-package /tmp/rd/project-package.json \
  --source-repository loteque/reasoning-distiller \
  --source-locator v0.1.1
```

The installer itself performs no network I/O and does not choose the release.

## Agent update procedure

Updating is the same deterministic install transaction against a newer accepted release:

```text
current local installation
  -> retrieve exact newer release read-only
  -> verify release package
  -> deterministic local install/update
  -> offline/local integration validation
  -> review exact managed-tree diff
  -> update project-owned binding metadata separately when the project stores a framework identity binding
  -> commit/review through project governance
```

Project-owned integration metadata is deliberately not changed by `rd_install.py`. If a project binds a canonical backend or workflow configuration to a framework version/content identity, the authorized project agent updates that binding as a separate project-owned change after successful installation.

## Runtime invariant

After installation, runtime operation must remain functional with the source repository unavailable and network access disabled. Runtime code must not fetch schemas, validators, role definitions, or executable framework content from the generic repository.

Allowed source references are limited to provenance, documentation, and explicit update discovery/retrieval pathways.

## Operator release procedure

A release operator does not hand-edit package artifacts.

1. Choose an exact validated source commit.
2. Run the deterministic builder for the intended release version.
3. Require package-contract, installer, recovery, runtime-isolation, and extraction-parity suites to pass.
4. Rebuild independently and compare canonical content identity and transport digest.
5. Create an immutable version tag at the exact source commit.
6. Publish the deterministic payload plus installer bootstrap as release assets.
7. Record source commit, release version, content identity, and transport digest as durable release evidence.
8. Demonstrate clean install and one package update in a real consumer before declaring the distribution architecture production-ready.

For `0.1.1`, steps 1–4 and the consumer install/update proofs were already established by P1–P7. The P8 workflow performs the final rebuild/tag/publish/status gate.

## Production invariants

- The release package is immutable and bound to an exact source commit.
- A release version must not identify multiple content identities.
- Retrieval is read-only from the framework repository.
- Installation executes locally under the consuming agent's existing authority.
- The installer never acquires project semantic reconciliation or admission authority.
- Installed runtime has no working dependency on the generic repository.
- Project knowledge and project integration policy remain project-owned.
- Updates are auditable repository diffs and fail closed on unexpected managed-tree drift.

## P8 exit criterion

P8 passes when the accepted `v0.1.1` release is retrievable as immutable assets, its source/content/transport identities are recorded and independently reproduced, agent/operator instructions are durable, and the existing P6/P7 consumer proofs demonstrate clean local installation and deterministic update without transferring project authority or modifying canonical project knowledge.