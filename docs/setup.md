# Setup

1. `cp config.example.json config.json` and edit the project path and destinations.
2. `bin/install-agent` — renders the launchd plist for this machine and loads it.
3. `bin/dunamis-watch --status` — shows what the watcher currently sees.
4. Drag a document into **Ready to Post**. The agent fires on the binder rewrite.

Keep `publish.dry_run` true until you have watched it behave. In dry-run the
watcher detects, converts, writes Markdown to the outbox, and prompts for a
destination, but publishes nothing.

Outbox: `~/Library/Application Support/DunamisPub/outbox`
State:  `~/Library/Application Support/DunamisPub/state.json`
Log:    `~/Library/Logs/dunamispub.log`

Remove with `bin/install-agent --remove`.
