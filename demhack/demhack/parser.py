
class ChatParser:

    def __init__(self):
        self.chats = []
        self.keywords = []

    def add_chat(self, id, descr=""):
        self.chats.append((id, descr))

    def erase_chat(self, id):
        for i in range(len(self.chats)):
            if (self.chats[i][0] == id):
                self.chats.pop(i)
                return
    
    def get_chats(self):
        return self.chats

    def add_keyword(self, word):
        self.keywords.append(word.lower())

    def erase_keyword(self, word):
        if word not in self.keywords:
            return
        self.keywords.pop(self.keywords.index(word))
    
    def get_keywords(self):
        return self.keywords

    def has_keyword(self):
        # TODO: your code goes here
        return True
