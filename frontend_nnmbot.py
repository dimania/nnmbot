#!/usr/bin/python3
#
# Telegram Bot for filter films from NNMCLUB channel
# version 0.5
# Module frontend_nnmbot.py listen NNMCLUB channel,
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
from telethon.sessions import StringSession
from datetime import datetime, date, time, timezone
from bs4 import BeautifulSoup
from collections import OrderedDict
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
#from requests.packages.urllib3.util.retry import Retry
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

Channel_my_id = None

async def query_all_records(event):
    ''' 
        Get and send all database records, 
        Use with carefully may be many records 
    '''
    logging.info(f"Query all db records")
    rows = dbm.db_list_all()
    await send_lists_records( rows, sts.LIST_REC_IN_MSG, event )

async def query_all_records_by_one(event):
    ''' 
        Get and send all database records, 
        one by one wint menu.
        Use with carefully may be many records 
    '''
    logging.info(f"Query db records for  ")
    rows = dbm.db_list_all_id()
    ret = await show_card_one_record_menu( rows, event )
    return ret

async def query_search(str_search, event):
    ''' Search Films in database '''
    logging.info(f"Search in database:{str_search}")
    rows = dbm.db_search_old(str_search)
    await send_lists_records( rows, sts.LIST_REC_IN_MSG, event )
    
async def query_tagged_records_list(id_user, tag, event):
    ''' Get films tagget for user '''
    logging.info(f"Query db records with set tag")
    rows = dbm.db_list_tagged_films( id_user=id_user, tag=tag )
    await send_lists_records( rows, sts.LIST_REC_IN_MSG, event )

async def query_tagged_records_by_one(id_user, tag, event):
    ''' Get films tagget for user '''
    logging.info(f"Query db records with set tag")
    rows = dbm.db_list_tagged_films_id( id_user=id_user, tag=tag )
    ret = await show_card_one_record_menu( rows, event )
    return ret

async def show_card_one_record_menu( rows=None, event=None ):
    ''' Create card of one film and send to channel 
        rows - list id records 
        event - descriptor channel '''
    lenrows=len(rows)
    if rows:
        await send_card_one_record( dict(rows[0]).get("id"), 0, event )
        @bot.on(events.CallbackQuery())
        async def callback_bot_list(event_bot_list):
            logging.debug(f"Get callback event_bot_list {event_bot_list}")  
            button_data = event_bot_list.data.decode()
            await event_bot_list.delete()
            i=0
            if button_data.find('NEXT', 0, 4) != -1:
                i = int(button_data.replace('NEXT', '')) + 1 
                if i == lenrows:
                   i = 0
                await send_card_one_record( dict(rows[i]).get("id"), i, event )  
            if button_data.find('PREV', 0, 4) != -1:
                i = int(button_data.replace('PREV', '')) - 1
                if i == -1:
                   i = lenrows-1
                await send_card_one_record( dict(rows[i]).get("id"), i, event )
            if button_data == 'HOME_MENU':
                removed_handler=bot.remove_event_handler(callback_bot_list)
                logging.debug(f"Remove handler event_bot_list =  {removed_handler}") 
    else:
        message = _("😔 No records")
        await event.respond(message, parse_mode='html', link_preview=0)
        return 0           

async def publish_all_new_films():
    ''' Publish All films on channel which are not published '''
    print(f"publish_all")
    #Publish new Films
    rows=dbm.db_list_4_publish(sts.PUBL_NOT)
    print(f"publish_all publ_upd rows:{rows}")
    if rows:
       for row in rows:
         id=dict(row).get("id")
         await publish_new_film(id, sts.PUBL_NOT)
         #set to sts.PUBL_YES
         dbm.db_update_publish(id)
         await asyncio.sleep(1)
         
    #Publish updated Films
    rows=dbm.db_list_4_publish(sts.PUBL_UPD)
    print(f"publish_all publ_upd rows:{rows}")
    if rows:
       for row in rows:
         id=dict(row).get("id")
         await publish_new_film(id, sts.PUBL_UPD)
         #set to sts.PUBL_YES
         dbm.db_update_publish(id)
         await asyncio.sleep(1)

async def publish_new_film( id, rec_upd ):
    ''' Publish film on channel 
        id - number film in db
        rec_upd - was updated exist film'''

    row=dbm.db_film_by_id( id )
    film_name = f"<a href='{dict(row).get("nnm_url")}'>{dict(row).get("name")}</a>\n"
    film_section = f"🟢<b>Раздел:</b> \n{dict(row).get("section")}"
    film_genre = f"🟢<b>Жанр:</b> {dict(row).get("genre")}\n"
    film_rating = f"🟢<b>Рейтинг:</b> КП[{dict(row).get("rate_kpsk")}] Imdb[{dict(row).get("rate_imdb")}]\n"
    film_description = f"🟢<b>Описание:</b> \n{dict(row).get("description")}\n"
    image_nnm_url = dict(row).get("image_nnm_url")
    id_nnm = dict(row).get("id_nnm") 
    # if magnet link exist create string and href link
    mag_link = dict(row).get("mag_link")
    if mag_link:
        film_magnet_link = f"<a href='{sts.magnet_helper+mag_link}'>🧲Примагнититься</a>\n" 
    else:
        film_magnet_link=""
    bdata = 'XX'+id_nnm
    buttons_film = [
                Button.inline(_("Add Film"), bdata),
                Button.url(_("Control"), 't.me/'+sts.bot_name+'?start')
                ]

    # Create new message 
    new_message = f"{film_name}{film_magnet_link}{film_section}{film_genre}{film_rating}{film_description}"
    if rec_upd == sts.PUBL_UPD:
       new_message = f"🔄{new_message}" 

    #trim long message ( telegramm support only 1024 byte caption )
    if len(new_message) > 1023:
        new_message = new_message[:1019]+'...'

    # Send new message to Channel
    try:                
        send_msg = await bot.send_file(PeerChannel(Channel_my_id), image_nnm_url, caption=new_message, \
                buttons=buttons_film, parse_mode="html" )
    except errors.FloodWaitError as e:
        logging.info('Have to sleep', e.seconds, 'seconds')
        asyncio.sleep(e.seconds)

    logging.debug(f"Send new film Message:{send_msg}")
    
async def send_card_one_record( id, index, event ):
    ''' Create card of one film and send to channel 
        id - number film in db
        event - descriptor channel '''

    row=dbm.db_film_by_id( id )
    film_name = f"<b>{index+1}. </b><a href='{dict(row).get("nnm_url")}'>{dict(row).get("name")}</a>\n"
    film_section = f"🟢<b>Раздел:</b> \n{dict(row).get("section")}"
    film_genre = f"🟢<b>Жанр:</b> {dict(row).get("genre")}\n"
    film_rating = f"🟢<b>Рейтинг:</b> КП[{dict(row).get("rate_kpsk")}] Imdb[{dict(row).get("rate_imdb")}]\n"
    film_description = f"🟢<b>Описание:</b> \n{dict(row).get("description")}\n"
    # if magnet link exist create string and href link
    mag_link = dict(row).get("mag_link")
    if mag_link:
        film_magnet_link = f"<a href='{sts.magnet_helper+mag_link}'>🧲Примагнититься</a>\n" 
    else:
        film_magnet_link=""
    # Create buttons for message
    f_prev = 'PREV'+f'{index}'
    f_next = 'NEXT'+f'{index}'
    f_curr = 'HOME_MENU'
    buttons_film = [
            Button.inline(_("◀"), f_prev),
            Button.inline(_("◼"), f_curr),
            Button.inline(_("▶"), f_next)
            ]
    film_photo =  dict(row).get("image_nnm_url")
    if not film_photo:
        film_photo = dict(row).get("photo")
        logging.debug(f"Film_photo:{film_photo}")
        if film_photo != None:
            file_photo = io.BytesIO(film_photo)
            file_photo.name = "image.jpg" 
            file_photo.seek(0)  # set cursor to the beginning        
        else:
            file_photo='no_image.jpg' #FIXME
            logging.debug(f"File_photo:{file_photo}")
    
    # Create new message 
    new_message = f"{film_name}{film_magnet_link}{film_section}{film_genre}{film_rating}{film_description}"
    logging.debug(f"New message:{new_message}")
    #FIX ME as send? as respond or as send_file message
    #await event.respond(message, parse_mode='html', link_preview=0)
    logging.debug(f"Event:{event}")
    send_msg = await bot.send_file(event.original_update.peer, file_photo, caption=new_message, buttons=buttons_film, parse_mode="html" )
    
async def send_lists_records( rows, num_per_message, event ):
    ''' Create messages from  list records and send to channel 
        rows - list records {url,name,magnet_url}
        num_per_message - module how many records insert in one messag
        event - descriptor channel '''
    
    if rows:
        i = 0
        message=""
        for row in rows:
            message = message + f'{i+1}. <a href="{dict(row).get("nnm_url")}">{dict(row).get("name")}</a>\n'
            mag_link_str = dict(row).get("mag_link")
            if mag_link_str:
               message = message + f'<a href="{sts.magnet_helper}+{mag_link_str}">🧲Примагнититься</a>\n'
            i = i + 1
            if not i%num_per_message:
                try:
                    await event.respond(message, parse_mode='html', link_preview=0)
                except errors.FloodWaitError as e:
                    logging.info('Have to sleep', e.seconds, 'seconds')
                    asyncio.sleep(e.seconds)
                message=""
        if i%num_per_message:
            try: 
                await event.respond(message, parse_mode='html', link_preview=0) 
            except errors.FloodWaitError as e:
                    logging.info('Have to sleep', e.seconds, 'seconds')
                    asyncio.sleep(e.seconds)
    else:
        message = _("😔 No records")
        await event.respond(message, parse_mode='html', link_preview=0)

async def query_clear_tagged_records(id_user, event):
    ''' Clear all tag for user '''
    logging.info(f"Query db for clear tag ")
    rows = dbm.db_switch_user_tag( sts.UNSETTAG, id_user )
    if rows:
        message = _('Clear ')+rows+_(' records')
    else:
        message = _("No records")
    await event.respond(message, parse_mode='html', link_preview=0)

async def query_db_info(event, id_user):
    ''' Get info about database records '''
    logging.info(f"Query info database for user {id_user}")
    rows = dbm.db_info(id_user)
    message = _("All records: ") + \
        str(rows[0][0])+_("\nTagged records: ") + \
        str(rows[1][0])+_("\nEarly tagged: ")+str(rows[2][0])
    await event.respond(message, parse_mode='html', link_preview=0)

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

    if level == sts.MENU_SUPERADMIN:
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

async def create_choice_dialog(question, choice_buttons, event, level):
    ''' Create dialog for choice buttons with text question
        and run function when choice was 
        question = "Text message for choice"
        dict choice_buttons = {
            "button1": ["Yes", "_yes",func_show_sombody0,[arg1,arg2...], SHOW_OR_NOT_MENU (optional) ],
            "button2": ["No", "_no", func_show_sombody1,[arg1,arg2...]],
            "button3": ["Cancel", "_cancel", func_show_sombody0,[arg1,arg2...]]
        }
        event = bot event handled id
        level = user level for show menu exxtended or no
    '''
    logging.debug(f"Create choice buttons")
    button = []
    # Create butons and send to channel (choice dialog)
    for button_s in choice_buttons:
        button.append(Button.inline(choice_buttons[button_s][0], choice_buttons[button_s][1]))
    await event.respond(question, parse_mode='md', buttons=button)
    # Run hundler for dialog
    @bot.on(events.CallbackQuery())
    async def callback_bot_choice(event_bot_choice):
        logging.debug(f"Get callback event_bot_list {event_bot_choice}")  
        button_data = event_bot_choice.data.decode()
        await event.delete()
        #Get reaction and run some function from dict choice_buttons
        for button_press in choice_buttons:
            if button_data == choice_buttons[button_press][1]:
                removed_handler=bot.remove_event_handler(callback_bot_choice)
                logging.debug(f"Remove handler callback_bot_choice =  {removed_handler}")
                await choice_buttons[button_press][2](*choice_buttons[button_press][3])
                if sts.BASIC_MENU in choice_buttons[button_press]: #FIXME sts.BASIC_MENU in list may be or not accidentally?
                    await create_basic_menu(level, event)
        
async def check_user(channel, user, event):
    ''' Check right of User '''
    logging.debug(f"Try Get permissions for channe={channel} user={user}")
    
    try:
      permissions = await bot.get_permissions(channel, user)
      if permissions.is_admin:
        return sts.USER_SUPERADMIN # Admin
    except:
      logging.error(f"Can not get permissions for channe={channel} user={user}. Possibly user not join to group but send request for Control")  
    
    user_db = dbm.db_exist_user(user)
    ret = -1
    if not user_db:
      logging.debug(f"User {user} is not in db - new user")
      ret = sts.USER_NEW
      return ret
    elif dict(user_db[0]).get('active') == sts.USER_BLOCKED:
      logging.debug(f"User {user} is blocked in db")
      ret = sts.USER_BLOCKED
    elif dict(user_db[0]).get('rights') == sts.USER_READ:
      logging.debug(f"User {user} can only view in db")
      ret = sts.USER_READ
    elif dict(user_db[0]).get('rights') == sts.USER_READ_WRITE:
      logging.debug(f"User {user} admin in your db")
      ret = sts.USER_READ_WRITE
    
    return ret

async def query_wait_users(event):
    ''' Get list users who submitted applications '''     
    rows = dbm.db_list_users( id_user=None, active=sts.USER_BLOCKED, rights=sts.USER_NO_RIGHTS )
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
    rows = dbm.db_list_users()
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
            if active == sts.USER_ACTIVE:
               status = status+'🇦 '
            if active == sts.USER_BLOCKED:
               status = status+'🇧 '
            if rights == sts.USER_READ_WRITE:
               status = status+'🇷 🇼 '
            if rights == sts.USER_READ:
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
    res=dbm.db_get_tag( id_nnm, id_user )
    if res:
       await event.answer(_('Film already in database!'), alert=True)
       logging.info(f"User tag film but already in database id_nnm={id_nnm} with result={res}")
       return
    res=dbm.db_add_tag( id_nnm, sts.SETTAG, id_user )
    logging.info(f"User {id_user} tag film id_nnm={id_nnm} with result={res}")
    #bdata = 'TAG'+id_nnm
    await event.answer(_('Film added to database'), alert=True)

async def add_new_user(event):
    '''
    Add new user to DB
    '''
    id_user = event.message.peer_id.user_id
    user_ent = await bot.get_entity(id_user)
    name_user = user_ent.username
    if name_user == None: name_user = user_ent.first_name
    logging.debug(f"Get username for id {id_user}: {name_user}")
    #await query_add_user(id_user, name_user, event)
    res = dbm.db_add_user(id_user, name_user)
    if res:
        await event.respond(_("Yoy already power user!"))
    else:
        await event.respond(_("You request send to Admins, and will be reviewed soon."))
        user_ent = await bot.get_input_entity(sts.admin_name)
        await bot.send_message(user_ent,_("New user **")+name_user+_("** request approve."),parse_mode='md')
    return res

async def home():
    '''
    stub function
    '''
    logging.debug("Call home stub function")
    return 0 

async def main_frontend():
    ''' Loop for bot connection '''
    
    global Channel_my_id

    print("MAIN BOT")
    Channel_my_id = await bot.get_peer_id(sts.Channel_my)
    print(f"MAIN BOT: {Channel_my_id}")
    # First run check db for new Films and publish in Channel
    await publish_all_new_films()
    
    # Get reaction user on inline Buttons in Channel
    @bot.on(events.CallbackQuery(chats=[PeerChannel(Channel_my_id)]))
    async def callback(event):
        logging.debug(f"Get callback event on channel {sts.Channel_my}: {event}")
        # Check user rights
        ret = await check_user(event.query.peer, event.query.user_id, event)
        
        if ret == sts.USER_NEW: 
            await event.answer(_('Sorry you are not registered user.\nYou can only set Reaction.\nYou can register, press [Control] button.'), alert=True)
            # Stop handle this event other handlers
            raise StopPropagation
        elif ret == sts.USER_BLOCKED:   # Blocked
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

    # Handle messages from backend
    @bot.on(events.NewMessage(from_users=sts.backend_user, pattern=r'.*PUBLISH#[:digital:]*'))
    async def bot_handler(event_publish):
        logging.debug(f"Get NewMessage event_bot: {event_publish}")
        #get Id
        button_data = event_publish.data.decode() 
        if button_data.find('UPDPUBLISH', 0, 10) != -1:
            id = button_data.replace('PUBLISH#', '')
            publish_new_film( id, sts.PUBL_UPD )
        elif button_data.find('PUBLISH', 0, 7) != -1:
            id = button_data.replace('PUBLISH#', '')
            publish_new_film( id, sts.PUBL_NOT )
        
                
        
    # Handle messages in bot chat
    @bot.on(events.NewMessage())
    async def bot_handler(event_bot):
        logging.debug(f"Get NewMessage event_bot: {event_bot}")
        menu_level = 0
        #user = event_bot.message.peer_id.user_id
        #logging.info(f"USER_ID:{event_bot.message.peer_id.user_id}")
        try:
            ret = await check_user(PeerChannel(Channel_my_id), event_bot.message.peer_id.user_id, event_bot)
        except Exception as error:
            print(f"Error get user: {error}")
            return
        
        if ret == sts.USER_NEW:     # New user
            choice_buttons = {
            "button1": [_("Yes"), "YES_NEW_USER",add_new_user,[event_bot,event_bot.message.peer_id.user_id]],
            "button2": [_("No"), "NO_NEW_USER", event_bot.respond,[_('Goodbye! See you later...')]]
            }
            await create_choice_dialog(_('**Y realy want tag/untag films**'), choice_buttons, event_bot, menu_level)
            send_menu = sts.NO_MENU
            return
        elif ret == sts.USER_BLOCKED:   # Blocked
            await event_bot.respond(_('Sorry You are Blocked!\n Send message to Admin this channel'))
            return
        elif ret == sts.USER_READ: menu_level = sts.MENU_USER_READ# FIXME no think # Only View?
        elif ret == sts.USER_READ_WRITE: menu_level = sts.MENU_USER_READ_WRITE # Admin
        elif ret == sts.USER_SUPERADMIN: menu_level = sts.MENU_SUPERADMIN # SuperUser
       
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
        send_menu = sts.MENU_USER_READ
        ret = await check_user(PeerChannel(Channel_my_id), id_user, event_bot)
        #Stop handle this event other handlers
        #raise StopPropagation
       
        if ret == sts.USER_BLOCKED:   # Blocked
          #await event_bot.respond(_('Sorry You are Blocked!\nSend message to Admin this channel.'))
          return
        elif ret == sts.USER_READ: menu_level = sts.MENU_USER_READ# FIXME no think # Only View
        elif ret == sts.USER_READ_WRITE: menu_level = sts.MENU_USER_READ_WRITE # Admin
        elif ret == sts.USER_SUPERADMIN: menu_level = sts.MENU_SUPERADMIN # SuperUser
       
        if button_data == 'HOME_MENU':  
            # Goto basic menu
            send_menu = sts.BASIC_MENU
        elif button_data == '/bm_dblist':  
            # Get all database, Use with carefully may be many records
            choice_buttons = {
            "button1": [_("Card"), "CARD", query_all_records_by_one,[event_bot]],
            "button2": [_("List"), "LIST", query_all_records,[event_bot],sts.BASIC_MENU],
            "button3": [_("Cancel"), "HOME_MENU", home,[]]
            }
            await create_choice_dialog(_("Output all in one List or in Card format one by one"), choice_buttons, event_bot, menu_level)
            send_menu = sts.NO_MENU            
        elif button_data == '/bm_dwclear':
            # Clear all tag 
            res=dbm.db_switch_user_tag( id_user, sts.UNSETTAG )
            await event_bot.respond(_("  Clear ")+res+_(" records  "))
            send_menu = sts.BASIC_MENU
        elif button_data == '/bm_dwlist':
            # Get films tagget
            choice_buttons = {
            "button1": [_("Card"), "CARD", query_tagged_records_by_one,[id_user, sts.SETTAG, event_bot]],
            "button2": [_("List"), "LIST", query_tagged_records_list,[id_user, sts.SETTAG, event_bot],sts.BASIC_MENU],
            "button3": [_("Cancel"), "HOME_MENU", home,[]]
            }
            await create_choice_dialog(_("Output all in one List or in Card format one by one"), choice_buttons, event_bot, menu_level)
            send_menu = sts.NO_MENU
        elif button_data == '/bm_dwearly':
            # Get films tagget early
            choice_buttons = {
            "button1": [_("Card"), "CARD", query_tagged_records_by_one,[id_user, sts.SETTAG, event_bot]],
            "button2": [_("List"), "LIST", query_tagged_records_list,[id_user, sts.SETTAG, event_bot],sts.BASIC_MENU],
            "button3": [_("Cancel"), "HOME_MENU", home,[]]
            }
            await create_choice_dialog(_("Get list or card format"), choice_buttons, event_bot, menu_level)
            send_menu = sts.NO_MENU
        elif button_data == '/bm_dbinfo':
            # Get info about DB
            await query_db_info(event_bot,id_user)
            send_menu =sts.BASIC_MENU
        elif button_data == '/bm_search':
            # Search Films
            await event_bot.respond(_("Write and send what you search:"))
            send_menu = sts.NO_MENU
            @bot.on(events.NewMessage()) 
            async def search_handler(event_search):
                logging.info(f"Get search string: {event_search.message.message}")
                await query_search(event_search.message.message, event_bot)
                await event_bot.respond(_("🏁............Done............🏁"))
                bot.remove_event_handler(search_handler)
                await create_basic_menu(menu_level, event_bot)
        elif button_data == '/bm_cum':
            # Go to control users menu 
            send_menu = sts.CUSER_MENU
        elif button_data == '/cu_bbm':
            # Back to basic menu 
            send_menu = sts.BASIC_MENU
        elif button_data == '/cu_lur':
            # Approve waiting users
            await query_wait_users(event_bot)
            send_menu = sts.CUSER_MENU
        elif button_data.find('ENABLE', 0, 6) != -1:
            data = button_data
            id_user_approve = data.replace('ENABLE', '') #FIXME change id_user_approve id_user
            # Approve waiting users
            logging.info(f"Approve waiting users: user={id_user_approve}")
            dbm.db_ch_rights_user(id_user_approve, sts.USER_ACTIVE, sts.USER_READ_WRITE)
            user_db=dbm.db_exist_user(id_user_approve)
            user_name=dict(user_db[0]).get('name_user')
            await event_bot.respond(_("User: ")+user_name+_(" add to DB"))
            #Send message to user
            await bot.send_message(PeerUser(int(id_user_approve)),_("You request approved\nNow Yoy can work with films."))
            send_menu = sts.CUSER_MENU
        elif button_data == '/cu_lar':
            # Approve waiting users
            await query_all_users(event_bot,'INFO',_('List current users:'))
            send_menu = sts.CUSER_MENU
        elif button_data == '/cu_du':
            # List user for select 4 delete
            await query_all_users(event_bot,'DELETE',_('Select user for delete:'))
            send_menu = sts.CUSER_MENU   
        elif button_data.find('DELETE', 0, 6) != -1:
            # Get user for delete
            data = button_data
            id_user_delete = data.replace('DELETE', '') #FIXME change id_user_delete id_user
            user_db=dbm.db_exist_user(id_user_delete)
            user_name=dict(user_db[0]).get('name_user')
            logging.info(f"Delete users: user={id_user_delete}")
            dbm.db_del_user(id_user_delete)
            await event_bot.respond(_("User: ")+user_name+_(" deleted from DB"))
            send_menu = sts.CUSER_MENU   
        elif button_data == '/cu_cur':
            # Change rights user
            await query_all_users(event_bot,'RIGHTS',_('Select user for change rights:'))
            send_menu = sts.NO_MENU
        elif button_data.find('RIGHTS', 0, 6) != -1:
            data = button_data
            id_user = data.replace('RIGHTS', '')
            logging.info(f"Change rights for user={id_user}")
            user_db=dbm.db_exist_user(id_user)
            user_name=dict(user_db[0]).get('name_user')
            await event_bot.respond(_("Change righst for user: ")+user_name)
            send_menu = sts.CURIGHTS_MENU
        elif button_data.find('/cr_ro', 0, 7) != -1:
            #Change to RO
            data = button_data
            id_user = data.replace('/cr_ro', '')
            dbm.db_ch_rights_user( id_user, sts.USER_ACTIVE, sts.USER_READ )
            logging.info(f"Change rights RO for user={id_user}")
            send_menu = sts.CUSER_MENU
        elif button_data.find('/cr_rw', 0, 7) != -1:
            #Change to RW
            data = button_data
            id_user = data.replace('/cr_rw', '')
            dbm.db_ch_rights_user( id_user, sts.USER_ACTIVE, sts.USER_READ_WRITE )
            logging.info(f"Change rights RW for user={id_user}")
            send_menu = sts.CUSER_MENU
        elif button_data == '/cu_buu':
            # Block/Unblock user
            await query_all_users(event_bot,'BLOCK_UNBLOCK',_('Select user for block/unblock:'))
            send_menu = sts.NO_MENU
        elif button_data.find('BLOCK_UNBLOCK', 0,13 ) != -1:
            data = button_data
            id_user = data.replace('BLOCK_UNBLOCK', '')
            user_db=dbm.db_exist_user(id_user)
            user_name=dict(user_db[0]).get('name_user')
            active=dict(user_db[0]).get('active')
            if active == sts.USER_BLOCKED:
              logging.info(f"Unblock user={id_user}")
              dbm.db_ch_rights_user( id_user, sts.USER_ACTIVE, sts.USER_READ_WRITE )
              user_db=dbm.db_exist_user(id_user_approve)
              await event_bot.respond(_("User: ")+user_name+_(" Unblocked"))
            else:
              logging.info(f"Block user={id_user}")
              dbm.db_ch_rights_user( id_user, sts.USER_BLOCKED, sts.USER_READ_WRITE )
              await event_bot.respond(_("User: ")+user_name+_(" Blocked"))
            send_menu = sts.CUSER_MENU
            #Back to user menu

        if send_menu == sts.BASIC_MENU:
            #await event_bot.respond(_("🏁............Done............🏁"))
            await create_basic_menu(menu_level, event_bot)
        elif send_menu == sts.CUSER_MENU:
            #await event_bot.respond(_("🏁............Done............🏁"))
            await create_control_user_menu(menu_level, event_bot)
        elif send_menu == sts.CURIGHTS_MENU:
            #await event_bot.respond(_("🏁............Done............🏁"))
            await create_rights_user_menu(menu_level, event_bot, id_user)

    return bot
    #with bot:
    #        try:
    #            bot.loop.run_until_complete(main_bot())
    #            #logging.debug(f"Get Channel_id: {Channel_my_id}")
    #        except Exception as BotMethodInvalidError:
    #            logging.error("Bot can't access get channel ID  by {sts.Cahnnel_my}.\n Please change Channel_my on digital notation!\n")
    #            logging.error("Original Error is: {BotMethodInvalidError}")
    #            print("Bot can't access get channel ID  by {sts.Cahnnel_my}.\n Please change Channel_my on digital notation!\n")
    #            bot.disconnect()
    #            return None

# main()
print('Start frontend.')

sts.get_config()

# Enable logging
logging.basicConfig(level=sts.log_level, filename="fronend_"+sts.logfile, filemode="a", format="%(asctime)s %(levelname)s %(message)s")
logging.info(f"Start backend bot.")

localedir = os.path.join(os.path.dirname(os.path.realpath(os.path.normpath(sys.argv[0]))), 'locales')

if os.path.isdir(localedir):
  translate = gettext.translation('nnmbot', localedir, [sts.Lang])
  _ = translate.gettext
else: 
  logging.info(f"No locale dir for support langs: {sts.localedir} \n Use default lang: Engilsh")
  def _(message): return message
 
sts.connection = sqlite3.connect(sts.db_name)
sts.connection.row_factory = sqlite3.Row
sts.cursor = sts.connection.cursor()

dbm.db_init()
# TODO: Neeed test exist DB or no, exist tables in DB or not
dbm.db_create()

# Connect to Telegram as bot
if sts.use_proxy:
    prx = re.search('(^.*)://(.*):(.*$)', sts.proxies.get('http'))
    proxy=(prx.group(1), prx.group(2), int(prx.group(3)))
else: 
    proxy=None

# Set type session: file or env string
if sts.ses_bot_str == '':
   session=sts.session_client
else:
   session=StringSession(sts.ses_usr_str)


bot = TelegramClient(sts.session_bot, sts.api_id, sts.api_hash, system_version=sts.system_version, proxy=proxy).start(bot_token=sts.mybot_token)

bot.start()
bot.loop.run_until_complete(main_frontend())
bot.run_until_disconnected()

sts.connection.close()
logging.info(f"End.\n--------------------------")
print('End.')