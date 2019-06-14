from abc import (ABCMeta,
                 abstractmethod)
import datetime
import logging
import os
from types import MappingProxyType
from typing import (Collection,
                    Iterable,
                    Optional,
                    Tuple,
                    Union,
                    )

import openpyxl as xlsx

from bcb_api import (DAY_RECORD,
                     IndicesRecord,
                     RECORDS)


logger = logging.getLogger(__name__)


class WorksheetWriter(metaclass=ABCMeta):
    """ Class responsible for writing information in a Worksheet object."""

    def __init__(self, worksheet: 'openpyxl.worksheet.worksheet.Worksheet',
                 records: RECORDS):
        """
        :param worksheet:
        :param records:
        """

        self._worksheet = worksheet
        self._indices_records = records
        self._headers = self._get_headers()

        self._write_headers()
        self._write_records()

    def _get_headers(self) -> Tuple[Union[str, float]]:
        """ Return the name of the headers. Headers may be text or numbers.
        """

        return ('date', 'value',)

    @abstractmethod
    def _format_record(self, record: DAY_RECORD) -> Collection:
        """ Return a collection of values corresponding to a row of data."""
        pass

    def _write_headers(self) -> None:
        """ Write the self._headers values starting at row 1, column 1."""

        for column, header in enumerate(self._headers, 1):
            self._worksheet.cell(1, column).value = header

    def _write_records(self, first_row: int = 2) -> None:
        """ Write all dates and values from self._indices_records in
        self._worksheet, starting at the first_row, column 1.

        :param first_row: Row to start writing.
        :return: None.
        """

        for row, record in enumerate(self._indices_records, first_row):
            formatted_record = self._format_record(record)
            for column, column_data in enumerate(formatted_record, 1):
                self._worksheet.cell(row, column).value = column_data


class SelicWriter(WorksheetWriter):

    def _format_record(self, record: DAY_RECORD
                       ) -> Iterable[Union[float, datetime.date]]:
        """ Format a record to be appropriate to the worksheet selic.

        :param record: IndicesRecord.
        :return: Iterable of the values of record.
        """

        return record.date, record.value


class CdiWriter(WorksheetWriter):

    @staticmethod
    def _decimal_precision(value: float) -> int:
        """ Return an integer signifying how many decimal point are necessary
        to properly represent value.

        :param value: Any number.
        :return: Necessary decimal points to represent value.
        """

        precision = 0
        while not float.is_integer(value):
            value *= 10
            precision += 1

        return precision

    def _generate_percentage_range(self, start: float, end: float, step: float
                                   ) -> Tuple[float]:
        """ Return all values between start and end (both included), that can
        can be achieved with increments of step.

        Pre-Condition: (start + (step * number_steps)) == end

        :param start: Initial value.
        :param end: Last value.
        :param step: Increment step.
        :return: All values between start and end (included).
        """

        number_steps = (end - start) / step

        # If number_steps isn't an integer, than it's impossible for the
        # summation of start and steps to ever reach the end.
        if not float.is_integer(number_steps):
            raise ValueError(f'Wrong values for start: {start} end:{end} '
                             f'and step:{step}')
        else:
            number_steps = int(number_steps)

        decimal_points = self._decimal_precision(step)
        cdi_range = [start]
        for _ in range(number_steps):
            start = round(start + step, decimal_points)
            cdi_range.append(start)

        assert cdi_range[-1] == end

        return tuple(cdi_range)

    def _get_headers(self) -> Tuple[Union[str, float]]:
        """ Generate the headers for a CDI worksheet, with percentages
        ranging from 0.700 to 2.000, with increments of 0.001 (70% to 200%).

        :return: Tuple of values.
        """

        return super()._get_headers() + self._generate_percentage_range(
            0.7, 2.0, 0.001
        )

    def _format_record(self, record: DAY_RECORD
                       ) -> Iterable[Union[float, datetime.date]]:
        """ Format a record to be appropriate to the worksheet cdi.

        :param record: IndicesRecord.
        :return: Iterable of the values of record.
        """

        elements = [record.date, record.value]
        for percentage in self._headers[len(super()._get_headers()):]:
            elements.append(1 + round(record.value * percentage / 100, 8))

        return iter(elements)


class IpcaWriter(WorksheetWriter):

    def _get_headers(self) -> Tuple[Union[str, float]]:
        """ Return the name of the headers. Headers may be string or numbers.
        """

        return ('ano', 'mes', 'valor')

    def _format_record(self, record: DAY_RECORD
                       ) -> Iterable[Union[float, datetime.date]]:
        """ Format a record to be appropriate to the worksheet ipca.

        :param record: IndicesRecord.
        :return: Iterable of the values of record.
        """

        return record.date.year, record.date.month, record.value


class TrWriter(WorksheetWriter):

    def _get_headers(self) -> Tuple[Union[str, float]]:
        """ Return the name of the headers. Headers may be string or numbers.
        """

        return ('data inicial', 'data final', 'valor')

    def _format_record(self, record: DAY_RECORD) -> Collection:
        """ Format a record to be appropriate to the worksheet tr.

        :param record: IndicesRecord.
        :return: Iterable of the values of record.
        """

        return record.date, record.end_date, record.value


class IndicesWorkbook:
    """ Class to represent an excel Workbook."""

    _worksheet_properties = MappingProxyType(
        {
            11: {
                'name': 'selic',
                'color': '0000FF',  # blue
                'writer': SelicWriter,
            },
            12: {
                'name': 'cdi',
                'color': '00FF00',  # green
                'writer': CdiWriter,
            },
            433: {
                'name': 'ipca',
                'color': 'FFA500',  # orange
                'writer': IpcaWriter,
            },
            226: {
                'name': 'tr',
                'color': 'FF0000',  # red
                'writer': TrWriter,
            },
        },
    )

    def __init__(self, filepath: Optional[str] = None):
        """ Constructor of a workbook.
        If a filepath is given, that xlsx file is opened, otherwise, a file
        named 'financial_indices.xlsx' is created at the current directory.

        :param filepath: String of a valid 'financial_indices.xlsx' file.
        """

        if filepath is None:
            filename = 'financial_indices.xlsx'
            current_path = os.path.abspath(os.getcwd())
            self._workbook_path = os.path.join(current_path, filename)
            self._workbook = xlsx.Workbook()
            self._delete_all_sheets()
        else:
            self._workbook_path = filepath
            self._workbook = xlsx.load_workbook(self._workbook_path)

    def __len__(self):
        """ Return the number of worksheets inside self._workbook."""

        return len(self._workbook.sheetnames)

    def __repr__(self):
        return f'{self.__class__.__name__}({self._workbook_path})'

    def _delete_all_sheets(self) -> None:
        """ Delete all existing worksheets from self._workbook."""

        for sheet in self._workbook.sheetnames:
            del self._workbook[sheet]

    def _create_sheet(self, indices_code: int
                      ) -> 'openpyxl.worksheet.worksheet.Worksheet':
        """ Create and return a worksheet in self._workbook based on the
        indices_code value. If that indices_code worksheet already exist, it
        is simply returned.

        :param indices_code: Integer representing a financial indices.
        :return: Worksheet object.
        """

        name = self.__class__._worksheet_properties[indices_code]['name']
        if name in self._workbook.sheetnames:
            return self._workbook[name]

        color = self.__class__._worksheet_properties[indices_code]['color']

        ws = self._workbook.create_sheet(name)
        ws.title = name
        ws.sheet_properties.tabColor = color

        return ws

    def write_records(self, indices_code: int, records: RECORDS) -> None:
        """ Create or load a worksheet from self._workbook, corresponding to
        the indices_code provided, and pass both the worksheet and records
        to the correct WorksheetWriter (ex: CdiWriter).

        :param indices_code: Integer representing a financial indices.
        :param records: Records of a financial indices.
        :return: None.
        """

        try:
            ws = self._workbook[self.__class__._worksheet_properties[indices_code]['name']]
        except KeyError:
            ws = self._create_sheet(indices_code)

        writer = self.__class__._worksheet_properties[indices_code]['writer']

        writer(ws, records)

    def save(self) -> None:
        """ Save self._workbook at self._workbook_path."""

        self._workbook.save(self._workbook_path)
