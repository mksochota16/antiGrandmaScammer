from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from dao.dao_base import DAOBase
from config import MONGO_CLIENT, MONGODB_DB_NAME
from models.log import Log, LogInDB


class DAOLogs(DAOBase):
    def __init__(self):
        super().__init__(MONGO_CLIENT,
                         MONGODB_DB_NAME,
                         'logs',
                         Log,
                         LogInDB)
