from datetime import datetime
from pydantic import BaseModel

from models.base_mongo_model import MongoDBModel, MongoObjectId


class WhoisBase(BaseModel):
    timestamp: datetime = datetime.now()
    result_dict: dict
    cert_domain_id: MongoObjectId

class Whois(WhoisBase):
    pass

class WhoisInDB(WhoisBase, MongoDBModel):
    pass
