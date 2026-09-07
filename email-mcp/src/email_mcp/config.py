"""Account configuration loaded from environment variables (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Account:
    name: str
    email: str
    password: str
    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int


def _env(name: str, required: bool = True, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value or ""


def load_accounts() -> dict[str, Account]:
    """Build the {name: Account} map from ACCOUNTS + <NAME>_* env vars."""
    names = [n.strip() for n in os.environ.get("ACCOUNTS", "").split(",") if n.strip()]
    accounts: dict[str, Account] = {}
    for name in names:
        prefix = name.upper()
        accounts[name.lower()] = Account(
            name=name,
            email=_env(f"{prefix}_EMAIL"),
            password=_env(f"{prefix}_PASSWORD"),
            imap_host=_env(f"{prefix}_IMAP_HOST"),
            imap_port=int(_env(f"{prefix}_IMAP_PORT", required=False, default="993")),
            smtp_host=_env(f"{prefix}_SMTP_HOST"),
            smtp_port=int(_env(f"{prefix}_SMTP_PORT", required=False, default="587")),
        )
    return accounts


def get_account(accounts: dict[str, Account], name: str) -> Account:
    account = accounts.get(name.lower())
    if account is None:
        available = ", ".join(sorted(accounts)) or "(none configured)"
        raise ValueError(f"Unknown account '{name}'. Configured accounts: {available}")
    return account
