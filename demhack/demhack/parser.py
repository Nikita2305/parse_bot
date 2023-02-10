from demhack.utils import SystemObject
import pymorphy2
import string

def get_tokens(text):
    analyser = pymorphy2.MorphAnalyzer()    
    tokens = text.translate(str.maketrans('', '', string.punctuation)).split()
    return [analyser.parse(token)[0].normal_form for token in tokens]

# Could be implemented much faster with hashing and Z-function or another data structure
def contains(text, keyword):
    text_tokens = get_tokens(text)
    keyword_tokens = get_tokens(keyword)
    count = len(text_tokens) - len(keyword_tokens) + 1
    if (count <= 0):
        return False
    for i in range(count):
        ok = True
        for j in range(len(keyword_tokens)):
            if (keyword_tokens[j] != text_tokens[i + j]):
                ok = False
                break
        if ok:
            return True
    return False
    
class ChatParser (SystemObject):

    def __init__(self):
        self.chats = []
        self.keywords = []
        self.source = (0, "НЕ НАСТРОЕН")

    def set_source(self, id, descr=""):
        self.source = (id, descr)

    def add_chat(self, id, descr=""):
        self.chats.append((id, descr))

    def erase_chat(self, id):
        index = self.find_chat(id)
        if (index == -1):
            return
        self.chats.pop(index) 

    def find_chat(self, id):
        for i in range(len(self.chats)):
            if (self.chats[i][0] == id):
                return i
        return -1

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

    def process(self, text, chat_id, bot):
        if self.source[0] == 0:
            return
        source_chat_id = self.source[0]
        index = self.find_chat(chat_id)
        if (index == -1):
            return
        chat = self.chats[index]
        for keyword in self.keywords:
            if contains(text, keyword):
                message = f"Message: {text}\nChat: {chat[1]} \nKeyword: {keyword}"
                bot.send_message(source_chat_id, message)
                return
        
