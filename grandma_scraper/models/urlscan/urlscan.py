from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from grandma_scraper.models.base_mongo_model import MongoDBModel, MongoObjectId
from grandma_scraper.models.urlscan.page import PageBase, PageRaw, Page
from grandma_scraper.models.urlscan.stats import Stats, StatsBase, StatsRaw
from grandma_scraper.models.urlscan.task import Task, TaskBase, TaskRaw

class UrlScanBase(BaseModel):
    total: int
    took: int
    has_more: bool
    updated_at: datetime = datetime.now()
    cert_domain_id: MongoObjectId

class UrlScanRaw(UrlScanBase):
    pass

class UrlScanInDB(UrlScanBase, MongoDBModel):
    pass
class UrlScanResultBase(BaseModel):
    task: TaskBase
    stats: StatsBase
    page: PageBase
    url_scan_id: str
    score: Optional[str]
    sort: List[str]
    result: str
    screenshot: Optional[str]
    url_scan_id: MongoObjectId

class UrlScanResultRaw(UrlScanResultBase):
    task: TaskRaw
    stats: StatsRaw
    page: PageRaw

class UrlScanResult(UrlScanResultBase):
    task: Task
    stats: Stats
    page: Page

class UrlScanResultInDB(UrlScanResult, MongoDBModel):
    pass
