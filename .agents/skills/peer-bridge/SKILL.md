---
name: peer-bridge
description: >-
  Communicate directly between Vidhaath's Antigravity agent and Yash Gupta's
  Antigravity agent via the shared GitHub CLI message bus on Vidhaath622/KMRWin.
  Use this skill whenever the user asks to talk to the teammate's Antigravity,
  check peer messages, coordinate frontend/backend ownership, announce schema
  changes, or hand off tasks.
---

# Antigravity Peer-to-Peer Bridge (`Vidhaath-AGY <-> Yash-AGY`)

This workspace skill connects the two Antigravity agents collaborating on **PollToll** (`Vidhaath622/KMRWin`) using an issue-backed JSON/Markdown message bus via the authenticated `gh` CLI—requiring zero external accounts or servers.

## Prerequisites

Verify `gh` CLI is installed and authenticated:

```bash
gh auth status
```

If Yash's machine has not run `gh auth login` yet, instruct Yash to run `gh auth login` once in his terminal and ensure `Vidhaath622` has added Yash as a collaborator on `Vidhaath622/KMRWin`.

## Identity Convention

- On Vidhaath's machine, pass `--sender "Vidhaath-AGY"`
- On Yash Gupta's machine, pass `--sender "Yash-AGY"`

## Commands

Run [peer_bus.py](./scripts/peer_bus.py) from the repository root:

### 1. Initialize or Verify the Peer Channel

Ensures the pinned `[AGENT-BUS]` issue exists on `Vidhaath622/KMRWin`:

```bash
python3 .agents/skills/peer-bridge/scripts/peer_bus.py init
```

### 2. Read Incoming Messages from Peer Antigravity

Fetch all messages (or `--unread` for messages since your last check):

```bash
python3 .agents/skills/peer-bridge/scripts/peer_bus.py inbox --viewer "Vidhaath-AGY"
```

### 3. Send a Structured Message to Peer Antigravity

Post an architecture update, task claim, API contract change, or question:

```bash
python3 .agents/skills/peer-bridge/scripts/peer_bus.py send \
  --sender "Vidhaath-AGY" \
  --topic "contract-sync" \
  --status "ready" \
  --message "Backend Change Ledger + OpenAPI contract exported to shared/openapi.json. Ready for Frontend hookup."
```

### 4. Sync Code + Peer Inbox Together

Before starting feature work on `frontend/` or `backend/`, always run:

```bash
git pull --rebase origin main && python3 .agents/skills/peer-bridge/scripts/peer_bus.py inbox --viewer "<YOUR-AGY-ID>"
```
