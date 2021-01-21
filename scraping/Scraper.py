import abc

class Scraper(abc.ABC):
    """
    Interface for scraper classes. Each website we scrape from will have a class that implements
    this scraper interface. This class should be instantiated with a query string which contains
    a searchable job term such as 'software engineering internship' or 'finance graduate'.
    """

    def __init__(self, jobType, industry):
        self._jobType = jobType
        self._industry = industry

    @abc.abstractmethod
    def scrape(self) -> None:
        pass

    @abc.abstractmethod
    def save_to_db(self) -> None:
        pass
