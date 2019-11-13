import os
from slack import RTMClient
from rlg_util import *

# file containing list of restaurants
rest_file='restaurant_list'

# random seed for restaurant selection
random.seed()

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

@RTMClient.run_on(event="reaction_added")

def democracy_is_freedom(**payload):
  data = payload['data']
  web_client = payload['web_client']
  
  item_user = data['item_user'] #who posted the message that received a reaction
  if item_user == rlgbot_id:
    channel_id = data['item']['channel']
    user = data['user']
    reaction = data['reaction']
    response=handle_reaction(reaction, user, reset_file)
    
    web_client.chat_postMessage(
      channel=channel_id,
      text=response
    )
    
with open('slack_token','r') as pwd:
    slack_token=pwd.readline().strip()
with open('bot_id', 'r') as uid:
    rlgbot_id=uid.readline().strip()
rtm_client = RTMClient(token=slack_token)
#rlgbot_id = rtm_client.api_call("auth.test")["user_id"]
rtm_client.start()
