"""Markdown 解析器的边界行为。解析器出错会静默毁掉一课，所以这里测细一点。"""

from __future__ import annotations

import unittest

from tutorial import markdown


class InlineTest(unittest.TestCase):
    def test_bold_and_italic(self):
        self.assertEqual(markdown._inline("**粗** 和 *斜*"), "<strong>粗</strong> 和 <em>斜</em>")

    def test_inline_code_not_formatted(self):
        out = markdown._inline("看 `**这里**` 不该加粗")
        self.assertEqual(out, "看 <code>**这里**</code> 不该加粗")

    def test_html_is_escaped(self):
        out = markdown._inline("<script>alert(1)</script>")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_link(self):
        out = markdown._inline("见 [文档](https://example.com)")
        self.assertIn('href="https://example.com"', out)
        self.assertIn(">文档</a>", out)


class BlockTest(unittest.TestCase):
    def test_heading_levels(self):
        blocks = markdown.parse("# 一级\n\n### 三级")
        self.assertEqual([b["level"] for b in blocks], [1, 3])

    def test_code_block_defaults_to_runnable(self):
        blocks = markdown.parse("```python\nprint(1)\n```")
        self.assertEqual(blocks[0]["type"], "code")
        self.assertTrue(blocks[0]["runnable"])
        self.assertEqual(blocks[0]["code"], "print(1)")

    def test_norun_flag(self):
        blocks = markdown.parse("```python norun\nprint(1)\n```")
        self.assertFalse(blocks[0]["runnable"])

    def test_expect_attaches_to_previous_code(self):
        blocks = markdown.parse("```python\nprint(1)\n```\n\n```expect\n1\n```")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["expect"], "1")

    def test_expect_without_code_fails(self):
        with self.assertRaises(ValueError):
            markdown.parse("```expect\n1\n```")

    def test_unclosed_fence_fails(self):
        with self.assertRaises(ValueError):
            markdown.parse("```python\nprint(1)")

    def test_quiz_toml(self):
        blocks = markdown.parse(
            '```quiz\nquestion = "1+1?"\noptions = ["1", "2"]\nanswer = 1\nexplain = "显然"\n```'
        )
        self.assertEqual(blocks[0]["type"], "quiz")
        self.assertEqual(blocks[0]["answer"], 1)
        self.assertEqual(blocks[0]["options"], ["1", "2"])

    def test_quiz_bad_answer_index(self):
        with self.assertRaises(ValueError):
            markdown.parse(
                '```quiz\nquestion = "q"\noptions = ["a", "b"]\nanswer = 5\n```'
            )

    def test_callout_marker(self):
        blocks = markdown.parse("> [!warn] 小心\n> 这里会炸")
        self.assertEqual(blocks[0]["type"], "callout")
        self.assertEqual(blocks[0]["kind"], "warn")
        self.assertEqual(blocks[0]["title"], "小心")
        self.assertIn("这里会炸", blocks[0]["html"])

    def test_plain_quote_is_quote(self):
        blocks = markdown.parse("> 只是引用")
        self.assertEqual(blocks[0]["kind"], "quote")

    def test_list_ordered_and_unordered(self):
        blocks = markdown.parse("- 一\n- 二\n\n1. 甲\n2. 乙")
        self.assertFalse(blocks[0]["ordered"])
        self.assertEqual(blocks[0]["items"], ["一", "二"])
        self.assertTrue(blocks[1]["ordered"])
        self.assertEqual(len(blocks[1]["items"]), 2)

    def test_table(self):
        blocks = markdown.parse("| a | b |\n|---|---|\n| 1 | 2 |")
        self.assertEqual(blocks[0]["type"], "table")
        self.assertEqual(blocks[0]["head"], ["a", "b"])
        self.assertEqual(blocks[0]["rows"], [["1", "2"]])

    def test_paragraph_terminated_by_list(self):
        blocks = markdown.parse("正文\n- 项目")
        self.assertEqual([b["type"] for b in blocks], ["p", "list"])


if __name__ == "__main__":
    unittest.main()
