CREATE FUNCTION find_date (@start_date date, @range int)
RETURNS @result TABLE (workday_date date)
AS
BEGIN
    DECLARE @i int = 0, @day_of_stock int = 0
    
    WHILE @i < @range
    BEGIN
        SELECT @day_of_stock = day_of_stock FROM calendar WHERE date = @start_date
        
        IF @day_of_stock > 0
        BEGIN
            INSERT INTO @result (workday_date) VALUES (@start_date)
            SET @i += 1
        END
        
        SET @start_date = DATEADD(day, 1, @start_date)
    END
    
    RETURN
END
使用方法：

sql
Copy code
SELECT * FROM find_date('2022-12-22', 10)
這會返回一個包含指定日期範圍內工作日的列表，類似這樣：

yaml
Copy code
workday_date
------------
2022-12-23
2022-12-26
2022-12-27
2022-12-28
2022-12-29
2022-12-30
2023-01-02
2023-01-03
2023-01-04
2023-01-05




