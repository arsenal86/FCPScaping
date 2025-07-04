import requests
from bs4 import BeautifulSoup
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime

def scrape_fca_news():
    """Scrapes the latest news from the FCA website based on user-provided HTML structure."""
    URL = "https://www.fca.org.uk/news/search-results?n_search_term=&category=news%20stories%2Cpress%20releases&sort_by=dmetaZ"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    }
    
    try:
        session = requests.Session()
        response = session.get(URL, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve the page. Error: {e}")
        return None, 0

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # **FINAL CORRECTOR based on user's HTML snippet**
    # The parent container for each result is a list item with class 'search-result'
    articles = soup.find_all('li', class_='search-result')
    
    if not articles:
        print("Scraper failed: Could not find any list items with class 'search-result'. The website structure has likely changed.")
        return None, 0

    scraped_data = []
    for article in articles:
        # The title/link is in an 'a' tag with class 'search-item__clickthrough'
        title_element = article.find('a', class_='search-item__clickthrough')
        
        # The date is in a 'span' tag with class 'search-item__date'
        date_element = article.find('span', class_='search-item__date')
        
        if title_element and date_element:
            title = title_element.get_text(strip=True)
            link = title_element['href']
            
            # Ensure the link is absolute
            if not link.startswith('http'):
                link = "https://www.fca.org.uk" + link
            
            date = date_element.get_text(strip=True)

            scraped_data.append([date, title, link])
    
    csv_filename = 'fca_news.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Date', 'Title', 'Link'])
        writer.writerows(scraped_data)
    
    article_count = len(scraped_data)
    if article_count > 0:
        print(f"Success! Found and saved {article_count} articles to {csv_filename}")
    else:
        # This case might occur if the selectors are right but there's no news, which is unlikely for the FCA.
        # More likely, it means a subtle change has occurred.
        print("Warning: Found the 'search-result' list but no articles inside. The internal structure may have changed.")
        
    return csv_filename, article_count

def send_email(csv_file, article_count):
    """Reads the CSV file and emails its content."""
    # --- Email Configuration ---
    sender_email = os.environ.get('SENDER_EMAIL')
    receiver_email = os.environ.get('RECEIVER_EMAIL')
    password = os.environ.get('EMAIL_PASSWORD')

    if not all([sender_email, receiver_email, password]):
        print("Email credentials not found in environment variables. Skipping email.")
        return

    # --- Create the Email Body ---
    email_body = ""
    if article_count > 0:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader) # Skip the header row
            for row in reader:
                if len(row) == 3: # Ensure the row has the expected number of columns
                    date, title, link = row
                    email_body += f"Published: {date}\nTitle: {title}\nLink: {link}\n\n"
    else:
        email_body = "No new articles were found on the FCA website today."

    # --- Create the Email Message ---
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    today_date = datetime.now().strftime('%d/%m/%Y')
    msg['Subject'] = f"FCA News Update - {today_date} ({article_count} articles)"

    msg.attach(MIMEText(email_body, 'plain', 'utf-8'))

    # --- Send the Email ---
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    news_csv, count = scrape_fca_news()
    if news_csv is not None:
        send_email(news_csv, count)
