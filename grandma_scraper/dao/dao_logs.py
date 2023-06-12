from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from grandma_scraper.dao.dao_base import DAOBase
from grandma_scraper.config import MONGO_CLIENT, MONGODB_DB_NAME
from grandma_scraper.models.log import Log, LogInDB


class DAOLogs(DAOBase):
    def __init__(self):
        super().__init__(MONGO_CLIENT,
                         MONGODB_DB_NAME,
                         'logs',
                         Log,
                         LogInDB)
