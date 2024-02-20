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
        self.assertEqual(self.sc.match('gas station', 'tank car #1'),
                         ('Exp:Car:Volvo', 'Assets:Bank'))
        self.assertEqual(self.sc.match('GAS station', 'tank CAR #1'),
                         ('Exp:Car:Volvo', 'Assets:Bank'))
        self.assertEqual(self.sc.match('Gas Station', 'Tank Car #2'),
                         ('Exp:Car:Saab', 'Assets:Bank'))

    def test_match_payee_only(self):
        self.assertEqual(self.sc.match('gas station', None),
                         ('Exp:Car', 'Assets:FIXME-NO-DESC'))



if __name__ == '__main__':
    unittest.main()
