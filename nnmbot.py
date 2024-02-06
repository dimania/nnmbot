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

import myconfig.py


#-------------- addition info vars
Id=["Название:", "Производство:", "Жанр:", "Режиссер:",
    "Актеры:", "Описание:", "Продолжительность:", "Качество видео:",
    "Перевод:","Язык озвучки:", "Субтитры:", "Видео:", "Аудио 1:",
    "Аудио 2:", "Аудио 3:", "Скриншоты:", "Время раздачи:"]

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
    date TEXT,
    download INT DEFAULT 0
    )
    ''')
    connection.commit()

def db_add_film( connection, cursor, id_nnm, nnm_url, name, id_kpsk, id_imdb ):
    ''' Add new Film to database '''
    cur_date=datetime.now()
    cursor.execute("INSERT INTO Films (id_nnm, nnm_url, name, id_kpsk, id_imdb, date) VALUES(?, ?, ?, ?, ?, ?)",\
    (id_nnm, nnm_url, name, id_kpsk, id_imdb, cur_date))
    connection.commit()

def db_exist_Id( cursor, id_kpsk, id_imdb ):
    ''' Test exist Film in database '''
    cursor.execute("SELECT 1 FROM Films WHERE id_kpsk = ? OR id_imdb = ?", (id_kpsk,id_imdb))
    return cursor.fetchone()

def db_switch_download( cursor, id_nnm, download):
    ''' Set tag in database for download film late '''
    cursor.execute("UPDATE Films SET download=? WHERE id_nnm=?", (download,id_nnm))
    connection.commit()


def db_list_all( cursor ):
    ''' List all database '''
    cursor.execute('SELECT  * FROM Films')
    rows = cursor.fetchall()    
    return rows

def db_list_download( cursor, download ):
    ''' List only records with set tag download '''
    cursor.execute("SELECT name,nnm_url FROM Films WHERE download = ?", (download,) )
    rows = cursor.fetchall()
    #for row in rows:
    #  print(dict(row))
    return rows

def db_clear_download( cursor, download ):
    ''' List only records with set tag download '''
    cursor.execute("UPDATE Films SET download=?", (download,))
    connection.commit()

# Connect to Telegram
if USE_PROXY client = TelegramClient(session_name, api_id, api_hash,system_version,proxies=proxies).start(bot_token=mybot_token):
else
client = TelegramClient(session_name, api_id, api_hash,system_version).start(bot_token=mybot_token)



connection = sqlite3.connect(db_name)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()
db_init(connection,cursor)

#Get reaction user
@client.on(events.CallbackQuery())
async def callback(event):
    #if not event.via_inline:       
      # Tag Film for download and clear buttons       
      db_switch_download( cursor, event.data.decode(), 1)      
      await client.edit_message(event.sender_id, event.message_id,buttons=Button.clear())      
    #else:
     # pass

#Parse My channel for command 
@client.on(events.NewMessage(chats = [PeerChannel(My_channelId)],pattern='^/.*'))
async def normal_handler(event):
    #print(event.message)
    msg=event.message
    if event.data == '/dblist':
       # Get all database, Use with carefully may be many records
       rows = db_list_all( cursor )
       for row in rows:
          #print(dict(row))        
          message = '<a href="' + dict(row).get('nnm_url') + '">' + dict(row).get('name') + '</a>'
          await client.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)       
    elif event.data == '/dwlist':
       # Get films tagget for download
       rows = db_list_download( cursor, 1 )
       for row in rows:
        #print(dict(row))        
          message = '<a href="' + dict(row).get('nnm_url') + '">' + dict(row).get('name') + '</a>'
          await client.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)
    elif event.data == '/dwclear':
       # Clear all tag for download
       db_clear_download( cursor, 0 )
    else
       # send help
       message="Use command:\n/dblist - list all records (carefully!)\n/dwlist - list films tagget for download\n/dwclear - clear tagget films"
       await client.send_message(PeerChannel(My_channelId),message,parse_mode='html')
       
   

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
    #await client.forward_messages(PeerChat(My_channelId), event.message)
    
    #------ work with Database -------
    if db_exist_Id(cursor,id_kpsk,id_imdb):
       print("Exist in db - no add, and no send",id_nnm)
    else:
       print("Not exist in db - add, and send",id_nnm)
       db_add_film( connection, cursor, id_nnm, url, mydict[Id[0]], id_kpsk, id_imdb )
       await client.send_message(PeerChannel(My_channelId),film_add_info,parse_mode='md',
                                 buttons=[ Button.inline('Add to DB', id_nnm),])
    #------End work with Database -----



client.start()
client.run_until_disconnected()
print("End.")
connection.close()
