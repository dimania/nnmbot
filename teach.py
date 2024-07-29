#!/usr/bin/python3
#
# Telegram Bot for filter films from NNMCLUB channel
# version 0.5
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
from functools import wraps

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
      id_kpsk TEXT,
      id_imdb TEXT,
      nnm_url TEXT,
      name TEXT,
      mag_link TEXT DEFAULT NULL,
      section  TEXT DEFAULT NULL,
      genre  TEXT DEFAULT NULL,
      rating_kpsk TEXT DEFAULT NULL,
      rating_imdb TEXT DEFAULT NULL,
      description TEXT DEFAULT NULL,
      photo BLOB DEFAULT NULL,
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

def db_list_tagged_films_id_new( id_user=None, tag=None ):
    ''' List only records with set tag '''
    cursor.execute("SELECT id FROM Films WHERE id IN (SELECT id_Films FROM Ufilms WHERE id_user=? and tag=?)", (id_user,tag,))
    rows = cursor.fetchall()
    return rows

def test_fun_as_parm0(a1,b1,c1):
  print(f"Call func as par: {a1},{b1},{c1}")
def test_fun_as_parm1(a1,b1,c1):
  print(f"Call func as par: {a1},{b1},{c1}")

def decorator_wrapper(*args_p, **kwargs_p):
    def real_decorator(func): # бъявляем декоратор
        @wraps(func)
        def wrapper(*args, **kwargs):
            #return func(*args, **kwargs)
            #print(f"before {kwargs_p['some']['Message']},{kwargs_p['d']}") # мой код до выполнения фукции
            for data in kwargs_p['some']:
              #eval(kwargs_p['some'][0])
              print(f"{kwargs_p['some'][data][2]}")
              eval(kwargs_p['some'][data][2])
            func( *args, **kwargs)
            print("after") # мой код после выполнения функции  
        return wrapper
        
    return real_decorator     # возвращаем декоратор
some_par=list(('test_fun_as_parm0(1,2,3)','test_fun_as_parm1(3,3,3)'))
#some_par[0]=test_fun_as_parm0(1,2,3)
#some_par[1]=test_fun_as_parm1(3,3,3)

button_run = {
      #"Message": "Text of Message",
      "button1": ["Yes", "yes", "test_fun_as_parm0(1,1,1)"],
      "button2": ["No", "no", "test_fun_as_parm0(2,2,2)"],
      "button3": ["Cancel", "cancel", "test_fun_as_parm0(3,3,3)"]
}

@decorator_wrapper(some=button_run, d='2')
def func(a,b,c,d):
  print(f"In func! {a},{b},{c},{d}")

@decorator_wrapper(some_par='10', d='20')
def funcnew(a,b,c,d):
  print(f"In func! {a},{b},{c},{d}")


func(3,4,5,6)

#funcnew(6,5,4,3)

exit(0)

def test_callf(func):
  func(1,2,3)

def func0(a,b,c):
  print(f"a={a},b={b},c={c}")  

# main()
print('Start test.')

keyboard = [[Button.inline("Yes", b"/yes"),Button.inline("No", b"/no")]]
print(keyboard)
index=0
choice_buttons = {"Yes":"yes", "No":"no"}
choice_list[0][1]="Yes"
choice_list[0][2]="yes"
choice_list[0][3]="func0(1,2,3)"
choice_list[1][1]="No"
choice_list[2][2]="no"
choice_list[3][3]="func0(3,4,5)"


#test_callf(func0(1,2,3))

exit(0)
button=[]
for text, action in choice_buttons.items():
  button.append(Button.inline(text, action))

 # if i > 0:
  #  buttons_inline=buttons_inline+","
  #i=i+1
  #buttons_inline=buttons_inline+f"Button.inline('{text}',b'{action}')"
 
keys=f"[[{buttons_inline}]]"
keyboard=eval(keys)
print(keyboard)
#Button.inline(_("Yes"), b"/yes"),
#Button.inline(_("No"), b"/no")


exit(0)
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
#---------------------------------------------


rows = db_list_tagged_films_id_new( id_user='1033339697', tag='1' )

str='NEXT1'
i=int(str.replace('NEXT',''))

print(dict(rows[int(i)]))
print(len(rows))

for row in rows:
   print(dict(row))

#od1 = OrderedDict(rows)
#print(od1)