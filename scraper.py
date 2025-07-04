import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# List of URLs to scrape
urls = [
    "https://www.fca.org.uk/firms/financial-crime-systems-and-controls",
    "https://www.fca.org.uk/firms/financial-crime/financial-sanctions",
    "https://www.fca.org.uk/publication/finalised-guidance",
    "https://www.fca.org.uk/publication/policy-statements",
    "https://www.fca.org.uk/publication/research",
    "https://www.legislation.gov.uk/ukpga/2002/29/contents",
    "https://www.legislation.gov.uk/ukpga/2017/21/contents",
    "https://www.legislation.gov.uk/ukpga/2018/13/contents",
    "https://www.legislation.gov.uk/uksi/2017/692/contents",
    "https://www.fca.org.uk/news/press-releases/",
    "https://www.fca.org.uk/news/speeches/",
    "https://www.fca.org.uk/publications/corporate-documents",
    "https://www.fca.org.uk/publications/finalised-guidance",
    "https://www.fca.org.uk/publications/multi-firm-reviews",
    "https://www.fca.org.uk/publications/primary-market-bulletins",
    "https://www.fca.org.uk/scamsmart",
    "https://www.fca.org.uk/consumers",
    "https://www.fca.org.uk/firms/being-regulated/enforcement",
    "https://www.fca.org.uk/firms/financial-crime",
    "https://www.fca.org.uk/markets/market-abuse",
    "https://www.fca.org.uk/consumers/how-complain"
]

all_updates = []

def parse_fca_page(soup, url):
    """Parses a standard FCA page to extract title, date, and summary."""
    try:
        title = soup.find('h1', class_='page-title').get_text(strip=True)

        # Attempt to find the publication date
        published_date_tag = soup.find('p', text=re.compile(r'Published:'))
        if published_date_tag:
            date = published_date_tag.get_text(strip=True).replace('Published:', '').strip()
        else:
            # Fallback for other date formats or tags
            date_tag = soup.find('span', class_='date-display-single')
            if date_tag:
                 date = date_tag.get_text(strip=True)
            else:
                 date = "Not found"

        # Extract summary/content from the main content area
        content_section = soup.find("div", class_=re.compile(r"layout--onecol|layout-content"))
        if content_section:
            paragraphs = content_section.find_all("p")
            summary = " ".join([p.get_text(strip=True) for p in paragraphs if not re.search(r'Published:|Contact us', p.get_text())])
        else:
            summary = "Content section not found."

        return {"Title": title, "URL": url, "Date": date, "Summary": summary.strip()}
    except Exception as e:
        print(f"Error parsing FCA page {url}: {e}")
        return None

def parse_legislation_page(soup, url):
    """Parses a legislation.gov.uk contents page."""
    try:
        title = soup.find('h1', class_='title').get_text(strip=True)
        # The content is a list of provisions, which can serve as a summary
        content_items = soup.find_all('p', class_='LegProvision-title')
        summary = "; ".join([item.get_text(strip=True) for item in content_items])
        if not summary:
            summary = "No provisions listed on the contents page."
        return {"Title": title, "URL": url, "Date": "N/A", "Summary": summary}
    except Exception as e:
        print(f"Error parsing legislation page {url}: {e}")
        return None

# --- Main Script ---
for url in urls:
    if url.lower().endswith('.pdf'):
        print(f"Skipping PDF file: {url}")
        continue

    print(f"Scraping: {url}")
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.content, "html.parser")

        data = None
        if "fca.org.uk" in url:
            data = parse_fca_page(soup, url)
        elif "legislation.gov.uk" in url:
            data = parse_legislation_page(soup, url)
        else:
            print(f"Skipping unsupported domain: {url}")
            continue

        if data:
            all_updates.append(data)

    except requests.exceptions.RequestException as e:
        print(f"Could not retrieve {url}: {e}")

# Save the collected data to a CSV file
if all_updates:
    df = pd.DataFrame(all_updates)
    df.to_csv("fca_updates.csv", index=False)
    print("\nScraping complete. Data saved to fca_updates.csv")
else:
    print("\nScraping complete. No data was extracted.")
