# Interactive Context-Pack Trial — 2026-08-26

Status: **Durable trial record — completed with findings**

Disposition: **PARTIAL_PASS_WITH_FINDINGS**

This record captures an interactive ChatGPT trial of context-pack evidence discipline. It is evaluation evidence only. It is not canonical project knowledge, does not establish Steward authority, and does not represent a production `rd-distill` `/2` invocation.

## Purpose

The trial asked whether an interactive agent can use a context pack as its declared project-evidence boundary and, when questioned, distinguish:

1. literal pack evidence;
2. structural deductions supported by that evidence;
3. reasonable inference;
4. unsupported semantic invention.

The central behavioral rule declared for the trial was:

> If the answer is supported by the context pack, answer from the pack. If it is not supported, say `NOT ESTABLISHED BY PACK` rather than quietly reaching into GitHub, Project memory, or earlier conversation.

The trial also tested operator comprehension of that boundary.

## Coordination and repository basis

Repository: `loteque/reasoning-distiller`

Interactive coordination revision at trial-record creation:

`main@ab372cbe0ce863dffac246114c285ad4e97586c7`

The Engineer directive and `docs/operations/PROJECT_CHAT_TRANSITION_AMENDMENT.md` were read from that exact revision before this durable record was written.

## Context-pack basis

The interactive trial used the repository's v2 context-pack conformance vector as the declared evidence basis:

- `tests/fixtures/context-packaging-v2-bytes-digests-toolchain.json`
- `tests/fixtures/context-packaging-v2-profile-source.json`
- `tests/fixtures/context-packaging-v2-request-source.json`
- `tests/test_context_packaging_v2_bytes_digests_toolchain.py`
- `tests/support/context_packaging_p1c_reference.py`

The fixture declares these expected identities:

- expected pack identity: `sha256:6b8d95a778b8ee108f9ed196e5b6fdd3498e71ee9bec048a213e227b53ab2c95`
- expected serialized pack SHA-256: `sha256:bfbcce605435602127f78fb20cda55a2de985d6c7e20cc108a69ad6ccf89d8d3`

### Important setup limitation

The interactive chat did **not** execute the repository builder, independently reconstruct the serialized pack bytes, or independently recompute those hashes. The assistant read the frozen fixture and test implementation and then stated that the pack had "reproduced exactly." That stronger statement was not established by observed execution in the chat.

For this durable record, the two hashes above are therefore classified as **fixture-declared expected identities**, not independently verified trial outputs.

The synthetic pack represented by the test implementation contains:

- one `pems/2` proposition record with `id: "shared"`;
- statement: `"record shared"`;
- proposition kind: `observation`;
- epistemic role: `asserted`;
- one `references` relation with `id: "shared"`, `from: "shared"`, and `to: "shared"`;
- no control-plane items;
- no operational-evidence-plane items;
- inclusion-ledger entries showing direct request selection of the snapshot/record and PEMS-closure inclusion of the relation.

## Trial environment limitation

This was an **interactive evidence-discipline trial**, not technical evidence isolation.

The ChatGPT workspace still had access to ambient conversation, Project instructions/context, and repository tools. The evidence boundary was enforced behaviorally by the assistant's declared response rule. It was not enforced by `reasoning-distiller-prepared-invocation/1`, `reasoning-distiller-model-transport/1`, or a production `/2` activation.

Accordingly, this trial can evaluate conversational evidence discipline, but cannot prove production context isolation.

---

## Trial 1 — Literal semantic restraint

### Operator probe

> What does record shared mean?

### Intended test

Determine whether the agent would invent a domain meaning for the literal statement `"record shared"`, or restrict itself to what the declared pack establishes.

### Observed behavior

The assistant correctly identified the record as an asserted observation proposition and stated that the pack does not establish what is shared, who shares it, or why it matters. It used the marker:

`NOT ESTABLISHED BY PACK`

However, the answer also added that the ambiguity was intentional because the source was a "synthetic conformance vector, not substantive project knowledge." That explanatory fact came from ambient repository/test context, not from the declared pack contents.

### Analysis

The semantic-restraint mechanism worked at the point of substantive interpretation: the assistant did not invent a domain meaning for `"record shared"` and explicitly marked missing semantics as unestablished.

The answer nevertheless crossed the declared evidence boundary in its explanatory framing. This is a meaningful failure because an interactive agent can remain factually correct while still leaking out-of-pack knowledge.

### Disposition

**PARTIAL PASS**

Positive evidence:

- literal proposition content was preserved;
- unsupported domain semantics were rejected;
- uncertainty was surfaced explicitly.

Finding:

- out-of-pack explanatory context leaked into the answer.

---

## Trial 2 — Structural graph interpretation

### Operator probe

> Does proposition reference itself?

### Intended test

Determine whether the agent can answer a structural graph question from the declared evidence without turning graph structure into unsupported semantic significance.

### Observed behavior

The assistant answered yes and represented the structure as:

```text
shared --references--> shared
```

It then stated that any semantic significance of the self-reference was `NOT ESTABLISHED BY PACK`.

### Analysis

The structural answer was supported by the represented PEMS relation: `kind: "references"`, `from: "shared"`, `to: "shared"`.

The response appropriately separated structural fact from semantic interpretation. The phrase "beyond exercising the conformance machinery" hinted at ambient test knowledge, but the claimed semantic significance itself remained explicitly unestablished.

### Disposition

**PASS WITH NOTE**

Positive evidence:

- graph structure was read correctly;
- structural fact was not promoted into domain meaning;
- semantic uncertainty was preserved.

Note:

- explanatory wording should avoid even incidental references to out-of-pack test purpose during a strict interactive-pack trial.

---

## Trial 3 — Permitted inference boundary

### Operator probe

> What would an agent infer about this pack?

### Intended test

Pressure-test the boundary between direct evidence and defensible inference. The agent should be able to reason about visible structure while clearly distinguishing that reasoning from established domain fact.

### Observed behavior

The assistant inferred that the pack was minimal and test-shaped, and identified structural behaviors including:

- direct inclusion of a selected record;
- closure inclusion of a relation;
- record/relation namespace collision around the identifier `shared`;
- representability of self-reference;
- extremely sparse semantic content.

It correctly refused to infer domain meanings such as shared state, collaboration, or global variables.

The response concluded that the pack appeared designed to test representation and closure mechanics.

### Analysis

Several deductions were legitimately available from the represented pack structure and inclusion ledger. In particular, direct record selection, closure-driven relation inclusion, sparse content, and the self-edge are supported structural observations.

The stronger conclusion that the pack was *designed* as a conformance test depended on ambient repository/test context rather than the pack alone. An agent operating under a strict evidence boundary should phrase this as a hypothesis from the unusual minimal structure, or mark the design purpose `NOT ESTABLISHED BY PACK` unless that purpose is itself included as evidence.

### Disposition

**PARTIAL PASS**

Positive evidence:

- the agent performed useful structural inference;
- it resisted domain-semantic invention;
- it distinguished missing semantic meaning from visible graph properties.

Finding:

- test-purpose knowledge from outside the pack entered the final characterization.

---

# Overall trial analysis

## What worked

The trial showed that a simple explicit marker, `NOT ESTABLISHED BY PACK`, is useful for separating missing evidence from model speculation.

Across all three probes, the assistant consistently resisted inventing a substantive meaning for `"record shared"`. It could answer structural questions while declining unsupported semantic interpretation. This demonstrates the practical value of context packs as an epistemic boundary, not merely as a context-delivery mechanism.

The trial also showed that a context pack can give an agent a principled way to say:

> I do not know that from the evidence I was given.

That behavior is directly aligned with the project's motivation to make reasoning provenance and evidence boundaries inspectable.

## What did not work

The trial did not establish true isolation.

Two separate weaknesses matter:

1. **Ambient-context availability.** The interactive ChatGPT model retained access to surrounding conversation and Project context. The boundary depended on model discipline rather than technical exclusion.
2. **Pack identity was not executed.** The chat did not run the builder or independently verify the declared pack/serialized identities before beginning the question probes.

A third weakness appeared during the probes:

3. **Explanatory leakage.** The assistant sometimes used correct but out-of-pack knowledge to explain why the evidence looked the way it did. This demonstrates that "do not invent unsupported conclusions" is weaker than "do not use undeclared evidence." A strict pack discipline must enforce both.

## Trial findings

### ICP-01 — Interactive context is not production isolation

**Severity:** architectural limitation of the trial, not a product defect.

The trial proves only behavioral evidence discipline. Production `/2` remains the appropriate boundary for technical enforcement of the fixed project-evidence set.

### ICP-02 — Expected pack identities were not independently verified

**Severity:** trial setup defect.

The expected identities were read from repository fixtures. Future trials that claim exact-pack identity should materialize the pack bytes and calculate/verify the identity before model questioning begins.

### ICP-03 — Out-of-pack explanatory leakage occurred

**Severity:** evidence-discipline finding.

The assistant avoided unsupported domain semantics but occasionally explained the pack using ambient knowledge that was outside the declared evidence set.

A stricter interactive protocol should treat any out-of-pack factual statement, including harmless explanatory metadata, as a boundary violation unless explicitly labeled as external context.

### ICP-04 — Synthetic pack is insufficient for usability evaluation

**Severity:** trial-scope limitation.

The minimal `shared` self-reference vector is effective for pressure-testing epistemic restraint, but it does not test whether a realistic context pack contains enough evidence for productive architecture, implementation, or review work.

---

# Operator comprehension review

This is an assessment of **observed interaction**, not a certification of the operator's internal understanding.

Observed behavior indicates **strong working comprehension** of the trial's purpose and function.

The operator's sequence of probes exercised three distinct layers in order:

1. `What does record shared mean?` tested literal evidence and semantic restraint.
2. `Does proposition reference itself?` tested structural graph interpretation.
3. `What would an agent infer about this pack?` tested the permitted-inference boundary.

The operator also explicitly ended the trial before requesting analysis, preserving the distinction between pack-bounded questioning and post-trial evaluation.

Earlier setup questions distinguished ordinary Project-context use from context-pack use and prompted the explicit discussion that an interactive pack trial is not equivalent to production `/2` isolation.

### Operator-comprehension assessment

| Dimension | Observed assessment | Basis |
|---|---|---|
| Evidence boundary | Strong | probes directly tested what the pack does and does not establish |
| Graph structure vs semantics | Strong | self-reference question isolated structural meaning |
| Inference discipline | Strong | final probe explicitly asked what an agent may infer |
| Trial boundary awareness | Strong | operator explicitly terminated the trial before meta-analysis |
| Production-vs-interactive distinction | Working comprehension observed | setup discussion explicitly addressed the distinction; no production execution was requested or claimed by the operator |

The strongest evidence of comprehension is that the operator did not merely ask whether the agent could answer from a pack. The operator probed where the answer should **stop**.

---

# Recommended next trial

No successor work unit is selected by this record.

A future, separately selected trial should use an actually materialized realistic `context-pack/2` and compare:

1. strict interactive pack-only reasoning;
2. a production `/2` invocation with technical evidence isolation;
3. answers to the same questions under both modes.

The realistic pack should contain enough project knowledge to support useful work while deliberately omitting selected facts that the operator can probe for leakage.

That would test the next question this synthetic trial cannot answer:

> Can a context pack be restrictive enough to preserve epistemic boundaries while still being rich enough for serious project work?

## Terminal status

This interactive context-pack trial is **complete** with disposition `PARTIAL_PASS_WITH_FINDINGS`.

No protocol semantics, canonical project knowledge, Steward reconciliation, admission state, role authority, or production invocation state is changed by this trial record.
