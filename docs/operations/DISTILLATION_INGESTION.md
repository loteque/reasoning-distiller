# Distillation Ingestion Wizard

The ingestion wizard is the human-facing entry point for constructing a
`reasoning-distiller-invocation/1` request and its activation bundle.

It does not call a model and it does not admit or mutate canonical knowledge.

## Interactive use

Run from an initialized project root:

```bash
python .reasoning-distiller/runtime/rd_distill.py ingest
```

The wizard accepts files, directories, and globs. It previews the exact evidence
set and SHA-256 digests before writing:

- `<invocations>/<invocation-id>.request.json`
- `<invocations>/<invocation-id>.bundle.json`

The `<invocations>` and `<submissions>` locations come from
`project-knowledge/project.json`.

## Scriptable use

```bash
python .reasoning-distiller/runtime/rd_distill.py ingest \
  --evidence 'docs/design/*.md' \
  --evidence docs/packaging/INSTALL_PACKAGE_CONTRACT.md \
  --evidence docs/packaging/INSTALLER_RUNNER_CONTRACT.md \
  --invocation-id first-baseline-20260820 \
  --created-at 2026-08-20T09:37:00-07:00 \
  --context 'First curated normative baseline' \
  --ref baseline:first-distillation
```

Directories are expanded recursively. Globs and resulting files are sorted
before source construction. Source IDs and SHA-256 digests are generated
automatically.

Use `--dry-run` to validate and preview without writing artifacts.

## Safety boundaries

The wizard fails closed for path escapes, symlinks, missing project
initialization, invalid project configuration, unsafe invocation IDs, and
different pre-existing request/bundle files.

The following project roots are excluded from evidence selection:

- `.git/`
- `.reasoning-distiller/`
- `project-knowledge/`

These defaults prevent the framework installation and prior distillation outputs
from silently becoming evidence for a new distillation.

Identical evidence plus identical invocation metadata produces byte-identical
request and bundle artifacts. Repeating the same build is idempotent. A
different artifact at the same invocation path is never overwritten.

## Next boundary

The bundle is input to a separate model runner. The model returns only the raw
`rgp/1` candidate graph. Finalization remains explicit:

```bash
python .reasoning-distiller/runtime/rd_distill.py finalize \
  --request project-knowledge/invocations/<id>.request.json \
  --raw-candidate project-knowledge/invocations/<id>.raw.json
```

`finalize` validates and creates a candidate submission. Admission remains a
separate authority boundary.
