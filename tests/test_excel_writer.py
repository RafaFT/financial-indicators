import os
import sys
import unittest

path = os.path.dirname(__file__)
path = os.path.join(path, '..')
sys.path.append(os.path.abspath(os.path.join(path, 'financial-indicators')))

from excel_writer import IndicatorsWorkbook


CURRENT_FOLDER = os.path.dirname(__file__)


class TestNewIndicatorsWorkbook(unittest.TestCase):
    """ Class to test the class IndicatorsWorkbook, whose setUp test methods
    consists of creating a new, clean instance of IndicatorsWorkbook."""

    def setUp(self) -> None:
        """ Create an instance of IndicatorsWorkbook."""
        # An initial instance of IndicatorsWorkbook should have a workbook
        # field with one worksheet ('metadata').
        self.wb = IndicatorsWorkbook(path_to_file=CURRENT_FOLDER,
                                  filename='testing.xlsx')

    def tearDown(self) -> None:
        """ Attempt to delete a financial_indicators.xlsx file from the current
        working directory.
        """
        try:
            os.remove(self.wb._workbook_path)
        except FileNotFoundError:
            pass

    def test_initial_workbook_has_one_sheet(self):
        """ When a new instance, without parameters is called, it should
        have a lonely worksheet named 'metadata' inside of it."""

        self.assertEqual(len(self.wb), 1)
        self.assertTrue(self.wb._workbook.sheetnames[0] == 'metadata')

    def test_delete_all_sheets(self):
        """ When called, _delete_all_sheets() should delete all sheets."""

        for name in ('sheet1', 'sheet2'):
            self.wb._workbook.create_sheet(name)

        # Making sure two sheets were created.
        self.assertEqual(len(self.wb), 3)

        self.wb._delete_all_sheets()

        self.assertEqual(len(self.wb), 0)

    def test_create_sheets(self):
        """ _create_sheet() should create a worksheet based on integer
        values, representing a financial indicator code.
        """

        # Delete existing metadata worksheet before this test.
        self.wb._delete_all_sheets()
        self.assertEqual(len(self.wb), 0)

        for i, indicator_code in enumerate(self.wb._worksheet_properties, 1):
            self.wb._create_sheet(indicator_code)

            # check the number of worksheet and their names.
            self.assertEqual(len(self.wb), i)
            self.assertTrue(
                self.wb._worksheet_properties[indicator_code]['name']
                in self.wb._workbook.sheetnames
            )


class TestExistingIndicatorsWorkbook(unittest.TestCase):
    """ Class to test the class IndicatorsWorkbook, whose setUp test methods
    consists of both creating a new, and loading a pre-existing instance of
    IndicatorsWorkbook."""

    def setUp(self) -> None:
        """ Create an instance of IndicatorsWorkbook and save some data."""
        # An initial instance of IndicatorsWorkbook should have a workbook
        # field with one worksheet ('metadata').
        self.wb = IndicatorsWorkbook(path_to_file=CURRENT_FOLDER,
                                     filename='testing.xlsx')

        self.ws = self.wb._create_sheet(11)
        for row in range(1, 101):
            for column in range(1, 101):
                self.ws.cell(row, column).value = row + column

    def tearDown(self) -> None:
        """ Attempt to delete a financial_indicators.xlsx file from the current
        working directory.
        """
        try:
            os.remove(self.wb._workbook_path)
        except FileNotFoundError:
            pass

    def test_delete_all_sheets(self):
        """ When called, _delete_all_sheets() should delete all sheets."""
        # self.wb should have two sheets at this moment. The sheet created
        # from setUp() and the metadata sheet.
        self.assertEqual(len(self.wb), 2)

        self.wb._delete_all_sheets()

        self.assertEqual(len(self.wb), 0)

    def test_create_sheet_return_same_existing_sheet(self):
        """ If _create_sheet() receives an integer of an already existing sheet,
        that existing sheet should be returned."""

        expected = id(self.ws)

        # Try to create new sheet with the same name.
        self.ws = self.wb._create_sheet(11)
        actual = id(self.ws)

        self.assertEqual(expected, actual)

    def test_create_sheet_holds_same_existing_values(self):
        """ If _create_sheet() receives an integer of an already existing sheet,
        that existing sheet should be returned."""

        # Store the existing values inside ws.
        expected = tuple(self.ws.rows) + tuple(self.ws.columns)

        # try to create new sheet with the same name.
        self.ws = self.wb._create_sheet(11)
        actual = tuple(self.ws.rows) + tuple(self.ws.columns)

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
