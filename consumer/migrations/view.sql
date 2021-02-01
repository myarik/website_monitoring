CREATE VIEW avg_stats AS select
  url,
  avg(total) filter (where hour is not null) as avg_hour,
  avg(total) filter (where day is not null) as avg_day,
  avg(total) filter (where month is not null) as avg_month
from (select
           url,
           date_trunc('hour', request_date) as hour,
           date_trunc('day', request_date) as day,
           date_trunc('month', request_date) as month,
           sum(load_time) as total
     from monitoring group by grouping sets ((url, hour), (url, day), (url, month))
) s group by url

-- hour history
CREATE VIEW hour_statistics as select url, date_trunc('hour', request_date) as hour, avg(load_time) as load_time from monitoring group by url, hour;