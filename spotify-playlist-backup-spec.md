# Spotify Playlist Backup/Restore Tool — Spec

## Goal

Create a single-file Python CLI script (`spotify-backup.py`) that can:

1. **List** all playlists in my Spotify account and let me interactively pick one
2. **Export** a playlist to a `.json` file (backup)
3. **Import/restore** a playlist from a `.json` backup (creates a new playlist)

## Requirements

- **Single file** — no package structure, just `scripts/spotify-backup.py`
- **Auth via env vars** — use the `spotipy` library which reads `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and `SPOTIPY_REDIRECT_URI` automatically. These must be set before running.
- **OAuth2 scopes needed**: `playlist-read-private`, `playlist-read-collaborative`, `playlist-modify-public`, `playlist-modify-private`
- **CLI interface** — use `argparse` with subcommands:
  - `python spotify-backup.py list` — list all playlists (numbered), no further action
  - `python spotify-backup.py export` — list playlists, let me pick one, export to JSON
  - `python spotify-backup.py export --playlist-id <id> --output <file>` — export directly without interactive selection
  - `python spotify-backup.py import --input <file>` — create a new playlist from JSON backup
  - `python spotify-backup.py import --input <file> --name "New Name"` — override the playlist name on import
- **Pagination** — Spotify API returns max 100 items per page. Handle pagination for both playlist listing and track fetching.
- **Dependencies**: `spotipy`, `requests` (spotipy dep). No other external deps.

## JSON Backup Schema

```json
{
  "exported_at": "2026-02-18T14:30:00Z",
  "source_account": "username",
  "playlist": {
    "name": "My Playlist",
    "description": "Optional description",
    "public": false,
    "collaborative": false,
    "spotify_id": "abc123",
    "snapshot_id": "xyz789",
    "total_tracks": 42
  },
  "tracks": [
    {
      "position": 0,
      "name": "Track Name",
      "artists": ["Artist 1", "Artist 2"],
      "album": "Album Name",
      "uri": "spotify:track:4iV5W9uYEdYUVa79Axb7Rh",
      "added_at": "2024-01-15T10:00:00Z",
      "duration_ms": 210000,
      "isrc": "USRC12345678"
    }
  ]
}
```

- `uri` is the critical field for restore — it uniquely identifies tracks
- `isrc` is stored as fallback identifier (international standard recording code)
- Human-readable fields (`name`, `artists`, `album`) are for reference when browsing the JSON

## Function Breakdown

1. `get_spotify_client()` — init spotipy with OAuth2, cache token in `.spotify-token-cache`
2. `list_playlists(sp)` — fetch all playlists (paginated), return list of dicts
3. `choose_playlist(playlists)` — interactive numbered selection, returns playlist dict
4. `export_playlist(sp, playlist_id, output_path)` — fetch all tracks (paginated), write JSON
5. `import_playlist(sp, input_path, name_override=None)` — read JSON, create playlist, add tracks in batches of 100
6. `main()` — argparse + dispatch

## Error Handling

- Missing env vars → clear error message listing what's needed
- Expired/invalid token → spotipy handles refresh automatically
- Tracks unavailable on import (e.g., region-locked) → log warning, continue with remaining tracks
- Network errors → let exceptions propagate with readable messages

## Usage Examples

```bash
# Set env vars (or put in .env and source it)
export SPOTIPY_CLIENT_ID="your_client_id"
export SPOTIPY_CLIENT_SECRET="your_client_secret"
export SPOTIPY_REDIRECT_URI="http://localhost:8888/callback"

# List all playlists
python scripts/spotify-backup.py list

# Interactive export
python scripts/spotify-backup.py export

# Direct export
python scripts/spotify-backup.py export --playlist-id 37i9dQZF1DXcBWIGoYBM5M --output today-top-hits.json

# Restore to new playlist
python scripts/spotify-backup.py import --input today-top-hits.json

# Restore with different name
python scripts/spotify-backup.py import --input today-top-hits.json --name "Top Hits Copy"
```

## Setup Instructions

```bash
pip install spotipy
```

Create a Spotify app at https://developer.spotify.com/dashboard to get client ID and secret. Set redirect URI to `http://localhost:8888/callback` in both the app settings and env var.

## File Location

`/home/coach/productivity/scripts/spotify-backup.py`

## Style

- Follow existing script patterns in `/home/coach/productivity/scripts/`
- `#!/usr/bin/env python3` shebang
- Standalone, no imports from local modules
- Print progress during export/import (e.g., "Fetching tracks... 100/342")
