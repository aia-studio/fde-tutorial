"""元数据与难度曲线校验。这些规则是「渐进式」的机器保险，必须有用。"""

from __future__ import annotations

import unittest

from tutorial.schema import check_progression, validate_meta

BASE = {
    "id": "s0-01-demo",
    "order": 1,
    "stage": "s0",
    "official_group": "beginner",
    "title": "示例",
    "concepts": ["demo"],
    "doc_refs": [{"title": "Tutorial", "url": "https://docs.python.org/3/tutorial/"}],
}


def lesson(**overrides):
    data = dict(BASE)
    data.update(overrides)
    return data


class MetaTest(unittest.TestCase):
    def test_valid_passes(self):
        self.assertEqual(validate_meta(lesson(), source="x.md"), [])

    def test_missing_field(self):
        data = lesson()
        del data["title"]
        errors = validate_meta(data, source="x.md")
        self.assertTrue(any("title" in e for e in errors))

    def test_bad_id(self):
        errors = validate_meta(lesson(id="S0 Demo"), source="x.md")
        self.assertTrue(any("id" in e for e in errors))

    def test_bad_stage(self):
        errors = validate_meta(lesson(stage="s9"), source="x.md")
        self.assertTrue(any("stage" in e for e in errors))

    def test_http_url_rejected(self):
        errors = validate_meta(
            lesson(doc_refs=[{"title": "a", "url": "http://example.com"}]), source="x.md"
        )
        self.assertTrue(any("https" in e for e in errors))

    def test_empty_concepts_rejected(self):
        errors = validate_meta(lesson(concepts=[]), source="x.md")
        self.assertTrue(any("concepts" in e for e in errors))


class ProgressionTest(unittest.TestCase):
    def test_forward_prereq_rejected(self):
        lessons = [
            lesson(id="a", order=2, prereq=[3]),
            lesson(id="b", order=3, prereq=[2]),
        ]
        errors = check_progression(lessons)
        self.assertTrue(any("单调性" in e for e in errors))

    def test_cross_stage_backwards_ok(self):
        lessons = [
            lesson(id="a", order=34, stage="s2", prereq=[33]),
            lesson(id="b", order=33, stage="s2", prereq=[1]),
            lesson(id="c", order=1, stage="s0", prereq=[]),
        ]
        self.assertEqual(check_progression(lessons), [])

    def test_prereq_from_later_stage_rejected(self):
        lessons = [
            lesson(id="a", order=5, stage="s0", prereq=[1]),
            lesson(id="b", order=6, stage="s4", prereq=[1]),
            lesson(id="c", order=1, stage="s0", prereq=[]),
            lesson(id="d", order=7, stage="s0", prereq=[6]),
        ]
        errors = check_progression(lessons)
        self.assertTrue(any("更晚的阶段" in e for e in errors))

    def test_island_rejected(self):
        lessons = [
            lesson(id="a", order=1, prereq=[]),
            lesson(id="b", order=2, prereq=[]),
        ]
        errors = check_progression(lessons)
        self.assertTrue(any("standalone" in e for e in errors))

    def test_island_allowed_when_standalone(self):
        lessons = [
            lesson(id="a", order=1, prereq=[]),
            lesson(id="b", order=2, prereq=[], standalone=True),
        ]
        self.assertEqual(check_progression(lessons), [])

    def test_self_prereq_rejected(self):
        lessons = [lesson(id="a", order=1, prereq=[1])]
        errors = check_progression(lessons)
        self.assertTrue(any("自己" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
