import datetime
import pandas as pd

start = 1996
end = datetime.date.today().year + 1 #to make the last year inclusive
year_range = range(start, end)

# template_url: https://wonder.cdc.gov/nndss/nndss_weekly_tables_menu.asp?mmwr_year=2019&mmwr_week=52
_BASE_URL = "https://wonder.cdc.gov/nndss/nndss_weekly_tables_menu.asp?mmwr_year={year}&mmwr_week={week}"

for year in year_range:
	week_range = range(1, 52)
	if year % 4 == 0:
		week_range = range(1, 53)
	for week in week_range:
		index_url = _BASE_URL.format(year=year, week=week)
		print(index_url)
		
