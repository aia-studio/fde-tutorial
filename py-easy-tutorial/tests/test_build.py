"""构建产物的契约：大纲锚点必须和前端 renderer 的编号规则一致。"""

from __future__ import annotations

import unittest

import build
from tutorial.schema import STAGES


class OutlineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lessons, cls.report = build.compile_all()

    def test_content_compiles_without_errors(self):
        self.assertTrue(self.report.ok, f"构建报错：{self.report.errors}")

    def test_outline_anchors_are_sequential(self):
        for lesson in self.lessons:
            outline = build.build_outline(lesson["blocks"])
            anchors = [item["anchor"] for item in outline]
            self.assertEqual(
                anchors, [f"sec-{i}" for i in range(1, len(outline) + 1)],
                f"{lesson['source']} 的锚点不连续：{anchors}",
            )

    def test_outline_matches_heading_blocks(self):
        for lesson in self.lessons:
            expected = sum(
                1
                for block in lesson["blocks"]
                if block["type"] == "heading" and block["level"] <= 3
            )
            self.assertEqual(len(build.build_outline(lesson["blocks"])), expected)

    def test_outline_text_has_no_markup(self):
        for lesson in self.lessons:
            for item in build.build_outline(lesson["blocks"]):
                self.assertNotIn("<", item["text"])
                self.assertTrue(item["text"].strip())

    def test_stage_is_known(self):
        for lesson in self.lessons:
            self.assertIn(lesson["stage"], STAGES)


if __name__ == "__main__":
    unittest.main()
