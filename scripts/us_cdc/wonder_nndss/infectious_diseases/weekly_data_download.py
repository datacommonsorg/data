import datetime
import time
import os
import requests
import pandas as pd
from absl import flags, app
from bs4 import BeautifulSoup

_START = 2014 #1996
_END = datetime.date.today().year + 1 #to make the last year inclusive

# template_url: https://wonder.cdc.gov/nndss/nndss_weekly_tables_menu.asp?mmwr_year=2019&mmwr_week=52
_BASE_URL = "https://wonder.cdc.gov/nndss/"
_WEEKLY_TABLE = _BASE_URL + "nndss_weekly_tables_menu.asp?mmwr_year={year}&mmwr_week={week}"

def scrape_table_from_page(page_url, output_path):
	page = requests.get(page_url)
	soup = BeautifulSoup(page.content, 'html.parser')
	# get link to all tables in the page
	table_link_list = [tag.find("a")["href"] for tag in soup.select("td:has(a)")]
	for table_link in table_link_list:
		# select requestMode=Submit
		if 'Submit' in table_link:
			table_url = _BASE_URL + table_link
			print(f"Downloading {table_url}", end=" ..... ", flush=True)
			table_content = requests.get(table_url)
			t_soup = BeautifulSoup(table_content.content, 'html.parser')
			try:
				table_result_set = t_soup.find_all('table')[1]
				df = pd.read_html(table_result_set.prettify())[0]
				# extract filename from link patterns like https://wonder.cdc.gov/nndss/nndss_reps.asp?mmwr_year=1996&mmwr_week=01&mmwr_table=2A&request=Submit
				filename = table_url.split('?')[1].split('&request')[0].replace('=', '_').replace('&', '_')
				# save the file in output path for each file
				df.to_csv(os.path.join(output_path, f'{filename}.csv'), index=False)
				print("Done.", flush=True)
			except IndexError:
				print("Terminated with error. Please check the link.", flush=True)
				continue
			time.sleep(2)

def download_weekly_nnds_data_across_years(year_range, output_path):
	output_path = os.path.join(output_path, './nndss_weekly_data')
	if not os.path.exists(output_path):
		os.makedirs(output_path)
	for year in year_range:
		week_range = [str(x).zfill(2) for x in range(1,52)]
		if year % 4 == 0:
			week_range = [str(x).zfill(2) for x in range(1,53)]
		for week in week_range:
			index_url = _WEEKLY_TABLE.format(year=year, week=week)
			print(f"Fetching data from {index_url}")
			scrape_table_from_page(index_url, output_path)

def get_next_week(year, output_path):
	all_files_in_dir = os.listdir(output_path)
	files_of_year = [files for files in all_files_in_dir if str(year) in files]
	last_downloaded_file = files_of_year[-1]
	week = last_downloaded_file.split('_mmwr_week_')[1].split('_mmwr_table')[0]
	return int(week) + 1

def download_latest_weekly_nndss_data(year, output_path):
	week = get_next_week(year, output_path)
	index_url = _WEEKLY_TABLE.format(year=year, week=week)
	print(f"Fetching data from {index_url}")
	scrape_table_from_page(index_url, output_path)

def main(_) -> None:
	FLAGS = flags.FLAGS
	flags.DEFINE_string(
		'output_path', './data',
		'Path to the directory where generated files are to be stored.')
	year_range = range(_START, _END)
	download_weekly_nnds_data_across_years(year_range, FLAGS.output_path)

if __name__ == '__main__':
	app.run(main)
