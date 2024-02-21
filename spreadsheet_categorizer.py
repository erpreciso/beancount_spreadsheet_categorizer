# -*- coding: utf-8 -*-
import re
import pandas as pd
import logging
import pprint


class SpreadsheetImportError(Exception):
    pass


class SpreadsheetCategorizer():

    def __init__(self, spreadsheet_path, sheet_name, cols=None,
                 log_level=logging.INFO):
        """Initialize class."""
        logging.basicConfig(format='%(levelname)s:%(message)s')
        self.lg = logging.getLogger("lg")
        self.lg.setLevel(log_level)
        if not cols:
            self.p = 'payee'
            self.d = 'description'
            self.a_s = 'account-source'
            self.a_d = 'account-destination'
        else:
            assert type(cols) == dict
            assert all([x in cols.keys() for x in ['p', 'd', 'a_s', 'a_d']])
            self.p, self.d = cols['p'], cols['d']
            self.a_s, self.a_d = cols['a_s'], cols['a_d']
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
                    err = "Already in dict. Illegal case\n"
                    err += "Payee: {}\n".format(payee)
                    err += "Desc:  {}\n".format(desc)
                    err += "Existing: {}".format(self.dct[payee])
                    raise KeyError(err)
            else:
                self.dct[payee] = {}
                self.dct[payee][desc] = val

    def sanity_checks(self):
        "Sanity checks on dct."
        if 'nan' not in self.dct.keys():
            self.lg.warning('No payee catch-all clause')
        for payee in self.dct.keys():
            self.lg.debug('Sanity checking {}'.format(payee))
            descs = self.dct[payee]
            # warning for missing catch-all for payee
            if 'nan' not in descs.keys():
                self.lg.info('No desc catch-all clause for {}'.format(payee))
            # error for one desc shadowing another
            for desc in descs.keys():
                self.lg.debug("  Search dups for {}".format(desc))
                # expect a list long 1 as the case matches with itself
                if len(self.search_key(desc, descs)) > 1:
                    err = "Desc {} duplicated for {}.".format(desc, payee)
                    raise SpreadsheetImportError(err)

    def _create(self, spreadsheet_path, sheet_name):
        "Parse spreadsheet and create categorizer dicts."
        self.lg.debug('Created categorizer with: {}'.format(spreadsheet_path))
        df = pd.read_excel(spreadsheet_path, engine='odf',
                           sheet_name=sheet_name)
        assert all([c in df.columns
                    for c in [self.p, self.d, self.a_s, self.a_d]])
        df.apply(self._read_line, axis=1)
        self.sanity_checks()

    def search_key(self, s: str, dct: dict, strict=False) -> list:
        "Convert s to regex and search in dct keys for partial match."
        rx = re.escape(s)
        keys = dct.keys()
        if not strict:
            matches = [k for k in keys if re.search(rx, k, re.IGNORECASE)]
        elif strict:
            matches = [k for k in keys if s.lower() == k.lower()]
        self.lg.debug(' Searches for {}: {}'.format(rx, matches))
        if len(matches) > 1:
            self.lg.info("  Multiple keys matches pattern {}".format(rx))
        return matches

    def match(self, p, d) -> tuple:
        "Return acc_source and acc_dest associated with p and d args."
        # Ensure when p or d are None it call-back with 'nan' for the missing.
        if not p and not d:
            self.lg.debug('Catch-all: p: None and d: None')
            return self.match('nan', 'nan')
        elif p and not d:
            self.lg.debug('Match: p: {} and d: None'.format(p))
            return self.match(p, 'nan')
        elif not p and d:
            self.lg.debug('Match: p: None and d: {}'.format(d))
            return self.match('nan', d)
        elif p and d:
            self.lg.debug('Match: p: {} and d: {}'.format(p, d))
            payee_keys = self.search_key(p, self.dct)
            payee_keys_strict = self.search_key(p, self.dct, True)
            if len(payee_keys) > 1:
                if len(payee_keys_strict) == 0:
                    self.lg.warning('Multiple payees {} -> catch-all'.format(p))
                    return self.match('nan', 'nan')
                else:
                    # case where a payee shadows another, but it's intended
                    payee_keys = payee_keys_strict
            elif len(payee_keys) == 0:
                self.lg.debug('No payees for {}. Search for desc'.format(p))
                return self.match('nan', d)
            self.lg.debug('Found {}'.format(payee_keys))
            payee_key = payee_keys[0]
            descs_dict = self.dct[payee_key]
            desc_keys = self.search_key(d, descs_dict)
            if len(desc_keys) == 0 and d == 'nan':
                self.lg.debug('No catch-all for {}. Catch-all all'.format(p))
                return self.match('nan', 'nan')
            elif len(desc_keys) > 1:
                self.lg.warning('Multiple desc for {}. Search payee'.format(d))
                return self.match(p, 'nan')
            elif len(desc_keys) == 0:
                self.lg.debug('No descs found for {}. Search payee'.format(d))
                return self.match(p, 'nan')
            elif len(desc_keys) == 1:
                self.lg.debug('Found {}'.format(desc_keys))
                desc_key = desc_keys[0]
                res = self.dct[payee_key][desc_key]
                return res[self.a_s], res[self.a_d]
