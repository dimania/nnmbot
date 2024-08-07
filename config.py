#
# Connfig settings file
# By default filename - config.py
# Please check directive - import config in programm
# version 0.4

# Api id getted from telegram from  https://my.telegram.org change to 60328456 by example
api_id = <API_ID>

# Api hash getted from telegram from  https://my.telegram.org change to '860438hcoibwe37842y3dcnblkjh333' by example
api_hash = <API_HASH> 

# Bot token getted form FatherBot change to '234324234:sdfkehf834608hlkcn38' by example  
mybot_token = <BOT_TOKEN>

# Set version client
system_version = "0.2-yorever"

#File name session for client connection - any filename
session_client='nnmbot_session_client'

#File name for bot connection - any filename
session_bot='nnmbot_session_bot'

#Channels must be public channel else use ID channel in notation -100ID example: -1002007192033 where 2007192033 ID channel
# Id channel for monitor
Channel_mon = 't.me/******' 
# Id chanell for filter messages 
Channel_my  = 't.me/######'
# Name of bot - will be to switch on you bot for control database.
bot_name = 'control_bd_bot'

#Admin name - where send messages from new user about request add to users bot
admin_name = 'adm_dimania'

# filename database - better use full path
db_name = 'database.db'  # database name, better set full path

# if use proxy set here 
# http required - use for set TelegramClient proxy parameter
proxies = {
  "http": "socks5://127.0.0.1:1080",
  "https": "socks5://127.0.0.1:1080",
}

#Log file name for write logs programm
logfile = 'nnmbot.log'

#Use proxy or d'not
use_proxy = 0 # if use proxy set to 1

#Pattern for filter messages from channelId 
filter=r'(?:.*Фильм.*)|(?:.*Новинки.*)'

#Helper for open magnet links in telegram
magnet_helper = 'https://ivan386.github.io/#'

#ICU extension for case independet search  in DB if Not when set in None
ICU_extension_lib = "/usr/lib64/sqlite3/libSqliteIcu.so"

#Set logging level for bot
#Possible value: NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL  
log_level='INFO'

# Set lang for dialogs. Possible values ru,en 
Lang='en'
