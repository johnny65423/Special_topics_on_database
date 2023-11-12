ALTER PROCEDURE [dbo].[practice3]
	@Date date,
	@days_num int
as
begin
	set nocount on;
	select stock_code from (
	select stock_code, count(*) days_num from price_history
	where date in (
		select date
		from find_date(@Date, @days_num, 1 ,0)
	) and d >= 0
	group by stock_code
	) allnotdown
	where allnotdown.days_num = 3
end

--exec practice3 '2022-12-22', 3