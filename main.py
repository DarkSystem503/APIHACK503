import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import concurrent.futures
import logging
import jsbeautifier
import time
import random
import getpass
from prettytable import PrettyTable
from pyfiglet import Figlet
from termcolor import colored

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# User-Agent rotation
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

def get_random_user_agent():
    return random.choice(user_agents)

def fetch_page_content(url):
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        return None

def extract_urls(content, base_url):
    soup = BeautifulSoup(content, 'html.parser')
    urls = set()

    for a_tag in soup.find_all('a', href=True):
        url = a_tag['href']
        full_url = urllib.parse.urljoin(base_url, url)
        urls.add(full_url)

    for script in soup.find_all('script', src=True):
        url = script['src']
        full_url = urllib.parse.urljoin(base_url, url)
        urls.add(full_url)

    for script in soup.find_all('script'):
        if script.string:
            matches = re.findall(r'https?://[^\s"]+', script.string)
            for match in matches:
                full_url = urllib.parse.urljoin(base_url, match)
                urls.add(full_url)

    return urls

def filter_api_endpoints(urls):
    api_endpoints = set()
    api_pattern = re.compile(r'/api/|/v\d+/|/service/')
    for url in urls:
        if api_pattern.search(url):
            api_endpoints.add(url)
    return api_endpoints

def deobfuscate_js(js_code):
    try:
        beautified_code = jsbeautifier.beautify(js_code)
        return beautified_code
    except Exception as e:
        logging.error(f"Error deobfuscating JavaScript: {e}")
        return js_code

def analyze_js_files(js_urls):
    api_endpoints = set()
    api_pattern = re.compile(r'/api/|/v\d+/|/service/')

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch_page_content, js_url): js_url for js_url in js_urls}
        for future in concurrent.futures.as_completed(future_to_url):
            js_url = future_to_url[future]
            try:
                js_content = future.result()
                if js_content:
                    beautified_js = deobfuscate_js(js_content)
                    matches = re.findall(r'https?://[^\s"]+', beautified_js)
                    for match in matches:
                        if api_pattern.search(match):
                            api_endpoints.add(match)
            except Exception as e:
                logging.error(f"Error analyzing JavaScript file {js_url}: {e}")

    return api_endpoints

def discover_apis(url, visited_urls):
    if url in visited_urls:
        return set()
    visited_urls.add(url)

    content = fetch_page_content(url)
    if content:
        urls = extract_urls(content, url)
        api_endpoints = filter_api_endpoints(urls)

        js_urls = [u for u in urls if u.endswith('.js')]
        js_api_endpoints = analyze_js_files(js_urls)
        api_endpoints.update(js_api_endpoints)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(discover_apis, linked_url, visited_urls): linked_url for linked_url in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                linked_url = future_to_url[future]
                try:
                    linked_api_endpoints = future.result()
                    api_endpoints.update(linked_api_endpoints)
                except Exception as e:
                    logging.error(f"Error discovering APIs for {linked_url}: {e}")

        return api_endpoints
    return set()

def retrieve_api_data(api_url):
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'application/json',
    }
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error retrieving data from {api_url}: {e}")
        return None

def display_banner():
    f = Figlet(font='slant')
    banner = f.renderText('API Hack 503')
    print(colored(banner, 'red'))
    print(colored("Selamat Datang di Layanan API Hack 503", 'red'))
    print(colored("BY MR.4REX_503", 'red'))

def display_results(api_endpoints, api_data):
    table = PrettyTable()
    table.field_names = ["API Endpoint", "Data"]
    for endpoint, data in zip(api_endpoints, api_data):
        table.add_row([endpoint, data])
    print(colored(table, 'cyan'))

def login():
    print(colored("Login ko dulu Kontol", 'red'))
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")
    if username == "admin" and password == "password":
        print(colored("Login successful!", 'green'))
        return True
    else:
        print(colored("salah iii memek", 'red'))
        return False

def main():
    if not login():
        return

    display_banner()

    target_url = input("Target mu ASU: ")
    visited_urls = set()

    api_endpoints = discover_apis(target_url, visited_urls)
    api_data = []
    if api_endpoints:
        print(colored("Discovered API Endpoints:", 'yellow'))
        for endpoint in api_endpoints:
            print(colored(endpoint, 'yellow'))
            api_data.append(retrieve_api_data(endpoint))

        display_results(api_endpoints, api_data)
    else:
        print(colored("No API endpoints found", 'red'))

if __name__ == "__main__":
    main()
