from demhack.utils import SystemObject, DATABASE_ENC_KEY, CODE_PATH
from demhack.log_config import LOGGING_CONFIG, toplevel
from telegram_simple.client import Telegram, AuthorizationState
import threading
import multiprocessing
import time
import queue
import copy
import logging.config

class AccountInfo:
    def __init__(self, phone, app_id, api_hash):
        self.phone = phone
        self.app_id = app_id
        self.api_hash = api_hash
        self.id = None

    def get_session(self):
        return Telegram(
                    api_id=self.app_id,
                    api_hash=self.api_hash,
                    phone=self.phone,
                    database_encryption_key=DATABASE_ENC_KEY,
                    files_directory=f'{CODE_PATH}/.tdlib_files/'
        )

    def get_state(self):
        session = self.get_session()
        state = session.login(blocking=False)
        session.stop()
        return state

    def is_ready(self):
        return self.get_state() == AuthorizationState.READY

    def calculate_id(self):
        session = self.get_session()
        session.login(blocking=False)
        result = session.get_me()
        result.wait()
        self.id = result.update["id"]
        session.stop()

"""
    # deprecated because of telegram-secutity-measure which prohibits sending codes by tg
    # and then prohibits interative login
    def provide_with_code(self, code):
        session = self.get_session()
        session.send_code(code)
        session.stop()

    def provide_with_password(self, password):
        session = self.get_session()
        session.send_password(password)
        session.stop()
"""

class Account:

    def __init__(self, account_info, message_source):
        self.account_info = account_info
        self.source = message_source
        self.queue = multiprocessing.Queue() # None btw 
        self.is_active = True
        self.process = None 
    
    def run(self):
        if (not self.account_info.is_ready()):
            raise RuntimeError(f"Not Ready account {self.account_info.phone}")
        self.account_info.calculate_id()
        thread = threading.Thread(target=self.server_event_loop)
        thread.daemon = True
        thread.start()
        self.process = multiprocessing.Process(target=self.client_event_loop)
        self.process.daemon = True
        self.process.start()
  
    def stop(self):
        self.is_active = False
        self.process.terminate()
 
    def server_event_loop(self):
        try:
            while (self.is_active):
                try:
                    update = self.queue.get(timeout=10)
                    self.server_message_handler(update)
                except queue.Empty:
                    continue
        except Exception as ex:
            print(f"serverside error {ex}")

    def client_event_loop(self):
        account_id = self.account_info.phone

        local_config = copy.deepcopy(LOGGING_CONFIG)
        local_config["handlers"]["stream_handler"]["filename"] = f"{CODE_PATH}/logs_{account_id}.txt"
        logging.config.dictConfig(local_config)
        logger = logging.getLogger(toplevel)
        logger.warning("Client event loop is going to run")
         
        self.session = self.account_info.get_session()
        self.session.login(blocking=False)
        self.session.add_message_handler(self.client_message_handler)
        while True:
            logger.warning("Client event loop is running")
            for i in range(3):
                try:
                    self.session.idle()
                except Exception as ex:
                    logger.warning(f"Error in client event loop on account {account_id}, attempt={i} : {ex}")
                    time.sleep(10)
            logger.error(f"Account {account_id} is sleeping for 60 min. Consider relogin.")
            time.sleep(3600)

    def client_message_handler(self, update):
        # print(update)
        message_content = update['message']['content']
        type = message_content['@type']
        if (type == 'messageChatAddMembers' and (self.account_info.id in message_content["member_user_ids"]) or type == 'messageChatJoinByLink'):
            result = self.session.get_chat(update['message']['chat_id'])
            result.wait() 
            chat_descr = result.update
            update['message']['chat_title'] = chat_descr['title']
        self.queue.put(update)

    def server_message_handler(self, update):
        # print(self.source.get_chats())
        message_content = update['message']['content']
        type = message_content['@type']
        if type == 'messageText': 
            message_text = message_content.get('text', {}).get('text', '').lower()
            chat_id = update['message']['chat_id']
            self.source.put(message_text, chat_id)
        elif ((type in ['messageChatAddMembers', 'messageChatJoinByLink']) and update["message"]["is_outgoing"]):
            # WAS: and (self.account_info.id in message_content["member_user_ids"]))
            id = update['message']['chat_id']
            chat_title = update['message']['chat_title']
            self.source.add_chat(id, chat_title)
        elif type == 'messageChatDeleteMember' and self.account_info.id == message_content["user_id"]:
            self.source.erase_chat(update['message']['chat_id'])

class AccountHandler (SystemObject):

    def __init__(self):
        self.accounts = []

    def add_account(self, account):
        if (self.find_account(account.account_info.phone) != -1):
            return
        self.accounts.append(account)
        account.run()

    def erase_account(self, phone):
        index = self.find_account(phone)
        if (index == -1):
            return
        self.accounts[index].stop()
        self.accounts.pop(index)

    def find_account(self, phone):
        for i in range(len(self.accounts)):
            if self.accounts[i].account_info.phone == phone:
                return i
        return -1

    def get_accounts(self):
        return self.accounts

    def setup_with_parser(self, parser):
        for account in self.accounts:
            account.source.parser = parser
            account.queue = multiprocessing.Queue()

    def run_all(self):
        for account in self.accounts:
            account.run()

    def unlock_all(self):
        for account in self.accounts:
            account.source.unlock()
