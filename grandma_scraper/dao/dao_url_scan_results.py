from dao.dao_base import DAOBase
from config import MONGO_CLIENT, MONGODB_DB_NAME
from models.urlscan.urlscan import UrlScanResultRaw, UrlScanResultInDB


class DAOUrlScanResults(DAOBase):
    def __init__(self):
        super().__init__(MONGO_CLIENT,
                         MONGODB_DB_NAME,
                         'url_scan_results',
                         UrlScanResultRaw,
                         UrlScanResultInDB)
