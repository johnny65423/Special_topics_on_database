# Exercise3 - Load JSON
import requests
import json
from fake_useragent import UserAgent
import numpy as np


def get_real_time_info(code, type) :
    ua = UserAgent()
    url = 'https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=%s_%s.tw&json=1&delay=0' % (type, code)
    response = requests.get(url, headers = {'User-Agent': ua.random})  # response.text為json格式
    dict = json.loads(response.text)    # 把json格式轉換為Python的dictionary
    info = dict['msgArray'][0]
    print(info)
    stock = []
    stock.append(info['c'])    # 股票代號
    stock.append(info['d'])    # 日期
    stock.append(info['t'])    # 時間
    stock.append(float(info['v']) * 1000)  # 成交股數 (上市)
    stock.append(0) #成交金額 
    stock.append(info['o'])    # 開盤價
    stock.append(info['h'])    # 最高價
    stock.append(info['l'])    # 最低價
    stock.append(0 if info['z'] == '-' else np.round(float(info['z']), 3) )   # 收盤價
    stock.append(0 if info['z'] == '-' else np.round(float(info['z']) - float(info['y']), 3 ) )    # 漲跌價差
    stock.append(0) # 成交筆數
    #print(stock)    # 請自己注意存入的類型和格式
    return stock

print(get_real_time_info('1802','tse'))
