import logging
import dotenv
import os

DEBUG = dotenv.get_key(dotenv.find_dotenv(), "DEBUG") in ["True", 1, "1", True]

class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[94m",
        "INFO": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "CRITICAL": "\033[95m",
    }

    def format(self, record):
        log_message = super().format(record)
        if record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            log_message = f"{color}{log_message}\033[0m"
        return log_message

logger = logging.getLogger("bot")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("bot.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)

if DEBUG:
    formatter = ColoredFormatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
else:
    formatter = ColoredFormatter(
        "%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(console_handler)
