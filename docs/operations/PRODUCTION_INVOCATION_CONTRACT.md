# Production Distiller Invocation Contract

Status: **Normative v1 operational contract**
Contract: `reasoning-distiller-invocation/1`

## Purpose

This contract defines the stable operational boundary for invoking an **installed** Reasoning Distiller in a consuming project. It does not change `rgp/1`, grant project authority, perform semantic reconciliation, or admit canonical knowledge.

The invocation boundary is intentionally small:

```text
project-local installed framework
        +
project-supplied invocation request
        +
fixed observable evidence
        ↓
Distiller invocation
        ↓
raw rgp/1 candidate
        ↓
deterministic validation
        ↓
immutable candidate submission
        ↓
project-authorized Steward
```

The Distiller ends at candidate production/submission. Steward reconciliation and admission remain separate operations.

## 1. Invocation entrypoint

The stable product-level operation is named:

```text
rd-distill
```

`rd-distill` is the logical interface. A runner MAY implement it through a Python CLI, agent activation, SDK wrapper, or equivalent adapter, but adapters MUST preserve this contract exactly.

The implementation MUST resolve generic Distiller instructions and validators from the project-local `.reasoning-distiller/` installation. It MUST NOT fetch or fall back to the generic source repository.

## 2. Required inputs

An invocation consumes one request document conforming to `reasoning-distiller-invocation/1`:

```json
{
  "contract": "reasoning-distiller-invocation/1",
  "invocation_id": "opaque-unique-id",
  "project_root": ".",
  "evidence": [
    {
      "source_id": "opaque-source-id",
      "type": "repository_file",
      "locator": "docs/example.md"
    }
  ],
  "source_registry": [
    {
      "source_id": "opaque-source-id",
      "type": "repository_file",
      "locator": "docs/example.md"
    }
  ],
  "source_context": {
    "summary": "Optional operational description.",
    "refs": []
  },
  "output": {
    "submission_path": "project-knowledge/submissions/RGP-example.json"
  }
}
```

Required request fields:

- `contract` — exactly `reasoning-distiller-invocation/1`;
- `invocation_id` — opaque identity for this production attempt;
- `project_root` — project workspace root;
- `evidence` — non-empty fixed evidence set;
- `source_registry` — registry sufficient to resolve every provenance identifier available to the Distiller;
- `output.submission_path` — project-designated immutable candidate-submission destination.

`source_context` is optional operational context and is not proposition provenance.

## 3. Evidence descriptors

Each evidence descriptor contains:

```json
{
  "source_id": "opaque-source-id",
  "type": "repository_file",
  "locator": "project-relative-or-runner-resolvable-locator",
  "digest": "optional immutable content digest"
}
```

`source_id`, `type`, and `locator` are required. `digest` is strongly recommended whenever the evidence transport can provide immutable bytes.

The runner resolves evidence before model activation. The evidence set is fixed for the invocation. The Distiller MUST NOT autonomously broaden the evidence set, search for additional project facts, or infer authority from locator spelling.

If required evidence cannot be resolved, the invocation fails before candidate submission.

## 4. Project discovery

V1 does **not** search arbitrary project paths for configuration.

The runner supplies `project_root`. Project-owned integration MAY materialize a Project Knowledge Package and use it to construct the request, including the designated submission path and source registry. The invocation interface itself does not mutate or initialize that package.

A future bootstrap/discovery contract may standardize project configuration discovery. Until then, absence or ambiguity is surfaced rather than guessed.

## 5. Distiller activation

The invocation activates the installed generic directive at:

```text
.reasoning-distiller/agents/distiller/DIRECTIVE.md
```

The runner supplies only:

1. that installed directive;
2. the fixed evidence bytes;
3. the request's source registry and operational context needed to interpret those bytes;
4. the requirement to return raw `rgp/1` candidate graph JSON.

No prior candidate, Steward disposition, canonical reconciliation result, or hidden reasoning trace is implicitly supplied. Such material is input only when explicitly included in the fixed evidence set for the invocation.

The raw model result MUST be preserved without post-hoc semantic editing.

## 6. Raw candidate output

The Distiller returns exactly the `rgp/1` candidate graph shape defined by its directive:

```json
{
  "records": [],
  "relations": []
}
```

The producer adapter MUST NOT repair, rewrite, normalize semantically, add missing propositions, change proposition kinds, change provenance, or otherwise improve the raw candidate after model return.

Mechanical JSON parsing and deterministic schema/protocol validation are allowed. A candidate that fails validation is preserved as failed invocation evidence but MUST NOT enter the ordinary Steward submission queue.

## 7. Submission output

For a valid raw candidate, the adapter creates the immutable candidate envelope defined by `protocols/rgp/SUBMISSION_PROTOCOL.md`.

The envelope MUST contain:

- a fresh `submission_id` for the exact candidate semantics;
- `producer.role: reasoning-distiller`;
- explicit `rgp_version: rgp/1`;
- `status: candidate`;
- the raw candidate graph unchanged as `candidate_graph`;
- deterministic validation status/validator identity;
- optional operational `source_context` copied from the request.

The submission is persisted exactly once to `output.submission_path`. Existing committed content at that path is never overwritten.

A retry that intentionally delivers the exact same candidate package reuses its existing submission identity according to the RGP Submission Protocol; a new model invocation uses a new `invocation_id` and does not silently impersonate the prior invocation.

## 8. Invocation result

The runner returns one machine-readable result:

### Success

```json
{
  "contract": "reasoning-distiller-invocation-result/1",
  "invocation_id": "opaque-unique-id",
  "status": "PASS",
  "submission_id": "RGP-...",
  "submission_path": "project-knowledge/submissions/RGP-example.json"
}
```

### Failure

```json
{
  "contract": "reasoning-distiller-invocation-result/1",
  "invocation_id": "opaque-unique-id",
  "status": "FAIL",
  "stage": "preflight | activation | parse | validation | persistence",
  "reason_code": "stable-machine-code",
  "detail": "human-readable diagnostic"
}
```

Failure results never claim admission and never mutate canonical knowledge.

## 9. Exit semantics

For CLI adapters:

| Exit | Meaning |
|---:|---|
| `0` | valid candidate submission persisted; result `PASS` |
| `2` | request/preflight failure |
| `3` | Distiller activation/model failure |
| `4` | raw output parse failure |
| `5` | RGP validation failure |
| `6` | immutable submission persistence failure/collision |
| `1` | unexpected internal failure |

Adapters that cannot expose process exit codes MUST preserve the same result `status`, `stage`, and reason semantics.

## 10. Failure invariants

The invocation fails closed when:

- the request contract is unsupported;
- the local framework installation is missing/incomplete;
- evidence or source-registry entries cannot be resolved;
- evidence digest verification fails;
- model activation fails;
- output is not parseable candidate JSON;
- candidate RGP validation fails;
- the destination already contains different bytes;
- persistence cannot be completed immutably.

No failure authorizes evidence expansion, candidate repair, canonical writes, or remote framework fallback.

## 11. Filesystem and network boundary

A production invocation MAY read:

- the installed `.reasoning-distiller/` runtime required for Distiller activation/validation;
- explicitly supplied evidence;
- explicitly supplied project integration/request material.

It MAY write:

- raw invocation evidence to a project-designated operational/evidence location when configured by the project;
- one immutable valid candidate submission to the designated submission path.

It MUST NOT write canonical knowledge, dispositions, project authority, policy, or project-owned role activation.

The invocation MUST remain functional with the generic Reasoning Distiller repository unavailable. Network access is not part of the invocation contract; a model runner may require its own model transport, but framework/configuration/evidence discovery MUST NOT depend on remote repository access.

## 12. Authority boundary

```text
Distiller invocation
    -> candidate production
    -> validation
    -> immutable submission
    STOP

Steward invocation
    -> semantic reconciliation
    -> disposition
    -> admission authorization when permitted
```

`rd-distill` has no semantic reconciliation or admission authority. Structural validity does not imply truth, acceptance, canonical identity, or project standing.

## 13. Determinism boundary

The surrounding invocation mechanics are deterministic for fixed local inputs: request validation, evidence resolution/digest checks, RGP validation, envelope construction rules, and persistence behavior.

The reasoning model itself is not required to produce byte-identical candidates across independent invocations. Independent invocations therefore preserve distinct raw outputs and invocation identities rather than hiding variance.

## 14. Production conformance tests

An implementation of `reasoning-distiller-invocation/1` is conforming only when tests prove:

1. valid fixed evidence can produce and persist a valid immutable submission;
2. raw candidate bytes/semantics are not post-hoc repaired;
3. invalid RGP output is preserved but not submitted;
4. missing/unresolvable evidence fails before activation/submission as appropriate;
5. evidence digest mismatch fails closed;
6. existing-path collision never overwrites a submission;
7. installed runtime works without generic-repository fallback;
8. canonical/project-authority paths are unchanged by invocation;
9. separate independent invocations receive distinct invocation identities and preserve separate raw outputs;
10. successful submission is consumable by the existing RGP Submission Protocol without semantic translation.

## 15. Compatibility

V1 requires:

- installed Reasoning Distiller package compatible with `rgp/1`;
- Distiller directive compatible with the raw candidate shape above;
- submission adapter compatible with the current RGP Submission Protocol.

Unknown major invocation or RGP contracts fail rather than being coerced.

## 16. Non-goals

This contract does not define:

- project bootstrap or initialization;
- model-provider credentials/transports;
- automatic evidence discovery;
- semantic reconciliation;
- canonical backend mutation;
- Steward role activation;
- release/package installation or update discovery.

Those remain separate boundaries.

## 17. Next implementation gate

Implement a reference `rd-distill` adapter and schemas for `reasoning-distiller-invocation/1` and `reasoning-distiller-invocation-result/1`, then pressure-test the conformance cases in §14 against a project-local installed package before declaring the invocation interface production-ready.
