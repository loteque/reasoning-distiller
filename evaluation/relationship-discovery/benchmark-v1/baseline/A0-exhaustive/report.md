# Relationship Discovery Algorithm Report

## Identity

- Algorithm: `A0-exhaustive/1`
- Benchmark: `relationship-discovery-v1`
- Execution: `relationship-discovery-v1-A0-exhaustive-20260821`
- Implementation: `sha256:70ad2b2b9fabb0a86ec1963e8cf1b0b31ce1b174d990f7906a1beb77e477f430`
- Benchmark digest: `sha256:2c6ee3c1d1db72e3cc14b44d624e05f14fd048ef85cf5ae2ef3a3615759bfc7a`

## Hypothesis

**Algorithm.** Enumerate every unordered pair of eligible current canonical propositions and consider all seven permitted directed or symmetric relation hypotheses for each pair. Batching is computational only and performs no semantic pruning.

**Why selected.** A0 is selected as the reference candidate because it makes no candidate-selection assumptions and therefore provides complete pair-space coverage against which pruning and indexing algorithms can be measured.

**Expected behavior.** A0 is expected to maximize relationship discovery recall at the cost of quadratic pair coverage: 67,528 proposition pairs and 472,696 relation hypotheses for the frozen 368-proposition corpus. It is not expected to be the production-efficient algorithm.

## Method

Sort the frozen eligible proposition corpus by canonical record ID, divide it into 32-proposition computational blocks, and assess every block pair exactly once. Within a diagonal block assess each unordered pair once; between distinct blocks assess the full Cartesian product. For every proposition pair consider supports and depends_on in both directions, supersedes in both directions, and contradicts symmetrically.

## Work

| Metric | Result |
|---|---:|
| eligible propositions | 368 (measured) |
| total possible pairs | 67528 (derived) |
| pairs retained | 67528 (derived) |
| pairs pruned | 0 (derived) |
| pair space searched percent | 100.0 % (derived) |
| pair space reduction percent | 0.0 % (derived) |
| relationship hypotheses retained | 472696 (derived) |
| semantic analyses required | 67528 (derived) |
| candidate generation runtime seconds | PENDING |
| input tokens | PENDING |
| output tokens | PENDING |
| monetary cost | UNAVAILABLE |
| index storage bytes | 0 (derived) |

## Relationship Results

| Metric | Result |
|---|---:|
| baseline relations | PENDING |
| baseline relations covered | PENDING |
| baseline relations missed | PENDING |
| baseline recall percent | PENDING |

## Misses

None recorded at this stage.

## Efficiency

**Pair-space reduction:** 0.0 % (derived)  
**Baseline recall:** PENDING

## Verdict

**INCOMPLETE**

Hypothesis recorded before semantic A0 results. A0 remains INCOMPLETE until all exhaustive semantic batches are complete and the resulting candidates receive fresh Steward semantic reconciliation.
