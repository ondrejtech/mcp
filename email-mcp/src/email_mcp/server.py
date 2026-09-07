"""Email MCP server: send/receive mail over SMTP/IMAP for multiple mailboxes."""

from __future__ import annotations

from typing import Any

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

from . import imap_client, smtp_client, templates
from .config import Account, get_account, load_accounts

load_dotenv()

mcp = MCPServer("email-mcp")
_accounts: dict[str, Account] = load_accounts()


def _account(name: str) -> Account:
    return get_account(_accounts, name)


def _send_and_save(acc: Account, msg) -> None:
    """Send via SMTP, then best-effort save a copy to the Sent folder over IMAP."""
    smtp_client.send(acc, msg)
    try:
        imap_client.append_message(acc, "Sent", msg, flag_set=["\\Seen"])
    except Exception:  # noqa: BLE001 - the send already succeeded, this is best-effort
        pass


@mcp.tool()
def list_accounts() -> list[dict[str, str]]:
    """List the mailbox accounts configured on this server (no passwords)."""
    return [{"name": a.name, "email": a.email} for a in _accounts.values()]


@mcp.tool()
def send_email(
    account: str,
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    bcc: str | None = None,
    attachments: list[str] | None = None,
) -> str:
    """Send a new email from the given account."""
    try:
        acc = _account(account)
        msg = smtp_client.build_message(acc, to, subject, body, cc, bcc, attachments)
        _send_and_save(acc, msg)
        return "success"
    except Exception as e:  # noqa: BLE001 - report failure to the MCP client, don't crash the server
        return f"failed: {e}"


@mcp.tool()
def reply_email(
    account: str,
    folder: str,
    uid: str,
    body: str,
    reply_all: bool = False,
    attachments: list[str] | None = None,
) -> str:
    """Reply to an existing email, keeping the thread headers intact."""
    try:
        acc = _account(account)
        original = imap_client.get_raw_message(acc, folder, uid)
        to = original.reply_to or original.from_
        cc = ", ".join(original.cc) if reply_all and original.cc else None
        subject = original.subject or ""
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
        message_id = original.headers.get("message-id", ("",))[0]
        references = original.headers.get("references", ("",))[0]
        extra_headers = {}
        if message_id:
            extra_headers["In-Reply-To"] = message_id
            extra_headers["References"] = f"{references} {message_id}".strip()
        msg = smtp_client.build_message(
            acc, to, subject, body, cc=cc, attachments=attachments, extra_headers=extra_headers
        )
        _send_and_save(acc, msg)
        return "success"
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"


@mcp.tool()
def forward_email(account: str, folder: str, uid: str, to: str, comment: str | None = None) -> str:
    """Forward an existing email to a new recipient."""
    try:
        acc = _account(account)
        original = imap_client.get_raw_message(acc, folder, uid)
        subject = original.subject or ""
        if not subject.lower().startswith("fwd:"):
            subject = f"Fwd: {subject}"
        body_parts = [comment, "---------- Forwarded message ----------", original.text or original.html or ""]
        body = "\n\n".join(p for p in body_parts if p)
        msg = smtp_client.build_message(acc, to, subject, body)
        _send_and_save(acc, msg)
        return "success"
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"


@mcp.tool()
def save_draft(
    account: str,
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    attachments: list[str] | None = None,
) -> str:
    """Save a message to the account's Drafts folder without sending it."""
    try:
        acc = _account(account)
        msg = smtp_client.build_message(acc, to, subject, body, cc=cc, attachments=attachments)
        imap_client.append_message(acc, "Drafts", msg, flag_set=["\\Draft"])
        return "success"
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"


@mcp.tool()
def list_drafts(account: str) -> list[dict[str, Any]] | str:
    """List messages currently in the account's Drafts folder."""
    try:
        return imap_client.list_in_folder(_account(account), "Drafts")
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"


@mcp.tool()
def list_templates() -> list[str]:
    """List the names of available email templates."""
    return templates.list_templates()


@mcp.tool()
def render_template(name: str, variables: dict[str, str] | None = None) -> str:
    """Render a template file, substituting $placeholder variables."""
    try:
        return templates.render_template(name, variables)
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"


@mcp.tool()
def list_folders(account: str) -> list[str] | str:
    """List the IMAP folders/mailboxes available on the account."""
    try:
        return imap_client.list_folders(_account(account))
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"


@mcp.tool()
def list_messages(
    account: str, folder: str = "INBOX", limit: int = 20, unseen_only: bool = False
) -> list[dict[str, Any]] | str:
    """List recent messages in a folder (newest first)."""
    try:
        return imap_client.list_messages(_account(account), folder, limit, unseen_only)
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"


@mcp.tool()
def search_messages(
    account: str,
    folder: str = "INBOX",
    from_: str | None = None,
    subject: str | None = None,
    since: str | None = None,
    text: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]] | str:
    """Search messages by sender, subject, date (YYYY-MM-DD) and/or body text."""
    try:
        return imap_client.search_messages(_account(account), folder, from_, subject, since, text, limit)
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"


@mcp.tool()
def get_message(account: str, folder: str, uid: str) -> dict[str, Any] | str:
    """Get full headers, body and attachment names for one message."""
    try:
        return imap_client.get_message(_account(account), folder, uid)
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"


@mcp.tool()
def download_attachment(account: str, folder: str, uid: str, filename: str, save_path: str) -> str:
    """Save one attachment of a message to a local file path."""
    try:
        return imap_client.download_attachment(_account(account), folder, uid, filename, save_path)
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"


@mcp.tool()
def mark_message(account: str, folder: str, uid: str, flag: str, add: bool = True) -> str:
    """Set or clear a flag (seen/flagged/deleted/answered/draft) on a message."""
    try:
        imap_client.mark_message(_account(account), folder, uid, flag, add)
        return "success"
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"


@mcp.tool()
def move_message(account: str, folder: str, uid: str, target_folder: str) -> str:
    """Move a message from one folder to another."""
    try:
        imap_client.move_message(_account(account), folder, uid, target_folder)
        return "success"
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"


@mcp.tool()
def delete_message(account: str, folder: str, uid: str) -> str:
    """Delete a message (marks \\Deleted and expunges)."""
    try:
        imap_client.delete_message(_account(account), folder, uid)
        return "success"
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
