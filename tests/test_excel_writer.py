import os
import sys
import unittest

path = os.path.dirname(__file__)
path = os.path.join(path, '..')
sys.path.append(os.path.abspath(os.path.join(path, 'financial_indices')))

from excel_writer import IndicesWorkbook


class TestNewIndicesWorkbook(unittest.TestCase):
    """ Class to test the class IndicesWorkbook, whose setUp test methods
    consists of creating a new, clean instance of IndicesWorkbook."""

    def setUp(self) -> None:
        """ Create an instance of IndicesWorkbook."""
        self.wb = IndicesWorkbook()

    def tearDown(self) -> None:
        """ Attempt to delete a financial_indices.xlsx file from the current
        working directory.
        """
        try:
            os.remove(self.wb._workbook_path)
        except FileNotFoundError:
            pass

    def test_initial_workbook_doesnt_have_sheets(self):
        """ When a new instance, without parameters is called, it should not
        have any worksheet inside of it.
        """

        self.assertEqual(len(self.wb), 0)

    def test_delete_all_sheets(self):
        """ When called, _delete_all_sheets() should delete all sheets."""

        for name in ('sheet1', 'sheet2'):
            self.wb._workbook.create_sheet(name)

        # Making sure two sheets were created.
        self.assertEqual(len(self.wb), 2)

        self.wb._delete_all_sheets()

        self.assertEqual(len(self.wb), 0)

    def test_create_sheets(self):
        """ _create_sheet() should create a worksheet based on integer values,
        representing a financial indices code.
        """

        for i, indices_code in enumerate(self.wb._worksheet_properties, 1):
            self.wb._create_sheet(indices_code)

            # check the number of worksheet and their names.
            self.assertEqual(len(self.wb), i)
            self.assertTrue(
                self.wb._worksheet_properties[indices_code]['name'] in self.wb._workbook.sheetnames
            )


class TestExistingIndicesWorkbook(unittest.TestCase):
    """ Class to test the class IndicesWorkbook, whose setUp test methods
    consists of both creating a new, and loading a pre-existing instance of
    IndicesWorkbook."""

    def setUp(self) -> None:
        """ Create an instance of IndicesWorkbook and save some data."""
        self.wb = IndicesWorkbook()

        self.wb._create_sheet(11)
        self.sheet = self.wb._workbook['selic']
        for row in range(1, 101):
            for column in range(1, 101):
                self.sheet.cell(row, column).value = row + column

    def tearDown(self) -> None:
        """ Attempt to delete a financial_indices.xlsx file from the current
        working directory.
        """
        try:
            os.remove(self.wb._workbook_path)
        except FileNotFoundError:
            pass

    def test_delete_all_sheets(self):
        """ When called, _delete_all_sheets() should delete all sheets."""
        # make sure self.wb has one sheet
        self.assertEqual(len(self.wb), 1)

        self.wb._delete_all_sheets()

        self.assertEqual(len(self.wb), 0)

    def test_create_sheet_overrides_existing_sheet(self):
        """ If _create_sheet() receives an integer of an already existing sheet,
        that sheet should be overwritten."""

        # Make sure the sheet has values.
        number_values = len(tuple(self.sheet.rows) + tuple(self.sheet.columns))

        self.assertTrue(number_values > 0)

        self.wb._create_sheet(11)
        self.sheet = self.wb._workbook['selic']
        expected = 0
        actual = len(tuple(self.sheet.rows) + tuple(self.sheet.columns))

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
