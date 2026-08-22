# Fixed Relationship Semantic Analyzer Protocol

Contract: `reasoning-distiller-fixed-relation-analyzer/1`

Status: **Benchmark implementation protocol**

This protocol is non-authoritative. It produces relationship candidates for later Steward semantic reconciliation and never mutates Canon.

For every proposition pair in the exact bound batch, consider all seven hypotheses:

```text
A supports B
B supports A
A depends_on B
B depends_on A
A supersedes B
B supersedes A
A contradicts B
```

Use the accepted RGP semantics:

- `supports`: the source proposition strengthens the target proposition without being constitutive of its derivation;
- `depends_on`: the source proposition's continued validity, applicability, or revision is conditional on the target proposition;
- `supersedes`: the source proposition intentionally replaces the target proposition for the relevant semantic scope;
- `contradicts`: the propositions are semantically incompatible for the relevant scope.

A shared topic, vocabulary, source, or provenance identity is not by itself a relationship. External validation evidence belongs in provenance rather than becoming a graph edge merely because it exists. Do not duplicate premise relationships as general relations.

The analyzer operates on the canonical proposition records supplied in the batch. It may use their statements and canonical metadata, but it does not gain authority from Canon, the repository, a test, a workflow, or this benchmark.

A batch result may emit zero candidate relations. `COMPLETE` means all pairs and all seven hypotheses in that batch were considered, not that any relation was found.
