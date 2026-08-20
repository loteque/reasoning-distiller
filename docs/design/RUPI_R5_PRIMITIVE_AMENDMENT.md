# Rupi R5 Primitive Amendment

Status: Accepted-by-implementation candidate; requires R5 gate evidence.

This amendment records one primitive gap discovered while implementing Gate R5 of the accepted Rupi design.

## Gap

The existing Human↔Agent contextual-intent primitive intentionally accepts narrow generic affirmations such as `yes` and `proceed`. Protected authority ceremonies intentionally require exact confirmation tokens such as `ESTABLISH_ROOT_OPERATOR` and `STEWARD_AUTHORIZATION_CHANGE`.

The existing operator and Steward approval constructors create approval artifacts containing those confirmation tokens, but no accepted primitive previously bound the Human's exact utterance to the exact proposal reference before those constructors were called.

Implementing that check inside Rupi would have created Rupi-owned authority semantics and violated the primitive-first design rule.

## Added primitive

`ril_human_confirmation.bind_exact_confirmation`

Rupi action mapping:

`bind_protected_confirmation → ril_human_confirmation.bind_exact_confirmation`

Contract: `reasoning-distiller-protected-confirmation/1`.

The primitive:

- accepts only an enumerated protected ceremony;
- requires an exact `proposal:` reference;
- requires the Human utterance to exactly equal the required ceremony token;
- rejects generic affirmations and case-normalized approximations;
- records the exact ceremony and proposal reference in its result;
- has `authority_effect: none`;
- performs no mutation.

The successful binding result is passed as authentication evidence to the existing authority-specific approval primitive. The approval primitive and apply primitive remain the sole authority/mutation semantics.

## Non-duplication

This primitive does not duplicate `ril_human_agent.bind_contextual_intent`.

`bind_contextual_intent` binds ordinary bounded conversational intent and deliberately accepts a small generic affirmation vocabulary. `bind_exact_confirmation` binds only protected ceremony tokens and deliberately rejects that vocabulary.

## R1 inventory amendment

The frozen Rupi primitive map is extended by exactly one action:

`bind_protected_confirmation`.

No existing action mapping changes. No legacy Steward setup surface is admitted. This amendment is accepted only if the R5 pressure suite proves that generic affirmation cannot cross either protected authority boundary and all prior R1-R4 tests remain green.
