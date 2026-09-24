#!/usr/bin/env python3
"""Autonomous YouTube uploads via the real Data API - no browser automation,
no file-size cap, no manual drag-and-drop.

Credentials live outside the repo at ~/LTX-Studio (same convention as
flow-quota.json): a Google Cloud "installed app" OAuth client
(youtube_client_secret.json) and, after the one-time consent below, a
refresh token (youtube_token.json). The client secret is never committed -
it lives in the user's home directory, not this checkout.

One-time setup (unavoidable - only the channel owner can grant this, the
same way any Google account owner has to click "Allow" on any app that
wants access):

    python3 youtube_upload.py --auth

This opens a local server on localhost and prints a consent URL. Open it,
sign in as the Options Educator channel owner, click Allow. After that,
every call below runs with zero interaction - the refresh token persists.

Usage once authorized:

    python3 youtube_upload.py <video.mp4> --title "..." --description "..." \
        --tags tag1,tag2,tag3 --playlist "Trailers" --privacy unlisted

Or import upload_video() directly from another script.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

CREDS_DIR = Path.home() / "LTX-Studio"
CLIENT_SECRET = CREDS_DIR / "youtube_client_secret.json"
TOKEN_PATH = CREDS_DIR / "youtube_token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube"]


class UploadError(RuntimeError):
    pass


def _get_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_PATH.is_file():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())
    if not creds or not creds.valid:
        if not CLIENT_SECRET.is_file():
            raise UploadError(
                f"No OAuth client at {CLIENT_SECRET} - copy the Google Cloud "
                "'installed app' client_secret*.json there first."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
        # Loopback flow: opens a local server, tries to launch a browser,
        # and prints the URL either way. Only the channel owner can complete
        # this - it is Google's own consent screen, not something this
        # script can click through on its own. One-time only: the resulting
        # refresh token is what makes every later call fully unattended.
        creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
        TOKEN_PATH.chmod(0o600)
    return creds


def _youtube():
    from googleapiclient.discovery import build

    return build("youtube", "v3", credentials=_get_credentials())


def _find_or_create_playlist(yt, title: str) -> str:
    req = yt.playlists().list(part="snippet", mine=True, maxResults=50)
    while req is not None:
        resp = req.execute()
        for item in resp.get("items", []):
            if item["snippet"]["title"] == title:
                return item["id"]
        req = yt.playlists().list_next(req, resp)
    created = (
        yt.playlists()
        .insert(
            part="snippet,status",
            body={
                "snippet": {"title": title},
                "status": {"privacyStatus": "public"},
            },
        )
        .execute()
    )
    return created["id"]


def upload_video(
    video_path: Path,
    title: str,
    description: str,
    tags: list[str],
    playlist: str | None = None,
    privacy: str = "unlisted",
    made_for_kids: bool = False,
) -> str:
    """Upload video_path to the authorized channel. Returns the video id."""
    from googleapiclient.http import MediaFileUpload

    video_path = Path(video_path)
    if not video_path.is_file():
        raise UploadError(f"video not found: {video_path}")

    yt = _youtube()
    media = MediaFileUpload(
        str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4"
    )
    body = {
        "snippet": {"title": title, "description": description, "tags": tags},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": made_for_kids},
    }
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(
                f"  uploading {video_path.name}: {int(status.progress() * 100)}%",
                flush=True,
            )
    video_id = response["id"]
    print(f"uploaded {video_path.name} -> https://youtu.be/{video_id}", flush=True)

    if playlist:
        playlist_id = _find_or_create_playlist(yt, playlist)
        yt.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                }
            },
        ).execute()
        print(f"added to playlist {playlist!r}", flush=True)

    return video_id


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video", nargs="?", help="path to the mp4 to upload")
    ap.add_argument("--title")
    ap.add_argument("--description", default="")
    ap.add_argument("--tags", default="", help="comma-separated")
    ap.add_argument("--playlist", default=None)
    ap.add_argument(
        "--privacy", default="unlisted", choices=["public", "unlisted", "private"]
    )
    ap.add_argument(
        "--auth", action="store_true", help="run the one-time consent flow and exit"
    )
    args = ap.parse_args()

    if args.auth:
        _get_credentials()
        print(f"authorized - token saved to {TOKEN_PATH}", flush=True)
        return 0

    if not args.video or not args.title:
        ap.error("video and --title are required unless using --auth")

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    upload_video(
        Path(args.video),
        args.title,
        args.description,
        tags,
        playlist=args.playlist,
        privacy=args.privacy,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
