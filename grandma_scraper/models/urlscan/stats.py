from pydantic import BaseModel, Field


class StatsBase(BaseModel):
    uniq_ips: int
    uniq_countries: int
    data_length: int
    encoded_data_length: int
    requests: int


class StatsRaw(StatsBase):
    uniq_ips: int = Field(default=None, alias='uniqIPs')
    uniq_countries: int = Field(default=None, alias='uniqCountries')
    data_length: int = Field(default=None, alias='dataLength')
    encoded_data_length: int = Field(default=None, alias='encodedDataLength')

class Stats(StatsBase):
    pass
