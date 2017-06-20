import requests
requests.packages.urllib3.disable_warnings()
from pushsafer import init, Client
import logging

init("***REMOVED***")
client = Client("")

def notify(msg):
    resp = client.send_message(msg, "PomBru", "4588", "1", "4", "2", "https://www.pushsafer.com", "Open Pushsafer", "0", "", "", "")
    logging.debug("response for push notification '" + msg + "' is: " + str(resp))
