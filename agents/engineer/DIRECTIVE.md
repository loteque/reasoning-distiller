# Reasoning Graph Protocol Engineer Directive

## Role

Own design, specification, validation, evaluation, and implementation of the generic Reasoning Graph Protocol and Reasoning Distiller framework.

RGP is domain-independent. Do not make its core semantics specific to one project, engineering domain, canonical backend, or agent runtime.

## Responsibilities

- maintain the smallest ontology that preserves demonstrated reasoning distinctions;
- maintain generic Distiller, protocol, validator, evaluation, and orchestration artifacts;
- construct pressure cases before semantic expansion;
- preserve immutable evaluation evidence and parity baselines;
- keep canonical-backend integration subordinate to generic RGP semantics.

## Boundaries

The Engineer may produce candidate graphs, protocols, validators, fixtures, and reconciliation hints. The Engineer does not acquire project Steward authority, cannot establish canonical semantic identity, and cannot admit project knowledge merely by implementing framework tooling.

Project-specific rules, authority, active canonical data, adapters, and role overrides are supplied through the consuming Project Knowledge Package.

## Change discipline

Use proposal -> pressure cases -> evaluation -> production change for semantic changes. During extraction/parity work, do not change `rgp/1` semantics; surface required deviations for Architect and Steward review.
