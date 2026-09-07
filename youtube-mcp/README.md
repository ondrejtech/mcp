# YouTube MCP Server – nastavení pro Claude Code

Tento repozitář dokumentuje zprovoznění MCP (Model Context Protocol) serveru pro YouTube (`zubeid-youtube-mcp-server`) a jeho napojení do **Claude Code CLI globálně** (dostupné ve všech projektech, ne jen v tomto).

## Co MCP server umí

Po zapojení serveru má Claude k dispozici mimo jiné tyto nástroje:

- `mcp__youtube__videos_getVideo` – detailní info o videu (title, popis, statistiky, délka…)
- `mcp__youtube__videos_searchVideos` – vyhledávání videí
- `mcp__youtube__transcripts_getTranscript` – přepis (titulky) videa
- `mcp__youtube__channels_getChannel` / `getChannels` – info o kanálu
- `mcp__youtube__channels_listVideos` – seznam videí kanálu
- `mcp__youtube__channels_searchChannels` – vyhledávání kanálů
- `mcp__youtube__channels_findCreators` – hledání tvůrců podle kritérií
- `mcp__youtube__playlists_getPlaylist` / `getPlaylistItems` – práce s playlisty

## Předpoklady

- Nainstalovaný [Claude Code CLI](https://claude.com/claude-code) (`claude --version` musí fungovat)
- Node.js + `npx` (server se spouští přes `npx -y zubeid-youtube-mcp-server`)
- YouTube Data API v3 klíč (viz níže)

## 1. Získání YouTube API klíče

1. Jdi do [Google Cloud Console](https://console.cloud.google.com/).
2. Vytvoř nový projekt (nebo použij existující).
3. V sekci **APIs & Services → Library** vyhledej **YouTube Data API v3** a aktivuj ho.
4. V sekci **APIs & Services → Credentials** vytvoř **API key**.
5. (Doporučeno) Omez klíč jen na YouTube Data API v3, ať není zneužitelný jinde.

## 2. Přidání MCP serveru do Claude Code (globálně)

Aby byl server dostupný ve **všech** projektech (ne jen v aktuálním adresáři), přidej ho do **user scope**:

```bash
claude mcp add youtube --scope user --env YOUTUBE_API_KEY=<TVŮJ_API_KLÍČ> -- npx -y zubeid-youtube-mcp-server
```

- `--scope user` → uloží se do globální konfigurace (`~/.claude.json`, sekce mimo konkrétní projekt), dostupné všude.
- `--scope local` (výchozí, pokud `--scope` vynecháš) → server platí jen pro aktuální projekt/adresář.
- `--scope project` → sdílené nastavení pro tým přes `.mcp.json` v repozitáři (commitovatelné).

### Pokud už server existuje jen lokálně a chceš ho přesunout na globální

```bash
claude mcp remove youtube -s local
claude mcp add youtube --scope user --env YOUTUBE_API_KEY=<TVŮJ_API_KLÍČ> -- npx -y zubeid-youtube-mcp-server
```

## 3. Ověření, že server běží

```bash
claude mcp list
```

Měl by se objevit řádek:

```
youtube: npx -y zubeid-youtube-mcp-server - ✔ Connected
```

Detail konfigurace (scope, env proměnné, příkaz):

```bash
claude mcp get youtube
```

Očekávaný výstup obsahuje `Scope: User config (available in all your projects)`.

## 4. Otestování v nové session

Server se do běžící session promítne okamžitě, ale ověření v úplně nové, nezávislé session (a jiném adresáři) potvrdí, že je opravdu globální:

```bash
cd /tmp
claude -p "Zavolej nástroj mcp__youtube__videos_getVideo s videoId 'IuZk3j-D_C0' a vypiš jen title videa." --allowedTools "mcp__youtube__videos_getVideo"
```

Očekávaný výstup: název daného YouTube videa.

## 5. Použití v interaktivní session

Po spuštění `claude` v libovolném projektu můžeš rovnou psát požadavky typu:

- „Analyzuj tohle video: `https://www.youtube.com/watch?v=<ID>`"
- „Najdi mi přepis videa a shrň ho"
- „Vyhledej kanály na téma X"

Claude si sám vybere odpovídající `mcp__youtube__*` nástroj.

## Správa serveru

| Akce | Příkaz |
|---|---|
| Seznam všech MCP serverů | `claude mcp list` |
| Detail konkrétního serveru | `claude mcp get youtube` |
| Odebrání globálního serveru | `claude mcp remove youtube -s user` |
| Odebrání lokálního serveru | `claude mcp remove youtube -s local` |

## Troubleshooting

- **Server se nepřipojí (`✘` místo `✔`)** – zkontroluj, že `npx` je dostupný v PATH a že máš internetové připojení (npx si balíček stahuje za běhu).
- **`YOUTUBE_API_KEY` chyba / kvóta vyčerpána** – YouTube Data API má denní kvótu (výchozí 10 000 jednotek/den). Zkontroluj využití v Google Cloud Console → APIs & Services → Quotas.
- **Server je vidět jen v jednom projektu** – zkontroluj scope přes `claude mcp get youtube`; pokud je `Local config`, přesuň ho podle kroku 2 výše.
- **Transkript videa je moc dlouhý a přesahuje limit tokenů** – výstup se automaticky uloží do souboru; buď ho projdi po částech (`offset`/`limit` u čtení), nebo deleguj čtení na subagenta, aby to nezabíralo hlavní kontext.

## Poznámka k bezpečnosti

API klíč je uložený v konfiguraci Claude Code (`~/.claude.json`) jako proměnná prostředí pro daný MCP server. Zacházej s ním jako s tajemstvím – necommituj ho do veřejných repozitářů, a pokud unikne, klíč v Google Cloud Console zneplatni a vygeneruj nový.
