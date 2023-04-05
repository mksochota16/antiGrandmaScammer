from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass

from models.base_mongo_model import MongoDBModel

from enum import Enum

# class syntax

class Action(str, Enum):
    UPDATED_CERT_DOMAINS = 'updated_cert_domains'
    ERROR_IN_URL_SCAN = 'error_in_url_scan'
    PERFORMED_URL_SCAN = 'performed_url_scan'
    PERFORMED_WEB_SCRAPE = 'performed_web_scrape'
    PERFORMED_WHOIS = 'performed_whois'


class LogBase(BaseModel):
    action: Action
    timestamp: datetime
    message: Optional[str]
    error_message: Optional[str]
    error_traceback: Optional[str]
    number_of_results: Optional[int]

class Log(LogBase):
    pass

class LogInDB(Log, MongoDBModel):
    pass
