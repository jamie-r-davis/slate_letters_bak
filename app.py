import logging

import config
from slate_letters.exceptions import NoLettersToRenderError
from slate_letters.destinations import (
    LocalDiskDestination,
    SFTPDestination,
    SourceFormatDestination,
)
from slate_letters.service import LetterService


logging.basicConfig(filename='logs.txt', level=logging.INFO)


def main():
    service = LetterService(config.AUTH)
    service.add_destination(SFTPDestination(**config.SFTP_CONFIG))
    try:
        zip_bytes = service.fetch_letters(config.LETTER_ENDPOINT)
    except NoLettersToRenderError:
        logging.info("No letters to render. Exiting application.")
    else:
        service.send(zip_bytes)


if __name__ == "__main__":
    main()
