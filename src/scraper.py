from dotenv import load_dotenv
import os
import requests
import psycopg2
from bs4 import BeautifulSoup 

load_dotenv()

conn = psycopg2.connect(
    host = os.getenv('DB_HOST'),
    database = os.getenv('DB_NAME'),
    port = os.getenv('DB_PORT'),
    user = os.getenv('DB_USER'),
    password = os.getenv('DB_PASSWORD')
)


def runScraper() :
    # GET Request
    URL =  'https://jojowiki.com/Art_Gallery#2021-2025-0'
    requests_session = requests.Session()
    page = requests_session.get( URL )  

    # Check for successful status code (200)
    print("Status Code - {}".format(page.status_code))
     

    # HTML Parser
    soup = BeautifulSoup(page.text, "lxml")
    divs = soup.find("div", {"class":"phantom-blood-tabs"})
    entries = divs.find_all("table", {"class":"diamonds volume"})

    # Scrapes every artwork entry on the page
    for entry in entries :

        # Initializes each subsection of an artwork entry, containing:
            # Artwork      (artworkList)
            # Date         (date)
            # Original Use (sourceTitle)
            # Source Image (sourceImgList)

        sections = entry.find_all("td", {"class":"volume"}) # Subsections are stored in <td> tags with class:"volume"
        artworkList = []
        date = ""
        sourceTitle = ""
        sourceImgList = []


        sectionCounter = 1 # Tracks which subsection/column is being viewed (sections are referred to as "volumes" within the html)
        for section in sections :

            # If on a subsection containing images (1 and 4), scrape image content
            if(sectionCounter == 1 or sectionCounter == 4) :
                thumbnails = section.find_all("a") # href is stored within <a> tags

                # For every thumbnail image, find full-res webpage and create new 
                for thumbnail in thumbnails :

                    # Grabs href for full-res image webpage from thumbnail container
                        # href = /File:ARTORK_NAME
                    href = thumbnail.get('href') 
                    newURL = f"https://jojowiki.com{href}" # Appends href to domain to form new url

                    # Temporary HTML parser to scrape full-res image
                    newRequests_session = requests.Session()
                    newPage = newRequests_session.get( newURL )  
                    newSoup = BeautifulSoup(newPage.text, "lxml")

                    media = newSoup.find("a", {"class":"internal"})
                    src = media.get('href') # Grabs image source-link
                    alt = media.get('title') # Grabs image alt text


                    if(sectionCounter == 1) :
                        # Stores in allArtEntries list
                        artworkObj = Artwork(src, alt) 
                        artEntryObj.artworkList.append(artworkObj) 

                        # Stores in CSV
                        artworkList.append("<src: " + src + "\nalt: " + alt + ">") # Uses <> for separation of entries and ease of possible parsing

                    elif(sectionCounter == 4) :
                        # Stores in allArtEntries list
                        srcImgObj = Artwork(src, alt) 
                        artEntryObj.sourceImgList.append(srcImgObj) 

                        # Stores in CSV
                        sourceImgList.append("<src: " + src + "\nalt: " + alt + ">") # Uses <> for separation of entries and ease of possible parsing

            # If on a subsection containing text (2 and 3), scrape text content
            elif(sectionCounter == 2 or sectionCounter == 3) :
                textContent = section.find("center") # Text content is stored within <center> tags

                for string in textContent.strings :
                    if(sectionCounter == 2) :
                        date += string
                    elif(sectionCounter == 3) :
                        sourceTitle += string

            # After scraping subsection, update tracker to next
            sectionCounter += 1
        
        # Appends artEntry to list allArtEntries
        artEntryObj.date = date
        artEntryObj.sourceTitle = sourceTitle
        allArtEntries.append(artEntryObj)

        # Writes to csv file, formatting the image lists into formatted strings
        writer.writerow([formatImgList(artworkList), date, sourceTitle, formatImgList(sourceImgList)])
        pickle.dump(allArtEntries, open("artEntriesData.p", "wb"))