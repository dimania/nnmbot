#---------------- basic settings --------
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
# Id chennel for monitor
channelId    = <CHANNEL_ID> # channel what monitor by example       -1001776763737
# Id chanell for filter messages 
My_channelId = <CYANNEL_ID> # channel or chat where send by example -1003333333333
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
#ICU extension for case independet search  in DB if Not when set in None
ICU_extension_lib = "/usr/lib64/sqlite3/libSqliteIcu.so"

