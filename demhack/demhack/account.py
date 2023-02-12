from demhack.utils import SystemObject

class AccountInfo:
    def __init__(self, name, app_id, api_hash):
        self.name = name
        self.app_id = app_id
        self.api_hash = api_hash 

class Account:

    def __init__(self, account_info, message_source):
        self.account_info = account_info
        self.source = message_source

    def run(self):
        self.source.add_chat(123, "hardcoded_chat")
        self.source.put("hello world from code", 123)

class AccountHandler (SystemObject):

    def __init__(self):
        self.accounts = []

    def add_account(self, account):
        self.accounts.append(account)

    def erase_account(self, name):
        for i in range(len(self.accounts)):
            if self.accounts[i].account_info.name == name:
                self.accounts.pop(i)
                return

    def get_accounts(self):
        return self.accounts

    def run_all(self):
        for account in self.accounts:
            account.run()
