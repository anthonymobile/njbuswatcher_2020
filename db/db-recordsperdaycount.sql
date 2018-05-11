SELECT    YEAR(Timestamp) AS 'Year',
          MONTH(Timestamp) AS 'Month',
          DAY(Timestamp) AS 'Day',
          COUNT(*) AS 'Position Reports'
FROM      positions
GROUP BY  DAY(Timestamp),
          MONTH(Timestamp),
          YEAR(Timestamp)
ORDER BY  'Year',
          'Month',
          'Day';