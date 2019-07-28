from bisect import bisect_left
import csv
import datetime
import logging
import os
from typing import (Any,
                    Iterator,
                    Optional,
                    Sequence,
                    Tuple,
                    )

import utils

logger = logging.getLogger('__main__.' + __name__)


@utils.singleton
class Workdays:
    """ CLass containing all Brazilian workdays from 2001 to 2078, both
    included.

    Responsible for generating and returning a tuple with extra workdays,
    based on a date and a number of extra days.
    """

    # Total number of workdays in Brazil from 2001 to 2078.
    _number_workdays = 19_593
    _filename = 'workdays.csv'

    def __init__(self, workdays_path: Optional[str] = None) -> None:
        """ Initializes instance of Workdays.

        :param workdays_path: Path to the folder containing the '_filename'.
        """
        if workdays_path is None:
            path = os.path.dirname(__file__)
            self._workdays_path = os.path.abspath(
                os.path.join(
                    path,
                    self.__class__._filename
                )
            )
        else:
            self._workdays_path = workdays_path

        self._workdays = self._load_workdays()

    def __repr__(self) -> str:
        return '{}("{}")'.format(self.__class__.__name__,
                                 self._workdays_path)

    def __len__(self) -> int:
        return self.__class__._number_workdays

    def __contains__(self, item) -> bool:
        return item in self._workdays

    def __getitem__(self, item) -> datetime.date:
        return self._workdays[item]

    def __iter__(self) -> Iterator:
        return iter(self._workdays)

    def _load_workdays(self) -> Tuple[datetime.date]:
        """ Load all workdays from self._workdays_path (should be a csv file)
        and return days as a tuple of datetime.date.

        :raise: AssertionError.
        :return: Tuple with all workdays available.
        """

        workdays_temp = []
        with open(self._workdays_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')

            # for each row, get the date, format it as datetime.date
            # and append it.
            for row in csv_reader:
                # each row comes as ['yyyy-mm-dd']
                string_date: str = row[0]
                date = datetime.datetime.strptime(string_date,
                                                  '%Y-%m-%d').date()
                workdays_temp.append(date)

        try:
            assert len(workdays_temp) == self.__class__._number_workdays
        except AssertionError:
            logger.exception(f'The number of workdays in '
                             f'{self.__class__._filename} is incorrect.')
            raise AssertionError

        logger.info(f'{self.__class__._number_workdays} Workdays loaded.')

        return tuple(workdays_temp)

    @staticmethod
    def binary_search(array: Sequence[Any], element: Any) -> int:
        """ Binary search algorithm, implemented using the built in bisect
        library.
        Raise LookupError if element is not in array.

        Pre-condition: array is sorted.

        :param array: Sorted sequence of elements.
        :param element: Element whose index is being searched.
        :raise: LookupError.
        :return: Index of element.
        """

        # binary search logic from python docs:
        # https://docs.python.org/3/library/bisect.html#module-bisect
        index = bisect_left(array, element)
        if index != len(array) and array[index] == element:
            return index

        raise LookupError(f'{element} is not in array')

    def get_extra_workdays(self, start_date: datetime.date,
                           extra_days: int = 30) -> Tuple[datetime.date]:
        """ Return a tuple of datetime.date objects of length equal to
        extra_days, where the first element is one workday after start_date.

        Raise LookupError if start_date is not a workday.

        :param start_date: Date being searched.
        :param extra_days: Integer representing the number of extra days.
        :raise: LookupError.
        :return: Tuple of datetime.date objects.
        """

        try:
            date_index = self.binary_search(self._workdays, start_date)
        except LookupError:
            logger.exception(f'{start_date} is not a valid workday between '
                             f'2001 and 2078')
            raise LookupError

        first_index = date_index + 1
        second_index = first_index + extra_days

        return self._workdays[first_index:second_index]
