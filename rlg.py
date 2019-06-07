import os
import time
import re
from slackclient import SlackClient
import random


# instantiate Slack client
with open('slack_token','r') as pwd:
    SLACK_BOT_TOKEN=pwd.readline().strip()
slack_client = SlackClient(SLACK_BOT_TOKEN)

# bot's user ID in Slack: value is assigned after the bot starts up
rlgbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

# file containing list of restaurants
rest_file='restaurant_list'


def load_restaurants(rest_file_name):
    """
        Loads and parses the file containing users' restaurant lists.
        Returns user:list dictionary and combined list of all restaurants.
    """
    rest_dict={}
    rest_list=[]
    with open(rest_file_name,'r') as infile:
        for line in infile.readlines():
            if line=="\n":      # skip empty lines
                continue
            elif line[-2]==':' and ':' not in line[:-2]:   # indicates the begining of a user's list
                user=line.split(':')[0]
                rest_dict[user]=[]
            else:               # append restaurant to user's list
                rest=line.strip()
                rest_dict[user].append(rest)
                rest_list.append(rest)
    return rest_dict, rest_list


def write_restaurants(rest_dict, rest_file_name):
    """
        Writes file containing users' restaurant lists.
    """
    with open(rest_file_name,'w') as outfile:

        for user in rest_dict.keys():       # loop over users
            outfile.write(user+':\n')

            for rest in rest_dict[user]:    # write each user's restaurants
                outfile.write(rest+'\n')
            outfile.write('\n')


# random seed for restaurant selection
random.seed()



def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command, channel, and user ID.
        If its not found, then this function returns None, None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == rlgbot_id:
                return message, event["channel"], event["user"]
    return None, None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_command(command, channel, user):
    """
        Executes bot command if the command is known
    """
    # default response is help text for the user
    default_response = "Not sure what you mean. Try *add*, *where*, or *list*."
    response = None

    command=command.lower() # case-insensitive


    # list restaurants on a user's list
    if command.startswith('list'):
        # load current lists
        rest_dict, rest_list = load_restaurants(rest_file)
       
        if user not in rest_dict:
            response = "It looks like your list is empty. You can ask me to add restaurants to the list by typing something like\n\t\"add restaurant1, restaurant2\"" 

        else:
            response = "Your list contains the following restaurants:"
            for rest in rest_dict[user]:
                response+="\n\t"+rest


    # add a restaurant to a user's list 
    if command.startswith('add'):
        to_add=command.split('add ')

        if len(to_add)<2:
            response="You can ask me to add restaurants to the list by typing something like\n\t\"add restaurant1, restaurant2\""

        else:
            to_add=to_add[1].split(', ')

            # load current lists
            rest_dict, rest_list = load_restaurants(rest_file)
            if user not in rest_dict:   # start new list for a new user
                rest_dict[user]=[]

            # add the restaurants to user's list
            for r in to_add:
                rest_dict[user].append(r)
                rest_list.append(r)
            # save modified lists
            write_restaurants(rest_dict, rest_file)

            # build response message
            response = "Sure... I added "

            if len(to_add)==1:
                response+=to_add[0]
            elif len(to_add)==2:
                response+=to_add[0]+' and '+to_add[1]
            else:
                for r in to_add[:-1]:
                    response += r+', '
                response += 'and '+to_add[-1]

            response += " to the list of restaurants!\nIf there were any mistakes, you can delete them from the list by typing\n\t\"del restaurant1, restaurant2\""


    # delete a restaurant from a user's list
    if command.startswith('del'):
        to_del=command.split('del ')

        if len(to_del)<2:
            response="You can ask me to delete restaurants from the list by typing something like\n\t\"del restaurant1 restaurant2\""

        else:
            to_del=to_del[1].split(', ')
            removed=[]

            # load current lists
            rest_dict, rest_list = load_restaurants(rest_file)
            # only delete from this user's list
            for r in rest_dict[user]:
                if r in to_del:
                    rest_dict[user].remove(r)
                    rest_list.remove(r)
                    removed.append(r)
                    to_del.remove(r)

            # save modified lists
            write_restaurants(rest_dict, rest_file)

            # build response message
            if len(removed)>0:
                response = "Sure... I deleted "

                if len(removed)==1:
                    response+=removed[0]
                elif len(removed)==2:
                    response+=removed[0]+' and '+removed[1]
                else:
                    for r in removed[:-1]:
                        response += r+', '
                    response += 'and '+removed[-1]

                response += " from the list of restaurants!"

            if len(to_del)>0:
                if response==None:
                    response=''
                if len(to_del)==1:
                    response+=to_del[0]+' was'
                elif len(restaurants)==2:
                    response+=to_del[0]+' and '+to_del[1]+' were'
                else:
                    for r in to_del[:-1]:
                        response += r+', '
                    response += 'and '+to_del[-1]+' were'
                response += " not in the list."
            

    # choose a random restaurant
    elif command.startswith('where'):
        response = "Here is a random restaurant selection: "

        rest_dict, rest_list = load_restaurants(rest_file)
        rest=random.choice(rest_list)
        while rest=="dunkin' donuts":
            response="Josh will be going to dunkin' donuts. Here is a different random restaurant selection: "
            rest=random.choice(rest_list)
        response += rest
        
        
    elif command.startswith('ravioli'):
        response = "The Krabby Patty formula can be found at: "
        
        rest_dict, rest_list = load_restaurants(rest_file)
        response += random.choice(rest_list)
       
    # send response
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )


if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")

        # read bot's user ID by calling Web API method `auth.test`
        rlgbot_id = slack_client.api_call("auth.test")["user_id"]

        while True:
            command, channel, user = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel, user)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
