# email-mcp

Vlastní MCP server pro odesílání a čtení firemní pošty (IMAP + SMTP) přes
více klientských schránek. Postavený na `mcp` SDK (`MCPServer`, dřívější
`FastMCP`) a `imap-tools`.

## Instalace

```bash
uv sync
cp .env.example .env
```

Vyplň v `.env` skutečné přihlašovací údaje k jednotlivým schránkám (IMAP/SMTP
host a port najdeš u svého hostingu, u czechia.com typicky
`imap.czechia.com:993` a `smtp.czechia.com:587`). Přidej do `ACCOUNTS` jméno
pro každý účet a doplň k němu blok `<JMENO>_EMAIL/PASSWORD/IMAP_HOST/...`.

`.env` se nikdy necommituje (je v `.gitignore`).

## Registrace do Claude Code (lokálně, stdio)

```bash
claude mcp add email --scope user -- uv run --directory /python/mcp/email-mcp python -m email_mcp.server
```

Ověření:

```bash
claude mcp list
claude mcp get email
```

V Claude Code/Desktop pak stačí požádat o práci s emailem — nástroje se
volají jménem, které jsi zadal v `ACCOUNTS` (např. "pošli přes klient1 email
na ...").

## Nástroje (MCP tools)

- **Účty**: `list_accounts`
- **Odesílání**: `send_email`, `reply_email`, `forward_email`
- **Koncepty**: `save_draft`, `list_drafts`
- **Šablony**: `list_templates`, `render_template` (soubory v `templates/`,
  placeholdery ve tvaru `$jmeno`)
- **Čtení**: `list_folders`, `list_messages`, `search_messages`,
  `get_message`, `download_attachment`
- **Správa zpráv**: `mark_message`, `move_message`, `delete_message`

Každý tool vrací buď výsledek, nebo řetězec `"failed: <chyba>"` — chyby
IMAP/SMTP nikdy nespadnou server, jen se vrátí jako text.

## Přechod na vzdálený provoz

Server zatím běží lokálně přes `stdio` transport (`mcp.run(transport="stdio")`
v `src/email_mcp/server.py`). Až poběží na vlastním serveru, stačí v
`main()` přepnout na `transport="streamable-http"` (nebo `"sse"`) a doplnit
autentizaci k samotnému MCP serveru — kód nástrojů (IMAP/SMTP logika) se
měnit nemusí.

## Bezpečnostní poznámka

Sesterský projekt `youtube-mcp` v tomto repu obsahuje v
`add-tavily-mcp.sh` natvrdo commitnutý API klíč — doporučeno rotovat a
nahradit env proměnnou, nesouvisí ale s tímto projektem.
