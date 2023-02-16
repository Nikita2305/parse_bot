import os
from demhack.access_manager import *
from demhack.functions import *
from demhack.log_config import *
from demhack.parser import *
from functools import wraps
from demhack.account import *
import multiprocessing

from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    CallbackQueryHandler,
    ConversationHandler
)

def dump_system(state):
    state.logger.debug("Dumping system...") 
    
    state.access_manager_obj.dump(manager_path)
    
    state.parser.dump(parser_path)

    # fixing jsonpiclke trouble. consider use fail_safe parameter
    queues = []
    for account in state.account_handler.accounts:
        queues.append(account.queue)
        account.queue = None
    state.account_handler.dump(account_handler_path)
    for account, queue in zip(state.account_handler.accounts, queues):
        account.queue = queue

    state.logger.debug("Successful!")

# deprecated menu_sender
def help_decorator(function, state):
    @wraps(function)
    def decorated(update, context):
        return function(update, context)
    return decorated

def cancel_decorator(function, state):
    @wraps(function)
    def decorated(update, context):
        message = obtain_message(update, state.logger, delete=False)
        if message is not None:    
            state.logger.debug(f"text: {message.text}\nuser: @{update.effective_user.username}")
            if (message.text == "/cancel"):
                state.logger.debug(f"~{function.__name__}() by cancel")
                return cancel(update, context)
        ret = function(update, context)
        dump_system(state)
        return ret
    return help_decorator(decorated, state)

def access_decorator(function, state):
    @wraps(function)
    def decorated(update, context):
        message = obtain_message(update, state.logger, delete=False) 
        if message is not None:
            state.logger.debug(f"text: {message.text}\nuser: @{update.effective_user.username}")
            user_permissions = state.access_manager_obj.get_status(str(update.effective_user.id), str(update.effective_user.username))
            if (not function in state.permissions[user_permissions]):
                state.logger.warning(f"Access denied for update: {update}")
                # message.reply_text("Нет доступа к данной операции")
                state.logger.debug(f"~{function.__name__}() by cancel")
                return ConversationHandler.END
        ret = function(update, context)
        dump_system(state) 
        return ret
    return help_decorator(decorated, state)           

# ============ ADDING HANDLERS ==============

class State:
    
    def __init__(self, logger, access_manager_obj, permissions, help_texts, parser, account_handler):
        self.logger = logger
        self.access_manager_obj = access_manager_obj
        self.permissions = permissions
        self.help_texts = help_texts 
        self.parser = parser
        self.account_handler = account_handler

def useless_f(update, context):
    pass

def main(logger, access_manager_obj, parser, account_handler):
    updater = Updater(BOT_KEY, use_context=True)
    dp = updater.dispatcher
    scenarios = [
        AddToChat(ChatMemberHandler(useless_f, ChatMemberHandler.MY_CHAT_MEMBER), show_help=False),
 
        PermissionHelpText("\n*MANAGER HELP:*\n", MANAGER),

        Help(),
        GetId(), 
        ThisIsAdminka(),

        PermissionHelpText("\n", MANAGER),
    
        GetInfo(),

        PermissionHelpText("\n*SETTINGS:*\n", MANAGER), 

        AddAccount(),
        EraseAccount(),

        AddKeyword(),
        EraseKeyword(),

        AddManager(),
        EraseManager(),

        ParseTextMessage(handler=MessageHandler(Filters.text & ~Filters.command, useless_f), show_help=False)
    ]
    
    help_texts = {USER: "", MANAGER: ""}
    permissions = {USER: [], MANAGER: []} 
 
    state = State(logger, access_manager_obj, permissions, help_texts, parser, account_handler)
 
    for new_obj in scenarios:
        state.logger.info(f"Adding handler: {new_obj}")
        if isinstance(new_obj, PermissionHelpText):
            for level in [USER, MANAGER]:
                if new_obj.permissions & level != 0:
                    state.help_texts[level] += new_obj.text
            continue
            
        new_obj.configure_globals(state)
        for level in [USER, MANAGER]:
            if level & new_obj.permissions != 0:
                if (new_obj.help_message is not None and new_obj.show_help):
                    command = new_obj.help_message.replace("_", "\_")
                    description = new_obj.description.replace("_", "\_")
                    state.help_texts[level] += f"/{command} - {description}\n"
                state.permissions[level] += [new_obj.get_callbacks()[0]]

        for i, callback in enumerate(new_obj.get_callbacks()):
            decorator = cancel_decorator
            if (i == 0):
                decorator = access_decorator
            new_obj.get_callbacks()[i] = decorator(callback, state)
       
        dp.add_handler(new_obj.convert_to_telegram_handler())

    error_handler = ErrorHandler()
    error_handler.configure_globals(state) 
    dp.add_error_handler(error_handler.execute)

    state.account_handler.setup_with_parser(state.parser) # problem of references + jsonpickle
    state.account_handler.run_all()

    logger.debug("Polling was started")
    updater.start_polling()
    updater.idle()

def declare_globals():
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(toplevel)
    logger.warning("Bot is running now, logging enabled")
 
    access_manager_obj = AccessManager()
    try:
        access_manager_obj = access_manager_obj.load(manager_path)
        logger.debug("Loaded access_manager from file")
    except Exception as e: 
        logger.debug(str(e))
    access_manager_obj.set_status(ADMIN_ID, MANAGER)

    parser = MessageParser()
    try:
        parser = parser.load(parser_path)
        logger.debug("Loaded parser from file")
    except Exception as e: 
        logger.debug(str(e))
   
    account_handler = AccountHandler()
    try:
        account_handler = account_handler.load(account_handler_path)
        logger.debug("Loaded accounts from file")
    except Exception as e: 
        logger.debug(str(e))
 
    return logger, access_manager_obj, parser, account_handler
    

# Any function wrapped with one of {access, cancel}_decorator to
# automatically dumps system
# automatically sends menu, when cancel or finish of dialogue

if __name__ == '__main__':
    multiprocessing.freeze_support()
    args = declare_globals() 
    main(*args)
