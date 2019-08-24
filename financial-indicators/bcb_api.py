from collections import namedtuple
import datetime
import decimal
import logging
import requests
from typing import (Dict,
                    List,
                    Iterator,
                    Mapping,
                    Optional,
                    Sequence,
                    Tuple,
                    Union,
                    )

# Type aliases
DAY_RECORD = Tuple[Union[datetime.date, decimal.Decimal]]
RECORDS = Union[Sequence[DAY_RECORD], Sequence]
COD_DATE = Mapping[int, Tuple[Optional[datetime.date]]]
INDICATORS_DATE_VALUES = Dict[int, RECORDS]
RAW_JSON = Union[List[Dict[str, str]], List]

logger = logging.getLogger('__main__.' + __name__)


class IndicatorRecord:
    """ namedtuple class to represent a single financial indicator
    record.
    """

    _attr_mapping = {
        'data': 'date',
        'datafim': 'end_date',
        'valor': 'value',
    }

    def __new__(cls, attr_value: Dict[str, Union[datetime.date, decimal.Decimal]]
                ) -> Tuple[Union[datetime.date, decimal.Decimal]]:

        mapped_attr_value = {}
        for key, value in sorted(attr_value.items()):
            try:
                new_key = cls._attr_mapping[key]
            except KeyError:
                mapped_attr_value[key] = value
            else:
                mapped_attr_value[new_key] = value

        return namedtuple('IndicatorRecord', mapped_attr_value.keys()
                          )(*mapped_attr_value.values())


class FinancialIndicatorsApi:
    """ Dict like class, responsible for accessing, retrieving and storing
    financial indicators data from Brazil's Central Bank (BCB) API.

    indicator data are stored in private instance field '_indicators_records', as
    a dict.

    '_indicators_records' is filled by calling the method 'set_indicators_records'.
    """

    _api_url: str = ('http://api.bcb.gov.br/dados/serie/bcdata.sgs.{'
                     'codigo_serie}/dados?formato=json&dataInicial={'
                     'dataInicial}&dataFinal={dataFinal}')

    def __init__(self) -> None:
        """ Initialize instance of FinancialIndicatorsApi."""

        self._arguments = {}
        self._indicators_records: INDICATORS_DATE_VALUES = {}

    def __repr__(self) -> str:
        return ('{}({})'
                .format(self.__class__.__name__, self._arguments))

    def __len__(self) -> int:
        return len(self._indicators_records)

    def __contains__(self, item) -> bool:
        return item in self._indicators_records

    def __getitem__(self, item) -> RECORDS:
        return self._indicators_records[item]

    def __iter__(self) -> Iterator:
        return iter(self._indicators_records)

    def __getattr__(self, item):
        return getattr(self._indicators_records, item)

    def _create_api_url(self, api_code: int,
                        start_date: Optional[datetime.date] = None,
                        end_date: Optional[datetime.date] = None) -> str:
        """ Constructs the query api url, from self.__class__._api_url, by
        replacing the parameters 'codigo_serie', 'dataInicial' and 'dataFinal'
        with api_code, start_date and end_date, respectively.

        If end_date would be None, it's replaced by the value of today, instead.

        OBS: The api will actually query all results from the database, if any
        of the dates are invalid (None values or swapped dates, as example).
        The reason end_date receives a value when empty, is to possibly limit
        the query in case start_date was provided.

        :param api_code: Integer representing a financial indicator.
        :param start_date: The initial date to query for the financial records.
        :param end_date: The last date to query.
        :return: String to be used in a query to the API.
        """

        if end_date is None:
            end_date = datetime.date.today()

        if isinstance(start_date, datetime.date):
            if start_date > end_date:
                raise ValueError('start_date can\'t be higher than the end_date.')

            start_date = start_date.strftime('%d/%m/%Y')

        end_date = end_date.strftime('%d/%m/%Y')

        return self.__class__._api_url.format(codigo_serie=api_code,
                                              dataInicial=start_date,
                                              dataFinal=end_date,
                                              )

    def _get_json_results(self, api_url: str) -> RAW_JSON:
        """ Makes request to api_url and return the result if no error
        occurred.

        :param api_url: String of the url that is requested.
        :raise: requests.HTTPError.
        :return: Response of the request.
        """

        response = requests.get(api_url)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.exception(f'Request error from: \n{api_url}')
            raise e
        else:
            logger.debug(f'Request successful from: \n{api_url}')

        return response.json()

    def _fix_api_results(self, json_result: RAW_JSON) -> RECORDS:
        """ Each element from json_result (dict) is converted to an
        IndicatorRecord object, which stores the numeric values as a Decimal,
        and dates as datetime.date objects.

        :param json_result: List of dict.
        :return: List of IndicatorRecord objects.
        """

        # If json_result was empty, simply return it.
        if not json_result:
            return json_result

        values = []
        for dictionary in json_result:
            # Every api result dict should always have a 'valor' key,
            # and it's always a Decimal.
            day_record_dict = {
                'valor': decimal.Decimal(dictionary.pop('valor')),
            }
            # Other keys may have unknown names, but they should be date
            # objects.
            for key, value in dictionary.items():
                date = datetime.datetime.strptime(value, r'%d/%m/%Y').date()
                day_record_dict[key] = date

            day_record = IndicatorRecord(day_record_dict)
            values.append(day_record)

        return values

    def _rm_records_outside_range(self, start_date: Optional[datetime.date],
                                  end_date: Optional[datetime.date],
                                  records_array: RECORDS) -> RECORDS:
        """ Return a new array with all records from records_array, whose date
        are either lower than the start_date, or higher than the end_date,
        removed.

        :param start_date: Initial date.
        :param end_date: Final date.
        :param records_array: Sequence of DAY_RECORDS.
        :return: New sequence of DAY_RECORDS.
        """

        new_records_array = []

        # The BCB's API result may have (oddly) instances whose date is
        # actually lower than the initial date provided to the api url
        # (parameter 'dataInicial').
        if isinstance(start_date, datetime.date):
            for index_, record in enumerate(records_array, 0):
                if record.date >= start_date:
                    new_records_array.extend(records_array[index_:])
                    break
        else:
            new_records_array = records_array[:]

        if isinstance(end_date, datetime.date):
            for record in new_records_array[::-1]:
                if record.date > end_date:
                    new_records_array.pop()
                else:
                    break

        return new_records_array

    def get_latest_date(self, indicator_code: int) -> Optional[datetime.date]:
        """ Return the date of the latest IndicatorRecord from
        self._indicators_records[indicator_code].

        Return None if self doesn't have records for the indicator_code or
        if there is no record.

        :param indicator_code: Integer representing a financial indicator.
        :return: The last available date of the indicator_code, or None
            if it can't be retrieved.
        """

        try:
            record = self._indicators_records[indicator_code][-1]
        except (KeyError, IndexError):
            return None
        else:
            return record.date

    def set_indicators_records(self, cod_start_date: COD_DATE) -> None:
        """ Stores/update the value of self._indicators_records with the
        json result (formatted with IndicatorRecord) of a query made to
        the API.

        :param cod_start_date: Mapping of integer as keys, representing the
            financial indicator, and a tuple of dates as values, representing the
            start and end date.
            If Both dates are valid, the instance will retrieve that indicator
                (key) records respecting the dates range.
            If start_date (first date) if None, the result will include records
                from the first available date of that indicator up to the end_data
                given.
            If end_date (second date) is None, the result will query all records
                from start_date up to datetime.date.today().
            If both dates are None, all available records from the indicator are
                retrieved.
        """

        logger.info(f'api request on: {cod_start_date}')

        if cod_start_date is None:
            return

        self._arguments.update(cod_start_date)

        for cod, dates in cod_start_date.items():
            url = self._create_api_url(cod, *dates)
            json_response = self._get_json_results(url)
            indicators_records = self._fix_api_results(json_response)

            self._indicators_records[cod] = self._rm_records_outside_range(
                *dates,
                indicators_records)
