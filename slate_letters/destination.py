from datetime import datetime
from io import BytesIO
import pysftp


class BaseDestination:
    """Base destination class."""

    def send(self, bytes_):
        """Abstract method that should send the `bytes` to the destination."""
        raise NotImplementedError


class LocalDiskDestination(BaseDestination):
    def __init__(self, filepath):
        """This destination will store data to the local disk.

        Parameters
        ----------
        filepath : str
            A valid filepath where the data will be stored.
        """
        self.filepath = filepath

    def send(self, bytes_):
        with open(self.filepath, "wb") as f:
            f.write(bytes_)


class NullDestination(BaseDestination):
    def send(self, bytes_):
        pass


class SFTPDestination(BaseDestination):
    def __init__(self, host, username, password, filename_pattern):
        self.sftp_args = {"host": host, "username": username, "password": password}
        self.filename_pattern = filename_pattern

    def send(self, bytes_):
        remotepath = self.filename_pattern.format(
            dttm=datetime.now().strftime("%Y%m%d%H%M%S")
        )
        with pysftp.Connection(**self.sftp_args) as sftp:
            sftp.putfo(BytesIO(bytes_), remotepath)
