# -*- coding: utf-8 -*-

import io
import sys
import twstock

# XXX: Repalce sys.stdout prevent Windows UnicodeEncodeError on cmd.exe
stdout = io.TextIOWrapper(
    getattr(sys.stdout, 'buffer', sys.stdout), encoding='utf-8', errors='replace')


def run(argv):
    print('四大買賣點判斷 Best Four Point', file=stdout)
    print('------------------------------', file=stdout)
    for sid in argv:
        bfp = twstock.BestFourPoint(twstock.Stock(sid))
        bfp = bfp.best_four_point()
        print('%s: ' % (sid), end='', file=stdout)
        if bfp:
            if bfp[0]:
                print('Buy  ', bfp[1], file=stdout)
            else:
                print('Sell ', bfp[1], file=stdout)
        else:
            print("Don't touch", file=stdout)
