from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass

from models.base_mongo_model import MongoDBModel

class CertDomainBase(BaseModel):
    register_position_id: int
    domain_address: str
    insert_date: datetime
    delete_date: Optional[datetime]

class CertDomainRaw(CertDomainBase):
    register_position_id: int = Field(..., alias='RegisterPositionId')
    domain_address: str = Field(..., alias='DomainAddress')
    insert_date: datetime = Field(..., alias='InsertDate')
    delete_date: Optional[datetime] = Field(..., alias='DeleteDate')

class CertDomain(CertDomainBase):
    pass

class CertDomainInDB(CertDomain, MongoDBModel):
    pass
