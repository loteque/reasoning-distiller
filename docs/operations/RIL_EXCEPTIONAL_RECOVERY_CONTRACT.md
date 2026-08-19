# RIL Exceptional Recovery Contract — R11

Status: normative implementation contract

## Purpose

R11 defines the only v1 path for continuing a RIL administrative event domain after its authoritative history is invalid and ordinary repair cannot proceed.

Exceptional recovery is not ordinary mutation and is not delegated administration. It is an explicit root-human recovery ceremony.

## Supported domains

- `operator_registry`
- `role_registry`
- `steward_authorization`

## Invariants

1. Damaged authoritative history MUST be preserved byte-for-byte.
2. Recovery MUST NOT rewrite, delete, renumber, or silently ignore damaged event files.
3. Recovery requires the currently established protected root operator. Delegated operators are insufficient.
4. Recovery requires explicit human-confirmation authentication evidence.
5. Recovery requires evidence describing the damage and the intended continuation state.
6. The proposed continuation state is explicit and digest-bound to the recovery approval.
7. A recovery record is append-only and stored separately from the damaged ordinary event stream.
8. Recovery records form their own deterministic sequence and hash chain.
9. Once a recovery record exists for a domain, recovered replay starts from its continuation state; the preserved damaged stream remains evidence, not silently repaired history.
10. A recovery record may only be created when ordinary replay of the target domain fails.
11. Repeating the exact approved recovery is idempotent. A different recovery for the same recovery generation fails closed in v1.
12. Recovery does not create Steward authority, change roles, or change operators except insofar as the explicitly approved continuation state represents the recovered state of that domain.

## Recovery evidence

Evidence is a canonical JSON object with:

- `method`: non-empty evidence method identifier;
- `damage`: non-empty description/object identifying observed corruption;
- optional additional evidence fields.

The evidence object is included in the proposal and therefore covered by its digest.

## Root approval

Approval uses the common approval contract. It MUST:

- be issued by the root operator recorded in the last valid operator state;
- use authentication method `human_confirmation`;
- contain confirmation `AUTHORIZE_EXCEPTIONAL_RECOVERY`.

For recovery of the operator registry itself, root identity is derived from the longest valid prefix of the damaged operator history. If no root can be established from that prefix, v1 refuses automated exceptional recovery and requires out-of-band repository governance.

## Recovery record

Recovery records live under:

`project-knowledge/recovery/<domain>/events/NNNNNNNN.json`

A record contains the proposal/approval digests, damaged-history fingerprint, previous recovery-record digest, and explicit continuation state/digest.

The damaged-history fingerprint hashes the ordered names and raw bytes of all entries in the ordinary event directory. This binds approval to the exact damaged material preserved at recovery time.

## Recovered replay

`replay_recovered_domain` first checks for a recovery record. Without one, ordinary replay semantics apply. With one, it verifies:

- recovery record canonicality and sequence;
- record hash chain;
- current damaged-history fingerprint equals the approved fingerprint;
- continuation-state digest;
- root approval binding.

It then returns the approved continuation state. V1 permits one exceptional-recovery generation per domain; subsequent ordinary mutations are future integration work and MUST NOT be inferred by R11.

## Failure behavior

Any malformed recovery artifact, changed damaged history, non-root approval, approval mismatch, valid ordinary history, unsafe path, or ambiguous root identity fails closed.
