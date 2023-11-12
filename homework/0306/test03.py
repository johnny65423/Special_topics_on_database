import pymssql
import requests
import json
from fake_useragent import UserAgent
import numpy as np
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
db_settings = {
    "host": "127.0.0.1",
    "user": "johnnyhsu",
    "password": "12345678",
    "database": "ncu_database",
    "charset": "UTF-8"
}

def get_real_time_info(code, type) :
    ua = UserAgent()
    url = 'https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=%s_%s.tw&json=1&delay=0' % (type, code)
    response = requests.get(url, headers = {'User-Agent': ua.random})  # response.text為json格式
    dict = json.loads(response.text)    # 把json格式轉換為Python的dictionary
    info = dict['msgArray'][0]
    print(info['nf'], info['c'], info['d'], info['t'])
    stock = []
    stock.append(info['c'])    # 股票代號
    stock.append(info['d'])    # 日期
    stock.append(info['t'])    # 時間
    if type == 'tse':
        stock.append(float(info['v']) * 1000)  # 成交股數 (上市)
    else :
        stock.append(float(info['v']))
    stock.append(0) #成交金額 
    stock.append(info['o'])    # 開盤價
    stock.append(info['h'])    # 最高價
    stock.append(info['l'])    # 最低價
    stock.append(0 if info['z'] == '-' else np.round(float(info['z']), 3) )   # 收盤價
    stock.append(0 if info['z'] == '-' else np.round(float(info['z']) - float(info['y']), 3 ) )    # 漲跌價差
    stock.append(0) # 成交筆數
    #print(stock)    # 請自己注意存入的類型和格式
    return stock


def insert_real_time(code, type):
    try:
        conn = pymssql.connect(**db_settings)   # 連接MSSQL，並使用前面寫好的設定
        # 要執行的命令 (注意型態)
        info = get_real_time_info(code,type)
        query = "INSERT INTO [dbo].[price_real_time](stock_code, date, time, tv, t, o, h, l, c, d, v) VALUES (%s, %s, %s, %d, %d, %s, %s, %s, %s, %s, %d)"    
        with conn.cursor() as cursor:
            cursor.execute(query, (info[0], info[1], info[2], info[3], info[4], info[5], info[6], info[7], info[8], info[9], info[10]))   # 執行命令
        conn.commit()   # 記得要commit，才會將資訊儲存到資料庫，不然只會暫存到記憶體
        conn.close()
        print("inserted!")
    except Exception as e:
        print(e)

def job():
    print('job:',datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'))

    insert_real_time('3481','tse')
    insert_real_time('3362','otc')

now = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
end = datetime.datetime.today().strftime('%Y-%m-%d') + ' 12:00:00'
scheduler = BlockingScheduler()
scheduler.add_job(job, 'interval', minutes=10, start_date=now, end_date=end, next_run_time=now)
scheduler.start()