# Distiller Phase 0 Baseline

Date: 2026-08-16
Role: Reasoning Graph Protocol Engineer
Contract: `rgp/1`
Status: baseline established for Phase-1 prototype evaluation

## Purpose

This document freezes the initial human-reviewed evaluation baseline for the Reasoning Distiller before prototype implementation begins.

The corpus is evaluation-only. It does not create canonical project memory and does not authorize admission.

## Baseline corpus

The existing core corpus in `cases.yaml` is retained because it already uses completed voxel-engine work and covers five materially different reasoning shapes:

1. `field-authority` — architectural ownership decision.
2. `offline-runtime-split` — generation/runtime separation with explicit scope limits.
3. `validation-demo-contract` — governed validation requirement plus implementation evidence.
4. `resource-loading-investigation` — evidence-driven investigation where conclusions must remain narrower than the hypothesis.
5. `deployed-ui-failure` — unresolved runtime failure where green deployment evidence must not erase negative runtime evidence.

The human-review oracle is `expected.yaml` version 2. It is aligned to the current `rgp/1` semantic core and does not use deprecated/unsupported `validated_by` or embedded authority fields.

The adversarial corpus in `adversarial-cases.yaml` is part of the baseline because it directly pressures:

- authority promotion from summaries/implementation;
- unsupported universal generalization;
- explicit premise requirements for derived claims;
- premise cycles;
- premise versus `depends_on`;
- green workflow evidence conflicting with runtime failure;
- fabricated provenance identifiers;
- unresolved state incorrectly promoted to assumption.

The provenance-specific corpus and scoring remain applicable for provenance-selection experiments.

## RGP/1 evaluation contract

Prototype output is judged against these semantic requirements:

- record kinds are only `observation`, `decision`, `assumption`, `uncertainty`, and `claim`;
- constitutive derivation is represented by non-empty `premise` on the derived record;
- general relations are only `supports`, `contradicts`, `depends_on`, and `supersedes`;
- `validated_by` is not emitted;
- provenance roles are `primary`, `corroborating`, and `context`;
- non-derived observations require supplied primary provenance;
- source identifiers are opaque references and are not graph premises;
- normative authority is resolved externally and is not emitted as an RGP record field;
- uncertainty is not silently converted to fact or assumption;
- unsupported material is omitted rather than repaired by invented provenance or causality;
- hidden chain-of-thought is neither requested nor represented.

## Required evaluation outputs

For every fresh prototype run, preserve the unedited candidate output and record separately:

- case ID;
- run identifier;
- validator pass/fail;
- record count;
- relation count;
- Durable Recall score, 0–3;
- Precision score, 0–3;
- Relation Integrity score, 0–3;
- Provenance score, 0–3;
- Authority / Epistemic Safety score, 0–3;
- Compression score, 0–3;
- hard-failure flags;
- missing required propositions;
- invented propositions;
- mistyped or invented relations;
- duplicate semantic propositions;
- provenance omissions/fabrications;
- authority/certainty promotions;
- notes on run-to-run instability.

Diagnostics are evaluation artifacts only and must not be mixed into the durable candidate graph.

## Phase-1 acceptance threshold

Use the existing precision-heavy scoring threshold:

- no hard failures;
- Precision = 3;
- Provenance = 3;
- Authority / Epistemic Safety = 3;
- total score >= 15 / 18 for each case.

A single passing run is not stability evidence. Each core case should be executed at least three times from fresh Distiller invocations before claiming prototype stability.

For a case to be considered stable enough for shadow-operation consideration:

- all three runs must satisfy the acceptance threshold;
- no run may invent a proposition, relation, provenance identifier, or authority transition;
- required high-value propositions must appear in at least 2 of 3 runs;
- materially equivalent propositions with cosmetic wording variation count as the same semantic proposition for evaluation;
- any disagreement over proposition kind or relation type must be reviewed before progression.

These repetition criteria are evaluation policy, not RGP protocol semantics.

## Explicit negative cases

The prototype must fail evaluation if it does any of the following:

- reconstructs or claims hidden reasoning;
- invents a causal explanation for the deployed UI failure;
- treats successful CI/deployment as proof of runtime correctness;
- turns implementation consistency into a governed future requirement without authoritative provenance;
- turns an unresolved state into an assumption for convenience;
- creates a universal claim from one successful validation/proof;
- collapses distinct proof-success and installation events merely because they concern the same feature;
- duplicates a proposition because of paraphrase alone;
- fabricates a source identifier to satisfy grounding requirements;
- uses `depends_on` as a substitute for premise;
- emits `validated_by` as a relation;
- emits an `authority` field in RGP output.

## Exit assessment

Phase 0 is considered established for prototype work because:

- a real-project core corpus exists;
- human-reviewed expected durable structure exists;
- adversarial failure cases exist;
- a numeric scoring rubric and hard failures exist;
- provenance-specific evaluation exists;
- the baseline is now reconciled to the current `rgp/1` semantic vocabulary.

What Phase 0 does **not** establish is Distiller quality. That evidence can only come from executing the Phase-1 prototype repeatedly against this baseline.

## Next gate

Implement and execute the Reasoning Distiller Phase-1 prototype against this baseline. Do not admit prototype output to canonical PEMS/COVE automatically. Candidate output should first pass the RGP validator and human evaluation.
