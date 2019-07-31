from collections import namedtuple
import datetime
import os
import sys
import unittest

path = os.path.dirname(__file__)
path = os.path.join(path, '..')
sys.path.append(os.path.abspath(os.path.join(path, 'financial-indices')))

from bcb_api import FinancialIndicesApi


class TestCreateApiUrl(unittest.TestCase):
    """ Class to test the _create_pi_url() method from FinancialIndicesApi class."""

    def setUp(self) -> None:
        """ Instantiate FinancialIndicesApi for each test."""
        self.bcb_api = FinancialIndicesApi()

    def test_empty_dates(self):
        """ Check url result when both start_date and end_date are omitted.
        """
        today = datetime.date.today().strftime('%d/%m/%Y')
        expected = f'http://api.bcb.gov.br/dados/serie/bcdata.sgs.{11}/dados?formato=json&dataInicial={None}&dataFinal={today}'
        actual = self.bcb_api._create_api_url(11)  # empty dates

        self.assertEqual(expected, actual)

    def test_both_dates_as_none(self):
        """ Check url result when both start_date and end_date are given with None
        values.
        """
        today = datetime.date.today().strftime('%d/%m/%Y')
        expected = f'http://api.bcb.gov.br/dados/serie/bcdata.sgs.{433}/dados?formato=json&dataInicial={None}&dataFinal={today}'
        actual = self.bcb_api._create_api_url(433, None, None)  # dates given as None

        self.assertEqual(expected, actual)

    def test_start_date_as_none(self):
        """ Check url result when start_date is None. In this scenario, it's
        impossible to guess a start_date, therefore it is left no None.
        """
        expected = f'http://api.bcb.gov.br/dados/serie/bcdata.sgs.{12}/dados?formato=json&dataInicial={None}&dataFinal=29/09/1989'
        actual = self.bcb_api._create_api_url(12, None, datetime.date(1989, 9, 29))

        self.assertEqual(expected, actual)

    def test_invalid_start_date_end_date_none(self):
        """ When start_date if provided, but it's higher than the date of today,
        it should raise a ValueError.
        """
        tomorrow = datetime.date.today() + datetime.timedelta(1)
        with self.assertRaises(ValueError):
            self.bcb_api._create_api_url(226,
                                         start_date=tomorrow,
                                         end_date=None)

    def test_end_date_as_none(self):
        """ Check url result when end_date is None. In this scenario, the
        method gives the end_date the date of today, whatever today might be.
        """
        today = datetime.date.today().strftime('%d/%m/%Y')
        expected = f'http://api.bcb.gov.br/dados/serie/bcdata.sgs.{12}/dados?formato=json&dataInicial=29/09/1989&dataFinal={today}'
        actual = self.bcb_api._create_api_url(12, datetime.date(1989, 9, 29), None)

        self.assertEqual(expected, actual)

    def test_valid_dates(self):
        """ Check url result when both start and end_date are provided."""
        expected = f'http://api.bcb.gov.br/dados/serie/bcdata.sgs.{7478}/dados?formato=json&dataInicial=29/09/1989&dataFinal=12/05/2019'
        actual = self.bcb_api._create_api_url(7478,
                                              datetime.date(1989, 9, 29),
                                              datetime.date(2019, 5, 12))

        self.assertEqual(expected, actual)

    def test_same_dates(self):
        """ Check url result when both start and end_date are equal. This is
        allowed, as the result is included in both ends.
        """
        expected = f'http://api.bcb.gov.br/dados/serie/bcdata.sgs.{7478}/dados?formato=json&dataInicial=21/04/2010&dataFinal=21/04/2010'
        actual = self.bcb_api._create_api_url(7478,
                                              datetime.date(2010, 4, 21),
                                              datetime.date(2010, 4, 21))

        self.assertEqual(expected, actual)

    def test_swap_start_and_end_dates(self):
        """ Method should raise ValueError when both dates are given, but
        start_date is higher than the end_date.
        """
        with self.assertRaises(ValueError):
            self.bcb_api._create_api_url(433,
                                         start_date=datetime.date(2019, 5, 12),
                                         end_date=datetime.date(1989, 9, 29))


class TestGetJsonResults(unittest.TestCase):
    """ Class to test the _get_json_results() method from FinancialIndicesApi."""

    def setUp(self) -> None:
        """ Instantiate FinancialIndicesApi for each test."""
        self.bcb_api = FinancialIndicesApi()

    # Testing for daily indices.

    def test_daily_indices_selic_format(self):
        """ Test to make sure Selic results come as expected."""
        url = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&dataInicial=04/03/1997&dataFinal=05/03/1997'
        expected = [
            {'data': '04/03/1997', 'valor': '0.085667'},
            {'data': '05/03/1997', 'valor': '0.085333'},
        ]
        actual = self.bcb_api._get_json_results(url)

        self.assertEqual(expected, actual)

    def test_daily_indices_cdi_format(self):
        """ Test to make sure CDI results come as expected."""
        url = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial=04/03/1997&dataFinal=05/03/1997'
        expected = [
            {'data': '04/03/1997', 'valor': '0.085000'},
            {'data': '05/03/1997', 'valor': '0.085000'},
        ]
        actual = self.bcb_api._get_json_results(url)

        self.assertEqual(expected, actual)

    def test_daily_indices_tr_format(self):
        """ Test to make sure TR results come as expected."""
        url = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.226/dados?formato=json&dataInicial=04/03/1997&dataFinal=05/03/1997'
        expected = [
            {'data': '04/03/1997', 'datafim': '04/04/1997', 'valor': '0.7612'},
            {'data': '05/03/1997', 'datafim': '05/04/1997', 'valor': '0.7852'},
        ]
        actual = self.bcb_api._get_json_results(url)

        self.assertEqual(expected, actual)

    def test_daily_indices_same_valid_dates(self):
        """ Since the results from the dates are inclusive, when one date is
        given as both start and end_date, one record is found.
        """
        url = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&dataInicial=02/01/2019&dataFinal=02/01/2019'
        expected = [
            {'data': '02/01/2019',
             'valor': '0.024620'}
        ]
        actual = self.bcb_api._get_json_results(url)

        self.assertEqual(expected, actual)

    def test_daily_indices_same_invalid_dates(self):
        """ Since the results from the dates are inclusive, when one date is
        given as both start and end_date, one record is found.

        If the date given doesn't have a value (holiday or weekend, depending
        on the indices), the api searches for the last valid date and returns
        that value.
        """
        url = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&dataInicial=01/01/2019&dataFinal=01/01/2019'
        expected = [
            {'data': '31/12/2018',
             'valor': '0.024620'}
        ]
        actual = self.bcb_api._get_json_results(url)

        self.assertEqual(expected, actual)

    def test_daily_indices_start_date_none_cdi(self):
        """ When start_date is an invalid value (such as an alphabetic character
        or None), the api will query all results, not respecting the end_date.

        This test proves that the end_date is not respected.
        """
        start_date = None  # invalid date
        end_date = datetime.date(1990, 1, 2).strftime('%d/%m/%Y')
        url = f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial={start_date}&dataFinal={end_date}'
        expected = {'data': '02/01/1990', 'valor': '2.655806'}

        actual = self.bcb_api._get_json_results(url)[-1]  # the last record

        self.assertNotEqual(expected, actual)

    def test_daily_indices_end_date_none_selic(self):
        """ When end_date is an invalid value (such as an alphabetic character
        or None), the api will query all results, not respecting the start_date.

        This test proves that the start_date is not respected.
        """
        start_date = datetime.date(2010, 4, 2).strftime('%d/%m/%Y')
        end_date = 'dkjahdkja'  # invalid date
        url = f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&dataInicial={start_date}&dataFinal={end_date}'
        expected = {
            'data': '04/06/1986', 'valor': '0.065041'  # first available record for this indices
        }
        actual = self.bcb_api._get_json_results(url)[0]  # first record

        self.assertEqual(expected, actual)

    def test_daily_indices_lengthy_result_selic(self):
        """ From 01/01/1994 to 01/01/2019 there should be 6271 selic records.
        """
        url = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&dataInicial=01/01/1994&dataFinal=01/01/2019'
        expected = 6271

        actual = len(self.bcb_api._get_json_results(url))

        self.assertEqual(expected, actual)

    # Testing for monthly indices.

    def test_monthly_indices_ipca_format(self):
        """ Test to make sure IPCA results come as expected."""
        url = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial=04/03/1997&dataFinal=05/03/1997'
        expected = [
            {'data': '01/03/1997', 'valor': '0.51'}
        ]
        actual = self.bcb_api._get_json_results(url)

        self.assertEqual(expected, actual)

    def test_monthly_indices_ipca15_format(self):
        """ Test to make sure IPCA-15 results come as expected."""
        url = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.7478/dados?formato=json&dataInicial=10/10/2003&dataFinal=10/10/2003'
        expected = [
            {'data': '01/10/2003', 'valor': '0.66'}
        ]
        actual = self.bcb_api._get_json_results(url)

        self.assertEqual(expected, actual)

    def test_monthly_indices_same_valid_dates(self):
        """ If dates are equal, there will always be one record, corresponding
        to either the month given, or the last available record.
        """
        url = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial=05/03/2010&dataFinal=05/03/2010'
        expected = [
            {'data': '01/03/2010', 'valor': '0.52'},
        ]
        actual = self.bcb_api._get_json_results(url)

        self.assertEqual(expected, actual)

    def test_monthly_indices_start_date_none_ipca(self):
        """ When start_date is an invalid value (such as an alphabetic character
        or None), the api will query all results, not respecting the end_date.

        This test proves that the end_date is not respected.
        """
        start_date = None
        end_date = datetime.date(2010, 3, 5).strftime('%d/%m/%Y')
        url = f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial={start_date}&dataFinal={end_date}'
        expected = {'data': '01/03/2010', 'valor': '0.52'}

        actual = self.bcb_api._get_json_results(url)[-1]

        self.assertNotEqual(expected, actual)

    def test_monthly_indices_end_date_none_ipca(self):
        """ When start_date is an invalid value (such as an alphabetic character
        or None), the api will query all results, not respecting the end_date.

        This test proves that the start_-date is not respected.
        """
        start_date = datetime.date(1995, 12, 12).strftime('%d/%m/%Y')
        end_date = None
        url = f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial={start_date}&dataFinal={end_date}'
        expected = {'data': '01/12/1995', 'valor': '1.56'}

        actual = self.bcb_api._get_json_results(url)[0]

        self.assertNotEqual(expected, actual)


class TestFixApiResultsTwoFields(unittest.TestCase):
    """ Class to test the _fix_api_results() method from FinancialIndicesApi,
    where each record has only two fields of values (date and value)."""

    def setUp(self) -> None:
        """ Instantiate FinancialIndicesApi, and define the namedtuple type that
         results from the method, for each test.
         """
        self.bcb_api = FinancialIndicesApi()
        self.IndicesRecord = namedtuple('IndicesRecord', ('date', 'value'))

    def test_empty_api_result(self):
        """ An empty api result should return an empty list."""
        argument = []  # an empty result probably looks like this
        expected = []
        actual = self.bcb_api._fix_api_results(argument)

        self.assertEqual(expected, actual)

    def test_one_record_result(self):
        """ A one record result should look like this."""
        argument = [
            {'data': '05/03/1992', 'valor': '1.250667'},
        ]
        expected = [
            self.IndicesRecord(date=datetime.date(1992, 3, 5), value=1.250667),
        ]
        actual = self.bcb_api._fix_api_results(argument)

        self.assertEqual(expected, actual)

    def test_result_five_records(self):
        """ Five records result should look like this."""
        argument = [
            {'data': '26/12/2008', 'valor': '0.050299'},
            {'data': '29/12/2008', 'valor': '0.050578'},
            {'data': '30/12/2008', 'valor': '0.050648'},
            {'data': '31/12/2008', 'valor': '0.050683'},
            {'data': '02/01/2009', 'valor': '0.050683'},
        ]
        expected = [
            self.IndicesRecord(date=datetime.date(2008, 12, 26), value=0.050299),
            self.IndicesRecord(date=datetime.date(2008, 12, 29), value=0.050578),
            self.IndicesRecord(date=datetime.date(2008, 12, 30), value=0.050648),
            self.IndicesRecord(date=datetime.date(2008, 12, 31), value=0.050683),
            self.IndicesRecord(date=datetime.date(2009, 1, 2), value=0.050683),
        ]
        actual = self.bcb_api._fix_api_results(argument)

        self.assertEqual(expected, actual)

    def test_result_five_records_inverted(self):
        """ The order of the records internal data should not matter."""
        argument = [
            {'valor': '0.43', 'data': '01/07/2012'},
            {'valor': '0.41', 'data': '01/08/2012'},
            {'valor': '0.57', 'data': '01/09/2012'},
            {'valor': '0.59', 'data': '01/10/2012'},
            {'valor': '0.60', 'data': '01/11/2012'},
        ]
        expected = [
            self.IndicesRecord(date=datetime.date(2012, 7, 1), value=0.43),
            self.IndicesRecord(date=datetime.date(2012, 8, 1), value=0.41),
            self.IndicesRecord(date=datetime.date(2012, 9, 1), value=0.57),
            self.IndicesRecord(date=datetime.date(2012, 10, 1), value=0.59),
            self.IndicesRecord(date=datetime.date(2012, 11, 1), value=0.60),
        ]
        actual = self.bcb_api._fix_api_results(argument)

        self.assertEqual(expected, actual)


class TestFixApiResultsThreeFields(unittest.TestCase):
    """ Class to test the _fix_api_results() method from FinancialIndicesApi,
    where each record has three fields of values (date, end_date and value).
    """

    def setUp(self) -> None:
        """ Instantiate FinancialIndicesApi, and define the namedtuple type that
         results from the method, for each test.
         """
        self.bcb_api = FinancialIndicesApi()
        self.IndicesRecord = namedtuple('IndicesRecord',
                                        ('date', 'end_date', 'value'))

    def test_empty_api_result(self):
        """An empty api result should return an empty list."""
        argument = []  # an empty result probably looks like this
        expected = []
        actual = self.bcb_api._fix_api_results(argument)

        self.assertEqual(expected, actual)

    def test_result_one_record(self):
        """ A one record result should look like this."""
        argument = [
            {'data': '03/05/1992', 'datafim': '03/06/1992', 'valor': '22.0529'},
        ]
        expected = [
            self.IndicesRecord(date=datetime.date(1992, 5, 3), end_date=datetime.date(1992, 6, 3), value=22.0529),
        ]
        actual = self.bcb_api._fix_api_results(argument)

        self.assertEqual(expected, actual)

    def test_result_five_records(self):
        """ Five records result should look like this."""
        argument = [
            {'data': '26/12/2008', 'datafim': '26/01/2009', 'valor': '0.1478'},
            {'data': '27/12/2008', 'datafim': '27/01/2009', 'valor': '0.1560'},
            {'data': '28/12/2008', 'datafim': '28/01/2009', 'valor': '0.1844'},
            {'data': '29/12/2008', 'datafim': '29/01/2009', 'valor': '0.1930'},
            {'data': '30/12/2008', 'datafim': '30/01/2009', 'valor': '0.2235'},
        ]
        expected = [
            self.IndicesRecord(date=datetime.date(2008, 12, 26), end_date=datetime.date(2009, 1, 26),  value=0.1478),
            self.IndicesRecord(date=datetime.date(2008, 12, 27), end_date=datetime.date(2009, 1, 27),  value=0.1560),
            self.IndicesRecord(date=datetime.date(2008, 12, 28), end_date=datetime.date(2009, 1, 28),  value=0.1844),
            self.IndicesRecord(date=datetime.date(2008, 12, 29), end_date=datetime.date(2009, 1, 29),  value=0.1930),
            self.IndicesRecord(date=datetime.date(2008, 12, 30), end_date=datetime.date(2009, 1, 30),  value=0.2235),
        ]
        actual = self.bcb_api._fix_api_results(argument)

        self.assertEqual(expected, actual)

    def test_result_three_records_inverted(self):
        """ The order of the records internal data should not matter."""
        argument = [
            {'valor': '0.0533', 'data': '21/04/2009', 'datafim': '21/05/2009'},
            {'valor': '0.0474', 'data': '22/04/2009', 'datafim': '22/05/2009'},
            {'valor': '0.0783', 'data': '23/04/2009', 'datafim': '23/05/2009'},
        ]
        expected = [
            self.IndicesRecord(date=datetime.date(2009, 4, 21), end_date=datetime.date(2009, 5, 21), value=0.0533),
            self.IndicesRecord(date=datetime.date(2009, 4, 22), end_date=datetime.date(2009, 5, 22), value=0.0474),
            self.IndicesRecord(date=datetime.date(2009, 4, 23), end_date=datetime.date(2009, 5, 23), value=0.0783),
        ]
        actual = self.bcb_api._fix_api_results(argument)

        self.assertEqual(expected, actual)


class TestRmRecordsOutsideRange(unittest.TestCase):
    """ Class to test _rm_records_outside_range() method from
    FinancialIndicesApi class.
    """

    def setUp(self) -> None:
        """ Instantiate FinancialIndicesApi for each test."""
        self.bcb_api = FinancialIndicesApi()
        self.IndicesRecord = namedtuple('IndicesRecord',
                                        ('date', 'value'))

    def test_empty_dates_empty_records(self):
        """ When both dates are None and records_array is an empty list,
        an empty list should be returned.
        """
        expected = []
        actual = self.bcb_api._rm_records_outside_range(None, None, [])

        self.assertEqual(expected, actual)

    def test_empty_dates_one_record(self):
        """ When both dates are None, the returned array should always be
        equal to the records_array provided.
        """
        records = [self.IndicesRecord(date=datetime.date(1986, 6, 4), value=0.065041),]
        expected = records[:]
        actual = self.bcb_api._rm_records_outside_range(None, None, records)

        self.assertEqual(expected, actual)

    def test_empty_dates_few_records(self):
        """ When both dates are None, the returned array should always be
        equal to the records_array provided.
        """
        records = [
            self.IndicesRecord(date=datetime.date(2018, 12, 14), value=0.024620),
            self.IndicesRecord(date=datetime.date(2018, 12, 17), value=0.024620),
            self.IndicesRecord(date=datetime.date(2018, 12, 18), value=0.024620),
            self.IndicesRecord(date=datetime.date(2018, 12, 19), value=0.024620),
        ]
        expected = records[:]
        actual = self.bcb_api._rm_records_outside_range(None, None, records)

        self.assertEqual(expected, actual)

    def test_first_record_equal_to_start_date(self):
        """ When start_date is given, but the first record'date is already equal
        to that date, the original records_array should be returned.
        """
        records = [  # result from api
            self.IndicesRecord(date=datetime.date(2014, 4, 10), value=0.040705),
            self.IndicesRecord(date=datetime.date(2014, 4, 11), value=0.040705),
            self.IndicesRecord(date=datetime.date(2014, 4, 14), value=0.040705),
            self.IndicesRecord(date=datetime.date(2014, 4, 15), value=0.040705),
            self.IndicesRecord(date=datetime.date(2014, 4, 16), value=0.040705),
            self.IndicesRecord(date=datetime.date(2014, 4, 17), value=0.040705),
            self.IndicesRecord(date=datetime.date(2014, 4, 22), value=0.040705),
            self.IndicesRecord(date=datetime.date(2014, 4, 23), value=0.040705),
        ]
        expected = records[:]
        actual = self.bcb_api._rm_records_outside_range(datetime.date(2014, 4, 10),
                                                        None, records)

        self.assertEqual(expected, actual)

    def test_first_record_lower_than_start_date(self):
        """ When start_date is given, and there are records with dates lower
        than the start_date, those records are removed.
        """
        records = [  # result from api
            self.IndicesRecord(date=datetime.date(2011, 12, 30), value=0.040956),
            self.IndicesRecord(date=datetime.date(2012, 1, 2), value=0.041028),
            self.IndicesRecord(date=datetime.date(2012, 1, 3), value=0.040992),
        ]
        expected = [
            self.IndicesRecord(date=datetime.date(2012, 1, 2), value=0.041028),
            self.IndicesRecord(date=datetime.date(2012, 1, 3), value=0.040992),
        ]
        actual = self.bcb_api._rm_records_outside_range(datetime.date(2011, 12, 31),
                                                        None, records)

        self.assertEqual(expected, actual)

    def test_last_record_equal_to_end_date(self):
        """ When the date of the last record is equal to the end_date,
        then it should be returned.
        """
        records = [  # result from the api
            self.IndicesRecord(date=datetime.date(1986, 6, 4), value=0.065041),
            self.IndicesRecord(date=datetime.date(1986, 6, 5), value=0.067397),
            self.IndicesRecord(date=datetime.date(1986, 6, 6), value=0.066740),
        ]
        expected = records[:]
        actual = self.bcb_api._rm_records_outside_range(None,
                                                        datetime.date(1986, 6, 6),
                                                        records)
        self.assertEqual(expected, actual)

    def test_last_record_higher_than_end_date(self):
        """ When there are records with dates higher than the end_date,
        they are removed.
        """
        records = [  # result from the api
            self.IndicesRecord(date=datetime.date(1986, 6, 4), value=0.065041),
            self.IndicesRecord(date=datetime.date(1986, 6, 5), value=0.067397),
            self.IndicesRecord(date=datetime.date(1986, 6, 6), value=0.066740),
            self.IndicesRecord(date=datetime.date(1986, 6, 9), value=0.068247),
            self.IndicesRecord(date=datetime.date(1986, 6, 10), value=0.067041),
        ]
        expected = records[:-2]
        actual = self.bcb_api._rm_records_outside_range(None,
                                                        datetime.date(1986, 6, 6),
                                                        records)
        self.assertEqual(expected, actual)

    def test_valid_dates_with_no_removals(self):
        """ When both start and end date are given, but the results are within
        both dates (included), than nothing happens.
        """
        records = [
            self.IndicesRecord(date=datetime.date(2007, 7, 26), value=0.058058),
            self.IndicesRecord(date=datetime.date(2007, 7, 27), value=0.058058),
            self.IndicesRecord(date=datetime.date(2007, 7, 28), value=0.058092),
            self.IndicesRecord(date=datetime.date(2007, 7, 29), value=0.058160),
            self.IndicesRecord(date=datetime.date(2007, 7, 30), value=0.058298),
            self.IndicesRecord(date=datetime.date(2007, 8, 2), value=0.058298),
        ]
        expected = records[:]
        actual = self.bcb_api._rm_records_outside_range(datetime.date(2007, 7, 23),
                                                        datetime.date(2007, 8, 2),
                                                        records)
        self.assertEqual(expected, actual)


class TestGetLatestDateTwoFields(unittest.TestCase):
    """ Class to test get_latest_date() method from the FinancialIndicesApi
    class.
    """
    def setUp(self) -> None:
        """ Instantiate FinancialIndicesApi for each test."""
        self.bcb_api = FinancialIndicesApi()
        self.IndicesRecord = namedtuple('IndicesRecord',
                                        ('date', 'value'))
        self.bcb_api._indices_records = {
            11: [
                self.IndicesRecord(date=datetime.date(2005, 9, 27), value=0.070718),
                self.IndicesRecord(date=datetime.date(2005, 9, 28), value=0.070784),
                self.IndicesRecord(date=datetime.date(2005, 9, 29), value=0.070784),
                self.IndicesRecord(date=datetime.date(2005, 9, 30), value=0.070818),
            ],
            12: [
                # Indices without a record
            ],
            433: [
                self.IndicesRecord(date=datetime.date(1987, 4, 1), value=19.10)
            ],
        }

    def test_non_existing_indices(self):
        """ When a non-existing indices is searched, it should return None."""
        expected = None
        actual = self.bcb_api.get_latest_date(1)

        self.assertEqual(expected, actual)

    def test_indices_without_records(self):
        """ If an indices do exist, but it doesn't have a value, it should
        return None."""
        expected = None
        actual = self.bcb_api.get_latest_date(12)

        self.assertEqual(expected, actual)

    def test_indices_with_single_record(self):
        """ get_latest_date() should return the date of the latest record,
        even if that indices has only one record.
        """
        expected = datetime.date(1987, 4, 1)
        actual = self.bcb_api.get_latest_date(433)

        self.assertEqual(expected, actual)

    def test_indices_with_multiple_records(self):
        """ get_latest_date() should return the date of the latest record."""
        expected = datetime.date(2005, 9, 30)
        actual = self.bcb_api.get_latest_date(11)

        self.assertEqual(expected, actual)


class TestGetLatestDateThreeFields(unittest.TestCase):
    """ Class to test get_latest_date() method from the FinancialIndicesApi
    class.
    """
    def setUp(self) -> None:
        """ Instantiate FinancialIndicesApi for each test."""
        self.bcb_api = FinancialIndicesApi()
        self.IndicesRecord = namedtuple('IndicesRecord',
                                        ('date', 'end_date', 'value'))
        self.bcb_api._indices_records = {
            226: [
                self.IndicesRecord(date=datetime.date(1991, 2, 1), end_date=datetime.date(1991, 3, 1), value=7.0000),
                self.IndicesRecord(date=datetime.date(1991, 2, 2), end_date=datetime.date(1991, 3, 2), value=7.4604),
                self.IndicesRecord(date=datetime.date(1991, 2, 3), end_date=datetime.date(1991, 3, 3), value=7.4604),
                self.IndicesRecord(date=datetime.date(1991, 2, 4), end_date=datetime.date(1991, 3, 4), value=7.4604),
                self.IndicesRecord(date=datetime.date(1991, 2, 5), end_date=datetime.date(1991, 3, 5), value=7.6135),
            ],
            253: [
                self.IndicesRecord(date=datetime.date(1998, 3, 30), end_date=datetime.datetime(1998, 4, 30), value=1.7585)
            ],
            25: [

            ],
        }

    def test_non_existing_indices(self):
        """ When a non-existing indices is searched, it should return None."""
        expected = None
        actual = self.bcb_api.get_latest_date(1)

        self.assertEqual(expected, actual)

    def test_indices_without_records(self):
        """ If an indices do exist, but it doesn't have a value, it should
        return None."""
        expected = None
        actual = self.bcb_api.get_latest_date(25)

        self.assertEqual(expected, actual)

    def test_indices_with_single_record(self):
        """ get_latest_date() should return the date of the latest record,
        even if that indices has only one record.
        """
        expected = datetime.date(1998, 3, 30)
        actual = self.bcb_api.get_latest_date(253)

        self.assertEqual(expected, actual)

    def test_indices_with_multiple_records(self):
        """ get_latest_date() should return the date of the latest record."""
        expected = datetime.date(1991, 2, 5)
        actual = self.bcb_api.get_latest_date(226)

        self.assertEqual(expected, actual)


class TestSetIndicesRecords(unittest.TestCase):
    """ Class to test the set_indices_records() method from the
    FinancialIndicesApi class.
    """

    def setUp(self) -> None:
        """ Instantiate FinancialIndicesApi for each test."""
        arguments = {
            7478: (None, None),
            433: (None, datetime.date(1989, 9, 29)),
            11: (datetime.date(2017, 5, 14), None),
            12: (datetime.date(2010, 1, 1), datetime.date(2011, 1, 1)),
            226: (datetime.date(1999, 12, 15), datetime.date(2000, 3, 5)),
            # 253: (datetime.date(), datetime.date()),
        }
        self.bcb_api = FinancialIndicesApi()
        self.bcb_api.set_indices_records(arguments)

    def test_start_date_end_date_as_none(self):
        """ Test both the first and last date from the ipca-15 indices, when
        both dates are None, and all available results are retrieved.
        """
        today = datetime.date.today()
        expected = (datetime.date(2000, 5, 1), True)
        actual = (self.bcb_api._indices_records[7478][0].date,
                  self.bcb_api._indices_records[7478][-1].date <= today,
                  )

        self.assertEqual(expected, actual)

    def test_start_date_as_none(self):
        """ Test the first date from ipca indices as None."""
        today = datetime.date.today()
        expected = (datetime.date(1980, 1, 1), True)
        actual = (self.bcb_api._indices_records[433][0].date,
                  self.bcb_api._indices_records[433][-1].date <= today,
                  )

        self.assertEqual(expected, actual)

    def test_end_date_as_none(self):
        """ When both dates are None, the end_date receives internally the
        value of today. Therefore, the api will NOT query all results since
        both dates are valid. The first_record should respect the start_date.
        """
        today = datetime.date.today()
        expected = (datetime.date(2017, 5, 15), True)
        actual = (self.bcb_api._indices_records[11][0].date,
                  self.bcb_api._indices_records[11][-1].date <= today,
                  )

        self.assertEqual(expected, actual)

    def test_valid_dates_two_field(self):
        """ The first record should be higher than the first date, and the last
        record should be lower to the last date provided.
        """
        expected = (datetime.date(2010, 1, 4), datetime.date(2010, 12, 31))
        actual = (self.bcb_api._indices_records[12][0].date,
                  self.bcb_api._indices_records[12][-1].date,
                  )

        self.assertEqual(expected, actual)

    def test_valid_dates_three_field(self):
        """ Both first and last record should have date values equal to the
        start and end_date.
        """
        expected = (datetime.date(1999, 12, 15), datetime.date(2000, 3, 5))
        actual = (self.bcb_api._indices_records[226][0].date,
                  self.bcb_api._indices_records[226][-1].date,
                  )

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
