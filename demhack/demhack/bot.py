import os
from demhack.access_manager import *
from demhack.functions import *
from demhack.log_config import *
from demhack.parser import *
from functools import wraps

from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    CallbackQueryHandler,
    ConversationHandler
)

# TODO: do not forget to dump ChatParser here

def dump_system(state):
    state.logger.debug("Dumping system...") 
    state.access_manager_obj.dump(manager_path)
    state.logger.debug("Successful!")

def help_decorator(function, state):
    @wraps(function)
    def decorated(update, context):
        ret = function(update, context)
        """
        if (ret == ConversationHandler.END):
            send_menu(update, context, state)
        """
        return ret
    return decorated

def cancel_decorator(function, state):
    @wraps(function)
    def decorated(update, context):
        message = obtain_message(update, state.logger, delete=False)
        state.logger.debug(f"{function.__name__}()\ntext: {message.text}\nuser: @{update.effective_user.username}")
        if (message.text == "/cancel"):
            state.logger.debug(f"~{function.__name__}() by cancel")
            return cancel(update, context)
        ret = function(update, context)
        state.logger.debug(f"~{function.__name__}()")
        dump_system(state)
        return ret
    return help_decorator(decorated, state)

def access_decorator(function, state):
    @wraps(function)
    def decorated(update, context):
        message = obtain_message(update, state.logger, delete=False) 
        state.logger.debug(f"{function.__name__}()\ntext: {message.text}\nuser: @{update.effective_user.username}")
        if (not function in state.permissions[state.access_manager_obj.get_status(str(update.effective_user.id), str(update.effective_user.username))]):
            state.logger.warning(f"Access denied for update: {update}")
            message.reply_text("Нет доступа к данной операции")
            state.logger.debug(f"~{function.__name__}() by cancel")
            return ConversationHandler.END
        ret = function(update, context)
        state.logger.debug(f"~{function.__name__}()")
        dump_system(state) 
        return ret
    return help_decorator(decorated, state)           

# ============ ADDING HANDLERS ==============

class State:
    
    def __init__(self, logger, access_manager_obj, permissions, help_texts, parser):
        self.logger = logger
        self.access_manager_obj = access_manager_obj
        self.permissions = permissions
        self.help_texts = help_texts 
        self.parser = parser

def add_to_chat(update, context):
    pass

def main(logger, access_manager_obj, parser):
    updater = Updater(BOT_KEY, use_context=True)
    dp = updater.dispatcher
    scenarios = [
        AddToChat(ChatMemberHandler(add_to_chat, ChatMemberHandler.MY_CHAT_MEMBER), show_help=False),

        PermissionHelpText("\n*MANAGER HELP:*\n", MANAGER),

        Help(),
        GetId(),

        PermissionHelpText("\n", MANAGER),

        GetKeywords(),
        AddKeyword(),
        EraseKeyword(),

        PermissionHelpText("\n", MANAGER),

        GetChats(),
        EraseCurrentChat(),

        PermissionHelpText("\n", MANAGER),

        GetManagers(),
        AddManager(),
        EraseManager() 
    ]
    
    help_texts = {USER: "", MANAGER: ""}
    permissions = {USER: [], MANAGER: []} 
 
    state = State(logger, access_manager_obj, permissions, help_texts, parser)
 
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

    logger.debug("Polling was started")
    updater.start_polling()
    updater.idle()

def declare_globals():
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(toplevel)
    logger.warning("Bot is running now, logging enabled")
 
    access_manager_obj = access_manager()
    try:
        access_manager_obj.load(manager_path)
        logger.debug("Loaded access_manager from file")
    except Exception as e: 
        logger.debug(str(e))
    access_manager_obj.set_status(ADMIN_ID, MANAGER)

    parser = ChatParser() # TODO: get from the file
    
    return logger, access_manager_obj, parser
    

# Any function wrapped with one of {access, cancel}_decorator to
# automatically dumps system
# automatically sends menu, when cancel or finish of dialogue

if __name__ == '__main__':
    args = declare_globals() 
    main(*args)
