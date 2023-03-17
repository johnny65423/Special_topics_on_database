declare @day_cnt INT

select @day_cnt = day_of_stock
from calendar 
where date = '2022-12-22'

select stock_code, count(*) cnt, string_agg(date, ',') date, string_agg(d, ',') d from price_history
where exists(
select date from calendar
where price_history.date = calendar.date 
and year(date) = year('2022-12-22')
and @day_cnt - day_of_stock between 0 and 4
and day_of_stock != -1
) and d > 0
group by stock_code