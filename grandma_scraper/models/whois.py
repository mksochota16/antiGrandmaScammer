from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from models.base_mongo_model import MongoDBModel, MongoObjectId


class WhoisBase(BaseModel):
    timestamp: datetime
    result_dict: Optional[dict]
    cert_domain_id: MongoObjectId

class Whois(WhoisBase):
    pass

class WhoisInDB(WhoisBase, MongoDBModel):
    pass
