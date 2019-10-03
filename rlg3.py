import os
from slack import RTMClient
import random
from rlg_util import *

# file containing list of restaurants
rest_file='restaurant_list'


@RTMClient.run_on(event="message")

def say_hello(**payload):
  data = payload['data']
  web_client = payload['web_client']

  # check for direct message
  user_id, message = parse_direct_mention(data['text'])
  if user_id == rlgbot_id:
    channel_id = data['channel']
#    thread_ts = data['ts']
    user = data['user']

    response=handle_command(message, user, rest_file)

    web_client.chat_postMessage(
      channel=channel_id,
      text=response #,
#      thread_ts=thread_ts
    )

with open('slack_token','r') as pwd:
    slack_token=pwd.readline().strip()
with open('bot_id', 'r') as uid:
    rlgbot_id=uid.readline().strip()
rtm_client = RTMClient(token=slack_token)
#rlgbot_id = rtm_client.api_call("auth.test")["user_id"]
rtm_client.start()
