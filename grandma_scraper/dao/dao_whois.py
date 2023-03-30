from dao.dao_base import DAOBase
from config import MONGO_CLIENT, MONGODB_DB_NAME
from models.whois import Whois, WhoisInDB


class DAOWhois(DAOBase):
    def __init__(self):
        super().__init__(MONGO_CLIENT,
                         MONGODB_DB_NAME,
                         'whois_results',
                         Whois,
                         WhoisInDB)
