import datetime

import bs4
import pandas as pd
import requests
import time

from bs4 import BeautifulSoup

from scraping.Scraper import Scraper
from scraping.Scraper import Scraper
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

class GradConnScraper(Scraper):

	def scrape(self):
		# Column titles used to save in csv
		columns = ['job_title', 'company_name', 'location', 'summary', 'apply_link', 'job_type', 'industry', 'active','post_date']
		sample_df = pd.DataFrame(columns=columns)

		# Parse query string and insert into relevant url search format
		jobt = self._jobType.split()
		if len(jobt) > 1:
			flag = False
			jobType = ""
			for word in jobt:
				jobType += word
				if flag:
					break
				jobType += '-'
				flag = True
		else:
			jobType = self._jobType
		URL = 'https://au.gradconnection.com/' + jobType + '/'

		# Load all contents of web page before scraping with scroll down selector
		driver = webdriver.Chrome(ChromeDriverManager().install())
		driver.get(URL)

		SCROLL_PAUSE_TIME = 30

		# Get scroll height
		last_height = driver.execute_script("return document.body.scrollHeight")

		while True:
			# Scroll down to bottom
			driver.execute_script("window.scrollTo(0, document.body.scrollHeight-1000);")

			# Wait to load page
			time.sleep(SCROLL_PAUSE_TIME)

			# Calculate new scroll height and compare with last scroll height
			new_height = driver.execute_script("return document.body.scrollHeight")
			soup = BeautifulSoup(driver.page_source, 'html.parser')

			if new_height == last_height:
				break
			last_height = new_height

			# This next whole loop is very specific to the website you're scraping
			i = 0
			for div in soup.find_all(name='div', attrs={'class': 'outer-container'}):
				print(i)
				i = i+1
				# Specifying row num for index of job posting in dataframe
				num = (len(sample_df) + 1)

				# Creating an empty list to hold the data for each posting
				job_post = {}

				# Grabbing job title
				job_post['job_title'] = div.find(name='h5', attrs={'class': 'list-item-title'}).get_text() + ' Internship'
				print(job_post['job_title'])

				if 'job_title' not in job_post:
					job_post['job_title'] = 'NO JOB_TITLE'

				# Grabbing company name
				job_post['company_name'] = div.find(name='h5', attrs={'class': 'list-item-title'}).get_text()
				print(job_post['company_name'])

				if 'company_name' not in job_post:
					job_post['company_name'] = 'NO COMPANY_NAME'

				# Grabbing location name
				job_post['location'] = div.find(name='p', attrs={'class': 'list-item-opportunities-country floatright'}).get_text()
				print(job_post['location'])

				if 'location' not in job_post:
					job_post['location'] = 'NO LOCATION'

				# Grabbing summary text
				job_post['summary'] = div.find(name='div', attrs={'class': 'ellipsis-text-paragraph'}).get_text()
				print(job_post['summary'])

				if 'summary' not in job_post:
					job_post['summary'] = 'NO SUMMARY'

				# Grabbing link to apply
				job_post['apply_link'] = 'https://au.gradconnection.com' + div.find(name='a').attrs['href']
				print(job_post['apply_link'])

				# Grabbing duration since post
				job_post['post_date'] = datetime.datetime.now()
				if 'post_date' not in job_post:
					job_post['post_date'] = 'NO POST_DATE'

				# Set listing to active
				job_post['active'] = True

				# Set job type
				job = self._jobType.split()
				for word in job:
					job_post['job_type'] = word
					break
				print(job_post['job_type'])

				# TODO: Set industry
				job_post['industry'] = True

				# Appending list of job post info to dataframe at index num
				sample_df.loc[num] = job_post

			# Check if there is another page to scrape
			terminate = True
			if soup.find(name='li', attrs={'class': 'pagination-item pagination-item--direction pagination-item--direction-next'}):
				terminate = False
			if terminate:
				break

		# Saving sample_df as a local csv file — define your own local path to save contents
		# file_path = 'scraping/listings/gradconn.csv'
		# sample_df.to_csv(file_path, encoding='utf-8')

	# TODO Save to database once setup
	def save_to_db(self):
		pass


hi = GradConnScraper("graduate jobs", "")
hi.scrape()
