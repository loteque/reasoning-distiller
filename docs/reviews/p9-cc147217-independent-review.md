# P9 Independent Review: Same-Bundle Resolver Remediation

Disposition: **P9_INDEPENDENT_REVIEW_PASS**

## Bound review basis

- Repository: `loteque/reasoning-distiller`
- Coordination control ref: `main`
- Coordination revision independently resolved before review: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Coordination revision re-resolved immediately before disposition write: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing implementation plan: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- Governing P9 renderer-identity amendment: `373667be85521e6f0f83bf19fed3378357e51118`
- Governing amendment blob: `90142ffe6b6652faceb3e8347f33fa71c8dc3ed9`
- Prior rejected candidate: `872ae5f0dfa0a123fe060a5ea17aa85c2de13097`
- Supplied prior blocker: `P9_POST_RESOLUTION_GLOBAL_RESOLVER_LOOKUP`
- Exact remediated candidate: `cc14721725949a560b52f0a5d80808e95c2d6ad0`
- Exact candidate parent: `872ae5f0dfa0a123fe060a5ea17aa85c2de13097`
- Exact candidate tree: `c9958d35801c1634907cb7dcb283afb65315cc38`
- Candidate branch re-resolved before disposition: `implement/p9-post-resolution-resolver-872ae5f0@cc14721725949a560b52f0a5d80808e95c2d6ad0`
- Renderer blob: `a88168c59de3235be92881bf1655416f0f1099e8`
- RI-15/bootstrap regression blob: `0076ef39b9161e9142f7389102503b52b90c649b`
- Engineer evidence: `a2d1ee4af973bc44d80d60f19c54d391b51f9aa2`
- Engineer evidence run: `32859201002`, attempt `1`
- Engineer execution disposition: `P9R6_POST_RESOLUTION_RESOLVER_EXECUTION_PASS`
- Active role: fresh independent Reasoning Graph Protocol Engineer, P9 review only.

The current Engineer directive, Project chat-transition amendment, and proposal-review method were read from the exact live coordination revision. This review establishes no Steward authority, accepted Steward activation, reconciliation, admission, canonical standing, canonical mutation, authority mutation, P10, or other successor scope.

## Evidence classification note

The handoff labels `d8d13c7d48a3baa91fe7bae99918965d4abcdbc4` as prior review evidence. Its own repository bytes identify it as a P9R5 candidate-bound provenance reconstruction and explicitly state that it does not perform the next independent review. This review therefore does not treat that commit as independent-review authority.

The supplied prior blocker is nevertheless independently reconstructible from the rejected parent side of the exact remediation diff: the `/2` entrypoints resolved a bundle with `_resolve_bundle()` and then performed a second module-global `_resolve_bundle` lookup when checking `bundle[3]`. That violated the frozen same-bundle rule forbidding module-global behavior lookup after resolution.

## Independently reconstructed P9 gate

The governing plan requires P9 deterministic rendering to remain a pure function of canonical pack plus renderer profile, preserve structural planes, discover nothing, be byte deterministic, and fail rather than truncate, summarize, rank, or silently omit.

The governing P9 amendment strengthens renderer replay identity with a runtime-derived execution binding over a mechanically closed bundle. For the same-bundle property relevant here, the required invariant is:

1. resolve exactly one bundle instance for the call;
2. capture the resolver/member/primitive references used by that instance;
3. validate closure and exact runtime ABI on that instance;
4. derive the actual execution binding from that same instance;
5. compare it against the profile-supplied expected binding before success;
6. execute render/decode only through references captured by that same instance;
7. emit the same derived binding in the activation;
8. perform no module-global behavior lookup after bundle resolution; and
9. use no stale binding cache.

The frozen P9R0 pressure set remains mandatory, including RI-15 verify-one/execute-another, RI-17 binding-verifier mutation, RI-18 post-resolution global substitution, RI-19 mutable closure/default, RI-20 exact runtime micro mismatch, RI-21 runtime primitive substitution, RI-22 unsupported interpreter family, RI-23 descriptor-noise stability, and RI-24 no discovery during identity validation.

## Candidate inspection and blocker closure

Candidate `cc14721725949a560b52f0a5d80808e95c2d6ad0` is a direct child of rejected candidate `872ae5f0dfa0a123fe060a5ea17aa85c2de13097`. Its delta is exactly:

- `context_packaging/renderer.py`
- `tests/test_context_packaging_renderer_ri15_remediation.py`

Both `/2` public entrypoints now use the same bootstrap shape:

```python
resolver = _resolve_bundle
bundle = resolver()
if bundle[3] is not resolver:
    ... fail UNSUPPORTED_RENDERER through bundle-captured result/failure members ...
return bundle[103 or 104](bundle, ...)
```

This closes `P9_POST_RESOLUTION_GLOBAL_RESOLVER_LOOKUP`:

- `_resolve_bundle` is loaded from module globals exactly once before resolution and captured into the local `resolver`;
- bundle resolution calls that captured local;
- resolver identity is checked against the captured local rather than performing another module-global lookup;
- the fail-closed path uses `bundle[25]` / `bundle[26]` and `bundle[24]`;
- the success path dispatches through `bundle[103]` / `bundle[104]`;
- neither path performs a second resolver lookup after bundle creation.

The candidate-local regression disassembles both `/2` entrypoints and requires exactly one `LOAD_GLOBAL _resolve_bundle`, followed by storage into local `resolver`. Source inspection independently confirms the intended ordering and dispatch shape rather than relying on the regression assertion alone.

## Complete same-bundle contract inspection

The remediation does not weaken the broader closed-bundle machinery inherited from P9R2/P9R3.

`_resolve_bundle()` returns a fresh tuple containing the registry and all behavior-bearing members/primitives used for execution. The registry includes, among others:

- `member:resolve_bundle` at bundle slot `3`;
- `member:render_v2_execute` at slot `103`;
- `member:decode_v2_execute` at slot `104`;
- `member:profile_v2` at slot `105`;
- `member:derive_execution_binding_execute` at slot `108`;
- `member:compare_execution_binding_execute` at slot `109`;
- public `member:render` and `member:decode` entrypoints.

The bootstrap-dependency map explicitly binds `_resolve_bundle` as the resolver dependency of public render/decode and binds the resolver's own dependency graph. Thus the changed public entrypoint bytecode remains part of the execution descriptor rather than becoming an unmeasured bootstrap shim.

The P9R2 structural gate walks registered executable members, rejects closures and mutable persistent defaults, and requires every non-bootstrap execution member to contain no `LOAD_GLOBAL`, `STORE_GLOBAL`, or `DELETE_GLOBAL` operations. Bootstrap globals must resolve to objects already present in the captured bundle. This is a strong mechanical check that the post-resolution execution graph is bundle-driven rather than merely identity-described.

The P9R2 substitution regression also captures a bundle, replaces a broad set of renderer helpers, primitives, constants, registry objects, and result types in module globals with failing sentinels, and verifies captured rendering/decoding still succeeds with identical bytes. The later RI-18 harness extends the same property over `/2` identity and binding members.

Inside `_render_v2_bound`, the profile is validated through `b[105]`, the actual binding is independently derived through `b[108]`, exact comparison is performed through `b[109]`, and subsequent rendering proceeds through the same `b`. The decode path is governed by the corresponding captured-bundle pattern. I found no execution path in the inspected remediation that can validate one resolved bundle and then silently dispatch through a later module-global resolver or behavior helper.

## Engineer evidence inspection

Engineer evidence commit `a2d1ee4af973bc44d80d60f19c54d391b51f9aa2` is directly above exact candidate `cc14721725949a560b52f0a5d80808e95c2d6ad0` and adds only the candidate-bound evidence record.

The underlying workflow run `32859201002`, attempt `1`, was inspected at job/log level rather than accepted from the summary alone. Observed execution establishes:

- transport commit `fd02988a94813a305f50f196b27d31807fb47714`;
- exact candidate/parent/tree/blob assertions matching this review basis;
- exact CPython `3.12.0`, implementation `cpython`, cache tag `cpython-312`;
- frozen P9 local gate including the new bootstrap regression: **27 passed**;
- external RI main harness: **22 passed, 2 deselected**;
- corrected RI-02 and RI-17 harness: **2 passed**;
- therefore RI-01 through RI-24: **PASS**;
- original deterministic P9 pytest gate: **22 passed**;
- original deterministic P9 unittest gate: **11 tests, all PASS**;
- unaffected P0-P8 regressions: **165 passed, 2 deselected, 162 subtests passed**;
- inherited PS-19 classifier mismatch reproduced separately as `PLANE_CLASSIFICATION_CONFLICT` versus expected `UNKNOWN_SEMANTICS_FIELD`.

The workflow then enforced all P9R6 statuses as green before emitting `P9R6_POST_RESOLUTION_RESOLVER_EXECUTION_PASS` and writing the exact candidate-bound evidence commit.

This review did not rerun that workflow. A rerun would reconstruct and push candidate/evidence branches and therefore is not treated as a read-only independent execution check. No independent rerun is claimed here. The disposition rests on independent contract reconstruction, source/structure challenge, exact candidate identity inspection, and direct inspection of the already-bound exact-runtime execution logs.

## Review findings

### Blocking findings

None.

### Closure finding

`P9_POST_RESOLUTION_GLOBAL_RESOLVER_LOOKUP`: **CLOSED** for exact candidate `cc14721725949a560b52f0a5d80808e95c2d6ad0`.

The rejected parent performed a post-resolution module-global resolver lookup. The remediated candidate captures the resolver before resolution and uses only that local plus the returned bundle afterward. The registered execution graph remains mechanically bundle-driven and the exact-runtime pressure matrix, including RI-15 and RI-18, passes.

### Non-blocking inherited red

The P1b PS-19 classifier mismatch remains separately reproduced and unchanged. This review does not reinterpret it as a P9 pass or claim it is fixed.

## Independent review disposition

**P9_INDEPENDENT_REVIEW_PASS**

Exact candidate `cc14721725949a560b52f0a5d80808e95c2d6ad0` satisfies the independently reconstructed P9 deterministic-renderer and same-bundle execution gate on the inspected source, structural tests, candidate-bound provenance, and exact-runtime Engineer evidence.

No P9-local blocking finding was identified. The prior same-bundle bootstrap blocker is closed without broadening the candidate beyond the two-file remediation, and the complete same-bundle contract remains preserved.

## Terminal boundary and bounded handoff

This independent-review activation ends with the P9 disposition. It does not begin P9R7 Steward reconciliation, admission, activation, canonical mutation, authority mutation, P10, or unrelated work.

If continuation is selected, the next consequential stage belongs to a **fresh Project Engineering Steward activation scoped only to P9 reconciliation**. That activation must independently establish whatever Steward authority and accepted activation evidence the live repository contracts require, then reconcile exact candidate `cc14721725949a560b52f0a5d80808e95c2d6ad0` against this independent-review evidence and Engineer evidence `a2d1ee4af973bc44d80d60f19c54d391b51f9aa2`.

This handoff does not itself create Steward authority or accepted activation evidence.