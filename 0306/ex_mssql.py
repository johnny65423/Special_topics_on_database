import pymssql

# 資料庫設定 (dictionary)
db_settings = {
    "host": "127.0.0.1",
    "user": "johnnyhsu",
    "password": "12345678",
    "database": "ncu_database",
    "charset": "UTF-8"
}

# 2330 20230306 13:30:00 股價資訊
info = ['2330', '20230306', '13:30:00', 21846000.0, 0, '520.0000', '524.0000', '517.0000', 521.0, 5.0, 0]

# main
try:
    conn = pymssql.connect(**db_settings)   # 連接MSSQL，並使用前面寫好的設定
    # 要執行的命令 (注意型態)
    query = "INSERT INTO [dbo].[price_real_time](stock_code, date, time, tv, t, o, h, l, c, d, v) VALUES (%s, %s, %s, %d, %d, %s, %s, %s, %s, %s, %d)"    
    with conn.cursor() as cursor:
        cursor.execute(query, (info[0], info[1], info[2], info[3], info[4], info[5], info[6], info[7], info[8], info[9], info[10]))   # 執行命令
    conn.commit()   # 記得要commit，才會將資訊儲存到資料庫，不然只會暫存到記憶體
    conn.close()
except Exception as e:
    print(e)