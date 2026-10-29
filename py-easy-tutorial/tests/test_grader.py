"""判题器：通过、失败、部分通过、超时、语法错误。"""

from __future__ import annotations

import unittest

from tutorial.grader import grade

TESTS = [
    {"name": "结果是列表", "code": "assert isinstance(result, list)"},
    {"name": "长度正确", "code": "assert len(result) == 3"},
]


class GradeTest(unittest.TestCase):
    def test_all_pass(self):
        out = grade("result = [1, 2, 3]", TESTS)
        self.assertTrue(out["passed"])
        self.assertEqual([r["passed"] for r in out["results"]], [True, True])
        self.assertFalse(out["timed_out"])

    def test_partial_pass(self):
        out = grade("result = [1, 2]", TESTS)
        self.assertFalse(out["passed"])
        self.assertEqual([r["passed"] for r in out["results"]], [True, False])
        self.assertIn("AssertionError", out["results"][1]["error"])

    def test_name_error_is_reported(self):
        out = grade("pass", TESTS)
        self.assertFalse(out["passed"])
        self.assertIn("NameError", out["results"][0]["error"])

    def test_user_print_does_not_break_parsing(self):
        out = grade("print('调试输出')\nresult = [1, 2, 3]", TESTS)
        self.assertTrue(out["passed"])

    def test_syntax_error_in_user_code(self):
        out = grade("result = [1, 2,, 3]", TESTS)
        self.assertFalse(out["passed"])
        self.assertTrue(out["missing_harness"])
        self.assertIn("SyntaxError", out["stderr"])

    def test_infinite_loop_times_out(self):
        out = grade("while True:\n    pass\nresult = []", TESTS, timeout=1.0)
        self.assertFalse(out["passed"])
        self.assertTrue(out["timed_out"])

    def test_no_tests_configured(self):
        out = grade("x = 1", [])
        self.assertFalse(out["passed"])
        self.assertIn("没有配置测试", out["stderr"])


if __name__ == "__main__":
    unittest.main()
