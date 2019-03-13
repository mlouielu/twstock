import json
from datetime import date, datetime, timedelta
from time import sleep
from urllib import request
from bs4 import BeautifulSoup
from soupsieve.util import string

num=[]
sell_price = []
buy_price=[]

def get_median (median):
    median.sort()
    if (len(median) % 2 == 0) :
        return median[int(len(median)/2)]
    else:
        return median[int(len(median) / 2) - 1]

def inff (url):
    # url = 'https://rate.bot.com.tw/gold?Lang=zh-TW'
    data = request.urlopen(url).read().decode("utf-8")
    Soup = BeautifulSoup(data, 'lxml')
    # print(Soup.td)
    try:
        if(int(Soup.select('td[class="text-right"]')[0].string) > 1500) :
            print('資料有錯誤')
        else:
            print('本行賣出 : '+Soup.select('td[class="text-right"]')[0].string)  # 本行賣出
            print('本行買進 : '+Soup.select('td[class="text-right"]')[1].string)  # 本行買進
            # aa=string(int(Soup.select('td[class="text-right"]')[0].string)-int(Soup.select('td[class="text-right"]')[1].string))
            # print('差額 : '+aa)
            num.append('1')
            sell_price.append(float(Soup.select('td[class="text-right"]')[0].string))
            buy_price.append(float(Soup.select('td[class="text-right"]')[1].string))
            # sleep(1)
    except:
        print('')

i=0
while (len(num) < 100): #檢差近幾筆資料
    theTime = datetime.now()+ timedelta(-i)
    theTime = theTime.strftime('%Y-%m-%d')
    # print(theTime)
    url = "https://rate.bot.com.tw/gold/quote/"+theTime
    inff(url)
    i=i+1



print(len(num))  #共有幾筆資料
sell_average = sum(sell_price)/len(num)  #平均賣出價格
buy_average = sum(buy_price)/len(num) #平均買入價格
print(sell_average)    #平均賣出價格   買價
print(sum(buy_price)/len(num))     #平均買入價格   賣價
print("我方買入中位數 :" + string(get_median(sell_price)))     #中位數

