"""
Self-update system. BB proposes code changes by asking Claude to rewrite
a file, then pushes the result to a NEW branch on GitHub (never main
directly) so nothing ships until you review and merge it yourself.

Setup (no code changes needed):
    "set github_token to YOUR_PERSONAL_ACCESS_TOKEN"   (needs repo scope)
    "set github_repo to prajwalsundas47-lang/bb_v4"
"""

import ssl
import certifi
import json
import base64
import urllib.request
import urllib.error
from settings import get_setting
from ai import API_URL, MODEL  # reuse existing Claude wiring

GITHUB_API = "https://api.github.com"

# Holds the most recently proposed (not-yet-applied) update so a follow-up
# "apply update" / "cancel update" command knows what it's acting on.
_pending = {"path": None, "content": None, "instruction": None}


def _gh_request(url, method="GET", data=None):
    token = get_setting("github_token")
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
      return json.loads(resp.read().decode("utf-8"))


def _get_file(repo, path, branch="main"):
    url = f"{GITHUB_API}/repos/{repo}/contents/{path}?ref={branch}"
    data = _gh_request(url)
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def propose_update(filename, instruction):
    """
    Step 1: ask Claude to rewrite `filename` per `instruction`.
    Returns a short spoken summary; does NOT touch GitHub yet.
    """
    repo = get_setting("github_repo")
    if not repo or not get_setting("github_token"):
        return ("I need GitHub access first. Say \"set github_token to "
                 "YOUR_TOKEN\" and \"set github_repo to owner/repo\".")

    try:
        current_content, _ = _get_file(repo, filename)
    except urllib.error.HTTPError as e:
        return f"⚠️ Couldn't fetch {filename} from GitHub (HTTP {e.code})."
    except Exception as e:
        return f"⚠️ GitHub error: {e}"

    prompt = (
        f"Here is the current content of {filename}:\n\n{current_content}\n\n"
        f"Apply this change: {instruction}\n\n"
        "Output ONLY the complete, updated file content. No explanation, "
        "no markdown code fences, no commentary — just the raw file."
    )

    api_key = get_setting("anthropic_api_key")
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL, data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    ctx = ssl.create_default_context(cafile=certifi.where())

    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        new_content = "".join(
            b["text"] for b in data.get("content", []) if b.get("type") == "text"
        ).strip()
    except Exception as e:
        return f"⚠️ AI request failed: {e}"

    if not new_content:
        return "⚠️ AI returned nothing — try rephrasing the instruction."

    _pending["path"] = filename
    _pending["content"] = new_content
    _pending["instruction"] = instruction

    old_lines = current_content.count("\n")
    new_lines = new_content.count("\n")
    return (f"🧠 I've drafted the change to {filename} ({old_lines} → "
            f"{new_lines} lines). Say \"apply update\" to push it to a "
            f"review branch, or \"cancel update\" to discard it.")
    
    
def apply_update():
    """Step 2: push the pending draft to a new branch (never main)."""
    if not _pending["path"]:
    return "There's no pending update to apply."

    repo = get_setting("github_repo")
    filename = _pending["path"]

    try:
        main_sha = _gh_request(f"{GITHUB_API}/repos/{repo}/git/ref/heads/main")["object"]["sha"]

        branch_name = f"bb-self-update-{filename.replace('/', '-').replace('.py', '')}"
        try:
            _gh_request(
                f"{GITHUB_API}/repos/{repo}/git/refs",
                method="POST",
                data={"ref": f"refs/heads/{branch_name}", "sha": main_sha}
            )
        except urllib.error.HTTPError as e:
            if e.code != 422:  # 422 = branch already exists, fine, reuse it
                raise

        _, file_sha = _get_file(repo, filename, branch=branch_name)

        _gh_request(
            f"{GITHUB_API}/repos/{repo}/contents/{filename}",
            method="PUT",
            data={
                "message": f"BB self-update: {_pending['instruction']}",
                "content": base64.b64encode(_pending["content"].encode("utf-8")).decode("utf-8"),
                "sha": file_sha,
                "branch": branch_name
            }
        )

        _pending["path"] = None
        return (f"✅ Pushed to branch '{branch_name}'. Open GitHub and "
                f"merge it into main when you're happy — that'll trigger a rebuild.")

    except Exception as e:
        return f"⚠️ Couldn't push update: {e}"


def cancel_update():
    if not _pending["path"]:
        return "There's nothing pending to cancel."
    _pending["path"] = None
    return "🗑️ Discarded the pending update."
