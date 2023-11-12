# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'test.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap
import pymssql
import pandas as pd
import numpy as np
import mplfinance as mpf
from collections import defaultdict
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class Stock():
    def __init__(self) -> None:
        self.__stockList = ["1303","2303","2308","2317","2330","2412","2454","2881","2891"] # 可選股票, 先寫死top10
        self.sign = self.initSign() # 先用來跑所有買賣訊號
        
        self.onDisplay = { "goldCross":False, "deadCross":False }
        self.startDate = "2021-01-01"
        self.endDate = "2023-03-01"
        
        self.stock_record = pd.DataFrame( { "stock_code":[], "date":[], "buy_or_sell":[], "trading":[], "balance":[] } )
        self.total_money = 100000 #init money
        self.current_money = self.total_money
        self.stock_current = { "1303" : [0,0],
                               "2303" : [0,0],
                               "2308" : [0,0],
                               "2317" : [0,0],
                               "2330" : [0,0],
                               "2412" : [0,0],
                               "2454" : [0,0],
                               "2881" : [0,0],
                               "2891" : [0,0] }
        
        

    def initSign(self):
        # df = pd.DataFrame()
        # for stockCode in self.__stockList:
        #     query = f"SELECT stock_code = '{stockCode}',date , buy_or_sell FROM SignBuyOrSell('{stockCode}')"
        #     df = pd.concat( [ df ,pd.read_sql_query(query, conn) ] )
        df = pd.read_csv("sign.csv")
        return df
        
    def connect_SQL_server(self):
        # to change: personal sql name
        db_settings = {
            "host": "127.0.0.1",
            "user": "johnnyhsu",
            "password": "12345678",
            "database": "ncu_database",
            "charset": "utf8"
        }

        
        conn  = pymssql.connect(**db_settings)
        return conn


    # 取得股票收盤價
    def get_close_price(self, company, cursor, date):

        today_c = []  # 各股票收盤價
        for stock_code in company:
            # tochange: personal sql name
            command = f"""SELECT c
                            FROM price_history
                            WHERE stock_code = '{stock_code}' AND date = '{date}'"""
            cursor.execute(command)
            today_c.append(cursor.fetchone()[0])
        return today_c

    # 趨勢判斷並取得當前本金能買賣哪幾支股票(回傳df:stock_code、today_c、buy_or_sell)
    def get_buy_stock(self, current_total, cursor, date):
        date = date.strftime("%Y-%m-%d") # datetime->str
        
        today_sign = self.sign[self.sign["date"] == date]
        company = today_sign[today_sign["buy_or_sell"] == 1].stock_code.tolist()  # 買進訊號股票
        company_sell = today_sign[today_sign["buy_or_sell"] == -1].stock_code.tolist()  # 賣出訊號股票
        have_sell = 0  # 有賣出訊號1、無0
        if company_sell:
            today_c_sell = self.get_close_price(company_sell, cursor, date)
            df_sell = pd.DataFrame(list(zip(company_sell, today_c_sell)), columns=['stock_code', 'today_c'])
            df_sell['buy_or_sell'] = [-1] * len(df_sell)
            df_sell.drop_duplicates(inplace=True)
            have_sell = 1

        if not company:
            if have_sell == 0:
                # print("無買進賣出訊號")
                pass
            else:
                return df_sell
        else:
            today_c = self.get_close_price(company, cursor, date)
            df = pd.DataFrame(list(zip(company, today_c)), columns=['stock_code', 'today_c'])
            df['buy_or_sell'] = [1] * len(df)
            # 刪除重複股票資料
            df.drop_duplicates(inplace=True)
            company = df['stock_code']
            today_c = df['today_c']

            if current_total >= sum(today_c):  # 有足夠本金買所有買進訊號股票
                if have_sell == 1:
                    total_df = pd.concat([df, df_sell], axis=0)
                    total_df.index = range(len(total_df))
                    df = total_df
                return df
            else:   # 本金不足用趨勢判斷優先買哪些
                trend = []  # 1為上漲、-1為下跌、0為盤整
                counter_plus = []  # 數前幾天共有多少今日MA>昨日MA
                for stock_code in company:
                    command = f"""SELECT trend, counter_plus 
                                    FROM find_MA_updown('{stock_code}', 8, 6)
                                    WHERE date = '{date}'"""
                    cursor.execute(command)
                    row = cursor.fetchone()
                    trend.append(row[0])
                    counter_plus.append(row[1])

                df['trend'] = trend
                df['counter_plus'] = counter_plus
                # 先比trend，再比counter_plus天數，排出購買順位
                df.sort_values(by=['trend', 'counter_plus'], ascending=False, inplace=True)
                df.index = range(len(df))
                for i in range(len(df)):
                    price = df.loc[i].today_c
                    if price <= current_total:  # 可買
                        current_total = current_total - price
                    else:  # 不夠錢
                        df.drop([i], inplace=True)

                # df.index = range(len(df))
                df.drop(['trend', 'counter_plus'], axis=1, inplace=True)
                if have_sell == 1:
                    total_df = pd.concat([df, df_sell], axis=0)
                    total_df.index = range(len(total_df))
                    df = total_df
                return df
            
        return pd.DataFrame()
    
    # 處理某日的交易
    def buy_and_sell_stock( self, date ):
        """
        string stock_code
        string date
        ? curosr
        """

        # 抓今日要買賣哪幾支股票
        try:  
            conn = self.connect_SQL_server()
            with conn.cursor() as cursor:

                if ( date.day == 10 ): # every month 10 add money
                    self.total_money = self.total_money+5000
                    self.current_money  = self.current_money+5000
                # end if
                
                buy_df = self.get_buy_stock( self.current_money, cursor, date )
        except Exception as ex:
            print(ex)

        conn.close()

        for index, row in buy_df.iterrows():
            stock_code_temp = str( int( row['stock_code'] ) )
            dealMoney = 0.0
            
            if ( row["buy_or_sell"] == 1 ): # buy one
                print( "買" + stock_code_temp )
                dealMoney = row['today_c']
                self.current_money = self.current_money - dealMoney
                self.stock_current[stock_code_temp][0] = self.stock_current[stock_code_temp][0]+1
                # self.stock_current[stock_code_temp][1] = self.stock_current[stock_code_temp][1]- row['today_c']
                # update record
                # self.stock_record.loc[len(self.stock_record.index)] = [ stock_code_temp, date, self.stock_current[stock_code_temp][0], self.stock_current[stock_code_temp][1]]
                
            # end if
            elif ( row["buy_or_sell"] == -1 ): # sell all
                print( "賣" + stock_code_temp )
                dealMoney = row['today_c'] * self.stock_current[stock_code_temp][0]
                self.current_money = self.current_money + dealMoney
                # self.stock_current[stock_code_temp][1] = self.stock_current[stock_code_temp][1] + row['today_c'] * self.stock_current[stock_code_temp][0]
                self.stock_current[stock_code_temp][0] = 0
                # update record
                # self.stock_record.loc[len(self.stock_record.index)] = [ stock_code_temp, date, self.stock_current[stock_code_temp][0], self.stock_current[stock_code_temp][1]]
            # end elif
            else:
                pass
            # end else
            
            self.stock_record = self.stock_record.append( 
                { "stock_code":stock_code_temp, 
                    "date":date.strftime("%Y-%m-%d"), 
                    "buy_or_sell":str(int(row["buy_or_sell"])),
                    "trading":dealMoney, 
                    "balance":self.current_money 
                }, ignore_index=True )
            print(self.stock_record)
        # end for

    
    # end buy_and_sell_stock()
    
    # 畫圖與存圖
    def show(self, day_end, company):
        
        day_start = day_end - relativedelta(years=1) # 固定往前抓一年
        
        # 轉格式datetime->str
        day_start = day_start.strftime("%Y-%m-%d")
        day_end = day_end.strftime("%Y-%m-%d")

        figHS, axHS = self.drawPlot(company, 
                                    self.onDisplay['goldCross'], self.onDisplay['deadCross'], 
                                    day_start, day_end)
        figHS.savefig('stockLine.png')  

    # 依照股票與區間與選擇狀態畫圖
    def drawPlot( self, company, gold, dead, startDate, endDate ):
        # print(startDate, endDate)
        result = []
        try:  
            conn = self.connect_SQL_server()
            with conn.cursor() as cursor:
                # to change: personal sql name
                command = f"""SELECT date, o, h, l, c, v
                            FROM price_history
                            WHERE stock_code = {company}
                            and date >= '{startDate}' AND date <= '{endDate}' order by date asc;"""
                cursor.execute(command)
                result = cursor.fetchall()
        except Exception as ex:
            print(ex)

        conn.close()

        arr = []
        for r in result:
            r = list(r)
            r[0] = r[0]
            r[1] = float(r[1])
            r[2] = float(r[2])
            r[3] = float(r[3])
            r[4] = float(r[4])
            r[5] = float(r[5])
            arr.append(r)

        arr_df = pd.DataFrame(arr)
        arr_df.index = pd.to_datetime(arr_df[0])
        arr_df = arr_df.drop(columns=[0])
        arr_df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        arr_df.index.name = "Date"

        try:  
            conn = self.connect_SQL_server()
            with conn.cursor() as cursor:
                command = f"""SELECT date, CASE 
                                WHEN result = '黃金交叉' THEN 1 
                                WHEN result = '死亡交叉' THEN -1 
                                ELSE 0 
                            END 
                            FROM FindKDCross( {company} )
                            where date >= '{startDate}' AND date <= '{endDate}'
                            order by date asc;"""
                cursor.execute(command)
                result = cursor.fetchall()
        except Exception as ex:
            print(ex)

        conn.close()

        arr_gold = []
        arr_dead = []

        for r in result:
            r = list(r)
            r[0] = r[0]
            r[1] = int(r[1])
            if r[1] == 1:
                arr_gold.append(r)
            else:
                arr_dead.append(r)
        if len( arr_gold ) > 0 :
            temp_df = pd.DataFrame(arr_gold)

            temp_df.index = pd.to_datetime(temp_df[0])
            temp_df = temp_df.drop(columns=[0])
            temp_df.columns = ['gold_or_dead']
            temp_df.index.name = "Date"

            arr_df['gold'] = temp_df['gold_or_dead']

            arr_df.loc[arr_df['gold'].notnull(), 'gold'] = arr_df['Close']
        else :
            arr_df = arr_df.assign(gold=pd.NA)

        if len( arr_dead ) > 0 :
            temp_df = pd.DataFrame(arr_dead)
            temp_df.index = pd.to_datetime(temp_df[0])
            temp_df = temp_df.drop(columns=[0])
            temp_df.columns = ['gold_or_dead']
            temp_df.index.name = "Date"

            arr_df['dead'] = temp_df['gold_or_dead']

            arr_df.loc[arr_df['dead'].notnull(), 'dead'] = arr_df['Close']
        else :
            arr_df = arr_df.assign(dead=pd.NA)

        gold_df = arr_df['gold']
        dead_df = arr_df['dead']


        result = self.sign
        arr_buy = []
        arr_sell = []
        result = result[result['stock_code'] == int(company)]
        result = result[result.columns[[0, 2]]]
        # print(result)
        for index, row in result.iterrows(): 
            r = list(row)
            # print(r)
            r[0] = datetime.strptime( r[0], "%Y-%m-%d").date()
            r[1] = int(r[1])
            if r[1] == 1:
                arr_buy.append(r)
            else:
                arr_sell.append(r)

        # print(arr_buy)
        arr_buy = list({tuple(item): item for item in arr_buy}.values())
        arr_sell = list({tuple(item): item for item in arr_sell}.values())
        # print(arr_buy)
        # print(arr_gold)
        # print(len(arr_buy), len(arr_sell), len(arr_gold), len(arr_dead))
        arr_buy = [item for item in arr_buy if item not in arr_gold]
        arr_sell = [item for item in arr_sell if item not in arr_dead]
        # print(len(arr_buy), len(arr_sell), len(arr_gold), len(arr_dead))


        if len( arr_buy ) > 0 :
            temp_df = pd.DataFrame(arr_buy)
            temp_df.index = pd.to_datetime(temp_df[0])
            temp_df = temp_df.drop(columns=[0])
            temp_df.columns = ['buy_or_sell']
            temp_df.index.name = "Date"
            # print(arr_df)
            # print(temp_df['buy_or_sell'])
            arr_df['buy'] = temp_df['buy_or_sell']

            arr_df.loc[arr_df['buy'].notnull(), 'buy'] = arr_df['Close']
        else :
            arr_df = arr_df.assign(buy=pd.NA)

        if len( arr_sell ) > 0 :
            temp_df = pd.DataFrame(arr_sell)
            temp_df.index = pd.to_datetime(temp_df[0])
            temp_df = temp_df.drop(columns=[0])
            temp_df.columns = ['buy_or_sell']
            temp_df.index.name = "Date"

            arr_df['sell'] = temp_df['buy_or_sell']

            arr_df.loc[arr_df['sell'].notnull(), 'sell'] = arr_df['Close']
        else :
            arr_df = arr_df.assign(sell=pd.NA)

        buy_df = arr_df['buy']
        sell_df = arr_df['sell']


        add = []

        if len( arr_buy ) > 0 :
            add.append( mpf.make_addplot(buy_df, type='scatter', markersize=150, marker='^', color = 'red') )

        if len( arr_sell ) > 0 :
            add.append( mpf.make_addplot(sell_df, type='scatter', markersize=150, marker='v', color = 'green') )
        if gold and len(arr_gold) > 0 :
            add.append( mpf.make_addplot(gold_df, type='scatter', markersize=150, marker='^', color = 'orange') )
        
        if dead and len(arr_dead) > 0 :
            add.append( mpf.make_addplot(dead_df, type='scatter', markersize=150, marker='v', color = 'black') )

        mc = mpf.make_marketcolors(up='r',
                                down='g',
                                edge='',
                                wick='inherit',
                                volume='inherit')
        s = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=mc)

        if( len(add) > 0 ):
            fig, ax = mpf.plot(arr_df, addplot=add, type='candle', style=s, returnfig=True)
        else :
            fig, ax = mpf.plot(arr_df, type='candle', style=s, returnfig=True)

        return fig, ax

    # 更新圖片
    def updateGraph( self, date, stockCode ):
        # print( stockCode )
        if ( stockCode != "all" ): # 如果選擇某個股票再去修改圖片
            self.show( date, stockCode )

    # 回傳目前交易紀錄
    def getDealRecord( self, stockCode ):
        
        if ( stockCode == "all" ):
            # return all record
            return self.stock_record
        # end if
        else :
            # return specific stock record
            return self.stock_record[ self.stock_record["stock_code"] == stockCode ]
        # end else
        
    # 更新交易紀錄(不含起始日)
    def updateDeal( self, startDay, endDay ) :
        currentDay = startDay + timedelta(days=1)
        while currentDay <= endDay:
            self.buy_and_sell_stock( currentDay ) # 處理某天的交易紀錄
            currentDay += timedelta(days=1)

    # 回傳今日買賣訊號
    def getTodaySign( self, date ):
        # 轉格式datetime->str
        date = date.strftime("%Y-%m-%d")
        return self.sign[ self.sign["date"] == date ]
    
    # 更新某個條件的顯示
    def updateCondition( self, condition, sign ):
        self.onDisplay[condition] = sign

    def getList(self):
        return self.__stockList

# class Stock

class Ui_MainWindow(object):
    def __init__(self) -> None:
        self.stock = Stock()
        self.currentDate = datetime.strptime( "2022-01-01", "%Y-%m-%d")
        self.endDate = datetime.strptime(self.stock.endDate, "%Y-%m-%d")
    
    # 依照stock設定股票選單
    def setStockChoice(self, translate):
        self.stockChoice = QtWidgets.QComboBox(self.centralwidget)
        self.stockChoice.setGeometry(QtCore.QRect(1170, 120, 141, 21))
        self.stockChoice.setObjectName("stockChoice")
        stockList = self.stock.getList()
        
        self.stockChoice.addItem("")
        self.stockChoice.setItemText(0, translate("MainWindow", "all"))
        self.stockChoice.setCurrentText(translate("MainWindow", "all"))

        for i in range( 0, len( stockList ) ):
            self.stockChoice.addItem("")
            self.stockChoice.setItemText(i+1, translate("MainWindow", stockList[i]))
        
        self.stockChoice.currentIndexChanged.connect(self.onStockChoiceChanged) # 設定監聽事件
        
    # 依現在日期+股票更新現在顯示的圖片
    def updateGraph(self) :
        selected_stock = self.stockChoice.currentText()
        self.stock.updateGraph( self.currentDate, selected_stock ) 
        self.resetGraph( "stockLine.png" )

    # 選擇股票觸發的事件, 切換更新股票
    def onStockChoiceChanged(self, index):
        self.updateGraph() # 圖片更新
        self.updateDeal( self.currentDate, self.currentDate )

    # 交易紀錄畫面更新
    def updateDeal( self, startDay, endDay ):
        self.stock.updateDeal( startDay, endDay ) # 更新股票交易

        selected_stock = self.stockChoice.currentText()
        df = self.stock.getDealRecord( selected_stock ) # 獲取交易紀錄

        # 設定格式
        self.record.setRowCount(df.shape[0])
        self.record.setColumnCount(df.shape[1])
        self.record.setHorizontalHeaderLabels(df.columns)

        # 遍历结果的每一行和每一列
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                # 获取每个单元格的值，并将其添加到表格中
                item = QtWidgets.QTableWidgetItem(str(df.iloc[row, col]))
                self.record.setItem(row, col, item)


        # 调整表格的大小，使其适应内容
        self.record.resizeColumnsToContents()
        self.record.resizeRowsToContents()

        # 显示 QTableWidget
        self.record.show()

    # 依照現在stock顯示股票趨勢圖
    def setGraph(self, translate):   
        self.graphicsView = QtWidgets.QLabel(self.centralwidget) 
        self.graphicsView.setGeometry(QtCore.QRect(20, 190, 1011, 641))
        self.graphicsView.setObjectName("graphicsView")

        self.resetGraph()

    # 讀入圖片
    def resetGraph(self, path=None):        
        if path == None:
            pass
        else:
            # 設置圖片對齊方式
            self.graphicsView.setAlignment(QtCore.Qt.AlignCenter)  # 將圖片居中對齊
            
            # 加載並將圖片縮放成框的大小一致
            pixmap = QPixmap(path)
            scaled_pixmap = pixmap.scaled(self.graphicsView.size(), QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
            self.graphicsView.setPixmap(scaled_pixmap)

    # 日期與切換按鍵
    def setTimeChange(self, translate):

        # 日期顯示
        self.date = QtWidgets.QLabel(self.centralwidget)
        self.date.setGeometry(QtCore.QRect(20, 30, 251, 41))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(24)
        self.date.setFont(font)
        self.date.setObjectName("date")
        self.date.setText(str(self.currentDate.strftime("%Y-%m-%d")))

        # 下一天 按鍵
        self.nextDay = QtWidgets.QPushButton(self.centralwidget)
        self.nextDay.setGeometry(QtCore.QRect(1290, 790, 71, 28))
        self.nextDay.setObjectName("nextDay")
        self.nextDay.setText(translate("MainWindow", "下一天"))
        self.nextDay.clicked.connect(self.chanageDay)

        # 下個月 按鍵
        self.nextMonth = QtWidgets.QPushButton(self.centralwidget)
        self.nextMonth.setGeometry(QtCore.QRect(1390, 790, 71, 28))
        self.nextMonth.setObjectName("nextMonth")
        self.nextMonth.setText(translate("MainWindow", "下個月"))
        self.nextMonth.clicked.connect(self.chanageMonth)

        # 下一年 按鍵
        self.nextYear = QtWidgets.QPushButton(self.centralwidget)
        self.nextYear.setGeometry(QtCore.QRect(1480, 790, 71, 28))
        self.nextYear.setObjectName("nextYear")
        self.nextYear.setText(translate("MainWindow", "下一年"))
        self.nextYear.clicked.connect(self.chanageYear)

    # 日期改變時會觸發的事件
    def timeChange( self, startDay, endDay ):
        self.updateGraph() # 更新股票趨勢圖
        self.updateTodaySign() # 更新今日買賣訊號
        self.updateDeal( startDay, endDay ) # 更新股票交易

    # 下一天
    def chanageDay(self):
        startDay = self.currentDate

        if(self.currentDate + timedelta(days = 1) < self.endDate):
            self.currentDate = self.currentDate + timedelta(days = 1)
        self.date.setText(str(self.currentDate.strftime("%Y-%m-%d")))

        endDay = self.currentDate
        self.timeChange( startDay, endDay )

    # 下個月
    def chanageMonth(self):
        startDay = self.currentDate

        if(self.currentDate + relativedelta(months=1) < self.endDate):
            self.currentDate = self.currentDate + relativedelta(months=1)
        self.date.setText(str(self.currentDate.strftime("%Y-%m-%d")))

        endDay = self.currentDate
        self.timeChange( startDay, endDay )

    # 下一年
    def chanageYear(self):
        startDay = self.currentDate

        if(self.currentDate + relativedelta(years=1) < self.endDate):
            self.currentDate = self.currentDate + relativedelta(years=1)   
        self.date.setText(str(self.currentDate.strftime("%Y-%m-%d")))

        endDay = self.currentDate
        self.timeChange( startDay, endDay )

    # 設定文本內容
    def setContext(self, translate):

        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(1070, 120, 120, 21))
        self.label.setObjectName("label")
        self.label.setText(translate("MainWindow", "股票選單："))

        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(1070, 150, 151, 16))
        self.label_2.setObjectName("label_2")
        self.label_2.setText(translate("MainWindow", "交易紀錄："))
        
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(30, 120, 91, 16))
        self.label_3.setObjectName("label_3")
        self.label_3.setText(translate("MainWindow", "篩選條件："))

        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(30, 150, 91, 16))
        self.label_4.setObjectName("label_4")
        self.label_4.setText(translate("MainWindow", "股票趨勢："))

    # 篩選條件的觸發事件
    def onConditionChange(self, name, state):
        self.stock.updateCondition( name, bool(state) ) # 更新股票狀態
        self.updateGraph() # 更新股票趨勢圖

    # 設定篩選條件
    def setCondition(self, translate):
        self.goldCross = QtWidgets.QCheckBox(self.centralwidget)
        self.goldCross.setGeometry(QtCore.QRect(120, 120, 85, 19))
        self.goldCross.setObjectName("goldCross")
        self.goldCross.setText(translate("MainWindow", "黃金交叉"))
        self.goldCross.stateChanged.connect( lambda state: self.onConditionChange('goldCross', state) )
        self.deadCross = QtWidgets.QCheckBox(self.centralwidget)
        self.deadCross.setGeometry(QtCore.QRect(220, 120, 85, 19))
        self.deadCross.setObjectName("deadCross")
        self.deadCross.setText(translate("MainWindow", "死亡交叉"))
        self.deadCross.stateChanged.connect( lambda state: self.onConditionChange('deadCross', state) )
    
    # 設定交易紀錄
    def setRecord(self, translate):
        # 交易紀錄
        self.record = QtWidgets.QTableWidget(self.centralwidget)
        self.record.setGeometry(QtCore.QRect(1070, 190, 491, 561))
        self.record.setObjectName("record")

    # 設定今日買賣訊號
    def setTodaySign(self, translate):
        self.signList = QtWidgets.QListWidget(self.centralwidget)
        self.signList.setGeometry(QtCore.QRect(370, 70, 661, 91))
        self.signList.setObjectName("signList")
        
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(370, 40, 111, 21))
        self.label_5.setObjectName("label_5")
        self.label_5.setText(translate("MainWindow", "今日買賣訊號："))
        self.updateTodaySign()

    def updateTodaySign(self):
        df = self.stock.getTodaySign( self.currentDate ) 
        self.signList.clear()
        if ( df.empty ): # 今日無訊號
            self.signList.addItem("無")
        else:
            for index, row in df.iterrows():
                stock_code = str(row["stock_code"])
                buy_or_sell = str(row["buy_or_sell"])
                self.signList.addItem("股票代碼: " + stock_code + " 買賣訊號: " + buy_or_sell)    
        self.signList.show()


    # 介面設定
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1600, 900)
        
        translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(translate("MainWindow", "MainWindow"))

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.setContext(translate) # 設定文本

        self.setCondition(translate) # 設定篩選條件

        self.setStockChoice(translate) # 設定股票選單

        self.setGraph(translate) # 設定股票趨勢圖

        self.setTimeChange(translate) # 設定日期相關

        self.setRecord(translate) # 設定交易紀錄

        self.setTodaySign(translate) # 設定今日買賣訊號
        

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1600, 25))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    

    MainWindow.show()
    sys.exit(app.exec_())

