import re
from bs4 import BeautifulSoup as bs


f  = open('./rent.html', 'r', encoding='utf-8')
page_source = bs(f, 'lxml')
class DivarHouse():
    
    def __init__(self, html):

        self.page_source = html.find('div', attrs={'class':'kt-col-5'})

    
    def extract_info(self):
        data = {}
        divs = self.page_source.find_all('div', attrs={'class':'kt-base-row kt-base-row--large kt-unexpandable-row'})
        if divs:
            for div in divs:
                title = div.find('p', attrs={'class':'kt-base-row__title kt-unexpandable-row__title'})
                value = div.find('div', attrs={'class':'kt-base-row__end kt-unexpandable-row__value-box'})

                if title and value:
                    data[title.text.strip()] = value.text.strip()

        area = self.page_source.find_all('div', attrs={'class':'kt-group-row-item kt-group-row-item--info-row'})
        if area:
            for a in area:
                title = a.find('span', attrs={'class':re.compile('.*title.*')})
                value = a.find('span', attrs={'class':re.compile('.*value.*')})
                if title and value:
                    data[title.text.strip()] = value.text.strip()
        
        features = self.page_source.find_all('span', attrs={'class':'kt-group-row-item__value kt-body kt-body--stable'})
        
        data['elevator'] = features[0].text
        data['parking'] = features[1].text
        data['Depot'] = features[2].text

        data['location'] = self.page_source.find('div', attrs={'class':'kt-page-title__subtitle kt-page-title__subtitle--responsive-sized'}).text.split('در')[1]

        return data
        
    

object = DivarHouse(page_source)


print(object.extract_info())

from bs4 import BeautifulSoup as bs
import requests
import time
import re
import selenium
import urllib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common import exceptions
from selenium.webdriver.chrome.options import Options
import psycopg2
from datetime import date
from divarhome import DivarHouse



conn = psycopg2.connect(host='localhost', dbname= 'bama',
                    user='postgres', password='123',
                    port=5432)

cursor = conn.cursor()
conn.autocommit = True

# Create Database if it is not exist
cursor.execute("SELECT * FROM pg_catalog.pg_database WHERE datname = 'bama'")
db_exists = cursor.fetchone()
#print(db_exists) # not working
if not db_exists:
    cursor.execute('CREATE DATABASE Bama')


#cursor.execute("""DROP TABLE bamalinks""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS divarlinks(
    ID serial  PRIMARY KEY,
    LINK VARCHAR(250) NOT NULL UNIQUE,
    TIME Date DEFAULT CURRENT_DATE
)""")

#cursor.execute("""
#DROP TABLE IF EXISTS CarInfo
#""")


class Data_Gathering():
    def __init__(self):
        self.base_url = 'https://divar.ir/s/mazandaran-province/real-estate'

        self.driver = None

    def load_driver(self):

        service = Service()
        chrome_options = Options()

        chrome_options.add_argument('--disable-notifications')
        #chrome_options.add_argument('--headless')
        #chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=service, options=chrome_options)




    def extract_links(self):
        self.load_driver()
        url = self.base_url
        self.driver.get(url)
        for i in range(30):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

            response_text = self.driver.page_source
            page_source = bs(response_text, 'html.parser')
            links = page_source.find_all("a", attrs={"href":re.compile('.*/v.*')})
            links = [i['href'] for i in links]
            time.sleep(3)

        return links



    def links2db(self):


        links = self.extract_links()
        for link in links:

        
            cursor.execute("""INSERT INTO divarlinks(LINK) VALUES(%s) 
            ON CONFLICT(LINK) DO NOTHING
            """,(link,))




        return DivarHouse(page_source).extract_info()


obj = Data_Gathering()

obj.links2db()