# Project Identity and First-Admission Amendment

Status: **Normative amendment**

This amendment supersedes conflicting project-identity and first-admission language in:

- `docs/operations/PROJECT_BOOTSTRAP_CONTRACT.md` (`reasoning-distiller-project/1` bootstrap configuration), and
- `docs/operations/RIL_ADMISSION_CONTRACT.md` (the package-defined empty PEMS/2 first-admission base).

It does not broaden Steward authority or change reconciliation/admission separation.

## Project identity contract

`reasoning-distiller-project/2` adds an explicit, project-owned identity descriptor to `project-knowledge/project.json`:

```json
{
  "contract": "reasoning-distiller-project/2",
  "project": {
    "id": "example-project",
    "name": "Example Project",
    "repository": "example/project",
    "summary": "A concise project-owned description."
  },
  "paths": {
    "evidence": "project-knowledge/evidence",
    "invocations": "project-knowledge/invocations",
    "submissions": "project-knowledge/submissions"
  }
}
```

All four project identity strings are explicit project-owned inputs. The generic framework MUST NOT infer them from repository contents, filesystem names, remotes, account metadata, or network state.

The v1 bootstrap configuration remains a recognized compatibility state. An exact v1 configuration may be upgraded only when all v2 identity fields are supplied explicitly. Unknown or conflicting project configuration still fails closed.

Reference CLI form:

```bash
python .reasoning-distiller/runtime/rd_bootstrap.py \
  --target /path/to/project \
  --project-id example-project \
  --project-name "Example Project" \
  --repository example/project \
  --summary "A concise project-owned description."
```

The four identity arguments are all-or-none. A known v1-to-v2 migration is a bounded project-config mutation and MUST NOT change authority, evidence, candidate, reconciliation, admission, or Canon state.

## First-admission base

R13 no longer treats this structurally incomplete object as the first canonical base:

```json
{"semantic":"pems/2","records":[],"relations":[]}
```

Before first Canon mutation, R13 MUST read a valid `reasoning-distiller-project/2` configuration and construct one exact project-seeded PEMS/2 base:

```json
{
  "semantic": "pems/2",
  "project_id": "<project.id>",
  "records": [
    {
      "id": "<project.id>",
      "kind": "project",
      "lifecycle": "current",
      "data": {
        "name": "<project.name>",
        "repository": "<project.repository>",
        "summary": "<project.summary>"
      }
    }
  ],
  "relations": []
}
```

`runtime/ril_admission.py:first_admission_base()` is the shared read-only construction primitive. Steward transaction planning and R13 mutation MUST hash and consume this same normalized base. R13 MUST NOT independently recreate a different first-base representation.

If no valid v2 project identity exists and no canonical PEMS already exists, admission stops with `PROJECT_IDENTITY_REQUIRED` before Canon mutation.

## R13 to R14 invariant

The first successful R13 admission MUST produce canonical PEMS/COVE bytes that immediately pass R14 storage verification, including:

- PEMS/2 schema validity;
- `project_id` resolving to a `kind: project` record;
- deterministic PEMS bytes;
- deterministic COVE round-trip;
- a matching immutable admission receipt.

A first-admission implementation that can return `PASS/ADMITTED` while R14 returns `PEMS_SCHEMA_INVALID` is non-conformant.

## Authority boundary

Project identity establishes project configuration only. It does not:

- establish an operator;
- grant a Steward scope;
- create activation evidence;
- reconcile a candidate;
- authorize an admission transaction;
- admit candidate knowledge;
- mutate Canon by itself.

The existing protected operator, Steward authorization, activation, reconciliation, and admission gates remain unchanged.
