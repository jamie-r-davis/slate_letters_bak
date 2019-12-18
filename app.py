import logging
from logging.handlers import TimedRotatingFileHandler
import os

from slate_letters import app
from slate_letters.destination import LocalDiskDestination, SFTPDestination
from config import Config


fmt = "%(asctime)s - %(levelname)s - %(name)s - %(msg)s"
logger = logging.getLogger()
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter(fmt))
logger.addHandler(stream_handler)
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = TimedRotatingFileHandler('logs/app_logs.log', when='W0', backupCount=4)
file_handler.setFormatter(logging.Formatter(fmt))
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


if __name__ == "__main__":
    sftp_destination = SFTPDestination(
        host=Config.SFTP_HOST,
        username=Config.SFTP_USERNAME,
        password=Config.SFTP_PASSWORD,
        filename_pattern=Config.SFTP_FILENAME
    )
    app.add_destination(sftp_destination)
    app.run()