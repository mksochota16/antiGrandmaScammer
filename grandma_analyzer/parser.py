import math
import re
from urllib.parse import urlparse

from grandma_scraper.dao.dao_cert_domains import DAOCertDomains
from grandma_scraper.dao.dao_scraped_websites import DAOScrapedWebsites
from grandma_scraper.dao.dao_url_scan_results import DAOUrlScanResults
from grandma_scraper.dao.dao_whois import DAOWhois


class ParsedSite:
    def __init__(self):
        self.tld = None
        self.registrar = None
        self.registrant_country = None
        self.domain_age = None
        self.nameserver_domain = None
        self.mail_domain = None
        self.tls_age = None
        self.tls_issuer = None
        self.url_len = None
        self.parameters_len = None
        self.parameters_count = None
        self.dollar_percent = None
        self.dash_percent = None
        self.underscore_percent = None
        self.dot_percent = None
        self.plus_percent = None
        self.exclamation_mark_percent = None
        self.star_percent = None
        self.quote_percent = None
        self.opening_bracket_percent = None
        self.closing_bracket_percent = None
        self.comma_percent = None
        self.numbers_percent = None
        self.url_entropy = None
        self.is_redirect = None
        self.subdomain_count = None
        self.content_link_count = None
        self.content_img_count = None

    def to_values_list(self):
        return [
            self.tld,
            self.registrar,
            self.registrant_country,
            self.domain_age,
            self.nameserver_domain,
            self.mail_domain,
            self.tls_age,
            self.tls_issuer,
            self.url_len,
            self.parameters_len,
            self.parameters_count,
            self.dollar_percent,
            self.dash_percent,
            self.underscore_percent,
            self.dot_percent,
            self.plus_percent,
            self.exclamation_mark_percent,
            self.star_percent,
            self.quote_percent,
            self.opening_bracket_percent,
            self.closing_bracket_percent,
            self.comma_percent,
            self.numbers_percent,
            self.url_entropy,
            self.is_redirect,
            self.subdomain_count,
            self.content_link_count,
            self.content_img_count
        ]

    @classmethod
    def get_field_names(cls):
        return [
            'tld',
            'registrar',
            'registrant_country',
            'domain_age',
            'nameserver_domain',
            'mail_domain',
            'tls_age',
            'tls_issuer',
            'url_len',
            'parameters_len',
            'parameters_count',
            'dollar_percent',
            'dash_percent',
            'underscore_percent',
            'dot_percent',
            'plus_percent',
            'exclamation_mark_percent',
            'star_percent',
            'quote_percent',
            'opening_bracket_percent',
            'closing_bracket_percent',
            'comma_percent',
            'numbers_percent',
            'url_entropy',
            'is_redirect',
            'subdomain_count',
            'content_link_count',
            'content_img_count'
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


def extract_parameters(url):
    return urlparse(url).query


def extract_path(url):
    return urlparse(url).path


def percent_in_url(url, key):
    key_count = url.count(key)
    return round(key_count/len(url), 2)


def parse_by_scraped_website_id(scrape_id):
    parsed_obj = ParsedSite()
    dao_whois: DAOWhois = DAOWhois()
    dao_urlscan_results: DAOUrlScanResults = DAOUrlScanResults()
    dao_scraped_websites: DAOScrapedWebsites = DAOScrapedWebsites()
    #dao_cert_domains: DAOCertDomains = DAOCertDomains()

    scraped_websites_dom = dao_scraped_websites.find_by_id(scrape_id)
    urlscanresults_dom = dao_urlscan_results.find_by_id(scraped_websites_dom.url_scan_result_id)

    # print(extract_domain(scraped_websites_dom.url))
    #cert_dom = dao_cert_domains.find_by_id(scraped_websites_dom.cert_domain_id)
    whois_dom = dao_whois.find_one_by_query({'cert_domain_id': scraped_websites_dom.cert_domain_id})
    url = scraped_websites_dom.url
    if whois_dom.result_dict is not None:
        parsed_obj.tld = whois_dom.result_dict['tld']
        parsed_obj.registrar = whois_dom.result_dict['registrar']
        parsed_obj.registrant_country = whois_dom.result_dict['registrant_country']
        if whois_dom.result_dict['creation_date'] is not None:
            parsed_obj.domain_age = (whois_dom.timestamp - whois_dom.result_dict['creation_date']).days
        if len(whois_dom.result_dict['name_servers']) > 0:
            if whois_dom.result_dict['name_servers'][0]:
                if whois_dom.result_dict['name_servers'][0].count('.') > 0:
                    dns_dom = whois_dom.result_dict['name_servers'][0].split('.')
                    parsed_obj.nameserver_domain = dns_dom[-2]+"."+dns_dom[-1]
        if 'emails' in whois_dom.result_dict:
            if len(whois_dom.result_dict['emails']) > 0:
                if whois_dom.result_dict['emails'][0]:
                    parsed_obj.mail_domain = whois_dom.result_dict['emails'][0].split("@")[1]
    parsed_obj.url_len = len(url)
    if urlscanresults_dom is not None:
        parsed_obj.tls_age = urlscanresults_dom.page.tls_age_days
        parsed_obj.tls_issuer = urlscanresults_dom.page.tls_issuer
        parsed_obj.is_redirect = urlscanresults_dom.page.redirected is not None

    parsed_obj.parameters_len = len(extract_parameters(url))
    parsed_obj.parameters_count = extract_parameters(url).count('.')
    parsed_obj.dollar_percent = percent_in_url(url, '$')
    parsed_obj.dash_percent = percent_in_url(url, '%')
    parsed_obj.underscore_percent = percent_in_url(url, '_')
    parsed_obj.dot_percent = percent_in_url(url, '.')
    parsed_obj.plus_percent = percent_in_url(url, '+')
    parsed_obj.exclamation_mark_percent = percent_in_url(url, '!')
    parsed_obj.star_percent = percent_in_url(url, '*')
    parsed_obj.quote_percent = percent_in_url(url, '\'')
    parsed_obj.opening_bracket_percent = percent_in_url(url, '(')
    parsed_obj.closing_bracket_percent = percent_in_url(url, ')')
    parsed_obj.comma_percent = percent_in_url(url, ',')
    parsed_obj.numbers_percent = sum(c.isdigit() for c in url)
    parsed_obj.url_entropy = calculate_entropy(url)
    parsed_obj.subdomain_count = subdomain_count(url)
    if scraped_websites_dom.html is not None:
        parsed_obj.content_link_count = scraped_websites_dom.html.count("<a")
        parsed_obj.content_img_count = scraped_websites_dom.html.count("<img")

    return parsed_obj


def parse_sites():
    dao_scraped_websites: DAOScrapedWebsites = DAOScrapedWebsites()
    dao_whois: DAOWhois = DAOWhois()
    all_scrapes = dao_scraped_websites.find_all()

    parsed_sites = []
    i = 0
    for scrape in all_scrapes:
        if dao_whois.find_one_by_query({'cert_domain_id': scrape.cert_domain_id}) is None:
            continue
        parsed_sites.append(parse_by_scraped_website_id(scrape.id).to_values_list())
        # i += 1
        # if i % 50 == 0:
        #     print("Parsing: " + str(i) + "/" + str(len(all_scrapes)))
    return parsed_sites


if __name__ == "__main__":
    parsed_sites = parse_sites()
    #with open('parsed.json', 'w') as f:
    #    f.write(json.dumps([site.__dict__ for site in parsed_sites]))
    #f.close()
    print('Finished parsing')
