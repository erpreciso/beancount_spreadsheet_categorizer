import sys
import os
import pdb
import inspect
import unittest
import logging

try:
    test_path = os.path.dirname(__file__)
except NameError:
    test_path = os.path.dirname(inspect.stack()[0][1])

# pdb.set_trace()
parent = os.path.abspath(os.path.join(test_path, os.pardir))
sys.path.append(parent)


class TestMatchesCommon(unittest.TestCase):
    spreadsheet_path = os.path.join(test_path, "test-categorizer.ods")
    import spreadsheet_categorizer as sc


class TestMatchesInvalidSpreadsheet(TestMatchesCommon):

    def test_load_spreadsheet_conflicting_cases(self):
        sheet_name = "invalid-1"
        with self.assertRaises(self.sc.SpreadsheetImportError):
            sc_class = self.sc.SpreadsheetCategorizer
            self.sc1 = sc_class(self.spreadsheet_path, sheet_name,
                                log_level=logging.WARNING)

    def test_load_spreadsheet_duplicate_payee(self):
        sheet_name = "invalid-2"
        with self.assertRaises(self.sc.SpreadsheetImportError):
            sc_class = self.sc.SpreadsheetCategorizer
            self.sc1 = sc_class(self.spreadsheet_path, sheet_name,
                                log_level=logging.WARNING)


class TestMatchesValidSpreadsheet(TestMatchesCommon):
    def setUp(self):
        sheet_name = "valid"
        self.sc1 = self.sc.SpreadsheetCategorizer(self.spreadsheet_path,
                                                  sheet_name,
                                                  log_level=logging.WARNING)

    def test_match_payee_desc_case_insensitive(self):
        """Validate that match is case insensitive."""
        self.assertEqual(self.sc1.match('gas station', 'tank car #1'),
                         ('Exp:Car:Volvo', 'Assets:Bank'))
        self.assertEqual(self.sc1.match('GAS station', 'tank CAR #1'),
                         ('Exp:Car:Volvo', 'Assets:Bank'))
        self.assertEqual(self.sc1.match('Gas Station', 'Tank Car #2'),
                         ('Exp:Car:Saab', 'Assets:Bank'))

    def test_match_payee_only(self):
        """Match payee, without description."""
        self.assertEqual(self.sc1.match('gas station', None),
                         ('Exp:Car', 'Assets:FIXME-NO-DESC'))
        self.assertEqual(self.sc1.match('gas station', ''),
                         ('Exp:Car', 'Assets:FIXME-NO-DESC'))

    def test_match_desc_only(self):
        self.assertEqual(self.sc1.match(None, 't-shirt'),
                         ('Exp:Clothes', None))
        self.assertEqual(self.sc1.match('', 't-shirt'),
                         ('Exp:Clothes', None))
        self.assertEqual(self.sc1.match('', 'shirt'),
                         ('Exp:Clothes', None))
        self.assertEqual(self.sc1.match('', 'pants'),
                         ('Exp:CATCH-ALL', 'Assets:CATCH-ALL'))

    def test_match_punctuation(self):
        self.assertEqual(self.sc1.match('A.B.C.', 'service'),
                         ('Exp:Software', 'Assets:Cash'))

    def test_match_ambiguous_description(self):
        self.assertEqual(self.sc1.match('gas station', 'tank car'),
                         ('Exp:Car', 'Assets:FIXME-NO-DESC'))

    def test_match_ambiguous_payee(self):
        self.assertEqual(self.sc1.match('gas stat', 'tank car #1'),
                         ('Exp:Car:Porsche', 'Assets:Bank'))

    def test_match_ambiguous_payee_and_desc(self):
        self.assertEqual(self.sc1.match('gas', 'tank'),
                         ('Exp:CATCH-ALL', 'Assets:CATCH-ALL'))

    def test_match_catchalls(self):
        self.assertEqual(self.sc1.match('a.b.c.', 'software'),
                         ('Exp:CATCH-ALL', 'Assets:CATCH-ALL'))


if __name__ == '__main__':
    unittest.main()
