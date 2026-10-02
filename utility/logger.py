import logging 
import os 
from datetime import datetime , date
from logging.handlers import RotatingFileHandler
os.makedirs("logs" , exist_ok= True)
logger =  logging.getLogger(__name__)

fileName = str(date.today()) + "_" + "logs"

filePath = f'logs/{fileName}'

if not os.path.exists(filePath):
    open(filePath, 'w').close()
LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(filename)s:%(lineno)d | "
    "%(message)s"
)


DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger():
    logger  = logging.getLogger()
    if logger.handlers : 
        return logger
    logger.setLevel(level = logging.DEBUG)
    formatter  = logging.Formatter(LOG_FORMAT , datefmt = DATE_FORMAT)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO)
    consoleHandler.setFormatter(formatter)
    
    file_handler = RotatingFileHandler(
    filePath,
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8"
)
    file_handler.setLevel(level = logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(consoleHandler)
    return logger

