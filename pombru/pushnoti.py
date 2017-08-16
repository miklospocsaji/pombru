"Send a push notification to my phone"
import logging
import sys

from pushsafer import init, Client
import requests
requests.packages.urllib3.disable_warnings()

init("***REMOVED***")
__CLIENT = Client("")

def notify(msg):
    try:
        resp = __CLIENT.send_message(msg, "PomBru", "4588", "1", "4", "2", "https://www.pushsafer.com", "Open Pushsafer", "0", "", "", "")
        logging.debug("response for push notification '" + msg + "' is: " + str(resp))
    except:
        logging.error("Error while sending push notification: " + sys.exc_info()[0])
