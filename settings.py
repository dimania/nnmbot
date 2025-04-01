#
# Telegram Bot for filter films from NNMCLUB channel
# version 0.5
# Module settings.py Set internal variables 
# and constants, get global configs from file myconfig.py
#
#
# 
#!!!!!!!! Replace with you config file here !!!!!!!
# replace myconfig with config by example
#------------------------
import myconfig as cfg
#------------------------
import re
import os

#-----------------
# CONSTANTS
#

DEFTAG = 0
SETTAG = 1
UNSETTAG = 2

PUBL_NOT = 0
PUBL_YES = 1
PUBL_UPD = 2

USER_ACTIVE = 1
USER_BLOCKED = 0
USER_SUPERADMIN = 4

USER_READ_WRITE = 3
USER_READ = 2
USER_NO_RIGHTS=0
USER_NEW = 1
USER_ADMIN_NEW = 4

MENU_USER_READ = 0
MENU_USER_READ_WRITE = 1
MENU_SUPERADMIN = 2

BASIC_MENU = 1
CUSER_MENU = 2
CURIGHTS_MENU = 3
NO_MENU = 0

LIST_REC_IN_MSG = 20
#-----------------



def get_config(config=cfg):
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
    global cursor
    global connection
    global backend_user
    global ses_usr_str
    global ses_bot_str

    
    try:
        api_id = os.environ.get("API_ID", config.API_ID)
        api_hash = os.environ.get("API_HASH", config.API_HASH)
        mybot_token = os.environ.get("BOT_TOKEN", config.BOT_TOKEN)
        ses_usr_str = os.environ.get("SESSION_STRING_USER", config.SESSION_STRING_USER)
        ses_bot_str = os.environ.get("SESSION_STRING_BOT", config.SESSION_STRING_BOT)
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
        backend_user = config.backend_user

        if use_proxy:
            proxies = config.proxies
        else:
            proxies = None

    except Exception as error:
        print(f"Error in config file: {error}")
        exit(-1)


