from demhack.utils import SystemObject, DATABASE_ENC_KEY
from telegram_simple.client import Telegram, AuthorizationState
import threading

class AccountInfo:
    def __init__(self, phone, app_id, api_hash):
        self.phone = phone
        self.app_id = app_id
        self.api_hash = api_hash
        self.tg = Telegram(api_id=app_id, api_hash=api_hash, phone=phone, database_encryption_key="changekey123")
        self.relogin()

    def needs_code(self):
        return self.tg.authorization_state == AuthorizationState.WAIT_CODE

    def provide_with_code(self, code):
        tg.send_code(code)
        self.relogin()

    def needs_password(self):
        return self.tg.authorization_state == AuthorizationState.WAIT_PASSWORD

    def provide_with_password(self, password):
        tg.send_password(password)
        self.relogin()

    def is_ready(self):
         return self.tg.authorization_state == AuthorizationState.READY

    def relogin(self):
        self.tg.login(blocking=False)

    def stop(self):
        self.tg.stop()

class Account:

    def __init__(self, account_info, message_source):
        self.account_info = account_info
        self.source = message_source
        self.source.add_chat(123) # TODO

    def run(self):
        thread = threading.Thread(target=self.event_loop)
        thread.daemon = True
        thread.start() 
    
    def event_loop(self):
        self.account_info.tg.add_message_handler(self.message_handler)
        self.account_info.tg.idle()
        print("stopped")
        self.account_info.tg.stop()

    def message_handler(self, update):
        # self.source.put("hello world from code", 123) # дёргаем за ручку
        # self.source.add_chat(id, title) # дергаем за другую ручку
        # self.source.erase_chat(id, title) # дергаем за третью ручку
        print(update)
        self.source.put(len(str(update)), 123)

class AccountHandler (SystemObject):

    def __init__(self):
        self.accounts = []

    def add_account(self, account):
        if (self.find_account(account.account_info.phone) != -1):
            return
        self.accounts.append(account)

    def erase_account(self, phone):
        index = self.find_account(phone)
        if (index != -1):
            return
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

    def run_all(self):
        for account in self.accounts:
            account.run()
