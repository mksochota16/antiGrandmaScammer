import math
import re
import json
from grandma_scraper.dao.dao_cert_domains import DAOCertDomains
from grandma_scraper.dao.dao_scraped_websites import DAOScrapedWebsites
from grandma_scraper.dao.dao_url_scan_results import DAOUrlScanResults
from grandma_scraper.dao.dao_whois import DAOWhois


class ParsedSite:
    def __init__(self):
        self.subdomain_count = None
        self.redirect_subdomain_count = None
        self.link_length = None
        self.redirect_link_length = None
        self.tld = None
        self.redirect_bool = None
        self.redirect_specific = None
        self.http_info = None
        self.http_info_redirect = None
        self.registrar = None
        self.registrant = None
        self.registrant_country = None
        self.registrant_email_domains = None
        self.asnname = None
        self.tls_age = None
        self.page_title = None
        self.redirected_link_entropy = None
        self.site_links_count = None
        self.site_images_count = None

    def to_values_list(self):
        return [
            self.subdomain_count,
            self.redirect_subdomain_count,
            self.link_length,
            self.redirect_link_length,
            self.tld,
            self.redirect_bool,
            self.redirect_specific,
            self.http_info,
            self.http_info_redirect,
            self.registrar,
            self.registrant,
            self.registrant_country,
            self.registrant_email_domains,
            self.asnname,
            self.tls_age,
            self.page_title,
            self.redirected_link_entropy,
            self.site_links_count,
            self.site_images_count
        ]

    @classmethod
    def get_field_names(cls):
        return [
            'subdomain_count',
            'redirect_subdomain_count',
            'link_length',
            'redirect_link_length',
            'tld',
            'redirect_bool',
            'redirect_specific',
            'http_info',
            'http_info_redirect',
            'registrar',
            'registrant',
            'registrant_country',
            'registrant_email_domains',
            'asnname',
            'tls_age',
            'page_title',
            'redirected_link_entropy',
            'site_links_count',
            'site_images_count'
        ]


def subdomain_count(url):
    domain = urlparse(url).netloc
    return domain.count('.') + 1


def calculate_entropy(string):
    char_freq = {}
    for char in string:
        if char in char_freq:
            char_freq[char] += 1
        else:
            char_freq[char] = 1
    entropy = 0
    string_len = len(string)
    for count in char_freq.values():
        frequency = count / string_len
        entropy -= frequency * math.log(frequency, 2)

    return entropy


def extract_domain(link):
    pattern = r"(?P<protocol>https?://)?(?:www\.)?(?P<domain>[^/:]+)"
    match = re.search(pattern, link)
    domain = match.group("domain")

    return domain


def parse_by_scraped_website_id(scrape_id):
    parsedObj = ParsedSite()
    dao_whois: DAOWhois = DAOWhois()
    dao_urlscan_results: DAOUrlScanResults = DAOUrlScanResults()
    dao_scraped_websites: DAOScrapedWebsites = DAOScrapedWebsites()
    dao_cert_domains: DAOCertDomains = DAOCertDomains()

    scraped_websites_dom = dao_scraped_websites.find_by_id(scrape_id)
    urlscanresults_dom = dao_urlscan_results.find_by_id(scraped_websites_dom.url_scan_result_id)

    # print(extract_domain(scraped_websites_dom.url))
    cert_dom = dao_cert_domains.find_by_id(scraped_websites_dom.cert_domain_id)
    whois_dom = dao_whois.find_by_id(scraped_websites_dom.cert_domain_id)

    if scraped_websites_dom.html is not None:
        parsedObj.site_links_count = scraped_websites_dom.html.count("<a")
        parsedObj.site_images_count = scraped_websites_dom.html.count("<img")
    if urlscanresults_dom is not None:
        parsedObj.subdomain_count = subdomain_count(urlscanresults_dom.task.url)
        parsedObj.redirect_subdomain_count = subdomain_count(urlscanresults_dom.page.url)
        parsedObj.link_length = len(urlscanresults_dom.task.url)
        parsedObj.redirect_link_length = len(urlscanresults_dom.page.url)
        parsedObj.redirect_bool = urlscanresults_dom.page.redirected is not None
        parsedObj.redirect_specific = urlscanresults_dom.page.redirected
        httpors = lambda x: "https" if x.startswith("https") else "http" if x.startswith("http") else "unknown"
        parsedObj.http_info = httpors(urlscanresults_dom.task.url)
        parsedObj.http_info_redirect = httpors(urlscanresults_dom.page.url)
        parsedObj.asnname = urlscanresults_dom.page.asnname
        parsedObj.tls_age = urlscanresults_dom.page.tls_age_days
        parsedObj.page_title = urlscanresults_dom.page.title
        parsedObj.redirected_link_entropy = calculate_entropy(urlscanresults_dom.page.url)
    if whois_dom is not None:
        parsedObj.tld = whois_dom.result_dict['tld']
        parsedObj.registrar = whois_dom.result_dict['registrar']
        parsedObj.registrant = whois_dom.result_dict['registrant']
        parsedObj.registrant_country = whois_dom.result_dict['registrant_country']
        if len(whois_dom.result_dict['emails']) > 0:
            if whois_dom.result_dict['emails'][0]:
                parsedObj.registrant_email_domains = whois_dom.result_dict['emails'][0].split("@")[1]
    return parsedObj


def parse_sites():
    dao_scraped_websites: DAOScrapedWebsites = DAOScrapedWebsites()
    all_scrapes = dao_scraped_websites.find_all()
    parsed_sites = []
    i = 0
    for scrape in all_scrapes:
        if scrape.url_scan_result_id is None:
            continue
        parsed_sites.append(parse_by_scraped_website_id(scrape.id).to_values_list())
        i += 1
        # if i % 50 == 0:
        #     print("Parsing: " + str(i) + "/" + str(len(all_scrapes)))
    return parsed_sites


if __name__ == "__main__":
    parsed_sites = parse_sites()


    with open('parsed.json', 'w') as f:
        f.write(json.dumps([site.__dict__ for site in parsed_sites]))
    f.close()
    print('Finished parsing')
