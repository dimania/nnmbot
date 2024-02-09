#!/usr/bin/python3
#
#Telegram Bot for filter films from NNMCLUB channel
#

from telethon import TelegramClient, sync, events
from telethon.tl.types import PeerChat, PeerChannel, MessageEntityTextUrl 
from telethon.tl.custom import Button
from datetime import datetime, date, time, timezone
from bs4 import BeautifulSoup
import requests
import re
import sqlite3
import logging

#load config file
import myconfig


#-------------- addition info vars
Id=["Название:", "Производство:", "Жанр:", "Режиссер:",
    "Актеры:", "Описание:", "Продолжительность:", "Качество видео:",
    "Перевод:","Язык озвучки:", "Субтитры:", "Видео:", "Аудио 1:",
    "Аудио 2:", "Аудио 3:", "Скриншоты:", "Время раздачи:"]

url = post_body = rating_url = []
mydict = {}

def get_config( config ):
    ''' set global variable from included config.py - import config directive''' 
    global api_id
    global api_hash
    global mybot_token
    global system_version
    global session_name
    global channelId
    global My_channelId
    global db_name
    global proxies
    global logfile
    global use_proxy
    api_id         =  config.api_id
    api_hash       =  config.api_hash
    mybot_token    =  config.mybot_token
    system_version =  config.system_version
    session_name   =  config.session_name
    channelId      =  config.channelId
    My_channelId   =  config.My_channelId
    db_name        =  config.db_name
    proxies        =  config.proxies
    logfile        =  config.logfile
    use_proxy      =  config.use_proxy
    
def db_init( connection, cursor ):
    ''' Initialize database '''
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

def db_info( cursor ):
    ''' Get Info database: all records, tagged for download records and tagged early records '''
    cursor.execute("SELECT COUNT(*) FROM Films UNION ALL SELECT COUNT(*) FROM Films WHERE download = 1 UNION ALL SELECT COUNT(*) FROM Films WHERE download = 2")
    rows = cursor.fetchall()
    return rows 

def db_switch_download( cursor, id_nnm, download):
    ''' Set tag in database for download film late '''
    cursor.execute("UPDATE Films SET download=? WHERE id_nnm=?", (download,id_nnm))
    connection.commit()
    return str(cursor.rowcount)
  
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
    ''' Set to N records with set tag download to 1 '''
    cursor.execute("UPDATE Films SET download=? WHERE download = 1", (download,))
    connection.commit()
    return str(cursor.rowcount)
    

async def query_all_records( cursor ): 
    ''' Get all database, Use with carefully may be many records '''
    logging.info(f"Query all db records")
    rows = db_list_all( cursor )
    if rows:
      for row in rows:
         #print(dict(row))        
         message = '<a href="' + dict(row).get('nnm_url') + '">' + dict(row).get('name') + '</a>'
         await client.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)
    else:
         message = "No records"
         await client.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)

async def query_tagged_records( cursor, tag ): 
    ''' Get films tagget for download '''
    logging.info(f"Query db records with set download tag ")
    rows = db_list_download( cursor, tag )
    if rows:
      for row in rows:
         #print(dict(row))        
         message = '<a href="' + dict(row).get('nnm_url') + '">' + dict(row).get('name') + '</a>'
         await client.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)
    else:
         message = "No records"
         await client.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)
    
async def query_clear_tagged_records( cursor ): 
    ''' Clear all tag for download '''
    logging.info(f"Query db for clear download tag ") 
    rows = db_clear_download( cursor, 2 )
    if rows:     
        message = 'Clear '+rows+'records'      
    else:
        message = "No records"         
    await client.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)

async def query_tag_record( cursor, event, data  ): 
    ''' Clear Button 'Add to DB' in message and set tag download to 1 '''
    logging.info(f"Clear Button 'Add to DB' in message and set tag download to 1 for id_nnm={data}")    
    db_switch_download( cursor, data, 1)
    await event.edit(buttons=Button.clear())      

async def query_info_db( cursor ): 
    ''' Get info about database records '''
    logging.info(f"Query info database ")
    rows = db_info( cursor )
    message="All records: "+str(rows[0][0])+"\nTagged records: "+str(rows[1][0])+"\nEarly tagged: "+str(rows[2][0])
    await client.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)
  

# main()
print('Start bot.')
# Enable logging
# !!! Correct parameter as in import derective above!
get_config(myconfig)

logging.basicConfig(level=logging.INFO, filename=logfile,filemode="a",format="%(asctime)s %(levelname)s %(message)s")
logging.info(f"Start bot.")

connection = sqlite3.connect(db_name)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()
db_init(connection,cursor)

# Connect to Telegram
if use_proxy:
    prx = re.search('(^.*)://(.*):(.*$)',proxies.get('http'))  
    client = TelegramClient(session_name, api_id, api_hash, system_version=system_version, proxy=(prx.group(1), prx.group(2), int(prx.group(3)))).start(bot_token=mybot_token)
else:
    proxies = None
    client = TelegramClient(session_name, api_id, api_hash, system_version=system_version).start(bot_token=mybot_token)


          
#Get reaction user on Buttons
@client.on(events.CallbackQuery())
async def callback(event):
     logging.info(f"Get callback event {event}")
     button_data=event.data.decode()

     if button_data == '/dblist':
       # Get all database, Use with carefully may be many records
       await query_all_records( cursor )       
     elif button_data == '/dwlist':
       # Get films tagget for download
       await query_tagged_records( cursor, 1 )
     elif button_data == '/dwclear':
       # Clear all tag for download
       await query_clear_tagged_records( cursor )
     elif button_data == '/dwearly':
       # Get films tagget early for download
       await query_tagged_records( cursor, 2 ) 
     elif button_data == '/dbinfo':
       # Get info about DB`
       await query_info_db( cursor )
     elif button_data.find('XX',0,2) != -1:
       # Add to Film to DB and remove Button 'Add to DB'
       data=button_data       
       datta = data.replace('XX','')
       await query_tag_record( cursor, event, data )
     else:
       pass
             
      
#Parse My channel for command 
@client.on(events.NewMessage(chats = [PeerChannel(My_channelId)],pattern='^/.*'))
async def normal_handler(event):
    #print(event.message)
    logging.info(f"Get NewMessage event: {event}\nEvent message:{event.message}")
    msg=event.message
    if msg.message == '/dblist':
       # Get all database, Use with carefully may be many records
       await query_all_records( cursor )     
    elif msg.message == '/dwlist':
       # Get films tagget for download
       await query_tagged_records( cursor, 1 )
    elif msg.message == '/dwclear':
       # Clear all tag for download
       await query_clear_tagged_records( cursor )
    elif msg.message == '/dwearly':
       # Get films tagget early for download
       await query_tagged_records( cursor, 2 )
    elif msg.message == '/dbinfo':
       # Get info about DB
       await query_info_db( cursor )   
    elif msg.message == '/m':
       # show menu 
       logging.info(f"Create menu buttons")
       keyboard = [
           [  
             #Button.inline("List All DB", b"/dblist"), 
             Button.inline("List Films tagged", b"/dwlist")
           ],
           [
             Button.inline("List Films tagged early", b"/dwearly")
           ],
           [
             Button.inline("Clear all tagged Films", b"/dwclear")
           ],
           [
             Button.inline("Get database info ", b"/dbinfo")
           ]
       ]
       await client.send_message(PeerChannel(My_channelId),"Work with database", buttons=keyboard)    
    else:
       # send help
       logging.info(f"Send help message")
       message="Use command:\n/dblist - list all records (carefully!)\n/dwlist - list films tagget for download\n/dwclear - clear tagget films"
       await client.send_message(PeerChannel(My_channelId),message,parse_mode='html')
       
   

#Parse channel NNMCLUB for Films 
@client.on(events.NewMessage(chats = [PeerChannel(channelId)],pattern='(?:.*Фильм.*)|(?:.*Новинки.*)'))
async def normal_handler(event):
    #print(event.message)
    logging.info(f"Get new message in NNMCLUB Channel: {event.message}")
    msg=event.message

    #Get URL nnmclub page with Film
    for url_entity, inner_text in msg.get_entities_text(MessageEntityTextUrl):
        if re.search(r'viewtopic.php\?t', url_entity.url):
           url = url_entity.url
           #print(url)
           
    logging.info(f"Get URL nnmclub page with Film: {url}") 
    
    #if URL exist get additional info for film
    if url:
       page = requests.get(url,proxies=proxies)

       if page.status_code != 200: 
         logging.error(f"Can't open url:{url}, status:{page.status}") 
         return

       # Parse data
       soup = BeautifulSoup(page.text, 'html.parser')

       # Select data where class - postbody
       post_body=soup.find(class_='postbody')
       text=post_body.get_text('\n', strip='True')

       # Get url picture with rating Film on Kinopoisk site 
       for a_hr in post_body.find_all(class_='postImg'):
           rat=a_hr.get('title')
           if re.search('www.kinopoisk.ru/rating',rat):
              rating_url=rat

       k=Id[0]
       v=""

       # Create Dict for data about Film 
       for line in text.split("\n"):
        if not line.strip():     
          continue    
        else: 
          if re.search(':$',line):
            k=line
            v=""
          elif k != "":
            v=v+line
            mydict[k]=v
       
       kpsk_r = imdb_r = "-"
       kpsk_url = imdb_url = rat_url = ""
       id_kpsk = id_imdb = id_nnm = 0

       #Get rating urls and id film on kinopoisk and iddb  
       for a_hr in post_body.find_all('a'):
           rat=a_hr.get('href')
           if rat.find('https://www.kinopoisk.ru/film/') != -1:
              id_kpsk=re.search("film/(.+?)/", rat).group(1)
              kpsk_url='https://rating.kinopoisk.ru/'+id_kpsk+'.xml'
              logging.info(f"Create url rating from kinopoisk: {kpsk_url}")
           elif rat.find('https://www.imdb.com/title/') != -1:
              id_imdb=re.search('title/(.+?)/', rat).group(1)
              imdb_url=rat.replace('?ref_=plg_rt_1','ratings/?ref_=tt_ov_rt')
              logging.info(f"Create url rating from imdb: {imdb_url}")
           
       id_nnm=re.search('viewtopic.php.t=(.+?)$',url).group(1)
       
       if db_exist_Id(cursor,id_kpsk,id_imdb):
          logging.info(f"Film {id_nnm} exist in db - end analize.")
          return
              
       # Get rating film from kinopoisk if not then from imdb site
       if kpsk_url:
          rat_url=kpsk_url
          page = requests.get(rat_url,headers={'User-Agent': 'Mozilla/5.0'},proxies=proxies)
          # Parse data
          soup = BeautifulSoup(page.text, 'html.parser') #BUG me be better use xml.parser ?
          try:
           rating_xml=soup.find('rating')
           kpsk_r=rating_xml.find('kp_rating').get_text('\n', strip='True')
           imdb_r=rating_xml.find('imdb_rating').get_text('\n', strip='True')
           logging.info(f"Get rating from kinopoisk: {kpsk_url}")
          except:
           logging.info(f"No kinopoisk rating on site")
       elif imdb_url:
          rat_url=imdb_url
          page = requests.get(rat_url,headers={'User-Agent': 'Mozilla/5.0'},proxies=proxies)
          # Parse data
          soup = BeautifulSoup(page.text, 'html.parser')
          post_body=soup.find(class_='sc-5931bdee-1 gVydpF')
          imdb_r=post_body.get_text('\n', strip='True')
          logging.info(f"Get rating from imdb: {imdb_url}")
       else:
          kpsk_r="-"
          imdb_r="-"

    logging.info(f"Add info to message") 
    film_add_info = "\n_________________________________\n"+\
                    "Рейтинг: КП[ "+kpsk_r+" ] Imdb[ "+imdb_r+" ]\n"+\
                    Id[2]+mydict.get(Id[2])+"\n"+\
                    Id[5]+"\n"+mydict.get(Id[5])  

    msg.message=msg.message+film_add_info
    logging.info(f"Film not exist in db - add and send, id_nnm:{id_nnm}\n Message:{msg}")
    db_add_film( connection, cursor, id_nnm, url, mydict[Id[0]], id_kpsk, id_imdb )
    bdata='XX'+id_nnm
    await client.send_message(PeerChannel(My_channelId),msg,parse_mode='md',
                                 buttons=[ Button.inline('Add Film to database', bdata),])
    
client.start()
client.run_until_disconnected()
logging.info(f"End.\n--------------------------")
print('End.')
connection.close()
