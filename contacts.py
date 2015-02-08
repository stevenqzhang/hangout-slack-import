# -*- coding: utf-8 -*-
__author__ = 'steven'

#file to convert google takeout contacts vcard to csv with name-well formed number pairs, to join in hangouts data.
import csv
import argparse
import phonenumbers
import codecs
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description='Parse your google takeout contacts for input into hangouts')
    parser.add_argument('-i', '--input', type=str, required=True, help='google takeouts', metavar='contacts_raw.csv')
    parser.add_argument('-o', '--output', type=argparse.FileType('wb'), required=True, help='CSV output file',
                        metavar='<contacts.csv>')
    args = parser.parse_args()

    # raw_csvfile = open(args.input, 'rb')
    # data = pd.read_csv(raw_csvfile, error_bad_lines=False)
    # data
    xls = pd.read_excel(args.input, 'Sheet 1')
    xls


if __name__ == "__main__":
    main()