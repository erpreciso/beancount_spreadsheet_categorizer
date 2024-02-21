import sys
import os
import pdb
import inspect
import unittest

try:
    test_path = os.path.dirname(__file__)
except NameError:
    test_path = os.path.dirname(inspect.stack()[0][1])

# pdb.set_trace()
parent = os.path.abspath(os.path.join(test_path, os.pardir))
sys.path.append(parent)


class TestMatches(unittest.TestCase):
    def setUp(self):
        spreadsheet_path = os.path.join(test_path, "categorizer.ods")
        sheet_name = "Sheet1"
        from spreadsheet_categorizer import SpreadsheetCategorizer as SC
        self.sc = SC(spreadsheet_path, sheet_name)

    def test_match_payee_desc_case_insensitive(self):
        """Validate that match is case insensitive."""
        self.assertEqual(self.sc.match('gas station', 'tank car #1'),
                         ('Exp:Car:Volvo', 'Assets:Bank'))
        self.assertEqual(self.sc.match('GAS station', 'tank CAR #1'),
                         ('Exp:Car:Volvo', 'Assets:Bank'))
        self.assertEqual(self.sc.match('Gas Station', 'Tank Car #2'),
                         ('Exp:Car:Saab', 'Assets:Bank'))

    def test_match_payee_only(self):
        """Match payee, without description."""
        self.assertEqual(self.sc.match('gas station', None),
                         ('Exp:Car', 'Assets:FIXME-NO-DESC'))
        self.assertEqual(self.sc.match('gas station', ''),
                         ('Exp:Car', 'Assets:FIXME-NO-DESC'))

    def test_match_desc_only(self):
        self.assertEqual(self.sc.match(None, 't-shirt'),
                         ('Exp:Clothes', None))
        self.assertEqual(self.sc.match('', 't-shirt'),
                         ('Exp:Clothes', None))
        self.assertEqual(self.sc.match('', 'shirt'),
                         ('Exp:Clothes', None))
        self.assertEqual(self.sc.match('', 'pants'),
                         ('Exp:CATCH-ALL', 'Assets:CATCH-ALL'))

    def test_match_punctuation(self):
        self.assertEqual(self.sc.match('A.B.C.', 'service'),
                         ('Exp:Software', 'Assets:Cash'))

    def test_match_ambiguous_description(self):
        self.assertEqual(self.sc.match('gas station', 'tank car'),
                         ('Exp:Car', 'Assets:FIXME-NO-DESC'))

    def test_match_ambiguous_payee_and_desc(self):
        self.assertEqual(self.sc.match('gas', 'tank'),
                         ('Exp:CATCH-ALL', 'Assets:CATCH-ALL'))

    def test_match_catchalls(self):
        self.assertEqual(self.sc.match('a.b.c.', 'software'),
                         ('Exp:CATCH-ALL', 'Assets:CATCH-ALL'))



if __name__ == '__main__':
    unittest.main()
