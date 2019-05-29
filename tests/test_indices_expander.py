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
        """ The _workdays field should have 16824 items."""
        expected = 16_824
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


if __name__ == '__main__':
    unittest.main()
