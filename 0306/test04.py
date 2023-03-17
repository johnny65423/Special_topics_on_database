import calendar
import time
import pymssql
import datetime
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import requests
import json
from fake_useragent import UserAgent
import numpy as np
from bs4 import BeautifulSoup

# 根據自己的Database來填入資訊
db_settings = {
    "host": "127.0.0.1",
    "user": "johnnyhsu",
    "password": "12345678",
    "database": "ncu_database",
    "charset": "UTF-8"
}

taiwan50 = []

# 搜尋台灣50前10
def find_Taiwan50():
    # 這邊是用Edge作為範例，可以依照你使用瀏覽器的習慣做修改
    options = EdgeOptions()
    options.add_argument("--headless")  # 執行時不顯示瀏覽器
    options.add_argument("--disable-notifications")  # 禁止瀏覽器的彈跳通知
    options.add_experimental_option("detach", True) # 爬蟲完不關閉瀏覽器
    edge = webdriver.Edge(EdgeChromiumDriverManager().install(),options=options)

    edge.get("https://www.cmoney.tw/etf/tw/0050")
    try:
        # 等元件跑完再接下來的動作，避免讀取不到內容
        lists = WebDriverWait(edge, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='cm-col cm-col-4 ']//div[@class='stock__table pb-8']//div[@class='cm-table stock__tableContent']//tr")))

    except TimeoutException as e:
        print("*************error***************")
        print(e) 
    # 練習2
    time.sleep(3)
    for i in lists :
        #print(i.text)
        #print("-------------")
        if i.text != '股票名稱\n權重' :
            taiwan50.append(i.text.split('\n')[0])

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
            temp = str(1911+int(temp[:3])) + temp[3:]
            print((code, temp, info[1], info[2], info[3], info[4], info[5], info[6], info[7], info[8]))
            query = "INSERT INTO [dbo].[price_history](stock_code, date, tv, t, o, h, l, c, d, v) VALUES (%s, %s, %d, %d, %s, %s, %s, %s, %s, %d)"    
            with conn.cursor() as cursor:
                cursor.execute(query, (code, temp, info[1], info[2], info[3], info[4], info[5], info[6], info[7].replace('X',''), info[8]))   # 執行命令
        conn.commit()   # 記得要commit，才會將資訊儲存到資料庫，不然只會暫存到記憶體
        conn.close()
        print("inserted!")
    except Exception as e:
        print(e)
        print((code, temp, info[1], info[2], info[3], info[4], info[5], info[6], info[7], info[8]))
        a = input()


find_Taiwan50()
print(taiwan50)

for comp in taiwan50 :

    try:
        conn = pymssql.connect(**db_settings)   # 連接MSSQL，並使用前面寫好的設定
        # 要執行的命令 (注意型態)
        query = "SELECT * FROM [dbo].[stock_info] WHERE name=%s"   
        cursor = conn.cursor()
        cursor.execute(query, comp)   # 執行命令
        code = cursor.fetchone()[0]
        conn.commit()   # 記得要commit，才會將資訊儲存到資料庫，不然只會暫存到記憶體
        conn.close()
    except Exception as e:
        print(e)

    print(code)
    for y in range(2021,2024):
        for m in range(12,13) :
            if y==2023 and m>3:
                pass
            else:
                print('insert', code, y, m)
                insert_history(code, y, m)
                time.sleep(3)
        print("---")