# DunamisPub for Scrivener™

**Dunamis** — δύναμις, the Greek word for *power*. Drag a document into **Ready to Post** and it publishes itself.

DunamisPub is a macOS automation that turns one gesture in Scrivener into a finished publish: it detects the move, asks where the piece should go, posts it, archives the markdown to a git repo, and files the document under **Published** in your binder.

It is **blog-agnostic**. Destinations are configuration, not assumptions — WordPress sites, static Jekyll sites, or anywhere else you can reach with a script.

> Not affiliated with, endorsed by, or sponsored by Literature & Latte, makers of Scrivener.
> "Scrivener" is their trademark. This tool merely works alongside it.

---

## How it works

```
  drag doc  ──►  Ready to Post
      │
      ├─ 1. launchd agent notices the .scrivx changed
      ├─ 2. binder parsed, new arrivals found, RTF converted to markdown
      ├─ 3. dialog: which destination? (free-text option included)
      ├─ 4. optional AI pass: excerpt, tags, slug, style check
      ├─ 5. published — scheduled a few days out, so there's a window to catch mistakes
      ├─ 6. markdown archived to that destination's git repo, committed, pushed
      └─ 7. document filed under Published/<destination>/<year>
```

## Design principles

**Read-only on your project.** The watcher never writes to the `.scriv` package. If Scrivener changes its format, the watcher finds nothing and does nothing — it cannot corrupt your work.

**The one exception is guarded.** Filing a document back into *Published* is the only write, and it runs only when Scrivener is closed (`Files/user.lock` absent), only when `Files/version.txt` matches the expected version, always after taking a timestamped backup, and it verifies the project still opens afterward.

**Fails loudly, not silently.** A startup canary checks that the *Ready to Post* folder is still findable and notifies you if it isn't. A post that never publishes is worse than an error message.

**Offline is normal.** Written on the road. Queues and retries rather than failing.

## Status

Early. Phase 1 (project scaffolding) and Phase 2 (repo layout) are in place. The watcher,
publisher, and reconciler are in progress.

## Layout

| Path | Holds |
|---|---|
| `bin/` | Entry points — the scaffolder, watcher, publisher, reconciler |
| `lib/` | Binder parsing, RTF conversion, destination adapters |
| `launchd/` | The user agent plist |
| `docs/` | Build plan, setup guide, format notes |
| `config.example.json` | Copy to `config.json` and fill in |

## Requirements

- macOS with Scrivener 3 (built against 3.5.2, project format 23)
- Python 3.9+
- `gh` authenticated, for the archive step
- Credentials in the macOS Keychain — never in this repo

## Setup

```bash
git clone https://github.com/snthor-phd/dunamispub.git
cd dunamispub
cp config.example.json config.json   # edit paths and destinations
bin/scaffold-writing-desk            # optional: build a fresh Writing Desk project
```

## License

MIT. See `LICENSE`.
