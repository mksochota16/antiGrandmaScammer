from grandma_scraper.dao.dao_base import DAOBase
from grandma_scraper.config import MONGO_CLIENT, MONGODB_DB_NAME
from grandma_scraper.models.urlscan.urlscan import UrlScanResultRaw, UrlScanResultInDB


class DAOUrlScanResults(DAOBase):
    def __init__(self):
        super().__init__(MONGO_CLIENT,
                         MONGODB_DB_NAME,
                         'url_scan_results',
                         UrlScanResultRaw,
                         UrlScanResultInDB)
