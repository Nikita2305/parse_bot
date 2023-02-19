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

class Guide (BasicMessage):
        
    def __init__(self, *args, **kwargs):
        self.help_message = "guide"
        self.description = "Гайд по использованию"
        self.permissions = MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context):
        guide = "\n".join([
            'Guide:',
            '1. Первоначальная настройка бота: добавить бота в админский чат и нажать /this_is_adminka в этом чате. Чтобы дать кому-то (допустим Ване) полномочия работать с ботом, нужно узнать его айдишник в телеграме (Ваня должен нажать /get_id), а затем админ должен нажать /add_manager и добавить ванин айдишник.\n',
            '2. Добавление телеграм-аккаунта для парсинга в три этапа: получить api_id, api_hash по этому гайду https://docs.telethon.dev/en/stable/basic/signing-in.html. Затем отправить phone, api_id, и api_hash тех. специалисту - он авторизует аккаунт на сервере. Затем нажать /add_account и следовать инструкциям.\n',
            '3. Работа с ботом осуществляется посредствам двух видов команд: работа с ключевыми словами (/add_keyword, /erase_keyword) и работа с чатами (/add_chat, /erase_chat). Если вы нажали /add_keyword а затем передумали его добавлять, нажмите /cancel. Это прервёт диалог добавления слова и позволит корректно начать новый диалог.'
        ])
        update.message.reply_text(guide)

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
        try:
            id = int(update.message.text)
        except Exception as ex:
            update.message.reply_text("Необходимо число")
            return BasicDialogue.END
        self.state.access_manager_obj.set_status(id, USER)
        update.message.reply_text(f"Удалён {id}")
        return BasicDialogue.END

class AddChat (BasicDialogue):

    def __init__(self, *args, **kwargs):
        self.help_message = "add_chat"
        self.description = "Добавить чат(ы)"
        self.permissions = MANAGER
        self.order = [
            SimpleHelloUnit("Введите номер телефона (можно нажать и /bot, это нужно для работы с чатами бота, а не аккаунта) (или /cancel)",
                            entry_message=self.help_message),
            DialogueUnit(self.get_source),
            DialogueUnit(self.get_chat_id)
        ]
        super().__init__(*args, **kwargs)

    def get_source(self, update, context):
        source = update.message.text.strip()
        context.user_data["source"] = source
        if (source == '/bot' or
            (source in [account.account_info.phone for account in self.state.account_handler.get_accounts()])):
            update.message.reply_text("Введите чат(ы) в следующем формате:\nchat_id chat_name. Чтобы добавить несколько чатов, можно отправить одно сообщение из нескольких строк в таком формате.")
            return BasicDialogue.NEXT
        update.message.reply_text("Не найден такой телефон.")
        return BasicDialogue.END

    def get_chat_id(self, update, context): 
        source_str = context.user_data["source"]
        source_obj = self.state.parser.get_default_message_source()
        if (source_str != '/bot'):
            account_ind = self.state.account_handler.find_account(source_str)
            if (account_ind == -1):
                update.message.reply_text(f"Не найден такой телефон")
                return BasicDialogue.END
            account = self.state.account_handler.accounts[account_ind]
            source_obj = account.source

        chats = update.message.text.split("\n")
        chat_pairs = []
        for chat_descr in chats:
            units = chat_descr.strip().split()
            if (len(units) == 0):
                update.message.reply_text(f"Ошибка формата в строке {chat_descr}, повторите запрос с исправлением")
                return BasicDialogue.END
            try:
                id = int(units[0])
                descr = " ".join(units[1:])
            except Exception as ex:
                update.message.reply_text(f"Ошибка формата в строке {chat_descr}, повторите запрос с исправлением")
                return BasicDialogue.END
            chat_pairs += [(id, descr)]

        for id, descr in chat_pairs:
            source_obj.add_chat(id, descr)
        update.message.reply_text("Добавлены!")
        return BasicDialogue.END

class EraseChat (BasicDialogue):

    def __init__(self, *args, **kwargs):
        self.help_message = "erase_chat"
        self.description = "Удалить чат(ы)"
        self.permissions = MANAGER
        self.order = [
            SimpleHelloUnit("Введите номер телефона (можно нажать и /bot, это нужно для работы с чатами бота, а не аккаунта) (или /cancel)",
                            entry_message=self.help_message),
            DialogueUnit(self.get_source),
            DialogueUnit(self.get_chat_id)
        ]
        super().__init__(*args, **kwargs)

    def get_source(self, update, context):
        source = update.message.text.strip()
        context.user_data["source"] = source
        if (source == '/bot' or
            (source in [account.account_info.phone for account in self.state.account_handler.get_accounts()])):
            update.message.reply_text("Введите число chat_id. Чтобы удалить несколько чатов, можно отправить одно сообщение из нескольких строк в таком формате.")
            return BasicDialogue.NEXT
        update.message.reply_text("Не найден такой телефон.")
        return BasicDialogue.END

    def get_chat_id(self, update, context): 
        source_str = context.user_data["source"]
        source_obj = self.state.parser.get_default_message_source()
        if (source_str != '/bot'):
            account_ind = self.state.account_handler.find_account(source_str)
            if (account_ind == -1):
                update.message.reply_text(f"Не найден такой телефон")
                return BasicDialogue.END
            account = self.state.account_handler.accounts[account_ind]
            source_obj = account.source

        chats = update.message.text.split("\n")
        chat_ids = []
        for chat_descr in chats:
            try:
                id = int(chat_descr.strip())
            except Exception as ex:
                update.message.reply_text(f"Ошибка формата в строке {chat_descr}, повторите запрос с исправлением")
                return BasicDialogue.END
            chat_ids += [id]

        for id in chat_ids:
            source_obj.erase_chat(id)
        update.message.reply_text("Удалены!")
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
        if (keyword.startswith("/")):
            update.message.reply_text(f"Не стоит добавлять '{keyword}' в качестве ключевого")
            return BasicDialogue.END
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

class GetInfo (BasicMessage):
        
    def __init__(self, *args, **kwargs):
        self.help_message = "get_info"
        self.description = "Админская информация"
        self.permissions = MANAGER
        super().__init__(*args, **kwargs)

    def execute(self, update, context): 
        chats = "\n".join([f"{chat[1]} ({chat[0]})" for chat in self.state.parser.get_default_message_source().get_chats()]) 
        keywords = "\n".join(self.state.parser.get_keywords())
        ret = self.state.access_manager_obj.get_managers()
        admins = "\n".join(["@" + x[1] + " (" + x[0] + ")" for x in ret])
        accounts_chats = ""
        for account in self.state.account_handler.get_accounts():
            accounts_chats += f"---{account.account_info.phone}---\n"
            for chat in account.source.get_chats():
                accounts_chats += f"{chat[1]} ({chat[0]})\n" 

        reply_text = f"Админский чат: {self.state.parser.source[1]}, ({self.state.parser.source[0]})\n\n"
        reply_text += f"Ключевые слова:\n{keywords}" + ("\n\n" if keywords else "\n")
        reply_text += f"Список чатов бота:\n{chats}" + ("\n\n" if chats else "\n")
        reply_text += f"Список доп. чатов:\n{accounts_chats}\n"
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
        try:
            id = update.message.chat.id
            text = update.message.text
        except Exception as ex:
            self.state.logger.debug(f"ParseMessageFromBot: {ex}")
            return
        self.state.parser.get_default_message_source().put(text, id)

class AddAccount (BasicDialogue):

    def __init__(self, *args, **kwargs):
        self.help_message = "add_account"
        self.description = "Добавить аккаунт"
        self.permissions = MANAGER
        self.order = [
            SimpleHelloUnit("Введите телефон, как при регистрации (или /cancel)",
                            entry_message=self.help_message),
            DialogueUnit(self.get_phone),
            DialogueUnit(self.get_app_id),
            DialogueUnit(self.get_api_hash) # ,
            # DialogueUnit(self.solve_problem_1),
            # DialogueUnit(self.solve_problem_2)
        ]
        super().__init__(*args, **kwargs)

    def get_phone(self, update, context):
        phone = update.message.text.strip()
        context.user_data["phone"] = phone
        update.message.reply_text(f"Введите app_id (или /cancel)")
        return BasicDialogue.NEXT

    def get_app_id(self, update, context):
        try:
            app_id = int(update.message.text.strip())
        except Exception:
            update.message.reply_text("Введите число - app_id")
            return BasicDialogue.END
        context.user_data["app_id"] = app_id
        update.message.reply_text(f"Введите api_hash (или /cancel)")
        return BasicDialogue.NEXT

    def get_api_hash(self, update, context):
        context.user_data["api_hash"] = update.message.text
        
        acc_info = self.create_account_info(update, context)

        if (acc_info.is_ready()):
            self.create_account(update, context)
        else:
            update.message.reply_text(f"Аккаунт не определён на сервере, обратитесь к админу.")

        return BasicDialogue.END

    def create_account(self, update, context):
        acc_info = self.create_account_info(update, context)
        new_message_source = self.state.parser.allocate_message_source()
        account = Account(acc_info, new_message_source)
        self.state.account_handler.add_account(account)
        update.message.reply_text(f"Добавлен аккаунт {acc_info.phone}")

    def create_account_info(self, update, context):
        return AccountInfo(context.user_data["phone"], context.user_data["app_id"], context.user_data["api_hash"])

"""
    def solve_problem_1(self, update, context):
        problem = context.user_data["problem"] 
        solution = update.message.text
        print(f"{problem}: {solution}")
        acc_info = self.create_account_info(update, context)
        print("created")
        if (problem == "code"):
            acc_info.provide_with_code(solution)
        if (problem == "password"):
            acc_info.provide_with_password(solution)
        print("provided")
        if (acc_info.is_ready()):
            print("ready")
            acc_info.stop()
            print("stopped")
            self.create_account(update, context)
            print("created")
            return BasicDialogue.END
        elif (problem == "code" and acc_info.needs_password()):
            print("needs pass")
            acc_info.stop()
            print("stopped")
            update.message.reply_text(f"Введите password")
            return BasicDialogue.NEXT
        acc_info.stop()
        update.message.reply_text(f"Ошибка, неверный ввод")
        return BasicDialogue.END
        
    def solve_problem_2(self, update, context):
        solution = update.message.text
        acc_info = self.create_account_info(update, context)
        acc_info.provide_with_password(solution)
        if (acc_info.is_ready()):
            acc_info.stop()
            self.create_account(update, context)
            return BasicDialogue.END
        acc_info.stop()
        update.message.reply_text(f"Ошибка, неверный ввод")
        return BasicDialogue.END 
"""

class EraseAccount (BasicDialogue):

    def __init__(self, *args, **kwargs):
        self.help_message = "erase_account"
        self.description = "Удалить аккаунт"
        self.permissions = MANAGER
        self.order = [
            SimpleHelloUnit("Введите телефон удаляемого (или /cancel)",
                            entry_message=self.help_message),
            DialogueUnit(self.get_phone)
        ]
        super().__init__(*args, **kwargs)

    def get_phone(self, update, context):
        phone = update.message.text
        self.state.account_handler.erase_account(phone)
        update.message.reply_text(f"Удален аккаунт {phone}")
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
