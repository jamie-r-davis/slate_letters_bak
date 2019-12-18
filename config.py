import os
import dotenv


dotenv.load_dotenv()


class Config:
    SESSION_HOSTNAME = os.getenv('SESSION_HOSTNAME')
    SESSION_USERNAME = os.getenv('SESSION_USERNAME')
    SESSION_PASSWORD = os.getenv('SESSION_PASSWORD')
    QUERY_URL = os.getenv('QUERY_URL')
    QUERY_USERNAME = os.getenv('QUERY_USERNAME')
    QUERY_PASSWORD = os.getenv('QUERY_PASSWORD')
    SFTP_HOST = os.getenv('SFTP_HOST')
    SFTP_USERNAME = os.getenv('SFTP_USERNAME')
    SFTP_PASSWORD = os.getenv('SFTP_PASSWORD')
    SFTP_FILENAME = os.getenv('SFTP_FILENAME')