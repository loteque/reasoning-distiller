# Canonical PEMS/COVE Recovery Mode B — B0 Protocol Freeze

Status: **B0 implementation remediated after independent review; successor not selected**

Operational role: fresh implementation Engineer

Coordination control ref and revision at activation: `main` at `4848b219dcdc432e1656aa3a1d40d26f8717f968`.

Accepted Mode A substrate: reviewed candidate `51ae28dca034cdd431b161a46d0f5cbc1a7e0116`, tree `c523ce99ea2932d070482d1fb14c556773f6405a`, merged by `4848b219dcdc432e1656aa3a1d40d26f8717f968`.

Governing Mode B Stage 3 plan: original commit `45919508cab9d18a6eab82869514be767edf5c68`, carried unchanged onto this implementation branch.

## Completed B0 scope

- froze the normative Mode B protocol-generation V2 domain contract;
- froze eleven exact artifact schemas plus one shared structural-definition schema;
- froze `/1` damage-analysis, semantic-disposition, disposition-result, and repair-proof envelopes;
- froze the exact `/2` plan, approval, journal, barrier, completion, and recovery-result family;
- froze R14 storage-verification result `/3` with explicit Mode B provenance bindings;
- froze compatibility, stable outcomes, disjoint storage namespaces, exact R8 `semantic_reconciliation` applicability boundary, and the Mode A non-regression boundary;
- separated the `MODE_B_RECOVERY` provenance class from the `VERIFIED_RECOVERED` verification outcome;
- required complete nonempty per-relation value tables for accept, reject, and defer dispositions;
- constrained disposition, recovery, and storage-verification results to exact coherent status/outcome/provenance/reference combinations;
- added structural conformance tests for schema validity, positive examples, unknown fields, version/mode confusion, candidate-free disposition, exact activation scope, and current PEMS relation vocabularies.

## Explicit absence

B0 adds no runtime reader or writer. It implements neither B2 nor B3, contains no incident semantic values, creates no disposition/candidate/plan/approval/recovery artifact, mutates no Canon/recovery/admission/authority state, and does not continue P3. The schemas contain no defaults.

The known lifecycle values for the 668 incident relations and `dependency_kind` values for the seven `depends_on` relations remain unknown.

## Validation

The remediated B0 schema suite passes 11 tests with 56 subtests. The combined B0, unchanged Mode A recovery, and R14 non-regression selection passes 96 tests with 96 subtests; the Mode A portion remains the same 85-test selection and includes the corrected G8 incident result `UNSUPPORTED_CANONICAL_DAMAGE`, zero candidates, and no plan.

Repository-wide discovery ran 700 tests but is not green in this checkout: nine imports require unavailable `pytest`; two isolated subprocess tests cannot see the user-installed `jsonschema`; and two pre-existing context-packaging assertions fail (`PS-19` classification and a frozen P5 digest). These failures do not touch B0 or Mode A recovery files. They are reported rather than repaired because B0 does not authorize unrelated remediation.

## Terminal boundary

B0 is terminal here. Completion does not select B2 or B3. A fresh independent review may inspect the exact B0 candidate; any successor implementation work requires separate selection.
