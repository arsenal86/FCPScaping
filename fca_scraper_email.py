import requests
from bs4 import BeautifulSoup
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime

def scrape_fca_news():
    """Scrapes the latest news from the FCA website and saves it to a CSV file."""
    # Correct URL that sorts by newest articles first
    URL = "https://www.fca.org.uk/news/search-results?n_search_term=&category=news%20stories%2Cpress%20releases&sort_by=dmetaZ"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Use a session with headers to appear more like a regular browser
    session = requests.Session()
    response = session.get(URL, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to retrieve page, status code: {response.status_code}")
        return None, 0

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # **UPDATED SELECTOR**: The articles are now inside <article> tags
    articles = soup.find_all('article')
    
    if not articles:
        print("No articles found. The website structure may have changed again.")
        return None, 0

    scraped_data = []
    for article in articles:
        # **UPDATED SELECTOR**: The title is in an <h3> tag inside a link
        title_element = article.find('h3').find('a') if article.find('h3') else None
        
        # **UPDATED SELECTOR**: The date is in a <time> tag
        date_element = article.find('time')
        
        if title_element and date_element:
            title = title_element.get_text(strip=True)
            # The link is the href attribute of the 'a' tag
            link = title_element['href']
            # Make the link absolute if it's relative
            if not link.startswith('http'):
                link = "https://www.fca.org.uk" + link
            
            # The date is the 'datetime' attribute of the <time> tag
            date_str = date_element['datetime']
            # Format the date nicely to DD/MM/YYYY
            date_obj = datetime.fromisoformat(date_str)
            date = date_obj.strftime('%d/%m/%Y')

            scraped_data.append([date, title, link])
    
    # Save the data to a CSV file
    csv_filename = 'fca_news.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Date', 'Title', 'Link'])
        writer.writerows(scraped_data)
    
    print(f"{len(scraped_data)} articles saved to {csv_filename}")
    return csv_filename, len(scraped_data)

def send_email(csv_file, article_count):
    """Reads the CSV file and emails its content."""
    # --- Email Configuration ---
    sender_email = os.environ.get('SENDER_EMAIL')
    receiver_email = os.environ.get('RECEIVER_EMAIL')
    password = os.environ.get('EMAIL_PASSWORD')

    if not all([sender_email, receiver_email, password]):
        print("Email credentials not found in environment variables. Skipping email.")
        return

    # --- Read CSV content for email body ---
    email_body = ""
    if article_count > 0:
        with open(csv_file, 'r', encoding='utf-8') as file:
            # Skip the header
            next(file) 
            for line in file:
                date, title, link = line.strip().split(',', 2)
                email_body += f"Published: {date}\nTitle: {title}\nLink: {link}\n\n"
    else:
        email_body = "No new articles were found on the FCA website today."

    # --- Create the Email ---
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    today_date = datetime.now().strftime('%d/%m/%Y')
    msg['Subject'] = f"FCA News Update - {today_date} ({article_count} articles)"

    msg.attach(MIMEText(email_body, 'plain'))

    # --- Send the Email ---
    try:
        # Using Gmail's SMTP server
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
