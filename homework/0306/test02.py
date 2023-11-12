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
    time.sleep(5)
    for i in lists :
        #print(i.text)
        #print("-------------")
        if i.text != '股票名稱\n權重' :
            taiwan50.append(i.text.split('\n')[0])
    #edge.close()

# 載入SQL (若為台灣50前10，isTaiwan50 = 1)
def find_stock(url, start, end):
    try:
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html5lib')
    except TimeoutException as e:
        print("*************error***************")
        print(e)

    table = soup.find("table", {"class" : "h4"})
    check = False
    stock_list = []
    for row in table.find_all("tr"):
        data = []
        for col in row.find_all('td'):
            col.attrs = {}
            data.append(col.text.strip().replace('\u3000', ''))
        
        if len(data) == 1:
            print(">",data,"<")
            if data[0] == start :
                check = True
            elif data[0] == end :
                check = False
            pass # title 股票, 上市認購(售)權證, ...
        else:
            if check :
                temp=[]
                temp.append(data[0][:4])
                temp.append(data[0][4:])
                temp.append(data[3])
                temp.append(data[4])
                if temp[1] in taiwan50 :
                    temp.append(True)
                else:
                    temp.append(False)
                stock_list.append(temp)
    
    print(len(stock_list))
    #for i in stock_list:
    #    print(i)
    try:
        conn = pymssql.connect(**db_settings)
        cursor = conn.cursor()
        command = "INSERT INTO [dbo].[stock_info] (stock_code, name, type, category, isTaiwan50) VALUES (%s, %s, %s, %s, %s)"
        # 練習1
        for i in stock_list :
            cursor.execute(command, (i[0], i[1], i[2], i[3], i[4]))
            print("insert",i)
        # 練習2
    except Exception as e:
       print(e)
    conn.commit()
    conn.close()
find_Taiwan50()
print(taiwan50)
find_stock("https://isin.twse.com.tw/isin/C_public.jsp?strMode=4", "股票", "特別股")
find_stock("https://isin.twse.com.tw/isin/C_public.jsp?strMode=2", "股票", "上市認購(售)權證")