import datetime
import os
import sys
import unittest

path = os.path.dirname(__file__)
path = os.path.join(path, '..')
sys.path.append(os.path.abspath(os.path.join(path, 'financial_indices')))

from workdays import Workdays


class TestWorkdays(unittest.TestCase):
    """Class to test all methods of the Workdays class."""

    def setUp(self) -> None:
        """Instantiate Workdays for each test."""
        self.workdays = Workdays()

    def test_load_workdays(self):
        """Making sure _load_workdays() works."""
        actual = self.workdays._load_workdays()
        expected = self.workdays._workdays

        self.assertEqual(actual, expected)

    def test_length_of_workdays(self):
        """Test that the number of workdays loaded is equal to the
        number of workdays expected.
        """
        actual = len(self.workdays)  # returns the length of self._workdays
        expected = self.workdays.__class__._number_workdays

        self.assertEqual(actual, expected)

    def test_binary_search_first_date(self):
        """Test that the binary search finds the first work date available."""
        first_date = datetime.date(2001, 1, 2)  # workday from workdays.csv
        actual = self.workdays.binary_search(self.workdays._workdays, first_date)
        expected = 0

        self.assertEqual(actual, expected)

    def test_binary_search_last_date(self):
        """Test that the binary search finds the last work date."""
        last_date = datetime.date(2078, 12, 30)  # workday from workdays.csv
        actual = self.workdays.binary_search(self.workdays._workdays, last_date)
        expected = 19_592

        self.assertEqual(actual, expected)

    def test_binary_search_outside_bottom_range(self):
        """Test for a working date outside the valid range, from bottom."""
        date = datetime.date(2000, 12, 28)  # workday below 2012

        with self.assertRaises(LookupError):
            self.workdays.binary_search(self.workdays._workdays, date)

    def test_binary_search_outside_top_range(self):
        """Test for a working date outside the valid range, from top."""
        date = datetime.date(2079, 1, 3)  # workday above 2078

        with self.assertRaises(LookupError):
            self.workdays.binary_search(self.workdays, date)

    def test_binary_search_workday_random_1(self):
        """Test an arbitrary work date for binary_search."""
        date = datetime.date(2072, 5, 12)
        actual = self.workdays.binary_search(self.workdays, date)
        expected = 17_926

        self.assertEqual(actual, expected)

    def test_binary_search_workday_random_2(self):
        """Test an arbitrary work date for binary_search."""
        date = datetime.date(2060, 10, 15)
        actual = self.workdays.binary_search(self.workdays, date)
        expected = 15_020

        self.assertEqual(actual, expected)

    def test_binary_search_weekend(self):
        """Test binary_search with a weekend date."""
        date = datetime.date(2024, 7, 20)  # This is a Saturday

        with self.assertRaises(LookupError):
            self.workdays.binary_search(self.workdays, date)

    def test_binary_search_holiday(self):
        """Test binary_search with a holiday date."""
        date = datetime.date(2053, 5, 1)  # This is a holiday on a Thursday

        with self.assertRaises(LookupError):
            self.workdays.binary_search(self.workdays, date)

    def test_get_extra_workdays_negative_extra_days(self):
        """get_extra_workdays() should return empty tuple if extra_days
        is <= 0."""
        date = datetime.date(2019, 4, 25)  # valid workday
        actual = self.workdays.get_extra_workdays(date, -10)
        expected = ()

        self.assertEqual(actual, expected)

    def test_get_extra_workdays_zero_extra_days(self):
        """get_extra_workdays() should return empty tuple if extra_days
        is <= 0."""
        date = datetime.date(2019, 4, 25)  # valid workday
        actual = self.workdays.get_extra_workdays(date, 0)
        expected = ()

        self.assertEqual(actual, expected)

    def test_get_extra_workdays_one_date_ahead_1(self):
        """The first date retrieved from a successful call to get_extra_workdays()
        should be one (workday) date ahead of the searched date."""
        date = datetime.date(2019, 4, 25)  # a valid Thursday
        actual = self.workdays.get_extra_workdays(date, 1)[0]
        expected = datetime.date(2019, 4, 26)  # a valid Friday

        self.assertEqual(actual, expected)

    def test_get_extra_workdays_one_date_ahead_2(self):
        """The first date retrieved from a successful call to get_extra_workdays()
        should be one (workday) date ahead of the searched date."""
        date = datetime.date(2019, 4, 26)  # a valid Friday
        actual = self.workdays.get_extra_workdays(date, 1)[0]
        expected = datetime.date(2019, 4, 29)  # a valid Monday

        self.assertEqual(actual, expected)

    def test_get_extra_workdays_lenght_1(self):
        """Check the number of extra workdays."""
        date = datetime.date(2021, 4, 30)
        actual = len(self.workdays.get_extra_workdays(date, 1))
        expected = 1

        self.assertEqual(actual, expected)

    def test_get_extra_workdays_lenght_2(self):
        """Check the number of extra workdays."""
        date = datetime.date(2021, 4, 30)
        actual = len(self.workdays.get_extra_workdays(date, 2))
        expected = 2

        self.assertEqual(actual, expected)

    def test_get_extra_workdays_lenght_10(self):
        """Check the number of extra workdays."""
        date = datetime.date(2021, 4, 30)
        actual = len(self.workdays.get_extra_workdays(date, 10))
        expected = 10

        self.assertEqual(actual, expected)

    def test_get_extra_workdays_lenght_20(self):
        """Check the number of extra workdays."""
        date = datetime.date(2021, 4, 30)
        actual = len(self.workdays.get_extra_workdays(date, 20))
        expected = 20

        self.assertEqual(actual, expected)

    def test_get_extra_workdays_lenght_30(self):
        """Check the number of extra workdays."""
        date = datetime.date(2021, 4, 30)
        actual = len(self.workdays.get_extra_workdays(date, 30))
        expected = 30

        self.assertEqual(actual, expected)

    def test_get_extra_workdays_legth_after_range_1(self):
        """If the number of extra_workdays passes the top range, the
        tuple should include the days up to the last one."""
        date = datetime.date(2078, 12, 29)  # penultimate workday
        actual = len(self.workdays.get_extra_workdays(date, 100))
        expected = 1

        self.assertEqual(actual, expected)

    def test_get_extra_workdays_legth_after_range_30(self):
        """If the number of extra_workdays passes the top range, the
        tuple should include the days up to the last one."""
        date = datetime.date(2078, 11, 10)
        actual = len(self.workdays.get_extra_workdays(date, 100))
        expected = 35

        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
