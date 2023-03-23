#!/usr/bin/env python3
from typing import List

import requests
import time
from datetime import datetime, timedelta
import pymongo
import pymongo.errors

from selenium import webdriver
from selenium.common import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from time import sleep

from io import BytesIO

from grandma_scraper.config import SLEEP_TIME
from grandma_scraper.dao.dao_cert_domains import DAOCertDomains
from grandma_scraper.dao.dao_scraped_websites import DAOScrapedWebsites
from grandma_scraper.dao.dao_url_scan_results import DAOUrlScanResults
from grandma_scraper.dao.dao_url_scans import DAOUrlScans
from grandma_scraper.models.base_mongo_model import MongoObjectId
from grandma_scraper.models.cert_domain import CertDomainInDB, CertDomain, CertDomainRaw
from grandma_scraper.models.scraped_website import ScrapedWebsite
from grandma_scraper.models.urlscan.urlscan import UrlScanRaw, UrlScanResultRaw, UrlScanResultInDB

def update_cert_blocklist_db() -> int:
    url = "https://hole.cert.pl/domains/domains.json"
    response = requests.get(url)
    assert response.status_code == 200

    cert_data: List[dict] = response.json()
    dao_cert_domains: DAOCertDomains = DAOCertDomains()
    known_ids: List[int] = [domain.register_position_id for domain in dao_cert_domains.find_all()]
    cert_domains: List[CertDomainRaw] = [CertDomainRaw(**cert_domain_dict) for cert_domain_dict in cert_data if cert_domain_dict['RegisterPositionId'] not in known_ids]
    if len(cert_domains) > 0:
        dao_cert_domains.insert_many(cert_domains)
    return len(cert_domains)

def get_cert_blocklist_from_mongo() -> List[CertDomainInDB]:
    dao_cert_domains: DAOCertDomains = DAOCertDomains()
    cert_domains: List[CertDomainInDB] = dao_cert_domains.find_all()
    return cert_domains


def get_cert_domains_filtered_by_time(last_update: datetime) -> List[CertDomainInDB]:
    dao_cert_domains: DAOCertDomains = DAOCertDomains()
    filtered_domains: List[CertDomainInDB] = dao_cert_domains.find_many_by_query({'insert_date': {'$gte': last_update}})
    return filtered_domains
def scrape_website(driver, url):
    dao_scraped_websites: DAOScrapedWebsites = DAOScrapedWebsites()
    if not url.startswith('http'):
        url = f'http://{url}'
    if dao_scraped_websites.find_one_by_query({'url': url}) is None:
        try:
            driver.get(url)
            html = driver.page_source
            screenshot = driver.get_screenshot_as_png()
            binary_data = BytesIO(screenshot).read()
            scraped_website: ScrapedWebsite = ScrapedWebsite(
                url=url,
                timestamp=datetime.now(),
                html=html,
                screenshot=binary_data
            )
            dao_scraped_websites.insert_one(scraped_website)
        except WebDriverException as e:
            scraped_website: ScrapedWebsite = ScrapedWebsite(
                url=url,
                timestamp=datetime.now(),
                html=None,
                screenshot=None,
                is_blocked=True,
                error_message=e.msg
            )
            dao_scraped_websites.insert_one(scraped_website)


def get_url_scan_info(cert_domain: CertDomainInDB) -> List[UrlScanResultInDB]:
    url = f"https://urlscan.io/api/v1/search/?q=domain:{cert_domain.domain_address}"
    response = requests.get(url)
    if response.status_code == 429:
        # If we hit the rate limit, wait for the reset time and try again
        #reset_time = int(response.headers['X-Rate-Limit-Reset'])
        response_json = response.json()
        error_message = response_json['message']
        reset_after = int(error_message.split('Reset in ')[1].split(' seconds')[0])
        # "Rate limit for 'search' exceeded, limit is 100 per hour. Reset in 611 seconds."
        print(f"Rate limit exceeded, waiting for {reset_after + 50} seconds")
        time.sleep(reset_after+ 50)
        response = requests.get(url)

    response_json = response.json()

    dao_url_scans: DAOUrlScans = DAOUrlScans()
    dao_url_scan_results: DAOUrlScanResults = DAOUrlScanResults()

    url_scan: UrlScanRaw = UrlScanRaw(total=response_json['total'],
                                      took=response_json['took'],
                                      has_more=response_json['has_more'],
                                      cert_domain_id=cert_domain.id)
    url_scan_id = dao_url_scans.insert_one(url_scan)
    results_list = response_json['results']
    if len(results_list) == 0:
        return []
    url_scan_results: List[UrlScanResultRaw] = []
    for result in results_list:
        url_scan_raw = UrlScanResultRaw(**result, url_scan_id=url_scan_id)
        url_scan_results.append(url_scan_raw)

    list_of_inserted_id: List[MongoObjectId] = dao_url_scan_results.insert_many(url_scan_results)

    return dao_url_scan_results.get_many_by_list_of_ids(list_of_inserted_id)

def perform_data_collection(skip_if_0_collected = True):
    # Load and filter CERT Polska official block list
    updated_count: int = update_cert_blocklist_db()
    if updated_count == 0 and skip_if_0_collected:
        return 0
    relevant_data: List[CertDomainInDB] = get_cert_domains_filtered_by_time(datetime.now() - timedelta(hours = 8))

    options = Options()
    options.headless = True
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    dao_url_scans: DAOUrlScans = DAOUrlScans()
    counter = 0
    for cert_domain in relevant_data:
        if dao_url_scans.find_one_by_query({'cert_domain_id': cert_domain.register_position_id}) is not None:
            continue
        url_scan_results: List[UrlScanResultInDB] = get_url_scan_info(cert_domain)
        if len(url_scan_results) == 0:
            #url scan could did not provide any results, probably the site is banned, however we still want to check that
            scrape_website(driver, cert_domain.domain_address)
            counter+=1
        else:
            for url_scan_result in url_scan_results:
                scrape_website(driver, url_scan_result.page.url)
                counter+=1


    # Quit Selenium webdriver
    driver.quit()
    return counter

def main():
    counter = 0
    while True:
        performed_scans = perform_data_collection(skip_if_0_collected=True)
        counter+=1
        print(f"{counter}. Performed {performed_scans} scans {datetime.now()}")
        sleep(SLEEP_TIME)

if __name__ == '__main__':
    main()
