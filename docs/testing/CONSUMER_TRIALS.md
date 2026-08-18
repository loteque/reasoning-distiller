# Consumer Adoption Trials

Status: **Durable test specification**

These trials test Reasoning Distiller as a released product from the consumer side. They are not development-unit tests and must not be made to pass by silently adding undocumented scaffolding to the test consumer.

## Shared test discipline

Both trials MUST:

- start from an exact accepted Reasoning Distiller release, never `main` or another branch head;
- use the public installation and invocation contracts;
- retrieve release artifacts read-only;
- install through the released deterministic installer;
- preserve project-owned knowledge, policy, integration, and authority outside `.reasoning-distiller/`;
- record every undocumented prerequisite, manual workaround, hidden source-tree dependency, or ambiguous instruction as a product finding;
- fail closed rather than repair the product or consumer during the measured run;
- preserve durable inputs, commands/operations, outputs, findings, and final PASS/FAIL disposition.

A failed trial is useful evidence. The purpose is to discover missing product boundaries, not merely obtain PASS.

---

# Trial A — Self-Consumption Isolation Trial

## Test motivation

The Reasoning Distiller repository contains both framework source and, after self-installation, a project-local released copy of that framework. This creates a deliberately hostile boundary test: source files are physically nearby and therefore capable of masking incorrect path resolution, implicit development assumptions, or fallback behavior.

The trial asks:

> Can Reasoning Distiller consume its own accepted release strictly as an ordinary project-local installation, without using its adjacent source tree as runtime framework state?

This test is valuable because an ordinary consumer cannot expose source-versus-installed confusion as directly. A self-install that succeeds only because the source tree is present is a failure.

## Initial state

Use a clean checkout of `loteque/reasoning-distiller` at a recorded commit. The repository MUST NOT already contain an active `.reasoning-distiller/` installation unless the trial explicitly begins by removing/recreating a prior test installation.

Record:

- repository commit;
- accepted release tag/version;
- release source commit;
- content identity;
- transport SHA-256;
- clean working-tree state.

## Procedure

1. Retrieve the exact accepted release artifacts using read-only access.
2. Follow `INSTALLING.md` without using unpublished installation knowledge.
3. Install the release into the repository root as `.reasoning-distiller/`.
4. Verify the installed manifest and installation record.
5. Establish only the minimum project-owned invocation material required by the public contracts. Record any missing bootstrap requirement as a finding.
6. Add or designate a small fixed evidence document owned by the consuming-project side of the trial.
7. Invoke `rd-distill` using the implementation under `.reasoning-distiller/`, not `runtime/` in the source tree.
8. Preserve the raw candidate and immutable RGP submission according to the production invocation contract.
9. Run installed validators/runtime operations needed to prove the submission path.
10. Repeat the runtime proof with source-tree framework paths made unavailable to the consumer operation, or with an equivalent guard that causes any source-tree access to fail.
11. Audit the invocation/runtime trace and executable configuration for source-tree framework references.
12. Record PASS/FAIL and all findings.

## Required isolation guard

The measured consumer operation MUST make these source-tree locations unusable as framework dependencies:

```text
agents/
admission/
backends/
protocols/
runtime/
schemas/
validators/
```

The guard MAY use temporary relocation, filesystem denial, sandboxing, path poisoning, or another deterministic mechanism. It MUST leave `.reasoning-distiller/` available.

Merely asserting that local paths were intended is insufficient.

## PASS criteria

PASS requires all of the following:

| Property | Required proof |
|---|---|
| Release installation | accepted package installs through released installer |
| Installed identity | version/source/content/transport identities verify |
| Runtime locality | consumer operation resolves framework only through `.reasoning-distiller/` |
| Source isolation | invocation still works while source-tree framework paths are unavailable |
| Invocation | valid fixed evidence reaches `rd-distill` through the public contract |
| Preservation | raw candidate is preserved without post-hoc semantic repair |
| Submission | valid candidate is immutably submitted using existing RGP protocol |
| Authority | no canonical admission/reconciliation authority is acquired by Distiller |
| Ownership | source/project-owned files outside intended trial material are unchanged |
| Audit | zero executable source-tree fallback/reference violations |

## FAIL conditions

The trial fails if, among other cases:

- installation requires unpublished repository knowledge;
- installed runtime imports, opens, resolves, or falls back to adjacent framework source;
- source-tree denial breaks a consumer operation that should be supplied by the package;
- project-owned authority is inferred from generic installed roles;
- canonical state is mutated by `rd-distill`;
- raw model output is silently repaired;
- the measured run requires editing product source to continue.

## Durable evidence

Persist a trial record containing exact release identities, repository base commit, installation result, isolation mechanism, invocation request/result, raw-candidate digest/path, submission digest/path, audit output, findings, and disposition.

---

# Trial B — Greenfield Consumer Trial

## Test motivation

Migration tests and self-consumption tests begin with repositories that already contain Reasoning Distiller development history or integration knowledge. They can therefore hide assumptions that a new adopter does not possess.

The greenfield trial asks:

> Can a person or agent begin with an essentially empty repository and reach a valid Reasoning Distiller candidate submission using only the released product and public documentation?

Its primary purpose is to discover the **minimum legitimate project bootstrap boundary**. Missing configuration, unclear ownership, undocumented directories, assumed role activation, and tribal operational knowledge are findings rather than things to quietly pre-seed.

## Initial state

Create a new disposable repository containing only:

```text
README.md
.gitignore
```

No Reasoning Distiller project structure, Project Knowledge Package, role assignment, canonical backend, source registry, submission directory, or integration wrapper may be pre-created unless a public document explicitly instructs a new consumer to create it before the measured run.

Record the initial commit and prove the repository contains no hidden Reasoning Distiller scaffolding.

## Procedure

1. Give the operator/agent the repository plus public Reasoning Distiller release/documentation entrypoints.
2. Select and retrieve an exact accepted release.
3. Follow `INSTALLING.md` to install `.reasoning-distiller/`.
4. Attempt to proceed toward a production `rd-distill` invocation using only public documentation.
5. When the product requires project-owned configuration that has no defined initialization path, STOP and record the requirement as a bootstrap finding. Do not invent a private convention during the measured run.
6. If a documented bootstrap path exists, follow it exactly.
7. Add one small evidence document with clear factual content.
8. Construct a fixed-evidence invocation request using only documented project/product mechanisms.
9. Execute installed `rd-distill` and preserve raw output.
10. Validate and immutably persist the candidate submission.
11. Verify the Distiller stops before reconciliation/admission.
12. Record the complete repository diff and classify every created path as package-managed or project-owned.
13. Record PASS/FAIL and all findings.

## Expected first-run value

This trial is explicitly permitted to fail at bootstrap. A clean failure that identifies an undefined project initialization requirement is more valuable than a PASS obtained through ad hoc scaffolding.

Findings should answer questions such as:

- What is the smallest project-owned structure required before first invocation?
- How is a submission path selected?
- How is a source registry established?
- Is a Project Knowledge Package required for first use or only for richer integration?
- How are project roles activated without confusing generic role definitions with authority?
- Which directories are conventions versus normative contracts?
- Can a human follow the docs without knowledge of the voxel-engine extraction history?

These findings are the evidence base for a Project Bootstrap Contract; the trial must not assume that contract in advance.

## PASS criteria

PASS requires all of the following without undocumented scaffolding:

| Property | Required proof |
|---|---|
| Greenfield state | initial repo contains no Distiller integration knowledge |
| Public install | exact accepted release installs using `INSTALLING.md` |
| Discoverability | public docs provide every required next operation |
| Ownership clarity | every created path is clearly package-managed or project-owned |
| Minimal bootstrap | required project configuration is explicit and reproducible |
| Invocation | installed `rd-distill` consumes fixed evidence through public contract |
| Preservation | raw candidate is preserved unchanged |
| Submission | valid RGP candidate is immutably persisted |
| Authority stop | Distiller performs no Steward reconciliation/admission |
| Isolation | generic source repository is unnecessary after release retrieval |

## FAIL conditions

The trial fails or stops with a product finding if:

- a required project path/configuration has no public creation procedure;
- instructions depend on extraction history or developer knowledge;
- the operator must inspect framework source to learn normal usage;
- installation or invocation requires the generic repository after artifact retrieval;
- generic role presence is treated as project authority;
- project-owned knowledge is created inside `.reasoning-distiller/`;
- an invalid/ambiguous state is silently guessed rather than surfaced.

## Durable evidence

Persist the initial tree, exact release identities, operator-visible documentation set, installation result, chronological action log, first blocking bootstrap requirement if any, invocation artifacts if reached, final tree/diff, findings, and disposition.

---

# Relationship between the trials

The trials are complementary and MUST NOT substitute for one another.

```text
Self-Consumption Isolation
    tests source ↔ installed boundary

Greenfield Consumer
    tests product ↔ new-project boundary
```

Recommended execution order:

1. **Self-Consumption Isolation Trial** — inexpensive pressure test for source fallback and package completeness.
2. **Greenfield Consumer Trial** — adoption test used to derive or validate the Project Bootstrap Contract.

A production-ready adoption story ultimately requires both to PASS. If the greenfield trial stops because bootstrap is undefined, use that durable finding to design the bootstrap contract, implement it, then rerun the same trial from a fresh empty repository rather than modifying the failed trial in place.
