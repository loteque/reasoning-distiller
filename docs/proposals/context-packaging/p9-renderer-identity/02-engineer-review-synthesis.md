# P9 Renderer Execution-Identity Amendment - Stage 2 Engineer Review/Synthesis

Status: **Independent review complete; compatible with required revisions**
Method: `proposal-review-synthesis/1`
Repository: `loteque/reasoning-distiller`
Coordination control ref: `main`
Coordination revision resolved before review and re-resolved before this write: `80b6e89ad2efe84b088ca06b908a257c449fac15`
Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
Exact blocked P9 candidate: `e961eb83d2c5dd1719b986c89a8915c102e395c3`
Blocking P9 independent review: `ff482ffcac5b58133ee3a480bab4164ee599732f`
Stage 1 proposal commit: `1cbbb61925c95219b8050c33efd1bf7b68a5fed4`
Stage 1 proposal blob: `a16edba937d8d30dd62dfe1082d0124673eb23e4`
Stage: **Stage 2 independent Engineer review and synthesis**

Authority posture: this is a bounded technical review artifact. It establishes no Project Steward authority, no accepted RIL activation, no reconciliation, no admission, no canonical standing, no implementation approval, and no authority or activation mutation. The Engineer role label is coordination metadata for this review. This artifact does not edit Stage 1 and does not perform the Stage 3 decision.

## 1. Review scope and method

This Stage 2 review is scoped only to the P9 renderer execution-identity amendment required by blocker `P9_RENDERER_COMPONENT_IDENTITY_UNBOUND`.

The review used the current Engineer directive, the current Project chat-transition amendment, and `docs/governance/PROPOSAL_REVIEW_METHOD.md` from exact live coordination revision `80b6e89ad2efe84b088ca06b908a257c449fac15`. It separately inspected the immutable governing plan, exact blocked P9 candidate, frozen renderer contract/profile schema, blocker review, current release-package machinery, and the complete Stage 1 proposal.

The required Stage 2 posture is technical challenge and synthesis rather than endorsement. The decisive questions are:

1. whether in-process self-measurement can be a sufficient trust root for the exact P9 replay requirement;
2. whether a normalized Python code graph can be defined completely enough to prevent stale behavior from hiding behind a stable identity;
3. whether the measured graph is necessarily the graph that executes;
4. what runtime and standard-library semantics must enter the binding;
5. whether the frozen `/1` family can remain wire-compatible;
6. whether a stronger immutable package or execution boundary is necessary rather than merely attractive.

No P9 implementation, P10, Steward reconciliation, admission, canonical mutation, authority mutation, or activation mutation is performed here.

## 2. Independent reconstruction of the blocker

The governing plan requires replay identity to bind the renderer contract and implementation when rendering is performed. The current plan permits individual immutable artifact digests, or a package content identity only when a normative package contract guarantees that the identity immutably fixes every relevant artifact and behavior version.

The exact P9 candidate does not meet that property. Its `/1` profile supplies a renderer Git-blob identity and raw SHA-256, but the executing renderer only validates the shape of those values and copies them into the activation. It does not establish that the supplied values identify the code that actually executed.

The blocker is therefore not a missing checksum field. It is a missing relation:

```text
recorded renderer identity
          |
          X  no proven binding
          |
executing behavior graph
```

A correct remediation must establish that relation while preserving P9's no-discovery rendering boundary.

## 3. Stage 1 agreements

### A1. The current `/1` identity mechanism is not salvageable by stronger syntax checks

Stage 1 correctly rejects caller self-attestation. More validation of a caller-supplied Git blob or SHA-256 does not prove which implementation executed.

### A2. Render-time source or repository hashing is incompatible with the frozen P9 purity boundary

P7 source-byte verification is useful evidence for the security property but is not transferable architecture for P9. P9 rendering and decoding must not acquire source paths, repository state, install receipts, or mutable filesystem state.

### A3. An embedded expected source digest is not an execution proof

A literal can remain stale when behavior changes. A rule that developers must remember to update the literal is process discipline, not a cryptographic relation between recorded identity and executing behavior.

### A4. The amended wire family must be honestly versioned

The `/1` renderer/profile/activation family explicitly represents a Git-blob-based component shape and claims exact implementation binding. Reinterpreting those same bytes to mean an execution fingerprint would silently change frozen semantics. A side-by-side `/2` family is required if the identity model changes.

### A5. Same-object execution is a real requirement

Measuring graph A and then executing through mutable graph B does not close the blocker. The identity check and the render/decode operations must be anchored to the same resolved bundle for the call.

### A6. Package content identity is not, by itself, execution identity

The current release package is a useful content-binding model, but at coordination revision `80b6e89...` it does not manage `context_packaging`. More importantly, the package builder and installer establish package/archive and installed-file identities, not that the Python objects currently executing were loaded from those exact immutable bytes and remained equivalent until execution.

## 4. Blocking Stage 2 findings and required amendments

The Stage 1 direction is technically viable only with the following required revisions. These are not optional hardening notes.

### R1. Freeze the threat model and stop calling self-measurement external attestation

**Finding:** Stage 1 correctly notices that an in-process verifier cannot defend against an arbitrarily malicious runtime, but that boundary is not strong enough in the proposed normative architecture. Without an explicit threat model, `implementation_binding` can be read as stronger evidence than the mechanism can provide.

**Required amendment:** the final plan must state that the runtime-derived scheme, if accepted, provides deterministic detection of stale or mismatched renderer behavior under an accepted, non-hostile execution runtime. It does not establish integrity against:

- a hostile or instrumented interpreter that can lie about code objects;
- untrusted same-process code that can arbitrarily rewrite the verifier and executed functions during a call;
- an attacker controlling both the binding derivation implementation and the runtime introspection results.

If P9 requires protection against those stronger adversaries, the runtime-derived scheme is insufficient and a separately verified immutable execution boundary becomes required.

### R2. Replace the open-ended `python-code-graph/1` idea with a mechanically closed execution-bundle contract

**Finding:** hashing a collection of Python function code objects is not enough. The current renderer reaches module globals and runtime objects including `base64`, `deepcopy`, `hashlib`, `json`, `math`, `BytesIO`, constants, helper functions, and Python builtins. A normalized descriptor that omits any behavior-bearing global, closure value, default, constant, or runtime primitive can reproduce the original blocker inside the fingerprint itself.

**Required amendment:** the accepted design must define a closed renderer bundle before it defines a hash. The bundle contract must:

1. enumerate every repository-owned callable and behavior-bearing constant used by render and decode;
2. enumerate the runtime primitives that may be used without separate artifact identity;
3. reject dynamic imports, dynamic helper discovery, mutable repository-local module dependencies, and unenumerated global references;
4. reject mutable defaults or closure state unless the state is included deterministically and cannot diverge before execution;
5. make unsupported dependency shapes fail closed rather than silently excluding them;
6. include the binding-derivation and binding-comparison behavior itself in the reviewed trust surface.

The contract may use Python code-object introspection as an implementation technique, but the semantic object being bound is the closed execution bundle, not an informal transitive walk of whatever objects happen to be reachable.

### R3. Freeze the normalized callable descriptor before implementation

**Finding:** Stage 1 intentionally leaves the normalized representation open. That is appropriate for Stage 1, but implementation cannot begin while the descriptor is still underspecified. Raw `marshal`, raw `repr`, source paths, line tables, and broad code-object serialization are not acceptable because they either carry host/debug noise or leave semantic inclusion rules implicit.

**Required amendment:** Stage 3 must require a protocol-freeze gate for a versioned normalized callable descriptor. At minimum it must disposition:

- executable instruction bytes or a versioned normalized instruction representation;
- nested code objects;
- argument counts and calling convention;
- flags that affect execution semantics;
- global/name references used by the code;
- free variables and cell variables;
- positional defaults and keyword defaults;
- behavior-bearing immutable closure data;
- behavior-bearing constants;
- exception behavior metadata when it can affect control flow;
- explicit exclusion of filename, checkout path, first line number, line table, and other debug-only metadata;
- treatment of docstrings and other constants that are not executable data;
- deterministic ordering and digest domain.

A field may be excluded only by a frozen rule showing that it cannot affect the accepted renderer behavior under the supported runtime contract.

### R4. Same-bundle execution must be structural, not a timing convention

**Finding:** `derive binding; then call module globals` remains vulnerable to graph substitution between verification and execution. A frozen dataclass around function objects is also not, by itself, enough because Python function objects can still depend on mutable globals and, under a hostile same-process model, can have their code replaced.

**Required amendment:** for the accepted non-hostile-runtime threat model, each render/decode call must:

1. resolve one explicit bundle instance;
2. derive the binding from that bundle instance;
3. compare the exact derived binding with the profile;
4. execute through references captured by that same bundle instance;
5. emit the same derived binding;
6. avoid any module-global behavior lookup after bundle resolution unless the reference is an allowlisted runtime primitive covered by the runtime contract.

No stale binding cache is permitted. If later optimization proposes caching, it must separately prove that the cached binding and executable references cannot diverge.

The final plan must also state the limit clearly: preventing arbitrary concurrent mutation by hostile same-process code requires a stronger execution boundary and is not established by Python object capture alone.

### R5. Runtime ABI identity must be conservative and exact

**Finding:** the proposed `runtime_abi` field is necessary, but `implementation family` or `major/minor` alone is too coarse. The current P9 evidence runs under `python-version: "3.12"`, which is patch-floating. Python patch releases and runtime builds can change interpreter or standard-library behavior without changing `3.12` as a broad label.

**Required amendment:** the initial execution-binding contract must fail closed on runtime equivalence that has not been proven. For CPython, the minimum reviewed ABI tuple should include:

- implementation name;
- major, minor, and micro version;
- implementation cache tag or an equivalent reviewed bytecode/runtime compatibility identifier;
- the execution-binding scheme version.

The final contract may add further runtime identity if pressure tests show the tuple is insufficient. It must not use source path, checkout path, host temporary path, or repository identity as runtime ABI.

The design should reduce the standard-library surface rather than recursively fingerprinting the entire Python installation. Standardized primitives such as SHA-256 and RFC 4648 Base64 may be treated by frozen semantic contract. Broader helpers such as JSON parsing or float rendering must either remain explicitly covered by the exact supported runtime ABI or be replaced by package-owned deterministic behavior.

### R6. The R7 interpretation change is a governance amendment, not an Engineer implementation choice

**Finding:** the governing plan currently names immutable implementation artifacts and qualifying package content identities. Stage 1 proposes a third accepted proof form, a runtime-derived execution binding. That is a semantic change to the approved replay-identity basis.

**Required amendment:** Stage 3 must explicitly disposition whether a frozen execution-binding contract is an accepted R7 proof form for P9. An implementation Engineer may not infer that approval from this review, from successful tests, or from the apparent technical sufficiency of the scheme.

If Stage 3 rejects that amendment, P9 remains blocked until an artifact/package/execution architecture satisfying the existing R7 text is approved.

### R7. `/2` migration must reject `/1` rather than auto-upgrade it

**Finding:** Stage 1 is correct that `/1` bytes cannot inherit `/2` guarantees. The final migration rule should be made normative rather than advisory.

**Required amendment:** the `/2` renderer must not accept a `/1` profile as an execution-bound profile, and no migration may transform a `/1` caller-declared Git blob/SHA pair into `/2` execution proof without deriving a valid `/2` binding from a supported renderer execution bundle.

## 5. Is a stronger immutable package/execution boundary necessary?

### Stage 2 conclusion

**Not strictly necessary for the exact P9 blocker under the bounded stale/mismatch threat model, but necessary for a stronger hostile-runtime or hostile-same-process integrity claim.**

A runtime-derived binding can close `P9_RENDERER_COMPONENT_IDENTITY_UNBOUND` if all of R1-R7 are satisfied. Under that bounded model, the accepted runtime is part of the trust base, the execution bundle is mechanically closed, the binding is derived from that exact bundle, and the same bundle performs the call. A changed renderer entrypoint, helper, constant, or supported runtime ABI then changes the required binding or fails closed under the old profile without any filesystem discovery.

A stronger package/execution boundary is therefore not required merely because self-measurement is in-process. It becomes required if the desired guarantee is any of the following:

- prove integrity against a runtime that can falsify introspection;
- prove integrity against arbitrary same-process mutation between measurement and execution;
- prove that loaded objects came from a particular release package rather than only that their normalized behavior descriptor matches;
- make package provenance itself the trust root rather than the accepted runtime plus execution-binding contract.

### Why the current package mechanism is insufficient as-is

The current release package does not include `context_packaging` in its managed roots. Even after adding it, the existing content identity proves the deterministic package file set, and the installer verifies transport/archive bytes and can detect installed-file drift when its drift check is invoked. Those properties do not by themselves prove that a render call is executing objects loaded from those exact files.

A package-based P9 solution would therefore need a new or amended execution contract that establishes at least:

```text
verified immutable package identity
            |
            v
verified loader / execution environment
            |
            v
exact loaded renderer behavior
            |
            v
render/decode call
```

That is a materially broader architecture than copying the existing package `content_identity` into the profile. It should not be smuggled into P9 as a small implementation detail.

## 6. Recommended architecture synthesis

Subject to Stage 3 authority, the narrowest viable amended P9 architecture is:

### 6.1 Side-by-side versioned contracts

Introduce:

```text
reasoning-distiller-context-renderer/2
reasoning-distiller-context-renderer-profile/2
reasoning-distiller-context-rendered-activation/2
reasoning-distiller-renderer-execution-binding/1
```

Retain unchanged:

```text
reasoning-distiller-context-renderer-framing/1
reasoning-distiller-context-pack-failure/1
reasoning-distiller-context-pack/1
reasoning-distiller-context-pack/2
jcs/1
```

### 6.2 Execution binding shape

The exact schema remains a Stage 3/freeze decision, but the semantic content should be equivalent to:

```json
{
  "contract": "reasoning-distiller-renderer-execution-binding/1",
  "scheme": "python-closed-bundle/1",
  "runtime_abi": {
    "implementation": "cpython",
    "major": 3,
    "minor": 12,
    "micro": 0,
    "cache_tag": "<reviewed exact value>"
  },
  "identity_sha256": "sha256:<64 lowercase hex>"
}
```

The profile carries the expected binding. The renderer derives the actual binding from the resolved execution bundle and compares exact canonical values before returning success. The activation records the derived value, not an unchecked profile copy.

### 6.3 Closed renderer bundle

The renderer should be refactored around one explicit bundle containing:

- render entry behavior;
- decode entry behavior;
- profile/component validation behavior;
- pack validation and summary behavior;
- strict JSON behavior;
- JCS behavior;
- frame encode/decode behavior;
- digest-domain behavior;
- limit behavior;
- activation identity behavior;
- all behavior-bearing constants;
- the binding descriptor/derivation logic required to bind the bundle;
- an explicit small allowlist of runtime primitives.

The bundle freeze gate must prove there are no hidden mutable repository-local dependencies.

### 6.4 Execution sequence

```text
pack + exact profile /2
        |
        v
resolve closed bundle once
        |
        +--> derive exact runtime ABI
        +--> derive normalized bundle descriptor
        +--> derive execution binding
        |
        +--> exact profile binding mismatch => fail closed
        |
        v
execute render/decode through that same bundle
        |
        v
activation records derived execution binding
```

## 7. Required pressure cases before implementation acceptance

Retain Stage 1 RI-01 through RI-16, with the following additions or sharpened forms.

### RI-17 - Binding verifier mutation

Change behavior-bearing code in the descriptor/binding verifier itself while holding the old profile binding constant. The old profile must fail or require a new binding.

### RI-18 - Post-resolution global substitution

Resolve the bundle and derive its binding, then substitute a module-global helper that would change behavior if later looked up. The call must either continue through the already-bound reference with unchanged correct behavior or fail closed. It must not silently execute the substituted global under the old binding.

### RI-19 - Mutable closure/default rejection

Introduce a renderer helper whose semantics depend on mutable closure data or a mutable default not represented by the binding. Bundle construction must fail closed rather than produce a successful binding.

### RI-20 - Runtime micro-version mismatch

Reuse an otherwise matching profile across a different supported CPython micro version without an explicit equivalence rule. The renderer must report runtime/toolchain incompatibility before success.

### RI-21 - Runtime primitive substitution

Replace an allowlisted runtime primitive reference with a semantically different callable. Bundle construction or binding comparison must fail unless the changed primitive is explicitly represented by a changed binding.

### RI-22 - Unsupported interpreter implementation

Run the binding derivation under an interpreter family not accepted by the execution-binding contract. Fail closed rather than generate a plausibly compatible binding.

### RI-23 - Descriptor noise stability

Change filename, checkout path, line table, first source line, and non-executable comments/docstrings. The derived binding must remain stable when the frozen descriptor contract classifies those fields as non-semantic.

### RI-24 - No discovery despite identity validation

Force repository, filesystem, installation-manifest, current-branch, and network APIs to fail. A truthful `/2` render/decode must still succeed because identity derivation uses only the in-memory bundle and accepted runtime information.

## 8. Implementation gates synthesized for Stage 3

If Stage 3 accepts the runtime-derived direction, P9 implementation should not resume directly from the Stage 1 sequence. The implementation-ready order should be:

1. **Threat-model freeze.** Accept or reject the bounded non-hostile-runtime trust model.
2. **R7 amendment disposition.** Explicitly authorize or reject `reasoning-distiller-renderer-execution-binding/1` as a P9 replay-identity proof form.
3. **Pressure-case freeze.** Materialize RI-01 through RI-24 with stable expected outcomes.
4. **Execution-bundle contract freeze.** Define allowed members, dependencies, mutable-state rejection, and same-bundle execution rules.
5. **Normalized descriptor freeze.** Define exact callable/data descriptor fields, exclusions, ordering, and digest domain.
6. **Runtime ABI freeze.** Define exact initial CPython ABI tuple and primitive boundary.
7. **Wire-contract freeze.** Freeze side-by-side renderer/profile/activation `/2` contracts and explicit `/1` rejection/migration rules.
8. **Implementation.** Refactor the existing structural renderer to the closed bundle without changing its plane, framing, pack, bounds, trust-channel, or no-side-effect semantics.
9. **Adversarial identity execution.** Prove stale entrypoint/helper/constant/verifier/runtime identities fail closed.
10. **Original P9 regressions.** Re-run structural plane, framing, round-trip, PC-33/44/45/46 intent, byte-bound, no-truncation, and purity gates.
11. **Unaffected P0-P8 regressions.** Preserve inherited red classifications separately.
12. **Candidate-bound immutable evidence and fresh independent P9 review.** P9 remains open until a remediated exact candidate receives independent PASS evidence.

If Stage 3 rejects the bounded self-measurement trust model, implementation must stop and a separately governed immutable package/execution-boundary design is required before P9 can resume.

## 9. Recommendations that are not blockers

### N1. Keep package provenance separate from execution proof

A source blob, source commit, or release-package identity remains useful audit provenance. It should not be presented as executing proof unless a later verified loader/execution contract establishes that relation.

### N2. Prefer a smaller primitive boundary over a larger runtime fingerprint

The renderer should continue owning deterministic JCS and strict validation behavior where practical. Reducing dependencies is easier to reason about than recursively fingerprinting a large standard-library object graph.

### N3. Use the existing failure family unless Stage 3 identifies a semantic gap

`TOOLCHAIN_IDENTITY_MISMATCH` or the existing renderer incompatibility path is sufficient for execution-binding mismatch. A new failure contract is not justified merely to rename the blocker.

### N4. Package/execution hardening can remain a future option

A later immutable execution-package design may provide a cleaner external root. It should remain compatible with `/2` by defining another execution-binding scheme rather than retroactively changing the meaning of `python-closed-bundle/1`.

## 10. Stage 2 recommendation

**Recommendation: `P9_RENDERER_IDENTITY_STAGE2_COMPATIBLE_WITH_REQUIRED_REVISIONS`.**

Retain the Stage 1 core direction of an honestly versioned `/2` renderer identity family and a runtime-derived execution binding, but do not approve implementation from the Stage 1 text as written.

The required synthesis is:

- explicitly bound the threat model;
- make the execution bundle the normative object, not an informal code graph;
- freeze a complete normalized descriptor before implementation;
- bind a conservative exact runtime ABI;
- structurally guarantee measure-and-execute through the same bundle for the accepted threat model;
- require Stage 3 to explicitly amend the R7 P9 proof basis;
- retain `/1` only as immutable historical evidence and reject silent upgrade;
- treat a stronger package/execution boundary as conditionally necessary, not automatically required.

This design closes the exact stale-renderer-identity blocker without introducing render-time filesystem or repository discovery, while making clear what it does and does not prove.

## 11. Unresolved Stage 3 decisions

Stage 3 must explicitly decide:

1. whether the bounded non-hostile-runtime threat model is sufficient for P9;
2. whether a runtime-derived execution binding is an accepted R7 proof form;
3. the exact normalized descriptor and runtime ABI freeze obligations before implementation;
4. whether any project requirement demands stronger hostile-runtime or same-process integrity, in which case an immutable package/execution boundary becomes mandatory;
5. the exact `/2` contract names and migration rule.

No Engineer-side inference can resolve those project-governance decisions.

## 12. Terminal boundary and bounded handoff

This Stage 2 bounded work unit is complete when this review/synthesis is durably committed unchanged.

Receiving role: **fresh Project Engineering Steward**, Stage 3 reconciliation only.

Exact next action: independently re-resolve live coordination state, establish whatever Steward authority and accepted activation evidence the live contracts require, then reconcile:

- governing plan `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd` / blob `8474d2da42f863f0a190fd80292085176d3f97f0`;
- exact P9 candidate `e961eb83d2c5dd1719b986c89a8915c102e395c3`;
- blocker review `ff482ffcac5b58133ee3a480bab4164ee599732f`;
- Stage 1 proposal `1cbbb61925c95219b8050c33efd1bf7b68a5fed4` / blob `a16edba937d8d30dd62dfe1082d0124673eb23e4`;
- this complete Stage 2 review/synthesis.

The Steward must explicitly disposition the R7 amendment, threat model, required revisions, package/execution-boundary contingency, `/2` versioning, implementation gates, and exact next authorized action.

Do not implement P9 or begin P10, admission, canonical mutation, authority mutation, activation mutation, or unrelated work from this Stage 2 activation.