# P6 — Consumer Migration

Status: **PASS**

The voxel-engine proving consumer now uses a project-local Reasoning Distiller installation under `.reasoning-distiller/` produced by the deterministic package installer. Active consumer runtime no longer checks out or resolves framework code from the generic repository.

## Installed identity

- version: `0.1.0`
- source commit: `8d81967b3f93e825172d961267818238fffc7d38`
- content identity: `sha256:ee0df2a91316ed0fa803d690b3e1b5bf6e07a320319255458e68ed1fb02b2dad`
- transport SHA-256: `773ab0c9a5946f69ec568aabd9a255569f9511227142baadde077f826aa6cd8a`
- consumer install commit: `9ec3fcee9c9b6db38a216f940fb2c7bb68253ae7`

## Final proof

Consumer repository: `loteque/gdscript-voxel-engine`, branch `project-chat-handoff`.

Final validation used PR 66 as a non-merged trigger against consumer base `ba3df89e302af86958b64b780b4cdbb44f78a897`.

- Consumer Integration run `32107264249`: PASS
- Local Framework Audit run `32107264236`: PASS

The proof verifies local package identity, Project Knowledge Package compatibility, local backend binding, network-blocked PEMS validation, network-blocked RGP validation, guarded admission, retirement of embedded generic implementation, exact manifest-managed tree contents, project-owned authority/rules/roles/policy/canonical state, and zero active cross-repository runtime framework references.

The consumer's durable machine-readable proof is `project-knowledge/p6-local-package-migration-proof.json` in the voxel-engine repository.

## Migration notes

The initial observable migration pressure exposed two operational issues and preserved them as test learning:

1. installer bootstrap files require their contract schemas in the expected sibling layout;
2. Python bytecode generated inside the managed tree is drift and must not be committed or left as managed content.

The final active Steward executor sets `PYTHONDONTWRITEBYTECODE=1` for framework execution paths, and the consumer audit requires the local managed tree to contain exactly the release manifest payload plus installation metadata.

The temporary `p6-package-candidate` branch/artifacts are migration scaffolding, not the final release topology. P8 establishes the accepted release baseline after P7 proves an update using a second package.

## Exit criterion

P6 is complete. The next gate is **P7 — second-package update proof**: retrieve and install a second deterministic package over this managed installation, prove the exact reviewable update diff, preserve project-owned knowledge, and re-run local/offline validation.
