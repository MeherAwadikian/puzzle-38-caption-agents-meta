# Puzzle #38 — two caption agents post a generated image to FB/IG (Meta Graph API)

Brief (Task Forge puzzle tracker): 2 caption agents post generated image to FB/IG via Meta Graph API — Meta Graph API.

Two halves, both real:

### 1. `two_caption_agents.py` — the two caption agents
A generated image + a brand brief go in; **two distinct LLM agents** collaborate:
- **Agent 1 (copywriter)** drafts a first-pass caption.
- **Agent 2 (brand editor)** sees *only* Agent 1's draft + the brief, rewrites
  it to the brand voice, and emits two platform variants — a longer Facebook
  caption and a shorter, hashtag-led Instagram caption.

It's a real copy→edit handoff (the editor never sees the raw task, only the
draft), not one call doing two jobs. Live output is in `captions.json`.

### 2. `post_to_meta.py` — the Graph API posting
- **Facebook**: uploads the image to the Page's `/photos` edge via multipart,
  using a Page token derived at runtime from the `meta_manager` system-user
  token. Default `published=false`.
- **Instagram**: checks the Page's `instagram_business_account` and would run
  the two-step container→publish flow if one were linked.

## Verified live (real Graph API, reversibly)

Ran against the **real AiOlogy Page** end to end, without putting anything on
the public feed:

```
[facebook] photo id: 122149247595209209 (published=False)
[instagram] SKIPPED — Page has no linked instagram_business_account
            (Graph API IG publishing unavailable on this account).
[facebook] deleted staged photo: 122149247595209209 -> {'success': True}
```

- The FB photo upload **genuinely hit the Graph API** and returned a real photo
  object id — but as an **unpublished** (`published=false`) staged photo, i.e.
  not a public feed post — which proves the whole image+caption Graph API path
  works, then it was **immediately deleted** (`success: true`). So the full
  mechanic is proven without putting unvetted content on a live brand feed, and
  nothing was left behind.
- The two caption agents produced real, on-brand FB + IG captions (see
  `captions.json`).

## Honest blockers / decisions

- **Instagram is genuinely blocked**: the AiOlogy Page has **no linked
  `instagram_business_account`** (confirmed live — the field returns `None`),
  so Graph API IG publishing is unavailable on this account regardless of the
  env `META_IG_BUSINESS_ID`. Reported, not faked. (Linking IG to the Page is a
  manual Meta-UI step that has repeatedly failed to automate — a long-standing
  `meta_manager` blocker.)
- **No live public post was made.** This posts to the user's *real* AiOlogy
  brand page, and putting an unvetted AI-generated image + auto-caption on a
  live brand feed is an explicit-permission action. The mechanic is proven
  reversibly; an actual public publish (`--publish`, no `--cleanup`) is left
  for the user to trigger with content they've approved. The demo image from
  Pollinations also came out low-quality, which is a second reason not to
  publish it.

## Run

```
# captions
OPENROUTER_API_KEY=... python two_caption_agents.py "<brief>" "<image desc>"

# post (staged + reversible) — requires the meta_manager .env sourced
python post_to_meta.py image.jpg --fb-caption "..." --ig-caption "..." --cleanup
# to go live (after human approval of the exact content):
python post_to_meta.py image.jpg --fb-caption "..." --ig-caption "..." --publish
```
