# Consumer migration from embedded framework

Status: Phase 6.0I migration contract

## Version pin

Consumers MUST pin the framework by immutable commit SHA. The first accepted pin is:

`fb7290622d6a9d929a059f111cdd60cd50496fcf`

This commit contains the persisted Phase 6.0 parity PASS evidence for the frozen voxel-engine extraction baseline.

## Dependency direction

A consuming project owns its Project Knowledge Package and active canonical state. Generic validators, role contracts, schemas, and deterministic admission/proof tools are consumed from the pinned framework checkout.

The framework MUST NOT read project state through hard-coded repository paths. The project supplies paths/configuration through its package and workflow invocation.

## Voxel-engine migration order

1. Add `project-knowledge/project.yaml` and project-owned configuration.
2. Checkout the pinned framework into `.reasoning-distiller/` during validation/execution workflows.
3. Redirect active RGP validation, PEMS/2 validation, and deterministic admission/proof execution to the pinned checkout.
4. Run an integration proof against project-owned canonical/evidence paths.
5. Remove embedded generic implementation files only after every active workflow has moved to the pinned framework.
6. Preserve historical evaluation/proof evidence as project history; do not treat it as executable framework code.

## Completion condition

Phase 6.0I passes when the voxel-engine active integration uses the immutable framework pin, integration proof passes, project canonical data remains project-owned, and no active duplicate generic implementation remains in the consuming repository.
