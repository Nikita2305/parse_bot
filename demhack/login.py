import argparse
import getpass
from pprint import pprint

from telegram_simple.client import Telegram, AuthorizationState

DATABASE_ENC_KEY = "vk_parse_bot_1234"

if __name__ == '__main__':

    PHONE = input("Enter Phone:")
    API_ID = input("Enter Api_id:")
    API_HASH = input("Enter Api_hash:") 

    tg = Telegram(
        api_id=API_ID,
        api_hash=API_HASH,
        phone=PHONE,
        database_encryption_key=DATABASE_ENC_KEY,
    )

    # you must call login method before others
    state = tg.login(blocking=False)

    print ("Checking the return state of the login(blocking=False) function call")

    if state == AuthorizationState.WAIT_CODE:
        print("Pin is required. In this example, the main program is asking it, not the python-telegram client")
        pin = input("Please insert pin code here: ")
        print("In this example, the main program is more polite than the python-telegram client")
        tg.send_code(pin)
        state = tg.login(blocking=False)

    if state == AuthorizationState.WAIT_PASSWORD:
        print("Password is required. In this example, the main program is asking it, not the python-telegram client")
        pwd = getpass.getpass('Insert password here (but please be sure that no one is spying on you): ')
        tg.send_password(pwd)
        state = tg.login(blocking=False)

    print('Authorization state: %s' % tg.authorization_state)

    # tg.add_message_handler(new_message_handler)
    # tg.add_any_update_handler(print_handler)
    # tg.idle()
    
    result = tg.get_me()
    result.wait()
    print(result.update)

    tg.stop()
