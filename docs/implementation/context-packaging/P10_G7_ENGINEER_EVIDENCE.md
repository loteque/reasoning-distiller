# P10-G7 Engineer execution evidence

## Evidence identity

- Repository: `loteque/reasoning-distiller`
- Coordination control: `main@80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing Stage 3 plan: `b435dff827b745d711a5c5a297587a0c4359bed1`
- Governing plan blob: `eae54b9e2c0618faec61acf2f9e4acd942ec063d`
- Exact G6 semantic predecessor: `ed04d9f711d2c5298b3b86ca5bf5ea6937d4082a`
- G6 Engineer evidence: `60c609a44ea74869aea81bcd9cbe280ac7126abb`
- G6 successful candidate-bound run: `32908277963`
- Exact G7 semantic candidate: `ec410a501e7db051f59eb2fb373c30da150bd81a`
- Evidence trigger commit: `6788b7bc3e8cb3b6a092d5133b97ece10f2d7182`
- Evidence branch: `evidence/p10-g7-ec410a50-engineer-20260825`
- Evidence PR: `#88`
- Successful candidate-bound workflow run: `32914349031`
- Certified runtime: CPython `3.12.0`, cache tag `cpython-312`
- Unsupported-runtime pressure: CPython `3.13.0`, cache tag `cpython-313`
- Historical downgrade target: Reasoning Distiller `0.5.3` at `1d781baf8be8f21d25eb85ddc340f1d2bc93922b`
- Historical manifest release-asset SHA-256: `5c9448c6e6acc6f3925aae173870f4d6e8a237035c0e870637ef8d7499765044`
- Historical archive release-asset SHA-256: `5d1751f1910e13ba5b3e9787a6188a1b995e0ac5b88bbec9c2ac935e9d33ef67`
- Disposition: `P10_G7_MIGRATION_ROLLBACK_COMPATIBILITY_ENGINEER_EXECUTION_PASS`

## Candidate-bound closure

The successful workflow checked out immutable semantic candidate
`ec410a501e7db051f59eb2fb373c30da150bd81a` directly in every evidence job.
The evidence workflow itself was not part of the semantic candidate under test.

The candidate is exactly one commit after the G6 semantic predecessor. Its
complete semantic delta is exactly one regression file:

- `tests/test_context_packaging_production_integration_p10_g7.py`

No production runtime, installer, packaging implementation, protocol, schema,
or policy file changed in G7. In particular, G7 introduced no production
`rollback` or `downgrade` API.

Before executing the exact G7 gate, the workflow established:

- checked-out `HEAD` exactly matched the G7 semantic candidate;
- merge-base with G6 exactly matched
  `ed04d9f711d2c5298b3b86ca5bf5ea6937d4082a`;
- the complete G6-to-G7 semantic delta was exactly the G7 regression file;
- the supported execution runtime was exactly CPython `3.12.0` /
  `cpython-312`;
- the G7 regression file compiled under that exact runtime;
- the published v0.5.3 manifest and archive were retrieved from the historical
  release and matched the pinned release-asset SHA-256 identities above.

## Observed successful jobs

Run `32914349031` completed with workflow conclusion `success`. All three
candidate-bound jobs completed successfully:

1. `g7-compatibility-and-downgrade` (`98014776041`)
   - exact immutable-candidate, G6 ancestry, bounded-delta, and CPython 3.12.0
     identity checks;
   - retrieval and SHA-256 verification of the real v0.5.3 manifest and archive;
   - exact G7 compatibility, contract-selective rollback, and true package
     downgrade gate.

2. `g7-unsupported-runtime-pressure` (`98014775775`)
   - exact immutable candidate;
   - actual CPython `3.13.0` / `cpython-313` runtime;
   - invocation/2 runtime rejection as `RENDERER_RUNTIME_INCOMPATIBLE`.

3. `g7-predecessor-regressions` (`98014775965`)
   - exact immutable candidate under CPython `3.12.0` / `cpython-312`;
   - P10 G2 through G6 regressions;
   - package-builder and package-contract regressions;
   - installer P3/P4 regressions;
   - fixed legacy production-invocation `/1` regressions.

## Nine G7 obligations

### 1. Legacy `/1` remains operable — PASS

The current candidate package was installed into a clean temporary project and
its installed `runtime/rd_distill.py` successfully prepared an explicit
`reasoning-distiller-invocation/1` request, producing
`reasoning-distiller-activation-bundle/1`. The predecessor regression job also
passed the existing production-invocation `/1` suite.

### 2. `/2` requires explicit selection and never silently replaces `/1` — PASS

The installed compatibility entrypoint dispatches the P10 path only for exact
`reasoning-distiller-invocation/2`. The G7 gate executed `/1`, then explicit
`/2`, then `/1` again. The `/1` requests remained on the legacy activation
bundle contract and the explicit `/2` request produced
`reasoning-distiller-activation-bundle/2`.

### 3. `/2` succeeds under exact CPython `3.12.0` / `cpython-312` — PASS

The exact-runtime G7 job established CPython `3.12.0` / `cpython-312` before
execution. Under that runtime, the installed semantic candidate successfully
prepared the explicit invocation/2 request.

### 4. `/2` rejects unsupported runtimes — PASS

A separate candidate-bound job used actual CPython `3.13.0` /
`cpython-313`. The invocation/2 runtime guard rejected that runtime in preflight
with reason code `RENDERER_RUNTIME_INCOMPATIBLE`.

### 5. Historical `/1`-only runtime rejects `/2` — PASS

After the true v0.5.3 downgrade, the installed historical runtime successfully
handled `/1`. A full legacy-shaped request whose contract was explicitly changed
to `reasoning-distiller-invocation/2` was rejected by the historical runtime with
exit code `2`, preflight stage, and `UNSUPPORTED_CONTRACT`. No `/2` output was
created.

### 6. Selecting `/1` after `/2` is contract-level rollback — PASS

The G7 gate selected `/1`, then `/2`, then `/1` again without performing any
package install or downgrade between those invocations. The second `/1`
activation bundle was byte-for-byte identical to the first. The installed
package manifest and installed runtime bytes were also unchanged across the
selection sequence. This proves contract-selective rollback separately from
package downgrade.

### 7. A real package downgrade to v0.5.3 restores the historical managed installation — PASS

The current semantic candidate was built as an otherwise ordinary numeric
`0.6.0` release package solely so the existing installer could exercise its real
lower-version transition classification against the published `0.5.3` release.
The first transition plan, without downgrade authorization, returned
`DOWNGRADE_REQUIRES_AUTHORIZATION`. The same verified historical archive and
manifest were then installed with the existing explicit `allow_downgrade=True`
path. The installer returned `PASS`, incoming version `0.5.3`, and previous
version `0.6.0`.

No new downgrade mechanism was introduced for G7; this gate exercised the
existing package installer behavior with a genuine published historical release.

### 8. Downgraded tree matches v0.5.3 manifest and historical bytes — PASS

The installed `.installation/MANIFEST.json` after downgrade exactly equaled the
verified published v0.5.3 manifest. The actual managed file set exactly equaled
the historical manifest inventory. Every historical managed file was hashed from
the installed tree and matched its v0.5.3 manifest SHA-256. The installation
record identified version `0.5.3` and source commit
`1d781baf8be8f21d25eb85ddc340f1d2bc93922b`.

The gate compared the full current and historical manifests rather than relying
only on the managed-root count. It derived both current-only paths and shared
paths whose bytes changed. The changed-shared set was non-empty and included
`runtime/rd_distill.py`; after downgrade, every changed-shared path matched the
historical SHA-256 and differed from its current-candidate SHA-256.

### 9. No P9/P10-managed residue remains after downgrade — PASS

The post-downgrade managed file set contained no current-only manifest paths.
The current-only `context_packaging` managed root was absent. Changed shared-root
files had historical bytes. Installer transaction residue
`.rd-install-transaction.json` and `.rd-install-backup` was absent after the
successful transition.

Taken together, the file-set equality, all-file historical hashing, explicit
current-only absence, changed-shared historical restoration, and transaction
cleanup establish the G7 package-residue requirement for the managed
installation.

## Separation of mechanisms

The successful gate preserved the three mechanisms required by the governing
plan as distinct operations:

1. legacy `/1` compatibility: ordinary legacy dispatch in the current package;
2. `/2 -> /1` contract-selective rollback: request-contract selection with no
   package mutation;
3. real package downgrade: installer replacement of the managed installation
   using the verified published v0.5.3 release and explicit downgrade
   authorization.

No production rollback API, downgrade API, reconciliation path, admission path,
or hidden coupling between those mechanisms was introduced.

## Production evidence boundary

G7 added only regression/evidence plumbing. It did not modify production
invocation evidence selection. The predecessor production-invocation regressions
passed on the exact G7 candidate, and no Project memory, prior-chat state,
unrelated repository files, prior candidates, canonical-state interpretation,
or hidden reasoning was added to a production `rd-distill` invocation.

## Authority and scope boundary

This artifact is Engineer execution evidence for P10-G7 only. It records an
observed candidate-bound execution result. It does not establish independent
review, Steward reconciliation, tranche closure, admission, canonical standing,
Project authority, role activation, authorization, or any mutation of canonical
or authority state.

No P10-G8+ implementation, independent review, Steward reconciliation,
admission, canonical mutation, role registration, RIL activation, authority
mutation, or activation-state mutation was performed as part of this evidence.
