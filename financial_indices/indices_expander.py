import logging

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

    def __iter__(self):
        return iter(self._expanded_indices_records)

    def __getattr__(self, item):
        return getattr(self._expanded_indices_records, item)
