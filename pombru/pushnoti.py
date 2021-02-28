"Send a push notification to my phone"
import argparse
import logging
import sys

from pushsafer import init, Client
import requests
requests.packages.urllib3.disable_warnings()

__CLIENT = None
def pushnoti_init():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pushsafer_key", required=True, type=str, help="PushSafer private key")
    args = parser.parse_args()

    init(args.pushsafer_key)
    global __CLIENT
    __CLIENT = Client("")

def notify(msg):
    try:
        resp = __CLIENT.send_message(msg, "PomBru", "36659", "1", "4", "2", "https://www.pushsafer.com", "Open Pushsafer", "0", "", "", "")
        logging.debug("response for push notification '" + msg + "' is: " + str(resp))
    except:
        logging.error("Error while sending push notification: " + sys.exc_info()[0])

if __name__ == "__main__":
    print("trying to send test message")
    pushnoti_init()
    notify("hello")
