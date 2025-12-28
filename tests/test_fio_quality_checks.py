import sys
import unittest

sys.path.insert(0, "src")

from domain.fio.quality_checks import detect_warnings  # noqa: E402
from domain.fio.constants import (  # noqa: E402
    WARN_HAS_DIGITS,
    WARN_HAS_LATIN,
    WARN_SPLIT_WORD_SUSPECTED,
    WARN_SINGLE_LETTER_TOKEN,
)
from domain.fio.normalize_value import normalize_fio_value  # noqa: E402


class TestFioQualityChecks(unittest.TestCase):
    def test_digits_attention(self):
        w = detect_warnings("Анна9")
        self.assertIn(WARN_HAS_DIGITS, w)

    def test_latin_attention(self):
        w = detect_warnings("Ivanov")
        self.assertIn(WARN_HAS_LATIN, w)

    def test_split_word_suspected(self):
        w = detect_warnings("Г еоргиевна")
        self.assertIn(WARN_SPLIT_WORD_SUSPECTED, w)
        self.assertIn(WARN_SINGLE_LETTER_TOKEN, w)

    def test_title_case_does_not_worsen_split_word(self):
        # T1: should not turn into "Г Еоргиевна"
        r = normalize_fio_value("Г еоргиевна")
        self.assertEqual(r.after, "Г еоргиевна")


if __name__ == "__main__":
    unittest.main()
