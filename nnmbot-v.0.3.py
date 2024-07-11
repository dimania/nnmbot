#!/usr/bin/python3
#
# Telegram Bot for filter films from NNMCLUB channel
# version 0.3
# load config file
#!!!!!!!! Replace with you config file here !!!!!!!
# replace myconfig with config by example
# --------------------------------
import myconfig as cfg
# --------------------------------

from telethon import TelegramClient, events, utils
from telethon.tl.types import PeerChat, PeerChannel, PeerUser, MessageEntityTextUrl, MessageEntityUrl
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
import sys
import gettext
import io
#import nnm_module as db

#-----------------
# CONSTANT
#
DEFTAG = 0
SETTAG = 1
UNSETTAG = 2

USER_ACTIVE = 1
USER_BLOCKED = 0
USER_SUPERADMIN = 4

USER_READ_WRITE = 3
USER_READ = 2
USER_NO_RIGHTS=0
USER_NEW = 1

MENU_USER_READ = 0
MENU_USER_READ_WRITE = 1
MENU_SUPERADMIN = 2

BASIC_MENU = 1
CUSER_MENU = 2
CURIGHTS_MENU = 3
NO_MENU = 0

LIST_REC_IN_MSG = 20
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
      mag_link TEXT DEFAULT NULL,
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
      tag INTEGER DEFAULT 0,
      FOREIGN KEY (id_user)
      REFERENCES Users (id_user)
        ON DELETE CASCADE
       )
      ''')

    connection.commit()

def db_add_film(id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, mag_link):
    ''' Add new Film to database '''
    cur_date = datetime.now()
    cursor.execute("INSERT INTO Films (id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, mag_link, date) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                   (id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, mag_link, cur_date))
    connection.commit()

def db_exist_Id(id_kpsk, id_imdb):
    ''' Test exist Film in database '''
    if id_kpsk == 0: 
      cursor.execute("SELECT 1 FROM Films WHERE id_imdb = ?", (id_imdb,))
    elif id_imdb == 0:
      cursor.execute("SELECT 1 FROM Films WHERE id_kpsk = ?", (id_kpsk,))
    else:
      cursor.execute("SELECT 1 FROM Films WHERE id_kpsk = ? OR id_imdb = ?", (id_kpsk, id_imdb))
     
    return cursor.fetchone()

def db_info( id_user ):
    ''' Get Info database: all records, tagged records and tagged early records for user '''
    cursor.execute("SELECT COUNT(*) FROM Films UNION ALL SELECT COUNT(*) FROM Ufilms WHERE tag = ? AND id_user = ? UNION ALL SELECT COUNT(*) FROM Ufilms WHERE tag = ? AND id_user = ?", (SETTAG, id_user, UNSETTAG, id_user,) )
    rows = cursor.fetchall()
    return rows

def db_list_all():
    ''' List all database '''
    cursor.execute('SELECT  * FROM Films')
    rows = cursor.fetchall()
    return rows

def db_search(str_search):
    ''' Search in db '''
    str_search = '%'+str_search+'%'
    cursor.execute(
        "SELECT name,nnm_url FROM Films WHERE name LIKE ? COLLATE NOCASE", (str_search,))
    rows = cursor.fetchall()
    return rows

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
        cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE id_user = ? AND active = ? AND rights = ?", (id_user, active, rights,))
    elif id_user is not None and active is not None:
        cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE id_user = ? AND active = ?", (id_user, active,))
    elif id_user is not None and rights is not None:
        cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE id_user = ? AND rights = ?", (id_user, rights,))
    elif active is not None and rights is not None:
        cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE active = ? AND rights = ?", (active, rights,))
    elif id_user is not None:
        cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE id_user = ?", (id_user,))
    elif active is not None:
        cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE active = ?", (active,))
    elif rights is not None:
        cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE rights = ?", (rights,))
    else:            
        cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users")
             
    rows = cursor.fetchall()
    
    logging.debug(f"SELECT USERS: id_user={id_user} active={active}, rights={rights} result={len(rows)}" )
    return rows

def db_list_tagged_films( id_user=None, tag=SETTAG ):
    ''' List only records with set tag '''
    cursor.execute("SELECT name,nnm_url,mag_link FROM Films WHERE id IN (SELECT id_Films FROM Ufilms WHERE id_user=? and tag=?)", (id_user,tag,))
    rows = cursor.fetchall()
    return rows

def db_add_tag( id_nnm, tag, id_user ):
    ''' User first Tag film in database '''
    cur_date=datetime.now()
    cursor.execute("INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (?,(SELECT id FROM Films WHERE id_nnm=?),?,?)",
                  (id_user,id_nnm,cur_date,tag))
    
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
    cursor.execute("UPDATE Ufilms SET tag=? WHERE id_user = ?", (tag,id_user))
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
    await send_lists_records( rows, LIST_REC_IN_MSG, event )
    
async def query_search(str_search, event):
    ''' Search Films in database '''
    logging.info(f"Search in database:{str_search}")
    rows = db_search(str_search)
    await send_lists_records( rows, LIST_REC_IN_MSG, event )
    
async def query_tagged_records(id_user, tag, event):
    ''' Get films tagget for user '''
    logging.info(f"Query db records with set tag")
    rows = db_list_tagged_films( id_user=id_user, tag=tag )
    await send_lists_records( rows, LIST_REC_IN_MSG, event )
    
async def send_lists_records( rows, num, event ):
    ''' Create messages from  list records and send to channel 
        rows - list records {url,name,magnet_url}
        num - module how many records insert in one messag
        event - descriptor channel '''
    
    if rows:
        i = 0
        message=""
        for row in rows:
            message = message + f'{i+1}. <a href="{dict(row).get('nnm_url')}">{dict(row).get('name')}</a>\n'
            mag_link_str = dict(row).get('mag_link')
            if mag_link_str:
               message = message + f'<a href="{magnet_helper}+{mag_link_str}">🧲Примагнититься</a>\n'
            i = i + 1
            if not i%num:
               await event.respond(message, parse_mode='html', link_preview=0)
               message=""
        if i < 8 and i != 0: 
           await event.respond(message, parse_mode='html', link_preview=0) 
    else:
        message = _("😔 No records")
        await event.respond(message, parse_mode='html', link_preview=0)

async def query_clear_tagged_records(id_user, event):
    ''' Clear all tag for user '''
    logging.info(f"Query db for clear tag ")
    rows = db_switch_user_tag( UNSETTAG, id_user )
    if rows:
        message = 'Clear '+rows+' records'
    else:
        message = _("No records")
    await event.respond(message, parse_mode='html', link_preview=0)

async def query_db_info(event, id_user):
    ''' Get info about database records '''
    logging.info(f"Query info database for user {id_user}")
    rows = db_info(id_user)
    message = _("All records: ") + \
        str(rows[0][0])+_("\nTagged records: ") + \
        str(rows[1][0])+_("\nEarly tagged: ")+str(rows[2][0])
    await event.respond(message, parse_mode='html', link_preview=0)

async def query_add_user(id_user, name_user, event):
    ''' Add user to database '''
    logging.info(f"Add user to database ")
    res = db_add_user(id_user, name_user)
    if res:
        await event.respond(_("Yoy already power user!"))
    else:
        message = _("You request send to Admins, and will be reviewed soon.")
        await event.respond(message)
        #TODO Send message Admins if need

async def create_basic_menu(level, event):
    ''' Create basic menu control database '''
    logging.info(f"Create menu buttons")
    keyboard = [
        [
            Button.inline(_("List Films tagged"), b"/bm_dwlist")
        ],
        [
            Button.inline(_("List Films tagged early"), b"/bm_dwearly")
        ],
        [
            Button.inline(_("Clear all tagged Films"), b"/bm_dwclear")
        ],
        [
            Button.inline(_("Get database info "), b"/bm_dbinfo")
        ],
        [
            Button.inline(_("Search Films in database "), b"/bm_search")
        ]
    ]

    if level == MENU_SUPERADMIN:
       # Add items for SuperUser
       keyboard.append([Button.inline(_("List All Films in DB"), b"/bm_dblist")])
       keyboard.append([Button.inline(_("Go to control users menu"), b"/bm_cum")])
       

    await event.respond(_("**☣ Work with database:**"), parse_mode='md', buttons=keyboard)

async def create_control_user_menu(level, event):
    ''' Create menu of control users '''
    logging.info(f"Create control user menu buttons")
    keyboard = [
        [
            Button.inline(_("List user requests"), b"/cu_lur")
        ],
        [
            Button.inline(_("List all users"), b"/cu_lar")
        ],
        [
            Button.inline(_("Block/Unblock user"), b"/cu_buu")
        ],
        [
            Button.inline(_("Change rights user"), b"/cu_cur")
        ],
        [
            Button.inline(_("Delete user"), b"/cu_du")
        ]
        ,
        [
            Button.inline(_("Back to basic menu"), b"/cu_bbm")
        ]
    ]

    await event.respond(_("**☣ Work with users:**"), parse_mode='md', buttons=keyboard)

async def create_rights_user_menu(level, event, id_user):
    ''' Create menu for change rights users '''
    logging.info(f"Create menu for change rights users menu buttons")

    keyboard = [
        [
            Button.inline(_("Set Read only"), b"/cr_ro"+str.encode(id_user))
        ],
        [
            Button.inline(_("Set Read Write"), b"/cr_rw"+str.encode(id_user))
        ],
        [
            Button.inline(_("Back to users menu"), b"/cr_bum")
        ]
    ]
    #await event.respond(_("Select user for change rights"))
    await event.respond(_("**☣     Select rights:    **"), parse_mode='md', buttons=keyboard)

async def create_yes_no_dialog(question, event):
    ''' Create yes or no buttons with text '''
    logging.debug(f"Create yes or no buttons")
    keyboard = [
        [
            Button.inline(_("Yes"), b"/yes"),
            Button.inline(_("No"), b"/no")
        ]
    ]
    # await bot.send_message(PeerChannel(Channel_my_id),_("Work with database"), buttons=keyboard)
    await event.respond(question, parse_mode='md', buttons=keyboard)

async def check_user(channel, user, event):
    ''' Check right of User '''
    logging.debug(f"Try Get permissions for channe={channel} user={user}")
    
    try:
      permissions = await bot.get_permissions(channel, user)
      if permissions.is_admin:
        return USER_SUPERADMIN # Admin
    except:
      logging.error(f"Can not get permissions for channe={channel} user={user}. Possibly user not join to group but send request for Control")  
    
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
            button.append([ Button.inline(message, bdata)])
        await event.respond(_("List awaiting users:"), buttons=button)    
    else:
        message = _(".....No records.....")
        await event.respond(message)

async def query_all_users(event, bdata_id, message):
    ''' Get list all users '''     
    rows = db_list_users()
    logging.debug(f"Get all users result={len(rows)}")
    button=[]
    if rows:
        for row in rows:
            status = "" 
            id_user = dict(row).get('id_user')
            user_name = dict(row).get('name_user')
            active = dict(row).get('active')
            rights = dict(row).get('rights')
            date = dict(row).get('date')
            if active == USER_ACTIVE:
               status = status+'🇦 '
            if active == USER_BLOCKED:
               status = status+'🇧 '
            if rights == USER_READ_WRITE:
               status = status+'🇷 🇼 '
            if rights == USER_READ:
               status = status+'🇷 '
            #2024-03-03 11:46:05.488155
            dt = datetime.strptime(date,'%Y-%m-%d %H:%M:%S.%f')
            date = dt.strftime('%d-%m-%y %H:%M')
            logging.info(f"Get user username={user_name} status={status} date={date}",)
            bdata=bdata_id+id_user
            button.append([ Button.inline(user_name+' '+status+' '+date , bdata)])
        await event.respond(message, buttons=button)
    else:
        message = _(".....No records.....")
        await event.respond(message)

async def query_user_tag_film(event, id_nnm, id_user):
    ''' User tag film '''
    res=db_get_tag( id_nnm, id_user )
    if res:
       await event.answer(_('Film already in database!'), alert=True)
       logging.info(f"User tag film but already in database id_nnm={id_nnm} with result={res}")
       return
    res=db_add_tag( id_nnm, SETTAG, id_user )
    logging.info(f"User {id_user} tag film id_nnm={id_nnm} with result={res}")
    #bdata = 'TAG'+id_nnm
    await event.answer(_('Film added to database'), alert=True)
  
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

    # Get reaction user on inline Buttons in Channel
    @bot.on(events.CallbackQuery(chats=[PeerChannel(Channel_my_id)]))
    async def callback(event):
        logging.debug(f"Get callback event on channel {Channel_my}: {event}")
        # Check user rights
        ret = await check_user(event.query.peer, event.query.user_id, event)
        
        if ret == USER_NEW: 
            await event.answer(_('Sorry you are not registered user.\nYou can only set Reaction.\nYou can register, press [Control] button.'), alert=True)
            # Stop handle this event other handlers
            raise StopPropagation
        elif ret == USER_BLOCKED:   # Blocked
            await event.answer(_('Sorry You are Blocked!\n Send message to Admin this channel'), alert=True)
            # Stop handle this event other handlers
            raise StopPropagation
        button_data = event.data.decode()
        if button_data.find('XX', 0, 2) != -1:
           # Add to Film to DB 
           data = button_data
           data = data.replace('XX', '')
           logging.info(f"Button 'Add...' pressed data={button_data} write {data}")
           await query_user_tag_film(event, data, event.query.user_id)
           raise StopPropagation

    # Handle messages in bot chat
    @bot.on(events.NewMessage())
    async def bot_handler(event_bot):
        logging.debug(f"Get NewMessage event_bot: {event_bot}")
        menu_level = 0
        #user = event_bot.message.peer_id.user_id
        try:
            ret = await check_user(PeerChannel(Channel_my_id), event_bot.message.peer_id.user_id, event_bot)
        except Exception as error:
            print(f"Error get user: {error}")
            return
        
        if ret == USER_NEW:     # New user
            await create_yes_no_dialog(_('**Y realy want tag/untag films**'), event_bot)
            return
        elif ret == USER_BLOCKED:   # Blocked
            await event_bot.respond(_('Sorry You are Blocked!\n Send message to Admin this channel'))
            return
        elif ret == USER_READ: menu_level = MENU_USER_READ# FIXME no think # Only View?
        elif ret == USER_READ_WRITE: menu_level = MENU_USER_READ_WRITE # Admin
        elif ret == USER_SUPERADMIN: menu_level = MENU_SUPERADMIN # SuperUser
       
        if event_bot.message.message == '/start':
          # show admin menu
          await create_basic_menu(menu_level, event_bot)
         
            
    # Handle basic Menu
    @bot.on(events.CallbackQuery())
    async def callback_bot(event_bot):
        logging.debug(f"Get callback event_bot {event_bot}")
        id_user = event_bot.query.user_id

        button_data = event_bot.data.decode()
        await event_bot.delete()               #Delete previous message (prev menu)
        send_menu = MENU_USER_READ
        ret = await check_user(PeerChannel(Channel_my_id), id_user, event_bot)
        #Stop handle this event other handlers
        #raise StopPropagation
       
        if ret == USER_BLOCKED:   # Blocked
          #await event_bot.respond(_('Sorry You are Blocked!\nSend message to Admin this channel.'))
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
            user_ent = await bot.get_input_entity(admin_name)
            await bot.send_message(user_ent,_("New user **")+name_user+_("** request approve."),parse_mode='md')
            send_menu = NO_MENU
            return
        elif button_data == '/no':
            # Say goodbye
            await event_bot.respond(_('Goodbye! See you later...'))
            send_menu = NO_MENU
            return
        
        if button_data == '/bm_dblist':  
            # Get all database, Use with carefully may be many records
            await query_all_records(event_bot)
            send_menu = BASIC_MENU
        elif button_data == '/bm_dwlist':
            # Get films tagget
            await query_tagged_records(id_user, SETTAG, event_bot)
            send_menu = BASIC_MENU
        elif button_data == '/bm_dwclear':
            # Clear all tag 
            res=db_switch_user_tag( id_user, UNSETTAG )
            await event_bot.respond(_("  Clear ")+res+_(" records  "))
            send_menu = BASIC_MENU
        elif button_data == '/bm_dwearly':
            # Get films tagget early
            await query_tagged_records(id_user, UNSETTAG, event_bot)
            send_menu = BASIC_MENU
        elif button_data == '/bm_dbinfo':
            # Get info about DB
            await query_db_info(event_bot,id_user)
            send_menu =BASIC_MENU
        elif button_data == '/bm_search':
            # Search Films
            await event_bot.respond(_("Write and send what you search:"))
            send_menu = NO_MENU
            @bot.on(events.NewMessage()) 
            async def search_handler(event_search):
                logging.info(f"Get search string: {event_search.message.message}")
                await query_search(event_search.message.message, event_bot)
                await event_bot.respond(_("🏁............Done............🏁"))
                bot.remove_event_handler(search_handler)
                await create_basic_menu(menu_level, event_bot)
        elif button_data == '/bm_cum':
            # Go to control users menu 
            send_menu = CUSER_MENU
        elif button_data == '/cu_bbm':
            # Back to basic menu 
            send_menu = BASIC_MENU
        elif button_data == '/cu_lur':
            # Approve waiting users
            await query_wait_users(event_bot)
            send_menu = CUSER_MENU
        elif button_data.find('ENABLE', 0, 6) != -1:
            data = button_data
            id_user_approve = data.replace('ENABLE', '') #FIXME change id_user_approve id_user
            # Approve waiting users
            logging.info(f"Approve waiting users: user={id_user_approve}")
            db_ch_rights_user(id_user_approve, USER_ACTIVE, USER_READ_WRITE)
            user_db=db_exist_user(id_user_approve)
            user_name=dict(user_db[0]).get('name_user')
            await event_bot.respond(_("User: ")+user_name+_(" add to DB"))
            #Send message to user
            await bot.send_message(PeerUser(int(id_user_approve)),_("You request approved\nNow Yoy can work with films."))
            send_menu = CUSER_MENU
        elif button_data == '/cu_lar':
            # Approve waiting users
            await query_all_users(event_bot,'INFO',_('List current users:'))
            send_menu = CUSER_MENU
        elif button_data == '/cu_du':
            # List user for select 4 delete
            await query_all_users(event_bot,'DELETE',_('Select user for delete:'))
            send_menu = CUSER_MENU   
        elif button_data.find('DELETE', 0, 6) != -1:
            # Get user for delete
            data = button_data
            id_user_delete = data.replace('DELETE', '') #FIXME change id_user_delete id_user
            user_db=db_exist_user(id_user_delete)
            user_name=dict(user_db[0]).get('name_user')
            logging.info(f"Delete users: user={id_user_delete}")
            db_del_user(id_user_delete)
            await event_bot.respond(_("User: ")+user_name+_(" deleted from DB"))
            send_menu = CUSER_MENU   
        elif button_data == '/cu_cur':
            # Change rights user
            await query_all_users(event_bot,'RIGHTS',_('Select user for change rights:'))
            send_menu = NO_MENU
        elif button_data.find('RIGHTS', 0, 6) != -1:
            data = button_data
            id_user = data.replace('RIGHTS', '')
            logging.info(f"Change rights for user={id_user}")
            user_db=db_exist_user(id_user)
            user_name=dict(user_db[0]).get('name_user')
            await event_bot.respond(_("Change righst for user: ")+user_name)
            send_menu = CURIGHTS_MENU
        elif button_data.find('/cr_ro', 0, 7) != -1:
            #Change to RO
            data = button_data
            id_user = data.replace('/cr_ro', '')
            db_ch_rights_user( id_user, USER_ACTIVE, USER_READ )
            logging.info(f"Change rights RO for user={id_user}")
            send_menu = CUSER_MENU
        elif button_data.find('/cr_rw', 0, 7) != -1:
            #Change to RW
            data = button_data
            id_user = data.replace('/cr_rw', '')
            db_ch_rights_user( id_user, USER_ACTIVE, USER_READ_WRITE )
            logging.info(f"Change rights RW for user={id_user}")
            send_menu = CUSER_MENU
        elif button_data == '/cu_buu':
            # Block/Unblock user
            await query_all_users(event_bot,'BLOCK_UNBLOCK',_('Select user for block/unblock:'))
            send_menu = NO_MENU
        elif button_data.find('BLOCK_UNBLOCK', 0,13 ) != -1:
            data = button_data
            id_user = data.replace('BLOCK_UNBLOCK', '')
            user_db=db_exist_user(id_user)
            user_name=dict(user_db[0]).get('name_user')
            active=dict(user_db[0]).get('active')
            if active == USER_BLOCKED:
              logging.info(f"Unblock user={id_user}")
              db_ch_rights_user( id_user, USER_ACTIVE, USER_READ_WRITE )
              user_db=db_exist_user(id_user_approve)
              await event_bot.respond(_("User: ")+user_name+_(" Unblocked"))
            else:
              logging.info(f"Block user={id_user}")
              db_ch_rights_user( id_user, USER_BLOCKED, USER_READ_WRITE )
              await event_bot.respond(_("User: ")+user_name+_(" Blocked"))
            send_menu = CUSER_MENU
            #Back to user menu

        if send_menu == BASIC_MENU:
            #await event_bot.respond(_("🏁............Done............🏁"))
            await create_basic_menu(menu_level, event_bot)
        elif send_menu == CUSER_MENU:
            #await event_bot.respond(_("🏁............Done............🏁"))
            await create_control_user_menu(menu_level, event_bot)
        elif send_menu == CURIGHTS_MENU:
            #await event_bot.respond(_("🏁............Done............🏁"))
            await create_rights_user_menu(menu_level, event_bot, id_user)


    return bot


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
    if use_proxy:
        prx = re.search('(^.*)://(.*):(.*$)', proxies.get('http'))
        client = TelegramClient(session_client, api_id, api_hash, system_version=system_version, proxy=(
            prx.group(1), prx.group(2), int(prx.group(3))))
    else:
        client = TelegramClient(session_client, api_id, api_hash, system_version=system_version)

    client.start()
    Channel_my_id = client.loop.run_until_complete(client.get_peer_id(Channel_my))
    Channel_mon_id = client.loop.run_until_complete(client.get_peer_id(Channel_mon))

    # Parse channel NNMCLUB for Films

    @client.on(events.NewMessage(chats=[PeerChannel(Channel_mon_id)], pattern=filter))
    async def normal_handler(event):
        url = post_body = rating_url = []
        mydict = {}
        logging.debug(f"Get new message in NNMCLUB Channel: {event.message}")
        msg = event.message

        # OLD NNM url parser 
        #                       viewtopic.php?t
        # Get URL nnmclub page with Film
        #for url_entity, inner_text in msg.get_entities_text(MessageEntityTextUrl):
        #    logging.debug(f"Urls: {url_entity}")
        #    if url_tmpl.search(url_entity.url):
        #        url = url_entity.url
        
        for url_entity, inner_text in msg.get_entities_text(MessageEntityUrl):
            logging.debug(f"Urls: {url_entity, inner_text}")
            if url_tmpl.search(inner_text):
                url = inner_text
        logging.info(f"Get URL nnmclub page with Film: {url}")
       
        # if URL not exist return 
        if not url:
           return
          
        try:
            page = requests.get(url, proxies=proxies)
            if page.status_code != 200:
                logging.error(f"Can't open url:{url}, status:{page.status}")
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

        if db_exist_Id(id_kpsk, id_imdb):
            logging.info(f"Film id_kpsk={id_kpsk} id_imdb={id_imdb} id_nnm={id_nnm} exist in db - end analize.")
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
                kpsk_r = rating_xml.find('kp_rating').get_text('\n', strip='True')
                imdb_r = rating_xml.find('imdb_rating').get_text('\n', strip='True')
                logging.info(f"Get rating from kinopoisk: {kpsk_url}")
            except:
                logging.info(f"No kinopoisk rating on site")
        elif imdb_url:
            rat_url = imdb_url
            page = requests.get(rat_url, headers={'User-Agent': 'Mozilla/5.0'}, proxies=proxies)
            # Parse data
            soup = BeautifulSoup(page.text, 'html.parser')
            post_body = soup.find(class_='sc-5931bdee-1 gVydpF')
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
        # Create buttons for message
        bdata = 'XX'+id_nnm
        buttons_film = [
                Button.inline(_("Add Film"), bdata),
                Button.url(_("Control"), 't.me/'+bot_name+'?start')
                ]
        # get photo from nnm message and create my photo
        film_photo = await client.download_media(msg, bytes)
        file_photo = io.BytesIO(film_photo)
        file_photo.name = "image.jpg" 
        file_photo.seek(0)  # set cursor to the beginning
        logging.debug(f"Message Photo{film_photo}")
        
        # Create new message 
        new_message = f"{film_name}{film_magnet_link}{film_section}{film_genre}{film_rating}{film_description}"
        logging.debug(f"New message:{new_message}")
        
        #trim long message
        if len(new_message) > 1023:
            new_message = new_message[:1019]+'...'

        try:
            async with db_lock:
                if db_exist_Id(id_kpsk, id_imdb):
                    logging.info(f"Check for resolve race condition: Film {id_nnm} exist in db - end analize.")
                else:
                    send_msg = await bot.send_file(PeerChannel(Channel_my_id), file_photo, caption=new_message, buttons=buttons_film, parse_mode="html" ) 
                    db_add_film(send_msg.id, id_nnm, url, mydict[Id[0]], id_kpsk, id_imdb, mag_link)
                    logging.info(f"Film not exist in db - add and send, name={mydict[Id[0]]} id_kpsk={id_kpsk} id_imdb={id_imdb} id_nnm:{id_nnm}\n")
                    logging.debug(f"Send Message:{send_msg}")
        except Exception as error:
            logging.error(f'Error in block db_lock: {error}')
    return client


# main()
print('Start bot.')

get_config(cfg)

# Enable logging
logging.basicConfig(level=log_level, filename=logfile, filemode="a", format="%(asctime)s %(levelname)s %(message)s")
logging.info(f"Start bot.")

localedir = os.path.join(os.path.dirname(os.path.realpath(os.path.normpath(sys.argv[0]))), 'locales')

if os.path.isdir(localedir):
  translate = gettext.translation('nnmbot', localedir, [Lang])
  _ = translate.gettext
else: 
  logging.info(f"No locale dir for support langs: {localedir} \n Use default lang: Engilsh")
  def _(message): return message
 
db_lock = asyncio.Lock()

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
