from dotenv import load_dotenv
import os
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

