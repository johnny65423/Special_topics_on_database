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

# 根據自己的Database來填入資訊
db_settings = {
    "host": "127.0.0.1",
    "user": "johnnyhsu",
    "password": "12345678",
    "database": "ncu_database",
    "charset": "UTF-8"
}

#特殊節日
holiday_dir = {}

# 爬蟲
def crawler():

    # 這邊是用Edge作為範例，可以依照你使用瀏覽器的習慣做修改
    options = EdgeOptions()
    options.add_argument("--headless")  # 執行時不顯示瀏覽器
    options.add_argument("--disable-notifications")  # 禁止瀏覽器的彈跳通知
    #options.add_experimental_option("detach", True)  # 爬蟲完不關閉瀏覽器
    edge = webdriver.Edge(EdgeChromiumDriverManager().install(), options=options)

    edge.get("https://www.wantgoo.com/global/holiday/twse")
    try:
        # 等元件跑完再接下來的動作，避免讀取不到內容
        lists = WebDriverWait(edge, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//tbody[@id='holidays']//tr")))
        


        # 練習1
    except TimeoutException as e:
        print(e)    
    #edge.close()
    time.sleep(5)
    res = {}
    for i in lists:
        #print("*",i.text.split(),"*")
        #print("---------------")
        temp = i.text.split()
        temp[0] = datetime.datetime.strptime(temp[0],'%Y/%m/%d').strftime("%Y-%m-%d")
        res[temp[0]] = temp[2]
    return res 

# 載入SQL
def insertSQL(ins):
    # 非休市日
    work_count = 0
    try:
        print("start connect")
        conn = pymssql.connect(**db_settings)
        cursor = conn.cursor()
        #conn = pymssql.connect(host="127.0.0.1", user="johnnyhsu", password="w21lacm3", database="ncu_database", charset="UTF-8")
        print("connected!")
        # 請根據自己的資料表修改command
        command = "INSERT INTO [dbo].[calendar] (date, day_of_stock, other) VALUES (%s, %d, %s)"
        # 練習1
        for i in ins :
            cursor.execute(command, (i[0], i[1], i[2]))

    except Exception as e:
        print("*************error***************")
        print(e)
    conn.commit()
    conn.close()


def daylist(holiday):
    res = []
    year = 2023
    print(holiday)
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year, 12, 31)

    day_of_stack = 1
    for single_date in range((end_date - start_date).days + 1):
        other = None
        date = start_date + datetime.timedelta(days=single_date)
        if date.weekday() > 4 :
            temp = -1
        elif date.strftime("%Y-%m-%d") in holiday.keys() :
            temp = -1
            other = holiday[date.strftime("%Y-%m-%d")]
        else :
            temp = day_of_stack
            day_of_stack+=1
        print(date.strftime("%Y-%m-%d"), " ", temp)
        
        res.append([date.strftime("%Y-%m-%d"), temp, other])
    
    return res

holiday = crawler()
ins = daylist (holiday)
for i in ins :
    print(i)
insertSQL(ins)