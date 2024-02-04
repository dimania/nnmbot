#!/usr/bin/python3
#
#Telegram Bot for filter films from NNMCLUB channel
#

from telethon import TelegramClient, sync, events
from telethon.tl.types import PeerChat, PeerChannel, MessageEntityTextUrl 
from datetime import datetime, date, time, timezone
from bs4 import BeautifulSoup
import requests
import re
import sqlite3

#---------------- basic vars --------
api_id = <YOUR API ID>
api_hash = <YOU API HASH>
system_version = "0.2-nnmbot"

channelId = -1001776763737 # channel what monitor
chat_my =   <-1008769769990> # You channel  where send

db_name = 'my_database.db'

proxies = {
  "http": "socks5://127.0.0.1:1080",
  "https": "socks5://127.0.0.1:1080",
}

#-------------- addition info vars
Id=["Название:", "Производство:", "Жанр:", "Режиссер:",
    "Актеры:", "Описание:", "Продолжительность:", "Качество видео:",
    "Перевод:","Язык озвучки:", "Субтитры:", "Видео:", "Аудио 1:",
    "Аудио 2:", "Аудио 3:", "Скриншоты:", "Время раздачи:"]

#url="https://nnmclub.to/forum/viewtopic.php?t=1695313"
#url="https://nnmclub.to/forum/viewtopic.php?t=1695055"

url = post_body = rating_url = []
mydict = {}
#k = v = ""
#--------------------

def db_init( connection, cursor ):
    
    # Создаем таблицу Films
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Films (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_nnm TEXT,
    nnm_url TEXT,
    name TEXT,
    id_kpsk TEXT,
    id_imdb TEXT,
    date TEXT
    )
    ''')
    connection.commit()

def db_add_film( connection, cursor, id_nnm, nnm_url, name, id_kpsk, id_imdb ):
    
    cur_date=datetime.now()
    cursor.execute("INSERT INTO Films (id_nnm, nnm_url, name, id_kpsk, id_imdb, date) VALUES(?, ?, ?, ?, ?, ?)",\
    (id_nnm, nnm_url, name, id_kpsk, id_imdb, cur_date))
    connection.commit()

def db_exist_Id( cursor, id_kpsk, id_imdb ):

    cursor.execute("SELECT 1 FROM Films WHERE id_kpsk = ? OR id_imdb = ?", (id_kpsk,id_imdb))
    return cursor.fetchone()



client = TelegramClient('session_tele_client2', api_id, api_hash,system_version="0.2-dmabot")


connection = sqlite3.connect(db_name)
cursor = connection.cursor()
db_init(connection,cursor)

#Parse channel NNMCLUB for Films 
@client.on(events.NewMessage(chats = [PeerChannel(channelId)],pattern='(?:.*Фильм.*)|(?:.*Новинки.*)'))
async def normal_handler(event):
    #print(event.message)
    msg=event.message

    #Get URL nnmclub page with Film
    for url_entity, inner_text in msg.get_entities_text(MessageEntityTextUrl):
        if re.search("viewtopic.php\?t", url_entity.url):
           url = url_entity.url
           #print(url)

    #if URL exist get additional info for film
    if url:
       page = requests.get(url)

       if page.status_code != 200: return

       # Parse data
       soup = BeautifulSoup(page.text, "html.parser")

       # Select data where class - postbody
       post_body=soup.find(class_="postbody")
       text=post_body.get_text('\n', strip='True')

       # Get url picture with rating Film on Kinopoisk site 
       for a_hr in post_body.find_all(class_='postImg'):
           rat=a_hr.get('title')
           if re.search("www.kinopoisk.ru/rating",rat):
              rating_url=rat

       k=Id[0]
       v=""

       # Create Dict for data about Film 
       for line in text.split("\n"):
        if not line.strip():     
          continue    
        else: 
          if re.search(":$",line):
            k=line
            v=""
          elif k != "":
            v=v+line
            mydict[k]=v
       
       # test getted info
       #i=0       
       #for line in Id:  
        # print(Id[i],"-->",mydict.get(Id[i]))
        # i+=1
       kpsk_r = imdb_r = "-"
       kpsk_url = imdb_url = rat_url = ""
       id_kpsk = id_imdb = id_nnm = 0

       #Get rating urls and id film on kinopoisk and iddb  
       for a_hr in post_body.find_all('a'):
           rat=a_hr.get('href')
           if rat.find('https://www.kinopoisk.ru/film/') != -1:
              id_kpsk=re.search("film/(.+?)/", rat).group(1)
              kpsk_url="https://rating.kinopoisk.ru/"+id_kpsk+".xml"
           elif rat.find('https://www.imdb.com/title/') != -1:
              id_imdb=re.search("title/(.+?)/", rat).group(1)
              imdb_url=rat.replace("?ref_=plg_rt_1","ratings/?ref_=tt_ov_rt")
           
       id_nnm=re.search("viewtopic.php.t=(.+?)$",url).group(1)
       #print("kpsId=",id_kpsk,"\nimdbId=",id_imdb,"\nnnmbId=",id_nnm)
              
       # Get rating film from kinopoisk if not then from imdb site
       if kpsk_url:
          rat_url=kpsk_url
          page = requests.get(rat_url,headers={'User-Agent': 'Mozilla/5.0'})
          # Parse data
          soup = BeautifulSoup(page.text, "html.parser")
          try:
           rating_xml=soup.find('rating')
           kpsk_r=rating_xml.find('kp_rating').get_text('\n', strip='True')
           imdb_r=rating_xml.find('imdb_rating').get_text('\n', strip='True')
          except:
           print("Get kinopoisk rating error.")
       elif imdb_url:
          rat_url=imdb_url
          page = requests.get(rat_url,headers={'User-Agent': 'Mozilla/5.0'})
          #print(page.status_code)
          # Parse data
          soup = BeautifulSoup(page.text, "html.parser")
          post_body=soup.find(class_="sc-5931bdee-1 gVydpF")
          imdb_r=post_body.get_text('\n', strip='True')
       else:
          kpsk_r="-"
          imdb_r="-"

    #film_add_info = "\n<b>Рейтинг:</b> КП[ "+kpsk_r+" ] Imdb[ "+imdb_r+" ]\n<b>"+Id[2]+"</b> "+mydict.get(Id[2])+"\n<b>"+Id[5]+"</b>\n"+mydict.get(Id[5])  
    film_add_info = "\n________________\n"+\
                    "Рейтинг: КП[ "+kpsk_r+" ] Imdb[ "+imdb_r+" ]\n"+\
                    Id[2]+mydict.get(Id[2])+"\n"+\
                    Id[5]+"\n"+mydict.get(Id[5])  


    msg.message=msg.message+film_add_info
    #await client.forward_messages(PeerChat(chat_my), event.message)
    
    #------ work with Database -------
    if db_exist_Id(cursor,id_kpsk,id_imdb):
       print("Exist in db - no add, and no send",id_nnm)
    else:
       print("Not exist in db - add, and send",id_nnm)
       db_add_film( connection, cursor, id_nnm, url, mydict[Id[0]], id_kpsk, id_imdb )
       await client.send_message(PeerChannel(chat_my),msg,parse_mode = 'html')

    #cursor.execute('SELECT * FROM Films')
    #tasks = cursor.fetchall()
    #for task in tasks:
    #    print(task)
    
    #------End work with Database -----



client.start()
client.run_until_disconnected()
print("End.")
connection.close()
