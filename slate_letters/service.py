from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from csv import DictWriter
from io import StringIO, BytesIO
import logging
import threading
from zipfile import ZipFile

from slate_utils.session import get_external_session

from slate_letters.exceptions import NoLettersToRenderError
from slate_letters.letter import Letter
from slate_letters.letter_getter import LetterGetter


thread_local = threading.local()
logger = logging.getLogger(__name__)


class LetterService:
    def __init__(self, config):
        self.config = config
        self._session = None
        self.destinations = []

    def add_destination(self, destination):
        self.destinations.append(destination)

    @property
    def session(self):
        if not hasattr(thread_local, "session"):
            hostname = self.config.SESSION_HOSTNAME
            username = self.config.SESSION_USERNAME
            password = self.config.SESSION_PASSWORD
            thread_local.session = get_external_session(hostname, username, password)
        return thread_local.session

    def query(self):
        url = self.config.QUERY_URL
        username = self.config.QUERY_USERNAME
        password = self.config.QUERY_PASSWORD
        logger.debug(f'Querying {url}...')
        response = self.session.get(url, auth=(username, password))
        return response.json().get("row")

    def fetch(self, letter_data):
        futures = []
        letters = []
        with ThreadPoolExecutor() as executor:
            for letter in letter_data:
                futures.append(executor.submit(self.fetch_letter, **letter))
            for future in as_completed(futures):
                try:
                    letter = future.result()
                except Exception as e:
                    logger.error(e)
                else:
                    letters.append(letter)
        return letters

    def combine(self, letters):
        if not letters:
            raise NoLettersToRenderError
        zip_obj = BytesIO()
        with ZipFile(zip_obj, 'w', allowZip64=True) as zf:
            for letter in letters:
                zf.writestr(letter.filename, letter.pdf)
            index_data = self.render_indexes(letters)
            zf.writestr('index.txt', index_data)
        return zip_obj.getvalue()

    def send(self, data):
        for destination in self.destinations:
            destination.send(data)

    def fetch_letter(self, decision, application, letter, **kwargs):
        lg = LetterGetter(self.session)
        filename = self.render_filename(decision)
        pdf = lg.render_letter(decision, application, letter, **kwargs)
        letter = Letter(decision=decision, letter=letter, application=application, filename=filename, pdf=pdf)
        logger.info(f"{letter.filename} rendered.")
        return letter

    @staticmethod
    def render_filename(decision):
        dttm_fmt = "%Y%m%d%H%M%S"
        now = datetime.now().strftime(dttm_fmt)
        return f"{decision}_{now}.pdf"

    @staticmethod
    def render_indexes(letters):
        index_obj = StringIO()
        fieldnames = ['filename', 'decision', 'application']
        dict_writer = DictWriter(index_obj, fieldnames=fieldnames, extrasaction='ignore')
        dict_writer.writeheader()
        for letter in letters:
            dict_writer.writerow(letter.as_dict())
        return index_obj.getvalue()

    def run(self):
        logger.info("Letter service started.")
        query_data = self.query()
        logger.info(f"{len(query_data):,} letters in query.")
        if query_data:
            letters = self.fetch(query_data)
            logger.info(f"{len(letters):,} letters retrieved.")
            zip_data = self.combine(letters)
            self.send(zip_data)
        logger.info("Letter service completed.")