import datetime
import logging
from typing import (List,
                    Tuple,
                    )

from bcb_api import (FinancialIndicatorsApi,
                     IndicatorRecord,
                     RECORDS,
                     )
from workdays import Workdays
import utils


logger = logging.getLogger('__main__.' + __name__)


@utils.singleton
class IndicatorExpander:
    """ Class capable of expanding a financial indicator
    RECORDS (see bcb_api) with extra DAY_RECORD objects, based on the
    financial indicator code (11, 12, 433, etc...).
    """

    def __init__(self) -> None:
        """ Initializes instance of IndicatorExpander."""

        self._expander_methods_mapping = {
            11: self._daily_workday_indicator_expander,  # Selic
            12: self._daily_workday_indicator_expander,  # CDI
            226: self._daily_three_field_indicator_expander,  # TR
            433: self._ipca_from_15_expander,  # Expand ipca with IPCA-15
        }

        self._workdays = Workdays()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}()'

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
        """ Indicator like TR (cod=226), have two days in a record, and a special
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

    def _daily_workday_indicator_expander(self, financial_records: RECORDS
                                          ) -> List[IndicatorRecord]:
        """ Return a list of IndicatorRecord where the 'date' attribute of
        the first IndicatorRecord instance is one workday ahead of the
        'date' of the last instance of financial_records.

        The 'value' attribute of the last instance of financial_records
        is repeated for the extra IndicatorRecord's.

        :param financial_records: Sequence of IndicatorRecord.
        :return: List of IndicatorRecord.
        """

        if not financial_records:
            return []

        last_date = financial_records[-1].date
        value = financial_records[-1].value

        extra_workdays = self._workdays.get_extra_workdays(last_date)

        extra_records = [IndicatorRecord({'date': day, 'value': value})
                         for day in extra_workdays]

        msg = f'Expanding {last_date} with: {[record.date for record in extra_records]}'
        logger.debug(msg)

        return financial_records + extra_records

    def _daily_three_field_indicator_expander(self, financial_records: RECORDS
                                              ) -> List[IndicatorRecord]:
        """ Return a list of IndicatorRecord, where the 'date' attribute of the
        first IndicatorRecord is one day ahead of the date of the last record
        from financial_records.

        The 'value' attribute of the last instance of financial_records is
        repeated for the extra IndicatorRecord's.

        :param financial_records: Sequence of IndicatorRecord.
        :return: List of IndicatorRecord
        """

        if not financial_records:
            return []

        date = financial_records[-1].date
        end_date = financial_records[-1].end_date
        value = financial_records[-1].value

        extra_records = []
        for _ in range(30):
            date, end_date = self._get_next_days(date, end_date)
            record = IndicatorRecord(
                {'date': date,
                 'end_date': end_date,
                 'value': value}
            )
            extra_records.append(record)

        msg = f'Expanding {date} with: {[(record.date, record.end_date) for record in extra_records]}'
        logger.debug(msg)

        return financial_records + extra_records

    def _ipca_from_15_expander(self, financial_records: RECORDS
                               ) -> List[IndicatorRecord]:
        """ Return a list of IndicatorRecord, where the last item is an extra
        record, with the ipca-15 from the next month.
        If ipca-15 is not available, the last record from the input list is
        duplicated, instead.

        :param financial_records: Sequence of IndicatorRecord.
        :return: List of IndicatorRecord
        """

        if not financial_records:
            return []

        last_date = financial_records[-1].date.replace(day=1)
        last_value = financial_records[-1].value
        next_month = self.get_next_month(last_date.month)
        next_year = last_date.year if next_month != 1 else last_date.year + 1
        new_date = last_date.replace(month=next_month, year=next_year)

        api = FinancialIndicatorsApi()
        api.set_indicators_records({7478: (last_date, None)})

        try:
            if api[7478][0].date == last_date:
                record = [IndicatorRecord({'date': new_date, 'value': api[7478][0].value})]
            else:
                raise IndexError
        except IndexError:
            record = [IndicatorRecord({'date': new_date, 'value': last_value})]

        logger.debug(f'Expanding {last_date} with: {record}')

        return financial_records + record

    def get_expanded_indicators(self, indicator_code: int,
                                financial_records: RECORDS,
                                ) -> RECORDS:
        """ Expand financial_records based on it's indicator_code and return
        the result.

        :param indicator_code: Integer representing a financial indicator from
            BCB's API.
        :param financial_records: Sequence of IndicatorRecord's to be expanded.
        :return: Sequence of expanded IndicatorRecord's.
        """

        logger.info(f'Expanding indicador code {indicator_code}')

        method = self._expander_methods_mapping[indicator_code]

        return method(financial_records)
