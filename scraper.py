import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://www.fca.org.uk/publications/policy-statements/ps24-17-financial-crime-guide-updates"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

content_section = soup.find("div", class_="layout layout--onecol")
updates = []

if content_section:
    paragraphs = content_section.find_all(["h2", "p"])
    current_title = ""
    current_date = ""
    current_summary = ""

    for tag in paragraphs:
        if tag.name == "h2":
            if current_title:
                updates.append({
                    "Title": current_title.strip(),
                    "Date": current_date.strip(),
                    "Summary": current_summary.strip()
                })
                current_summary = ""
            current_title = tag.get_text()
            current_date = ""
        elif tag.name == "p":
            if "Published" in tag.get_text():
                current_date = tag.get_text().replace("Published:", "").strip()
            else:
                current_summary += tag.get_text() + " "

    if current_title:
        updates.append({
            "Title": current_title.strip(),
            "Date": current_date.strip(),
            "Summary": current_summary.strip()
        })

df = pd.DataFrame(updates)
df.to_csv("fca_updates.csv", index=False)
print("Scraping complete. Data saved to fca_updates.csv")
