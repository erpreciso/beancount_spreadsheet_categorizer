# -*- coding: utf-8 -*-
import re
import pandas as pd
import logging
import pprint
import pdb


logging.basicConfig(format='%(levelname)s:%(message)s')
lg = logging.getLogger("lg")
lg.setLevel(logging.INFO)


class SpreadsheetCategorizer():
    def __init__(self, spreadsheet_path, sheet_name):
        self.create_categorizer(spreadsheet_path, sheet_name)

    def create_categorizer(self, spreadsheet_path, sheet_name):
        "Parse spreadsheet and create categorizer dicts."
        lg.debug('Created categorizer with file: {}'.format(spreadsheet_path))
        df = pd.read_excel(spreadsheet_path, engine='odf',
                           sheet_name=sheet_name)
        self.payee_desc_dct, self.payee_dct, self.desc_dct = {}, {}, {}
        assert set(df.columns) == {'account-destination',
                                   'payee',
                                   'account-source',
                                   'description'}

        def _read_line(line):
            payee, desc = line['payee'], line['description']
            acc_source, acc_dest = line['account-source'], \
                line['account-destination']
            if not pd.isnull(acc_source):
                if not pd.isnull(payee) and not pd.isnull(desc):
                    keypd = "|".join([payee, desc])
                    self.payee_desc_dct[keypd] = {'payee': str(payee),
                                                  'desc': desc,
                                                  'acc_source': acc_source,
                                                  'acc_dest': acc_dest}
                elif not pd.isnull(payee):
                    self.payee_dct[str(payee)] = {'acc_source': acc_source,
                                                  'acc_dest': acc_dest}
                elif not pd.isnull(desc):
                    self.desc_dct[desc] = {'acc_source': acc_source,
                                           'acc_dest': acc_dest}
        df.apply(_read_line, axis=1)

    def match(self, p, d):
        "Match P and D with dict"
        for keypd in self.payee_desc_dct:
            payee = self.payee_desc_dct[keypd]['payee']
            desc = self.payee_desc_dct[keypd]['desc']
            if not d:  # to search for acc_dest using only payee
                if not pd.isnull(payee) and not pd.isnull(desc) and\
                   re.search(payee, p, re.IGNORECASE):
                    k = self.payee_desc_dct[keypd]
                    # TODO add validation that there is only one acc_dest
                    return k['acc_source'], k['acc_dest']
            if not pd.isnull(payee) and not pd.isnull(desc) and\
               re.search(payee, p, re.IGNORECASE) and \
               re.search(desc, d, re.IGNORECASE):
                k = self.payee_desc_dct[keypd]
                return k['acc_source'], k['acc_dest']
        for payee in self.payee_dct:
            if re.search(payee, p, re.IGNORECASE):
                k = self.payee_dct[payee]
                return k['acc_source'], k['acc_dest']
        for desc in self.desc_dct:
            if re.search(desc, d, re.IGNORECASE):
                k = self.desc_dct[desc]
                return k['acc_source'], k['acc_dest']
        return None, None
