import logging
from io import BytesIO

from bs4 import BeautifulSoup
from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter
from reportlab.lib import pagesizes
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from weasyprint import CSS, HTML


from slate_letters.letter import Letter

logger = logging.getLogger(__name__)


class LetterGetter:
    def __init__(self, session):
        self.session = session
        self.hostname = self.session.headers.get('Origin')

    @staticmethod
    def _append_pdfs(pdfs):
        """Takes an iterable of pdf byte arrays and merges them into a single byte array.

        Parameters
        ----------
        pdf : iterable(bytes)
            An iterable of byte arrays for the pdfs to merge.

        Returns
        -------
        bytes
            The bytes of the merged pdf.
        """
        pdf_merger = PdfFileMerger()
        pdf_fos = [BytesIO(pdf) for pdf in pdfs]
        for fo in pdf_fos:
            pdf_merger.append(fo)
        out_pdf = BytesIO()
        pdf_merger.write(out_pdf)
        return out_pdf.getvalue()

    @staticmethod
    def _mask_header(pdf_obj, height=1.375):
        """Draws white rectangle over top `height` of pdf_obj.

        Parameters
        ----------
        pdf_obj : bytes
            The bytes of a PDF document.

        Returns
        -------
        bytes
            The bytes of the modified pdf.
        """
        final_pdf = BytesIO()
        watermark = BytesIO()
        c = Canvas(watermark, pagesize=pagesizes.letter)
        c.setFillColorRGB(255, 255, 255)
        c.rect(0, (11 - height) * inch, 8.5 * inch, height * inch, stroke=0, fill=1)
        c.showPage()
        c.save()
        pdfwriter = PdfFileWriter()
        pdf = PdfFileReader(pdf_obj)
        for i in range(pdf.getNumPages()):
            page = pdf.getPage(i)
            page.mergePage(PdfFileReader(watermark).getPage(0))
            pdfwriter.addPage(page)
        pdfwriter.write(final_pdf)
        return final_pdf.getvalue()

    def retrieve_html(self, application, letter, **kwargs):
        """
        Fetch & return the sample html for a given letter and application.

        Parameters
        ----------
        letter : str (guid)
            The guid of the letter to generate.
        application : str (guid)
            The guid of the application to generate the letter for.

        Returns
        -------
        str
            The html body of the letter.
        """
        url = f"{self.hostname}/manage/database/letter?id={letter}&application={application}&cmd=sample_html_plain"
        r = self.session.get(url)
        logger.debug(f"{r.status_code}: {url}")
        r.raise_for_status()
        # letter html body is nested within the body of response
        soup = BeautifulSoup(r.text, "html.parser")
        body = soup.find("body").find("body")
        # return source code of content body element
        return str(body)

    def render_html(self, application, letter, css="static/style.css", **kwargs):
        """
        Fetches the html for the given application/letter and returns bytes of the rendered pdf.

        Parameters
        ----------
        application : str (guid)
            The guid of the application the decision is attached to
        letter : str (guid)
            The guid of the letter ([lookup.letter] or [decision].[letter]) to render
        css : str
            The filepath of the css to use while rendering the letter pdf.

        Returns
        -------
        bytes
            The bytes of the rendered letter pdf.
        """
        html = self.retrieve_html(application, letter)
        logger.debug(f"{letter}: Retrieved letter html")
        pdf_css = CSS(css)
        pdf_obj = HTML(string=html)
        pdf_bytes = pdf_obj.write_pdf(stylesheets=[pdf_css])
        return pdf_bytes

    def retrieve_attachment(self, decision, **kwargs):
        """
        Fetch & return the given stream as bytes.

        Parameters
        ----------
        decision : str (guid)
            The guid of the decision to retreive ([decision].[id])

        Returns
        -------
        bytes
            The bytes of the finalized attachment pdf.
        """
        url = f"{self.hostname}/apply/update?cmd=stream&id={decision}"
        r = self.session.get(url)
        r.raise_for_status()
        attachment = BytesIO(r.content)
        masked_attachment = self._mask_header(attachment)
        return masked_attachment

    def render_letter(self, decision, application, letter, **kwargs):
        """Renders the given letter (and its attachments, if present) and
        returns the byte object of the combined pdf.

        Parameters
        ----------
        decision : str (guid)
            The guid of the decision record.
        application : str (guid)
            The guid of the application the decision belongs to.
        letter : str (guid)
            The guid of the letter code associated with the letter.
        """
        pdfs = []
        # only render attachment, if override is set
        if kwargs.get("stream"):
            logger.debug("Attachment is included, retrieving...")
            attachment = self.retrieve_attachment(decision)
            logger.debug("Attachment retrieved.")
        if kwargs.get("stream_override") == "1":
            logger.debug("Stream override is set")
            pdfs.append(attachment)
        else:
            # render letter
            letter = self.render_html(application, letter)
            pdfs.append(letter)
            # render attachment, if a stream is present
            if kwargs.get("stream"):
                pdfs.append(attachment)
        # merge the output into a single pdf
        final_pdf = self._append_pdfs(pdfs)
        return final_pdf