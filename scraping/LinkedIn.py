import datetime

import bs4
import pandas as pd
import requests
import time

from bs4 import BeautifulSoup

from scraping.Scraper import Scraper


class LinkedInScraper(Scraper):

	def scrape(self):
		# Column titles used to save in csv
		columns = ['job_title', 'company_name', 'location', 'summary', 'duration_since_post', 'apply_link']
		sample_df = pd.DataFrame(columns=columns)

		# Parse query string and insert into relevant url search format
		job = self._query.split()
		URL = 'https://au.linkedin.com/jobs/internship-jobs?position=1&pageNum=0'

		# Get page source code
		page = requests.get(URL)
		# Parse page
		soup = BeautifulSoup(page.text, 'html.parser')

		# This next whole loop is very specific to the website you're scraping
		i = 0
		for div in soup.find_all(name='li',
								 attrs={'class': 'result-card job-result-card result-card--with-hover-state'}):
			# Specifying row num for index of job posting in dataframe
			num = (len(sample_df) + 1)

			# Creating an empty list to hold the data for each posting
			job_post = {}

			# Grabbing job title
			job_post['job_title'] = div.find(name='span', attrs={'class': 'screen-reader-text'}).get_text()
			print(job_post['job_title'])

			if 'job_title' not in job_post:
				job_post['job_title'] = 'NO JOB_TITLE'

			# Grabbing company name
			# print(div.find(name='a', attrs={'class': 'result-card__subtitle-link job-result-card__subtitle-link'}))
			#
			# if 'company_name' not in job_post:
			# 	job_post['company_name'] = 'NO COMPANY_NAME'

	#
	# # Grabbing location name
	# result = div.find_all(name='span', attrs={'class': 'location'})
	# for span in result:
	#     job_post['location'] = span.text
	# if 'location' not in job_post:
	#     job_post['location'] = 'NO LOCATION'
	#
	# # Grabbing summary text
	# d = div.find_all(name='div', attrs={'class': 'summary'})
	# for result in d:
	#     job_post['summary'] = result.text.strip()
	# if 'summary' not in job_post:
	#     job_post['summary'] = 'NO SUMMARY'
	#
	# # Grabbing duration since post
	# result = div.find_all(name='span', attrs={'class':'date'})
	# for span in result:
	#     job_post['duration_since_post'] = span.text
	# if 'duration_since_post' not in job_post:
	#     job_post['duration_since_post'] = 'NO DURATION_SINCE_POST'
	#
	# # Grabbing link to apply
	# job_post['apply_link'] = self._scrape_apply_link(temp_link)
	# if job_post['apply_link'] == 'NO APPLY_LINK':
	#     job_post['apply_link'] = 'https://au.indeed.com' + temp_link
	#
	# # Appending list of job post info to dataframe at index num
	# sample_df.loc[num] = job_post
	#
	# # Check if there is another page to scrape
	# terminate = True
	# for div in soup.find_all(name='div', attrs={'class':'pagination'}):
	#     for span in soup.find_all(name='span', attrs={'class':'np'}):
	#         if span.text.strip() == 'Next »':
	#             terminate = False
	# if terminate:
	#     break

	# # Saving sample_df as a local csv file — define your own local path to save contents
	# file_path = 'scraping/listings/indeed_'
	# for word in job:
	# 	if job.index(word) > 0:
	# 		file_path += '_'
	# 	file_path += word
	# file_path += '.csv'
	# sample_df.to_csv(file_path, encoding='utf-8')

	# TODO Save to database once setup
	def save_to_db(self):
		pass


hi = LinkedInScraper("hi")
hi.scrape()
