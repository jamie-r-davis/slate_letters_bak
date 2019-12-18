# Slate Letters

This service will render all admit decision letters, along with any attachments, to PDFs and upload the results to be consumed by a DIP source format. The need for this service is to facilitate the printing of hard-copy letters on letterhead.


## Process

The service will call a query web service to retrieve details about any admit letters that have not already been rendered. For each letter, the service will retrieve the HTML of the letter, along with any attachments letters. Then the letter HTML will be rendered as a PDF using a custom print stylesheet (`static/style.css`). Any attachments will have a white box rendered over the header to move any letterhead graphics. The letter, along with any attachments, will be combined into a single PDF. The batch of rendered PDFs will then be zipped and sent to the SFTP endpoint so that it can be consumed back into Slate as an Admit Letter material.

In cases where it has been designated only the attachment should be displayed, just the attachment will be retrieved.


## Usage

To run the app, use the following command:
```bash
pipenv run python app.py
```

Make sure to configure the appropriate environment variables:
- SESSION_HOSTNAME
- SESSION_USERNAME
- SESSION_PASSWORD
- QUERY_URL
- QUERY_USERNAME
- QUERY_PASSWORD
- SFTP_HOST
- SFTP_USERNAME
- SFTP_PASSWORD
- SFTP_FILENAME

## Technical Description

### Web Service Endpoint
A query should be configured in Slate which will return JSON with the following fields:

| Field | Logical Definition | Description |
|---|---|---|
| `decision` | `decision.id` | The guid of the decision |
| `letter` | `decision.letter` | The guid of the letter to be rendered |
| `stream` | `decision.stream` | The guid of the stream for any attachments |
| `stream_override` | `decision.stream_override` | Bit field indicating whether the attachment/stream should usurp the letter |
| `application` | `decision.application` | The guid of the application the decision is attached to |

Only released admit decisions should be returned by the query. Furthermore, only decisions which do not have a matching Admit Letter material with the filename `{decision_guid}*.pdf` should be returned.


### Letter Rendering

To render each letter as a PDF, the service fetches the simple html of the letter and renders the html as a PDF using the print stylesheet.

The simple html for any given letter is available at the following endpoint:
`/manage/database/letter?id={letter}&application={application}&cmd=sample_html_plain`

The letter renderer extracts the body tag from the response and renders its contents as a PDF.

Any attachments are available from the following endpoint:
`/apply/update?cmd=stream&id={decision}`

The response contains the bytes of the attachment already rendered as a PDF. A white rectangle will be drawn over the header of the PDF so that any letterhead on the PDF is masked for printing.