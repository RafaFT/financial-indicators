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
