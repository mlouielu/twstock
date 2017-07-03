import twstock


def run(argv):
    print('四大買賣點判斷 Best Four Point')
    print('------------------------------')
    for sid in argv:
        bfp = twstock.BestFourPoint(twstock.Stock(sid))
        bfp = bfp.best_four_point()
        print('%s: ' % (sid), end='')
        if bfp:
            if bfp[0]:
                print('Buy  ', bfp[1])
            else:
                print('Sell ', bfp[1])
        else:
            print("Don't touch")
