"""Building and sending outgoing messages (send / reply / forward / draft)."""

from __future__ import annotations

import mimetypes
import smtplib
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path

from .config import Account


def _add_attachments(msg: EmailMessage, attachments: list[str] | None) -> None:
    for path_str in attachments or []:
        path = Path(path_str)
        data = path.read_bytes()
        ctype, _ = mimetypes.guess_type(path.name)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=path.name)


def build_message(
    account: Account,
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    bcc: str | None = None,
    attachments: list[str] | None = None,
    extra_headers: dict[str, str] | None = None,
) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = account.email
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    for key, value in (extra_headers or {}).items():
        msg[key] = value
    msg.set_content(body)
    _add_attachments(msg, attachments)
    return msg


def send(account: Account, msg: EmailMessage) -> None:
    with smtplib.SMTP(account.smtp_host, account.smtp_port) as server:
        server.starttls()
        server.login(account.email, account.password)
        server.send_message(msg)
