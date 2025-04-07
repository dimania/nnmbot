# Telegram Bot for filter films from NNMCLUB channel
# version 0.5
# Tools gen_ses_str.py generate session string
# for use in TelegramClient instead of session file
# for more security
#
# client: user/bot
# mode: gen/show/test
#
from sys import argv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
# --------------------------------
import settings as sts
# --------------------------------

def Usage():
    print(f"Usage: {argv[0]} <client> <mode>\n where:\n <client>: user or bot\n <mode>: gen or show or test\n")
    print(f"Example:\n{argv[0]} user gen\n{argv[0]} bot test\n")
    print("client - connect to Telegram as user\nbot - connect to Telegram as bot\n")
    print("gen - generate session string")
    print("test - connect to Telegram with session string and send test messagee to admin (admin_name in config.py)")
    print("show - show current connect string")

if len(argv) != 3:
   Usage()
   exit()

client = argv[1]
mode = argv[2]

sts.get_config()

#---------------------------user connect--------------------------------------
if argv[1] == 'user' and argv[2] == 'gen':
    # Generate string session for user client connection
    client = TelegramClient(StringSession(), sts.api_id, sts.api_hash)
    string=client.session.save()
    print(f"String session for user:\n{string}")
    exit()
  
if argv[1] == 'user' and argv[2] == 'test':
    # Test connection for user connection
    if sts.ses_usr_str == '':
       print("Session string not set in env var or config file!")
       exit()

    print("Set string session for client:\n----------------------------------------------")
    print(f"{sts.ses_usr_str}\n-------------------------------------------------\n")
    client = TelegramClient(StringSession(sts.ses_usr_str), sts.api_id, sts.api_hash, system_version=sts.system_version)
    client.send_message(sts.admin_name, 'Hi')
    string=client.session.save()
    print("Current String session for client:\n----------------------------------------------")
    print(f"{string}\n-----------------------------------------------\n")
    exit()

if argv[1] == 'user' and argv[2] == 'show':
    # Test connection for user connection
    if sts.ses_usr_str == '':
       print("Session string not set in env var or config file!")
       exit()
    else:
       print("Current string session for client is:\n----------------------------------------------")
       print(f"{sts.ses_usr_str}\n-------------------------------------------------\n")
       exit()

#---------------------------bot connect--------------------------------------
if argv[1] == 'bot' and argv[2] == 'gen':
    # Generate string session for user client connection
    bot = TelegramClient(StringSession(), sts.api_id, sts.api_hash, system_version=sts.system_version).start(bot_token=sts.mybot_token)
    string=bot.session.save()
    print(f"String session for bot:\n{string}")
    exit()
if argv[1] == 'bot' and argv[2] == 'test':
    # Test connection for user connection
    if sts.ses_bot_str == '':
       print("Session string not set in env var or config file!")
       exit()

    print("Set string session for client connect:\n----------------------------------------------")
    print(f"{sts.ses_bot_str}\n-------------------------------------------------\n")\

    bot=TelegramClient(StringSession(sts.ses_bot_str), sts.api_id, sts.api_hash, system_version=sts.system_version).start(bot_token=sts.mybot_token)
    bot.send_message(sts.admin_name, 'Hi')
    string=bot.session.save()
    print("Current String session for bot:\n----------------------------------------------")
    print(f"{string}\n-----------------------------------------------\n")
    exit()

if argv[1] == 'bot' and argv[2] == 'show':
    # Test connection for user connection
    if sts.ses_bot_str == '':
       print("Session string not set in env var or config file!")
       exit()
    else:
       print("Current string session for bot is:\n----------------------------------------------")
       print(f"{sts.ses_bot_str}\n-------------------------------------------------\n")
       exit()

print("ERROR in arguments!")
Usage()
exit()