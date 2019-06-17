from collections import namedtuple
import datetime
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
DAY_RECORD = Tuple[Union[datetime.date, float]]
RECORDS = Union[Sequence[DAY_RECORD], Sequence]
COD_DATE = Mapping[int, Tuple[Optional[datetime.date]]]
INDICES_DATE_VALUES = Dict[int, RECORDS]
RAW_JSON = Union[List[Dict[str, str]], List]

# Constant
TODAY = datetime.date.today().strftime('%d/%m/%Y')

logger = logging.getLogger()


class IndicesRecord:
    """ namedtuple class to represent a single financial indices
    record.
    """

    _attr_mapping = {
        'data': 'date',
        'datafim': 'end_date',
        'valor': 'value',
    }

    def __new__(cls, attr_value: Dict[str, Union[datetime.date, float]]
                ) -> Tuple[Union[datetime.date, float]]:

        mapped_attr_value = {}
        for key, value in sorted(attr_value.items()):
            try:
                new_key = cls._attr_mapping[key]
            except KeyError:
                mapped_attr_value[key] = value
            else:
                mapped_attr_value[new_key] = value

        return namedtuple('IndicesRecord', mapped_attr_value.keys()
                          )(*mapped_attr_value.values())


class FinancialIndicesApi:
    """ Dict like class, responsible for accessing, retrieving and storing
    financial indices data from Brazil Central Bank (BCB) API.

    Indices data are stored in private instance field '_indices_records', as
    a dict.

    '_indices_records' is filled by calling the method 'set_indices_records'.
    """

    _api_url: str = ('http://api.bcb.gov.br/dados/serie/bcdata.sgs.{'
                     'codigo_serie}/dados?formato=json&dataInicial={'
                     'dataInicial}&dataFinal={dataFinal}')

    def __init__(self, cod_start_date: COD_DATE = None) -> None:
        """ Initialize instance of FinancialIndicesApi."""

        self._arguments = {}
        self._indices_records: INDICES_DATE_VALUES = {}

    def __repr__(self) -> str:
        return ('{}({})'
                .format(self.__class__.__name__, self._arguments))

    def __len__(self) -> int:
        return len(self._indices_records)

    def __contains__(self, item) -> bool:
        return item in self._indices_records

    def __getitem__(self, item) -> RECORDS:
        return self._indices_records[item]

    def __iter__(self) -> Iterator:
        return iter(self._indices_records)

    def __getattr__(self, item):
        return getattr(self._indices_records, item)

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

        :param api_code: Integer representing a financial indices.
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
        """ Makes request to _api_url and return the result if no error
        occurred.

        :param api_url: String of the url that is requested.
        :return: Response of the request.
        :raise: requests.HTTPError.
        """

        response = requests.get(api_url)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.exception(f'Could not complete request to: \n{api_url}')
            raise e
        else:
            logger.debug(f'Successful request to: \n{api_url}')

        return response.json()

    def _fix_api_results(self, json_result: RAW_JSON) -> RECORDS:
        """ Each element from json_result (dict) is converted to an
        IndicesRecord object, with string values converted to either float
        or datetime.date objects.

        :param json_result: List of dict.
        :return: List of IndicesRecord objects.
        """

        # If json_result was empty, simply return it.
        if not json_result:
            return json_result

        values = []
        for dictionary in json_result:
            # Every api result dict should always have a 'valor' key, and it's
            # always a float.
            day_record_dict = {
                'valor': float(dictionary.pop('valor')),
            }
            # Other keys may have unknown names, but they should be date
            # objects.
            for key, value in dictionary.items():
                date = datetime.datetime.strptime(value, r'%d/%m/%Y').date()
                day_record_dict[key] = date

            day_record = IndicesRecord(day_record_dict)
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

    def get_latest_date(self, indices_code: int) -> Optional[datetime.date]:
        """ Return the date of the latest IndicesRecord record from
        self._indices_records[indices_code].

        Return None if self doesn't have records for the indices_code or
        if there is no record.

        :param indices_code: Integer representing a financial indices.
        :return: The last available date of the indices_code, or None
            if it can't be retrieved.
        """

        try:
            record = self._indices_records[indices_code][-1]
        except (KeyError, IndexError):
            return None
        else:
            return record.date

    def set_indices_records(self, cod_start_date: COD_DATE) -> None:
        """ Stores/update the value of self._indices_records with the
        json result (formatted with IndicesRecord) of a query made to
        the API.

        :param cod_start_date: Mapping of integer as keys, representing the
            financial indices, and a tuple of dates as values, representing the
            start and end date.
            If Both dates are valid, the instance will retrieve that indices
                (key) records respecting the dates range.
            If start_date (first date) if None, the result will include records
                from the first available date of that indices up to the end_data
                given.
            If end_date (second date) is None, the result will query all records
                from start_date up to datetime.date.today().
            If both dates are None, all available records from the indices are
                retrieved.
        """

        if cod_start_date is None:
            return

        self._arguments.update(cod_start_date)

        for cod, dates in cod_start_date.items():
            url = self._create_api_url(cod, *dates)
            json_response = self._get_json_results(url)
            indices_records = self._fix_api_results(json_response)

            self._indices_records[cod] = self._rm_records_outside_range(*dates,
                                                                        indices_records)
