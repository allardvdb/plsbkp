# plsbkp

Spotify playlist backup/restore CLI tool. Export playlists to JSON, import them back — even across accounts.

## Setup

1. Install the dependency:

```bash
pip install spotipy
```

2. Create a Spotify app at https://developer.spotify.com/dashboard and set the redirect URI to `http://localhost:8888/callback`.

3. Set environment variables:

```bash
export SPOTIPY_CLIENT_ID="your_client_id"
export SPOTIPY_CLIENT_SECRET="your_client_secret"
export SPOTIPY_REDIRECT_URI="http://localhost:8888/callback"
```

## Usage

```bash
# List all your playlists
python scripts/spotify-backup.py list

# Interactive export (pick from a menu)
python scripts/spotify-backup.py export

# Direct export
python scripts/spotify-backup.py export --playlist-id <id> --output backup.json

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
