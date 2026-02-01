import time
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class ImprovedSeleniumCrawler:
    """
    Selenium-based crawler for Coventry PurePortal
    """

    def __init__(self, crawl_delay=2):
        """
        :param crawl_delay: seconds to wait between requests (polite crawling)
        """
        self.driver = None
        self.crawl_delay = crawl_delay
        self.seen_titles = set()

    def init_driver(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

    def crawl_department(self, base_url, max_authors=20):
        self.init_driver()
        publications = []

        # ---------- Load department page ----------
        self.driver.get(base_url)
        time.sleep(self.crawl_delay)

        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # ---------- Extract author profile links ----------
        author_links = list({
            urljoin(base_url, a["href"])
            for a in soup.find_all("a", href=True)
            if "/en/persons/" in a["href"]
        })[:max_authors]

        # ---------- Crawl each author ----------
        for profile_url in author_links:
            self.driver.get(profile_url)
            time.sleep(self.crawl_delay)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            name_tag = soup.find("h1")
            author_name = name_tag.get_text(strip=True) if name_tag else "Unknown Author"

            # ---------- Extract publications ----------
            for pub in soup.find_all("a", href=re.compile("/en/publications/")):
                title = pub.get_text(strip=True)

                # Deduplication
                if title.lower() in self.seen_titles:
                    continue
                self.seen_titles.add(title.lower())

                container_text = pub.parent.get_text(" ")

                # Year extraction
                year_match = re.search(r"(19|20)\d{2}", container_text)
                year = int(year_match.group()) if year_match else None

                # Co-authors
                co_authors = [
                    a.get_text(strip=True)
                    for a in pub.parent.find_all("a", href=re.compile("/en/persons/"))
                ]

                if author_name not in co_authors:
                    co_authors.insert(0, author_name)

                publications.append({
                    "title": title,
                    "authors": list(set(co_authors)),
                    "year": year,
                    "publication_link": urljoin(profile_url, pub["href"]),
                    "profile_link": profile_url,
                    "crawled_at": datetime.now().isoformat()
                })
import time
import re
from urllib.parse import urljoin
from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class ImprovedSeleniumCrawler:
    """
    Selenium-based crawler for Coventry PurePortal
    with robust year extraction and polite crawling
    """

    def __init__(self, crawl_delay=2):
        self.driver = None
        self.crawl_delay = crawl_delay
        self.seen_titles = set()

    def init_driver(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

    def crawl_department(self, base_url, max_authors=20):
        self.init_driver()
        publications = []

        # ---------- Load department page ----------
        self.driver.get(base_url)
        time.sleep(self.crawl_delay)

        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # ---------- Extract author profile links ----------
        author_links = list({
            urljoin(base_url, a["href"])
            for a in soup.find_all("a", href=True)
            if "/en/persons/" in a["href"]
        })[:max_authors]

        # ---------- Crawl each author ----------
        for profile_url in author_links:
            self.driver.get(profile_url)
            time.sleep(self.crawl_delay)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            name_tag = soup.find("h1")
            author_name = name_tag.get_text(strip=True) if name_tag else "Unknown Author"

            # ---------- Extract publications ----------
            for pub_link in soup.find_all("a", href=re.compile("/en/publications/")):
                title = pub_link.get_text(strip=True)

                # ---- Deduplication ----
                if not title or title.lower() in self.seen_titles:
                    continue
                self.seen_titles.add(title.lower())

                # ---------- ROBUST YEAR EXTRACTION ----------
                year = None

                # 1️⃣ Try closest logical container
                container = pub_link.find_parent(["li", "article", "div"])
                if container:
                    text = container.get_text(" ")
                    match = re.search(r"(19|20)\d{2}", text)
                    if match:
                        year = int(match.group())

                # 2️⃣ Fallback: parent text
                if year is None:
                    text = pub_link.parent.get_text(" ")
                    match = re.search(r"(19|20)\d{2}", text)
                    if match:
                        year = int(match.group())

                # ---------- Co-authors ----------
                co_authors = [
                    a.get_text(strip=True)
                    for a in pub_link.find_parent(["li", "article", "div"])
                    .find_all("a", href=re.compile("/en/persons/"))
                ] if pub_link.find_parent(["li", "article", "div"]) else []

                if author_name not in co_authors:
                    co_authors.insert(0, author_name)

                publications.append({
                    "title": title,
                    "authors": list(set(co_authors)),
                    "year": year,
                    "publication_link": urljoin(profile_url, pub_link["href"]),
                    "profile_link": profile_url,
                    "crawled_at": datetime.now().isoformat()
                })

        self.driver.quit()
        return publications


        self.driver.quit()
        return publications
