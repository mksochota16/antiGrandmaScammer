from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PageBase(BaseModel):
    server: Optional[str]
    redirected: Optional[str]
    ip: Optional[str]
    mime_type: Optional[str]
    title: Optional[str]
    url: str
    tls_valid_days: Optional[int]
    tls_age_days: Optional[int]
    tls_valid_from: datetime
    domain: Optional[str]
    asnname: Optional[str]
    asn: Optional[str]
    tls_issuer: Optional[str]
    status: Optional[str]


class PageRaw(PageBase):
    mime_type: Optional[str] = Field(default=None, alias='mimeType')
    tls_valid_days: Optional[int] = Field(default=None, alias='tlsValidDays')
    tls_age_days: Optional[int] = Field(default=None, alias='tlsAgeDays')
    tls_valid_from: Optional[datetime] = Field(default=None, alias='tlsValidFrom')
    tls_issuer: Optional[str] = Field(default=None, alias='tlsIssuer')

class Page(PageBase):
    pass
