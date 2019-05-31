from collections import namedtuple
import datetime
import os
import sys
import unittest

path = os.path.dirname(__file__)
path = os.path.join(path, '..')
sys.path.append(os.path.abspath(os.path.join(path, 'financial_indices')))

from workdays import Workdays
from indices_expander import IndicesExpander


class TestWorkdaysField(unittest.TestCase):
    """ Class to test the private field _workdays from IndicesExpander."""

    def setUp(self) -> None:
        """ Instantiate IndicesExpander for each test."""
        self.expander = IndicesExpander()
        self.indices_record = namedtuple('IndicesRecord',
                                         ('date', 'value'))

    def test_workdays_exists(self):
        """ The instance of IndicesExpander should have a private field for
        workdays."""
        self.assertTrue(hasattr(self.expander, '_workdays'))

    def test_workdays_is_workdays(self):
        """ The field _workdays should be an instance of Workdays()."""
        self.assertTrue(isinstance(self.expander._workdays, Workdays))

    def test_workdays_length(self):
        """ The _workdays field should have 19593 items."""
        expected = 19_593
        actual = len(self.expander._workdays)

        self.assertEqual(expected, actual)


class TestDailyWorkdayIndicesExpander(unittest.TestCase):
    """ Class to test the method _daily_workdays_indices_expander().

    This method should receive a sequence of namedtuple (IndicesRecord)
    and return that sequence expanded with 30 workdays, and the last value
    repeated.
    """

    def setUp(self) -> None:
        """ Instantiate IndicesExpander for each test."""
        self.expander = IndicesExpander()
        self.indices_record = namedtuple('IndicesRecord',
                                         ('date', 'value'))

    def test_empty_input(self):
        """ An empty list should be returned when an empty list is given."""
        expected = []
        actual = self.expander._daily_workday_indices_expander([])

        self.assertEqual(expected, actual)

    def test_one_item_input(self):
        """ Test to make sure the return has 30 more items."""
        input_ = [
            self.indices_record(date=datetime.date(2012, 1, 2), value=0.041063),
        ]
        expect = 31
        actual = len(self.expander._daily_workday_indices_expander(input_))

        self.assertEqual(expect, actual)

    def test_initial_records_are_preserved(self):
        """ Test to ensure that the input records are part of, and in the same
        indexes as before, in the result output.
        """
        input_ = [
            self.indices_record(date=datetime.date(2013, 8, 7), value=0.032012),
            self.indices_record(date=datetime.date(2013, 8, 8), value=0.032012),
            self.indices_record(date=datetime.date(2013, 8, 9), value=0.032012),
        ]
        records = self.expander._daily_workday_indices_expander(input_)

        same_date_values = [record.date == records[index_].date and
                            record.value == records[index_].value
                            for index_, record in enumerate(input_)]

        self.assertTrue(all(same_date_values))

    def test_new_items_have_increasing_dates(self):
        """ Test to make sure that each new item created has a date higher
        than the last date given.
        """
        input_ = [
            self.indices_record(date=datetime.date(2016, 10, 4), value=0.052531),
            self.indices_record(date=datetime.date(2016, 10, 5), value=0.052531),
            self.indices_record(date=datetime.date(2016, 10, 6), value=0.052531),
        ]
        records = self.expander._daily_workday_indices_expander(input_)
        increasing_days = [records[index_].date < record.date
                           for index_, record in enumerate(records[1:])]

        self.assertTrue(all(increasing_days))

    def test_last_output_date(self):
        """ Since the expander adds exactly 30 days, and those days are only
        workdays, the last date of the output should necessarily be higher than
        the last date given in the input, by at least 30 days.
        """
        delta = datetime.timedelta(days=30)
        input_ = [
            self.indices_record(date=datetime.date(2014, 7, 10), value=0.041063),
            self.indices_record(date=datetime.date(2014, 7, 11), value=0.041063),
            self.indices_record(date=datetime.date(2014, 7, 14), value=0.041063),
        ]
        output = self.expander._daily_workday_indices_expander(input_)
        last_input_date = input_[-1].date + delta
        last_output_date = output[-1].date

        self.assertTrue(last_input_date < last_output_date)

    def test_last_value_replicated(self):
        """ Test to make sure that all expanded records have the same value as
        the last input record.
        """
        input_ = [
            self.indices_record(date=datetime.date(2012, 1, 18), value=0.041063),
            self.indices_record(date=datetime.date(2012, 1, 19), value=0.039270),
        ]
        output = self.expander._daily_workday_indices_expander(input_)

        last_value_copied = [input_[-1].value == record.value for record in output[1:]]

        self.assertTrue(all(last_value_copied))

    def test_no_weekend_dates(self):
        """ No record, from either input or output should have weekend dates."""
        input_ = [
            self.indices_record(date=datetime.date(2014, 10, 14), value=0.035657),
        ]
        output = self.expander._daily_workday_indices_expander(input_)
        no_weekend_dates = [record.date.weekday() < 5 for record in output]

        self.assertTrue(all(no_weekend_dates))

    def test_outside_workdays_bottom_range(self):
        """ If the last date of the input is older than the first available
        workday date from self._workdays, a LookupError should be raised.
        """
        input_ = [
            self.indices_record(date=datetime.date(2000, 12, 29), value=0.058366),
        ]
        with self.assertRaises(LookupError):
            self.expander._daily_workday_indices_expander(input_)

    def test_outside_workdays_top_range(self):
        """ If the last date of the input is newer than the last available
        workday date from self._workdays, a LookupError should be raised.
        """
        input_ = [
            self.indices_record(date=datetime.date(2079, 12, 28), value=0.0),
        ]
        with self.assertRaises(LookupError):
            self.expander._daily_workday_indices_expander(input_)

    def test_half_records_outside_workdays_bottom_range(self):
        """ The only value from the input, whose date needs to be higher than
        the first workday date from self._workdays, is the last record from the
        input.
        """
        input_ = [
            # First record is outside range
            self.indices_record(date=datetime.date(2000, 12, 29), value=0.058366),
            # Second record is inside range
            self.indices_record(date=datetime.date(2001, 1, 2), value=0.058400),
        ]
        output = self.expander._daily_workday_indices_expander(input_)
        expected = 32
        actual = len(output)

        self.assertEqual(expected, actual)

    def test_less_than_30_extra_records(self):
        """ The only time a less than 30 records is possible and acceptable,
        is when the range of extra days is above the last available date from
        self._workdays.
        """
        input_ = [
            self.indices_record(date=datetime.date(2078, 12, 30), value=0.0),
        ]
        output = self.expander._daily_workday_indices_expander(input_)
        expected = 1
        actual = len(output)

        self.assertEqual(expected, actual)


class TestDailyThreeFieldIndicesExpander(unittest.TestCase):
    """ Class to test the _daily_three_field_indices_expander() method."""

    def setUp(self) -> None:
        """ Instantiate IndicesExpander for each test."""
        self.expander = IndicesExpander()
        self.indices_record = namedtuple('IndicesRecord',
                                         ('date', 'end_date', 'value'))

    def test_empty_input(self):
        """ An empty list should be returned when an empty list is given."""
        expected = []
        actual = self.expander._daily_three_field_indices_expander([])

        self.assertEqual(expected, actual)

    def test_one_item_input(self):
        """ Test to make sure the return has 30 more items."""
        input_ = [
            self.indices_record(date=datetime.date(2008, 12, 30),
                                end_date=datetime.date(2009, 1, 30),
                                value=0.2235)
        ]
        expect = 31
        actual = len(self.expander._daily_three_field_indices_expander(input_))

        self.assertEqual(expect, actual)

    def test_initial_records_are_preserved(self):
        """ Test to ensure that the input records are part of, and in the same
        indexes as before, in the result output.
        """
        input_ = [
            self.indices_record(date=datetime.date(2008, 6, 26),
                                end_date=datetime.date(2008, 7, 26),
                                value=0.1664),
            self.indices_record(date=datetime.date(2008, 6, 27),
                                end_date=datetime.date(2008, 7, 27),
                                value=0.1363),
        ]
        records = self.expander._daily_three_field_indices_expander(input_)

        same_date_values = [record.date == records[index_].date and
                            record.end_date == records[index_].end_date and
                            record.value == records[index_].value
                            for index_, record in enumerate(input_)]

        self.assertTrue(all(same_date_values))

    def test_new_items_have_increasing_dates(self):
        """ Test to make sure that each new item created has a date higher
        than the last date given.
        """
        input_ = [
            self.indices_record(date=datetime.date(2014, 2, 24),
                                end_date=datetime.date(2014, 3, 24),
                                value=0.0000),
            self.indices_record(date=datetime.date(2014, 2, 25),
                                end_date=datetime.date(2014, 3, 25),
                                value=0.0007),
        ]
        records = self.expander._daily_three_field_indices_expander(input_)
        increasing_days = [records[index_].date < record.date and
                           records[index_].end_date < record.end_date
                           for index_, record in enumerate(records[1:])]

        self.assertTrue(all(increasing_days))

    def test_last_output_date(self):
        """ Since _daily_three_field_indices_expander adds 30 days in a row,
        the last date from the output should be exactly 30 days ahead of the
        last date from the input.
        """
        delta = datetime.timedelta(days=30)
        input_ = [
            self.indices_record(date=datetime.date(2017, 8, 21),
                                end_date=datetime.date(2017, 9, 21),
                                value=0.0122),
            self.indices_record(date=datetime.date(2017, 8, 22),
                                end_date=datetime.date(2017, 9, 22),
                                value=0.0191),
        ]
        output = self.expander._daily_three_field_indices_expander(input_)
        expected = input_[-1].date + delta
        actual = output[-1].date

        self.assertEqual(expected, actual)

    def test_last_value_replicated(self):
        """ Test to make sure that all expanded records have the same value as
        the last input record.
        """
        input_ = [
            self.indices_record(date=datetime.date(2006, 9, 9),
                                end_date=datetime.date(2006, 10, 9),
                                value=0.1576),
            self.indices_record(date=datetime.date(2006, 9, 10),
                                end_date=datetime.date(2006, 10, 10),
                                value=0.1890),
            self.indices_record(date=datetime.date(2006, 9, 11),
                                end_date=datetime.date(2006, 10, 11),
                                value=0.2244),
        ]
        output = self.expander._daily_three_field_indices_expander(input_)

        last_value_copied = [input_[-1].value == record.value for record in output[2:]]

        self.assertTrue(all(last_value_copied))

    def test_match_input_output_dates(self):
        """ Test to make sure all dates are correct."""
        input_ = [
            self.indices_record(date=datetime.date(1991, 2, 1),
                                end_date=datetime.date(1991, 3, 1),
                                value=7.0000),
        ]
        output = self.expander._daily_three_field_indices_expander(input_)
        array_of_days = [input_[0].date] + [input_[0].date + datetime.timedelta(day)
                                            for day in range(30)]
        match_input_output_days = [record.date == date
                                   for record, date in zip(output, array_of_days)]

        self.assertTrue(all(match_input_output_days))

    def test_january_29_non_leap_year(self):
        """ On a non-leap year, the dates of 29, 30 and 31 of January should
        point to the the end_date of March the 1º.
        """
        input_ = [
            self.indices_record(date=datetime.date(1993, 1, 28),
                                end_date=datetime.date(1993, 2, 28),
                                value=29.4691),
        ]
        output = self.expander._daily_three_field_indices_expander(input_)

        expected = [(datetime.date(1993, 1, 28), datetime.date(1993, 2, 28)),
                    (datetime.date(1993, 1, 29), datetime.date(1993, 3, 1)),
                    (datetime.date(1993, 1, 30), datetime.date(1993, 3, 1)),
                    (datetime.date(1993, 1, 31), datetime.date(1993, 3, 1)),
                    ]

        actual = [(record.date, record.end_date) for record in output[:4]]

        self.assertEqual(expected, actual)

    def test_january_29_leap_year(self):
        """ On a leap year, the dates of 30 and 31 of January should point to
        the the end_date of March the 1º.
        """
        input_ = [
            self.indices_record(date=datetime.date(1996, 1, 28),
                                end_date=datetime.date(1996, 2, 28),
                                value=1.1415),
        ]
        output = self.expander._daily_three_field_indices_expander(input_)

        expected = [(datetime.date(1996, 1, 28), datetime.date(1996, 2, 28)),
                    (datetime.date(1996, 1, 29), datetime.date(1996, 2, 29)),
                    (datetime.date(1996, 1, 30), datetime.date(1996, 3, 1)),
                    (datetime.date(1996, 1, 31), datetime.date(1996, 3, 1)),
                    ]

        actual = [(record.date, record.end_date) for record in output[:4]]

        self.assertEqual(expected, actual)

    def test_end_dates_month_end(self):
        """ When the current month as 31 days and the following month as only
        30, the end_date of the 1º day of the next/next month, should appear
        twice, for both the day 31 and 1.
        """
        input_ = [
            self.indices_record(date=datetime.date(2000, 5, 30),
                                end_date=datetime.date(2000, 6, 30),
                                value=0.2568),
        ]
        output = self.expander._daily_three_field_indices_expander(input_)

        expected = [(datetime.date(2000, 5, 30), datetime.date(2000, 6, 30)),
                    (datetime.date(2000, 5, 31), datetime.date(2000, 7, 1)),
                    (datetime.date(2000, 6, 1), datetime.date(2000, 7, 1)),
                    ]

        actual = [(record.date, record.end_date) for record in output[:3]]

        self.assertEqual(expected, actual)

    def test_end_of_year(self):
        """ Test to make sure date and end_date are working properly when there
        is a change of the year.
        """
        input_ = [
            self.indices_record(date=datetime.date(2005, 12, 29),
                                end_date=datetime.date(2006, 1, 29),
                                value=0.2276),
        ]
        output = self.expander._daily_three_field_indices_expander(input_)

        expected = [(datetime.date(2005, 12, 29), datetime.date(2006, 1, 29)),
                    (datetime.date(2005, 12, 30), datetime.date(2006, 1, 30)),
                    (datetime.date(2005, 12, 31), datetime.date(2006, 1, 31)),
                    (datetime.date(2005, 1, 1), datetime.date(2006, 2, 1)),
                    (datetime.date(2005, 1, 2), datetime.date(2006, 2, 2)),
                    ]

        actual = [(record.date, record.end_date) for record in output[:5]]

        self.assertEqual(expected, actual)


class TestIpcaFrom15Expander(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
