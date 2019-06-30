import datetime
import logging
from typing import (List,
                    Iterator,
                    Tuple,
                    )

from bcb_api import (FinancialIndicesApi,
                     IndicesRecord,
                     INDICES_DATE_VALUES,
                     RECORDS,
                     )
from workdays import Workdays
import utils


logger = logging.getLogger('__main__.' + __name__)


@utils.singleton
class IndicesExpander:
    """ Dict like class, capable of expanding a financial indices
    RECORDS (see bcb_api) with extra DAY_RECORD objects, based on the
    financial indices type (11, 12, 433, etc...).

    Indices data is stored in private instance field
    '_expanded_indices_records'.
    """

    def __init__(self) -> None:
        """ Initializes instance of IndicesExpander."""

        self._expander_methods_mapping = {
            11: self._daily_workday_indices_expander,  # Selic
            12: self._daily_workday_indices_expander,  # CDI
            226: self._daily_three_field_indices_expander,  # TR
            433: self._ipca_from_15_expander,  # Expand ipca with IPCA-15
        }

        self._workdays = Workdays()
        self._expanded_indices_records: INDICES_DATE_VALUES = {}

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}()'

    def __len__(self) -> int:
        return len(self._expanded_indices_records)

    def __contains__(self, item) -> bool:
        return item in self._expanded_indices_records

    def __getitem__(self, item) -> RECORDS:
        return self._expanded_indices_records[item]

    def __iter__(self) -> Iterator:
        return iter(self._expanded_indices_records)

    def __getattr__(self, item):
        return getattr(self._expanded_indices_records, item)

    @staticmethod
    def get_next_month(month: int) -> int:
        """ Return the integer corresponding to the next month of the month
        provided.

        Precondition: 1 <= month <= 12

        :param month: Integer of a month (1-12).
        :return: The integer of the next month.
        """

        if not 1 <= month <= 12:
            raise ValueError(f'Invalid argument: month={month}')

        return (month + 1) % 12 or 12

    def is_same_date_month_ahead(self, date1: datetime.date, date2: datetime.date) -> bool:
        """ Return True if date2 is equal to date1, but exactly one month ahead,
        False otherwise.

        :param date1: Date.
        :param date2: Date.
        :return: True if date2 is month ahead of date1.
        """

        next_month = self.get_next_month(date1.month)
        next_year = date1.year if next_month != 1 else date1.year + 1
        try:
            new_date = datetime.date(year=next_year, month=next_month, day=date1.day)
        except ValueError:
            return False

        return new_date == date2

    def _get_next_days(self, start_date: datetime.date, end_date: datetime.date
                       ) -> Tuple[datetime.date, datetime.date]:
        """ Indices like TR (cod=226), have two days in a record, and a special
        rule to determine the next couple of days following them. This method
        is intended to receive those two dates, and return the next days.

        :param start_date: The 'date' attribute of a DAY_RECORD from financial
            code like 226.
        :param end_date: The 'end_date' attribute of the same DAY_RECORD.
        :return: Tuple of dates.
        """

        if start_date >= end_date:
            logger.warning(f'Invalid arguments: start_date={start_date} - '
                           f'end_date={end_date}')
            raise ValueError("end_date can't be lower or equal to start_date")

        log_start_date = start_date
        log_end_date = end_date

        one_day = datetime.timedelta(days=1)

        if self.is_same_date_month_ahead(start_date, end_date):
            start_date += one_day
            end_date += one_day
        elif start_date.day == 1:
            end_date += one_day
        elif end_date.day == 1:
            start_date += one_day
        else:
            logger.warning(f'Invalid arguments: start_date={start_date} - '
                           f'end_date={end_date}')
            raise ValueError('Inconsistent input dates')

        logger.debug(f'({log_start_date}, {log_end_date}) -> ({start_date}, {end_date})')

        return start_date, end_date

    def _daily_workday_indices_expander(self, financial_records: RECORDS
                                        ) -> List[IndicesRecord]:
        """ Return a list of IndicesRecord where the 'date' attribute of
        the first IndicesRecord instance is one workday ahead of the
        'date' of the last instance of financial_records.

        The 'value' attribute of the last instance of financial_records
        is repeated for the extra IndicesRecord's.

        :param financial_records: Sequence of IndicesRecord.
        :return: List of IndicesRecord.
        """

        if not financial_records:
            return []

        last_date = financial_records[-1].date
        value = financial_records[-1].value

        extra_workdays = self._workdays.get_extra_workdays(last_date)

        extra_records = [IndicesRecord({'date': day, 'value': value})
                         for day in extra_workdays]

        msg = f'Expanding {last_date} with: {[record.date for record in extra_records]}'
        logger.debug(msg)

        return financial_records + extra_records

    def _daily_three_field_indices_expander(self, financial_records: RECORDS
                                            ) -> List[IndicesRecord]:
        """ Return a list of IndicesRecord, where the 'date' attribute of the
        first IndicesRecord is one day ahead of the date of the last record
        from financial_records.

        The 'value' attribute of the last instance of financial_records is
        repeated for the extra IndicesRecord's.

        :param financial_records: Sequence of IndicesRecord.
        :return: List of IndicesRecord
        """

        if not financial_records:
            return []

        date = financial_records[-1].date
        end_date = financial_records[-1].end_date
        value = financial_records[-1].value

        extra_records = []
        for _ in range(30):
            date, end_date = self._get_next_days(date, end_date)
            record = IndicesRecord(
                {'date': date,
                 'end_date': end_date,
                 'value': value}
            )
            extra_records.append(record)

        msg = f'Expanding {date} with: {[(record.date, record.end_date) for record in extra_records]}'
        logger.debug(msg)

        return financial_records + extra_records

    def _ipca_from_15_expander(self, financial_records: RECORDS
                               ) -> List[IndicesRecord]:
        """ Return a list of IndicesRecord, where the last item is an extra
        record, with the ipca-15 from the next month.
        If ipca-15 is not available, the last record from the input list is
        duplicated, instead.

        :param financial_records: Sequence of IndicesRecord.
        :return: List of IndicesRecord
        """

        if not financial_records:
            return []

        last_date = financial_records[-1].date.replace(day=1)
        last_value = financial_records[-1].value
        next_month = self.get_next_month(last_date.month)
        next_year = last_date.year if next_month != 1 else last_date.year + 1
        new_date = last_date.replace(month=next_month, year=next_year)

        api = FinancialIndicesApi()
        api.set_indices_records({7478: (last_date, None)})

        try:
            if api[7478][0].date == last_date:
                record = [IndicesRecord({'date': new_date, 'value': api[7478][0].value})]
            else:
                raise IndexError
        except IndexError:
            record = [IndicesRecord({'date': new_date, 'value': last_value})]

        logger.debug(f'Expanding {last_date} with: {record}')

        return financial_records + record

    def set_expanded_indices(self, indices_code: int,
                             financial_records: RECORDS,
                             ) -> None:
        """ Expand and stores records based on the indices_code in
        self._expanded_indices_records.

        :param indices_code: Integer representing a financial indices from
            BCB's API.
        :param financial_records: Sequence of IndicesRecords to be expanded.
        :return: None.
        """

        logger.info(f'Expanding indices code {indices_code}')

        method = self._expander_methods_mapping[indices_code]

        self._expanded_indices_records[indices_code] = method(financial_records)
