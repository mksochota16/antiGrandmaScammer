from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from grandma_scraper.models.base_mongo_model import MongoDBModel

class TaskBase(BaseModel):
    visibility: str
    method: str
    domain: str
    apex_domain: Optional[str]
    time: datetime
    uuid: str
    url: str


class TaskRaw(TaskBase):
    apex_domain: Optional[str] = Field(default=None, alias='apexDomain')

class Task(TaskBase):
    pass
