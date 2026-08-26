"""Pure P1e governed-consumer/profile eligibility reference operation."""

ELIGIBLE = "eligible"
ELIGIBILITY_BINDING_MISSING = "ELIGIBILITY_BINDING_MISSING"
PROFILE_INELIGIBLE = "PROFILE_INELIGIBLE"


def _normalized_sha256(value):
    prefix, sep, hex_value = value.partition(":")
    if prefix != "sha256" or sep != ":" or len(hex_value) != 64:
        return None
    try:
        int(hex_value, 16)
    except ValueError:
        return None
    return "sha256:" + hex_value.lower()


def _profile_equal(left, right):
    left_digest = _normalized_sha256(left["raw_sha256"])
    right_digest = _normalized_sha256(right["raw_sha256"])
    return (
        left["profile_id"] == right["profile_id"]
        and left["profile_version"] == right["profile_version"]
        and left_digest is not None
        and left_digest == right_digest
    )


def _consumer_equal(left, right):
    return (
        left["consumer_contract"] == right["consumer_contract"]
        and left["consumer_id"] == right["consumer_id"]
        and left["immutable_policy_snapshot_id"]
        == right["immutable_policy_snapshot_id"]
    )


def _policy_evidence_equal(left, right):
    left_digest = _normalized_sha256(left["raw_sha256"])
    right_digest = _normalized_sha256(right["raw_sha256"])
    return (
        left["contract"] == right["contract"]
        and left["immutable_snapshot_id"] == right["immutable_snapshot_id"]
        and left_digest is not None
        and left_digest == right_digest
    )


def evaluate_profile_eligibility(
    requested_profile,
    eligibility_binding,
    expected_consumer,
    required_policy_evidence=None,
):
    """Accept an already supplied, schema-valid P1b eligibility binding.

    This operation intentionally performs no discovery, source resolution,
    policy lookup, file/network I/O, model call, or mutation.
    """
    if eligibility_binding is None:
        return ELIGIBILITY_BINDING_MISSING

    if not _consumer_equal(eligibility_binding["consumer"], expected_consumer):
        return PROFILE_INELIGIBLE

    if not _profile_equal(eligibility_binding["profile"], requested_profile):
        return PROFILE_INELIGIBLE

    if required_policy_evidence is not None and not _policy_evidence_equal(
        eligibility_binding["policy_evidence"], required_policy_evidence
    ):
        return PROFILE_INELIGIBLE

    if eligibility_binding["decision"] != ELIGIBLE:
        return PROFILE_INELIGIBLE

    return ELIGIBLE
