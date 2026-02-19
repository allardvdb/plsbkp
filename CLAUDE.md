# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**plsbkp** is a Spotify playlist backup/restore CLI tool. The full specification is in `spotify-playlist-backup-spec.md`.

The tool is a **single-file Python script** (`scripts/spotify-backup.py`) using `spotipy` for Spotify API access. No package structure — just one standalone script with a `#!/usr/bin/env python3` shebang.

## Setup and Running

```bash
pip install spotipy
pip install python-dotenv  # optional, enables .env file support
```

Uses **PKCE auth** (no client secret required). Requires two environment variables (read automatically by spotipy):
- `SPOTIPY_CLIENT_ID`
- `SPOTIPY_REDIRECT_URI` (set to `http://127.0.0.1:8888/callback`)

These can be set in the shell or in a `.env` file (loaded automatically when `python-dotenv` is installed).

Auth runs with `open_browser=False` — the user must manually open the auth URL printed to the terminal.

```bash
python scripts/spotify-backup.py list                          # list playlists
python scripts/spotify-backup.py export                        # interactive export
python scripts/spotify-backup.py export --playlist-id <id> --output <file>
python scripts/spotify-backup.py export --playlist-id 3        # export by list number
python scripts/spotify-backup.py import --input <file>         # restore playlist
python scripts/spotify-backup.py import --input <file> --name "New Name"
python scripts/spotify-backup.py --account alice export        # multi-account support
python scripts/spotify-backup.py --account bob import --input <file>
```

## Architecture

Single file with six functions:

1. `get_spotify_client(account=None)` — PKCE OAuth2 init, caches token in `.spotify-token-cache` (or `.spotify-token-cache-<account>` with `--account`)
2. `list_playlists(sp)` — paginated playlist fetch
3. `choose_playlist(playlists)` — interactive numbered menu
4. `export_playlist(sp, playlist_id, output_path)` — paginated track fetch → JSON
5. `import_playlist(sp, input_path, name_override=None)` — JSON → new playlist, adds tracks in batches of 100
6. `main()` — argparse with `list`, `export`, `import` subcommands; validates required env vars on startup; resolves numeric playlist IDs to real Spotify IDs via the list

## Key Constraints

- Spotify API pages at 100 items — all listing/fetching must handle pagination
- OAuth2 scopes: `playlist-read-private`, `playlist-read-collaborative`, `playlist-modify-public`, `playlist-modify-private`
- Track URIs are the primary identifier for restore; ISRCs are fallback
- Unavailable tracks on import should log a warning and continue
- Print progress during export/import (e.g., "Fetching tracks... 100/342")
- No imports from local modules — fully standalone
