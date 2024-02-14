#!/usr/bin/python3
#
#Telegram Bot for filter films from NNMCLUB channel
#

from telethon import TelegramClient, events
from telethon.tl.types import PeerChat, PeerChannel, MessageEntityTextUrl 
from telethon.tl.custom import Button
from telethon.errors import MessageNotModifiedError
from datetime import datetime, date, time, timezone
from bs4 import BeautifulSoup
import requests
import re
import sqlite3
import logging
import textwrap
import asyncio
import os.path

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
    global session_client
    global session_bot
    global channelId
    global My_channelId
    global db_name
    global proxies
    global logfile
    global use_proxy
    global filter
    global ICU_extension_lib 
    
    try:
     api_id         =  config.api_id
     api_hash       =  config.api_hash
     mybot_token    =  config.mybot_token
     system_version =  config.system_version
     session_client =  config.session_client
     session_bot    =  config.session_bot    
     channelId      =  config.channelId
     My_channelId   =  config.My_channelId
     db_name        =  config.db_name
     proxies        =  config.proxies
     logfile        =  config.logfile
     use_proxy      =  config.use_proxy
     filter         =  config.filter
     ICU_extension_lib = config.ICU_extension_lib
    except Exception as error:
     print(f"Error in config file: { error }" ) 
     exit(-1)


def db_init( connection, cursor ):
    ''' Initialize database '''
    
    #Load ICU extension in exist for case independet search  in DB
    if os.path.isfile(ICU_extension_lib):
      connection.enable_load_extension(True)
      connection.load_extension(ICU_extension_lib)
    
    # Создаем таблицу Films
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Films (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_msg TEXT,
    id_nnm TEXT,
    nnm_url TEXT,
    name TEXT,
    id_kpsk TEXT,
    id_imdb TEXT,
    date TEXT,
    download INT DEFAULT 0
    )
    ''')
    connection.commit()

def db_add_film( connection, cursor, id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb ):
    ''' Add new Film to database '''
    cur_date=datetime.now()
    cursor.execute("INSERT INTO Films (id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, date) VALUES(?, ?, ?, ?, ?, ?, ?)",\
    (id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, cur_date))
    connection.commit()

def db_exist_Id( cursor, id_kpsk, id_imdb ):
    ''' Test exist Film in database '''
    cursor.execute("SELECT 1 FROM Films WHERE id_kpsk = ? OR id_imdb = ?", (id_kpsk,id_imdb))
    return cursor.fetchone()

def db_get_id_nnm( cursor, id_msg ):
    ''' Get id_nm by id_msg '''
    cursor.execute("SELECT id_nnm FROM Films WHERE id_msg = ?", (id_msg,))    
    row = cursor.fetchone()
    if row: 
      return dict(row).get('id_nnm')
    else: 
      return None

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

def db_search( cursor, str_search ):
    ''' Search in db '''
    str_search='%'+str_search+'%'
    cursor.execute("SELECT name,nnm_url FROM Films WHERE name LIKE ? COLLATE NOCASE", (str_search,) )
    rows = cursor.fetchall()
    for row in rows:
      print(dict(row))
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
         await bot.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)
    else:
         message = "No records"
         await bot.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)

async def query_search( cursor, str_search ): 
    ''' Search Films in database '''
    logging.info(f"Search in database:{str_search}")
    rows = db_search( cursor, str_search )
    if rows:
      for row in rows:
         #print(dict(row))        
         message = '<a href="' + dict(row).get('nnm_url') + '">' + dict(row).get('name') + '</a>'
         await bot.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)
    else:
         message = "No records"
         await bot.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)
         
async def query_tagged_records( cursor, tag ): 
    ''' Get films tagget for download '''
    logging.info(f"Query db records with set download tag ")
    rows = db_list_download( cursor, tag )
    if rows:
      for row in rows:
         #print(dict(row))        
         message = '<a href="' + dict(row).get('nnm_url') + '">' + dict(row).get('name') + '</a>'
         await bot.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)
    else:
         message = "No records"
         await bot.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)
    
async def query_clear_tagged_records( cursor ): 
    ''' Clear all tag for download '''
    logging.info(f"Query db for clear download tag ") 
    rows = db_clear_download( cursor, 2 )
    if rows:     
        message = 'Clear '+rows+' records'      
    else:
        message = "No records"         
    await bot.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)

async def query_tag_record_revert_button( cursor, event, data  ): 
    ''' Revert Button to 'Remove from DB' in message and set tag download to 1 '''
    db_switch_download( cursor, data, 1)
    #id_nnm=db_get_id_nnm( cursor, event.message_id )
    logging.info(f"Revert Button 'Add to DB' to 'Remove from DB' in message and set tag download to 1 for id_nnm={data}")  
    try: 
      #await event.edit(buttons=Button.clear())
      bdata='RXX'+data
      await event.edit(buttons=[ Button.inline('Remove from BD', bdata),Button.inline("Menu", b"/m")])
    except MessageNotModifiedError:
      pass

async def query_untag_record_revert_button( cursor, event, data  ): 
    ''' Revert Button to 'Add to DB' in message and set tag download to 2 '''
    db_switch_download( cursor, data, 2)
    #id_nnm=db_get_id_nnm( cursor, event.message_id )
    logging.info(f"Revert Button 'Add to DB' to 'Remove from DB' in message and set tag download to 1 for id_nnm={data}")  
    try: 
      #await event.edit(buttons=Button.clear())
      bdata='XX'+data
      await event.edit(buttons=[ Button.inline('Add Film to BD', bdata),Button.inline("Menu", b"/m")])
    except MessageNotModifiedError:
      pass
    
async def query_info_db( cursor ): 
    ''' Get info about database records '''
    logging.info(f"Query info database ")
    rows = db_info( cursor )
    message="All records: "+str(rows[0][0])+"\nTagged records: "+str(rows[1][0])+"\nEarly tagged: "+str(rows[2][0])
    await bot.send_message(PeerChannel(My_channelId),message,parse_mode='html',link_preview=0)

async def query_add_button( cursor, event, id_msg ): 
    ''' Add Button 'Add to DB' in message and set tag download to 1 '''
    id_nnm=db_get_id_nnm( cursor, id_msg )
    logging.info(f"Get id_nnm={id_nnm} by message id={id_msg}")
    if id_nnm:
      bdata='XX'+id_nnm
      await event.edit(buttons=[ Button.inline('Add Film to BD', bdata),Button.inline("Menu", b"/m")])
  
async def create_menu():
       ''' Create menu on channel '''
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
           ],
           [
             Button.inline("Search Films in database ", b"/s")
           ]
       ]
       await bot.send_message(PeerChannel(My_channelId),"Work with database", buttons=keyboard)  

# main()
print('Start bot.')
# !!! Correct parameter as in import derective above!
get_config(myconfig)

# Enable logging
logging.basicConfig(level=logging.INFO, filename=logfile,filemode="a",format="%(asctime)s %(levelname)s %(message)s")
logging.info(f"Start bot.")

connection = sqlite3.connect(db_name)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()
db_init(connection,cursor)


# Connect to Telegram
if use_proxy:
    prx = re.search('(^.*)://(.*):(.*$)',proxies.get('http'))  
    bot = TelegramClient(session_bot, api_id, api_hash, system_version=system_version, proxy=(prx.group(1), prx.group(2), int(prx.group(3)))).start(bot_token=mybot_token)
    client = TelegramClient(session_client, api_id, api_hash, system_version=system_version, proxy=(prx.group(1), prx.group(2), int(prx.group(3))))
else:
    proxies = None
    bot = TelegramClient(session_bot, api_id, api_hash, system_version=system_version).start(bot_token=mybot_token)
    client = TelegramClient(session_client, api_id, api_hash, system_version=system_version)
         
#Get reaction user on Buttons
@bot.on(events.CallbackQuery())
async def callback(event):
     logging.debug(f"Get callback event {event}")
     user=event.query.user_id
     # Check user rights
     permissions = await bot.get_permissions(event.query.peer, user)
     logging.info(f"Get Permission for user: {user} ->  {permissions.is_admin} for chat={event.query.peer}")
     
     if not permissions.is_admin:
       event.respond("Sorry you are not Admin. You can only set Reaction.")
       return
     
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
       # Get info about DB
       await query_info_db( cursor )
     elif button_data == '/m':
       # Menu button pressed - show menu 
       await create_menu()
     elif button_data == '/s':
       # search Films 
       await event.respond("Write and send what you search:")
       @bot.on(events.NewMessage(chats = [PeerChannel(My_channelId)]))
       async def search_handler(event_search):
           logging.info(f"Get search string: {event_search.message.message}")
           await query_search( cursor, event_search.message.message )
           await event.respond("...Done...",buttons=[Button.inline("Menu", b"/m")])
           bot.remove_event_handler(search_handler)
     elif button_data.find('XX',0,2) != -1:
       # Add to Film to DB and remove Button 'Add to DB'
       data = button_data       
       data = data.replace('XX','')
       logging.info(f"Button 'Add...' pressed data={button_data} write {data}")
       await query_tag_record_revert_button( cursor, event, data )
     elif button_data.find('RXX',0,3) != -1:
       # Remove Film from DB and revert Button to 'Add to DB'
       data = button_data       
       data = data.replace('RXX','')
       logging.info(f"Button 'Remove...' pressed data={button_data} write {data}")
       await query_untag_record_revert_button( cursor, event, data )
     else:
       pass
             
      
#Parse My channel for command 
@bot.on(events.NewMessage(chats = [PeerChannel(My_channelId)],pattern="(^/.*)|"+filter))
async def normal_handler(event):
    #print(event.message)
    logging.debug(f"Get NewMessage event: {event}\nEvent message:{event.message}")
    msg=event.message
    #user = await event.get_input_sender()
    # Check user rights
    #print(f"Peer={msg.peer_id} User={user}")
    #permissions = await bot.get_permissions(msg.peer_id, user)
    #logging.info(f"Get Permission for user: {user} ->  {permissions.is_admin}")
    if not permissions.is_admin:
       return
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
       await create_menu()
    elif re.search(filter,msg.message):
       # Add button 'Add Film to database' as inline button for message
       await query_add_button( cursor, event, msg.id ) 
    else:
       # send help
       logging.info(f"Send help message")
       message="Use command:\n/dblist - list all records (carefully!)\n/dwlist - list films tagget for download\n/dwclear - clear tagget films"
       await bot.send_message(PeerChannel(My_channelId),message,parse_mode='html')
       
       
#Parse channel NNMCLUB for Films 
@client.on(events.NewMessage(chats = [PeerChannel(channelId)],pattern=filter))
async def normal_handler(event):
    #print(event.message)
   
    logging.debug(f"Get new message in NNMCLUB Channel: {event.message}")    
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
    msg.message=textwrap.shorten(msg.message, width=1019, placeholder="...")    
    #bdata='XX'+id_nnm
    #await bot.send_message(PeerChannel(My_channelId),msg,parse_mode='md', buttons=[ Button.inline('Add Film to database', bdata),])
    send_msg = await client.send_message(PeerChannel(My_channelId),msg,parse_mode='md')
    db_add_film( connection, cursor, send_msg.id, id_nnm, url, mydict[Id[0]], id_kpsk, id_imdb )
    logging.info(f"Film not exist in db - add and send, src_id_msg={msg.id} dst_id_msg={send_msg.id} id_nnm:{id_nnm}\n Message:{msg}")
    logging.debug(f"Send Message:{send_msg}")
    

client.start()    
bot.start()
client.run_until_disconnected()
bot.run_until_disconnected()
connection.close()
logging.info(f"End.\n--------------------------")
print('End.')
