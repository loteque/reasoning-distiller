# Installing Reasoning Distiller

Reasoning Distiller is installed **into a project repository**. The installed framework lives under `.reasoning-distiller/`; project knowledge, project rules, and project authority remain outside that managed directory.

The installer is a local, deterministic Python program. It does not fetch anything from the network and it does not choose a version. First retrieve an exact accepted release, then run the installer against those local files.

## Installation

### Requirements

- Python 3.
- A local checkout of the project to receive Reasoning Distiller.
- The assets from one exact accepted Reasoning Distiller release.

Do not install from an unpinned branch such as `main`. Use a versioned accepted release.

### 1. Get the release files

From the selected Reasoning Distiller release, download these seven files into a temporary directory:

```text
reasoning-distiller-<version>.tar.gz
reasoning-distiller-<version>.manifest.json
reasoning-distiller-<version>.sha256
rd_install.py
validate_install_package_contract.py
install-package-manifest.schema.json
installation-record.schema.json
```

For the accepted `v0.1.1` baseline, `<version>` is `0.1.1`.

### 2. Arrange the installer files

The installer expects its validator beside it and the schemas one directory above it:

```text
/tmp/rd/
├── reasoning-distiller-<version>.tar.gz
├── reasoning-distiller-<version>.manifest.json
├── reasoning-distiller-<version>.sha256
├── packaging/
│   ├── rd_install.py
│   └── validate_install_package_contract.py
└── schemas/
    ├── install-package-manifest.schema.json
    └── installation-record.schema.json
```

### 3. Verify the package digest

Open `reasoning-distiller-<version>.sha256`. Its first value is the expected SHA-256 digest of the `.tar.gz` package. Verify the archive with the SHA-256 tool available on the local system before installing it.

For accepted release `v0.1.1`, the expected archive SHA-256 is:

```text
773ab0c9a5946f69ec568aabd9a255569f9511227142baadde077f826aa6cd8a
```

### 4. Run the installer

Set the target to the root directory of the project repository. Then run:

```bash
python /tmp/rd/packaging/rd_install.py \
  --package /tmp/rd/reasoning-distiller-0.1.1.tar.gz \
  --manifest /tmp/rd/reasoning-distiller-0.1.1.manifest.json \
  --transport-sha256 773ab0c9a5946f69ec568aabd9a255569f9511227142baadde077f826aa6cd8a \
  --target /path/to/project \
  --source-repository loteque/reasoning-distiller \
  --source-locator v0.1.1
```

If the project has a compatible Project Knowledge Package materialized as JSON, add `--project-package /path/to/project-package.json` to perform compatibility preflight before installation.

A successful installation reports `"status": "PASS"` and creates `/path/to/project/.reasoning-distiller/`.

### 5. Review the project diff

Review the repository diff before committing it. The installer owns only `.reasoning-distiller/` plus its temporary crash-recovery state while an installation is in progress. It must not rewrite project knowledge, project policy, or project-owned integration configuration.

If an installation was interrupted, rerunning a normal installation performs recovery first. Recovery can also be requested explicitly:

```bash
python /tmp/rd/packaging/rd_install.py --recover-only --target /path/to/project
```

### Updating

Updating uses the same procedure with a newer **accepted, exact release**. Do not manually edit `.reasoning-distiller/`; the installer detects managed-tree drift and fails closed. Review the resulting diff. If the project separately records the installed Distiller version or content identity in project-owned configuration, update that binding separately through the project's normal authority and review process.

Downgrades are rejected by default. Use `--allow-downgrade` only for an intentional, reviewed downgrade.

## Agent

```text
Install Reasoning Distiller into <PROJECT_ROOT>.
1. Select an exact accepted release; never a branch head.
2. Retrieve its 7 assets: package, manifest, .sha256, rd_install.py, validator, 2 schemas.
3. Verify package SHA-256 against .sha256. Fail on mismatch.
4. Place rd_install.py + validator in <TMP>/packaging/; schemas in <TMP>/schemas/.
5. Run: python <TMP>/packaging/rd_install.py --package <PKG> --manifest <MANIFEST> --transport-sha256 <SHA256> --target <PROJECT_ROOT> --source-repository loteque/reasoning-distiller --source-locator <TAG> [--project-package <PKP_JSON>].
6. Require status PASS. Review diff. Do not alter project-owned knowledge/policy/config as installer work. Do not use --allow-downgrade unless explicitly authorized.
```
