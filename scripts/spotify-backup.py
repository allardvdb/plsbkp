#!/usr/bin/env python3
"""Spotify playlist backup/restore CLI tool."""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import spotipy
from spotipy.oauth2 import SpotifyPKCE

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

SCOPES = " ".join([
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-public",
    "playlist-modify-private",
])


def get_spotify_client(account=None):
    """Initialize and return an authenticated Spotify client using PKCE."""
    cache_path = f".spotify-token-cache-{account}" if account else ".spotify-token-cache"
    auth_manager = SpotifyPKCE(
        scope=SCOPES,
        cache_path=cache_path,
        open_browser=False,
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def list_playlists(sp):
    """Fetch all playlists for the current user (paginated)."""
    playlists = []
    results = sp.current_user_playlists(limit=50)
    while results:
        playlists.extend(results["items"])
        if results["next"]:
            results = sp.next(results)
        else:
            break
    return playlists


def choose_playlist(playlists):
    """Display a numbered menu and return the selected playlist dict."""
    print("\nYour playlists:\n")
    for i, pl in enumerate(playlists, 1):
        total = pl.get("tracks", {}).get("total", "?")
        print(f"  {i:3d}. {pl['name']}  ({total} tracks)")

    print()
    while True:
        try:
            choice = input("Select a playlist number: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(playlists):
                return playlists[idx]
            print(f"Please enter a number between 1 and {len(playlists)}.")
        except ValueError:
            print("Please enter a valid number.")
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(1)


def export_playlist(sp, playlist_id, output_path):
    """Export a playlist to JSON."""
    playlist = sp.playlist(playlist_id)
    user = sp.current_user()

    tracks = []
    results = playlist.get("tracks") or playlist["items"]
    position = 0
    total = results["total"]
    print(f"Fetching tracks... 0/{total}", end="", flush=True)

    while results:
        for item in results["items"]:
            track = item.get("track") or item.get("item")
            if track is None:
                position += 1
                continue

            isrc = None
            ext_ids = track.get("external_ids")
            if ext_ids:
                isrc = ext_ids.get("isrc")

            tracks.append({
                "position": position,
                "name": track["name"],
                "artists": [a["name"] for a in track["artists"]],
                "album": track["album"]["name"],
                "uri": track["uri"],
                "added_at": item.get("added_at"),
                "duration_ms": track["duration_ms"],
                "isrc": isrc,
            })
            position += 1
            print(f"\rFetching tracks... {position}/{total}", end="", flush=True)

        if results["next"]:
            results = sp.next(results)
        else:
            break

    print()

    backup = {
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_account": user["id"],
        "playlist": {
            "name": playlist["name"],
            "description": playlist.get("description") or "",
            "public": playlist["public"],
            "collaborative": playlist["collaborative"],
            "spotify_id": playlist["id"],
            "snapshot_id": playlist["snapshot_id"],
            "total_tracks": len(tracks),
        },
        "tracks": tracks,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(backup, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(tracks)} tracks to {output_path}")


def import_playlist(sp, input_path, name_override=None):
    """Create a new playlist from a JSON backup."""
    with open(input_path, "r", encoding="utf-8") as f:
        backup = json.load(f)

    playlist_info = backup["playlist"]
    name = name_override or playlist_info["name"]
    description = playlist_info.get("description", "")
    public = playlist_info.get("public", False)

    user = sp.current_user()
    new_playlist = sp.user_playlist_create(
        user["id"],
        name,
        public=public,
        description=description,
    )
    print(f"Created playlist: {name}")

    uris = [t["uri"] for t in backup["tracks"]]
    total = len(uris)
    added = 0

    for i in range(0, total, 100):
        batch = uris[i : i + 100]
        try:
            sp.playlist_add_items(new_playlist["id"], batch)
            added += len(batch)
            print(f"\rAdding tracks... {added}/{total}", end="", flush=True)
        except spotipy.exceptions.SpotifyException as e:
            # Try tracks individually to skip unavailable ones
            for uri in batch:
                try:
                    sp.playlist_add_items(new_playlist["id"], [uri])
                    added += 1
                except spotipy.exceptions.SpotifyException:
                    print(f"\n  Warning: could not add track {uri}, skipping")
            print(f"\rAdding tracks... {added}/{total}", end="", flush=True)

    print(f"\nImported {added}/{total} tracks into '{name}'")
    print(f"Playlist URL: {new_playlist['external_urls']['spotify']}")


def main():
    parser = argparse.ArgumentParser(
        description="Spotify playlist backup/restore tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s list                                  List all your playlists
  %(prog)s export                                Interactive export (pick from menu)
  %(prog)s export --playlist-id ID -o out.json   Export a specific playlist
  %(prog)s import --input backup.json            Restore a playlist from backup
  %(prog)s --account alice export                Use a named account

environment variables (required):
  SPOTIPY_CLIENT_ID       Spotify app client ID
  SPOTIPY_CLIENT_SECRET   Spotify app client secret
  SPOTIPY_REDIRECT_URI    Redirect URI (e.g. http://127.0.0.1:8888/callback)""",
    )
    parser.add_argument("--account", help="Account name (uses separate token cache per account)")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List all your playlists")

    export_parser = subparsers.add_parser("export", help="Export a playlist to JSON")
    export_parser.add_argument("--playlist-id", help="Spotify playlist ID (skips interactive selection)")
    export_parser.add_argument("--output", "-o", help="Output JSON file path")

    import_parser = subparsers.add_parser("import", help="Import/restore a playlist from JSON")
    import_parser.add_argument("--input", "-i", required=True, help="Input JSON backup file")
    import_parser.add_argument("--name", help="Override the playlist name")

    args = parser.parse_args()

    if load_dotenv:
        load_dotenv()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    missing = [v for v in ("SPOTIPY_CLIENT_ID", "SPOTIPY_REDIRECT_URI")
               if not os.environ.get(v)]
    if missing:
        print(f"Error: missing environment variables: {', '.join(missing)}", file=sys.stderr)
        print("Set them in your shell or add them to a .env file.", file=sys.stderr)
        sys.exit(1)

    sp = get_spotify_client(args.account)

    if args.command == "list":
        playlists = list_playlists(sp)
        print(f"\nFound {len(playlists)} playlists:\n")
        for i, pl in enumerate(playlists, 1):
            total = pl.get("tracks", {}).get("total", "?")
            owner = pl.get("owner", {}).get("display_name", "?")
            print(f"  {i:3d}. {pl['name']}  ({total} tracks, by {owner})")

    elif args.command == "export":
        if args.playlist_id:
            # If it looks like a list number, resolve it to a real playlist
            if args.playlist_id.isdigit():
                idx = int(args.playlist_id) - 1
                playlists = list_playlists(sp)
                if idx < 0 or idx >= len(playlists):
                    print(f"Error: number {args.playlist_id} out of range (1-{len(playlists)})", file=sys.stderr)
                    sys.exit(1)
                selected = playlists[idx]
                playlist_id = selected["id"]
                output_path = args.output or f"{selected['name']}.json"
            else:
                playlist_id = args.playlist_id
                output_path = args.output or f"{playlist_id}.json"
        else:
            playlists = list_playlists(sp)
            selected = choose_playlist(playlists)
            playlist_id = selected["id"]
            output_path = args.output or f"{selected['name']}.json"

        export_playlist(sp, playlist_id, output_path)

    elif args.command == "import":
        import_playlist(sp, args.input, args.name)


if __name__ == "__main__":
    main()
