from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from grandma_scraper.dao.dao_base import DAOBase
from grandma_scraper.config import MONGO_CLIENT, MONGODB_DB_NAME
from grandma_scraper.models.scraped_website import ScrapedWebsite, ScrapedWebsiteInDB


class DAOScrapedWebsites(DAOBase):
    def __init__(self):
        super().__init__(MONGO_CLIENT,
                         MONGODB_DB_NAME,
                         'scraped_websites',
                         ScrapedWebsite,
                         ScrapedWebsiteInDB)


    def insert_one(self, scraped_website: ScrapedWebsite) -> ObjectId:
        self.collection.create_index([('url', 1)], unique=True)
        try:
            return super().insert_one(scraped_website)
        except DuplicateKeyError:
            super().replace_one('url', scraped_website.url, scraped_website)
            scraped_website_in_db: ScrapedWebsiteInDB = super().find_one_by_query({'url': scraped_website.url})
            return ObjectId(scraped_website_in_db.id)