import csv
import logging
from datetime import datetime as dt
from io import BytesIO, StringIO
from zipfile import ZipFile

import requests

from slate_letters.exceptions import NoLettersToRenderError
from slate_letters.letters import LetterGetter
from slate_letters.session import get_external_session


class LetterService:
    def __init__(self, auth):
        self.session = get_external_session(**auth)
        self.destinations = []

    def add_destination(self, destination):
        self.destinations.append(destination)

    @staticmethod
    def query_letters(url, auth):
        auth_tuple = (auth["username"], auth["password"])
        r = requests.get(url, auth=auth_tuple)
        r.raise_for_status()
        return r.json()["row"]

    def fetch_letters(self, query_args):
        lg = LetterGetter(self.session)
        zip_fo = BytesIO()
        letter_indexes = []
        letters = self.query_letters(**query_args)
        logging.debug(letters)
        if not letters:
            raise NoLettersToRenderError
        with ZipFile(zip_fo, "w", allowZip64=True) as zf:
            for letter in letters:
                try:
                    pdf = lg.render_letter(**letter)
                except TypeError:
                    logging.error(f"No letter specified: {letter}")
                    continue
                filename = "{decision}_{dttm}.pdf".format(
                    decision=letter["decision"], dttm=dt.now().strftime("%Y%m%d%H%M%S")
                )
                letter["filename"] = filename
                zf.writestr(filename, pdf)
                letter_indexes.append(letter)
            index_fo = StringIO()
            logging.debug(f"letter_indexes: {letter_indexes}")
            fieldnames = ["filename", "decision", "application"]
            dict_writer = csv.DictWriter(
                index_fo, fieldnames=fieldnames, extrasaction="ignore"
            )
            dict_writer.writeheader()
            dict_writer.writerows(letter_indexes)
            zf.writestr("index.txt", index_fo.getvalue())
        return zip_fo.getvalue()

    def send(self, bytes, *args, **kwargs):
        for destination in self.destinations:
            destination.send(bytes=bytes, *args, **kwargs)
