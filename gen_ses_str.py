# Telegram Bot for filter films from NNMCLUB channel
# version 0.5
# Tools gen_ses_str.py generate session string
# for use in TelegramClient instead of session file
# for more security
#
# client: user/bot
# mode: gen/show/test
#
# --------------------------------
import settings as sts
# --------------------------------
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from sys import argv


if len(argv) > 2:
    
    print(f"Ok argv={argv}")
else: 
    print(f"NOT Ok argv={argv}")
    exit()

client = argv[1]
mode = argv[2]

# example:
access_template = ['switchport mode access',
                   'switchport access vlan {}',
                   'switchport nonegotiate',
                   'spanning-tree portfast',
                   'spanning-tree bpduguard enable']

print('client {}'.format(mode))
print('\n'.join(access_template).format(mode))



exit()
sts.get_config()

# Generate string session for user client connection
#with TelegramClient(StringSession(), sts.api_id, sts.api_hash) as client:
#    string=client.session.save()
#    print(f"String session for user connect:\n{string}")

# Generate string session for user client connection
bot = TelegramClient(StringSession(), sts.api_id, sts.api_hash, system_version=sts.system_version).start(bot_token=sts.mybot_token)
string=bot.session.save()
print(f"String session for bot connect:\n----------------------------------------------")
print(f"{string}\n-------------------------------------------------\n")

exit()

#with TelegramClient(StringSession(), sts.api_id, sts.api_hash, system_version=sts.system_version) as client:
#    client.connect()
#    client.sign_in(bot_token=sts.mybot_token)
#    string=client.session.save()
#    print(f"String session for bot connect:\n----------------------------------------------\n")
#    print(f"{string}\n-------------------------------------------------\n")

# Test connection for user connection
print(f"Set string session for client connect:\n----------------------------------------------")
print(f"{sts.ses_usr_str}\n-------------------------------------------------\n")
with TelegramClient(StringSession(sts.ses_usr_str), sts.api_id, sts.api_hash, system_version=sts.system_version) as client:
    client.send_message(sts.admin_name, 'Hi')
    string=client.session.save()
    print(f"Current String session for client connect:\n----------------------------------------------")
    print(f"{string}\n-----------------------------------------------\n")


