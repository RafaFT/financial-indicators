import os
from types import MappingProxyType
from typing import (Optional,
                    )


import openpyxl as xlsx


class IndicesWorkbook:
    """ Class to represent an excel Workbook."""

    _worksheet_properties = MappingProxyType(
        {
            11: {
                'name': 'selic',
                'color': '0000FF',  # blue
            },
            12: {
                'name': 'cdi',
                'color': '00FF00',  # green
            },
            433: {
                'name': 'ipca',
                'color': 'FFA500',  # orange
            },
            226: {
                'name': 'tr',
                'color': 'FF0000',  # red
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

    def _create_sheet(self, indices_code: int) -> None:
        """ Create a worksheet in self._workbook based on the indices_code
        value. If a worksheet already exists for that indices_code, it is
        overwritten.

        :param indices_code: Integer representing a financial indices.
        """

        name = self.__class__._worksheet_properties[indices_code]['name']
        if name in self._workbook.sheetnames:
            del self._workbook[name]

        color = self.__class__._worksheet_properties[indices_code]['color']

        ws = self._workbook.create_sheet(name)
        ws.title = name
        ws.sheet_properties.tabColor = color

    def save(self) -> None:
        """ Save self._workbook at self._workbook_path."""

        self._workbook.save(self._workbook_path)
