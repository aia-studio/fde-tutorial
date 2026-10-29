"""进度存储：默认值、校验、原子写、备份、损坏恢复。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tutorial.progress import ProgressStore, validate


class ValidateTest(unittest.TestCase):
    def test_defaults_filled(self):
        data = validate({"xp": 30})
        self.assertEqual(data["schema"], 1)
        self.assertEqual(data["xp"], 30)
        self.assertEqual(data["streak"]["current"], 0)
        self.assertEqual(data["lessons"], {})

    def test_unknown_top_level_keys_dropped(self):
        data = validate({"xp": 1, "junk": "x" * 1000, "lessons": {}})
        self.assertNotIn("junk", data)

    def test_negative_xp_rejected(self):
        with self.assertRaises(ValueError):
            validate({"xp": -5})

    def test_xp_must_be_int(self):
        with self.assertRaises(ValueError):
            validate({"xp": "10"})

    def test_bad_schema_rejected(self):
        with self.assertRaises(ValueError):
            validate({"schema": 99})

    def test_non_dict_rejected(self):
        with self.assertRaises(ValueError):
            validate([1, 2, 3])

    def test_malformed_entries_ignored(self):
        data = validate(
            {
                "lessons": {"a": {"status": "done"}, "b": "不是字典"},
                "weak": {"x": 2, "y": "many"},
            }
        )
        self.assertIn("a", data["lessons"])
        self.assertNotIn("b", data["lessons"])
        self.assertEqual(data["weak"], {"x": 2})

    def test_updated_at_is_set(self):
        self.assertTrue(validate({})["updated_at"])


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "progress.json"
        self.store = ProgressStore(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_file_returns_default(self):
        data = self.store.load()
        self.assertEqual(data["xp"], 0)
        self.assertFalse(self.path.exists())

    def test_roundtrip(self):
        self.store.save({"xp": 40, "lessons": {"s0-01": {"status": "done"}}})
        loaded = self.store.load()
        self.assertEqual(loaded["xp"], 40)
        self.assertEqual(loaded["lessons"]["s0-01"]["status"], "done")

    def test_backup_written_on_second_save(self):
        self.store.save({"xp": 10})
        self.store.save({"xp": 20})
        backup = self.path.with_suffix(".json.bak")
        self.assertTrue(backup.exists())
        self.assertEqual(json.loads(backup.read_text(encoding="utf-8"))["xp"], 10)

    def test_corrupted_file_falls_back_without_overwriting(self):
        self.path.write_text("{ 这不是 JSON", encoding="utf-8")
        data = self.store.load()
        self.assertEqual(data["xp"], 0)
        # 不能把用户的坏文件悄悄覆盖掉
        self.assertIn("这不是 JSON", self.path.read_text(encoding="utf-8"))

    def test_rejects_oversized_payload(self):
        huge = {"lessons": {f"k{i}": {"status": "done", "pad": "x" * 900} for i in range(1500)}}
        with self.assertRaises(ValueError):
            self.store.save(huge)


if __name__ == "__main__":
    unittest.main()
