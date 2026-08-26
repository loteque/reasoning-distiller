# Reasoning Distiller

## Purpose

AI reasoning is powerful, but without clear boundaries it can become a black box: unclear evidence, fuzzy provenance, hidden context, and conclusions that quietly gain more authority than they deserve.

Reasoning Distiller exists to make that process inspectable. It gives models a sealed evidence set, records exactly what they produce, preserves where ideas came from, and keeps reasoning separate from acceptance and authority.

The long-term ambition is a system where projects can build durable knowledge through repeated cycles of **evidence → reasoning → review → admission**, while still being able to answer a simple question years later:

**What did we know, why did we believe it, and how did it become part of the project?**

A kind of flight recorder for collective reasoning, with fewer mystery buttons. ✦

Standalone knowledge-system framework extracted from `loteque/gdscript-voxel-engine` under the Steward-approved Phase 6.0 extraction plan.

Phase 6.0 extraction parity is established for the frozen voxel-engine baseline. `rgp/1` semantics remain unchanged. The accepted consumer pin is `fb7290622d6a9d929a059f111cdd60cd50496fcf`; durable parity evidence is in `docs/extraction/phase6-parity-report.json` and the immutable marker branch is `phase6.0-parity-baseline`.

Authority boundary: the Distiller produces candidates; the project Steward owns semantic reconciliation and admission authority; deterministic execution applies only an already-authorized reconciliation plan.

## Installation

See [`INSTALLING.md`](INSTALLING.md) for human installation instructions and the minimal safe agent installation procedure.

## Project bootstrap

The deterministic `rd-bootstrap` primitive initializes the minimum project-owned structure required for first use. Its contract and the future `rd_init` orchestration boundary are defined by [`docs/operations/PROJECT_BOOTSTRAP_CONTRACT.md`](docs/operations/PROJECT_BOOTSTRAP_CONTRACT.md).

## Production invocation

The stable installed Distiller operation is `rd-distill`. Its inputs, outputs, failure semantics, filesystem boundary, and authority boundary are defined by [`docs/operations/PRODUCTION_INVOCATION_CONTRACT.md`](docs/operations/PRODUCTION_INVOCATION_CONTRACT.md) (`reasoning-distiller-invocation/1`).

## Governance methods

Consequential architecture, protocol, governance, extraction, installation, and production-design proposals may use the durable three-stage review method defined in [`docs/governance/PROPOSAL_REVIEW_METHOD.md`](docs/governance/PROPOSAL_REVIEW_METHOD.md): RPG Engineer proposal → independent Engineer review/synthesis → Project Engineering Steward reconciliation/final plan.