from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from grandma_scraper.dao.dao_base import DAOBase
from grandma_scraper.config import MONGO_CLIENT, MONGODB_DB_NAME
from grandma_scraper.models.cert_domain import CertDomain, CertDomainInDB


class DAOCertDomains(DAOBase):
    def __init__(self):
        super().__init__(MONGO_CLIENT,
                         MONGODB_DB_NAME,
                         'cert_domains',
                         CertDomain,
                         CertDomainInDB)


    def insert_one(self, cert_domain: CertDomain) -> ObjectId:
        self.collection.create_index([('register_position_id', 1)], unique=True)
        try:
            return super().insert_one(cert_domain)
        except DuplicateKeyError:
            super().replace_one('register_position_id', cert_domain.register_position_id, cert_domain)
            account_in_db: CertDomainInDB = super().find_one_by_query({'register_position_id': cert_domain.register_position_id})
            return ObjectId(account_in_db.id)