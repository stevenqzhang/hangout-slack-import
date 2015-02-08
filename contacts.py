# -*- coding: utf-8 -*-
__author__ = 'steven'

#file to convert google takeout contacts vcard to csv with name-well formed number pairs, to join in hangouts data.
import csv
import argparse
import phonenumbers
import codecs
import pandas as pd
from hangouts2csv import is_name, UserNamesAndNumbers


def main():
    parser = argparse.ArgumentParser(description='Parse your google takeout contacts for input into hangouts')
    parser.add_argument('-i', '--input', type=str, required=True, help='google takeouts', metavar='contacts_raw.csv')
    parser.add_argument('-o', '--output', type=argparse.FileType('wb'), required=True, help='CSV output file',
                        metavar='<contacts.csv>')
    args = parser.parse_args()

    # raw_csvfile = open(args.input, 'rb')
    # data = pd.read_csv(raw_csvfile, error_bad_lines=Fallsse)
    # data
    xls = read_contacts(args.input)
    xls.to_csv(args.output, encoding='utf-8')
    xls.to_pickle('contacts.pickle')


# don't want to deal with imports, compied to main file
def read_contacts(file):
    xls = pd.read_excel(file, 'Sheet 1')
    xls.columns = ['Name', 'Phone raw']
    length = len(xls['Name'])
    xls['Phone parsed'] = pd.Series()

    for i, row in xls.iterrows():
        try:
            xls.ix[i, 'Phone parsed'] = str(UserNamesAndNumbers.formatNumber(row["Phone raw"]))
        except phonenumbers.phonenumberutil.NumberParseException:
            pass
    return xls


if __name__ == "__main__":
    main()