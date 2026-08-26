import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path

from context_packaging.cove_adapter import (
    COVE_SEMANTIC,
    FROZEN_COVE_SOURCE,
    FROZEN_COVE_SOURCE_GIT_BLOB,
    PEMS_SEMANTIC,
    SERIALIZER,
    SUPPORTED_TUPLES,
    CoveAdapterError,
    CoveSemanticTuple,
    _frozen_cove_module,
    _git_blob_sha,
    decode_cove_pems,
    encode_cove_pems,
)
from context_packaging.pems_projection import _jcs

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "backends/pems-cove/validate_pems2_contract.py"


def valid_doc():
    spec = importlib.util.spec_from_file_location("p4_test_pems_validator", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    valid, _invalid = module.structural_smoke_documents()
    return deepcopy(valid)


class P4CoveAdapterTests(unittest.TestCase):
    def test_scope_tuple_and_frozen_behavior_binding(self):
        self.assertEqual(
            SUPPORTED_TUPLES,
            (CoveSemanticTuple("cove/1", "pems/2", "jcs/1"),),
        )
        self.assertEqual((COVE_SEMANTIC, PEMS_SEMANTIC, SERIALIZER), ("cove/1", "pems/2", "jcs/1"))
        self.assertEqual(FROZEN_COVE_SOURCE, ROOT / "admission/apply_admission_transaction.py")
        self.assertEqual(_git_blob_sha(FROZEN_COVE_SOURCE.read_bytes()), FROZEN_COVE_SOURCE_GIT_BLOB)
        frozen = _frozen_cove_module()
        self.assertEqual((frozen.COVE, frozen.PROFILE, frozen.SERIALIZER), ("cove/1", "pems/2", "jcs/1"))

    def test_exact_pems_round_trip_and_repeated_bytes(self):
        document = valid_doc()
        before = deepcopy(document)
        first = encode_cove_pems(document)
        second = encode_cove_pems(document)
        self.assertEqual(first, second)
        self.assertEqual(document, before)
        self.assertEqual(decode_cove_pems(first), document)
        self.assertEqual(encode_cove_pems(decode_cove_pems(first)), first)

    def test_adapter_is_exactly_structural_parity_with_frozen_encoder(self):
        document = valid_doc()
        frozen = _frozen_cove_module()
        envelope = frozen.encode_cove(deepcopy(document))
        self.assertEqual(encode_cove_pems(document), _jcs(envelope))
        self.assertEqual(frozen._decode(envelope["x"], envelope["d"], envelope["h"]), document)

    def test_object_member_insertion_order_does_not_change_bytes(self):
        document = valid_doc()
        reordered = dict(reversed(list(document.items())))
        reordered["records"] = [dict(reversed(list(item.items()))) for item in reordered["records"]]
        reordered["relations"] = [dict(reversed(list(item.items()))) for item in reordered["relations"]]
        self.assertEqual(reordered, document)
        self.assertEqual(encode_cove_pems(reordered), encode_cove_pems(document))

    def test_only_supported_semantic_tuple_is_accepted(self):
        raw = encode_cove_pems(valid_doc())
        envelope = json.loads(raw.decode("utf-8"))
        for key, bad in (("c", "cove/2"), ("p", "pems/1"), ("s", "json/1")):
            mutated = deepcopy(envelope)
            mutated[key] = bad
            with self.assertRaisesRegex(CoveAdapterError, "unsupported COVE semantic tuple"):
                decode_cove_pems(_jcs(mutated))

    def test_noncanonical_or_malleable_cove_fails_closed(self):
        raw = encode_cove_pems(valid_doc())
        with self.assertRaisesRegex(CoveAdapterError, "canonical jcs/1"):
            decode_cove_pems(b" " + raw)
        envelope = json.loads(raw.decode("utf-8"))
        envelope["d"].append("unused")
        with self.assertRaisesRegex(CoveAdapterError, "deterministic package encoding"):
            decode_cove_pems(_jcs(envelope))
        envelope = json.loads(raw.decode("utf-8"))
        envelope["extra"] = 1
        with self.assertRaisesRegex(CoveAdapterError, "envelope shape"):
            decode_cove_pems(_jcs(envelope))

    def test_non_pems_input_and_non_bytes_decode_are_rejected(self):
        with self.assertRaisesRegex(CoveAdapterError, "PEMS/2"):
            encode_cove_pems({"semantic": "pems/1", "project_id": "p", "records": [], "relations": []})
        with self.assertRaisesRegex(CoveAdapterError, "must be bytes"):
            decode_cove_pems("{}")


if __name__ == "__main__":
    unittest.main()
