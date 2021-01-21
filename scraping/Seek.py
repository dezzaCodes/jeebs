import bs4
import pandas as pd
import requests
import time

from bs4 import BeautifulSoup

from scraping.Scraper import Scraper


class SeekScraper(Scraper):

    def scrape(self):
        # Column titles used to save in csv
        columns = ['job_title', 'company_name', 'location', 'summary', 'duration_since_post', 'apply_link']
        sample_df = pd.DataFrame(columns = columns)

        # Parse query string and insert into relevant url search format
        job = self._query.split()
        URL = 'https://www.seek.com.au/'
        for word in job:
            if job.index(word) > 0:
                URL += '-'
            URL += word
        URL += '-jobs'
        URL += '?page='

        # Scrape through a maximum of 100 pages
        for start in range(1, 100, 1):
            # Ensuring at least 1 second between page grabs to prevent us from getting blocked by the website
            time.sleep(1)

            print(f'Scraping page {start}')

            # Get page source code
            page = requests.get(URL + str(start))
            # Parse page
            soup = BeautifulSoup(page.text, 'html.parser')
            
            # This next whole loop is very specific to the website you're scraping
            for div in soup.find_all(name='article', attrs={'data-automation':'normalJob'}): 

                # Specifying row num for index of job posting in dataframe
                num = (len(sample_df) + 1) 
                
                # Creating an empty list to hold the data for each posting
                job_post = {}
                
                # Grabbing job title
                for result in div.find_all(name='a', attrs={'data-automation':'jobTitle'}):
                    job_post['job_title'] = result.text
                    temp_link = result['href']
                if 'job_title' not in job_post:
                    job_post['job_title'] = 'NO JOB_TITLE'
                
                # Grabbing company name
                for result in div.find_all(name='a', attrs={'class':'_3AMdmRg'}):
                    job_post['company_name'] = result.text.strip()
                if 'company_name' not in job_post:
                    job_post['company_name'] = 'NO COMPANY_NAME'
                
                # Grabbing location name
                result = div.find_all(name='a', attrs={'data-automation': 'jobLocation'}) 
                for span in result: 
                    job_post['location'] = span.text
                if 'location' not in job_post:
                    job_post['location'] = 'NO LOCATION'

                # Grabbing summary text
                d = div.find_all(name='span', attrs={'class': 'bl7UwXp'}) 
                for result in d:
                    job_post['summary'] = result.text.strip() 
                if 'summary' not in job_post:
                    job_post['summary'] = 'NO SUMMARY'

                # Grabbing duration since post
                result = div.find_all(name='span', attrs={'data-automation':'jobListingDate'})
                for span in result:
                    job_post['duration_since_post'] = span.text
                if 'duration_since_post' not in job_post:
                    job_post['duration_since_post'] = 'NO DURATION_SINCE_POST'

                # Grabbing link to apply
                job_post['apply_link'] = 'https://seek.com.au' + temp_link

                # Appending list of job post info to dataframe at index num
                sample_df.loc[num] = job_post

            # Check if there is another page to scrape
            terminate = True
            result = soup.find_all(name='a', attrs={'data-automation':'page-next'})
            if result:
                terminate = False
            if terminate:
                break

        # Saving sample_df as a local csv file — define your own local path to save contents 
        file_path = 'scraping/listings/seek_' 
        for word in job:
            if job.index(word) > 0:
                file_path += '_'
            file_path += word
        file_path += '.csv'
        sample_df.to_csv(file_path, encoding='utf-8')

    # TODO Save to database once setup
    def save_to_db(self):
        pass
