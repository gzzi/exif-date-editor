import unittest
from exif_date_editor import *


class GuessDateFromStringTest(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(guess_date_from_string('2018'), datetime(2018, 1, 1))
        self.assertEqual(guess_date_from_string('2018.12.1'), datetime(2018, 12, 1))
        self.assertEqual(guess_date_from_string('2018_12_1_14_16_17'), datetime(2018, 12, 1, 14, 16, 17))
        self.assertEqual(guess_date_from_string('20181201_141617'), datetime(2018, 12, 1, 14, 16, 17))

    def test_with_pre_and_post(self):
        self.assertEqual(guess_date_from_string('20181201_141617titi'), datetime(2018, 12, 1, 14, 16, 17))
        self.assertEqual(guess_date_from_string('toto20181201_141617'), datetime(2018, 12, 1, 14, 16, 17))
        self.assertEqual(guess_date_from_string('toto20181201_141617titi'), datetime(2018, 12, 1, 14, 16, 17))

    def test_with_multiple_digit(self):
        self.assertEqual(guess_date_from_string('20181201_at_beach22'), datetime(2018, 12, 1))
        self.assertEqual(guess_date_from_string('20181201_141617_at_beach2'), datetime(2018, 12, 1, 14, 16, 17))
        self.assertEqual(guess_date_from_string('toto2018_12_01_14_16_17_titi2'), datetime(2018, 12, 1, 14, 16, 17))

    def test_invalid_must_raise_error(self):
        with self.assertRaises(ValueError):
            guess_date_from_string('toto')


if __name__ == '__main__':
    init_logger(to_file=False)
    unittest.main()
