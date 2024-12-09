import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from queue import Queue
from threading import Thread
from random import choice
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from colorama import Fore, Style

# Color constants
GREEN = Fore.GREEN
RED = Fore.RED
RESET = Style.RESET_ALL

# User-Agent list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
]

# Function to print custom banner
def print_custom_banner():
    banner = """
      #######      ##            ##      ##########  #########  
      ##      ##   ##           ## ##           ##   ##
      ##       ##  ##          ##   ##         ##    ##
      ##      ##   ##         ##     ##       ##     ##
      ########     ##         #########      ##      #########
      ##      ##   ##         ##     ##     ##       ##
      ##       ##  ##         ##     ##    ##        ##
      ##      ##   ##         ##     ##   ##         ##
      #######      #########  ##     ##  #########   #########
                                 
                                       author- Ayush Singh
_________________________________________________________________                               
    """
    print(f"{RED}{banner}{RESET}")

# Function to fetch and parse robots.txt
def parse_robots_txt(url):
    robots_url = urljoin(url, "/robots.txt")
    try:
        response = requests.get(robots_url, headers={"User-Agent": choice(USER_AGENTS)}, timeout=10)
        if response.status_code == 200:
            print(f"{GREEN}[+] Fetched robots.txt: {robots_url}{RESET}")
            return response.text.splitlines()
    except Exception as e:
        print(f"{GREEN}[!] Error fetching robots.txt: {e}{RESET}")
    return []

# Function to extract links from a page
def extract_links(url, domain, visited):
    links = []
    try:
        response = requests.get(
            url, headers={"User-Agent": choice(USER_AGENTS)}, timeout=10
        )
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup.find_all("a", href=True):
            link = urljoin(url, tag["href"])
            if is_valid_url(link, domain, visited):
                links.append(link)
    except Exception as e:
        print(f"{GREEN}[!] Error extracting links from {url}: {e}{RESET}")
    return links

# Function to validate URLs
def is_valid_url(url, domain, visited):
    parsed_url = urlparse(url)
    return (
        parsed_url.scheme in ["http", "https"]
        and domain in parsed_url.netloc
        and url not in visited
    )

# Worker function for crawling
def crawl_worker(queue, domain, visited, results):
    while not queue.empty():
        url = queue.get()
        if url in visited:
            queue.task_done()
            continue
        visited.add(url)
        print(f"{GREEN}[+] Crawling:{RESET} {RED}{url}{RESET}")  # Green "Crawling" and Red URL
        links = extract_links(url, domain, visited)
        results.extend(links)
        for link in links:
            queue.put(link)
        queue.task_done()

# Brute-force hidden pages
def brute_force_hidden_pages(base_url, wordlist, results):
    for word in wordlist:
        target_url = f"{base_url.rstrip('/')}/{word}"
        try:
            response = requests.get(
                target_url, headers={"User-Agent": choice(USER_AGENTS)}, timeout=5
            )
            if response.status_code == 200:
                print(f"{RED}[+] Found (Brute-force): {target_url}{RESET}")  # Results in RED
                results.append(target_url)
        except Exception as e:
            print(f"{GREEN}[!] Error Brute-forcing {target_url}: {e}{RESET}")

# Main function
def main():
    print_custom_banner()  # Print custom banner

    base_url = input(f"{GREEN}Enter the website URL: {RESET}").strip()
    max_depth = int(input(f"{GREEN}Enter maximum crawling depth (e.g., 3): {RESET}").strip())
    threads = int(input(f"{GREEN}Enter number of threads (e.g., 10): {RESET}").strip())
    use_default_wordlist = input(f"{GREEN}Use default wordlist? (yes/no): {RESET}").strip().lower()

    # Load wordlist
    if use_default_wordlist == "yes":
        wordlist = ["admin", "login", "dashboard", "config"]
    else:
        wordlist_file = input(f"{GREEN}Enter the path to your wordlist file: {RESET}").strip()
        wordlist = load_wordlist(wordlist_file)

    # Fetch robots.txt
    robots = parse_robots_txt(base_url)

    # Setup
    domain = urlparse(base_url).netloc
    queue = Queue()
    visited = set()
    results = []

    # Add base URL to the queue
    queue.put(base_url)

    # Start crawling
    print(f"{GREEN}[!] Starting Crawling...{RESET}")
    for _ in range(threads):
        thread = Thread(target=crawl_worker, args=(queue, domain, visited, results))
        thread.start()
    queue.join()

    # Limit results by depth
    results = list(set(results))  # Remove duplicates
    if max_depth > 0:
        results = results[:max_depth]

    # Start brute-forcing
    print(f"\n{GREEN}[!] Starting Brute-force Hidden Page Search...{RESET}")
    brute_force_hidden_pages(base_url, wordlist, results)

    # Display results on terminal
    print(f"\n{GREEN}[!] Discovered Pages and Links:{RESET}")
    for page in results:
        print(f"{RED}{page}{RESET}")  # Results in RED


if __name__ == "__main__":
    main()