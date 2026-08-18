# Reasoning Distiller

Standalone knowledge-system framework extracted from `loteque/gdscript-voxel-engine` under the Steward-approved Phase 6.0 extraction plan.

Phase 6.0 extraction parity is established for the frozen voxel-engine baseline. `rgp/1` semantics remain unchanged. The accepted consumer pin is `fb7290622d6a9d929a059f111cdd60cd50496fcf`; durable parity evidence is in `docs/extraction/phase6-parity-report.json` and the immutable marker branch is `phase6.0-parity-baseline`.

Authority boundary: the Distiller produces candidates; the project Steward owns semantic reconciliation and admission authority; deterministic execution applies only an already-authorized reconciliation plan.

## Installation

See [`INSTALLING.md`](INSTALLING.md) for human installation instructions and the minimal safe agent installation procedure.

## Production invocation

The stable installed Distiller operation is `rd-distill`. Its inputs, outputs, failure semantics, filesystem boundary, and authority boundary are defined by [`docs/operations/PRODUCTION_INVOCATION_CONTRACT.md`](docs/operations/PRODUCTION_INVOCATION_CONTRACT.md) (`reasoning-distiller-invocation/1`).

## Governance methods

Consequential architecture, protocol, governance, extraction, installation, and production-design proposals may use the durable three-stage review method defined in [`docs/governance/PROPOSAL_REVIEW_METHOD.md`](docs/governance/PROPOSAL_REVIEW_METHOD.md): RPG Engineer proposal → independent Engineer review/synthesis → Project Engineering Steward reconciliation/final plan.
