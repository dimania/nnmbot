# Test Select users dialog
import requests
import json 
 
def test():
    buttons = [
    {
        "text": "Select Users",
        "request_chat": {
            "request_id": 1, # button id
            "chat_is_channel": True,
            "title": "Select users",
        }
    }
    ]
    reply_markup = {"keyboard": [buttons],"resize_keyboard": True, "one_time_keyboard": True}

    url = f"https://api.telegram.org/bot{sts.mybot_token}/sendMessage"

    payload = {
    "chat_id": 1033339697, # Id user to
    "text": "Click in the button and users",
    "reply_markup": json.dumps(reply_markup)
    }
    
    response = requests.post(url, data=payload)
    logging.debug(f"Rsponse Select user button post:{response}\n Event:{event}")

# hanled answer
    @bot.on(events.Raw(types=UpdateNewMessage))
    async def on_requested_peer_channel(event):
    try:
        if event.message.action.peers[0].__class__.__name__ == "RequestedPeerChannel":
            button_id = event.message.action.button_id
            if button_id == 1: # button id
                peer = event.message.action.peers[0]
                channel_id = peer.channel_id
                title = peer.title
    except:
       logging.debug(f"Error...") 