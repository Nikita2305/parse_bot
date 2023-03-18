import argparse
import getpass
from pprint import pprint
import json
import os

from telegram_simple.client import Telegram, AuthorizationState

DATABASE_ENC_KEY = "vk_parse_bot_1234"
CODE_PATH = os.path.dirname(os.path.abspath(__file__)) + "/demhack"

def main(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)    
        PHONE = config["phone"]
        API_ID = config["api_id"]
        API_HASH = config["api_hash"]
        PASSWORD = None
        if "password" in config:
            PASSWORD = config["password"]

    print(PHONE)

    tg = Telegram(
        api_id=API_ID,
        api_hash=API_HASH,
        phone=PHONE,
        database_encryption_key=DATABASE_ENC_KEY,
        files_directory=f'{CODE_PATH}/.tdlib_files/'
    )

    # you must call login method before others
    state = tg.login(blocking=False)

    # print ("Checking the return state of the login(blocking=False) function call")

    if state == AuthorizationState.WAIT_CODE:
        # print("Pin is required. In this example, the main program is asking it, not the python-telegram client")
        pin = input("Please insert pin code here: ")
        # print("In this example, the main program is more polite than the python-telegram client")
        tg.send_code(pin)
        state = tg.login(blocking=False)

    if state == AuthorizationState.WAIT_PASSWORD:
        # print("Password is required. In this example, the main program is asking it, not the python-telegram client")
        # pwd = getpass.getpass('Insert password here (but please be sure that no one is spying on you): ')
        if PASSWORD is None:
            tg.stop()
            print("Error: no second-factor password in config file") 
            quit()
        tg.send_password(PASSWORD)
        state = tg.login(blocking=False)

    print('Authorization state: %s' % tg.authorization_state)

    result = tg.get_me()
    result.wait()
    print(result.update)

    tg.stop()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Auth tg-acc on the server')
    parser.add_argument("input", help='.config file')
    args = parser.parse_args()
    if args.input is None:
        print("Expected path to .config file")
        quit()
    main(args.input)
