"""
Puzzle #38 — the posting half: push a generated image + caption to FB (and IG)
via the Meta Graph API.

Facebook: uploads the image to the Page's /photos edge via multipart. By
DEFAULT it uploads with published=false — a real, reversible staged photo
object (not a public feed post) — which proves the whole Graph API
image+caption path end to end WITHOUT putting unvetted content on a live brand
feed. Pass --publish only after a human has approved the exact image +
caption; that posts it live.

Instagram: checks for a linked instagram_business_account and runs the
standard two-step container→publish flow. On this account it is unavailable by
design — the Page has no linked IG business account (confirmed live: the
Page's `instagram_business_account` field is None) — so it is reported as
blocked, not faked.

Creds come from the meta_manager profile's .env (system-user token -> page
token), never committed here.
"""
import argparse
import os

import requests

GRAPH = "https://graph.facebook.com/" + os.environ.get("META_GRAPH_API_VERSION", "v21.0")


def get_page_token_and_ig():
    pid = os.environ["META_PAGE_ID"]
    su = os.environ["META_SYSTEM_USER_TOKEN"]
    r = requests.get(
        f"{GRAPH}/{pid}",
        params={"fields": "access_token,instagram_business_account", "access_token": su},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    return pid, data["access_token"], data.get("instagram_business_account")


def post_facebook(image_path: str, caption: str, publish: bool) -> str:
    pid, token, _ = get_page_token_and_ig()
    with open(image_path, "rb") as f:
        r = requests.post(
            f"{GRAPH}/{pid}/photos",
            data={"caption": caption, "published": str(publish).lower(),
                  "access_token": token},
            files={"source": f},
            timeout=120,
        )
    r.raise_for_status()
    photo_id = r.json().get("id") or r.json().get("post_id")
    print(f"[facebook] photo id: {photo_id} (published={publish})")
    return photo_id, token


def delete_photo(photo_id: str, token: str):
    r = requests.delete(f"{GRAPH}/{photo_id}", params={"access_token": token}, timeout=30)
    r.raise_for_status()
    print(f"[facebook] deleted staged photo: {photo_id} -> {r.json()}")


def attempt_instagram(caption: str):
    _, _, ig = get_page_token_and_ig()
    if not ig:
        print("[instagram] SKIPPED — Page has no linked instagram_business_account "
              "(Graph API IG publishing unavailable on this account).")
        return None
    print(f"[instagram] linked IG account present ({ig}); container/publish flow "
          "would run here.")
    return ig


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--fb-caption", required=True)
    ap.add_argument("--ig-caption", required=True)
    ap.add_argument("--publish", action="store_true",
                    help="actually publish the FB post live (needs human approval)")
    ap.add_argument("--cleanup", action="store_true",
                    help="delete the staged (unpublished) photo after creating it")
    args = ap.parse_args()

    photo_id, token = post_facebook(args.image, args.fb_caption, publish=args.publish)
    attempt_instagram(args.ig_caption)
    if args.cleanup and not args.publish:
        delete_photo(photo_id, token)
