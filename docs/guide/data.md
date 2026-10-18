# 7. Saved data and resources

Rusty does not equate closing a terminal, forgetting a lesson, deleting a
conversation, signing out and uninstalling. Each affects different state.

| State | Where to look / what to know |
|---|---|
| Preferences and dotenv credentials | `RUSTY_HOME`, normally `~/.config/rusty` |
| Input history | `history` beneath the Rusty home; accepted input is retained with redaction, so review it before sharing |
| Conversations and catalog | Project namespaces beneath that home; use `--sessions` from the original project |
| Side discussions and trajectories | Separate saved records; inspect before sharing backups |
| Codex sign-in/config | Codex's own home/config, separate from Rusty preferences |
| Memory lessons/service | Managed by `rusty-memoryd`; see [memory guide](../MEMORY.md) |
| Executables | Cargo install bin directory, independent of saved user data |

Transcripts retain conversation and tool evidence; redaction reduces accidental
secret exposure but does not justify publishing raw records. Paths, source code,
user messages and sensitive non-key data can remain. Inspect captures, manifests,
trajectories and archives before sharing. Store credentials in their designated
files/environment rather than prompt text.

Saved transcripts keep their `.json` filename when compressed. Rusty saves JSON
of at least 64 KiB as gzip and reads both formats when resuming. A large saved
conversation shows binary data with `cat`; JSON tools such as `jq` cannot parse
it directly. Use Rusty’s session list and resume commands; inspect the type before a
JSON tool, and decompress only a copy when needed. Compression saves storage;
loading still materializes the transcript in memory.

`--memory off` disables memory for the run; it does not erase prior lessons or
stop a separately running shared memory service. `/clear` keeps memories.
`/forget <id>` removes a lesson, not the conversation that mentioned it.
The default `learn` mode can start a matching companion `rusty-memoryd`.
That service deliberately survives CLI exit and can be reused by later launches;
a detached daemon is not by itself a leaked CLI child. Inspect it with
`rusty-memoryd status` and stop the intended home with `rusty-memoryd stop`
when you deliberately want the service shut down. `status` can itself start a
missing service; use it only when that is intended. Replacing the executable
does not restart an already running daemon. For a custom home, pass the matching
`--home /absolute/path` or `RUSTY_HOME` to companion commands.
Use the [memory lifecycle and commands](../MEMORY.md) to inspect the daemon and
its data. Do not kill an unrelated/shared process just to clean a test fixture.

## Resource expectations

A long conversation can add transcripts, catalog records, captures and memory.
Compaction reduces active context; it is not a storage deletion policy. Provider
budgets do not impose OS RAM or filesystem quotas. Very large paste, output and
session lists should be tested with bounded inputs before relying on them in a
constrained environment. File reads still load the full UTF-8 file before formatting
a selected line range; a small requested range does not impose a RAM cap. Cloud
preparation now spools its largest build context to a private unlinked temporary
file: allow temporary disk space, and inspect [preparation memory](../CLOUD.md#preparation-memory)
before using a constrained machine.

On read-only storage, corrupt JSON, or disk exhaustion, preserve existing bytes
and inspect errors before retrying. A successful-looking preference change should
be checked after restarting. Do not manually edit a live SQLite catalog or delete
transcripts while another session owns them. Back up the whole relevant home
before recovery, and record which executable wrote it.

## Leave or uninstall

Quit owned sessions and inspect any owned service before removing executables.
`cargo uninstall rusty` removes Cargo-managed installed binaries; it does not
remove project files, Rusty data or Codex credentials. For a trial installed with
`--root`, pass the matching `--root` when uninstalling. If you want to remove saved
data, locate the exact Rusty home, back it up, and review its contents first.
Use Codex's own sign-out mechanism for its credentials. Keep these actions
separate so uninstalling one build does not destroy unrelated conversations.

Check: you can locate your data, know what remains after exit, and can identify
owned processes without stopping someone else's session. Default-service cleanup,
forced OOM and a truly full volume require dedicated qualification; a small mock
run does not prove them.
