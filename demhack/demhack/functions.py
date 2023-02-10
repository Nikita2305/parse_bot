from datetime import datetime
from demhack.utils import *
from demhack.access_manager import *
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
    ParseMode
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
            try:
                update.message.reply_text("Ой, кажется была обнаружена ошибка, разработчик оповещён.")
            except Exception as ex:
                self.state.logger.warning(f"Error report was not sent to the user, cause: {ex}")
        except Exception as ex:
            self.state.logger.error(f"Error report was not sent to the admin, cause: {ex}")
            try:
                update.message.reply_text("Ой, кажется была обнаружена ошибка, но не удалось оповестить разработчика. Пожалуйста, свяжитесь с куратором бота.")
            except Exception as ex1:
                self.state.logger.error(f"Nobody got error report!\nCause for admin: {ex}\nCause for user: {ex1}\n")
            

class AddToChat(BasicMessage):
    
    def __init__(self, *args, **kwargs):
        self.help_message = "add_to_chat"
        self.description = ""
        self.permissions = MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context):
        self.state.parser.add_chat(update.message.chat.id, update.message.chat.title)

class Help (BasicMessage):
        
    def __init__(self, *args, **kwargs):
        self.help_message = "help"
        self.description = "Получить помощь"
        self.permissions = MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context):
        print(update, context)
        message = obtain_message(update)
        message.reply_text(self.state.help_texts[self.state.access_manager_obj.get_status(
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
        return BasicDialogue.END

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

class GetKeywords (BasicMessage):
        
    def __init__(self, *args, **kwargs):
        self.help_message = "get_keywords"
        self.description = "Получить ключевые слова"
        self.permissions = MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context):
        keywords = "\n".join(self.state.parser.get_keywords())
        update.message.reply_text(f"Ключевые слова:\n{keywords}")

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

