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
| candidate generation runtime seconds | UNAVAILABLE |
| input tokens | UNAVAILABLE |
| output tokens | UNAVAILABLE |
| monetary cost | UNAVAILABLE |
| index storage bytes | 0 (derived) |

## Relationship Results

| Metric | Result |
|---|---:|
| baseline relations | 668 (measured) |
| baseline relations covered | 668 (derived) |
| baseline relations missed | 0 (derived) |
| baseline recall percent | 100.0 % (derived) |

## Misses

None recorded at this stage.

## Efficiency

**Pair-space reduction:** 0.0 % (derived)  
**Baseline recall:** 100.0 % (derived)

## Verdict

**PASS**

The pre-result hypothesis is preserved unchanged from the report template.

All 78 exhaustive A0 semantic batches are COMPLETE and validated: 67528 unordered pairs, 472696 relationship hypotheses, and 1128 raw non-authoritative candidate relations.

Fresh Steward semantic reconciliation reviewed all 1128 raw A0 candidates and established 668 approved exhaustive baseline relations.

This reconciliation is non-admitting; canonical PEMS/COVE state remains unchanged until a separately activated admission invocation.
