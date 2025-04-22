
# Telegram Bot for filter films from NNMCLUB channel
# version 0.5
# Module backend_nnmbot.py listen NNMCLUB channel,
# filter films and write to database
#

import io
import re
import sqlite3
import logging
import asyncio
import os.path
import sys
import gettext
import requests
from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel, MessageEntityUrl
from telethon.sessions import StringSession
from bs4 import BeautifulSoup
#from requests.adapters import HTTPAdapter
#from urllib3.util import Retry
# --------------------------------
import settings as sts
import dbmodule_nnmbot as dbm
# --------------------------------

async def get_image(msg): #TODO NO NEED I think
    '''Get image poster form message'''
    # get photo from nnm message and create my photo

    film_photo = await client.download_media(msg, bytes)
    film_photo_d = film_photo
    file_photo = io.BytesIO(film_photo_d)
    file_photo.name = "image.jpg" 
    file_photo.seek(0)  # set cursor to the beginning
    logging.debug(f"Message Photo{film_photo_d}")

    return { 'image_nnm': file_photo, 'image_msg': film_photo}

def get_film_id( soup ):
    ''' Get Kinopoisk id of Film'''
    
     # Select data where class - postbody
    post_body = soup.find(class_='postbody')
    f_tmpl = re.compile('film/(.+?)/')
    t_tmpl = re.compile('title/(.+?)/')
    id_kpsk = None
    id_imdb = None
    for a_hr in post_body.find_all('a'):
        rat = a_hr.get('href')
        if not rat:
            return None
        if rat.find('https://www.kinopoisk.ru/film/') != -1:
            id_kpsk = f_tmpl.search(rat).group(1)
            logging.info(f"Get film id on kinopoisk: {id_kpsk}")
        elif rat.find('https://www.imdb.com/title/') != -1:
            id_imdb = t_tmpl.search(rat).group(1)
            logging.info(f"Get film id on imdb: {id_imdb}")

    return { 'id_kpsk':id_kpsk,'id_imdb':id_imdb  }

def get_ukp_film_info( id_kpsk ):
    ''' Get film info from unofficial kinopoisk api'''

    if not sts.ukp_api_key or not sts.ukp_api_url:
        return None

    try:
        response = requests.get(sts.ukp_api_url+str(id_kpsk), timeout=30, headers={'accept': 'application/json', 'X-API-KEY': sts.ukp_api_key}, proxies=sts.proxies)
        if response.status_code == 401: 
            logging.info(f"Resposse status={response.status_code}:Token Error!")
            return None
        if response.status_code == 402:
            logging.info(f"Resposse status={response.status_code}:Limit over! Need wait in 24h.")
            return None        
        if response.status_code == 404:
            logging.info(f"Resposse status={response.status_code}:No film found!")
            return None        
        if response.status_code == 429:
            logging.info(f"Resposse status={response.status_code}:Too many requests per sec (>20)!")
            return None                      
        # Convert json into dictionary 
        response_dict = response.json()
        film_name=response_dict.get('nameRu')
        description=response_dict.get('description')
        kpsk_r=response_dict.get('ratingKinopoisk')
        kpsk_r_vk=response_dict.get('ratingKinopoiskVoteCount')
        imdb_r=response_dict.get('ratingImdb')
        imdb_r_vk=response_dict.get('ratingImdbVoteCount')
        image_nnm_url=response_dict.get('posterUrlPreview')
        genres=response_dict.get('genres')
        genre=''
        for gen in genres:
            genre=genre+gen.get('genre')+','
        genre=genre[:-1]

    except Exception as error:
        logging.error(f"Can't open url:{sts.ukp_api_url}")
        return None

    return { 'film_name':film_name,
            'description':description, 
            'kpsk_r':kpsk_r, 
            'kpsk_r_vk':kpsk_r_vk, 
            'imdb_r':imdb_r, 
            'imdb_r_vk':imdb_r_vk, 
            'image_nnm_url':image_nnm_url,
            'genres':genre }        

def get_rating_kp_imdb(id_kpsk, id_imdb):
    '''Get raiting film from kinopoisk site or immdb site'''
    
    kpsk_url = 'https://rating.kinopoisk.ru/'+id_kpsk+'.xml'
    if id_imdb: 
        imdb_url = 'https://www.imdb.com/title/'+id_imdb+'/ratings/?ref_=tt_ov_rt'
    else: 
        imdb_url = None
    kpsk_r=None
    imdb_r=None
    # Get rating film from kinopoisk if not then from imdb site

    page = requests.get(kpsk_url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'}, proxies=sts.proxies)
    # Parse data
    # FIXME: me be better use xml.parser ?
    soup = BeautifulSoup(page.text, 'html.parser')
    try:
        rating_xml = soup.find('rating')
        kpsk_r = rating_xml.find('kp_rating').get_text('\n', strip='True')
        imdb_r = rating_xml.find('imdb_rating').get_text('\n', strip='True')
        logging.info(f"Get rating from kinopoisk: {kpsk_url}")
    except Exception as error:
        logging.info(f"No kinopoisk rating on site:{error}")

    if not imdb_r and id_imdb:
        page = requests.get(imdb_url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'}, proxies=sts.proxies)
        # Parse data
        soup = BeautifulSoup(page.text, 'html.parser')
        post_body = soup.find(class_='sc-5931bdee-1 gVydpF')
        if post_body:
            imdb_r = post_body.get_text('\n', strip='True')
            logging.info(f"Get rating from imdb: {imdb_url}")
    
    return { 'kpsk_r':kpsk_r,'imdb_r':imdb_r  }

async def main_backend():
    ''' Loop for client connection '''

    # -------------- addition info vars
    fileds_name = ["Название:", "Производство:", "Жанр:", "Режиссер:",
          "Актеры:", "Описание:", "Продолжительность:", "Качество видео:",
          "Перевод:", "Язык озвучки:", "Субтитры:", "Видео:", "Аудио 1:",
          "Аудио 2:", "Аудио 3:", "Скриншоты:", "Время раздачи:"]

    
    channel_mon_id = await client.get_peer_id(sts.Channel_mon)
    # Parse channel NNMCLUB for Films

    @client.on(events.NewMessage(chats=[PeerChannel(channel_mon_id)], pattern=sts.pattern_filter))
    async def normal_handler(event):
        url = post_body  = []
        mydict = {}
        image_nnm_url = None
        kpsk_r = None
        imdb_r = None

        logging.debug(f"Get new message in NNMCLUB Channel: {event.message}")
        msg = event.message

        # Get URL of nnmclub film page
        url_tmpl = re.compile(r'viewtopic.php\?t')
        for url_entity, inner_text in msg.get_entities_text(MessageEntityUrl):
            logging.debug(f"Urls: {url_entity, inner_text}")
            if url_tmpl.search(inner_text):
                url = inner_text
        logging.info(f"Try Get URL nnmclub page with Film: {url}")

        # if URL not exist return
        if not url:
            logging.info(f"Cannot get URL nnmclub page with Film: {url}")
            return

        try:
            # Configure session requests
            #ses = requests.Session()

            # Set retry strategy
            #retries = Retry(total=5,
            #    backoff_factor=0.1,
            #    status_forcelist=[500, 502, 503, 504],
            #    allowed_methods=frozenset(['GET', 'POST']))

            # Link strategy with session
            #ses.mount('http://', HTTPAdapter(max_retries=retries))
            #ses.mount('https://', HTTPAdapter(max_retries=retries))

            # Get html page film
            page = requests.get(url, timeout=30, proxies=sts.proxies)
            if page.status_code != 200:
                logging.error(f"Can't open url:{url}, status:{page.status_code}")
                return
        except requests.Timeout as e:
            logging.error(f"Timeout Error: Can't open url:{url}, status:{e}")
            return
        except requests.ConnectionError as e:
            logging.error(f"Max retries exceeded Error: Can't open url:{url}, status:{e}")
            logging.error("May be you need use proxy? For it set use_proxy=1 in config file.")
            return
        except requests.RequestException as e:
            logging.error(f"General Error: Can't open url:{url}, status:{e}")
            logging.error("May be you need use proxy? For it set use_proxy=1 in config file.")
            client.disconnect()
            return

        logging.debug(f"Getted URL nnmclub page with status code: {page.status_code}")
        soup = BeautifulSoup(page.text, 'html.parser')

        film_ids=get_film_id(soup)
        
        if not film_ids:
            logging.info(f"No info for film (possible in archive): {url}")
            return

        id_kpsk=film_ids.get('id_kpsk')
        id_imdb=film_ids.get('id_imdb')
        id_nnm = re.search('viewtopic.php.t=(.+?)$', url).group(1)
        
        # Get film info from unofficial kinopoisk API 
        ukp_info=get_ukp_film_info(id_kpsk)
        if ukp_info:
            image_nnm_url=ukp_info.get('image_nnm_url')
            film_name=ukp_info.get('film_name')
            description=ukp_info.get('description')
            kpsk_r=ukp_info.get('kpsk_r')
            imdb_r=ukp_info.get('imdb_r')
            genres=ukp_info.get('genres')

        # Select data where class - nav - info about tracker section
        post_body = soup.find_all('a', {'class': 'nav'}) 
        section = post_body[-1].get_text('\n', strip='True')
        logging.debug(f"Section nnm tracker: {section}")

        # Select data where class - gensmall - get magnet link
        post_body = soup.find( href=re.compile("magnet:") )
        if post_body:
            mag_link = post_body.get('href')
            logging.debug(f"Magnet link: {mag_link}\n")
        else:
            mag_link = None

        # Select data where class - postbody
        post_body = soup.find(class_='postbody')
        
        #Get poster url
        if not image_nnm_url:
            for a_hr in post_body.find_all(class_='postImg postImgAligned img-right'):
                image_nnm_url = a_hr.get('title')
            logging.info(f"Get image url from nnmblub: {image_nnm_url}")

        if not kpsk_r and not imdb_r:
            rating=get_rating_kp_imdb(id_kpsk, id_imdb)
            kpsk_r=rating.get('kpsk_r')
            imdb_r=rating.get('imdb_r')

        k = fileds_name[0]
        v = ''

        # Create Dict for data about Film
        text = post_body.get_text('\n', strip='True')
        desc_tmpl = re.compile(':$')
    
        for line in text.split("\n"):
            if line := line.strip():
                if desc_tmpl.search(line):
                    k=line
                    v=''
                elif k:
                    v=v+line
                    mydict[k]=v
        
        #if not film_name:
        #    film_name=mydict[fileds_name[0]]

        # Alwais select film name from nnmclub
        film_name=mydict[fileds_name[0]]

        if not description:
            description=mydict[fileds_name[5]]
        if not kpsk_r:
            kpsk_r='-'
        if not imdb_r:
            imdb_r='-'
        if not genres:
            genres=mydict.get(fileds_name[2])

        image_msg = await client.download_media(msg, bytes)
       
        try:
            async with db_lock:
                rec_id=dbm.db_exist_Id(id_kpsk, id_imdb)
                if rec_id:
                    rec_id=dict(rec_id).get("id")
                    # Update exist film to DB 🔄
                    dbm.db_update_film(rec_id, id_nnm, url, film_name, \
                        id_kpsk, id_imdb, mag_link, section, genres, kpsk_r, imdb_r, \
                        description, image_nnm_url, image_msg, sts.PUBL_UPD)
                    #rec_upd='UPD'
                    logging.info(f"Dublicate in DB: Film id={rec_id} id_nnm={id_nnm} exist in db - update to new release.")
                else:
                    # Add new film to DB
                    rec_id=dbm.db_add_film(id_nnm, url, film_name, id_kpsk, id_imdb, mag_link, section, \
                        genres, kpsk_r, imdb_r, description, image_nnm_url, image_msg, sts.PUBL_NOT)
                    logging.info(f"Film not exist in db - add and send id={rec_id}, name={film_name} id_kpsk={id_kpsk} id_imdb={id_imdb} id_nnm:{id_nnm}\n")
            try:
                # Send inline query message to frondend bot for publish Film
                result = await client.inline_query(sts.bot_name,"PUBLISH#"+str(rec_id))
                logging.debug(f"Send inline_query:{result}")
            except Exception as error:
                logging.warning(f'Cant send inline_query to bot. Ignore this because frondend not running:\n {error}')
        except Exception as error:
            logging.error(f'Error in block db_lock: {error}') 
    
    return client


# main()
print('Start backend.')

sts.get_config()

# Enable logging
logging.basicConfig(level=sts.log_level, filename="backend_"+sts.logfile, filemode="a", format="%(asctime)s %(levelname)s %(message)s")
logging.info("--------------------------------------\nStart backend bot.")

localedir = os.path.join(os.path.dirname(os.path.realpath(os.path.normpath(sys.argv[0]))), 'locales')

if os.path.isdir(localedir):
    translate = gettext.translation('nnmbot', localedir, [sts.Lang])
    _ = translate.gettext
else:
    logging.info(f"No locale dir for support langs: {localedir} \n Use default lang: Engilsh")
    def _(message):
        return message

db_lock = asyncio.Lock()
sts.connection = sqlite3.connect(sts.db_name, timeout=10)
sts.connection.row_factory = sqlite3.Row
sts.cursor = sts.connection.cursor()

# Init database
dbm.db_init()
dbm.db_create()

# Connect to Telegram as user
if sts.use_proxy:
    prx = re.search('(^.*)://(.*):(.*$)', sts.proxies.get('http'))
    proxy = (prx.group(1), prx.group(2), int(prx.group(3)))
else:
    proxy = None

# Set type session: file or env string
if not sts.ses_usr_str:
    session=sts.session_client
    logging.info("Use File session mode")
else:
    session=StringSession(sts.ses_usr_str)
    logging.info("Use String session mode")

# Init and start Telegram client as bot
client = TelegramClient(session, sts.api_id, sts.api_hash, system_version=sts.system_version, proxy=proxy)

client.start()
client.loop.run_until_complete(main_backend())
client.run_until_disconnected()

sts.connection.close()
logging.info("End backend.\n--------------------------")
print('End.')
