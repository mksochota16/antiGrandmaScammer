import ssl
import urllib
import socket
import random

from bs4 import BeautifulSoup
import pandas as pd
import requests
import tldextract
import whoisdomain as whois
import datetime
import re
import math


def extract_domain(url):
    ext = tldextract.extract(url)
    return ext.suffix


def whois_info(url):
    who = whois.query(url)
    if who is None:
        return {
            "registrar": "",
            "registrant_country": "",
            "domain_age": "",
            "ns": "",
            "email": ""
        }
    ns = ""
    abuse = ""
    domain_age = ""
    try:
        domain_age = (datetime.datetime.now() - who.creation_date).days
    except:
        pass
    try:
        ns = tldextract.extract(who.name_servers[0]).registered_domain
    except:
        pass
    try:
        abuse = who.emails[0].split("@")[1]
    except:
        pass
    return {
        "registrar": who.registrar,
        "registrant_country": who.registrant_country,
        "domain_age": domain_age,
        "ns": ns,
        "email": abuse
    }


def get_certificate_info(url):
    # Get the hostname from the URL using urllib.parse
    hostname = urllib.parse.urlparse(url).hostname


    try:
        if url.startswith("https://"):
            # Establish a connection with the server
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Get the certificate from the server
                    cert = ssock.getpeercert()

            # Extract issuer and validity information from the certificate
            issuer = dict(x[0] for x in cert['issuer'])
            valid_from = cert['notBefore']
            valid_to = cert['notAfter']

            # Calculate the age of the certificate
            now = datetime.datetime.now()
            valid_from_dt = datetime.datetime.strptime(valid_from, "%b %d %H:%M:%S %Y %Z")
            valid_to_dt = datetime.datetime.strptime(valid_to, "%b %d %H:%M:%S %Y %Z")
            age = (now - valid_from_dt).days
            return issuer["organizationName"], str(age)
        else:
            return None, None

    except socket.error as e:
        # Handle any SSL or socket errors that may occur
        print(f"Error retrieving certificate information: {str(e)}")

        return None, None


def get_url_len(url):
    return len(url)


def get_parameters_len(url):
    params = re.findall(r'\?.+', url)
    if params:
        return len(params[0]) - 1  # Exclude the question mark
    else:
        return 0


def get_parameters_count(url):
    # Get the parameters from the URL
    ext = urllib.parse.urlparse(url)
    params = ext.query.split('&')
    return len(params) + 1


def get_special_character_percent(url, char):
    count = url.count(char)
    return count / len(url)


def get_url_entropy(string):
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


def is_redirect(url):
    # make a request to the URL and compare urls using requests
    r = requests.get(url, timeout=2)
    return r.url != url


def get_subdomain_count(url):
    ext = tldextract.extract(url)
    return len(ext.subdomain.split('.'))


def get_label(url):
    return 'legitimate'  # Placeholder value


def get_content_link_count(url):
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            image_tags = soup.find_all('img')
            return len(image_tags)
        else:
            return None
    except:
        return None


def get_content_img_count(url):
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            link_tags = soup.find_all('a')
            return len(link_tags)
        else:
            return None
    except:
        return None


def create_dataframe(url):
    domain = tldextract.extract(url).registered_domain
    who = whois_info(domain)
    tls = get_certificate_info(url)
    data = {
        'url': [url],
        'tld': [extract_domain(url)],
        'registrar': who["registrar"],
        'registrant_country': who["registrant_country"],
        'domain_age': who["domain_age"],
        'nameserver_domain': who["ns"],
        'mail_domain': who["email"],
        'tls_age': tls[1],
        'tls_issuer': tls[0],
        'url_len': [get_url_len(url)],
        'parameters_len': [get_parameters_len(url)],
        'parameters_count': [get_parameters_count(url)],
        'dollar_percent': [get_special_character_percent(url, '$')],
        'dash_percent': [get_special_character_percent(url, '-')],
        'underscore_percent': [get_special_character_percent(url, '_')],
        'dot_percent': [get_special_character_percent(url, '.')],
        'plus_percent': [get_special_character_percent(url, '+')],
        'exclamation_mark_percent': [get_special_character_percent(url, '!')],
        'star_percent': [get_special_character_percent(url, '*')],
        'quote_percent': [get_special_character_percent(url, '\'')],
        'opening_bracket_percent': [get_special_character_percent(url, '(')],
        'closing_bracket_percent': [get_special_character_percent(url, ')')],
        'comma_percent': [get_special_character_percent(url, ',')],
        'numbers_percent': [get_special_character_percent(url, r'\d')],
        'url_entropy': [get_url_entropy(url)],
        'is_redirect': [is_redirect(url)],
        'subdomain_count': [get_subdomain_count(url)],
        "content_link_count": [get_content_link_count(url)],
        "content_img_count": [get_content_img_count(url)],
        'label': [get_label(url)]
    }

    df = pd.DataFrame(data)
    return df

def calculate_numbers_percent(string):
    digit_count = sum(char.isdigit() for char in string)
    total_characters = len(string)
    return (digit_count / total_characters) * 100

def analyze_urls():
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    # Example usage
    # load all urls from urls_uniq.txt
    urls = []
    with open('urls_uniq.txt', 'r') as f:
        urls = f.readlines()
    urls = [url.strip() for url in urls]
    # get all urls from urls.csv
    df = pd.read_csv('urls.csv')
    # get rid of urls that are already in the csv
    # get only 3 url per domain from url list
    urls_per_domain = {}

    # Iterate through the URLs
    for url in urls:
        # Parse the URL to extract the domain
        domain = urllib.parse.urlparse(url).netloc

        # Check if the domain already exists in the dictionary
        if domain in urls_per_domain:
            # If it exists, append the URL to the list
            urls_per_domain[domain].append(url)
        else:
            # If it doesn't exist, create a new list with the URL
            urls_per_domain[domain] = [url]

    # Iterate through the dictionary and get the first 3 URLs from each domain
    urls = []
    for domain, url_list in urls_per_domain.items():
        if len(url_list) > 10:
            urls.extend(url_list[:10])
        else:
            urls.extend(url_list)

    # get only one url per domain
    urls = [url for url in urls if url not in df['url'].values]
    # put urls in random order
    random.shuffle(urls)
    print(len(urls))

    # create dataframe for each url and marge them
    df = pd.DataFrame()
    i = 0

    for url in urls:
        try:
            i = i + 1
            if i % 50 == 0:
                print("Time right now: {}".format(datetime.datetime.now()))
                print("saving, {} left".format(len(urls) - i))
                df.to_csv('urls.csv', mode='a', index=False,header=False)
                df = pd.DataFrame()
            df = pd.concat([df, create_dataframe(url)])
        except Exception as e:
            print(e)
            df.to_csv('urls.csv', mode='a', index=False,header=False)

    # save it to csv
    df.to_csv('urls.csv', mode='a', index=False,header=False)

    # calculate numbers_percent as a percentage of numbers in url devided by url_len
    df = pd.read_csv('urls.csv')
    # Apply the function to create the 'numbers_percent' column
    df['numbers_percent'] = df['url'].apply(lambda x: calculate_numbers_percent(x))

    df.drop_duplicates(subset=['url'], inplace=True, keep='first')
    # Save the dataframe to a CSV file
    df.to_csv('urls.csv', index=False)

