import datetime
import logging
from typing import (List,
                    Iterator,
                    Tuple,
                    )

from bcb_api import (IndicesRecord,
                     INDICES_DATE_VALUES,
                     RECORDS,
                     )
from workdays import Workdays


logger = logging.getLogger(__name__)


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
            433: self._ipca_from_15_expander,  # IPCA
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

    def _get_next_days(self, start_date: datetime.date, end_date: datetime.date
                       ) -> Tuple[datetime.date, datetime.date]:
        """ Return the corresponding next couple of dates (date and end_date)
        according to the rules followed by financial indices with two dates,
        such as 226.

        :param start_date:
        :param end_date:
        :return:
        """

        if start_date >= end_date:
            raise ValueError("end_date can't be lower or equal to start_date")

        increment = datetime.timedelta(days=1)

        if start_date.day == end_date.day:
            start_date += increment
            end_date += increment
        elif start_date.day == 1:
            end_date += increment
        elif end_date.day == 1:
            start_date += increment
        else:
            raise ValueError('Invalid input values')

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

        return financial_records + extra_records

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

        method = self._expander_methods_mapping[indices_code]

        self._expanded_indices_records[indices_code] = method(financial_records)
