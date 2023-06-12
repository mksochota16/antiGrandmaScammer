#!/usr/bin/env python3
from typing import List

import requests
import time
from datetime import datetime, timedelta
import whois

from selenium import webdriver
from selenium.common import WebDriverException
from time import sleep

from io import BytesIO

from grandma_scraper.config import SLEEP_TIME, SKIP_CERT_DOMAINS_CHECK, CHROMEDRIVER_PATH
from grandma_scraper.dao.dao_cert_domains import DAOCertDomains
from grandma_scraper.dao.dao_logs import DAOLogs
from grandma_scraper.dao.dao_scraped_websites import DAOScrapedWebsites
from grandma_scraper.dao.dao_url_scan_results import DAOUrlScanResults
from grandma_scraper.dao.dao_url_scans import DAOUrlScans
from grandma_scraper.dao.dao_whois import DAOWhois
from grandma_scraper.models.base_mongo_model import MongoObjectId
from grandma_scraper.models.cert_domain import CertDomainInDB, CertDomainRaw
from grandma_scraper.models.log import Log, Action
from grandma_scraper.models.scraped_website import ScrapedWebsite
from grandma_scraper.models.urlscan.urlscan import UrlScanRaw, UrlScanResultRaw, UrlScanResultInDB
from grandma_scraper.models.whois import Whois


def update_cert_blocklist_db() -> int:
    url = "https://hole.cert.pl/domains/domains.json"
    response = requests.get(url)
    assert response.status_code == 200

    cert_data: List[dict] = response.json()
    dao_cert_domains: DAOCertDomains = DAOCertDomains()
    known_ids: List[int] = [domain.register_position_id for domain in dao_cert_domains.find_all()]
    cert_domains: List[CertDomainRaw] = [CertDomainRaw(**cert_domain_dict) for cert_domain_dict in cert_data if
                                         int(cert_domain_dict['RegisterPositionId']) not in known_ids]
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


def scrape_website(driver, url, cert_domain_id, url_scan_result_id):
    dao_scraped_websites: DAOScrapedWebsites = DAOScrapedWebsites()
    if not url.startswith('http'):
        url = f'http://{url}'
    if dao_scraped_websites.find_one_by_query({'url': url}) is None:
        try:
            driver.get(url)
            sleep(5)
            html = driver.page_source
            screenshot = driver.get_screenshot_as_png()
            binary_data = BytesIO(screenshot).read()
            scraped_website: ScrapedWebsite = ScrapedWebsite(
                url=url,
                timestamp=datetime.now(),
                html=html,
                screenshot=binary_data,
                cert_domain_id=cert_domain_id,
                url_scan_result_id=url_scan_result_id
            )
            dao_scraped_websites.insert_one(scraped_website)
        except WebDriverException as e:
            scraped_website: ScrapedWebsite = ScrapedWebsite(
                url=url,
                timestamp=datetime.now(),
                html=None,
                screenshot=None,
                is_blocked=True,
                error_message=e.msg,
                cert_domain_id=cert_domain_id,
                url_scan_result_id=url_scan_result_id
            )
            dao_scraped_websites.insert_one(scraped_website)


def get_url_scan_info(cert_domain: CertDomainInDB) -> List[UrlScanResultInDB]:
    url = f"https://urlscan.io/api/v1/search/?q=domain:{cert_domain.domain_address}"
    response = requests.get(url)
    dao_logs: DAOLogs = DAOLogs()
    while response.status_code == 429:
        # If we hit the rate limit, wait for the reset time and try again
        # reset_time = int(response.headers['X-Rate-Limit-Reset'])
        response_json = response.json()
        error_message = response_json['message']
        reset_after = int(error_message.split('Reset in ')[1].split(' seconds')[0])
        # "Rate limit for 'search' exceeded, limit is 100 per hour. Reset in 611 seconds."
        print(f"Rate limit exceeded, waiting for {reset_after + 120} seconds")
        url_scan_results_log = Log(
            action=Action.ERROR_IN_URL_SCAN,
            timestamp=datetime.now(),
            message=f"Error while performing scan, waiting for {reset_after + 120} seconds",
            error_message=error_message,
        )
        dao_logs.insert_one(url_scan_results_log)
        time.sleep(reset_after + 120)
        response = requests.get(url)

    response_json = response.json()

    dao_url_scans: DAOUrlScans = DAOUrlScans()
    dao_url_scan_results: DAOUrlScanResults = DAOUrlScanResults()

    url_scan: UrlScanRaw = UrlScanRaw(total=response_json['total'],
                                      took=response_json['took'],
                                      has_more=response_json['has_more'],
                                      updated_at=datetime.now(),
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


def perform_data_collection():
    # Load and filter CERT Polska official block list
    print("Performing update_cert_blocklist_db")
    updated_count: int = update_cert_blocklist_db()
    print("After update_cert_blocklist_db")

    if updated_count == 0 and not SKIP_CERT_DOMAINS_CHECK:
        return 0
    dao_logs: DAOLogs = DAOLogs()
    updated_cert_domains_log = Log(
        action=Action.UPDATED_CERT_DOMAINS,
        timestamp=datetime.now(),
        message=f"Updated {updated_count} domains from CERT Polska blocklist",
        number_of_results=updated_count
    )
    dao_logs.insert_one(updated_cert_domains_log)

    relevant_data: List[CertDomainInDB] = get_cert_domains_filtered_by_time(datetime.now() - timedelta(hours=8))

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options)

    dao_url_scans: DAOUrlScans = DAOUrlScans()
    dao_whois: DAOWhois = DAOWhois()
    counter = 0
    for cert_domain in relevant_data:
        print(f"Scan for domain {cert_domain.domain_address}")
        if dao_whois.find_one_by_query({'cert_domain_id': cert_domain.id}) is None:
            try:
                print(f"Whois scan for domain: {cert_domain.domain_address}")
                whois_info = whois.query(cert_domain.domain_address)
                whois_info_log = Log(
                    action=Action.PERFORMED_WHOIS,
                    timestamp=datetime.now(),
                    message=f"Performed whois for {cert_domain.domain_address}",
                    number_of_results=1
                )
                dao_logs.insert_one(whois_info_log)
                if whois_info is not None:
                    result_dict = whois_info.__dict__
                else:
                    result_dict = None
                dao_whois.insert_one(Whois(
                    timestamp=datetime.now(),
                    cert_domain_id=cert_domain.id,
                    result_dict=result_dict
                ))
            except Exception as e:
                print(e)
                print(f"Failed to whois scan on {cert_domain.domain_address}")
        else:
            print(f"Skipping whois for {cert_domain}")

        if dao_url_scans.find_one_by_query({'cert_domain_id': cert_domain.id}) is not None:
            print(f"Skipping urlscan for {cert_domain}")
            continue

        print(f"Urlscan for: {cert_domain.domain_address}")

        url_scan_results: List[UrlScanResultInDB] = get_url_scan_info(cert_domain)
        url_scan_results_log = Log(
            action=Action.PERFORMED_URL_SCAN,
            timestamp=datetime.now(),
            message=f"Performed url scan for {cert_domain.domain_address}",
            number_of_results=len(url_scan_results)
        )
        dao_logs.insert_one(url_scan_results_log)

        if len(url_scan_results) == 0:
            print(f"Webscrape for: {cert_domain.domain_address}")

            # url scan could did not provide any results, probably the site is banned, however we still want to check that
            scrape_website(driver, cert_domain.domain_address, cert_domain.id, None)
            web_scrape_log = Log(
                action=Action.PERFORMED_WEB_SCRAPE,
                timestamp=datetime.now(),
                message=f"Performed web scrape for {cert_domain.domain_address}"
            )
            dao_logs.insert_one(web_scrape_log)
            counter += 1
        else:
            for url_scan_result in url_scan_results:
                print(f"Webscrape for url_scan_result: {url_scan_result.page.url}")

                scrape_website(driver, url_scan_result.page.url, cert_domain.id, url_scan_result.id)
                web_scrape_log = Log(
                    timestamp=datetime.now(),
                    action=Action.PERFORMED_WEB_SCRAPE,
                    message=f"Performed web scrape for url_scan_result: {url_scan_result.page.url}"
                )
                dao_logs.insert_one(web_scrape_log)
                counter += 1

    # Quit Selenium webdriver
    driver.quit()
    return counter


def main():
    counter = 0
    while True:
        performed_scans = perform_data_collection()
        counter += 1
        print(f"{counter}. Performed {performed_scans} scans {datetime.now()}, sleeping {SLEEP_TIME}")
        sleep(SLEEP_TIME)


if __name__ == '__main__':
    main()
