#
#   Cisco Prime Alert Extractor and Informer
#
#   Claudio Ippolito(cippolit@cisco.com)
#   Nicholas Rees (nrees@cisco.com)
#   May 2016
#
#   REQUIREMENTS:
#       It needs the PrimeAPI module for easy access to the
#       Prime Infrastructure API.
#
#       It also needs the "requests" python library, which you can easily download.
#           (issue the "pip install requests" command in shell or cmd)
#     
#       Furthermore, you need a settings file named "settings.cfg" in the root
#       directory of the application, defining the following variables:
#       PRIME_URL = the url to your Prime Infrasture 3.0 instance
#       PRIME_USER = the username with which you want to log in to Prime
#       PRIME_PW = the password with which you want to log in to Prime
#       SPARK_AUTH_TOKEN = your auth Token to access Spark via the REST API
#       SPARK_ROOM_ID = the room ID of the room you want to post into
#       SPARK_URL = the url to the SPARP API (probably https://api.ciscospark.com/v1/messages)
#       TROPO_PHONE_NR = the phone number you want to dial via tropo. Include the country code, but omit the "+"
#           (so for Germany this could be 49151282828 for instance, since +49 is the country code...)
#
#     WARNING:
#       Any use of these scripts and tools is at
#       your own risk. There is no guarantee that
#       they have been through thorough testing in a
#       comparable environment and we are not
#       responsible for any damage or data loss
#       incurred with their use.
#

import time
import requests
import json
import configparser

from PrimeAPI import PrimeAPI

# constants for settings
PRIME_URL = ""
PRIME_USER = ""
PRIME_PW = ""

SPARK_AUTH_TOKEN = ""
SPARK_ROOM_ID = ""
SPARK_URL = ""

TROPO_AUTH_TOKEN = ""
TROPO_PHONE_NR = ""

def fetch_alerts(api):
    """ fetch all alerts from PI within the last 48 hours which are critical. """
    try:

        # get current date and date 48 hours prior.
        yesterday = time.strftime("%Y-%m-%d",time.localtime((time.time() - 172800)))
        today = time.strftime("%Y-%m-%d",time.localtime(time.time()))

        print("Fetching all critical Alerts between " + yesterday + " and " + today + ".")
        print()
      
        # issue API call to PI for critical alerts between today and yesterday
        response = api.send_prime_request("data/Alarms?severity=CRITICAL&alarmFoundAt=between(\"" + yesterday + "\",\"" + today + "\")", "XML")
        
        # write all IDs of the fetches alarms to a list
        alarmIDs = list()

        for child in response:
            alarmIDs.append(child.text)

        return alarmIDs

    except Exception as e:
        print("Error while fetching alerts from Prime.")
        print("==============================")
        print("Exception dump below: ")
        print("==============================")
        print(str(e))
        print("==============================")

def fetch_alerts_text(alarmIDs, api):
    """fetch all messages for all prior gathered alert IDs and write them to a list."""
    
    messages = list()

    # iterate over the alarmIDs, fetch the message text and write it to the list
    for id in alarmIDs:
        response = api.send_prime_request("data/Alarms/"+id, "XML")
        message = response.find(".//message").text
        messages.append(message)
        print("\t" + message)
        print()

    return messages

def build_notification_string(messages):
    """piece together the notification message as a string for the SPARK and TROPO API calls"""

    notificationMessage = "There were a total of " + str(len(messages)) + " critical alerts in the last 48 hours. "

    # iterate over the messages list and append each message to the notification string
    for message in messages:
        notificationMessage += "Alert number " + str(messages.index(message)+1) + ". "
        notificationMessage += message + " "

    notificationMessage += "Goodbye... And Good Luck."

    # write the notification string to the console
    print(notificationMessage)  

    return notificationMessage
    
def post_to_spark(notificationMessage):
    """post a notification message to Spark via the REST API"""
    
    SPARK_HEADERS = {'Content-type' : 'application/json; charset=utf-8', 'Authorization' : SPARK_AUTH_TOKEN}
    SPARK_PAYLOAD = json.dumps( {'roomId':SPARK_ROOM_ID, 'text':notificationMessage} )

    # issue the API call to SPARK
    try: 
        spark_request = requests.post(SPARK_URL, headers=SPARK_HEADERS, data=SPARK_PAYLOAD, verify=False)

    except Exception as e:
        print("Error whilst posting to Spark.")
        print(str(e))
        input("Press RETURN to continue...")


def issue_tropo_call(notificationMessage):
    """issue an API call to Tropo, for calling the network admin and reading the notification message to him"""

    # replace whitespaces with "+" for correct get-parameter http url encoding
    tropoNotificationMessage = notificationMessage.replace(" ", "+")

    # issue the API call to TROPO
    requests.get("https://api.tropo.com/1.0/sessions?action=create&token=" + TROPO_AUTH_TOKEN + "&numberToDial=" + TROPO_PHONE_NR + "&msg=" + tropoNotificationMessage)
    
def load_config():

    try:
        config = configparser.RawConfigParser()
        config.read('settings.cfg')

        # get access to global variables
        global PRIME_URL, PRIME_USER, PRIME_PW, SPARK_AUTH_TOKEN, SPARK_ROOM_ID, SPARK_URL, TROPO_AUTH_TOKEN, TROPO_PHONE_NR
        
        PRIME_URL = config['PRIME']['PRIME_URL']
        PRIME_USER = config['PRIME']['PRIME_USER']
        PRIME_PW = config['PRIME']['PRIME_PW']

        SPARK_AUTH_TOKEN = config['SPARK']['SPARK_AUTH_TOKEN']
        SPARK_ROOM_ID= config['SPARK']['SPARK_ROOM_ID']
        SPARK_URL = config['SPARK']['SPARK_URL']

        TROPO_AUTH_TOKEN = config['TROPO']['TROPO_AUTH_TOKEN']
        TROPO_PHONE_NR = config['TROPO']['TROPO_PHONE_NR']

    except Exception as e:
        print("Error whilst reading from the config file. Make sure settings.cfg is present in the application root directory.")
        print("The following variables have to be defined: PRIME_URL, PRIME_USER, PRIME_PW, SPARK_AUTH_TOKEN, SPARK_ROOM_ID, SPARK_URL, SPARK_HEADERS and SPARK_PAYLOAD.")
        print(str(e))
        input("Press RETURN to continue...")

def main():
    """main function. starting point of the script."""

    # load all settings constants from config file
    load_config()

    print("######################################################")
    print("####                                              ####")
    print("####                                              ####")
    print("####     PRIME INFRASTRUCTURE ALARM EXTRACTOR     ####")
    print("####               AND NOTIFIER TOOL              ####")
    print("####                                              ####")
    print("####                                              ####")
    print("######################################################")
    print()

    try:
        print("Logging into Prime @" + PRIME_URL + " as " + PRIME_USER + "...")
        print()

        api = PrimeAPI(PRIME_URL, PRIME_USER, PRIME_PW)

    except Exception as e:
        print("Access to Prime Infrastructure failed.")
        print("==============================")
        print("Exception dump below: ")
        print("==============================")
        print(str(e))
        print("==============================")
        input("Press RETURN to continue...")
        return

    print("Access to PI successful")
    print()
    input("Press RETURN to continue with fetching the alarms from Prime...")
    print()

    # calling our alarm extraction function and writing result to variable
    alarmIDs = fetch_alerts(api)

    # fetching all messages for all prior gathered alerts and writing result to variable
    messages = fetch_alerts_text(alarmIDs, api)

    # piecing together the notification message as string for SPARK and TROPO API calls and saving to variable
    notificationMessage = build_notification_string(messages)

    # pause for better demo effect
    print()
    input("HIT RETURN TO CONTINUE TO SEND THE NOTIFICATION MESSAGE TO SPARK")
    print()

    # post to SPARK
    post_to_spark(notificationMessage)

    # pause for better demo effect
    input("HIT RETURN TO ISSUE THE CALL TO THE TROPO API")
    print()

    # call TROPO API to notify network admin via phone
    issue_tropo_call(notificationMessage)

# helper to call this script as a utility from shell
if __name__ == "__main__":
    main()