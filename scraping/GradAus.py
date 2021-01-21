import datetime

import bs4
import pandas as pd
import requests
import time

from bs4 import BeautifulSoup

from scraping.Scraper import Scraper


class GradAusScraper(Scraper):

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
				jobType += '+'
				flag = True
		else:
			jobType = self._jobType
		URL = 'https://gradaustralia.com.au/search-jobs?opportunity_types=' + jobType + '&study_field_tids=' + self._industry + '&default=1&start='

		# Scrape through a maximum of 100 pages
		# NOTE: Indeed increments pages in url by 10 which is why we iterate by 10 here
		for start in range(0, 800, 8):
			# Ensuring at least 1 second between page grabs to prevent us from getting blocked by the website
			time.sleep(1)

			print(f'Scraping page {int(start/8 + 1)}')

			# Get page source code
			page = requests.get(URL + str(start))
			# Parse page
			soup = BeautifulSoup(page.text, 'html.parser')

			# This next whole loop is very specific to the website you're scraping
			for div in soup.find_all(name='div', attrs={'class': 'Boxstyle__Box-sc-1jxggr3-0 Teaserstyle__Teaser-egwky8-0 OpportunityTeaserstyle__OpportunityListing-sc-1vbfrdq-0 cqpUPt'}):

				print("--------------------")
				# Specifying row num for index of job posting in dataframe
				num = (len(sample_df) + 1)

				# Creating an empty list to hold the data for each posting
				job_post = {}

				# Grabbing job title
				flag = False
				for result in div.find_all(name='a'):
					if not flag:
						flag = True
					else:
						job_post['job_title'] = result.get_text()
						print(job_post['job_title'])

						# Apply link
						temp_link = 'https://gradaustralia.com.au' + result.attrs['href']
						break

				if 'job_title' not in job_post:
					job_post['job_title'] = 'NO JOB_TITLE'

				# Grabbing company name
				job_post['company_name'] = div.find(name='p').get_text()
				print(job_post['company_name'])

				if 'company_name' not in job_post:
					job_post['company_name'] = 'NO COMPANY_NAME'

				# Grabbing location name
				result = div.find_all(name='div', attrs={'class': 'Bylinestyle__Byline-sc-1fgjca9-0 fooXca byline'})
				for span in result:
					job_post['location'] = span.text
					print(span.text)
				if 'location' not in job_post:
					job_post['location'] = 'NO LOCATION'

				# Grabbing summary text
				d = div.find_all(name='div', attrs={'class': 'teaser__item teaser__item--overview'})
				for result in d:
					job_post['summary'] = result.text.strip()
					print(result.text)
				if 'summary' not in job_post:
					job_post['summary'] = 'NO SUMMARY'

				# Grabbing link to apply
				jlink= div.find_all(name='a', attrs={'class': 'Buttonstyle__Button-rtiawy-0 gBOixf button button--type-apply'})

				if jlink is not None:
					for j in jlink:
						job_post['apply_link'] = j.attrs['href']
						break

				if 'apply_link' not in job_post:
					job_post['apply_link'] = temp_link
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

				# Set industry
				# TODO: need to make dictionary with key value pairs for URL num and saving in industry as field as string
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
		file_path = 'scraping/listings/gradaus.csv'
		sample_df.to_csv(file_path, encoding='utf-8')

	# TODO Save to database once setup
	def save_to_db(self):
		pass


hi = GradAusScraper("Graduate Job", "")
hi.scrape()
