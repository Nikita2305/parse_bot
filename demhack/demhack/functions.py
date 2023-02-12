from datetime import datetime
from demhack.utils import *
from demhack.access_manager import *
from demhack.log_config import BOT_KEY
from demhack.account import Account, AccountInfo
import traceback
import os


from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler
)

from telegram import (
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Document,
    ParseMode,
    ChatMember,
    Bot
)

class ErrorHandler (BasicCommunication):
    def __init__(self, *args, **kwargs):
        self.help_message = ""
        self.description = ""
        self.permissions = 0
        self.callbacks = []
        super().__init__(*args, **kwargs) 

    def execute(self, update, context):
        trace = ''.join(traceback.format_list(traceback.extract_tb(context.error.__traceback__)))
        self.state.logger.error(f"Update:\n{update}\n\nTrace:\n{trace}\nError: {context.error}") 
        try:
            context.bot.send_message(int(ADMIN_ID), "[Unhandled exception]")
        except Exception as ex:
            self.state.logger.debug(f"Error report was not sent to the admin, cause: {ex}")
            

class AddToChat(BasicMessage):
    
    def __init__(self, *args, **kwargs):
        self.help_message = "add_to_chat"
        self.description = ""
        self.permissions = MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context):
        status = update.my_chat_member.new_chat_member.status
        id = update.my_chat_member.chat.id
        title = update.my_chat_member.chat.title
        if (status in [ChatMember.LEFT, ChatMember.RESTRICTED]):
            self.state.parser.get_default_message_source().erase_chat(id) 
        elif (status in [ChatMember.MEMBER,ChatMember.CREATOR, ChatMember.ADMINISTRATOR]):
            self.state.parser.get_default_message_source().add_chat(id, title)
        else:
            self.state.logger.error(f"Unknown status: {status}")

class Help (BasicMessage):
        
    def __init__(self, *args, **kwargs):
        self.help_message = "help"
        self.description = "Получить помощь"
        self.permissions = MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context):
        update.message.reply_text(self.state.help_texts[self.state.access_manager_obj.get_status(
                                str(update.effective_user.id),
                                str(update.effective_user.username))
                            ],
        parse_mode=ParseMode.MARKDOWN)

class GetId (BasicMessage):
        
    def __init__(self, *args, **kwargs):
        self.help_message = "get_id"
        self.description = "Получить свой tg-id"
        self.permissions = USER | MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context):
        self.state.access_manager_obj.get_status(str(update.effective_user.id), str(update.effective_user.username))
        update.message.reply_text(str(update.effective_user.id))

class AddManager (BasicDialogue):

    def __init__(self, *args, **kwargs):
        self.help_message = "add_manager"
        self.description = "Добавить менеджера"
        self.permissions = MANAGER
        self.order = [
            SimpleHelloUnit("Введите его id, или /cancel, если не знаете",
                            entry_message=self.help_message),
            DialogueUnit(self.get_id)
        ]
        super().__init__(*args, **kwargs)

    def get_id(self, update, context):
        try:
            id = int(update.message.text)
        except Exception:
            update.message.reply_text("Введите число - id пользователя Telegram")
            return BasicDialogue.END
        self.state.access_manager_obj.set_status(update.message.text, MANAGER)
        update.message.reply_text("Добавлен " + update.message.text)
        return BasicDialogue.END

class EraseManager (BasicDialogue):

    def __init__(self, *args, **kwargs):
        self.help_message = "erase_manager"
        self.description = "Удалить менеджера"
        self.permissions = MANAGER
        self.order = [
            SimpleHelloUnit("Введите его id, или /cancel, если не знаете",
                            entry_message=self.help_message),
            DialogueUnit(self.get_id)
        ]
        super().__init__(*args, **kwargs)

    def get_id(self, update, context):
        self.state.access_manager_obj.set_status(update.message.text, USER)
        update.message.reply_text("Удалён " + update.message.text)
        return BasicDialogue.END

class AddKeyword (BasicDialogue):

    def __init__(self, *args, **kwargs):
        self.help_message = "add_keyword"
        self.description = "Добавить ключ. слово"
        self.permissions = MANAGER
        self.order = [
            SimpleHelloUnit("Введите слово (или /cancel)",
                            entry_message=self.help_message),
            DialogueUnit(self.get_word)
        ]
        super().__init__(*args, **kwargs)

    def get_word(self, update, context):
        keyword = update.message.text
        self.state.parser.add_keyword(keyword)
        update.message.reply_text(f"Добавлено слово '{keyword}'")
        return BasicDialogue.END

class EraseKeyword (BasicDialogue):

    def __init__(self, *args, **kwargs):
        self.help_message = "erase_keyword"
        self.description = "Удалить ключ. слово"
        self.permissions = MANAGER
        self.order = [
            SimpleHelloUnit("Введите слово (или /cancel)",
                            entry_message=self.help_message),
            DialogueUnit(self.get_word)
        ]
        super().__init__(*args, **kwargs)

    def get_word(self, update, context):
        keyword = update.message.text
        self.state.parser.erase_keyword(keyword)
        update.message.reply_text(f"Удалено слово '{keyword}'")
        return BasicDialogue.END

class ThisIsAdminka (BasicMessage):
        
    def __init__(self, *args, **kwargs):
        self.help_message = "this_is_adminka"
        self.description = "Сделать этот чат админским"
        self.permissions = MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context):
        self.state.parser.get_default_message_source().erase_chat(update.message.chat.id)
        self.state.parser.set_source(update.message.chat.id, update.message.chat.title)
        update.message.reply_text(f"Теперь это админка")

# TODO: fix info!
class GetInfo (BasicMessage):
        
    def __init__(self, *args, **kwargs):
        self.help_message = "get_info"
        self.description = "Админская информация"
        self.permissions = MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context): 
        chats = "\n".join([f"{chat[1]} (id = {chat[0]})" for chat in self.state.parser.get_default_message_source().get_chats()]) 
        keywords = "\n".join(self.state.parser.get_keywords())
        ret = self.state.access_manager_obj.get_managers()
        admins = "\n".join(["@" + x[1] + " (" + x[0] + ")" for x in ret])

        reply_text = f"Админский чат: {self.state.parser.source[1]}, (id = {self.state.parser.source[0]})\n\n"
        reply_text += f"Ключевые слова:\n{keywords}" + ("\n\n" if keywords else "\n")
        reply_text += f"Список чатов:\n{chats}" + ("\n\n" if chats else "\n")
        reply_text += f"Список админов:\n{admins}" + ("\n\n" if admins else "\n")
        reply_text += f"Помощь: /help"
        update.message.reply_text(reply_text) 

class ParseTextMessage (BasicMessage):
        
    def __init__(self, *args, **kwargs):
        self.help_message = ""
        self.description = ""
        self.permissions = USER | MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context):
        id = update.message.chat.id
        text = update.message.text
        self.state.parser.get_default_message_source().put(text, id)

class AddAccount (BasicDialogue):

    def __init__(self, *args, **kwargs):
        self.help_message = "add_account"
        self.description = "Добавить аккаунт"
        self.permissions = MANAGER
        self.order = [
            SimpleHelloUnit("Придумайте nickname (или /cancel)",
                            entry_message=self.help_message),
            DialogueUnit(self.get_nickname),
            DialogueUnit(self.get_app_id),
            DialogueUnit(self.get_api_hash)
        ]
        super().__init__(*args, **kwargs)

    def get_nickname(self, update, context):
        context.user_data["nickname"] = update.message.text
        update.message.reply_text(f"Введите app_id (или /cancel)")
        return BasicDialogue.NEXT

    def get_app_id(self, update, context):
        context.user_data["app_id"] = update.message.text
        update.message.reply_text(f"Введите api_hash (или /cancel)")
        return BasicDialogue.NEXT

    def get_api_hash(self, update, context):
        nickname = context.user_data["nickname"]
        app_id = context.user_data["app_id"]
        api_hash = update.message.text
        acc_info = AccountInfo(nickname, app_id, api_hash)
        new_message_source = self.state.parser.allocate_message_source()
        account = Account(acc_info, new_message_source)
        self.state.account_handler.add_account(account)
        update.message.reply_text(f"Добавлен аккаунт {nickname}")
        account.run()
        return BasicDialogue.END

class EraseAccount (BasicDialogue):

    def __init__(self, *args, **kwargs):
        self.help_message = "erase_account"
        self.description = "Удалить аккаунт"
        self.permissions = MANAGER
        self.order = [
            SimpleHelloUnit("Введите ник удаляемого (или /cancel)",
                            entry_message=self.help_message),
            DialogueUnit(self.get_nickname)
        ]
        super().__init__(*args, **kwargs)

    def get_nickname(self, update, context):
        nickname = update.message.text
        self.state.account_handler.erase_account(nickname)
        update.message.reply_text(f"Удален аккаунт {nickname}")
        return BasicDialogue.END

"""
class GetKeywords (BasicMessage):
        
    def __init__(self, *args, **kwargs):
        self.help_message = "get_keywords"
        self.description = "Получить ключевые слова"
        self.permissions = MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context):
        keywords = "\n".join(self.state.parser.get_keywords())
        update.message.reply_text(f"Ключевые слова:\n{keywords}")

class GetChats (BasicMessage):
        
    def __init__(self, *args, **kwargs):
        self.help_message = "get_chats"
        self.description = "Получить список чатов"
        self.permissions = MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context):
        chats = "\n".join([f"{chat[1]} (id = {chat[0]})" for chat in self.state.parser.get_chats()])
        update.message.reply_text(f"Список чатов:\n{chats}")

class EraseCurrentChat (BasicMessage):
        
    def __init__(self, *args, **kwargs):
        self.help_message = "throw_chat"
        self.description = "Удалить этот чат из выборки"
        self.permissions = MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context):
        self.state.parser.erase_chat(update.message.chat.id)
        update.message.reply_text(f"Удалён из выборки")

class GetManagers (BasicMessage):
        
    def __init__(self, *args, **kwargs):
        self.help_message = "get_managers"
        self.description = "Получить список менеджеров"
        self.permissions = MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context):
        ret = self.state.access_manager_obj.get_managers()
        s = "Вот они, сверху вниз:\n"
        for x in ret:
            s += "@" + x[1] + " (" + x[0] + ")\n"
        update.message.reply_text(s)
"""
