# Live Model Activation Trial

Status: **Durable test specification — execution pending**

## Motivation

The Greenfield First Invocation Trial proved the installed production mechanics through immutable candidate submission, but represented the model/provider boundary with a fixed fixture. That leaves one independent production question:

> Can an actual reasoning model consume the exact `rd-distill prepare` activation semantics and return raw `rgp/1` candidate bytes that the released runtime can preserve, validate, and submit without repair?

This trial isolates that question. It does not test semantic reconciliation or admission authority.

## Model activation

The first execution uses an interactive OpenAI ChatGPT model invocation as the live provider boundary. The model receives only the Distiller directive, fixed evidence, source registry, and the output instruction represented by the activation bundle. No prior candidate, canonical state, Steward disposition, or hidden chain-of-thought is supplied.

The model output MUST be persisted byte-for-byte as external model output evidence before `rd-distill finalize` consumes it. The workflow MUST NOT rewrite the candidate to make validation pass.

## Fixed evidence

```text
The greenfield live model activation reached explicit evidence preparation.
```

Source registry identity:

```text
source_id: src:greenfield:live
source type: repository_file
locator: project-knowledge/evidence/live.txt
```

## First live model output

Provider boundary: OpenAI ChatGPT interactive invocation.  
Model: GPT-5.6 Sol.  
Raw output path in this repository: `docs/testing/evidence/live-model-activation-1.raw.json`.

The raw output is treated as immutable evaluation evidence. It is not canonical project knowledge and carries no Steward or admission authority.

## Measured procedure

1. Create a fresh disposable repository containing only `README.md` and `.gitignore`.
2. Retrieve accepted Reasoning Distiller `v0.3.0` read-only and verify its accepted identities.
3. Install the release using the released deterministic installer.
4. Bootstrap project-owned state using only installed `rd_bootstrap.py`.
5. Add the exact fixed evidence above and calculate its digest.
6. Construct a `reasoning-distiller-invocation/1` request with only that evidence/source registry.
7. Run installed `rd_distill.py prepare` and verify the activation bundle contains exactly the fixed evidence and registry.
8. Copy the immutable externally produced live-model bytes into the provider-return location without modifying them.
9. Run installed `rd_distill.py finalize`.
10. Verify exact raw-byte preservation.
11. Verify `rgp/1` validation and immutable candidate submission.
12. Verify no canonical, PEMS, COVE, authority, reconciliation, or admission state is created.
13. Preserve the activation bundle, live raw bytes, final result, submission, installation identities, and disposition as run evidence.

## PASS criteria

PASS requires:

| Property | Requirement |
|---|---|
| Accepted distribution | exact `v0.3.0` identities verify |
| Installed-only runtime | bootstrap/prepare/finalize use `.reasoning-distiller/` |
| Fixed activation | activation contains only declared evidence/registry plus installed directive |
| Live provider output | raw candidate was produced by an actual reasoning-model invocation, not authored by the CI harness |
| No repair | CI copies provider bytes unchanged into finalize |
| Raw preservation | stored raw bytes exactly equal live provider bytes |
| RGP validity | installed validator accepts the resulting candidate submission |
| Immutable submission | a candidate envelope is persisted once |
| Authority boundary | no reconciliation/admission/canonical authority is exercised |

A model output that fails RGP validation is a legitimate observed model-quality result, not permission for the harness to repair it. In that case the trial records FAIL/PRODUCT_OR_MODEL_FINDING while preserving the invalid raw bytes.

## Relationship to next gate

A PASS proves the full product path through **live candidate production**:

```text
accepted release
→ install
→ bootstrap
→ explicit evidence
→ prepare
→ live reasoning model
→ raw candidate
→ finalize
→ immutable candidate submission
→ STOP
```

The next independent gate is Steward handoff/reconciliation. That gate requires explicit project-authorized Steward authority; the Distiller and this trial do not manufacture it.
