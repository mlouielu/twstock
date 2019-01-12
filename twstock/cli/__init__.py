# -*- coding: utf-8 -*-
import argparse
from twstock.codes import __update_codes
from twstock.cli import best_four_point
from twstock.cli import stock
from twstock.cli import realtime


def run():
    parser = argparse.ArgumentParser()

    parser.add_argument('-b', '--bfp', nargs='+')
    parser.add_argument('-s', '--stock', nargs='+')
    parser.add_argument('-r', '--realtime', nargs='+')
    parser.add_argument('-p', '--proxy', nargs='+')
    parser.add_argument('-U', '--upgrade-codes', action='store_true', help='Update entites codes')
    args = parser.parse_args()

    proxies_list = args.proxy or []
    if args.bfp:
        best_four_point.run(args.bfp, proxies_list=proxies_list)
    elif args.stock:
        stock.run(args.stock, initial_fetch=True, proxies_list=proxies_list)
    elif args.realtime:
        realtime.run(args.realtime, proxies_list=proxies_list)
    elif args.upgrade_codes:
        print('Start to update codes')
        __update_codes()
        print('Done!')
    else:
        parser.print_help()
