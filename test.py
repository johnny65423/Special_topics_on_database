import calendar
import pymssql
from datetime import datetime
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
        WebDriverWait(edge, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//tbody[@id='holidays']//tr//th")))
        # 練習1
    except TimeoutException as e:
        print(e)    
    #edge.close()


# 載入SQL
def insertSQL():
    # 非休市日
    work_count = 0
    try:
        print("start connect")
        conn = pymssql.connect(**db_settings)
        #conn = pymssql.connect(host="127.0.0.1", user="johnnyhsu", password="w21lacm3", database="ncu_database", charset="UTF-8")
        print("connected!")
        # 請根據自己的資料表修改command
        command = "INSERT INTO [dbo].[calendar] (date, day_of_stock, other) VALUES (%s, %d, %s)"
        # 練習1

    except Exception as e:
        print("*************error***************")
        print(e)
    conn.close()

crawler()
insertSQL()