# Production Distiller Invocation Contract

Status: **Normative v1 operational contract**  
Contract: `reasoning-distiller-invocation/1`

## Purpose

This contract defines the stable operational boundary for invoking an **installed** Reasoning Distiller in a consuming project. It does not change `rgp/1`, grant project authority, perform semantic reconciliation, or admit canonical knowledge.

```text
project-local installed framework
        +
fixed project evidence
        +
explicit invocation request
        ↓
rd-distill
        ↓
raw rgp/1 candidate (preserved exactly)
        ↓
deterministic validation
        ↓
immutable candidate submission
        ↓
STOP — project-authorized Steward acts separately
```

## 1. Stable operation and reference adapter

The stable product-level operation is `rd-distill`.

The reference provider-neutral implementation is:

```text
.reasoning-distiller/runtime/rd_distill.py
```

It exposes two deterministic sides of one logical invocation:

```text
prepare  -> validate fixed inputs and emit exact model activation bundle
model runner/provider boundary
finalize -> preserve raw model bytes, validate rgp/1, persist immutable submission
```

The model transport itself is intentionally not standardized here. A runner may use any model/provider mechanism, but it must feed the prepared bundle without silently broadening evidence and must return the raw candidate unchanged to `finalize`.

The adapter resolves the directive and validator only from the project-local `.reasoning-distiller/` installation. No source-repository fallback is permitted.

## 2. Request

A request conforms to `schemas/invocation-request.schema.json`:

```json
{
  "contract": "reasoning-distiller-invocation/1",
  "invocation_id": "opaque-unique-id",
  "created_at": "2026-08-18T00:00:00-07:00",
  "project_root": ".",
  "evidence": [
    {
      "source_id": "opaque-source-id",
      "type": "repository_file",
      "locator": "docs/example.md",
      "digest": "sha256:<64-lowercase-hex>"
    }
  ],
  "source_registry": [
    {
      "source_id": "opaque-source-id",
      "type": "repository_file",
      "locator": "docs/example.md",
      "digest": "sha256:<64-lowercase-hex>"
    }
  ],
  "source_context": {
    "summary": "Optional operational description.",
    "refs": []
  },
  "output": {
    "raw_candidate_path": "project-knowledge/invocations/example.raw.json",
    "submission_path": "project-knowledge/submissions/RGP-example.json"
  }
}
```

Required fields:

- `contract` — exactly `reasoning-distiller-invocation/1`;
- `invocation_id` — opaque identity for this production attempt;
- `created_at` — runner-supplied event time used in deterministic submission metadata;
- `project_root` — project workspace root relative to the runner working directory;
- `evidence` — non-empty fixed evidence set;
- `source_registry` — registry for available provenance identifiers;
- `output.raw_candidate_path` — immutable location for exact raw model bytes;
- `output.submission_path` — immutable location for a valid RGP candidate envelope.

`source_context` is optional operational context, not proposition provenance.

## 3. Evidence boundary

Every evidence item identifies one project-local regular file. The reference adapter resolves paths beneath `project_root`, rejects path escape/symlink evidence, and verifies an optional `sha256:` digest.

The evidence set is fixed before activation. The Distiller must not autonomously search for more project facts or infer authority from source-ID or locator spelling.

Every evidence source must resolve through `source_registry`. Candidate provenance may reference only registered source IDs.

Missing evidence, registry mismatch, unsafe paths, and digest mismatch fail before submission.

## 4. Activation bundle

`prepare` reads only:

1. `.reasoning-distiller/agents/distiller/DIRECTIVE.md`;
2. the fixed evidence bytes;
3. the supplied source registry;
4. optional source context.

It emits `reasoning-distiller-activation-bundle/1`, including the exact directive, exact evidence content/digests, and the instruction to return only raw `rgp/1` candidate graph JSON.

Example:

```bash
python .reasoning-distiller/runtime/rd_distill.py prepare \
  --request invocation.json \
  --bundle-out activation.json
```

No prior candidate, disposition, reconciliation result, canonical state interpretation, or hidden reasoning trace is implicitly added.

## 5. Raw candidate preservation

The model runner returns raw candidate bytes. `finalize` persists those exact bytes to `output.raw_candidate_path` **before** parsing or RGP validation.

```bash
python .reasoning-distiller/runtime/rd_distill.py finalize \
  --request invocation.json \
  --raw-candidate model-output.json
```

If parsing or validation fails, the raw artifact remains preserved and no ordinary Steward submission is created.

The adapter must not repair, rewrite, normalize semantically, add propositions, change kinds, alter provenance, or otherwise improve the model result after return.

## 6. RGP validation and submission

A valid raw graph is checked by the installed `rgp-validator/1` implementation. Its provenance references must also resolve through the request source registry.

The adapter then creates the immutable candidate envelope defined by `protocols/rgp/SUBMISSION_PROTOCOL.md` with:

- deterministic `submission_id` derived from `invocation_id` plus canonical candidate semantics;
- `producer.role: reasoning-distiller`;
- `producer.instance: <invocation_id>`;
- request `created_at`;
- `rgp_version: rgp/1`;
- `status: candidate`;
- the parsed raw graph unchanged as `candidate_graph`;
- deterministic validation metadata;
- optional request `source_context`.

The envelope is written once to `output.submission_path`. Existing different bytes are never overwritten. Replaying the exact same request/candidate to the same paths is idempotent.

Separate independent invocations use distinct `invocation_id` values and therefore retain distinct submission identities even when their candidate semantics happen to match.

## 7. Result contract

Results conform to `schemas/invocation-result.schema.json` and `reasoning-distiller-invocation-result/1`.

Success:

```json
{
  "contract": "reasoning-distiller-invocation-result/1",
  "invocation_id": "opaque-unique-id",
  "status": "PASS",
  "submission_id": "RGP-...",
  "raw_candidate_path": "project-knowledge/invocations/example.raw.json",
  "submission_path": "project-knowledge/submissions/RGP-example.json"
}
```

Failure:

```json
{
  "contract": "reasoning-distiller-invocation-result/1",
  "invocation_id": "opaque-unique-id",
  "status": "FAIL",
  "stage": "preflight | activation | parse | validation | persistence | internal",
  "reason_code": "stable-machine-code",
  "detail": "human-readable diagnostic"
}
```

When raw bytes were successfully preserved before a later failure, the failure result may also include `raw_candidate_path`.

## 8. Exit semantics

| Exit | Meaning |
|---:|---|
| `0` | operation succeeded |
| `2` | request/evidence preflight failure |
| `3` | model/activation boundary failure |
| `4` | raw output parse failure |
| `5` | RGP/provenance validation failure |
| `6` | immutable persistence failure/collision |
| `1` | unexpected internal failure |

Adapters without process exit codes must preserve equivalent result semantics.

## 9. Filesystem and network boundary

The invocation may read only the installed runtime/directive/validator, the explicit request, and explicitly supplied evidence. It may write only the configured raw candidate artifact and valid candidate submission, plus ordinary runner-selected temporary activation output outside the semantic project state.

It must not write canonical knowledge, dispositions, project authority, policy, rules, or role activation.

The installed invocation path must work with the generic Reasoning Distiller repository unavailable. Model-provider networking is a runner concern; framework/configuration/evidence discovery must remain local.

## 10. Authority boundary

```text
rd-distill
    -> candidate production
    -> validation
    -> immutable submission
    STOP

project-authorized Steward
    -> semantic reconciliation
    -> disposition
    -> admission authorization when permitted
```

`rd-distill` has no semantic reconciliation or admission authority. Structural validity does not imply truth, acceptance, canonical identity, lifecycle state, or project standing.

## 11. Determinism boundary

For fixed local inputs, the reference mechanics are deterministic: request checking, evidence resolution, digest checks, activation-bundle construction, RGP validation, submission-ID derivation, envelope construction, persistence rules, and failure classification.

The reasoning model is not required to be deterministic. Independent invocations preserve independent raw outputs rather than hiding variance.

## 12. Conformance requirements

A production adapter is conforming only when tests prove:

1. valid fixed evidence can produce and persist a valid immutable submission;
2. raw candidate bytes are preserved exactly and semantics are not post-hoc repaired;
3. invalid RGP output is preserved but not submitted;
4. missing/unresolvable evidence fails closed;
5. evidence digest mismatch fails closed;
6. output collision never overwrites existing evidence/submissions;
7. an isolated installed copy works without generic-repository fallback;
8. canonical/project-authority bytes are unchanged;
9. independent invocations preserve distinct identities/raw artifacts;
10. successful submission is directly consumable by the existing RGP Submission Protocol.

The reference suite is `tests/test_production_invocation.py` and CI is `.github/workflows/production-invocation.yml`.

## 13. Compatibility

V1 requires:

- installed package containing `runtime/rd_distill.py`;
- `rgp/1`-compatible Distiller directive;
- `rgp-validator/1`;
- current RGP Submission Protocol;
- request/result schemas shipped in the installed package.

Unknown major invocation or RGP contracts fail rather than being coerced.

## 14. Non-goals

This contract does not define project bootstrap, model-provider credentials/transports, automatic evidence discovery, Steward activation, semantic reconciliation, canonical mutation, package installation, or update discovery. Those remain separate boundaries.
