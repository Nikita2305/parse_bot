from demhack.utils import SystemObject
import threading

class AccountInfo:
    def __init__(self, phone, app_id, api_hash):
        self.phone = phone
        self.app_id = app_id
        self.api_hash = api_hash 

class Account:

    def __init__(self, account_info, message_source):
        self.account_info = account_info
        self.source = message_source

    def run(self):
        thread = threading.Thread(target=self.event_loop)
        thread.daemon = True
        thread.start()
        
        # self.source.put("hello world from code", 123) # дёргаем за ручку
        # self.source.add_chat(id, title) # дергаем за другую ручку
        # self.source.erase_chat(id, title) # дергаем за третью ручку
    
    def event_loop(self):
        return

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
