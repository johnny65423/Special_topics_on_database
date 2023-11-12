declare @day_cnt INT

select @day_cnt = day_of_stock
from calendar 
where date = '2022-12-22'



select date from calendar
where year(date) = year('2022-12-22')
and @day_cnt - day_of_stock between 0 and 4
and day_of_stock != -1