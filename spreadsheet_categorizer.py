# -*- coding: utf-8 -*-
import re
import pandas as pd
import logging
import pprint
import pdb


logging.basicConfig(format='%(levelname)s:%(message)s')
lg = logging.getLogger("lg")
lg.setLevel(logging.DEBUG)


class SpreadsheetCategorizer():

    def __init__(self, spreadsheet_path, sheet_name, cols=None):
        if not cols:
            self.p = 'payee'
            self.d = 'description'
            self.a_s = 'account-source'
            self.a_d = 'account-destination'
        self.dct = {}
        self._create(spreadsheet_path, sheet_name)

    def print_dct(self):
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(self.dct)

    def _read_line(self, line):
        "Parse a line from the spreadsheet and update dict"
        payee, desc = str(line[self.p]), str(line[self.d])
        acc_source, acc_dest = str(line[self.a_s]), str(line[self.a_d])
        if acc_dest == 'nan':
            acc_dest = None  # convert nan to None
        if desc:
            val = {self.a_s: acc_source, self.a_d: acc_dest}
            if payee in self.dct.keys():
                if desc not in self.dct[payee].keys():
                    self.dct[payee][desc] = val
                else:
                    raise KeyError("Desc already in dict. Illegal case")
            else:
                self.dct[payee] = {}
                self.dct[payee][desc] = val

    def _create(self, spreadsheet_path, sheet_name):
        "Parse spreadsheet and create categorizer dicts."
        # TODO create catch-all clause if not existing in spreadsheet
        # TODO ensure only one catch-all exists for each case
        lg.debug('Created categorizer with file: {}'.format(spreadsheet_path))
        df = pd.read_excel(spreadsheet_path, engine='odf',
                           sheet_name=sheet_name)
        assert all([c in df.columns
                    for c in [self.p, self.d, self.a_s, self.a_d]])
        df.apply(self._read_line, axis=1)

    def search_key(self, s: str, dct: dict) -> list:
        "Convert s to regex and search in dct keys for partial match."
        rx = re.escape(s)
        keys = dct.keys()
        matches = [k for k in keys if re.search(rx, k, re.IGNORECASE)]
        lg.debug(' Searches for {}: {}'.format(rx, matches))
        if len(matches) > 1:
            lg.debug("Multiple keys matches search pattern {}".format(rx))
        return matches

    def match(self, p, d) -> tuple:
        "Return acc_source and acc_dest associated with p and d args."
        # Ensure when p or d are None it call-back with 'nan' for the missing.
        if not p and not d:
            lg.debug('Catch-all: p: None and d: None')
            return self.match('nan', 'nan')
        elif p and not d:
            lg.debug('Match: p: {} and d: None'.format(p))
            return self.match(p, 'nan')
        elif not p and d:
            lg.debug('Match: p: None and d: {}'.format(d))
            return self.match('nan', d)
        elif p and d:
            lg.debug('Match: p: {} and d: {}'.format(p, d))
            payee_keys = self.search_key(p, self.dct)
            if len(payee_keys) > 1:
                lg.debug('Multiple payees for {}. Going catch-all'.format(p))
                return self.match('nan', 'nan')
            elif len(payee_keys) == 0:
                lg.debug('No payees for {}. Search for desc'.format(p))
                return self.match('nan', d)
            elif len(payee_keys) == 1:
                lg.debug('Found {}'.format(payee_keys))
                payee_key = payee_keys[0]
                descs_dict = self.dct[payee_key]
                desc_keys = self.search_key(d, descs_dict)
                if len(desc_keys) > 1:
                    lg.debug('Multiple desc for {}. Search payee'.format(d))
                    return self.match(p, 'nan')
                elif len(desc_keys) == 0:
                    lg.debug('No descs found for {}. Search payee'.format(d))
                    return self.match(p, 'nan')
                elif len(desc_keys) == 1:
                    lg.debug('Found {}'.format(desc_keys))
                    desc_key = desc_keys[0]
                    res = self.dct[payee_key][desc_key]
                    return res[self.a_s], res[self.a_d]
