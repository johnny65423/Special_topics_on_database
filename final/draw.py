import mplfinance as mpf
import pymssql
import json
import pandas as pd
import numpy as np

db_settings = {
    "host": "127.0.0.1",
    "port": 1433,
    "user": "johnnyhsu",
    "password": "12345678",
    "database": "ncu_database",
    "charset": "UTF-8"
}
def drawPlot( company, gold, dead, startDate, endDate ):
    result = []
    try:  
        conn = pymssql.connect(**db_settings)
        with conn.cursor() as cursor:
            command = f"""SELECT date, o, h, l, c, v FROM price_history WHERE stock_code = {company}
                        and date >= '{startDate}' AND date < '{endDate}' order by date asc;"""
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
    arr_df

    try:  
        conn = pymssql.connect(**db_settings)
        with conn.cursor() as cursor:
            command = f"""SELECT date, buy_or_sell FROM GB_rule({company})
                    where date >= '{startDate}' AND date < '{endDate}' order by date asc;"""
            cursor.execute(command)
            result = cursor.fetchall()
    except Exception as ex:
        print(ex)

    conn.close()

    arr_buy = []
    arr_sell = []

    for r in result:
        r = list(r)
        r[0] = r[0]
        r[1] = int(r[1])
        if r[1] == 1:
            arr_buy.append(r)
        else:
            arr_sell.append(r)

    if len( arr_buy ) > 0 :
        temp_df = pd.DataFrame(arr_buy)
        temp_df.index = pd.to_datetime(temp_df[0])
        temp_df = temp_df.drop(columns=[0])
        temp_df.columns = ['buy_or_sell']
        temp_df.index.name = "Date"

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

    try:  
        conn = pymssql.connect(**db_settings)
        with conn.cursor() as cursor:
            command = f"""SELECT date, CASE WHEN result = '黃金交叉' THEN 1 WHEN result = '死亡交叉' THEN -1 ELSE 0 END FROM FindKDCross( {company} )
                        where date >= '{startDate}' AND date < '{endDate}'
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

if __name__ == '__main__' :
    fig, ax = drawPlot('2317' ,1 ,1 , '2022-01-01', '2022-06-30')
    fig.savefig('2317_0_0.png')
