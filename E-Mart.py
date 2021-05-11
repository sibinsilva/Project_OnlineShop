from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import sqlite3
from urllib.request import Request, urlopen
import requests


def Scraper_InitialPage(dbconnect):
    dbcursor = dbconnect.cursor()
    #Path = "D:/PY/E-Mart/"
    req = Request('https://www.websitename.ie/store/',
                  headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, 'html.parser')
    divs = soup.find_all(
        'div', class_='grid-category__card')
    for item in divs:
        try:
            Category = item.find(
                'div', class_='grid-category__shadow-inner').text.strip()
            #directory = Path + Category
            # if not os.path.exists(directory):
            #    os.makedirs(directory)
        except:
            pass
        try:
            tempLink = item.find(
                "a", {"class": "grid-category__title"})
            Link = tempLink['href']
        except:
            pass
        dbcursor.execute(
            """INSERT INTO ProductGroups(ProductGroup,SubGroup) values(?,?)""", (Category, ''))
        Item = {'Category': Category, 'Link': Link
                }
        MainItems.append(Item)
    dbconnect.commit()
    dbcursor.close()
    return


def Scraper_InnerPage(dbconnect, Category, itemURL, SubCategory=None):
    dbcursor = dbconnect.cursor()
    # if SubCategory is None:
    #    Path = "D:/PY/E-Mart/" + Category
    # else:
    #    Path = "D:/PY/E-Mart/" + Category + '/' + SubCategory
    req = Request(itemURL,
                  headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, 'html.parser')
    Folderdivs = soup.find_all(
        'div', class_='grid-category__card')
    for item in Folderdivs:
        try:
            SubList = item.find(
                'div', class_='grid-category__shadow-inner').text.strip()
            #directory = Path + '/' + SubList
            # if not os.path.exists(directory):
            #    os.makedirs(directory)
        except:
            pass
        try:
            tempLink = item.find(
                "a", {"class": "grid-category__title"})
            Link = tempLink['href']
        except:
            pass
        SubItem = {'Category': Category, 'SubCategory': SubList, 'Link': Link
                   }
        SubItems.append(SubItem)
        dbcursor.execute(
            """INSERT INTO ProductGroups(ProductGroup,SubGroup) values(?,?)""", (Category, SubList))
    dbconnect.commit()
    dbcursor.close()
    Itemdivs = soup.find_all(
        'div', class_='grid-product__wrap-inner')
    for divitem in Itemdivs:
        try:
            tempItemLink = divitem.find(
                "a", {"class": "grid-product__title"})
            ItemLink = tempItemLink['href']
        except:
            pass
        if ItemLink is not None:
            SaveItem(dbconnect, Category, ItemLink)
    return


def SaveItem(dbconnect, ProductGroup, URL):
    productcursor = dbconnect.cursor()
    #Filepath = path
    URL = URL.replace('€', '%E2%82%AC')
    URL = URL.replace('\u200b', 'A')
    req = Request(URL,
                  headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, 'html.parser')
    try:
        Itemdivs = soup.find_all(
            'div', class_='product-details__sidebar')
        for item in Itemdivs:
            ProductName = item.find(
                'h1', class_='product-details__product-title ec-header-h3').text.strip()
            ProductSKU = item.find(
                'div', class_='product-details__product-sku ec-text-muted').text.strip()
            ProductPrice = item.find(
                'span', class_='details-product-price__value ec-price-item notranslate').text.strip()
            ProductDescription = item.find(
                'div', class_='product-details__product-description').text.strip()
            if str(ProductName) != '':
                print(ProductName)
            picture = None
            ImageDiv = soup.find_all(
                'div', class_='details-gallery__image-wrapper')
            for link in ImageDiv:
                ImageURL = link.find_all('img', src=True)
                image_title = [x['title'] for x in ImageURL]
                image_src = [x['src'] for x in ImageURL]
                # url is definitely correct
                response = requests.get(image_src[0])
                picture = sqlite3.Binary(response.content)
            productcursor.execute(
                """INSERT OR IGNORE INTO Products(ProductName,ProductGroup,ProductSKU,ProductPrice,ProductDescription,Picture,CreationDate) values(?,?,?,?,?,?,?)""", (ProductName, ProductGroup, ProductSKU, ProductPrice, ProductDescription, picture, datetime.now()))
            dbconnect.commit()
            productcursor.close()
    except:
        pass
    #SavingImages(image_title, image_src, Filepath)


def SavingImages(item_name, item_link, filepath):
    filename = item_name[0].replace('/', '_')
    response = requests.session().get(item_link[0], stream=True)
    if response.status_code == 200:
        try:
            os.chdir(filepath)
        except:
            if not os.path.exists(filepath):
                os.makedirs(filepath)
            os.chdir(filepath)
        with open(filename + '.jpg', 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)


def CreateConnection():
    if not os.path.exists('./EMart/Database'):
        os.makedirs('./EMart/Database')
    # create a new database
    conn = sqlite3.connect('./EMart/Database/EMart.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS Products (ID INTEGER PRIMARY KEY AUTOINCREMENT, ProductName Varchar(100) UNIQUE,ProductGroup Varchar(100), ProductSKU Varchar(100),ProductPrice Varchar(100),ProductDescription Varchar(100),Picture BLOB,CreationDate timestamp)')
    c.execute('CREATE TABLE IF NOT EXISTS ProductGroups(ID INTEGER PRIMARY KEY AUTOINCREMENT, ProductGroup Varchar(100),SubGroup Varchar(100))')
    return conn


MainItems = []
SubItems = []
dbconnect = CreateConnection()
Scraper_InitialPage(dbconnect)
for item in MainItems:
    ItemLinks = []
    Scraper_InnerPage(dbconnect, item['Category'], item['Link'])
for subitem in SubItems:
    Scraper_InnerPage(dbconnect, subitem['Category'],
                      subitem['Link'], subitem['SubCategory'])
