import arxiv, logging
from biorxiv_retriever import BiorxivRetriever
from datetime import datetime, timedelta
import os
import requests
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
from io import BytesIO
from logging.handlers import TimedRotatingFileHandler

load_dotenv()  # take environment variables from .env

# Set your OpenAI API Key

from openai import OpenAI


# Configure logging
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
log_handler = TimedRotatingFileHandler('/home/rohan/Documents/arxiv_llm/automation_arxiv.log', when='midnight', interval=1)
log_handler.setFormatter(log_formatter)
log_handler.suffix = "%Y-%m-%d"
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

sheet_url = "https://docs.google.com/spreadsheets/d/1so95YlEVJmGjh8HPhEUPcp158HGPciyBldRq9DDsZ78/edit#gid=0"

# Email configuration
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_user = os.getenv("ID")
from_email = smtp_user
smtp_password = os.getenv("pawd")

# Define a function to use ChatGPT (gpt-3.5-turbo or gpt-4)
def summarize_paper(title, abstract):
    """
    Summarizes the title and abstract of a paper using OpenAI's Chat API.
    """
    prompt = f"Summarize the following research paper. Keep summary concie with only 2 to 3 lines and write form author's perspective:\nTitle: {title}\nAbstract: {abstract}\nSummary: \n\n"
    print(title)
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes research papers."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4o-mini",
            #response_format={"type": "json_object"},
        )
        # Extract and return the content of the assistant's response
        return chat_completion.choices[0].message.content.strip()
    
    except Exception as e:
        return f"Error summarizing paper: {str(e)}"


def filters(positive, negative, title, abstract):
    """
    Filters the papers based on positive and negative keywords.
    """
    title = title.lower()
    abstract = abstract.lower()
    if any(pos in title or pos in abstract for pos in positive) and not any(neg in title or neg in abstract for neg in negative):
        return True
    return False

# Log the start of the script
logger.info("Script started")

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)

## Query bioarxiv 24 hours
# Get today's date
today = datetime.today().strftime('%Y-%m-%d')
yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
# Example of a range of dates (1-week range)
start_date = yesterday
end_date = today  # Modify this for a range if needed



#####################################Replace this with the code from querying.py############################################
# URL to query the API
base_url = "https://api.biorxiv.org/details/biorxiv"
query_url = f"{base_url}/{start_date}/{end_date}/"

# Make the API request
print(query_url)
# Initialize variables
cursor = 0
all_entries = []

while True:
    # Construct the API URL with the current cursor
    url = f"{query_url}{str(cursor)}"
    logger.info(f"Querying {url}")
    # Make the API request
    response = requests.get(url)
    data = response.json()
    
    # Extract the total number of entries and the current batch of entries
    total = int(data['messages'][0]['total'])
    entries = data['collection']
    
    # Add the current batch of entries to the list of all entries
    all_entries.extend(entries)
    
    # Update the cursor for the next batch
    cursor += len(entries)
    print(cursor)
    # Check if we have collected all entries
    if cursor >= total:
        break

neuro_entries = []
for entries in all_entries:
    if 'neuro' in entries['category'].lower():
        neuro_entries.append(entries)


csv_export_url = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=')
df = pd.read_csv(csv_export_url)




to_email = "1810.rohan@gmail.com"
subject = f"Yesterdays preprints {end_date}"
from_email = smtp_user
contains = ["acetylcholine", "dopamine", "astrocyte", "neuromodulation", "computational","non-linear", "dynamical systems", "cholinergic", "serotonin", "neurotransmitter"]
not_contains = ["cancer", "tumor"]
# Create the email content
summarized = {}

for index, row in df.iterrows():
    email_content = "<h1>BioRxiv Neuroscience Abstracts and Titles</h1>"
    contains, not_contains = [x.strip() for x in row['Contains (comma separated)'].split(',')], [x.strip() for x in  row['Not contains (comma separated)'].split(',')]
    for entry in neuro_entries:
        if filters(contains, not_contains, entry['title'], entry['abstract']):
            if entry['doi'] not in summarized:
                summary = summarize_paper(entry['title'], entry['abstract'])
                entry['summary'] = summary
                summarized[entry['doi']] = entry
            else:
                summary = summarized[entry['doi']]['summary']
            email_content += f"<h2><a href='https://doi.org/{entry['doi']}'>{entry['title']}</a></h2>"
            email_content += f"<p>{summary}</p>"
            #email_content += f"<p><a href='https://doi.org/{entry['doi']}'>Read more</a></p>"

    # Create the email message

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = row['Email']
    msg['Subject'] = subject
    msg.attach(MIMEText(email_content, 'html'))
    to_email = row['Email']
    # Send the email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        #print("Email sent successfully to ", to_email)
        logger.info(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")


# Log the end of the script
logger.info("Script finished")