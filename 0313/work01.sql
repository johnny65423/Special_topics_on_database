declare @day_cnt INT

select @day_cnt = day_of_stock
from calendar 
where date = '2022-01-18'

select result.d, string_agg(stock_info.name, ',') Company, @day_cnt StockDays from
(
	select d , stock_code from price_history
	where 
	date = '2022-01-18'
	and ( d between -1 and 1 )
) result, stock_info
where result.stock_code = stock_info.stock_code
group by result.d
order by d desc
