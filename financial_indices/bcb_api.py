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
COD_DATE = Optional[Mapping[int, Optional[datetime.date]]]
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
    """ Dict like class, capable of accessing, retrieving, storing and
    updating financial indices data from Brazil Central Bank (BCB) API.

    Indices data are stored in private instance field '_indices_records'.

    The '_indices_records' may be filled when instantiating the class, or
    by calling the method 'set_indices_records()', with the desired parameter.
    """

    _api_url: str = ('http://api.bcb.gov.br/dados/serie/bcdata.sgs.{'
                     'codigo_serie}/dados?formato=json&dataInicial={'
                     'dataInicial}&dataFinal={dataFinal}')

    def __init__(self, cod_start_date: COD_DATE = None) -> None:
        """ Initialize instance of FinancialIndicesApi.

        :param cod_start_date: Mapping of integer as keys, representing the
            financial indices, and a date as value, representing the initial
            date.
            If key and value are valid, the instance will retrieve that
                indices (key) records starting from the date given.
            If key is valid but it's value is None, this instance will retrieve
                that indices from the first date available on the API.
            If None, initializes instance with no indices records.
        """
        self._arguments: COD_DATE = cod_start_date

        self._indices_records: INDICES_DATE_VALUES = {}
        self.set_indices_records(cod_start_date)

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
                        start_date: Optional[datetime.date] = None) -> str:
        """ Return a new '_api_url' that queries for the indices
        equal to the api_code, starting from the start_date.

        If start_date is None, the search begins from the first available
        date for that api_code.

        dataFinal parameter from the _api_url is always equal to
        datetime.date.today().date().

        :param api_code: Integer representing a financial indices.
        :param start_date: The initial date to query for the financial records.
        :return: String to be used in a query to the API.
        """

        if start_date is not None:
            start_date = start_date.strftime('%d/%m/%Y')

        return self.__class__._api_url.format(codigo_serie=api_code,
                                              dataInicial=start_date,
                                              dataFinal=TODAY,
                                              )

    def _get_json_results(self, api_url: str) -> RAW_JSON:
        """ Makes request to _api_url and return the result if no error
        occurred.

        :param api_url: String of the url that is requested.
        :return: Response of the requests.
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

    def _fix_json_types(self, json_result: RAW_JSON
                        ) -> RECORDS:
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
            # Every api result dict should always have a 'valor' key, and
            # it's always a float.
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

    def _remove_wrong_records(self) -> None:
        """ Remove all IndicesRecord's from self._indices_records values
        whose date is either equal or lower than the date in the corresponding
        self._arguments.

        :return: None
        """

        # The BCB's API result may have (oddly) instances whose date is
        # actually lower than the initial date provided to the api url
        # (parameter 'dataInicial').
        for indices_code in self._indices_records:
            requested_date = self._arguments[indices_code]
            # requested_date may be None if the query wanted all records of
            # a financial indices (see set_indices_records() or __init__()).
            if requested_date is None:
                continue
            for index, record in enumerate(self._indices_records[indices_code]):
                if record.date > requested_date:
                    self._indices_records[indices_code] = (
                        self._indices_records[indices_code][index:])
                    break
            else:
                self._indices_records[indices_code] = []

    def _get_latest_date(self, indices_code: int) -> Optional[datetime.date]:
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

    def set_indices_records(self, cod_start_date_: COD_DATE) -> None:
        """ Stores/update the value of self._indices_records with the
        json result (formatted with IndicesRecord) of a query made to
        the API.

        :param cod_start_date_: Mapping of integer as keys, representing the
            financial indices, and a date as value, representing the initial
            date.
            If key and value are valid, the instance will retrieve that
                indices (key) records starting from the date given.
            If key is valid but it's value is None, this instance will retrieve
                that indices from the first date available on the API.
            If None, initializes instance with no indices records.
        """

        if cod_start_date_ is None:
            return

        self._arguments.update(cod_start_date_)

        for cod, date in cod_start_date_.items():
            url = self._create_api_url(cod, date)
            json_response = self._get_json_results(url)
            indices_records = self._fix_json_types(json_response)

            self._indices_records[cod] = indices_records

        self._remove_wrong_records()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    scraper = FinancialIndicesApi({433: datetime.date(2019, 1, 29),
                                   12: datetime.date(2019, 4, 5)})

    import pprint
    pprint.pprint(scraper._indices_records)
