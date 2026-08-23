# P1c Remediation Amendment: Raw Binding, JCS, Toolchain, and P1a Hex Normalization

Status: **Normative P1c remediation amendment**

Contract amended:

- `reasoning-distiller-context-pack-bytes-digests-toolchain/1`

Governing plan:

- commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- artifact: `docs/proposals/context-packaging/FINAL_PLAN.md`
- blob: `8474d2da42f863f0a190fd80292085176d3f97f0`

Reviewed basis:

- P1b candidate: `cffc2c27da64f052380a1a5a26a42bb7621b0335`
- blocked P1c candidate: `356e926f6214a7ee13d55f7d6510af13fbfd69ef`
- supplied disposition: `P1C_REVIEW_BLOCKED`

Remediation scope: **the four review findings below only**.

This amendment narrows and corrects the P1c contract without changing any P1b
schema bytes or wire-field semantics. Where this amendment is more specific
than `CONTEXT_PACKAGING_BYTES_DIGESTS_TOOLCHAIN_CONTRACT.md`, these clauses
control for the remediated P1c candidate. All unaffected clauses of that
contract remain unchanged.

It does not implement source resolution, PEMS closure, profile eligibility,
projection, COVE behavior, persistence, rendering, production integration,
canonical mutation, reconciliation, admission, authorization, or activation.
P1d and later gates remain out of scope.

## 1. Raw profile/request bytes and validated objects are one document

The exact source bytes and the validated parsed object used for a canonical
profile or request digest MUST be two representations of the same JSON
document. They are not independent inputs.

For a profile:

```text
profile_object =
  strict_parse_json(exact_profile_source_bytes)

validate_P1b_profile_schema(profile_object)

profile.raw_sha256 =
  raw_sha256(exact_profile_source_bytes)

identity.profile_sha256 =
  domain_sha256(
    "context-profile",
    JCS(profile_object)
  )
```

For a request:

```text
request_object =
  strict_parse_json(exact_request_source_bytes)

validate_P1b_request_schema(request_object)

request.raw_sha256 =
  raw_sha256(exact_request_source_bytes)

identity.request_sha256 =
  domain_sha256(
    "context-pack-request",
    JCS(request_object)
  )
```

The strict parse boundary rejects duplicate object member names, invalid UTF-8,
non-finite numbers, invalid Unicode, and any other input that cannot enter the
selected JCS/I-JSON contract.

A builder or conformance implementation MUST fail before claiming identity if:

- the exact profile bytes do not parse to the P1b-validated profile object;
- the exact request bytes do not parse to the P1b-validated request object;
- the request's `profile.raw_sha256` does not bind the exact profile bytes;
- the pack's profile raw identity does not bind the exact profile bytes; or
- the pack's request raw identity does not bind the exact request bytes.

Formatting changes may therefore alter a raw digest while preserving a
canonical digest only when the changed bytes still parse to the same validated
object.

## 2. `jcs/1` means RFC 8785, not sorted Python JSON

The P1c `jcs/1` contract is exactly RFC 8785 JSON Canonicalization Scheme.

A serializer is not conforming merely because it removes whitespace and sorts
Python dictionary keys. Conformance includes all RFC 8785 requirements that
affect bytes, including:

- I-JSON input constraints;
- ECMAScript-compatible string escaping;
- rejection of lone surrogates;
- IEEE-754 / ECMAScript-compatible number serialization, including negative
  zero and fixed-versus-exponent thresholds;
- recursive object-member ordering by UTF-16 code units;
- preservation of array order; and
- UTF-8 output with no BOM or trailing newline.

The P1c conformance reference is package-owned at:

- `tests/support/context_packaging_p1c_reference.py`

The conformance suite MUST verify RFC 8785 Appendix B IEEE-754 vectors plus
string and UTF-16 member-ordering cases that distinguish RFC 8785 from
`json.dumps(..., sort_keys=True)`.

This freezes serializer behavior for the P1c reference vector. It does not make
that test helper a production serializer or authorize production integration.

## 3. Toolchain identities must bind actual immutable behavior artifacts

A P1c fixture or successful pack MUST NOT use labels such as `ps`, `pv`, `jcs`,
or `pb` as if they were immutable implementation identities.

For every toolchain component used by the P1c frozen vector:

```text
component.immutable_identity =
  "git-blob:" || git_blob_sha1(exact_behavior_artifact_bytes)

component.raw_sha256 =
  raw_sha256(exact_behavior_artifact_bytes)
```

The fixture records the repository-relative artifact used for each role, and
the conformance test recomputes both identities from the actual bytes.

The P1c fixture binds:

- `pems_schema` to the exact PEMS/2 schema artifact;
- `pems_validator` to the exact PEMS/2 semantic-validator artifact;
- `closure_descriptor` to a P1c-only immutable identity fixture;
- `jcs_serializer` to the P1c conformance reference artifact; and
- `pack_builder` to the P1c conformance reference artifact.

The closure identity fixture explicitly contains no closure rules. Its purpose
is only to exercise immutable toolchain binding at P1c. It MUST NOT be treated
as P1d closure semantics or evidence that P1d has been implemented.

If a future COVE-bearing P1c/P4 vector is introduced, its `cove_adapter`
component must satisfy the same real-artifact rule. P1c does not manufacture a
synthetic COVE implementation identity merely to make a positive fixture pass.

## 4. P1a hex normalization precedes standing-evidence set canonicalization

P1a already freezes standing-evidence identity as a mathematical set after its
permitted digest normalization. P1c MUST preserve that semantic boundary.

Before deduplicating or sorting `standing_evidence`, the builder MUST normalize
each evidence identity's `raw_sha256` to:

```text
"sha256:" || lowercase(64 hexadecimal digits)
```

Only the P1a-permitted hexadecimal spelling normalization occurs. `contract`
and `immutable_snapshot_id` remain exact opaque strings.

Then the builder:

1. computes `JCS(normalized_evidence_identity)` for each item;
2. removes duplicate normalized identities; and
3. sorts the surviving identities by ascending JCS bytes.

This normalization applies wherever a canonical-state binding or canonical
snapshot reference is materialized into the canonical pack, so an uppercase
and lowercase spelling of the same P1a evidence digest cannot produce two set
members or two different canonical pack identities.

The request/profile canonical digest still covers the parsed request/profile
value supplied at that boundary. P1c does not rewrite the caller's raw source
bytes to make their raw identity match a preferred spelling.

## 5. Remediation conformance evidence

The remediated P1c suite MUST mechanically demonstrate all four findings:

1. exact raw profile/request bytes parse to and validate as the same P1b objects
   used for canonical digest computation, and mismatched raw/object pairs fail;
2. RFC 8785 vectors exercise IEEE-754 number serialization, UTF-16 key ordering,
   string escaping, non-finite rejection, and lone-surrogate rejection;
3. every P1c frozen-vector toolchain component recomputes its Git blob identity
   and SHA-256 from an actual repository artifact; and
4. uppercase/lowercase equivalent P1a standing-evidence SHA spellings collapse
   before set ordering and reproduce identical canonical pack bytes and
   identities.

No successful test under this amendment is evidence that P1d or any later gate
is complete or authorized.
