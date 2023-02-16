from demhack.utils import SystemObject, DATABASE_ENC_KEY
from telegram_simple.client import Telegram, AuthorizationState
import threading
import multiprocessing
import time
import queue

class AccountInfo:
    def __init__(self, phone, app_id, api_hash):
        self.phone = phone
        self.app_id = app_id
        self.api_hash = api_hash

    def get_session(self):
        return Telegram(
                    api_id=self.app_id,
                    api_hash=self.api_hash,
                    phone=self.phone,
                    database_encryption_key=DATABASE_ENC_KEY
        )

    def get_state(self):
        session = self.get_session()
        state = session.login(blocking=False)
        session.stop()
        return state

    def is_ready(self):
        return self.get_state() == AuthorizationState.READY 

"""
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
        thread = threading.Thread(target=self.server_event_loop)
        thread.daemon = True
        thread.start()
        self.process = multiprocessing.Process(target=self.client_event_loop)
        self.daemon = True
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
        session = self.account_info.get_session()
        session.login(blocking=False)
        session.add_message_handler(self.client_message_handler)
        session.idle()

    def client_message_handler(self, update):
        self.queue.put(update)

    def server_message_handler(self, update):
        # self.source.put("hello world from code", 123) # дёргаем за ручку
        # self.source.add_chat(id, title) # дергаем за другую ручку # TODO
        # self.source.erase_chat(id, title) # дергаем за третью ручку # TODO

        message_content = update['message']['content']
        if message_content['@type'] == 'messageText': 
            message_text = message_content.get('text', {}).get('text', '').lower()
            chat_id = update['message']['chat_id']
            self.source.put(message_text, chat_id)

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
        if (index != -1):
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
