#!/usr/bin/env python3
"""GitHub-backed Agent-to-Agent message bus for Vidhaath-AGY <-> Yash-AGY."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys
from typing import Any

REPO = "Vidhaath622/KMRWin"
BUS_TITLE_PREFIX = "[AGENT-BUS]"
BUS_FULL_TITLE = "[AGENT-BUS] PollToll Antigravity Peer Channel (Vidhaath-AGY <-> Yash-AGY)"
STATE_FILE = pathlib.Path(__file__).resolve().parents[4] / ".peer_bus_state.json"


def run_gh(args: list[str]) -> str:
    cmd = ["gh", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command `{' '.join(cmd)}` failed (exit {proc.returncode}):\n{proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def load_state() -> dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_state(state: dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def find_bus_issue() -> dict[str, Any] | None:
    raw = run_gh(
        [
            "issue",
            "list",
            "--repo",
            REPO,
            "--state",
            "open",
            "--search",
            f'"{BUS_TITLE_PREFIX}" in:title',
            "--json",
            "number,title,url,createdAt",
        ]
    )
    issues = json.loads(raw) if raw else []
    for issue in issues:
        if issue.get("title", "").startswith(BUS_TITLE_PREFIX):
            return issue
    return None


def ensure_bus_issue() -> dict[str, Any]:
    existing = find_bus_issue()
    if existing:
        return existing

    body = (
        "## PollToll Agent-to-Agent Communication Bus\n\n"
        "This issue serves as the structured real-time message bus between:\n"
        "- **Vidhaath-AGY** (Vidhaath's Antigravity Agent)\n"
        "- **Yash-AGY** (Yash Gupta's Antigravity Agent)\n\n"
        "### How Yash's Antigravity Connects\n"
        "1. Clone or `git pull` `https://github.com/Vidhaath622/KMRWin.git`\n"
        "2. Ensure `gh auth status` is logged in (and Yash's GitHub account has collaborator access to `Vidhaath622/KMRWin`).\n"
        "3. Tell Yash's Antigravity: *\"Read `AGENTS.md` and check the peer inbox using `.agents/skills/peer-bridge/SKILL.md`.\"*\n"
    )
    url = run_gh(
        [
            "issue",
            "create",
            "--repo",
            REPO,
            "--title",
            BUS_FULL_TITLE,
            "--body",
            body,
        ]
    )
    created = find_bus_issue()
    if not created:
        return {"number": int(url.rstrip("/").split("/")[-1]), "title": BUS_FULL_TITLE, "url": url}
    return created


def cmd_init(_: argparse.Namespace) -> None:
    issue = ensure_bus_issue()
    print(json.dumps({"status": "ok", "bus_issue": issue}, indent=2))


def cmd_send(args: argparse.Namespace) -> None:
    issue = ensure_bus_issue()
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    git_head = "unknown"
    try:
        git_head = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
        )
    except Exception:
        pass

    envelope = {
        "protocol": "polltoll-a2a/v1",
        "sender": args.sender,
        "topic": args.topic,
        "status": args.status,
        "commit": git_head,
        "timestamp_utc": now_iso,
    }
    comment_md = (
        f"### `{args.sender}` • Topic: `{args.topic}` • Status: `{args.status}`\n"
        f"**Commit:** `{git_head}` | **Time (UTC):** `{now_iso}`\n\n"
        f"{args.message}\n\n"
        f"<!-- AGENT_ENVELOPE {json.dumps(envelope)} -->"
    )
    url = run_gh(
        [
            "issue",
            "comment",
            str(issue["number"]),
            "--repo",
            REPO,
            "--body",
            comment_md,
        ]
    )
    print(
        json.dumps(
            {
                "status": "sent",
                "issue_number": issue["number"],
                "comment_url": url,
                "envelope": envelope,
            },
            indent=2,
        )
    )


def parse_envelope(body: str) -> dict[str, Any]:
    marker = "<!-- AGENT_ENVELOPE "
    if marker in body:
        tail = body.split(marker, 1)[1]
        if " -->" in tail:
            raw_json = tail.split(" -->", 1)[0]
            try:
                return json.loads(raw_json)
            except json.JSONDecodeError:
                pass
    return {}


def cmd_inbox(args: argparse.Namespace) -> None:
    issue = find_bus_issue()
    if not issue:
        print(json.dumps({"status": "empty", "reason": "No [AGENT-BUS] issue initialized yet."}))
        return

    raw = run_gh(
        [
            "issue",
            "view",
            str(issue["number"]),
            "--repo",
            REPO,
            "--json",
            "number,title,url,comments",
        ]
    )
    data = json.loads(raw)
    comments = data.get("comments", [])
    state = load_state()
    last_seen_idx = int(state.get(f"last_seen_{args.viewer}", 0)) if args.unread else 0

    sliced = comments[last_seen_idx:]
    formatted = []
    for idx, c in enumerate(sliced, start=last_seen_idx + 1):
        body = c.get("body", "")
        env = parse_envelope(body)
        clean_body = body.split("<!-- AGENT_ENVELOPE ", 1)[0].strip()
        formatted.append(
            {
                "seq": idx,
                "github_author": c.get("author", {}).get("login"),
                "created_at": c.get("createdAt"),
                "sender_agent": env.get("sender", "human-or-unknown"),
                "topic": env.get("topic", "general"),
                "status": env.get("status", "info"),
                "commit": env.get("commit"),
                "body": clean_body,
            }
        )

    state[f"last_seen_{args.viewer}"] = len(comments)
    save_state(state)

    print(
        json.dumps(
            {
                "bus_issue_number": issue["number"],
                "bus_url": issue["url"],
                "total_messages": len(comments),
                "returned_messages": len(formatted),
                "messages": formatted[-args.limit :] if args.limit else formatted,
            },
            indent=2,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PollToll Antigravity Peer-to-Peer Message Bus")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Ensure the [AGENT-BUS] GitHub issue exists")
    p_init.set_defaults(func=cmd_init)

    p_send = sub.add_parser("send", help="Send a message to the peer Antigravity agent")
    p_send.add_argument("--sender", required=True, help="e.g. Vidhaath-AGY or Yash-AGY")
    p_send.add_argument("--topic", default="sync", help="Message topic")
    p_send.add_argument("--status", default="info", help="info | ready | blocked | question")
    p_send.add_argument("--message", required=True, help="Markdown body to send")
    p_send.set_defaults(func=cmd_send)

    p_inbox = sub.add_parser("inbox", help="Read messages from the peer Antigravity channel")
    p_inbox.add_argument("--viewer", default="Vidhaath-AGY", help="Your agent ID")
    p_inbox.add_argument("--unread", action="store_true", help="Only return unread messages")
    p_inbox.add_argument("--limit", type=int, default=15, help="Max messages to display")
    p_inbox.set_defaults(func=cmd_inbox)

    return parser


if __name__ == "__main__":
    parser = build_parser()
    ns = parser.parse_args()
    try:
        ns.func(ns)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        sys.exit(1)
