from scraping.Indeed import IndeedScraper
from scraping.Seek import SeekScraper

# Seek
print('===== Seek =====')
seek_scraper = SeekScraper('accounting intern')
seek_scraper.scrape()

print('===== Indeed =====')
# Indeed
indeed_scraper = IndeedScraper('accounting intern')
indeed_scraper.scrape()
