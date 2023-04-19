from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from models.base_mongo_model import MongoDBModel, MongoObjectId

class ScrapedWebsiteBase(BaseModel):
    url: str
    timestamp: datetime
    html: Optional[str]
    screenshot: Optional[bytes]
    is_blocked: bool = False
    error_msg: Optional[str]
    cert_domain_id: MongoObjectId
    url_scan_result_id: Optional[MongoObjectId]

class ScrapedWebsite(ScrapedWebsiteBase):
    pass

class ScrapedWebsiteInDB(ScrapedWebsite, MongoDBModel):
    pass
