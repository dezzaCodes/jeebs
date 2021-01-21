import bs4
import pandas as pd
import requests
import time

from bs4 import BeautifulSoup

from scraping.Scraper import Scraper


class IndeedScraper(Scraper):

    def scrape(self):
        # Column titles used to save in csv
        columns = ['job_title', 'company_name', 'location', 'summary', 'duration_since_post', 'apply_link']
        sample_df = pd.DataFrame(columns = columns)

        # Parse query string and insert into relevant url search format
        job = self._query.split()
        URL = 'https://au.indeed.com/jobs?q='
        for word in job:
            if job.index(word) > 0:
                URL += '+'
            URL += word
        URL += '&start='

        # Scrape through a maximum of 100 pages
        # NOTE: Indeed increments pages in url by 10 which is why we iterate by 10 here
        for start in range(0, 1000, 10):
            # Ensuring at least 1 second between page grabs to prevent us from getting blocked by the website
            time.sleep(1)

            print(f'Scraping page {int(len(sample_df) / 10 + 1)}')

            # Get page source code
            page = requests.get(URL + str(start))
            # Parse page
            soup = BeautifulSoup(page.text, 'html.parser')
            
            # This next whole loop is very specific to the website you're scraping
            for div in soup.find_all(name='div', attrs={'class':'jobsearch-SerpJobCard'}): 
                if div.find_all(name='span', attrs={'class': 'sponsoredGray'}):
                    continue

                # Specifying row num for index of job posting in dataframe
                num = (len(sample_df) + 1) 
                
                # Creating an empty list to hold the data for each posting
                job_post = {}
                
                # Grabbing job title
                for result in div.find_all(name='a', attrs={'data-tn-element':'jobTitle'}):
                    job_post['job_title'] = result['title']
                    temp_link = result['href']

                if 'job_title' not in job_post:
                    job_post['job_title'] = 'NO JOB_TITLE'
                
                # Grabbing company name
                company = div.find_all(name='span', attrs={'class':'company'}) 
                if len(company) > 0: 
                    for result in company:
                        job_post['company_name'] = result.text.strip()
                else: 
                    sec_try = div.find_all(name='span', attrs={'class':'result-link-source'})
                    for span in sec_try:
                        job_post['company_name'] = span.text
                if 'company_name' not in job_post:
                    job_post['company_name'] = 'NO COMPANY_NAME'
                
                # Grabbing location name
                result = div.find_all(name='span', attrs={'class': 'location'}) 
                for span in result: 
                    job_post['location'] = span.text
                if 'location' not in job_post:
                    job_post['location'] = 'NO LOCATION'

                # Grabbing summary text
                d = div.find_all(name='div', attrs={'class': 'summary'}) 
                for result in d:
                    job_post['summary'] = result.text.strip() 
                if 'summary' not in job_post:
                    job_post['summary'] = 'NO SUMMARY'

                # Grabbing duration since post
                result = div.find_all(name='span', attrs={'class':'date'})
                for span in result:
                    job_post['duration_since_post'] = span.text
                if 'duration_since_post' not in job_post:
                    job_post['duration_since_post'] = 'NO DURATION_SINCE_POST'

                # Grabbing link to apply
                job_post['apply_link'] = self._scrape_apply_link(temp_link)
                if job_post['apply_link'] == 'NO APPLY_LINK':
                    job_post['apply_link'] = 'https://au.indeed.com' + temp_link

                # Appending list of job post info to dataframe at index num
                sample_df.loc[num] = job_post

            # Check if there is another page to scrape
            terminate = True
            for div in soup.find_all(name='div', attrs={'class':'pagination'}):
                for span in soup.find_all(name='span', attrs={'class':'np'}):
                    if span.text.strip() == 'Next »':
                        terminate = False
            if terminate:
                break

        # Saving sample_df as a local csv file — define your own local path to save contents 
        file_path = 'scraping/listings/indeed_' 
        for word in job:
            if job.index(word) > 0:
                file_path += '_'
            file_path += word
        file_path += '.csv'
        sample_df.to_csv(file_path, encoding='utf-8')

    # TODO Save to database once setup
    def save_to_db(self):
        pass

    # This is also indeed specific code as I needed to do this to get the application link
    def _scrape_apply_link(self, link: str) -> str:
        url = 'https://au.indeed.com' + link
        time.sleep(1)
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        result = 'NO APPLY_LINK'

        for div in soup.find_all(name='div', attrs={'id':'viewJobButtonLinkContainer'}):
            for a in div.find_all(name='a'):
                if a.text == 'Apply On Company Site':
                    result = a['href']
        return result
