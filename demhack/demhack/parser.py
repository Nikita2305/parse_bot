from demhack.utils import SystemObject
import pymorphy2
import string
from demhack.log_config import BOT_KEY
from telegram import Bot
import threading

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

class MessageSource:
    
    def __init__(self, parser):
        self.chats = []
        self.parser = parser

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

    def put(self, text, chat_id):
        index = self.find_chat(chat_id)
        if (index == -1):
            return
        chat = self.chats[index]
        self.parser.process(text, chat[1])

class MessageParser (SystemObject):

    def __init__(self):
        self.default_source = self.allocate_message_source()
        self.keywords = []
        self.source = (0, "НЕ НАСТРОЕН")
        self.mutex = threading.Lock()

    def set_source(self, id, descr=""):
        self.mutex.acquire()
        self.source = (id, descr)
        self.mutex.release()

    def add_keyword(self, word):
        self.mutex.acquire()
        self.keywords.append(word.lower())
        self.mutex.release()

    def erase_keyword(self, word):
        self.mutex.acquire()
        if word not in self.keywords:
            self.mutex.release()
            return
        self.keywords.pop(self.keywords.index(word))
        self.mutex.release()
    
    def get_keywords(self):
        return self.keywords

    def get_default_message_source(self): 
        return self.default_source

    def allocate_message_source(self):
        return MessageSource(self)

    def process(self, text, chat_title):
        self.mutex.acquire()
        if self.source[0] == 0:
            self.mutex.release()
            return
        source_chat_id = self.source[0]
 
        for keyword in self.keywords:
            if contains(text, keyword):
                message = f"Message: {text}\nChat: {chat_title} \nKeyword: {keyword}"
                Bot(BOT_KEY).send_message(source_chat_id, message)
                self.mutex.release()
                return
        self.mutex.release()
