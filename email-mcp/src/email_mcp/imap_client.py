"""Reading and managing messages over IMAP (imap-tools)."""

from __future__ import annotations

import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from imap_tools import AND, MailBox, MailMessage

from .config import Account

FLAG_MAP = {
    "seen": "\\Seen",
    "flagged": "\\Flagged",
    "deleted": "\\Deleted",
    "answered": "\\Answered",
    "draft": "\\Draft",
}


def _connect(account: Account) -> MailBox:
    mailbox = MailBox(account.imap_host, port=account.imap_port)
    mailbox.login(account.email, account.password)
    return mailbox


def list_folders(account: Account) -> list[str]:
    with _connect(account) as mailbox:
        return [f.name for f in mailbox.folder.list()]


def _summary(msg: MailMessage) -> dict[str, Any]:
    return {
        "uid": msg.uid,
        "from": msg.from_,
        "to": list(msg.to),
        "subject": msg.subject,
        "date": msg.date_str,
        "flags": list(msg.flags),
        "has_attachments": bool(msg.attachments),
    }


def list_messages(
    account: Account,
    folder: str = "INBOX",
    limit: int = 20,
    unseen_only: bool = False,
) -> list[dict[str, Any]]:
    with _connect(account) as mailbox:
        mailbox.folder.set(folder)
        criteria = AND(seen=False) if unseen_only else "ALL"
        messages = mailbox.fetch(criteria, limit=limit, reverse=True, mark_seen=False)
        return [_summary(msg) for msg in messages]


def search_messages(
    account: Account,
    folder: str = "INBOX",
    from_: str | None = None,
    subject: str | None = None,
    since: str | None = None,
    text: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    kwargs: dict[str, Any] = {}
    if from_:
        kwargs["from_"] = from_
    if subject:
        kwargs["subject"] = subject
    if text:
        kwargs["text"] = text
    if since:
        kwargs["date_gte"] = datetime.date.fromisoformat(since)
    criteria = AND(**kwargs) if kwargs else "ALL"
    with _connect(account) as mailbox:
        mailbox.folder.set(folder)
        messages = mailbox.fetch(criteria, limit=limit, reverse=True, mark_seen=False)
        return [_summary(msg) for msg in messages]


def get_message(account: Account, folder: str, uid: str) -> dict[str, Any]:
    with _connect(account) as mailbox:
        mailbox.folder.set(folder)
        messages = list(mailbox.fetch(AND(uid=uid), mark_seen=False))
        if not messages:
            raise ValueError(f"Message uid={uid} not found in folder '{folder}'")
        msg = messages[0]
        return {
            **_summary(msg),
            "cc": list(msg.cc),
            "text": msg.text,
            "html": msg.html,
            "attachments": [a.filename for a in msg.attachments],
        }


def download_attachment(
    account: Account, folder: str, uid: str, filename: str, save_path: str
) -> str:
    with _connect(account) as mailbox:
        mailbox.folder.set(folder)
        messages = list(mailbox.fetch(AND(uid=uid), mark_seen=False))
        if not messages:
            raise ValueError(f"Message uid={uid} not found in folder '{folder}'")
        for attachment in messages[0].attachments:
            if attachment.filename == filename:
                Path(save_path).write_bytes(attachment.payload)
                return save_path
        raise ValueError(f"Attachment '{filename}' not found on message uid={uid}")


def get_raw_message(account: Account, folder: str, uid: str) -> MailMessage:
    """Fetch a single message with full content, for reply/forward building."""
    with _connect(account) as mailbox:
        mailbox.folder.set(folder)
        messages = list(mailbox.fetch(AND(uid=uid), mark_seen=False))
        if not messages:
            raise ValueError(f"Message uid={uid} not found in folder '{folder}'")
        return messages[0]


def mark_message(account: Account, folder: str, uid: str, flag: str, add: bool = True) -> None:
    imap_flag = FLAG_MAP.get(flag.lower())
    if imap_flag is None:
        raise ValueError(f"Unknown flag '{flag}'. Known flags: {', '.join(FLAG_MAP)}")
    with _connect(account) as mailbox:
        mailbox.folder.set(folder)
        mailbox.flag(uid, imap_flag, add)


def move_message(account: Account, folder: str, uid: str, target_folder: str) -> None:
    with _connect(account) as mailbox:
        mailbox.folder.set(folder)
        mailbox.move(uid, target_folder)


def delete_message(account: Account, folder: str, uid: str) -> None:
    with _connect(account) as mailbox:
        mailbox.folder.set(folder)
        mailbox.delete(uid)


def append_message(account: Account, folder: str, msg: EmailMessage, flag_set: list[str] | None = None) -> None:
    with _connect(account) as mailbox:
        mailbox.append(msg.as_bytes(), folder, flag_set=flag_set)


def list_in_folder(account: Account, folder: str, limit: int = 50) -> list[dict[str, Any]]:
    with _connect(account) as mailbox:
        mailbox.folder.set(folder)
        messages = mailbox.fetch("ALL", limit=limit, reverse=True, mark_seen=False)
        return [_summary(msg) for msg in messages]
