import requests
from bs4 import BeautifulSoup
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

def scrape_fca_news():
    """Scrapes the latest news from the FCA website and saves it to a CSV file."""
    URL = "https://www.fca.org.uk/news/search-results?n_search_term&category=news%20stories%2Cpress%20releases&sort_by=dmetaZ"
    response = requests.get(URL)
    
    if response.status_code != 200:
        print(f"Failed to retrieve page, status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    articles = soup.find_all('li', class_='fca-search-results__item')
    
    scraped_data = []
    for article in articles:
        title_element = article.find('a')
        date_element = article.find('span', class_='fca-search-results__item-date')
        if title_element and date_element:
            title = title_element.get_text(strip=True)
            link = "https://www.fca.org.uk" + title_element['href']
            date = date_element.get_text(strip=True)
            scraped_data.append([date, title, link])
    
    # Save the data to a CSV file
    csv_filename = 'fca_news.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Date', 'Title', 'Link'])
        writer.writerows(scraped_data)
    
    print(f"Data saved to {csv_filename}")
    return csv_filename

def send_email(csv_file):
    """Reads the CSV file and emails its content."""
    # --- Email Configuration ---
    # These will be set as GitHub Secrets
    sender_email = os.environ.get('SENDER_EMAIL')
    receiver_email = os.environ.get('RECEIVER_EMAIL')
    password = os.environ.get('EMAIL_PASSWORD')

    if not all([sender_email, receiver_email, password]):
        print("Email credentials not found in environment variables. Skipping email.")
        return

    # --- Read CSV content for email body ---
    with open(csv_file, 'r', encoding='utf-8') as file:
        email_body = file.read()

    # --- Create the Email ---
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Your Daily FCA News Update"

    msg.attach(MIMEText("Here are the latest articles from the FCA:\n\n", 'plain'))
    msg.attach(MIMEText(email_body, 'plain'))

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
    news_csv = scrape_fca_news()
    if news_csv:
        send_email(news_csv)
