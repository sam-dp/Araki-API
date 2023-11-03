from dotenv import load_dotenv
import os
import lxml
import urllib3
import requests
import psycopg2
from bs4 import BeautifulSoup 

class Artwork:
    src = ""
    alt = ""

    def __init__(self, src, alt):
        self.src = src
        self.alt = alt

    def getSrc(self):
        return self.src

    def getAlt(self):
        return self.alt
    

load_dotenv()

conn = psycopg2.connect(
    host = os.getenv('DB_HOST'),
    database = os.getenv('DB_NAME'),
    port = os.getenv('DB_PORT'),
    user = os.getenv('DB_USER'),
    password = os.getenv('DB_PASSWORD')
)

conn.autocommit = True
cursor = conn.cursor()
cursor.execute("SET client_encoding = 'UTF8'")

# GET Request
URL =  'https://jojowiki.com/Art_Gallery#1970-1990-0'
requests_session = requests.Session()
page = requests_session.get( URL )  

# Check for successful status code (200)
print("Status Code - {}".format(page.status_code))
    

# HTML Parser
soup = BeautifulSoup(page.text, "lxml")
divs = soup.find("div", {"class":"phantom-blood-tabs"})
entries = divs.find_all("table", {"class":"diamonds volume"})

# Scrapes every artwork entry on the page
LIMIT = 10
for entry in entries:

    # Initializes each subsection of an artwork entry, containing:
        # Artwork      (artworkList)
        # Date         (date)
        # Original Use (name)
        # Source Image (sourceImgList)

    sections = entry.find_all("td", {"class":"volume"}) # Subsections are stored in <td> tags with class:"volume"

    artworkList = []
    date = ""
    name = ""
    sourceImgList = []


    for sectionIndex, section in enumerate(sections) :

        # If on a subsection containing images (1 and 4), scrape image content
        if(sectionIndex == 1 or sectionIndex == 4) :
            thumbnails = section.find_all("a") # href is stored within <a> tags

            # For every thumbnail image, find full-res webpage and create new 
            for thumbnail in thumbnails :
                href = thumbnail.get('href')

                img = thumbnail.find("img")
                alt = img.get('alt')
                if(sectionIndex == 1):
                    artworkList.append(Artwork(href, alt))
                elif(sectionIndex == 4) :
                    sourceImgList.append(Artwork(href, alt))

        # If on a subsection containing text (2 and 3), scrape text content
        elif(sectionIndex == 2 or sectionIndex == 3) :
            textContent = section.find("center") # Text content is stored within <center> tags

            for string in textContent.strings :
                if(sectionIndex == 2) :
                    date += string
                elif(sectionIndex == 3) :
                    name += string
    
    # Check if ARTENTRY exists in database
        cursor.execute("SELECT id FROM artentry WHERE name = '%s' AND date = '%s';", (name, date))
        artentryID = cursor.fetchone()

        if not artentryID :
            cursor.execute("INSERT INTO artentry(name, date) VALUES(%s,%s)", (name, date))
            cursor.execute("SELECT id FROM artentry WHERE name = '%s' AND date = '%s';", (name, date))
            artentryID = cursor.fetchone()

    # Check if IMAGE exists in database                        
    for artwork in artworkList: 
        cursor.execute("SELECT id FROM image WHERE alt = '%s';", (artwork.getAlt()))
        imageID = cursor.fetchone()

        if not imageID:
            
            # Grabs href for full-res image webpage from thumbnail container
                    # href = /File:ARTORK_NAME
            newURL = f"https://jojowiki.com{artwork.getSrc()}" # Appends href to domain to form new url

            # Temporary HTML parser to scrape full-res image
            newRequests_session = requests.Session()
            newPage = newRequests_session.get( newURL )  
            newSoup = BeautifulSoup(newPage.text, "lxml")

            media = newSoup.find("a", {"class":"internal"})
            src = media.get('href') # Grabs image source-link
            alt = media.get('title') # Grabs image alt text

            cursor.execute("INSERT INTO image(artentry_id, url, alt) VALUES(%s,%s,%s)", (artentryID, src, alt))

    # Check if IMAGE exists in database                        
    for artwork in sourceImgList: 
        cursor.execute("SELECT id FROM source WHERE alt = '%s';", (artwork.getAlt()))
        imageID = cursor.fetchone()

        if not imageID:

            # Grabs href for full-res image webpage from thumbnail container
                    # href = /File:ARTORK_NAME
            newURL = f"https://jojowiki.com{artwork.getSrc()}" # Appends href to domain to form new url

            # Temporary HTML parser to scrape full-res image
            newRequests_session = requests.Session()
            newPage = newRequests_session.get( newURL )  
            newSoup = BeautifulSoup(newPage.text, "lxml")

            media = newSoup.find("a", {"class":"internal"})
            src = media.get('href') # Grabs image source-link
            alt = media.get('title') # Grabs image alt text

            cursor.execute("INSERT INTO source(artentry_id, url, alt) VALUES(%s,%s,%s)", (artentryID, src, alt))
    
    LIMIT -=1
    if LIMIT == 0 :
        break
        

conn.close()