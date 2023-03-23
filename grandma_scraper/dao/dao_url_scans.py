from dao.dao_base import DAOBase
from config import MONGO_CLIENT, MONGODB_DB_NAME
from models.urlscan.urlscan import UrlScanRaw, UrlScanInDB


class DAOUrlScans(DAOBase):
    def __init__(self):
        super().__init__(MONGO_CLIENT,
                         MONGODB_DB_NAME,
                         'url_scans',
                         UrlScanRaw,
                         UrlScanInDB)
