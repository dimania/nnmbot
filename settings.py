# Telegram Bot for filter films from NNMCLUB channel
# version 0.5
# Module settings.py Set internal variables
# and constants, get global configs from file myconfig.py
#
#
#
#!!!!!!!! Replace with you config file here !!!!!!!
# replace myconfig with config by example

import re
import os

#------------------------
import myconfig as cfg
#------------------------

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

MENU_USER_READ = 0
MENU_USER_READ_WRITE = 1
MENU_SUPERADMIN = 2

BASIC_MENU = 1
CUSER_MENU = 2
CURIGHTS_MENU = 3
NO_MENU = 0

LIST_REC_IN_MSG = 20
#-----------------
RETRIES_DB_LOCK = 5 



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
    global pattern_filter
    global ICU_extension_lib
    global log_level
    global Lang
    global magnet_helper
    global cursor
    global connection
    global backend_user
    global ses_usr_str
    global ses_bot_str
    global ukp_api_key
    global ukp_api_url 

    cursor = None
    connection = None

    try:
        system_version = config.system_version
        bot_name = config.bot_name
        admin_name = config.admin_name
        Channel_mon = config.Channel_mon
        Channel_my = config.Channel_my
        db_name = config.db_name
        logfile = config.logfile
        use_proxy = config.use_proxy
        pattern_filter = re.compile(config.pattern_filter)
        log_level = config.log_level
        Lang = config.Lang
        backend_user = config.backend_user
        
        # May be comment out in config.py
        if 'API_ID' in vars(config):
            api_id = config.API_ID
        else: api_id = os.environ.get("API_ID", None)

        if 'API_HASH' in vars(config):
            api_hash = config.API_HASH
        else: api_hash = os.environ.get("API_HASH", None)

        if 'BOT_TOKEN' in vars(config):
            mybot_token = config.BOT_TOKEN
        else: mybot_token = os.environ.get("BOT_TOKEN", None)

        if 'SESSION_STRING_USER' in vars(config):
            ses_usr_str = config.SESSION_STRING_USER
        else: ses_usr_str = os.environ.get("SESSION_STRING_USER", None) 

        if 'SESSION_STRING_BOT' in vars(config):
            ses_bot_str = config.SESSION_STRING_BOT 
        else: ses_bot_str = os.environ.get("SESSION_STRING_BOT", None)

        if 'UKP_API_KEY' in vars(config):
            ukp_api_key = config.UKP_API_KEY
        else: ukp_api_key = os.environ.get("UKP_API_KEY", None)
    
        if not ses_usr_str: session_client = config.session_client
        if not ses_bot_str: session_bot = config.session_bot 

        if 'ukp_api_url' in vars(config):
            ukp_api_url = config.ukp_api_url
        else: ukp_api_url = None

        if 'magnet_helper' in vars(config):
            magnet_helper = config.magnet_helper
        else: magnet_helper = None
    
        if 'ICU_extension_lib' in vars(config):
            ICU_extension_lib = config.ICU_extension_lib
        else: ICU_extension_lib = None

        if use_proxy:
            proxies = config.proxies
        else:
            proxies = None

    except Exception as error:
        print(f"Error in config file: {error}")
        exit(-1)


