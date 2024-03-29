USE [ncu_database]
GO
/****** Object:  UserDefinedFunction [dbo].[find_date]    Script Date: 2023/3/13 下午 03:00:58 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER function [dbo].[find_date] (@Init_date date, @days_num int, @Include_today int, @Back int )
returns @Return_table table (
	date date,
	day_of_stock int,
	other nvarchar(50)
)
as
begin
	declare @day_cnt INT
	declare @year INT

	select @day_cnt = day_of_stock, @year = CONVERT(INT, YEAR(date))
	from calendar 
	where date = @Init_date

	insert @Return_table
	select * from calendar
	where year(date) = year(@Init_date)
	--and @day_cnt - day_of_stock between 0 and 4
	and day_of_stock != -1

	and (
			(
			@Back = 0 and
				@day_cnt - calendar.day_of_stock between 1 - @Include_today and @days_num-1
				--dbo.count_days(@Init_date) - dbo.count_days(calendar.date) between 1 - @Include_today and @days_num-1
			)
			or
			(
			@Back = 1 and
				calendar.day_of_stock -@day_cnt between 1 - @Include_today and @days_num-1
				--dbo.count_days(calendar.date) - dbo.count_days(@Init_date) between 1 - @Include_today and @days_num-1
			)

	)

	return;
end