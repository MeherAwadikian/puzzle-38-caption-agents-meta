"""
Puzzle #38 — two caption agents post a generated image to FB/IG (Meta Graph API).

This module is the "two caption agents" half: a generated image goes in, and
TWO distinct LLM agents collaborate to produce the final captions:

  - Agent 1 (COPYWRITER): drafts a punchy first-pass caption for the image on
    the given brief/brand.
  - Agent 2 (BRAND EDITOR): takes Agent 1's draft and rewrites it to the brand
    voice, tightening it and producing two platform-specific variants (a
    longer Facebook caption and a shorter, hashtag-led Instagram caption).

Two agents, not one call with two jobs — the editor only ever sees the
copywriter's draft + the brief, mirroring a real copy → edit handoff.

Output: JSON { "facebook": "...", "instagram": "..." } to stdout.
"""
import json
import os
import sys
import urllib.request

OPENROUTER_KEY = os.environ["OPENROUTER_API_KEY"]
MODEL = "nvidia/nemotron-3.5-lightning:free"


def _chat(system: str, user: str) -> str:
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {OPENROUTER_KEY}",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()


def copywriter_agent(brief: str, image_desc: str) -> str:
    system = (
        "You are a social-media COPYWRITER. Given a brand brief and a "
        "description of the image being posted, write ONE punchy first-draft "
        "caption (2-3 sentences). Output only the caption text."
    )
    return _chat(system, f"Brand brief: {brief}\nImage: {image_desc}")


def brand_editor_agent(brief: str, draft: str) -> dict:
    system = (
        "You are a BRAND EDITOR. You receive a copywriter's draft caption and "
        "the brand brief. Rewrite it to a confident, concrete brand voice (no "
        "hype words like 'revolutionary', no emojis in the Facebook version). "
        "Produce TWO platform variants and output EXACTLY a JSON object with "
        "keys 'facebook' (longer, 2-4 sentences, a clear point) and 'instagram' "
        "(shorter, punchy, ending with 4-6 relevant hashtags). No prose outside "
        "the JSON."
    )
    out = _chat(system, f"Brand brief: {brief}\nCopywriter draft: {draft}")
    if out.startswith("```"):
        out = out.split("```")[1].lstrip("json").strip()
    return json.loads(out)


def run(brief: str, image_desc: str) -> dict:
    draft = copywriter_agent(brief, image_desc)
    print(f"[agent 1 — copywriter] {draft}", file=sys.stderr)
    final = brand_editor_agent(brief, draft)
    print(f"[agent 2 — brand editor] facebook: {final.get('facebook')}", file=sys.stderr)
    print(f"[agent 2 — brand editor] instagram: {final.get('instagram')}", file=sys.stderr)
    return final


if __name__ == "__main__":
    brief = sys.argv[1] if len(sys.argv) > 1 else (
        "AiOlogy — an AI automation agency that turns repetitive business "
        "busywork into reliable automated workflows for small and mid-size teams."
    )
    image_desc = sys.argv[2] if len(sys.argv) > 2 else (
        "a clean, modern illustration of tangled manual tasks on the left "
        "flowing into smooth automated pipelines on the right"
    )
    print(json.dumps(run(brief, image_desc), indent=2))
