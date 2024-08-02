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
      photo BLOB DEFAULT NULL,
      image_nnm_url TEXT NULL,
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
      id_film INTEGER
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
    cursor.execute("INSERT INTO Not_exist_films (id_film) VALUES(?)", (id_film,))
    connection.commit()


def get_film_id_from_DB():
    ''' Get id, nnm_url,id_kpsk, id_imdb from database for parsing site NNM'''
    cursor.execute('SELECT id, nnm_url, id_nnm, id_kpsk, id_imdb FROM Films WHERE image_nnm_url IS NULL' )
    rows = cursor.fetchall()
    return rows

def get_data():
    ''' main get data func '''

    # -------------- addition info vars
    Id = ["Название:", "Производство:", "Жанр:", "Режиссер:",
          "Актеры:", "Описание:", "Продолжительность:", "Качество видео:",
          "Перевод:", "Язык озвучки:", "Субтитры:", "Видео:", "Аудио 1:",
          "Аудио 2:", "Аудио 3:", "Скриншоты:", "Время раздачи:"]

    f_tmpl = re.compile('film/(.+?)/')
    t_tmpl = re.compile('title/(.+?)/')
    url_tmpl = re.compile(r'viewtopic.php\?t')
    kpr_tmpl = re.compile('www.kinopoisk.ru/rating')
    desc_tmpl = re.compile(':$')

    rows = get_film_id_from_DB()
    i=0
    print(f"ALL RECORDS: {len(rows)}")
    #for rec in rows:
    #    print(f"rec:{dict(rec).get("nnm_url")}")

    for row in rows:
        i=i+1
        print(f"CURRENT RECORD={i}")
        if i == 100: 
            return 
        url=dict(row).get("nnm_url")
        id=dict(row).get("id")
        id_kpsk=dict(row).get("id_kpsk")
        id_imdb=dict(row).get("id_imdb")
        
        #url = post_body = rating_url = []
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
            return

        logging.debug(f"Getted URL nnmclub page with status code: {page.status_code}")

        soup = BeautifulSoup(page.text, 'html.parser')
        
        if not soup.find(class_='thHead'):
           logging.error(f"I think film Transfer to archive:{url}")
           print(f"FILM WAS TRANSFER TO ARCHIVE {id}:{url}")
           db_add_not_exist_film(id) 
           continue
        
        # Select data where class - gensmall - get magnet link
        post_body = soup.find( href=re.compile("magnet:") )
        if post_body:
           mag_link = post_body.get('href')
           logging.debug(f"Magnet link: {mag_link}\n")
        else:
           mag_link = None  

        # Select data where class - postbody
        post_body = soup.find(class_='postbody')
        text = post_body.get_text('\n', strip='True')

        # Select data where class - nav - info about tracker section
        post_body = soup.findAll('a', {'class': 'nav'})        
        section = post_body[-1].get_text('\n', strip='True')
        logging.debug(f"Section nnm tracker: {section}")

        # Get url picture with rating Film on Kinopoisk site
        for a_hr in post_body.find_all(class_='postImg'):
            print(f"a_hr={a_hr}")
            rat = a_hr.get('title')
            if kpr_tmpl.search(rat):
                rating_url = rat
        
        for a_hr in post_body.find_all(class_='postImg postImgAligned img-right'):
            image_url = a_hr.get('title')
            #<img class="postImg postImgAligned img-right" alt="pic" title="pic" src="https://nnmstatic.win/forum/image.php?link=https://i6.imageban.ru/out/2024/07/12/389682ee7ff2fc08e2faf153742e10ae.jpg">
            print(f"image_url={image_url}")
        
        # Select data where class - nav - info about tracker section
        post_body = soup.findAll('a', {'class': 'nav'})        
        section = post_body[-1].get_text('\n', strip='True')
        logging.debug(f"Section nnm tracker: {section}")
        
        k = Id[0]
        v = ""
        
        # Create Dict for data about Film
        for line in text.split("\n"):
            if not line.strip():
                continue
            else:
                if desc_tmpl.search(line):
                    k = line
                    v = ""
                elif k != "":
                    v = v+line
                    mydict[k] = v

        kpsk_r = imdb_r = "-"
        kpsk_url = imdb_url = rat_url = ""
        #id_kpsk = id_imdb = id_nnm = 0

        # Get rating urls and id film on kinopoisk and iddb
        for a_hr in post_body.find_all('a'):
            print(f"a_hr={a_hr}")
            rat = a_hr.get('href')
            if not rat:
                continue
            if rat.find('https://www.kinopoisk.ru/film/') != -1:
                id_kpsk = f_tmpl.search(rat).group(1)
                kpsk_url = 'https://rating.kinopoisk.ru/'+id_kpsk+'.xml'
                logging.info(f"Create url rating from kinopoisk: {kpsk_url}")
            elif rat.find('https://www.imdb.com/title/') != -1:
                id_imdb = t_tmpl.search(rat).group(1)
                imdb_url = rat.replace('?ref_=plg_rt_1', 'ratings/?ref_=tt_ov_rt')
                logging.info(f"Create url rating from imdb: {imdb_url}")
            
        exit(0)   
        id_nnm = re.search('viewtopic.php.t=(.+?)$', url).group(1)

               # Get rating film from kinopoisk if not then from imdb site
        if kpsk_url:
            rat_url = kpsk_url
            page = requests.get(rat_url, headers={'User-Agent': 'Mozilla/5.0'}, proxies=proxies)
            # Parse data
            # FIXME me be better use xml.parser ?
            soup = BeautifulSoup(page.text, 'html.parser')
            try:
                rating_xml = soup.find('rating')
                kpsk_r = rating_xml.find('kp_rating').get_text('\n', strip='True')
                imdb_r = rating_xml.find('imdb_rating').get_text('\n', strip='True')
                logging.info(f"Get rating from kinopoisk: {kpsk_url}")
            except:
                logging.info(f"No kinopoisk rating on site")
        elif imdb_url:
            rat_url = imdb_url
            page = requests.get(rat_url, headers={'User-Agent': 'Mozilla/5.0'}, proxies=proxies)
            soup = BeautifulSoup(page.text, 'html.parser')
            #post_body = soup.find(class_='sc-5931bdee-1 gVydpF') #WAS:<span class="sc-40b53d-1 kJANdR">5.2</span>
            post_body = soup.find(class_='sc-40b53d-1 kJANdR')
            imdb_r = post_body.get_text('\n', strip='True')
            logging.info(f"Get rating from imdb: {imdb_url}")
        else:
            kpsk_r = "-"
            imdb_r = "-"


        logging.info(f"Add info to message")
        film_name = f"<a href='{url}'>{mydict.get(Id[0])}</a>\n"
        film_section = f"🟢<b>Раздел:</b> {section}\n"
        film_genre = f"🟢<b>Жанр:</b> {mydict.get(Id[2])}\n"
        film_rating = f"🟢<b>Рейтинг:</b> КП[{kpsk_r}] Imdb[{imdb_r}]\n"
        film_description = f"🟢<b>Описание:</b> \n{mydict.get(Id[5])}\n"
        # if magnet link exist create string and href link
        if mag_link:
           film_magnet_link = f"<a href='{magnet_helper+mag_link}'>🧲Примагнититься</a>\n" 
        else:
           film_magnet_link=""
        # get photo from nnm message and create my photo
        #film_photo = client.download_media(msg, bytes) #HERE
        #film_photo_d = film_photo
        #file_photo = io.BytesIO(film_photo_d)
        #file_photo.name = "image.jpg" 
        #file_photo.seek(0)  # set cursor to the beginning
        #logging.debug(f"Message Photo{film_photo_d}")
        #film_photo=NULL
        print(f"Add record:\n {mag_link}\n{section}\n{mydict.get(Id[2])}\n{kpsk_r}\n{imdb_r}\n{mydict.get(Id[5])}\n{image_url}")
        db_mod_film( id, mag_link, section, mydict.get(Id[2]), kpsk_r, imdb_r, mydict.get(Id[5]),image_url )
        #new_message = f"{film_name}{film_magnet_link}{film_section}{film_genre}{film_rating}{film_description}{image_url}"
        #print(f"\n-------------\n{new_message}\n")

    #return 0

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
get_data()
connection.close()
logging.info(f"End.\n--------------------------")
print('End.')
