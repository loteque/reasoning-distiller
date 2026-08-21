# Relationship Discovery Benchmark Design Contract

Status: **Accepted**

Contract: `reasoning-distiller-relationship-discovery-benchmark/1`

Accepted amendment: every individual run report MUST include a concise hypothesis explaining the algorithm and why it was selected as a candidate. The hypothesis MUST be preserved in both the human-readable and machine-readable report.

Implementation status: **implementation and benchmark execution authorized by this contract; Steward semantic reconciliation, relation admission, and Canon mutation are not authorized by this document alone.**

## 1. Purpose

This contract defines a reproducible experiment for:

1. producing an exhaustive relationship-discovery baseline over existing Canon;
2. using that baseline to repair currently missing canonical relations through normal Steward reconciliation and guarded admission;
3. evaluating more efficient relationship candidate-selection algorithms against the frozen baseline;
4. identifying the least expensive algorithm that preserves baseline relationship coverage; and
5. producing durable human-readable and machine-readable reports for every algorithm and for the experiment as a whole.

The experiment tests relationship discovery efficiency, not alternative semantic authority models.

## 2. Frozen benchmark corpus

The benchmark SHALL bind to one immutable PEMS state.

Initial benchmark:

```text
benchmark_id:
  relationship-discovery-v1

repository_commit:
  b04bfd16b4e6a73f37490a6a4be83b843b69cbd4

pems_sha256:
  217eaedc614420a904b1ccc637b46a7cefce5c4b54b98ae9d39615ad1af5be0e

cove_sha256:
  3e7326f1a1c6e35bc9c615f92ff9808922fff7a02609e0e3569f6042522b5925

eligible_records:
  kind == "proposition"
  lifecycle == "current"
```

The expected initial eligible population is 368 propositions.

The benchmark runner SHALL fail closed if the frozen corpus does not match its declared identity.

Future Canon mutations do not alter this benchmark corpus.

## 3. Relationship vocabulary

Only existing canonical relation types are in scope:

```text
supports
depends_on
supersedes
contradicts
```

For each unordered proposition pair `{A,B}`, the exhaustive analyzer considers:

```text
A supports B
B supports A

A depends_on B
B depends_on A

A supersedes B
B supersedes A

A contradicts B
```

`contradicts` is treated as symmetric for candidate-space accounting.

No new relation vocabulary may be introduced during the experiment.

## 4. A0 exhaustive baseline

Algorithm:

```text
A0-exhaustive/1
```

For `n` eligible propositions:

```text
PAIRSPACE = n(n-1)/2
```

For the initial corpus:

```text
n = 368

PAIRSPACE = 67,528 unordered pairs

HYPOTHESIS_SPACE =
    67,528 × 7
  = 472,696 relationship hypotheses
```

The implementation MAY batch work for context and execution efficiency.

Batch boundaries SHALL have no semantic meaning.

Coverage MUST satisfy:

```text
expected = every_unique_pair(P)
covered = union(all_A0_batches)

assert covered == expected
assert duplicate_pair_assessments == 0
assert missing_pairs == 0
```

A0 may emit zero or more candidate relations for each assessed pair.

## 5. Baseline semantic reconciliation

Exhaustive coverage does not make A0 semantically authoritative.

A0 output SHALL pass through normal semantic reconciliation using freshly activated authorized Steward authority.

```text
A0 candidates
    ↓
Steward reconciliation
    ↓
approved exhaustive relations
    ↓
REFERENCE BASELINE
```

The resulting approved set is:

```text
B = baseline relationship set
```

`B` is the benchmark reference answer.

It is explicitly not claimed to be metaphysically complete truth. It is the controlled exhaustive baseline against which algorithms in this experiment are measured.

## 6. Canon backfill

After the baseline is reconciled, the approved A0 relationships MAY be admitted into Canon through a separate fresh admission activation.

Admission SHALL:

```text
add approved relations only
change zero existing records
change zero proposition contents
change zero source identities
```

The benchmark continues to use the original frozen pre-backfill corpus.

Thus Canon repair and algorithm evaluation cannot change the benchmark underneath later algorithms.

## 7. Algorithms under test

Algorithms `A1...An` are primarily candidate-selection algorithms.

Every algorithm receives:

```text
same frozen proposition corpus
same relationship vocabulary
same relationship semantics
```

The algorithm produces a subset:

```text
C ⊆ PAIRSPACE
```

or, where relation-type-aware selection is used:

```text
H ⊆ HYPOTHESIS_SPACE
```

The algorithm's job is to reduce semantic work while retaining relationships present in `B`.

### Baseline blindness

Algorithms under test MUST NOT inspect:

```text
A0 candidate relations
A0 Steward dispositions
baseline positive pairs
baseline relationship set B
previous algorithm evaluation results that reveal B
```

during candidate generation.

The evaluator may read both algorithm output and `B` after candidate generation is immutable.

This prevents benchmark leakage.

## 8. Primary correctness metric

The primary metric is baseline relationship coverage recall:

```text
R = |B_covered| / |B|
```

where `B_covered` is the set of baseline-approved relationships whose necessary pair or hypothesis survived candidate selection.

A candidate production algorithm initially requires:

```text
baseline coverage recall = 100%
```

Any algorithm below 100% is loss-bearing relative to the baseline and SHALL identify every missed baseline relationship and the pruning rule responsible.

## 9. Efficiency metrics

Every algorithm SHALL report at least:

```text
eligible propositions
total possible pairs
pairs retained
pairs pruned
pair-space searched %
pair-space reduction %

relationship hypotheses retained
baseline relations
baseline relations covered
baseline relations missed
baseline recall %

candidate generation runtime
semantic analyses required
input tokens, when measurable
output tokens, when measurable
monetary cost, when measurable
index/storage overhead, when applicable
```

The benchmark SHALL distinguish measured metrics from derived or unavailable metrics.

## 10. Controlled semantic analyzer

Optimized candidate-selection algorithms SHALL NOT silently replace the semantic relationship analyzer.

Conceptually:

```text
candidate_pairs = ALGORITHM(Canon)
relations = FIXED_RELATION_ANALYZER(candidate_pairs)
```

This allows the experiment to determine whether improvement came from candidate selection rather than changing semantic judgment.

Candidate coverage against `B` is the deterministic primary comparison.

End-to-end semantic reruns MAY additionally be measured, but model variance SHALL NOT replace candidate-coverage recall as the primary selector metric.

## 11. Required individual reports

Every algorithm, including failures, SHALL persist:

```text
report.md
report.json
```

The Markdown report is human-readable.

The JSON report is machine-readable and governed by:

```text
reasoning-distiller-relationship-algorithm-report/1
```

Both representations MUST describe the same run.

The JSON report is normative for aggregation.

The Markdown report SHALL be deterministically generated from, or validated against, the JSON report.

### Concise hypothesis

Every individual run report MUST contain a concise hypothesis recorded before the run result is known.

The hypothesis MUST explain:

1. what the algorithm does;
2. why the algorithm was selected as a candidate for this experiment; and
3. what efficiency or coverage behavior is expected and why.

The machine-readable report MUST preserve this as structured fields equivalent to:

```text
hypothesis:
  algorithm_summary
  selection_rationale
  expected_behavior
```

The human-readable report MUST present the same information under a `Hypothesis` section.

The hypothesis is historical experimental reasoning. It MUST NOT be rewritten after results are known. Post-run interpretation belongs in the report's results, misses, efficiency, and verdict sections.

### Standard human report

Every report SHALL use:

```text
Relationship Discovery Algorithm Report

Identity
Hypothesis
Method
Work
Relationship Results
Misses
Efficiency
Verdict
```

and prominently expose:

```text
Pair-space reduction: X%
Baseline recall:       Y%
```

### Verdict vocabulary

```text
PASS
FAIL_LOSS
FAIL_INVALID
INCOMPLETE
```

`PASS` requires 100% baseline coverage recall unless a later accepted contract explicitly changes the benchmark objective.

## 12. Durable repository layout

```text
evaluation/relationship-discovery/
  benchmark-v1/
    benchmark.json

    baseline/
      A0-exhaustive/
        coverage.json
        candidates.json
        steward-dispositions.json
        report.json
        report.md

    algorithms/
      A1-<name>/
        candidates.json
        report.json
        report.md

      A2-<name>/
        candidates.json
        report.json
        report.md

      ...

    experiment-summary.json
    experiment-summary.md
```

Raw artifacts MAY be subdivided when size requires it, provided their manifest and hashes preserve exact identity.

Reports SHALL never be overwritten by later algorithm versions. A changed algorithm/configuration receives a new algorithm identity.

## 13. Algorithm identity

Every run SHALL bind to:

```text
algorithm_id
algorithm_version
implementation_digest
configuration
benchmark_id
benchmark_digest
execution identity
```

Changing a material pruning rule or configuration produces a distinct run identity.

This prevents results from drifting beneath an unchanged algorithm name.

## 14. Miss analysis

For every failed baseline relationship:

```text
missed = B - covered(B, algorithm_output)
```

the report SHALL identify, when determinable:

```text
relationship
source proposition
target proposition
relation type
pruning stage
pruning rule
reason pair/hypothesis was excluded
```

These misses are experimental evidence.

They SHALL NOT be deleted merely because a later algorithm fixes them.

## 15. Experiment progression

Initial candidate sequence:

```text
A0  exhaustive baseline

A1  provenance/source indexing

A2  concept/entity indexing

A3  typed relation-specific indexing

A4  semantic signatures

A5  multi-index union

A6+ algorithms motivated by prior results
```

This sequence is exploratory, not normative.

An algorithm MAY be skipped or replaced when prior results justify doing so, but the reason SHALL appear in the experiment summary.

Every selected algorithm MUST have its concise hypothesis persisted before its results are recorded.

## 16. Final experiment summary

After the selected algorithm series is complete, persist:

```text
experiment-summary.json
experiment-summary.md
```

The summary SHALL include a comparison table equivalent to:

| Algorithm | Pairs | Reduction | Recall | Semantic Work | Runtime | Verdict |
|---|---:|---:|---:|---:|---:|---|
| A0 | 67,528 | 0% | 100% reference | ... | ... | BASELINE |
| A1 | ... | ... | ... | ... | ... | ... |
| A2 | ... | ... | ... | ... | ... | ... |

The summary SHALL identify:

```text
best lossless algorithm
lowest pair count at 100% recall
lowest measured semantic cost at 100% recall
known tradeoffs
remaining uncertainty
recommended production algorithm
```

Every referenced individual report SHALL be digest-bound.

The experiment summary MAY compare the original hypotheses with observed results, but MUST NOT retroactively modify individual run hypotheses.

## 17. Experiment completion criterion

The experiment is complete when:

```text
assert A0_pair_coverage == 100%
assert A0_reconciliation_complete
assert baseline_reference_set_is_frozen

assert every_algorithm_has_json_report
assert every_algorithm_has_markdown_report
assert every_report_has_pre_result_hypothesis
assert every_report_validates
assert every_report_is_persisted

assert experiment_summary_json_exists
assert experiment_summary_md_exists
assert summary_references_exact_report_digests
```

There is no required number of optimized algorithms.

The experiment ends when sufficient evidence exists to select a production strategy or when further optimization is judged not worthwhile.

## 18. Authority boundaries

The benchmark framework:

```text
may analyze
may measure
may propose relations
may compare algorithms
may persist evaluation evidence
```

It may not:

```text
grant Steward authority
activate Steward authority
approve semantic relationships
admit relationships
mutate Canon directly
treat benchmark success as admission authority
```

Relationship analysis is evidence generation.

Steward reconciliation is semantic judgment.

Admission remains an independently authorized canonical mutation.

## 19. Production integration is out of scope

This contract does not select or integrate the final relationship-discovery algorithm into Distiller.

That requires a later contract based on the experimental results.

The intended sequence is:

```text
benchmark
    ↓
algorithm selection
    ↓
general relationship-analysis/repair primitive
    ↓
Distiller relationship-discovery integration
```

This prevents us from designing the production mechanism before we have empirical evidence about which search strategy works.

## 20. Approval effect

Approval of this contract authorizes implementation and execution of the benchmark machinery described here.

It does not itself authorize:

- Steward semantic reconciliation;
- relation admission; or
- Canon mutation.

Those continue to require their existing explicit authority and activation steps.

The accepted implementation sequence is:

1. commit this exact accepted contract on a feature branch;
2. implement the benchmark/report contracts and validation machinery;
3. freeze and verify the A0 corpus;
4. begin `A0-exhaustive/1`;
5. persist the A0 human-readable and machine-readable reports; and
6. stop at any existing semantic-reconciliation or admission authority boundary that requires a fresh explicit activation.
