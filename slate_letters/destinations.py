from datetime import datetime as dt
from io import BytesIO

import pysftp
import requests


class DestinationBase(object):
    """Base destination class"""

    def send(self, bytes):
        """This method should be implemented by any subclasses and send the
        `bytes` to the destination being implemented."""
        raise NotImplementedError()


class LocalDiskDestination(DestinationBase):
    def __init__(self, filepath):
        """This destination will store data to the local disk.

        Parameters
        ----------
        filepath : str
            A valid filepath where the data will be stored.
        """
        self.filepath = filepath

    def send(self, bytes):
        with open(self.filepath, "wb") as f:
            f.write(bytes)


class SourceFormatDestination(DestinationBase):
    def __init__(self, url, username, password):
        """Destination to deliver data to a source format endpoint."""
        self.url = url
        self.auth = (username, password)

    def send(self, bytes):
        headers = {"content-type": "application/octet-stream"}
        requests.post(self.url, data=bytes, auth=self.auth, headers=headers)


class SFTPDestination(DestinationBase):
    def __init__(self, sftp_args, filename_pattern):
        self.sftp_args = sftp_args
        self.filename_pattern = filename_pattern

    def send(self, bytes):
        remotepath = self.filename_pattern.format(
            dttm=dt.now().strftime("%Y%m%d%H%M%S")
        )
        with pysftp.Connection(**self.sftp_args) as sftp:
            sftp.putfo(BytesIO(bytes), remotepath)
