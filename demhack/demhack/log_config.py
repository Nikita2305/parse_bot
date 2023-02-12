import logging.config
import os
from demhack.utils import ADMIN_ID

from telegram import Bot

BOT_KEY = "5133601045:AAH8FIsPniGeoLK-8yo59wjEbX15VKqNAyM" # TEST
# BOT_KEY = "6125509742:AAHeDyuVpH_b7OuR2t2lIiR6s6AriRZlE98"
toplevel = 'demhack'

class TelegramBotHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record: logging.LogRecord):
        try:
            Bot(BOT_KEY).send_message(int(ADMIN_ID), str(self.format(record)))
        except Exception as ex:
            logging.getLogger(toplevel).info("Previous report was not sent by Telegram")

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'default_formatter': {
            'format': '[%(levelname)s:%(asctime)s] %(message)s'
        },
    },

    'handlers': {
        'stream_handler': {
            'class': 'logging.FileHandler',
            'filename': os.path.dirname(__file__) + '/logs.txt',
            'level': 'DEBUG',
            'formatter': 'default_formatter'
        },
        'telegram_handler': {
            'class': '__main__.TelegramBotHandler',
            'level': 'WARNING',
            'formatter': 'default_formatter'
        }
    },

    'loggers': {
        toplevel: {
            'handlers': ['stream_handler', 'telegram_handler'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}
