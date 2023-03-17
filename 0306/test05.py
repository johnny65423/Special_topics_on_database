# Exercise3 - Load JSON
import requests
import json
from fake_useragent import UserAgent
import numpy as np
import pymssql
d = 20230101

db_settings = {
    "host": "127.0.0.1",
    "user": "johnnyhsu",
    "password": "12345678",
    "database": "ncu_database",
    "charset": "UTF-8"
}

def get_history(code, d):

    ua = UserAgent()
    url = 'https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date=%s&stockNo=%s' % (d, code)
    response = requests.get(url, headers = {'User-Agent': ua.random})  # response.text為json格式
    dict = json.loads(response.text)    # 把json格式轉換為Python的dictionary
    info = dict['data']
    info = [[j.replace(',','') for j in i] for i in info ]
    return info

#print( get_history(2330, 2023, 1) )

def insert_history(code, y, m):
    if m < 10 :
        m = '0'+str(m)
    d = str(y)+str(m)+'01'
    try:
        conn = pymssql.connect(**db_settings)   # 連接MSSQL，並使用前面寫好的設定
        # 要執行的命令 (注意型態)
        infos = get_history(code,d)
        for info in infos :
            temp = info[0]
            print(temp)
            temp = str(1911+int(temp[:3])) + temp[3:]
            print(temp,d)
            query = "INSERT INTO [dbo].[price_history](stock_code, date, tv, t, o, h, l, c, d, v) VALUES (%s, %s, %d, %d, %s, %s, %s, %s, %s, %d)"    
            with conn.cursor() as cursor:
                cursor.execute(query, (code, temp, info[1], info[2], info[3], info[4], info[5], info[6], info[7], info[8]))   # 執行命令
        conn.commit()   # 記得要commit，才會將資訊儲存到資料庫，不然只會暫存到記憶體
        conn.close()
        print("inserted!")
    except Exception as e:
        print(e)

insert_history(2330,2023,1)