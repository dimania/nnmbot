
# Telegram Bot for filter films from NNMCLUB channel
# version 0.5
# Module backend_nnmbot.py listen NNMCLUB channel,
# filter films and write to database
#

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
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
# --------------------------------
import settings as sts
import dbmodule_nnmbot as dbm
# --------------------------------

async def main_backend():
    ''' Loop for client connection '''

    # -------------- addition info vars
    fileds_name = ["Название:", "Производство:", "Жанр:", "Режиссер:",
          "Актеры:", "Описание:", "Продолжительность:", "Качество видео:",
          "Перевод:", "Язык озвучки:", "Субтитры:", "Видео:", "Аудио 1:",
          "Аудио 2:", "Аудио 3:", "Скриншоты:", "Время раздачи:"]

    f_tmpl = re.compile('film/(.+?)/')
    t_tmpl = re.compile('title/(.+?)/')
    url_tmpl = re.compile(r'viewtopic.php\?t')
    desc_tmpl = re.compile(':$')

    channel_mon_id = await client.get_peer_id(sts.Channel_mon)
    # Parse channel NNMCLUB for Films

    @client.on(events.NewMessage(chats=[PeerChannel(channel_mon_id)], pattern=sts.pattern_filter))
    async def normal_handler(event):
        url = post_body  = []
        mydict = {}
        logging.debug(f"Get new message in NNMCLUB Channel: {event.message}")
        msg = event.message

        for url_entity, inner_text in msg.get_entities_text(MessageEntityUrl):
            logging.debug(f"Urls: {url_entity, inner_text}")
            if url_tmpl.search(inner_text):
                url = inner_text
        logging.info(f"Get URL nnmclub page with Film: {url}")

        # if URL not exist return
        if not url:
            return

        try:
            # Конфигурируем сессию requests
            ses = requests.Session()

            # Устанавливаем стратегию повторных попыток
            retries = Retry(total=5,
                backoff_factor=0.1,
                status_forcelist=[500, 502, 503, 504],
                allowed_methods=frozenset(['GET', 'POST']))

            # Связываем стратегию с сессией requests
            ses.mount('http://', HTTPAdapter(max_retries=retries))
            ses.mount('https://', HTTPAdapter(max_retries=retries))

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

        # Select data where class - nav - info about tracker section
        post_body = soup.findAll('a', {'class': 'nav'})
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
        text = post_body.get_text('\n', strip='True')

        #Get poster url
        for a_hr in post_body.find_all(class_='postImg postImgAligned img-right'):
            image_nnm_url = a_hr.get('title')
        logging.info(f"Get image url from nnmblub: {image_nnm_url}")

        k = fileds_name[0]
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
        id_kpsk = id_imdb = id_nnm = 0

        # Get rating urls and id film on kinopoisk and iddb
        for a_hr in post_body.find_all('a'):
            rat = a_hr.get('href')
            if rat.find('https://www.kinopoisk.ru/film/') != -1:
                id_kpsk = f_tmpl.search(rat).group(1)
                kpsk_url = 'https://rating.kinopoisk.ru/'+id_kpsk+'.xml'
                logging.info(f"Create url rating from kinopoisk: {kpsk_url}")
            elif rat.find('https://www.imdb.com/title/') != -1:
                id_imdb = t_tmpl.search(rat).group(1)
                imdb_url = rat.replace('?ref_=plg_rt_1', 'ratings/?ref_=tt_ov_rt')
                logging.info(f"Create url rating from imdb: {imdb_url}")

        id_nnm = re.search('viewtopic.php.t=(.+?)$', url).group(1)

        # Get rating film from kinopoisk if not then from imdb site
        if kpsk_url:
            rat_url = kpsk_url
            page = requests.get(rat_url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'}, proxies=sts.proxies)
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
        elif imdb_url:
            rat_url = imdb_url
            page = requests.get(rat_url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'}, proxies=sts.proxies)
            # Parse data
            soup = BeautifulSoup(page.text, 'html.parser')
            post_body = soup.find(class_='sc-5931bdee-1 gVydpF')
            if post_body:
                imdb_r = post_body.get_text('\n', strip='True')
                logging.info(f"Get rating from imdb: {imdb_url}")
            else:
                imdb_r = "-"
        else:
            kpsk_r = "-"
            imdb_r = "-"

        rec_upd = ""
        try:
            async with db_lock:
                rec_id=dbm.db_exist_Id(id_kpsk, id_imdb)
                if rec_id:
                    rec_id=dict(rec_id).get("id")
                    # Update exist film to DB 🔄
                    dbm.db_update_film(rec_id, id_nnm, url, mydict[fileds_name[0]], \
                        id_kpsk, id_imdb, mag_link, section, mydict.get(fileds_name[2]), kpsk_r, imdb_r, \
                            mydict.get(fileds_name[5]), image_nnm_url, sts.PUBL_UPD)
                    rec_upd='UPD'
                    logging.info(f"Dublicate in DB: Film id={rec_id} id_nnm={id_nnm} exist in db - update to new release.")
                else:
                    # Add new film to DB
                    rec_id=dbm.db_add_film(id_nnm, url, mydict[fileds_name[0]], id_kpsk, id_imdb, mag_link, section, \
                        mydict.get(fileds_name[2]), kpsk_r, imdb_r, mydict.get(fileds_name[5]), image_nnm_url, sts.PUBL_NOT)
                    logging.info(f"Film not exist in db - add and send id={rec_id}, name={mydict[fileds_name[0]]} id_kpsk={id_kpsk} id_imdb={id_imdb} id_nnm:{id_nnm}\n")
            # Send message to frondend bot for publish Film
            #send_msg = await client.send_message(sts.bot_name,rec_upd+"PUBLISH#"+str(rec_id))
            #logging.debug(f"Send Message:{send_msg}")
            try:
                # Send inline query message to frondend bot for publish Film
                result = await client.inline_query(sts.bot_name,rec_upd+"PUBLISH#"+str(rec_id))
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
logging.info("Start backend bot.")

localedir = os.path.join(os.path.dirname(os.path.realpath(os.path.normpath(sys.argv[0]))), 'locales')

if os.path.isdir(localedir):
    translate = gettext.translation('nnmbot', localedir, [sts.Lang])
    _ = translate.gettext
else:
    logging.info(f"No locale dir for support langs: {localedir} \n Use default lang: Engilsh")
    def _(message):
        return message

db_lock = asyncio.Lock()
sts.connection = sqlite3.connect(sts.db_name)
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

string=client.session.save()
print(f"String session for user:\n{string}")

client.start()
client.loop.run_until_complete(main_backend())
client.run_until_disconnected()

sts.connection.close()
logging.info("End backend.\n--------------------------")
print('End.')
