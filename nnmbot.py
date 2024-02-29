#!/usr/bin/python3
#
# Telegram Bot for filter films from NNMCLUB channel
#
# load config file
#!!!!!!!! Replace with you config file here !!!!!!!
# replace myconfig with config by example
# --------------------------------
import myconfig as cfg
# --------------------------------

from telethon import TelegramClient, events, utils
from telethon.tl.types import PeerChat, PeerChannel, PeerUser, MessageEntityTextUrl
from telethon.tl.custom import Button
from telethon.errors import MessageNotModifiedError
from telethon.events import StopPropagation
from datetime import datetime, date, time, timezone
from bs4 import BeautifulSoup
import requests
import re
import sqlite3
import logging
import textwrap
import asyncio
import os.path

#import nnm_module as db

#-----------------
# CONSTANT
#
DEFTAG = 0
SETTAG = 1
UNSETTAG = 2
USER_ACTIVE = 1
USER_BLOCKED = 0
USER_UNBLOCKED = 1
USER_SUPERADMIN = 4
USER_READ_WRITE = 3
USER_READ = 2
USER_NEW = 1
USER_NO_RIGHTS=0
MENU_USER_READ = 0
MENU_USER_READ_WRITE = 1
MENU_SUPERADMIN = 2
#-----------------

def get_config(config):
    ''' set global variable from included config.py - import config directive'''
    global api_id
    global api_hash
    global mybot_token
    global system_version
    global session_client
    global session_bot
    global bot_name
    global Channel_mon
    global Channel_my
    global db_name
    global proxies
    global logfile
    global use_proxy
    global filter
    global ICU_extension_lib
    global log_level

    try:
        api_id = config.api_id
        api_hash = config.api_hash
        mybot_token = config.mybot_token
        system_version = config.system_version
        session_client = config.session_client
        session_bot = config.session_bot
        bot_name = config.bot_name
        Channel_mon = config.Channel_mon
        Channel_my = config.Channel_my
        db_name = config.db_name
        logfile = config.logfile
        use_proxy = config.use_proxy
        filter = re.compile(config.filter)
        log_level = config.log_level
        ICU_extension_lib = config.ICU_extension_lib

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

    # Create basic table Films
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
    # Ctreate table Users
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Users (
      id_user TEXT NOT NULL PRIMARY KEY,
      name_user TEXT NOT NULL,
      date TEXT NOT NULL,
      active INTEGER DEFAULT 0,
      rights INTEGER DEFAULT 0
      )
      ''')
    # Create table Ufilms - films tagged users
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Ufilms (
      ufilms_id INTEGER PRIMARY KEY AUTOINCREMENT,
      id_user TEXT NOT NULL,
      id_Films  TEXT NOT NULL,
      date  TEXT NOT NULL,
      download INTEGER DEFAULT 0,
      FOREIGN KEY (id_user)
      REFERENCES Users (id_user)
        ON DELETE CASCADE
       )
      ''')

    connection.commit()

def db_add_film(id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb):
    ''' Add new Film to database '''
    cur_date = datetime.now()
    cursor.execute("INSERT INTO Films (id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, date) VALUES(?, ?, ?, ?, ?, ?, ?)",
                   (id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, cur_date))
    connection.commit()

def db_exist_Id(id_kpsk, id_imdb):
    ''' Test exist Film in database '''
    cursor.execute(
        "SELECT 1 FROM Films WHERE id_kpsk = ? OR id_imdb = ?", (id_kpsk, id_imdb))
    return cursor.fetchone()

def db_get_id_nnm(id_msg):
    ''' Get id_nm by id_msg '''
    cursor.execute("SELECT id_nnm FROM Films WHERE id_msg = ?", (id_msg,))
    row = cursor.fetchone()
    if row:
        return dict(row).get('id_nnm')
    else:
        return None

def db_info():
    ''' Get Info database: all records, tagged for download records and tagged early records '''
    cursor.execute(
        "SELECT COUNT(*) FROM Films UNION ALL SELECT COUNT(*) FROM Films WHERE download = 1 UNION ALL SELECT COUNT(*) FROM Films WHERE download = 2")
    rows = cursor.fetchall()
    return rows

def db_switch_download(id_nnm, download): #FIXME Not used
    ''' Set tag in database for download film late '''
    cursor.execute("UPDATE Films SET download=? WHERE id_nnm=?",
                   (download, id_nnm))
    connection.commit()
    return str(cursor.rowcount)

def db_list_all():
    ''' List all database '''
    cursor.execute('SELECT  * FROM Films')
    rows = cursor.fetchall()
    return rows

def db_list_download(download): #FIXME Not used
    ''' List only records with set tag download '''
    cursor.execute(
        "SELECT name,nnm_url FROM Films WHERE download = ?", (download,))
    rows = cursor.fetchall()
    # for row in rows:
    #  print(dict(row))
    return rows

def db_search(str_search):
    ''' Search in db '''
    str_search = '%'+str_search+'%'
    cursor.execute(
        "SELECT name,nnm_url FROM Films WHERE name LIKE ? COLLATE NOCASE", (str_search,))
    rows = cursor.fetchall()
    return rows

def db_clear_download(download): #FIXME Not used
    ''' Set to N records with set tag download to 1 '''
    cursor.execute(
        "UPDATE Films SET download=? WHERE download = 1", (download,))
    connection.commit()
    return str(cursor.rowcount)

def db_add_user( id_user, name_user ):
    ''' Add new user to database '''
    cur_date=datetime.now()
    try:
      cursor.execute("INSERT INTO Users (id_user, name_user, date) VALUES(?, ?, ?)",\
      (id_user, name_user, cur_date,))
      connection.commit()
    except Exception as IntegrityError:
      logging.error(f"User already exist in BD\n") 
      logging.error(f"Original Error is: {IntegrityError}")           
      return 1
   
    return 0

def db_del_user( id_user ):
    '''Delete user from database and user tagged films'''
    cursor.execute("DELETE FROM Users WHERE id_user = ?", (id_user,))
    rows = cursor.fetchall()
    return rows

def db_exist_user( id_user ):
    ''' Test exist User in database '''
    cursor.execute("SELECT active,rights,name_user FROM Users WHERE id_user = ?", (id_user,))
    rows = cursor.fetchall()
    return rows

def db_ch_rights_user( id_user, active, rights ):
    ''' Change rights and status (active or blocked) for user '''
    cursor.execute("UPDATE Users SET active=?, rights=? WHERE id_user = ?", (active,rights,id_user))
    connection.commit()
    logging.info(f"SQL UPDATE: id_user={id_user} active={active}, rights={rights} result={str(cursor.rowcount)}" )
    return str(cursor.rowcount)  

def db_list_users( id_user=None, active=None, rights=None ):
    '''List users in database '''
    
    if id_user is not None and active is not None and rights is not None:
        cursor.execute("SELECT active,rights,name_user,id_user FROM Users WHERE id_user = ? AND active = ? AND rights = ?", (id_user, active, rights,))
    elif id_user is not None and active is not None:
        cursor.execute("SELECT active,rights,name_user,id_user FROM Users WHERE id_user = ? AND active = ?", (id_user, active,))
    elif id_user is not None and rights is not None:
        cursor.execute("SELECT active,rights,name_user,id_user FROM Users WHERE id_user = ? AND rights = ?", (id_user, rights,))    
    elif active is not None and rights is not None:
        cursor.execute("SELECT active,rights,name_user,id_user FROM Users WHERE active = ? AND rights = ?", (active, rights,))        
    elif id_user is not None:
        cursor.execute("SELECT active,rights,name_user,id_user FROM Users WHERE id_user = ?", (id_user,))
    elif active is not None:
        cursor.execute("SELECT active,rights,name_user,id_user FROM Users WHERE active = ?", (active,))
    elif rights is not None:
        cursor.execute("SELECT active,rights,name_user,id_user FROM Users WHERE rights = ?", (rights,))
    else:            
        cursor.execute("SELECT active,rights,name_user,id_user FROM Users")
             
    rows = cursor.fetchall()
    
    logging.info(f"SELECT USERS: id_user={id_user} active={active}, rights={rights} result={rows}" )
    return rows

def db_list_tagged_films( id_user=None, tag=SETTAG ):
    ''' List only records with set tag '''
    cursor.execute("SELECT name,nnm_url FROM Films WHERE id IN (SELECT id_Films FROM Ufilms WHERE id_user=? and tag=?)", (id_user,tag,))
    rows = cursor.fetchall()
    return rows

def db_add_tag( id_nnm, tag, id_user ):
    ''' User first Tag film in database '''
    cur_date=datetime.now()
    cursor.execute("INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (?,(SELECT id FROM Films WHERE id_nnm=?),?,?)",
                  (id_user,id_nnm,cur_date,tag))
    
    connection.commit()
    return str(cursor.rowcount)

def db_switch_tag( id_nnm, tag, id_user ): #FIXME Not used
    ''' Update tag in database for control film '''
    cursor.execute("UPDATE Ufilms SET tag=? WHERE id_user = ? AND id_Films = (SELECT id FROM Films WHERE id_nnm=?)",
                  (tag,id_user,id_nnm))
    connection.commit()
    return str(cursor.rowcount)

def db_switch_film_tag( id_nnm, tag, id_user ):
    ''' Update user tagging in database for films  '''
    cursor.execute("UPDATE Ufilms SET tag=? WHERE id_user = ? AND id_Films = (SELECT id FROM Films WHERE id_nnm=?)",
                  (tag,id_user,id_nnm))
    connection.commit()
    return str(cursor.rowcount)

def db_switch_user_tag( id_user, tag ):
    ''' Update tag in database for user '''
    cursor.execute("UPDATE Ufilms SET tag=? WHERE id_user = ?",
                  (tag,id_user))
    connection.commit()
    return str(cursor.rowcount)    
    
def db_get_tag( id_nnm, id_user ):
    ''' Get if exist current tag for user '''
    cursor.execute("SELECT tag FROM Ufilms WHERE id_Films = (SELECT id FROM Films WHERE id_nnm=?) AND id_user=?", (id_nnm, id_user,))
    rows = cursor.fetchall()
    return rows

async def query_all_records(event):
    ''' Get all database, Use with carefully may be many records '''
    logging.info(f"Query all db records")
    rows = db_list_all()
    if rows:
        for row in rows:
            # print(dict(row))
            message = '<a href="' + \
                dict(row).get('nnm_url') + '">' + \
                dict(row).get('name') + '</a>'
            await event.respond(message, parse_mode='html', link_preview=0)
    else:
        message = ".....No records....."
        await event.respond(message, parse_mode='html', link_preview=0)

async def query_search(str_search, event):
    ''' Search Films in database '''
    logging.info(f"Search in database:{str_search}")
    rows = db_search(str_search)
    if rows:
        for row in rows:
            message = '<a href="' + \
                dict(row).get('nnm_url') + '">' + \
                dict(row).get('name') + '</a>'
            await event.respond(message, parse_mode='html', link_preview=0)
    else:
        message = "No records"
        await event.respond(message, parse_mode='html', link_preview=0)

async def query_tagged_records(id_user, tag, event):
    ''' Get films tagget for user '''
    logging.info(f"Query db records with set download tag ")
    rows = db_list_tagged_films( id_user=id_user, tag=tag )
    if rows:
        for row in rows:
            # print(dict(row))
            message = '<a href="' + \
                dict(row).get('nnm_url') + '">' + \
                dict(row).get('name') + '</a>'
            await event.respond(message, parse_mode='html', link_preview=0)
    else:
        message = "No records"
        await event.respond(message, parse_mode='html', link_preview=0)

async def query_clear_tagged_records(id_user, event):
    ''' Clear all tag for user '''
    logging.info(f"Query db for clear tag ")
    rows = db_switch_user_tag( UNSETTAG, id_user )
    if rows:
        message = 'Clear '+rows+' records'
    else:
        message = "No records"
    await event.respond(message, parse_mode='html', link_preview=0)

async def query_tag_record_revert_button(event, id_nnm, bot_name, id_user): #FIXME Not used in future?
    ''' Revert Button to 'Remove from DB' in message and set tag download to 1 '''
    db_switch_film_tag( id_nnm, SETTAG, id_user )
    #db_switch_download(data, 1)
    logging.info(f"Revert Button 'Add to DB' to 'Remove from DB' in message and set tag download to 1 for id_nnm={data}")
    try:
        # await event.edit(buttons=Button.clear())
        bdata = 'RXX'+data
        await event.edit(buttons=[Button.inline('Remove from BD', bdata), Button.url('Control BD', 't.me/'+bot_name+'?start')])
    except MessageNotModifiedError:
        pass

async def query_untag_record_revert_button(event, data, bot_name): #FIXME Not used in future?
    ''' Revert Button to 'Add to DB' in message and set tag download to 2 '''
    db_switch_film_tag( id_nnm, UNSETTAG, id_user )
    # id_nnm=db_get_id_nnm( event.message_id )
    logging.info(f"Revert Button 'Add to DB' to 'Remove from DB' in message and set tag download to 1 for id_nnm={data}")
    try:
        # await event.edit(buttons=Button.clear())
        bdata = 'XX'+data
        await event.edit(buttons=[Button.inline('Add Film to BD', bdata), Button.url('Control BD', 't.me/'+bot_name+'?start')])
    except MessageNotModifiedError:
        pass

async def query_info_db(Channel_my_id):
    ''' Get info about database records '''
    logging.info(f"Query info database ")
    rows = db_info()
    message = "All records: " + \
        str(rows[0][0])+"\nTagged records: " + \
        str(rows[1][0])+"\nEarly tagged: "+str(rows[2][0])
    await Channel_my_id.respond(message, parse_mode='html', link_preview=0)

async def query_add_button(event, id_msg, bot_name):
    ''' Add Button 'Add to DB' and 'Control DB' in message '''
    await asyncio.sleep(2)  # wait while write to DB on previous step
    id_nnm = db_get_id_nnm(id_msg)
    logging.info(f"Get id_nnm={id_nnm} by message id={id_msg} bot_name={bot_name}")
    if id_nnm:
        bdata = 'XX'+id_nnm
        buttons_film = [
                Button.inline('Add Film to DB', bdata),
                Button.url('Control DB', 't.me/'+bot_name+'?start')
                ]
        await event.edit(buttons=buttons_film)

async def query_add_user(id_user, name_user, event):
    ''' Add user to database '''
    logging.info(f"Add user to database ")
    res = db_add_user(id_user, name_user)
    if res:
        await event.respond('Yoy already power user!')
    else:
        message = "You request send to Admins, and will be reviewed soon."
        await event.respond(message)
        #TODO Send message Admins if need

async def create_menu_bot(level, event):
    ''' Create menu on channel '''
    logging.info(f"Create menu buttons")
    keyboard = [
        [
            # Button.inline("List All DB", b"/dblist"),
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

    if level == MENU_SUPERADMIN:
       # Add items for SuperUser
       keyboard.append([Button.inline("List user requests for add", b"/lur")])

    await event.respond("**☣ Work with database:**", parse_mode='md', buttons=keyboard)

async def create_yes_no_bot(question, event):
    ''' Create yes or no buttons with text '''
    logging.debug(f"Create yes or no buttons")
    keyboard = [
        [
            Button.inline("Yes", b"/yes"),
            Button.inline("No", b"/no")
        ]
    ]
    # await bot.send_message(PeerChannel(Channel_my_id),"Work with database", buttons=keyboard)
    await event.respond(question, parse_mode='md', buttons=keyboard)

async def check_user(channel, user, event):
    ''' Check right of User '''
    permissions = await bot.get_permissions(channel, user)
    logging.debug(f"Get permissions for channe={channel} user={user}")
    user_db = db_exist_user(user)
    ret = -1
    if not user_db:
      logging.debug(f"User {user} is not in db - new user")
      ret = USER_NEW
      return ret
    elif dict(user_db[0]).get('active') == USER_BLOCKED:
      logging.debug(f"User {user} is blocked in db")
      ret = USER_BLOCKED
    elif dict(user_db[0]).get('rights') == USER_READ:
      logging.debug(f"User {user} can only view in db")
      ret = USER_READ
    elif dict(user_db[0]).get('rights') == USER_READ_WRITE:
      logging.debug(f"User {user} admin in your db")
      ret = USER_READ_WRITE
     
    if permissions.is_admin:
        ret = USER_SUPERADMIN  # Admin
    return ret

async def query_wait_users(event):
    ''' Get list users who submitted applications '''     
    rows = db_list_users( id_user=None, active=USER_BLOCKED, rights=USER_NO_RIGHTS )
    logging.debug(f"Get users waiting approve")
    button=[]
    if rows:
        #await event.respond('List awaiting users:')
        for row in rows:
            id_user = dict(row).get('id_user')
            message = dict(row).get('name_user')
            bdata='ENABLE'+id_user
            button.append([ Button.inline('☑ '+message, bdata)])
        await event.respond('List awaiting users:', buttons=button)    
    else:
        message = ".....No records....."
        await event.respond(message)

async def query_all_users(event):
    ''' Get list all users '''     
    rows = db_list_users()
    logging.gebug(f"Get users waiting approve")
    if rows:
        await event.respond('List awaiting users:')
        for row in rows:
            #id_user = "dict(row).get('id_user')"
            message = dict(row).get('name_user')
            await event.respond(message, buttons=button)
    else:
        message = ".....No records....."
        await event.respond(message)

async def query_user_tag_film(event, id_nnm, id_user):
    ''' User tag film '''
    res=db_get_tag( id_nnm, id_user )
    if res:
       await event.answer('Film already in database!', alert=True) #FIXME Me be remove alert=True need test
       logging.info(f"User tag film but already in database id_nnm={data} with result={res}")
       return
    res=db_add_tag( id_nnm, SETTAG, id_user )
    logging.info(f"User tag film id_nnm={data} with result={res}")
    bdata = 'TAG'+data
    await event.answer('Film add to database', alert=True) #FIXME Me be remove alert=True need test
    
def main_bot():
    ''' Loop for bot connection '''

    # Connect to Telegram
    if use_proxy:
        prx = re.search('(^.*)://(.*):(.*$)', proxies.get('http'))
        bot = TelegramClient(session_bot, api_id, api_hash, system_version=system_version, proxy=(
            prx.group(1), prx.group(2), int(prx.group(3)))).start(bot_token=mybot_token)
    else:
        bot = TelegramClient(session_bot, api_id, api_hash, system_version=system_version).start(bot_token=mybot_token)

    bot.start()
    try:
        Channel_my_id = bot.loop.run_until_complete(bot.get_peer_id(Channel_my))
    except Exception as BotMethodInvalidError:
        logging.error("Bot can't access get channel ID  by {Cahnnel_my}.\n Please change Channel_my on digital notation!\n")
        logging.error("Original Error is: {BotMethodInvalidError}")
        print("Bot can't access get channel ID  by {Cahnnel_my}.\n Please change Channel_my on digital notation!\n")
        bot.disconnect()
        return None

    # Get reaction user on inline Buttons
    @bot.on(events.CallbackQuery(chats=[PeerChannel(Channel_my_id)]))
    async def callback(event):
        logging.debug(f"Get callback event on channel {Channel_my}: {event}")
        # Check user rights
        ret = await check_user(event.query.peer, event.query.user_id, event)
        if ret == USER_NEW: await event.answer('Sorry you are not registered user. You can only set Reaction.', alert=True)
        # Stop handle this event other handlers
        raise StopPropagation
        button_data = event.data.decode()
        if button_data.find('XX', 0, 2) != -1:
           # Add to Film to DB and remove Button 'Add to DB'
           data = button_data
           data = data.replace('XX', '')
           logging.info(f"Button 'Add...' pressed data={button_data} write {data}")
           await query_user_tag_film(event, data, event.query.user_id)
           raise StopPropagation

    # Attach inline button to new film message
    @bot.on(events.NewMessage(chats=[PeerChannel(Channel_my_id)], pattern=filter))
    async def normal_handler(event):
        logging.debug(f"Get NewMessage event: {event}\nEvent message:{event.message}")
        # Add button 'Add Film to database' as inline button for message
        await query_add_button(event, event.message.id, bot_name)
        raise StopPropagation  # Stop handle this event other handlers

    # Handle messages in bot chat
    @bot.on(events.NewMessage())
    async def bot_handler(event_bot):
        logging.debug(f"Get NewMessage event_bot: {event_bot}")
        menu_level = 0
        #user = event_bot.message.peer_id.user_id
        ret = await check_user(PeerChannel(Channel_my_id), event_bot.message.peer_id.user_id, event_bot)
       
        if ret == USER_NEW:     # New user
             await create_yes_no_bot('**Y realy want tag/untag films**', event_bot)
             return
        elif ret == USER_BLOCKED:   # Blocked
             await evant_bot.answer('Sorry You are Blocked!\n Send message to Admin Channel.', Alert=True)
             return
        elif ret == USER_READ: menu_level = MENU_USER_READ# FIXME no think # Only View
        elif ret == USER_READ_WRITE: menu_level = MENU_USER_READ_WRITE # Admin
        elif ret == USER_SUPERADMIN: menu_level = MENU_SUPERADMIN # SuperUser
       
        if event_bot.message.message == '/start':
          # show admin menu
          await create_menu_bot(menu_level, event_bot)

    # Handle basic Menu
    @bot.on(events.CallbackQuery())
    async def callback_bot(event_bot):
        logging.debug(f"Get callback event_bot {event_bot}")
        id_user = event_bot.query.user_id

        button_data = event_bot.data.decode()
        await event_bot.delete()
        send_menu = 0
        ret = await check_user(PeerChannel(Channel_my_id), id_user, event_bot)
        #Stop handle this event other handlers
        #raise StopPropagation
       
        if ret == USER_BLOCKED:   # Blocked
          await event_bot.answer('Sorry You are Blocked!\n Send message to Admin Channel.', Alert=True)
          return
        elif ret == USER_READ: menu_level = MENU_USER_READ# FIXME no think # Only View
        elif ret == USER_READ_WRITE: menu_level = MENU_USER_READ_WRITE # Admin
        elif ret == USER_SUPERADMIN: menu_level = MENU_SUPERADMIN # SuperUser
        
        if ret == USER_NEW and button_data == '/yes':
            # Add new user to db and set min rights and block
            user_ent = await bot.get_entity(id_user)
            name_user = user_ent.username
            if name_user == None: name_user = user_ent.first_name
            logging.debug(f"Get username for id {id_user}: {name_user}")
            await query_add_user(id_user, name_user, event_bot)
            send_menu = 0
            return
        elif button_data == '/no':
            # Say goodbye
            await event_bot.respond('Goodbye! See you later...')
            send_menu = 0
            return
        if button_data == '/lur':
            #Approve waiting users
            await query_wait_users(event_bot)
            send_menu = 1
        if  button_data.find('ENABLE', 0, 6) != -1:
            data = button_data
            id_user_approve = data.replace('ENABLE', '')
            #Approve waiting users
            logging.info(f"Approve waiting users: user={id_user_approve}")
            db_ch_rights_user(id_user_approve, USER_UNBLOCKED, USER_READ_WRITE)
            send_menu = 1
        if button_data == '/dblist':  # Not Use now
            # Get all database, Use with carefully may be many records
            await query_all_records(event_bot)
            send_menu = 1
        elif button_data == '/dwlist':
            # Get films tagget for download
            await query_tagged_records(id_user, SETTAG, event_bot)
            send_menu = 1
        elif button_data == '/dwclear':
            # Clear all tag for download
            await db_switch_user_tag( id_user, UNSETTAG )
            send_menu = 1
        elif button_data == '/dwearly':
            # Get films tagget early for download
            await query_tagged_records(id_user, UNSETTAG, event_bot)
            send_menu = 1
        elif button_data == '/dbinfo':
            # Get info about DB
            await query_info_db(event_bot)
            send_menu = 1
        elif button_data == '/s':
            # search Films
            await event_bot.respond("Write and send what you search:")
            send_menu = 0

            @bot.on(events.NewMessage())
            async def search_handler(event_search):
                logging.info(f"Get search string: {
                             event_search.message.message}")
                await query_search(event_search.message.message, event_bot)
                await event_bot.respond("🏁............Done............🏁")
                bot.remove_event_handler(search_handler)
                await create_menu_bot(menu_level, event_bot)

        if send_menu:
            await event_bot.respond("🏁............Done............🏁")
            await create_menu_bot(menu_level, event_bot)

    return bot


def main_client():
    ''' Loop for client connection '''

    # -------------- addition info vars
    Id = ["Название:", "Производство:", "Жанр:", "Режиссер:",
          "Актеры:", "Описание:", "Продолжительность:", "Качество видео:",
          "Перевод:", "Язык озвучки:", "Субтитры:", "Видео:", "Аудио 1:",
          "Аудио 2:", "Аудио 3:", "Скриншоты:", "Время раздачи:"]

    url = post_body = rating_url = []
    mydict = {}

    # Connect to Telegram
    if use_proxy:
        prx = re.search('(^.*)://(.*):(.*$)', proxies.get('http'))
        client = TelegramClient(session_client, api_id, api_hash, system_version=system_version, proxy=(
            prx.group(1), prx.group(2), int(prx.group(3))))
    else:
        client = TelegramClient(session_client, api_id,
                                api_hash, system_version=system_version)

    client.start()
    Channel_my_id = client.loop.run_until_complete(client.get_peer_id(Channel_my))
    Channel_mon_id = client.loop.run_until_complete(client.get_peer_id(Channel_mon))

    # Parse channel NNMCLUB for Films

    @client.on(events.NewMessage(chats=[PeerChannel(Channel_mon_id)], pattern=filter))
    async def normal_handler(event):

        logging.debug(f"Get new message in NNMCLUB Channel: {event.message}")
        msg = event.message

        url_tmpl = re.compile(r'viewtopic.php\?t')
        # Get URL nnmclub page with Film
        for url_entity, inner_text in msg.get_entities_text(MessageEntityTextUrl):
            if url_tmpl.search(url_entity.url):
                url = url_entity.url

        logging.info(f"Get URL nnmclub page with Film: {url}")

        # if URL exist get additional info for film
        if url:
            try:
                page = requests.get(url, proxies=proxies)
                if page.status_code != 200:
                    logging.error(f"Can't open url:{
                                  url}, status:{page.status}")
                    return
            except Exception as ConnectionError:
                logging.error(f"Can't open url:{
                              url}, status:{ConnectionError}")
                logging.error(
                    f"May be you need use proxy? For it set use_proxy=1 in config file.")
                client.disconnect()
                return

            logging.debug(f"Getted URL nnmclub page with status code: {
                          page.status_code}")
            soup = BeautifulSoup(page.text, 'html.parser')

            # Select data where class - postbody
            post_body = soup.find(class_='postbody')
            text = post_body.get_text('\n', strip='True')

            kpr_tmpl = re.compile('www.kinopoisk.ru/rating')
            # Get url picture with rating Film on Kinopoisk site
            for a_hr in post_body.find_all(class_='postImg'):
                rat = a_hr.get('title')
                if kpr_tmpl.search(rat):
                    rating_url = rat

            k = Id[0]
            v = ""

            desc_tmpl = re.compile(':$')
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
            f_tmpl = re.compile('film/(.+?)/')
            t_tmpl = re.compile('title/(.+?)/')
            for a_hr in post_body.find_all('a'):
                rat = a_hr.get('href')
                if rat.find('https://www.kinopoisk.ru/film/') != -1:
                    id_kpsk = f_tmpl.search(rat).group(1)
                    kpsk_url = 'https://rating.kinopoisk.ru/'+id_kpsk+'.xml'
                    logging.info(
                        f"Create url rating from kinopoisk: {kpsk_url}")
                elif rat.find('https://www.imdb.com/title/') != -1:
                    id_imdb = t_tmpl.search(rat).group(1)
                    imdb_url = rat.replace(
                        '?ref_=plg_rt_1', 'ratings/?ref_=tt_ov_rt')
                    logging.info(f"Create url rating from imdb: {imdb_url}")

            id_nnm = re.search('viewtopic.php.t=(.+?)$', url).group(1)

            if db_exist_Id(id_kpsk, id_imdb):
                logging.info(f"Film {id_nnm} exist in db - end analize.")
                return

            # Get rating film from kinopoisk if not then from imdb site
            if kpsk_url:
                rat_url = kpsk_url
                page = requests.get(
                    rat_url, headers={'User-Agent': 'Mozilla/5.0'}, proxies=proxies)
                # Parse data
                # FIXME me be better use xml.parser ?
                soup = BeautifulSoup(page.text, 'html.parser')
                try:
                    rating_xml = soup.find('rating')
                    kpsk_r = rating_xml.find(
                        'kp_rating').get_text('\n', strip='True')
                    imdb_r = rating_xml.find(
                        'imdb_rating').get_text('\n', strip='True')
                    logging.info(f"Get rating from kinopoisk: {kpsk_url}")
                except:
                    logging.info(f"No kinopoisk rating on site")
            elif imdb_url:
                rat_url = imdb_url
                page = requests.get(
                    rat_url, headers={'User-Agent': 'Mozilla/5.0'}, proxies=proxies)
                # Parse data
                soup = BeautifulSoup(page.text, 'html.parser')
                post_body = soup.find(class_='sc-5931bdee-1 gVydpF')
                imdb_r = post_body.get_text('\n', strip='True')
                logging.info(f"Get rating from imdb: {imdb_url}")
            else:
                kpsk_r = "-"
                imdb_r = "-"

        logging.info(f"Add info to message")
        film_add_info = f"\n_________________________________\nРейтинг: КП[{kpsk_r}] Imdb[{
            imdb_r}]\n{Id[2]} {mydict.get(Id[2])}\n{Id[5]}\n{mydict.get(Id[5])}"

        msg.message = msg.message+film_add_info

        if len(msg.message) > 1023:
            msg.message = msg.message[:1019]+'...'

        try:
            async with db_lock:
                if db_exist_Id(id_kpsk, id_imdb):
                    logging.info(f"Check for resolve race condition: Film {
                                 id_nnm} exist in db - end analize.")
                else:
                    send_msg = await client.send_message(PeerChannel(Channel_my_id), msg, parse_mode='md')
                    db_add_film(send_msg.id, id_nnm, url,
                                mydict[Id[0]], id_kpsk, id_imdb)
                    logging.info(f"Film not exist in db - add and send, id_kpsk={
                                 id_kpsk} id_imdb={id_imdb} id_nnm:{id_nnm}\n")
                    logging.debug(f"Send Message:{send_msg}")
        except errors.BadRequestError as error:
            logging.error(f'Error db_lock: {error}')

    return client


# main()
print('Start bot.')

get_config(cfg)
db_lock = asyncio.Lock()

# Enable logging
logging.basicConfig(level=log_level, filename=logfile,
                    filemode="a", format="%(asctime)s %(levelname)s %(message)s")
logging.info(f"Start bot.")


connection = sqlite3.connect(db_name)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

db_init()

bot = main_bot()
if bot:
    client = main_client()
    client.run_until_disconnected()

connection.close()
logging.info(f"End.\n--------------------------")
print('End.')
