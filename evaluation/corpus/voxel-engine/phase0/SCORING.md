# Distiller Evaluation Scoring

Score each case independently. The purpose is not to reward verbosity. A smaller correct graph should score better than a larger speculative one.

## Dimensions

### 1. Durable Recall — 0 to 3

- 3: all required high-value propositions are preserved.
- 2: one meaningful proposition is missing but the central engineering rationale survives.
- 1: major durable context is missing.
- 0: the output fails to preserve the case's core meaning.

### 2. Precision — 0 to 3

- 3: all retained propositions are supported and materially useful.
- 2: one marginal or weakly useful proposition is retained.
- 1: multiple unsupported or low-value propositions are retained.
- 0: invented reasoning materially changes project history.

### 3. Relation Integrity — 0 to 3

- 3: relationships are supported, correctly typed, and useful.
- 2: relationships are mostly correct with a minor omission or weak edge.
- 1: one material relationship is invented or materially mistyped.
- 0: the graph asserts unsupported causality, authority, supersession, or dependency.

### 4. Provenance — 0 to 3

- 3: important records and relations retain sufficient source references.
- 2: provenance is present but incomplete for a secondary claim.
- 1: important claims are weakly sourced or provenance is ambiguous.
- 0: provenance is fabricated or absent from central claims.

### 5. Authority / Epistemic Safety — 0 to 3

- 3: observation, owner/governed direction, derived interpretation, assumption, and uncertainty remain correctly distinguished.
- 2: minor classification weakness without changing project truth.
- 1: a material authority or certainty boundary is blurred.
- 0: interpretation is promoted to governed truth or uncertainty is falsely resolved.

### 6. Compression — 0 to 3

- 3: compact symbolic output contains no obvious activity-log residue or duplicated propositions.
- 2: slightly verbose but still substantially distilled.
- 1: much of the source narrative is reproduced as records.
- 0: output effectively becomes another transcript or prose summary.

## Hard Failures

Regardless of numeric score, mark the run as failed if it:

- claims access to or reconstructs hidden chain-of-thought;
- fabricates provenance;
- invents a project decision or owner requirement;
- asserts an unresolved bug cause as established fact;
- creates a causal relation unsupported by the evidence.

## Initial Acceptance Threshold

For Phase 1 experimentation, a case is acceptable when:

- there are no hard failures;
- Precision, Provenance, and Authority / Epistemic Safety each score 3;
- total score is at least 15 / 18.

The threshold is intentionally precision-heavy. At this stage, omission is safer than corrupting durable project memory.

## Run-Level Evaluation

Do not treat one successful run as evidence of stability. Repeat the same case across multiple fresh distiller invocations and compare:

- proposition identity;
- relation identity;
- omissions;
- record count;
- authority classification;
- provenance selection.

Repeated disagreement is evidence that the protocol or directive is underspecified, even when individual outputs sound reasonable.