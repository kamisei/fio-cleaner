import sys
import unittest

# Ensure "src/" is importable when running from repo root
sys.path.insert(0, "src")

from domain.fio.normalize_value import normalize_fio_value  # noqa: E402
from domain.fio.constants import (  # noqa: E402
    TECH_STATUS_OK,
    TECH_STATUS_FIXED,
    RULE_STRIP_INVISIBLE,
    RULE_NORMALIZE_PUNCTUATION,
    RULE_NORMALIZE_SPACES,
    RULE_NORMALIZE_DASH,
    RULE_TITLE_CASE,
)


class TestNormalizeFioValue(unittest.TestCase):
    def test_none_is_ok_empty(self):
        r = normalize_fio_value(None)
        self.assertEqual(r.after, "")
        self.assertEqual(r.status, TECH_STATUS_OK)
        self.assertEqual(r.applied_rules, [])

    def test_spaces_and_case(self):
        r = normalize_fio_value("  ИВАНОВ   иВАН  ")
        self.assertEqual(r.after, "Иванов Иван")
        self.assertEqual(r.status, TECH_STATUS_FIXED)
        self.assertEqual(r.applied_rules, [RULE_NORMALIZE_SPACES, RULE_TITLE_CASE])

    def test_tabs_newlines_to_spaces(self):
        r = normalize_fio_value("ИВАНОВ\tИВАН\nИВАНОВИЧ")
        self.assertEqual(r.after, "Иванов Иван Иванович")
        self.assertEqual(r.status, TECH_STATUS_FIXED)
        self.assertIn(RULE_NORMALIZE_SPACES, r.applied_rules)
        self.assertIn(RULE_TITLE_CASE, r.applied_rules)

    def test_unicode_dash_normalization(self):
        r = normalize_fio_value("Иванов—ПЕТРОВ")
        self.assertEqual(r.after, "Иванов-Петров")
        self.assertEqual(r.status, TECH_STATUS_FIXED)
        self.assertIn(RULE_NORMALIZE_DASH, r.applied_rules)
        self.assertIn(RULE_TITLE_CASE, r.applied_rules)

    def test_invisible_chars_removed(self):
        r = normalize_fio_value("\ufeffИванов\u200b Иван")
        self.assertEqual(r.after, "Иванов Иван")
        self.assertEqual(r.status, TECH_STATUS_FIXED)
        self.assertIn(RULE_STRIP_INVISIBLE, r.applied_rules)

    def test_punctuation_to_spaces_quotes_removed_parentheses_kept(self):
        r = normalize_fio_value('  "ИВАНОВ,ИВАН" (дЕвИчья) ')
        # Quotes removed, comma->space, spaces collapsed, title-cased; parentheses kept
        self.assertEqual(r.after, "Иванов Иван (дЕвИчья)")
        self.assertEqual(r.status, TECH_STATUS_FIXED)
        self.assertIn(RULE_NORMALIZE_PUNCTUATION, r.applied_rules)
        self.assertIn(RULE_NORMALIZE_SPACES, r.applied_rules)
        self.assertIn(RULE_TITLE_CASE, r.applied_rules)

    def test_already_clean_is_ok(self):
        r = normalize_fio_value("Иванов Иван")
        self.assertEqual(r.after, "Иванов Иван")
        self.assertEqual(r.status, TECH_STATUS_OK)
        self.assertEqual(r.applied_rules, [])


if __name__ == "__main__":
    unittest.main()
