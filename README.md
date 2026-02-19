# plsbkp

Spotify playlist backup/restore CLI tool. Export playlists to JSON, import them back — even across accounts.

## Setup

1. Install dependencies:

```bash
pip install spotipy
pip install python-dotenv  # optional, enables .env file support
```

2. Create a Spotify app at https://developer.spotify.com/dashboard and set the redirect URI to `http://127.0.0.1:8888/callback`.

3. Set environment variables (or add them to a `.env` file):

```bash
export SPOTIPY_CLIENT_ID="your_client_id"
export SPOTIPY_REDIRECT_URI="http://127.0.0.1:8888/callback"
```

Uses PKCE authentication — no client secret required. On first run, the script prints an auth URL to open in your browser.

## Usage

```bash
# List all your playlists
python scripts/spotify-backup.py list

# Interactive export (pick from a menu)
python scripts/spotify-backup.py export

# Export by playlist number (from the list output)
python scripts/spotify-backup.py export --playlist-id 3

# Direct export by Spotify ID
python scripts/spotify-backup.py export --playlist-id <spotify_id> --output backup.json

# Restore a playlist
python scripts/spotify-backup.py import --input backup.json

# Restore with a different name
python scripts/spotify-backup.py import --input backup.json --name "Copy of Playlist"
```

### Multi-account support

Use `--account <name>` to maintain separate auth tokens per account. This makes transferring playlists between accounts seamless:

```bash
# Export from one account
python scripts/spotify-backup.py --account alice export

# Import into another
python scripts/spotify-backup.py --account bob import --input "My Playlist.json"
```

Without `--account`, the default token cache is used.

## JSON backup format

Exports produce a JSON file containing playlist metadata and tracks with URIs, ISRCs, artist/album info, and timestamps. See `spotify-playlist-backup-spec.md` for the full schema.

Exported JSON files (`*.json`) are gitignored by default. An example backup looks like:

```json
{
  "exported_at": "2026-02-19T09:54:18Z",
  "source_account": "username",
  "playlist": {
    "name": "My Playlist",
    "description": "",
    "public": true,
    "collaborative": false,
    "spotify_id": "...",
    "snapshot_id": "...",
    "total_tracks": 42
  },
  "tracks": [
    {
      "position": 0,
      "name": "Track Name",
      "artists": ["Artist"],
      "album": "Album",
      "uri": "spotify:track:...",
      "added_at": "2024-01-15T12:00:00Z",
      "duration_ms": 215493,
      "isrc": "USXX12345678"
    }
  ]
}
```
