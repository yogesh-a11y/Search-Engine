from crawler.selenium_crawler import ImprovedSeleniumCrawler
from indexing.inverted_index2 import AdvancedInvertedIndex
import json, os

BASE_URL = "https://pureportal.coventry.ac.uk/en/organisations/ics-research-centre-for-computational-science-and-mathematical-mo"

crawler = ImprovedSeleniumCrawler(crawl_delay=3)
pubs = crawler.crawl_department(BASE_URL, 50)

index = AdvancedInvertedIndex()
for i, p in enumerate(pubs):
    index.add_document(i, p)

index.save("data/index.pkl")

with open("data/data.json", "w") as f:
    json.dump(pubs, f, indent=2)
