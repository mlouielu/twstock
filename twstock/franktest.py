import twstock
import os, sys
import subprocess
from subprocess import PIPE

stocknumber = []

for item in twstock.twse.keys(): #上市
    stock = twstock.realtime.get(item) # realtime — 即時股票資訊
    try :      #accumulate_trade_volume	 累積成交量字串
        if stock['realtime']['open'] is not None and stock['success']:
            if float(stock['realtime']['open']) > 20 and float(stock['realtime']['open']) < 40  :
                print(stock)
                stocknumber.append(item)
                            # print(str(stock['info']['name']))
                print("%s \n%s%s %s"%(str(stock['info']['name']),'開盤價',':',str(stock['realtime']['open'])))
                            # print('盤中最高價 : ' + str(stock['realtime']['high']))   and float(stock['realtime']['trade_volume']) > 100
                            # print('盤中最低價 : ' + str(stock['realtime']['low']))
            if float(stock['info']['code']) > 9500 :        #後面都英文字的 open沒東西
                break
    except:
        pass

print(len(stocknumber))
print(stocknumber)





# stock = twstock.Stock('1102',initial_fetch=True)
# stock.fetch_from(2018,10)
# print(stock.data)
# print(stock.ma_bias_ratio(5,10))
# list = []
# for item in stock.data: #上市  從舊到新
#     print('開盤價 : '+str(item[3]))
#     if item is not None :
#         list.append(item[3])
#     # stock = twstock.realtime.get(item)  # realtime — 即時股票資訊
#     # if stock['success']:
#     #     print(stock)
#     #     print('開盤價 : ' + str(stock['realtime']['open']))
#     #     print('盤中最高價 : ' + str(stock['realtime']['high']))
#     #     print('盤中最低價 : ' + str(stock['realtime']['low']))
# print('max : '+str(max(list)))
# print('min : '+str(min(list)))
# stdout,process = subprocess.Popen("twstock -b {}".format('1102'), stdout=subprocess.PIPE, stderr=PIPE, stdin=subprocess.PIPE, shell=True).communicate()
# print(stdout.decode('utf-8'))






# for item in twstock.twse.keys(): #上市
#     print(item)
#     stock = twstock.realtime.get(item)  # realtime — 即時股票資訊
#     if stock['success']:
#         print(stock)
#         print('開盤價 : ' + str(stock['realtime']['open']))
#         print('盤中最高價 : ' + str(stock['realtime']['high']))
#         print('盤中最低價 : ' + str(stock['realtime']['low']))




# print(stock.moving_average(stock.price, 1))
# stdout,process = subprocess.Popen("twstock -b {}".format('2330'), stdout=subprocess.PIPE, stderr=PIPE, stdin=subprocess.PIPE, shell=True).communicate()
# print(stdout.decode('utf-8'))
# stock.sid
# sidstock.price  #回傳各日之收盤價

# print(stock.sid)

# print(stock.price)


