from collections import namedtuple
import datetime
import os
import sys
import unittest

path = os.path.dirname(__file__)
path = os.path.join(path, '..')
sys.path.append(os.path.abspath(os.path.join(path, 'financial-indicators')))

from workdays import Workdays
from indicators_expander import IndicatorExpander


class TestWorkdaysField(unittest.TestCase):
    """ Class to test the private field _workdays from IndicatorExpander."""

    def setUp(self) -> None:
        """ Instantiate IndicatorExpander for each test."""
        self.expander = IndicatorExpander()
        self.indicator_record = namedtuple('IndicatorRecord',
                                         ('date', 'value'))

    def test_workdays_exists(self):
        """ The instance of IndicatorExpander should have a private field for
        workdays."""
        self.assertTrue(hasattr(self.expander, '_workdays'))

    @unittest.skip('''This test should fail since Workdays is a singleton
                   by a decorator implementation''')
    def test_workdays_is_workdays(self):
        """ The field _workdays should be an instance of Workdays()."""
        self.assertTrue(isinstance(self.expander._workdays, Workdays))

    def test_workdays_length(self):
        """ The _workdays field should have 19593 items."""
        expected = 19_593
        actual = len(self.expander._workdays)

        self.assertEqual(expected, actual)


class TestDailyWorkdayIndicatorExpander(unittest.TestCase):
    """ Class to test the method _daily_workdays_indicator_expander().

    This method should receive a sequence of namedtuple (IndicatorRecord)
    and return that sequence expanded with 30 workdays, and the last value
    repeated.
    """

    def setUp(self) -> None:
        """ Instantiate IndicatorExpander for each test."""
        self.expander = IndicatorExpander()
        self.indicator_record = namedtuple('IndicatorRecord',
                                         ('date', 'value'))

    def test_empty_input(self):
        """ An empty list should be returned when an empty list is given."""
        expected = []
        actual = self.expander._daily_workday_indicator_expander([])

        self.assertEqual(expected, actual)

    def test_one_item_input(self):
        """ Test to make sure the return has 30 more items."""
        input_ = [
            self.indicator_record(date=datetime.date(2012, 1, 2), value=0.041063),
        ]
        expect = 31
        actual = len(self.expander._daily_workday_indicator_expander(input_))

        self.assertEqual(expect, actual)

    def test_initial_records_are_preserved(self):
        """ Test to ensure that the input records are part of, and in the same
        indexes as before, in the result output.
        """
        input_ = [
            self.indicator_record(date=datetime.date(2013, 8, 7), value=0.032012),
            self.indicator_record(date=datetime.date(2013, 8, 8), value=0.032012),
            self.indicator_record(date=datetime.date(2013, 8, 9), value=0.032012),
        ]
        records = self.expander._daily_workday_indicator_expander(input_)

        same_date_values = [record.date == records[index_].date and
                            record.value == records[index_].value
                            for index_, record in enumerate(input_)]

        self.assertTrue(all(same_date_values))

    def test_new_items_have_increasing_dates(self):
        """ Test to make sure that each new item created has a date higher
        than the last date given.
        """
        input_ = [
            self.indicator_record(date=datetime.date(2016, 10, 4), value=0.052531),
            self.indicator_record(date=datetime.date(2016, 10, 5), value=0.052531),
            self.indicator_record(date=datetime.date(2016, 10, 6), value=0.052531),
        ]
        records = self.expander._daily_workday_indicator_expander(input_)
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
            self.indicator_record(date=datetime.date(2014, 7, 10), value=0.041063),
            self.indicator_record(date=datetime.date(2014, 7, 11), value=0.041063),
            self.indicator_record(date=datetime.date(2014, 7, 14), value=0.041063),
        ]
        output = self.expander._daily_workday_indicator_expander(input_)
        last_input_date = input_[-1].date + delta
        last_output_date = output[-1].date

        self.assertTrue(last_input_date < last_output_date)

    def test_last_value_replicated(self):
        """ Test to make sure that all expanded records have the same value as
        the last input record.
        """
        input_ = [
            self.indicator_record(date=datetime.date(2012, 1, 18), value=0.041063),
            self.indicator_record(date=datetime.date(2012, 1, 19), value=0.039270),
        ]
        output = self.expander._daily_workday_indicator_expander(input_)

        last_value_copied = [input_[-1].value == record.value for record in output[1:]]

        self.assertTrue(all(last_value_copied))

    def test_no_weekend_dates(self):
        """ No record, from either input or output should have weekend dates."""
        input_ = [
            self.indicator_record(date=datetime.date(2014, 10, 14), value=0.035657),
        ]
        output = self.expander._daily_workday_indicator_expander(input_)
        no_weekend_dates = [record.date.weekday() < 5 for record in output]

        self.assertTrue(all(no_weekend_dates))

    def test_outside_workdays_bottom_range(self):
        """ If the last date of the input is older than the first available
        workday date from self._workdays, a LookupError should be raised.
        """
        input_ = [
            self.indicator_record(date=datetime.date(2000, 12, 29), value=0.058366),
        ]
        with self.assertRaises(LookupError):
            self.expander._daily_workday_indicator_expander(input_)

    def test_outside_workdays_top_range(self):
        """ If the last date of the input is newer than the last available
        workday date from self._workdays, a LookupError should be raised.
        """
        input_ = [
            self.indicator_record(date=datetime.date(2079, 12, 28), value=0.0),
        ]
        with self.assertRaises(LookupError):
            self.expander._daily_workday_indicator_expander(input_)

    def test_half_records_outside_workdays_bottom_range(self):
        """ The only value from the input, whose date needs to be higher than
        the first workday date from self._workdays, is the last record from the
        input.
        """
        input_ = [
            # First record is outside range
            self.indicator_record(date=datetime.date(2000, 12, 29), value=0.058366),
            # Second record is inside range
            self.indicator_record(date=datetime.date(2001, 1, 2), value=0.058400),
        ]
        output = self.expander._daily_workday_indicator_expander(input_)
        expected = 32
        actual = len(output)

        self.assertEqual(expected, actual)

    def test_less_than_30_extra_records(self):
        """ The only time a less than 30 records is possible and acceptable,
        is when the range of extra days is above the last available date from
        self._workdays.
        """
        input_ = [
            self.indicator_record(date=datetime.date(2078, 12, 30), value=0.0),
        ]
        output = self.expander._daily_workday_indicator_expander(input_)
        expected = 1
        actual = len(output)

        self.assertEqual(expected, actual)


class TestGetNextDays(unittest.TestCase):
    """ Class to test the method _get_next_days() of the IndicatorExpander class."""

    def setUp(self) -> None:
        """ Instantiate IndicatorExpander for each test."""
        self.expander = IndicatorExpander()

    def test_simple_case(self):
        """ Example of a simple call."""
        input_ = (datetime.date(1991, 2, 26), datetime.date(1991, 3, 26))

        expected = (datetime.date(1991, 2, 27), datetime.date(1991, 3, 27))
        actual = self.expander._get_next_days(*input_)

        self.assertEqual(expected, actual)

    def test_delta_28_days(self):
        """ With a few exceptions, the delta between the first date and the
        second date should be equal to the number of days in the month of the
        first date.
        """
        input_ = (datetime.date(1999, 2, 11), datetime.date(1999, 3, 11))
        output = self.expander._get_next_days(*input_)
        expected = 28
        actual = (output[-1] - output[0]).days

        self.assertEqual(expected, actual)

    def test_delta_29_days(self):
        """ With a few exceptions, the delta between the first date and the
        second date should be equal to the number of days in the month of the
        first date.
        """
        input_ = (datetime.date(2000, 2, 28), datetime.date(2000, 3, 28))
        output = self.expander._get_next_days(*input_)
        expected = 29
        actual = (output[-1] - output[0]).days

        self.assertEqual(expected, actual)

    def test_delta_30_days(self):
        """ With a few exceptions, the delta between the first date and the
        second date should be equal to the number of days in the month of the
        first date.
        """
        input_ = (datetime.date(1996, 4, 1), datetime.date(1996, 5, 1))
        output = self.expander._get_next_days(*input_)
        expected = 30
        actual = (output[-1] - output[0]).days

        self.assertEqual(expected, actual)

    def test_delta_31_days(self):
        """ With a few exceptions, the delta between the first date and the
        second date should be equal to the number of days in the month of the
        first date.
        """
        input_ = (datetime.date(1996, 3, 30), datetime.date(1996, 4, 30))
        output = self.expander._get_next_days(*input_)
        expected = 31
        actual = (output[-1] - output[0]).days

        self.assertEqual(expected, actual)

    def test_first_date_static_1(self):
        """ Sometimes, only the second date is incremented."""
        input_ = (datetime.date(2006, 3, 1), datetime.date(2006, 3, 30))
        expected = (datetime.date(2006, 3, 1), datetime.date(2006, 3, 31))
        actual = self.expander._get_next_days(*input_)

        self.assertEqual(expected, actual)

    def test_first_date_static_2(self):
        """ Sometimes, only the second date is incremented."""
        input_ = (datetime.date(2006, 3, 1), datetime.date(2006, 3, 31))
        expected = (datetime.date(2006, 3, 1), datetime.date(2006, 4, 1))
        actual = self.expander._get_next_days(*input_)

        self.assertEqual(expected, actual)

    def test_second_date_static_1(self):
        """ Sometimes, only the first date is incremented."""
        input_ = (datetime.date(1993, 1, 29), datetime.date(1993, 3, 1))
        expected = (datetime.date(1993, 1, 30), datetime.date(1993, 3, 1))
        actual = self.expander._get_next_days(*input_)

        self.assertEqual(expected, actual)

    def test_second_date_static_2(self):
        """ Sometimes, only the first date is incremented."""
        input_ = (datetime.date(1993, 1, 30), datetime.date(1993, 3, 1))
        expected = (datetime.date(1993, 1, 31), datetime.date(1993, 3, 1))
        actual = self.expander._get_next_days(*input_)

        self.assertEqual(expected, actual)

    def test_second_date_static_3(self):
        """ Sometimes, only the first date is incremented."""
        input_ = (datetime.date(1993, 1, 31), datetime.date(1993, 3, 1))
        expected = (datetime.date(1993, 2, 1), datetime.date(1993, 3, 1))
        actual = self.expander._get_next_days(*input_)

        self.assertEqual(expected, actual)

    def test_equal_dates(self):
        """ When both dates are the same, ValueError should be raised."""
        input_ = (datetime.date(2018, 12, 12), datetime.date(2018, 12, 12))
        with self.assertRaises(ValueError):
            self.expander._get_next_days(*input_)

    def test_second_date_lower(self):
        """ When the second date is lower than the first date, ValueError
        should be raised.
        """
        input_ = (datetime.date(2015, 10, 24), datetime.date(2014, 12, 12))
        with self.assertRaises(ValueError):
            self.expander._get_next_days(*input_)


class TestDailyThreeFieldIndicatorExpander(unittest.TestCase):
    """ Class to test the _daily_three_field_indicator_expander() method."""

    def setUp(self) -> None:
        """ Instantiate IndicatorExpander for each test."""
        self.expander = IndicatorExpander()
        self.indicator_record = namedtuple('IndicatorRecord',
                                         ('date', 'end_date', 'value'))

    def test_empty_input(self):
        """ An empty list should be returned when an empty list is given."""
        expected = []
        actual = self.expander._daily_three_field_indicator_expander([])

        self.assertEqual(expected, actual)

    def test_one_item_input(self):
        """ Test to make sure the return has 30 more items."""
        input_ = [
            self.indicator_record(date=datetime.date(2008, 12, 30),
                                end_date=datetime.date(2009, 1, 30),
                                value=0.2235)
        ]
        expect = 31
        actual = len(self.expander._daily_three_field_indicator_expander(input_))

        self.assertEqual(expect, actual)

    def test_initial_records_are_preserved(self):
        """ Test to ensure that the input records are part of, and in the same
        indexes as before, in the result output.
        """
        input_ = [
            self.indicator_record(date=datetime.date(2008, 6, 26),
                                end_date=datetime.date(2008, 7, 26),
                                value=0.1664),
            self.indicator_record(date=datetime.date(2008, 6, 27),
                                end_date=datetime.date(2008, 7, 27),
                                value=0.1363),
        ]
        records = self.expander._daily_three_field_indicator_expander(input_)

        same_date_values = [record.date == records[index_].date and
                            record.end_date == records[index_].end_date and
                            record.value == records[index_].value
                            for index_, record in enumerate(input_)]

        self.assertTrue(all(same_date_values))

    def test_new_items_have_equal_higher_dates(self):
        """ Test to make sure that each new item created has a date either
        higher or equal than the last date given.
        """
        input_ = [
            self.indicator_record(date=datetime.date(2014, 2, 24),
                                end_date=datetime.date(2014, 3, 24),
                                value=0.0000),
            self.indicator_record(date=datetime.date(2014, 2, 25),
                                end_date=datetime.date(2014, 3, 25),
                                value=0.0007),
        ]
        records = self.expander._daily_three_field_indicator_expander(input_)
        increasing_days = [records[index_].date <= record.date and
                           records[index_].end_date <= record.end_date
                           for index_, record in enumerate(records[1:])]

        self.assertTrue(all(increasing_days))

    def test_last_value_replicated(self):
        """ Test to make sure that all expanded records have the same value as
        the last input record.
        """
        input_ = [
            self.indicator_record(date=datetime.date(2006, 9, 9),
                                end_date=datetime.date(2006, 10, 9),
                                value=0.1576),
            self.indicator_record(date=datetime.date(2006, 9, 10),
                                end_date=datetime.date(2006, 10, 10),
                                value=0.1890),
            self.indicator_record(date=datetime.date(2006, 9, 11),
                                end_date=datetime.date(2006, 10, 11),
                                value=0.2244),
        ]
        output = self.expander._daily_three_field_indicator_expander(input_)

        last_value_copied = [input_[-1].value == record.value for record in output[2:]]

        self.assertTrue(all(last_value_copied))

    def test_january_29_non_leap_year(self):
        """ On a non-leap year, the dates of 29, 30 and 31 of January should
        point to the the end_date of March the 1º.
        """
        input_ = [
            self.indicator_record(date=datetime.date(1993, 1, 28),
                                end_date=datetime.date(1993, 2, 28),
                                value=29.4691),
        ]
        output = self.expander._daily_three_field_indicator_expander(input_)

        expected = [(datetime.date(1993, 1, 28), datetime.date(1993, 2, 28)),
                    (datetime.date(1993, 1, 29), datetime.date(1993, 3, 1)),
                    (datetime.date(1993, 1, 30), datetime.date(1993, 3, 1)),
                    (datetime.date(1993, 1, 31), datetime.date(1993, 3, 1)),
                    (datetime.date(1993, 2, 1), datetime.date(1993, 3, 1)),
                    ]

        actual = [(record.date, record.end_date) for record in output[:5]]

        self.assertEqual(expected, actual)

    def test_january_29_leap_year(self):
        """ On a leap year, the dates of 30 and 31 of January should point to
        the the end_date of March the 1º.
        """
        input_ = [
            self.indicator_record(date=datetime.date(1996, 1, 28),
                                end_date=datetime.date(1996, 2, 28),
                                value=1.1415),
        ]
        output = self.expander._daily_three_field_indicator_expander(input_)

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
            self.indicator_record(date=datetime.date(2000, 5, 30),
                                end_date=datetime.date(2000, 6, 30),
                                value=0.2568),
        ]
        output = self.expander._daily_three_field_indicator_expander(input_)

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
            self.indicator_record(date=datetime.date(2005, 12, 29),
                                end_date=datetime.date(2006, 1, 29),
                                value=0.2276),
        ]
        output = self.expander._daily_three_field_indicator_expander(input_)

        expected = [(datetime.date(2005, 12, 29), datetime.date(2006, 1, 29)),
                    (datetime.date(2005, 12, 30), datetime.date(2006, 1, 30)),
                    (datetime.date(2005, 12, 31), datetime.date(2006, 1, 31)),
                    (datetime.date(2006, 1, 1), datetime.date(2006, 2, 1)),
                    (datetime.date(2006, 1, 2), datetime.date(2006, 2, 2)),
                    ]

        actual = [(record.date, record.end_date) for record in output[:5]]

        self.assertEqual(expected, actual)


class TestIpcaFrom15Expander(unittest.TestCase):
    """ Class to test the method _ipca_from_15_expander().

    This method should receive a sequence of namedtuple (IndicatorRecord)
    and return that sequence expanded with one extra namedtuple, corresponding
    to the next month ipca, from ipca-15.
    """

    def setUp(self) -> None:
        """ Instantiate IndicatorExpander for each test."""
        self.expander = IndicatorExpander()
        self.indicator_record = namedtuple('IndicatorRecord',
                                         ('date', 'value'))

    def test_empty_input(self):
        """ An empty list should be returned when an empty list is given."""
        expected = []
        actual = self.expander._ipca_from_15_expander([])

        self.assertEqual(expected, actual)

    def test_one_item_input(self):
        """ Test to make sure the return has 30 more items."""
        input_ = [
            self.indicator_record(date=datetime.date(1984, 2, 1), value=9.50),
        ]
        expected = 2
        actual = len(self.expander._ipca_from_15_expander(input_))

        self.assertEqual(expected, actual)

    def test_initial_records_are_preserved(self):
        """ Test to ensure that the input records are part of, and in the same
        indexes as before, in the result output.
        """
        input_ = [
            self.indicator_record(date=datetime.date(1998, 5, 1), value=0.50),
            self.indicator_record(date=datetime.date(1998, 6, 1), value=0.02),
            self.indicator_record(date=datetime.date(1998, 7, 1), value=-0.12),
        ]
        records = self.expander._ipca_from_15_expander(input_)

        same_date_values = [record.date == records[index_].date and
                            record.value == records[index_].value
                            for index_, record in enumerate(input_)]

        self.assertTrue(all(same_date_values))

    def test_new_items_have_increasing_dates(self):
        """ Test to make sure that the new record has a higher date than the last
        record from the input.
        """
        input_ = [
            self.indicator_record(date=datetime.date(2004, 11, 1), value=0.69),
            self.indicator_record(date=datetime.date(2004, 12, 1), value=0.86),
            self.indicator_record(date=datetime.date(2005, 1, 1), value=0.58),
        ]
        records = self.expander._ipca_from_15_expander(input_)

        self.assertTrue(records[-1].date > input_[-1].date)

    def test_output_day(self):
        """ The day of the new record must always be equal to 1."""
        input_ = [
            self.indicator_record(date=datetime.date(2011, 1, 1), value=0.83),
            self.indicator_record(date=datetime.date(2011, 2, 1), value=0.80),
        ]
        output = self.expander._ipca_from_15_expander(input_)

        self.assertEqual(output[-1].date.day, 1)

    def test_outside_bottom_range(self):
        """ If the last date of the input cannot be properly completed by the
        first available date for the indicator ipca-15, the value of the last
        record from the input should be repeated.

        The first record for ipca-15 is datetime.date(2000, 5, 1).
        """
        input_ = [
            self.indicator_record(date=datetime.date(2000, 2, 1), value=0.13),
            self.indicator_record(date=datetime.date(2000, 3, 1), value=0.22),
        ]
        output = self.expander._ipca_from_15_expander(input_)
        expected = self.indicator_record(date=datetime.date(2000, 4, 1), value=0.22)
        actual = output[-1]

        self.assertEqual(expected, actual)

    def test_outside_top_range(self):
        """ If the last date of the input is newer than the ipca-15 date could
        possibly be, a ValueError is raised.
        """
        today = datetime.date.today()
        month_ahead = today + datetime.timedelta(31)
        input_ = [
            self.indicator_record(date=month_ahead, value=0.0),
        ]
        with self.assertRaises(ValueError):
            self.expander._ipca_from_15_expander(input_)

    def test_change_of_year(self):
        """ If the last date of the input is from month 12, than the new record
        should be from month 1 of next year."""

        input_ = [
            self.indicator_record(date=datetime.date(2006, 11, 1), value=0.31),
            self.indicator_record(date=datetime.date(2006, 12, 1), value=0.48),
        ]
        output = self.expander._ipca_from_15_expander(input_)
        expected = self.indicator_record(date=datetime.date(2007, 1, 1), value=0.35)
        actual = output[-1]

        self.assertEqual(expected, actual)


class TestGetNextMonth(unittest.TestCase):
    """ Class to test method get_next_month()."""

    def setUp(self) -> None:
        """ Instantiate IndicatorExpander for each test."""
        self.expander = IndicatorExpander()

    def test_outside_bottom_range(self):
        """ If input is below 1, ValueError should be raised."""

        with self.assertRaises(ValueError):
            self.expander.get_next_month(0)

    def test_outside_top_range(self):
        """ If input is above 12, ValueError should be raised."""

        with self.assertRaises(ValueError):
            self.expander.get_next_month(13)

    def test_all_valid_months(self):
        """ 'Brute force' tests for all possibilities."""

        for expected, month in enumerate(range(1, 12), 2):
            actual = self.expander.get_next_month(month)
            self.assertEqual(expected, actual)
        self.assertEqual(1, self.expander.get_next_month(12))


class TestIsSameDateMonthAhead(unittest.TestCase):
    """ Class to test method is_same_date_month_ahead()."""

    def setUp(self) -> None:
        """ Instantiate IndicatorExpander for each test."""
        self.expander = IndicatorExpander()

    def test_date2_lower_date1(self):
        """ If date2 is lower than date1, should return False."""
        date1 = datetime.date(2019, 5, 2)
        date2 = datetime.date(2019, 5, 1)

        self.assertFalse(self.expander.is_same_date_month_ahead(date1, date2))

    def test_date1_equal_date2(self):
        """ If both date are the same, return False."""
        date1 = datetime.date(2014, 11, 29)
        date2 = datetime.date(2014, 11, 29)

        self.assertFalse(self.expander.is_same_date_month_ahead(date1, date2))

    def test_date1_date_higher_date2_month_days(self):
        """ In a case where date1 has a day attribute value, higher than the
        total of days from the next month (ex. January 30-31th from any year),
        it should return false.
        """
        dates1 = (
            datetime.date(1999, 1, 29),
            datetime.date(2005, 1, 30),
            datetime.date(2012, 1, 31),
            datetime.date(1999, 3, 31),
            datetime.date(1999, 5, 31),
            datetime.date(1999, 8, 31),
        )

        dates2 = (
            datetime.date(1999, 2, 28),
            dates1[1] + datetime.timedelta(31),
            dates1[2] + datetime.timedelta(31),
            datetime.date(1999, 4, 30),
            datetime.date(1999, 6, 30),
            datetime.date(1999, 10, 1),
        )
        for date1, date2 in zip(dates1, dates2):
            self.assertFalse(self.expander.is_same_date_month_ahead(date1, date2))

    def test_leap_years(self):
        """ In a leap year, Janury 29 should return True."""

        dates1 = (
            datetime.date(2000, 1, 29),
            datetime.date(2004, 1, 29),
            datetime.date(2008, 1, 29),
            datetime.date(2012, 1, 29),
            datetime.date(2016, 1, 29),
            datetime.date(2020, 1, 29),
            datetime.date(2024, 1, 29),
        )

        dates2 = (
            datetime.date(2000, 2, 29),
            datetime.date(2004, 2, 29),
            datetime.date(2008, 2, 29),
            datetime.date(2012, 2, 29),
            datetime.date(2016, 2, 29),
            datetime.date(2020, 2, 29),
            datetime.date(2024, 2, 29),
        )

        for date1, date2 in zip(dates1, dates2):
            self.assertTrue(self.expander.is_same_date_month_ahead(date1, date2))

    def test_correct_known_examples(self):
        """ Testing some examples that should return True."""

        dates1 = (
            datetime.date(1978, 1, 1),
            datetime.date(1983, 2, 5),
            datetime.date(1994, 3, 9),
            datetime.date(2000, 4, 10),
            datetime.date(2003, 5, 13),
            datetime.date(2008, 6, 18),
            datetime.date(2010, 7, 20),
            datetime.date(2011, 8, 25),
            datetime.date(2015, 9, 26),
            datetime.date(2018, 10, 29),
            datetime.date(2019, 11, 30),
            datetime.date(2020, 12, 31),
        )
        dates2 = (
            datetime.date(1978, 2, 1),
            datetime.date(1983, 3, 5),
            datetime.date(1994, 4, 9),
            datetime.date(2000, 5, 10),
            datetime.date(2003, 6, 13),
            datetime.date(2008, 7, 18),
            datetime.date(2010, 8, 20),
            datetime.date(2011, 9, 25),
            datetime.date(2015, 10, 26),
            datetime.date(2018, 11, 29),
            datetime.date(2019, 12, 30),
            datetime.date(2021, 1, 31),
        )

        for date1, date2 in zip(dates1, dates2):
            self.assertTrue(self.expander.is_same_date_month_ahead(date1, date2))


if __name__ == '__main__':
    unittest.main()
