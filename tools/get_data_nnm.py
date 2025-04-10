#!/usr/bin/python3
#
# Util get data from nnm sise for load to DB 
# version 0.5
# load config file
#!!!!!!!! Replace with you config file here !!!!!!!
# replace myconfig with config by example
# --------------------------------

import myconfig as cfg
# --------------------------------

from datetime import datetime, date, time, timezone
from bs4 import BeautifulSoup
from collections import OrderedDict
import requests
import re
import sqlite3
import logging 
import textwrap
import asyncio
import os.path
import sys
import gettext
import io
import time


def get_config(config):
    ''' set global variable from included config.py - import config directive'''
    global api_id
    global api_hash
    global mybot_token
    global system_version
    global session_client
    global session_bot
    global bot_name
    global admin_name
    global Channel_mon
    global Channel_my
    global db_name
    global proxies
    global logfile
    global use_proxy
    global filter
    global ICU_extension_lib
    global log_level
    global Lang
    global magnet_helper

    try:
        api_id = config.api_id
        api_hash = config.api_hash
        mybot_token = config.mybot_token
        system_version = config.system_version
        session_client = config.session_client
        session_bot = config.session_bot
        bot_name = config.bot_name
        admin_name = config.admin_name
        Channel_mon = config.Channel_mon
        Channel_my = config.Channel_my
        db_name = config.db_name
        logfile = config.logfile
        use_proxy = config.use_proxy
        filter = re.compile(config.filter)
        log_level = config.log_level
        Lang = config.Lang
        ICU_extension_lib = config.ICU_extension_lib
        magnet_helper = config.magnet_helper

        if use_proxy:
            proxies = config.proxies
        else:
            proxies = None

    except Exception as error:
        print(f"Error in config file: {error}")
        exit(-1)

def db_init():
    ''' Initialize database '''
    # Load ICU extension in exist for case independet search  in DB
    if os.path.isfile(ICU_extension_lib):
        connection.enable_load_extension(True)
        connection.load_extension(ICU_extension_lib)

    cursor.execute('''PRAGMA foreign_keys = ON''')
    
    #ALTER TABLE Films add COLUMN image_nnm_url TEXT DEFAULT NULL
    
    # Create basic table Films
    # remove: photo BLOB DEFAULT NULL,
    # add: publish INTEGER DEFAULT 0, - Flag no publish/upgrade/not publish - 1/2/0 
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Films (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      id_msg TEXT,
      id_nnm TEXT,
      id_kpsk TEXT,
      id_imdb TEXT,
      nnm_url TEXT,
      name TEXT,
      mag_link TEXT DEFAULT NULL,
      section  TEXT DEFAULT NULL,
      genre  TEXT DEFAULT NULL,
      rating_kpsk TEXT DEFAULT NULL,
      rating_imdb TEXT DEFAULT NULL,
      description TEXT DEFAULT NULL,
      image_nnm_url TEXT NULL,
      publish INTEGER DEFAULT 0,
      date TEXT
      )
      ''')
    # Ctreate table Users
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Users (
      id_user TEXT NOT NULL PRIMARY KEY,
      name_user TEXT NOT NULL,
      date TEXT NOT NULL,
      active INTEGER DEFAULT 0,
      rights INTEGER DEFAULT 0,
      setings TEXT DEFAULT NULL
      )
      ''')
    # Create table Ufilms - films tagged users
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Ufilms (
      ufilms_id INTEGER PRIMARY KEY AUTOINCREMENT,
      id_user TEXT NOT NULL,
      id_Films  TEXT NOT NULL,
      date  TEXT NOT NULL,
      tag INTEGER DEFAULT 0,
      FOREIGN KEY (id_user)
      REFERENCES Users (id_user)
        ON DELETE CASCADE
       )
      ''')
# Create table Ufilms - films tagged users
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Not_exist_films (
      nef_id INTEGER PRIMARY KEY AUTOINCREMENT,
      id_film INTEGER UNIQUE
       )
      ''')
    connection.commit()

def db_mod_film( id, film_magnet_link, film_section, film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url ):
    ''' Add new Film to database '''
    update_statement = "UPDATE Films SET mag_link=?, section=?, genre=?, rating_kpsk=?, rating_imdb=?, description=?, image_nnm_url=? WHERE id=?"
    cursor.execute(update_statement, (film_magnet_link, film_section, film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url, id,))
    connection.commit()

def db_add_not_exist_film(id_film):
    ''' Add to DB Not exist films for deletion from DB '''
    cursor.execute("INSERT OR IGNORE INTO Not_exist_films (id_film) VALUES(?)", (id_film,))
    connection.commit()


def get_film_id_from_DB():
    ''' Get id, nnm_url,id_kpsk, id_imdb from database for parsing site NNM'''
    #cursor.execute('SELECT id, nnm_url, id_nnm, id_kpsk, id_imdb FROM Films WHERE image_nnm_url=1' )
    cursor.execute('SELECT id, nnm_url, id_nnm, id_kpsk, id_imdb FROM Films a1 WHERE image_nnm_url is NULL AND  NOT EXISTS ( SELECT 1 FROM Not_exist_films a2 WHERE a2.id_film = a1.id )')
    rows = cursor.fetchall()
    return rows

def get_data():
    ''' main get data func '''

    # -------------- addition info vars
    Id = ["Название:", "Производство:", "Жанр:", "Режиссер:",
          "Актеры:", "Описание:", "Продолжительность:", "Качество видео:",
          "Перевод:", "Язык озвучки:", "Субтитры:", "Видео:", "Аудио 1:",
          "Аудио 2:", "Аудио 3:", "Скриншоты:", "Время раздачи:"]

    desc_tmpl = re.compile(':$')
    
    # Get all records from DB where not exist image_url
    rows = get_film_id_from_DB()
    ci=0
    rlen = len(rows)
    print(f"ALL RECORDS: {rlen}")

    if rlen == 0: return -1  

    for row in rows:
        ci=ci+1
        print(f"CURRENT RECORD={ci}")
        
        if ci == 10: return 0 # TEST ONLY

        url=dict(row).get("nnm_url")
        id=dict(row).get("id")
        id_kpsk=dict(row).get("id_kpsk")
        mydict = {}
                  
        try:
            page = requests.get(url, proxies=proxies)
            if page.status_code != 200:
                logging.error(f"Can't open url:{url}, status:{page.status_code}")
                print(f"FILM NOT EXIST ON NNM {id}:{url}")
                db_add_not_exist_film(id)
                continue
        except Exception as ConnectionError:
            logging.error(f"Can't open url:{url}, Error:{ConnectionError}")
            logging.error(f"May be you need use proxy? For it set use_proxy=1 in config file.")
            return -2

        logging.debug(f"Getted URL nnmclub page with status code: {page.status_code}")

        soup = BeautifulSoup(page.text, 'html.parser')
        
        # if no acces to film, get login page - class thHead on login page
        if soup.find(class_='thHead'):
           logging.error(f"I think film Transfer to archive:{url}")
           print(f"FILM WAS TRANSFER TO ARCHIVE {id}:{url}")
           db_add_not_exist_film(id) 
           continue
       
        # Select data where class is nav - info about tracker section
        post_body = soup.findAll('a', {'class': 'nav'})        
        section = post_body[-1].get_text('\n', strip='True')
        logging.debug(f"Section nnm tracker: {section}")

        # Select data where class is gensmall - get magnet link
        post_body = soup.find( href=re.compile("magnet:") )
        if post_body:
           mag_link = post_body.get('href')
           logging.debug(f"Magnet link: {mag_link}\n")
        else:
           mag_link = None  

        # Select data where class is postbody
        post_body = soup.find(class_='postbody')
        text = post_body.get_text('\n', strip='True')

        # Get url poster where class postImg 'postImgAligned img-right'
        for a_hr in post_body.find_all(class_='postImg postImgAligned img-right'):
            image_url = a_hr.get('title')
            #<img class="postImg postImgAligned img-right" alt="pic" title="pic" src="https://nnmstatic.win/forum/image.php?link=https://i6.imageban.ru/out/2024/07/12/389682ee7ff2fc08e2faf153742e10ae.jpg">
            #print(f"image_url={image_url}")
        
        k = Id[0]
        v = ""

        # Create Dict for data about Film 
        for line in text.split("\n"):
            #print(f"Line:{line}")
            if not line.strip():
                continue
            else:
                if desc_tmpl.search(line):
                    k = line
                    v = ""
                elif k != "":
                    v = v+line
                    mydict[k] = v

        # Get data about film from kinopoisk over unofficial API 
        if id_kpsk:            
            kp_api_url='https://kinopoiskapiunofficial.tech/api/v2.2/films/'
            kp_api_key='59a0a979-e2f4-4875-b1fe-bae7a57bfa26' 
            try:
                response = requests.get(kp_api_url+str(id_kpsk), headers={'accept': 'application/json', 'X-API-KEY': kp_api_key}) #, proxies=proxies
                if (response.status_code == 401): 
                   print(f"Token Error!")
                   return 401
                if (response.status_code == 402):
                   print(f"Limit over! Need wait in 24h.")
                   return 402        
                if (response.status_code == 404):
                   print(f"No film found!")
                   return 404         
                if (response.status_code == 429):
                   print(f"Too many requests per sec (>20)!")
                   return 429                       
                # Convert json into dictionary 
                response_dict = response.json() 
                #print(f"Status={response.status_code}")
                #print(f"RatingKinopoisk:\n{response_dict.get('ratingKinopoisk')}")
                #print(f"Description:\n{response_dict.get('description')}")
                description=response_dict.get('description')
                kpsk_r=response_dict.get('ratingKinopoisk')
                imdb_r=response_dict.get('ratingImdb')
                genres=response_dict.get('genres')
                glen=len(genres)
                gi=0
                genres_out=""
                for genre in genres:
                    g=genre.get('genre')
                    gi=gi+1
                    if gi == glen:
                        genres_out=genres_out+g  
                        break
                    else:
                      genres_out=genres_out+g+','

                #print(f"Genres_out={genres_out}")
            except Exception as ConnectionError:
                logging.error(f"Can't open url:{url}, Error:{ConnectionError}")
                return -2
        else:
            kpsk_r = "-"
            imdb_r = "-"
            genres_out=mydict.get('Жанр:')
            description=mydict.get('Описание:')

        if mydict.get('Описание:'): description=mydict.get('Описание:') 

        print(f"Update BD record[{id}]:\n {mag_link}\n{section}\n{genres_out}\n{kpsk_r}\n{imdb_r}\n{description}\n{image_url}")
        print(f"\n------------------------------------------------------------------------------------------------------------")
        #db_mod_film( id, mag_link, section, genres_out, kpsk_r, imdb_r, description,image_url )
        # Limit requests to world 1 req in 1sec
        time.sleep(1)

    return 0

# main()
print('Start getting data for films.')

get_config(cfg)

# Enable logging
logging.basicConfig(level=log_level, filename=logfile, filemode="a", format="%(asctime)s %(levelname)s %(message)s")
logging.info(f"Start getting data for films.")

localedir = os.path.join(os.path.dirname(os.path.realpath(os.path.normpath(sys.argv[0]))), 'locales')

if os.path.isdir(localedir):
  translate = gettext.translation('nnmbot', localedir, [Lang])
  _ = translate.gettext
else: 
  logging.info(f"No locale dir for support langs: {localedir} \n Use default lang: Engilsh")
  def _(message): return message
 
#db_lock = asyncio.Lock()

connection = sqlite3.connect(db_name)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

db_init()

ret=get_data()

#while True:
# ret=get_data()
# if ret == -1: 
#    logging.info(f"\nAll done. No records for processin.\n--------------------------")
#    break
# elif ret == -2
#    logging.info(f"\nConnection error. Check Network.\n--------------------------")
#    break
# elif ret == 0:
#    logging.info(f"\nAll done. But yet one\n--------------------------")
# elif ret == 402:
#    logging.info(f"\nLimit API 400 requests in 24h - sleen 24h.\n--------------------------")
#    time.sleep(60*60*24)
# elif ret == 429:
#    logging.info(f"\nLimit API per second sleen 1m.\n--------------------------")
#    time.sleep(60)
# else:
#     logging.info(f"\nError:{ret}\n--------------------------")

 
 
connection.close()
logging.info(f"End.\n--------------------------")
print('End.')
