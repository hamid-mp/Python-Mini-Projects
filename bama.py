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



class CarInfo():

    def __init__(self, html):
        self.html = html

    def price(self):
        x = self.html.find('span', attrs={'class':re.compile('bama-ad-detail-price__price-text.*')})
        if x:
            x = x.text.strip() if x.text != 'توافقی' else 'N/A'
        else:
            x = 'N/A'
        return x

    def location(self):
        x = self.html.find('span', attrs={'class':re.compile('address-text')})
        if x:
            x = x.text.strip()[:28]
        else:
            x = 'N/A'
        return x
    def name(self):
        
        x = self.html.find('h1', attrs={'class':'bama-ad-detail-title__title'})
        if x:
        
            name, model = x.text.split('،')
            name = name.strip()
            model = model.strip()
        else:
            
            name= 'N/A'
            model = 'N/A'
        return name, model
    def modelvscategory(self):
        x = self.html.find_all('span', attrs={'class':'bama-ad-detail-title__subtitle'})
        
        if x:
            year, subbrand = self.html.find_all('span', attrs={'class':'bama-ad-detail-title__subtitle'})
            
            year = int(year.text.strip())
            subbrand = subbrand.text.strip()
            if year > 1950:
                year -= 621
                year = str(year)
        else:
            year = 'N/A'
            subbrand = 'N/A'
        return year, subbrand

    def otherInfo(self):
        data = {}
        info = self.html.find_all('div', attrs={'class':'bama-vehicle-detail-with-icon__detail-holder'})
        for char in info:
            field = char.find('span')
            x = char.find('p')#, attrs={'class':'data-v-data-v-2dd7bb62'})
            data[field.text] = x.text
 
        return data
    
    def all_info(self):
        data = self.otherInfo()
        year, subbrand = self.modelvscategory()
        data['year'] = year
        data['subbrand'] = subbrand
        data['location'] = self.location()
        data['price'] = self.price()
        name, brand = self.name()
        data['Brand'] = name
        data['Model'] = brand
        if data['year'] == 'N/A' and data['year'] == 'N/A' and data['Brand'] == 'N/A':
            return None
        else:
            return data 
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
CREATE TABLE IF NOT EXISTS bamalinks(
    ID serial  PRIMARY KEY,
    LINK VARCHAR(250) NOT NULL UNIQUE,
    TIME Date DEFAULT CURRENT_DATE
)""")

#cursor.execute("""
#DROP TABLE IF EXISTS CarInfo
#""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS CarInfo(
    ID serial  PRIMARY KEY,
    BRAND VARCHAR(40) NOT NULL,
    MODEL VARCHAR(30),
    SUBMODEL VARCHAR(30),
    YEAR VARCHAR(4) NOT NULL,
    LOCATION VARCHAR(30),
    PRICE VARCHAR(20) NOT NULL,
    GearBox Varchar(20),
    Operations VARCHAR(20) NOT NULL,
    BODY VARCHAR(20),
    GAS Varchar(20),
    COLOR VARCHAR(20),
    INSIDECOLOR VARCHAR(20),
    UNIQUE(BRAND, YEAR, PRICE, Operations)
)""")


class Data_Gathering():
    def __init__(self):
        self.base_url = 'https://bama.ir'

        self.driver = None

    def load_driver(self):

        service = Service()
        chrome_options = Options()

        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=service, options=chrome_options)




    def extract_links(self, domain='/car'):
        self.load_driver()
        url = self.base_url + domain
        self.driver.get(url)
        for i in range(20):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)


        response_text = self.driver.page_source
        page_source = bs(response_text, 'html.parser')
        links = page_source.find_all("a", attrs={"href":re.compile('/car/.*')})
        links = [i['href'] for i in links]
        return links

    def info2db(self):
        self.load_driver()
        cursor.execute("SELECT * FROM bamalinks")
        data = cursor.fetchall()
        
        for d in data:

            if d[2] == date.today():
                url = self.base_url + d[1]
                #print(url)
                CarInfo = self.extract_carinfo(url)
                #print(CarInfo)
                if CarInfo:
                    cursor.execute("""
                        INSERT INTO CarInfo (
                            BRAND, MODEL, SUBMODEL, YEAR, LOCATION, PRICE, GearBox,
                            Operations, BODY, GAS, COLOR, INSIDECOLOR
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) 
                        ON CONFLICT(BRAND, YEAR, PRICE, Operations) DO NOTHING
                    """, (
                        CarInfo['Brand'], CarInfo['Model'], CarInfo['subbrand'],
                        (CarInfo['year']), CarInfo['location'], CarInfo['price'],
                        CarInfo['گیربکس'], CarInfo['کارکرد'], CarInfo['وضعیت بدنه'],
                        CarInfo['نوع سوخت'], CarInfo['رنگ بدنه'], CarInfo['رنگ داخلی']
                    ))
            #time.sleep(3)
            #cursor.execute("SELECT * FROM CarInfo")
            #print(cursor.fetchall())

    def links2db(self):


        links = self.extract_links()
        for link in links:

        
            cursor.execute("""INSERT INTO bamalinks(LINK) VALUES(%s) 
            ON CONFLICT(LINK) DO NOTHING
            """,(link,))


    def extract_carinfo(self, url):
        cursor.execute("SELECT * FROM bamalinks WHERE TIME=current_date")
        self.driver.get(url)
        response_text = self.driver.page_source
        page_source = bs(response_text, 'html.parser')


        return CarInfo(page_source).all_info()








Scraper = Data_Gathering()

Scraper.links2db()

Scraper.info2db()

cursor.execute("SELECT * FROM CarInfo")
#print(cursor.fetchall())



conn.commit()
cursor.close()
conn.close()