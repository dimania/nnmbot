
#!/usr/bin/python3
#
# Telegram Bot for filter films from NNMCLUB channel
# version 0.5
# Module backend_nnmbot.py listen NNMCLUB channel,
# filter films and write to database 
#
#
# --------------------------------
import settings as sts
import dbmodule_nnmbot as dbm
# --------------------------------

from telethon import TelegramClient, events, utils
from telethon.tl.types import PeerChat, PeerChannel, PeerUser, MessageEntityTextUrl, MessageEntityUrl
from telethon.tl.custom import Button
from telethon import errors
from telethon.errors import MessageNotModifiedError 
from telethon.events import StopPropagation
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




def main_client():
    ''' Loop for client connection '''

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

    # Connect to Telegram
    if sts.use_proxy:
        prx = re.search('(^.*)://(.*):(.*$)', sts.proxies.get('http'))
        client = TelegramClient(sts.session_client, sts.api_id, sts.api_hash, system_version=sts.system_version, proxy=(
            prx.group(1), prx.group(2), int(prx.group(3)))).start(bot_token=sts.mybot_token)
    else:
        client = TelegramClient(sts.session_client, sts.api_id, sts.api_hash, system_version=sts.system_version).start(bot_token=sts.mybot_token)

    client.start()
    Channel_my_id = client.loop.run_until_complete(client.get_peer_id(sts.Channel_my))
    Channel_mon_id = client.loop.run_until_complete(client.get_peer_id(sts.Channel_mon))

    # Parse channel NNMCLUB for Films

    @client.on(events.NewMessage(chats=[PeerChannel(Channel_mon_id)], pattern=sts.filter))
    async def normal_handler(event):
        url = post_body = rating_url =  image_url = []
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
            page = requests.get(url, proxies=sts.proxies)
            if page.status_code != 200:
                logging.error(f"Can't open url:{url}, status:{page.status_code}")
                return
        except Exception as ConnectionError:
            logging.error(f"Can't open url:{url}, status:{ConnectionError}")
            logging.error(f"May be you need use proxy? For it set use_proxy=1 in config file.")
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

        # Get url picture with rating Film on Kinopoisk site
        for a_hr in post_body.find_all(class_='postImg'):
            rat = a_hr.get('title')
            if kpr_tmpl.search(rat):
                rating_url = rat
        #Get poster url
        for a_hr in post_body.find_all(class_='postImg postImgAligned img-right'):
            image_nnm_url = a_hr.get('title')
        logging.info(f"Get image url fron nnmblub: {image_nnm_url}")

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

        # Comment becouse now if film exist in DB, it to be update to new release from NNM
        #if dbm.db_exist_Id(id_kpsk, id_imdb):
        #    logging.info(f"Film id_kpsk={id_kpsk} id_imdb={id_imdb} id_nnm={id_nnm} exist in db - end analize.")
        #    return

        # Get rating film from kinopoisk if not then from imdb site
        if kpsk_url:
            rat_url = kpsk_url
            page = requests.get(rat_url, headers={'User-Agent': 'Mozilla/5.0'}, proxies=sts.proxies)
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
            page = requests.get(rat_url, headers={'User-Agent': 'Mozilla/5.0'}, proxies=sts.proxies)
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

        logging.info(f"Add info to message")
        film_name = f"<a href='{url}'>{mydict.get(Id[0])}</a>\n"
        film_section = f"🟢<b>Раздел:</b> {section}\n"
        film_genre = f"🟢<b>Жанр:</b> {mydict.get(Id[2])}\n"
        film_rating = f"🟢<b>Рейтинг:</b> КП[{kpsk_r}] Imdb[{imdb_r}]\n"
        film_description = f"🟢<b>Описание:</b> \n{mydict.get(Id[5])}\n"
        # if magnet link exist create string and href link
        #--------------------
        # DISBLE magnet link
        mag_link = None
        #--------------------
        if mag_link:
           film_magnet_link = f"<a href='{sts.magnet_helper+mag_link}'>🧲Примагнититься</a>\n" 
        else:
           film_magnet_link=""
        # Create buttons for message
        bdata = 'XX'+id_nnm
        buttons_film = [
                Button.inline(_("Add Film"), bdata),
                Button.url(_("Control"), 't.me/'+sts.bot_name+'?start')
                ]

        # get photo from nnm message and create my photo
        #film_photo = await client.download_media(msg, bytes)
        #film_photo_d = film_photo
        #file_photo = io.BytesIO(film_photo_d)
        #file_photo.name = "image.jpg" 
        #file_photo.seek(0)  # set cursor to the beginning
        #logging.debug(f"Message Photo:\n{film_photo_d}")
        
        # Create new message 
        new_message = f"{film_name}{film_magnet_link}{film_section}{film_genre}{film_rating}{film_description}"
        logging.debug(f"New message:{new_message}")
        
        #trim long message ( telegramm support only 1024 byte caption )
        if len(new_message) > 1023:
            new_message = new_message[:1019]+'...'

        try:
            async with db_lock:
                rec_id=dbm.db_exist_Id(id_kpsk, id_imdb)
                if rec_id:
                    # Update exist film to DB 🔄
                    new_message = f"🔄{new_message}"
                    dbm.db_update_film(dict(rec_id).get("id"), id_nnm, url, mydict[Id[0]], \
                        id_kpsk, id_imdb, mag_link, section, mydict.get(Id[2]), kpsk_r, imdb_r, \
                            mydict.get(Id[5]), image_nnm_url, sts.PUBL_UPD)

                    logging.info(f"Dublicate in DB: Film id={dict(rec_id).get("id")} id_nnm={id_nnm} exist in db - update to new release.")
                else:
                    # Add new film to DB                     
                    dbm.db_add_film(id_nnm, url, mydict[Id[0]], id_kpsk, id_imdb, mag_link, section, \
                        mydict.get(Id[2]), kpsk_r, imdb_r, mydict.get(Id[5]), image_nnm_url, sts.PUBL_NOT)
                    logging.info(f"Film not exist in db - add and send, name={mydict[Id[0]]} id_kpsk={id_kpsk} id_imdb={id_imdb} id_nnm:{id_nnm}\n")

            # Send message to Telegramm channel    
            send_msg = await client.send_file(PeerChannel(Channel_my_id), image_nnm_url, caption=new_message, \
                buttons=buttons_film, parse_mode="html" )

            logging.debug(f"Send Message:{send_msg}")
        except Exception as error:
            logging.error(f'Error in block db_lock: {error}')
        
    return client


# main()
print('Start backend.')

sts.get_config()

# Enable logging
logging.basicConfig(level=sts.log_level, filename="backend_"+sts.logfile, filemode="a", format="%(asctime)s %(levelname)s %(message)s")
logging.info(f"Start backend bot.")

localedir = os.path.join(os.path.dirname(os.path.realpath(os.path.normpath(sys.argv[0]))), 'locales')

if os.path.isdir(localedir):
  translate = gettext.translation('nnmbot', localedir, [sts.Lang])
  _ = translate.gettext
else: 
  logging.info(f"No locale dir for support langs: {sts.localedir} \n Use default lang: Engilsh")
  def _(message): return message
 
db_lock = asyncio.Lock()
sts.connection = sqlite3.connect(sts.db_name)
sts.connection.row_factory = sqlite3.Row
sts.cursor = sts.connection.cursor()

dbm.db_init()

client = main_client()
client.run_until_disconnected()

sts.connection.close()
logging.info(f"End.\n--------------------------")
print('End.')