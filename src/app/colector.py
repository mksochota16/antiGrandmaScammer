#!/usr/bin/env python3

import requests
import time
from datetime import datetime, timedelta
import pymongo
import json
from os import environ
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from time import sleep

from io import BytesIO

def load_cert_blocklist():
    with open("../../domains.json") as f:
        return json.load(f)
    url = "https://hole.cert.pl/domains/domains.json"
    response = requests.get(url)
    cert_data = response.json()

    return cert_data

def filter_by_date(data, last_update):
    filtered_data = [d for d in data if datetime.strptime(d['InsertDate'], '%Y-%m-%dT%H:%M:%S') > last_update]
    return filtered_data

def get_domains(data):
    domains = [d['DomainAddress'] for d in data]
    return domains

def scrape_website(driver, url, collection):
    if True or not collection.find_one({'url': url}):
        try:
            driver.get(url)
            html = driver.page_source
            screenshot = driver.get_screenshot_as_png()
            binary_data = BytesIO(screenshot).read()
            document = {
                'url': url,
                'timestamp': datetime.now(),
                'html': html,
                'screenshot': binary_data
            }
            collection.insert_one(document)
            print(f"Successfully captured screenshot and HTML of {url}")
        except Exception as e:
            print(f"Error capturing screenshot and HTML of {url}: {str(e)}")
    else:
        print(f"Skipping {url} as it has already been captured")

def get_urls(domain):
    url = f"https://urlscan.io/api/v1/search/?q=domain:{domain}"
    response = requests.get(url)
    print(response.json())
    if response.status_code == 429:
        # If we hit the rate limit, wait for the reset time and try again
        reset_time = int(response.headers['X-Rate-Limit-Reset'])
        reset_after = int(response.headers['X-Rate-Limit-Reset-After'])
        print(f"Rate limit exceeded, waiting for {reset_after} seconds")
        time.sleep(reset_after)
        response = requests.get(url)
    results = response.json()['results']

    urls = []
    for r in results:
        urls.append(r['page']['url'])


    return urls

def main():
    # Load and filter CERT Polska official block list
    cert_data = load_cert_blocklist()
    filtered_data = filter_by_date(cert_data, datetime.now() - timedelta(hours = 8))
    domains = get_domains(filtered_data)
    urls = get_urls(domains[-5])

    # Initialize Selenium webdriver
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    sleep(5)
    driver = webdriver.Remote(
        environ.get("SELENIUM_URL"),
        desired_capabilities=DesiredCapabilities.CHROME,
        options=options
    )

    # Query urlscan.io for each domain and store results in MongoDB
    client = pymongo.MongoClient(environ.get("MONGO_URL"))
    db = client['adac']
    collection = db['results']
    scrape_website(driver, urls[0], collection)

    # Quit Selenium webdriver
    driver.quit()

    # Print all results in the database
    for result in collection.find():
        print(result)

if __name__ == '__main__':
    main()
