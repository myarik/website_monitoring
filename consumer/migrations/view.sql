CREATE VIEW avg_stats AS select
  url,
  avg(avg_load_time) filter (where hour is not null) as avg_hour,
  avg(avg_load_time) filter (where day is not null) as avg_day,
  avg(avg_load_time) filter (where month is not null) as avg_month
from (select
           url,
           date_trunc('hour', request_date) as hour,
           date_trunc('day', request_date) as day,
           date_trunc('month', request_date) as month,
           avg(load_time) as avg_load_time
     from monitoring group by grouping sets ((url, hour), (url, day), (url, month))
) s group by url

-- hour history
CREATE VIEW hour_statistics as select url, date_trunc('hour', request_date) as hour, avg(load_time) as load_time from monitoring group by url, hour;