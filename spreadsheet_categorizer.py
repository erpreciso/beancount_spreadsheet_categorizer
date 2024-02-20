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
    def __init__(self, spreadsheet_path, sheet_name, cols=None):
        if not cols:
            self.p = 'payee'
            self.d = 'description'
            self.a_s = 'account-source'
            self.a_d = 'account-destination'
        self.create_categorizer(spreadsheet_path, sheet_name)

    def print_dict(self, dct):
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(dct)

    def _read_line(self, line):
        "Parse a line from the spreadsheet and update dict"
        payee, desc = str(line[self.p]), str(line[self.d])
        acc_source, acc_dest = str(line[self.a_s]), str(line[self.a_d])
        if acc_dest == 'nan':
            acc_dest = None  # convert nan to None
        if desc:
            val = {desc: {self.a_s: acc_source, self.a_d: acc_dest}}
            if payee in self.dct.keys():
                if desc not in self.dct[payee]:
                    self.dct[payee].append(val)
                else:
                    raise KeyError("Desc already in dict. Illegal case")
            else:
                self.dct[payee] = [val]

    def create_categorizer(self, spreadsheet_path, sheet_name):
        "Parse spreadsheet and create categorizer dicts."
        lg.debug('Created categorizer with file: {}'.format(spreadsheet_path))
        df = pd.read_excel(spreadsheet_path, engine='odf',
                           sheet_name=sheet_name)
        self.payee_desc_dct, self.payee_dct, self.desc_dct = {}, {}, {}
        assert all([c in df.columns
                    for c in [self.p, self.d, self.a_s, self.a_d]])
        df.apply(self._read_line, axis=1)

    def search_key(self, s):
        "Convert s to regex and search in self.dct keys for partial match."
        rx = re.compile(s)
        keys = self.dct.keys()
        matches = [k for k in keys if re.search(rx, k, re.IGNORECASE)]
        if not matches:
            return None
        if len(matches) > 1:
            err = "Multiple keys matches search pattern {}".format(rx)
            raise KeyError(err)
        else:
            return matches[0]

    def match(self, p, d):
        "Match P and D with dict"
        for keypd in self.payee_desc_dct:
            payee = self.payee_desc_dct[keypd][self.p]
            desc = self.payee_desc_dct[keypd][self.d]
            if not d:  # to search for acc_dest using only payee
                if not pd.isnull(payee) and not pd.isnull(desc) and\
                   re.search(payee, p, re.IGNORECASE):
                    k = self.payee_desc_dct[keypd]
                    # TODO add validation that there is only one acc_dest
                    return k[self.a_c], k[self.a_d]
            if not pd.isnull(payee) and not pd.isnull(desc) and\
               re.search(payee, p, re.IGNORECASE) and \
               re.search(desc, d, re.IGNORECASE):
                k = self.payee_desc_dct[keypd]
                return k[self.a_s], k[self.a_d]
        for payee in self.payee_dct:
            if re.search(payee, p, re.IGNORECASE):
                k = self.payee_dct[payee]
                return k[self.a_s], k[self.a_d]
        for desc in self.desc_dct:
            if re.search(desc, d, re.IGNORECASE):
                k = self.desc_dct[desc]
                return k[self.a_s], k[self.a_d]
        return None, None


    # TODO: escape punctuation in dict
    # catchall clause if payee only
